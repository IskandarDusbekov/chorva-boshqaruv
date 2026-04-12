from pathlib import Path
import os
import logging.config

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

SECRET_KEY = "change-me"
DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

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
    "apps.accounts.middleware.SecurityProbeBlockMiddleware",
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
                "apps.dashboard.context_processors.header_farm_balance",
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

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/auth/forbidden/"
LOGIN_REDIRECT_URL = "/panel/"
LOGOUT_REDIRECT_URL = "/auth/forbidden/"
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

ACCESS_LINK_TTL_SECONDS = 180
SESSION_IDLE_TIMEOUT_SECONDS = 3600
FIRST_LOGIN_MAX_ATTEMPTS = 3
FIRST_LOGIN_LOCK_MINUTES = 10
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://127.0.0.1:8000")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_URL = os.getenv("ADMIN_URL", "botgate-admin/").strip("/") + "/"
REPORT_TELEGRAM_CHAT_ID = os.getenv("REPORT_TELEGRAM_CHAT_ID", "")
REPORT_EMAIL_TO = [email.strip() for email in os.getenv("REPORT_EMAIL_TO", "").split(",") if email.strip()]
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "BotGate Ferma <noreply@example.com>")
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in {"1", "true", "yes"}
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DJANGO_LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO")
DJANGO_ERROR_LOG_LEVEL = os.getenv("DJANGO_ERROR_LOG_LEVEL", "ERROR")

JAZZMIN_SETTINGS = {
    "site_title": "BotGate Admin",
    "site_header": "BotGate boshqaruv paneli",
    "site_brand": "BotGate",
    "site_logo_classes": "img-circle",
    "welcome_sign": "BotGate boshqaruv paneliga xush kelibsiz",
    "copyright": "BotGate Panel",
    "search_model": [
        "accounts.User",
        "accounts.AllowedContact",
        "accounts.TelegramSession",
        "dashboard.MilkRecord",
        "dashboard.FinanceEntry",
        "dashboard.Worker",
        "dashboard.WorkerAdvance",
    ],
    "topmenu_links": [
        {"name": "Asosiy sayt", "url": "/panel/", "new_window": False},
        {"model": "accounts.User"},
        {"model": "dashboard.FinanceEntry"},
        {"model": "dashboard.Worker"},
    ],
    "order_with_respect_to": [
        "accounts",
        "accounts.User",
        "accounts.AllowedContact",
        "accounts.TelegramSession",
        "accounts.AccessLink",
        "accounts.AuditLog",
        "dashboard",
        "dashboard.MilkRecord",
        "dashboard.MilkPrice",
        "dashboard.FinanceEntry",
        "dashboard.FinanceCategory",
        "dashboard.Worker",
        "dashboard.WorkerAdvance",
        "dashboard.WorkerJobType",
    ],
    "icons": {
        "accounts": "fas fa-user-shield",
        "accounts.User": "fas fa-users",
        "accounts.AllowedContact": "fas fa-address-card",
        "accounts.TelegramSession": "fab fa-telegram",
        "accounts.AccessLink": "fas fa-link",
        "accounts.AuditLog": "fas fa-clipboard-list",
        "dashboard": "fas fa-chart-column",
        "dashboard.MilkRecord": "fas fa-glass-water-droplet",
        "dashboard.MilkPrice": "fas fa-tags",
        "dashboard.FinanceEntry": "fas fa-wallet",
        "dashboard.FinanceCategory": "fas fa-layer-group",
        "dashboard.Worker": "fas fa-users-gear",
        "dashboard.WorkerAdvance": "fas fa-money-bill-transfer",
        "dashboard.WorkerJobType": "fas fa-briefcase",
    },
    "navigation_expanded": True,
    "show_sidebar": True,
    "changeform_format": "horizontal_tabs",
    "hide_apps": ["auth"],
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": None,
    "navbar_small_text": True,
    "footer_small_text": True,
    "body_small_text": False,
    "brand_small_text": False,
    "accent": "accent-indigo",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "sidebar": "sidebar-light-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme_color": "primary",
    "button_classes": {
        "primary": "btn btn-primary",
        "secondary": "btn btn-outline-secondary",
        "info": "btn btn-info",
        "warning": "btn btn-warning",
        "danger": "btn btn-danger",
        "success": "btn btn-success",
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(name)s %(message)s",
        },
        "simple": {
            "format": "%(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "app_file": {
            "class": "logging.FileHandler",
            "filename": LOGS_DIR / "app.log",
            "formatter": "verbose",
            "level": DJANGO_LOG_LEVEL,
            "encoding": "utf-8",
        },
        "error_file": {
            "class": "logging.FileHandler",
            "filename": LOGS_DIR / "error.log",
            "formatter": "verbose",
            "level": DJANGO_ERROR_LOG_LEVEL,
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console", "app_file", "error_file"],
        "level": DJANGO_LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console", "app_file", "error_file"],
            "level": DJANGO_LOG_LEVEL,
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "app_file", "error_file"],
            "level": DJANGO_ERROR_LOG_LEVEL,
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "app_file", "error_file"],
            "level": DJANGO_LOG_LEVEL,
            "propagate": False,
        },
        "bot": {
            "handlers": ["console", "app_file", "error_file"],
            "level": DJANGO_LOG_LEVEL,
            "propagate": False,
        },
    },
}
