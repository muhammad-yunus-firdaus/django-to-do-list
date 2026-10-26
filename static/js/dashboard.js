/**
 * DASHBOARD.JS — Interactive AJAX toggles, PWA prompt, and toast notifications
 * Pure Vanilla JS, <150 lines
 */

function getCsrfToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag && metaTag.content) return metaTag.content;
    if (window.CSRF_TOKEN) return window.CSRF_TOKEN;
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
}

// ── Dashboard Agenda Quick Action (AJAX) ──
async function dashToggle(id, targetStatus) {
    try {
        const response = await fetch(`/tugas/agenda/toggle/${id}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ status: targetStatus })
        });
        const data = await response.json();

        if (data.success) {
            // Update badge
            const badgeCell = document.getElementById(`dashBadge${id}`);
            if (badgeCell) {
                const badgeMap = {
                    'selesai': '<span class="badge badge-success">Selesai</span>',
                    'terlewat': '<span class="badge badge-destructive">Terlewat</span>',
                    'belum': '<span class="badge badge-secondary">Belum</span>',
                };
                badgeCell.innerHTML = badgeMap[data.status] || badgeMap['belum'];
            }

            // Update row styling
            const row = document.getElementById(`dashRow${id}`);
            if (row) {
                const isSelesai = data.status === 'selesai';
                row.style.opacity = isSelesai ? '0.6' : '1';
                const titleSpan = row.querySelector('.dash-item-title');
                if (titleSpan) {
                    titleSpan.style.textDecoration = isSelesai ? 'line-through' : 'none';
                    titleSpan.style.color = isSelesai ? 'var(--foreground-muted)' : 'var(--foreground)';
                }
            }

            // Update actions button
            const actionsCell = document.getElementById(`dashActions${id}`);
            if (actionsCell) {
                let btns = '';
                if (data.status !== 'selesai') {
                    btns += `<button onclick="dashToggle(${id}, 'selesai')" class="btn btn-outline btn-icon" title="Tandai Selesai" type="button"><i data-lucide="check" style="width:14px;height:14px;color:var(--success);"></i></button>`;
                }
                if (data.status === 'belum') {
                    btns += `<button onclick="dashToggle(${id}, 'terlewat')" class="btn btn-outline btn-icon" title="Tandai Terlewat" type="button"><i data-lucide="x" style="width:14px;height:14px;color:var(--warning);"></i></button>`;
                }
                if (data.status === 'selesai' || data.status === 'terlewat') {
                    btns += `<button onclick="dashToggle(${id}, 'belum')" class="btn btn-outline btn-icon" title="Kembalikan" type="button"><i data-lucide="rotate-ccw" style="width:14px;height:14px;"></i></button>`;
                }
                actionsCell.innerHTML = btns;
                if (window.lucide) lucide.createIcons();
            }

            // Update stats badge
            const statsBadge = document.getElementById('dashAgendaStats');
            if (statsBadge) {
                statsBadge.textContent = `${data.selesai}/${data.total} Selesai (${Math.round(data.persen)}%)`;
            }

            if (window.showToast) {
                window.showToast(`Jadwal ditandai ${data.status}`, 'success');
            }
        }
    } catch (err) {
        console.error('Dashboard toggle error:', err);
        if (window.showToast) window.showToast('Gagal memperbarui status', 'error');
    }
}

// ── PWA Install Prompt Handler ──
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    const banner = document.getElementById('pwaInstallBanner');
    if (banner && !localStorage.getItem('pwaInstallDismissed')) {
        banner.style.display = 'block';
        if (window.lucide) lucide.createIcons();
    }
});

function installPWA() {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
        if (choiceResult.outcome === 'accepted') {
            console.log('User accepted PWA installation');
        }
        deferredPrompt = null;
        const banner = document.getElementById('pwaInstallBanner');
        if (banner) banner.style.display = 'none';
    });
}

function dismissInstallBanner() {
    const banner = document.getElementById('pwaInstallBanner');
    if (banner) banner.style.display = 'none';
    localStorage.setItem('pwaInstallDismissed', 'true');
}
