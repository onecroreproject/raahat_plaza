"""
Tenant panel views: Browse shops, apply for rent, upload documents,
make payments, view invoices, agreements.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import FileResponse, Http404
import os

from ..models import (
    Shop, RentApplication, Document, Rental, Payment, Invoice, Agreement
)
from ..forms import RentApplicationForm, DocumentUploadForm, AgreementUploadForm
from ..decorators import tenant_required
from ..utils import (
    create_notification, send_application_submitted_email
)


# ─── Apply for Rent ─────────────────────────────────────────────

@tenant_required
def apply_for_rent(request, shop_id):
    """Tenant submits rental application."""
    shop = get_object_or_404(Shop, pk=shop_id)

    if not shop.is_available:
        messages.error(request, 'This shop is not available for rent.')
        return redirect('rental_listing')

    # Check if tenant already has a pending application for this shop
    existing = RentApplication.objects.filter(
        tenant=request.user, shop=shop,
        status__in=['draft', 'submitted', 'under_review', 'documents_pending', 'approved', 'awaiting_payment']
    ).first()
    if existing:
        messages.info(request, 'You already have an active application for this shop.')
        return redirect('tenant_application_detail', pk=existing.id)

    if request.method == 'POST':
        form = RentApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.shop = shop
            application.tenant = request.user
            application.owner = shop.owner
            application.status = 'submitted'
            application.submitted_at = timezone.now()
            application.save()

            # Update shop status
            shop.rental_status = 'applied'
            shop.save()

            messages.success(request, 'Rental application submitted successfully! Please upload required documents.')
            send_application_submitted_email(application)
            create_notification(
                request.user,
                'Application Submitted',
                f'Your rental application for Shop {shop.shop_number} has been submitted.',
                'success',
                f'/tenant/application/{application.id}/'
            )

            # Notify shop owner/admin
            if shop.owner:
                create_notification(
                    shop.owner,
                    'New Application Received',
                    f'New rental application for Shop {shop.shop_number} from {request.user.get_full_name()}.',
                    'info',
                    f'/owner/application/{application.id}/'
                )

            return redirect('tenant_upload_documents', application_id=application.id)
    else:
        form = RentApplicationForm()

    context = {'form': form, 'shop': shop}
    return render(request, 'tenant_panel/apply.html', context)


# ─── My Applications ────────────────────────────────────────────

@tenant_required
def tenant_applications(request):
    """List tenant's applications."""
    applications = RentApplication.objects.filter(
        tenant=request.user
    ).select_related('shop', 'shop__floor')
    return render(request, 'tenant_panel/applications.html', {'applications': applications})


@tenant_required
def tenant_application_detail(request, pk):
    """Tenant: View application detail."""
    application = get_object_or_404(
        RentApplication.objects.select_related('shop', 'shop__floor', 'owner'),
        pk=pk, tenant=request.user
    )
    documents = Document.objects.filter(application=application)
    can_pay = application.can_make_payment

    context = {
        'application': application,
        'documents': documents,
        'can_pay': can_pay,
    }
    return render(request, 'tenant_panel/application_detail.html', context)


# ─── Document Upload ────────────────────────────────────────────

@tenant_required
def tenant_upload_documents(request, application_id):
    """Tenant uploads documents for application."""
    application = get_object_or_404(
        RentApplication, pk=application_id, tenant=request.user
    )

    if not application.can_upload_documents:
        messages.info(request, 'Document upload is not available for this application status.')
        return redirect('tenant_application_detail', pk=application.id)

    existing_documents = Document.objects.filter(application=application)

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.user = request.user
            doc.application = application
            doc.request_type = 'rent_application'
            doc.request_id = application.id
            doc.file_name = request.FILES['file'].name
            doc.mime_type = request.FILES['file'].content_type
            doc.file_size = request.FILES['file'].size
            doc.status = 'pending_review'
            doc.save()

            # Update application status if needed
            if application.status == 'draft':
                application.status = 'submitted'
                application.submitted_at = timezone.now()
                application.save()
            elif application.status == 'documents_pending':
                application.status = 'under_review'
                application.save()

            messages.success(request, f'{doc.get_document_type_display()} uploaded successfully.')
            return redirect('tenant_upload_documents', application_id=application.id)
    else:
        form = DocumentUploadForm()

    context = {
        'form': form,
        'application': application,
        'documents': existing_documents,
    }
    return render(request, 'tenant_panel/upload_documents.html', context)


