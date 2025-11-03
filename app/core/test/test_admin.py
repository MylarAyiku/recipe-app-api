"""
Test for the admin modification
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client


class AdminSiteTests(TestCase):
    """Tests for admin modifications"""

    def setUp(self):
        """Create user and client"""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123password',
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='test123password',
            name='Test User',
        )


    def test_user_listed(self):
        """Test that users are listed on user page"""
        url = reverse('admin:core_user_changelist')
        self.client.force_login(self.admin_user)

        res = self.client.get(url)

        self.assertContains(res, self.admin_user.name)
        self.assertContains(res, self.admin_user.email)

    def test_user_change_page(self):
        """Test that the user edit page works"""
        url = reverse('admin:core_user_change', args=[self.user.id])
        self.client.force_login(self.admin_user)

        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)