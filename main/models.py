from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from .sanitizers import (
    sanitize_input,
    validate_location_allowlist,
    validate_no_injection,
    validate_review_allowlist,
    validate_username_allowlist,
)


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('penumpang', 'Penumpang'),
        ('pengemudi', 'Pengemudi'),
        ('penyedia', 'Penyedia Layanan'),
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='penumpang')

    def clean(self):
        validate_username_allowlist(self.username)
        validate_no_injection(self.username)


class Pesanan(models.Model):
    STATUS_CHOICES = (
        ('Menunggu Pengemudi', 'Menunggu Pengemudi'),
        ('Sedang Diantar',     'Sedang Diantar'),
        ('Selesai',            'Selesai'),
        ('Dibatalkan',         'Dibatalkan'),
    )
    penumpang  = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                   related_name='pesanan')
    pengemudi  = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,
                                   null=True, blank=True,
                                   related_name='pesanan_diambil')
    titik_jemput = models.CharField(max_length=255)
    titik_tujuan = models.CharField(max_length=255)
    status       = models.CharField(max_length=25, choices=STATUS_CHOICES,
                                    default='Menunggu Pengemudi')
    waktu_pesan  = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validate and sanitize location fields at model level."""
        validate_location_allowlist(self.titik_jemput)
        validate_location_allowlist(self.titik_tujuan)
        validate_no_injection(self.titik_jemput)
        validate_no_injection(self.titik_tujuan)
        
        self.titik_jemput = sanitize_input(self.titik_jemput)
        self.titik_tujuan = sanitize_input(self.titik_tujuan)

    def save(self, *args, **kwargs):
        """Validate the full model before saving."""
        self.clean()
        self.full_clean(exclude=None)
        super().save(*args, **kwargs)

    def __str__(self):
        return (f"{self.penumpang.username}: "
                f"{self.titik_jemput} → {self.titik_tujuan}")


class Rating(models.Model):
    pesanan    = models.OneToOneField(Pesanan, on_delete=models.CASCADE,
                                      related_name='rating')
    penumpang  = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                   related_name='rating_diberikan')
    pengemudi  = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                   related_name='rating_diterima')
    skor       = models.PositiveSmallIntegerField(
                     validators=[MinValueValidator(1), MaxValueValidator(5)])
    ulasan     = models.TextField(blank=True)
    waktu      = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validate and sanitize review text at model level."""
        if self.ulasan:
            validate_review_allowlist(self.ulasan)
            validate_no_injection(self.ulasan)
            self.ulasan = sanitize_input(self.ulasan)

    def save(self, *args, **kwargs):
        """Validate the full model before saving."""
        self.clean()
        self.full_clean(exclude=None)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Rating {self.skor}★ — {self.pengemudi.username} oleh {self.penumpang.username}"