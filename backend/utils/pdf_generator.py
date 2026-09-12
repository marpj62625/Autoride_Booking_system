from fpdf import FPDF
import os
from datetime import datetime

class ReceiptGenerator(FPDF):
    def header(self):
        # Company Logo Banner
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

def generate_booking_pdf(booking, user, vehicle, payment=None):
    pdf = ReceiptGenerator()
    pdf.add_page()
    
    # 1. Invoice Summary Header
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(100, 10, f'RECEIPT #{booking["id"]:06d}', 0, 0, 'L')
    
    # Status Tag in header
    b_status = str(booking.get('status') or 'Pending').upper()
    p_status = str(booking.get('payment_status') or 'Unpaid').upper()
    pdf.set_font('Helvetica', 'B', 10)
    if b_status == 'CANCELLED':
        pdf.set_text_color(220, 38, 38) # Red
    elif b_status in ('CONFIRMED', 'APPROVED', 'PICKED UP', 'COMPLETED'):
        pdf.set_text_color(22, 163, 74) # Green
    else:
        pdf.set_text_color(217, 119, 6) # Amber
    pdf.cell(90, 10, f'BOOKING: {b_status}', 0, 1, 'R')
    pdf.set_text_color(30, 41, 59)
    pdf.ln(2)
    
    # Grid Layout for Customer & Rental Info
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(95, 7, 'BILLED TO:', 0, 0)
    pdf.cell(95, 7, 'RENTAL PERIOD:', 0, 1)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(95, 6, str(user.get('full_name') or 'Valued Customer'), 0, 0)
    s_time = f" {booking['start_time']}" if booking.get('start_time') else ""
    pdf.cell(95, 6, f'Start: {booking["start_date"]}{s_time}', 0, 1)
    
    pdf.cell(95, 6, str(user.get('email') or 'N/A'), 0, 0)
    e_time = f" {booking['end_time']}" if booking.get('end_time') else ""
    pdf.cell(95, 6, f'End:   {booking["end_date"]}{e_time}', 0, 1)
    
    if user.get('phone'):
        pdf.cell(95, 6, f'Phone: {user["phone"]}', 0, 1)
    else:
        pdf.ln(2)
        
    pdf.ln(6)

    # 2. Vehicle Info
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, ' VEHICLE DETAILS', 0, 1, 'L', fill=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(40, 7, ' Brand/Model:', 0, 0)
    pdf.cell(0, 7, f'{vehicle.get("brand", "")} {vehicle.get("model", "")}', 0, 1)
    pdf.cell(40, 7, ' Plate Number:', 0, 0)
    pdf.cell(0, 7, f'{vehicle.get("plate_number", "N/A")}', 0, 1)
    pdf.cell(40, 7, ' Rental Type:', 0, 0)
    pdf.cell(0, 7, f'{booking.get("rental_type", "Self Drive")}', 0, 1)
    
    pdf.ln(6)

    # 3. Cost Breakdown Table
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, ' COST BREAKDOWN', 0, 1, 'L', fill=True)
    
    def add_row(label, value, is_bold=False, is_total=False, custom_val_str=None):
        if is_total:
            pdf.ln(2)
            pdf.set_draw_color(30, 41, 59)
            pdf.line(130, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)
            pdf.set_font('Helvetica', 'B', 11)
        elif is_bold:
            pdf.set_font('Helvetica', 'B', 10)
        else:
            pdf.set_font('Helvetica', '', 10)
            
        pdf.cell(120, 7, f' {label}', 0, 0)
        if custom_val_str:
            pdf.cell(70, 7, custom_val_str, 0, 1, 'R')
        else:
            pdf.cell(70, 7, f'PHP {float(value):,.2f}', 0, 1, 'R')

    add_row('Base Rental Rate', booking['base_price'])
    
    if float(booking.get('addon_price', 0) or 0) > 0:
        add_row('Insurance/Extras', booking['addon_price'])
    
    insurance = float(booking.get('insurance_price', 0) or 0)
    if insurance > 0:
        add_row('Basic Insurance', insurance)

    discount = float(booking.get('discount_amount', 0) or 0)
    if discount > 0:
        pdf.set_text_color(185, 28, 28)
        add_row('Promo Discount', -discount)
        pdf.set_text_color(0, 0, 0)

    points_disc = float(booking.get('points_discount_amount', 0) or 0)
    if points_disc > 0:
        pdf.set_text_color(185, 28, 28)
        add_row('Loyalty Points Redemption', -points_disc)
        pdf.set_text_color(0, 0, 0)

    penalty = float(booking.get('penalty_amount', 0) or 0)
    if penalty > 0:
        pdf.set_text_color(185, 28, 28)
        add_row('Late / Damage Penalties', penalty)
        pdf.set_text_color(0, 0, 0)

    add_row('Total Contract Amount', booking['total_price'], is_total=True)
    pdf.ln(6)

    # 4. Payment Details & Settlement Record
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, ' PAYMENT DETAILS & SETTLEMENT RECORD', 0, 1, 'L', fill=True)
    
    # Determine payment method
    pay_method = 'N/A'
    if payment and payment.get('method'):
        pay_method = str(payment['method'])
    elif booking.get('payment_method'):
        pay_method = str(booking['payment_method'])
    elif booking.get('payment_type'):
        pay_method = str(booking['payment_type'])
        
    p_type = booking.get('payment_type')
    if p_type and p_type != pay_method:
        pay_method_full = f"{pay_method} ({p_type})"
    else:
        pay_method_full = pay_method

    ref_num = (payment and payment.get('reference_number')) or booking.get('reference_num') or 'N/A'
    amt_paid = float(booking.get('amount_paid', 0) or 0)
    bal_amt = float(booking.get('balance_amount', 0) or 0)
    is_cancelled = b_status in ('CANCELLED', 'REJECTED')

    add_row('Payment Status', 0, custom_val_str=p_status)
    add_row('Payment Method', 0, custom_val_str=pay_method_full)
    if ref_num and ref_num != 'N/A':
        add_row('Reference / Trans No.', 0, custom_val_str=str(ref_num))
    
    pdf.set_text_color(22, 163, 74) # Green for amount paid
    add_row('Amount Actually Paid', amt_paid, is_bold=True)
    pdf.set_text_color(0, 0, 0)

    if is_cancelled:
        add_row('Remaining Balance Due', 0, custom_val_str='PHP 0.00 (Cancelled - Void)')
        # Refund status
        ref_amt = float(booking.get('refund_amount') or amt_paid)
        if booking.get('payment_status') == 'Refund Pending':
            pdf.set_text_color(217, 119, 6) # Amber
            add_row('Refund Status', 0, custom_val_str=f'Refund Pending: PHP {ref_amt:,.2f}')
            pdf.set_text_color(0, 0, 0)
        elif booking.get('payment_status') == 'Refunded':
            pdf.set_text_color(22, 163, 74)
            ref_ref_str = f" (Ref: {booking.get('refund_ref')})" if booking.get('refund_ref') else ""
            add_row('Refund Status', 0, custom_val_str=f'Refunded: PHP {ref_amt:,.2f}{ref_ref_str}')
            pdf.set_text_color(0, 0, 0)
    else:
        if bal_amt > 0:
            pdf.set_text_color(220, 38, 38) # Red for balance
            add_row('Remaining Balance Due', bal_amt, is_bold=True)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.set_text_color(22, 163, 74)
            add_row('Remaining Balance Due', 0, custom_val_str='PHP 0.00 (Fully Settled)', is_bold=True)
            pdf.set_text_color(0, 0, 0)

    # Points Earned
    earned = booking.get('points_earned', 0)
    if earned and earned > 0:
        pdf.ln(4)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(21, 128, 61)
        pdf.cell(0, 5, f'* You earned {earned} loyalty points with this booking!', 0, 1, 'R')

    return bytes(pdf.output())
