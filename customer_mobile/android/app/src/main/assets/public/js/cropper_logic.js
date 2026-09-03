var _cropperInstance = null;
var _cropperCallback = null;

function openCropperAndCallback(file, aspectRatio, callback) {
  var modal = document.getElementById('cropperModal');
  var img = document.getElementById('cropperImage');
  if (!modal || !img || !file) return;

  _cropperCallback = callback;
  modal.style.display = 'flex';

  var startCropper = function(srcUrl) {
    if (_cropperInstance) {
      _cropperInstance.destroy();
      _cropperInstance = null;
    }
    img.src = srcUrl;

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
  };

  if (typeof file === 'string') {
    startCropper(file);
  } else {
    var reader = new FileReader();
    reader.onload = function(e) {
      startCropper(e.target.result);
    };
    reader.onerror = function() {
      startCropper(URL.createObjectURL(file));
    };
    reader.readAsDataURL(file);
  }

  var btn = document.getElementById('cropperConfirmBtn');
  btn.onclick = function() {
    if (!_cropperInstance) return;
    var oldText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cropping...';
    btn.disabled = true;

    setTimeout(function() {
      try {
        var canvas = _cropperInstance.getCroppedCanvas({
          maxWidth: 1920,
          maxHeight: 1920,
          fillColor: '#fff',
          imageSmoothingEnabled: true,
          imageSmoothingQuality: 'high',
        });
        if (!canvas) {
          throw new Error('Canvas could not be created');
        }
        var dataUrl = canvas.toDataURL('image/jpeg', 0.85);
        
        var arr = dataUrl.split(','), mime = arr[0].match(/:(.*?);/)[1];
        var bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
        while(n--){
            u8arr[n] = bstr.charCodeAt(n);
        }
        var blob = new Blob([u8arr], {type:mime});
        blob.name = file.name || "cropped_image.jpg";
        blob.previewUrl = dataUrl;
        
        var cb = _cropperCallback;
        closeCropper();
        btn.innerHTML = oldText;
        btn.disabled = false;
        
        if (blob && cb) {
          cb(blob);
        }
      } catch (e) {
        closeCropper();
        btn.innerHTML = oldText;
        btn.disabled = false;
        console.error('Cropper error:', e);
        if (typeof showToast === 'function') {
           showToast('Failed to crop image: ' + (e.message || 'Error'), 'error');
        }
      }
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
