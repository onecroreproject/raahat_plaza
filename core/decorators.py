"""
Role-based access decorators for Raahat Plaza.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def admin_required(view_func):
    """Allow only admin users."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def owner_required(view_func):
    """Allow only owner users."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'owner':
            messages.error(request, 'Access denied. Owner privileges required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def tenant_required(view_func):
    """Allow only tenant users."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'tenant':
            messages.error(request, 'Access denied. Tenant privileges required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_or_owner_required(view_func):
    """Allow admin or owner users."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ['admin', 'owner']:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
