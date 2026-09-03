from django.conf import settings
from django.utils import timezone
from django.db import transaction, models
from django.db.models import Q
from datetime import timedelta
from .models import Book, BorrowRecord, BookReservation, BookReview, WishlistItem, Category


def get_borrow_period_days():
    return getattr(settings, 'LIBRARY_BORROW_PERIOD_DAYS', 14)


def get_max_borrow_limit():
    return getattr(settings, 'LIBRARY_MAX_BORROW_LIMIT', 5)


def calculate_fine(due_date, return_date=None):
    if return_date is None:
        return_date = timezone.now().date()
    if return_date <= due_date:
        return 0
    days = (return_date - due_date).days
    free_days = getattr(settings, 'LIBRARY_FINE_FREE_DAYS', 7)
    initial_rate = getattr(settings, 'LIBRARY_FINE_INITIAL_RATE', 5)
    late_rate = getattr(settings, 'LIBRARY_FINE_LATE_RATE', 10)
    if days <= free_days:
        return days * initial_rate
    return (free_days * initial_rate) + ((days - free_days) * late_rate)


def calculate_days_overdue(due_date):
    today = timezone.now().date()
    if today > due_date:
        return (today - due_date).days
    return 0


def can_issue_book(member, book):
    errors = []
    if not hasattr(member, 'member_profile'):
        errors.append('Member profile not found.')
        return errors
    if not member.member_profile.is_active_member:
        errors.append('Member account is inactive.')
        return errors
    if not book.is_available():
        errors.append('This book is currently unavailable (no copies available).')
    active_count = BorrowRecord.objects.filter(
        member=member, status='issued'
    ).count()
    max_limit = get_max_borrow_limit()
    if active_count >= max_limit:
        errors.append(f'Borrowing limit reached (max {max_limit} books).')
    already_has = BorrowRecord.objects.filter(
        member=member, book=book, status='issued'
    ).exists()
    if already_has:
        errors.append('Member already has this book issued.')
    return errors


@transaction.atomic
def issue_book(member, book, issued_by=None):
    errors = can_issue_book(member, book)
    if errors:
        return None, errors
    today = timezone.now().date()
    due_date = today + timedelta(days=get_borrow_period_days())
    record = BorrowRecord.objects.create(
        member=member,
        book=book,
        issue_date=today,
        due_date=due_date,
        status='issued',
        issued_by=issued_by,
    )
    book.available_copies -= 1
    book.borrow_count += 1
    book.save(update_fields=['available_copies', 'borrow_count'])
    return record, []


@transaction.atomic
def return_book(record, returned_by=None):
    if record.status == 'returned':
        return record, 'This book has already been returned.'
    if record.status == 'lost':
        return record, 'This book is marked as lost.'
    today = timezone.now().date()
    record.return_date = today
    fine = calculate_fine(record.due_date, today)
    record.fine_amount = fine
    record.status = 'returned'
    record.returned_to = returned_by
    record.save(update_fields=['return_date', 'fine_amount', 'status', 'returned_to'])
    record.book.available_copies += 1
    record.book.save(update_fields=['available_copies'])
    return record, None


def update_overdue_records():
    today = timezone.now().date()
    BorrowRecord.objects.filter(
        status='issued',
        due_date__lt=today
    ).update(status='overdue')
    overdue_records = BorrowRecord.objects.filter(
        status='issued',
        due_date__lt=today
    )
    for record in overdue_records:
        record.status = 'overdue'
        record.fine_amount = calculate_fine(record.due_date, today)
        record.save(update_fields=['status', 'fine_amount'])
    return overdue_records.count()


