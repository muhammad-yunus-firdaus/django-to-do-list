/**
 * Notification System JavaScript
 * Handle notification bell, dropdown, dan interactions
 */

// Global state
let notificationsCache = [];
let isNotificationOpen = false;

// Toggle notification dropdown
function toggleNotifications() {
    const dropdown = document.getElementById('notificationDropdown');
    const backdrop = document.getElementById('notificationBackdrop');
    isNotificationOpen = !isNotificationOpen;
    
    if (isNotificationOpen) {
        dropdown.style.display = 'block';
        if (backdrop) backdrop.classList.add('active');
        loadNotifications();
        // Prevent body scroll on mobile when notification open
        if (window.innerWidth <= 768) {
            document.body.style.overflow = 'hidden';
        }
        // Close dropdown when clicking outside
        setTimeout(() => {
            document.addEventListener('click', closeNotificationsOutside);
        }, 100);
    } else {
        dropdown.style.display = 'none';
        if (backdrop) backdrop.classList.remove('active');
        document.body.style.overflow = '';
        document.removeEventListener('click', closeNotificationsOutside);
    }
}

// Close dropdown when clicking outside
function closeNotificationsOutside(event) {
    const dropdown = document.getElementById('notificationDropdown');
    const bell = document.getElementById('notificationBell');
    const backdrop = document.getElementById('notificationBackdrop');
    
    if (!dropdown.contains(event.target) && !bell.contains(event.target)) {
        dropdown.style.display = 'none';
        if (backdrop) backdrop.classList.remove('active');
        isNotificationOpen = false;
        document.body.style.overflow = '';
        document.removeEventListener('click', closeNotificationsOutside);
    }
}

// Load notifications from API
async function loadNotifications() {
    const listContainer = document.getElementById('notificationList');
    
    try {
        const response = await fetch('/tugas/notifications/');
        const data = await response.json();
        
        notificationsCache = data.notifications;
        updateBadge(data.unread_count);
        renderNotifications(data.notifications);
    } catch (error) {
        console.error('Error loading notifications:', error);
        listContainer.innerHTML = `
            <div class="notification-empty">
                <i data-lucide="wifi-off"></i>
                <p style="font-size:0.9rem;margin-top:8px;">Gagal memuat notifikasi</p>
                <button onclick="loadNotifications()" class="btn btn-sm btn-primary" style="margin-top:12px;">
                    Coba Lagi
                </button>
            </div>
        `;
        lucide.createIcons();
    }
}

// Render notifications list
function renderNotifications(notifications) {
    console.log('Rendering notifications:', notifications.length);
    const listContainer = document.getElementById('notificationList');
    
    if (notifications.length === 0) {
        listContainer.innerHTML = `
            <div class="notification-empty">
                <i data-lucide="bell-off"></i>
                <p style="font-size:0.9rem;margin-top:8px;">Tidak ada notifikasi</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }
    
    listContainer.innerHTML = notifications.map(notif => {
        const iconData = getNotificationIcon(notif.tipe);
        const unreadClass = notif.is_read ? '' : 'unread';
        
        return `
            <div class="notification-item ${unreadClass}" data-notification-id="${notif.id}" data-tugas-id="${notif.tugas_id}">
                <div class="notification-icon ${iconData.class}">
                    <i data-lucide="${iconData.icon}" style="width:20px;height:20px;"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-message">${notif.pesan}</div>
                    <div class="notification-time">
                        <i data-lucide="clock" style="width:12px;height:12px;"></i>
                        ${notif.time_ago}
                    </div>
                </div>
                <div class="notification-actions">
                    ${!notif.is_read ? `
                        <button class="notification-action-btn mark-read-btn" data-id="${notif.id}" title="Tandai dibaca">
                            <i data-lucide="check" style="width:14px;height:14px;"></i>
                        </button>
                    ` : ''}
                    <button class="notification-action-btn delete delete-btn" data-id="${notif.id}" title="Hapus">
                        <i data-lucide="trash-2" style="width:14px;height:14px;"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    lucide.createIcons();
    console.log('Icons created, now attaching listeners...');
    
    // Attach event listeners after rendering
    attachNotificationListeners();
    console.log('Render notifications complete');
}

// Get icon data based on notification type
function getNotificationIcon(tipe) {
    const icons = {
        'deadline_soon': { icon: 'clock', class: 'deadline' },
        'overdue': { icon: 'alert-circle', class: 'overdue' },
        'subtask_complete': { icon: 'check-circle', class: 'complete' }
    };
    return icons[tipe] || { icon: 'bell', class: 'deadline' };
}

// Attach event listeners to notification items
function attachNotificationListeners() {
    console.log('=== ATTACH NOTIFICATION LISTENERS START ===');
    
    // Notification item click (go to task detail)
    document.querySelectorAll('.notification-item').forEach(item => {
        item.addEventListener('click', function(e) {
            // Jangan trigger jika click pada button
            if (e.target.closest('.notification-action-btn')) {
                return;
            }
            
            const notifId = this.dataset.notificationId;
            const tugasId = this.dataset.tugasId;
            
            if (tugasId && tugasId !== 'null') {
                handleNotificationClick(notifId, tugasId);
            }
        });
    });
    
    // Mark as read buttons
    const markReadBtns = document.querySelectorAll('.mark-read-btn');
    console.log('Found mark-read buttons:', markReadBtns.length);
    
    markReadBtns.forEach((btn, index) => {
        console.log(`Attaching listener to mark-read button ${index + 1}, ID:`, btn.dataset.id);
        btn.addEventListener('click', function(e) {
            console.log('Mark-read button clicked!', this.dataset.id);
            e.stopPropagation();
            const notifId = this.dataset.id;
            markAsRead(notifId);
        });
    });
    
    // Delete buttons
    const deleteBtns = document.querySelectorAll('.delete-btn');
    console.log('Found delete buttons:', deleteBtns.length);
    
    deleteBtns.forEach((btn, index) => {
        console.log(`Attaching listener to delete button ${index + 1}, ID:`, btn.dataset.id);
        btn.addEventListener('click', function(e) {
            console.log('Delete button clicked!', this.dataset.id);
            e.stopPropagation();
            const notifId = this.dataset.id;
            deleteNotification(notifId);
        });
    });
}

// Handle notification click (go to task detail)
function handleNotificationClick(notificationId, tugasId) {
    if (tugasId) {
        // Mark as read then redirect
        markAsRead(notificationId, true);
        window.location.href = `/tugas/detail/${tugasId}/`;
    }
}

// Mark notification as read
async function markAsRead(notificationId, skipReload = false) {
    console.log('Marking notification as read:', notificationId);
    
    try {
        const csrfToken = getCsrfToken();
        console.log('CSRF Token:', csrfToken ? 'Found' : 'Not found');
        
        const url = `/tugas/notifications/mark-read/${notificationId}/`;
        console.log('Request URL:', url);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.success) {
            updateBadge(data.unread_count);
            if (!skipReload) {
                loadNotifications();
            }
        } else {
            console.error('Mark as read failed:', data.error);
            alert('Gagal menandai notifikasi sebagai dibaca');
        }
    } catch (error) {
        console.error('Error marking as read:', error);
        alert('Terjadi kesalahan saat menandai notifikasi: ' + error.message);
    }
}

