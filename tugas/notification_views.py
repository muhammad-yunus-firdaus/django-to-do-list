"""
Views untuk Notification System
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils.timezone import now

from .models import Notification


@login_required
def get_notifications(request):
    """API untuk fetch notifications user (AJAX)."""
    notifications = Notification.objects.filter(user=request.user)[:20]  # Max 20 terbaru
    
    data = [{
        'id': notif.id,
        'tipe': notif.tipe,
        'pesan': notif.pesan,
        'is_read': notif.is_read,
        'tugas_id': notif.tugas.id if notif.tugas else None,
        'created_at': notif.created_at.strftime('%d %b %Y, %H:%M'),
        'time_ago': get_time_ago(notif.created_at)
    } for notif in notifications]
    
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return JsonResponse({
        'notifications': data,
        'unread_count': unread_count
    })


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Tandai notifikasi sebagai sudah dibaca."""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        return JsonResponse({
            'success': True,
            'unread_count': unread_count
        })
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notifikasi tidak ditemukan'}, status=404)


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Tandai semua notifikasi sebagai sudah dibaca."""
    count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    return JsonResponse({
        'success': True,
        'count': count
    })


@login_required
@require_POST
def delete_notification(request, notification_id):
    """Hapus notifikasi."""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.delete()
        
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        return JsonResponse({
            'success': True,
            'unread_count': unread_count
        })
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notifikasi tidak ditemukan'}, status=404)


# Helper function
def get_time_ago(datetime_obj):
    """Convert datetime to human-readable time ago format."""
    diff = now() - datetime_obj
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Baru saja"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} menit yang lalu"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} jam yang lalu"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} hari yang lalu"
    else:
        return datetime_obj.strftime('%d %b %Y')
