"""
tugas/views/auth_views.py
View controller untuk autentikasi user: login, logout, registrasi, dan edit profil.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from ..forms import CustomAuthenticationForm, RegisterForm, ProfilForm, GantiPasswordForm


def login_view(request):
    """Halaman login user, auto redirect ke dashboard jika sudah login."""
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
    """Logout user dan arahkan kembali ke halaman login."""
    logout(request)
    messages.info(request, "Kamu telah logout.")
    return redirect("tugas:login")


def register(request):
    """Halaman pendaftaran akun baru."""
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


@login_required
def edit_profil_view(request):
    """Halaman edit profil: ubah username/email dan ganti password."""
    user = request.user
    profil_form = ProfilForm(user=user)
    password_form = GantiPasswordForm(user=user)
    profil_success = False
    password_success = False

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "update_profil":
            profil_form = ProfilForm(request.POST, user=user)
            if profil_form.is_valid():
                profil_form.save()
                messages.success(request, "Profil berhasil diperbarui!")
                profil_success = True
                return redirect("tugas:edit_profil")
            else:
                messages.error(request, "Gagal memperbarui profil. Periksa kembali data kamu.")

        elif action == "update_password":
            password_form = GantiPasswordForm(request.POST, user=user)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password berhasil diubah!")
                password_success = True
                return redirect("tugas:edit_profil")
            else:
                messages.error(request, "Gagal mengubah password. Periksa kembali data kamu.")

    context = {
        "profil_form": profil_form,
        "password_form": password_form,
        "profil_success": profil_success,
        "password_success": password_success,
    }
    return render(request, "tugas/edit_profil.html", context)
