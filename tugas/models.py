from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from datetime import timedelta, date, datetime, time

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


class AktivitasHarian(models.Model):
    """Model untuk aktivitas harian / time-blocking."""
    STATUS_CHOICES = [
        ('belum', 'Belum'),
        ('selesai', 'Selesai'),
        ('terlewat', 'Terlewat'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="aktivitas_harian",
        verbose_name="Pemilik", db_index=True,
        help_text="User yang memiliki aktivitas ini."
    )
    judul = models.CharField(
        max_length=255, verbose_name="Judul Aktivitas",
        help_text="Masukkan judul aktivitas."
    )
    jam_mulai = models.TimeField(
        verbose_name="Jam Mulai",
        help_text="Waktu mulai aktivitas."
    )
    durasi_menit = models.PositiveIntegerField(
        verbose_name="Durasi (Menit)",
        help_text="Durasi aktivitas dalam menit."
    )
    jam_selesai = models.TimeField(
        verbose_name="Jam Selesai", blank=True, null=True,
        help_text="Otomatis dihitung dari jam_mulai + durasi_menit."
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='belum',
        verbose_name="Status", db_index=True,
        help_text="Status penyelesaian aktivitas."
    )
    is_habit = models.BooleanField(
        default=False, verbose_name="Ulangi Setiap Hari",
        help_text="Jika dicentang, aktivitas ini akan otomatis diulang setiap hari."
    )
    tanggal = models.DateField(
        default=date.today, verbose_name="Tanggal", db_index=True,
        help_text="Tanggal aktivitas."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Dibuat Pada"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Diperbarui Pada"
    )

    def _calculate_jam_selesai(self):
        """Hitung jam_selesai berdasarkan jam_mulai + durasi_menit."""
        if self.jam_mulai and self.durasi_menit:
            start_dt = datetime.combine(date.today(), self.jam_mulai)
            end_dt = start_dt + timedelta(minutes=self.durasi_menit)
            return end_dt.time()
        return None

    def clean(self):
        """Validasi anti-overlap: cegah aktivitas di jam yang sudah terisi."""
        if not self.jam_mulai or not self.durasi_menit:
            return

        calculated_end = self._calculate_jam_selesai()
        if not calculated_end:
            return

        # Cari aktivitas lain di tanggal yang sama milik user ini
        qs = AktivitasHarian.objects.filter(
            user=self.user,
            tanggal=self.tanggal,
        )
        # Kecualikan diri sendiri saat edit
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        for aktivitas in qs:
            existing_start = aktivitas.jam_mulai
            existing_end = aktivitas.jam_selesai or aktivitas._calculate_jam_selesai()
            if not existing_end:
                continue

            # Cek overlap: new_start < existing_end AND new_end > existing_start
            if self.jam_mulai < existing_end and calculated_end > existing_start:
                raise ValidationError(
                    f"Jadwal bertabrakan dengan aktivitas \"{aktivitas.judul}\" "
                    f"({existing_start.strftime('%H:%M')} - {existing_end.strftime('%H:%M')}). "
                    f"Silakan pilih jam yang berbeda."
                )

    def save(self, *args, **kwargs):
        """Auto-calculate jam_selesai sebelum save."""
        self.jam_selesai = self._calculate_jam_selesai()
        # Jalankan validasi (termasuk anti-overlap)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        status_icon = {"belum": "○", "selesai": "✓", "terlewat": "✗"}.get(self.status, "○")
        habit_tag = " [Habit]" if self.is_habit else ""
        return f"{status_icon} {self.judul}{habit_tag} ({self.jam_mulai.strftime('%H:%M')} - {self.jam_selesai.strftime('%H:%M') if self.jam_selesai else '?'})"

    class Meta:
        ordering = ['tanggal', 'jam_mulai']
        verbose_name = "Aktivitas Harian"
        verbose_name_plural = "Aktivitas Harian"


class EvaluasiMingguan(models.Model):
    """
    Model untuk evaluasi mingguan.
    Arsitektur terisolasi dan bersih — siap diintegrasikan dengan Gemini AI API di masa depan.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="evaluasi_mingguan",
        verbose_name="Pemilik", db_index=True,
        help_text="User yang memiliki evaluasi ini."
    )
    minggu_mulai = models.DateField(
        verbose_name="Awal Minggu",
        help_text="Tanggal awal periode minggu evaluasi."
    )
    minggu_selesai = models.DateField(
        verbose_name="Akhir Minggu",
        help_text="Tanggal akhir periode minggu evaluasi."
    )
    # Statistik Tugas Utama
    total_tugas = models.IntegerField(
        default=0, verbose_name="Total Tugas",
        help_text="Jumlah tugas pada minggu tersebut."
    )
    tugas_selesai = models.IntegerField(
        default=0, verbose_name="Tugas Selesai",
        help_text="Jumlah tugas yang diselesaikan."
    )
    persen_tugas = models.FloatField(
        default=0.0, verbose_name="% Penyelesaian Tugas",
        help_text="Persentase penyelesaian tugas utama."
    )
    # Statistik Aktivitas Harian
    total_aktivitas = models.IntegerField(
        default=0, verbose_name="Total Aktivitas",
        help_text="Jumlah aktivitas harian pada minggu tersebut."
    )
    aktivitas_selesai = models.IntegerField(
        default=0, verbose_name="Aktivitas Selesai",
        help_text="Jumlah aktivitas harian yang diselesaikan."
    )
    persen_aktivitas = models.FloatField(
        default=0.0, verbose_name="% Penyelesaian Aktivitas",
        help_text="Persentase penyelesaian aktivitas harian."
    )
    # Catatan refleksi manual dari user
    catatan_evaluasi = models.TextField(
        blank=True, default="", verbose_name="Catatan Evaluasi",
        help_text="Catatan refleksi atau evaluasi mingguan dari user."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Dibuat Pada"
    )

    def __str__(self):
        return (
            f"Evaluasi {self.user.username}: "
            f"{self.minggu_mulai.strftime('%d %b')} - {self.minggu_selesai.strftime('%d %b %Y')} "
            f"(Tugas: {self.persen_tugas:.0f}%, Aktivitas: {self.persen_aktivitas:.0f}%)"
        )

    class Meta:
        ordering = ['-minggu_mulai']
        verbose_name = "Evaluasi Mingguan"
        verbose_name_plural = "Evaluasi Mingguan"
        # Satu user hanya bisa punya satu evaluasi per minggu
        unique_together = ['user', 'minggu_mulai']

