/**
 * AGENDA.JS — Zero-Lag AJAX, Optimistic UI, Quick Duration Pills & Toast Integration
 * Modular Vanilla JS, <300 lines, Zero AI-Slop
 */

function getCsrfToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag && metaTag.content) return metaTag.content;
    if (window.CSRF_TOKEN) return window.CSRF_TOKEN;
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
}

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function updateSummaryKPI(stats) {
    if (!stats) return;
    const selesaiEl = document.getElementById('statsSelesai');
    const totalEl = document.getElementById('statsTotal');
    const persenEl = document.getElementById('statsPersen');
    const progressFill = document.getElementById('progressFill');

    if (selesaiEl && stats.selesai !== undefined) selesaiEl.textContent = stats.selesai;
    if (totalEl && stats.total !== undefined) totalEl.textContent = stats.total;
    if (persenEl && stats.persen !== undefined) persenEl.textContent = Math.round(stats.persen) + '%';
    if (progressFill && stats.persen !== undefined) progressFill.style.width = Math.round(stats.persen) + '%';
}

// ── 1. Status Toggle (Optimistic AJAX) ──
async function setAktivitasStatus(id, targetStatus) {
    const card = document.getElementById(`aktCard-${id}`) || document.querySelector(`.aktivitas-card[data-id="${id}"]`);
    if (!card) return;

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
            updateSummaryKPI(data);
            const isSelesai = data.status === 'selesai';
            card.classList.toggle('status-selesai', isSelesai);

            const indicator = card.querySelector('.akt-indicator-bar');
            if (indicator) {
                indicator.className = `akt-indicator-bar ${data.status}`;
            }

            const metaBadge = card.querySelector('.akt-meta');
            if (metaBadge) {
                const badgeClass = isSelesai ? 'badge-success' : (data.status === 'terlewat' ? 'badge-destructive' : 'badge-secondary');
                const badgeLabel = isSelesai ? 'Selesai' : (data.status === 'terlewat' ? 'Terlewat' : 'Belum');
                const habitSpan = card.querySelector('.badge-outline') ? '<span class="badge badge-outline"><i data-lucide="repeat" style="width:10px;height:10px;"></i> Habit</span>' : '';
                metaBadge.innerHTML = `${habitSpan}<span class="badge ${badgeClass}">${badgeLabel}</span>`;
            }

            // Update action button
            const actions = card.querySelector('.akt-actions');
            if (actions) {
                const toggleBtn = actions.querySelector('button[title="Tandai Selesai"], button[title="Kembalikan ke Belum"]');
                if (toggleBtn) {
                    if (isSelesai) {
                        toggleBtn.title = 'Kembalikan ke Belum';
                        toggleBtn.setAttribute('onclick', `setAktivitasStatus(${id}, 'belum')`);
                        toggleBtn.innerHTML = '<i data-lucide="rotate-ccw" style="width:14px;height:14px;"></i>';
                    } else {
                        toggleBtn.title = 'Tandai Selesai';
                        toggleBtn.setAttribute('onclick', `setAktivitasStatus(${id}, 'selesai')`);
                        toggleBtn.innerHTML = '<i data-lucide="check" style="width:14px;height:14px;color:var(--success);"></i>';
                    }
                }
            }

            if (window.lucide) lucide.createIcons();
            if (window.showToast) window.showToast(`Status berhasil diubah ke ${data.status}`, 'success');
        } else {
            if (window.showToast) window.showToast(data.error || 'Gagal mengubah status', 'error');
        }
    } catch (err) {
        console.error('Toggle error:', err);
        if (window.showToast) window.showToast('Gagal menghubungkan ke server', 'error');
    }
}

