import sys
sys.path.insert(0, 'backend')
from app import app
import openpyxl, io

client = app.test_client()
res = client.get('/api/admin/reports/export-excel?filter=month&date_from=2026-10-01&date_to=2026-10-31')

wb = openpyxl.load_workbook(io.BytesIO(res.data))
for sheetname in wb.sheetnames:
    ws = wb[sheetname]
    print(f"Sheet: {sheetname:25s} | Orientation: {ws.page_setup.orientation} | fitToWidth: {ws.page_setup.fitToWidth} | fitToHeight: {ws.page_setup.fitToHeight}")
