// ══════════════════════════════════════════════════════════════════════
// AGENDA.JS — Timeline 24 Jam Dinamis, Filter, & Notifikasi Pengingat
// ══════════════════════════════════════════════════════════════════════

// ── Status Toggle AJAX ──
function setAktivitasStatus(id, targetStatus) {
    fetch(`/tugas/agenda/toggle/${id}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': window.CSRF_TOKEN,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: targetStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        }
    })
    .catch(error => console.error('Error:', error));
}

// ── Edit Aktivitas Modal ──
function editAktivitas(id, judul, jamMulai, durasi, isHabit) {
    Swal.fire({
        title: 'Edit Aktivitas',
        html: `
            <div style="text-align:left; display:flex; flex-direction:column; gap:12px;">
                <div>
                    <label class="form-label" style="display:block; font-size:0.875rem; font-weight:600; margin-bottom:6px;">Aktivitas</label>
                    <input id="swal-judul" class="form-input" type="text" value="${judul}">
                </div>
                <div class="swal-form-grid">
                    <div>
                        <label class="form-label" style="display:block; font-size:0.875rem; font-weight:600; margin-bottom:6px;">Jam Mulai</label>
                        <input id="swal-jam-mulai" class="form-input" type="time" value="${jamMulai}">
                    </div>
                    <div>
                        <label class="form-label" style="display:block; font-size:0.875rem; font-weight:600; margin-bottom:6px;">Durasi (Menit)</label>
                        <input id="swal-durasi" class="form-input" type="number" min="5" max="480" value="${durasi}">
                    </div>
                </div>
                <div style="margin-top:6px;">
                    <label style="display:flex; align-items:center; gap:8px; cursor:pointer; font-size:0.875rem; color:var(--text-secondary);">
                        <input id="swal-is-habit" class="form-checkbox" type="checkbox" ${isHabit ? 'checked' : ''}>
                        <i data-lucide="repeat" style="width:14px; height:14px; color:var(--primary);"></i>
                        Ulangi Setiap Hari
                    </label>
                </div>
            </div>
        `,
        width: 'min(500px, 92vw)',
        showCancelButton: true,
        confirmButtonColor: 'var(--primary)',
        cancelButtonColor: 'var(--secondary)',
        confirmButtonText: 'Simpan',
        cancelButtonText: 'Batal',
        focusConfirm: false,
        didOpen: () => {
            if (window.lucide) {
                lucide.createIcons();
            }
            const swalTimeInput = document.getElementById('swal-jam-mulai');
            if (swalTimeInput) {
                initTimeInputPicker(swalTimeInput);
            }
        },
        preConfirm: () => {
            const newJudul = document.getElementById('swal-judul').value.trim();
            const newJamMulai = document.getElementById('swal-jam-mulai').value;
            const newDurasi = document.getElementById('swal-durasi').value;
            const newIsHabit = document.getElementById('swal-is-habit').checked;

            if (!newJudul) {
                Swal.showValidationMessage('Judul tidak boleh kosong!');
                return false;
            }
            if (!newJamMulai) {
                Swal.showValidationMessage('Jam mulai harus ditentukan!');
                return false;
            }
            if (!newDurasi || parseInt(newDurasi) < 5) {
                Swal.showValidationMessage('Durasi minimal 5 menit!');
                return false;
            }

            return {
                judul: newJudul,
                jam_mulai: newJamMulai,
                durasi_menit: newDurasi,
                is_habit: newIsHabit ? 'on' : ''
            };
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/tugas/agenda/edit/${id}/`;

            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = window.CSRF_TOKEN;
            form.appendChild(csrfInput);

            for (const [key, value] of Object.entries(result.value)) {
                if (value !== '') {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = key;
                    input.value = value;
                    form.appendChild(input);
                }
            }

            document.body.appendChild(form);
            form.submit();
        }
    });
}

// ── Time Input Picker Helper ──
function initTimeInputPicker(input) {
    if (!input) return;
    if (input.parentElement) {
        input.parentElement.style.cursor = 'pointer';
    }
    input.addEventListener('click', function() {
        if (typeof this.showPicker === 'function') {
            this.showPicker();
        }
    });
}

