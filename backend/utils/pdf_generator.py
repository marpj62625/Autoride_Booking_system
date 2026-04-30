from fpdf import FPDF
import os
from datetime import datetime

class ReceiptGenerator(FPDF):
    def header(self):
        # Company Logo Placeholder or Border
        self.set_fill_color(30, 41, 59) # Dark blue/slate
        self.rect(0, 0, 210, 40, 'F')
        
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(255, 255, 255)
        self.cell(0, 20, 'AUTORIDE SYSTEM', 0, 1, 'C')
        self.set_font('Helvetica', '', 10)
        self.cell(0, 0, 'Official Electronic Receipt', 0, 1, 'C')
        self.ln(25)

    def footer(self):
        self.set_y(-25)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Authorized Digital Copy', 0, 0, 'C')
        self.ln(5)
        self.cell(0, 10, 'Thank you for choosing Autoride!', 0, 0, 'C')

def generate_booking_pdf(booking, user, vehicle):
    pdf = ReceiptGenerator()
    pdf.add_page()
    
    # 1. Invoice Summary
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, f'RECEIPT #{booking["id"]:06d}', 0, 1, 'L')
    pdf.ln(5)
    
    # Grid Layout for Customer & Rental Info
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(95, 7, 'BILLED TO:', 0, 0)
    pdf.cell(95, 7, 'RENTAL PERIOD:', 0, 1)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(95, 6, str(user['full_name']), 0, 0)
    pdf.cell(95, 6, f'Start: {booking["start_date"]}', 0, 1)
    
    pdf.cell(95, 6, str(user['email']), 0, 0)
    pdf.cell(95, 6, f'End:   {booking["end_date"]}', 0, 1)
    
    pdf.ln(10)

    # 2. Vehicle Info
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 10, f' VEHICLE DETAILS', 0, 1, 'L', fill=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(40, 8, ' Brand/Model:', 0, 0)
    pdf.cell(0, 8, f'{vehicle["brand"]} {vehicle["model"]}', 0, 1)
    pdf.cell(40, 8, ' Plate Number:', 0, 0)
    pdf.cell(0, 8, f'{vehicle["plate_number"]}', 0, 1)
    pdf.cell(40, 8, ' Rental Type:', 0, 0)
    pdf.cell(0, 8, f'{booking["rental_type"]}', 0, 1)
    
    pdf.ln(10)

    # 3. Financial Breakdown Table
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 10, ' COST BREAKDOWN', 0, 1, 'L', fill=True)
    
    def add_row(label, value, is_bold=False, is_total=False):
        if is_total:
            pdf.ln(2)
            pdf.set_draw_color(30, 41, 59)
            pdf.line(140, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)
            pdf.set_font('Helvetica', 'B', 12)
        elif is_bold:
            pdf.set_font('Helvetica', 'B', 10)
        else:
            pdf.set_font('Helvetica', '', 10)
            
        pdf.cell(140, 8, f' {label}', 0, 0)
        pdf.cell(50, 8, f'PHP {float(value):,.2f}', 0, 1, 'R')

    add_row('Base Rental Rate', booking['base_price'])
    
    if float(booking.get('addon_price', 0)) > 0:
        add_row('Insurance/Extras', booking['addon_price'])
    
    insurance = float(booking.get('insurance_price', 0))
    if insurance > 0:
        add_row('Basic Insurance', insurance)

    # Enterprise Fields
    discount = float(booking.get('discount_amount', 0))
    if discount > 0:
        pdf.set_text_color(185, 28, 28) # Red for discount
        add_row('Promo Discount', -discount)
        pdf.set_text_color(0, 0, 0)

    points_disc = float(booking.get('points_discount_amount', 0))
    if points_disc > 0:
        pdf.set_text_color(185, 28, 28)
        add_row('Loyalty Points Redemption', -points_disc)
        pdf.set_text_color(0, 0, 0)

    add_row('Total Payable Amount', booking['total_price'], is_total=True)
    
    # Points Earned
    earned = booking.get('points_earned', 0)
    if earned > 0:
        pdf.ln(5)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(21, 128, 61) # Green
        pdf.cell(0, 5, f'* You earned {earned} loyalty points with this booking!', 0, 1, 'R')

    return pdf.output()
