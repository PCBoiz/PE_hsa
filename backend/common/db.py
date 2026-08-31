"""
Helper raw-SQL trả dict rows — thay cho _ConnWrapper/RealDictCursor của bản Flask.

Lý do giữ raw SQL thay vì viết lại bằng ORM: logic nghiệp vụ (XP, streak,
achievement, upsert ON CONFLICT) phải giữ NGUYÊN từng câu SQL để không lệch
hành vi (MIGRATION_NOTES §SQL). Django autocommit thay cho conn.commit() cũ;
flow nhiều câu lệnh cần nguyên tử thì bọc transaction.atomic() ở view.

RESILIENT (2026-08-10): Neon free scale-to-zero đóng connection trong pool sau
idle → query kế tiếp trên conn chết ném "SSL error: unexpected eof while reading"
(OperationalError) → 500 (điển hình ở /auth/login sau khi backend idle). Bọc
q/q1/x trong _run(): bắt lỗi connection, RESET CẢ POOL (buộc mở conn mới =
đánh thức Neon) rồi THỬ LẠI tối đa _MAX_TRIES. KHÔNG retry khi đang trong
transaction (atomic block) để không phá tính nguyên tử.

FIX v2 (2026-08-10): connection.close() CHỈ trả conn chết về pool — pool KHÔNG
loại nó (conn 'trông vẫn mở' phía client vì TCP chưa nhận ra Neon đóng) nên
retry cứ bốc phải conn chết khác → cả 6 lần đều fail (login treo ~19s rồi 500).
Nay dùng connection.close_pool(): HỦY hẳn pool → lần cursor() kế tiếp Django
dựng pool MỚI toàn conn tươi. Kèm keep-warm ping (common/keepalive.py) để Neon
gần như không bao giờ scale-to-zero khi backend đang chạy.
"""
import logging
import time

from django.db import InterfaceError, OperationalError, connection
from psycopg import errors as psycopg_errors

# Lỗi báo hiệu connection hỏng/đóng (Neon EOF, SSL abort, conn closed…).
_CONN_ERR = (OperationalError, InterfaceError)

# ── LOẠI TRỪ: những lỗi TRÔNG như connection chết nhưng KHÔNG phải ────────────
#
# `psycopg_pool.PoolTimeout` và họ hàng đều kế thừa `psycopg.OperationalError`,
# và Django bọc chúng lại thành `django.db.OperationalError` (đã đo: dựng
# `DatabaseErrorWrapper` rồi ném `PoolTimeout` → bắt được
# `django.db.utils.OperationalError`, và `isinstance(e, _CONN_ERR)` trả True).
# Nên chúng rơi thẳng vào nhánh HỦY CẢ POOL bên dưới — trong khi pool hoàn toàn
# khoẻ, chỉ đang bận.
#
# Vì sao đó là vòng xoáy tự khuếch đại chứ không chỉ là một lần chậm:
#   1. Tải cao, mọi kết nối đều bận. Một luồng chờ trong `getconn()`.
#   2. Sau `timeout` giây → `PoolTimeout`.
#   3. `_run` tưởng connection chết → `_reset_pool()` → `close_pool()`.
#   4. `psycopg_pool.close()` ĐÁ NGAY mọi luồng đang chờ ra với `PoolClosed` —
#      cũng là OperationalError, nên chúng cũng gọi `_reset_pool()`.
#   5. Pool mới phải mở lại từ đầu; mở một kết nối tới Neon (TLS + SCRAM) mất
#      khoảng 1,9 giây (xem chú thích ở config/settings.py).
#   6. Trong lúc đó các luồng ngủ theo `_BACKOFF` = 19 giây, vẫn giữ chỗ worker.
#   7. Yêu cầu mới đổ vào, pool mới cạn ngay → quay lại bước 1.
# Với `gunicorn timeout = 30`, một yêu cầu chờ 15s + ngủ 1s + chờ 15s đã vượt
# ngưỡng ngay ở lần thử THỨ HAI → gunicorn giết cả worker, kéo theo mọi yêu cầu
# đang chạy dở trong worker đó.
#
# `QueryCanceled` (statement timeout) cũng vậy: hủy pool rồi chạy lại ĐÚNG câu
# chậm đó sáu lần. `TooManyConnections` (Neon chạm trần) thì còn ngược đời hơn —
# phản ứng là mở thêm một loạt kết nối mới.
#
# Cả bốn đều KHÔNG được sửa bằng cách dựng lại pool. Để chúng bay lên trên: bên
# gọi nhận 500/503 một lần, còn hơn kéo sập hệ thống cho mọi người.
_NOT_DEAD_CONN = (
    psycopg_errors.QueryCanceled,
)
try:  # psycopg_pool là phụ thuộc gián tiếp qua Django; không có thì bỏ qua.
    from psycopg_pool import PoolClosed, PoolTimeout, TooManyRequests
    _NOT_DEAD_CONN += (PoolTimeout, PoolClosed, TooManyRequests)
except ImportError:  # pragma: no cover
    pass
