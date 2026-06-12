# -*- coding: utf-8 -*-
with open('backend/app.py', encoding='utf-8') as f:
    c = f.read()

OLD = '''filename = secure_filename(f"refund_{booking_id}_{int(datetime.now().timestamp())}_{file.filename}")

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file.save(filepath)

        url = f"/uploads/{filename}"

        

        ref_val'''

NEW = '''filename = secure_filename(f"refund_{booking_id}_{int(datetime.now().timestamp())}_{file.filename}")

        # Save to /tmp as fallback
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_bytes = file.read()
        with open(filepath, 'wb') as _f:
            _f.write(file_bytes)
        url = f"/uploads/{filename}"

        # Upload to Supabase Storage for persistent public access
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
            pass  # Keep /tmp fallback

        ref_val'''

if OLD in c:
    c = c.replace(OLD, NEW, 1)
    with open('backend/app.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Done')
else:
    print('NOT FOUND - searching...')
    idx = c.find('refund_{booking_id}')
    print('refund_booking_id at:', idx)
    print(repr(c[idx-10:idx+200]))
