const fs = require('fs');
const html = fs.readFileSync('admin_mobile/android/app/src/main/assets/public/index.html', 'utf8');
const re = /<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/gi;
let m, i = 0;
while ((m = re.exec(html)) !== null) {
  i++;
  if (i !== 1) continue; // only check script 1
  const code = m[1];
  const lines = code.split('\n');
  // Try to find the error by checking progressively larger chunks
  for (let end = 100; end <= lines.length; end += 100) {
    const chunk = lines.slice(0, end).join('\n');
    try {
      new Function(chunk);
    } catch(e) {
      if (e.message.includes("Unexpected token")) {
        console.log('Error found around line ' + end + ' of script: ' + e.message);
        // Print surrounding lines
        const errLines = lines.slice(Math.max(0, end-20), end+5);
        errLines.forEach((l, idx) => console.log((end-20+idx) + ': ' + l));
        break;
      }
    }
  }
}
