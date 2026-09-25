"""Tiến độ theo khung (`chuong_trinh/tien_do.py`) — luật ở docstring đầu tệp ấy."""
import pytest

from chuong_trinh.tien_do import danh_gia, tien_do_em, tien_do_lop


# ── Luật thuần: ngưỡng CHẬM ở biên ─────────────────────────────────────────────

def test_tre_dung_hai_buoi_la_CHAM():
    # 5 buổi khung trọng số 1: phải xong 4, xong 2 → trễ đúng 2 buổi (biên ≥).
    d = danh_gia(tong_w=5, so_buoi_khung=5, phai_w=4, xong_w=2)
    assert d['treBuoi'] == 2.0
    assert d['cham'] is True


def test_tre_duoi_hai_buoi_va_ti_le_du_80_la_KHONG_cham():
    # phải xong 5, xong 4 → trễ 1, tỉ lệ đúng 80 % (biên < 0,8 là chậm) → không chậm.
    d = danh_gia(tong_w=10, so_buoi_khung=10, phai_w=5, xong_w=4)
    assert d['tiLe'] == 80.0 and d['treBuoi'] == 1.0
    assert d['cham'] is False


def test_ti_le_75_ma_tre_duoi_hai_buoi_van_CHAM():
    # Chỉ vế tỉ lệ bắt được: trễ 1,25 buổi (< 2) nhưng 75 % < 80 %.
    d = danh_gia(tong_w=10, so_buoi_khung=10, phai_w=5, xong_w=3.75)
    assert d['treBuoi'] == 1.2 and d['tiLe'] == 75.0
    assert d['cham'] is True


def test_chua_toi_buoi_nao_thi_khong_cham_va_khong_chia_cho_0():
    d = danh_gia(tong_w=10, so_buoi_khung=10, phai_w=0, xong_w=0)
    assert d['cham'] is False and d['tiLe'] is None and d['keHoachPct'] == 0.0


def test_day_vuot_ke_hoach_tre_am():
    d = danh_gia(tong_w=10, so_buoi_khung=10, phai_w=2, xong_w=3)
    assert d['treBuoi'] == -1.0 and d['cham'] is False


# ── Trên CSDL ──────────────────────────────────────────────────────────────────

@pytest.fixture
def lop_4_buoi(dung):
    """Khung 4 buổi × 1 mục trọng số 2; lớp có 4 buổi đã gắn: 3 đã diễn ra, 1 tuần sau."""
    k = dung.khoa()
    b = dung.ban(k, [[2], [2], [2], [2]])
    lop = dung.lop(k, vid=b['id'])
    buoi = [dung.buoi(lop, ngay=-9 + 3 * i, ss=b['buoi'][i]) for i in range(3)]
    buoi.append(dung.buoi(lop, ngay=7, ss=b['buoi'][3]))
    return {'lop': lop, 'ban': b, 'buoi': buoi, 'khoa': k}


def test_phai_xong_la_buoi_khung_da_toi_da_xong_tinh_mot_phan_la_nua(dung, lop_4_buoi):
    L = lop_4_buoi
    dung.ghi_so(L['buoi'][0], [(L['ban']['muc'][0][0], 'done')])
    dung.ghi_so(L['buoi'][1], [(L['ban']['muc'][1][0], 'partial')])
    # buổi 3 đã dạy, CHƯA ghi sổ; buổi 4 chưa tới.
    d = tien_do_lop([L['lop']])[L['lop']]
    assert d['phaiXong'] == 6.0, 'ba buổi khung đã tới × trọng số 2'
    assert d['daXong'] == 3.0, 'đã dạy 2 + một phần (0,5 × 2) = 3'
    assert d['tongTrongSo'] == 8.0
    assert d['chuaGhiSo'] == 1 and d['buoiDaDay'] == 3
    assert d['treBuoi'] == 1.5 and d['cham'] is True, 'tỉ lệ 50 % < 80 %'


def test_muc_ghi_hai_buoi_lay_muc_cao_nhat_khong_cong_don(dung, lop_4_buoi):
    L = lop_4_buoi
    m = L['ban']['muc'][0][0]
    dung.ghi_so(L['buoi'][0], [(m, 'partial')])
    dung.ghi_so(L['buoi'][1], [(m, 'done')])
    assert tien_do_lop([L['lop']])[L['lop']]['daXong'] == 2.0


