from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.timezone import now

class Tugas(models.Model):
    PRIORITAS_CHOICES = [
        ('tinggi', 'Tinggi'),
        ('sedang', 'Sedang'),
        ('rendah', 'Rendah'),
    ]

    KATEGORI_CHOICES = [
        ('kerja', 'Kerja'),
        ('pribadi', 'Pribadi'),
        ('perkuliahan', 'Perkuliahan'),
    ]

    STATUS_CHOICES = [
        ('belum', 'Belum Selesai'),
        ('selesai', 'Selesai'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tugas_user",
        verbose_name="Pemilik Tugas", db_index=True,
        help_text="Pilih pengguna yang memiliki tugas ini."
    )
    judul = models.CharField(
        max_length=255, verbose_name="Judul Tugas",
        help_text="Masukkan judul tugas."
    )
    deskripsi = models.TextField(
        blank=True, null=True, verbose_name="Deskripsi Tugas",
        help_text="Opsional: Deskripsikan tugas secara detail."
    )
    deadline = models.DateTimeField(
        null=True, blank=True, verbose_name="Batas Waktu",
        help_text="Pilih batas waktu penyelesaian tugas."
    )
    prioritas = models.CharField(
        max_length=10, choices=PRIORITAS_CHOICES, default='sedang',
        verbose_name="Prioritas", db_index=True,
        help_text="Tentukan prioritas tugas."
    )
    kategori = models.CharField(
        max_length=20, choices=KATEGORI_CHOICES, default='kerja',
        verbose_name="Kategori", db_index=True,
        help_text="Pilih kategori tugas."
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='belum',
        verbose_name="Status", blank=False, db_index=True,
        help_text="Tentukan status tugas (Belum Selesai atau Selesai)."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Dibuat Pada"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Diperbarui Pada"
    )

    def clean(self):
        """
        Validasi agar deadline tidak boleh lebih kecil dari waktu sekarang
        jika tugas masih dalam status 'belum selesai'.
        """
        if self.deadline:
            if self.deadline < now() and self.status.lower() == "belum":
                raise ValidationError("⛔ Deadline tidak boleh lebih kecil dari waktu sekarang untuk tugas yang belum selesai.")

    def save(self, *args, **kwargs):
        
        self.full_clean()  # Memastikan validasi dijalankan sebelum save()
        super().save(*args, **kwargs)

    @property
    def selesai(self):
        """Mengembalikan True jika tugas sudah selesai."""
        return self.status == 'selesai'

    def __str__(self):
        """Menampilkan tugas dengan format yang lebih informatif."""
        return f"{self.judul} - {self.get_status_display()} (Prioritas: {self.get_prioritas_display()})"

    class Meta:
        ordering = ['deadline', 'created_at']
        verbose_name = "Tugas"
        verbose_name_plural = "Daftar Tugas"
