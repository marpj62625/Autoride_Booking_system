const fs = require('fs');
const html = fs.readFileSync('admin_mobile/android/app/src/main/assets/public/index.html', 'utf8');
const re = /<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/gi;
let m;
re.exec(html); // skip first call to get script 1
m = re.exec(html); // nope, restart
re.lastIndex = 0;
m = re.exec(html); // script 1

const code = m[1];
const lines = code.split('\n');

// Find the exact error line by binary search
const vm = require('vm');
let lo = 1, hi = lines.length;
while (lo < hi) {
  const mid = Math.floor((lo + hi) / 2);
  try {
    new vm.Script(lines.slice(0, mid).join('\n'));
    lo = mid + 1;
  } catch(e) {
    hi = mid;
  }
}

console.log('First error appears at line ' + lo + ' of the script block');
const start = Math.max(0, lo - 8);
const end = Math.min(lines.length, lo + 3);
lines.slice(start, end).forEach((l, i) => {
  const ln = start + i + 1;
  const marker = ln === lo ? ' <<<' : '';
  console.log(String(ln).padStart(4) + ': ' + l + marker);
});
