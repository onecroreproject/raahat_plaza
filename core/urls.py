"""
URL configuration for Raahat Plaza core app.
"""
from django.urls import path
from .views import (
    auth_views, admin_views, owner_views, tenant_views, payment_views
)

urlpatterns = [
    # ─── Public Pages ────────────────────────────────────────
    path('', auth_views.home_view, name='home'),
    path('rentals/', auth_views.rental_listing_view, name='rental_listing'),
    path('shop/<int:pk>/', auth_views.shop_detail_public_view, name='shop_detail_public'),

    # ─── Authentication ──────────────────────────────────────
    path('auth/login/', auth_views.login_view, name='login'),
    path('auth/register/', auth_views.register_view, name='register'),
    path('auth/logout/', auth_views.logout_view, name='logout'),
    path('auth/profile/', auth_views.profile_view, name='profile'),

    # ─── Dashboard ───────────────────────────────────────────
    path('dashboard/', auth_views.dashboard_view, name='dashboard'),

    # ─── Notifications ───────────────────────────────────────
    path('notifications/', auth_views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/read/', auth_views.mark_notification_read, name='mark_notification_read'),

    # ═══════════════════════════════════════════════════════════
    # ─── Admin Panel URLs ────────────────────────────────────
    # ═══════════════════════════════════════════════════════════

    # Mall Management
    path('admin-panel/mall/', admin_views.manage_mall, name='manage_mall'),

    # Floor Management
    path('admin-panel/floors/', admin_views.manage_floors, name='manage_floors'),
    path('admin-panel/floors/add/', admin_views.add_floor, name='add_floor'),
    path('admin-panel/floors/<int:pk>/edit/', admin_views.edit_floor, name='edit_floor'),
    path('admin-panel/floors/<int:pk>/delete/', admin_views.delete_floor, name='delete_floor'),

    # Shop Management
    path('admin-panel/shops/', admin_views.manage_shops, name='manage_shops'),
    path('admin-panel/shops/add/', admin_views.add_shop, name='add_shop'),
    path('admin-panel/shops/<int:pk>/edit/', admin_views.edit_shop, name='edit_shop'),
    path('admin-panel/shops/<int:pk>/delete/', admin_views.delete_shop, name='delete_shop'),
    path('admin-panel/shops/<int:pk>/', admin_views.shop_detail_admin, name='shop_detail_admin'),

    # Owner Management
    path('admin-panel/owners/', admin_views.manage_owners, name='manage_owners'),
    path('admin-panel/owners/add/', admin_views.add_owner, name='add_owner'),
    path('admin-panel/owners/<int:pk>/edit/', admin_views.edit_owner, name='edit_owner'),
    path('admin-panel/owners/<int:pk>/toggle/', admin_views.toggle_owner_status, name='toggle_owner_status'),

    # Tenant Management
    path('admin-panel/tenants/', admin_views.manage_tenants, name='manage_tenants'),
    path('admin-panel/tenants/<int:pk>/edit/', admin_views.edit_tenant, name='edit_tenant'),
    path('admin-panel/tenants/<int:pk>/toggle/', admin_views.toggle_tenant_status, name='toggle_tenant_status'),

    # Application Management (Admin)
    path('admin-panel/applications/', admin_views.admin_applications, name='admin_applications'),
    path('admin-panel/applications/<int:pk>/', admin_views.admin_application_detail, name='admin_application_detail'),

    # Document Management (Admin)
    path('admin-panel/documents/', admin_views.admin_documents, name='admin_documents'),
    path('admin-panel/documents/<int:pk>/review/', admin_views.admin_review_document, name='admin_review_document'),

    # Payment Monitoring (Admin)
    path('admin-panel/payments/', admin_views.admin_payments, name='admin_payments'),

    # Invoice Management (Admin)
    path('admin-panel/invoices/', admin_views.admin_invoices, name='admin_invoices'),

    # Agreement Management (Admin)
    path('admin-panel/agreements/', admin_views.admin_agreements, name='admin_agreements'),
    path('admin-panel/agreements/upload/<int:rental_id>/', admin_views.admin_upload_agreement, name='admin_upload_agreement'),

    # Rental Management (Admin)
    path('admin-panel/rentals/', admin_views.admin_rentals, name='admin_rentals'),

    # Reports (Admin)
    path('admin-panel/reports/', admin_views.admin_reports, name='admin_reports'),

    # ═══════════════════════════════════════════════════════════
    # ─── Owner Panel URLs ────────────────────────────────────
    # ═══════════════════════════════════════════════════════════

    path('owner/shops/', owner_views.owner_shops, name='owner_shops'),
    path('owner/shop/<int:pk>/', owner_views.owner_shop_detail, name='owner_shop_detail'),
    path('owner/shop/<int:pk>/update-rental/', owner_views.owner_update_rental, name='owner_update_rental'),
    path('owner/applications/', owner_views.owner_applications, name='owner_applications'),
    path('owner/application/<int:pk>/', owner_views.owner_application_detail, name='owner_application_detail'),
    path('owner/documents/<int:pk>/review/', owner_views.owner_review_document, name='owner_review_document'),
    path('owner/payments/', owner_views.owner_payments, name='owner_payments'),
    path('owner/invoices/', owner_views.owner_invoices, name='owner_invoices'),
    path('owner/agreements/', owner_views.owner_agreements, name='owner_agreements'),
    path('owner/agreements/upload/<int:rental_id>/', owner_views.owner_upload_agreement, name='owner_upload_agreement'),
    path('owner/rentals/', owner_views.owner_rentals, name='owner_rentals'),

    # ═══════════════════════════════════════════════════════════
    # ─── Tenant Panel URLs ───────────────────────────────────
    # ═══════════════════════════════════════════════════════════

    path('tenant/apply/<int:shop_id>/', tenant_views.apply_for_rent, name='apply_for_rent'),
    path('tenant/applications/', tenant_views.tenant_applications, name='tenant_applications'),
    path('tenant/application/<int:pk>/', tenant_views.tenant_application_detail, name='tenant_application_detail'),
    path('tenant/application/<int:application_id>/documents/', tenant_views.tenant_upload_documents, name='tenant_upload_documents'),
    path('tenant/document/<int:pk>/delete/', tenant_views.tenant_delete_document, name='tenant_delete_document'),
    path('tenant/rentals/', tenant_views.tenant_rentals, name='tenant_rentals'),
    path('tenant/rental/<int:pk>/', tenant_views.tenant_rental_detail, name='tenant_rental_detail'),
    path('tenant/payments/', tenant_views.tenant_payments, name='tenant_payments'),
    path('tenant/invoices/', tenant_views.tenant_invoices, name='tenant_invoices'),
    path('tenant/agreements/', tenant_views.tenant_agreements, name='tenant_agreements'),
    path('tenant/agreements/upload/<int:rental_id>/', tenant_views.tenant_upload_agreement, name='tenant_upload_agreement'),

    # ─── Download ────────────────────────────────────────────
    path('invoice/<int:pk>/download/', tenant_views.download_invoice, name='download_invoice'),
    path('agreement/<int:pk>/download/', tenant_views.download_agreement, name='download_agreement'),

    # ═══════════════════════════════════════════════════════════
    # ─── Payment URLs ────────────────────────────────────────
    # ═══════════════════════════════════════════════════════════

    path('payment/initiate/<int:application_id>/', payment_views.initiate_payment, name='initiate_payment'),
    path('payment/verify/', payment_views.verify_payment, name='verify_payment'),
    path('payment/success/', payment_views.payment_success, name='payment_success'),
    path('payment/monthly/<int:rental_id>/', payment_views.pay_monthly_rent, name='pay_monthly_rent'),
    path('payment/verify-monthly/', payment_views.verify_monthly_payment, name='verify_monthly_payment'),
]
