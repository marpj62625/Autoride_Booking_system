# -*- coding: utf-8 -*-
# Remove the Live Coordinates card from GPS tab in both admin files

import re

for path in ['admin_mobile/www/index.html', 'admin_app/index.html']:
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        c = f.read()

    # Remove the Live Coordinates card div
    # It starts with a chart-card/stat-card containing "Live Coordinates" and ends before </div>\n\n        </div>
    # Use the unique "Live Coordinates" heading as anchor
    start_marker = '        <!-- Live Coordinates -->'
    if start_marker not in c:
        # Try without comment
        start_marker = None
        # Find by content
        idx = c.find('Live Coordinates')
        if idx == -1:
            print(path, ': Live Coordinates not found')
            continue

        # Walk back to find the opening div of the card
        # Look for the nearest preceding <div class="chart-card" or stat-card
        card_open = c.rfind('<div class="chart-card"', 0, idx)
        card_open2 = c.rfind('<div class="stat-card"', 0, idx)
        card_start = max(card_open, card_open2)
        # Walk back further to find any preceding whitespace/newline
        while card_start > 0 and c[card_start-1] in ' \t':
            card_start -= 1
        if c[card_start-1] == '\n':
            card_start -= 1

        # Find the closing </div> that matches this card
        # Count depth
        depth = 0
        i = card_start
        while i < len(c):
            if c[i:i+4] == '<div':
                depth += 1
                i += 4
            elif c[i:i+6] == '</div>':
                depth -= 1
                if depth == 0:
                    card_end = i + 6
                    # Consume trailing newline
                    if card_end < len(c) and c[card_end] == '\n':
                        card_end += 1
                    break
                i += 6
            else:
                i += 1

        c = c[:card_start] + c[card_end:]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)
        print(path, ': Removed Live Coordinates card')
    else:
        # Remove from comment to end of card
        print(path, ': Has comment marker, handle differently')
