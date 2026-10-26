"""
tugas/services/notification_service.py
Service layer untuk pembuatan notifikasi deadline, overdue, subtask, dan utilitas notifikasi.
"""
from datetime import timedelta
from django.utils.timezone import now
from ..models import Tugas, Notification


def generate_deadline_notifications(user):
    """
    Generate notifikasi deadline < 24 jam untuk user tertentu.
    Harus selalu dipanggil dengan user yang sedang aktif (request.user).
    """
    threshold = now() + timedelta(hours=24)

    tugas_deadline_soon = Tugas.objects.filter(
        user=user,
        status='belum',
        deadline__isnull=False,
        deadline__lte=threshold,
        deadline__gte=now()
    )

    created_count = 0
    for tugas in tugas_deadline_soon:
        exists = Notification.objects.filter(
            user=user,
            tugas=tugas,
            tipe='deadline_soon',
            created_at__gte=now() - timedelta(hours=6)
        ).exists()

        if not exists:
            hours_left = int((tugas.deadline - now()).total_seconds() / 3600)
            pesan = f"Tugas '{tugas.judul}' deadline dalam {hours_left} jam!"
            Notification.objects.create(
                user=user,
                tugas=tugas,
                tipe='deadline_soon',
                pesan=pesan
            )
            created_count += 1

    return created_count


def generate_overdue_notifications(user):
    """Generate notifikasi tugas overdue untuk user tertentu."""
    tugas_overdue = Tugas.objects.filter(
        user=user,
        status='belum',
        deadline__isnull=False,
        deadline__lt=now()
    )

    created_count = 0
    for tugas in tugas_overdue:
        exists = Notification.objects.filter(
            user=user,
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
                user=user,
                tugas=tugas,
                tipe='overdue',
                pesan=pesan
            )
            created_count += 1

    return created_count


def check_subtask_completion(tugas):
    """Cek apakah semua subtask sudah selesai dan buat notifikasi jika 100%."""
    if tugas.status == 'selesai' or not tugas.has_subtasks:
        return False

    all_complete = tugas.subtask_progress == 100.0

    if all_complete:
        exists = Notification.objects.filter(
            user=tugas.user,
            tugas=tugas,
            tipe='subtask_complete',
            created_at__gte=now() - timedelta(hours=1)
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
    """Get jumlah notifikasi yang belum dibaca untuk user."""
    return Notification.objects.filter(user=user, is_read=False).count()


def mark_notification_read(notification_id, user):
    """Tandai notifikasi sebagai sudah dibaca."""
    try:
        notification = Notification.objects.get(id=notification_id, user=user)
        notification.is_read = True
        notification.save()
        return True
    except Notification.DoesNotExist:
        return False


def mark_all_read(user):
    """Tandai semua notifikasi user sebagai sudah dibaca."""
    return Notification.objects.filter(user=user, is_read=False).update(is_read=True)


def delete_notification(notification_id, user):
    """Hapus notifikasi."""
    try:
        notification = Notification.objects.get(id=notification_id, user=user)
        notification.delete()
        return True
    except Notification.DoesNotExist:
        return False
