from django.contrib import admin
from .models import Tugas, Subtask, Notification, AktivitasHarian, EvaluasiMingguan


@admin.register(Tugas)
class TugasAdmin(admin.ModelAdmin):
    """Konfigurasi admin panel untuk model Tugas."""

    list_display = (
        "judul",
        "user",
        "kategori",
        "prioritas",
        "status",
        "deadline",
        "created_at",
    )
    list_filter = ("status", "prioritas", "kategori", "user")
    search_fields = ("judul", "deskripsi", "user__username")
    list_per_page = 25
    list_editable = ("status", "prioritas")
    date_hierarchy = "deadline"
    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Informasi Tugas", {
            "fields": ("judul", "deskripsi", "kategori", "prioritas"),
        }),
        ("Status & Deadline", {
            "fields": ("status", "deadline"),
        }),
        ("Pemilik", {
            "fields": ("user",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(Subtask)
class SubtaskAdmin(admin.ModelAdmin):
    """Konfigurasi admin panel untuk model Subtask."""
    
    list_display = ("judul", "tugas", "selesai", "urutan", "created_at")
    list_filter = ("selesai", "tugas__kategori")
    search_fields = ("judul", "tugas__judul")
    list_per_page = 25
    list_editable = ("selesai", "urutan")
    ordering = ("tugas", "urutan", "created_at")
    
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Informasi Subtask", {
            "fields": ("tugas", "judul", "urutan"),
        }),
        ("Status", {
            "fields": ("selesai",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Konfigurasi admin panel untuk model Notification."""
    
    list_display = ("user", "tipe", "pesan", "is_read", "created_at")
    list_filter = ("tipe", "is_read", "created_at")
    search_fields = ("user__username", "pesan", "tugas__judul")
    list_per_page = 50
    list_editable = ("is_read",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    
    readonly_fields = ("created_at",)
    
    fieldsets = (
        ("Informasi Notifikasi", {
            "fields": ("user", "tugas", "tipe", "pesan"),
        }),
        ("Status", {
            "fields": ("is_read",),
        }),
        ("Timestamp", {
            "fields": ("created_at",),
        }),
    )


@admin.register(AktivitasHarian)
class AktivitasHarianAdmin(admin.ModelAdmin):
    """Konfigurasi admin panel untuk model AktivitasHarian."""

    list_display = (
        "judul", "user", "tanggal", "jam_mulai", "jam_selesai",
        "durasi_menit", "status", "is_habit",
    )
    list_filter = ("status", "is_habit", "tanggal", "user")
    search_fields = ("judul", "user__username")
    list_per_page = 25
    list_editable = ("status",)
    date_hierarchy = "tanggal"
    ordering = ("-tanggal", "jam_mulai")

    readonly_fields = ("jam_selesai", "created_at", "updated_at")

    fieldsets = (
        ("Informasi Aktivitas", {
            "fields": ("user", "judul", "tanggal"),
        }),
        ("Waktu", {
            "fields": ("jam_mulai", "durasi_menit", "jam_selesai"),
        }),
        ("Status & Habit", {
            "fields": ("status", "is_habit"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(EvaluasiMingguan)
class EvaluasiMingguanAdmin(admin.ModelAdmin):
    """Konfigurasi admin panel untuk model EvaluasiMingguan."""

    list_display = (
        "user", "minggu_mulai", "minggu_selesai",
        "persen_tugas", "persen_aktivitas", "created_at",
    )
    list_filter = ("user", "minggu_mulai")
    search_fields = ("user__username", "catatan_evaluasi")
    list_per_page = 25
    date_hierarchy = "minggu_mulai"
    ordering = ("-minggu_mulai",)

    readonly_fields = ("created_at",)

    fieldsets = (
        ("Periode", {
            "fields": ("user", "minggu_mulai", "minggu_selesai"),
        }),
        ("Statistik Tugas", {
            "fields": ("total_tugas", "tugas_selesai", "persen_tugas"),
        }),
        ("Statistik Aktivitas", {
            "fields": ("total_aktivitas", "aktivitas_selesai", "persen_aktivitas"),
        }),
        ("Catatan", {
            "fields": ("catatan_evaluasi",),
        }),
        ("Timestamp", {
            "fields": ("created_at",),
        }),
    )
