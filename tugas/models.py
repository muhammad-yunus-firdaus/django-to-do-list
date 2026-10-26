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
        """Validasi deadline: hanya tolak deadline lampau saat membuat tugas baru.
        Saat edit, izinkan jika deadline tidak diubah atau tidak lebih lampau dari sebelumnya.
        """
        if self.deadline and self.status.lower() == 'belum':
            if self.pk is None:
                # Tugas baru: deadline wajib di masa depan
                if self.deadline < now():
                    raise ValidationError(
                        "Deadline tidak boleh di masa lampau untuk tugas yang belum selesai."
                    )
            else:
                # Tugas lama (edit): hanya tolak jika deadline DIUBAH menjadi lebih lampau
                try:
                    original = Tugas.objects.get(pk=self.pk)
                    if self.deadline < original.deadline and self.deadline < now():
                        raise ValidationError(
                            "Deadline baru tidak boleh lebih lampau dari deadline sebelumnya."
                        )
                except Tugas.DoesNotExist:
                    pass

    def save(self, *args, **kwargs):
        """Jalankan validasi sebelum menyimpan."""
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
        status = "[selesai]" if self.selesai else "[belum]"
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
        status = "[dibaca]" if self.is_read else "[belum dibaca]"
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
        """Hitung jam_selesai berdasarkan jam_mulai + durasi_menit.
        Jika melewati tengah malam, jam_selesai bisa menjadi time hari berikutnya.
        """
        if self.jam_mulai and self.durasi_menit:
            start_dt = datetime.combine(date.today(), self.jam_mulai)
            end_dt = start_dt + timedelta(minutes=self.durasi_menit)
            return end_dt.time()
        return None

    @staticmethod
    def _time_to_minutes(t):
        """Konversi datetime.time ke menit sejak 00:00 (integer)."""
        return t.hour * 60 + t.minute

    @staticmethod
    def _get_time_intervals(start_min, durasi):
        """Mengembalikan list tuple (start, end) dalam rentang 0..1440.
        Jika melewati tengah malam (end_min > 1440), dipecah menjadi dua interval:
        (start_min, 1440) dan (0, end_min - 1440).
        """
        end_min = start_min + (durasi or 0)
        if end_min <= 1440:
            return [(start_min, end_min)]
        else:
            return [(start_min, 1440), (0, end_min - 1440)]

    @staticmethod
    def _intervals_overlap(intervals1, intervals2):
        """Cek apakah ada pasangan interval yang saling beririsan."""
        for s1, e1 in intervals1:
            for s2, e2 in intervals2:
                if s1 < e2 and e1 > s2:
                    return True
        return False

    def clean(self):
        """Validasi anti-overlap menggunakan satuan menit dan interval wrapping untuk midnight-crossing."""
        if not self.jam_mulai or not self.durasi_menit:
            return

        if not self.user_id:
            return

        new_start = self._time_to_minutes(self.jam_mulai)
        new_intervals = self._get_time_intervals(new_start, self.durasi_menit)

        # Cari aktivitas lain di tanggal yang sama milik user ini
        qs = AktivitasHarian.objects.filter(
            user=self.user,
            tanggal=self.tanggal,
        )
        # Kecualikan diri sendiri saat edit
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        for aktivitas in qs:
            ex_start = self._time_to_minutes(aktivitas.jam_mulai)
            ex_intervals = self._get_time_intervals(ex_start, aktivitas.durasi_menit)

            if self._intervals_overlap(new_intervals, ex_intervals):
                ex_end_time = (aktivitas.jam_selesai or aktivitas._calculate_jam_selesai())
                ex_end_str = ex_end_time.strftime('%H:%M') if ex_end_time else '?'
                raise ValidationError(
                    f"Jadwal bertabrakan dengan aktivitas \"{aktivitas.judul}\" "
                    f"({aktivitas.jam_mulai.strftime('%H:%M')} - {ex_end_str}). "
                    f"Silakan pilih jam yang berbeda."
                )

        # Cek overlap dengan Kegiatan
        kegiatan_qs = Kegiatan.objects.filter(
            user=self.user,
            tanggal=self.tanggal,
        )
        for keg in kegiatan_qs:
            keg_start = self._time_to_minutes(keg.jam_mulai)
            keg_end = self._time_to_minutes(keg.jam_selesai) if keg.jam_selesai else keg_start
            if keg_end > keg_start:
                keg_intervals = [(keg_start, keg_end)]
                if self._intervals_overlap(new_intervals, keg_intervals):
                    raise ValidationError(
                        f"Jadwal bertabrakan dengan acara/kegiatan \"{keg.judul}\" "
                        f"({keg.jam_mulai.strftime('%H:%M')} - {keg.jam_selesai.strftime('%H:%M')}). "
                        f"Silakan pilih jam yang berbeda."
                    )

    def save(self, *args, **kwargs):
        """Auto-calculate jam_selesai sebelum save."""
        self.jam_selesai = self._calculate_jam_selesai()
        # Jalankan validasi (termasuk anti-overlap)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        status_label = {"belum": "[belum]", "selesai": "[selesai]", "terlewat": "[terlewat]"}.get(self.status, "[belum]")
        habit_tag = " [Habit]" if self.is_habit else ""
        end_time = self.jam_selesai.strftime('%H:%M') if self.jam_selesai else '?'
        return f"{status_label} {self.judul}{habit_tag} ({self.jam_mulai.strftime('%H:%M')} - {end_time})"

    class Meta:
        ordering = ['tanggal', 'jam_mulai']
        verbose_name = "Aktivitas Harian"
        verbose_name_plural = "Aktivitas Harian"
        indexes = [
            models.Index(fields=['user', 'tanggal']),
        ]


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


