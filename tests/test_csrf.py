from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import NoReverseMatch, reverse


class CSRFProtectionTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="csrf_test_user",
            password="TestPassword123",
            role="penumpang",
        )

        self.normal_client = Client()
        self.csrf_client = Client(enforce_csrf_checks=True)

    def get_url(self, url_name, fallback_path):
        try:
            return reverse(f"main:{url_name}")
        except NoReverseMatch:
            return fallback_path

    def test_csrf_middleware_is_enabled(self):
        self.assertIn(
            "django.middleware.csrf.CsrfViewMiddleware",
            settings.MIDDLEWARE,
        )

    def test_views_do_not_use_csrf_exempt(self):
        views_path = Path(settings.BASE_DIR) / "main" / "views.py"
        views_content = views_path.read_text()

        self.assertNotIn("@csrf_exempt", views_content)
        self.assertNotIn("csrf_exempt", views_content)

    def test_login_form_contains_csrf_token(self):
        url = self.get_url("login", "/login/")
        response = self.normal_client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_register_form_contains_csrf_token(self):
        url = self.get_url("register", "/register/")
        response = self.normal_client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_pesan_ojek_form_contains_csrf_token(self):
        url = self.get_url("pesan", "/pesan/")

        self.normal_client.login(
            username="csrf_test_user",
            password="TestPassword123",
        )

        response = self.normal_client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_login_post_without_csrf_token_is_rejected(self):
        url = self.get_url("login", "/login/")

        response = self.csrf_client.post(url, {
            "username": "csrf_test_user",
            "password": "TestPassword123",
        })

        self.assertEqual(response.status_code, 403)

    def test_register_post_without_csrf_token_is_rejected(self):
        url = self.get_url("register", "/register/")

        response = self.csrf_client.post(url, {
            "username": "attacker_user",
            "password1": "TestPassword123",
            "password2": "TestPassword123",
            "role": "penumpang",
        })

        self.assertEqual(response.status_code, 403)

    def test_pesan_ojek_post_without_csrf_token_is_rejected(self):
        url = self.get_url("pesan", "/pesan/")

        self.csrf_client.login(
            username="csrf_test_user",
            password="TestPassword123",
        )

        response = self.csrf_client.post(url, {
            "titik_jemput": "Depok",
            "titik_tujuan": "Jakarta",
        })

        self.assertEqual(response.status_code, 403)

    def test_login_post_with_valid_csrf_token_is_not_rejected_by_csrf(self):
        url = self.get_url("login", "/login/")

        self.csrf_client.get(url)
        csrf_token = self.csrf_client.cookies["csrftoken"].value

        response = self.csrf_client.post(url, {
            "username": "csrf_test_user",
            "password": "TestPassword123",
            "csrfmiddlewaretoken": csrf_token,
        })

        self.assertNotEqual(response.status_code, 403)