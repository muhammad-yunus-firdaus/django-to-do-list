"""
tugas/views/agenda_views.py
View controller untuk Agenda Harian (Timeline 24 Jam, Habit Tracker, CRUD Aktivitas Harian).
"""
import json
from datetime import date, timedelta, time as dt_time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError

from ..models import AktivitasHarian, Kegiatan
from ..forms import AktivitasHarianForm
from ..services.agenda_service import (
    copy_habits_for_today,
    get_next_free_slot,
    generate_24h_timeline,
)

# Alias untuk backward compatibility (termasuk dipanggil di tests)
_copy_habits_for_today = copy_habits_for_today
_get_next_free_slot = get_next_free_slot
_generate_24h_timeline = generate_24h_timeline


@login_required
def agenda_harian_view(request):
    """Halaman agenda harian: timeline terpadu aktivitas + kegiatan + form tambah + navigasi tanggal."""
    tanggal_str = request.GET.get('tanggal', '')
    if tanggal_str:
        try:
            tanggal = date.fromisoformat(tanggal_str)
        except ValueError:
            tanggal = date.today()
    else:
        tanggal = date.today()

    if tanggal == date.today():
        copy_habits_for_today(request.user)

    aktivitas_list = (
        AktivitasHarian.objects.filter(user=request.user, tanggal=tanggal)
        .select_related('user')
        .order_by('jam_mulai')
    )

    kegiatan_list = (
        Kegiatan.objects.filter(user=request.user, tanggal=tanggal)
        .select_related('user')
        .order_by('jam_mulai')
    )

    timeline_items = []
    for akt in aktivitas_list:
        timeline_items.append({
            'type': 'aktivitas',
            'item': akt,
            'jam_mulai': akt.jam_mulai,
        })
    for keg in kegiatan_list:
        timeline_items.append({
            'type': 'kegiatan',
            'item': keg,
            'jam_mulai': keg.jam_mulai,
        })
    timeline_items.sort(key=lambda x: x['jam_mulai'])

    total = aktivitas_list.count()
    selesai = aktivitas_list.filter(status='selesai').count()
    persen = round((selesai / total) * 100, 1) if total > 0 else 0

    form_has_error = False
    saved_form_data = request.session.pop('agenda_form_data', None)

    if saved_form_data:
        form = AktivitasHarianForm(initial=saved_form_data)
        form_has_error = True
    else:
        next_slot = get_next_free_slot(request.user, tanggal)
        form = AktivitasHarianForm(initial={'jam_mulai': next_slot})

    show_yesterday_prompt = False
    yesterday_activities = []
    if total == 0:
        kemarin = tanggal - timedelta(days=1)
        akt_kemarin = (
            AktivitasHarian.objects.filter(user=request.user, tanggal=kemarin)
            .select_related('user')
            .order_by('jam_mulai')
        )
        if akt_kemarin.exists():
            show_yesterday_prompt = True
            yesterday_activities = list(
                akt_kemarin.values('judul', 'jam_mulai', 'durasi_menit', 'is_habit')
            )
            for akt in yesterday_activities:
                akt['jam_mulai'] = akt['jam_mulai'].strftime('%H:%M')

    timeline_24h_json = generate_24h_timeline(aktivitas_list, kegiatan_list)

    prev_date = tanggal - timedelta(days=1)
    next_date = tanggal + timedelta(days=1)

    context = {
        "aktivitas_list": aktivitas_list,
        "timeline_items": timeline_items,
        "timeline_24h_json": timeline_24h_json,
        "tanggal": tanggal,
        "is_today": tanggal == date.today(),
        "prev_date": prev_date,
        "next_date": next_date,
        "form": form,
        "form_has_error": form_has_error,
        "total_aktivitas": total,
        "aktivitas_selesai": selesai,
        "persen_aktivitas": persen,
        "show_yesterday_prompt": show_yesterday_prompt,
        "yesterday_activities_json": yesterday_activities,
    }
    return render(request, "tugas/agenda_harian.html", context)


