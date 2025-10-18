@echo off
cd C:\Application\Django\manajemen_tugas  REM Sesuaikan dengan lokasi proyek kamu
call venv\Scripts\activate  REM Aktifkan virtual environment jika ada
python kirim_email.py  REM Jalankan skrip Python
