"""
tugas/views/kegiatan_views.py
View controller untuk pengelolaan Kegiatan & Acara (list, filter, tambah, edit, hapus, toggle status via AJAX).
"""
import json
from datetime import date
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db.models import Q

from ..models import Kegiatan
from ..forms import KegiatanForm


@login_required
def kegiatan_list_view(request):
    """Halaman utama daftar & form kegiatan acara dengan filter."""
    kategori = request.GET.get('kategori', '')
    status_filter = request.GET.get('status_filter', 'akan_datang')

    qs = Kegiatan.objects.filter(user=request.user).select_related('user')

    if kategori:
        qs = qs.filter(kategori=kategori)

    today = date.today()
    if status_filter == 'akan_datang':
        qs = qs.filter(status='akan_datang', tanggal__gte=today).order_by('tanggal', 'jam_mulai')
    elif status_filter == 'riwayat':
        qs = qs.filter(Q(status__in=['selesai', 'dibatalkan']) | Q(tanggal__lt=today)).order_by('-tanggal', '-jam_mulai')
    else:
        qs = qs.order_by('tanggal', 'jam_mulai')

    form = KegiatanForm()

    context = {
        'kegiatan_list': qs,
        'form': form,
        'kategori_filter': kategori,
        'status_filter': status_filter,
        'kategori_choices': Kegiatan.KATEGORI_CHOICES,
        'today': today,
    }
    return render(request, 'tugas/kegiatan_list.html', context)


@login_required
@require_POST
def kegiatan_tambah_view(request):
    """Tambah kegiatan acara baru via AJAX."""
    form = KegiatanForm(request.POST)
    if form.is_valid():
        kegiatan = form.save(commit=False)
        kegiatan.user = request.user
        try:
            kegiatan.save()
            return JsonResponse({'success': True})
        except ValidationError as e:
            return JsonResponse({'success': False, 'error': e.messages[0] if hasattr(e, 'messages') else str(e)})
    else:
        errors = []
        for field, err_list in form.errors.items():
            for err in err_list:
                errors.append(f"{form.fields[field].label or field}: {err}")
        return JsonResponse({'success': False, 'error': "; ".join(errors)})


@login_required
def kegiatan_edit_view(request, kegiatan_id):
    """Edit kegiatan acara via AJAX."""
    kegiatan = get_object_or_404(Kegiatan, id=kegiatan_id, user=request.user)
    if request.method == "POST":
        form = KegiatanForm(request.POST, instance=kegiatan)
        if form.is_valid():
            try:
                form.save()
                return JsonResponse({'success': True})
            except ValidationError as e:
                return JsonResponse({'success': False, 'error': e.messages[0] if hasattr(e, 'messages') else str(e)})
        else:
            errors = []
            for field, err_list in form.errors.items():
                for err in err_list:
                    errors.append(f"{form.fields[field].label or field}: {err}")
            return JsonResponse({'success': False, 'error': "; ".join(errors)})
    else:
        data = {
            'id': kegiatan.id,
            'judul': kegiatan.judul,
            'kategori': kegiatan.kategori,
            'tanggal': kegiatan.tanggal.isoformat(),
            'jam_mulai': kegiatan.jam_mulai.strftime('%H:%M'),
            'jam_selesai': kegiatan.jam_selesai.strftime('%H:%M'),
            'lokasi': kegiatan.lokasi,
            'catatan': kegiatan.catatan,
            'status': kegiatan.status,
        }
        return JsonResponse({'success': True, 'data': data})


@login_required
@require_POST
def kegiatan_hapus_view(request, kegiatan_id):
    """Hapus kegiatan acara via AJAX."""
    kegiatan = get_object_or_404(Kegiatan, id=kegiatan_id, user=request.user)
    kegiatan.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def kegiatan_toggle_status_view(request, kegiatan_id):
    """Toggle atau ubah status kegiatan langsung (AJAX-friendly)."""
    kegiatan = get_object_or_404(Kegiatan, id=kegiatan_id, user=request.user)

    target_status = None
    try:
        data = json.loads(request.body)
        target_status = data.get('status')
    except (json.JSONDecodeError, ValueError, AttributeError):
        pass

    if target_status in ['akan_datang', 'selesai', 'dibatalkan']:
        kegiatan.status = target_status
        try:
            kegiatan.save(update_fields=['status', 'updated_at'])
            return JsonResponse({'success': True, 'status': kegiatan.status})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    else:
        return JsonResponse({'success': False, 'error': 'Status tidak valid.'}, status=400)
