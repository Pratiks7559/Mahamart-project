import os
from django.core.wsgi import get_wsgi_application

# Apply Django patch for Python 3.14 compatibility
try:
    from config.django_patch import *
except ImportError:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()