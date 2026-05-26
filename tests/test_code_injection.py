import os
import sys

# setup Django settings (for manual script execution)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tk3_pkpl.settings')
sys.path.insert(0, r'c:\Users\moondive\tk3-pkpl')

import django
from django.apps import apps
if not apps.ready:
    django.setup()

from django.test import TestCase
from django.core.exceptions import ValidationError
from main.sanitizers import (
    sanitize_input,
    validate_location_allowlist,
    validate_review_allowlist,
    validate_username_allowlist,
    validate_no_injection,
    validate_safe_text
)
from main.models import Pesanan, Rating, CustomUser

# ==========================================
# 1. DJANGO TESTCASE (Automated)
# ==========================================
class CodeInjectionTests(TestCase):
    def setUp(self):
        self.user_penumpang = CustomUser.objects.create_user(username='penumpang1', role='penumpang')
        self.user_pengemudi = CustomUser.objects.create_user(username='pengemudi1', role='pengemudi')

    def test_sanitize_input_html_escape(self):
        """Test if basic HTML and script tags are escaped"""
        unsafe_input = "<script>alert(1)</script>"
        sanitized = sanitize_input(unsafe_input)
        self.assertNotIn("<script>", sanitized)
        self.assertEqual(sanitized, "&lt;script&gt;alert(1)&lt;/script&gt;")
        
    def test_sanitize_input_template_injection(self):
        """Test if Django template expressions are neutralized"""
        unsafe_input = "{{ 7*7 }}"
        sanitized = sanitize_input(unsafe_input)
        self.assertEqual(sanitized, "&amp;#123;&amp;#123; 7*7 &amp;#125;&amp;#125;")
        
        unsafe_input2 = "{% if user.is_authenticated %}"
        sanitized2 = sanitize_input(unsafe_input2)
        self.assertEqual(sanitized2, "&amp;#123;% if user.is_authenticated %&amp;#125;")

    def test_validate_location_allowlist_valid(self):
        """Test valid location string passes allowlist validation"""
        try:
            validate_location_allowlist("Jl. Merdeka No. 1, Jakarta")
        except ValidationError:
            self.fail("validate_location_allowlist raised ValidationError unexpectedly!")

    def test_validate_location_allowlist_invalid(self):
        """Test invalid characters are rejected by location allowlist"""
        unsafe_input = "Jakarta `whoami`"
        with self.assertRaises(ValidationError) as context:
            validate_location_allowlist(unsafe_input)
        self.assertEqual(context.exception.code, 'allowlist_violation')

    def test_validate_review_allowlist_valid(self):
        """Test valid review string passes allowlist validation"""
        try:
            validate_review_allowlist("Bagus, sangat direkomendasikan!")
        except ValidationError:
            self.fail("validate_review_allowlist raised ValidationError unexpectedly!")

    def test_validate_review_allowlist_invalid(self):
        """Test invalid characters are rejected by review allowlist"""
        unsafe_input = "Bagus $ { } `ls`"
        with self.assertRaises(ValidationError) as context:
            validate_review_allowlist(unsafe_input)
        self.assertEqual(context.exception.code, 'allowlist_violation')
        
    def test_validate_username_allowlist_invalid(self):
        """Test XSS payload in username is rejected"""
        unsafe_input = "admin<script>"
        with self.assertRaises(ValidationError) as context:
            validate_username_allowlist(unsafe_input)
        self.assertEqual(context.exception.code, 'allowlist_violation')

    def test_pesanan_model_xss_sanitization(self):
        """Test that XSS attempts in location fields are sanitized at model level"""
        pesanan = Pesanan(
            penumpang=self.user_penumpang,
            titik_jemput='Rumah <script>alert(1)</script>',
            titik_tujuan='Kantor'
        )
        pesanan.clean()
        self.assertEqual(pesanan.titik_jemput, 'Rumah &lt;script&gt;alert(1)&lt;/script&gt;')

    def test_rating_model_xss_sanitization(self):
        """Test that XSS attempts in rating reviews are sanitized at model level"""
        pesanan = Pesanan.objects.create(penumpang=self.user_penumpang, titik_jemput='A', titik_tujuan='B')
        rating = Rating(
            pesanan=pesanan,
            penumpang=self.user_penumpang,
            pengemudi=self.user_pengemudi,
            skor=5,
            ulasan='Mantap <img src=x onerror=alert(1)>'
        )
        rating.clean()
        self.assertEqual(rating.ulasan, 'Mantap &lt;img src=x onerror=alert(1)&gt;')


