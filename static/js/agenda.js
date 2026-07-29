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

function editAktivitas(id, judul, jamMulai, durasi, isHabit) {
    Swal.fire({
        title: 'Edit Aktivitas',
        html: `
            <div style="text-align:left; display:flex; flex-direction:column; gap:12px;">
                <div>
                    <label class="form-label" style="display:block; font-size:0.875rem; font-weight:600; margin-bottom:6px;">Aktivitas</label>
                    <input id="swal-judul" class="form-input" type="text" value="${judul}">
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
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
                lucide.createIcons(); // Initialize layout icons
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

// Helper to get CSRF cookie value safely
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

document.addEventListener('DOMContentLoaded', function() {
    // Init time input picker listeners for all static time inputs
    const timeInputs = document.querySelectorAll('input[type="time"]');
    timeInputs.forEach(initTimeInputPicker);

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
                    // Add time input pickers to dynamically generated inputs inside modal
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
});
