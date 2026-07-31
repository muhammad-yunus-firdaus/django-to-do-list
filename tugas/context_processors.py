from django.utils.timezone import now
from datetime import timedelta, date
from tugas.models import Tugas, AktivitasHarian

def user_stats(request):
    if not request.user or not request.user.is_authenticated:
        return {}
    
    # Hitung level: dari jumlah tugas yang selesai (level naik setiap 5 tugas)
    completed_tasks_count = Tugas.objects.filter(user=request.user, status='selesai').count()
    level = 1 + (completed_tasks_count // 5)
    
    # Hitung streak: jumlah hari beruntun ke belakang di mana user menyelesaikan minimal 1 tugas atau aktivitas
    streak = 0
    today = now().date()
    current_date = today
    
    # Kita izinkan streak hari ini/kemarin sebagai pemeliharaan streak aktif
    checked_today = False
    
    while True:
        has_task = Tugas.objects.filter(
            user=request.user,
            status='selesai',
            updated_at__date=current_date
        ).exists()
        
        has_activity = AktivitasHarian.objects.filter(
            user=request.user,
            status='selesai',
            tanggal=current_date
        ).exists()
        
        if has_task or has_activity:
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
