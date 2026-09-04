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

# ĐỘ DÀI KHOÁ LÀ MỘT ĐIỀU KIỆN, KHÔNG PHẢI MỘT LỜI KHUYÊN (04/09/2026).
#
# Khoá đang dùng dài 19 byte. RFC 7518 §3.2 đòi tối thiểu 32 byte cho HS256 —
# đúng thuật toán đang ký MỌI JWT của hệ thống. `pyjwt` có cảnh báo chuyện này,
# và nó in ra ở mỗi lượt sinh token suốt nhiều ngày mà không ai làm gì.
#
# Đó là lý do đổi cảnh báo thành CHẶN: một cảnh báo lặp lại mỗi request là một
# cảnh báo người ta học cách không đọc. Chỉ chặn ở production — máy dev sinh
# khoá 64 ký tự ở nhánh trên nên không bao giờ chạm vào đây.
if IS_PRODUCTION and len(SECRET_KEY.encode()) < 32:
    raise RuntimeError(
        'SECRET_KEY dài %d byte, cần tối thiểu 32 cho HS256 (RFC 7518 §3.2). '
        'Sinh khoá mới: python -c "import secrets;print(secrets.token_urlsafe(48))"'
        % len(SECRET_KEY.encode()))

DEBUG = os.environ.get('DJANGO_DEBUG', os.environ.get('FLASK_DEBUG', '0')) == '1'

# `.strip()` KHÔNG thừa (A5, 04/09/2026). Cách viết tự nhiên nhất của một danh
# sách là `"a.com, b.com"` — có dấu cách. Thiếu `strip` thì phần tử thứ hai
# thành host tên `" b.com"`, không bao giờ khớp, và triệu chứng là 400 trên
# toàn miền chứ không phải một câu lỗi cấu hình đọc được.
# `CSRF_TRUSTED_ORIGINS` ngay dưới ĐÃ strip từ đầu — hai dòng cạnh nhau, cùng
# một việc, một dòng có và một dòng không.
ALLOWED_HOSTS = [h.strip() for h in
                 os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# Frontend Next.js (origin khác) — dùng cho CORS + redirect sau OAuth
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
ALLOWED_ORIGINS = [o.strip() for o in
                   os.environ.get('ALLOWED_ORIGINS', FRONTEND_URL).split(',') if o.strip()]

# Render inject RENDER_EXTERNAL_HOSTNAME khi deploy → tự thêm vào ALLOWED_HOSTS
# (đỡ phải biết trước domain <app>.onrender.com).
_render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)

# CSRF: domain HTTPS được tin cho form POST cross-origin (OAuth allauth qua HTTPS,
# admin nếu có). Ưu tiên env CSRF_TRUSTED_ORIGINS (phẩy); mặc định suy từ
# ALLOWED_ORIGINS https + chính domain backend Render.
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if o.strip().startswith('https')
]
CSRF_TRUSTED_ORIGINS += [
    o for o in ALLOWED_ORIGINS if o.startswith('https') and o not in CSRF_TRUSTED_ORIGINS
]
if _render_host and ('https://' + _render_host) not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append('https://' + _render_host)

