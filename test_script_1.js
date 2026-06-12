
function adminDbg(msg, color) {
  var list = document.getElementById('__adminDbgList');
  if (!list) return;
  var d = document.createElement('div');
  d.style.color = color || '#aaa';
  d.style.borderBottom = '1px solid #222';
  d.style.padding = '2px 0';
  var t = new Date().toLocaleTimeString();
  d.textContent = '[' + t + '] ' + msg;
  list.appendChild(d);
  list.scrollTop = list.scrollHeight;
}
var _origLog = console.log;
var _origErr = console.error;
console.log = function() { _origLog.apply(console, arguments); adminDbg(Array.from(arguments).join(' '), '#aaa'); };
console.error = function() { _origErr.apply(console, arguments); adminDbg(Array.from(arguments).join(' '), '#ff4444'); };
window.onerror = function(msg, src, line) { adminDbg('ERROR: ' + msg + ' [' + (src||'').split('/').pop() + ':' + line + ']', '#ff4444'); };

    function viewLicenseImage(url) {
        var modal = document.getElementById('licensePreviewModal');
        var img = document.getElementById('licensePreviewImg');
        if (modal && img) {
            img.src = url;
            modal.style.display = 'flex';
        }
    }

