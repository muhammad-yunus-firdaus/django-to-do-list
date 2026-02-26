"""
Helper functions untuk notification system.
"""
from django.utils.timezone import now
from datetime import timedelta
from .models import Tugas, Notification


def generate_deadline_notifications():
    """
    Generate notifikasi untuk tugas yang deadline-nya < 24 jam.
    Dipanggil secara periodic atau saat user login.
    """
    threshold = now() + timedelta(hours=24)
    
    # Ambil tugas yang deadline-nya < 24 jam dan belum selesai
    tugas_deadline_soon = Tugas.objects.filter(
        status='belum',
        deadline__isnull=False,
        deadline__lte=threshold,
        deadline__gte=now()
    )
    
    created_count = 0
    for tugas in tugas_deadline_soon:
        # Cek apakah notifikasi untuk tugas ini sudah ada (hindari duplikasi)
        exists = Notification.objects.filter(
            user=tugas.user,
            tugas=tugas,
            tipe='deadline_soon',
            created_at__gte=now() - timedelta(hours=6)  # Hanya create jika belum ada dalam 6 jam terakhir
        ).exists()
        
        if not exists:
            hours_left = int((tugas.deadline - now()).total_seconds() / 3600)
            pesan = f"Tugas '{tugas.judul}' deadline dalam {hours_left} jam!"
            
            Notification.objects.create(
                user=tugas.user,
                tugas=tugas,
                tipe='deadline_soon',
                pesan=pesan
            )
            created_count += 1
    
    return created_count


def generate_overdue_notifications():
    """
    Generate notifikasi untuk tugas yang sudah melewati deadline.
    """
    # Ambil tugas yang sudah overdue dan belum selesai
    tugas_overdue = Tugas.objects.filter(
        status='belum',
        deadline__isnull=False,
        deadline__lt=now()
    )
    
    created_count = 0
    for tugas in tugas_overdue:
        # Cek duplikasi (hanya create 1x per hari)
        exists = Notification.objects.filter(
            user=tugas.user,
            tugas=tugas,
            tipe='overdue',
            created_at__gte=now() - timedelta(days=1)
        ).exists()
        
        if not exists:
            days_late = (now() - tugas.deadline).days
            if days_late == 0:
                pesan = f"Tugas '{tugas.judul}' sudah melewati deadline!"
            else:
                pesan = f"Tugas '{tugas.judul}' terlambat {days_late} hari!"
            
            Notification.objects.create(
                user=tugas.user,
                tugas=tugas,
                tipe='overdue',
                pesan=pesan
            )
            created_count += 1
    
    return created_count


def check_subtask_completion(tugas):
    """
    Cek apakah semua subtask sudah selesai dan generate notifikasi.
    Dipanggil setiap kali subtask di-toggle.
    
    Args:
        tugas: Instance dari model Tugas
    
    Returns:
        bool: True jika notifikasi dibuat, False jika tidak
    """
    # Skip jika tugas sudah selesai atau tidak punya subtask
    if tugas.status == 'selesai' or not tugas.has_subtasks:
        return False
    
    # Cek apakah semua subtask selesai
    all_complete = tugas.subtask_progress == 100.0
    
    if all_complete:
        # Cek duplikasi
        exists = Notification.objects.filter(
            user=tugas.user,
            tugas=tugas,
            tipe='subtask_complete',
            created_at__gte=now() - timedelta(hours=1)  # Hindari spam notif
        ).exists()
        
        if not exists:
            pesan = f"Semua subtask '{tugas.judul}' selesai! Tandai tugas sebagai selesai?"
            
            Notification.objects.create(
                user=tugas.user,
                tugas=tugas,
                tipe='subtask_complete',
                pesan=pesan
            )
            return True
    
    return False


def get_unread_count(user):
    """
    Get jumlah notifikasi yang belum dibaca untuk user.
    
    Args:
        user: Instance dari User model
    
    Returns:
        int: Jumlah notifikasi belum dibaca
    """
    return Notification.objects.filter(user=user, is_read=False).count()


def mark_notification_read(notification_id, user):
    """
    Tandai notifikasi sebagai sudah dibaca.
    
    Args:
        notification_id: ID notifikasi
        user: Instance dari User model
    
    Returns:
        bool: True jika berhasil, False jika gagal
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=user)
        notification.is_read = True
        notification.save()
        return True
    except Notification.DoesNotExist:
        return False


def mark_all_read(user):
    """
    Tandai semua notifikasi user sebagai sudah dibaca.
    
    Args:
        user: Instance dari User model
    
    Returns:
        int: Jumlah notifikasi yang di-update
    """
    return Notification.objects.filter(user=user, is_read=False).update(is_read=True)


def delete_notification(notification_id, user):
    """
    Hapus notifikasi.
    
    Args:
        notification_id: ID notifikasi
        user: Instance dari User model
    
    Returns:
        bool: True jika berhasil, False jika gagal
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=user)
        notification.delete()
        return True
    except Notification.DoesNotExist:
        return False
