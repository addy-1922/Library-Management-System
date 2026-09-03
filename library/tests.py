from django.test import TestCase
from django.contrib.auth.models import User
from library.models import (
    Book, Author, Category, Publisher, BorrowRecord,
    BookReview, BookReservation, WishlistItem,
)
from library.services import (
    issue_book, return_book, calculate_fine, can_issue_book,
    create_reservation, toggle_wishlist, save_review, get_chart_data,
)
from accounts.models import MemberProfile
from django.utils import timezone
from datetime import timedelta, date


class BaseTestSetup(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Fiction', description='Fiction works')
        self.author = Author.objects.create(name='Test Author', nationality='American')
        self.publisher = Publisher.objects.create(name='Test Publisher', email='pub@test.com')
        self.book = Book.objects.create(
            title='Test Book', isbn='9781234567897', author=self.author,
            category=self.category, publisher=self.publisher,
            total_copies=3, available_copies=3, shelf_location='A-1',
        )
        self.member = User.objects.create_user(
            username='member', password='pass12345', first_name='Test', last_name='Member'
        )
        self.profile = self.member.member_profile
        self.librarian = User.objects.create_user(
            username='librarian', password='pass12345', first_name='Lib'
        )


class AuthenticationTests(BaseTestSetup):
    def test_login_required_for_dashboard(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)

    def test_user_can_login(self):
        self.client.login(username='member', password='pass12345')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_member_can_access_self_service_issue(self):
        self.client.login(username='member', password='pass12345')
        response = self.client.get('/issue/')
        self.assertEqual(response.status_code, 200)

    def test_member_cannot_access_reports(self):
        self.client.login(username='member', password='pass12345')
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 302)

    def test_member_cannot_access_member_management(self):
        self.client.login(username='member', password='pass12345')
        response = self.client.get('/accounts/members/')
        self.assertEqual(response.status_code, 302)


class BookModelTests(BaseTestSetup):
    def test_book_creation(self):
        self.assertEqual(Book.objects.count(), 1)
        self.assertEqual(self.book.available_copies, 3)

    def test_availability_status(self):
        self.assertEqual(self.book.availability_status, 'available')
        self.book.available_copies = 0
        self.assertEqual(self.book.availability_status, 'unavailable')
        self.book.available_copies = 2
        self.book.total_copies = 3
        self.assertEqual(self.book.availability_status, 'limited')

    def test_is_available(self):
        self.assertTrue(self.book.is_available())
        self.book.available_copies = 0
        self.assertFalse(self.book.is_available())


class BookIssueTests(BaseTestSetup):
    def test_successful_issue_decreases_copies(self):
        record, errors = issue_book(self.member, self.book, issued_by=self.librarian)
        self.assertIsNotNone(record)
        self.assertEqual(errors, [])
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 2)

    def test_cannot_issue_when_unavailable(self):
        self.book.available_copies = 0
        self.book.save()
        record, errors = issue_book(self.member, self.book, issued_by=self.librarian)
        self.assertIsNone(record)
        self.assertTrue(any('unavailable' in e for e in errors))

    def test_cannot_issue_same_book_twice(self):
        issue_book(self.member, self.book)
        record, errors = issue_book(self.member, self.book)
        self.assertIsNone(record)
        self.assertTrue(any('already has' in e for e in errors))

    def test_borrowing_limit(self):
        from django.conf import settings
        limit = getattr(settings, 'LIBRARY_MAX_BORROW_LIMIT', 5)
        books = []
        for i in range(limit):
            b = Book.objects.create(
                title=f'Book {i}', isbn=f'97801000000{i:03d}',
                author=self.author, category=self.category,
                available_copies=1, total_copies=1,
            )
            books.append(b)
            issue_book(self.member, b)
        extra_book = Book.objects.create(
            title='Extra', isbn='9780199999999', author=self.author,
            category=self.category, available_copies=1, total_copies=1,
        )
        record, errors = issue_book(self.member, extra_book)
        self.assertIsNone(record)
        self.assertTrue(any('limit' in e for e in errors))

    def test_inactive_member_cannot_issue(self):
        self.profile.is_active_member = False
        self.profile.save()
        record, errors = issue_book(self.member, self.book)
        self.assertIsNone(record)
        self.assertTrue(any('inactive' in e for e in errors))


class BookReturnTests(BaseTestSetup):
    def test_successful_return_increases_copies(self):
        record, _ = issue_book(self.member, self.book)
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 2)
        record, error = return_book(record, returned_by=self.librarian)
        self.assertIsNone(error)
        self.assertEqual(record.status, 'returned')
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 3)

    def test_cannot_return_twice(self):
        record, _ = issue_book(self.member, self.book)
        return_book(record)
        record2, error = return_book(record)
        self.assertIsNotNone(error)


