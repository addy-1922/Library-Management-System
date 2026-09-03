from django.core.management.base import BaseCommand
from django.utils import timezone
from library.services import update_overdue_records


class Command(BaseCommand):
    help = 'Mark overdue borrow records and send fine notifications (if email configured).'

    def handle(self, *args, **options):
        count = update_overdue_records()
        self.stdout.write(self.style.SUCCESS(f'Processed overdue records: {count} marked overdue.'))
