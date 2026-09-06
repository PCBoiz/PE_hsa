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
    """Các header SecurityMiddleware của Django không cover: CSP và bộ đệm.

    (X-Content-Type-Options / X-Frame-Options / Referrer-Policy / HSTS đã do
    SecurityMiddleware + settings đảm nhiệm, giá trị y hệt bản Flask.)
    Dùng setdefault-semantics như app.py cũ: không đè nếu view đã tự set.

    ── VÌ SAO THÊM `Cache-Control` (07/09/2026) ────────────────────────────

    Audit đo được: **không phản hồi API nào** đặt `Cache-Control` — kể cả
    `/api/user`, `/api/admin/overview`, và đường CÔNG KHAI
    `/api/public/parent-report/<chìa>` vốn trả về dữ liệu học tập của một đứa
    trẻ cho người không có tài khoản.

    Thiếu header thì bộ đệm trung gian được phép **tự suy diễn** (RFC 9111
    §4.2.2): một phản hồi 200 trên một URL trông tĩnh có thể bị CDN hay mạng
    công ty giữ lại. Rủi ro hôm nay hẹp — trình duyệt không bao giờ thấy các
    phản hồi này (mọi lời gọi đi từ máy chủ Next), và trang `/bc/<chìa>` đã tự
    đặt `no-store`. Nhưng "hẹp" khác "không có", và cái giá để đóng là một dòng.

    `no-store` chứ không `no-cache`: `no-cache` vẫn CHO PHÉP lưu, chỉ bắt hỏi
    lại trước khi dùng. Với dữ liệu của một đứa trẻ thì thứ cần là "đừng ghi ra
    đĩa", không phải "ghi rồi hỏi lại".

    `setdefault` giữ nguyên: view nào muốn cho phép cache (ví dụ danh mục khoá
    học công khai về sau) chỉ cần tự đặt header của nó, không phải sửa chỗ này.
    """

    #: Tiền tố đường dẫn được coi là API. Chỉ `/api/`, KHÔNG gồm `/auth/`:
    #: `/auth/login` và `/auth/refresh` là POST, mà POST thì không bộ đệm nào
    #: lưu theo mặc định — thêm vào đây là thêm một dòng không làm gì cả.
    TIEN_TO_API = '/api/'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault('Content-Security-Policy', settings.CSP_POLICY)
        if request.path.startswith(self.TIEN_TO_API):
            response.headers.setdefault('Cache-Control', 'private, no-store')
        return response
