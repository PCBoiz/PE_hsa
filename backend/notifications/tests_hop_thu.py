"""HỘP THƯ ĐI (§61a, E2) — `notifications/hop_thu.py`.

Phần lớn chạy trong giao dịch cuộn lại (conftest.py). Riêng hai phép kiểm "hai máy nhận
việc" cần HAI kết nối thật cùng thấy dòng đã commit: chúng mở kết nối psycopg riêng tới
CSDL trong `DATABASE_URL`, ghi dòng mang dấu riêng rồi tự xoá ở `finally`.
Thư không gửi thật: `mail.gui` / `zalo.gui_zns` bị thay bằng bản giả.
"""
import json
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
    # `mail.gui` PHẢI là bản giả (sửa 26/09/2026). Bản đầu chỉ vá `da_cau_hinh` và
    # `che_do_thu` — hai cờ mà `mail.gui` KHÔNG hỏi lại: nó tự đọc biến môi trường. Đo trên
    # máy dev 26/09: `da_cau_hinh()` thật = True, `che_do_thu()` thật = False, nên lời gọi
    # đi TRỌN tới Gmail và phép kiểm này là chỗ DUY NHẤT trong repo mở kết nối SMTP thật.
    # Nó đỏ ('sent' thay vì 'dropped') đúng vì lá thư đã gửi được. Bản giả trả về đúng thứ
    # `mail.gui` thật trả khi thiếu thông số.
    monkeypatch.setattr(mail, 'gui', lambda *a, **k: (False, None, 'Chưa cấu hình email (EMAIL_USER).'))
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
    # Hàng rào thư máy dev (26/09/2026) chặn ZNS theo SỐ: cho đúng số của phép kiểm vào
    # danh sách, để phép kiểm này vẫn đo đường gửi thật chứ không đo hàng rào.
    monkeypatch.setenv('OUTBOX_SO_CHO_PHEP', '0900000000')
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
    assert d['status'] == 'sent' and d['body'] == '' and 'html' not in json.loads(d['params'])
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


def _nhan(conn, ids, n=20, uu_tien=None):
    from notifications.hop_thu import CAU_NHAN, GIAO_DICH, TREO_PHUT
    return [r[0] for r in conn.execute(
        CAU_NHAN, {'n': n, 'ids': ids, 'treo': TREO_PHUT,
                   'uu_tien': GIAO_DICH if uu_tien is None else uu_tien}).fetchall()]


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


# ── ƯU TIÊN + TRẦN NGÀY (quyết định 4 của anh Sơn, 26/09/2026) ──────────────

@pytest.fixture
def khong_hang_rao(monkeypatch):
    """Tắt hàng rào thư máy dev cho các phép kiểm về ƯU TIÊN — hai việc khác nhau, một
    phép kiểm chỉ đo một việc. (Hàng rào có bộ riêng: `tests_hang_rao_thu.py`.)"""
    from notifications import hang_rao_thu
    monkeypatch.setattr(hang_rao_thu, 'bat', lambda: False)


def _xep(uu_tien, den='a@example.com'):
    from notifications.hop_thu import xep
    return xep('email', den, 'T', 'N', uu_tien=uu_tien, dedup='ut:%s' % uuid.uuid4().hex)


def test_xep_mac_dinh_la_thu_giao_dich():
    from notifications.hop_thu import GIAO_DICH, xep
    oid = xep('email', 'a@example.com', 'T', 'N')
    assert _dong(oid)['priority'] == GIAO_DICH, 'không khai thì là thư một người đang chờ'


def test_thu_giao_dich_nhan_truoc_thu_hang_loat(khong_hang_rao, thu):
    """Một lượt chỉ nhận được 1 việc: phải là việc GIAO DỊCH, dù nó xếp SAU."""
    from notifications.hop_thu import GIAO_DICH, HANG_LOAT, nhan_viec
    hl = _xep(HANG_LOAT)
    x("UPDATE outbox SET next_try_at = now() - interval '5 minutes' WHERE id = %s", (hl,))
    gd = _xep(GIAO_DICH)
    ds = nhan_viec(1, ids=[hl, gd])
    assert [d['id'] for d in ds] == [gd], 'thư quên mật khẩu không được chờ sau thư cả khối'


def test_mot_luot_lay_du_thi_lay_ca_hai_loai(khong_hang_rao, thu):
    from notifications.hop_thu import GIAO_DICH, HANG_LOAT, nhan_viec
    ids = [_xep(HANG_LOAT), _xep(GIAO_DICH)]
    ds = nhan_viec(20, ids=ids)
    assert sorted(d['id'] for d in ds) == sorted(ids)
    assert [d['priority'] for d in ds] == [GIAO_DICH, HANG_LOAT], 'giao dịch đứng trước trong lượt'


def _da_gui_hang_loat_hom_nay(n):
    """Ghi `n` dòng hàng loạt ĐÃ GỬI hôm nay (giờ VN) để ăn hết trần."""
    from notifications.hop_thu import HANG_LOAT
    for _ in range(n):
        x('''INSERT INTO outbox (channel, to_addr, priority, status, sent_at, dedup_key)
             VALUES ('email', 'x@example.com', %s, 'sent', now(), %s)''',
          (HANG_LOAT, 'tran:%s' % uuid.uuid4().hex))


