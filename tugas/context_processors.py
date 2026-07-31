from django.utils.timezone import now
from datetime import timedelta, date
from tugas.models import Tugas, AktivitasHarian

def user_stats(request):
    if not request.user or not request.user.is_authenticated:
        return {}
    
    # Hitung level: dari jumlah tugas yang selesai (level naik setiap 5 tugas)
    completed_tasks_count = Tugas.objects.filter(user=request.user, status='selesai').count()
    level = 1 + (completed_tasks_count // 5)
    
    # Ambil semua tanggal unik penyelesaian tugas dan aktivitas untuk optimasi query (menghindari query di dalam loop)
    completed_task_dates = set(
        Tugas.objects.filter(user=request.user, status='selesai')
        .values_list('updated_at__date', flat=True)
    )
    
    completed_activity_dates = set(
        AktivitasHarian.objects.filter(user=request.user, status='selesai')
        .values_list('tanggal', flat=True)
    )
    
    activity_dates = completed_task_dates.union(completed_activity_dates)
    
    # Hitung streak secara in-memory
    streak = 0
    today = now().date()
    current_date = today
    checked_today = False
    
    while True:
        if current_date in activity_dates:
            streak += 1
            current_date -= timedelta(days=1)
            checked_today = True
        else:
            # Jika hari pertama dicek (hari ini) tidak ada aktivitas, kita boleh periksa kemarin
            if not checked_today and current_date == today:
                current_date -= timedelta(days=1)
                checked_today = True
                continue
            break
            
    return {
        'user_level': level,
        'user_streak': streak,
    }
