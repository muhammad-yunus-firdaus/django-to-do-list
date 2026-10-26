/**
 * dom.js — Core DOM Utility Module
 * Menyediakan fungsi sanitasi XSS dan helper DOM yang aman.
 * WAJIB digunakan di seluruh file JS yang merender data dari server ke innerHTML.
 */

'use strict';

/**
 * Escape karakter HTML berbahaya untuk mencegah stored/reflected XSS.
 * Gunakan SELALU sebelum menyisipkan string dinamis ke innerHTML.
 * @param {*} str - String yang akan di-escape
 * @returns {string} String yang sudah aman
 */
export function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Set teks konten sebuah elemen dengan aman (tidak perlu escaping manual).
 * @param {Element} el - Elemen DOM target
 * @param {string} text - Teks yang akan di-set
 */
export function setText(el, text) {
    if (el) el.textContent = text ?? '';
}

/**
 * Buat elemen HTML baru dengan atribut opsional.
 * @param {string} tag - Nama tag HTML
 * @param {Object} attrs - Atribut elemen (key-value)
 * @param {string} [textContent] - Teks konten opsional
 * @returns {Element}
 */
export function createElement(tag, attrs = {}, textContent = '') {
    const el = document.createElement(tag);
    for (const [key, val] of Object.entries(attrs)) {
        el.setAttribute(key, val);
    }
    if (textContent) el.textContent = textContent;
    return el;
}

/**
 * Inisialisasi ulang ikon Lucide di dalam kontainer tertentu.
 * Dipanggil setelah DOM update via AJAX agar ikon baru ter-render.
 * @param {Element} [container=document] - Kontainer tempat mencari ikon baru
 */
export function refreshLucideIcons(container = document) {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons({ attrs: { 'stroke-width': '1.75' } });
    }
}

/**
 * Tampilkan elemen (hapus class 'hidden').
 * @param {Element} el
 */
export function showEl(el) {
    if (el) el.classList.remove('hidden');
}

/**
 * Sembunyikan elemen (tambah class 'hidden').
 * @param {Element} el
 */
export function hideEl(el) {
    if (el) el.classList.add('hidden');
}

/**
 * Toggle class pada elemen.
 * @param {Element} el
 * @param {string} className
 */
export function toggleClass(el, className) {
    if (el) el.classList.toggle(className);
}
