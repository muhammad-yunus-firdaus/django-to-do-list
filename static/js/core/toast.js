/**
 * toast.js — Lightweight Non-blocking Toast System (Sonner / shadcn/ui style)
 * Zero emoji, 100% Lucide Icons, non-blocking floating notifications
 */

'use strict';

(function () {
    let container = null;

    function getOrCreateContainer() {
        if (!container) {
            container = document.querySelector('.toast-container');
            if (!container) {
                container = document.createElement('div');
                container.className = 'toast-container';
                document.body.appendChild(container);
            }
        }
        return container;
    }

    /**
     * Tampilkan Toast notification non-blocking di pojok kanan bawah
     * @param {string} message - Pesan notifikasi
     * @param {'success'|'error'|'info'} type - Tipe notifikasi
     * @param {number} duration - Durasi tampil dalam milidetik (default: 2500ms)
     */
    function showToast(message, type = 'success', duration = 2500) {
        if (!message) return;

        const parent = getOrCreateContainer();
        const toast = document.createElement('div');
        toast.className = `toast-item toast-${type}`;

        let iconName = 'check';
        if (type === 'error') iconName = 'alert-circle';
        if (type === 'info') iconName = 'info';

        toast.innerHTML = `
            <span class="toast-icon">
                <i data-lucide="${iconName}" style="width:16px;height:16px;"></i>
            </span>
            <span class="toast-message">${escapeText(message)}</span>
            <button class="toast-close" type="button" aria-label="Tutup">
                <i data-lucide="x" style="width:14px;height:14px;"></i>
            </button>
        `;

        parent.appendChild(toast);

        if (typeof lucide !== 'undefined') {
            lucide.createIcons({ root: toast, attrs: { 'stroke-width': '1.75' } });
        }

        // Trigger animasi masuk
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Close button handler
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => removeToast(toast));
        }

        // Auto dismiss
        const timer = setTimeout(() => {
            removeToast(toast);
        }, duration);

        toast._timer = timer;
    }

    function removeToast(toast) {
        if (!toast || toast._isRemoving) return;
        toast._isRemoving = true;
        clearTimeout(toast._timer);

        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 180);
    }

    function escapeText(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Expose global API
    window.showToast = showToast;

    // Otomatis tangkap pesan dari Django messages jika ada
    document.addEventListener('DOMContentLoaded', () => {
        const djangoMessages = document.querySelectorAll('#django-messages .django-message');
        djangoMessages.forEach((msgEl) => {
            const text = msgEl.getAttribute('data-text');
            const tags = msgEl.getAttribute('data-tags') || '';
            let type = 'info';
            if (tags.includes('success')) type = 'success';
            else if (tags.includes('error') || tags.includes('warning')) type = 'error';

            if (text) {
                showToast(text, type, 3000);
            }
        });
    });
})();