# Backoff (giây) giữa các lần thử — TỔNG ~20s để phủ trọn cold-start Neon free
# (compute từ trạng thái scale-to-zero thức dậy mất ~5-20s).
_BACKOFF = (1, 2, 3, 5, 8)

logger = logging.getLogger(__name__)


def _dictfetchall(cursor):
    cols = [c[0] for c in cursor.description]
    # `strict=True`: số cột và số giá trị PHẢI bằng nhau. Lệch nghĩa là hàng
    # trả về không khớp `cursor.description` — `zip` mặc định sẽ lặng lẽ CẮT
    # phần thừa, tức mất cột cuối mà không ai biết. Thà nổ ra.
    return [dict(zip(cols, row, strict=True)) for row in cursor.fetchall()]


def _reset_pool():
    """Vứt TOÀN BỘ connection chết: đóng conn hiện tại + HỦY cả pool.

    connection.close() chỉ trả conn về pool, mà pool KHÔNG loại conn chết (nó
    'trông vẫn mở' phía client) → retry cứ bốc phải conn chết khác. close_pool()
    hủy hẳn pool; lần connection.cursor() kế tiếp Django dựng pool MỚI với conn
    tươi = mở kết nối mới tới Neon (đánh thức compute). Cả hai bọc try để một
    lỗi không chặn lỗi kia."""
    # Ghi log chứ không nuốt im lặng (RULES §8): nếu `close_pool()` hỏng thì
    # vòng thử lại bên dưới cứ chạy tiếp trên một pool đã chết, và không ai biết
    # vì sao mọi thứ chậm dần rồi đứng hẳn.
    # noqa CÓ LÝ DO ở cả hai chỗ dưới: đây là DỌN DẸP cố-gắng-hết-sức trên một
    # kết nối ĐÃ hỏng. Bất cứ thứ gì ném ra ở đây cũng không được chặn nhánh
    # dọn dẹp còn lại — và cả hai đều GHI LOG, không nuốt im lặng (RULES §8).
    try:
        connection.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning('[db] không đóng được connection: %s', exc)
    try:
        connection.close_pool()
    except Exception as exc:  # noqa: BLE001
        logger.error('[db] KHÔNG hủy được pool — các lần thử lại sau sẽ chạy '
                     'trên pool cũ: %s', exc)


def _run(sql, params, handler):
    """Chạy 1 câu SQL, tự phục hồi khi connection chết (Neon cold-start).

    Pool giữ connection tới Neon; khi Neon scale-to-zero (idle ~5 phút) thì MỌI
    connection trong pool chết — query kế tiếp ném 'SSL error: unexpected eof'
    (OperationalError). Django/psycopg check không bắt được (conn 'open' phía
    client). Ở đây: RESET cả pool (buộc mở conn mới = đánh thức Neon) rồi thử
    lại, backoff tăng dần phủ trọn thời gian Neon thức. KHÔNG retry khi đang
    trong transaction (đã rollback) để không phá tính nguyên tử."""
    last = None
    for attempt in range(len(_BACKOFF) + 1):
        try:
            with connection.cursor() as cur:
                cur.execute(sql, params or ())
                return handler(cur)
        except _CONN_ERR as e:
            # PHẢI soi `__cause__`, không bắt trực tiếp bằng `except`.
            #
            # `DatabaseErrorWrapper` của Django không ném lại ngoại lệ gốc mà
            # dựng một ngoại lệ MỚI (`dj_exc_type(*exc_value.args)`) rồi gắn bản
            # gốc vào `__cause__`. Nên thứ tới đây KHÔNG còn là `PoolTimeout`
            # nữa — một `except PoolTimeout` đặt phía trên sẽ không bao giờ khớp.
            # Đã đo: bản vá đầu tiên viết đúng kiểu đó và `_reset_pool` vẫn bị
            # gọi đủ 6 lần.
            if isinstance(getattr(e, '__cause__', None), _NOT_DEAD_CONN):
                raise
            last = e
            if connection.in_atomic_block:
                raise
            _reset_pool()  # hủy pool chết → cursor() kế tiếp dựng pool tươi
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
        return dict(zip(cols, row, strict=True))   # xem `_dictfetchall`
    return _run(sql, params, _one)


def x(sql, params=None):
    """INSERT/UPDATE/DELETE không cần kết quả."""
    return _run(sql, params, lambda cur: None)


def xn(sql, params=None):
    """Như ``x`` nhưng TRẢ SỐ DÒNG đã chạm.

    Dùng khi câu lệnh có mệnh đề canh trong ``WHERE`` — kiểu
    ``WHERE id=%s AND submitted_at IS NULL``. Viết ra một hàng rào rồi vứt kết
    quả đi là có hàng rào trên giấy: câu lệnh trượt hết mọi dòng vẫn im lặng
    như lúc nó chạy đúng, và mã đi tiếp như thể đã ghi được.

    Đo 31/08/2026: đúng cái bẫy ấy ở đường nộp bài thi thử — lượt bị đóng bởi
    một tab khác thì UPDATE trúng 0 dòng, bài làm biến mất, mà XP vẫn cộng và
    sự kiện vẫn ghi trỏ vào một dòng không còn.
    """
    return _run(sql, params, lambda cur: cur.rowcount)
