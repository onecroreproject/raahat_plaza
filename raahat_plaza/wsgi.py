"""
WSGI config for Raahat Plaza project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'raahat_plaza.settings')
application = get_wsgi_application()
