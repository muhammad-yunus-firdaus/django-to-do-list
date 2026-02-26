from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Tugas, Subtask
from .forms import TugasForm, RegisterForm, CustomAuthenticationForm, SubtaskForm
from .notifications import check_subtask_completion, generate_deadline_notifications, generate_overdue_notifications
from .services import (
    get_dashboard_stats,
    get_upcoming_deadlines,
    get_high_priority_tasks,
    get_approaching_deadline_tasks,
    get_overdue_tasks,
    get_filtered_tugas,
    mark_task_complete,
    get_export_data,
)


# ══════════════════════════════════════════════════════════════════════
# AUTH - Login, Logout, Register
# ══════════════════════════════════════════════════════════════════════

def login_view(request):
    # Halaman login, auto redirect ke dashboard kalo udah login
    if request.user.is_authenticated:
        return redirect("tugas:dashboard")

    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Login berhasil! Selamat datang, {user.username}.")
            return redirect(request.GET.get("next") or "tugas:dashboard")
        else:
            messages.error(request, "Username atau password salah.")
    else:
        form = CustomAuthenticationForm(request)

    return render(request, "tugas/login.html", {"form": form})


@login_required
def logout_view(request):
    # Logout user terus balik ke halaman login
    logout(request)
    messages.info(request, "Kamu telah logout.")
    return redirect("tugas:login")


def register(request):
    # Halaman daftar akun baru, cuma pake username doang tanpa email
    if request.user.is_authenticated:
        return redirect("tugas:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registrasi berhasil! Silakan login terlebih dahulu.")
            return redirect("tugas:login")
    else:
        form = RegisterForm()

    return render(request, "tugas/register.html", {"form": form})


# ══════════════════════════════════════════════════════════════════════
# DASHBOARD - Statistik & Overview
# ══════════════════════════════════════════════════════════════════════

@login_required
def dashboard_view(request):
    # Halaman utama setelah login, nampilin semua statistik tugas
    user = request.user

    # Ambil semua data statistik dari service layer
    stats = get_dashboard_stats(user)
    tugas_deadline_terdekat = get_upcoming_deadlines(user)
    prioritas_tinggi = get_high_priority_tasks(user)
    tugas_mendekati_deadline = get_approaching_deadline_tasks(user)
    tugas_overdue = get_overdue_tasks(user)

    # Generate notifikasi otomatis waktu buka dashboard
    generate_deadline_notifications()
    generate_overdue_notifications()

    # NOTE: Django messages udah ga dipake lagi, sekarang pake notification system
    # if tugas_mendekati_deadline.exists():
    #     messages.warning(
    #         request,
    #         f"Ada {tugas_mendekati_deadline.count()} tugas yang mendekati deadline (kurang dari 2 hari)!"
    #     )

    # if tugas_overdue.exists():
    #     messages.error(
    #         request,
    #         f"Ada {tugas_overdue.count()} tugas yang sudah melewati deadline!"
    #     )

    context = {
        **stats,
        "tugas_deadline_terdekat": tugas_deadline_terdekat,
        "prioritas_tinggi": prioritas_tinggi,
        "tugas_mendekati_deadline": tugas_mendekati_deadline,
        "tugas_overdue": tugas_overdue,
    }

    return render(request, "tugas/dashboard.html", context)


# ══════════════════════════════════════════════════════════════════════
# CRUD TUGAS - Create, Read, Update, Delete
# ══════════════════════════════════════════════════════════════════════

@login_required
def daftar_tugas(request):
    # Nampilin semua tugas punya user ini, bisa di-filter dan di-search
    filters = {
        "prioritas": request.GET.get("prioritas", ""),
        "kategori": request.GET.get("kategori", ""),
        "status": request.GET.get("status", ""),
        "q": request.GET.get("q", ""),
    }

    tugas_list = get_filtered_tugas(request.user, filters)
    kategori_list = [k[0] for k in Tugas.KATEGORI_CHOICES]

    # Buat pagination biar ga terlalu banyak di satu halaman
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
    # Form buat bikin tugas baru
    if request.method == "POST":
        form = TugasForm(request.POST)
        if form.is_valid():
            tugas = form.save(commit=False)
            tugas.user = request.user
            tugas.save()
            messages.success(request, "Tugas berhasil ditambahkan!")
            return redirect("tugas:daftar")
    else:
        form = TugasForm()

    return render(request, "tugas/tambah_tugas.html", {"form": form})


@login_required
def edit_tugas(request, tugas_id):
    # Form buat edit tugas yang udah ada
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
    # Hapus tugas, cuma bisa lewat POST biar aman
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)
    tugas.delete()
    messages.success(request, "Tugas berhasil dihapus!")
    return redirect("tugas:daftar")


@login_required
@require_POST
def tandai_selesai(request, tugas_id):
    # Tandain tugas jadi selesai, cuma bisa lewat POST
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)

    if mark_task_complete(tugas):
        messages.success(request, f"Tugas '{tugas.judul}' telah selesai!")
    else:
        messages.warning(request, "Tugas ini sudah selesai sebelumnya!")

    return redirect("tugas:daftar")


