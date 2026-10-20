import sys
sys.path.append('backend')
import app
import fleet_import

with app.app.app_context():
    cur = app.get_cursor()
    records = fleet_import.parse_fleet_excel_file('ARC-MONITORING-2026.xlsx')
    print(f"Extracted {len(records)} records from ARC-MONITORING-2026.xlsx")
    
    preview = fleet_import.match_and_validate_import_records(records[:25], cur)
    print("\nSummary for first 25 records:")
    print(preview['summary'])
    
    print("\nFirst 6 enriched records:")
    for r in preview['records'][:6]:
        print(f"Customer: {r['customer_name']} | Match Status: {r['user_match_status']} (UID: {r['matched_user_id']}) | Vehicle: {r['vehicle_name']} ({r['plate_number']}) | {r['start_date']} -> {r['end_date']} ({r['total_days']}d) | Price: P{r['total_price']} | Conflict: {r['is_conflict']}")
    
    cur.close()
