"""
Admin panel views: Mall, Floor, Shop, Owner, Tenant management,
Document review, Application review, Reports.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q

from ..models import (
    User, Mall, Floor, Shop, RentApplication, Document,
    Rental, Payment, Invoice, Agreement, Notification
)
from ..forms import (
    MallForm, FloorForm, ShopForm, OwnerCreateForm, OwnerEditForm,
    TenantEditForm, DocumentReviewForm, ApplicationReviewForm
)
from ..decorators import admin_required
from ..utils import (
    create_notification, send_application_status_email,
    send_notification_email
)


# ─── Mall Management ────────────────────────────────────────────

@admin_required
def manage_mall(request):
    """Create or edit mall."""
    mall = Mall.objects.first()
    if request.method == 'POST':
        form = MallForm(request.POST, request.FILES, instance=mall)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mall details updated successfully.')
            return redirect('manage_mall')
    else:
        form = MallForm(instance=mall)
    floors = Floor.objects.all() if mall else []
    context = {'form': form, 'mall': mall, 'floors': floors}
    return render(request, 'admin_panel/manage_mall.html', context)


# ─── Floor Management ───────────────────────────────────────────

@admin_required
def manage_floors(request):
    """List all floors."""
    floors = Floor.objects.select_related('mall').all()
    return render(request, 'admin_panel/manage_floors.html', {'floors': floors})


@admin_required
def add_floor(request):
    """Add a new floor."""
    mall = Mall.objects.first()
    if not mall:
        messages.error(request, 'Please create the mall first.')
        return redirect('manage_mall')

    if request.method == 'POST':
        form = FloorForm(request.POST)
        if form.is_valid():
            floor = form.save(commit=False)
            floor.mall = mall
            floor.save()
            messages.success(request, f'Floor "{floor.floor_name}" added successfully.')
            return redirect('manage_floors')
    else:
        form = FloorForm()
    return render(request, 'admin_panel/floor_form.html', {'form': form, 'title': 'Add Floor'})


@admin_required
def edit_floor(request, pk):
    """Edit a floor."""
    floor = get_object_or_404(Floor, pk=pk)
    if request.method == 'POST':
        form = FloorForm(request.POST, instance=floor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Floor "{floor.floor_name}" updated successfully.')
            return redirect('manage_floors')
    else:
        form = FloorForm(instance=floor)
    return render(request, 'admin_panel/floor_form.html', {'form': form, 'title': 'Edit Floor', 'floor': floor})


@admin_required
def delete_floor(request, pk):
    """Delete a floor."""
    floor = get_object_or_404(Floor, pk=pk)
    if request.method == 'POST':
        floor.delete()
        messages.success(request, 'Floor deleted successfully.')
    return redirect('manage_floors')


# ─── Shop Management ────────────────────────────────────────────

@admin_required
def manage_shops(request):
    """List all shops with filters."""
    shops = Shop.objects.select_related('floor', 'owner').all()

    # Filters
    floor_id = request.GET.get('floor')
    status = request.GET.get('status')
    ownership = request.GET.get('ownership')

    if floor_id:
        shops = shops.filter(floor_id=floor_id)
    if status:
        shops = shops.filter(rental_status=status)
    if ownership:
        shops = shops.filter(ownership_type=ownership)

    floors = Floor.objects.all()
    context = {
        'shops': shops,
        'floors': floors,
        'selected_floor': floor_id,
        'selected_status': status,
        'selected_ownership': ownership,
    }
    return render(request, 'admin_panel/manage_shops.html', context)


@admin_required
def add_shop(request):
    """Add a new shop."""
    if request.method == 'POST':
        form = ShopForm(request.POST, request.FILES)
        if form.is_valid():
            shop = form.save()
            messages.success(request, f'Shop "{shop.shop_number}" created successfully.')
            return redirect('manage_shops')
    else:
        form = ShopForm()
    return render(request, 'admin_panel/shop_form.html', {'form': form, 'title': 'Add Shop'})


@admin_required
def edit_shop(request, pk):
    """Edit a shop."""
    shop = get_object_or_404(Shop, pk=pk)
    if request.method == 'POST':
        form = ShopForm(request.POST, request.FILES, instance=shop)
        if form.is_valid():
            form.save()
            messages.success(request, f'Shop "{shop.shop_number}" updated successfully.')
            return redirect('manage_shops')
    else:
        form = ShopForm(instance=shop)
    return render(request, 'admin_panel/shop_form.html', {'form': form, 'title': 'Edit Shop', 'shop': shop})


@admin_required
def delete_shop(request, pk):
    """Delete a shop."""
    shop = get_object_or_404(Shop, pk=pk)
    if request.method == 'POST':
        shop.delete()
        messages.success(request, 'Shop deleted successfully.')
    return redirect('manage_shops')


@admin_required
def shop_detail_admin(request, pk):
    """Admin view: Detailed shop information."""
    shop = get_object_or_404(Shop.objects.select_related('floor', 'owner'), pk=pk)
    applications = RentApplication.objects.filter(shop=shop).select_related('tenant')
    active_rental = Rental.objects.filter(shop=shop, status='active').first()
    payments = Payment.objects.filter(shop=shop, status='successful')

    context = {
        'shop': shop,
        'applications': applications,
        'active_rental': active_rental,
        'payments': payments,
    }
    return render(request, 'admin_panel/shop_detail.html', context)


# ─── Owner Management ───────────────────────────────────────────

@admin_required
def manage_owners(request):
    """List all owners."""
    owners = User.objects.filter(role='owner').annotate(
        shop_count=Count('owned_shops')
    )
    return render(request, 'admin_panel/manage_owners.html', {'owners': owners})


@admin_required
def add_owner(request):
    """Create a new owner account."""
    if request.method == 'POST':
        form = OwnerCreateForm(request.POST)
        if form.is_valid():
            owner = form.save()
            messages.success(request, f'Owner "{owner.get_full_name()}" created successfully.')
            return redirect('manage_owners')
    else:
        form = OwnerCreateForm()
    return render(request, 'admin_panel/owner_form.html', {'form': form, 'title': 'Add Owner'})


@admin_required
def edit_owner(request, pk):
    """Edit owner account."""
    owner = get_object_or_404(User, pk=pk, role='owner')
    if request.method == 'POST':
        form = OwnerEditForm(request.POST, instance=owner)
        if form.is_valid():
            form.save()
            messages.success(request, f'Owner "{owner.get_full_name()}" updated.')
            return redirect('manage_owners')
    else:
        form = OwnerEditForm(instance=owner)
    shops = Shop.objects.filter(owner=owner)
    context = {'form': form, 'title': 'Edit Owner', 'owner_user': owner, 'shops': shops}
    return render(request, 'admin_panel/owner_form.html', context)


@admin_required
def toggle_owner_status(request, pk):
    """Activate/deactivate owner."""
    owner = get_object_or_404(User, pk=pk, role='owner')
    owner.is_active_account = not owner.is_active_account
    owner.is_active = owner.is_active_account
    owner.save()
    status = 'activated' if owner.is_active_account else 'deactivated'
    messages.success(request, f'Owner "{owner.get_full_name()}" {status}.')
    return redirect('manage_owners')


# ─── Tenant Management ──────────────────────────────────────────

@admin_required
def manage_tenants(request):
    """List all tenants."""
    tenants = User.objects.filter(role='tenant').annotate(
        application_count=Count('rent_applications'),
        rental_count=Count('tenant_rentals', filter=Q(tenant_rentals__status='active'))
    )
    return render(request, 'admin_panel/manage_tenants.html', {'tenants': tenants})


@admin_required
def edit_tenant(request, pk):
    """Edit tenant account."""
    tenant = get_object_or_404(User, pk=pk, role='tenant')
    if request.method == 'POST':
        form = TenantEditForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tenant "{tenant.get_full_name()}" updated.')
            return redirect('manage_tenants')
    else:
        form = TenantEditForm(instance=tenant)
    applications = RentApplication.objects.filter(tenant=tenant)
    context = {'form': form, 'title': 'Edit Tenant', 'tenant_user': tenant, 'applications': applications}
    return render(request, 'admin_panel/tenant_form.html', context)


@admin_required
def toggle_tenant_status(request, pk):
    """Activate/deactivate tenant."""
    tenant = get_object_or_404(User, pk=pk, role='tenant')
    tenant.is_active_account = not tenant.is_active_account
    tenant.is_active = tenant.is_active_account
    tenant.save()
    status = 'activated' if tenant.is_active_account else 'deactivated'
    messages.success(request, f'Tenant "{tenant.get_full_name()}" {status}.')
    return redirect('manage_tenants')


# ─── Application Review (Admin) ─────────────────────────────────

@admin_required
def admin_applications(request):
    """List all rent applications."""
    applications = RentApplication.objects.select_related(
        'shop', 'shop__floor', 'tenant', 'owner'
    ).all()

    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)

    context = {
        'applications': applications,
        'selected_status': status_filter,
    }
    return render(request, 'admin_panel/applications.html', context)


@admin_required
def admin_application_detail(request, pk):
    """Admin: View application detail and review."""
    application = get_object_or_404(
        RentApplication.objects.select_related('shop', 'shop__floor', 'tenant', 'owner'),
        pk=pk
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
                application.admin_remarks = remarks
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
                application.admin_remarks = remarks
                application.save()
                application.shop.rental_status = 'vacant'
                application.shop.save()
                messages.warning(request, 'Application rejected.')
                send_application_status_email(application, 'rejected')
                create_notification(
                    application.tenant,
                    'Application Rejected',
                    f'Your application for Shop {application.shop.shop_number} has been rejected. Reason: {remarks}',
                    'error',
                    f'/tenant/application/{application.id}/'
                )
            elif action == 'request_docs':
                application.status = 'documents_pending'
                application.admin_remarks = remarks
                application.save()
                messages.info(request, 'Document re-upload requested.')
                send_application_status_email(application, 'documents_pending')
                create_notification(
                    application.tenant,
                    'Documents Required',
                    f'Additional documents needed for Shop {application.shop.shop_number}. {remarks}',
                    'warning',
                    f'/tenant/application/{application.id}/'
                )
            return redirect('admin_application_detail', pk=pk)
    else:
        form = ApplicationReviewForm()

    context = {
        'application': application,
        'documents': documents,
        'form': form,
    }
    return render(request, 'admin_panel/application_detail.html', context)


# ─── Document Review (Admin) ────────────────────────────────────

@admin_required
def admin_documents(request):
    """List all documents for review."""
    documents = Document.objects.select_related('user', 'application').all()

    status_filter = request.GET.get('status')
    if status_filter:
        documents = documents.filter(status=status_filter)

    context = {
        'documents': documents,
        'selected_status': status_filter,
    }
    return render(request, 'admin_panel/documents.html', context)


@admin_required
def admin_review_document(request, pk):
    """Admin: Review a specific document."""
    document = get_object_or_404(Document.objects.select_related('user', 'application'), pk=pk)

    if request.method == 'POST':
        form = DocumentReviewForm(request.POST)
        if form.is_valid():
            document.status = form.cleaned_data['status']
            document.remarks = form.cleaned_data['remarks']
            document.verified_at = timezone.now()
            document.verified_by = request.user
            document.save()

            status_msg = {
                'approved': 'Document approved.',
                'rejected': 'Document rejected.',
                'reupload_required': 'Re-upload requested.',
            }
            messages.success(request, status_msg.get(document.status, 'Document updated.'))

            # Notify
            create_notification(
                document.user,
                f'Document {document.get_status_display()}',
                f'Your {document.get_document_type_display()} has been {document.get_status_display().lower()}. {document.remarks}',
                'success' if document.status == 'approved' else 'warning',
            )
            return redirect('admin_documents')
    else:
        form = DocumentReviewForm()

    context = {'document': document, 'form': form}
    return render(request, 'admin_panel/review_document.html', context)


# ─── Payment Monitoring (Admin) ─────────────────────────────────

@admin_required
def admin_payments(request):
    """View all payments."""
    payments = Payment.objects.select_related(
        'tenant', 'owner', 'shop', 'rental'
    ).all()

    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')

    if status_filter:
        payments = payments.filter(status=status_filter)
    if type_filter:
        payments = payments.filter(payment_type=type_filter)

    total = payments.filter(status='successful').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'payments': payments,
        'total': total,
        'selected_status': status_filter,
        'selected_type': type_filter,
    }
    return render(request, 'admin_panel/payments.html', context)


# ─── Invoice Management (Admin) ─────────────────────────────────

@admin_required
def admin_invoices(request):
    """View all invoices."""
    invoices = Invoice.objects.select_related('payment', 'payment__tenant', 'payment__shop').all()
    return render(request, 'admin_panel/invoices.html', {'invoices': invoices})


# ─── Agreement Management (Admin) ───────────────────────────────

@admin_required
def admin_agreements(request):
    """View all agreements."""
    agreements = Agreement.objects.select_related(
        'rental', 'rental__shop', 'rental__tenant', 'uploaded_by_user'
    ).all()
    return render(request, 'admin_panel/agreements.html', {'agreements': agreements})


@admin_required
def admin_upload_agreement(request, rental_id):
    """Admin uploads agreement for a rental."""
    from ..forms import AgreementUploadForm
    rental = get_object_or_404(Rental, pk=rental_id)

    if request.method == 'POST':
        form = AgreementUploadForm(request.POST, request.FILES)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.rental = rental
            agreement.uploaded_by_role = 'admin'
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
            return redirect('admin_agreements')
    else:
        form = AgreementUploadForm()

    context = {'form': form, 'rental': rental}
    return render(request, 'admin_panel/upload_agreement.html', context)


# ─── Reports (Admin) ────────────────────────────────────────────

@admin_required
def admin_reports(request):
    """Generate admin reports with charts and month-wise filters."""
    import calendar
    from collections import defaultdict
    from datetime import date

    # Month/Year filter
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')

    current_year = timezone.now().year
    current_month = timezone.now().month
    years = list(range(current_year - 2, current_year + 1))
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]

    # Base querysets
    all_payments = Payment.objects.filter(status='successful')
    all_rentals = Rental.objects.all()
    all_applications = RentApplication.objects.all()

    # Apply month/year filters if selected
    filtered_payments = all_payments
    if selected_year:
        filtered_payments = filtered_payments.filter(paid_at__year=int(selected_year))
    if selected_month:
        filtered_payments = filtered_payments.filter(paid_at__month=int(selected_month))

    # ─── Floor-wise Occupancy (Pie Chart) ───
    floors = Floor.objects.all()
    floor_labels = []
    floor_occupied = []
    floor_vacant = []
    floor_data = []
    total_shops = 0
    total_vacant = 0
    total_occupied = 0

    for floor in floors:
        shops = Shop.objects.filter(floor=floor)
        total = shops.count()
        vacant = shops.filter(rental_status='vacant').count()
        occupied = shops.filter(rental_status='occupied').count()
        applied = shops.filter(rental_status='applied').count()

        floor_labels.append(floor.floor_name)
        floor_occupied.append(occupied)
        floor_vacant.append(vacant)
        total_shops += total
        total_vacant += vacant
        total_occupied += occupied

        floor_data.append({
            'floor': floor,
            'total': total,
            'vacant': vacant,
            'occupied': occupied,
            'applied': applied,
        })

    # ─── Monthly Revenue (Bar Chart — last 12 months) ───
    revenue_labels = []
    revenue_data = []
    rent_revenue_data = []
    deposit_revenue_data = []

    today = timezone.now().date()
    for i in range(11, -1, -1):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1

        month_payments = all_payments.filter(paid_at__year=year, paid_at__month=month)
        total_rev = month_payments.aggregate(t=Sum('amount'))['t'] or 0
        rent_rev = month_payments.filter(payment_type='rent').aggregate(t=Sum('amount'))['t'] or 0
        dep_rev = month_payments.filter(payment_type__in=['deposit', 'initial']).aggregate(t=Sum('amount'))['t'] or 0

        revenue_labels.append(f"{calendar.month_abbr[month]} {year}")
        revenue_data.append(float(total_rev))
        rent_revenue_data.append(float(rent_rev))
        deposit_revenue_data.append(float(dep_rev))

    # ─── Payment Status Distribution (Pie Chart) ───
    all_payment_records = Payment.objects.all()
    payment_status_data = {
        'successful': all_payment_records.filter(status='successful').count(),
        'created': all_payment_records.filter(status='created').count(),
        'failed': all_payment_records.filter(status='failed').count(),
    }

    # ─── Application Status (Pie Chart) ───
    app_status_data = {
        'Submitted': all_applications.filter(status='submitted').count(),
        'Under Review': all_applications.filter(status='under_review').count(),
        'Approved': all_applications.filter(status__in=['approved', 'awaiting_payment', 'active']).count(),
        'Rejected': all_applications.filter(status='rejected').count(),
        'Docs Pending': all_applications.filter(status='documents_pending').count(),
    }

    # ─── Financial Summary ───
    total_revenue = filtered_payments.aggregate(t=Sum('amount'))['t'] or 0
    rent_total = filtered_payments.filter(payment_type='rent').aggregate(t=Sum('amount'))['t'] or 0
    deposit_total = filtered_payments.filter(payment_type__in=['deposit', 'initial']).aggregate(t=Sum('amount'))['t'] or 0

    # Active vs expired rentals
    active_rentals = all_rentals.filter(status='active').count()
    expired_rentals = all_rentals.filter(status='expired').count()
    terminated_rentals = all_rentals.filter(status='terminated').count()

    # ─── Month-wise Payment Table ───
    monthly_payments = []
    if selected_year:
        y = int(selected_year)
        month_range = [int(selected_month)] if selected_month else range(1, 13)
        for m in month_range:
            mp = all_payments.filter(paid_at__year=y, paid_at__month=m)
            monthly_payments.append({
                'month': calendar.month_name[m],
                'year': y,
                'count': mp.count(),
                'total': mp.aggregate(t=Sum('amount'))['t'] or 0,
                'rent': mp.filter(payment_type='rent').aggregate(t=Sum('amount'))['t'] or 0,
                'initial': mp.filter(payment_type='initial').aggregate(t=Sum('amount'))['t'] or 0,
            })

    import json
    context = {
        'floor_data': floor_data,
        'total_revenue': total_revenue,
        'rent_total': rent_total,
        'deposit_total': deposit_total,
        'overall_total': all_payments.aggregate(t=Sum('amount'))['t'] or 0,
        'active_rentals': active_rentals,
        'expired_rentals': expired_rentals,
        'terminated_rentals': terminated_rentals,
        'total_shops': total_shops,
        'total_vacant': total_vacant,
        'total_occupied': total_occupied,
        # Chart data (JSON)
        'floor_labels_json': json.dumps(floor_labels),
        'floor_occupied_json': json.dumps(floor_occupied),
        'floor_vacant_json': json.dumps(floor_vacant),
        'revenue_labels_json': json.dumps(revenue_labels),
        'revenue_data_json': json.dumps(revenue_data),
        'rent_revenue_json': json.dumps(rent_revenue_data),
        'deposit_revenue_json': json.dumps(deposit_revenue_data),
        'payment_status_json': json.dumps(list(payment_status_data.values())),
        'payment_status_labels_json': json.dumps(list(payment_status_data.keys())),
        'app_status_json': json.dumps(list(app_status_data.values())),
        'app_status_labels_json': json.dumps(list(app_status_data.keys())),
        # Filters
        'years': years,
        'months': months,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'monthly_payments': monthly_payments,
    }
    return render(request, 'admin_panel/reports.html', context)


# ─── Rental Management (Admin) ──────────────────────────────────

@admin_required
def admin_rentals(request):
    """View all rentals."""
    rentals = Rental.objects.select_related(
        'shop', 'shop__floor', 'tenant', 'owner'
    ).all()

    status_filter = request.GET.get('status')
    if status_filter:
        rentals = rentals.filter(status=status_filter)

    context = {
        'rentals': rentals,
        'selected_status': status_filter,
    }
    return render(request, 'admin_panel/rentals.html', context)
