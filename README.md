# 📝 Manajemen Tugas - Task Management System

Website aplikasi manajemen tugas yang membantu kamu mengorganisir pekerjaan dengan lebih efisien. Bisa bikin tugas, lacak progress, dan dapat notifikasi deadline otomatis.

## 🚀 Teknologi yang Digunakan

- **Backend:** Django 5.2.7 + Python 3.12
- **Database:** SQLite3 (bisa diganti PostgreSQL untuk production)
- **Frontend:** HTML, CSS, JavaScript (Vanilla)
- **UI Library:** Lucide Icons, SweetAlert2, Chart.js
- **Export:** openpyxl (Excel), ReportLab (PDF)
- **PWA:** Service Worker + Manifest.json

## ✨ Fitur Utama

### 🔐 Autentikasi
- Register akun baru
- Login/Logout
- Session management (timeout 1 jam)

### 📋 Manajemen Tugas
- Buat, edit, dan hapus tugas
- Set deadline untuk setiap tugas
- Atur prioritas (Tinggi, Sedang, Rendah)
- Kategorisasi tugas (Kerja, Pribadi, Perkuliahan)
- Status tugas (Belum Selesai, Selesai)

### ✅ Subtask System
- Tambah subtask ke dalam tugas utama
- Centang/uncentang subtask
- Progress bar otomatis berdasarkan subtask yang selesai
- Notifikasi ketika semua subtask selesai

### 🔔 Sistem Notifikasi Real-time
- Notifikasi H-1 sebelum deadline
- Notifikasi tugas yang melewati deadline
- Notifikasi ketika semua subtask selesai
- Browser notification (dengan izin user)
- Auto-refresh setiap 30 detik

### 📊 Dashboard & Analytics
- Statistik tugas (Total, Selesai, Progress, Belum Mulai)
- Chart visualisasi data tugas
- Daftar tugas dengan deadline terdekat
- Daftar tugas prioritas tinggi

### 🔍 Filter & Pencarian
- Filter berdasarkan status
- Filter berdasarkan kategori
- Filter berdasarkan prioritas
- Search tugas by judul atau deskripsi

### 📥 Export Data
- Export ke Excel (.xlsx) dengan styling
- Export ke PDF dengan tabel rapi
- Export ke CSV

### 📱 Mobile Responsive
- Layout dual (desktop: table, mobile: card)
- Touch-friendly interface
- Responsive navigation
- Optimized untuk semua ukuran layar

### 🌐 Progressive Web App (PWA)
- Bisa diinstall sebagai aplikasi standalone
- Service Worker untuk offline support
- Add to Home Screen di mobile

