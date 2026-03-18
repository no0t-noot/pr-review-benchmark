from .base import *  # noqa

DJANGO_ENV = "test"

SECRET_KEY = "test"  # pragma: allowlist secret  # nosec

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
