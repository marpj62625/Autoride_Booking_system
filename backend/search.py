import sys

def find_routes():
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if 'def book(' in line or 'def modify_booking(' in line or 'def check_vehicle_availability(' in line:
            print(f"{i+1}: {line.strip()}")

find_routes()