@tenant_required
def tenant_delete_document(request, pk):
    """Tenant deletes an uploaded document (only if not yet approved)."""
    document = get_object_or_404(Document, pk=pk, user=request.user)
    if document.status in ['uploaded', 'pending_review', 'rejected', 'reupload_required']:
        app_id = document.application_id
        document.file.delete()
        document.delete()
        messages.success(request, 'Document deleted.')
        if app_id:
            return redirect('tenant_upload_documents', application_id=app_id)
    else:
        messages.error(request, 'Cannot delete an approved document.')
    return redirect('tenant_applications')


# ─── My Rentals ──────────────────────────────────────────────────

@tenant_required
def tenant_rentals(request):
    """View tenant's active rentals."""
    rentals = Rental.objects.filter(
        tenant=request.user
    ).select_related('shop', 'shop__floor', 'owner')
    return render(request, 'tenant_panel/rentals.html', {'rentals': rentals})


@tenant_required
def tenant_rental_detail(request, pk):
    """Tenant: View rental details."""
    rental = get_object_or_404(
        Rental.objects.select_related('shop', 'shop__floor', 'owner'),
        pk=pk, tenant=request.user
    )
    payments = Payment.objects.filter(rental=rental).order_by('-created_at')
    agreements = Agreement.objects.filter(rental=rental)

    context = {
        'rental': rental,
        'payments': payments,
        'agreements': agreements,
    }
    return render(request, 'tenant_panel/rental_detail.html', context)


# ─── Payment History ────────────────────────────────────────────

@tenant_required
def tenant_payments(request):
    """View tenant's payment history."""
    payments = Payment.objects.filter(
        tenant=request.user
    ).select_related('shop', 'rental').order_by('-created_at')
    return render(request, 'tenant_panel/payments.html', {'payments': payments})


# ─── Invoices ────────────────────────────────────────────────────

@tenant_required
def tenant_invoices(request):
    """View tenant's invoices."""
    invoices = Invoice.objects.filter(
        payment__tenant=request.user
    ).select_related('payment').order_by('-generated_at')
    return render(request, 'tenant_panel/invoices.html', {'invoices': invoices})


@login_required
def download_invoice(request, pk):
    """Download invoice PDF."""
    invoice = get_object_or_404(Invoice, pk=pk)

    # Check access
    if request.user.role == 'tenant' and invoice.payment.tenant != request.user:
        raise Http404
    elif request.user.role == 'owner' and invoice.payment.owner != request.user:
        raise Http404

    if invoice.pdf_path:
        from django.conf import settings
        file_path = os.path.join(settings.MEDIA_ROOT, str(invoice.pdf_path))
        if os.path.exists(file_path):
            return FileResponse(open(file_path, 'rb'), content_type='application/pdf',
                              as_attachment=True, filename=f'Invoice_{invoice.invoice_number}.pdf')

    messages.error(request, 'Invoice file not found.')
    return redirect('dashboard')


# ─── Agreement Access ────────────────────────────────────────────

@tenant_required
def tenant_agreements(request):
    """View tenant's agreements."""
    agreements = Agreement.objects.filter(
        rental__tenant=request.user
    ).select_related('rental', 'rental__shop')
    return render(request, 'tenant_panel/agreements.html', {'agreements': agreements})


@tenant_required
def tenant_upload_agreement(request, rental_id):
    """Tenant uploads signed agreement copy."""
    rental = get_object_or_404(Rental, pk=rental_id, tenant=request.user)

    if request.method == 'POST':
        form = AgreementUploadForm(request.POST, request.FILES)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.rental = rental
            agreement.uploaded_by_role = 'tenant'
            agreement.uploaded_by_user = request.user
            agreement.file_name = request.FILES['file'].name
            agreement.status = 'tenant_signed'
            agreement.save()
            messages.success(request, 'Signed agreement uploaded successfully.')

            if rental.owner:
                create_notification(
                    rental.owner,
                    'Tenant Signed Agreement',
                    f'Tenant has uploaded a signed agreement for Shop {rental.shop.shop_number}.',
                    'info',
                    f'/owner/agreements/'
                )
            return redirect('tenant_agreements')
    else:
        form = AgreementUploadForm()

    context = {'form': form, 'rental': rental}
    return render(request, 'tenant_panel/upload_agreement.html', context)


@login_required
def download_agreement(request, pk):
    """Download agreement file."""
    agreement = get_object_or_404(Agreement, pk=pk)

    # Check access
    if request.user.role == 'tenant' and agreement.rental.tenant != request.user:
        raise Http404
    elif request.user.role == 'owner' and agreement.rental.owner != request.user:
        raise Http404

    if agreement.file:
        return FileResponse(agreement.file.open('rb'), content_type='application/pdf',
                          as_attachment=True, filename=agreement.file_name or 'agreement.pdf')

    messages.error(request, 'Agreement file not found.')
    return redirect('dashboard')
