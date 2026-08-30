
// Centralized API Configuration for Vercel Deployment
// If on Vercel, API_BASE should just be the origin (rewrites handle /api)
const API_BASE = window.location.origin;

// Export for global use
window.API_BASE = API_BASE;
console.log('Autoride API Base:', API_BASE);
