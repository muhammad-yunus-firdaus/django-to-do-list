// Pastikan modal & tombol terformat sesuai Design System
const swalModalConfig = {
    customClass: {
        popup: 'swal-custom-modal',
        confirmButton: 'btn-indigo-primary',
        cancelButton: 'btn-slate-secondary',
        actions: 'swal-actions-gap'
    },
    buttonsStyling: false
};

// Kustom config khusus untuk form tambah/edit kegiatan yang melebar & responsif
const swalKegiatanConfig = {
    ...swalModalConfig,
    customClass: {
        ...swalModalConfig.customClass,
        popup: 'swal-kegiatan-modal'
    },
    width: '720px'
};

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
    formData.append('judul', data.judul);
    formData.append('kategori', data.kategori);
    formData.append('status', data.status);
    formData.append('tanggal', data.tanggal);
    formData.append('jam_mulai', data.jam_mulai);
    formData.append('jam_selesai', data.jam_selesai);
    formData.append('lokasi', data.lokasi);
    formData.append('catatan', data.catatan);
    formData.append('csrfmiddlewaretoken', window.CSRF_TOKEN);
    return formData;
}

function manageAlert(popup, errorMsg) {
    const alertBox = popup.querySelector('#swal-error-alert');
    if (!alertBox) return;
    if (errorMsg) {
        alertBox.querySelector('.error-text').textContent = errorMsg;
        alertBox.style.display = 'flex';
    } else {
        alertBox.style.display = 'none';
        alertBox.querySelector('.error-text').textContent = '';
    }
}

function initModalAlertListeners(popup) {
    const judulInput = popup.querySelector('#swal-judul');
    const alertBox = popup.querySelector('#swal-error-alert');
    if (judulInput && alertBox) {
        judulInput.addEventListener('input', () => {
            if (judulInput.value.trim()) {
                alertBox.style.display = 'none';
                alertBox.querySelector('.error-text').textContent = '';
            }
        });
    }
}

function bukaModalTambah() {
    Swal.fire({
        ...swalKegiatanConfig,
        title: 'Tambah Kegiatan Baru',
        html: document.getElementById('kegiatanFormTemplate').innerHTML,
        showCancelButton: true,
        confirmButtonText: 'Simpan',
        cancelButtonText: 'Batal',
        didOpen: () => {
            const popup = Swal.getPopup();
            const hariIni = new Date().toISOString().split('T')[0];
            popup.querySelector('#swal-tanggal').value = hariIni;
            popup.querySelector('#swal-status').value = 'akan_datang';
            manageAlert(popup, null);
            initModalAlertListeners(popup);
        },
        preConfirm: () => {
            const popup = Swal.getPopup();
            const data = dapatkanFormData(popup);
            
            if (!data.judul) {
                manageAlert(popup, 'Mohon lengkapi judul kegiatan Anda terlebih dahulu.');
                return false;
            }
            if (!data.tanggal) {
                manageAlert(popup, 'Tanggal kegiatan harus ditentukan!');
                return false;
            }
            if (!data.jam_mulai || !data.jam_selesai) {
                manageAlert(popup, 'Jam mulai & selesai harus ditentukan!');
                return false;
            }
            if (data.jam_selesai <= data.jam_mulai) {
                manageAlert(popup, 'Jam selesai harus setelah jam mulai!');
                return false;
            }
            return data;
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const payload = serializeFormData(result.value);
            
            const urlTambah = document.getElementById('kegiatan-urls').getAttribute('data-tambah');
            fetch(urlTambah, {
                method: 'POST',
                body: payload
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Berhasil!',
                        text: 'Kegiatan berhasil ditambahkan.',
                        showConfirmButton: false,
                        showCancelButton: false,
                        timer: 1400,
                        timerProgressBar: true,
                        customClass: {
                            popup: 'swal-success-popup-custom',
                            title: 'swal-success-title-custom',
                            htmlContainer: 'swal-success-text-custom'
                        }
                    }).then(() => {
                        location.reload();
                    });
                } else {
                    Swal.fire({
                        ...swalModalConfig,
                        title: 'Gagal Menyimpan!',
                        text: data.error,
                        icon: 'error',
                        showCancelButton: false,
                        confirmButtonText: 'OK'
                    });
                }
            })
            .catch(err => {
                Swal.fire({
                    ...swalModalConfig,
                    title: 'Error!',
                    text: 'Terjadi kegagalan koneksi.',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
            });
        }
    });
}

