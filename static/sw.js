// Service Worker for PWA (Bust Cache & Offline Resilience)
const CACHE_NAME = 'task-manager-prod-v1';
const urlsToCache = [
  '/tugas/dashboard/',
  '/tugas/daftar/',
  '/tugas/agenda/',
  '/static/css/main.css',
  '/static/css/tokens.css',
  '/static/css/base.css',
  '/static/css/components/buttons.css',
  '/static/css/components/cards.css',
  '/static/css/components/forms.css',
  '/static/css/components/badges.css',
  '/static/css/components/modals-toasts.css',
  '/static/css/components/tables.css',
  '/static/js/core/toast.js',
  '/static/js/core/dom.js',
  '/static/js/core/api.js',
  '/static/js/core/pomodoro.js',
  '/static/js/core/command-palette.js',
  '/static/js/notifications.js',
  '/static/js/tugas.js',
  '/static/js/agenda.js',
  '/static/images/android-chrome-192x192.png',
  '/static/images/android-chrome-512x512.png',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(urlsToCache);
      })
      .catch((err) => {
        console.debug('SW install cache error:', err);
      })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches immediately
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.debug('Deleting obsolete cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - network-first for HTML, stale-while-revalidate for static assets
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') {
    return;
  }

  const url = new URL(event.request.url);

  // Jangan cache API endpoints dinamis
  if (url.pathname.startsWith('/tugas/api/') || url.pathname.includes('/notifikasi/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => {
        if (cachedResponse) return cachedResponse;
        if (event.request.headers.get('accept') && event.request.headers.get('accept').includes('text/html')) {
          return caches.match('/tugas/dashboard/');
        }
      });

      return cachedResponse || fetchPromise;
    })
  );
});
