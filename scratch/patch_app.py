import os

target_file = r"c:\Users\patri\OneDrive\Desktop\AutorideSystem2side\AutorideSystem\backend\app.py"

with open(target_file, "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
in_func = False

for i, line in enumerate(lines):
    if "def get_vehicles():" in line:
        in_func = True
        new_lines.append(line)
        continue
    
    if in_func:
        if "@app.route" in line and i > 218: # Next route
            in_func = False
            new_lines.append(line)
            continue
        
        # We are inside the function
        if "try:" in line and not skip:
            new_lines.append("    try:\n")
            new_lines.append("        cur = get_cursor()\n")
            new_lines.append("\n")
            new_lines.append("        # Base query logic\n")
            new_lines.append("        if favorites_only and user_id and user_id != 'null':\n")
            new_lines.append("            query = \"\"\"\n")
            new_lines.append("                SELECT v.* FROM vehicles v\n")
            new_lines.append("                JOIN favorites f ON v.id = f.vehicle_id\n")
            new_lines.append("                WHERE f.user_id = %s\n")
            new_lines.append("            \"\"\"\n")
            new_lines.append("            params = [user_id]\n")
            new_lines.append("        else:\n")
            new_lines.append("            query = \"SELECT * FROM vehicles v WHERE 1=1\"\n")
            new_lines.append("            params = []\n")
            new_lines.append("\n")
            new_lines.append("        # Add Date Availability Logic\n")
            new_lines.append("        if start_date and end_date:\n")
            new_lines.append("            query += \"\"\"\n")
            new_lines.append("                AND NOT EXISTS (\n")
            new_lines.append("                    SELECT 1 FROM bookings b\n")
            new_lines.append("                    WHERE b.vehicle_id = v.id\n")
            new_lines.append("                    AND b.status IN ('Confirmed', 'Pending')\n")
            new_lines.append("                    AND (%s <= b.end_date AND %s >= b.start_date)\n")
            new_lines.append("                )\n")
            new_lines.append("            \"\"\"\n")
            new_lines.append("            params.extend([start_date, end_date])\n")
            new_lines.append("\n")
            new_lines.append("        cur.execute(query, params)\n")
            new_lines.append("        vehicles = cur.fetchall()\n")
            skip = True
            continue
        
        if skip:
            if "vehicles = cur.fetchall()" in line:
                skip = False
            continue
            
    new_lines.append(line)

with open(target_file, "w") as f:
    f.writelines(new_lines)
