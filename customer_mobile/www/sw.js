/* ============================================================
   Autoride Customer — Service Worker
   Enables offline caching & installability for PWA on
   Android (Chrome) and iOS (Safari)
   ============================================================ */

const CACHE_NAME = 'autoride-v2';

// Core shell files to cache during install
const CORE_ASSETS = [
    '/',
    '/login.html',
    '/register.html',
    '/vehicles.html',
    '/dashboard.html',
    '/profile.html',
    '/payment.html',
    '/booking-confirmation.html',
    '/vehicle-details.html',
    '/style.css',
    '/chat.js',
    '/manifest.json',
    '/mobile.css',
    '/Autoride-logo-nobg.png',
    '/Autoride-logo.png',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
];

// ==================== INSTALL ====================
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[Customer SW] Caching core assets');
                return cache.addAll(CORE_ASSETS).catch(err => {
                    console.warn('[Customer SW] Some assets failed to pre-cache:', err);
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
                        console.log('[Customer SW] Removing old cache:', key);
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
        url.includes('/admin') ||
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

    // 4. For static shell assets — Stale-While-Revalidate with bulletproof Response fallback
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
                    return caches.match('/index.html') || caches.match('/') || new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/plain' } });
                }
                return new Response('', { status: 503, statusText: 'Network Unavailable' });
            });

            return cachedResponse || networkFetch;
        }).catch(() => {
            return new Response('', { status: 503, statusText: 'Service Unavailable' });
        })
    );
});
