import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, HttpResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Book, Author, Category, Publisher, BorrowRecord,
    BookReview, BookReservation, WishlistItem,
)
from .forms import (
    BookForm, AuthorForm, CategoryForm, PublisherForm,
    IssueBookForm, BookSearchForm,
)
from .services import (
    get_dashboard_stats, issue_book, return_book,
    search_books, update_overdue_records, calculate_fine,
    create_reservation, toggle_wishlist, save_review, get_chart_data,
)
from .utils import get_borrow_period_days


def custom_404(request, exception):
    return render(request, 'library/404.html', status=404)


def custom_500(request):
    return render(request, 'library/500.html', status=500)


@login_required
def dashboard_view(request):
    update_overdue_records()
    stats = get_dashboard_stats()
    chart = get_chart_data()
    stats['chart_json'] = json.dumps(chart)
    return render(request, 'dashboard/index.html', stats)


@login_required
def book_list_view(request):
    form = BookSearchForm(request.GET)
    books = Book.objects.select_related('author', 'category', 'publisher')
    if form.is_valid():
        books = search_books(
            query=form.cleaned_data.get('query'),
            category=form.cleaned_data.get('category'),
            author=form.cleaned_data.get('author'),
            availability=form.cleaned_data.get('availability'),
        )
    paginator = Paginator(books, 12)
    page = request.GET.get('page', 1)
    books_page = paginator.get_page(page)
    return render(request, 'library/book_list.html', {
        'books': books_page,
        'search_form': form,
    })


@login_required
def book_detail_view(request, pk):
    book = get_object_or_404(
        Book.objects.select_related('author', 'category', 'publisher'),
        pk=pk
    )
    recent_borrows = BorrowRecord.objects.filter(
        book=book
    ).select_related('member').order_by('-created_at')[:10]
    reviews = book.reviews.select_related('user')[:20]
    user_review = None
    in_wishlist = False
    has_reservation = False
    if request.user.is_authenticated:
        user_review = book.reviews.filter(user=request.user).first()
        in_wishlist = book.wishlisted_by.filter(user=request.user).exists()
        has_reservation = book.reservations.filter(
            member=request.user, status__in=['pending', 'ready']
        ).exists()
    return render(request, 'library/book_detail.html', {
        'book': book,
        'recent_borrows': recent_borrows,
        'reviews': reviews,
        'user_review': user_review,
        'in_wishlist': in_wishlist,
        'has_reservation': has_reservation,
    })


@login_required
def book_create_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to add books.')
        return redirect('book_list')
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" added successfully.')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm()
    return render(request, 'library/book_form.html', {'form': form, 'action': 'Add'})


@login_required
def book_edit_view(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to edit books.')
        return redirect('book_list')
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f'Book "{book.title}" updated successfully.')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
    return render(request, 'library/book_form.html', {
        'form': form, 'action': 'Edit', 'book': book
    })


