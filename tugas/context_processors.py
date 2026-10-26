"""
context_processors.py — Global context untuk level dan streak user.

Dioptimasi dengan per-request caching menggunakan django.core.cache
agar tidak ada query berat di setiap HTTP request (BUG-04 fix).
Cache key bersifat per-user dan di-invalidate saat ada tugas/aktivitas baru.
"""
from django.core.cache import cache
from django.utils.timezone import now
from datetime import timedelta
from tugas.models import Tugas, AktivitasHarian

# Durasi cache dalam detik (5 menit — cukup sering untuk tetap akurat)
STATS_CACHE_TTL = 300


def user_stats(request):
    """
    Menyediakan `user_level` dan `user_streak` ke semua template.
    Di-cache per-user selama STATS_CACHE_TTL detik untuk menghindari
    query berat di setiap HTTP request.
    """
    if not request.user or not request.user.is_authenticated:
        return {}

    user = request.user
    cache_key = f"user_stats_{user.pk}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Hitung level: naik setiap 5 tugas selesai
    completed_tasks_count = Tugas.objects.filter(
        user=user, status='selesai'
    ).count()
    level = 1 + (completed_tasks_count // 5)

    # Ambil semua tanggal penyelesaian secara in-bulk (hindari query di dalam loop)
    completed_task_dates = set(
        Tugas.objects.filter(user=user, status='selesai')
        .values_list('updated_at__date', flat=True)
    )
    completed_activity_dates = set(
        AktivitasHarian.objects.filter(user=user, status='selesai')
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
            if not checked_today and current_date == today:
                current_date -= timedelta(days=1)
                checked_today = True
                continue
            break

    result = {'user_level': level, 'user_streak': streak}
    cache.set(cache_key, result, STATS_CACHE_TTL)
    return result
