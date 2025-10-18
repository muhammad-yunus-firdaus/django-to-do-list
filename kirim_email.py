import os
import django
from datetime import timedelta
from django.core.mail import send_mail
from django.utils.timezone import now, localtime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manajemen_tugas.settings')
django.setup()

from django.conf import settings
from tugas.models import Tugas

# Ambil waktu sekarang dalam UTC
sekarang_utc = now()
batas_waktu_utc = sekarang_utc + timedelta(days=1)

print(f"🔍 [DEBUG] Mencari tugas dengan deadline antara {sekarang_utc} - {batas_waktu_utc} (UTC)")

# Debug: Cek semua tugas dalam database
print("📋 [DEBUG] Semua tugas dalam database:")
for tugas in Tugas.objects.all():
    print(f"📝 {tugas.judul} | Deadline (UTC): {tugas.deadline} | Deadline (WIB): {localtime(tugas.deadline)} | Status: {tugas.status}")

# Query untuk mencari tugas mendekati deadline
tugas_mendekati_deadline = Tugas.objects.filter(
    deadline__gte=sekarang_utc,
    deadline__lte=batas_waktu_utc,
    status__iexact="belum"  # UBAH DI SINI agar sesuai dengan yang ada di database
)

# Debug: Apakah ada tugas yang ditemukan?
if not tugas_mendekati_deadline.exists():
    print("🚨 [WARNING] Tidak ada tugas mendekati deadline.")
else:
    print(f"✅ [INFO] Ditemukan {tugas_mendekati_deadline.count()} tugas yang mendekati deadline.")

    for tugas in tugas_mendekati_deadline:
        deadline_wib = localtime(tugas.deadline)
        subject = f"Reminder: Tugas '{tugas.judul}' akan segera jatuh tempo!"
        message = (
            f"Halo,\n\n"
            f"Tugas '{tugas.judul}' memiliki deadline pada {deadline_wib.strftime('%d-%m-%Y %H:%M')} WIB.\n"
            f"Segera selesaikan agar tidak terlambat!\n\n"
            f"Terima kasih.\n"
        )
        recipient_list = [tugas.user.email]

        print(f"📧 [INFO] Mengirim email ke {recipient_list}...")

        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,  
                recipient_list,
                fail_silently=False,
            )
            print(f"✅ [SUCCESS] Email terkirim ke {recipient_list}")
        except Exception as e:
            print(f"❌ [ERROR] Gagal mengirim email ke {recipient_list}: {e}")

print("✅ [INFO] Proses kirim email selesai!")
