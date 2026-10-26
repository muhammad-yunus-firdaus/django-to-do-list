"""
tugas/views/dashboard_views.py
View controller untuk halaman dashboard utama dan analitik ringkas.
"""
from datetime import date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ..models import AktivitasHarian, Kegiatan
from ..services.task_service import (
    get_dashboard_stats,
    get_upcoming_deadlines,
    get_high_priority_tasks,
    get_approaching_deadline_tasks,
    get_overdue_tasks,
)
from ..services.notification_service import (
    generate_deadline_notifications,
    generate_overdue_notifications,
)


@login_required
def dashboard_view(request):
    """Halaman utama setelah login, menampilkan statistik tugas dan agenda hari ini."""
    user = request.user

    # Ambil data statistik dari service layer
    stats = get_dashboard_stats(user)
    tugas_deadline_terdekat = get_upcoming_deadlines(user)
    prioritas_tinggi = get_high_priority_tasks(user)
    tugas_mendekati_deadline = get_approaching_deadline_tasks(user)
    tugas_overdue = get_overdue_tasks(user)

    # Generate notifikasi otomatis saat buka dashboard (scoped ke user ini saja)
    generate_deadline_notifications(user)
    generate_overdue_notifications(user)

    # Ambil agenda hari ini untuk widget ringkasan jadwal
    agenda_hari_ini = (
        AktivitasHarian.objects.filter(user=user, tanggal=date.today())
        .select_related('user')
        .order_by('jam_mulai')
    )

    agenda_total = agenda_hari_ini.count()
    agenda_selesai = agenda_hari_ini.filter(status='selesai').count()
    agenda_persen = round((agenda_selesai / agenda_total) * 100, 1) if agenda_total > 0 else 0

    # Ambil kegiatan mendatang (maksimal 5)
    kegiatan_mendatang = (
        Kegiatan.objects.filter(
            user=user,
            status='akan_datang',
            tanggal__gte=date.today(),
        )
        .select_related('user')
        .order_by('tanggal', 'jam_mulai')[:5]
    )

    # Hitung kegiatan hari ini untuk statistik gabungan
    kegiatan_hari_ini = Kegiatan.objects.filter(user=user, tanggal=date.today())
    kegiatan_total_today = kegiatan_hari_ini.count()
    kegiatan_selesai_today = kegiatan_hari_ini.filter(status='selesai').count()

    # Hitung progres keseluruhan gabungan (Tugas + Aktivitas Hari Ini + Kegiatan Hari Ini)
    total_tugas = stats.get("total_tugas", 0)
    tugas_selesai = stats.get("tugas_selesai", 0)
    total_items = total_tugas + agenda_total + kegiatan_total_today
    completed_items = tugas_selesai + agenda_selesai + kegiatan_selesai_today
    belum_items = total_items - completed_items
    progres_persen = round((completed_items / total_items * 100)) if total_items > 0 else 0

    context = {
        **stats,
        "tugas_deadline_terdekat": tugas_deadline_terdekat,
        "prioritas_tinggi": prioritas_tinggi,
        "tugas_mendekati_deadline": tugas_mendekati_deadline,
        "tugas_overdue": tugas_overdue,
        "agenda_hari_ini": agenda_hari_ini,
        "agenda_total": agenda_total,
        "agenda_selesai": agenda_selesai,
        "agenda_persen": agenda_persen,
        "kegiatan_mendatang": kegiatan_mendatang,
        "total_items": total_items,
        "completed_items": completed_items,
        "belum_items": belum_items,
        "progres_persen": progres_persen,
    }

    return render(request, "tugas/dashboard.html", context)
