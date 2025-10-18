from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse_lazy
from django.http import HttpResponse
from .models import Tugas
from .forms import TugasForm, RegisterForm, CustomAuthenticationForm
from openpyxl import Workbook
from openpyxl.styles.borders import Border, Side 
from openpyxl.styles import Font, Alignment, PatternFill
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.utils.timezone import now, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
import csv

User = get_user_model()

# Konstanta status tugas
STATUS_SELESAI = "selesai"
STATUS_BELUM = "belum"

# Halaman utama
def index(request):
    return render(request, "tugas/index.html")

#  Login
def login_view(request):
    if request.user.is_authenticated:
        return redirect("tugas:dashboard")

    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)  # ← tambahkan "request" di sini!
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Login berhasil! Selamat datang, {user.username}.")
            return redirect(request.GET.get("next") or "tugas:dashboard")
        else:
            messages.error(request, "Username atau password salah.")
    else:
        form = CustomAuthenticationForm(request)  # ← tambahkan juga "request" di sini

    return render(request, "tugas/login.html", {"form": form})


# Logout
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Kamu telah logout.")
    return redirect("tugas:login")

#  Register
def register(request):
    if request.user.is_authenticated:
        return redirect("tugas:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, "Registrasi berhasil! Silakan login terlebih dahulu.")
            return redirect("tugas:login")
    else:
        form = RegisterForm()
    
    return render(request, "tugas/register.html", {"form": form})

#  Fungsi filter & pencarian tugas
def get_filtered_tugas(request, tugas_list):
    prioritas_filter = request.GET.get('prioritas', '')
    kategori_filter = request.GET.get('kategori', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')

    if prioritas_filter:
        tugas_list = tugas_list.filter(prioritas=prioritas_filter)
    if kategori_filter:
        tugas_list = tugas_list.filter(kategori=kategori_filter)
    if status_filter:
        tugas_list = tugas_list.filter(status=status_filter)
    if search_query:
        tugas_list = tugas_list.filter(
            Q(judul__icontains=search_query) | Q(deskripsi__icontains=search_query)
        )

    return tugas_list

#  Daftar tugas dengan filter & pencarian
@login_required
def daftar_tugas(request):
    tugas_list = Tugas.objects.filter(user=request.user)
    tugas_list = get_filtered_tugas(request, tugas_list)

    kategori_list = [kategori[0] for kategori in Tugas.KATEGORI_CHOICES]

    context = {
        "tugas_list": tugas_list,
        "kategori_list": kategori_list,
        "prioritas_filter": request.GET.get('prioritas', ''),
        "kategori_filter": request.GET.get('kategori', ''),
        "status_filter": request.GET.get('status', ''),
        "search_query": request.GET.get('q', ''),
    }
    return render(request, "tugas/daftar_tugas.html", context)

#  Tambah tugas
@login_required
def tambah_tugas(request):
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

#  Edit tugas
@login_required
def edit_tugas(request, tugas_id):
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)

    if request.method == "POST":
        form = TugasForm(request.POST, instance=tugas)
        if form.is_valid():
            updated_tugas = form.save(commit=False)
            
            # Pastikan field yang tidak diubah (seperti deadline) tetap dipertahankan
            if not form.cleaned_data.get("deadline"):
                updated_tugas.deadline = tugas.deadline

            updated_tugas.save()
            messages.success(request, "Tugas berhasil diperbarui!")
            return redirect("tugas:daftar")
        else:
            messages.error(request, "Terjadi kesalahan saat memperbarui tugas. Periksa kembali form kamu.")
    else:
        form = TugasForm(instance=tugas)
    
    return render(request, "tugas/edit_tugas.html", {"form": form})


#  Hapus tugas
@login_required
def hapus_tugas(request, tugas_id):
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)
    
    if request.method == "POST":
        tugas.delete()
        messages.success(request, "Tugas berhasil dihapus!")
        return redirect("tugas:daftar")

    return render(request, "tugas/konfirmasi_hapus.html", {"tugas": tugas})

