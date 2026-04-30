
// Centralized API Configuration for Vercel Deployment
const API_BASE = window.location.origin + '/api';

// Export for global use
window.API_BASE = API_BASE;
console.log('Autoride API Base:', API_BASE);
