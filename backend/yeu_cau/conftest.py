"""Bộ dựng dữ liệu cho phép kiểm hộp Yêu cầu — CSDL thật, cuộn lại cuối mỗi phép kiểm
(`backend/conftest.py`). Mọi người / lớp mang hậu tố ngẫu nhiên; phần ĐANG KIỂM luôn đi qua
view thật (APIClient) — chỉ dữ liệu nền dựng thẳng bằng SQL.
"""
import secrets
import uuid

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.db import q1, x


def _h():
    return uuid.uuid4().hex[:10]


class Dung:
    def nguoi(self, vai='Học viên', ten=None):
        h = _h()
        return q1("INSERT INTO users (name, email, password, role, streak) VALUES (%s, %s, 'x', %s, 0) "
                  'RETURNING id', (ten or 'YC %s' % h, 'dj_yc_%s@example.com' % h, vai))['id']

    def api(self, uid):
        c = APIClient()
        c.force_authenticate(user=User.objects.get(id=uid))
        c.uid = uid
        return c

    def lop(self, gv=None, mon='hsa_quantitative', loai='nhom', ten=None):
        return q1("INSERT INTO classes (name, course_id, status, class_type, teacher_id) "
                  "VALUES (%s, %s, 'active', %s, %s) RETURNING id",
                  (ten or 'Lớp YC %s' % _h(), mon, loai, gv))['id']

    def vao(self, lop, uid):
        x("INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, now() - interval '20 days')",
          (lop, uid))

    def buoi(self, lop):
        return q1("INSERT INTO class_sessions (class_id, starts_at, recording_url) "
                  "VALUES (%s, now() - interval '1 day', 'https://zoom.example/rec') RETURNING id", (lop,))['id']

    def link(self, lop, em, tao, han="now() + interval '10 days'", thu_hoi=None):
        tk = secrets.token_urlsafe(32)
        x('INSERT INTO parent_report_links (token, class_id, user_id, period_from, period_to, created_by, '
          'expires_at, revoked_at) VALUES (%s, %s, %s, current_date - 30, current_date, %s, ' + han + ', %s)',
          (tk, lop, em, tao, thu_hoi))
        return tk


@pytest.fixture
def d(db):
    return Dung()


@pytest.fixture
def canh(d):
    """Một trung tâm nhỏ: học vụ, GV A dạy lớp A (có TG A + hai em), GV B dạy lớp B."""
    c = {}
    c['hv'] = d.nguoi('Quản lý học vụ')
    c['gv'] = d.nguoi('Giảng viên')
    c['gv_b'] = d.nguoi('Giảng viên')
    c['tg'] = d.nguoi('Trợ giảng')
    c['em'] = d.nguoi('Học viên')
    c['em2'] = d.nguoi('Học viên')
    c['a'] = d.lop(gv=c['gv'])
    c['b'] = d.lop(gv=c['gv_b'], mon='hsa_verbal')
    d.vao(c['a'], c['tg'])
    d.vao(c['a'], c['em'])
    d.vao(c['a'], c['em2'])
    return c