// ── 2. Edit Aktivitas Modal (Zero-Lag AJAX) ──
function editAktivitas(id, judul, jamMulai, durasi, isHabit) {
    const safeJudul = escapeHtml(judul);

    Swal.fire({
        title: 'Edit Aktivitas',
        html: `
            <div style="display:flex;flex-direction:column;gap:12px;text-align:left;">
                <div class="form-group">
                    <label class="form-label" for="swal-judul">Nama Aktivitas</label>
                    <input id="swal-judul" class="form-input" type="text" value="${safeJudul}">
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                    <div class="form-group">
                        <label class="form-label" for="swal-jam-mulai">Jam Mulai</label>
                        <input id="swal-jam-mulai" class="form-input" type="time" value="${jamMulai}">
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="swal-durasi">Durasi (Menit)</label>
                        <input id="swal-durasi" class="form-input" type="number" min="5" max="480" value="${durasi}">
                    </div>
                </div>
                <div class="quick-pills-wrapper">
                    <button type="button" class="quick-pill" onclick="document.getElementById('swal-durasi').value=15">15m</button>
                    <button type="button" class="quick-pill" onclick="document.getElementById('swal-durasi').value=30">30m</button>
                    <button type="button" class="quick-pill" onclick="document.getElementById('swal-durasi').value=45">45m</button>
                    <button type="button" class="quick-pill" onclick="document.getElementById('swal-durasi').value=60">60m</button>
                    <button type="button" class="quick-pill" onclick="document.getElementById('swal-durasi').value=90">90m</button>
                    <button type="button" class="quick-pill" onclick="document.getElementById('swal-durasi').value=120">120m</button>
                </div>
                <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:0.8125rem;color:var(--foreground-muted);margin-top:4px;">
                    <input id="swal-is-habit" class="form-checkbox" type="checkbox" ${isHabit ? 'checked' : ''}>
                    <span>Ulangi Setiap Hari (Habit)</span>
                </label>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'Simpan Perubahan',
        cancelButtonText: 'Batal',
        customClass: {
            popup: 'swal-custom-modal',
            confirmButton: 'btn btn-primary',
            cancelButton: 'btn btn-outline',
            actions: 'swal2-actions'
        },
        buttonsStyling: false,
        preConfirm: () => {
            const newJudul = document.getElementById('swal-judul').value.trim();
            const newJamMulai = document.getElementById('swal-jam-mulai').value;
            const newDurasi = document.getElementById('swal-durasi').value;
            const newIsHabit = document.getElementById('swal-is-habit').checked;

            if (!newJudul) {
                Swal.showValidationMessage('Nama aktivitas tidak boleh kosong');
                return false;
            }
            if (!newJamMulai) {
                Swal.showValidationMessage('Jam mulai harus ditentukan');
                return false;
            }
            if (!newDurasi || parseInt(newDurasi) < 5) {
                Swal.showValidationMessage('Durasi minimal 5 menit');
                return false;
            }

            return {
                judul: newJudul,
                jam_mulai: newJamMulai,
                durasi_menit: newDurasi,
                is_habit: newIsHabit ? 'on' : ''
            };
        }
    }).then(async (result) => {
        if (!result.isConfirmed) return;

        const formData = new URLSearchParams();
        for (const [key, value] of Object.entries(result.value)) {
            if (value !== '') formData.append(key, value);
        }

        try {
            const response = await fetch(`/tugas/agenda/edit/${id}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData.toString()
            });
            const data = await response.json();

            if (data.success) {
                const card = document.getElementById(`aktCard-${id}`) || document.querySelector(`.aktivitas-card[data-id="${id}"]`);
                if (card) {
                    const judulEl = card.querySelector('.akt-judul');
                    if (judulEl) judulEl.textContent = data.judul;

                    const timeStartEl = card.querySelector('.akt-time-start');
                    if (timeStartEl) timeStartEl.textContent = data.jam_mulai;

                    const timeEndEls = card.querySelectorAll('.akt-time-end');
                    if (timeEndEls[0]) timeEndEls[0].textContent = data.jam_selesai;
                    if (timeEndEls[1]) timeEndEls[1].textContent = `${data.durasi_menit} mnt`;

                    const editBtn = card.querySelector('button[title="Edit Aktivitas"]');
                    if (editBtn) {
                        editBtn.setAttribute('onclick', `editAktivitas(${data.id}, '${escapeHtml(data.judul)}', '${data.jam_mulai}', ${data.durasi_menit}, ${data.is_habit ? 'true' : 'false'})`);
                    }
                }
                updateSummaryKPI(data);
                if (window.showToast) window.showToast('Aktivitas berhasil diperbarui', 'success');
            } else {
                if (window.showToast) window.showToast(data.error || 'Gagal menyimpan perubahan', 'error');
            }
        } catch (err) {
            console.error('Edit error:', err);
            if (window.showToast) window.showToast('Terjadi kesalahan saat menyimpan', 'error');
        }
    });
}

