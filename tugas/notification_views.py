"""
Backward-compatibility proxy for notification views.
Implementasi modular berada di package tugas.views.notification_views.
"""
from .views.notification_views import (
    get_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    delete_notification,
    get_time_ago,
)

__all__ = [
    "get_notifications",
    "mark_notification_read",
    "mark_all_notifications_read",
    "delete_notification",
    "get_time_ago",
]
