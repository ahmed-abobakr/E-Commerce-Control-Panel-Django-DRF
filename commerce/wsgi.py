"""
WSGI config for commerce project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from phoenix.otel import register

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'commerce.settings')
register(
    project_name="ecommerce-managemtn-django-project",
    endpoint="http://localhost:6006/v1/traces" # Default local phoenix endpoint
)
application = get_wsgi_application()
