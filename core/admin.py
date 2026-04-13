"""
Django Admin registration for Raahat Plaza models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Mall, Floor, Shop, RentApplication, Document,
    Rental, Payment, Invoice, Agreement, Notification
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active_account', 'phone')
    list_filter = ('role', 'is_active_account', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Profile', {
            'fields': ('role', 'phone', 'address', 'is_active_account', 'profile_image'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Profile', {
            'fields': ('role', 'phone', 'email', 'first_name', 'last_name'),
        }),
    )


@admin.register(Mall)
class MallAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'created_at')


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('floor_name', 'mall', 'floor_order', 'total_shops')
    list_filter = ('mall',)
    ordering = ('floor_order',)


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('shop_number', 'floor', 'size', 'monthly_rent', 'ownership_type', 'owner', 'rental_status', 'listing_type')
    list_filter = ('floor', 'ownership_type', 'rental_status', 'listing_type')
    search_fields = ('shop_number',)


@admin.register(RentApplication)
class RentApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'shop', 'status', 'submitted_at', 'approved_at')
    list_filter = ('status',)
    search_fields = ('tenant__username', 'tenant__first_name')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'document_type', 'status', 'file_name', 'uploaded_at')
    list_filter = ('document_type', 'status')


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'tenant', 'owner', 'rent_amount', 'start_date', 'end_date', 'status')
    list_filter = ('status',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'shop', 'payment_type', 'amount', 'status', 'paid_at')
    list_filter = ('payment_type', 'status')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'tenant_name', 'shop_number', 'total_amount', 'generated_at')


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ('id', 'rental', 'status', 'uploaded_by_role', 'uploaded_at')
    list_filter = ('status', 'uploaded_by_role')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