class FineCalculationTests(BaseTestSetup):
    def test_no_fine_when_on_time(self):
        self.assertEqual(calculate_fine(date(2024, 1, 10), date(2024, 1, 5)), 0)

    def test_fine_within_free_days(self):
        self.assertEqual(calculate_fine(date(2024, 1, 10), date(2024, 1, 15)), 25)

    def test_fine_after_free_days(self):
        self.assertEqual(calculate_fine(date(2024, 1, 10), date(2024, 1, 20)), 65)

    def test_due_date_calculation_on_issue(self):
        record, _ = issue_book(self.member, self.book)
        from django.conf import settings
        period = getattr(settings, 'LIBRARY_BORROW_PERIOD_DAYS', 14)
        self.assertEqual(record.due_date, record.issue_date + timedelta(days=period))

    def test_fine_amount_saved_on_return(self):
        record, _ = issue_book(self.member, self.book)
        record.due_date = record.issue_date - timedelta(days=10)
        record.save()
        returned, _ = return_book(record, returned_by=self.librarian)
        self.assertGreater(returned.fine_amount, 0)


class TransactionTests(BaseTestSetup):
    def test_issue_reduces_available_and_increments_borrow_count(self):
        before = self.book.borrow_count
        record, _ = issue_book(self.member, self.book)
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 2)
        self.assertEqual(self.book.borrow_count, before + 1)


class ReviewTests(BaseTestSetup):
    def test_save_review_creates_and_updates(self):
        review, created = save_review(self.member, self.book, 5, 'Great!')
        self.assertTrue(created)
        review, created = save_review(self.member, self.book, 3, 'Updated')
        self.assertFalse(created)
        self.assertEqual(BookReview.objects.filter(book=self.book, user=self.member).count(), 1)

    def test_average_rating_property(self):
        save_review(self.member, self.book, 4, 'Nice')
        other = User.objects.create_user(username='member2', password='pass12345')
        save_review(other, self.book, 2, 'Meh')
        self.book.refresh_from_db()
        self.assertEqual(self.book.average_rating, 3.0)
        self.assertEqual(self.book.rating_count, 2)

    def test_review_view_requires_login(self):
        self.client.login(username='member', password='pass12345')
        response = self.client.post(f'/books/{self.book.pk}/review/', {'rating': 5, 'comment': 'Loved it'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BookReview.objects.filter(book=self.book, user=self.member).exists())


class ReservationTests(BaseTestSetup):
    def test_reservation_requires_unavailable_book(self):
        self.book.available_copies = 0
        self.book.save()
        reservation, errors = create_reservation(self.member, self.book)
        self.assertIsNotNone(reservation)
        self.assertEqual(errors, [])

    def test_reservation_rejected_when_available(self):
        reservation, errors = create_reservation(self.member, self.book)
        self.assertIsNone(reservation)
        self.assertTrue(errors)

    def test_reservation_position_increments(self):
        self.book.available_copies = 0
        self.book.save()
        r1, _ = create_reservation(self.member, self.book)
        other = User.objects.create_user(username='res2', password='pass12345')
        other.member_profile.is_active_member = True
        other.member_profile.save()
        r2, _ = create_reservation(other, self.book)
        self.assertEqual(r1.position, 1)
        self.assertEqual(r2.position, 2)


class WishlistTests(BaseTestSetup):
    def test_toggle_adds_and_removes(self):
        self.assertEqual(toggle_wishlist(self.member, self.book), 'added')
        self.assertTrue(WishlistItem.objects.filter(user=self.member, book=self.book).exists())
        self.assertEqual(toggle_wishlist(self.member, self.book), 'removed')
        self.assertFalse(WishlistItem.objects.filter(user=self.member, book=self.book).exists())


class ChartDataTests(BaseTestSetup):
    def test_chart_data_shape(self):
        data = get_chart_data()
        self.assertIn('monthly_labels', data)
        self.assertIn('monthly_data', data)
        self.assertEqual(len(data['monthly_labels']), 6)
        self.assertEqual(len(data['monthly_data']), 6)


class ExportTests(BaseTestSetup):
    def test_member_cannot_export_books(self):
        self.client.login(username='member', password='pass12345')
        response = self.client.get('/export/books/')
        self.assertEqual(response.status_code, 302)

    def test_librarian_can_export_books(self):
        self.librarian.is_staff = True
        self.librarian.save()
        self.client.login(username='librarian', password='pass12345')
        response = self.client.get('/export/books/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_member_can_export_own_history(self):
        self.client.login(username='member', password='pass12345')
        response = self.client.get('/export/history/')
        self.assertEqual(response.status_code, 200)
