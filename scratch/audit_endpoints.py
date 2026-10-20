import re

with open("backend/app.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

routes = []
current_decorators = []

for idx, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith("@"):
        current_decorators.append((idx + 1, stripped))
    elif stripped.startswith("def "):
        # Check if any decorator is @app.route
        route_decs = [d for d in current_decorators if "@app.route" in d[1] or "@api." in d[1]]
        if route_decs:
            fn_name = stripped.split("(")[0].replace("def ", "").strip()
            routes.append({
                "line": idx + 1,
                "def": stripped,
                "fn": fn_name,
                "decorators": [d[1] for d in current_decorators],
                "route_paths": route_decs
            })
        current_decorators = []
    elif not stripped or stripped.startswith("#"):
        continue
    else:
        current_decorators = []

print(f"Found {len(routes)} route functions.")

# 1. Routes that look like Admin or Sensitive but have NO auth decorator
sensitive_keywords = ['admin', 'delete', 'update', 'setting', 'export', 'wipe', 'reset', 'payout', 'refund']
auth_decorators = ['token_required', 'admin_required', 'role_required', 'staff_required', 'jwt_required', 'login_required']

unprotected_sensitive = []
for r in routes:
    has_auth = any(any(auth in dec for auth in auth_decorators) for dec in r["decorators"])
    paths = " ".join([d[1] for d in r["route_paths"]]).lower()
    fn = r["fn"].lower()
    
    is_sensitive = any(k in paths or k in fn for k in sensitive_keywords)
    # Exclude public assets, login, register, callback, health
    is_public_intentional = any(p in paths for p in ['login', 'register', 'static', 'webhook', 'callback', 'forgot', 'health', 'public'])

    if is_sensitive and not has_auth and not is_public_intentional:
        unprotected_sensitive.append(r)

print(f"\n--- POTENTIALLY UNPROTECTED SENSITIVE ROUTES ({len(unprotected_sensitive)}) ---")
for r in unprotected_sensitive[:30]:
    paths_str = ", ".join([d[1] for d in r["route_paths"]])
    print(f"Line {r['line']}: {r['fn']} | Routes: {paths_str} | Decs: {r['decorators']}")

