from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def book_count(self):
        return self.books.count()


class Author(models.Model):
    name = models.CharField(max_length=200)
    biography = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def book_count(self):
        return self.books.count()


class Publisher(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Publishers'

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=300)
    isbn = models.CharField(max_length=13, unique=True, verbose_name='ISBN')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    publication_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    shelf_location = models.CharField(max_length=50, blank=True)
    borrow_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} by {self.author.name}"

    @property
    def availability_status(self):
        if self.available_copies == 0:
            return 'unavailable'
        elif self.available_copies < self.total_copies:
            return 'limited'
        return 'available'

    @property
    def availability_label(self):
        status = self.availability_status
        return {
            'available': 'Available',
            'limited': 'Limited',
            'unavailable': 'Unavailable',
        }.get(status, 'Unknown')

    def is_available(self):
        return self.available_copies > 0

    @property
    def average_rating(self):
        ratings = self.reviews.exclude(rating=None)
        if not ratings.exists():
            return 0
        total = sum(r.rating for r in ratings)
        return round(total / ratings.count(), 1)

    @property
    def rating_count(self):
        return self.reviews.count()

    @property
    def active_reservations_count(self):
        return self.reservations.filter(status__in=['pending', 'ready']).count()

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.total_copies < 0:
            raise ValidationError('Total copies cannot be negative.')
        if self.available_copies < 0:
            raise ValidationError('Available copies cannot be negative.')
        if self.available_copies > self.total_copies:
            raise ValidationError('Available copies cannot exceed total copies.')


class BorrowRecord(models.Model):
    STATUS_CHOICES = [
        ('issued', 'Issued'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('lost', 'Lost'),
    ]

    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='borrow_records')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_records')
    issue_date = models.DateField()
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='issued')
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='issued_records'
    )
    returned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='returned_records'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.book.title} ({self.status})"

    @property
    def days_overdue(self):
        from django.utils import timezone
        if self.status in ('returned', 'lost'):
            return 0
        today = timezone.now().date()
        if today > self.due_date:
            return (today - self.due_date).days
        return 0

    @property
    def calculated_fine(self):
        days = self.days_overdue
        if days <= 0:
            return 0
        free_days = getattr(settings, 'LIBRARY_FINE_FREE_DAYS', 7)
        initial_rate = getattr(settings, 'LIBRARY_FINE_INITIAL_RATE', 5)
        late_rate = getattr(settings, 'LIBRARY_FINE_LATE_RATE', 10)
        if days <= free_days:
            return days * initial_rate
        return (free_days * initial_rate) + ((days - free_days) * late_rate)


class BookReview(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='book_reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('book', 'user')
        verbose_name = 'Book Review'
        verbose_name_plural = 'Book Reviews'

    def __str__(self):
        return f'{self.user.username} rated {self.book.title} {self.rating}★'


class BookReservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ready', 'Ready for pickup'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
    ]
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='book_reservations')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Book Reservation'
        verbose_name_plural = 'Book Reservations'

    def __str__(self):
        return f'{self.member.username} reserved {self.book.title} ({self.status})'


class WishlistItem(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='wishlisted_by')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('book', 'user')
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'

    def __str__(self):
        return f'{self.user.username} wishes {self.book.title}'
