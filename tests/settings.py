DEBUG=True

USE_TZ=True

DATABASES={
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    }
}

ROOT_URLCONF="tests.urls"

SECRET_KEY = 'fake-key'

INSTALLED_APPS=[
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "tests",
]

CACHES = {
    'default': {
        'BACKEND': 'django_snippets.hierarchical_cache.HierarchicalCache',
        'OPTIONS': {
            'CACHE_NAMES': ['locmem1', 'locmem2'],
        }
    },
    'locmem1': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'locmem1',},
    'locmem2': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'locmem2',},
}