"""
PDF Generator for Development and Testing Documentation
Converts the markdown documentation to a professional PDF format
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib import colors
from datetime import datetime

def create_pdf():
    # Create PDF document
    pdf_filename = "DEVELOPMENT_AND_TESTING_AUTORIDE.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=16, textColor=colors.HexColor('#2c3e50')))
    styles.add(ParagraphStyle(name='Heading1Custom', parent=styles['Heading1'], 
                              fontSize=24, textColor=colors.HexColor('#2c3e50'), spaceAfter=12))
    styles.add(ParagraphStyle(name='Heading2Custom', parent=styles['Heading2'],
                              fontSize=18, textColor=colors.HexColor('#34495e'), spaceAfter=10))
    styles.add(ParagraphStyle(name='Code', parent=styles['Code'],
                              fontSize=9, leftIndent=20, textColor=colors.HexColor('#c7254e'),
                              backColor=colors.HexColor('#f9f2f4')))
    
    # Title Page
    elements.append(Spacer(1, 2*inch))
    title = Paragraph("DEVELOPMENT AND TESTING FRAMEWORK", styles['Heading1Custom'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    subtitle = Paragraph("Autoride Car Rental Booking System", styles['Center'])
    elements.append(subtitle)
    elements.append(Spacer(1, 0.5*inch))
    
    date_text = Paragraph(f"Document Version: 1.0<br/>Last Updated: {datetime.now().strftime('%B %d, %Y')}", 
                         styles['Center'])
    elements.append(date_text)
    elements.append(PageBreak())
    
    # Table of Contents
    toc_title = Paragraph("Table of Contents", styles['Heading1Custom'])
    elements.append(toc_title)
    elements.append(Spacer(1, 0.2*inch))
    
    toc_data = [
        ["1.", "System Overview", "3"],
        ["2.", "Development Framework", "5"],
        ["3.", "Testing Framework", "12"],
        ["4.", "Quality Assurance Process", "20"],
        ["5.", "Tools and Technologies", "22"],
        ["6.", "Best Practices", "24"],
    ]
    
    toc_table = Table(toc_data, colWidths=[0.5*inch, 5*inch, 0.5*inch])
    toc_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 12),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(toc_table)
    elements.append(PageBreak())
    
    # Section 1: System Overview
    add_section(elements, styles, "1. System Overview",
                "The Autoride Car Rental Booking System is a comprehensive mobile-first application " +
                "that enables customers to rent vehicles and administrators to manage the rental business operations.")
    
    elements.append(Paragraph("<b>Architecture</b>", styles['Heading2Custom']))
