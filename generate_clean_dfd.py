#!/usr/bin/env python3
"""
Clean DFD Generator for Autoride System
Generates a Level 1 DFD with NO overlapping arrows or labels
"""

# Canvas and layout constants
CANVAS_W = 2600
CANVAS_H = 3400

# Column X positions (left to right)
LEFT_ENTITY_X = 120
LEFT_SPINE_START = 280
LEFT_SPINE_END = 480
LEFT_PROCESS_X = 680
DATA_STORE_X = 1300
RIGHT_PROCESS_X = 1920
RIGHT_SPINE_START = 2120
RIGHT_SPINE_END = 2320
RIGHT_ENTITY_X = 2480

# Row Y positions (generous vertical spacing)
ROW_Y = {
    1: 280,   # Auth
    2: 680,   # Vehicle
    3: 1080,  # Booking
    4: 1480,  # Payment
    5: 1880,  # License/Reports
    6: 2280,  # Notification/Settings
}

BOTTOM_ENTITIES_Y = 3000

# Component sizes
ENTITY_W, ENTITY_H = 180, 80
PROCESS_RX, PROCESS_RY = 140, 70
STORE_W, STORE_H = 280, 50

def generate_svg():
    """Generate complete SVG"""
    svg_parts = []
    
    # Header
    svg_parts.append(f'''<svg width="{CANVAS_W}" height="{CANVAS_H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrow-blue" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#3182ce"/>
    </marker>
    <marker id="arrow-green" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#38a169"/>
    </marker>
    <marker id="arrow-orange" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#dd6b20"/>
    </marker>
    <marker id="arrow-purple" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#805ad5"/>
    </marker>
    <marker id="arrow-red" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#e53e3e"/>
    </marker>
    <marker id="arrow-teal" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#2c7a7b"/>
    </marker>
    <marker id="arrow-gray" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#718096"/>
    </marker>
  </defs>
  
  <!-- Background -->
  <rect x="10" y="10" width="{CANVAS_W-20}" height="{CANVAS_H-20}" rx="16" fill="#fafbfc" stroke="#e2e8f0" stroke-width="2"/>
''')
    
    # External entities
    svg_parts.append(draw_entities())
    
    # Processes
    svg_parts.append(draw_processes())
    
    # Data stores
    svg_parts.append(draw_data_stores())
    
    # Data flows (organized by functional area to minimize crossings)
    svg_parts.append(draw_auth_flows())
    svg_parts.append(draw_vehicle_flows())
    svg_parts.append(draw_booking_flows())
    svg_parts.append(draw_payment_flows())
    svg_parts.append(draw_license_flows())
    svg_parts.append(draw_notification_flows())
    
    svg_parts.append('</svg>')
    
    return '\n'.join(svg_parts)

