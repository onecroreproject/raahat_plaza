"""
Context processors for Raahat Plaza templates.
"""
from .models import Notification


def global_context(request):
    """Add global context variables to all templates."""
    context = {
        'app_name': 'Raahat Plaza',
        'app_description': 'Mall Rental Management System',
    }
    if request.user.is_authenticated:
        context['unread_notifications'] = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        context['recent_notifications'] = Notification.objects.filter(
            user=request.user
        )[:5]
        context['user_role'] = request.user.role
    return context
