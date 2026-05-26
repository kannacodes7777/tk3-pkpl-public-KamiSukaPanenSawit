import re

from django.core.exceptions import ValidationError
from django.utils.html import escape

LOCATION_ALLOWED = re.compile(r"^[A-Za-z0-9\s.,\-'/()<>=\"\]\[:;!?{}%*_]+$")
REVIEW_ALLOWED = re.compile(r"^[A-Za-z0-9\s.,;:!?\-'/()\n{}%*_<>=\"\[\]]+$")
USERNAME_ALLOWED = re.compile(r"^[A-Za-z0-9._-]+$")

class InjectionPatterns:    
    SCRIPT_TAG = re.compile(r'<\s*script[^>]*>.*?</\s*script\s*>', re.IGNORECASE | re.DOTALL)
    EVENT_HANDLER = re.compile(r'on\w+\s*=', re.IGNORECASE)
    
    DANGEROUS_TAGS = re.compile(
        r'<\s*(iframe|object|embed|applet|form|input|button|'
        r'img[^>]*(?:onerror|src\s*=\s*["\']?(?:javascript|data))|'
        r'svg|math)\b',
        re.IGNORECASE
    )
    
    TEMPLATE_EXPR = re.compile(r'[{][{%].*?[}][}%]', re.DOTALL)
    TEMPLATE_VAR = re.compile(r'[{][{].*?[}][}]', re.DOTALL)
    
    SQL_INJECTION = re.compile(
        r"('|(\")|(--)|(;)|(\/\*))",
        re.IGNORECASE
    )

def sanitize_input(value, allow_basic_html=False):
    if not value:
        return value
    
    value = str(value).strip()
    
    value = value.replace('{{', '&#123;&#123;').replace('}}', '&#125;&#125;')
    value = value.replace('{%', '&#123;%').replace('%}', '%&#125;')
    
    value = escape(value)
    
    return value

def sanitize_review_text(value):
    if not value:
        return value

    value = str(value).strip()
    
    return escape(value)


def validate_no_injection(value):
    if not value:
        return
    value = str(value)

    if InjectionPatterns.SQL_INJECTION.search(value):
        raise ValidationError(
            "Input terdeteksi mengandung karakter SQL Injection berbahaya.",
            code='sql_injection_detected'
        )

    numeric_bypass_pattern = re.compile(r"\b(UNION|SELECT|DROP|DELETE|UPDATE|OR\s+\d+\s*=\s*\d+)\b", re.IGNORECASE)
    if numeric_bypass_pattern.search(value):
        raise ValidationError(
            "Input terdeteksi mengandung kata kunci atau logika bypass SQL Injection.",
            code='sql_logic_bypass_detected'
        )


def validate_safe_text(value):
    if not value:
        return
    
    safe_pattern = re.compile(r"^[a-zA-Z0-9\s.,\-'?!ñÑáéíóúÁÉÍÓÚ]+$")
    
    if not safe_pattern.match(str(value)):
        raise ValidationError(
            "Input hanya boleh berisi huruf, angka, dan tanda baca dasar.",
            code='unsafe_characters'
        )


def validate_allowlist(value, pattern, message):
    if not value:
        return

    if not pattern.fullmatch(str(value)):
        raise ValidationError(message, code='allowlist_violation')


def validate_location_allowlist(value):
    validate_allowlist(
        value,
        LOCATION_ALLOWED,
        "Input lokasi hanya boleh berisi huruf, angka, spasi, dan tanda baca dasar."
    )


def validate_review_allowlist(value):
    validate_allowlist(
        value,
        REVIEW_ALLOWED,
        "Input ulasan hanya boleh berisi huruf, angka, spasi, dan tanda baca dasar."
    )


def validate_username_allowlist(value):
    validate_allowlist(
        value,
        USERNAME_ALLOWED,
        "Username hanya boleh berisi huruf, angka, titik, underscore, atau strip."
    )
