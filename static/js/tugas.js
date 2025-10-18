function konfirmasiHapus(tugasId, tugasJudul) {
    Swal.fire({
        title: `Hapus Tugas?`,
        html: `<b>"${tugasJudul}"</b> akan dihapus secara permanen!`,
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#d33",
        cancelButtonColor: "#3085d6",
        confirmButtonText: "Ya, Hapus",
        cancelButtonText: "Batal",
        reverseButtons: true,
        customClass: {
            popup: "animate__animated animate__fadeInDown"
        }
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = `/tugas/hapus/${tugasId}/`;
        }
    });
}
