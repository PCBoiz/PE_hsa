"""
Cấu hình gunicorn cho production (Linux) — PERF 2026-07-19.

Vì sao cần nhiều worker: đo thực tế 1 tiến trình Python (GIL) chỉ phục vụ
~115 req/s cho request DRF đầy đủ, bất kể pool DB to bao nhiêu. Kịch bản
100 user chuyển bước ~1.5s cần ~167 req/s → tối thiểu 2 worker; mặc định 4
cho dư địa (~460 req/s).

Ràng buộc kết nối Neon: pool psycopg là PER-PROCESS, Neon -pooler cấp 64
backend/user+db dùng chung với bản Flask → tổng workers × DB_POOL_MAX ≤ ~56.
Đặt qua biến môi trường khi chạy:

    WEB_CONCURRENCY=4 DB_POOL_MAX=14 DB_POOL_MIN=3 \
        gunicorn config.wsgi -c gunicorn.conf.py

SSE đã gỡ (2026-07-19) nên worker sync là đủ — không cần gthread/gevent.
"""
import multiprocessing
import os

bind = '0.0.0.0:' + os.environ.get('PORT', '9000')
workers = int(os.environ.get('WEB_CONCURRENCY', min(4, multiprocessing.cpu_count())))
threads = int(os.environ.get('GUNICORN_THREADS', '8'))
timeout = 30
graceful_timeout = 20
keepalive = 5
accesslog = None          # request-id log đã có trong common/logging.py
errorlog = '-'
