"""
tugas/services/agenda_service.py
Service layer untuk agenda harian, habit copy, free time slot, dan kalkulasi timeline 24 jam.
"""
from datetime import date, time as dt_time, datetime as dt_datetime, timedelta
from django.core.exceptions import ValidationError
from ..models import AktivitasHarian, Kegiatan


def copy_habits_for_today(user):
    """
    Salin semua aktivitas habit ke tanggal hari ini jika belum ada.
    Dipanggil on-demand saat halaman agenda dibuka (PythonAnywhere compatible).
    """
    today = date.today()
    habits = (
        AktivitasHarian.objects.filter(user=user, is_habit=True)
        .values('judul', 'jam_mulai', 'durasi_menit')
        .distinct()
    )

    for habit in habits:
        exists = AktivitasHarian.objects.filter(
            user=user,
            tanggal=today,
            judul=habit['judul'],
            jam_mulai=habit['jam_mulai'],
        ).exists()

        if not exists:
            try:
                AktivitasHarian.objects.create(
                    user=user,
                    judul=habit['judul'],
                    jam_mulai=habit['jam_mulai'],
                    durasi_menit=habit['durasi_menit'],
                    is_habit=True,
                    tanggal=today,
                    status='belum',
                )
            except ValidationError:
                pass


def get_next_free_slot(user, tanggal):
    """
    Hitung slot waktu kosong berikutnya berdasarkan aktivitas/kegiatan terakhir di hari tersebut.
    - Jika ada, ambil jam_selesai terakhir + 1 menit.
    - Jika belum ada dan tanggal = hari ini, default ke waktu sekarang (dibulatkan ke 5 menit berikutnya).
    - Jika belum ada dan bukan hari ini, default ke 07:00.
    """
    last_activity = (
        AktivitasHarian.objects.filter(user=user, tanggal=tanggal)
        .order_by('-jam_mulai')
        .first()
    )
    last_kegiatan = (
        Kegiatan.objects.filter(user=user, tanggal=tanggal)
        .order_by('-jam_mulai')
        .first()
    )

    latest_time = None
    if last_activity and last_activity.jam_selesai:
        latest_time = last_activity.jam_selesai
    if last_kegiatan and last_kegiatan.jam_selesai:
        if latest_time is None or last_kegiatan.jam_selesai > latest_time:
            latest_time = last_kegiatan.jam_selesai

    if latest_time:
        last_end_dt = dt_datetime.combine(tanggal, latest_time)
        next_slot_dt = last_end_dt + timedelta(minutes=1)
        if next_slot_dt.time() < dt_time(23, 59):
            return next_slot_dt.time().strftime('%H:%M')
        return '23:00'

    if tanggal == date.today():
        from django.utils.timezone import localtime
        now_local = localtime()
        minute = now_local.minute
        rounded_minute = ((minute // 5) + 1) * 5
        if rounded_minute >= 60:
            next_hour = now_local.hour + 1
            if next_hour > 23:
                return '23:00'
            return dt_time(next_hour, 0).strftime('%H:%M')
        return dt_time(now_local.hour, rounded_minute).strftime('%H:%M')

    return '07:00'


def generate_24h_timeline(aktivitas_list, kegiatan_list):
    """
    Membuat timeline 24 jam dengan slot 30 menit.
    Aktivitas/kegiatan disisipkan secara presisi ke slot yang sesuai.
    Slot kosong ditandai sebagai 'kosong'.
    Returns list of dicts siap dijadikan JSON.
    """
    occupied = []
    for akt in aktivitas_list:
        end_time = akt.jam_selesai or akt._calculate_jam_selesai()
        if end_time:
            occupied.append({
                'type': 'aktivitas',
                'id': akt.id,
                'judul': akt.judul,
                'jam_mulai': akt.jam_mulai.strftime('%H:%M'),
                'jam_selesai': end_time.strftime('%H:%M'),
                'durasi_menit': akt.durasi_menit,
                'status': akt.status,
                'is_habit': akt.is_habit,
                'start_minutes': akt.jam_mulai.hour * 60 + akt.jam_mulai.minute,
                'end_minutes': end_time.hour * 60 + end_time.minute,
            })
    for keg in kegiatan_list:
        if keg.jam_selesai:
            occupied.append({
                'type': 'kegiatan',
                'id': keg.id,
                'judul': keg.judul,
                'jam_mulai': keg.jam_mulai.strftime('%H:%M'),
                'jam_selesai': keg.jam_selesai.strftime('%H:%M'),
                'kategori': keg.kategori,
                'status': keg.status,
                'lokasi': keg.lokasi or '',
                'start_minutes': keg.jam_mulai.hour * 60 + keg.jam_mulai.minute,
                'end_minutes': keg.jam_selesai.hour * 60 + keg.jam_selesai.minute,
            })

    occupied.sort(key=lambda x: x['start_minutes'])

    timeline = []
    cursor = 0

    for item in occupied:
        while cursor < item['start_minutes']:
            slot_end = min(cursor + 30, item['start_minutes'])
            timeline.append({
                'type': 'kosong',
                'jam_mulai': f"{cursor // 60:02d}:{cursor % 60:02d}",
                'jam_selesai': f"{slot_end // 60:02d}:{slot_end % 60:02d}",
            })
            cursor = slot_end

        timeline.append(item)
        cursor = max(cursor, item['end_minutes'])

    while cursor < 1440:
        slot_end = min(cursor + 30, 1440)
        end_h = slot_end // 60 if slot_end < 1440 else 23
        end_m = slot_end % 60 if slot_end < 1440 else 59
        timeline.append({
            'type': 'kosong',
            'jam_mulai': f"{cursor // 60:02d}:{cursor % 60:02d}",
            'jam_selesai': f"{end_h:02d}:{end_m:02d}",
        })
        cursor = slot_end

    return timeline
