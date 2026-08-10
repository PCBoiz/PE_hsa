"""Keep-warm ping: giữ Neon (free scale-to-zero) KHÔNG ngủ khi backend đang chạy.

Neon free scale-to-zero tắt compute sau ~5 phút không có kết nối → mọi connection
trong pool chết → request kế tiếp (điển hình /auth/login) ném 'SSL error:
unexpected eof' → 500. Luồng nền này ping DB đều đặn (chu kỳ < 5 phút) để Neon
luôn thức suốt phiên chạy. Ping qua common.db.q (đã có retry + reset pool) nên
nếu lỡ ngủ vẫn tự đánh thức lại; lỗi ping KHÔNG được phép giết luồng.
"""
import logging
import threading
import time

log = logging.getLogger("common.keepalive")

# Chu kỳ ping (giây). Neon free scale-to-zero ~300s idle → 90s dư an toàn.
_INTERVAL = 90
_started = False
_lock = threading.Lock()


def _loop():
    from common.db import q  # import trễ: tránh chạm DB khi app chưa sẵn sàng
    while True:
        time.sleep(_INTERVAL)
        try:
            q("SELECT 1")
        except Exception as e:  # noqa: BLE001 — ping hỏng KHÔNG được giết luồng
            log.warning("keepalive ping lỗi (sẽ thử lại lần sau): %s", e)


def start_keepalive():
    """Bật luồng ping (idempotent — gọi nhiều lần chỉ chạy đúng 1 luồng)."""
    global _started
    with _lock:
        if _started:
            return
        _started = True
    t = threading.Thread(target=_loop, name="neon-keepalive", daemon=True)
    t.start()
    log.info("keepalive: bật luồng ping Neon mỗi %ss", _INTERVAL)
