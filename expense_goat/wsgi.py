"""
WSGI config for Expense Goat project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expense_goat.settings')

application = get_wsgi_application()
