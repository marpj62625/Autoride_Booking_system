with open('backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the 4 routes that incorrectly have /api prefix
replacements = [
    ("/api/admin/bookings/<int:booking_id>/license-details", "/admin/bookings/<int:booking_id>/license-details"),
    ("/api/admin/users/<int:user_id>/license-details", "/admin/users/<int:user_id>/license-details"),
    ("/api/user/license-details", "/user/license-details"),
]

for old, new in replacements:
    count = content.count(f"'{old}'")
    content = content.replace(f"'{old}'", f"'{new}'")
    print(f"Replaced '{old}' -> '{new}' ({count} occurrences)")

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDone! All routes fixed.")
