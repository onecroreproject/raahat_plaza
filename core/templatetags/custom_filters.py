"""
Custom template filters for Raahat Plaza.
"""
from django import template

register = template.Library()


@register.filter
def currency(value):
    """Format number as Indian currency."""
    try:
        value = float(value)
        return f"₹{value:,.2f}"
    except (ValueError, TypeError):
        return value


@register.filter
def status_badge(status):
    """Return CSS class for status badge."""
    status_classes = {
        'vacant': 'badge-success',
        'applied': 'badge-warning',
        'occupied': 'badge-info',
        'available': 'badge-success',
        'hidden': 'badge-secondary',
        'draft': 'badge-secondary',
        'submitted': 'badge-primary',
        'under_review': 'badge-warning',
        'documents_pending': 'badge-warning',
        'approved': 'badge-success',
        'awaiting_payment': 'badge-info',
        'active': 'badge-success',
        'rejected': 'badge-danger',
        'cancelled': 'badge-secondary',
        'uploaded': 'badge-primary',
        'pending_review': 'badge-warning',
        'reupload_required': 'badge-danger',
        'pending': 'badge-warning',
        'created': 'badge-info',
        'successful': 'badge-success',
        'failed': 'badge-danger',
        'refunded': 'badge-secondary',
        'expired': 'badge-secondary',
        'terminated': 'badge-danger',
    }
    return status_classes.get(status, 'badge-secondary')


@register.filter
def percentage(value, total):
    """Calculate percentage."""
    try:
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