@login_required
def tambah_aktivitas_view(request):
    """Tambah aktivitas harian baru dengan validasi anti-overlap."""
    if request.method == "POST":
        form = AktivitasHarianForm(request.POST)
        tanggal_str = request.POST.get('tanggal', '')
        tanggal = date.today()
        if tanggal_str:
            try:
                tanggal = date.fromisoformat(tanggal_str)
            except ValueError:
                pass

        form.instance.user = request.user
        form.instance.tanggal = tanggal

        def _save_form_to_session():
            request.session['agenda_form_data'] = {
                'judul': request.POST.get('judul', ''),
                'jam_mulai': request.POST.get('jam_mulai', ''),
                'durasi_menit': request.POST.get('durasi_menit', ''),
                'is_habit': 'is_habit' in request.POST,
            }

        if form.is_valid():
            try:
                saved_item = form.save()
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    all_akt = AktivitasHarian.objects.filter(user=request.user, tanggal=tanggal)
                    total = all_akt.count()
                    selesai = all_akt.filter(status='selesai').count()
                    persen = round((selesai / total) * 100, 1) if total > 0 else 0
                    return JsonResponse({
                        'success': True,
                        'message': f"Aktivitas '{saved_item.judul}' berhasil ditambahkan!",
                        'id': saved_item.id,
                        'judul': saved_item.judul,
                        'jam_mulai': saved_item.jam_mulai.strftime('%H:%M'),
                        'jam_selesai': saved_item.jam_selesai.strftime('%H:%M') if saved_item.jam_selesai else '',
                        'durasi_menit': saved_item.durasi_menit,
                        'is_habit': saved_item.is_habit,
                        'status': saved_item.status,
                        'total': total,
                        'selesai': selesai,
                        'persen': persen,
                    })
                messages.success(request, f"Aktivitas '{saved_item.judul}' berhasil ditambahkan!")
            except ValidationError as e:
                error_msg = "; ".join(e.messages) if hasattr(e, 'messages') else str(e)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                messages.error(request, error_msg)
                _save_form_to_session()
        else:
            errors_list = []
            for field, errors in form.errors.items():
                for error in errors:
                    prefix = "" if field == "__all__" else f"{field.capitalize()}: "
                    errors_list.append(f"{prefix}{error}")
            error_msg = "; ".join(errors_list)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg}, status=400)
            for field, errors in form.errors.items():
                for error in errors:
                    prefix = "" if field == "__all__" else f"{field.capitalize()}: "
                    messages.error(request, f"{prefix}{error}")
            _save_form_to_session()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect(f"/tugas/agenda/?tanggal={tanggal.isoformat()}")

    return redirect("tugas:agenda")


@login_required
@require_POST
def toggle_aktivitas_view(request, aktivitas_id):
    """Toggle atau ubah status aktivitas (AJAX-friendly)."""
    aktivitas = get_object_or_404(AktivitasHarian, id=aktivitas_id, user=request.user)

    target_status = None
    try:
        data = json.loads(request.body)
        target_status = data.get('status')
    except (json.JSONDecodeError, ValueError, AttributeError):
        pass

    if target_status in ['belum', 'selesai', 'terlewat']:
        if aktivitas.status == 'selesai' and target_status == 'terlewat':
            return JsonResponse({
                'success': False,
                'error': 'Aktivitas yang sudah selesai tidak boleh ditandai terlewat.'
            }, status=400)
        aktivitas.status = target_status
    else:
        if aktivitas.status == 'selesai':
            aktivitas.status = 'belum'
        else:
            aktivitas.status = 'selesai'

    aktivitas.save(update_fields=['status', 'updated_at'])

    tanggal = aktivitas.tanggal
    all_akt = AktivitasHarian.objects.filter(user=request.user, tanggal=tanggal)
    total = all_akt.count()
    selesai = all_akt.filter(status='selesai').count()
    persen = round((selesai / total) * 100, 1) if total > 0 else 0

    return JsonResponse({
        'success': True,
        'status': aktivitas.status,
        'total': total,
        'selesai': selesai,
        'persen': persen,
    })


@login_required
def edit_aktivitas_view(request, aktivitas_id):
    """Edit data aktivitas harian — hanya mengubah objek tunggal berdasarkan pk."""
    aktivitas = get_object_or_404(AktivitasHarian, id=aktivitas_id, user=request.user)
    if request.method == "POST":
        form = AktivitasHarianForm(request.POST, instance=aktivitas)
        form.instance.user = request.user
        form.instance.tanggal = aktivitas.tanggal

        if form.is_valid():
            try:
                saved_instance = form.save()
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    all_akt = AktivitasHarian.objects.filter(user=request.user, tanggal=aktivitas.tanggal)
                    total = all_akt.count()
                    selesai = all_akt.filter(status='selesai').count()
                    persen = round((selesai / total) * 100, 1) if total > 0 else 0
                    return JsonResponse({
                        'success': True,
                        'message': f"Aktivitas '{saved_instance.judul}' berhasil diperbarui!",
                        'id': saved_instance.id,
                        'judul': saved_instance.judul,
                        'jam_mulai': saved_instance.jam_mulai.strftime('%H:%M'),
                        'jam_selesai': saved_instance.jam_selesai.strftime('%H:%M') if saved_instance.jam_selesai else '',
                        'durasi_menit': saved_instance.durasi_menit,
                        'is_habit': saved_instance.is_habit,
                        'status': saved_instance.status,
                        'total': total,
                        'selesai': selesai,
                        'persen': persen,
                    })
                messages.success(request, f"Aktivitas '{saved_instance.judul}' berhasil diperbarui!")
            except ValidationError as e:
                error_msg = "; ".join(e.messages) if hasattr(e, 'messages') else str(e)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                messages.error(request, error_msg)
        else:
            errors_list = []
            for field, errors in form.errors.items():
                for error in errors:
                    prefix = "" if field == "__all__" else f"{field.capitalize()}: "
                    errors_list.append(f"{prefix}{error}")
            error_msg = "; ".join(errors_list)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg}, status=400)
            for field, errors in form.errors.items():
                for error in errors:
                    prefix = "" if field == "__all__" else f"{field.capitalize()}: "
                    messages.error(request, f"{prefix}{error}")

        return redirect(f"/tugas/agenda/?tanggal={aktivitas.tanggal.isoformat()}")

    return redirect("tugas:agenda")


