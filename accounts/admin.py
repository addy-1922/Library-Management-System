from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django import forms
from .models import MemberProfile


class MemberProfileInline(admin.StackedInline):
    model = MemberProfile
    can_delete = False
    verbose_name_plural = 'Member Profile'
    fields = ('member_id', 'phone', 'department', 'address', 'profile_image', 'membership_date', 'is_active_member')


class CustomUserAdmin(UserAdmin):
    inlines = (MemberProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ['member_id', 'user', 'department', 'phone', 'membership_date', 'is_active_member']
    search_fields = ['member_id', 'user__username', 'user__first_name', 'user__last_name', 'department']
    list_filter = ['is_active_member', 'department', 'membership_date']
    readonly_fields = ['member_id', 'membership_date']
    autocomplete_fields = ['user']
    ordering = ['-membership_date']
