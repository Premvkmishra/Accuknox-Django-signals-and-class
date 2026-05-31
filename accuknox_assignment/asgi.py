"""
ASGI config for accuknox_assignment project.

This module contains the ASGI application that Django uses to handle
asynchronous requests. It exposes the ASGI callable as a module-level
variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "accuknox_assignment.settings")

application = get_asgi_application()
