from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import export_csv, export_pdf, export_excel

app_name = "tugas" 
urlpatterns = [
    # Halaman utama (redirect ke login)
    path("", views.index, name="index"), 
    
    # Login dan Logout
    path("login/", views.login_view, name="login"),  
    path("logout/", views.logout_view, name="logout"), 

    # Register
    path("register/", views.register, name="register"),

    # Dashboard
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # Manajemen Tugas
    path("daftar/", views.daftar_tugas, name="daftar"),
    path("tambah/", views.tambah_tugas, name="tambah"),
    path("edit/<int:tugas_id>/", views.edit_tugas, name="edit"),
    path("hapus/<int:tugas_id>/", views.hapus_tugas, name="hapus"),
    path("selesai/<int:tugas_id>/", views.tandai_selesai, name="selesai"),
    path('tandai_selesai/<int:tugas_id>/', views.tandai_selesai, name='tandai_selesai'), 
    path("tugas/selesai/<int:tugas_id>/", views.tandai_selesai, name="selesai"),
    path("detail/<int:tugas_id>/", views.detail_tugas, name="detail"),

     # 🔹 URL Export
    path("export/csv/", views.export_csv, name="export_csv"),
    path("export/excel/", views.export_excel, name="export_excel"),
    path("export/pdf/", views.export_pdf, name="export_pdf"),

    
]