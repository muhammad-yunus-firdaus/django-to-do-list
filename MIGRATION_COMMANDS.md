# Migration Commands

Setelah model Notification dibuat, jalankan command berikut:

```bash
# Activate virtual environment
& c:\Application\Django\manajemen_tugas\env\Scripts\Activate.ps1

# Generate migration
python manage.py makemigrations

# Apply migration
python manage.py migrate
```

Setelah migration selesai, lanjutkan development notification system.
