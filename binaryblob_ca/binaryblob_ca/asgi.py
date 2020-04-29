"""
ASGI config for binaryblob_ca project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os

import django
from channels.routing import get_default_application
from channels.staticfiles import StaticFilesWrapper

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'binaryblob_ca.settings')

django.setup()

application = StaticFilesWrapper(get_default_application())
