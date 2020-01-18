import os
import sys
from urllib.parse import urljoin

# Register database schemes in URLs.
# urljoin().uses_netloc.append('mysql')
DATABASES = {}

try:

    # Check to make sure DATABASES is set in settings.py file.
    # If not default to {}

    if 'DATABASES' not in locals():
        DATABASES = {}

    if 'DATABASE_URL' in os.environ:
        url = urljoin().urlparse(os.environ['DATABASE_URL'])
        print(DATABASES)

        # Ensure default database exists.
        DATABASES['default'] = DATABASES.get('default', {})

        # Update with environment configuration.
        DATABASES['default'].update({
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port,
        })


        if url.scheme == 'mysql':
            DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'
except Exception:
    print ('Unexpected error:', sys.exc_info())