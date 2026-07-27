#!/usr/bin/env python3
"""
Converts DEVELOPMENT_AND_TESTING.md to HTML and optionally PDF
Usage: python convert_to_pdf.py
"""

def md_to_html():
    """Convert markdown to HTML with professional styling"""
    
    # Read markdown file
    with open('DEVELOPMENT_AND_TESTING.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple markdown to HTML conversion
    html_content = content
    
    # Headers
    import re
    html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html_content, flags=re.MULTILINE)
    
    # Bold and italic
    html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
    html_content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_content)
    
    # Code blocks
    html_content = re.sub(r'```python\n(.*?)```', r'<pre class="code python"><code>\1</code></pre>', html_content, flags=re.DOTALL)
    html_content = re.sub(r'```javascript\n(.*?)```', r'<pre class="code javascript"><code>\1</code></pre>', html_content, flags=re.DOTALL)
    html_content = re.sub(r'```json\n(.*?)```', r'<pre class="code json"><code>\1</code></pre>', html_content, flags=re.DOTALL)
    html_content = re.sub(r'```bash\n(.*?)```', r'<pre class="code bash"><code>\1</code></pre>', html_content, flags=re.DOTALL)
    html_content = re.sub(r'```\n(.*?)```', r'<pre class="code"><code>\1</code></pre>', html_content, flags=re.DOTALL)
    
    # Inline code
    html_content = re.sub(r'`(.+?)`', r'<code>\1</code>', html_content)
    
    # Lists
    html_content = re.sub(r'^\- (.+)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'(<li>.*?</li>\n)+', r'<ul>\g<0></ul>', html_content, flags=re.DOTALL)
    
    # Checkboxes
    html_content = re.sub(r'\[ \]', r'<input type="checkbox" disabled>', html_content)
    html_content = re.sub(r'\[?\]', r'<input type="checkbox" checked disabled>', html_content)
    
