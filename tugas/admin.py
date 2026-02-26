from django.contrib import admin
from .models import Tugas, Subtask, Notification


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
