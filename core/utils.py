"""
Utility functions for Raahat Plaza.
Includes: email sending, PDF invoice generation, Razorpay helpers, notifications.
"""
import os
import razorpay
from decimal import Decimal
from io import BytesIO
from datetime import datetime

from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


# ─── Razorpay Client ────────────────────────────────────────────

def get_razorpay_client():
    """Get Razorpay client instance."""
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_razorpay_order(amount, currency='INR', receipt='', notes=None):
    """
    Create a Razorpay order.
    amount: in rupees (will be converted to paise)
    """
    client = get_razorpay_client()
    amount_paise = int(Decimal(str(amount)) * 100)
    data = {
        'amount': amount_paise,
        'currency': currency,
        'receipt': receipt,
        'notes': notes or {},
    }
    order = client.order.create(data=data)
    return order


def verify_razorpay_payment(order_id, payment_id, signature):
    """Verify Razorpay payment signature."""
    client = get_razorpay_client()
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature,
        })
        return True
    except razorpay.errors.SignatureVerificationError:
        return False


# ─── PDF Invoice Generation ─────────────────────────────────────

def generate_invoice_pdf(invoice):
    """Generate PDF invoice using ReportLab."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=30, leftMargin=30,
        topMargin=30, bottomMargin=30
    )

    styles = getSampleStyleSheet()
    story = []

    # Title style
    title_style = ParagraphStyle(
        'InvoiceTitle', parent=styles['Heading1'],
        fontSize=24, textColor=colors.HexColor('#1a1a2e'),
        alignment=TA_CENTER, spaceAfter=20
    )

    # Header
    story.append(Paragraph("RAAHAT PLAZA", title_style))
    story.append(Paragraph("Mall Rental Invoice", ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=12, textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER, spaceAfter=30
    )))

    # Divider line
    story.append(Spacer(1, 10))

    # Invoice details table
    invoice_info = [
        ['Invoice Number:', invoice.invoice_number, 'Date:', invoice.generated_at.strftime('%d/%m/%Y')],
        ['Payment Ref:', invoice.payment_reference or 'N/A', 'Payment Type:', invoice.payment_type],
    ]
    info_table = Table(invoice_info, colWidths=[100, 180, 100, 150])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # Tenant & Shop details
    details = [
        ['Tenant Name:', invoice.tenant_name],
        ['Shop Number:', invoice.shop_number],
        ['Floor:', invoice.floor_name],
    ]
    detail_table = Table(details, colWidths=[120, 400])
    detail_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 25))

    # Payment breakdown table
    payment_data = [['Description', 'Amount (₹)']]

    if invoice.rent_amount > 0:
        payment_data.append(['Monthly Rent', f'₹ {invoice.rent_amount:,.2f}'])
    if invoice.deposit_amount > 0:
        payment_data.append(['Security Deposit', f'₹ {invoice.deposit_amount:,.2f}'])
    if invoice.maintenance_amount > 0:
        payment_data.append(['Maintenance Charge', f'₹ {invoice.maintenance_amount:,.2f}'])

    payment_data.append(['', ''])
    payment_data.append(['Total Amount', f'₹ {invoice.total_amount:,.2f}'])

    payment_table = Table(payment_data, colWidths=[380, 150])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -3), 0.5, colors.HexColor('#dddddd')),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#1a1a2e')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1a1a2e')),
    ]))
    story.append(payment_table)
    story.append(Spacer(1, 40))

    # Footer
    story.append(Paragraph(
        "This is a computer-generated invoice and does not require a signature.",
        ParagraphStyle('Footer', parent=styles['Normal'],
                      fontSize=8, textColor=colors.HexColor('#999999'),
                      alignment=TA_CENTER)
    ))
    story.append(Paragraph(
        f"Raahat Plaza | Generated on {timezone.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle('Footer2', parent=styles['Normal'],
                      fontSize=8, textColor=colors.HexColor('#999999'),
                      alignment=TA_CENTER)
    ))

    doc.build(story)

    # Save to file
    pdf_content = buffer.getvalue()
    buffer.close()

    # Save file
    invoice_dir = os.path.join(settings.MEDIA_ROOT, 'invoices', timezone.now().strftime('%Y'), timezone.now().strftime('%m'))
    os.makedirs(invoice_dir, exist_ok=True)
    filename = f"invoice_{invoice.invoice_number}.pdf"
    filepath = os.path.join(invoice_dir, filename)

    with open(filepath, 'wb') as f:
        f.write(pdf_content)

    # Update invoice record with relative path
    relative_path = os.path.join('invoices', timezone.now().strftime('%Y'), timezone.now().strftime('%m'), filename)
    invoice.pdf_path = relative_path
    invoice.save()

    return pdf_content, relative_path


# ─── Email Notifications ────────────────────────────────────────

def send_notification_email(subject, message, recipient_list, html_message=None):
    """Send email notification."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=True,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False


