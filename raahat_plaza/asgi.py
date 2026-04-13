"""
ASGI config for Raahat Plaza project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'raahat_plaza.settings')
application = get_asgi_application()
