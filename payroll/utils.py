from io import BytesIO
from django.http import HttpResponse
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_salary_slip_pdf(salary_record):
    """
    Generate a PDF salary slip for a given salary record.
    
    Args:
        salary_record: Salary model instance
        
    Returns:
        HttpResponse with PDF content
    """
    if not REPORTLAB_AVAILABLE:
        return HttpResponse(
            "<h1>Error: PDF Generation Not Available</h1>"
            "<p>ReportLab is not installed. Please install it with:</p>"
            "<code>pip install reportlab</code>",
            content_type='text/html',
            status=503
        )
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a3a52'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#555555'),
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=3
    )
    
    # Header
    elements.append(Paragraph("SALARY SLIP", title_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Company and Employee Info Header
    header_data = [
        [
            f"<b>Company:</b> Avvento Media",
            f"<b>Month:</b> {salary_record.month_name} {salary_record.year}"
        ],
        [
            f"<b>Employee ID:</b> {salary_record.employee.id}",
            f"<b>Slip Date:</b> {datetime.now().strftime('%d-%m-%Y')}"
        ]
    ]
    
    header_table = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Employee Details
    emp = salary_record.employee
    emp_details = [
        [f"<b>Employee Name:</b> {emp.full_name}"],
        [f"<b>Job Title:</b> {emp.job_title}"],
        [f"<b>Department:</b> {emp.department.name if emp.department else 'N/A'}"],
        [f"<b>Bank Account:</b> {emp.account_number} ({emp.bank})"],
    ]
    
    emp_table = Table(emp_details, colWidths=[7*inch])
    emp_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Earnings and Deductions Table
    salary_details = [
        ['EARNINGS', '', 'DEDUCTIONS', ''],
        ['Description', 'Amount (KES)', 'Description', 'Amount (KES)'],
    ]
    
    # Earnings side
    salary_details.append([
        'Basic Salary',
        f"{salary_record.basic_salary:,.2f}",
        'Deductions',
        f"{salary_record.deductions:,.2f}"
    ])
    
    salary_details.append([
        'Allowances',
        f"{salary_record.allowances:,.2f}",
        'Tax',
        f"{salary_record.tax:,.2f}"
    ])
    
    salary_details.append([
        'Total Earnings',
        f"{salary_record.total_earnings:,.2f}",
        'Total Deductions',
        f"{salary_record.total_deductions:,.2f}"
    ])
    
    salary_details.append(['', '', '', ''])
    salary_details.append([
        'NET SALARY',
        f"{salary_record.net_salary:,.2f}",
        'Payment Method',
        salary_record.get_payment_method_display()
    ])
    
    salary_table = Table(salary_details, colWidths=[1.75*inch, 1.75*inch, 1.75*inch, 1.75*inch])
    salary_table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1a3a52')),
        ('BACKGROUND', (2, 0), (3, 0), colors.HexColor('#1a3a52')),
        ('TEXTCOLOR', (0, 0), (3, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (3, 0), 10),
        
        # Column headers
        ('BACKGROUND', (0, 1), (3, 1), colors.HexColor('#e8e8e8')),
        ('FONTNAME', (0, 1), (3, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (3, 1), 9),
        
        # Data rows
        ('FONTSIZE', (0, 2), (3, -1), 9),
        ('ROWBACKGROUNDS', (0, 2), (3, -3), [colors.white, colors.HexColor('#f5f5f5')]),
        
        # Total row styling
        ('BACKGROUND', (0, -2), (3, -2), colors.HexColor('#1a3a52')),
        ('TEXTCOLOR', (0, -2), (3, -2), colors.whitesmoke),
        ('FONTNAME', (0, -2), (3, -2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -2), (3, -2), 11),
        
        # Borders
        ('GRID', (0, 0), (3, -1), 1, colors.black),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (3, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (3, -1), 5),
        ('RIGHTPADDING', (0, 0), (3, -1), 5),
        ('TOPPADDING', (0, 0), (3, -1), 5),
        ('BOTTOMPADDING', (0, 0), (3, -1), 5),
    ]))
    
    elements.append(salary_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Payment Status
    status = "PAID" if salary_record.is_paid else "PENDING"
    status_color = colors.HexColor('#28a745') if salary_record.is_paid else colors.HexColor('#ffc107')
    
    paid_date = salary_record.paid_on.strftime('%d-%m-%Y') if salary_record.paid_on else 'Not yet paid'
    
    status_text = f"<b>Payment Status:</b> <font color='{status_color}>{status}</font> | <b>Payment Date:</b> {paid_date}"
    elements.append(Paragraph(status_text, normal_style))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Footer
    footer_text = "This is a system-generated salary slip. For queries, contact HR department."
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Return as HTTP response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Salary_Slip_{salary_record.employee.id}_{salary_record.month}_{salary_record.year}.pdf"'
    
    return response
