/* ============================================================
   Autoride Admin — Service Worker
   Enables offline caching & installability for PWA on
   Android (Chrome) and iOS (Safari)
   ============================================================ */

const CACHE_NAME = 'autoride-admin-v1';

// Core shell files to cache during install
const CORE_ASSETS = [
    '/admin_app/',
    '/admin_app/index.html',
    '/admin_app/desktop.css',
    '/admin_app/print-header.css',
    '/admin_app/print-receipt.html',
    '/admin_app/manifest.json',
    '/admin_app/Autoride-logo.png',
    '/admin_app/Autoride-logo-nobg.png',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
];

// ==================== INSTALL ====================
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[Admin SW] Caching core assets');
                return cache.addAll(CORE_ASSETS).catch(err => {
                    console.warn('[Admin SW] Some assets failed to cache:', err);
                });
            })
            .then(() => self.skipWaiting())
    );
});

// ==================== ACTIVATE ====================
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME)
                    .map(key => {
                        console.log('[Admin SW] Removing old cache:', key);
                        return caches.delete(key);
                    })
            );
        }).then(() => self.clients.claim())
    );
});

// ==================== FETCH — Network First, Cache Fallback ====================
self.addEventListener('fetch', (event) => {
    const { request } = event;

    // Skip non-GET requests (API calls, updates, etc.)
    if (request.method !== 'GET') return;

    // Skip third-party requests (Google APIs, Supabase, etc.)
    if (!request.url.includes(self.location.origin)) return;

    // API calls always go network first
    if (request.url.includes('/bookings') || request.url.includes('/vehicles') || request.url.includes('/inspections') || request.url.includes('/users') || request.url.includes('/api/')) {
        event.respondWith(
            fetch(request)
                .catch(() => caches.match(request))
        );
        return;
    }

    // For HTML/CSS/JS — Stale While Revalidate
    event.respondWith(
        caches.match(request).then(cachedResponse => {
            const networkFetch = fetch(request).then(networkResponse => {
                if (networkResponse && networkResponse.status === 200) {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, responseClone);
                    });
                }
                return networkResponse;
            }).catch(() => {
                return cachedResponse;
            });

            return cachedResponse || networkFetch;
        })
    );
});
