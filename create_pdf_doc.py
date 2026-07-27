#!/usr/bin/env python3
"""
Converts DEVELOPMENT_AND_TESTING.md to a professional HTML document
Usage: python create_pdf_doc.py
"""

import markdown
from datetime import datetime

def create_html():
    # Read markdown
    with open('DEVELOPMENT_AND_TESTING_FIXED.md', 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    md = markdown.Markdown(extensions=['extra', 'codehilite', 'tables', 'fenced_code'])
    content_html = md.convert(md_content)
    
    # Create full HTML with styling
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Development and Testing - Autoride System</title>
    <style>
        @media print {{
            body {{ margin: 0.5in; }}
            .page-break {{ page-break-before: always; }}
            .no-print {{ display: none; }}
        }}
        
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            max-width: 8.5in;
            margin: 0 auto;
            padding: 1in;
            color: #333;
            background: white;
        }}
        
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-top: 30px; font-size: 28px; }}
        h2 {{ color: #34495e; margin-top: 25px; font-size: 22px; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }}
        h3 {{ color: #7f8c8d; margin-top: 20px; font-size: 18px; }}
        h4 {{ color: #95a5a6; margin-top: 15px; font-size: 16px; }}
        
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 0.9em;
            color: #c7254e;
        }}
        
        pre {{
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-left: 4px solid #3498db;
            padding: 15px;
            overflow-x: auto;
            border-radius: 4px;
            font-family: 'Courier New', 'Consolas', monospace;
            font-size: 12px;
            line-height: 1.3;
            white-space: pre;
        }}
        
        pre code {{ background: none; padding: 0; color: #333; }}
        
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px 8px; text-align: left; }}
        th {{ background-color: #3498db; color: white; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        
        ul, ol {{ margin: 10px 0; padding-left: 30px; }}
        li {{ margin: 5px 0; }}
        
        .title-page {{ text-align: center; margin-top: 3in; }}
        .title-page h1 {{ font-size: 36px; border: none; margin-bottom: 20px; }}
        .title-page .subtitle {{ font-size: 24px; color: #7f8c8d; margin-bottom: 40px; }}
        .title-page .meta {{ font-size: 14px; color: #95a5a6; }}
        
        .print-button {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 24px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
        }}
        
        .print-button:hover {{ background: #2980b9; }}
    </style>
</head>
<body>
    <button class="print-button no-print" onclick="window.print()">??? Print/Save as PDF</button>
    
    <!-- Title Page -->
    <div class="title-page page-break">
        <h1>DEVELOPMENT AND TESTING FRAMEWORK</h1>
        <div class="subtitle">Autoride Car Rental Booking System</div>
        <div class="meta">
            Document Version: 1.0<br>
            Last Updated: {datetime.now().strftime('%B %d, %Y')}
        </div>
    </div>
    
    <div class="page-break"></div>
    
    <!-- Content -->
    {content_html}
    
</body>
</html>
'''
    
    # Write HTML file
    with open('DEVELOPMENT_AND_TESTING.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("? HTML document created: DEVELOPMENT_AND_TESTING.html")
    print("\n?? To convert to PDF:")
    print("   1. Open the HTML file in Chrome or Edge")
    print("   2. Press Ctrl+P (or click Print button)")
    print("   3. Select 'Save as PDF'")
    print("   4. Click Save")

if __name__ == '__main__':
    create_html()
