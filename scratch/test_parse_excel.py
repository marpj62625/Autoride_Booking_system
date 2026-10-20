import sys, os
sys.path.append(os.path.abspath('backend'))
import fleet_import

recs = fleet_import.parse_fleet_excel_file('ARC-MONITORING-2026.xlsx')
oct_recs = [r for r in recs if r['start_date'] >= '2026-10-01']
print(f"Total records in Excel: {len(recs)}")
print(f"Total records from Oct 2026 onwards: {len(oct_recs)}")
for r in oct_recs:
    print(r['start_date'], "to", r['end_date'], "::", r.get('vehicle_label'), "::", r.get('customer_name'))
