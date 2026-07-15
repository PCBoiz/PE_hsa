"""
Port từ Flask:
- RequestIDMiddleware  ← utils/logging.py init_request_id (UUID vào context + header X-Request-ID)
- SecurityHeadersMiddleware ← app.py set_security_headers (CSP nguyên văn danh sách domain cũ)
"""
import threading
import uuid

from django.conf import settings

_local = threading.local()


def get_request_id() -> str:
    return getattr(_local, 'request_id', '-')


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rid = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        _local.request_id = rid
        request.request_id = rid
        try:
            response = self.get_response(request)
            response['X-Request-ID'] = rid
            return response
        finally:
            _local.request_id = '-'


class SecurityHeadersMiddleware:
    """Các header SecurityMiddleware của Django không cover: CSP.

    (X-Content-Type-Options / X-Frame-Options / Referrer-Policy / HSTS đã do
    SecurityMiddleware + settings đảm nhiệm, giá trị y hệt bản Flask.)
    Dùng setdefault-semantics như app.py cũ: không đè nếu view đã tự set.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault('Content-Security-Policy', settings.CSP_POLICY)
        return response
