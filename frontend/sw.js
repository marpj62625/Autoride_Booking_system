/* ============================================================
   Autoride — Service Worker
   Enables offline caching & installability for PWA on
   Android (Chrome) and iOS (Safari)
   ============================================================ */

const CACHE_NAME = 'autoride-v1';

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
                console.log('[SW] Caching core assets');
                return cache.addAll(CORE_ASSETS).catch(err => {
                    console.warn('[SW] Some assets failed to cache:', err);
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
                        console.log('[SW] Removing old cache:', key);
                        return caches.delete(key);
                    })
            );
        }).then(() => self.clients.claim())
    );
});

// ==================== FETCH — Network First, Cache Fallback ====================
self.addEventListener('fetch', (event) => {
    const { request } = event;

    // Skip non-GET requests (API calls, form submissions, etc.)
    if (request.method !== 'GET') return;

    // Skip third-party requests (Google APIs, Supabase, etc.)
    if (!request.url.includes(self.location.origin)) return;

    // For API calls, always go network-first
    if (request.url.includes('/api/') || request.url.includes('9999')) {
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
                // Update cache in background
                if (networkResponse && networkResponse.status === 200) {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, responseClone);
                    });
                }
                return networkResponse;
            }).catch(() => {
                // Network failed — return cached or offline fallback
                return cachedResponse;
            });

            // Return cached version immediately if available, otherwise wait for network
            return cachedResponse || networkFetch;
        })
    );
});
