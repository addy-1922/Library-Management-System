from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from library.models import Book, BorrowRecord
from library.services import calculate_fine


class Command(BaseCommand):
    help = 'Seed borrowing records spread across the last 6 months for chart data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--records', type=int, default=30,
            help='Total number of records to spread across months (default: 30)',
        )

    def handle(self, *args, **options):
        total = options['records']
        members = list(User.objects.filter(is_staff=False, is_superuser=False).select_related('member_profile'))
        books = list(Book.objects.filter(available_copies__gt=0))
        if not members or not books:
            self.stdout.write(self.style.ERROR('Need both members and books. Run seed_library first.'))
            return

        librarian = User.objects.filter(is_staff=True).first()
        today = timezone.now().date()
        created = 0

        months = list(range(1, 7))
        records_per_month = total // 6
        remainder = total % 6

        for month_offset, month in enumerate(months):
            count = records_per_month + (1 if month_offset < remainder else 0)
            month_start = today - timedelta(days=30 * (6 - month))
            month_end = today - timedelta(days=30 * (5 - month)) if month < 6 else today

            for _ in range(count):
                member = random.choice(members)
                book = random.choice(books)
                if book.available_copies < 1:
                    continue

                day_offset = random.randint(0, 29)
                issue_date = month_start + timedelta(days=day_offset)
                if issue_date > today:
                    issue_date = today - timedelta(days=random.randint(0, 5))

                period = random.choice([7, 14, 14, 14, 21])
                due_date = issue_date + timedelta(days=period)

                is_returned = random.random() < 0.6 and due_date < today
                if is_returned:
                    return_offset = random.randint(1, min(period + 10, (today - issue_date).days))
                    return_date = issue_date + timedelta(days=return_offset)
                    fine = calculate_fine(due_date, return_date) if return_date > due_date else 0
                    BorrowRecord.objects.create(
                        member=member, book=book,
                        issue_date=issue_date, due_date=due_date,
                        return_date=return_date,
                        status='returned', fine_amount=fine,
                        issued_by=librarian, returned_to=librarian,
                    )
                else:
                    BorrowRecord.objects.create(
                        member=member, book=book,
                        issue_date=issue_date, due_date=due_date,
                        status='issued' if due_date >= today else 'overdue',
                        issued_by=librarian,
                    )
                book.borrow_count += 1
                book.save(update_fields=['borrow_count'])
                created += 1

        total_records = BorrowRecord.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'Done! Created {created} historical records. Total borrowing records: {total_records}'
        ))
