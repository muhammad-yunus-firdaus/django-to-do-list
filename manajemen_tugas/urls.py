"""
URL configuration for manajemen_tugas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from tugas.views import tambah_tugas, daftar_tugas, export_csv, export_pdf, export_excel
from tugas import views
from django.conf import settings
from django.conf.urls.static import static  
from pathlib import Path
from django.views.static import serve

BASE_DIR = Path(__file__).resolve().parent.parent

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tugas/', include('tugas.urls')),
    path('', include('tugas.urls')), 
    path('tambah/', tambah_tugas, name='tambah_tugas'),
    path('daftar/', daftar_tugas, name='daftar_tugas'),
    path('', views.index, name='index'),
    path("export-csv/", export_csv, name="export_csv"), 
    path("export/pdf/", export_pdf, name="export_pdf"),
    path('export/excel/', export_excel, name='export_excel'),
    path("accounts/", include("allauth.urls")),
    
]

# Serve static files di development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
