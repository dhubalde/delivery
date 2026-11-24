import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

INSECURE_SECRET_KEY = "dev-only-insecure-key"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", INSECURE_SECRET_KEY)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

if not DEBUG and SECRET_KEY == INSECURE_SECRET_KEY:
    raise ImproperlyConfigured(
        "Set DJANGO_SECRET_KEY to a real secret before running with DJANGO_DEBUG=0."
    )


def env_list(name: str) -> list[str]:
    """Parse a comma-separated environment variable into a list of values."""
    raw = os.environ.get(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


# Origins of the local dev servers (Vite on 5173, Django on 8000).
LOCAL_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
]

# Railway exposes the public domain of the service, so a fresh deploy works
# without hand-copying the host into a variable.
_configured_hosts = env_list("DJANGO_ALLOWED_HOSTS")
if not _configured_hosts and os.environ.get("RAILWAY_PUBLIC_DOMAIN"):
    _configured_hosts = [os.environ["RAILWAY_PUBLIC_DOMAIN"]]
ALLOWED_HOSTS = _configured_hosts or (["*"] if DEBUG else [])

CSRF_TRUSTED_ORIGINS = LOCAL_DEV_ORIGINS + env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# The SPA runs on a different origin than the API outside local dev (dev uses
# the Vite proxy, so same-origin is not guaranteed in production).
CORS_ALLOWED_ORIGINS = (LOCAL_DEV_ORIGINS if DEBUG else []) + env_list(
    "DJANGO_CORS_ALLOWED_ORIGINS"
)

ROOT_URLCONF = "config.urls"

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.common",
    "apps.tenancy",
    "apps.catalog",
    "apps.orders",
    "apps.customers",
    "apps.payments",
    "apps.delivery",
    "apps.closing",
    "apps.audit",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.common.middleware.TenantContextMiddleware",
    "apps.common.middleware.IdempotencyMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# WhiteNoise serves STATIC_ROOT when DEBUG=0. The non-manifest variant keeps a
# first production deploy from failing on one missing asset reference.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///" + (BASE_DIR / "db.sqlite3").as_posix(),
    ),
}

USE_TZ = True
# Business timezone: schedules, business dates and open/closed checks are all
# computed in local time (hours are entered per weekday in AR local time).
TIME_ZONE = "America/Argentina/Buenos_Aires"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_V2 = os.environ.get("AUTH_V2", "0") == "1"

# Customer auth gate — allows rollback of per-company client registration without dropping tables
CUSTOMER_AUTH_ENABLED = os.environ.get("CUSTOMER_AUTH_ENABLED", "1") == "1"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
}

# Production hardening. The platform terminates TLS and forwards the original
# scheme in X-Forwarded-Proto.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "1") == "1"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Off by default: enabling HSTS on a domain you may still move is painful.
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "0"))
