from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class MemberProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    member_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    address = models.TextField(blank=True)
    membership_date = models.DateField(auto_now_add=True)
    is_active_member = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Member Profile'
        verbose_name_plural = 'Member Profiles'

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.member_id})"

    @property
    def active_borrows(self):
        return self.user.borrow_records.filter(status='issued').count()

    @property
    def total_borrows(self):
        return self.user.borrow_records.exclude(status='returned').count()

    @property
    def total_fines(self):
        from django.db.models import Sum
        total = self.user.borrow_records.aggregate(total=Sum('fine_amount'))['total']
        return total or 0

    @property
    def unpaid_fines(self):
        from django.db.models import Sum
        total = self.user.borrow_records.filter(
            fine_amount__gt=0
        ).exclude(status='returned').aggregate(total=Sum('fine_amount'))['total']
        return total or 0


@receiver(post_save, sender=User)
def create_member_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'member_profile'):
        last_profile = MemberProfile.objects.order_by('-id').first()
        if last_profile:
            try:
                last_num = int(last_profile.member_id.replace('LIB', ''))
                new_num = last_num + 1
            except (ValueError, AttributeError):
                new_num = MemberProfile.objects.count() + 1
        else:
            new_num = 1
        MemberProfile.objects.create(
            user=instance,
            member_id=f'LIB{new_num:04d}',
        )