function bukaModalEdit(id) {
    // Fetch data kegiatan
    fetch(`/tugas/kegiatan/edit/${id}/`)
    .then(res => res.json())
    .then(resData => {
        if (resData.success) {
            const d = resData.data;
            Swal.fire({
                ...swalKegiatanConfig,
                title: 'Edit Kegiatan',
                html: document.getElementById('kegiatanFormTemplate').innerHTML,
                showCancelButton: true,
                confirmButtonText: 'Perbarui',
                cancelButtonText: 'Batal',
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
                    manageAlert(popup, null);
                    initModalAlertListeners(popup);
                },
                preConfirm: () => {
                    const popup = Swal.getPopup();
                    const data = dapatkanFormData(popup);
                    
                    if (!data.judul) {
                        manageAlert(popup, 'Mohon lengkapi judul kegiatan Anda terlebih dahulu.');
                        return false;
                    }
                    if (!data.tanggal) {
                        manageAlert(popup, 'Tanggal kegiatan harus ditentukan!');
                        return false;
                    }
                    if (!data.jam_mulai || !data.jam_selesai) {
                        manageAlert(popup, 'Jam mulai & selesai harus ditentukan!');
                        return false;
                    }
                    if (data.jam_selesai <= data.jam_mulai) {
                        manageAlert(popup, 'Jam selesai harus setelah jam mulai!');
                        return false;
                    }
                    return data;
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    const payload = serializeFormData(result.value);
                    
                    fetch(`/tugas/kegiatan/edit/${id}/`, {
                        method: 'POST',
                        body: payload
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Berhasil!',
                                text: 'Kegiatan berhasil diperbarui.',
                                showConfirmButton: false,
                                showCancelButton: false,
                                timer: 1400,
                                timerProgressBar: true,
                                customClass: {
                                    popup: 'swal-success-popup-custom',
                                    title: 'swal-success-title-custom',
                                    htmlContainer: 'swal-success-text-custom'
                                }
                            }).then(() => {
                                location.reload();
                            });
                        } else {
                            Swal.fire({
                                ...swalModalConfig,
                                title: 'Gagal Memperbarui!',
                                text: data.error,
                                icon: 'error',
                                showCancelButton: false,
                                confirmButtonText: 'OK'
                            });
                        }
                    });
                }
            });
        }
    });
}

function konfirmasiHapusKegiatan(id, judul, event) {
    if (event) {
        event.preventDefault();
        event.stopImmediatePropagation();
    }
    Swal.fire({
        ...swalModalConfig,
        title: 'Hapus Kegiatan?',
        text: 'Kegiatan ini akan dihapus secara permanen.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Ya, Hapus',
        cancelButtonText: 'Batal',
        customClass: {
            ...swalModalConfig.customClass,
            confirmButton: 'btn-danger-primary'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', window.CSRF_TOKEN);

            fetch(`/tugas/kegiatan/hapus/${id}/`, {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Dihapus!',
                        text: 'Kegiatan berhasil dihapus.',
                        showConfirmButton: false,
                        showCancelButton: false,
                        timer: 1400,
                        timerProgressBar: true,
                        customClass: {
                            popup: 'swal-success-popup-custom',
                            title: 'swal-success-title-custom',
                            htmlContainer: 'swal-success-text-custom'
                        }
                    }).then(() => {
                        location.reload();
                    });
                }
            });
        }
    });
}

function quickFinishKegiatan(id) {
    updateKegiatanStatus(id, 'selesai', 'Kegiatan ditandai selesai!');
}

function quickUndoKegiatan(id) {
    updateKegiatanStatus(id, 'akan_datang', 'Status kegiatan dikembalikan.');
}

function updateKegiatanStatus(id, status, toastMsg) {
    const urlTemplate = document.getElementById('kegiatan-urls').getAttribute('data-toggle');
    const url = urlTemplate.replace('/0/', `/${id}/`);
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': window.CSRF_TOKEN,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: status })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Berhasil!',
                text: toastMsg,
                showConfirmButton: false,
                showCancelButton: false,
                timer: 1400,
                timerProgressBar: true,
                customClass: {
                    popup: 'swal-success-popup-custom',
                    title: 'swal-success-title-custom',
                    htmlContainer: 'swal-success-text-custom'
                }
            }).then(() => {
                location.reload();
            });
        } else {
            Swal.fire({
                ...swalModalConfig,
                title: 'Gagal!',
                text: data.error || 'Gagal memperbarui status kegiatan.',
                icon: 'error',
                showCancelButton: false,
                confirmButtonText: 'OK'
            });
        }
    })
    .catch(err => {
        Swal.fire({
            ...swalModalConfig,
            title: 'Error!',
            text: 'Terjadi kegagalan koneksi.',
            icon: 'error',
            showCancelButton: false,
            confirmButtonText: 'OK'
        });
    });
}