def test_tran_ngay_het_thi_thu_hang_loat_NAM_LAI_queued(khong_hang_rao, thu, monkeypatch):
    from notifications.hop_thu import BIEN_TRAN, HANG_LOAT, gui_het
    monkeypatch.setenv(BIEN_TRAN, '2')
    _da_gui_hang_loat_hom_nay(2)
    oid = _xep(HANG_LOAT)
    gui_het()
    d = _dong(oid)
    assert d['status'] == 'queued', 'vượt trần thì CHỜ sang ngày sau, không bỏ'
    assert d['attempts'] == 0 and d['error'] is None and thu['da_gui'] == []


def test_tran_ngay_khong_chan_thu_giao_dich(khong_hang_rao, thu, monkeypatch):
    from notifications.hop_thu import BIEN_TRAN, GIAO_DICH, gui_het
    monkeypatch.setenv(BIEN_TRAN, '0')
    oid = _xep(GIAO_DICH)
    gui_het()
    assert _dong(oid)['status'] == 'sent', 'trần chỉ chặn thư hàng loạt'


def test_tran_0_thi_khong_thu_hang_loat_nao_di(khong_hang_rao, thu, monkeypatch):
    from notifications.hop_thu import BIEN_TRAN, HANG_LOAT, con_lai_hang_loat, gui_het
    monkeypatch.setenv(BIEN_TRAN, '0')
    assert con_lai_hang_loat() == 0
    oid = _xep(HANG_LOAT)
    gui_het()
    assert _dong(oid)['status'] == 'queued' and thu['da_gui'] == []


def test_con_lai_hang_loat_tru_dan_va_khong_am(khong_hang_rao, monkeypatch):
    from notifications.hop_thu import BIEN_TRAN, con_lai_hang_loat
    monkeypatch.setenv(BIEN_TRAN, '3')
    dau = con_lai_hang_loat()
    _da_gui_hang_loat_hom_nay(1)
    assert con_lai_hang_loat() == max(0, dau - 1)
    _da_gui_hang_loat_hom_nay(10)
    assert con_lai_hang_loat() == 0, 'không bao giờ âm'


def test_con_lai_hang_loat_dem_theo_NGAY_GIO_VIET_NAM(khong_hang_rao, monkeypatch):
    """Ranh giới ngày là 0h giờ VN, không phải 0h UTC — `sent_at` ghi theo đồng hồ phiên
    (UTC), nên một dòng gửi 22h VN hôm qua (15h UTC hôm qua) KHÔNG được tính vào hôm nay,
    còn dòng gửi 1h VN hôm nay (18h UTC hôm qua) THÌ CÓ."""
    from notifications.hop_thu import BIEN_TRAN, DAU_NGAY_VN, HANG_LOAT, con_lai_hang_loat
    monkeypatch.setenv(BIEN_TRAN, '100')
    dau = con_lai_hang_loat()
    for lech in ("- interval '1 hour'", "+ interval '1 hour'"):
        x('''INSERT INTO outbox (channel, to_addr, priority, status, sent_at, dedup_key)
             VALUES ('email', 'x@example.com', %%s, 'sent', %s %s, %%s)''' % (DAU_NGAY_VN, lech),
          (HANG_LOAT, 'ranh:%s' % uuid.uuid4().hex))
    assert con_lai_hang_loat() == dau - 1, 'chỉ dòng SAU 0h VN mới tính vào hôm nay'


def test_tran_bien_hong_thi_dung_mac_dinh(monkeypatch):
    from notifications.hop_thu import BIEN_TRAN, TRAN_HANG_LOAT_MAC_DINH, tran_hang_loat
    monkeypatch.delenv(BIEN_TRAN, raising=False)
    assert tran_hang_loat() == TRAN_HANG_LOAT_MAC_DINH
    for xau in ('ba tram', '', '-5'):
        monkeypatch.setenv(BIEN_TRAN, xau)
        assert tran_hang_loat() == TRAN_HANG_LOAT_MAC_DINH, xau
    monkeypatch.setenv(BIEN_TRAN, '7')
    assert tran_hang_loat() == 7


def test_thong_bao_trung_tam_va_nhac_han_la_thu_HANG_LOAT():
    """Đường nào xếp thư cả lớp thì phải đánh dấu hàng loạt — đọc mã, không đoán."""
    import inspect

    from notifications import gui as mat_tien
    from notifications import nhac_han, thong_bao
    for m in (thong_bao, nhac_han):
        ma = inspect.getsource(m)
        assert 'uu_tien' in ma and 'HANG_LOAT' in ma, m.__name__
    assert 'HANG_LOAT if len(ids)' in inspect.getsource(mat_tien.xep_thu) \
        or 'len(ids) <= 1' in inspect.getsource(mat_tien.xep_thu)
