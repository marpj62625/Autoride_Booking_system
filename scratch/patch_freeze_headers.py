import os

def patch_freeze(filepath):
    print(f"Patching sticky frozen headers in {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update the table container & thead in HTML
    old_container = """        <div id="fleetCalendarScrollContainer" style="overflow-x: auto; background: var(--surface-solid); border-radius: 12px; border: 1px solid var(--border); box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);">
            <table style="width: max-content; table-layout: fixed; border-collapse: separate; border-spacing: 0; min-width: 800px; font-size: 0.78rem; color: var(--text-main);" id="fleetCalendarTable">
                <thead>
                    <tr id="fleetCalendarDaysOfWeekRow" style="background: var(--surface-solid);">
                        <!-- Days of week: TUE, WED, THU... injected via JS -->
                    </tr>
                    <tr id="fleetCalendarHeaderRow" style="background: var(--surface-solid); border-bottom: 2px solid var(--border);">
                        <!-- Dates: 1, 2, 3... injected via JS -->
                    </tr>
                </thead>"""

    new_container = """        <div id="fleetCalendarScrollContainer" style="overflow: auto; max-height: calc(100vh - 210px); min-height: 480px; background: var(--surface-solid); border-radius: 12px; border: 1px solid var(--border); box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);">
            <table style="width: max-content; table-layout: fixed; border-collapse: separate; border-spacing: 0; min-width: 800px; font-size: 0.78rem; color: var(--text-main);" id="fleetCalendarTable">
                <thead style="position: sticky; top: 0; z-index: 25; background: var(--surface-solid);">
                    <tr id="fleetCalendarDaysOfWeekRow" style="height: 38px; background: var(--surface-solid);">
                        <!-- Days of week: TUE, WED, THU... injected via JS -->
                    </tr>
                    <tr id="fleetCalendarHeaderRow" style="height: 24px; background: var(--surface-solid); border-bottom: 2px solid var(--border);">
                        <!-- Dates: 1, 2, 3... injected via JS -->
                    </tr>
                </thead>"""

    if old_container in content:
        content = content.replace(old_container, new_container, 1)
        print("  Updated scroll container & thead HTML successfully")
    else:
        print("  Warning: old_container not found, checking if already modified")

    # 2. Update the JS header generation to include position: sticky, top, z-index and opaque background
    old_js_start = "            // 2-Tier Header:"
    old_js_end = "            const headerRowEl = document.getElementById('fleetCalendarHeaderRow');\n            if (headerRowEl) headerRowEl.innerHTML = row2Html;"

    new_js_block = """            // 2-Tier Header:
            // Row 1: Day Name & Number (Colspan 2 for AM and PM, frozen at top: 0)
            // Left sticky cell spans 2 rows (frozen at top: 0, left: 0, z-index: 35)
            let row1Html = `<th rowspan="2" class="fc-vcol fc-vhead" style="padding: 10px 12px; border: 1px solid var(--border); text-align: left; background: var(--surface-solid); font-weight: 800; min-width: 180px; width: 180px; max-width: 180px; position: sticky; left: 0; top: 0; z-index: 35; border-right: 2px solid var(--border); border-bottom: 2px solid var(--border); color: var(--text-main); font-size: 0.8rem; vertical-align: middle;">
                <div style="display:flex; align-items:center; gap:6px;">
                    <i class="fas fa-car-side" style="color:#00B14F;"></i>
                    <span class="fc-vhead-text">VEHICLE / UNIT</span>
                </div>
            </th>`;

            // Row 2: Sub-columns for AM and PM (frozen at top: 38px, z-index: 20)
            let row2Html = '';

            for (let d = 1; d <= daysInMonth; d++) {
                const dayDate = new Date(year, month, d);
                const dayOfWeek = dayDate.getDay();
                const isWeekend = (dayOfWeek === 0 || dayOfWeek === 6);
                const isToday = isCurrentMonth && today.getDate() === d;
                
                const dowBg = isToday ? '#dcfce7' : (isWeekend ? '#fee2e2' : 'var(--surface-solid)');
                const dowColor = isToday ? '#15803d' : (isWeekend ? '#ef4444' : 'var(--text-muted)');
                const dateBg = isToday ? '#bbf7d0' : (isWeekend ? '#fef2f2' : 'var(--surface-solid)');
                const dateColor = isToday ? '#15803d' : 'var(--text-main)';

                row1Html += `<th colspan="2" style="padding: 4px 2px; border: 1px solid var(--border); text-align: center; background: ${dowBg}; position: sticky; top: 0; z-index: 20;">
                    <div style="font-weight: 800; font-size: 0.62rem; color: ${dowColor}; text-transform: uppercase;">${dayNamesShort[dayOfWeek]}</div>
                    <div style="font-weight: 900; font-size: 0.82rem; color: ${dateColor}; line-height: 1.1;">${d}</div>
                </th>`;

                row2Html += `<th style="padding: 2px; border: 1px solid var(--border); border-right: 1px dashed var(--border); border-bottom: 2px solid var(--border); text-align: center; font-weight: 800; font-size: 0.58rem; min-width: 28px; width: 28px; background: ${dateBg}; color: ${isToday ? '#15803d' : 'var(--text-muted)'}; position: sticky; top: 38px; z-index: 20;">AM</th>`;
                row2Html += `<th style="padding: 2px; border: 1px solid var(--border); border-bottom: 2px solid var(--border); text-align: center; font-weight: 800; font-size: 0.58rem; min-width: 28px; width: 28px; background: ${dateBg}; color: ${isToday ? '#15803d' : 'var(--text-muted)'}; position: sticky; top: 38px; z-index: 20;">PM</th>`;
            }

            const daysOfWeekEl = document.getElementById('fleetCalendarDaysOfWeekRow');
            if (daysOfWeekEl) daysOfWeekEl.innerHTML = row1Html;
            const headerRowEl = document.getElementById('fleetCalendarHeaderRow');
            if (headerRowEl) headerRowEl.innerHTML = row2Html;"""

    if old_js_start in content and old_js_end in content:
        start_idx = content.find(old_js_start)
        end_idx = content.find(old_js_end) + len(old_js_end)
        content = content[:start_idx] + new_js_block + content[end_idx:]
        print("  Updated JS Header block with sticky coordinates successfully")
    else:
        print("  Warning: old_js block not found")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Finished {filepath}!")

if __name__ == '__main__':
    patch_freeze('AutorideSystem/admin_app/index.html')
    patch_freeze('AutorideSystem/admin_mobile/www/index.html')
