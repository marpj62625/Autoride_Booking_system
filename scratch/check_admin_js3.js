const fs = require('fs');
const html = fs.readFileSync('admin_mobile/android/app/src/main/assets/public/index.html', 'utf8');
const re = /<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/gi;
let m, i = 0;
while ((m = re.exec(html)) !== null) {
  i++;
  if (i !== 1) continue;
  const code = m[1];
  const lines = code.split('\n');
  // Fine-grained: check line by line accumulation from line 150 onwards
  for (let end = 150; end <= 250; end++) {
    const chunk = lines.slice(0, end).join('\n');
    try {
      new Function(chunk + '\n}'); // add closing brace to avoid incomplete block errors
    } catch(e) {
      if (e.message.includes("Unexpected token") || e.message.includes("SyntaxError")) {
        // Check if adding one more line fixes it (to skip false positives)
        try {
          new Function(lines.slice(0, end+1).join('\n') + '\n}');
          continue; // next line fixed it - incomplete block, not real error
        } catch(e2) {}
        console.log('Likely error at line ' + end + ': ' + e.message);
        lines.slice(Math.max(0,end-5), end+3).forEach((l,idx) => console.log((end-5+idx)+': '+l));
        console.log('---');
      }
    }
  }
}
