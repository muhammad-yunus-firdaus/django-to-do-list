# Manajemen Tugas — Modern Task & Productivity Platform

Aplikasi manajemen tugas dan produktivitas harian modern berbasis **Django** dan **Vanilla JavaScript**, dirancang dengan prinsip desain minimalis, cepat, dan berfokus pada alur kerja (*keyboard-first & mobile-first*).

---

## Fitur Utama

### 1. Task & Dynamic Subtask Checklist
- Buat, kelola, dan kategorisasi tugas (**Kuliah**, **Kerja**, **Pribadi**) dengan level prioritas (**Tinggi**, **Sedang**, **Rendah**).
- Checklist subtask interaktif dengan pelacakan persentase progres dinamis tanpa reload halaman.
- Indikator deadline real-time dengan status peringatan *OVERDUE* otomatis.

### 2. Interactive 24-Hour Timeline (Agenda Harian)
- Visualisasi jadwal harian berbasis timeline 24 jam yang rapi dan terstruktur.
- Filter slot waktu (*Semua*, *Hanya Terisi*, *Waktu Luang*).
- **Quick-Fill Slot:** Isi slot waktu kosong secara instan dengan satu klik untuk mempermudah perencanaan agenda.

### 3. Circular Focus Timer (Pomodoro)
- Timer fokus berbasis **Circular SVG Progress Ring** dengan animasi denyut (*pulse-ring*) saat sesi berjalan.
- Preset durasi fleksibel: `10m`, `25m`, `45m`, dan opsi `Custom` (1–120 menit).
- Feedback audio lembut menggunakan **Web Audio API** sintetis (murni kode, tanpa aset file eksternal).

### 4. Global Command Palette (`Ctrl + K` / `Cmd + K`)
- Navigasi instan dan aksi cepat ala Notion & Linear dari halaman mana saja.
- Akses pencarian menu, pembuatan tugas baru, hingga pembukaan Focus Timer secara instan melalui keyboard.

### 5. PWA & Mobile-First Responsive Design
- **Responsive Table-to-Card:** Transformasi otomatis dari tabel desktop multi-kolom menjadi kartu mandiri yang elegan di layar ponsel (< 768px).
- Bottom navigation bar yang ergonomis untuk perangkat mobile.
- Dukungan Progressive Web App (PWA) dengan Service Worker untuk ketahanan offline dan instalasi di layar utama (*Add to Home Screen*).

### 6. Analytics & Multi-Format Export
- Dashboard analitik ringkas dengan ringkasan status tugas harian dan metrik penyelesaian.
- Export laporan ke format **Excel (.xlsx)** berformat rapi, **PDF**, dan **CSV**.

---

## Tech Stack

- **Backend:** Python 3.12, Django 5.x
- **Database:** SQLite3 (development) / PostgreSQL ready
- **Frontend:** Semantic HTML5, Vanilla JavaScript (ES6+ modular), Modern CSS Design Tokens (*Nordic Frost / shadcn style*)
- **Icons & UI Utilities:** [Lucide Icons](https://lucide.dev/), SweetAlert2, Instant.page
- **Testing:** Django TestCase (Automated Endpoint Smoke Testing)

---

## Panduan Instalasi & Menjalankan Lokal

### 1. Clone Repository
```bash
git clone https://github.com/muhammad-yunus-firdaus/django-to-do-list.git
cd django-to-do-list
```

### 2. Buat & Aktifkan Virtual Environment
```bash
# Windows
python -m venv env
env\Scripts\activate

# macOS / Linux
python3 -m venv env
source env/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Migrasi Database & Static Files
```bash
python manage.py migrate
```

### 5. Jalankan Endpoint Smoke Test
```bash
python manage.py test endpoint
```

### 6. Jalankan Development Server
```bash
python manage.py runserver
```
Akses aplikasi melalui browser di `http://127.0.0.1:8000/`.

---

## Lisensi
Proyek ini dilisensikan di bawah lisensi [MIT](LICENSE).
