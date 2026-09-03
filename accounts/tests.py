from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import MemberProfile


class MemberProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='pass12345',
            first_name='Test', last_name='User',
        )

    def test_profile_auto_created(self):
        self.assertTrue(hasattr(self.user, 'member_profile'))
        self.assertIsNotNone(self.user.member_profile.member_id)

    def test_member_id_unique(self):
        user2 = User.objects.create_user(
            username='testuser2', password='pass12345',
            first_name='Test2', last_name='User2',
        )
        self.assertNotEqual(
            self.user.member_profile.member_id,
            user2.member_profile.member_id,
        )

    def test_register_view(self):
        response = self.client.post('/accounts/register/', {
            'username': 'newuser',
            'email': 'new@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'supersecret123',
            'password2': 'supersecret123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
