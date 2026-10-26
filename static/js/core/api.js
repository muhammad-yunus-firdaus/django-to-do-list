/**
 * api.js — Core API Request Module
 * Menyediakan wrapper terpusat untuk semua fetch() request dengan CSRF token
 * yang dibaca dari meta tag (bukan document.cookie yang tidak bisa dibaca
 * karena CSRF_COOKIE_HTTPONLY = True).
 *
 * Penggunaan:
 *   import { apiPost, apiGet } from '/static/js/core/api.js';
 *   const data = await apiPost('/tugas/toggle/1/', { status: 'selesai' });
 */

'use strict';

/**
 * Ambil CSRF token dari meta tag di <head>.
 * Wajib dipasang: <meta name="csrf-token" content="{{ csrf_token }}">
 * @returns {string} CSRF token string
 */
function getCsrfToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (!metaTag) {
        console.error('[api.js] Meta tag <meta name="csrf-token"> tidak ditemukan di halaman ini!');
        return '';
    }
    return metaTag.getAttribute('content') || '';
}

/**
 * Basis internal untuk semua request.
 * @param {string} url - URL endpoint
 * @param {string} method - HTTP method (GET, POST, PUT, DELETE, PATCH)
 * @param {Object|null} body - Data yang akan dikirim (untuk POST/PUT/PATCH)
 * @param {Object} extraHeaders - Header tambahan opsional
 * @returns {Promise<Object>} Response JSON yang sudah di-parse
 * @throws {Error} Jika response bukan OK (non-2xx)
 */
async function request(url, method = 'GET', body = null, extraHeaders = {}) {
    const headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        ...extraHeaders,
    };

    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase())) {
        headers['X-CSRFToken'] = getCsrfToken();
    }

    const config = { method, headers };
    if (body !== null) {
        config.body = JSON.stringify(body);
    }

    const response = await fetch(url, config);

    if (!response.ok) {
        let errorData = { error: `HTTP ${response.status}: ${response.statusText}` };
        try {
            errorData = await response.json();
        } catch (_) {
            // biarkan default errorData
        }
        const error = new Error(errorData.error || errorData.message || `HTTP error ${response.status}`);
        error.status = response.status;
        error.data = errorData;
        throw error;
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
        return response.json();
    }
    return { ok: true };
}

/**
 * GET request.
 * @param {string} url
 * @param {Object} [extraHeaders={}]
 * @returns {Promise<Object>}
 */
export function apiGet(url, extraHeaders = {}) {
    return request(url, 'GET', null, extraHeaders);
}

/**
 * POST request dengan CSRF token otomatis.
 * @param {string} url
 * @param {Object} [body={}]
 * @param {Object} [extraHeaders={}]
 * @returns {Promise<Object>}
 */
export function apiPost(url, body = {}, extraHeaders = {}) {
    return request(url, 'POST', body, extraHeaders);
}

/**
 * POST request dengan FormData (untuk form submit).
 * @param {string} url
 * @param {FormData} formData
 * @returns {Promise<Response>}
 */
export async function apiPostForm(url, formData) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken(),
        },
        body: formData,
    });

    if (!response.ok) {
        let errorData = { error: `HTTP ${response.status}` };
        try {
            errorData = await response.json();
        } catch (_) { }
        const error = new Error(errorData.error || `HTTP error ${response.status}`);
        error.status = response.status;
        error.data = errorData;
        throw error;
    }

    return response.json();
}

/**
 * DELETE request dengan CSRF token otomatis.
 * @param {string} url
 * @param {Object} [body={}]
 * @returns {Promise<Object>}
 */
export function apiDelete(url, body = {}) {
    return request(url, 'DELETE', body);
}
