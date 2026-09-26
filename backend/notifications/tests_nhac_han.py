"""NHẮC HẠN NỘP (`notifications/nhac_han.py`, E2) — chạy trên CSDL thật rồi cuộn lại."""
import uuid
from datetime import timedelta

import pytest

from common.clock import local_now
from common.db import q, q1, x
from common.permissions import ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db


def _nguoi(vai=ROLE_STUDENT, **cai):
    uid = q1("INSERT INTO users (name, email, password, role, streak) VALUES ('NH', %s, 'x', %s, 0) RETURNING id",
             ('nh_%s@example.com' % uuid.uuid4().hex[:10], vai))['id']
    if cai:
        x('INSERT INTO notification_settings (user_id, email_notif, study_remind) VALUES (%s, %s, %s)',
          (uid, cai.get('email_notif', 1), cai.get('study_remind', 1)))
    return uid


@pytest.fixture
def lop():
    gv = _nguoi(ROLE_TEACHER)
    cid = q1("INSERT INTO classes (name, teacher_id, status) VALUES ('Lớp NH', %s, 'active') RETURNING id",
             (gv,))['id']
    return {'id': cid, 'gv': gv}


def _vao(lop, *uids):
    for u in uids:
        x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, now())', (lop['id'], u))


def _bai(lop, gio=24, **kw):
    return q1('''INSERT INTO assignments (class_id, title, due_at, status, kind, target_mode)
                 VALUES (%s, %s, %s, %s, %s, %s) RETURNING id''',
              (lop['id'], kw.get('title', 'Bài NH'), local_now() + timedelta(hours=gio),
               kw.get('status', 'open'), kw.get('kind', 'bai_tap'), kw.get('target_mode', 'lop')))['id']


def _chuong(uid):
    return q("SELECT ref_id, link FROM notifications WHERE user_id = %s AND type = 'nhac_han'", (uid,))


def _thu(uid):
    return q("SELECT dedup_key FROM outbox WHERE user_id = %s AND dedup_key LIKE 'nhac_han:%%'", (uid,))


def test_bai_con_24_gio_chua_nop_thi_nhac_mot_chuong_mot_thu(lop):
    from notifications.nhac_han import quet
    em = _nguoi()
    _vao(lop, em)
    bai = _bai(lop)
    assert quet() >= 1
    assert _chuong(em) == [{'ref_id': bai, 'link': '/bai-tap'}]
    assert _thu(em) == [{'dedup_key': 'nhac_han:%d:%d' % (bai, em)}]


def test_hai_nhip_chi_ra_mot_loi_nhac(lop):
    from notifications.nhac_han import quet
    em = _nguoi()
    _vao(lop, em)
    _bai(lop)
    quet()
    assert quet() == 0
    assert len(_chuong(em)) == 1 and len(_thu(em)) == 1


def test_ngoai_cua_so_20_28_gio_thi_khong_nhac(lop):
    from notifications.nhac_han import quet
    em = _nguoi()
    _vao(lop, em)
    for gio in (19, 29, -1):
        _bai(lop, gio=gio)
    quet()
    assert _chuong(em) == []


def test_da_nop_thi_khong_nhac(lop):
    from notifications.nhac_han import quet
    em = _nguoi()
    _vao(lop, em)
    bai = _bai(lop)
    x('INSERT INTO submissions (assignment_id, user_id, submitted_at, content) VALUES (%s, %s, now(), %s)',
      (bai, em, 'xong'))
    quet()
    assert _chuong(em) == []


def test_tat_nhac_hoc_thi_khong_nhac_gi(lop):
    from notifications.nhac_han import quet
    em = _nguoi(study_remind=0)
    _vao(lop, em)
    _bai(lop)
    quet()
    assert _chuong(em) == [] and _thu(em) == []


def test_tat_email_thi_chi_chuong(lop):
    from notifications.nhac_han import quet
    em = _nguoi(email_notif=0)
    _vao(lop, em)
    _bai(lop)
    quet()
    assert len(_chuong(em)) == 1 and _thu(em) == []


def test_chi_nhac_em_duoc_giao_bai_nhom(lop):
    from notifications.nhac_han import quet
    trong, ngoai = _nguoi(), _nguoi()
    _vao(lop, trong, ngoai)
    bai = _bai(lop, target_mode='nhom')
    x('INSERT INTO assignment_targets (assignment_id, user_id) VALUES (%s, %s)', (bai, trong))
    quet()
    assert len(_chuong(trong)) == 1 and _chuong(ngoai) == []


def test_khong_nhac_bai_kiem_tra_tren_lop_nhap_hay_lop_tam_dung(lop):
    from notifications.nhac_han import quet
    em = _nguoi()
    _vao(lop, em)
    _bai(lop, kind='kiem_tra')
    _bai(lop, status='draft')
    quet()
    assert _chuong(em) == []
    x("UPDATE classes SET status = 'paused' WHERE id = %s", (lop['id'],))
    _bai(lop)
    quet()
    assert _chuong(em) == []


def test_khong_nhac_giang_vien_va_em_da_roi_lop(lop):
    from notifications.nhac_han import quet
    roi = _nguoi()
    _vao(lop, roi, lop['gv'])
    x('UPDATE class_members SET left_at = now() WHERE user_id = %s', (roi,))
    _bai(lop)
    quet()
    assert _chuong(roi) == [] and _chuong(lop['gv']) == []


def test_nhip_quet_roi_gui(lop, monkeypatch):
    from common import mail
    from notifications.hop_thu import nhip
    monkeypatch.setattr(mail, 'gui', lambda den, t, c: (True, 'x', None))
    em = _nguoi()
    _vao(lop, em)
    _bai(lop)
    assert nhip()['nhacHan'] >= 1
    assert q1("SELECT status FROM outbox WHERE user_id = %s", (em,))['status'] == 'sent'
