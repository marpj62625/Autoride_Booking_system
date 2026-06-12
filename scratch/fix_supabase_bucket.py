# -*- coding: utf-8 -*-
# Fix: ensure bucket creation and correct upload method for Supabase Storage

with open('backend/app.py', encoding='utf-8') as f:
    c = f.read()

OLD = """        # Upload to Supabase Storage for persistent public access
        try:
            import requests as _req
            from config import SUPABASE_URL, SUPABASE_KEY
            supa_path = f"refund-proofs/{filename}"
            supa_res = _req.post(
                f"{SUPABASE_URL}/storage/v1/object/{supa_path}",
                headers={
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': file.content_type or 'image/jpeg',
                    'x-upsert': 'true'
                },
                data=file_bytes
            )
            if supa_res.status_code in (200, 201):
                url = f"{SUPABASE_URL}/storage/v1/object/public/{supa_path}"
        except Exception:
            pass  # Keep /tmp fallback"""

NEW = """        # Upload to Supabase Storage for persistent public access
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

if OLD in c:
    c = c.replace(OLD, NEW, 1)
    with open('backend/app.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Done')
else:
    print('NOT FOUND')
