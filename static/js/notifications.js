/**
 * Notification System JavaScript
 * Pure Vanilla JS, Shadcn/ui Popover & Sonner-style Toast integration
 * Zero emoji, zero AI-slop, sanitized XSS
 */

let notificationsCache = [];
let isNotificationOpen = false;

// Sanitasi XSS untuk konten dinamis
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Toggle notification popover
function toggleNotifications() {
    const dropdown = document.getElementById('notificationDropdown');
    const backdrop = document.getElementById('notificationBackdrop');
    if (!dropdown) return;

    isNotificationOpen = !isNotificationOpen;

    if (isNotificationOpen) {
        dropdown.style.display = 'flex';
        if (backdrop) backdrop.classList.add('active');
        loadNotifications();

        if (window.innerWidth <= 768) {
            document.body.style.overflow = 'hidden';
        }

        setTimeout(() => {
            document.addEventListener('click', closeNotificationsOutside);
        }, 50);
    } else {
        closeNotificationPopover();
    }
}

function closeNotificationPopover() {
    const dropdown = document.getElementById('notificationDropdown');
    const backdrop = document.getElementById('notificationBackdrop');
    if (dropdown) dropdown.style.display = 'none';
    if (backdrop) backdrop.classList.remove('active');
    isNotificationOpen = false;
    document.body.style.overflow = '';
    document.removeEventListener('click', closeNotificationsOutside);
}

// Close when clicking outside
function closeNotificationsOutside(event) {
    const dropdown = document.getElementById('notificationDropdown');
    const bell = document.getElementById('notificationBell');
    if (!dropdown || !bell) return;

    if (!dropdown.contains(event.target) && !bell.contains(event.target)) {
        closeNotificationPopover();
    }
}

