"""
Django settings — port từ Flask app.py/config.py của Programming_EDU.

Nguyên tắc: giữ nguyên hành vi nghiệp vụ (rate-limit, security headers, CORS,
error JSON tiếng Việt); thay session-cookie auth bằng JWT vì frontend Next.js
nằm ở domain khác (lý do chi tiết: MIGRATION_NOTES.md §Auth).
"""
import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

DJANGO_ENV = os.environ.get('DJANGO_ENV', os.environ.get('FLASK_ENV', 'development'))
IS_PRODUCTION = DJANGO_ENV == 'production'

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    # Giữ đúng policy Flask cũ (Mavis P0#3): production bắt buộc có SECRET_KEY,
    # dev thiếu thì sinh ngẫu nhiên per-process (JWT cấp ra mất hiệu lực khi restart).
    if IS_PRODUCTION:
        raise RuntimeError('SECRET_KEY phải được thiết lập trong production')
    import secrets as _secrets
    SECRET_KEY = _secrets.token_hex(32)

DEBUG = os.environ.get('DJANGO_DEBUG', os.environ.get('FLASK_DEBUG', '0')) == '1'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Frontend Next.js (origin khác) — dùng cho CORS + redirect sau OAuth
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', FRONTEND_URL).split(',')

INSTALLED_APPS = [
    # KHÔNG dùng django.contrib.admin — trang quản trị là /admin của frontend
    # (port từ admin.html) + API /api/admin/* trong app courseadmin.
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',

    'common',
    'accounts',
    'courses',
    'lessons',
    'quizzes',
    'stats',
    'notifications',
    'roadmap',
    'leaderboard',
    'achievements',
    'forum',
    'courseadmin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'common.middleware.RequestIDMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'common.middleware.SecurityHeadersMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ── Database: cùng NeonDB với bản Flask ──────────────────────────────────────
# Cold-start Neon: chọn phương án (b) — CONN_MAX_AGE giữ connection sống giữa
# các request + health_checks loại connection chết (Neon có thể drop khi idle).
# Kết hợp endpoint /health cho cron ping ngoài nếu muốn giữ compute ấm 24/7.
# Lý do chi tiết: MIGRATION_NOTES.md §Neon.
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL chưa được cấu hình trong .env')

DATABASES = {
    'default': dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=240,          # tương đương chu kỳ keepalive 240s của bản Flask
        conn_health_checks=True,
    )
}
# TCP keepalive như db/connection.py cũ (chống Neon proxy drop connection idle)
DATABASES['default'].setdefault('OPTIONS', {}).update({
    'connect_timeout': 10,
    'keepalives': 1,
    'keepalives_idle': 30,
    'keepalives_interval': 10,
    'keepalives_count': 5,
})

# ── Auth ─────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'

# Mật khẩu trong DB là hash werkzeug (scrypt:/pbkdf2:) — hasher tương thích đứng
# đầu để verify không cần reset; hash MỚI cũng ghi bằng định dạng werkzeug để
# 2 bản Flask/Django chạy song song cùng DB trong thời gian chuyển tiếp.
PASSWORD_HASHERS = [
    'accounts.hashers.WerkzeugScryptHasher',
    'accounts.hashers.WerkzeugPBKDF2Hasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

REST_FRAMEWORK = {
    # JWT thay session — CSRF middleware của Django không áp lên JWT header auth
    # (tương đương WTF_CSRF_CHECK_DEFAULT=False + csrf.exempt của Flask cũ).
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'EXCEPTION_HANDLER': 'common.errors.api_exception_handler',
    # Rate limit mặc định như extensions.py Flask: 200/day + 50/hour theo IP.
    # Static KHÔNG đi qua DRF (Next.js serve) nên bug 429 file tĩnh
    # (AUDIT-FIX 2026-07-07) không thể tái diễn ở kiến trúc mới.
    'DEFAULT_THROTTLE_CLASSES': [
        'common.throttling.DailyIPThrottle',
        'common.throttling.HourlyIPThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'ip_day': '200/day',
        'ip_hour': '50/hour',
        'login': '5/min',
        'register': '3/min',
    },
    'UNAUTHENTICATED_USER': 'django.contrib.auth.models.AnonymousUser',
}

# Dev/test chạy e2e + reload liên tục từ 1 IP nên quota production quá chật.
if not IS_PRODUCTION:
    REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].update({
        'ip_day': '20000/day',
        'ip_hour': '5000/hour',
        'login': '100/min',
        'register': '100/min',
    })

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    # PERMANENT_SESSION_LIFETIME của Flask là 8h → refresh token 8h giữ UX cũ
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=8),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
}

# ── CORS (flask-cors: /api/* + supports_credentials) ────────────────────────
CORS_ALLOWED_ORIGINS = [o for o in ALLOWED_ORIGINS if o.startswith('http')]
CORS_ALLOW_CREDENTIALS = True
CORS_URLS_REGEX = r'^/(api|auth)/.*$'

# ── allauth (OAuth Google/Facebook — luồng cũ từ flask-dance) ────────────────
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*']
SOCIALACCOUNT_LOGIN_ON_GET = True   # giữ luồng redirect thẳng như flask-dance
SOCIALACCOUNT_ADAPTER = 'accounts.oauth.LegacySocialAccountAdapter'
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
            'secret': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
        },
        'SCOPE': ['openid', 'email', 'profile'],
    },
    'facebook': {
        'APP': {
            'client_id': os.environ.get('FACEBOOK_CLIENT_ID', ''),
            'secret': os.environ.get('FACEBOOK_CLIENT_SECRET', ''),
        },
        'SCOPE': ['email', 'public_profile'],
    },
}
LOGIN_REDIRECT_URL = '/auth/oauth-complete'          # → cấp JWT rồi redirect về Next
ACCOUNT_LOGOUT_REDIRECT_URL = FRONTEND_URL

# ── Security headers (port set_security_headers của app.py) ─────────────────
SECURE_CONTENT_TYPE_NOSNIFF = True          # X-Content-Type-Options: nosniff
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
if IS_PRODUCTION:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
# CSP y hệt danh sách domain cũ — set trong common.middleware.SecurityHeadersMiddleware
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net "
    "https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com "
    "https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
    "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
    "img-src 'self' data: blob:; "
    "connect-src 'self' https://generativelanguage.googleapis.com; "
    "frame-ancestors 'self'"
)

# ── Logging: request-id + log 5xx (port utils/logging.py — BẬT theo quyết định chủ dự án) ──
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {'()': 'common.logging.RequestIDFilter'},
    },
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(request_id)s] %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['request_id'],
            'formatter': 'verbose',
        },
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django.request': {'handlers': ['console'], 'level': 'ERROR', 'propagate': False},
    },
}

LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
