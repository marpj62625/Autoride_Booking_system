import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()

print("--- TAB NEW LINES 6325 to 6385 ---")
for i in range(6324, min(len(lines), 6385)):
    print(f"{i+1}: {lines[i]}")

print("\n--- SEARCHING FOR GPS MAP / RADAR OVERLAYS ---")
for i, line in enumerate(lines):
    if any(k in line.lower() for k in ['vehicles live', 'radar', 'view all', 'devices live', 'gps_map', 'gpsmap', 'map-container', 'mapcontainer']):
        print(f"Line {i+1}: {line[:120]}")
