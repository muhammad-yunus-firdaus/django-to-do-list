from django import forms
from .models import Tugas, Subtask, AktivitasHarian, EvaluasiMingguan
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.contrib.auth.forms import AuthenticationForm


class CustomAuthenticationForm(AuthenticationForm):
    # Form login custom, cuma username sama password
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan username',
            'autocomplete': 'username',
        }),
        label="Username"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan password',
            'autocomplete': 'current-password',
        }),
        label="Password"
    )

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError("Akun ini tidak aktif. Hubungi admin.")

    def get_invalid_login_error(self):
        return forms.ValidationError(
            "Username atau password salah. Periksa kembali huruf besar/kecil."
        )


class RegisterForm(forms.Form):
    # Form daftar akun baru, username harus unik, tanpa email
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan username',
            'autocomplete': 'username',
        }),
        label="Username",
        help_text="Username harus unik dan maksimal 150 karakter."
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan password',
            'autocomplete': 'new-password',
        }),
        label="Password",
        min_length=8,
        help_text="Password minimal 8 karakter."
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Konfirmasi password',
            'autocomplete': 'new-password',
        }),
        label="Konfirmasi Password"
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "Username ini sudah digunakan. Silakan pilih username lain."
            )
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Password tidak cocok!")

        return cleaned_data

    def save(self):
        # Bikin user baru, passwordnya otomatis di-hash biar aman
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password"],
        )
        return user


class TugasForm(forms.ModelForm):
    # Form buat bikin dan edit tugas
    class Meta:
        model = Tugas
        fields = ['judul', 'deskripsi', 'deadline', 'prioritas', 'kategori', 'status']
        widgets = {
            'judul': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masukkan judul tugas',
            }),
            'deskripsi': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Tambahkan deskripsi tugas',
                'rows': 3,
            }),
            'deadline': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format="%Y-%m-%dT%H:%M"
            ),
            'prioritas': forms.Select(attrs={'class': 'form-select'}),
            'kategori': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data.get("deadline")

        if not deadline:
            raise forms.ValidationError("Deadline tidak boleh kosong!")

        if deadline < now():
            raise forms.ValidationError("Deadline harus di masa depan!")

        return deadline


class SubtaskForm(forms.ModelForm):
    # Form buat bikin dan edit subtask
    class Meta:
        model = Subtask
        fields = ['judul']
        widgets = {
            'judul': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masukkan judul subtask...',
                'autofocus': True,
            }),
        }
        labels = {
            'judul': 'Subtask',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['judul'].required = True


# ══════════════════════════════════════════════════════════════════════
# PROFIL - Edit Username, Email, dan Password
# ══════════════════════════════════════════════════════════════════════

class ProfilForm(forms.Form):
    """Form untuk mengubah Username & Email user."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan username baru',
            'autocomplete': 'username',
        }),
        label="Username",
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan email (opsional)',
            'autocomplete': 'email',
        }),
        label="Email",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email or ''

    def clean_username(self):
        username = self.cleaned_data.get("username")
        # Cek duplikat, kecuali username sendiri
        if User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Username ini sudah digunakan oleh user lain.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            # Cek duplikat email, kecuali email sendiri
            if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
                raise forms.ValidationError("Email ini sudah digunakan oleh user lain.")
        return email

    def save(self):
        self.user.username = self.cleaned_data["username"]
        self.user.email = self.cleaned_data.get("email", "")
        self.user.save(update_fields=["username", "email"])
        return self.user


class GantiPasswordForm(forms.Form):
    """Form untuk mengubah Password dengan verifikasi password lama."""
    password_lama = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan password lama',
            'autocomplete': 'current-password',
        }),
        label="Password Lama",
    )
    password_baru = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan password baru (min. 8 karakter)',
            'autocomplete': 'new-password',
        }),
        label="Password Baru",
    )
    password_konfirmasi = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Konfirmasi password baru',
            'autocomplete': 'new-password',
        }),
        label="Konfirmasi Password Baru",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password_lama(self):
        password_lama = self.cleaned_data.get("password_lama")
        if not self.user.check_password(password_lama):
            raise forms.ValidationError("Password lama salah!")
        return password_lama

    def clean(self):
        cleaned_data = super().clean()
        baru = cleaned_data.get("password_baru")
        konfirmasi = cleaned_data.get("password_konfirmasi")

        if baru and konfirmasi and baru != konfirmasi:
            raise forms.ValidationError("Password baru dan konfirmasi tidak cocok!")

        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data["password_baru"])
        self.user.save()
        return self.user


# ══════════════════════════════════════════════════════════════════════
# AKTIVITAS HARIAN - Form Time-Blocking
# ══════════════════════════════════════════════════════════════════════

class AktivitasHarianForm(forms.ModelForm):
    """Form untuk input aktivitas harian / time-blocking."""
    class Meta:
        model = AktivitasHarian
        fields = ['judul', 'jam_mulai', 'durasi_menit', 'is_habit']
        widgets = {
            'judul': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Judul aktivitas...',
            }),
            'jam_mulai': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'durasi_menit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Durasi (menit)',
                'min': '5',
                'max': '480',
            }),
            'is_habit': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
        }
        labels = {
            'judul': 'Aktivitas',
            'jam_mulai': 'Jam Mulai',
            'durasi_menit': 'Durasi (Menit)',
            'is_habit': 'Ulangi Setiap Hari',
        }


# ══════════════════════════════════════════════════════════════════════
# EVALUASI MINGGUAN - Form Catatan Refleksi
# ══════════════════════════════════════════════════════════════════════

class EvaluasiForm(forms.Form):
    """Form untuk input catatan evaluasi mingguan."""
    catatan_evaluasi = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Tulis refleksi dan evaluasi kamu untuk minggu ini...\n\nContoh:\n- Apa yang sudah berjalan baik?\n- Apa yang perlu diperbaiki?\n- Target untuk minggu depan?',
            'rows': 6,
        }),
        label="Catatan Evaluasi",
    )

