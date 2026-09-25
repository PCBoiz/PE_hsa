"""Bộ dựng dữ liệu cho phép kiểm miền chương trình — chạy trên CSDL thật, cuộn lại cuối
mỗi phép kiểm (`backend/conftest.py`). Mọi môn / lớp / người đều mang hậu tố ngẫu nhiên,
và mọi khẳng định lọc về đúng dòng của phép kiểm — CSDL dev dùng chung với luồng khác.
"""
import uuid
from datetime import timedelta

import pytest

from common.clock import local_now
from common.db import q1, x


def _hau_to():
    return uuid.uuid4().hex[:10]


class Dung:
    """Dựng thẳng bằng SQL (nhanh hơn đi qua API) — chỉ cho phần DỮ LIỆU NỀN; phần đang
    kiểm luôn đi qua API / hàm dịch vụ thật."""

    def __init__(self):
        self.nay = local_now()

    def nguoi(self, vai='Học viên', ten=None):
        h = _hau_to()
        return q1("INSERT INTO users (name, email, password, role) VALUES (%s, %s, 'x', %s) "
                  'RETURNING id', (ten or 'CT %s' % h, 'dj_ct_%s@example.com' % h, vai))['id']

    def api(self, vai='admin'):
        from rest_framework.test import APIClient

        from accounts.models import User
        c = APIClient()
        uid = self.nguoi(vai)
        c.force_authenticate(user=User.objects.get(id=uid))
        c.uid = uid
        return c

    def khoa(self):
        cid = 'zz_ct_%s' % _hau_to()
        x("INSERT INTO courses (id, title, is_published) VALUES (%s, %s, true)",
          (cid, 'Môn thử ' + cid))
        return cid

    def ban(self, khoa, buoi, status='xuat_ban', lineage=None, ten='Khung thử'):
        """`buoi`: danh sách buổi, mỗi buổi là danh sách TRỌNG SỐ các mục. Trả
        `{'id', 'buoi': [ss_id…], 'muc': [[item_id…]…]}`."""
        vid = q1('''INSERT INTO syllabus_versions (course_id, name, status, lineage_id)
                    VALUES (%s, %s, %s, %s) RETURNING id''', (khoa, ten, status, lineage))['id']
        ra = {'id': vid, 'buoi': [], 'muc': []}
        for so, trong_so in enumerate(buoi, 1):
            ss = q1('INSERT INTO syllabus_sessions (version_id, sort_order, name) '
                    'VALUES (%s, %s, %s) RETURNING id', (vid, so * 10, 'Buổi khung %d' % so))['id']
            ra['buoi'].append(ss)
            ra['muc'].append([q1('''INSERT INTO syllabus_items (session_id, sort_order, kind, title,
                                                                 weight)
                                    VALUES (%s, %s, 'chu_de', %s, %s) RETURNING id''',
                                 (ss, k, 'Mục %d.%d' % (so, k), w))['id']
                              for k, w in enumerate(trong_so, 1)])
        return ra

    def lop(self, khoa=None, gv=None, vid=None, status='active'):
        return q1('''INSERT INTO classes (name, course_id, teacher_id, status, syllabus_version_id)
                     VALUES (%s, %s, %s, %s, %s) RETURNING id''',
                  ('Lớp CT %s' % _hau_to(), khoa, gv, status, vid))['id']

    def buoi(self, lop, ngay=-1, status='planned', ss=None, topic=None, makeup_for=None):
        """`ngay` âm = đã diễn ra ngần ấy ngày trước (giờ VN)."""
        return q1('''INSERT INTO class_sessions (class_id, starts_at, status, syllabus_session_id,
                                                 topic, makeup_for)
                     VALUES (%s, %s, %s, %s, %s, %s) RETURNING id''',
                  (lop, self.nay + timedelta(days=ngay), status, ss, topic, makeup_for))['id']

    def vao(self, lop, uid):
        x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, %s)',
          (lop, uid, self.nay - timedelta(days=90)))

    def diem_danh(self, buoi, uid, status='present'):
        x('INSERT INTO attendance (session_id, user_id, status) VALUES (%s, %s, %s)',
          (buoi, uid, status))

    def ghi_so(self, buoi, muc):
        """`muc`: [(item_id, status)] — ghi thẳng một sổ đầu bài."""
        x('INSERT INTO session_logs (session_id, logged_at) VALUES (%s, %s)', (buoi, self.nay))
        for iid, st in muc:
            x('INSERT INTO session_log_items (session_id, item_id, label, status) '
              "VALUES (%s, %s, 'mục', %s)", (buoi, iid, st))


@pytest.fixture
def dung(db):
    return Dung()