// Load notifications from API
async function loadNotifications() {
    const listContainer = document.getElementById('notificationList');
    if (!listContainer) return;

    try {
        const response = await fetch('/tugas/notifications/');
        if (!response.ok) throw new Error('Gagal terhubung ke server');
        const data = await response.json();

        notificationsCache = data.notifications || [];
        updateBadge(data.unread_count || 0);
        renderNotifications(notificationsCache);
    } catch (error) {
        console.error('Error loading notifications:', error);
        listContainer.innerHTML = `
            <div class="notification-empty">
                <i data-lucide="wifi-off" style="width:24px;height:24px;stroke-width:1.5;"></i>
                <p>Gagal memuat notifikasi</p>
                <button onclick="loadNotifications()" class="btn btn-sm btn-outline" style="margin-top:8px;">
                    Coba Lagi
                </button>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
    }
}

// Render notifications list
function renderNotifications(notifications) {
    const listContainer = document.getElementById('notificationList');
    if (!listContainer) return;

    if (!notifications || notifications.length === 0) {
        listContainer.innerHTML = `
            <div class="notification-empty">
                <i data-lucide="bell-off" style="width:28px;height:28px;stroke-width:1.5;color:var(--foreground-muted);"></i>
                <p>Belum ada notifikasi baru</p>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    listContainer.innerHTML = notifications.map(notif => {
        const iconData = getNotificationIcon(notif.tipe);
        const unreadClass = notif.is_read ? '' : 'unread';
        const safePesan = escapeHtml(notif.pesan);
        const safeTimeAgo = escapeHtml(notif.time_ago);
        const safeId = escapeHtml(notif.id);
        const safeTugasId = notif.tugas_id ? escapeHtml(notif.tugas_id) : '';

        return `
            <div class="notification-item ${unreadClass}" data-notification-id="${safeId}" data-tugas-id="${safeTugasId}">
                <div class="notification-icon-box ${iconData.class}">
                    <i data-lucide="${iconData.icon}" style="width:16px;height:16px;stroke-width:2;"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-message">${safePesan}</div>
                    <div class="notification-time">
                        <i data-lucide="clock" style="width:12px;height:12px;stroke-width:1.5;"></i>
                        <span>${safeTimeAgo}</span>
                    </div>
                </div>
                <div class="notification-actions">
                    ${!notif.is_read ? `
                        <button class="notification-action-btn mark-read-btn" data-id="${safeId}" title="Tandai dibaca" aria-label="Tandai dibaca">
                            <i data-lucide="check" style="width:14px;height:14px;stroke-width:2;"></i>
                        </button>
                    ` : ''}
                    <button class="notification-action-btn delete delete-btn" data-id="${safeId}" title="Hapus notifikasi" aria-label="Hapus notifikasi">
                        <i data-lucide="trash-2" style="width:14px;height:14px;stroke-width:1.75;"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');

    if (window.lucide) lucide.createIcons();
    attachNotificationListeners();
}

// Get icon data based on notification type (Lucide icons only)
function getNotificationIcon(tipe) {
    const icons = {
        'deadline_soon': { icon: 'clock', class: 'deadline' },
        'overdue': { icon: 'alert-circle', class: 'overdue' },
        'subtask_complete': { icon: 'check-circle-2', class: 'complete' }
    };
    return icons[tipe] || { icon: 'bell', class: 'deadline' };
}

// Attach event listeners
function attachNotificationListeners() {
    document.querySelectorAll('.notification-item').forEach(item => {
        item.addEventListener('click', function(e) {
            if (e.target.closest('.notification-action-btn')) return;
            const notifId = this.dataset.notificationId;
            const tugasId = this.dataset.tugasId;
            if (tugasId && tugasId !== 'null' && tugasId !== '') {
                markAsRead(notifId, true);
                window.location.href = `/tugas/detail/${tugasId}/`;
            }
        });
    });

    document.querySelectorAll('.mark-read-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            markAsRead(this.dataset.id);
        });
    });

    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            deleteNotification(this.dataset.id);
        });
    });
}

// Mark single notification as read
async function markAsRead(notificationId, skipReload = false) {
    try {
        const csrfToken = getCsrfToken();
        const response = await fetch(`/tugas/notifications/mark-read/${notificationId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) throw new Error('Status respon tidak valid');
        const data = await response.json();

        if (data.success) {
            updateBadge(data.unread_count || 0);
            if (!skipReload) loadNotifications();
        } else {
            notifyFeedback(data.error || 'Gagal menandai notifikasi', 'error');
        }
    } catch (error) {
        console.error('Error marking as read:', error);
        notifyFeedback('Terjadi kesalahan saat memproses notifikasi', 'error');
    }
}

// Mark all notifications as read
async function markAllRead() {
    try {
        const csrfToken = getCsrfToken();
        const response = await fetch('/tugas/notifications/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) throw new Error('Status respon tidak valid');
        const data = await response.json();

        if (data.success) {
            updateBadge(0);
            loadNotifications();
            notifyFeedback('Semua notifikasi ditandai dibaca', 'success');
        } else {
            notifyFeedback('Gagal menandai semua notifikasi', 'error');
        }
    } catch (error) {
        console.error('Error marking all as read:', error);
        notifyFeedback('Terjadi kesalahan saat memproses permintaan', 'error');
    }
}

// Delete notification
async function deleteNotification(notificationId) {
    try {
        const csrfToken = getCsrfToken();
        const response = await fetch(`/tugas/notifications/delete/${notificationId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) throw new Error('Status respon tidak valid');
        const data = await response.json();

        if (data.success) {
            updateBadge(data.unread_count || 0);
            loadNotifications();
            notifyFeedback('Notifikasi dihapus', 'info');
        } else {
            notifyFeedback(data.error || 'Gagal menghapus notifikasi', 'error');
        }
    } catch (error) {
        console.error('Error deleting notification:', error);
        notifyFeedback('Gagal menghapus notifikasi', 'error');
    }
}

// Update badge counter
function updateBadge(count) {
    const badge = document.getElementById('notificationBadge');
    if (!badge) return;

    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}

// Toast helper fallback
function notifyFeedback(message, type = 'info') {
    if (window.showToast) {
        window.showToast(message, type);
    } else {
        console.log(`[Toast ${type}]: ${message}`);
    }
}

// CSRF Token getter
function getCsrfToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag && metaTag.content) return metaTag.content;
    if (window.CSRF_TOKEN) return window.CSRF_TOKEN;

    const name = 'csrftoken';
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
    }
    return '';
}

// Background polling for notifications
function startNotificationPolling() {
    fetch('/tugas/notifications/')
        .then(response => response.json())
        .then(data => updateBadge(data.unread_count || 0))
        .catch(err => console.debug('Initial polling check:', err));

    setInterval(() => {
        fetch('/tugas/notifications/')
            .then(response => response.json())
            .then(data => {
                const oldCount = notificationsCache.length;
                const newCount = (data.notifications || []).length;
                updateBadge(data.unread_count || 0);

                if (data.unread_count > 0 && newCount > oldCount && data.notifications[0]) {
                    showBrowserNotification(data.notifications[0]);
                }
                notificationsCache = data.notifications || [];
            })
            .catch(err => console.debug('Background poll error:', err));
    }, 30000);
}

// Web Push API Notification
function showBrowserNotification(notification) {
    if ('Notification' in window && Notification.permission === 'granted') {
        const notif = new Notification('Manajemen Tugas', {
            body: notification.pesan,
            icon: '/static/images/icon-192x192.png',
            tag: `notification-${notification.id}`,
            requireInteraction: false
        });

        notif.onclick = function() {
            window.focus();
            if (notification.tugas_id) {
                window.location.href = `/tugas/detail/${notification.tugas_id}/`;
            }
            notif.close();
        };
    }
}

// Request Web Push permission
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// Initialization on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    startNotificationPolling();
    setTimeout(requestNotificationPermission, 3000);
});
