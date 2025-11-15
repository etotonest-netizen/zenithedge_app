"""Production settings for zenithedge project.

This module extends the base settings and pulls deployment-specific values
from environment variables configured on the server (see `.htaccess`).
"""

from .settings import *  # noqa

# ---------------------------------------------------------------------------
# Core Django configuration
# ---------------------------------------------------------------------------

# Debug must be off in production unless explicitly enabled
DEBUG = os.environ.get("DEBUG", "False").strip().lower() == "true"

# Allowed hosts & CSRF trusted origins are provided via environment variables
_raw_hosts = os.environ.get(
    "ALLOWED_HOSTS",
    "etotonest.com,www.etotonest.com"
)
ALLOWED_HOSTS = [host.strip() for host in _raw_hosts.split(",") if host.strip()]

_raw_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "https://etotonest.com,https://www.etotonest.com")
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _raw_csrf.split(",") if origin.strip()]

# ---------------------------------------------------------------------------
# Database configuration (defaults to MySQL via cPanel environment variables)
# ---------------------------------------------------------------------------

DB_ENGINE = os.environ.get("DB_ENGINE", "django.db.backends.mysql")
DB_OPTIONS = {}

if DB_ENGINE.endswith("mysql"):
    # Ensure MySQL driver is configured correctly for shared hosting
    DB_OPTIONS = {
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        "charset": "utf8mb4",
        "use_unicode": True,
    }

DATABASES = {
    "default": {
        "ENGINE": DB_ENGINE,
        "NAME": os.environ.get("DB_NAME", ""),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "OPTIONS": DB_OPTIONS,
    }
}

# Fallback to SQLite if required variables are missing
if not DATABASES["default"]["NAME"]:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }

# ---------------------------------------------------------------------------
# Static files & media
# ---------------------------------------------------------------------------

STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# ---------------------------------------------------------------------------
# Security hardening for HTTPS production deployment
# ---------------------------------------------------------------------------

SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").strip().lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", 31536000))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------------
# Logging: write to file in production (inherit handlers from base settings)
# ---------------------------------------------------------------------------

for handler in ("console", "file", "zenbot_file", "webhook_file"):
    if handler in LOGGING.get("handlers", {}):  # noqa: F405 (imported from base)
        LOGGING["handlers"][handler]["level"] = os.environ.get("LOG_LEVEL", "INFO")

# ---------------------------------------------------------------------------
# Channels configuration – use Redis when available
# ---------------------------------------------------------------------------

redis_url = os.environ.get("REDIS_URL")
if redis_url:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [redis_url]},
        }
    }

# ---------------------------------------------------------------------------
# Email backend overrides (optional)
# ---------------------------------------------------------------------------

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)

# If SMTP credentials are present, configure them
if EMAIL_BACKEND.endswith("EmailBackend"):
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").strip().lower() == "true"
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

# ---------------------------------------------------------------------------
# Miscellaneous tweaks
# ---------------------------------------------------------------------------

# Ensure Django trusts the Proxy (important when behind cPanel/CloudLinux)
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
