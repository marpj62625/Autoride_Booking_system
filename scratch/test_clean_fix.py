import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import LineChart, BarChart, PieChart, Reference
from datetime import datetime
import os, zipfile

wb = openpyxl.Workbook()
ws_dash = wb.active
ws_dash.title = "Executive Summary"
ws_dash.views.sheetView[0].showGridLines = True

PRIMARY_GREEN = "00B14F"
NAVY_HEADER = "1E293B"
CARD_BG = "F8FAFC"
TEXT_MUTED = "64748B"
BORDER_COLOR = "CBD5E1"

thin_border = Border(
    left=Side(style='thin', color=BORDER_COLOR),
    right=Side(style='thin', color=BORDER_COLOR),
    top=Side(style='thin', color=BORDER_COLOR),
    bottom=Side(style='thin', color=BORDER_COLOR)
)
card_header_fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
card_body_fill = PatternFill(start_color=CARD_BG, end_color=CARD_BG, fill_type="solid")

report_title = "AUTORIDE SYSTEM - ANNUAL REPORT (2026)"
date_subtitle = "Period: 2026-01-01 to 2026-12-31 | Generated: Oct 13, 2026 11:33 AM"

# Header Banner
ws_dash["A1"] = report_title
ws_dash["A1"].font = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
ws_dash["A1"].fill = PatternFill(start_color=PRIMARY_GREEN, end_color=PRIMARY_GREEN, fill_type="solid")
ws_dash["A1"].alignment = Alignment(horizontal="center", vertical="center")
ws_dash.merge_cells("A1:L2")

# Subtitle Banner
ws_dash["A3"] = date_subtitle
ws_dash["A3"].font = Font(name="Calibri", size=10, italic=True, color=TEXT_MUTED)
ws_dash["A3"].alignment = Alignment(horizontal="center", vertical="center")
ws_dash.merge_cells("A3:L3")

# 4 Symmetrical KPI Cards
total_revenue = 1359397.0
total_bookings = 302
total_expenses = 5000.0
net_profit = 1354397.0
avg_rev = 4501.0
active_fleet = 19
margin_pct = 99.6

kpi_cards = [
    {
        "cols": (1, 3),
        "title": "TOTAL REVENUE",
        "value": f"PHP {total_revenue:,.2f}",
        "sub": f"Avg: PHP {avg_rev:,.2f} / booking",
        "val_color": PRIMARY_GREEN
    },
    {
        "cols": (4, 6),
        "title": "TOTAL BOOKINGS",
        "value": f"{total_bookings:,}",
        "sub": f"Fleet: {active_fleet} active vehicles",
        "val_color": "1E293B"
    },
    {
        "cols": (7, 9),
        "title": "TOTAL EXPENSES",
        "value": f"PHP {total_expenses:,.2f}",
        "sub": "Operations & Maintenance",
        "val_color": "DC2626"
    },
    {
        "cols": (10, 12),
        "title": "NET PROFIT",
        "value": f"PHP {net_profit:,.2f}",
        "sub": f"Operating Margin: {margin_pct:.1f}%",
        "val_color": PRIMARY_GREEN
    }
]

for card in kpi_cards:
    c_start, c_end = card["cols"]
    col_start_letter = get_column_letter(c_start)
    col_end_letter = get_column_letter(c_end)

    top_cell = ws_dash[f"{col_start_letter}5"]
    top_cell.value = card["title"]
    top_cell.font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
    top_cell.fill = card_header_fill
    top_cell.alignment = Alignment(horizontal="center", vertical="center")
    top_cell.border = thin_border
    ws_dash.merge_cells(f"{col_start_letter}5:{col_end_letter}5")

    val_cell = ws_dash[f"{col_start_letter}6"]
    val_cell.value = card["value"]
    val_cell.font = Font(name="Calibri", size=14, bold=True, color=card["val_color"])
    val_cell.fill = card_body_fill
    val_cell.alignment = Alignment(horizontal="center", vertical="center")
    val_cell.border = thin_border
    ws_dash.merge_cells(f"{col_start_letter}6:{col_end_letter}6")

    sub_cell = ws_dash[f"{col_start_letter}7"]
    sub_cell.value = card["sub"]
    sub_cell.font = Font(name="Calibri", size=8, italic=True, color=TEXT_MUTED)
    sub_cell.fill = card_body_fill
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    sub_cell.border = thin_border
    ws_dash.merge_cells(f"{col_start_letter}7:{col_end_letter}7")

# Chart Data sheet
ws_data = wb.create_sheet(title="Chart_Data")
ws_data.views.sheetView[0].showGridLines = True
ws_data.append(["Period", "Bookings", "Revenue (PHP)"])
for row in [("Jan", 25, 115000), ("Feb", 42, 189000), ("Mar", 58, 260000)]:
    ws_data.append(list(row))

line_chart = LineChart()
line_chart.title = "Revenue Trend"
line_chart.width = 15.5
line_chart.height = 11
rev_data_ref = Reference(ws_data, min_col=3, min_row=1, max_row=4)
cats_ref = Reference(ws_data, min_col=1, min_row=2, max_row=4)
line_chart.add_data(rev_data_ref, titles_from_data=True)
line_chart.set_categories(cats_ref)
ws_dash.add_chart(line_chart, "A9")

# Landscape setup with NO forced vertical squash
for ws in [ws_dash, ws_data]:
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    if ws == ws_dash:
        for c_idx in range(1, 13):
            col_letter = get_column_letter(c_idx)
            ws.column_dimensions[col_letter].width = 14
    else:
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = 14

out_path = r"C:\Users\patri\Downloads\clean_fix_test.xlsx"
wb.save(out_path)
print(f"Generated clean fix test: {out_path}")

with zipfile.ZipFile(out_path) as z:
    content = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
    for line in content.split("<row"):
        if line.strip():
            print("<row" + line[:120])
