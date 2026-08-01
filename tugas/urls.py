from django.urls import path
from . import views
from . import notification_views

app_name = "tugas"
urlpatterns = [
    # Auth
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),

    # Dashboard
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # CRUD Tugas
    path("daftar/", views.daftar_tugas, name="daftar"),
    path("tambah/", views.tambah_tugas, name="tambah"),
    path("edit/<int:tugas_id>/", views.edit_tugas, name="edit"),
    path("hapus/<int:tugas_id>/", views.hapus_tugas, name="hapus"),
    path("selesai/<int:tugas_id>/", views.tandai_selesai, name="selesai"),
    path("belum/<int:tugas_id>/", views.tandai_belum, name="belum"),
    path("detail/<int:tugas_id>/", views.detail_tugas, name="detail"),

    # Export
    path("export/csv/", views.export_csv, name="export_csv"),
    path("export/excel/", views.export_excel, name="export_excel"),
    path("export/pdf/", views.export_pdf, name="export_pdf"),
    path("export/kegiatan/pdf/", views.export_kegiatan_pdf, name="export_kegiatan_pdf"),
    path("export/kegiatan/excel/", views.export_kegiatan_excel, name="export_kegiatan_excel"),

    # Subtask
    path("subtask/tambah/<int:tugas_id>/", views.tambah_subtask, name="tambah_subtask"),
    path("subtask/edit/<int:subtask_id>/", views.edit_subtask, name="edit_subtask"),
    path("subtask/hapus/<int:subtask_id>/", views.hapus_subtask, name="hapus_subtask"),
    path("subtask/toggle/<int:subtask_id>/", views.toggle_subtask, name="toggle_subtask"),

    # Notifications
    path("notifications/", notification_views.get_notifications, name="get_notifications"),
    path("notifications/mark-read/<int:notification_id>/", notification_views.mark_notification_read, name="mark_notification_read"),
    path("notifications/mark-all-read/", notification_views.mark_all_notifications_read, name="mark_all_notifications_read"),
    path("notifications/delete/<int:notification_id>/", notification_views.delete_notification, name="delete_notification"),

    # Edit Profil
    path("profil/edit/", views.edit_profil_view, name="edit_profil"),

    # Agenda Harian (Daily Time-Blocking + Habit Tracker)
    path("agenda/", views.agenda_harian_view, name="agenda"),
    path("agenda/tambah/", views.tambah_aktivitas_view, name="tambah_aktivitas"),
    path("agenda/toggle/<int:aktivitas_id>/", views.toggle_aktivitas_view, name="toggle_aktivitas"),
    path("agenda/edit/<int:aktivitas_id>/", views.edit_aktivitas_view, name="edit_aktivitas"),
    path("agenda/hapus/<int:aktivitas_id>/", views.hapus_aktivitas_view, name="hapus_aktivitas"),
    path("agenda/copy-kemarin/", views.copy_jadwal_kemarin_view, name="copy_jadwal_kemarin"),
    path("agenda/export-pdf/", views.export_jadwal_pdf_view, name="export_jadwal_pdf"),
    path("agenda/export-excel/", views.export_jadwal_excel_view, name="export_jadwal_excel"),
    path("agenda/api/today/", views.api_jadwal_hari_ini, name="api_jadwal_today"),

    # Evaluasi Mingguan
    path("evaluasi/", views.evaluasi_view, name="evaluasi"),

    # Kegiatan & Acara
    path("kegiatan/", views.kegiatan_list_view, name="kegiatan_list"),
    path("kegiatan/tambah/", views.kegiatan_tambah_view, name="kegiatan_tambah"),
    path("kegiatan/edit/<int:kegiatan_id>/", views.kegiatan_edit_view, name="kegiatan_edit"),
    path("kegiatan/hapus/<int:kegiatan_id>/", views.kegiatan_hapus_view, name="kegiatan_hapus"),
    path("kegiatan/toggle/<int:kegiatan_id>/", views.kegiatan_toggle_status_view, name="kegiatan_toggle_status"),

    # AJAX Task Utils
    path("tambah-cepat/", views.tambah_tugas_cepat, name="tambah_tugas_cepat"),
    path("toggle-tugas/<int:tugas_id>/", views.toggle_tugas_view, name="toggle_tugas"),
]