// ── 3. Hapus Aktivitas Confirmation ──
function konfirmasiHapusAktivitas(aktId, judul) {
    Swal.fire({
        title: 'Hapus Aktivitas?',
        text: `Aktivitas "${judul}" akan dihapus dari jadwal hari ini.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Ya, Hapus',
        cancelButtonText: 'Batal',
        customClass: {
            popup: 'swal-custom-modal',
            confirmButton: 'btn btn-destructive',
            cancelButton: 'btn btn-outline',
            actions: 'swal2-actions'
        },
        buttonsStyling: false
    }).then(async (result) => {
        if (!result.isConfirmed) return;

        try {
            const response = await fetch(`/tugas/agenda/hapus/${aktId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            const data = await response.json();

            if (data.success) {
                const card = document.getElementById(`aktCard-${aktId}`) || document.querySelector(`.aktivitas-card[data-id="${aktId}"]`);
                if (card) {
                    card.style.transition = 'all 0.25s ease';
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.95)';
                    setTimeout(() => card.remove(), 250);
                }
                updateSummaryKPI(data);
                if (window.showToast) window.showToast('Aktivitas berhasil dihapus', 'success');
            } else {
                if (window.showToast) window.showToast(data.error || 'Gagal menghapus aktivitas', 'error');
            }
        } catch (err) {
            console.error('Delete error:', err);
            if (window.showToast) window.showToast('Terjadi kesalahan saat menghapus', 'error');
        }
    });
}

// ── 4. Form Tambah Aktivitas (Loading State & Anti Double-Click) ──
function initFormTambah() {
    const form = document.getElementById('formTambahAktivitas');
    const submitBtn = document.getElementById('btnSubmitAktivitas');
    if (!form || !submitBtn) return;

    // Quick Duration Pills click listener
    document.querySelectorAll('.quick-pills-wrapper .quick-pill').forEach(pill => {
        pill.addEventListener('click', function() {
            const durasiInput = document.getElementById('id_durasi_menit');
            if (durasiInput) {
                durasiInput.value = this.dataset.durasi || this.textContent.replace('m', '');
                document.querySelectorAll('.quick-pills-wrapper .quick-pill').forEach(p => p.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i data-lucide="loader-2" class="animate-spin" style="width:14px;height:14px;"></i> <span>Menyimpan...</span>';
        if (window.lucide) lucide.createIcons();

        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });
            const data = await response.json();

            if (data.success) {
                if (window.showToast) window.showToast('Aktivitas baru berhasil dijadwalkan', 'success');
                setTimeout(() => window.location.reload(), 300);
            } else {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
                if (window.lucide) lucide.createIcons();
                if (window.showToast) window.showToast(data.error || 'Jadwal bertabrakan atau format tidak valid', 'error');
            }
        } catch (err) {
            console.error('Submit error:', err);
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHtml;
            if (window.lucide) lucide.createIcons();
            if (window.showToast) window.showToast('Koneksi terganggu', 'error');
        }
    });
}

// ── 5. Salin Jadwal Kemarin ──
function initCopyKemarin() {
    const btn = document.getElementById('btnCopyKemarin');
    if (!btn) return;

    btn.addEventListener('click', async function() {
        const copyUrl = this.dataset.copyUrl;
        const tanggal = this.dataset.tanggal;
        const yesterdayScript = document.getElementById('yesterday-data');
        if (!yesterdayScript) return;

        let items = [];
        try {
            items = JSON.parse(yesterdayScript.textContent);
        } catch (e) {
            console.error('Parse yesterday data:', e);
        }

        try {
            const res = await fetch(copyUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ tanggal: tanggal, aktivitas: items })
            });
            const data = await res.json();
            if (data.success) {
                if (window.showToast) window.showToast(data.message, 'success');
                setTimeout(() => window.location.reload(), 400);
            } else {
                if (window.showToast) window.showToast(data.error || 'Gagal menyalin jadwal', 'error');
            }
        } catch (err) {
            console.error('Copy error:', err);
        }
    });
}