def test_buoi_huy_da_gan_van_la_phai_xong(dung, lop_4_buoi):
    L = lop_4_buoi
    from common.db import x
    x("UPDATE class_sessions SET status = 'cancelled' WHERE id = %s", (L['buoi'][2],))
    d = tien_do_lop([L['lop']])[L['lop']]
    assert d['phaiXong'] == 6.0, 'nội dung buổi huỷ chưa dạy — vẫn phải xong'
    assert d['buoiDaDay'] == 2, 'buổi huỷ không là buổi đã dạy'
    assert d['chuaGhiSo'] == 2


def test_lop_khong_co_khung_khong_co_khoa(dung):
    lop = dung.lop(dung.khoa())
    dung.buoi(lop, ngay=-1)
    assert tien_do_lop([lop]) == {}, 'lớp chưa nhận khung không bị tính (và không bị nhắc ghi sổ)'


def test_muc_cua_ban_khac_khong_tinh(dung, lop_4_buoi):
    L = lop_4_buoi
    khac = dung.ban(L['khoa'], [[5]])
    dung.ghi_so(L['buoi'][0], [(khac['muc'][0][0], 'done')])
    assert tien_do_lop([L['lop']])[L['lop']]['daXong'] == 0.0


def test_kem_buoi_chua_ghi_so(dung, lop_4_buoi):
    L = lop_4_buoi
    dung.ghi_so(L['buoi'][0], [])
    d = tien_do_lop([L['lop']], kem_buoi=True)[L['lop']]
    assert [b['sessionId'] for b in d['buoiChuaGhiSo']] == [L['buoi'][2], L['buoi'][1]]


def test_so_cau_truy_van_co_dinh_2_lop_va_20_lop(dung):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    k = dung.khoa()
    b = dung.ban(k, [[1], [1]])
    ids = []

    def them(n):
        for _ in range(n):
            lop = dung.lop(k, vid=b['id'])
            s = dung.buoi(lop, ngay=-1, ss=b['buoi'][0])
            dung.ghi_so(s, [(b['muc'][0][0], 'done')])
            ids.append(lop)

    them(2)
    with CaptureQueriesContext(connection) as hai:
        tien_do_lop(ids, kem_buoi=True)
    them(18)
    with CaptureQueriesContext(connection) as hai_muoi:
        d = tien_do_lop(ids, kem_buoi=True)
    assert len(d) == 20
    assert len(hai) == len(hai_muoi) == 2, (len(hai), len(hai_muoi))


# ── % của một em ───────────────────────────────────────────────────────────────

def test_pct_cua_em_chi_tinh_buoi_co_mat_hoac_muon(dung, lop_4_buoi):
    L = lop_4_buoi
    em = dung.nguoi()
    dung.vao(L['lop'], em)
    for i in range(3):
        dung.ghi_so(L['buoi'][i], [(L['ban']['muc'][i][0], 'done')])
    dung.diem_danh(L['buoi'][0], em, 'present')
    dung.diem_danh(L['buoi'][1], em, 'late')
    dung.diem_danh(L['buoi'][2], em, 'absent')
    d = tien_do_em(em, [L['lop']])[L['lop']]
    assert d['daXong'] == 4.0, 'có mặt + muộn = 2 buổi × 2; buổi vắng không tính'
    assert d['pct'] == 50.0 and d['keHoachPct'] == 75.0


def test_pct_cua_em_co_phep_khong_tinh(dung, lop_4_buoi):
    L = lop_4_buoi
    em = dung.nguoi()
    dung.vao(L['lop'], em)
    dung.ghi_so(L['buoi'][0], [(L['ban']['muc'][0][0], 'done')])
    dung.diem_danh(L['buoi'][0], em, 'excused')
    assert tien_do_em(em, [L['lop']])[L['lop']]['daXong'] == 0.0


def test_buoi_bu_tinh_cho_buoi_goc(dung, lop_4_buoi):
    """Em vắng buổi gốc, có mặt ở buổi bù của nó → được tính phần sổ của buổi gốc."""
    L = lop_4_buoi
    em = dung.nguoi()
    dung.vao(L['lop'], em)
    dung.ghi_so(L['buoi'][0], [(L['ban']['muc'][0][0], 'done')])
    dung.diem_danh(L['buoi'][0], em, 'absent')
    bu = dung.buoi(L['lop'], ngay=-2, makeup_for=L['buoi'][0])
    dung.diem_danh(bu, em, 'present')
    assert tien_do_em(em, [L['lop']])[L['lop']]['daXong'] == 2.0
