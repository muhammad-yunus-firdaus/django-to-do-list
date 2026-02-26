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
    path("detail/<int:tugas_id>/", views.detail_tugas, name="detail"),

    # Export
    path("export/csv/", views.export_csv, name="export_csv"),
    path("export/excel/", views.export_excel, name="export_excel"),
    path("export/pdf/", views.export_pdf, name="export_pdf"),

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
]