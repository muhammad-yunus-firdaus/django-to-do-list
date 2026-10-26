"""
tugas/views/subtask_views.py
View controller untuk pengelolaan subtask: tambah, edit, hapus, dan toggle status via AJAX (Optimistic UI).
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse

from ..models import Tugas, Subtask
from ..forms import SubtaskForm
from ..services.notification_service import check_subtask_completion


@login_required
@require_POST
def tambah_subtask(request, tugas_id):
    """Tambah subtask baru ke dalam tugas tertentu."""
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)
    form = SubtaskForm(request.POST)

    if form.is_valid():
        subtask = form.save(commit=False)
        subtask.tugas = tugas

        last_subtask = tugas.subtasks.order_by('-urutan').first()
        subtask.urutan = (last_subtask.urutan + 1) if last_subtask else 1

        subtask.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"Subtask '{subtask.judul}' berhasil ditambahkan!",
                'id': subtask.id,
                'judul': subtask.judul,
                'selesai': subtask.selesai,
                'progress': tugas.subtask_progress
            })
        messages.success(request, f"Subtask '{subtask.judul}' berhasil ditambahkan!")
    else:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Gagal menambahkan subtask.'}, status=400)
        messages.error(request, "Gagal menambahkan subtask. Silakan coba lagi.")

    return redirect('tugas:detail', tugas_id=tugas.id)


@login_required
@require_POST
def edit_subtask(request, subtask_id):
    """Ubah judul subtask."""
    subtask = get_object_or_404(Subtask, id=subtask_id, tugas__user=request.user)
    judul_baru = request.POST.get('judul', '').strip()

    if judul_baru:
        subtask.judul = judul_baru
        subtask.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Subtask berhasil diperbarui!',
                'id': subtask.id,
                'judul': subtask.judul,
                'progress': subtask.tugas.subtask_progress
            })
        messages.success(request, "Subtask berhasil diupdate!")
    else:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Judul subtask tidak boleh kosong.'}, status=400)
        messages.error(request, "Judul subtask tidak boleh kosong.")

    return redirect('tugas:detail', tugas_id=subtask.tugas.id)


@login_required
@require_POST
def hapus_subtask(request, subtask_id):
    """Hapus subtask dari tugas."""
    subtask = get_object_or_404(Subtask, id=subtask_id, tugas__user=request.user)
    tugas = subtask.tugas
    judul = subtask.judul

    subtask.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Subtask '{judul}' berhasil dihapus!",
            'progress': tugas.subtask_progress
        })
    messages.success(request, f"Subtask '{judul}' berhasil dihapus!")
    return redirect('tugas:detail', tugas_id=tugas.id)


@login_required
@require_POST
def toggle_subtask(request, subtask_id):
    """Toggle centang/uncentang subtask via AJAX."""
    subtask = get_object_or_404(Subtask, id=subtask_id, tugas__user=request.user)

    subtask.selesai = not subtask.selesai
    subtask.save()

    check_subtask_completion(subtask.tugas)

    return JsonResponse({
        'success': True,
        'selesai': subtask.selesai,
        'progress': subtask.tugas.subtask_progress
    })