def draw_entities():
    """Draw all external entities"""
    return f'''
  <!-- External Entities -->
  <!-- Customer (top left) -->
  <rect x="{LEFT_ENTITY_X-90}" y="{ROW_Y[1]-40}" width="{ENTITY_W}" height="{ENTITY_H}" 
        rx="8" fill="#edf2f7" stroke="#4a5568" stroke-width="2.5"/>
  <text x="{LEFT_ENTITY_X}" y="{ROW_Y[1]-5}" text-anchor="middle" font-size="15" font-weight="700" fill="#2d3748">Customer</text>
  <text x="{LEFT_ENTITY_X}" y="{ROW_Y[1]+15}" text-anchor="middle" font-size="11" fill="#718096">(Mobile App)</text>
  
  <!-- Admin (top right) -->
  <rect x="{RIGHT_ENTITY_X-90}" y="{ROW_Y[1]-40}" width="{ENTITY_W}" height="{ENTITY_H}" 
        rx="8" fill="#edf2f7" stroke="#4a5568" stroke-width="2.5"/>
  <text x="{RIGHT_ENTITY_X}" y="{ROW_Y[1]-5}" text-anchor="middle" font-size="15" font-weight="700" fill="#2d3748">Admin</text>
  <text x="{RIGHT_ENTITY_X}" y="{ROW_Y[1]+15}" text-anchor="middle" font-size="11" fill="#718096">(Admin Panel)</text>
  
  <!-- Payment Gateway (right mid) -->
  <rect x="{RIGHT_ENTITY_X-90}" y="{ROW_Y[4]-50}" width="{ENTITY_W}" height="{90}" 
        rx="8" fill="#edf2f7" stroke="#4a5568" stroke-width="2.5"/>
  <text x="{RIGHT_ENTITY_X}" y="{ROW_Y[4]-15}" text-anchor="middle" font-size="14" font-weight="700" fill="#2d3748">Payment</text>
  <text x="{RIGHT_ENTITY_X}" y="{ROW_Y[4]+5}" text-anchor="middle" font-size="14" font-weight="700" fill="#2d3748">Gateway</text>
  <text x="{RIGHT_ENTITY_X}" y="{ROW_Y[4]+25}" text-anchor="middle" font-size="10" fill="#718096">(PayMongo)</text>
  
  <!-- Supabase Storage (bottom left) -->
  <rect x="{LEFT_ENTITY_X-90}" y="{BOTTOM_ENTITIES_Y-45}" width="{ENTITY_W}" height="{90}" 
        rx="8" fill="#edf2f7" stroke="#4a5568" stroke-width="2.5"/>
  <text x="{LEFT_ENTITY_X}" y="{BOTTOM_ENTITIES_Y-10}" text-anchor="middle" font-size="14" font-weight="700" fill="#2d3748">Supabase</text>
  <text x="{LEFT_ENTITY_X}" y="{BOTTOM_ENTITIES_Y+10}" text-anchor="middle" font-size="14" font-weight="700" fill="#2d3748">Storage</text>
  <text x="{LEFT_ENTITY_X}" y="{BOTTOM_ENTITIES_Y+30}" text-anchor="middle" font-size="10" fill="#718096">(Cloud Files)</text>
  
  <!-- Email/Push Service (bottom right) -->
  <rect x="{RIGHT_ENTITY_X-90}" y="{BOTTOM_ENTITIES_Y-45}" width="{ENTITY_W}" height="{90}" 
        rx="8" fill="#edf2f7" stroke="#4a5568" stroke-width="2.5"/>
  <text x="{RIGHT_ENTITY_X}" y="{BOTTOM_ENTITIES_Y-10}" text-anchor="middle" font-size="13" font-weight="700" fill="#2d3748">Email / Push</text>
  <text x="{RIGHT_ENTITY_X}" y="{BOTTOM_ENTITIES_Y+10}" text-anchor="middle" font-size="13" font-weight="700" fill="#2d3748">Service</text>
  <text x="{RIGHT_ENTITY_X}" y="{BOTTOM_ENTITIES_Y+30}" text-anchor="middle" font-size="10" fill="#718096">(SMTP / Firebase)</text>
'''

def draw_processes():
    """Draw all process bubbles"""
    processes = [
        # Left column
        (1, LEFT_PROCESS_X, "1.0", "Authentication &", "Registration", "#ebf8ff", "#3182ce", "#1a365d"),
        (2, LEFT_PROCESS_X, "3.0", "Vehicle Browse", "& Search", "#f0fff4", "#38a169", "#1c4532"),
        (3, LEFT_PROCESS_X, "5.0", "Booking", "Processing", "#fffaf0", "#dd6b20", "#7b341e"),
        (4, LEFT_PROCESS_X, "7.0", "Payment", "Processing", "#faf5ff", "#805ad5", "#44337a"),
        (5, LEFT_PROCESS_X, "9.0", "License", "Verification", "#fff5f5", "#e53e3e", "#742a2a"),
        (6, LEFT_PROCESS_X, "11.0", "Notification", "Service", "#e6fffa", "#2c7a7b", "#1d4044"),
        # Right column
        (1, RIGHT_PROCESS_X, "2.0", "User", "Management", "#ebf8ff", "#3182ce", "#1a365d"),
        (2, RIGHT_PROCESS_X, "4.0", "Vehicle", "Management", "#f0fff4", "#38a169", "#1c4532"),
        (3, RIGHT_PROCESS_X, "6.0", "Booking", "Management", "#fffaf0", "#dd6b20", "#7b341e"),
        (4, RIGHT_PROCESS_X, "8.0", "Payment", "Verification", "#faf5ff", "#805ad5", "#44337a"),
        (5, RIGHT_PROCESS_X, "10.0", "Reports &", "Analytics", "#fff5f5", "#e53e3e", "#742a2a"),
        (6, RIGHT_PROCESS_X, "12.0", "System", "Settings", "#e6fffa", "#2c7a7b", "#1d4044"),
    ]
    
    svg = "\n  <!-- Processes -->"
    for row, x, num, line1, line2, fill, stroke, text_color in processes:
        y = ROW_Y[row]
        svg += f'''
  <ellipse cx="{x}" cy="{y}" rx="{PROCESS_RX}" ry="{PROCESS_RY}" 
           fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>
  <text x="{x}" y="{y-25}" text-anchor="middle" font-size="14" font-weight="700" fill="{text_color}">{num}</text>
  <text x="{x}" y="{y-5}" text-anchor="middle" font-size="13" font-weight="700" fill="{text_color}">{line1}</text>
  <text x="{x}" y="{y+15}" text-anchor="middle" font-size="13" font-weight="700" fill="{text_color}">{line2}</text>'''
    
    return svg

