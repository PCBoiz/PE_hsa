"""Mặt tiền gửi thông báo dùng chung `notifications/gui.py` (kế hoạch v2, Ngày 0 — 25/09/2026).

Chạy trên CSDL thật rồi cuộn lại (conftest.py); mỗi test dựng người của riêng nó.
Thư không gửi thật: thay `mail.gui` bằng hàm ghi lại.
"""
import uuid

import pytest

from common.db import q, q1, x

pytestmark = pytest.mark.django_db


def _nguoi(nhan_thu=None):
    uid = q1("INSERT INTO users (name, email, password, streak) VALUES ('TB', %s, 'x', 0) RETURNING id",
             ('tb_%s@example.com' % uuid.uuid4().hex[:10],))['id']
    if nhan_thu is not None:
        x('INSERT INTO notification_settings (user_id, email_notif) VALUES (%s, %s)', (uid, nhan_thu))
    return uid


def _chuong(uid):
    return q('SELECT type, title, body, ref_type, ref_id FROM notifications WHERE user_id = %s', (uid,))


@pytest.fixture
def thu(monkeypatch):
    from notifications import gui as mo_dun
    da_gui = []
    monkeypatch.setattr(mo_dun, 'GUI_NGAY', True)
    monkeypatch.setattr(mo_dun.mail, 'gui', lambda den, tieu_de, chu: (da_gui.append((den, tieu_de, chu)) or (True, 'x', None)))
    return da_gui


def test_chuong_moi_nguoi_mot_lan(thu):
    from notifications.gui import gui
    a, b = _nguoi(), _nguoi()
    assert gui([a, b, a, None], 'thu_nghiem', 'Tiêu đề', 'Nội dung', ref=('yeu_cau', 7)) == 2
    for uid in (a, b):
        assert _chuong(uid) == [{'type': 'thu_nghiem', 'title': 'Tiêu đề', 'body': 'Nội dung',
                                 'ref_type': 'yeu_cau', 'ref_id': 7}]
    assert thu == [], 'không xin email thì không gửi thư'


def test_thu_chi_toi_nguoi_bat_email(thu):
    from notifications.gui import gui
    mac_dinh, tat, bat = _nguoi(), _nguoi(nhan_thu=0), _nguoi(nhan_thu=1)
    assert gui([mac_dinh, tat, bat], 'thu_nghiem', 'Lớp A: có tin', 'Chi tiết', email=True) == 3
    nhan = {den for den, _, _ in thu}
    email = {r['id']: r['email'] for r in q('SELECT id, email FROM users WHERE id = ANY(%s)', ([mac_dinh, tat, bat],))}
    assert nhan == {email[mac_dinh], email[bat]}, 'tắt email thì chỉ có chuông'
    assert len(_chuong(tat)) == 1
    assert all(t == 'Lớp A: có tin' and c.startswith('Chi tiết') for _, t, c in thu)


def test_loi_khong_chan_viec_chinh(monkeypatch):
    from notifications import gui as mo_dun

    def hong(*a, **k):
        raise RuntimeError('CSDL đứt')
    monkeypatch.setattr(mo_dun, 'notify', hong)
    assert mo_dun.gui([_nguoi()], 'thu_nghiem', 'T', 'N') == 0


def test_sau_commit_chi_bao_khi_giao_dich_xong(thu, django_capture_on_commit_callbacks):
    from notifications.gui import gui_sau_commit
    a = _nguoi()
    with django_capture_on_commit_callbacks(execute=False) as cho:
        gui_sau_commit([a], 'thu_nghiem', 'T', 'N')
    assert _chuong(a) == [], 'chưa commit thì chưa báo'
    for f in cho:
        f()
    assert len(_chuong(a)) == 1
