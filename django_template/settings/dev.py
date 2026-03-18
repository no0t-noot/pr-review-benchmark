from .base import *  # noqa

DJANGO_ENV = "development"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-nvg5arlsvczsdk5pzu-=f2qpst%ze8#jyuhfmldp7--j#ao5)j"  # pragma: allowlist secret  # nosec  # noqa: E501

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]


# django-browser-reload
# https://github.com/adamchainz/django-browser-reload
INSTALLED_APPS.append("django_browser_reload")  # noqa: F405
MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")  # noqa: F405


# django-extensions
# https://django-extensions.readthedocs.io/en/stable/

# Configure IPython to automatically reload modules
# https://ipython.org/ipython-doc/3/config/extensions/autoreload.html
IPYTHON_ARGUMENTS = [
    "-c=%load_ext autoreload\n%autoreload 2",
    "-i",
]


# Profiling
# https://github.com/jazzband/django-silk

# Unconditionally store request body regardless of size
SILKY_MAX_REQUEST_BODY_SIZE = -1

# Unconditionally store response body regardless of size
SILKY_MAX_RESPONSE_BODY_SIZE = -1

# Unconditionally log all requests
SILKY_INTERCEPT_PERCENT = 100
