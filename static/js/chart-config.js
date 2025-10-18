document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById("tugasChart").getContext("2d");

    const tugasChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Selesai", "Belum Selesai"],
            datasets: [{
                label: "Jumlah Tugas",
                data: [selesai, belumSelesai], // 🔹 Data dari Django (akan kita tambahkan di template)
                backgroundColor: ["#36A2EB", "#FF6384"],
                borderColor: ["#007bb5", "#ff4c4c"],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
});
