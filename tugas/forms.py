from django import forms
from .models import Tugas, Subtask
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