# Chatbot "Trợ lý HSA" — DeepSeek (API OpenAI-compatible), key SERVER-SIDE.
# DeepSeek dùng tạm cho testing (rẻ); đổi provider = đổi 3 biến này.
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')
DEEPSEEK_BASE_URL = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

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
    'mockexam',
    'chatbot',
    # Lớp học + báo cáo giảng viên (bước đầu thành ERP, 2026-08-24).
    'teaching',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise serve static (DRF browsable API, staticfiles) khi DEBUG=0 trên
    # host chạy-dài (Render) — phải NGAY SAU SecurityMiddleware.
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
    # PERF 2026-07-19: pool psycopg3 native của Django thay CONN_MAX_AGE.
    # Đo thực tế: mở kết nối mới tới Neon (TLS+SCRAM) mất ~1.9s, mà
    # CONN_MAX_AGE chỉ giữ kết nối THEO THREAD — runserver/gunicorn sync
    # mỗi request 1 thread mới → gần như request nào cũng trả 1.9s phí mở.
    # Pool chia sẻ kết nối ấm giữa mọi thread → chỉ còn RTT query (~260ms/câu
    # khi dev từ VN; <5ms khi backend deploy cùng region với DB).
    # Lưu ý: Django cấm dùng pool chung với conn_max_age ≠ 0.
    'default': dj_database_url.parse(DATABASE_URL, conn_max_age=0)
}
# TCP keepalive như db/connection.py cũ (chống Neon proxy drop connection idle)
DATABASES['default'].setdefault('OPTIONS', {}).update({
    'connect_timeout': 10,
    'keepalives': 1,
    'keepalives_idle': 30,
    'keepalives_interval': 10,
    'keepalives_count': 5,
    'pool': {
        # LOAD TEST 2026-07-19 (100 user đồng thời): mỗi kết nối chỉ phục vụ
        # ~4 query/s khi DB ở region xa (RTT 250ms) → max_size là trần
        # throughput DB; còn trần CPU là ~115 req/s MỖI TIẾN TRÌNH Python
        # (GIL) — muốn hơn phải tăng số worker gunicorn (gunicorn.conf.py).
        # QUAN TRỌNG: pool là PER-PROCESS. Tổng kết nối = workers × max_size
        # phải ≤ ~56 (Neon -pooler cấp 64 backend/user+db, chia sẻ với bản
        # Flask). Mặc định dưới đây cho 1 process dev; production đặt
        # DB_POOL_MAX = 56 // số worker (ví dụ 4 worker → 14).
        'min_size': int(os.environ.get('DB_POOL_MIN', '10')),
        'max_size': int(os.environ.get('DB_POOL_MAX', '48')),
        'num_workers': 6,   # mở kết nối nền song song hơn (mặc định 3) — pool
                            # đầy sau ~12s thay vì ~25s, bớt đuôi chậm sau deploy
        'timeout': 15,      # chờ tối đa 15s khi pool cạn rồi mới lỗi
        'max_idle': 240,    # thu hồi kết nối idle sau 240s (như keepalive cũ)
        # LƯU Ý: KHÔNG thêm 'check' ở đây — Django tự truyền check cho pool
        # (postgresql/base.py) → thêm nữa gây "multiple values for check" crash.
        # Chống conn chết (Neon scale-to-zero) xử lý ở common/db.py (_run retry).
    },
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

# ── Số chặng proxy TIN CẬY đứng trước Django ────────────────────────────────
#
# `X-Forwarded-For` là chuỗi mà MỖI proxy nối thêm vào cuối; phần đầu là thứ
# khách tự viết. Nên "IP thật" = phần tử thứ NUM_PROXIES tính từ cuối.
#
# Đo 04/09/2026 (`SimpleRateThrottle.get_ident`, RequestFactory thật):
#   · để trống (hiện trạng cũ) → dùng CẢ chuỗi làm khoá → xoay header là lọt
#     mọi giới hạn. Đã đo trước đó: 300/300 request qua được hàng rào.
#   · `=1` trên máy dev KHÔNG bảo vệ gì (không có chặng nào, phần tử cuối vẫn
#     do khách đặt) — nên dev dùng `0`, tức `REMOTE_ADDR`, thứ không giả được.
#   · `=1` trên production đúng, vì không gì tới được Django mà không qua tầng
#     biên của Render, và chính nó nối IP thật vào cuối.
#
# Đặt được bằng biến môi trường: nếu anh đo ra chuỗi proxy của Render dài hơn
# một chặng thì đổi biến, không phải sửa mã. TUYỆT ĐỐI đừng đặt `2` khi chỉ có
# một chặng — khi đó khoá lại rơi vào phần khách tự viết, tệ hơn hiện trạng.
NUM_PROXIES = int(os.environ.get('NUM_PROXIES', '1' if IS_PRODUCTION else '0'))

# ── BÍ MẬT GIỮA VERCEL VÀ RENDER (05/09/2026) ────────────────────────────────
#
# `NUM_PROXIES` KHÔNG sửa được chuyện MỌI người dùng thật chung một xô giới hạn:
# `src/lib/proxy.ts` gỡ `x-forwarded-for` của khách (đúng — để khách không tự
# đặt khoá giới hạn), và `fetch` của Node không thêm lại, nên chuỗi tới Django
# không còn IP khách nào để chọn phần tử.
#
# Nên `proxy.ts` gửi IP khách trong header RIÊNG `X-PE-Client-IP`, kèm bí mật
# này trong `X-PE-Proxy-Secret`. Django chỉ tin header IP khi bí mật khớp —
# không có bước ấy thì ai gọi THẲNG Render cũng đặt được, tức mở lại đúng cái lỗ
# vừa bịt, chỉ đổi tên header. Xem `common/net.py`.
#
# ĐẶT Ở HAI NƠI, CÙNG MỘT GIÁ TRỊ:
#   Render  → biến môi trường  PROXY_SHARED_SECRET
#   Vercel  → biến môi trường  PE_PROXY_SECRET   (server-side, KHÔNG `NEXT_PUBLIC_`)
#
# Sinh giá trị:  python -c "import secrets; print(secrets.token_urlsafe(32))"
#
# Để TRỐNG thì mọi thứ chạy y như trước — mặc định ĐÓNG, xem `net._bi_mat_khop`.
# Ngắn hơn 16 ký tự cũng bị coi như chưa có.
PROXY_SHARED_SECRET = os.environ.get('PROXY_SHARED_SECRET', '')

REST_FRAMEWORK = {
    # JWT thay session — CSRF middleware của Django không áp lên JWT header auth
    # (tương đương WTF_CSRF_CHECK_DEFAULT=False + csrf.exempt của Flask cũ).
    # PERF 2026-07-19: bản cache 60s — tránh SELECT users mỗi request
    # (accounts/authentication.py có giải thích đánh đổi).
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.authentication.CachedJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'EXCEPTION_HANDLER': 'common.errors.api_exception_handler',
    # Rate limit đếm PER-ENDPOINT per-IP (common/throttling.py).
    # PERF 2026-07-19: nâng từ 200/day + 50/hour (port nguyên từ Flask-Limiter
    # defaults) — mức cũ giết trải nghiệm nhiều user thật: cả lớp học sau 1 NAT
    # chia nhau 50 request/giờ/endpoint, và login 5/phút chặn từ người thứ 6
    # đăng nhập đầu giờ. Mức mới vẫn chặn được vét cạn/scrape per-endpoint.
    # Static KHÔNG đi qua DRF (Next.js serve) nên bug 429 file tĩnh
    # (AUDIT-FIX 2026-07-07) không thể tái diễn ở kiến trúc mới.
    # Giữ cho mọi throttle của DRF mà mã này KHÔNG ghi đè cũng hiểu đúng chuỗi
    # proxy. Các throttle trong `common/throttling.py` thì đi qua
    # `common.net.client_ip` — xem chú thích ở đó về việc vì sao phải MỘT cửa.
    'NUM_PROXIES': NUM_PROXIES,
    'DEFAULT_THROTTLE_CLASSES': [
        'common.throttling.DailyIPThrottle',
        'common.throttling.HourlyIPThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'ip_day': '10000/day',
        'ip_hour': '1000/hour',
        # Quota theo NGƯỜI DÙNG cho đường chấm bài — xem common/throttling.py.
        # Một em học tối đa vài chục bài mỗi ngày, mỗi bài ~10 lượt chấm.
        'user_day': '2000/day',
        'user_hour': '600/hour',
        'login': '20/min',
        'register': '10/min',
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

# ── Bộ đệm ───────────────────────────────────────────────────────────────────
#
# VÌ SAO PHẢI CÓ MỘT BỘ ĐỆM DÙNG CHUNG (B12, audit 01/09/2026).
#
# Không khai `CACHES` thì Django dùng `LocMemCache` — sống trong bộ nhớ TỪNG
# TIẾN TRÌNH. Mà `render.yaml` chạy `gunicorn --workers 2`. Ba hệ quả đo được
# trên chính mã đang chạy:
#
#   · `quen_dap_an` (bản vá A10) chỉ xoá đệm của MỘT worker. Giảng viên sửa một
#     đáp án sai xong, worker kia vẫn CHẤM bằng đáp án cũ tới hết 60 giây TTL —
#     và con số ấy đi thẳng vào XP và bản đồ năng lực. Bản vá ấy đang có tác
#     dụng đúng một nửa.
#   · `quen_ghi_danh` y hệt: huỷ ghi danh xong vẫn đọc được nội dung khoá thêm
#     một phút qua worker còn lại.
#   · Trần request THỰC TẾ GẤP ĐÔI con số cấu hình: `SimpleRateThrottle` đếm
#     trong cache, mỗi worker một bộ đếm riêng. `user_hour = 600` thực tế là
#     ~1200/giờ/người, và mọi kịch bản làm nghẽn đều được nhân đôi ngân sách.
#
# CÁCH BẬT (anh Sơn làm, tôi không tự tạo dịch vụ tốn tiền):
#   1. Render Dashboard → New → Key Value (Redis) → cùng region `ohio`.
#   2. Copy "Internal Redis URL" → thêm biến môi trường `REDIS_URL` cho
#      service `pe-hsa-backend`.
#   3. Deploy lại. Không có `REDIS_URL` thì mọi thứ chạy y như cũ (LocMemCache),
#      nên bật/tắt không cần sửa một dòng mã nào.
#
# `django-redis` đã nằm trong requirements.txt.
REDIS_URL = os.getenv('REDIS_URL', '').strip()
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                # Redis chết KHÔNG được làm chết cả app: bộ đệm ở đây chỉ để
                # nhanh hơn và để đếm quota, không phải nguồn sự thật nào.
                # `IGNORE_EXCEPTIONS` cho `cache.get` trả None và mã rơi về
                # đường đọc CSDL — chậm hơn, vẫn đúng.
                'IGNORE_EXCEPTIONS': True,
                'SOCKET_CONNECT_TIMEOUT': 3,
                'SOCKET_TIMEOUT': 3,
            },
            'KEY_PREFIX': 'pehsa',
        }
    }
    DJANGO_REDIS_IGNORE_EXCEPTIONS = True

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
    # Render (và mọi PaaS): TLS kết thúc ở proxy, app nhận HTTP kèm header
    # X-Forwarded-Proto=https. KHÔNG khai báo → request.is_secure()=False →
    # cookie Secure không set + redirect có thể loop. Chỉ tin header sau proxy.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
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
STATIC_ROOT = BASE_DIR / 'staticfiles'
# WhiteNoise nén + serve static trực tiếp (không cần Nginx). Non-manifest để
# tránh lỗi thiếu file khi hash (backend chủ yếu trả JSON; static chỉ của DRF).
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
