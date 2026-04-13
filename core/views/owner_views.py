"""
Owner panel views: Shop management, rental listing, tenant review,
document review, payment tracking.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum

from ..models import (
    Shop, RentApplication, Document, Rental, Payment, Invoice, Agreement
)
from ..forms import (
    ShopRentalUpdateForm, DocumentReviewForm, ApplicationReviewForm,
    AgreementUploadForm
)
from ..decorators import owner_required
from ..utils import (
    create_notification, send_application_status_email
)


# ─── Shop Management (Owner) ────────────────────────────────────

@owner_required
def owner_shops(request):
    """List owner's shops."""
    shops = Shop.objects.filter(owner=request.user).select_related('floor')
    return render(request, 'owner_panel/shops.html', {'shops': shops})


@owner_required
def owner_shop_detail(request, pk):
    """Owner: View shop details."""
    shop = get_object_or_404(Shop, pk=pk, owner=request.user)
    applications = RentApplication.objects.filter(shop=shop).select_related('tenant')
    active_rental = Rental.objects.filter(shop=shop, status='active').first()
    payments = Payment.objects.filter(shop=shop, status='successful')

    context = {
        'shop': shop,
        'applications': applications,
        'active_rental': active_rental,
        'payments': payments,
    }
    return render(request, 'owner_panel/shop_detail.html', context)


@owner_required
def owner_update_rental(request, pk):
    """Owner: Update shop rental details."""
    shop = get_object_or_404(Shop, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = ShopRentalUpdateForm(request.POST, instance=shop)
        if form.is_valid():
            form.save()
            messages.success(request, f'Rental details for Shop {shop.shop_number} updated.')
            return redirect('owner_shop_detail', pk=pk)
    else:
        form = ShopRentalUpdateForm(instance=shop)
    return render(request, 'owner_panel/update_rental.html', {'form': form, 'shop': shop})


# ─── Application Review (Owner) ─────────────────────────────────

@owner_required
def owner_applications(request):
    """List applications for owner's shops."""
    applications = RentApplication.objects.filter(
        owner=request.user
    ).select_related('shop', 'shop__floor', 'tenant')

    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)

    context = {
        'applications': applications,
        'selected_status': status_filter,
    }
    return render(request, 'owner_panel/applications.html', context)


@owner_required
def owner_application_detail(request, pk):
    """Owner: View and review application."""
    application = get_object_or_404(
        RentApplication.objects.select_related('shop', 'shop__floor', 'tenant'),
        pk=pk, owner=request.user
    )
    documents = Document.objects.filter(application=application)

    if request.method == 'POST':
        form = ApplicationReviewForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            remarks = form.cleaned_data['remarks']

            if action == 'approve':
                application.status = 'awaiting_payment'
                application.approved_at = timezone.now()
                application.owner_remarks = remarks
                application.save()
                messages.success(request, 'Application approved. Tenant can now make payment.')
                send_application_status_email(application, 'awaiting_payment')
                create_notification(
                    application.tenant,
                    'Application Approved',
                    f'Your application for Shop {application.shop.shop_number} has been approved. Please proceed with payment.',
                    'success',
                    f'/tenant/application/{application.id}/'
                )
            elif action == 'reject':
                application.status = 'rejected'
                application.rejected_at = timezone.now()
                application.owner_remarks = remarks
                application.save()
                application.shop.rental_status = 'vacant'
                application.shop.save()
                messages.warning(request, 'Application rejected.')
                send_application_status_email(application, 'rejected')
                create_notification(
                    application.tenant,
                    'Application Rejected',
                    f'Your application for Shop {application.shop.shop_number} has been rejected. {remarks}',
                    'error',
                    f'/tenant/application/{application.id}/'
                )
            elif action == 'request_docs':
                application.status = 'documents_pending'
                application.owner_remarks = remarks
                application.save()
                messages.info(request, 'Document re-upload requested.')
                send_application_status_email(application, 'documents_pending')
                create_notification(
                    application.tenant,
                    'Documents Required',
                    f'Additional documents needed for Shop {application.shop.shop_number}.',
                    'warning',
                    f'/tenant/application/{application.id}/'
                )
            return redirect('owner_application_detail', pk=pk)
    else:
        form = ApplicationReviewForm()

    context = {
        'application': application,
        'documents': documents,
        'form': form,
    }
    return render(request, 'owner_panel/application_detail.html', context)


