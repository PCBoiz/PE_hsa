"""
Port từ utils/logging.py (Flask): JSON formatter + request_id filter + log_5xx.
Bản Flask ghi RotatingFileHandler logs/app.log — giữ nguyên khả năng đó qua
setup trong settings.LOGGING; request_id lấy từ thread-local thay vì Flask g.
"""
import json
import logging
import traceback

from common.middleware import get_request_id


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    """Chuyển mọi LogRecord thành một dòng JSON (giữ format bản Flask)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            'timestamp': self.formatTime(record, self.datefmt or '%Y-%m-%dT%H:%M:%S%z'),
            'level': record.levelname,
            'logger': record.name,
            'request_id': getattr(record, 'request_id', get_request_id()),
            'message': record.getMessage(),
        }
        if record.exc_info:
            payload['exc_info'] = self.formatException(record.exc_info)
        if hasattr(record, 'stack_trace'):
            payload['stack_trace'] = record.stack_trace
        for key, val in record.__dict__.items():
            if key not in {
                'args', 'asctime', 'created', 'exc_info', 'exc_text',
                'filename', 'funcName', 'id', 'levelname', 'levelno',
                'lineno', 'module', 'msecs', 'message', 'msg', 'name',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'stack_trace', 'thread', 'threadName',
                'request_id', 'taskName',
            } and not key.startswith('_'):
                payload[key] = val
        return json.dumps(payload, ensure_ascii=False, default=str)


def log_5xx(logger: logging.Logger, exc: BaseException | None = None,
            message: str = 'Server Error', request=None) -> None:
    """Ghi ERROR kèm stack trace + request info + request_id (như bản Flask)."""
    extra: dict = {}
    if request is not None:
        extra['http_method'] = request.method
        extra['path'] = request.path
        # IP QUA CỬA DUY NHẤT, không đọc `REMOTE_ADDR` thô (A1, 05/09/2026).
        #
        # `common/net.py` tự nhận là "nơi duy nhất trả lời request này đến từ
        # đâu", và `docs/VIEC_CUA_ANH.md` §A2 chép lại nguyên câu ấy cho anh
        # đọc. Dòng này làm câu ấy thành SAI: nó là người đọc IP thứ ba, và nó
        # đọc một nguồn khác.
        #
        # Đo trên production (NUM_PROXIES=1, một chặng biên Render):
        #     client_ip(req)          → 203.0.113.9   ← IP học viên thật
        #     META['REMOTE_ADDR']     → 10.0.0.7      ← chặng biên, MỌI request
        #
        # Tức mọi dòng nhật ký 5xx đều mang CÙNG một IP vô nghĩa, và nó mâu
        # thuẫn với dòng `admin_audit` của chính request đó. Khi đi truy một sự
        # cố, hai con số khác nhau cho cùng một request tệ hơn không có số nào:
        # người đọc phải dừng lại chọn tin cái nào.
        # Nhập TRONG hàm chứ không ở đầu tệp: `settings.LOGGING` trỏ tới
        # `common.logging.RequestIDFilter`, nên tệp này được nạp ngay lúc
        # `dictConfig` chạy. Kéo thêm một mô-đun đọc `settings` vào đúng lúc ấy
        # là một rủi ro không cần chuốc, đổi lấy đúng một lần `import` đã nằm
        # sẵn trong `sys.modules` ở mọi lượt gọi sau.
        from common.net import client_ip

        extra['remote_addr'] = client_ip(request)
    if exc is not None:
        extra['stack_trace'] = traceback.format_exc()
        logger.error(message, exc_info=exc, extra=extra)
    else:
        extra['stack_trace'] = traceback.format_stack()
        logger.error(message, extra=extra)
