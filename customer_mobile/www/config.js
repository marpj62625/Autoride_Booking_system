// Centralized API Configuration for Vercel Deployment & Native Android
const isNativeApp = (window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform()) ||
                    window.location.protocol === 'file:' ||
                    (window.location.hostname === 'localhost' && window.Capacitor);

const API_BASE = isNativeApp || window.location.origin.includes('localhost')
  ? 'https://autoride-booking-system.vercel.app'
  : window.location.origin;

// Export for global use
window.API_BASE = API_BASE;
console.log('Autoride API Base:', API_BASE);

