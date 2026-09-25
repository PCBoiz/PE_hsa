"""HỘP THƯ ĐI (§61a, E2) — `notifications/hop_thu.py`.

Phần lớn chạy trong giao dịch cuộn lại (conftest.py). Riêng hai phép kiểm "hai máy nhận
việc" cần HAI kết nối thật cùng thấy dòng đã commit: chúng mở kết nối psycopg riêng tới
CSDL trong `DATABASE_URL`, ghi dòng mang dấu riêng rồi tự xoá ở `finally`.
Thư không gửi thật: `mail.gui` / `zalo.gui_zns` bị thay bằng bản giả.
"""
import os
import threading
import uuid

import psycopg
import pytest

from common.db import q1, x

pytestmark = pytest.mark.django_db


@pytest.fixture
def thu(monkeypatch):
    """Email đã cấu hình; `mail.gui` giả, trả lần lượt kết quả trong `ket` (mặc định: thành công)."""
    from common import mail
    da_gui, ket = [], []
    monkeypatch.setattr(mail, 'da_cau_hinh', lambda: True)
    monkeypatch.setattr(mail, 'che_do_thu', lambda: False)

    def gia(den, tieu_de, chu, html=None, dinh_kem=()):
        da_gui.append({'den': den, 'tieuDe': tieu_de, 'chu': chu, 'html': html})
        return ket.pop(0) if ket else (True, '<gia-%d>' % len(da_gui), None)
    monkeypatch.setattr(mail, 'gui', gia)
    return {'da_gui': da_gui, 'ket': ket}


def _dong(oid):
    return q1('SELECT * FROM outbox WHERE id = %s', (oid,))


def _den_han(oid):
    """Đưa việc về 'tới lượt' ngay — thay cho chờ hết khoảng lùi."""
    x("UPDATE outbox SET next_try_at = now() - interval '1 second' WHERE id = %s", (oid,))


def test_xep_cung_dedup_chi_mot_dong():
    from notifications.hop_thu import xep
    k = 'kiem_thu:%s' % uuid.uuid4().hex
    a = xep('email', 'a@example.com', 'T', 'N', dedup=k)
    b = xep('email', 'a@example.com', 'T', 'N', dedup=k)
    assert a and b is None
    assert q1('SELECT count(*) AS n FROM outbox WHERE dedup_key = %s', (k,))['n'] == 1


def test_gui_thanh_cong_thi_sent(thu):
    from notifications.hop_thu import gui_ngay, xep
    oid = xep('email', 'a@example.com', 'Tiêu đề', 'Thân')
    kq = gui_ngay([oid])
    d = _dong(oid)
    assert kq[oid][0] == 'sent' and d['status'] == 'sent' and d['attempts'] == 1
    assert d['provider_id'] == '<gia-1>' and d['sent_at'] is not None and d['error'] is None
    assert thu['da_gui'] == [{'den': 'a@example.com', 'tieuDe': 'Tiêu đề', 'chu': 'Thân', 'html': None}]


def test_loi_thi_lui_1_5_30_120_360_phut_roi_bo(thu):
    from notifications.hop_thu import BACKOFF_PHUT, gui_ngay, xep
    assert BACKOFF_PHUT == (1, 5, 30, 120, 360)
    oid = xep('email', 'a@example.com', 'T', 'N')
    for i, phut in enumerate(BACKOFF_PHUT):
        thu['ket'].append((False, None, 'SMTP sập lần %d' % (i + 1)))
        gui_ngay([oid])
        d = q1("SELECT status, attempts, error, "
               "round(extract(epoch FROM next_try_at - now()) / 60) AS phut FROM outbox WHERE id = %s", (oid,))
        assert (d['status'], d['attempts'], int(d['phut'])) == ('failed', i + 1, phut), d
        assert d['error'] == 'SMTP sập lần %d' % (i + 1)
        _den_han(oid)
    thu['ket'].append((False, None, 'SMTP sập lần cuối'))
    gui_ngay([oid])
    d = _dong(oid)
    assert (d['status'], d['attempts']) == ('dropped', len(BACKOFF_PHUT) + 1)


def test_chua_toi_han_thi_khong_nhan(thu):
    from notifications.hop_thu import gui_ngay, xep
    oid = xep('email', 'a@example.com', 'T', 'N')
    thu['ket'].append((False, None, 'tạm hỏng'))
    gui_ngay([oid])
    assert gui_ngay([oid]) == {}, 'việc đang chờ lùi 1 phút mà vẫn bị nhận lại'
    assert len(thu['da_gui']) == 1


def test_dia_chi_hong_bo_ngay_khong_thu_lai(thu):
    from notifications.hop_thu import gui_ngay, xep
    oid = xep('email', 'khong-phai-email', 'T', 'N')
    gui_ngay([oid])
    d = _dong(oid)
    assert d['status'] == 'dropped' and d['error'] and thu['da_gui'] == []


