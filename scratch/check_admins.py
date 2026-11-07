import os, sys

backend_dir = r'c:\Dev\AutorideSystem2sides\AutorideSystem\backend'
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from app import app, get_cursor

with app.app_context():
    cur = get_cursor()
    cur.execute("SELECT id, username FROM admins")
    admins = cur.fetchall()
    print("Admins table:")
    for a in admins:
        print(" ", dict(a))
    
    cur.execute("SELECT id, full_name, role FROM users WHERE role IN ('admin', 'super_admin')")
    admin_users = cur.fetchall()
    print("Users table with admin role:")
    for u in admin_users:
        print(" ", dict(u))
