var _cropperInstance = null;
var _cropperCallback = null;

function openCropperAndCallback(file, aspectRatio, callback) {
  var modal = document.getElementById('cropperModal');
  var img = document.getElementById('cropperImage');
  if (!modal || !img || !file) return;

  _cropperCallback = callback;
  
  img.src = URL.createObjectURL(file);
  modal.style.display = 'flex';

  if (_cropperInstance) {
    _cropperInstance.destroy();
  }

  setTimeout(function() {
    _cropperInstance = new Cropper(img, {
      aspectRatio: aspectRatio,
      viewMode: 1,
      dragMode: 'move',
      autoCropArea: 0.9,
      restore: false,
      guides: true,
      center: true,
      highlight: false,
      cropBoxMovable: true,
      cropBoxResizable: true,
      toggleDragModeOnDblclick: false
    });
  }, 100);

  var btn = document.getElementById('cropperConfirmBtn');
  btn.onclick = function() {
    if (!_cropperInstance) return;
    var oldText = btn.innerHTML;
    btn.innerHTML = '<i class=\"fas fa-spinner fa-spin\"></i> Cropping...';
    btn.disabled = true;

    setTimeout(function() {
      _cropperInstance.getCroppedCanvas({
        maxWidth: 1920,
        maxHeight: 1920,
        fillColor: '#fff',
        imageSmoothingEnabled: true,
        imageSmoothingQuality: 'high',
      }).toBlob(function(blob) {
        closeCropper();
        btn.innerHTML = oldText;
        btn.disabled = false;
        if (blob && _cropperCallback) {
          _cropperCallback(blob);
        }
      }, 'image/jpeg', 0.85);
    }, 50);
  };
}

function closeCropper() {
  var modal = document.getElementById('cropperModal');
  if (modal) modal.style.display = 'none';
  if (_cropperInstance) {
    _cropperInstance.destroy();
    _cropperInstance = null;
  }
  var img = document.getElementById('cropperImage');
  if (img) img.src = '';
  _cropperCallback = null;
}
