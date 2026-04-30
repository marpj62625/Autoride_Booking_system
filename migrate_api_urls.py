
import os
import re

def migrate_urls():
    # Root directory of the project
    root_dir = r"c:\Users\patri\OneDrive\Desktop\AutorideSystem2sides\AutorideSystem"
    
    # Target folders to scan
    target_folders = ["frontend", "admin_app"]
    
    # Patterns to replace
    # 1. Local IP: 192.168.1.26:9999
    # 2. Localhost: localhost:9999 or 127.0.0.1:9999
    patterns = [
        (r'http://192\.168\.1\.26:9999', '/api'),
        (r'http://localhost:9999', '/api'),
        (r'http://127\.0\.1:9999', '/api'),
        (r'const API_BASE = .*9999.*', 'const API_BASE = "/api";'), # Catch variable declarations
    ]

    for folder in target_folders:
        folder_path = os.path.join(root_dir, folder)
        if not os.path.exists(folder_path):
            continue
            
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(('.html', '.js')):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = content
                    for pattern, replacement in patterns:
                        new_content = re.sub(pattern, replacement, new_content)
                    
                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"MIGRATED: {file_path}")

if __name__ == "__main__":
    migrate_urls()
