/**
 * pomodoro.js — Circular SVG Focus Timer & Productivity Widget
 * Lightweight, modular (< 250 lines), zero external audio dependencies.
 */
(() => {
    let timerInterval = null;
    let isRunning = false;
    let currentDurationSec = 25 * 60;
    let timeLeftSec = 25 * 60;
    const RING_RADIUS = 52;
    const CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS; // ~326.73

    function playBeep() {
        try {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) return;
            const ctx = new AudioCtx();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, ctx.currentTime);
            gain.gain.setValueAtTime(0.15, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.7);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.7);
        } catch (e) {
            console.debug('AudioContext muted:', e);
        }
    }

    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }

    function updateDisplays() {
        const text = formatTime(timeLeftSec);
        document.querySelectorAll('.pomodoro-display').forEach(el => {
            el.textContent = text;
        });

        // Circular Ring SVG Stroke Dashoffset Calculation
        const fraction = currentDurationSec > 0 ? (timeLeftSec / currentDurationSec) : 0;
        const offset = CIRCUMFERENCE * (1 - fraction);

        document.querySelectorAll('.focus-ring-progress').forEach(circle => {
            circle.style.strokeDasharray = `${CIRCUMFERENCE}`;
            circle.style.strokeDashoffset = `${offset}`;
        });

        // Pulse Animation Toggle on Running State
        document.querySelectorAll('.focus-ring-svg').forEach(svg => {
            if (isRunning) {
                svg.classList.add('is-running');
            } else {
                svg.classList.remove('is-running');
            }
        });

        // Toggle buttons (Play/Pause)
        document.querySelectorAll('.pomodoro-toggle-btn').forEach(btn => {
            const icon = btn.querySelector('[data-lucide]');
            const label = btn.querySelector('.pomodoro-toggle-label');
            if (isRunning) {
                if (icon) icon.setAttribute('data-lucide', 'pause');
                if (label) label.textContent = 'Jeda';
            } else {
                if (icon) icon.setAttribute('data-lucide', 'play');
                if (label) label.textContent = 'Mulai';
            }
        });
        if (window.lucide) lucide.createIcons();
    }

    function startTimer() {
        if (isRunning) return;
        isRunning = true;
        updateDisplays();

        timerInterval = setInterval(() => {
            if (timeLeftSec > 0) {
                timeLeftSec--;
                updateDisplays();
            } else {
                pauseTimer();
                playBeep();
                if (typeof window.showToast === 'function') {
                    window.showToast('Sesi fokus selesai! Istirahat sejenak.', 'success');
                }
            }
        }, 1000);
    }

    function pauseTimer() {
        isRunning = false;
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        updateDisplays();
    }

    function toggleTimer() {
        if (isRunning) {
            pauseTimer();
        } else {
            startTimer();
        }
    }

    function resetTimer() {
        pauseTimer();
        timeLeftSec = currentDurationSec;
        updateDisplays();
    }

    function setDuration(minutes, pillElement) {
        pauseTimer();
        currentDurationSec = minutes * 60;
        timeLeftSec = currentDurationSec;

        // Hide custom rows
        document.querySelectorAll('.focus-custom-row').forEach(row => {
            row.style.display = 'none';
        });

        // Update active button state
        document.querySelectorAll('.focus-preset-btn, .pomodoro-pill').forEach(p => p.classList.remove('active'));
        if (pillElement) {
            pillElement.classList.add('active');
        }

        // Update badge label if present
        const labelEl = document.getElementById('pomodoroLabel');
        if (labelEl) {
            labelEl.textContent = `Fokus (${minutes}m)`;
        }

        updateDisplays();
    }

    function toggleCustomPomodoroInput(btnElement) {
        const rows = document.querySelectorAll('.focus-custom-row');
        let isVisible = false;
        rows.forEach(row => {
            if (row.style.display === 'flex' || row.style.display === 'block') {
                row.style.display = 'none';
            } else {
                row.style.display = 'flex';
                isVisible = true;
            }
        });

        if (isVisible) {
            document.querySelectorAll('.focus-preset-btn, .pomodoro-pill').forEach(p => p.classList.remove('active'));
            if (btnElement) btnElement.classList.add('active');
            const input = document.querySelector('#focusCustomMinutes, .focus-custom-minutes');
            if (input) input.focus();
        }
    }

    function applyCustomPomodoro(value) {
        let mins = value;
        if (mins === undefined || mins === null) {
            const input = document.querySelector('#focusCustomMinutes, .focus-custom-minutes');
            mins = input ? input.value : 0;
        }
        mins = parseInt(mins, 10);

        if (isNaN(mins) || mins < 1 || mins > 120) {
            if (typeof window.showToast === 'function') {
                window.showToast('Masukkan durasi antara 1 - 120 menit', 'error');
            }
            return;
        }

        pauseTimer();
        currentDurationSec = mins * 60;
        timeLeftSec = currentDurationSec;

        const labelEl = document.getElementById('pomodoroLabel');
        if (labelEl) {
            labelEl.textContent = `Kustom (${mins}m)`;
        }

        // Hide custom input row after applied
        document.querySelectorAll('.focus-custom-row').forEach(row => {
            row.style.display = 'none';
        });

        updateDisplays();

        if (typeof window.showToast === 'function') {
            window.showToast(`Durasi timer diatur ke ${mins} menit`, 'success');
        }
    }

    // Modal view for other pages (e.g. Agenda, Command Palette)
    function openPomodoroModal() {
        if (typeof Swal === 'undefined') return;
        const currentMins = Math.round(currentDurationSec / 60);

        Swal.fire({
            title: 'Focus Timer',
            html: `
                <div style="text-align:center;padding:0.25rem 0;">
                    <!-- Circular Ring Timer in Modal -->
                    <div class="focus-timer-circular-container" style="margin:0.25rem auto 1rem auto;">
                        <svg class="focus-ring-svg ${isRunning ? 'is-running' : ''}" viewBox="0 0 120 120">
                            <circle class="focus-ring-track" cx="60" cy="60" r="52"></circle>
                            <circle class="focus-ring-progress" cx="60" cy="60" r="52"></circle>
                        </svg>
                        <div class="focus-timer-inner">
                            <div class="pomodoro-display">${formatTime(timeLeftSec)}</div>
                            <div style="font-size:0.6875rem;color:var(--foreground-muted);max-width:96px;margin-top:4px;" class="truncate">Sesi Fokus</div>
                        </div>
                    </div>

                    <!-- Segmented Presets -->
                    <div class="focus-presets-segmented" style="max-width:300px;margin:0 auto 0.75rem auto;">
                        <button type="button" class="focus-preset-btn ${currentMins === 10 ? 'active' : ''}" onclick="window.setPomodoroDuration(10, this)">10m</button>
                        <button type="button" class="focus-preset-btn ${currentMins === 25 ? 'active' : ''}" onclick="window.setPomodoroDuration(25, this)">25m</button>
                        <button type="button" class="focus-preset-btn ${currentMins === 45 ? 'active' : ''}" onclick="window.setPomodoroDuration(45, this)">45m</button>
                        <button type="button" class="focus-preset-btn ${[10,25,45].indexOf(currentMins) === -1 ? 'active' : ''}" onclick="window.toggleCustomPomodoroInput(this)">Custom</button>
                    </div>

                    <!-- Custom Minutes Row -->
                    <div class="focus-custom-row" style="display:none;justify-content:center;gap:0.5rem;max-width:300px;margin:0 auto 0.75rem auto;">
                        <input type="number" class="form-input focus-custom-minutes" min="1" max="120" placeholder="Menit (1-120)" style="padding:0.375rem 0.625rem;font-size:0.8125rem;height:32px;flex:1;" onkeydown="if(event.key==='Enter'){event.preventDefault();window.applyCustomPomodoro();}">
                        <button type="button" class="btn btn-sm btn-outline" onclick="window.applyCustomPomodoro()" style="height:32px;padding:0 0.75rem;">Set</button>
                    </div>

                    <!-- Action Buttons -->
                    <div style="display:flex;justify-content:center;gap:0.75rem;margin-top:1rem;">
                        <button type="button" class="btn btn-primary pomodoro-toggle-btn" onclick="window.togglePomodoro()" style="min-width:110px;">
                            <i data-lucide="${isRunning ? 'pause' : 'play'}" style="width:16px;height:16px;"></i>
                            <span class="pomodoro-toggle-label">${isRunning ? 'Jeda' : 'Mulai'}</span>
                        </button>
                        <button type="button" class="btn btn-outline" onclick="window.resetPomodoro()" title="Reset Timer">
                            <i data-lucide="rotate-ccw" style="width:16px;height:16px;"></i>
                            <span>Reset</span>
                        </button>
                    </div>
                </div>
            `,
            showConfirmButton: false,
            showCancelButton: true,
            cancelButtonText: 'Tutup',
            customClass: { popup: 'swal-custom-modal' },
            didOpen: () => {
                if (window.lucide) lucide.createIcons();
                updateDisplays();
            }
        });
    }

    // Expose global methods
    window.togglePomodoro = toggleTimer;
    window.resetPomodoro = resetTimer;
    window.setPomodoroDuration = setDuration;
    window.toggleCustomPomodoroInput = toggleCustomPomodoroInput;
    window.applyCustomPomodoro = applyCustomPomodoro;
    window.openPomodoroModal = openPomodoroModal;

    document.addEventListener('DOMContentLoaded', updateDisplays);
})();
