"""
tugas/views/evaluasi_views.py
View controller untuk Evaluasi Mingguan: kalkulasi ringkasan statistik, refleksi, dan riwayat mingguan.
"""
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from ..models import Tugas, AktivitasHarian, EvaluasiMingguan
from ..forms import EvaluasiForm


def _get_week_range(ref_date=None):
    """Hitung tanggal awal (Senin) dan akhir (Minggu) dari minggu yang mengandung ref_date."""
    if ref_date is None:
        ref_date = date.today()
    start = ref_date - timedelta(days=ref_date.weekday())
    end = start + timedelta(days=6)
    return start, end


def _get_weekly_stats(user, start_date, end_date):
    """
    Hitung statistik mingguan secara real-time.
    Arsitektur terisolasi — siap untuk diintegrasikan dengan Gemini AI.
    """
    tugas_qs = Tugas.objects.filter(user=user)
    total_tugas = tugas_qs.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    ).count()
    tugas_selesai = tugas_qs.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        status='selesai',
    ).count()
    persen_tugas = round((tugas_selesai / total_tugas) * 100, 1) if total_tugas > 0 else 0

    akt_qs = AktivitasHarian.objects.filter(
        user=user,
        tanggal__gte=start_date,
        tanggal__lte=end_date,
    )
    total_aktivitas = akt_qs.count()
    aktivitas_selesai = akt_qs.filter(status='selesai').count()
    persen_aktivitas = round((aktivitas_selesai / total_aktivitas) * 100, 1) if total_aktivitas > 0 else 0

    return {
        "total_tugas": total_tugas,
        "tugas_selesai": tugas_selesai,
        "persen_tugas": persen_tugas,
        "total_aktivitas": total_aktivitas,
        "aktivitas_selesai": aktivitas_selesai,
        "persen_aktivitas": persen_aktivitas,
    }


@login_required
def evaluasi_view(request):
    """Halaman evaluasi mingguan: ringkasan statistik + catatan refleksi + riwayat."""
    user = request.user
    minggu_mulai, minggu_selesai = _get_week_range()
    stats = _get_weekly_stats(user, minggu_mulai, minggu_selesai)

    evaluasi_existing = EvaluasiMingguan.objects.filter(
        user=user,
        minggu_mulai=minggu_mulai,
    ).first()

    if request.method == "POST":
        form = EvaluasiForm(request.POST)
        if form.is_valid():
            catatan = form.cleaned_data.get("catatan_evaluasi", "")

            if evaluasi_existing:
                evaluasi_existing.total_tugas = stats["total_tugas"]
                evaluasi_existing.tugas_selesai = stats["tugas_selesai"]
                evaluasi_existing.persen_tugas = stats["persen_tugas"]
                evaluasi_existing.total_aktivitas = stats["total_aktivitas"]
                evaluasi_existing.aktivitas_selesai = stats["aktivitas_selesai"]
                evaluasi_existing.persen_aktivitas = stats["persen_aktivitas"]
                evaluasi_existing.catatan_evaluasi = catatan
                evaluasi_existing.save()
            else:
                EvaluasiMingguan.objects.create(
                    user=user,
                    minggu_mulai=minggu_mulai,
                    minggu_selesai=minggu_selesai,
                    total_tugas=stats["total_tugas"],
                    tugas_selesai=stats["tugas_selesai"],
                    persen_tugas=stats["persen_tugas"],
                    total_aktivitas=stats["total_aktivitas"],
                    aktivitas_selesai=stats["aktivitas_selesai"],
                    persen_aktivitas=stats["persen_aktivitas"],
                    catatan_evaluasi=catatan,
                )

            messages.success(request, "Evaluasi mingguan berhasil disimpan!")
            return redirect("tugas:evaluasi")
    else:
        initial_catatan = evaluasi_existing.catatan_evaluasi if evaluasi_existing else ""
        form = EvaluasiForm(initial={"catatan_evaluasi": initial_catatan})

    evaluasi_history = (
        EvaluasiMingguan.objects.filter(user=request.user)
        .select_related('user')
        .order_by('-created_at')
    )

    tugas_minggu_ini = (
        Tugas.objects.filter(
            user=user,
            deadline__date__range=[minggu_mulai, minggu_selesai]
        )
        .select_related('user')
        .prefetch_related('subtasks')
        .order_by('deadline')
    )

    aktivitas_minggu_ini = (
        AktivitasHarian.objects.filter(
            user=user,
            tanggal__range=[minggu_mulai, minggu_selesai]
        )
        .select_related('user')
        .order_by('tanggal', 'jam_mulai')
    )

    context = {
        "minggu_mulai": minggu_mulai,
        "minggu_selesai": minggu_selesai,
        "stats": stats,
        "form": form,
        "evaluasi_existing": evaluasi_existing,
        "evaluasi_history": evaluasi_history,
        "tugas_minggu_ini": tugas_minggu_ini,
        "aktivitas_minggu_ini": aktivitas_minggu_ini,
    }
    return render(request, "tugas/evaluasi.html", context)
