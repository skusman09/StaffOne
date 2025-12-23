"""
PDF generation utilities for reports.

Generates professional PDF reports for payroll and attendance.
"""
from io import BytesIO
from datetime import date
from typing import List, Dict, Any

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_payroll_pdf(
    records: List[Dict[str, Any]],
    year: int,
    month: int,
    company_name: str = "Company Name"
) -> bytes:
    """Generate a PDF payroll report.
    
    Args:
        records: List of salary records with employee details
        year: Payroll year
        month: Payroll month
        company_name: Company name for header
    
    Returns:
        PDF file as bytes
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    elements = []
    
    # Header
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    
    elements.append(Paragraph(f"{company_name}", title_style))
    elements.append(Paragraph(f"Payroll Report - {month_names[month-1]} {year}", subtitle_style))
    elements.append(Paragraph(f"Generated on: {date.today().strftime('%B %d, %Y')}", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Table headers
    table_data = [
        ['Employee', 'Days\nWorked', 'Hours\nWorked', 'OT Hours', 'Base Salary', 'OT Pay', 'Deductions', 'Net Salary']
    ]
    
    # Add records
    for record in records:
        table_data.append([
            record.get('user_full_name', 'Unknown')[:20],
            str(record.get('days_worked', 0)),
            f"{record.get('total_hours_worked', 0):.1f}",
            f"{record.get('overtime_hours', 0):.1f}",
            f"₹{record.get('base_salary', 0):,.0f}",
            f"+₹{record.get('overtime_pay', 0):,.0f}",
            f"-₹{(record.get('deductions', 0) + record.get('absence_deductions', 0)):,.0f}",
            f"₹{record.get('net_salary', 0):,.0f}"
        ])
    
    # Add totals row
    total_base = sum(r.get('base_salary', 0) for r in records)
    total_ot = sum(r.get('overtime_pay', 0) for r in records)
    total_ded = sum(r.get('deductions', 0) + r.get('absence_deductions', 0) for r in records)
    total_net = sum(r.get('net_salary', 0) for r in records)
    
    table_data.append([
        'TOTAL', '', '', '', 
        f"₹{total_base:,.0f}", 
        f"+₹{total_ot:,.0f}", 
        f"-₹{total_ded:,.0f}", 
        f"₹{total_net:,.0f}"
    ])
    
    # Create table
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        # Header style
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        
        # Body style
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 8),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        
        # Totals row
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e5e7eb')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9fafb')]),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Summary
    summary_style = ParagraphStyle('Summary', parent=styles['Normal'], fontSize=10)
    elements.append(Paragraph(f"<b>Total Employees:</b> {len(records)}", summary_style))
    elements.append(Paragraph(f"<b>Total Net Payroll:</b> ₹{total_net:,.2f}", summary_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_attendance_pdf(
    records: List[Dict[str, Any]],
    start_date: date,
    end_date: date,
    company_name: str = "Company Name"
) -> bytes:
    """Generate a PDF attendance report.
    
    Args:
        records: List of attendance summary records
        start_date: Report start date
        end_date: Report end date
        company_name: Company name for header
    
    Returns:
        PDF file as bytes
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER, spaceAfter=20
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, spaceAfter=10
    )
    
    elements = []
    
    # Header
    elements.append(Paragraph(f"{company_name}", title_style))
    elements.append(Paragraph(f"Attendance Report", subtitle_style))
    elements.append(Paragraph(f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Table
    table_data = [
        ['Employee', 'Days Worked', 'Total Hours', 'Avg Hours/Day', 'Overtime Days', 'Overtime Hours']
    ]
    
    for record in records:
        table_data.append([
            record.get('user_full_name', 'Unknown')[:25],
            str(record.get('days_worked', 0)),
            f"{record.get('total_hours', 0):.1f}",
            f"{record.get('total_hours', 0) / max(record.get('days_worked', 1), 1):.1f}",
            str(record.get('overtime_days', 0)),
            f"{record.get('overtime_hours', 0):.1f}"
        ])
    
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
