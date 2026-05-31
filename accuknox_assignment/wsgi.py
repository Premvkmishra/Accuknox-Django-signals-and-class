"""
WSGI config for accuknox_assignment project.

This module contains the WSGI application that Django uses to serve
HTTP requests. It exposes the WSGI callable as a module-level variable
named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "accuknox_assignment.settings")

application = get_wsgi_application()