// ── Hapus Aktivitas Confirmation ──
function konfirmasiHapusAktivitas(aktId, judul) {
    Swal.fire({
        title: 'Hapus Aktivitas?',
        text: `Aktivitas "${judul}" akan dihapus.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#F43F5E',
        cancelButtonColor: '#64748B',
        confirmButtonText: 'Ya, Hapus',
        cancelButtonText: 'Batal'
    }).then((result) => {
        if (result.isConfirmed) {
            document.getElementById(`hapusAkt${aktId}`).submit();
        }
    });
}

// ── Cookie Helper ──
function getCookie(name) {
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


// ══════════════════════════════════════════════════════════════════════
// TIMELINE 24 JAM RENDERER
// ══════════════════════════════════════════════════════════════════════

function renderTimeline(filterMode) {
    const container = document.getElementById('timelineContainer');
    if (!container) return;

    const dataEl = document.getElementById('timeline-24h-data');
    if (!dataEl) return;

    let timelineData;
    try {
        console.log("Raw timeline text:", dataEl.textContent);
        timelineData = JSON.parse(dataEl.textContent);
        console.log("Parsed timelineData type:", typeof timelineData, Array.isArray(timelineData), timelineData);
        if (typeof timelineData === 'string') {
            timelineData = JSON.parse(timelineData);
            console.log("Second parse timelineData type:", typeof timelineData, Array.isArray(timelineData), timelineData);
        }
    } catch (e) {
        console.error('Failed to parse timeline data:', e);
        return;
    }

    // Check if there are matches for the selected filter mode
    let hasMatches = false;
    if (filterMode === 'all') {
        hasMatches = timelineData.length > 0;
    } else if (filterMode === 'filled') {
        hasMatches = timelineData.some(item => item.type !== 'kosong');
    } else if (filterMode === 'empty') {
        hasMatches = timelineData.some(item => item.type === 'kosong');
    } else {
        hasMatches = timelineData.some(item => item.type !== 'kosong'); // default is filled only
    }

    // Build empty state if no matches
    if (!hasMatches) {
        const emptyMsg = filterMode === 'empty'
            ? 'Semua slot waktu sudah terisi jadwal'
            : 'Belum ada aktivitas atau acara yang dijadwalkan';
        const emptyHint = filterMode === 'empty'
            ? 'Efisiensi waktu Anda sudah optimal'
            : 'Tambahkan aktivitas menggunakan form di atas atau buat kegiatan acara baru';

        container.innerHTML = `
            <div class="card" style="padding:20px;">
                <div class="empty-state" style="padding:32px;">
                    <i data-lucide="calendar-off" style="width:48px;height:48px;"></i>
                    <p style="font-size:1rem;font-weight:500;margin-top:8px;">${emptyMsg}</p>
                    <p class="text-xs" style="color:var(--text-muted);">${emptyHint}</p>
                </div>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    // Render ALL slots to DOM first
    let html = '<div style="display:flex;flex-direction:column;gap:8px;">';

    timelineData.forEach(item => {
        if (item.type === 'kosong') {
            html += renderEmptySlot(item);
        } else if (item.type === 'aktivitas') {
            html += renderAktivitasCard(item);
        } else if (item.type === 'kegiatan') {
            html += renderKegiatanCard(item);
        }
    });

    html += '</div>';
    container.innerHTML = html;

    // Apply display toggling based on filter classes
    applyFilter(filterMode);

    // Re-initialize Lucide icons for dynamically rendered content
    if (window.lucide) lucide.createIcons();
}

function applyFilter(filterMode) {
    if (filterMode === 'all') {
        document.querySelectorAll('.slot-filled').forEach(el => el.style.display = 'flex');
        document.querySelectorAll('.slot-empty').forEach(el => el.style.display = 'flex');
    } else if (filterMode === 'filled') {
        document.querySelectorAll('.slot-filled').forEach(el => el.style.display = 'flex');
        document.querySelectorAll('.slot-empty').forEach(el => el.style.display = 'none');
    } else if (filterMode === 'empty') {
        document.querySelectorAll('.slot-filled').forEach(el => el.style.display = 'none');
        document.querySelectorAll('.slot-empty').forEach(el => el.style.display = 'flex');
    }
}

function renderEmptySlot(item) {
    return `
        <div class="timeline-slot-empty slot-empty" onclick="scrollToForm()">
            <div style="min-width:90px;text-align:center;flex-shrink:0;">
                <div style="font-weight:600;font-size:.85rem;color:var(--text-muted);">
                    ${item.jam_mulai}
                </div>
                <div class="text-xs" style="color:var(--text-muted);opacity:.7;">
                    ${item.jam_selesai}
                </div>
            </div>
            <div style="width:3px;height:32px;border-radius:2px;flex-shrink:0;background:var(--border);opacity:.5;"></div>
            <div style="flex:1;min-width:0;display:flex;align-items:center;justify-content:space-between;">
                <span style="font-size:.85rem;color:var(--text-muted);font-style:italic;">Waktu Kosong</span>
                <button class="btn-add-slot" onclick="event.stopPropagation();scrollToForm()" title="Tambah Jadwal di slot ini">
                    <i data-lucide="plus" style="width:12px;height:12px;"></i> Tambah Jadwal
                </button>
            </div>
        </div>
    `;
}

function renderAktivitasCard(item) {
    const isSelesai = item.status === 'selesai';
    const isTerlewat = item.status === 'terlewat';
    const isBelum = item.status === 'belum';

    const dividerColor = isSelesai ? 'var(--accent-success)' : (isTerlewat ? 'var(--accent-danger)' : 'var(--primary-100)');
    const opacity = isSelesai ? 'opacity:0.65;' : '';
    const textDecor = isSelesai ? 'text-decoration:line-through;' : '';

    const habitBadge = item.is_habit
        ? '<span class="badge badge-info" style="font-size:.65rem;padding:2px 6px;"><i data-lucide="repeat" style="width:10px;height:10px;"></i> Habit</span>'
        : '';

    let statusBadge = '';
    if (isSelesai) statusBadge = '<span class="badge badge-success" style="font-size:.65rem;padding:2px 6px;">Selesai</span>';
    else if (isTerlewat) statusBadge = '<span class="badge badge-danger" style="font-size:.65rem;padding:2px 6px;">Terlewat</span>';
    else statusBadge = '<span class="badge badge-muted" style="font-size:.65rem;padding:2px 6px;">Belum</span>';

    // Action buttons
    let actionBtns = `
        <button onclick="editAktivitas(${item.id}, '${escapeJs(item.judul)}', '${item.jam_mulai}', ${item.durasi_menit}, ${item.is_habit})" title="Edit Aktivitas"
            style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1px solid var(--border);background:var(--bg);cursor:pointer;transition:all 0.2s;"
            onmouseenter="this.style.borderColor='var(--primary)';this.style.background='var(--primary-light)';"
            onmouseleave="this.style.borderColor='var(--border)';this.style.background='var(--bg)';">
            <i data-lucide="pencil" style="width:14px;height:14px;color:var(--primary);"></i>
        </button>
    `;

    if (!isSelesai) {
        actionBtns += `
            <button onclick="setAktivitasStatus(${item.id}, 'selesai')" title="Tandai Selesai"
                style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1px solid var(--border);background:var(--bg);cursor:pointer;transition:all 0.2s;"
                onmouseenter="this.style.borderColor='var(--accent-success)';this.style.background='var(--accent-success-light)';"
                onmouseleave="this.style.borderColor='var(--border)';this.style.background='var(--bg)';">
                <i data-lucide="check" style="width:16px;height:16px;color:var(--accent-success);"></i>
            </button>
        `;
    }

    if (isBelum) {
        actionBtns += `
            <button onclick="setAktivitasStatus(${item.id}, 'terlewat')" title="Tandai Terlewat"
                style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1px solid var(--border);background:var(--bg);cursor:pointer;transition:all 0.2s;"
                onmouseenter="this.style.borderColor='var(--accent-warning)';this.style.background='var(--accent-warning-light)';"
                onmouseleave="this.style.borderColor='var(--border)';this.style.background='var(--bg)';">
                <i data-lucide="x" style="width:16px;height:16px;color:var(--accent-warning);"></i>
            </button>
        `;
    }

    if (isSelesai || isTerlewat) {
        actionBtns += `
            <button onclick="setAktivitasStatus(${item.id}, 'belum')" title="Kembalikan ke Belum"
                style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1px solid var(--border);background:var(--bg);cursor:pointer;transition:all 0.2s;"
                onmouseenter="this.style.borderColor='var(--secondary)';this.style.background='var(--bg-secondary)';"
                onmouseleave="this.style.borderColor='var(--border)';this.style.background='var(--bg)';">
                <i data-lucide="rotate-ccw" style="width:14px;height:14px;color:var(--text-secondary);"></i>
            </button>
        `;
    }

    // Delete form + button
    actionBtns += `
        <form method="POST" action="/tugas/agenda/hapus/${item.id}/" style="margin:0;" id="hapusAkt${item.id}">
            <input type="hidden" name="csrfmiddlewaretoken" value="${window.CSRF_TOKEN}">
        </form>
        <button onclick="konfirmasiHapusAktivitas(${item.id}, '${escapeJs(item.judul)}')" title="Hapus"
            style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1px solid var(--border);background:var(--bg);cursor:pointer;transition:all 0.2s;"
            onmouseenter="this.style.background='var(--accent-danger-light)';this.style.borderColor='var(--accent-danger)'"
            onmouseleave="this.style.background='var(--bg)';this.style.borderColor='var(--border)'">
            <i data-lucide="trash-2" style="width:14px;height:14px;color:var(--accent-danger);"></i>
        </button>
    `;

    return `
        <div class="card aktivitas-item slot-filled" data-id="${item.id}"
            style="padding:16px 20px;display:flex;align-items:center;gap:14px;transition:all 0.2s;${opacity}">
            <div style="min-width:90px;text-align:center;flex-shrink:0;">
                <div style="font-weight:700;font-size:.95rem;color:var(--primary);">${item.jam_mulai}</div>
                <div class="text-xs" style="color:var(--text-muted);">${item.jam_selesai}</div>
                <div class="text-xs" style="color:var(--text-muted);margin-top:2px;">${item.durasi_menit} mnt</div>
            </div>
            <div style="width:3px;height:48px;border-radius:2px;flex-shrink:0;background:${dividerColor};"></div>
            <div style="flex:1;min-width:0;">
                <div style="font-weight:600;font-size:.95rem;color:var(--text-primary);${textDecor}">${escapeHtml(item.judul)}</div>
                <div style="display:flex;align-items:center;gap:6px;margin-top:4px;">${habitBadge}${statusBadge}</div>
            </div>
            <div class="akt-actions" style="display:flex;gap:6px;flex-shrink:0;align-items:center;">${actionBtns}</div>
        </div>
    `;
}

function renderKegiatanCard(item) {
    const isSelesai = item.status === 'selesai';
    const isDibatalkan = item.status === 'dibatalkan';

    const dividerColor = isSelesai ? 'var(--accent-success)' : (isDibatalkan ? 'var(--text-muted)' : '#6366F1');
    const cardStyle = isSelesai ? 'opacity:0.65;' : (isDibatalkan ? 'opacity:0.5;background:var(--border);' : '');
    const textDecor = isSelesai ? 'text-decoration:line-through;' : '';

    const kategoriMap = {
        'akademik': '<span class="badge badge-info" style="font-size:.65rem;padding:2px 6px;">Akademik</span>',
        'pekerjaan': '<span class="badge badge-warning" style="font-size:.65rem;padding:2px 6px;">Pekerjaan</span>',
        'keluarga': '<span class="badge badge-danger" style="font-size:.65rem;padding:2px 6px;background-color:#EF4444;color:white;">Keluarga</span>',
        'pribadi_sosial': '<span class="badge badge-success" style="font-size:.65rem;padding:2px 6px;">Pribadi & Sosial</span>',
        'acara': '<span class="badge badge-primary" style="font-size:.65rem;padding:2px 6px;background-color:#6366F1;color:white;">Acara</span>',
    };
    const kategoriBadge = kategoriMap[item.kategori] || '<span class="badge badge-muted" style="font-size:.65rem;padding:2px 6px;">Lainnya</span>';

    let statusBadge = '';
    if (isSelesai) statusBadge = '<span class="badge badge-success" style="font-size:.65rem;padding:2px 6px;">Selesai</span>';
    else if (isDibatalkan) statusBadge = '<span class="badge badge-danger" style="font-size:.65rem;padding:2px 6px;">Dibatalkan</span>';
    else statusBadge = '<span class="badge badge-muted" style="font-size:.65rem;padding:2px 6px;">Akan Datang</span>';

    let lokasiHtml = '';
    if (item.lokasi) {
        if (item.lokasi.includes('http')) {
            lokasiHtml = `<a href="${escapeHtml(item.lokasi)}" target="_blank" class="text-xs" style="display:inline-flex;align-items:center;gap:4px;color:var(--primary);text-decoration:none;font-weight:500;"><i data-lucide="video" style="width:12px;height:12px;"></i> Zoom/Meet</a>`;
        } else {
            lokasiHtml = `<span class="text-xs" style="display:inline-flex;align-items:center;gap:4px;color:var(--text-muted);"><i data-lucide="map-pin" style="width:12px;height:12px;"></i> ${escapeHtml(item.lokasi)}</span>`;
        }
    }

    return `
        <div class="card kegiatan-item slot-filled"
            style="padding:16px 20px;display:flex;align-items:center;gap:14px;transition:all 0.2s;border-left:4px solid #6366F1;${cardStyle}">
            <div style="min-width:90px;text-align:center;flex-shrink:0;">
                <div style="font-weight:700;font-size:.95rem;color:#6366F1;">${item.jam_mulai}</div>
                <div class="text-xs" style="color:var(--text-muted);">${item.jam_selesai}</div>
                <div class="text-xs" style="color:var(--text-muted);margin-top:2px;">Acara</div>
            </div>
            <div style="width:3px;height:48px;border-radius:2px;flex-shrink:0;background:${dividerColor};"></div>
            <div style="flex:1;min-width:0;">
                <div style="font-weight:600;font-size:.95rem;color:var(--text-primary);${textDecor}">${escapeHtml(item.judul)}</div>
                <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:4px;">
                    ${kategoriBadge}${statusBadge}${lokasiHtml}
                </div>
            </div>
            <div style="flex-shrink:0;">
                <a href="/tugas/kegiatan/?kategori=${item.kategori}&status_filter=${item.status}" title="Kelola Kegiatan"
                    style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1px solid var(--border);background:var(--bg);cursor:pointer;transition:all 0.2s;text-decoration:none;"
                    onmouseenter="this.style.borderColor='var(--primary)';this.style.background='var(--primary-light)';"
                    onmouseleave="this.style.borderColor='var(--border)';this.style.background='var(--bg)';">
                    <i data-lucide="calendar" style="width:14px;height:14px;color:var(--primary);"></i>
                </a>
            </div>
        </div>
    `;
}

// ── Helper: Scroll to Add Form ──
function scrollToForm() {
    const formCard = document.getElementById('formTambahCard');
    if (formCard) {
        formCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        formCard.style.animation = 'none';
        formCard.offsetHeight; // trigger reflow
        formCard.style.animation = 'fadeUp 0.4s ease';
    }
}

// ── Helper: HTML Escape ──
function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// ── Helper: JS String Escape ──
function escapeJs(text) {
    return text.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"');
}


// ══════════════════════════════════════════════════════════════════════
// NOTIFIKASI PENGINGAT REAL-TIME
// ══════════════════════════════════════════════════════════════════════

const _notifiedSchedules = new Set();

function checkScheduleReminders() {
    const config = document.getElementById('agenda-config');
    if (!config || config.getAttribute('data-is-today') !== 'true') return;

    const apiUrl = config.getAttribute('data-api-today-url');
    if (!apiUrl) return;

    fetch(apiUrl, {
        headers: { 'X-CSRFToken': window.CSRF_TOKEN }
    })
    .then(r => r.json())
    .then(data => {
        if (!data.items || data.items.length === 0) return;

        const now = new Date();
        const nowMinutes = now.getHours() * 60 + now.getMinutes();

        data.items.forEach(item => {
            const [h, m] = item.jam_mulai.split(':').map(Number);
            const itemMinutes = h * 60 + m;
            const diff = itemMinutes - nowMinutes;

            // Notify if within 5 minutes and not already notified
            const notifKey = `${item.judul}_${item.jam_mulai}`;
            if (diff >= 0 && diff <= 5 && !_notifiedSchedules.has(notifKey)) {
                _notifiedSchedules.add(notifKey);
                showScheduleReminder(item.judul, item.jam_mulai);
            }
        });
    })
    .catch(err => console.error('Reminder check error:', err));
}

function showScheduleReminder(judul, jamMulai) {
    Swal.fire({
        toast: true,
        position: 'top-end',
        iconHtml: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>`,
        title: 'Pengingat Jadwal',
        html: `<span style="font-size:.875rem;color:var(--text-secondary);">Jadwal '<strong>${escapeHtml(judul)}</strong>' akan dimulai pada <strong>${jamMulai}</strong>!</span>`,
        showConfirmButton: false,
        timer: 8000,
        timerProgressBar: true,
        customClass: {
            popup: 'swal-reminder-toast'
        }
    });
}


// ══════════════════════════════════════════════════════════════════════
// DOM READY INITIALIZATION
// ══════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', function() {
    // Init time input picker listeners for all static time inputs
    const timeInputs = document.querySelectorAll('input[type="time"]');
    timeInputs.forEach(initTimeInputPicker);

    // ── Render Timeline (default: filled only) ──
    renderTimeline('filled');

    // ── Filter Button Handlers ──
    document.querySelectorAll('[data-filter]').forEach(btn => {
        btn.addEventListener('click', function() {
            // Hapus class active dari semua filter button
            document.querySelectorAll('[data-filter]').forEach(b => b.classList.remove('active', 'bg-white', 'shadow-sm'));
            this.classList.add('active', 'bg-white', 'shadow-sm');

            const filterType = this.getAttribute('data-filter'); // 'all', 'filled', 'empty'

            renderTimeline(filterType);

            if (filterType === 'all') {
                document.querySelectorAll('.slot-filled, .slot-empty').forEach(el => el.style.display = 'flex');
            } else if (filterType === 'filled') {
                document.querySelectorAll('.slot-filled').forEach(el => el.style.display = 'flex');
                document.querySelectorAll('.slot-empty').forEach(el => el.style.display = 'none');
            } else if (filterType === 'empty') {
                document.querySelectorAll('.slot-filled').forEach(el => el.style.display = 'none');
                document.querySelectorAll('.slot-empty').forEach(el => el.style.display = 'flex');
            }
        });
    });

    // ── Copy Jadwal Kemarin Event Listener ──
    const btnCopyKemarin = document.getElementById('btnCopyKemarin');
    if (btnCopyKemarin) {
        btnCopyKemarin.addEventListener('click', function() {
            const yesterdayScript = document.getElementById('yesterday-data');
            if (!yesterdayScript) return;
            const yesterdayData = JSON.parse(yesterdayScript.textContent);
            const tanggalAktif = btnCopyKemarin.getAttribute('data-tanggal');
            const copyUrl = btnCopyKemarin.getAttribute('data-copy-url');

            let checkboxesHtml = yesterdayData.map((akt, idx) => `
                <div class="yesterday-item-card">
                    <div style="display:flex;align-items:center;gap:8px;flex:1;min-width:0;">
                        <input type="checkbox" id="akt-cb-${idx}" checked style="width:18px;height:18px;cursor:pointer;flex-shrink:0;accent-color:#4F46E5;">
                        <input type="text" id="akt-judul-${idx}" class="form-input-swal" value="${akt.judul}" style="font-weight:500;" placeholder="Nama aktivitas...">
                    </div>
                    <div style="width:110px;flex-shrink:0;">
                        <input type="time" id="akt-jam-${idx}" class="form-input-swal" value="${akt.jam_mulai}">
                    </div>
                    <div style="width:90px;flex-shrink:0;">
                        <input type="number" id="akt-durasi-${idx}" class="form-input-swal" value="${akt.durasi_menit}" min="5" max="480">
                    </div>
                </div>
            `).join('');

            Swal.fire({
                title: 'Salin Jadwal Kemarin',
                html: `
                    <div style="text-align:left;margin-bottom:12px;">
                        <p style="font-size:.875rem;color:var(--text-secondary);margin:0 0 16px 0;line-height:1.5;">Pilih aktivitas yang ingin disalin. Anda dapat menyesuaikan nama, jam mulai, dan durasi sebelum menyimpan ke hari ini.</p>
                        <div style="display:flex;align-items:center;gap:12px;padding:0 1rem;margin-bottom:8px;">
                            <div style="flex:1;font-size:.75rem;font-weight:700;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.05em;display:flex;align-items:center;gap:8px;padding-left:26px;">Aktivitas</div>
                            <div style="width:110px;font-size:.75rem;font-weight:700;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.05em;">Jam Mulai</div>
                            <div style="width:90px;font-size:.75rem;font-weight:700;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.05em;">Durasi (Mnt)</div>
                        </div>
                        <div style="max-height:360px;overflow-y:auto;padding-right:4px;">${checkboxesHtml}</div>
                    </div>
                `,
                width: '680px',
                customClass: {
                    popup: 'swal-custom-modal',
                    actions: 'swal-actions-gap',
                    confirmButton: 'btn-indigo-primary',
                    cancelButton: 'btn-slate-secondary'
                },
                buttonsStyling: false,
                showCancelButton: true,
                confirmButtonText: '<i data-lucide="clipboard-copy" style="width:14px;height:14px;margin-right:4px;"></i> Salin ke Hari Ini',
                cancelButtonText: 'Batal',
                didOpen: () => {
                    if (window.lucide) {
                        lucide.createIcons();
                    }
                    const modalTimeInputs = Swal.getHtmlContainer().querySelectorAll('input[type="time"]');
                    modalTimeInputs.forEach(initTimeInputPicker);
                },
                preConfirm: () => {
                    const selected = [];
                    yesterdayData.forEach((akt, idx) => {
                        const cb = document.getElementById(`akt-cb-${idx}`);
                        if (cb && cb.checked) {
                            selected.push({
                                judul: document.getElementById(`akt-judul-${idx}`).value.trim(),
                                jam_mulai: document.getElementById(`akt-jam-${idx}`).value,
                                durasi_menit: parseInt(document.getElementById(`akt-durasi-${idx}`).value) || 30,
                                is_habit: akt.is_habit
                            });
                        }
                    });
                    if (selected.length === 0) {
                        Swal.showValidationMessage('Pilih minimal 1 aktivitas!');
                        return false;
                    }
                    return selected;
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(copyUrl, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken') || window.CSRF_TOKEN,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            tanggal: tanggalAktif,
                            aktivitas: result.value
                        })
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Berhasil!',
                                text: data.message,
                                confirmButtonColor: '#4F46E5',
                                timer: 2000,
                                timerProgressBar: true,
                            }).then(() => {
                                window.location.reload();
                            });
                        } else {
                            Swal.fire({ icon: 'error', title: 'Gagal', text: data.error || 'Terjadi kesalahan.' });
                        }
                    })
                    .catch(() => Swal.fire({ icon: 'error', title: 'Error', text: 'Gagal mengirim data.' }));
                }
            });
        });
    }

    // Auto-scroll ke form jika ada error overlap
    const formCard = document.getElementById('formTambahCard');
    if (formCard && formCard.getAttribute('data-has-error') === 'true') {
        formCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        formCard.style.animation = 'fadeUp 0.3s ease';
    }

    // AJAX form submission handler for formTambahAktivitas
    const formTambahAktivitas = document.getElementById('formTambahAktivitas');
    if (formTambahAktivitas) {
        formTambahAktivitas.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(formTambahAktivitas);

            fetch(formTambahAktivitas.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken') || window.CSRF_TOKEN
                },
                body: formData
            })
            .then(res => {
                if (!res.ok) {
                    return res.json().then(data => { throw new Error(data.error || 'Terjadi kesalahan'); });
                }
                return res.json();
            })
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        toast: true,
                        position: 'top-end',
                        icon: 'success',
                        title: 'Berhasil!',
                        html: `<span style="font-size:.875rem;color:var(--text-secondary);">Aktivitas berhasil ditambahkan</span>`,
                        showConfirmButton: false,
                        timer: 1500,
                        timerProgressBar: true
                    }).then(() => {
                        location.reload();
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Gagal!',
                        text: data.error || 'Terjadi kesalahan.',
                        confirmButtonColor: 'var(--primary)'
                    });
                }
            })
            .catch(err => {
                Swal.fire({
                    icon: 'error',
                    title: 'Gagal!',
                    text: err.message,
                    confirmButtonColor: 'var(--primary)'
                });
            });
        });
    }

    // Django messages parser
    const messageElements = document.querySelectorAll('#django-messages .django-message');
    messageElements.forEach(msg => {
        const tags = msg.getAttribute('data-tags');
        const text = msg.getAttribute('data-text');
        let icon = 'info';
        let title = 'Info';
        if (tags === 'success') {
            icon = 'success';
            title = 'Berhasil!';
        } else if (tags === 'danger' || tags === 'error') {
            icon = 'error';
            title = 'Gagal!';
        } else if (tags === 'warning') {
            icon = 'warning';
            title = 'Peringatan!';
        }
        Swal.fire({
            icon: icon,
            title: title,
            text: text,
            confirmButtonColor: '#4F46E5',
            timer: 3000,
            timerProgressBar: true,
        });
    });

    // ── Start Reminder Check Interval (every 30 seconds) ──
    checkScheduleReminders(); // Check immediately on load
    setInterval(checkScheduleReminders, 30000);
});
