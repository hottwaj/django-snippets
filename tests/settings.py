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