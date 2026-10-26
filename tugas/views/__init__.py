"""
tugas/views/__init__.py
Re-export semua view function untuk backward compatibility dengan urls.py dan tests.py.
"""
from .auth_views import (
    login_view,
    logout_view,
    register,
    edit_profil_view,
)
from .dashboard_views import (
    dashboard_view,
)
from .task_views import (
    daftar_tugas,
    tambah_tugas,
    edit_tugas,
    hapus_tugas,
    tandai_selesai,
    tandai_belum,
    detail_tugas,
    tambah_tugas_cepat,
    toggle_tugas_view,
)
from .subtask_views import (
    tambah_subtask,
    edit_subtask,
    hapus_subtask,
    toggle_subtask,
)
from .agenda_views import (
    agenda_harian_view,
    tambah_aktivitas_view,
    toggle_aktivitas_view,
    edit_aktivitas_view,
    hapus_aktivitas_view,
    copy_jadwal_kemarin_view,
    api_jadwal_hari_ini,
    _copy_habits_for_today,
    _get_next_free_slot,
    _generate_24h_timeline,
)
from .kegiatan_views import (
    kegiatan_list_view,
    kegiatan_tambah_view,
    kegiatan_edit_view,
    kegiatan_hapus_view,
    kegiatan_toggle_status_view,
)
from .evaluasi_views import (
    _get_week_range,
    _get_weekly_stats,
    evaluasi_view,
)
from .export_views import (
    export_csv,
    export_excel,
    export_pdf,
    export_kegiatan_pdf,
    export_kegiatan_excel,
    export_jadwal_pdf_view,
    export_jadwal_excel_view,
)
from .notification_views import (
    get_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    delete_notification,
)

__all__ = [
    # Auth
    "login_view",
    "logout_view",
    "register",
    "edit_profil_view",
    # Dashboard
    "dashboard_view",
    # Task
    "daftar_tugas",
    "tambah_tugas",
    "edit_tugas",
    "hapus_tugas",
    "tandai_selesai",
    "tandai_belum",
    "detail_tugas",
    "tambah_tugas_cepat",
    "toggle_tugas_view",
    # Subtask
    "tambah_subtask",
    "edit_subtask",
    "hapus_subtask",
    "toggle_subtask",
    # Agenda
    "agenda_harian_view",
    "tambah_aktivitas_view",
    "toggle_aktivitas_view",
    "edit_aktivitas_view",
    "hapus_aktivitas_view",
    "copy_jadwal_kemarin_view",
    "api_jadwal_hari_ini",
    "_copy_habits_for_today",
    "_get_next_free_slot",
    "_generate_24h_timeline",
    # Kegiatan
    "kegiatan_list_view",
    "kegiatan_tambah_view",
    "kegiatan_edit_view",
    "kegiatan_hapus_view",
    "kegiatan_toggle_status_view",
    # Evaluasi
    "_get_week_range",
    "_get_weekly_stats",
    "evaluasi_view",
    # Export
    "export_csv",
    "export_excel",
    "export_pdf",
    "export_kegiatan_pdf",
    "export_kegiatan_excel",
    "export_jadwal_pdf_view",
    "export_jadwal_excel_view",
    # Notifications
    "get_notifications",
    "mark_notification_read",
    "mark_all_notifications_read",
    "delete_notification",
]
