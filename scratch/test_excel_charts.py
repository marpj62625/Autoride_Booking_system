import openpyxl
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import io

wb = openpyxl.Workbook()

# Sheet 1: Executive Dashboard
ws_dash = wb.active
ws_dash.title = "Executive Summary"
ws_dash.views.sheetView[0].showGridLines = True

# Title
ws_dash["A1"] = "AUTORIDE SYSTEM — EXECUTIVE PERFORMANCE REPORT"
ws_dash["A1"].font = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
ws_dash["A1"].fill = PatternFill(start_color="00B14F", end_color="00B14F", fill_type="solid")
ws_dash["A1"].alignment = Alignment(horizontal="center", vertical="center")
ws_dash.merge_cells("A1:H2")

# Summary KPI Table
kpis = [
    ("TOTAL REVENUE", "PHP 1,359,397.00"),
    ("TOTAL BOOKINGS", "302"),
    ("AVG REVENUE / BOOKING", "PHP 4,501.00"),
    ("TOTAL EXPENSES", "PHP 5,000.00"),
    ("NET PROFIT", "PHP 1,354,397.00"),
    ("ACTIVE FLEET", "19")
]

ws_dash["A4"] = "KPI METRIC"
ws_dash["B4"] = "VALUE"
ws_dash["A4"].font = Font(bold=True, color="FFFFFF")
ws_dash["B4"].font = Font(bold=True, color="FFFFFF")
ws_dash["A4"].fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
ws_dash["B4"].fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")

for i, (k, v) in enumerate(kpis, start=5):
    ws_dash[f"A{i}"] = k
    ws_dash[f"B{i}"] = v
    ws_dash[f"A{i}"].font = Font(bold=True)
    ws_dash[f"B{i}"].font = Font(bold=True, color="00B14F" if "PROFIT" in k or "REVENUE" in k else "000000")

# Sheet 2: Data Sources (for charts)
ws_data = wb.create_sheet(title="Data_Sources")
ws_data.views.sheetView[0].showGridLines = True

# Monthly Trend Data
months_data = [
    ("Month", "Bookings", "Revenue (PHP)"),
    ("Jan", 26, 124186.0),
    ("Feb", 17, 88986.0),
    ("Mar", 12, 127888.0),
    ("Apr", 29, 96587.0),
    ("May", 39, 174880.0),
    ("Jun", 32, 137582.0),
    ("Jul", 48, 162981.0),
    ("Aug", 44, 168061.0),
    ("Sep", 34, 83494.0),
    ("Oct", 16, 164653.0),
    ("Nov", 3, 9599.0),
    ("Dec", 2, 20500.0),
]

for row in months_data:
    ws_data.append(row)

# Format header in Data_Sources
for col in range(1, 4):
    cell = ws_data.cell(row=1, column=col)
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")

# 1. Line Chart: Revenue Trend
line_chart = LineChart()
line_chart.title = "Revenue Trend (2026)"
line_chart.style = 13
line_chart.y_axis.title = "Revenue (PHP)"
line_chart.x_axis.title = "Month"
line_chart.width = 16
line_chart.height = 9.5

data_ref = Reference(ws_data, min_col=3, min_row=1, max_row=13)
cats_ref = Reference(ws_data, min_col=1, min_row=2, max_row=13)
line_chart.add_data(data_ref, titles_from_data=True)
line_chart.set_categories(cats_ref)
ws_dash.add_chart(line_chart, "D4")

# 2. Bar Chart: Bookings Detail
bar_chart = BarChart()
bar_chart.type = "col"
bar_chart.style = 10
bar_chart.title = "Bookings Detail (2026)"
bar_chart.y_axis.title = "Number of Bookings"
bar_chart.x_axis.title = "Month"
bar_chart.width = 16
bar_chart.height = 9.5

b_data_ref = Reference(ws_data, min_col=2, min_row=1, max_row=13)
bar_chart.add_data(b_data_ref, titles_from_data=True)
bar_chart.set_categories(cats_ref)
ws_dash.add_chart(bar_chart, "D20")

# Top Vehicles Data
ws_data.cell(row=1, column=5, value="Vehicle")
ws_data.cell(row=1, column=6, value="Revenue")
ws_data.cell(row=1, column=5).font = Font(bold=True, color="FFFFFF")
ws_data.cell(row=1, column=6).font = Font(bold=True, color="FFFFFF")
ws_data.cell(row=1, column=5).fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
ws_data.cell(row=1, column=6).fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")

top_vehs = [
    ("Toyota Innova XE AT (NHN 5388)", 375000.0),
    ("Honda BR-V (NID 2724)", 268555.0),
    ("Toyota Hiace (NCW 3918)", 207948.0),
    ("Toyota Vios J MT (NCX 4117)", 185696.0),
    ("Toyota Vios XLE AT (DBJ 9483)", 127600.0)
]

for r_idx, (v_name, v_rev) in enumerate(top_vehs, start=2):
    ws_data.cell(row=r_idx, column=5, value=v_name)
    ws_data.cell(row=r_idx, column=6, value=v_rev)

# 3. Pie Chart: Top Vehicles
pie_chart = PieChart()
pie_chart.title = "Top Vehicles by Revenue"
pie_chart.width = 14
pie_chart.height = 9.5

pie_data = Reference(ws_data, min_col=6, min_row=1, max_row=6)
pie_cats = Reference(ws_data, min_col=5, min_row=2, max_row=6)
pie_chart.add_data(pie_data, titles_from_data=True)
pie_chart.set_categories(pie_cats)
ws_dash.add_chart(pie_chart, "A12")

# Set Column Widths
for ws in [ws_dash, ws_data]:
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

out_buf = io.BytesIO()
wb.save(out_buf)
out_buf.seek(0)
print(f"Generated Excel file with charts successfully! Size: {len(out_buf.getvalue())} bytes")

wb.save("scratch/test_report_with_charts.xlsx")
print("Saved to scratch/test_report_with_charts.xlsx")
