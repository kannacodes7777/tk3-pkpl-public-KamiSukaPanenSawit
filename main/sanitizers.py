import re

from django.core.exceptions import ValidationError
from django.utils.html import escape

LOCATION_ALLOWED = re.compile(r"^[A-Za-z0-9\s.,\-'/()]+$")
REVIEW_ALLOWED = re.compile(r"^[A-Za-z0-9\s.,;:!?\-'/()\n{}%]+$")
USERNAME_ALLOWED = re.compile(r"^[A-Za-z0-9._-]+$")

class InjectionPatterns:    
    # script tags + event handlers
    SCRIPT_TAG = re.compile(r'<\s*script[^>]*>.*?</\s*script\s*>', re.IGNORECASE | re.DOTALL)
    EVENT_HANDLER = re.compile(r'on\w+\s*=', re.IGNORECASE)
    
    # HTML tags
    DANGEROUS_TAGS = re.compile(
        r'<\s*(iframe|object|embed|applet|form|input|button|'
        r'img[^>]*(?:onerror|src\s*=\s*["\']?(?:javascript|data))|'
        r'svg|math)\b',
        re.IGNORECASE
    )
    
    # template injection patterns (Django/Jinja2)
    TEMPLATE_EXPR = re.compile(r'[{][{%].*?[}][}%]', re.DOTALL)
    TEMPLATE_VAR = re.compile(r'[{][{].*?[}][}]', re.DOTALL)
    
    # SQL injection patterns (defense in depth)
    SQL_INJECTION = re.compile(
        r"('|(\")|(--)|(;)|(\/\*))",
        re.IGNORECASE
    )

# removes dangerous patterns and HTML-escapes input for safe display
def sanitize_input(value, allow_basic_html=False):
    if not value:
        return value
    
    value = str(value).strip()
    
    # remove script tags
    value = InjectionPatterns.SCRIPT_TAG.sub('', value)
    
    # remove event handlers
    value = InjectionPatterns.EVENT_HANDLER.sub('', value)
    
    # remove dangerous HTML tags
    value = InjectionPatterns.DANGEROUS_TAGS.sub('', value)
    
    # escape template markers so they render literally and cannot be evaluated
    value = value.replace('{{', '&#123;&#123;').replace('}}', '&#125;&#125;')
    value = value.replace('{%', '&#123;%').replace('%}', '%&#125;')
    
    # HTML escape the final result
    value = escape(value)
    
    return value


# validates input against dangerous injection patterns; raises ValidationError if threats detected
def validate_no_injection(value):
    if not value:
        return
    
    value = str(value)
    
    # check for script tags
    if InjectionPatterns.SCRIPT_TAG.search(value):
        raise ValidationError(
            "Input tidak boleh mengandung tag script.",
            code='script_tag_detected'
        )
    
    # check for event handlers
    if InjectionPatterns.EVENT_HANDLER.search(value):
        raise ValidationError(
            "Input tidak boleh mengandung event handler.",
            code='event_handler_detected'
        )
    
    # check for dangerous HTML tags
    if InjectionPatterns.DANGEROUS_TAGS.search(value):
        raise ValidationError(
            "Input mengandung tag HTML yang tidak diizinkan.",
            code='dangerous_tag_detected'
        )
    
    # template markers are allowed but will be escaped by sanitizer; do not reject here
    # (defense-in-depth keeps other pattern checks above)


# validates input contains only safe characters using a strict allowlist pattern
def validate_safe_text(value):
    if not value:
        return
    
    # allow: letters, numbers, spaces, dots, commas, hyphens, apostrophes, question marks, exclamation marks
    safe_pattern = re.compile(r"^[a-zA-Z0-9\s.,\-'?!ñÑáéíóúÁÉÍÓÚ]+$")
    
    if not safe_pattern.match(str(value)):
        raise ValidationError(
            "Input hanya boleh berisi huruf, angka, dan tanda baca dasar.",
            code='unsafe_characters'
        )


# checks if value matches pattern or raises ValidationError
def validate_allowlist(value, pattern, message):
    if not value:
        return

    if not pattern.fullmatch(str(value)):
        raise ValidationError(message, code='allowlist_violation')


# validates location input (titik_jemput, titik_tujuan) against location-safe character allowlist
def validate_location_allowlist(value):
    validate_allowlist(
        value,
        LOCATION_ALLOWED,
        "Input lokasi hanya boleh berisi huruf, angka, spasi, dan tanda baca dasar."
    )


# validates review text (ulasan) against review-safe character allowlist
def validate_review_allowlist(value):
    validate_allowlist(
        value,
        REVIEW_ALLOWED,
        "Input ulasan hanya boleh berisi huruf, angka, spasi, dan tanda baca dasar."
    )


# validates username input against username-safe character allowlist
def validate_username_allowlist(value):
    validate_allowlist(
        value,
        USERNAME_ALLOWED,
        "Username hanya boleh berisi huruf, angka, titik, underscore, atau strip."
    )
