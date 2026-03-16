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
        # Cek deadline biar ga kelewat dari waktu sekarang
        # Khusus buat tugas yang masih belum selesai aja
        if self.deadline:
            if self.deadline < now() and self.status.lower() == "belum":
                raise ValidationError("⛔ Deadline tidak boleh lebih kecil dari waktu sekarang untuk tugas yang belum selesai.")

    def save(self, *args, **kwargs):
        # Jalanin validasi dulu sebelum disimpan
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def selesai(self):
        # Cek apakah tugas ini udah selesai atau belum
        return self.status == 'selesai'

    @property
    def is_overdue(self):
        """Mengembalikan True jika tugas belum selesai dan sudah melewati deadline."""
        if self.deadline and self.status == 'belum':
            return now() > self.deadline
        return False

    @property
    def subtask_progress(self):
        """Hitung persentase progress subtask."""
        total = self.subtasks.count()
        if total == 0:
            return None  # Tidak ada subtask
        selesai = self.subtasks.filter(selesai=True).count()
        return round((selesai / total) * 100, 1)

    @property
    def has_subtasks(self):
        """Check apakah tugas punya subtask."""
        return self.subtasks.exists()

    def __str__(self):
        """Menampilkan tugas dengan format yang lebih informatif."""
        return f"{self.judul} - {self.get_status_display()} (Prioritas: {self.get_prioritas_display()})"

    class Meta:
        ordering = ['deadline', 'created_at']
        verbose_name = "Tugas"
        verbose_name_plural = "Daftar Tugas"


class Subtask(models.Model):
    """Model untuk subtask/sub-tugas dari tugas utama."""
    tugas = models.ForeignKey(
        Tugas, on_delete=models.CASCADE, related_name="subtasks",
        verbose_name="Tugas Utama",
        help_text="Tugas utama yang memiliki subtask ini."
    )
    judul = models.CharField(
        max_length=500, verbose_name="Judul Subtask",
        help_text="Masukkan judul subtask."
    )
    selesai = models.BooleanField(
        default=False, verbose_name="Selesai",
        help_text="Centang jika subtask sudah selesai."
    )
    urutan = models.IntegerField(
        default=0, verbose_name="Urutan",
        help_text="Urutan tampilan subtask (semakin kecil semakin atas)."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Dibuat Pada"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Diperbarui Pada"
    )

    def __str__(self):
        status = "✓" if self.selesai else "○"
        return f"{status} {self.judul}"

    class Meta:
        ordering = ['urutan', 'created_at']
        verbose_name = "Subtask"
        verbose_name_plural = "Subtasks"


class Notification(models.Model):
    """Model untuk menyimpan notifikasi user."""
    TIPE_CHOICES = [
        ('deadline_soon', 'Deadline Mendekati'),
        ('overdue', 'Melewati Deadline'),
        ('subtask_complete', 'Semua Subtask Selesai'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications",
        verbose_name="Penerima", db_index=True,
        help_text="User yang menerima notifikasi."
    )
    tugas = models.ForeignKey(
        Tugas, on_delete=models.CASCADE, related_name="notifications",
        verbose_name="Tugas Terkait", null=True, blank=True,
        help_text="Tugas yang terkait dengan notifikasi ini."
    )
    tipe = models.CharField(
        max_length=20, choices=TIPE_CHOICES, verbose_name="Tipe Notifikasi",
        help_text="Jenis notifikasi."
    )
    pesan = models.CharField(
        max_length=255, verbose_name="Pesan",
        help_text="Isi pesan notifikasi."
    )
    is_read = models.BooleanField(
        default=False, verbose_name="Sudah Dibaca", db_index=True,
        help_text="Status apakah notifikasi sudah dibaca."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Dibuat Pada", db_index=True
    )

    def __str__(self):
        status = "✓" if self.is_read else "●"
        return f"{status} {self.get_tipe_display()} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notifikasi"
        verbose_name_plural = "Notifikasi"
