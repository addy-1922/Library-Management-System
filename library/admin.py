from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Book, Author, Category, Publisher, BorrowRecord,
    BookReview, BookReservation, WishlistItem,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'book_count']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'nationality', 'book_count']
    search_fields = ['name', 'nationality']
    list_filter = ['nationality']
    ordering = ['name']


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone']
    search_fields = ['name', 'email']
    ordering = ['name']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'isbn', 'author', 'category', 'publisher', 'total_copies', 'available_copies', 'availability_status']
    list_filter = ['category', 'author', 'publication_date']
    search_fields = ['title', 'isbn', 'author__name', 'category__name']
    list_editable = ['available_copies', 'total_copies']
    autocomplete_fields = ['author', 'category', 'publisher']
    readonly_fields = ['created_at', 'updated_at', 'borrow_count']
    ordering = ['title']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'isbn', 'description', 'cover_image')
        }),
        ('Relationships', {
            'fields': ('author', 'category', 'publisher')
        }),
        ('Publication', {
            'fields': ('publication_date', 'shelf_location')
        }),
        ('Inventory', {
            'fields': ('total_copies', 'available_copies', 'borrow_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def availability_status(self, obj):
        colors = {
            'available': 'green',
            'limited': 'orange',
            'unavailable': 'red',
        }
        color = colors.get(obj.availability_status, 'gray')
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            color, obj.availability_label
        )
    availability_status.short_description = 'Status'


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ['member', 'book', 'issue_date', 'due_date', 'return_date', 'status', 'fine_amount']
    list_filter = ['status', 'issue_date', 'due_date']
    search_fields = ['member__username', 'member__first_name', 'member__last_name', 'book__title', 'book__isbn']
    autocomplete_fields = ['member', 'book', 'issued_by', 'returned_to']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    list_select_related = ['member', 'book', 'book__author']


@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['book__title', 'user__username']
    autocomplete_fields = ['book', 'user']
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['book', 'user']


@admin.register(BookReservation)
class BookReservationAdmin(admin.ModelAdmin):
    list_display = ['book', 'member', 'status', 'position', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['book__title', 'member__username']
    autocomplete_fields = ['book', 'member']
    readonly_fields = ['created_at']
    ordering = ['position']
    list_select_related = ['book', 'member']


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'created_at']
    search_fields = ['user__username', 'book__title']
    autocomplete_fields = ['user', 'book']
    readonly_fields = ['created_at']
    list_select_related = ['user', 'book']
