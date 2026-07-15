"""
Error JSON thống nhất — port từ app.py Flask.

Hai format cùng tồn tại ở bản Flask, giữ nguyên cả hai:
1. Guard `api_login_required`/`api_admin_required` (utils/__init__.py) trả
   {'error': 'Chưa đăng nhập'} 401 / {'error': 'Không có quyền truy cập'} 403
   → là body 401/403 mà frontend thực tế gặp → map cho NotAuthenticated/PermissionDenied.
2. errorhandler app.py trả {"error": {"status", "message", "detail"}, "request_id"}
   → dùng cho 400/404/429/500 và mọi lỗi khác.
"""
import logging

from django.http import JsonResponse
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from common.logging import log_5xx
from common.middleware import get_request_id

logger = logging.getLogger(__name__)


def _error_payload(status: int, message: str, detail=None) -> dict:
    payload = {'error': {'status': status, 'message': message}}
    if detail:
        payload['error']['detail'] = detail
    payload['request_id'] = get_request_id()
    return payload


def api_exception_handler(exc, context):
    request = context.get('request')

    if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
        return Response({'error': 'Chưa đăng nhập'}, status=401)
    if isinstance(exc, exceptions.PermissionDenied):
        return Response({'error': 'Không có quyền truy cập'}, status=403)
    if isinstance(exc, exceptions.Throttled):
        return Response(
            _error_payload(429, 'Quá nhiều yêu cầu — vui lòng thử lại sau',
                           f'Thử lại sau {exc.wait} giây' if exc.wait else None),
            status=429)
    if isinstance(exc, exceptions.NotFound):
        return Response(
            _error_payload(404, 'Không tìm thấy tài nguyên',
                           request.path if request else None),
            status=404)
    if isinstance(exc, exceptions.ValidationError):
        return Response(_error_payload(400, 'Yêu cầu không hợp lệ', exc.detail), status=400)

    response = drf_exception_handler(exc, context)
    if response is not None:
        return Response(
            _error_payload(response.status_code, 'Yêu cầu không hợp lệ', response.data),
            status=response.status_code)

    # Exception chưa xử lý → 500, log kèm stack trace + request_id (log_5xx cũ)
    log_5xx(logger, exc=exc, message=f'Unhandled exception: {type(exc).__name__}',
            request=request)
    return Response(_error_payload(500, 'Lỗi máy chủ nội bộ — chúng tôi đang xử lý'),
                    status=500)


# Handler ngoài DRF (urls.py handler404/handler500) — giữ JSON tiếng Việt
def handler404(request, exception=None):
    return JsonResponse(_error_payload(404, 'Không tìm thấy tài nguyên', request.path),
                        status=404)


def handler500(request):
    log_5xx(logger, message='HTTP 500 Internal Server Error', request=request)
    return JsonResponse(_error_payload(500, 'Lỗi máy chủ nội bộ — chúng tôi đang xử lý'),
                        status=500)