// ── 6. 24-Hour Timeline Slots & Quick-Fill Feature ──
function quickFillSlot(startTime, duration) {
    const jamInput = document.getElementById('id_jam_mulai');
    const durasiInput = document.getElementById('id_durasi_menit');
    const judulInput = document.getElementById('id_judul');

    if (jamInput) jamInput.value = startTime;
    if (durasiInput) {
        durasiInput.value = duration || 60;
        document.querySelectorAll('.quick-pills-wrapper .quick-pill').forEach(pill => {
            pill.classList.toggle('active', (pill.dataset.durasi === '60' || pill.textContent.trim() === '60m'));
        });
    }

    const formCard = document.getElementById('formTambahCard');
    if (formCard) {
        formCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    setTimeout(() => {
        if (judulInput) judulInput.focus();
    }, 250);

    const startH = parseInt(startTime.split(':')[0], 10);
    const endH = startH + 1;
    const endStr = endH === 24 ? '24:00' : `${String(endH).padStart(2, '0')}:00`;
    if (typeof window.showToast === 'function') {
        window.showToast(`Slot ${startTime} - ${endStr} dipilih`, 'info');
    }
}
window.quickFillSlot = quickFillSlot;

function init24HourTimeline() {
    const container = document.getElementById('timelineContainer');
    if (!container) return;

    // Collect occupied intervals from existing scheduled items
    const occupiedRanges = [];
    const filledCards = container.querySelectorAll('.aktivitas-card.slot-filled');

    filledCards.forEach(card => {
        const startText = card.querySelector('.akt-time-start')?.textContent.trim();
        const endText = card.querySelector('.akt-time-end')?.textContent.trim();
        if (startText && endText && startText.includes(':') && endText.includes(':')) {
            const [sh, sm] = startText.split(':').map(Number);
            const [eh, em] = endText.split(':').map(Number);
            const startMins = sh * 60 + sm;
            let endMins = eh * 60 + em;
            if (endMins <= startMins) endMins += 24 * 60;
            occupiedRanges.push({ start: startMins, end: endMins });
            card.dataset.startMinutes = startMins;
        } else {
            card.dataset.startMinutes = 0;
        }
    });

    // Generate 24 1-hour slots: 00:00 - 01:00 ... 23:00 - 24:00
    for (let h = 0; h < 24; h++) {
        const slotStartMins = h * 60;
        const slotEndMins = (h + 1) * 60;

        const isOccupied = occupiedRanges.some(range => {
            return Math.max(slotStartMins, range.start) < Math.min(slotEndMins, range.end);
        });

        if (!isOccupied) {
            const startStr = `${String(h).padStart(2, '0')}:00`;
            const nextH = h + 1;
            const endStr = nextH === 24 ? '24:00' : `${String(nextH).padStart(2, '0')}:00`;

            const emptyCard = document.createElement('div');
            emptyCard.className = 'slot-empty-card slot-empty';
            emptyCard.dataset.startMinutes = slotStartMins;
            emptyCard.style.display = 'none'; // default filter is "filled"
            emptyCard.innerHTML = `
                <div style="display:flex;align-items:center;gap:0.75rem;">
                    <div style="display:flex;align-items:center;gap:6px;">
                        <i data-lucide="clock" style="width:14px;height:14px;color:var(--foreground-muted);"></i>
                        <span style="font-size:0.8125rem;font-weight:600;color:var(--foreground-muted);font-variant-numeric:tabular-nums;">
                            ${startStr} — ${endStr}
                        </span>
                    </div>
                    <span class="badge badge-secondary" style="font-size:0.6875rem;">Waktu Luang</span>
                </div>
                <button type="button" class="btn btn-outline btn-sm quick-fill-btn" onclick="quickFillSlot('${startStr}', 60)" style="font-size:0.75rem;padding:3px 10px;display:inline-flex;align-items:center;gap:4px;">
                    <i data-lucide="plus" style="width:14px;height:14px;"></i>
                    <span>Isi Slot</span>
                </button>
            `;
            container.appendChild(emptyCard);
        }
    }

    // Sort container children chronologically
    const allItems = Array.from(container.children);
    allItems.sort((a, b) => {
        const aMin = parseInt(a.dataset.startMinutes || '0', 10);
        const bMin = parseInt(b.dataset.startMinutes || '0', 10);
        return aMin - bMin;
    });
    allItems.forEach(el => container.appendChild(el));

    if (window.lucide) lucide.createIcons();
}

function initTimelineFilter() {
    const emptyNotice = document.querySelector('#timelineContainer .timeline-empty-notice');

    document.querySelectorAll('.timeline-filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.timeline-filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const filter = this.dataset.filter;

            document.querySelectorAll('#timelineContainer .aktivitas-card, #timelineContainer .slot-empty-card').forEach(item => {
                if (filter === 'all') {
                    item.style.display = 'flex';
                } else if (filter === 'filled') {
                    item.style.display = item.classList.contains('slot-filled') ? 'flex' : 'none';
                } else if (filter === 'empty') {
                    item.style.display = item.classList.contains('slot-empty') ? 'flex' : 'none';
                }
            });

            if (emptyNotice) {
                if (filter === 'filled') {
                    const hasFilled = document.querySelectorAll('#timelineContainer .slot-filled').length > 0;
                    emptyNotice.style.display = hasFilled ? 'none' : 'block';
                } else {
                    emptyNotice.style.display = 'none';
                }
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initFormTambah();
    initCopyKemarin();
    init24HourTimeline();
    initTimelineFilter();
});