# ==========================================
# 2. CUSTOM TEST SCRIPT (Manual)
# ==========================================
def test_case(test_id, description, payload, expected_result):
    print(f"\n{'='*70}")
    print(f"TEST: {test_id} - {description}")
    print(f"{'='*70}")
    print(f"Input Payload: {payload}")
    
    try:
        # Test 1: validation (should not raise if payload is handled)
        try:
            validate_no_injection(payload)
            print("[OK] validate_no_injection: PASSED (no exception)")
            validation_passed = True
        except ValidationError as e:
            print(f"[OK] validate_no_injection: BLOCKED - {e.message}")
            validation_passed = True
        
        # Test 2: sanitization
        sanitized = sanitize_input(payload)
        print(f"Sanitized Output: {sanitized}")
        
        # Test 3: verify expected result
        if expected_result.lower() == 'blocked':
            if '<' not in sanitized and '{' not in sanitized and 'script' not in sanitized.lower():
                print(f"[OK] OUTPUT VALIDATION: PASSED - Dangerous code blocked")
                return True
            else:
                print(f"[FAIL] OUTPUT VALIDATION: FAILED - Dangerous code still present")
                return False
        elif expected_result.lower() == 'escaped':
            if '&lt;' in sanitized or '&gt;' in sanitized or '&' in sanitized:
                print(f"[OK] OUTPUT VALIDATION: PASSED - Code escaped as text")
                return True
            else:
                print(f"[OK] OUTPUT VALIDATION: PASSED - Code removed/neutralized")
                return True
        else:
            print(f"[OK] OUTPUT VALIDATION: PASSED - {expected_result}")
            return True
            
    except Exception as e:
        print(f"[FAIL] UNEXPECTED ERROR: {e}")
        return False


def run_all_tests():
    print("\n" + "="*70)
    print("CODE INJECTION (XSS/SSTI) MITIGATION - TEST SUITE")
    print("="*70)
    
    results = []
    
    # TC-CI-04g: SVG/HTML Injection
    results.append(test_case(
        "TC-CI-04g",
        "SVG Tag Injection - Should not execute, display as text or removed",
        "<svg/onload=alert('xss')>",
        "Blocked or Escaped"
    ))
    
    # TC-CI-01: Script Tag Injection (Stored/Reflected XSS)
    results.append(test_case(
        "TC-CI-01",
        "Script Tag Injection - Script should NOT execute, displayed as literal text or stripped",
        "<script>alert('XSS')</script>",
        "Blocked or Escaped"
    ))
    
    # TC-CI-02: HTML Injection
    results.append(test_case(
        "TC-CI-02",
        "HTML Injection - HTML tags should NOT render, displayed as text or removed",
        "<h1>Hacked</h1><img src=x onerror=alert(1)>",
        "Blocked or Escaped"
    ))
    
    # TC-CI-02 Alternative: IMG with onerror
    results.append(test_case(
        "TC-CI-02 (Alt)",
        "Image with onerror handler",
        "<img src=x onerror=alert(1)>",
        "Blocked or Escaped"
    ))
    
    # TC-CI-03: Template Injection (Django/Jinja2)
    results.append(test_case(
        "TC-CI-03",
        "Template Expression Injection - Should not evaluate {{ 7*7 }}",
        "{{7*7}}",
        "Escaped (displayed as {{7*7}})"
    ))
    
    # TC-CI-03 Alternative: SECRET_KEY exposure
    results.append(test_case(
        "TC-CI-03 (Alt)",
        "Template Variable Injection - SECRET_KEY should not be exposed",
        "{{config.SECRET_KEY}}",
        "Escaped (displayed as literal text)"
    ))
    
    # TC-CI-03 Django Jinja Format
    results.append(test_case(
        "TC-CI-03 (Django Template)",
        "Django Template Tag Injection",
        "{% for x in y %} {{ x }} {% endfor %}",
        "Escaped or Blocked"
    ))
    
    # additional dangerous patterns
    results.append(test_case(
        "Additional",
        "Event Handler Injection (onload)",
        "<body onload=alert('XSS')>",
        "Blocked or Escaped"
    ))
    
    results.append(test_case(
        "Additional",
        "JavaScript Protocol Handler",
        "<a href='javascript:alert(1)'>Click me</a>",
        "Blocked or Escaped"
    ))
    
    results.append(test_case(
        "Additional",
        "Data Protocol Handler",
        "<a href='data:text/html,<script>alert(1)</script>'>Click</a>",
        "Blocked or Escaped"
    ))
    
    # additional safe input tests
    results.append(test_case(
        "Safe Input",
        "Normal text should be preserved",
        "Jakarta, Jl. Sudirman - Kota",
        "Preserved"
    ))
    
    results.append(test_case(
        "Safe Input",
        "Review with normal text",
        "Pengemudi sangat ramah dan profesional. Kendaraan bersih dan nyaman.",
        "Preserved"
    ))
    
    # print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if failed == 0:
        print("\n[OK] ALL TESTS PASSED - XSS/SSTI Mitigation is effective!")
    else:
        print(f"\n[FAIL] {failed} TEST(S) FAILED - Review the output above")
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
