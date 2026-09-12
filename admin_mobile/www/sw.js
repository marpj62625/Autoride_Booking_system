/* ============================================================
   Autoride Admin — Service Worker
   Enables offline caching & installability for PWA on
   Android (Chrome) and iOS (Safari)
   ============================================================ */

const CACHE_NAME = 'autoride-admin-v3';

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

// ==================== FETCH ====================
self.addEventListener('fetch', (event) => {
    const { request } = event;

    // 1. Skip non-GET requests immediately (POST, PUT, DELETE, PATCH, etc.)
    if (request.method !== 'GET') return;

    const url = request.url;

    // 2. Bypass all backend API, websocket, auth, blynk, and dynamic endpoints.
    // Returning without calling event.respondWith() lets the browser handle the fetch natively.
    if (
        url.includes('/api/') ||
        url.includes('/bookings') ||
        url.includes('/vehicles') ||
        url.includes('/inspections') ||
        url.includes('/users') ||
        url.includes('/admin/') ||
        url.includes('/chat') ||
        url.includes('/notifications') ||
        url.includes('/fcm-token') ||
        url.includes('/paymongo') ||
        url.includes(':9999') ||
        url.includes(':5000') ||
        url.includes('blynk.cloud') ||
        url.includes('nominatim.openstreetmap.org')
    ) {
        return;
    }

    // 3. Skip cross-origin requests except Google fonts
    if (!url.startsWith(self.location.origin) && !url.includes('fonts.googleapis.com') && !url.includes('fonts.gstatic.com')) {
        return;
    }

    // 4. For HTML/CSS/JS shell assets — Stale-While-Revalidate with bulletproof Response fallback
    event.respondWith(
        caches.match(request).then(cachedResponse => {
            const networkFetch = fetch(request).then(networkResponse => {
                if (networkResponse && networkResponse.status === 200 && (networkResponse.type === 'basic' || networkResponse.type === 'cors')) {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, responseClone);
                    });
                }
                return networkResponse;
            }).catch(() => {
                if (cachedResponse) return cachedResponse;
                if (request.mode === 'navigate') {
                    return caches.match('/admin_app/index.html') || caches.match('/admin_app/') || new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/plain' } });
                }
                return new Response('', { status: 503, statusText: 'Network Unavailable' });
            });

            return cachedResponse || networkFetch;
        }).catch(() => {
            return new Response('', { status: 503, statusText: 'Service Unavailable' });
        })
    );
});
