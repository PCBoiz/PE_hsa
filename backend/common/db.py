"""
Helper raw-SQL trả dict rows — thay cho _ConnWrapper/RealDictCursor của bản Flask.

Lý do giữ raw SQL thay vì viết lại bằng ORM: logic nghiệp vụ (XP, streak,
achievement, upsert ON CONFLICT) phải giữ NGUYÊN từng câu SQL để không lệch
hành vi (MIGRATION_NOTES §SQL). Django autocommit thay cho conn.commit() cũ;
flow nhiều câu lệnh cần nguyên tử thì bọc transaction.atomic() ở view.
"""
from django.db import connection


def _dictfetchall(cursor):
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def q(sql, params=None):
    """SELECT nhiều row → list[dict]."""
    with connection.cursor() as cur:
        cur.execute(sql, params or ())
        return _dictfetchall(cur)


def q1(sql, params=None):
    """SELECT/RETURNING 1 row → dict | None."""
    with connection.cursor() as cur:
        cur.execute(sql, params or ())
        row = cur.fetchone()
        if row is None:
            return None
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))


def x(sql, params=None):
    """INSERT/UPDATE/DELETE không cần kết quả."""
    with connection.cursor() as cur:
        cur.execute(sql, params or ())
