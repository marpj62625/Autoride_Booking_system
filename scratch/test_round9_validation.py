import io
import sys
import os
from werkzeug.datastructures import FileStorage

sys.path.insert(0, os.path.abspath('backend'))
import app as app_mod

print("Testing is_allowed_image & reject_non_image...")

# 1. Normal image
img_mock = FileStorage(
    stream=io.BytesIO(b"dummy image data"),
    filename="test.png",
    content_type="image/png"
)
assert app_mod.is_allowed_image(img_mock) == True, "Failed valid image test"
with app_mod.app.test_request_context():
    assert app_mod.reject_non_image(img_mock, "Test image") is None, "Failed reject_non_image valid image"

# 2. Dangerous file (.exe, .php)
exe_mock = FileStorage(
    stream=io.BytesIO(b"malicious data"),
    filename="payload.exe",
    content_type="application/octet-stream"
)
assert app_mod.is_allowed_image(exe_mock) == False, "Failed dangerous file test"
with app_mod.app.test_request_context():
    err = app_mod.reject_non_image(exe_mock, "Executable")
    assert err is not None and err[1] == 400, "Failed to reject executable"

# 3. PDF with allow_pdf=False
pdf_mock = FileStorage(
    stream=io.BytesIO(b"%PDF-1.4 test pdf content"),
    filename="document.pdf",
    content_type="application/pdf"
)
assert app_mod.is_allowed_image(pdf_mock, allow_pdf=False) == False, "PDF should be disallowed when allow_pdf=False"
with app_mod.app.test_request_context():
    err = app_mod.reject_non_image(pdf_mock, "Doc", allow_pdf=False)
    assert err is not None and err[1] == 400, "PDF should return 400 when allow_pdf=False"

# 4. PDF with allow_pdf=True
assert app_mod.is_allowed_image(pdf_mock, allow_pdf=True) == True, "PDF should be allowed when allow_pdf=True"
with app_mod.app.test_request_context():
    assert app_mod.reject_non_image(pdf_mock, "Doc", allow_pdf=True) is None, "reject_non_image should pass PDF when allow_pdf=True"

# 5. Oversized image
big_stream = io.BytesIO(b"x" * (16 * 1024 * 1024))
big_mock = FileStorage(
    stream=big_stream,
    filename="huge.jpg",
    content_type="image/jpeg"
)
with app_mod.app.test_request_context():
    err_big = app_mod.reject_non_image(big_mock, "Big image", max_mb=15)
    assert err_big is not None and err_big[1] == 400, "Failed to reject oversized file"

print("ALL ROUND 9 VALIDATION TESTS PASSED 100%!")