@login_required
def detail_tugas(request, tugas_id):
    # Halaman detail tugas, nampilin info lengkap sama subtask-nya
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)
    return render(request, "tugas/detail_tugas.html", {"tugas": tugas})


# ══════════════════════════════════════════════════════════════════════
# EXPORT - CSV, Excel, PDF
# ══════════════════════════════════════════════════════════════════════

@login_required
def export_csv(request):
    # Download semua tugas dalam format CSV
    import csv

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tugas.csv"'

    writer = csv.writer(response)
    writer.writerow(['Judul', 'Kategori', 'Prioritas', 'Deadline', 'Status'])

    for row in get_export_data(request.user):
        writer.writerow([
            row["judul"], row["kategori"], row["prioritas"],
            row["deadline"], row["status"]
        ])

    return response


@login_required
def export_excel(request):
    # Download tugas dalam format Excel (.xlsx) dengan styling
    from openpyxl import Workbook
    from openpyxl.styles.borders import Border, Side
    from openpyxl.styles import Font, Alignment, PatternFill

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="tugas.xlsx"'

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Daftar Tugas"

    # Kasih styling biar lebih rapi
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    border_style = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    headers = ["Judul", "Kategori", "Prioritas", "Deadline", "Status"]
    sheet.append(headers)

    for cell in sheet[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_style

    for row_idx, row in enumerate(get_export_data(request.user), start=2):
        sheet.append([
            row["judul"], row["kategori"], row["prioritas"],
            row["deadline"], row["status"]
        ])
        for cell in sheet[row_idx]:
            cell.alignment = Alignment(horizontal="left", vertical="center")
            cell.border = border_style

    # Atur lebar kolom otomatis sesuai isi
    for col in sheet.columns:
        max_len = max((len(str(c.value or "")) for c in col), default=0)
        sheet.column_dimensions[col[0].column_letter].width = max_len + 2

    workbook.save(response)
    return response


@login_required
def export_pdf(request):
    # Download tugas dalam format PDF dengan tabel rapi
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="tugas.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]

    data = [["Judul", "Deskripsi", "Kategori", "Prioritas", "Deadline", "Status"]]

    for row in get_export_data(request.user):
        data.append([
            Paragraph(row["judul"], style_normal),
            Paragraph(row["deskripsi"], style_normal),
            row["kategori"], row["prioritas"],
            row["deadline"], row["status"],
        ])

    table = Table(data, colWidths=[150, 250, 100, 80, 120, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
    ]))

    doc.build([table])
    return response


# ══════════════════════════════════════════════════════════════════════
# SUBTASK - Kelola Sub-tugas
# ══════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def tambah_subtask(request, tugas_id):
    # Tambahin subtask baru ke dalam tugas
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)
    form = SubtaskForm(request.POST)
    
    if form.is_valid():
        subtask = form.save(commit=False)
        subtask.tugas = tugas
        
        # Kasih nomor urutan otomatis (ambil yang terakhir + 1)
        last_subtask = tugas.subtasks.order_by('-urutan').first()
        subtask.urutan = (last_subtask.urutan + 1) if last_subtask else 1
        
        subtask.save()
        messages.success(request, f"Subtask '{subtask.judul}' berhasil ditambahkan!")
    else:
        messages.error(request, "Gagal menambahkan subtask. Silakan coba lagi.")
    
    return redirect('tugas:detail', tugas_id=tugas.id)


@login_required
@require_POST
def edit_subtask(request, subtask_id):
    # Ubah judul subtask
    subtask = get_object_or_404(Subtask, id=subtask_id, tugas__user=request.user)
    
    judul_baru = request.POST.get('judul', '').strip()
    if judul_baru:
        subtask.judul = judul_baru
        subtask.save()
        messages.success(request, "Subtask berhasil diupdate!")
    else:
        messages.error(request, "Judul subtask tidak boleh kosong.")
    
    return redirect('tugas:detail', tugas_id=subtask.tugas.id)


@login_required
@require_POST
def hapus_subtask(request, subtask_id):
    # Hapus subtask dari tugas
    subtask = get_object_or_404(Subtask, id=subtask_id, tugas__user=request.user)
    tugas_id = subtask.tugas.id
    judul = subtask.judul
    
    subtask.delete()
    messages.success(request, f"Subtask '{judul}' berhasil dihapus!")
    
    return redirect('tugas:detail', tugas_id=tugas_id)


@login_required
@require_POST
def toggle_subtask(request, subtask_id):
    # Toggle centang/uncentang subtask (dipanggil via AJAX)
    from django.http import JsonResponse
    
    subtask = get_object_or_404(Subtask, id=subtask_id, tugas__user=request.user)
    
    subtask.selesai = not subtask.selesai
    subtask.save()
    
    # Cek kalo semua subtask udah selesai, bikin notifikasi
    check_subtask_completion(subtask.tugas)
    
    # Kirim balik response JSON buat update UI
    return JsonResponse({
        'success': True,
        'selesai': subtask.selesai,
        'progress': subtask.tugas.subtask_progress
    })