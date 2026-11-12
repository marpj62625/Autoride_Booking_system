
// Centralized API Configuration for Web & Custom Domain Deployment
let API_BASE = window.location.origin;

if (window.location.hostname.includes('arcph.net')) {
    API_BASE = 'https://api.arcph.net';
} else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    API_BASE = 'http://localhost:5000';
}

// Export for global use
window.API_BASE = API_BASE;
console.log('Autoride API Base:', API_BASE);
