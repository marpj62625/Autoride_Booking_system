# -*- coding: utf-8 -*-
with open('backend/app.py', encoding='utf-8') as f:
    c = f.read()

OLD = """        # Upload to Supabase Storage for persistent public access
        try:
            import requests as _req
            from config import SUPABASE_URL, SUPABASE_KEY
            _headers = {
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'apikey': SUPABASE_KEY
            }
            # Ensure bucket exists (create if not)
            _req.post(
                f"{SUPABASE_URL}/storage/v1/bucket",
                headers={**_headers, 'Content-Type': 'application/json'},
                json={'id': 'refund-proofs', 'name': 'refund-proofs', 'public': True}
            )
            # Upload file
            supa_path = f"refund-proofs/{filename}"
            supa_res = _req.post(
                f"{SUPABASE_URL}/storage/v1/object/{supa_path}",
                headers={
                    **_headers,
                    'Content-Type': file.content_type or 'image/jpeg',
                    'x-upsert': 'true'
                },
                data=file_bytes
            )
            if supa_res.status_code in (200, 201):
                url = f"{SUPABASE_URL}/storage/v1/object/public/refund-proofs/{filename}"
        except Exception:
            pass  # Keep /tmp fallback"""

NEW = """        # Upload to Supabase Storage for persistent public access
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
                f"{SUPABASE_URL}/storage/v1/bucket",
                data=_bucket_data,
                headers={**_auth_headers, 'Content-Type': 'application/json'},
                method='POST'
            )
            try: _urlreq.urlopen(_bucket_req, timeout=5)
            except Exception: pass
            # Upload file
            supa_path = f"refund-proofs/{filename}"
            _upload_req = _urlreq.Request(
                f"{SUPABASE_URL}/storage/v1/object/{supa_path}",
                data=file_bytes,
                headers={**_auth_headers, 'Content-Type': file.content_type or 'image/jpeg', 'x-upsert': 'true'},
                method='POST'
            )
            with _urlreq.urlopen(_upload_req, timeout=10) as _resp:
                if _resp.status in (200, 201):
                    url = f"{SUPABASE_URL}/storage/v1/object/public/refund-proofs/{filename}"
        except Exception as _supa_err:
            print(f"Supabase upload failed: {_supa_err}, using local fallback")"""

if OLD in c:
    c = c.replace(OLD, NEW, 1)
    with open('backend/app.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Done')
else:
    print('NOT FOUND')
