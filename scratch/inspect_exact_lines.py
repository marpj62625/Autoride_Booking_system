with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_range(start, end):
    for i in range(start-1, end):
        print(f"{i+1}: {repr(lines[i])}")

print("=== 18. VehiclePhotos._addFile (15682-15690) ===")
print_range(15682, 15690)

print("=== 19. Inspections.handlePhotoSelect (31298-31315) ===")
print_range(31298, 31315)

print("=== 20. Bookings._onProofSelected (20340-20348) ===")
print_range(20340, 20348)

print("=== 21. FleetCalendar.handleImportFileSelect (17427-17434) ===")
print_range(17427, 17434)

print("=== 22. expProofFile in Reports (28444-28452) ===")
print_range(28444, 28452)