@login_required
@require_POST
def book_delete_view(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can delete books.')
        return redirect('book_list')
    book = get_object_or_404(Book, pk=pk)
    title = book.title
    book.delete()
    messages.success(request, f'Book "{title}" deleted successfully.')
    return redirect('book_list')


@login_required
def issue_book_view(request):
    is_staff = request.user.is_staff or request.user.is_superuser
    if request.method == 'POST':
        if is_staff:
            form = IssueBookForm(request.POST)
        else:
            form = IssueBookForm(request.POST, for_member=request.user)
        if form.is_valid():
            if is_staff:
                member_profile = form.cleaned_data['member']
            else:
                member_profile = request.user.member_profile
            book = form.cleaned_data['book']
            record, errors = issue_book(member_profile.user, book, issued_by=request.user)
            if errors:
                for error in errors:
                    messages.error(request, error)
            else:
                messages.success(
                    request,
                    f'Book "{book.title}" issued to {member_profile.user.get_full_name()} '
                    f'Due: {record.due_date}'
                )
                return redirect('borrowing_history')
    else:
        if is_staff:
            form = IssueBookForm()
        else:
            form = IssueBookForm(for_member=request.user)
    update_overdue_records()
    return render(request, 'library/issue_book.html', {
        'form': form,
        'borrow_period_days': get_borrow_period_days(),
    })


@login_required
def return_book_view(request):
    is_staff = request.user.is_staff or request.user.is_superuser
    update_overdue_records()
    query = request.GET.get('q', '')
    active_records = BorrowRecord.objects.filter(
        status__in=['issued', 'overdue']
    ).select_related('member', 'book', 'book__author')
    if not is_staff:
        active_records = active_records.filter(member=request.user)
    if query:
        active_records = active_records.filter(
            Q(member__username__icontains=query) |
            Q(member__first_name__icontains=query) |
            Q(member__last_name__icontains=query) |
            Q(book__title__icontains=query) |
            Q(book__isbn__icontains=query)
        )
    return render(request, 'library/return_book.html', {
        'active_records': active_records,
        'query': query,
    })


@login_required
@require_POST
def return_book_confirm_view(request, pk):
    record = get_object_or_404(BorrowRecord, pk=pk)
    if not (request.user.is_staff or request.user.is_superuser):
        if record.member != request.user:
            messages.error(request, 'You do not have permission to return this book.')
            return redirect('borrowing_history')
    record, error = return_book(record, returned_by=request.user)
    if error:
        messages.error(request, error)
    else:
        msg = f'Book "{record.book.title}" returned successfully.'
        if record.fine_amount > 0:
            msg += f' Fine: ₹{record.fine_amount:.2f}'
        messages.success(request, msg)
    return redirect('return_book')


@login_required
def borrowing_history_view(request):
    records = BorrowRecord.objects.select_related(
        'member', 'book', 'book__author', 'issued_by', 'returned_to'
    )
    status_filter = request.GET.get('status', '')
    if status_filter:
        records = records.filter(status=status_filter)
    if not (request.user.is_staff or request.user.is_superuser):
        records = records.filter(member=request.user)
    paginator = Paginator(records, 15)
    page = request.GET.get('page', 1)
    records_page = paginator.get_page(page)
    return render(request, 'library/borrowing_history.html', {
        'records': records_page,
        'status_filter': status_filter,
    })


@login_required
def author_list_view(request):
    authors = Author.objects.annotate(book_count_val=Count('books')).order_by('name')
    query = request.GET.get('q', '')
    if query:
        authors = authors.filter(name__icontains=query)
    paginator = Paginator(authors, 15)
    page = request.GET.get('page', 1)
    authors_page = paginator.get_page(page)
    return render(request, 'library/author_list.html', {
        'authors': authors_page, 'query': query
    })


@login_required
def author_detail_view(request, pk):
    author = get_object_or_404(Author, pk=pk)
    books = author.books.select_related('category', 'publisher')
    return render(request, 'library/author_detail.html', {
        'author': author, 'books': books
    })


@login_required
def author_create_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission.')
        return redirect('author_list')
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            author = form.save()
            messages.success(request, f'Author "{author.name}" added.')
            return redirect('author_list')
    else:
        form = AuthorForm()
    return render(request, 'library/author_form.html', {'form': form, 'action': 'Add'})


@login_required
def author_edit_view(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission.')
        return redirect('author_list')
    author = get_object_or_404(Author, pk=pk)
    if request.method == 'POST':
        form = AuthorForm(request.POST, instance=author)
        if form.is_valid():
            form.save()
            messages.success(request, f'Author "{author.name}" updated.')
            return redirect('author_list')
    else:
        form = AuthorForm(instance=author)
    return render(request, 'library/author_form.html', {
        'form': form, 'action': 'Edit', 'author': author
    })


@login_required
@require_POST
def author_delete_view(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can delete authors.')
        return redirect('author_list')
    author = get_object_or_404(Author, pk=pk)
    author.delete()
    messages.success(request, f'Author "{author.name}" deleted.')
    return redirect('author_list')


@login_required
def category_list_view(request):
    categories = Category.objects.annotate(book_count_val=Count('books')).order_by('name')
    query = request.GET.get('q', '')
    if query:
        categories = categories.filter(name__icontains=query)
    return render(request, 'library/category_list.html', {
        'categories': categories, 'query': query
    })


@login_required
def category_detail_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    books = category.books.select_related('author', 'publisher')
    paginator = Paginator(books, 12)
    page = request.GET.get('page', 1)
    books_page = paginator.get_page(page)
    return render(request, 'library/category_detail.html', {
        'category': category, 'books': books_page
    })


@login_required
def category_create_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission.')
        return redirect('category_list')
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'library/category_form.html', {'form': form, 'action': 'Add'})


@login_required
def category_edit_view(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission.')
        return redirect('category_list')
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'library/category_form.html', {
        'form': form, 'action': 'Edit', 'category': category
    })


@login_required
@require_POST
def category_delete_view(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can delete categories.')
        return redirect('category_list')
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, 'Category deleted.')
    return redirect('category_list')


@login_required
def publisher_list_view(request):
    publishers = Publisher.objects.annotate(book_count_val=Count('books')).order_by('name')
    query = request.GET.get('q', '')
    if query:
        publishers = publishers.filter(name__icontains=query)
    return render(request, 'library/publisher_list.html', {
        'publishers': publishers, 'query': query
    })


@login_required
def publisher_detail_view(request, pk):
    publisher = get_object_or_404(Publisher, pk=pk)
    books = publisher.books.select_related('author', 'category')
    return render(request, 'library/publisher_detail.html', {
        'publisher': publisher, 'books': books
    })


@login_required
def publisher_create_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission.')
        return redirect('publisher_list')
    if request.method == 'POST':
        form = PublisherForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Publisher created.')
            return redirect('publisher_list')
    else:
        form = PublisherForm()
    return render(request, 'library/publisher_form.html', {'form': form, 'action': 'Add'})


@login_required
def publisher_edit_view(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission.')
        return redirect('publisher_list')
    publisher = get_object_or_404(Publisher, pk=pk)
    if request.method == 'POST':
        form = PublisherForm(request.POST, instance=publisher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Publisher updated.')
            return redirect('publisher_list')
    else:
        form = PublisherForm(instance=publisher)
    return render(request, 'library/publisher_form.html', {
        'form': form, 'action': 'Edit', 'publisher': publisher
    })


@login_required
@require_POST
def publisher_delete_view(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can delete publishers.')
        return redirect('publisher_list')
    publisher = get_object_or_404(Publisher, pk=pk)
    publisher.delete()
    messages.success(request, 'Publisher deleted.')
    return redirect('publisher_list')


@login_required
def reports_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission.')
        return redirect('dashboard')
    update_overdue_records()
    from django.contrib.auth.models import User
    total_books = Book.objects.count()
    total_copies = sum(b.total_copies for b in Book.objects.all())
    total_issued = BorrowRecord.objects.filter(status='issued').count()
    total_returned = BorrowRecord.objects.filter(status='returned').count()
    total_overdue = BorrowRecord.objects.filter(status='overdue').count()
    total_lost = BorrowRecord.objects.filter(status='lost').count()
    total_members = User.objects.filter(is_active=True).count()
    total_fines = BorrowRecord.objects.aggregate(total=Sum('fine_amount'))['total'] or 0
    collected_fines = BorrowRecord.objects.filter(
        status='returned', fine_amount__gt=0
    ).aggregate(total=Sum('fine_amount'))['total'] or 0
    pending_fines = total_fines - collected_fines
    popular_books = Book.objects.order_by('-borrow_count')[:10]
    active_members = User.objects.annotate(
        borrow_count=Count('borrow_records')
    ).order_by('-borrow_count')[:10]
    category_stats = Category.objects.annotate(
        book_count_val=Count('books')
    ).order_by('-book_count_val')
    return render(request, 'library/reports.html', {
        'total_books': total_books,
        'total_copies': total_copies,
        'total_issued': total_issued,
        'total_returned': total_returned,
        'total_overdue': total_overdue,
        'total_lost': total_lost,
        'total_members': total_members,
        'total_fines': total_fines,
        'collected_fines': collected_fines,
        'pending_fines': pending_fines,
        'popular_books': popular_books,
        'active_members': active_members,
        'category_stats': category_stats,
    })


@login_required
@require_POST
def review_book_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        messages.error(request, 'Please select a valid rating.')
        return redirect('book_detail', pk=book.pk)
    if rating < 1 or rating > 5:
        messages.error(request, 'Rating must be between 1 and 5.')
        return redirect('book_detail', pk=book.pk)
    review, created = save_review(request.user, book, rating, comment)
    if created:
        messages.success(request, f'Thanks! Your {rating}★ rating for "{book.title}" was saved.')
    else:
        messages.success(request, 'Your review was updated.')
    return redirect('book_detail', pk=book.pk)


@login_required
@require_POST
def delete_review_view(request, pk):
    review = get_object_or_404(BookReview, pk=pk)
    if review.user != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to delete this review.')
        return redirect('book_detail', pk=review.book.pk)
    book = review.book
    review.delete()
    messages.success(request, 'Review removed.')
    return redirect('book_detail', pk=book.pk)


@login_required
@require_POST
def reserve_book_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reservation, errors = create_reservation(request.user, book)
    if errors:
        for error in errors:
            messages.error(request, error)
    else:
        messages.success(
            request,
            f'Reservation placed for "{book.title}". You are #{reservation.position} in the queue.'
        )
    return redirect('book_detail', pk=book.pk)


@login_required
@require_POST
def cancel_reservation_view(request, pk):
    reservation = get_object_or_404(BookReservation, pk=pk)
    if reservation.member != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission.')
        return redirect('dashboard')
    book_title = reservation.book.title
    reservation.delete()
    messages.success(request, f'Reservation for "{book_title}" cancelled.')
    return redirect('dashboard')


@login_required
@require_POST
def toggle_wishlist_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    action = toggle_wishlist(request.user, book)
    if action == 'added':
        messages.success(request, f'"{book.title}" added to your wishlist.')
    else:
        messages.info(request, f'"{book.title}" removed from your wishlist.')
    return redirect('book_detail', pk=book.pk)


@login_required
def wishlist_view(request):
    items = WishlistItem.objects.filter(
        user=request.user
    ).select_related('book', 'book__author')[:50]
    return render(request, 'library/wishlist.html', {'items': items})


def _export_csv_response(filename, header, rows):
    import csv
    import io
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def export_books_csv(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission.')
        return redirect('book_list')
    books = Book.objects.select_related('author', 'category', 'publisher')
    header = ['Title', 'ISBN', 'Author', 'Category', 'Publisher', 'Total Copies', 'Available', 'Shelf', 'Published', 'Borrowed']
    rows = [[
        b.title, b.isbn, b.author.name,
        b.category.name if b.category else '',
        b.publisher.name if b.publisher else '',
        b.total_copies, b.available_copies, b.shelf_location,
        b.publication_date.isoformat() if b.publication_date else '',
        b.borrow_count,
    ] for b in books]
    return _export_csv_response('books.csv', header, rows)


@login_required
def export_members_csv(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission.')
        return redirect('member_list')
    from django.contrib.auth.models import User
    profiles = User.objects.select_related('member_profile').filter(is_active=True)
    header = ['Member ID', 'Username', 'Name', 'Email', 'Department', 'Phone', 'Joined']
    rows = []
    for u in profiles:
        p = u.member_profile
        rows.append([p.member_id, u.username, u.get_full_name(), u.email, p.department, p.phone, p.membership_date.isoformat()])
    return _export_csv_response('members.csv', header, rows)


@login_required
def export_history_csv(request):
    records = BorrowRecord.objects.select_related('member', 'book', 'book__author')
    if not (request.user.is_staff or request.user.is_superuser):
        records = records.filter(member=request.user)
    header = ['Book', 'Member', 'Issue Date', 'Due Date', 'Return Date', 'Status', 'Fine']
    rows = [[
        r.book.title, r.member.get_full_name() or r.member.username,
        r.issue_date.isoformat(), r.due_date.isoformat(),
        r.return_date.isoformat() if r.return_date else '',
        r.get_status_display(), r.fine_amount,
    ] for r in records]
    return _export_csv_response('borrowing_history.csv', header, rows)
