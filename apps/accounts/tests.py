from django.test import TestCase
from django.urls import reverse

from .models import AccessLink, User, UserRole


class AccessLinkFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="StrongPass123",
            phone_number="+998901234567",
            full_name="Test User",
            role=UserRole.USER,
        )

    def test_access_link_redirects_to_panel(self):
        access_link = AccessLink.objects.create(
            user=self.user,
            token="abc123",
            target_path="/panel/",
            expires_at=AccessLink.default_expiry(),
        )
        response = self.client.get(reverse("accounts:access_with_token", args=[access_link.token]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/panel/")

    def test_access_link_exchange_returns_redirect_url(self):
        access_link = AccessLink.objects.create(
            user=self.user,
            token="bridge123",
            target_path="/panel/finance/",
            expires_at=AccessLink.default_expiry(),
        )
        response = self.client.post(
            reverse("accounts:access_link_exchange"),
            data='{"token":"bridge123"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redirect_url"], "/panel/finance/")

    def test_access_link_entry_is_no_store(self):
        response = self.client.get(reverse("dashboard:panel_access_open"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])

# Create your tests here.