def get_dashboard_stats():
    from django.contrib.auth.models import User
    update_overdue_records()
    total_books = Book.objects.count()
    total_available = sum(b.available_copies for b in Book.objects.all())
    total_issued = BorrowRecord.objects.filter(status='issued').count()
    total_overdue = BorrowRecord.objects.filter(status='overdue').count()
    total_members = User.objects.filter(is_active=True).count()
    total_fines = sum(
        r.fine_amount for r in BorrowRecord.objects.filter(fine_amount__gt=0)
    )
    recent_issues = BorrowRecord.objects.select_related(
        'member', 'book', 'book__author'
    ).filter(status='issued').order_by('-created_at')[:10]
    recent_returns = BorrowRecord.objects.select_related(
        'member', 'book', 'book__author'
    ).filter(status='returned').order_by('-return_date')[:10]
    overdue_books = BorrowRecord.objects.select_related(
        'member', 'book', 'book__author'
    ).filter(status='overdue').order_by('due_date')[:10]
    popular_books = Book.objects.order_by('-borrow_count')[:10]
    return {
        'total_books': total_books,
        'total_available': total_available,
        'total_issued': total_issued,
        'total_overdue': total_overdue,
        'total_members': total_members,
        'total_fines': total_fines,
        'recent_issues': recent_issues,
        'recent_returns': recent_returns,
        'overdue_books': overdue_books,
        'popular_books': popular_books,
    }


def search_books(query=None, category=None, author=None, availability=None):
    qs = Book.objects.select_related('author', 'category', 'publisher')
    if query:
        qs = qs.filter(
            Q(title__icontains=query) |
            Q(isbn__icontains=query) |
            Q(author__name__icontains=query) |
            Q(category__name__icontains=query)
        )
    if category:
        qs = qs.filter(category_id=category)
    if author:
        qs = qs.filter(author_id=author)
    if availability == 'available':
        qs = qs.filter(available_copies__gt=0)
    elif availability == 'unavailable':
        qs = qs.filter(available_copies=0)
    elif availability == 'limited':
        qs = qs.filter(available_copies__gt=0, available_copies__lt=models.F('total_copies'))
    return qs


def create_reservation(member, book):
    """Create a reservation for a book. Returns (reservation, errors)."""
    errors = []
    if hasattr(book, 'is_available') and book.is_available():
        errors.append('This book is currently available. You can borrow it directly.')
        return None, errors
    if not hasattr(member, 'member_profile') or not member.member_profile.is_active_member:
        errors.append('Member account is inactive.')
        return None, errors
    existing = book.reservations.filter(
        member=member, status__in=['pending', 'ready']
    ).exists()
    if existing:
        errors.append('You already have an active reservation for this book.')
        return None, errors
    max_position = book.reservations.filter(
        status__in=['pending', 'ready']
    ).aggregate(max=models.Max('position'))['max']
    position = (max_position or 0) + 1
    reservation = BookReservation.objects.create(
        book=book, member=member, status='pending', position=position
    )
    return reservation, []


def toggle_wishlist(user, book):
    item, created = WishlistItem.objects.get_or_create(user=user, book=book)
    if created:
        return 'added'
    item.delete()
    return 'removed'


def save_review(user, book, rating, comment):
    review, created = BookReview.objects.update_or_create(
        book=book,
        user=user,
        defaults={'rating': rating, 'comment': comment},
    )
    return review, created


def get_chart_data():
    """Return data for dashboard charts."""
    from django.db.models import Count
    from datetime import datetime, date
    today = timezone.now().date()
    labels = []
    data = []
    for i in range(5, -1, -1):
        ref = today - timedelta(days=30 * i)
        month_start = date(ref.year, ref.month, 1)
        if ref.month == 12:
            next_month = date(ref.year + 1, 1, 1)
        else:
            next_month = date(ref.year, ref.month + 1, 1)
        labels.append(month_start.strftime('%b'))
        count = BorrowRecord.objects.filter(
            issue_date__gte=month_start,
            issue_date__lt=next_month,
        ).count()
        data.append(count)
    # Category distribution
    categories = []
    cat_counts = []
    for cat in Category.objects.annotate(book_count=Count('books')).order_by('-book_count'):
        categories.append(cat.name)
        cat_counts.append(cat.book_count)
    return {
        'monthly_labels': labels,
        'monthly_data': data,
        'category_labels': categories,
        'category_data': cat_counts,
    }
