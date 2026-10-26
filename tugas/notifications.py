"""
Backward-compatibility proxy for notification service.
Implementasi modular berada di package tugas.services.notification_service.
"""
from .services.notification_service import (
    generate_deadline_notifications,
    create_notification,
    get_user_notifications,
    mark_as_read,
    mark_all_as_read,
    delete_user_notification,
)

__all__ = [
    "generate_deadline_notifications",
    "create_notification",
    "get_user_notifications",
    "mark_as_read",
    "mark_all_as_read",
    "delete_user_notification",
]
