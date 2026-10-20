with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Find all occurrences of #fleet-calendar in style
matches = [m.start() for m in re.finditer(r'#fleet-calendar', text)]
for idx, pos in enumerate(matches):
    if pos < 11000: # inside style
        print(f"CSS match {idx+1} at {pos}:")
        print(text[pos-20:pos+300])
        print("="*40)

# Check how the calendar container/table/grid is structured
m_grid = re.search(r'id=["\']fcGrid["\']|id=["\']fcTable["\']|class=["\']fc-container["\']|class=["\']fc-grid["\']', text)
if m_grid:
    print("Found grid/container element:", m_grid.group(0))
    print(text[m_grid.start()-50:m_grid.start()+200])
