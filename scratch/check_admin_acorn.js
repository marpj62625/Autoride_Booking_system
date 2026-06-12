const fs = require('fs');
const html = fs.readFileSync('admin_mobile/android/app/src/main/assets/public/index.html', 'utf8');

// Extract all inline script blocks
const re = /<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/gi;
let m, i = 0;
const blocks = [];
while ((m = re.exec(html)) !== null) {
  blocks.push({ pos: m.index, code: m[1] });
  i++;
}

console.log('Found ' + i + ' script blocks');

// Use vm to check syntax with modern JS support
const vm = require('vm');
blocks.forEach(function(b, idx) {
  try {
    new vm.Script(b.code);
    console.log('Script ' + (idx+1) + ' OK');
  } catch(e) {
    console.log('Script ' + (idx+1) + ' SYNTAX ERROR at pos ~' + b.pos);
    console.log('  ' + e.message);
    // Find the line
    if (e.stack) {
      const lineMatch = e.stack.match(/:(\d+)/);
      if (lineMatch) {
        const errLine = parseInt(lineMatch[1]);
        const lines = b.code.split('\n');
        const start = Math.max(0, errLine - 4);
        const end = Math.min(lines.length, errLine + 2);
        lines.slice(start, end).forEach((l, idx2) => {
          console.log('  ' + (start + idx2 + 1) + ': ' + l);
        });
      }
    }
  }
});