# ─── Document Review (Owner) ────────────────────────────────────

@owner_required
def owner_review_document(request, pk):
    """Owner: Review a tenant's document."""
    document = get_object_or_404(Document.objects.select_related('user', 'application'), pk=pk)

    # Ensure document belongs to a shop owned by this owner
    if document.application and document.application.owner != request.user:
        messages.error(request, 'Access denied.')
        return redirect('owner_applications')

    if request.method == 'POST':
        form = DocumentReviewForm(request.POST)
        if form.is_valid():
            document.status = form.cleaned_data['status']
            document.remarks = form.cleaned_data['remarks']
            document.verified_at = timezone.now()
            document.verified_by = request.user
            document.save()
            messages.success(request, f'Document {document.get_status_display().lower()}.')
            create_notification(
                document.user,
                f'Document {document.get_status_display()}',
                f'Your {document.get_document_type_display()} has been {document.get_status_display().lower()}.',
                'success' if document.status == 'approved' else 'warning',
            )
            if document.application:
                return redirect('owner_application_detail', pk=document.application.id)
            return redirect('owner_applications')
    else:
        form = DocumentReviewForm()

    return render(request, 'owner_panel/review_document.html', {'document': document, 'form': form})


# ─── Payment Tracking (Owner) ───────────────────────────────────

@owner_required
def owner_payments(request):
    """View payments for owner's shops."""
    payments = Payment.objects.filter(
        owner=request.user
    ).select_related('tenant', 'shop', 'rental')

    total = payments.filter(status='successful').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'payments': payments,
        'total': total,
    }
    return render(request, 'owner_panel/payments.html', context)


# ─── Invoice Access (Owner) ─────────────────────────────────────

@owner_required
def owner_invoices(request):
    """View invoices for owner's shops."""
    invoices = Invoice.objects.filter(
        payment__owner=request.user
    ).select_related('payment')
    return render(request, 'owner_panel/invoices.html', {'invoices': invoices})


# ─── Agreement Management (Owner) ───────────────────────────────

@owner_required
def owner_agreements(request):
    """View agreements for owner's shops."""
    agreements = Agreement.objects.filter(
        rental__owner=request.user
    ).select_related('rental', 'rental__shop', 'rental__tenant')
    return render(request, 'owner_panel/agreements.html', {'agreements': agreements})


@owner_required
def owner_upload_agreement(request, rental_id):
    """Owner uploads agreement for a rental."""
    rental = get_object_or_404(Rental, pk=rental_id, owner=request.user)

    if request.method == 'POST':
        form = AgreementUploadForm(request.POST, request.FILES)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.rental = rental
            agreement.uploaded_by_role = 'owner'
            agreement.uploaded_by_user = request.user
            agreement.file_name = request.FILES['file'].name
            agreement.status = 'uploaded'
            agreement.save()
            messages.success(request, 'Agreement uploaded successfully.')
            create_notification(
                rental.tenant,
                'Agreement Uploaded',
                f'A rental agreement has been uploaded for Shop {rental.shop.shop_number}.',
                'info',
                f'/tenant/rental/{rental.id}/'
            )
            return redirect('owner_agreements')
    else:
        form = AgreementUploadForm()

    context = {'form': form, 'rental': rental}
    return render(request, 'owner_panel/upload_agreement.html', context)


# ─── Rental Management (Owner) ──────────────────────────────────

@owner_required
def owner_rentals(request):
    """View all owner's rentals."""
    rentals = Rental.objects.filter(
        owner=request.user
    ).select_related('shop', 'shop__floor', 'tenant')
    return render(request, 'owner_panel/rentals.html', {'rentals': rentals})
