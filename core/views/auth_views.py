"""
Authentication views: login, register, logout, dashboard redirect.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q

from ..models import (
    User, Mall, Floor, Shop, RentApplication, Document,
    Rental, Payment, Invoice, Agreement, Notification
)
from ..forms import LoginForm, TenantRegistrationForm


def home_view(request):
    """Public landing page."""
    mall = Mall.objects.first()
    floors = Floor.objects.all()
    available_shops = Shop.objects.filter(
        rental_status='vacant', listing_type='available'
    ).select_related('floor')
    context = {
        'mall': mall,
        'floors': floors,
        'available_shops': available_shops,
        'total_shops': Shop.objects.count(),
        'available_count': available_shops.count(),
    }
    return render(request, 'public/home.html', context)


def login_view(request):
    """User login."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_active_account:
                messages.error(request, 'Your account has been deactivated. Contact admin.')
                return render(request, 'auth/login.html', {'form': form})
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})


def register_view(request):
    """Tenant registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = TenantRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Raahat Plaza.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = TenantRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})


def logout_view(request):
    """User logout."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def dashboard_view(request):
    """Role-based dashboard redirect."""
    if request.user.role == 'admin':
        return admin_dashboard(request)
    elif request.user.role == 'owner':
        return owner_dashboard(request)
    else:
        return tenant_dashboard(request)


def admin_dashboard(request):
    """Admin dashboard."""
    total_floors = Floor.objects.count()
    total_shops = Shop.objects.count()
    vacant_shops = Shop.objects.filter(rental_status='vacant').count()
    occupied_shops = Shop.objects.filter(rental_status='occupied').count()
    owner_count = User.objects.filter(role='owner').count()
    tenant_count = User.objects.filter(role='tenant').count()
    pending_applications = RentApplication.objects.filter(
        status__in=['submitted', 'under_review']
    ).count()
    pending_docs = Document.objects.filter(
        status__in=['uploaded', 'pending_review']
    ).count()
    total_payments = Payment.objects.filter(status='successful').aggregate(
        total=Sum('amount')
    )['total'] or 0
    recent_payments = Payment.objects.filter(status='successful').order_by('-paid_at')[:5]
    recent_applications = RentApplication.objects.order_by('-created_at')[:5]
    recent_invoices = Invoice.objects.order_by('-generated_at')[:5]

    context = {
        'total_floors': total_floors,
        'total_shops': total_shops,
        'vacant_shops': vacant_shops,
        'occupied_shops': occupied_shops,
        'owner_count': owner_count,
        'tenant_count': tenant_count,
        'pending_applications': pending_applications,
        'pending_docs': pending_docs,
        'total_payments': total_payments,
        'recent_payments': recent_payments,
        'recent_applications': recent_applications,
        'recent_invoices': recent_invoices,
    }
    return render(request, 'admin_panel/dashboard.html', context)


def owner_dashboard(request):
    """Owner dashboard."""
    user = request.user
    owned_shops = Shop.objects.filter(owner=user)
    vacant = owned_shops.filter(rental_status='vacant').count()
    occupied = owned_shops.filter(rental_status='occupied').count()
    pending_requests = RentApplication.objects.filter(
        owner=user, status__in=['submitted', 'under_review']
    ).count()
    approved_tenants = Rental.objects.filter(owner=user, status='active').count()
    total_rent = Payment.objects.filter(
        owner=user, status='successful'
    ).aggregate(total=Sum('amount'))['total'] or 0
    recent_payments = Payment.objects.filter(
        owner=user, status='successful'
    ).order_by('-paid_at')[:5]
    recent_applications = RentApplication.objects.filter(
        owner=user
    ).order_by('-created_at')[:5]

    context = {
        'owned_shops': owned_shops,
        'total_owned': owned_shops.count(),
        'vacant': vacant,
        'occupied': occupied,
        'pending_requests': pending_requests,
        'approved_tenants': approved_tenants,
        'total_rent': total_rent,
        'recent_payments': recent_payments,
        'recent_applications': recent_applications,
    }
    return render(request, 'owner_panel/dashboard.html', context)


def tenant_dashboard(request):
    """Tenant dashboard."""
    user = request.user
    applications = RentApplication.objects.filter(tenant=user).select_related('shop', 'shop__floor')
    documents = Document.objects.filter(user=user)
    active_rentals = Rental.objects.filter(tenant=user, status='active').select_related('shop', 'shop__floor')
    payments = Payment.objects.filter(tenant=user).order_by('-created_at')[:10]
    invoices = Invoice.objects.filter(payment__tenant=user).order_by('-generated_at')[:10]
    pending_payments = RentApplication.objects.filter(
        tenant=user, status='awaiting_payment'
    )

    context = {
        'applications': applications,
        'documents': documents,
        'active_rentals': active_rentals,
        'payments': payments,
        'invoices': invoices,
        'pending_payments': pending_payments,
        'total_applications': applications.count(),
        'approved_count': applications.filter(status='approved').count() + applications.filter(status='awaiting_payment').count(),
        'active_rental_count': active_rentals.count(),
    }
    return render(request, 'tenant_panel/dashboard.html', context)


@login_required
def notifications_view(request):
    """View all notifications."""
    notifications = Notification.objects.filter(user=request.user)
    return render(request, 'includes/notifications.html', {'notifications': notifications})


@login_required
def mark_notification_read(request, pk):
    """Mark notification as read."""
    notification = Notification.objects.filter(id=pk, user=request.user).first()
    if notification:
        notification.is_read = True
        notification.save()
    return redirect(notification.link if notification and notification.link else 'dashboard')


@login_required
def profile_view(request):
    """View/edit user profile."""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        if request.FILES.get('profile_image'):
            user.profile_image = request.FILES['profile_image']
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'auth/profile.html')


def rental_listing_view(request):
    """Public rental listing page for tenants to browse shops."""
    shops = Shop.objects.filter(
        rental_status='vacant', listing_type='available'
    ).select_related('floor', 'owner')

    # Filters
    floor_id = request.GET.get('floor')
    min_rent = request.GET.get('min_rent')
    max_rent = request.GET.get('max_rent')
    size = request.GET.get('size')

    if floor_id:
        shops = shops.filter(floor_id=floor_id)
    if min_rent:
        shops = shops.filter(monthly_rent__gte=min_rent)
    if max_rent:
        shops = shops.filter(monthly_rent__lte=max_rent)

    floors = Floor.objects.all()
    context = {
        'shops': shops,
        'floors': floors,
        'selected_floor': floor_id,
        'min_rent': min_rent,
        'max_rent': max_rent,
    }
    return render(request, 'public/rental_listing.html', context)


def shop_detail_public_view(request, pk):
    """Public shop detail page."""
    shop = Shop.objects.select_related('floor', 'owner').get(pk=pk)
    context = {'shop': shop}
    return render(request, 'public/shop_detail.html', context)
