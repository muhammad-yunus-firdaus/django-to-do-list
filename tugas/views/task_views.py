"""
tugas/views/task_views.py
View controller untuk CRUD Tugas, pagination, detail tugas, tambah cepat, dan toggle status.
"""
import json
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils.timezone import now, is_aware, make_aware, get_current_timezone

from ..models import Tugas, Subtask
from ..forms import TugasForm
from ..services.task_service import get_filtered_tugas, mark_task_complete


@login_required
def daftar_tugas(request):
    """Menampilkan semua tugas milik user aktif dengan filter, pencarian, dan pagination."""
    filters = {
        "prioritas": request.GET.get("prioritas", ""),
        "kategori": request.GET.get("kategori", ""),
        "status": request.GET.get("status", ""),
        "q": request.GET.get("q", ""),
    }

    tugas_list = get_filtered_tugas(request.user, filters)
    kategori_list = [k[0] for k in Tugas.KATEGORI_CHOICES]

    paginator = Paginator(tugas_list, 10)
    page_number = request.GET.get('page')

    try:
        tugas_page = paginator.page(page_number)
    except PageNotAnInteger:
        tugas_page = paginator.page(1)
    except EmptyPage:
        tugas_page = paginator.page(paginator.num_pages)

    context = {
        "tugas_list": tugas_page,
        "kategori_list": kategori_list,
        "prioritas_filter": filters["prioritas"],
        "kategori_filter": filters["kategori"],
        "status_filter": filters["status"],
        "search_query": filters["q"],
    }
    return render(request, "tugas/daftar_tugas.html", context)


@login_required
def tambah_tugas(request):
    """Form pembuatan tugas baru beserta subtask dinamis."""
    if request.method == "POST":
        form = TugasForm(request.POST)
        if form.is_valid():
            tugas = form.save(commit=False)
            tugas.user = request.user
            tugas.save()

            subtask_list = request.POST.getlist('subtasks[]')
            for idx, judul in enumerate(subtask_list):
                judul_clean = judul.strip()
                if judul_clean:
                    Subtask.objects.create(
                        tugas=tugas,
                        judul=judul_clean,
                        urutan=idx + 1,
                    )

            messages.success(request, "Tugas berhasil ditambahkan!")
            return redirect("tugas:daftar")
    else:
        form = TugasForm()

    return render(request, "tugas/tambah_tugas.html", {"form": form})


@login_required
def edit_tugas(request, tugas_id):
    """Form edit data tugas yang sudah ada."""
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)

    if request.method == "POST":
        form = TugasForm(request.POST, instance=tugas)
        if form.is_valid():
            updated_tugas = form.save(commit=False)
            if not form.cleaned_data.get("deadline"):
                updated_tugas.deadline = tugas.deadline
            updated_tugas.save()
            messages.success(request, "Tugas berhasil diperbarui!")
            return redirect("tugas:daftar")
        else:
            messages.error(request, "Terjadi kesalahan. Periksa kembali form kamu.")
    else:
        form = TugasForm(instance=tugas)

    return render(request, "tugas/edit_tugas.html", {"form": form})


@login_required
@require_POST
def hapus_tugas(request, tugas_id):
    """Hapus tugas milik user aktif (POST only)."""
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)
    judul = tugas.judul
    tugas.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f"Tugas '{judul}' berhasil dihapus!"})
    messages.success(request, "Tugas berhasil dihapus!")
    return redirect("tugas:daftar")


@login_required
@require_POST
def tandai_selesai(request, tugas_id):
    """Tandai tugas jadi selesai (POST only)."""
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)
    if mark_task_complete(tugas):
        messages.success(request, f"Tugas '{tugas.judul}' telah selesai!")
    else:
        messages.warning(request, "Tugas ini sudah selesai sebelumnya!")
    return redirect("tugas:daftar")


@login_required
@require_POST
def tandai_belum(request, tugas_id):
    """Kembalikan tugas ke status belum selesai (POST only)."""
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)
    tugas.status = 'belum'
    tugas.save()
    messages.success(request, f"Tugas '{tugas.judul}' dikembalikan ke belum selesai.")
    return redirect("tugas:daftar")


@login_required
def detail_tugas(request, tugas_id):
    """Halaman detail tugas beserta daftar subtask-nya."""
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)
    return render(request, "tugas/detail_tugas.html", {"tugas": tugas})


@login_required
@require_POST
def tambah_tugas_cepat(request):
    """Endpoint AJAX untuk tambah tugas cepat."""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
        else:
            data = request.POST

        judul = data.get('judul', '').strip()
        deskripsi = data.get('deskripsi', '').strip()
        deadline_str = data.get('deadline', '').strip()
        prioritas = data.get('prioritas', 'sedang').strip()
        kategori = data.get('kategori', 'kerja').strip()

        if not judul:
            return JsonResponse({'success': False, 'message': 'Judul tugas tidak boleh kosong'}, status=400)

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                try:
                    deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass

        if not deadline:
            return JsonResponse({'success': False, 'message': 'Deadline tidak boleh kosong'}, status=400)

        if deadline < now().replace(tzinfo=None):
            if is_aware(now()):
                deadline = make_aware(deadline, get_current_timezone())
            if deadline < now():
                return JsonResponse({'success': False, 'message': 'Deadline harus di masa depan'}, status=400)

        if not is_aware(deadline) and is_aware(now()):
            deadline = make_aware(deadline, get_current_timezone())

        Tugas.objects.create(
            user=request.user,
            judul=judul,
            deskripsi=deskripsi,
            deadline=deadline,
            prioritas=prioritas,
            kategori=kategori,
            status='belum'
        )
        return JsonResponse({'success': True, 'message': 'Tugas berhasil ditambahkan!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_POST
def toggle_tugas_view(request, tugas_id):
    """Toggle status tugas selesai/belum via AJAX."""
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)
    if tugas.status == 'selesai':
        tugas.status = 'belum'
    else:
        tugas.status = 'selesai'
    tugas.save()
    return JsonResponse({
        'success': True,
        'status': tugas.status,
        'judul': tugas.judul
    })
