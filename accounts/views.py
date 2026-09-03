from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import MemberRegistrationForm, MemberEditForm, MemberProfileForm
from .models import MemberProfile
from library.models import BorrowRecord


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully. Welcome!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MemberRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile_view(request):
    profile, _ = MemberProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = MemberEditForm(request.POST, instance=request.user)
        profile_form = MemberProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        user_form = MemberEditForm(instance=request.user)
        profile_form = MemberProfileForm(instance=profile)
    borrow_records = BorrowRecord.objects.filter(
        member=request.user
    ).select_related('book', 'book__author')[:10]
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
        'borrow_records': borrow_records,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def member_list_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to view members.')
        return redirect('dashboard')
    query = request.GET.get('q', '')
    members = MemberProfile.objects.select_related('user').order_by('-membership_date')
    if query:
        members = members.filter(
            user__first_name__icontains=query
        ) | members.filter(
            user__last_name__icontains=query
        ) | members.filter(
            member_id__icontains=query
        ) | members.filter(
            user__username__icontains=query
        )
    from django.core.paginator import Paginator
    paginator = Paginator(members, 15)
    page = request.GET.get('page', 1)
    members_page = paginator.get_page(page)
    return render(request, 'accounts/member_list.html', {
        'members': members_page,
        'query': query,
    })


@login_required
def member_detail_view(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        if request.user.pk != pk:
            messages.error(request, 'You do not have permission to view this member.')
            return redirect('dashboard')
    user_obj = get_object_or_404(User, pk=pk)
    profile, _ = MemberProfile.objects.get_or_create(user=user_obj)
    active_records = BorrowRecord.objects.filter(
        member=user_obj, status='issued'
    ).select_related('book', 'book__author')
    history = BorrowRecord.objects.filter(
        member=user_obj
    ).exclude(status='issued').select_related('book', 'book__author').order_by('-return_date')[:20]
    return render(request, 'accounts/member_detail.html', {
        'member_user': user_obj,
        'profile': profile,
        'active_records': active_records,
        'history': history,
    })


@login_required
def member_edit_view(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission.')
        return redirect('dashboard')
    user_obj = get_object_or_404(User, pk=pk)
    profile, _ = MemberProfile.objects.get_or_create(user=user_obj)
    if request.method == 'POST':
        user_form = MemberEditForm(request.POST, instance=user_obj)
        profile_form = MemberProfileForm(request.POST, request.FILES, instance=profile)
        is_active = request.POST.get('is_active_member')
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            if is_active is not None:
                profile.is_active_member = is_active == 'on'
                profile.save(update_fields=['is_active_member'])
            messages.success(request, 'Member updated successfully.')
            return redirect('member_detail', pk=user_obj.pk)
    else:
        user_form = MemberEditForm(instance=user_obj)
        profile_form = MemberProfileForm(instance=profile)
    return render(request, 'accounts/member_edit.html', {
        'member_user': user_obj,
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    })


@login_required
def change_password_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Password changed successfully. Please log in again.')
            return redirect('login')
    return render(request, 'accounts/change_password.html')
