"""
tugas/services/task_service.py
Service layer untuk tugas, filter, query, statistik dashboard, dan streak.
"""
from django.db.models import Q
from django.utils.timezone import now, timedelta
from ..models import Tugas

STATUS_SELESAI = "selesai"
STATUS_BELUM = "belum"


def get_dashboard_stats(user):
    """Hitung semua statistik tugas untuk dashboard."""
    tugas_user = Tugas.objects.filter(user=user)
    total = tugas_user.count()
    selesai = tugas_user.filter(status=STATUS_SELESAI).count()
    belum = total - selesai

    if total > 0:
        persen_selesai = round((selesai / total) * 100, 1)
        persen_belum = round(100 - persen_selesai, 1)
    else:
        persen_selesai = 0
        persen_belum = 0

    return {
        "total_tugas": total,
        "tugas_selesai": selesai,
        "tugas_belum_selesai": belum,
        "persentase_selesai": persen_selesai,
        "persentase_belum_selesai": persen_belum,
    }


def get_upcoming_deadlines(user, limit=5):
    """Ambil tugas yang deadline-nya paling dekat."""
    return (
        Tugas.objects.filter(user=user, status=STATUS_BELUM)
        .order_by("deadline")[:limit]
    )


def get_high_priority_tasks(user, limit=5):
    """Ambil tugas dengan prioritas tinggi yang belum selesai."""
    return (
        Tugas.objects.filter(user=user, prioritas="tinggi", status=STATUS_BELUM)
        .order_by("deadline")[:limit]
    )


def get_approaching_deadline_tasks(user, days=2):
    """Ambil tugas yang mendekati deadline (default H-2)."""
    return Tugas.objects.filter(
        user=user,
        status=STATUS_BELUM,
        deadline__gt=now(),
        deadline__lte=now() + timedelta(days=days),
    )


def get_overdue_tasks(user):
    """Ambil tugas yang sudah melewati deadline tapi belum selesai."""
    return Tugas.objects.filter(
        user=user,
        status=STATUS_BELUM,
        deadline__lt=now(),
    )


def get_filtered_tugas(user, filters):
    """Filter dan search tugas berdasarkan prioritas, kategori, status, atau keyword."""
    qs = Tugas.objects.filter(user=user)

    if filters.get("prioritas"):
        qs = qs.filter(prioritas=filters["prioritas"])
    if filters.get("kategori"):
        qs = qs.filter(kategori=filters["kategori"])
    if filters.get("status"):
        qs = qs.filter(status=filters["status"])
    if filters.get("q"):
        qs = qs.filter(
            Q(judul__icontains=filters["q"]) | Q(deskripsi__icontains=filters["q"])
        )

    return qs.select_related('user').prefetch_related('subtasks').order_by('-created_at')


def mark_task_complete(tugas):
    """Tandai tugas jadi selesai, return True jika berhasil diubah."""
    if tugas.status == STATUS_SELESAI:
        return False
    tugas.status = STATUS_SELESAI
    tugas.save(update_fields=["status", "updated_at"])
    return True


def get_export_data(user):
    """Ambil data tugas untuk kebutuhan export dokumen."""
    tugas_list = Tugas.objects.filter(user=user)
    rows = []
    for tugas in tugas_list:
        rows.append({
            "judul": tugas.judul,
            "deskripsi": tugas.deskripsi or "-",
            "kategori": tugas.get_kategori_display(),
            "prioritas": tugas.get_prioritas_display(),
            "deadline": tugas.deadline.strftime("%d-%m-%Y %H:%M") if tugas.deadline else "N/A",
            "status": "Selesai" if tugas.status == STATUS_SELESAI else "Belum Selesai",
        })
    return rows