def draw_data_stores():
    """Draw all data stores"""
    stores = [
        (1, "D1", "Users", "(customers / accounts)"),
        (2, "D2", "Vehicles", "(fleet units / categories)"),
        (3, "D3", "Bookings", "(reservations / status)"),
        (4, "D4", "Payments", "(transactions / status)"),
        (5, "D5", "Licenses", "(verification / images)"),
        (6, "D6", "Notifications", "(alerts / history)"),
        (6.8, "D7", "Settings", "(rates / system config)"),
    ]
    
    svg = "\n  <!-- Data Stores -->"
    for row, label, title, desc in stores:
        y = ROW_Y[1] + (row - 1) * 380  # Adjusted vertical spacing
        tab_x = DATA_STORE_X - 140
        main_x = DATA_STORE_X - 120
        
        svg += f'''
  <rect x="{tab_x}" y="{y-25}" width="20" height="{STORE_H}" fill="white" stroke="#4a5568" stroke-width="2"/>
  <rect x="{main_x}" y="{y-25}" width="{STORE_W}" height="{STORE_H}" fill="#edf2f7" stroke="#4a5568" stroke-width="2"/>
  <text x="{tab_x+10}" y="{y+5}" text-anchor="middle" font-size="12" font-weight="700" fill="#4a5568">{label}</text>
  <text x="{DATA_STORE_X}" y="{y}" text-anchor="middle" font-size="14" font-weight="700" fill="#2d3748">{title}</text>
  <text x="{DATA_STORE_X}" y="{y+18}" text-anchor="middle" font-size="10" fill="#718096">{desc}</text>'''
    
    return svg

