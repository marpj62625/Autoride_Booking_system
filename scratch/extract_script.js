const fs = require('fs');
const html = fs.readFileSync('admin_mobile/www/index.html', 'utf8');
const re = /<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/gi;
const m = re.exec(html);
fs.writeFileSync('scratch/admin_script1.js', m[1]);
console.log('Extracted ' + m[1].split('\n').length + ' lines to scratch/admin_script1.js');
