from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<int:pk>/', views.member_detail_view, name='member_detail'),
    path('members/', views.member_list_view, name='member_list'),
    path('members/<int:pk>/edit/', views.member_edit_view, name='member_edit'),
    path('change-password/', views.change_password_view, name='change_password'),
]
