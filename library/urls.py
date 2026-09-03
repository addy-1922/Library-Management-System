from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),

    path('books/', views.book_list_view, name='book_list'),
    path('books/add/', views.book_create_view, name='book_create'),
    path('books/<int:pk>/', views.book_detail_view, name='book_detail'),
    path('books/<int:pk>/edit/', views.book_edit_view, name='book_edit'),
    path('books/<int:pk>/delete/', views.book_delete_view, name='book_delete'),

    path('issue/', views.issue_book_view, name='issue_book'),
    path('return/', views.return_book_view, name='return_book'),
    path('return/<int:pk>/confirm/', views.return_book_confirm_view, name='return_book_confirm'),

    path('borrowing-history/', views.borrowing_history_view, name='borrowing_history'),

    path('authors/', views.author_list_view, name='author_list'),
    path('authors/add/', views.author_create_view, name='author_create'),
    path('authors/<int:pk>/', views.author_detail_view, name='author_detail'),
    path('authors/<int:pk>/edit/', views.author_edit_view, name='author_edit'),
    path('authors/<int:pk>/delete/', views.author_delete_view, name='author_delete'),

    path('categories/', views.category_list_view, name='category_list'),
    path('categories/add/', views.category_create_view, name='category_create'),
    path('categories/<int:pk>/', views.category_detail_view, name='category_detail'),
    path('categories/<int:pk>/edit/', views.category_edit_view, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete_view, name='category_delete'),

    path('publishers/', views.publisher_list_view, name='publisher_list'),
    path('publishers/add/', views.publisher_create_view, name='publisher_create'),
    path('publishers/<int:pk>/', views.publisher_detail_view, name='publisher_detail'),
    path('publishers/<int:pk>/edit/', views.publisher_edit_view, name='publisher_edit'),
    path('publishers/<int:pk>/delete/', views.publisher_delete_view, name='publisher_delete'),

    path('reports/', views.reports_view, name='reports'),

    path('books/<int:pk>/review/', views.review_book_view, name='review_book'),
    path('reviews/<int:pk>/delete/', views.delete_review_view, name='delete_review'),
    path('books/<int:pk>/reserve/', views.reserve_book_view, name='reserve_book'),
    path('reservations/<int:pk>/cancel/', views.cancel_reservation_view, name='cancel_reservation'),
    path('books/<int:pk>/wishlist/', views.toggle_wishlist_view, name='toggle_wishlist'),
    path('wishlist/', views.wishlist_view, name='wishlist'),

    path('export/books/', views.export_books_csv, name='export_books'),
    path('export/members/', views.export_members_csv, name='export_members'),
    path('export/history/', views.export_history_csv, name='export_history'),
]
