/**
 * command-palette.js — Global Command Palette (Ctrl+K / Cmd+K)
 * Clean, modular (<180 lines), zero external libraries.
 */
(() => {
    const COMMANDS = [
        { group: 'Navigasi Cepat', label: 'Dashboard', icon: 'layout-dashboard', url: '/tugas/dashboard/' },
        { group: 'Navigasi Cepat', label: 'Daftar Tugas', icon: 'list-todo', url: '/tugas/' },
        { group: 'Navigasi Cepat', label: 'Jadwal Hari Ini (Agenda)', icon: 'calendar-clock', url: '/tugas/agenda/' },
        { group: 'Navigasi Cepat', label: 'Kegiatan & Acara', icon: 'calendar-days', url: '/tugas/kegiatan/' },
        { group: 'Navigasi Cepat', label: 'Evaluasi Mingguan', icon: 'bar-chart-3', url: '/tugas/evaluasi/' },
        { group: 'Navigasi Cepat', label: 'Edit Profil Pengguna', icon: 'user-cog', url: '/tugas/profil/' },
        { group: 'Aksi Cepat', label: 'Tambah Tugas Baru', icon: 'plus-circle', url: '/tugas/tambah/' },
        { group: 'Aksi Cepat', label: 'Buka Focus Timer (Pomodoro)', icon: 'timer', action: () => window.openPomodoroModal && window.openPomodoroModal() },
        { group: 'Aksi Cepat', label: 'Ekspor Data Dokumen (PDF / Excel)', icon: 'file-down', action: () => window.openExportModal && window.openExportModal() }
    ];

    let overlay = null;
    let input = null;
    let listContainer = null;
    let selectedIndex = 0;
    let filteredCommands = [...COMMANDS];

    function createPaletteDOM() {
        if (overlay) return;
        overlay = document.createElement('div');
        overlay.id = 'commandPaletteModal';
        overlay.className = 'cmd-palette-overlay';
        overlay.innerHTML = `
            <div class="cmd-palette-box" onclick="event.stopPropagation()">
                <div class="cmd-palette-search">
                    <i data-lucide="search" style="width:16px;height:16px;color:var(--foreground-muted);"></i>
                    <input type="text" class="cmd-palette-input" placeholder="Ketik perintah atau cari navigasi..." autocomplete="off" spellcheck="false">
                    <kbd class="cmd-kbd">ESC</kbd>
                </div>
                <div class="cmd-palette-list"></div>
                <div class="cmd-palette-footer">
                    <span>Gunakan <kbd class="cmd-kbd">↑</kbd> <kbd class="cmd-kbd">↓</kbd> untuk memilih</span>
                    <span>Tekan <kbd class="cmd-kbd">Enter</kbd> untuk buka</span>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        input = overlay.querySelector('.cmd-palette-input');
        listContainer = overlay.querySelector('.cmd-palette-list');

        overlay.addEventListener('click', closePalette);
        input.addEventListener('input', onSearchInput);
        input.addEventListener('keydown', onKeyNav);
    }

    function renderList() {
        if (!listContainer) return;
        if (filteredCommands.length === 0) {
            listContainer.innerHTML = `
                <div style="padding:1.5rem;text-align:center;color:var(--foreground-muted);font-size:0.8125rem;">
                    Tidak ada perintah atau navigasi yang cocok.
                </div>
            `;
            return;
        }

        let html = '';
        let lastGroup = '';

        filteredCommands.forEach((cmd, idx) => {
            if (cmd.group !== lastGroup) {
                lastGroup = cmd.group;
                html += `<div class="cmd-palette-group-title">${lastGroup}</div>`;
            }
            const isSelected = idx === selectedIndex ? 'selected' : '';
            html += `
                <div class="cmd-palette-item ${isSelected}" data-index="${idx}">
                    <div style="display:flex;align-items:center;gap:0.625rem;">
                        <i data-lucide="${cmd.icon}" style="width:15px;height:15px;"></i>
                        <span>${cmd.label}</span>
                    </div>
                    <i data-lucide="corner-down-left" style="width:12px;height:12px;opacity:0.5;"></i>
                </div>
            `;
        });

        listContainer.innerHTML = html;
        if (window.lucide) lucide.createIcons();

        listContainer.querySelectorAll('.cmd-palette-item').forEach(item => {
            item.addEventListener('click', () => {
                const idx = parseInt(item.getAttribute('data-index'), 10);
                executeCommand(idx);
            });
        });
    }

    function openPalette() {
        createPaletteDOM();
        filteredCommands = [...COMMANDS];
        selectedIndex = 0;
        input.value = '';
        renderList();
        overlay.classList.add('active');
        setTimeout(() => input.focus(), 50);
    }

    function closePalette() {
        if (overlay) overlay.classList.remove('active');
    }

    function onSearchInput(e) {
        const query = e.target.value.toLowerCase().trim();
        filteredCommands = COMMANDS.filter(cmd => {
            return cmd.label.toLowerCase().includes(query) || cmd.group.toLowerCase().includes(query);
        });
        selectedIndex = 0;
        renderList();
    }

    function onKeyNav(e) {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (filteredCommands.length > 0) {
                selectedIndex = (selectedIndex + 1) % filteredCommands.length;
                renderList();
                scrollSelectedIntoView();
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (filteredCommands.length > 0) {
                selectedIndex = (selectedIndex - 1 + filteredCommands.length) % filteredCommands.length;
                renderList();
                scrollSelectedIntoView();
            }
        } else if (e.key === 'Enter') {
            e.preventDefault();
            executeCommand(selectedIndex);
        } else if (e.key === 'Escape') {
            closePalette();
        }
    }

    function scrollSelectedIntoView() {
        const selectedEl = listContainer.querySelector('.cmd-palette-item.selected');
        if (selectedEl) {
            selectedEl.scrollIntoView({ block: 'nearest' });
        }
    }

    function executeCommand(idx) {
        const cmd = filteredCommands[idx];
        if (!cmd) return;
        closePalette();
        if (typeof cmd.action === 'function') {
            cmd.action();
        } else if (cmd.url) {
            window.location.href = cmd.url;
        }
    }

    // Global Key Listener for Ctrl+K or Cmd+K
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            if (overlay && overlay.classList.contains('active')) {
                closePalette();
            } else {
                openPalette();
            }
        }
    });

    window.openCommandPalette = openPalette;
    window.closeCommandPalette = closePalette;
})();
