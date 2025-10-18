from django import forms
from .models import Tugas
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.contrib.auth.forms import AuthenticationForm

# Form Login
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan username'}),
        label="Username"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan password'}),
        label="Password"
    )

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError("Akun ini tidak aktif. Hubungi admin.")
    
    def get_invalid_login_error(self):
        return forms.ValidationError("Username atau password salah. Periksa kembali huruf besar/kecil.")

# Form Registrasi
class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan password'}),
        label="Password"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Konfirmasi password'}),
        label="Konfirmasi Password"
    )

    class Meta:
        model = User
        fields = ["username", "email"]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan email'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Password tidak cocok!")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  # Enkripsi password sebelum disimpan
        if commit:
            user.save()
        return user

# Form Tugas
class TugasForm(forms.ModelForm):
    class Meta:
        model = Tugas
        fields = ['judul', 'deskripsi', 'deadline', 'prioritas', 'kategori', 'status']
        widgets = {
            'judul': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan judul tugas'}),
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Tambahkan deskripsi tugas', 'rows': 3}),
            'deadline': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format="%Y-%m-%dT%H:%M"  # Format yang sesuai untuk input HTML5
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
