const fs = require('fs');
const html = fs.readFileSync('admin_mobile/android/app/src/main/assets/public/index.html', 'utf8');
const re = /<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/gi;
const m = re.exec(html);
const code = m[1];
const lines = code.split('\n');

// Show lines 20-28 with char codes for any non-ASCII
for (let i = 19; i <= 27; i++) {
  const line = lines[i] || '';
  let display = '';
  for (let j = 0; j < line.length; j++) {
    const c = line.charCodeAt(j);
    if (c > 127) {
      display += '[0x' + c.toString(16).toUpperCase() + ']';
    } else {
      display += line[j];
    }
  }
  console.log('Line ' + (i+1) + ': ' + display);
}
