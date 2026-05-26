import os
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.conf import settings
from main.models import CustomUser, Pesanan

class SQLInjectionTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='penumpang_sqli', password='Password123!', role='penumpang')

    def test_tc_sqli_01(self):
        pesanan = Pesanan(
            penumpang=self.user,
            titik_jemput="Kampus",
            titik_tujuan="'OR'1 ='1 --"
        )
        with self.assertRaises(ValidationError):
            pesanan.full_clean()

    def test_tc_sqli_02(self):
        pesanan = Pesanan(
            penumpang=self.user,
            titik_jemput="' UNION SELECT username, password, null FROM users --",
            titik_tujuan="Kampus"
        )
        with self.assertRaises(ValidationError):
            pesanan.full_clean()

    def test_tc_sqli_03(self):
        app_dir = os.path.join(settings.BASE_DIR, 'main')
        files_to_check = ['views.py', 'models.py']

        for file_name in files_to_check:
            file_path = os.path.join(app_dir, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.assertNotIn('.raw(', content, f"Ditemukan penggunaan .raw() pada file {file_name}")
                    self.assertNotIn('cursor.execute(', content, f"Ditemukan penggunaan cursor.execute() pada file {file_name}")

    def test_tc_sqli_04g(self):
        pesanan = Pesanan(
            penumpang=self.user,
            titik_jemput="5 OR 1=1",
            titik_tujuan="Kampus"
        )
        with self.assertRaises(ValidationError):
            pesanan.full_clean()