@login_required
@require_POST
def hapus_aktivitas_view(request, aktivitas_id):
    """Hapus aktivitas harian."""
    aktivitas = get_object_or_404(AktivitasHarian, id=aktivitas_id, user=request.user)
    tanggal = aktivitas.tanggal
    judul = aktivitas.judul
    aktivitas.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        all_akt = AktivitasHarian.objects.filter(user=request.user, tanggal=tanggal)
        total = all_akt.count()
        selesai = all_akt.filter(status='selesai').count()
        persen = round((selesai / total) * 100, 1) if total > 0 else 0
        return JsonResponse({
            'success': True,
            'message': f"Aktivitas '{judul}' berhasil dihapus!",
            'total': total,
            'selesai': selesai,
            'persen': persen,
        })
    messages.success(request, f"Aktivitas '{judul}' berhasil dihapus!")
    return redirect(f"/tugas/agenda/?tanggal={tanggal.isoformat()}")


@login_required
def api_jadwal_hari_ini(request):
    """API endpoint: return jadwal hari ini berstatus 'belum' untuk notifikasi pengingat."""
    today = date.today()
    aktivitas = AktivitasHarian.objects.filter(
        user=request.user,
        tanggal=today,
        status='belum',
    ).order_by('jam_mulai')

    kegiatan = Kegiatan.objects.filter(
        user=request.user,
        tanggal=today,
        status='akan_datang',
    ).order_by('jam_mulai')

    items = []
    for akt in aktivitas:
        items.append({
            'judul': akt.judul,
            'jam_mulai': akt.jam_mulai.strftime('%H:%M'),
            'type': 'aktivitas',
        })
    for keg in kegiatan:
        items.append({
            'judul': keg.judul,
            'jam_mulai': keg.jam_mulai.strftime('%H:%M'),
            'type': 'kegiatan',
        })

    items.sort(key=lambda x: x['jam_mulai'])
    return JsonResponse({'items': items})


@login_required
@require_POST
def copy_jadwal_kemarin_view(request):
    """Copy jadwal dari hari kemarin ke tanggal target."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Data tidak valid.'}, status=400)

    tanggal_str = data.get('tanggal', date.today().isoformat())
    try:
        tanggal_target = date.fromisoformat(tanggal_str)
    except ValueError:
        tanggal_target = date.today()

    aktivitas_items = data.get('aktivitas', [])
    created_count = 0
    skipped_count = 0

    for item in aktivitas_items:
        judul = item.get('judul', '').strip()
        jam_mulai_str = item.get('jam_mulai', '')
        durasi_menit = item.get('durasi_menit', 30)
        is_habit = item.get('is_habit', False)

        if not judul or not jam_mulai_str:
            continue

        try:
            jam_mulai = dt_time.fromisoformat(jam_mulai_str)
        except ValueError:
            continue

        try:
            durasi_int = int(durasi_menit)
        except (ValueError, TypeError):
            durasi_int = 30

        try:
            AktivitasHarian.objects.create(
                user=request.user,
                judul=judul,
                jam_mulai=jam_mulai,
                durasi_menit=durasi_int,
                is_habit=is_habit,
                tanggal=tanggal_target,
                status='belum',
            )
            created_count += 1
        except ValidationError:
            skipped_count += 1

    return JsonResponse({
        'success': True,
        'created': created_count,
        'skipped': skipped_count,
        'message': f'{created_count} aktivitas berhasil disalin.'
                   + (f' {skipped_count} dilewati karena jadwal bertabrakan.' if skipped_count > 0 else ''),
    })