#  Tandai tugas selesai
@login_required
def tandai_selesai(request, tugas_id):
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)
    
    if tugas.status == STATUS_SELESAI:
        messages.warning(request, "Tugas ini sudah selesai sebelumnya!")
    else:
        tugas.status = STATUS_SELESAI
        tugas.save()
        messages.success(request, f"Tugas '{tugas.judul}' telah selesai!")

    return redirect("tugas:daftar")

#  Halaman Dashboard dengan statistik tugas
@login_required
def dashboard_view(request):
    tugas_user = Tugas.objects.filter(user=request.user)

    # Hitung tugas selesai & belum selesai
    tugas_selesai = tugas_user.filter(status="selesai").count()
    tugas_belum_selesai = tugas_user.filter(status="belum").count()
    total_tugas = tugas_user.count()
    
    # Hitung persentase
    if total_tugas > 0:
        persentase_selesai = (tugas_selesai / total_tugas) * 100
        persentase_belum_selesai = 100 - persentase_selesai
    else:
        persentase_selesai = 0
        persentase_belum_selesai = 0

    #  Ambil tugas dengan deadline terdekat
    tugas_deadline_terdekat = tugas_user.filter(status="belum").order_by("deadline")[:5]

    #  Ambil tugas dengan prioritas tinggi
    prioritas_tinggi = tugas_user.filter(
    prioritas__iexact="Tinggi",
    status="belum"
    ).order_by("deadline")[:5]

    #  Notifikasi untuk tugas mendekati deadline
    tugas_mendekati_deadline = tugas_user.filter(
        status="belum",
        deadline__gt=now(),
        deadline__lte=now() + timedelta(days=2)
    )
    if tugas_mendekati_deadline.exists():
        messages.warning(request, "⚠️ Ada tugas yang mendekati deadline! Segera selesaikan.")

    #  Kirim semua data ke template
    context = {
        "tugas_selesai": tugas_selesai,
        "tugas_belum_selesai": tugas_belum_selesai,
        "total_tugas": total_tugas,
        "persentase_selesai": persentase_selesai,
        "persentase_belum_selesai": persentase_belum_selesai,
        "tugas_deadline_terdekat": tugas_deadline_terdekat,
        "prioritas_tinggi": prioritas_tinggi,  # <--- ini dia kuncinya
    }

    return render(request, "tugas/dashboard.html", context)


#  Detail tugas dengan validasi pengguna
@login_required
def detail_tugas(request, tugas_id):
    tugas = get_object_or_404(Tugas, id=tugas_id, user=request.user)
    return render(request, "tugas/detail_tugas.html", {"tugas": tugas})

@login_required
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tugas.csv"'

    writer = csv.writer(response)
    writer.writerow(['Judul', 'Kategori', 'Prioritas', 'Deadline', 'Status'])

    tugas_list = Tugas.objects.filter(user=request.user)
    for tugas in tugas_list:
        writer.writerow([
            tugas.judul,
            tugas.get_kategori_display(),
            tugas.prioritas,
            tugas.deadline.strftime("%d-%m-%Y %H:%M"),
            "Selesai" if tugas.status == STATUS_SELESAI else "Belum Selesai"
        ])

    return response

#  Export data tugas ke Excel (.xlsx)
@login_required
def export_excel(request):
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="tugas.xlsx"'

    # Buat workbook dan sheet
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Daftar Tugas"

    #  Styling Header
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    border_style = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    headers = ["Judul", "Kategori", "Prioritas", "Deadline", "Status"]
    sheet.append(headers)

    # Terapkan styling ke header
    for col_idx, cell in enumerate(sheet[1], 1):
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_style

    #  Ambil data tugas berdasarkan user
    tugas_list = Tugas.objects.filter(user=request.user)

    #  Tambahkan data ke dalam sheet
    for row_idx, tugas in enumerate(tugas_list, start=2):  # Mulai dari baris kedua
        status_text = "Selesai" if tugas.status == STATUS_SELESAI else "Belum Selesai"
        deadline_str = tugas.deadline.strftime("%d-%m-%Y %H:%M") if tugas.deadline else "N/A"

        data_row = [
            tugas.judul,
            tugas.get_kategori_display(),
            tugas.get_prioritas_display() if hasattr(tugas, "get_prioritas_display") else tugas.prioritas,
            deadline_str,
            status_text
        ]
        sheet.append(data_row)

        # Terapkan border ke setiap sel di baris ini
        for col_idx, cell in enumerate(sheet[row_idx], 1):
            cell.alignment = Alignment(horizontal="left", vertical="center")
            cell.border = border_style

    #  Mengatur lebar kolom otomatis
    for col in sheet.columns:
        max_length = 0
        col_letter = col[0].column_letter  # Mendapatkan huruf kolom (A, B, C, dll.)
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        sheet.column_dimensions[col_letter].width = max_length + 2

    # Simpan workbook ke response
    workbook.save(response)
    return response

