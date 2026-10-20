import re

with open("admin_app/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

target_ids = [
    'popupDateFrom', 'popupDateTo', 'dashDateFrom', 'dashDateTo',
    'blackoutStartDate', 'blackoutEndDate', 'quickCustomColorPicker',
    'quickBalanceAmount', 'walkinStartDate', 'walkinStartTime',
    'walkinEndDate', 'walkinEndTime', 'fleetExportStartDate',
    'fleetExportEndDate', 'expDate', 'rptDateFrom', 'rptDateTo',
    'vNextService', 'vLtoExpiry', 'inspectDriverOTAmount'
]

for idx, line in enumerate(lines):
    for tid in target_ids:
        if f'id="{tid}"' in line or f"id='{tid}'" in line:
            print(f"Line {idx+1} [{tid}]: {line.strip()}")