def send_application_submitted_email(application):
    """Send email when tenant submits application."""
    subject = f"Rental Application Submitted - Shop {application.shop.shop_number}"
    message = f"""
Dear {application.tenant.get_full_name()},

Your rental application for Shop {application.shop.shop_number} ({application.shop.floor.floor_name}) 
has been submitted successfully.

Application ID: #{application.id}
Shop: {application.shop.shop_number}
Floor: {application.shop.floor.floor_name}
Monthly Rent: ₹{application.shop.monthly_rent}

Please upload the required documents to proceed with your application.

Thank you,
Raahat Plaza Management
    """
    send_notification_email(subject, message, [application.tenant.email])

    # Notify owner/admin
    if application.owner:
        owner_msg = f"""
Dear {application.owner.get_full_name()},

A new rental application has been received for your Shop {application.shop.shop_number}.

Tenant: {application.tenant.get_full_name()}
Business Type: {application.business_type}

Please review the application in your dashboard.

Thank you,
Raahat Plaza Management
        """
        send_notification_email(
            f"New Rental Application - Shop {application.shop.shop_number}",
            owner_msg, [application.owner.email]
        )


def send_application_status_email(application, status):
    """Send email when application status changes."""
    status_messages = {
        'approved': 'has been approved! Please proceed with the payment.',
        'rejected': 'has been rejected.',
        'awaiting_payment': 'has been approved. Please proceed with the payment.',
        'documents_pending': 'requires additional documents. Please check your dashboard.',
    }
    msg = status_messages.get(status, f'status has been updated to: {status}')

    subject = f"Application Update - Shop {application.shop.shop_number}"
    message = f"""
Dear {application.tenant.get_full_name()},

Your rental application (#{application.id}) for Shop {application.shop.shop_number} {msg}

Please log in to your dashboard for more details.

Thank you,
Raahat Plaza Management
    """
    send_notification_email(subject, message, [application.tenant.email])


def send_payment_confirmation_email(payment, invoice=None):
    """Send email after successful payment."""
    subject = f"Payment Confirmation - ₹{payment.amount}"
    message = f"""
Dear {payment.tenant.get_full_name()},

Your payment has been received successfully!

Payment Details:
Amount: ₹{payment.amount}
Payment Type: {payment.get_payment_type_display()}
Shop: {payment.shop.shop_number}
Transaction ID: {payment.razorpay_payment_id}
Date: {timezone.now().strftime('%d/%m/%Y %H:%M')}

{"Invoice Number: " + invoice.invoice_number if invoice else ""}

Thank you for your payment.

Raahat Plaza Management
    """
    send_notification_email(subject, message, [payment.tenant.email])


# ─── In-App Notifications ───────────────────────────────────────

def create_notification(user, title, message, notification_type='info', link=''):
    """Create an in-app notification."""
    from .models import Notification
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link
    )
