from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = "change-me"
DEBUG = False
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.accounts",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.accounts.middleware.AccessLinkMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "botgate-panel-cache",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = False

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/auth/forbidden/"
LOGIN_REDIRECT_URL = "/panel/"
LOGOUT_REDIRECT_URL = "/auth/forbidden/"

ACCESS_LINK_TTL_SECONDS = 180
SESSION_IDLE_TIMEOUT_SECONDS = 3600
FIRST_LOGIN_MAX_ATTEMPTS = 3
FIRST_LOGIN_LOCK_MINUTES = 10
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://127.0.0.1:8000")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
REPORT_TELEGRAM_CHAT_ID = os.getenv("REPORT_TELEGRAM_CHAT_ID", "")
REPORT_EMAIL_TO = [email.strip() for email in os.getenv("REPORT_EMAIL_TO", "").split(",") if email.strip()]
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "BotGate Ferma <noreply@example.com>")
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in {"1", "true", "yes"}
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

JAZZMIN_SETTINGS = {
    "site_title": "BotGate Admin",
    "site_header": "BotGate boshqaruv paneli",
    "site_brand": "BotGate",
    "site_logo_classes": "img-circle",
    "welcome_sign": "BotGate boshqaruv paneliga xush kelibsiz",
    "copyright": "BotGate Panel",
    "search_model": ["accounts.User", "dashboard.DailyEntry", "dashboard.Report"],
    "topmenu_links": [
        {"name": "Asosiy sayt", "url": "/panel/", "new_window": False},
        {"model": "accounts.User"},
        {"model": "dashboard.Report"},
    ],
    "order_with_respect_to": ["accounts", "dashboard"],
    "icons": {
        "accounts": "fas fa-user-shield",
        "accounts.User": "fas fa-users",
        "accounts.TelegramSession": "fab fa-telegram",
        "accounts.AccessLink": "fas fa-link",
        "accounts.AuditLog": "fas fa-clipboard-list",
        "dashboard": "fas fa-chart-column",
        "dashboard.DailyEntry": "fas fa-pen-to-square",
        "dashboard.Report": "fas fa-file-lines",
    },
    "navigation_expanded": True,
    "show_sidebar": True,
    "changeform_format": "horizontal_tabs",
}