@login_required
def export_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="tugas.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []
    
    # Gunakan style untuk teks agar bisa wrap
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]

    # Header tabel
    data = [["Judul", "Deskripsi", "Kategori", "Prioritas", "Deadline", "Status"]]

    # Ambil data tugas dari user
    tugas_list = Tugas.objects.filter(user=request.user)

    for tugas in tugas_list:
        judul_paragraph = Paragraph(tugas.judul, style_normal)  # Wrap text pada Judul
        deskripsi_paragraph = Paragraph(tugas.deskripsi, style_normal)  # Wrap text pada Deskripsi
        deadline_str = tugas.deadline.strftime("%d-%m-%Y %H:%M") if tugas.deadline else "N/A"
        status_text = "Selesai" if tugas.status == STATUS_SELESAI else "Belum Selesai"

        data.append([
            judul_paragraph,   # ✅ Wrap text pada Judul
            deskripsi_paragraph,  # ✅ Wrap text pada Deskripsi
            tugas.get_kategori_display(),
            tugas.prioritas,
            deadline_str,
            status_text
        ])

    # Membuat tabel dengan kolom lebih fleksibel
    table = Table(data, colWidths=[150, 250, 100, 80, 120, 100])  # Lebar kolom Judul diperbesar
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),  # Agar teks tetap rata atas
    ]))

    elements.append(table)
    doc.build(elements)

    return response

    # Buat tabel dengan kolom lebih fleksibel
    table = Table(data, colWidths=[100, 250, 100, 80, 120, 100])  # Sesuaikan ukuran kolom
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (1, 1), (-1, -1), 'TOP'),  # Agar teks deskripsi tetap dari atas
    ]))

    elements.append(table)
    doc.build(elements)

    return response

@login_required
def get_filtered_tugas(request, tugas_list):
    prioritas_filter = request.GET.get("prioritas", "")
    kategori_filter = request.GET.get("kategori", "")
    status_filter = request.GET.get("status", "")
    search_query = request.GET.get("q", "")

    if prioritas_filter:
        tugas_list = tugas_list.filter(prioritas=prioritas_filter)
    
    if kategori_filter:
        tugas_list = tugas_list.filter(kategori=kategori_filter)

    if status_filter:
        tugas_list = tugas_list.filter(status=status_filter)

    # 🔍 Filter berdasarkan pencarian (judul atau kategori)
    if search_query:
        tugas_list = tugas_list.filter(
            Q(judul__icontains=search_query) | Q(kategori__icontains=search_query)
        )

    return tugas_list


def kirim_reminder_tugas():
    batas_waktu = now() + timedelta(days=1)  # Tugas yang deadline-nya dalam 1 hari ke depan
    tugas_mendekati = Tugas.objects.filter(deadline__lte=batas_waktu, status="Belum Selesai")

    for tugas in tugas_mendekati:
        user_email = tugas.user.email  # Asumsikan setiap tugas punya relasi ke User
        send_mail(
            'Reminder: Tugas Mendekati Deadline!',
            f'Halo {tugas.user.username}, tugas "{tugas.judul}" memiliki deadline {tugas.deadline.strftime("%d-%m-%Y %H:%M")}. Jangan lupa untuk menyelesaikannya!',
            'yunusproject14@gmail.com',  # Ganti dengan email pengirimmu
            [user_email],  # Kirim ke email pemilik tugas
            fail_silently=False,
            headers={'Reply-To': 'yunusproject14@gmail.com'}
        )