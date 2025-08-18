import os
from pathlib import Path
from decimal import getcontext, ROUND_HALF_UP
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # apps
    "users",
    "finance",
    "miners",
    "botapp",
    "autoclaim",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

# Database
if os.environ.get("DB_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.environ.get("DB_HOST"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "NAME": os.environ.get("DB_NAME", "stanok"),
            "USER": os.environ.get("DB_USER", "stanok"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "stanok"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Internationalization / TZ
LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",   # для backend/static
]
# для продакшена:
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Decimal context
getcontext().rounding = ROUND_HALF_UP

# Business / env
DEPOSIT_STANOK_ADDRESS = os.environ.get("DEPOSIT_STANOK_ADDRESS", "UQ...")
CA_TOKEN = os.environ.get("CA_TOKEN", "")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_ADMIN_TOKEN = os.environ.get("BOT_ADMIN_TOKEN", "")
ADMIN_TG_ID = int(os.environ.get("ADMIN_TG_ID", "0") or 0)


ALLOWED_HOSTS = [
    "*",
    # ...при необходимости ещё домены
]

CSRF_TRUSTED_ORIGINS = [
    "https://optionally-ideal-gnu.cloudpub.ru",
    # можно шире:
    # "https://*.cloudpub.ru",
]