class Kegiatan(models.Model):
    """Model untuk mengelola Kegiatan & Acara (Events & Meetings)."""
    KATEGORI_CHOICES = [
        ('akademik', 'Akademik'),
        ('pekerjaan', 'Pekerjaan'),
        ('keluarga', 'Keluarga'),
        ('pribadi_sosial', 'Pribadi & Sosial'),
        ('acara', 'Acara/Event'),
        ('lainnya', 'Lainnya'),
    ]

    STATUS_CHOICES = [
        ('akan_datang', 'Akan Datang'),
        ('selesai', 'Selesai'),
        ('dibatalkan', 'Dibatalkan'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="kegiatan",
        verbose_name="Pemilik", db_index=True
    )
    judul = models.CharField(max_length=255, verbose_name="Judul Kegiatan")
    kategori = models.CharField(
        max_length=20, choices=KATEGORI_CHOICES, default='lainnya',
        verbose_name="Kategori", db_index=True
    )
    tanggal = models.DateField(verbose_name="Tanggal", db_index=True)
    jam_mulai = models.TimeField(verbose_name="Jam Mulai")
    jam_selesai = models.TimeField(verbose_name="Jam Selesai")
    lokasi = models.CharField(max_length=255, blank=True, default="", verbose_name="Lokasi / Link")
    catatan = models.TextField(blank=True, default="", verbose_name="Catatan")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='akan_datang',
        verbose_name="Status", db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui Pada")

    @staticmethod
    def _time_to_minutes(t):
        """Konversi datetime.time ke menit sejak 00:00 (integer)."""
        return t.hour * 60 + t.minute

    def clean(self):
        """Validasi overlap untuk Kegiatan: jam_selesai harus setelah jam mulai."""
        if not self.tanggal or not self.jam_mulai or not self.jam_selesai:
            return

        if self.jam_selesai <= self.jam_mulai:
            raise ValidationError("Jam selesai harus setelah jam mulai.")

        if not self.user_id:
            return

        new_start = self._time_to_minutes(self.jam_mulai)
        new_end = self._time_to_minutes(self.jam_selesai)

        # 1. Cek overlap dengan Kegiatan lain
        keg_qs = Kegiatan.objects.filter(
            user=self.user,
            tanggal=self.tanggal,
        )
        if self.pk:
            keg_qs = keg_qs.exclude(pk=self.pk)

        for keg in keg_qs:
            keg_start = self._time_to_minutes(keg.jam_mulai)
            keg_end = self._time_to_minutes(keg.jam_selesai)

            if new_start < keg_end and new_end > keg_start:
                raise ValidationError(
                    f"Jadwal bertabrakan dengan acara \"{keg.judul}\" "
                    f"({keg.jam_mulai.strftime('%H:%M')} - {keg.jam_selesai.strftime('%H:%M')})."
                )

        # 2. Cek overlap dengan Aktivitas Harian
        akt_qs = AktivitasHarian.objects.filter(
            user=self.user,
            tanggal=self.tanggal,
        )
        keg_intervals = [(new_start, new_end)]
        for akt in akt_qs:
            akt_start = AktivitasHarian._time_to_minutes(akt.jam_mulai)
            akt_intervals = AktivitasHarian._get_time_intervals(akt_start, akt.durasi_menit)

            if AktivitasHarian._intervals_overlap(keg_intervals, akt_intervals):
                akt_end_time = akt.jam_selesai or akt._calculate_jam_selesai()
                akt_end_str = akt_end_time.strftime('%H:%M') if akt_end_time else '?'
                raise ValidationError(
                    f"Jadwal bertabrakan dengan aktivitas \"{akt.judul}\" "
                    f"({akt.jam_mulai.strftime('%H:%M')} - {akt_end_str})."
                )


    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.judul} ({self.tanggal} {self.jam_mulai.strftime('%H:%M')} - {self.jam_selesai.strftime('%H:%M')})"

    class Meta:
        ordering = ['tanggal', 'jam_mulai']
        verbose_name = "Kegiatan & Acara"
        verbose_name_plural = "Kegiatan & Acara"
        indexes = [
            models.Index(fields=['user', 'tanggal']),
        ]


