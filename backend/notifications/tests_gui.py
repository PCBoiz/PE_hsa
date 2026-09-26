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


# ── Từ E2 (§61): thư vào HỘP THƯ ĐI trong cùng giao dịch với chuông ─────────

def _hop_thu(uid):
    return q("SELECT channel, to_addr, subject, body, status, dedup_key FROM outbox WHERE user_id = %s", (uid,))


def test_thu_nam_trong_hop_thu_di_khi_khong_gui_ngay(django_capture_on_commit_callbacks):
    """Không gửi ngay (đường thật): lời gọi chỉ GHI thư — chưa commit thì chưa đi đâu cả."""
    from notifications.gui import gui
    bat, tat = _nguoi(nhan_thu=1), _nguoi(nhan_thu=0)
    with django_capture_on_commit_callbacks(execute=False) as cho:
        assert gui([bat, tat], 'thu_nghiem', 'Tiêu đề', 'Nội dung', email=True) == 2
    thu = _hop_thu(bat)
    assert len(thu) == 1 and thu[0]['status'] == 'queued' and thu[0]['subject'] == 'Tiêu đề'
    assert thu[0]['body'].startswith('Nội dung')
    assert _hop_thu(tat) == [], 'tắt email thì chỉ có chuông'
    assert len(cho) == 1, 'phải hẹn một lượt gửi sau commit'


def test_tai_khoan_mau_khong_co_thu(thu):
    from notifications.gui import gui
    mau = _nguoi()
    x('UPDATE users SET is_demo = TRUE WHERE id = %s', (mau,))
    gui([mau], 'thu_nghiem', 'T', 'N', email=True)
    assert len(_chuong(mau)) == 1 and _hop_thu(mau) == [] and thu == []


def test_dedup_mot_thu_moi_nguoi(thu):
    from notifications.gui import gui
    a = _nguoi()
    gui([a], 'thu_nghiem', 'T', 'N', email=True, dedup='viec:1')
    gui([a], 'thu_nghiem', 'T', 'N', email=True, dedup='viec:1')
    assert [r['dedup_key'] for r in _hop_thu(a)] == ['viec:1:%d' % a]
    assert len(thu) == 1


def test_chuong_va_thu_cung_giao_dich(monkeypatch):
    """Hỏng giữa chừng thì không còn chuông nào, không còn thư nào (không nửa vời)."""
    from notifications import gui as mo_dun
    a, b = _nguoi(), _nguoi()
    that = mo_dun.notify
    lan = []

    def hong_lan_hai(*ar, **kw):
        lan.append(1)
        if len(lan) == 2:
            raise RuntimeError('CSDL đứt')
        return that(*ar, **kw)
    monkeypatch.setattr(mo_dun, 'notify', hong_lan_hai)
    assert mo_dun.gui([a, b], 'thu_nghiem', 'T', 'N', email=True) == 0
    assert _chuong(a) == [] and _hop_thu(a) == []


def test_link_gan_vao_chuong(thu):
    from notifications.gui import gui
    a = _nguoi()
    gui([a], 'thu_nghiem', 'T', 'N', link='/bai-tap')
    assert q1('SELECT link FROM notifications WHERE user_id = %s', (a,))['link'] == '/bai-tap'
