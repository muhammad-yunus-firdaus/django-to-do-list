"""
tugas/views/export_views.py
View controller untuk endpoint unduhan dokumen: CSV, Excel, PDF (Tugas, Kegiatan, dan Jadwal Harian).
"""
from datetime import date
from django.contrib.auth.decorators import login_required
from ..services.export_service import (
    generate_tugas_csv,
    generate_tugas_excel,
    generate_tugas_pdf,
    generate_kegiatan_pdf,
    generate_kegiatan_excel,
    generate_jadwal_pdf,
    generate_jadwal_excel,
)


@login_required
def export_csv(request):
    """Download semua tugas dalam format CSV."""
    return generate_tugas_csv(request.user)


@login_required
def export_excel(request):
    """Download daftar tugas dalam format Excel (.xlsx)."""
    return generate_tugas_excel(request.user)


@login_required
def export_pdf(request):
    """Download daftar tugas dalam format PDF."""
    return generate_tugas_pdf(request.user)


@login_required
def export_kegiatan_pdf(request):
    """Download daftar kegiatan & acara dalam format PDF."""
    return generate_kegiatan_pdf(request.user)


@login_required
def export_kegiatan_excel(request):
    """Download daftar kegiatan & acara dalam format Excel (.xlsx)."""
    return generate_kegiatan_excel(request.user)


@login_required
def export_jadwal_pdf_view(request):
    """Download jadwal harian dalam format PDF A4."""
    tanggal_str = request.GET.get('tanggal', '')
    if tanggal_str:
        try:
            tanggal = date.fromisoformat(tanggal_str)
        except ValueError:
            tanggal = date.today()
    else:
        tanggal = date.today()
    return generate_jadwal_pdf(request.user, tanggal)


@login_required
def export_jadwal_excel_view(request):
    """Download jadwal harian dalam format Excel (.xlsx)."""
    tanggal_str = request.GET.get('tanggal', '')
    if tanggal_str:
        try:
            tanggal = date.fromisoformat(tanggal_str)
        except ValueError:
            tanggal = date.today()
    else:
        tanggal = date.today()
    return generate_jadwal_excel(request.user, tanggal)
