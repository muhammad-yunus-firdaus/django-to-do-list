/**
 * KEGIATAN.JS — Zero-Lag AJAX, Instant DOM updates, and Sonner-style Toast
 * Pure Vanilla JS, <250 lines, Zero AI-Slop
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

function dapatkanFormData(container) {
    const root = container || Swal.getPopup() || document;
    return {
        judul: (root.querySelector('#swal-judul')?.value || '').trim(),
        kategori: root.querySelector('#swal-kategori')?.value || '',
        status: root.querySelector('#swal-status')?.value || '',
        tanggal: root.querySelector('#swal-tanggal')?.value || '',
        jam_mulai: root.querySelector('#swal-jam_mulai')?.value || '',
        jam_selesai: root.querySelector('#swal-jam_selesai')?.value || '',
        lokasi: root.querySelector('#swal-lokasi')?.value || '',
        catatan: root.querySelector('#swal-catatan')?.value || '',
    };
}

function serializeFormData(data) {
    const formData = new FormData();
    for (const [key, value] of Object.entries(data)) {
        formData.append(key, value);
    }
    formData.append('csrfmiddlewaretoken', getCsrfToken());
    return formData;
}

// ── Buka Modal Tambah Kegiatan ──
function bukaModalTambah() {
    const template = document.getElementById('kegiatanFormTemplate');
    if (!template) return;

    Swal.fire({
        title: 'Tambah Acara / Pertemuan',
        html: template.innerHTML,
        showCancelButton: true,
        confirmButtonText: 'Simpan Acara',
        cancelButtonText: 'Batal',
        customClass: {
            popup: 'swal-custom-modal',
            confirmButton: 'btn btn-primary',
            cancelButton: 'btn btn-outline',
            actions: 'swal2-actions'
        },
        buttonsStyling: false,
        didOpen: () => {
            const popup = Swal.getPopup();
            popup.querySelector('#swal-tanggal').value = new Date().toISOString().split('T')[0];
            popup.querySelector('#swal-status').value = 'akan_datang';
        },
        preConfirm: () => {
            const popup = Swal.getPopup();
            const data = dapatkanFormData(popup);

            if (!data.judul) {
                Swal.showValidationMessage('Judul kegiatan wajib diisi');
                return false;
            }
            if (!data.tanggal) {
                Swal.showValidationMessage('Tanggal kegiatan wajib ditentukan');
                return false;
            }
            if (!data.jam_mulai || !data.jam_selesai) {
                Swal.showValidationMessage('Jam mulai dan selesai wajib ditentukan');
                return false;
            }
            if (data.jam_selesai <= data.jam_mulai) {
                Swal.showValidationMessage('Jam selesai harus setelah jam mulai');
                return false;
            }
            return data;
        }
    }).then(async (result) => {
        if (!result.isConfirmed) return;

        const confirmBtn = Swal.getConfirmButton();
        if (confirmBtn) confirmBtn.disabled = true;

        const payload = serializeFormData(result.value);
        const urlTambah = document.getElementById('kegiatan-urls').getAttribute('data-tambah');

        try {
            const res = await fetch(urlTambah, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: payload
            });
            const data = await res.json();
            if (data.success) {
                if (window.showToast) window.showToast('Acara baru berhasil disimpan', 'success');
                setTimeout(() => location.reload(), 400);
            } else {
                if (window.showToast) window.showToast(data.error || 'Gagal menyimpan acara', 'error');
            }
        } catch (err) {
            console.error('Tambah kegiatan error:', err);
            if (window.showToast) window.showToast('Koneksi terganggu', 'error');
        }
    });
}

// ── Buka Modal Edit Kegiatan ──
async function bukaModalEdit(id) {
    try {
        const res = await fetch(`/tugas/kegiatan/edit/${id}/`);
        const resData = await res.json();
        if (!resData.success) {
            if (window.showToast) window.showToast('Gagal memuat data kegiatan', 'error');
            return;
        }

        const d = resData.data;
        const template = document.getElementById('kegiatanFormTemplate');

        Swal.fire({
            title: 'Edit Acara / Pertemuan',
            html: template.innerHTML,
            showCancelButton: true,
            confirmButtonText: 'Perbarui Acara',
            cancelButtonText: 'Batal',
            customClass: {
                popup: 'swal-custom-modal',
                confirmButton: 'btn btn-primary',
                cancelButton: 'btn btn-outline',
                actions: 'swal2-actions'
            },
            buttonsStyling: false,
            didOpen: () => {
                const popup = Swal.getPopup();
                popup.querySelector('#swal-judul').value = d.judul;
                popup.querySelector('#swal-kategori').value = d.kategori;
                popup.querySelector('#swal-status').value = d.status;
                popup.querySelector('#swal-tanggal').value = d.tanggal;
                popup.querySelector('#swal-jam_mulai').value = d.jam_mulai;
                popup.querySelector('#swal-jam_selesai').value = d.jam_selesai;
                popup.querySelector('#swal-lokasi').value = d.lokasi || '';
                popup.querySelector('#swal-catatan').value = d.catatan || '';
            },
            preConfirm: () => {
                const popup = Swal.getPopup();
                const data = dapatkanFormData(popup);

                if (!data.judul) {
                    Swal.showValidationMessage('Judul kegiatan wajib diisi');
                    return false;
                }
                if (!data.tanggal) {
                    Swal.showValidationMessage('Tanggal kegiatan wajib ditentukan');
                    return false;
                }
                if (!data.jam_mulai || !data.jam_selesai) {
                    Swal.showValidationMessage('Jam mulai dan selesai wajib ditentukan');
                    return false;
                }
                if (data.jam_selesai <= data.jam_mulai) {
                    Swal.showValidationMessage('Jam selesai harus setelah jam mulai');
                    return false;
                }
                return data;
            }
        }).then(async (result) => {
            if (!result.isConfirmed) return;

            const payload = serializeFormData(result.value);
            try {
                const res = await fetch(`/tugas/kegiatan/edit/${id}/`, {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                    body: payload
                });
                const data = await res.json();
                if (data.success) {
                    if (window.showToast) window.showToast('Perubahan acara berhasil disimpan', 'success');
                    setTimeout(() => location.reload(), 400);
                } else {
                    if (window.showToast) window.showToast(data.error || 'Gagal memperbarui kegiatan', 'error');
                }
            } catch (err) {
                console.error('Edit kegiatan error:', err);
                if (window.showToast) window.showToast('Koneksi terganggu', 'error');
            }
        });
    } catch (err) {
        console.error('Load edit error:', err);
    }
}

// ── Konfirmasi Hapus Kegiatan (Optimistic DOM Removal) ──
function konfirmasiHapusKegiatan(id, judul, event) {
    if (event) {
        event.preventDefault();
        event.stopImmediatePropagation();
    }

    Swal.fire({
        title: 'Hapus Acara?',
        text: `Acara "${judul}" akan dihapus permanen.`,
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

        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', getCsrfToken());

        try {
            const res = await fetch(`/tugas/kegiatan/hapus/${id}/`, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            });
            const data = await res.json();
            if (data.success) {
                const card = document.querySelector(`.keg-card[data-id="${id}"]`) || document.getElementById(`kegCard-${id}`);
                if (card) {
                    card.style.transition = 'all 0.25s ease';
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.95)';
                    setTimeout(() => card.remove(), 250);
                }
                if (window.showToast) window.showToast('Acara berhasil dihapus', 'success');
            }
        } catch (err) {
            console.error('Delete kegiatan error:', err);
            if (window.showToast) window.showToast('Koneksi terganggu', 'error');
        }
    });
}

// ── Quick Finish & Undo (Optimistic UI) ──
function quickFinishKegiatan(id) {
    updateKegiatanStatus(id, 'selesai', 'Kegiatan ditandai selesai');
}

function quickUndoKegiatan(id) {
    updateKegiatanStatus(id, 'akan_datang', 'Status kegiatan dikembalikan ke akan datang');
}

async function updateKegiatanStatus(id, status, toastMsg) {
    const urlTemplate = document.getElementById('kegiatan-urls').getAttribute('data-toggle');
    const url = urlTemplate.replace('/0/', `/${id}/`);

    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ status: status })
        });
        const data = await res.json();
        if (data.success) {
            const card = document.querySelector(`.keg-card[data-id="${id}"]`) || document.getElementById(`kegCard-${id}`);
            if (card) {
                const statusBadge = card.querySelector('.keg-status-badge');
                if (statusBadge) {
                    if (status === 'selesai') {
                        statusBadge.className = 'badge badge-success keg-status-badge';
                        statusBadge.innerHTML = '<i data-lucide="check" style="width:10px;height:10px;"></i> Selesai';
                    } else {
                        statusBadge.className = 'badge badge-secondary keg-status-badge';
                        statusBadge.innerHTML = '<i data-lucide="clock-3" style="width:10px;height:10px;"></i> Akan Datang';
                    }
                }

                const actionWrapper = card.querySelector('.keg-quick-action');
                if (actionWrapper) {
                    if (status === 'selesai') {
                        actionWrapper.innerHTML = `
                            <button onclick="quickUndoKegiatan(${id})" class="btn btn-outline btn-icon" title="Kembalikan" type="button">
                                <i data-lucide="rotate-ccw" style="width:14px;height:14px;"></i>
                            </button>
                        `;
                    } else {
                        actionWrapper.innerHTML = `
                            <button onclick="quickFinishKegiatan(${id})" class="btn btn-outline btn-icon" title="Tandai Selesai" type="button">
                                <i data-lucide="check" style="width:14px;height:14px;color:var(--success);"></i>
                            </button>
                        `;
                    }
                }
                if (window.lucide) lucide.createIcons();
            }
            if (window.showToast) window.showToast(toastMsg, 'success');
        } else {
            if (window.showToast) window.showToast(data.error || 'Gagal memperbarui status', 'error');
        }
    } catch (err) {
        console.error('Update status kegiatan error:', err);
        if (window.showToast) window.showToast('Koneksi terganggu', 'error');
    }
}
