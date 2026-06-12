
with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

old = """        # Save to /tmp as fallback
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_bytes = file.read()
        with open(filepath, 'wb') as _f:
            _f.write(file_bytes)
        url = f\"/uploads/{filename}\"

        # Upload to Supabase Storage for persistent public access
        try:
            import urllib.request as _urlreq
            import urllib.error as _urlerr
            import json as _json
            from config import SUPABASE_URL, SUPABASE_KEY
            _auth_headers = {
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'apikey': SUPABASE_KEY
            }
            # Ensure bucket exists
            _bucket_data = _json.dumps({'id': 'refund-proofs', 'name': 'refund-proofs', 'public': True}).encode()
            _bucket_req = _urlreq.Request(
                f\"{SUPABASE_URL}/storage/v1/bucket\",
                data=_bucket_data,
                headers={**_auth_headers, 'Content-Type': 'application/json'},
                method='POST'
            )
            try: _urlreq.urlopen(_bucket_req, timeout=5)
            except Exception: pass
            # Upload file
            supa_path = f\"refund-proofs/{filename}\"
            _upload_req = _urlreq.Request(
                f\"{SUPABASE_URL}/storage/v1/object/{supa_path}\",
                data=file_bytes,
                headers={**_auth_headers, 'Content-Type': file.content_type or 'image/jpeg', 'x-upsert': 'true'},
                method='POST'
            )
            with _urlreq.urlopen(_upload_req, timeout=10) as _resp:
                if _resp.status in (200, 201):
                    url = f\"{SUPABASE_URL}/storage/v1/object/public/refund-proofs/{filename}\"
        except Exception as _supa_err:
            pass"""

new = """        # Read file bytes
        file_bytes = file.read()
        url = None  # Will only be set if Supabase upload succeeds

        # Upload to Supabase Storage for persistent public access
        try:
            import urllib.request as _urlreq
            import urllib.error as _urlerr
            import json as _json
            from config import SUPABASE_URL, SUPABASE_KEY
            _auth_headers = {
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'apikey': SUPABASE_KEY
            }
            # Ensure bucket exists (public)
            _bucket_data = _json.dumps({'id': 'refund-proofs', 'name': 'refund-proofs', 'public': True}).encode()
            _bucket_req = _urlreq.Request(
                f\"{SUPABASE_URL}/storage/v1/bucket\",
                data=_bucket_data,
                headers={**_auth_headers, 'Content-Type': 'application/json'},
                method='POST'
            )
            try: _urlreq.urlopen(_bucket_req, timeout=5)
            except Exception: pass
            # Upload file
            supa_path = f\"refund-proofs/{filename}\"
            _upload_req = _urlreq.Request(
                f\"{SUPABASE_URL}/storage/v1/object/{supa_path}\",
                data=file_bytes,
                headers={**_auth_headers, 'Content-Type': file.content_type or 'image/jpeg', 'x-upsert': 'true'},
                method='POST'
            )
            with _urlreq.urlopen(_upload_req, timeout=15) as _resp:
                if _resp.status in (200, 201):
                    url = f\"{SUPABASE_URL}/storage/v1/object/public/refund-proofs/{filename}\"
        except Exception as _supa_err:
            print(f"Supabase upload failed: {_supa_err}")
            return jsonify({"error": "Failed to upload proof image. Please check your internet connection and try again."}), 500

        if not url:
            return jsonify({"error": "Failed to upload proof image to storage. Please try again."}), 500"""

if old in content:
    new_content = content.replace(old, new)
    with open('backend/app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Fixed successfully!')
else:
    # Try with \r\n line endings
    old_crlf = old.replace('\n', '\r\n')
    if old_crlf in content:
        new_content = content.replace(old_crlf, new)
        with open('backend/app.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Fixed successfully (CRLF)!')
    else:
        print('Target block NOT found.')
        idx = content.find('Save to /tmp as fallback')
        print(f'Unique marker found at index: {idx}')
        if idx != -1:
            print(repr(content[idx-5:idx+100]))
