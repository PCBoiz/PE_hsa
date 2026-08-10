"""
Helper raw-SQL trả dict rows — thay cho _ConnWrapper/RealDictCursor của bản Flask.

Lý do giữ raw SQL thay vì viết lại bằng ORM: logic nghiệp vụ (XP, streak,
achievement, upsert ON CONFLICT) phải giữ NGUYÊN từng câu SQL để không lệch
hành vi (MIGRATION_NOTES §SQL). Django autocommit thay cho conn.commit() cũ;
flow nhiều câu lệnh cần nguyên tử thì bọc transaction.atomic() ở view.

RESILIENT (2026-08-10): Neon free scale-to-zero đóng connection trong pool sau
idle → query kế tiếp trên conn chết ném "SSL error: unexpected eof while reading"
(OperationalError) → 500 (điển hình ở /auth/login sau khi backend idle). Bọc
q/q1/x trong _run(): bắt lỗi connection, ĐÓNG conn chết (buộc mở conn mới =
đánh thức Neon) rồi THỬ LẠI tối đa _MAX_TRIES. KHÔNG retry khi đang trong
transaction (atomic block) để không phá tính nguyên tử.
"""
import time

from django.db import InterfaceError, OperationalError, connection

# Lỗi báo hiệu connection hỏng/đóng (Neon EOF, SSL abort, conn closed…).
_CONN_ERR = (OperationalError, InterfaceError)
# Backoff (giây) giữa các lần thử — TỔNG ~20s để phủ trọn cold-start Neon free
# (compute từ trạng thái scale-to-zero thức dậy mất ~5-20s).
_BACKOFF = (1, 2, 3, 5, 8)


def _dictfetchall(cursor):
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _run(sql, params, handler):
    """Chạy 1 câu SQL, tự phục hồi khi connection chết (Neon cold-start).

    Pool giữ connection tới Neon; khi Neon scale-to-zero (idle ~5 phút) thì MỌI
    connection trong pool chết — query kế tiếp ném 'SSL error: unexpected eof'
    (OperationalError). Django/psycopg check không bắt được (conn 'open' phía
    client). Ở đây: đóng conn chết (buộc pool mở conn mới = đánh thức Neon) rồi
    thử lại, backoff tăng dần phủ trọn thời gian Neon thức. KHÔNG retry khi đang
    trong transaction (đã rollback) để không phá tính nguyên tử."""
    last = None
    for attempt in range(len(_BACKOFF) + 1):
        try:
            with connection.cursor() as cur:
                cur.execute(sql, params or ())
                return handler(cur)
        except _CONN_ERR as e:
            last = e
            if connection.in_atomic_block:
                raise
            try:
                connection.close()  # trả conn chết về pool → pool discard, mở mới
            except Exception:
                pass
            if attempt < len(_BACKOFF):
                time.sleep(_BACKOFF[attempt])  # chờ Neon compute thức dậy
    raise last


def q(sql, params=None):
    """SELECT nhiều row → list[dict]."""
    return _run(sql, params, _dictfetchall)


def q1(sql, params=None):
    """SELECT/RETURNING 1 row → dict | None."""
    def _one(cur):
        row = cur.fetchone()
        if row is None:
            return None
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))
    return _run(sql, params, _one)


def x(sql, params=None):
    """INSERT/UPDATE/DELETE không cần kết quả."""
    return _run(sql, params, lambda cur: None)