def test_email_chua_cau_hinh_thi_bo_kem_ly_do(monkeypatch):
    from common import mail
    from notifications.hop_thu import gui_ngay, xep
    monkeypatch.setattr(mail, 'da_cau_hinh', lambda: False)
    monkeypatch.setattr(mail, 'che_do_thu', lambda: False)
    oid = xep('email', 'a@example.com', 'T', 'N')
    gui_ngay([oid])
    d = _dong(oid)
    assert d['status'] == 'dropped' and 'cấu hình' in d['error']


def test_zalo_chua_co_OA_thi_bo_kem_ly_do(monkeypatch):
    from common import zalo
    from notifications.hop_thu import gui_ngay, xep
    goi = []
    monkeypatch.setattr(zalo, 'da_cau_hinh', lambda: False)
    monkeypatch.setattr(zalo, 'che_do_thu', lambda: False)
    monkeypatch.setattr(zalo, 'gui_zns', lambda *a: goi.append(a) or (True, 'x', None))
    oid = xep('zalo', '0900000000', params={'zns': {'ten': 'A'}})
    gui_ngay([oid])
    d = _dong(oid)
    assert d['status'] == 'dropped' and 'Zalo' in d['error'] and goi == []


def test_zalo_co_OA_thi_gui_tham_so_mau(monkeypatch):
    from common import zalo
    from notifications.hop_thu import gui_ngay, xep
    goi = []
    monkeypatch.setattr(zalo, 'da_cau_hinh', lambda: True)
    monkeypatch.setattr(zalo, 'che_do_thu', lambda: False)
    monkeypatch.setattr(zalo, 'gui_zns', lambda so, ts: goi.append((so, ts)) or (True, 'msg-1', None))
    oid = xep('zalo', '0900000000', params={'zns': {'ten': 'A'}})
    gui_ngay([oid])
    assert _dong(oid)['status'] == 'sent' and goi == [('0900000000', {'ten': 'A'})]


def test_viec_treo_qua_10_phut_duoc_nhan_lai(thu):
    from notifications.hop_thu import TREO_PHUT, gui_ngay, xep
    assert TREO_PHUT == 10
    treo, moi_nhan = xep('email', 'a@example.com', 'T', 'N'), xep('email', 'b@example.com', 'T', 'N')
    x("UPDATE outbox SET status='sending', attempts=1, claimed_at = now() - interval '11 minutes' WHERE id=%s",
      (treo,))
    x("UPDATE outbox SET status='sending', attempts=1, claimed_at = now() - interval '5 minutes' WHERE id=%s",
      (moi_nhan,))
    kq = gui_ngay([treo, moi_nhan])
    assert set(kq) == {treo}, 'việc treo phải được nhận lại, việc vừa nhận thì không'
    assert _dong(treo)['status'] == 'sent' and _dong(moi_nhan)['status'] == 'sending'


def test_than_co_chia_bi_xoa_sau_khi_gui(thu):
    from notifications.hop_thu import gui_ngay, xep
    oid = xep('email', 'a@example.com', 'Đặt lại', 'link #chia=BI-MAT',
              params={'html': '<a href="#chia=BI-MAT">x</a>', 'xoa_than': True})
    gui_ngay([oid])
    d = _dong(oid)
    assert d['status'] == 'sent' and d['body'] == '' and 'html' not in d['params']
    assert thu['da_gui'][0]['html'] and 'BI-MAT' in thu['da_gui'][0]['chu']
    assert not q1("SELECT 1 AS c FROM outbox WHERE id=%s AND (body LIKE '%%BI-MAT%%' OR params::text LIKE '%%BI-MAT%%')",
                  (oid,))


def test_qua_han_thi_bo_va_xoa_than(thu):
    from datetime import timedelta

    from django.utils import timezone

    from notifications.hop_thu import gui_ngay, xep
    oid = xep('email', 'a@example.com', 'Đặt lại', 'link #chia=CU',
              params={'xoa_than': True, 'het_han': (timezone.now() - timedelta(minutes=1)).isoformat()})
    gui_ngay([oid])
    d = _dong(oid)
    assert d['status'] == 'dropped' and d['body'] == '' and thu['da_gui'] == []


# ── Hai máy nhận việc (kết nối thật, dữ liệu commit rồi tự xoá) ─────────────

def _ket_noi():
    return psycopg.connect(os.environ['DATABASE_URL'])