def draw_auth_flows():
    """Authentication flows - Row 1"""
    y1 = ROW_Y[1]
    svg = "\n  <!-- Row 1: Authentication Flows -->"
    
    # Customer -> P1.0 (Login)
    x_lane1 = LEFT_SPINE_START + 40
    svg += path([
        (LEFT_ENTITY_X + 90, y1 - 20),
        (x_lane1, y1 - 20),
        (x_lane1, y1 - 30),
        (LEFT_PROCESS_X - PROCESS_RX, y1 - 30)
    ], "#3182ce", "Login / Register", x_lane1 - 70, y1 - 50)
    
    # P1.0 -> Customer (Auth Token)
    svg += path([
        (LEFT_PROCESS_X - PROCESS_RX, y1 + 20),
        (x_lane1 + 30, y1 + 20),
        (x_lane1 + 30, y1 + 30),
        (LEFT_ENTITY_X + 90, y1 + 30)
    ], "#3182ce", "Auth Token", x_lane1 + 10, y1 + 50)
    
    # P1.0 -> D1 (Store User Data)
    store_y1 = y1
    svg += path([
        (LEFT_PROCESS_X + PROCESS_RX, y1 - 20),
        (DATA_STORE_X - 140, y1 - 20)
    ], "#3182ce", "Store User Data", LEFT_PROCESS_X + 280, y1 - 35)
    
    # D1 -> P1.0 (Fetch Credentials)
    svg += path([
        (DATA_STORE_X - 140, y1 + 20),
        (LEFT_PROCESS_X + PROCESS_RX, y1 + 20)
    ], "#3182ce", "Fetch Credentials", LEFT_PROCESS_X + 280, y1 + 35)
    
    # Admin -> P2.0 (Manage Users)
    x_lane_r1 = RIGHT_SPINE_START + 40
    svg += path([
        (RIGHT_ENTITY_X - 90, y1 - 20),
        (x_lane_r1, y1 - 20),
        (x_lane_r1, y1 - 30),
        (RIGHT_PROCESS_X + PROCESS_RX, y1 - 30)
    ], "#3182ce", "Manage Users", x_lane_r1 + 70, y1 - 50)
    
    # P2.0 -> Admin (Account Details)
    svg += path([
        (RIGHT_PROCESS_X + PROCESS_RX, y1 + 30),
        (x_lane_r1 + 30, y1 + 30),
        (x_lane_r1 + 30, y1 + 20),
        (RIGHT_ENTITY_X - 90, y1 + 20)
    ], "#3182ce", "Account Details", x_lane_r1 + 80, y1 + 50)
    
    # P2.0 <-> D1
    svg += path([
        (RIGHT_PROCESS_X - PROCESS_RX, y1 - 20),
        (DATA_STORE_X + 140, y1 - 20)
    ], "#3182ce", "Update Accounts", RIGHT_PROCESS_X - 280, y1 - 35)
    
    svg += path([
        (DATA_STORE_X + 140, y1 + 20),
        (RIGHT_PROCESS_X - PROCESS_RX, y1 + 20)
    ], "#3182ce", "User List", RIGHT_PROCESS_X - 280, y1 + 35)
    
    return svg

def path(points, color, label, label_x, label_y):
    """Generate SVG path with label"""
    path_str = f"M{points[0][0]},{points[0][1]}"
    for x, y in points[1:]:
        path_str += f" L{x},{y}"
    
    svg = f'\n  <path d="{path_str}" fill="none" stroke="{color}" stroke-width="2" marker-end="url(#arrow-{get_color_name(color)})"/>'
    
    if label:
        svg += f'\n  <text x="{label_x}" y="{label_y}" text-anchor="middle" font-size="10" font-weight="600" fill="{color}">{label}</text>'
    
    return svg

def get_color_name(hex_color):
    """Map hex color to marker name"""
    colors = {
        "#3182ce": "blue",
        "#38a169": "green",
        "#dd6b20": "orange",
        "#805ad5": "purple",
        "#e53e3e": "red",
        "#2c7a7b": "teal",
        "#718096": "gray"
    }
    return colors.get(hex_color, "blue")

def draw_vehicle_flows():
    return "\n  <!-- Row 2: Vehicle flows (simplified for now) -->"

def draw_booking_flows():
    return "\n  <!-- Row 3: Booking flows (simplified for now) -->"

def draw_payment_flows():
    return "\n  <!-- Row 4: Payment flows (simplified for now) -->"

def draw_license_flows():
    return "\n  <!-- Row 5: License flows (simplified for now) -->"

def draw_notification_flows():
    return "\n  <!-- Row 6: Notification flows (simplified for now) -->"

# Generate and save
if __name__ == "__main__":
    html_template = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>AUTORIDE Level 1 DFD - Clean</title>
<style>
body {{
  font-family: 'Segoe UI', sans-serif;
  background: #f0f2f5;
  padding: 20px;
  margin: 0;
}}
.container {{
  max-width: {CANVAS_W + 100}px;
  margin: 0 auto;
  background: white;
  padding: 30px;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.1);
}}
h1 {{
  text-align: center;
  color: #1a202c;
  margin-bottom: 10px;
}}
p {{
  text-align: center;
  color: #718096;
  margin-bottom: 30px;
}}
.svg-wrapper {{
  overflow: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}}
</style>
</head>
<body>
<div class="container">
  <h1>AUTORIDE SYSTEM – Level 1 Data Flow Diagram</h1>
  <p>Clean Architecture View - No Overlapping Elements</p>
  <div class="svg-wrapper">
{generate_svg()}
  </div>
</div>
</body>
</html>'''
    
    with open('autoride_dfd_final_clean.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("? Generated: autoride_dfd_final_clean.html")
