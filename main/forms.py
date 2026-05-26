from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Pesanan, Rating
from .sanitizers import (
    sanitize_input,
    validate_location_allowlist,
    validate_no_injection,
    validate_review_allowlist,
    sanitize_review_text,
    validate_username_allowlist,
)


class RegisterForm(UserCreationForm):
    class Meta:
        model  = CustomUser
        fields = ('username', 'role')
    
    def clean_username(self):
        """Validate username against a strict allowlist."""
        username = self.cleaned_data.get('username', '')
        validate_no_injection(username)
        validate_username_allowlist(username)
        return username

class PesananForm(forms.ModelForm):
    class Meta:
        model  = Pesanan
        fields = ('titik_jemput', 'titik_tujuan')

    def clean_titik_jemput(self):
        """Validate and sanitize pickup location."""
        val = self.cleaned_data.get('titik_jemput', '')
        if not val:
            return val
        
        validate_no_injection(val)
        validate_location_allowlist(val)
        val = sanitize_input(val, allow_basic_html=False)
        return val

    def clean_titik_tujuan(self):
        """Validate and sanitize destination location."""
        val = self.cleaned_data.get('titik_tujuan', '')
        if not val:
            return val
        
        validate_no_injection(val)
        validate_location_allowlist(val)
        val = sanitize_input(val, allow_basic_html=False)
        return val


class RatingForm(forms.ModelForm):
    skor = forms.ChoiceField(
        choices=[(i, f"{i} Bintang") for i in range(1, 6)],
        widget=forms.RadioSelect,
        label="Nilai Pengemudi",
    )

    class Meta:
        model  = Rating
        fields = ('skor', 'ulasan')
        widgets = {
            'ulasan': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Tulis ulasan Anda (opsional)...',
            }),
        }
    
    def clean_ulasan(self):
        """Validate and sanitize review text."""
        ulasan = self.cleaned_data.get('ulasan', '')
        if not ulasan:
            return ulasan
        
        validate_no_injection(ulasan)
        validate_review_allowlist(ulasan)
        ulasan = sanitize_review_text(ulasan)
        
        return ulasan