@pytest.fixture
def dong_that():
    """30 dòng outbox ĐÃ COMMIT, mang `source_type` riêng; xoá sạch sau phép kiểm."""
    dau = 'kiem_thu_nhan_%s' % uuid.uuid4().hex[:10]
    with _ket_noi() as c:
        ids = [r[0] for r in c.execute(
            "INSERT INTO outbox (channel, to_addr, source_type) "
            "SELECT 'email', 'a@example.com', %s FROM generate_series(1, 30) RETURNING id", (dau,)).fetchall()]
    try:
        yield ids
    finally:
        with _ket_noi() as c:
            c.execute('DELETE FROM outbox WHERE source_type = %s', (dau,))


def _nhan(conn, ids, n=20):
    from notifications.hop_thu import CAU_NHAN, TREO_PHUT
    return [r[0] for r in conn.execute(CAU_NHAN, {'n': n, 'ids': ids, 'treo': TREO_PHUT}).fetchall()]


def test_hai_may_nhan_viec_khong_trung_dong(dong_that):
    """Máy A nhận nhưng CHƯA commit (đang giữ khoá dòng) → máy B bỏ qua đúng các dòng ấy
    và nhận phần còn lại; A commit xong B hỏi lại cũng không nhận lại dòng của A."""
    a, b = _ket_noi(), _ket_noi()
    try:
        cua_a = _nhan(a, dong_that)                  # giao dịch A còn mở
        cua_b = _nhan(b, dong_that)
        b.commit()
        assert len(cua_a) == 20 and len(cua_b) == 10
        assert not set(cua_a) & set(cua_b)
        a.commit()
        assert _nhan(b, dong_that) == []
        b.commit()
    finally:
        a.close()
        b.close()


def test_nhieu_luong_nhan_cung_luc_khong_dong_nao_hai_lan(dong_that):
    nhan, loi = [], []

    def may():
        try:
            with _ket_noi() as c:
                while True:
                    ds = _nhan(c, dong_that, n=3)
                    c.commit()
                    if not ds:
                        return
                    nhan.extend(ds)
        except Exception as e:     # noqa: BLE001
            loi.append(e)
    ts = [threading.Thread(target=may) for _ in range(4)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(60)
    assert not loi, loi
    assert sorted(nhan) == sorted(dong_that), 'có dòng bị nhận hai lần hoặc bị sót'


# ── Cửa cho máy gọi ngoài + lệnh ────────────────────────────────────────────

def test_tick_tat_khi_chua_dat_khoa(api, monkeypatch):
    monkeypatch.delenv('OUTBOX_TICK_SECRET', raising=False)
    assert api.post('/api/noi-bo/tick').status_code == 404


def test_tick_sai_khoa_403_dung_khoa_chay(api, monkeypatch, thu):
    from notifications.hop_thu import xep
    monkeypatch.setenv('OUTBOX_TICK_SECRET', 'k' * 40)
    assert api.post('/api/noi-bo/tick', HTTP_X_TICK_KEY='sai').status_code == 403
    assert api.post('/api/noi-bo/tick').status_code == 403
    oid = xep('email', 'a@example.com', 'T', 'N')
    # Thẻ đăng nhập rác không làm 401: cửa này không xác thực người dùng.
    r = api.post('/api/noi-bo/tick', HTTP_X_TICK_KEY='k' * 40, HTTP_AUTHORIZATION='Bearer rac')
    assert r.status_code == 200, r.content
    assert r.json()['sent'] >= 1 and _dong(oid)['status'] == 'sent'


def test_tick_co_gioi_han_toc_do(api, monkeypatch):
    from notifications.views_hop_thu import TickThrottle
    monkeypatch.setenv('OUTBOX_TICK_SECRET', 'k' * 40)
    monkeypatch.setattr(TickThrottle, 'rate', '2/min')
    ma = [api.post('/api/noi-bo/tick', HTTP_X_TICK_KEY='k' * 40).status_code for _ in range(3)]
    assert ma == [200, 200, 429]


def test_lenh_gui_hop_thu(thu):
    from django.core.management import call_command

    from notifications.hop_thu import xep
    oid = xep('email', 'a@example.com', 'T', 'N')
    call_command('gui_hop_thu')
    assert _dong(oid)['status'] == 'sent'


def test_luong_nen_chi_bat_khi_co_ENABLE_OUTBOX(monkeypatch):
    from notifications import hop_thu
    bat = []
    monkeypatch.setattr(hop_thu, '_bat_luong', lambda: bat.append(1))
    monkeypatch.delenv('ENABLE_OUTBOX', raising=False)
    hop_thu.bat_luong_nen_neu_duoc()
    monkeypatch.setenv('ENABLE_OUTBOX', '1')
    hop_thu.bat_luong_nen_neu_duoc()
    assert bat == [1]


def test_q_khong_dung_khoa_tu_van():
    """Neon đi qua pooler: không advisory lock ở bất cứ đâu trong hộp thư đi."""
    import inspect

    from notifications import hop_thu
    assert 'pg_advisory' not in inspect.getsource(hop_thu).lower()
