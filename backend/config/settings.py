import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "apps.common",
    "apps.tenancy",
    "apps.catalog",
    "apps.orders",
    "apps.payments",
    "apps.delivery",
    "apps.closing",
    "apps.audit",
]

MIDDLEWARE = [
    "apps.common.middleware.TenantContextMiddleware",
    "apps.common.middleware.IdempotencyMiddleware",
]

DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///" + (BASE_DIR / "db.sqlite3").as_posix(),
    ),
}

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
