const fs = require('fs');
const html = fs.readFileSync('admin_mobile/android/app/src/main/assets/public/index.html', 'utf8');
const re = /<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/gi;
let m, i = 0;
while ((m = re.exec(html)) !== null) {
  i++;
  try {
    new Function(m[1]);
    console.log('Script ' + i + ' OK (pos ' + m.index + ')');
  } catch(e) {
    console.log('ERROR in script ' + i + ' at pos ~' + m.index + ': ' + e.message);
    // Show surrounding context
    const lines = m[1].substring(0, e.message.match(/\d+/) ? 500 : 200);
    console.log('--- snippet ---');
    console.log(lines.substring(Math.max(0, lines.length-300)));
    console.log('--- end ---');
  }
}
console.log('Total script blocks checked: ' + i);