// Mark all as read
async function markAllRead() {
    console.log('Marking all notifications as read');
    
    try {
        const csrfToken = getCsrfToken();
        console.log('CSRF Token:', csrfToken ? 'Found' : 'Not found');
        
        const response = await fetch('/tugas/notifications/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.success) {
            updateBadge(0);
            loadNotifications();
        } else {
            console.error('Mark all as read failed');
            alert('Gagal menandai semua notifikasi sebagai dibaca');
        }
    } catch (error) {
        console.error('Error marking all as read:', error);
        alert('Terjadi kesalahan: ' + error.message);
    }
}

// Delete notification
async function deleteNotification(notificationId) {
    console.log('Deleting notification:', notificationId);
    
    try {
        const csrfToken = getCsrfToken();
        console.log('CSRF Token:', csrfToken ? 'Found' : 'Not found');
        
        const url = `/tugas/notifications/delete/${notificationId}/`;
        console.log('Request URL:', url);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.success) {
            updateBadge(data.unread_count);
            loadNotifications();
        } else {
            console.error('Delete failed:', data.error);
            alert('Gagal menghapus notifikasi');
        }
    } catch (error) {
        console.error('Error deleting notification:', error);
        alert('Terjadi kesalahan saat menghapus: ' + error.message);
    }
}

// Update badge counter
function updateBadge(count) {
    const badge = document.getElementById('notificationBadge');
    
    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}

// Get CSRF token from cookie
function getCsrfToken() {
    // Try to get from window object first (set by Django template)
    if (window.CSRF_TOKEN) {
        return window.CSRF_TOKEN;
    }
    
    // Fallback to cookie
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Poll for new notifications every 30 seconds
function startNotificationPolling() {
    // Initial load
    fetch('/tugas/notifications/')
        .then(response => response.json())
        .then(data => {
            updateBadge(data.unread_count);
        })
        .catch(error => console.error('Error polling notifications:', error));
    
    // Poll every 30 seconds
    setInterval(() => {
        fetch('/tugas/notifications/')
            .then(response => response.json())
            .then(data => {
                const oldCount = notificationsCache.length;
                const newCount = data.notifications.length;
                
                updateBadge(data.unread_count);
                
                // Show notification if new unread notifications
                if (data.unread_count > 0 && newCount > oldCount) {
                    showBrowserNotification(data.notifications[0]);
                }
                
                notificationsCache = data.notifications;
            })
            .catch(error => console.error('Error polling notifications:', error));
    }, 30000); // 30 seconds
}

// Show browser notification (Web Push API)
function showBrowserNotification(notification) {
    if ('Notification' in window && Notification.permission === 'granted') {
        const iconData = getNotificationIcon(notification.tipe);
        
        const notif = new Notification('Manajemen Tugas', {
            body: notification.pesan,
            icon: '/static/images/icon-192x192.png',
            badge: '/static/images/icon-192x192.png',
            tag: `notification-${notification.id}`,
            requireInteraction: false,
            silent: false
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

// Request notification permission
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                console.log('Notification permission granted');
            }
        });
    }
}

// Initialize notification system on page load
document.addEventListener('DOMContentLoaded', function() {
    // Start polling for notifications
    startNotificationPolling();
    
    // Request notification permission after 3 seconds
    setTimeout(requestNotificationPermission, 3000);
});
