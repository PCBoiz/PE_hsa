"""Hộp Yêu cầu (E3, §65) — phạm vi từng vai, máy trạng thái, duyệt = thực thi, link phụ huynh.

Đi qua VIEW THẬT (APIClient); CSDL trong giao dịch cuộn lại cuối mỗi phép kiểm.
"""
import json

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.db import q, q1, x
from yeu_cau import loai as L

pytestmark = pytest.mark.django_db


def _tao(c, body, duong='/api/yeu-cau'):
    return c.post(duong, body, format='json')


def _check(ten):
    r = q1("SELECT pg_get_constraintdef(oid) AS d FROM pg_constraint WHERE conname = %s", (ten,))
    import re
    return set(re.findall(r"'([a-z_]+)'::text", r['d']))


# ── Danh mục = CHECK ────────────────────────────────────────────────────────

def test_danh_muc_khop_check():
    assert _check('yeu_cau_loai_check') == set(L.LOAI)
    assert _check('yeu_cau_trang_thai_check') == set(L.TRANG_THAI)
    assert _check('yeu_cau_nguon_check') == set(L.NGUON)
    assert _check('yeu_cau_su_kien_kieu_check') == set(L.KIEU_SU_KIEN)
    assert set(L.NHAN_TRANG_THAI) == set(L.TRANG_THAI)
    for nguon, ds in L.TAO_DUOC.items():
        assert nguon in L.NGUON and set(ds) <= set(L.LOAI)


def test_bang_chuyen_chi_duyet_moi_toi_da_duyet():
    for (tu, den) in L.CHUYEN:
        for loai in L.LOAI:
            ai = L.ai_duoc_chuyen(loai, tu, den)
            if den == 'da_duyet' and ai is not None:
                assert L.la_thay_doi(loai) and ai == L.DUYET
            if ai == L.NGUOI_TAO:
                assert (tu, den) == ('moi', 'da_huy')
    # Loại thay đổi đã duyệt không mở lại được; loại hỗ trợ thì được.
    assert L.ai_duoc_chuyen('tt_chuyen_lop', 'da_xong', 'dang_xu_ly') is None
    assert L.ai_duoc_chuyen('ht_hoc_tap', 'da_xong', 'dang_xu_ly') == L.NHAN_SU
    assert L.ai_duoc_chuyen('tt_bao_luu', 'moi', 'tu_choi') == L.DUYET
    assert L.ai_duoc_chuyen('ht_hoc_tap', 'moi', 'tu_choi') == L.NHAN_SU


# ── Phạm vi ────────────────────────────────────────────────────────────────

def test_hoi_dap_toi_gv_lop_minh_khong_toi_gv_lop_khac(d, canh):
    hs = d.api(canh['em'])
    r = _tao(hs, {'loai': 'hoi_dap', 'tieu_de': 'Câu 5 bài tập', 'noi_dung': 'Em chưa hiểu'})
    assert r.status_code == 201, r.data
    yid = r.data['id']
    assert r.data['lop']['id'] == canh['a'], 'em học đúng một lớp thì tự gắn lớp ấy'
    gv, tg, gv_b = d.api(canh['gv']), d.api(canh['tg']), d.api(canh['gv_b'])
    assert gv.get('/api/teach/yeu-cau/%d' % yid).status_code == 200
    assert tg.get('/api/teach/yeu-cau/%d' % yid).status_code == 200
    assert gv_b.get('/api/teach/yeu-cau/%d' % yid).status_code == 404
    assert yid not in [y['id'] for y in gv_b.get('/api/teach/yeu-cau').data['yeuCau']]
    assert yid in [y['id'] for y in gv.get('/api/teach/yeu-cau').data['yeuCau']]
    # Gửi câu hỏi vào lớp em không học → 404 (không lộ lớp có tồn tại).
    r = _tao(hs, {'loai': 'hoi_dap', 'tieu_de': 'x', 'class_id': canh['b']})
    assert r.status_code == 404, r.data
    # Em khác cùng lớp: ngoài phạm vi → 404, không lộ yêu cầu có tồn tại.
    assert d.api(canh['em2']).get('/api/yeu-cau/%d' % yid).status_code == 404


def test_hoc_vien_khong_thay_ghi_chu_noi_bo(d, canh):
    hs = d.api(canh['em'])
    yid = _tao(hs, {'loai': 'ht_hoc_tap', 'tieu_de': 'Xin tài liệu'}).data['id']
    hv = d.api(canh['hv'])
    r = hv.post('/api/teach/yeu-cau/%d/tra-loi' % yid, {'noi_dung': 'Em này hay xin muộn', 'noi_bo': True},
                format='json')
    assert r.status_code == 200, r.data
    r = hv.post('/api/teach/yeu-cau/%d/tra-loi' % yid, {'noi_dung': 'Đã gửi tài liệu qua email'}, format='json')
    assert r.data['trangThai'] == 'dang_xu_ly', 'nhân sự trả lời = đã nhận việc'
    nhan_su = [s['noiDung'] for s in hv.get('/api/teach/yeu-cau/%d' % yid).data['suKien']]
    assert 'Em này hay xin muộn' in nhan_su
    hoc_vien = hs.get('/api/yeu-cau/%d' % yid).data
    chu = [s['noiDung'] for s in hoc_vien['suKien']]
    assert 'Đã gửi tài liệu qua email' in chu and 'Em này hay xin muộn' not in chu
    assert not any(s['noiBo'] for s in hoc_vien['suKien'])
    # Học viên không tự ghi được ghi chú nội bộ (đường học viên bỏ qua cờ noi_bo).
    r = hs.post('/api/yeu-cau/%d/tra-loi' % yid, {'noi_dung': 'Cảm ơn', 'noi_bo': True}, format='json')
    assert r.status_code == 200, r.data
    assert [s['noiDung'] for s in r.data['suKien']][-1] == 'Cảm ơn'
    assert not q1('SELECT 1 AS c FROM yeu_cau_su_kien WHERE yeu_cau_id=%s AND noi_bo AND actor_id=%s',
                  (yid, canh['em']))


def test_gv_tg_khong_thay_ho_tro_tai_khoan(d, canh):
    hs = d.api(canh['em'])
    yid = _tao(hs, {'loai': 'ht_tai_khoan', 'tieu_de': 'Quên mật khẩu', 'class_id': canh['a']}).data['id']
    for ai in (canh['gv'], canh['tg']):
        c = d.api(ai)
        assert c.get('/api/teach/yeu-cau/%d' % yid).status_code == 404
        assert yid not in [y['id'] for y in c.get('/api/teach/yeu-cau').data['yeuCau']]
    hv = d.api(canh['hv'])
    assert hv.get('/api/teach/yeu-cau/%d' % yid).status_code == 200
    r = hv.post('/api/admin/yeu-cau/%d/giao' % yid, {'nguoi_xu_ly_id': canh['gv']}, format='json')
    assert r.status_code == 400, 'hỗ trợ tài khoản không giao cho giảng viên được'
    assert d.api(canh['gv']).get('/api/teach/yeu-cau/%d' % yid).status_code == 404


def test_tro_giang_khong_thay_sdt_phu_huynh(d, canh):
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    r = APIClient().post('/api/public/phu-huynh/%s/yeu-cau' % tk,
                         {'loai': 'ht_lich_hoc', 'tieu_de': 'Hỏi lịch tuần sau',
                          'du_lieu': {'sdt': '0912345678'}}, format='json')
    assert r.status_code == 201, r.data
    yid = r.data['id']
    assert d.api(canh['gv']).get('/api/teach/yeu-cau/%d' % yid).data['duLieu'].get('sdt') == '0912345678'
    assert 'sdt' not in d.api(canh['tg']).get('/api/teach/yeu-cau/%d' % yid).data['duLieu']
    tg_ds = [y for y in d.api(canh['tg']).get('/api/teach/yeu-cau').data['yeuCau'] if y['id'] == yid]
    assert tg_ds and 'sdt' not in tg_ds[0]['duLieu']


def test_nhan_su_ngoai_duong_hoc_vien_403(d, canh):
    assert d.api(canh['gv']).get('/api/yeu-cau').status_code == 403
    assert d.api(canh['em']).get('/api/teach/yeu-cau').status_code == 403


def test_bao_loi_ban_ghi_bat_buoc_buoi(d, canh):
    hs = d.api(canh['em'])
    r = _tao(hs, {'loai': 'bao_loi_ban_ghi', 'tieu_de': 'Record không mở được', 'class_id': canh['a']})
    assert r.status_code == 400
    buoi = d.buoi(canh['a'])
    r = _tao(hs, {'loai': 'bao_loi_ban_ghi', 'tieu_de': 'Record không mở được', 'session_id': buoi})
    assert r.status_code == 201, r.data
    assert r.data['buoi']['id'] == buoi and r.data['lop']['id'] == canh['a']
    # Buổi của lớp em không học → 404.
    r = _tao(hs, {'loai': 'bao_loi_ban_ghi', 'tieu_de': 'x', 'session_id': d.buoi(canh['b'])})
    assert r.status_code == 404


def test_tro_giang_bao_len_giang_vien(d, canh):
    tg = d.api(canh['tg'])
    r = _tao(tg, {'loai': 'bao_cao_len', 'tieu_de': 'Em A không phản hồi', 'class_id': canh['a'],
                  'hoc_vien_id': canh['em']}, '/api/teach/yeu-cau')
    assert r.status_code == 201, r.data
    assert r.data['nguon'] == 'tro_giang'
    assert d.api(canh['gv']).get('/api/teach/yeu-cau/%d' % r.data['id']).status_code == 200
    # Lớp không phụ trách → 404.
    r = _tao(tg, {'loai': 'bao_cao_len', 'tieu_de': 'x', 'class_id': canh['b']}, '/api/teach/yeu-cau')
    assert r.status_code == 404


# ── Máy trạng thái ─────────────────────────────────────────────────────────

def test_rut_khi_con_moi_khong_rut_khi_da_nhan(d, canh):
    hs = d.api(canh['em'])
    y1 = _tao(hs, {'loai': 'ht_ky_thuat', 'tieu_de': 'Không vào được Zoom'}).data['id']
    r = hs.post('/api/yeu-cau/%d/huy' % y1)
    assert r.status_code == 200 and r.data['trangThai'] == 'da_huy' and r.data['closedAt']
    y2 = _tao(hs, {'loai': 'ht_ky_thuat', 'tieu_de': 'Mất tiếng'}).data['id']
    d.api(canh['hv']).post('/api/teach/yeu-cau/%d/trang-thai' % y2, {'den': 'dang_xu_ly'}, format='json')
    assert hs.post('/api/yeu-cau/%d/huy' % y2).status_code == 409
    # Mọi chuyển đều có dòng sự kiện.
    kieu = [r['kieu'] for r in q('SELECT kieu FROM yeu_cau_su_kien WHERE yeu_cau_id=%s ORDER BY id', (y1,))]
    assert kieu == ['tao', 'trang_thai']


def test_loai_thay_doi_khong_dong_xong_khi_chua_duyet(d, canh):
    hs = d.api(canh['em'])
    yid = _tao(hs, {'loai': 'tt_bao_luu', 'tieu_de': 'Xin bảo lưu 2 tháng'}).data['id']
    gv = d.api(canh['gv'])
    assert gv.post('/api/teach/yeu-cau/%d/trang-thai' % yid, {'den': 'da_xong'}, format='json').status_code == 409
    assert gv.post('/api/teach/yeu-cau/%d/trang-thai' % yid, {'den': 'tu_choi'}, format='json').status_code == 403
    assert gv.post('/api/teach/yeu-cau/%d/trang-thai' % yid, {'den': 'da_duyet'}, format='json').status_code == 400
    assert q1('SELECT trang_thai FROM yeu_cau WHERE id=%s', (yid,))['trang_thai'] == 'moi'


def test_ho_tro_xong_va_mo_lai(d, canh):
    yid = _tao(d.api(canh['em']), {'loai': 'ht_hoc_tap', 'tieu_de': 'x'}).data['id']
    hv = d.api(canh['hv'])
    r = hv.post('/api/teach/yeu-cau/%d/trang-thai' % yid, {'den': 'da_xong', 'ket_qua': 'Đã gọi em'},
                format='json')
    assert r.data['trangThai'] == 'da_xong' and r.data['ketQua'] == 'Đã gọi em'
    r = hv.post('/api/teach/yeu-cau/%d/trang-thai' % yid, {'den': 'dang_xu_ly'}, format='json')
    assert r.data['trangThai'] == 'dang_xu_ly' and r.data['closedAt'] is None


# ── Duyệt = thực thi ───────────────────────────────────────────────────────

def _xin(d, canh, loai, **them):
    body = dict({'loai': loai, 'tieu_de': 'Xin %s' % loai, 'class_id': canh['a']}, **them)
    r = _tao(d.api(canh['em']), body)
    assert r.status_code == 201, r.data
    return r.data['id']


def _luot(lop, em):
    return q('SELECT id, left_at, leave_reason, reserve_until, transferred_to FROM class_members '
             'WHERE class_id=%s AND user_id=%s ORDER BY id', (lop, em))


def test_tro_giang_giang_vien_duyet_403(d, canh):
    yid = _xin(d, canh, 'tt_chuyen_lop')
    for ai in (canh['tg'], canh['gv']):
        r = d.api(ai).post('/api/admin/yeu-cau/%d/duyet' % yid, {'den_lop_id': canh['b']}, format='json')
        assert r.status_code == 403
    assert _luot(canh['a'], canh['em'])[0]['left_at'] is None


def test_duyet_chuyen_lop_em_sang_lop_moi_ghi_nguoi_duyet(d, canh, django_capture_on_commit_callbacks):
    yid = _xin(d, canh, 'tt_chuyen_lop', du_lieu={'lop_mong_muon': 'Lớp tối thứ 3'})
    hv = d.api(canh['hv'])
    xt = hv.get('/api/admin/yeu-cau/%d/duyet' % yid, {'den_lop_id': canh['b']})
    assert xt.status_code == 200 and 'Chuyển' in xt.data['moTa'], xt.data
    assert _luot(canh['a'], canh['em'])[0]['left_at'] is None, 'xem trước không ghi gì'
    with django_capture_on_commit_callbacks(execute=True):
        r = hv.post('/api/admin/yeu-cau/%d/duyet' % yid, {'den_lop_id': canh['b']}, format='json')
    assert r.status_code == 200, r.data
    (cu,), (moi,) = _luot(canh['a'], canh['em']), _luot(canh['b'], canh['em'])
    assert cu['leave_reason'] == 'transferred' and cu['transferred_to'] == moi['id'] and moi['left_at'] is None
    y = q1('SELECT * FROM yeu_cau WHERE id=%s', (yid,))
    assert y['nguoi_duyet'] == canh['hv'] and y['duyet_luc'] is not None
    assert y['trang_thai'] == 'da_xong' and json.loads(y['thuc_thi'])['denLop'] == canh['b']
    kieu = [r['kieu'] for r in q('SELECT kieu FROM yeu_cau_su_kien WHERE yeu_cau_id=%s ORDER BY id', (yid,))]
    assert kieu == ['tao', 'duyet', 'thuc_thi', 'trang_thai']
    assert q1("SELECT count(*) AS n FROM admin_audit WHERE action='request.approve' AND target_id=%s",
              (str(yid),))['n'] == 1
    # Người gửi được báo sau commit.
    assert q1("SELECT 1 AS c FROM notifications WHERE user_id=%s AND type='yeu_cau' AND ref_id=%s",
              (canh['em'], yid))


def test_lop_gia_su_du_ba_em_409_va_khong_gi_doi(d, canh):
    gs = d.lop(loai='gia_su')
    for _ in range(3):
        d.vao(gs, d.nguoi())
    yid = _xin(d, canh, 'tt_chuyen_lop')
    truoc = q1('SELECT * FROM yeu_cau WHERE id=%s', (yid,))
    # Chỉ đếm lượt của CHÍNH phép kiểm (hai lớp + em) — đếm cả bảng thì đỏ oan khi lead / agent
    # khác đang ghi `class_members` song song trên cùng nhánh Neon (soát 26/09/2026).
    dem = 'SELECT count(*) AS n FROM class_members WHERE class_id = ANY(%s) OR user_id = %s'
    so_luot = q1(dem, ([canh['a'], gs], canh['em']))['n']
    r = d.api(canh['hv']).post('/api/admin/yeu-cau/%d/duyet' % yid, {'den_lop_id': gs}, format='json')
    assert r.status_code == 409, r.data
    assert _luot(canh['a'], canh['em'])[0]['left_at'] is None and not _luot(gs, canh['em'])
    assert q1(dem, ([canh['a'], gs], canh['em']))['n'] == so_luot
    sau = q1('SELECT * FROM yeu_cau WHERE id=%s', (yid,))
    for k in ('trang_thai', 'nguoi_duyet', 'duyet_luc', 'thuc_thi', 'closed_at'):
        assert sau[k] == truoc[k], k
    assert not q1("SELECT 1 AS c FROM admin_audit WHERE action IN ('request.approve', "
                  "'class.member.transfer') AND (target_id=%s OR detail->>'userId'=%s)",
                  (str(yid), str(canh['em'])))
    # Chỉ để lại một dấu nội bộ "duyệt không thành".
    loi = q("SELECT noi_bo FROM yeu_cau_su_kien WHERE yeu_cau_id=%s AND kieu='loi'", (yid,))
    assert loi == [{'noi_bo': True}]


def test_duyet_hai_lan_chi_chuyen_mot_lan(d, canh):
    yid = _xin(d, canh, 'tt_chuyen_lop')
    hv = d.api(canh['hv'])
    assert hv.post('/api/admin/yeu-cau/%d/duyet' % yid, {'den_lop_id': canh['b']}, format='json').status_code == 200
    r = hv.post('/api/admin/yeu-cau/%d/duyet' % yid, {'den_lop_id': canh['b']}, format='json')
    assert r.status_code == 409
    assert len(_luot(canh['b'], canh['em'])) == 1 and len(_luot(canh['a'], canh['em'])) == 1
    assert q1("SELECT count(*) AS n FROM admin_audit WHERE action='class.member.transfer' "
              "AND detail->>'userId'=%s", (str(canh['em']),))['n'] == 1
    assert q1("SELECT count(*) AS n FROM yeu_cau_su_kien WHERE yeu_cau_id=%s AND kieu='thuc_thi'",
              (yid,))['n'] == 1


def test_bao_luu_em_mat_quyen_mon(d, canh, django_capture_on_commit_callbacks):
    from courses.truy_cap import quyen_khoa
    em = User.objects.get(id=canh['em'])
    assert 'hsa_quantitative' in quyen_khoa(em), 'đệm đang giữ quyền môn của lớp A'
    yid = _xin(d, canh, 'tt_bao_luu', du_lieu={'den_ngay': '2099-01-31'})
    with django_capture_on_commit_callbacks(execute=True):
        r = d.api(canh['hv']).post('/api/admin/yeu-cau/%d/duyet' % yid, {}, format='json')
    assert r.status_code == 200, r.data
    (luot,) = _luot(canh['a'], canh['em'])
    assert luot['leave_reason'] == 'reserved' and luot['left_at'] is not None
    assert str(luot['reserve_until']) == '2099-01-31'
    assert 'hsa_quantitative' not in quyen_khoa(em), 'đệm quyền môn phải xoá sau commit'


def test_huy_khoa_dong_luot_bo_giua_chung(d, canh):
    yid = _xin(d, canh, 'tt_huy_khoa')
    assert d.api(canh['hv']).post('/api/admin/yeu-cau/%d/duyet' % yid, {}, format='json').status_code == 200
    assert _luot(canh['a'], canh['em'])[0]['leave_reason'] == 'dropped'


def test_hoc_lai_them_luot_moi(d, canh):
    x("UPDATE class_members SET left_at = now() - interval '1 day', leave_reason='completed' "
      'WHERE class_id=%s AND user_id=%s', (canh['a'], canh['em']))
    yid = _xin(d, canh, 'tt_hoc_lai')
    r = d.api(canh['hv']).post('/api/admin/yeu-cau/%d/duyet' % yid, {}, format='json')
    assert r.status_code == 200, r.data
    luot = _luot(canh['a'], canh['em'])
    assert len(luot) == 2 and luot[1]['left_at'] is None


def test_hoc_bu_v1_chi_ghi_quyet_dinh_roi_hoc_vu_dong(d, canh):
    yid = _xin(d, canh, 'tt_hoc_bu')
    hv = d.api(canh['hv'])
    r = hv.post('/api/admin/yeu-cau/%d/duyet' % yid, {}, format='json')
    assert r.status_code == 200 and r.data['trangThai'] == 'da_duyet', r.data
    assert r.data['thucThi']['cach'] == 'tay'
    r = hv.post('/api/teach/yeu-cau/%d/trang-thai' % yid, {'den': 'da_xong'}, format='json')
    assert r.data['trangThai'] == 'da_xong'


def test_tu_choi_chi_hoc_vu(d, canh):
    yid = _xin(d, canh, 'tt_chuyen_lich')
    assert d.api(canh['gv']).post('/api/admin/yeu-cau/%d/tu-choi' % yid, {}, format='json').status_code == 403
    r = d.api(canh['hv']).post('/api/admin/yeu-cau/%d/tu-choi' % yid, {'ket_qua': 'Lớp khác đã kín'},
                               format='json')
    assert r.status_code == 200 and r.data['trangThai'] == 'tu_choi'
    assert d.api(canh['hv']).post('/api/admin/yeu-cau/%d/duyet' % yid, {}, format='json').status_code == 409


def test_viec_hom_nay_dem_cho_duyet(d, canh):
    _xin(d, canh, 'tt_bao_luu')
    r = d.api(canh['hv']).get('/api/teach/viec-hom-nay')
    assert r.data['yeuCau']['choDuyet'] >= 1
    assert d.api(canh['gv']).get('/api/teach/viec-hom-nay').data['yeuCau']['choDuyet'] == 0


# ── Phụ huynh qua link ───────────────────────────────────────────────────

def test_link_thu_hoi_het_han_va_link_la_cung_mot_404(d, canh):
    thu_hoi = d.link(canh['a'], canh['em'], canh['gv'], thu_hoi='2026-01-01')
    het_han = d.link(canh['a'], canh['em'], canh['gv'], han="now() - interval '1 day'")
    body = {'loai': 'ht_hoc_tap', 'tieu_de': 'x'}
    kq = []
    for tk in (thu_hoi, het_han, 'khong-co-chia-nay'):
        for r in (APIClient().get('/api/public/phu-huynh/%s/yeu-cau' % tk),
                  APIClient().post('/api/public/phu-huynh/%s/yeu-cau' % tk, body, format='json')):
            kq.append((r.status_code, r.data))
    assert len({(m, str(b)) for m, b in kq}) == 1 and kq[0][0] == 404, kq
    assert not q1('SELECT 1 AS c FROM yeu_cau WHERE hoc_vien_id=%s', (canh['em'],))


def test_phu_huynh_toi_da_nam_yeu_cau_mo(d, canh):
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    c = APIClient()
    for i in range(L.TRAN_MO_PHU_HUYNH):
        r = c.post('/api/public/phu-huynh/%s/yeu-cau' % tk, {'loai': 'ht_hoc_tap', 'tieu_de': 'Hỏi %d' % i},
                   format='json')
        assert r.status_code == 201, r.data
        assert r.data['nguon'] == 'phu_huynh' and r.data['hocVien']['id'] == canh['em']
    r = c.post('/api/public/phu-huynh/%s/yeu-cau' % tk, {'loai': 'ht_hoc_tap', 'tieu_de': 'Thứ sáu'},
               format='json')
    assert r.status_code == 429
    assert q1("SELECT count(*) AS n FROM yeu_cau WHERE nguon='phu_huynh' AND hoc_vien_id=%s",
              (canh['em'],))['n'] == L.TRAN_MO_PHU_HUYNH
    # Đóng một yêu cầu → gửi được tiếp.
    yid = q1("SELECT id FROM yeu_cau WHERE nguon='phu_huynh' AND hoc_vien_id=%s LIMIT 1", (canh['em'],))['id']
    d.api(canh['hv']).post('/api/teach/yeu-cau/%d/trang-thai' % yid, {'den': 'da_xong'}, format='json')
    r = c.post('/api/public/phu-huynh/%s/yeu-cau' % tk, {'loai': 'ht_hoc_tap', 'tieu_de': 'Lại'}, format='json')
    assert r.status_code == 201


def test_phu_huynh_chi_thay_yeu_cau_phu_huynh_khong_thay_noi_bo(d, canh):
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    c = APIClient()
    yid = c.post('/api/public/phu-huynh/%s/yeu-cau' % tk, {'loai': 'tt_nghi_hoc', 'tieu_de': 'Cho cháu nghỉ'},
                 format='json').data['id']
    cua_em = _tao(d.api(canh['em']), {'loai': 'ht_hoc_tap', 'tieu_de': 'Việc riêng của em'}).data['id']
    hv = d.api(canh['hv'])
    hv.post('/api/teach/yeu-cau/%d/tra-loi' % yid, {'noi_dung': 'Ghi chú nội bộ', 'noi_bo': True}, format='json')
    hv.post('/api/teach/yeu-cau/%d/tra-loi' % yid, {'noi_dung': 'Trung tâm đã nhận'}, format='json')
    ds = c.get('/api/public/phu-huynh/%s/yeu-cau' % tk).data['yeuCau']
    assert [y['id'] for y in ds] == [yid] and cua_em not in [y['id'] for y in ds]
    chu = [s['noiDung'] for s in ds[0]['suKien']]
    assert 'Trung tâm đã nhận' in chu and 'Ghi chú nội bộ' not in chu
    assert 'thucThi' not in ds[0]
    # Phụ huynh không chọn được em khác / lớp khác qua thân request.
    r = c.post('/api/public/phu-huynh/%s/yeu-cau' % tk,
               {'loai': 'ht_hoc_tap', 'tieu_de': 'x', 'hoc_vien_id': canh['em2'], 'class_id': canh['b']},
               format='json')
    assert r.data['hocVien']['id'] == canh['em'] and r.data['lop']['id'] == canh['a']


# ── Soát 26/09/2026 (E3 lượt 2): phạm vi học viên / phụ huynh, phân loại, mở lại, chữ lỗi ──

def test_hoc_vien_chi_thay_yeu_cau_minh_gui(d, canh):
    """Học viên KHÔNG thấy trợ giảng báo lên về em, phụ huynh gửi về em, giảng viên xin thay đổi
    cho em — "của mình" là mình GỬI. Bản đầu lọc `hoc_vien_id = em OR nguoi_tao = em`: em đọc
    được cả lời trợ giảng báo "em không phản hồi" lẫn điều phụ huynh nhờ trung tâm để ý."""
    bl = _tao(d.api(canh['tg']), {'loai': 'bao_cao_len', 'tieu_de': 'Em không trả lời tin nhắn',
                                  'class_id': canh['a'], 'hoc_vien_id': canh['em']},
              '/api/teach/yeu-cau')
    assert bl.status_code == 201, bl.data
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    ph = APIClient().post('/api/public/phu-huynh/%s/yeu-cau' % tk,
                          {'loai': 'ht_hoc_tap', 'tieu_de': 'Nhờ thầy cô để ý cháu'}, format='json')
    assert ph.status_code == 201, ph.data
    gv = _tao(d.api(canh['gv']), {'loai': 'tt_hoc_bu', 'tieu_de': 'Đề xuất học bù', 'class_id': canh['a'],
                                  'hoc_vien_id': canh['em']}, '/api/teach/yeu-cau')
    assert gv.status_code == 201, gv.data
    hs = d.api(canh['em'])
    cua_em = _tao(hs, {'loai': 'ht_hoc_tap', 'tieu_de': 'Xin tài liệu'}).data['id']
    assert [y['id'] for y in hs.get('/api/yeu-cau').data['yeuCau']] == [cua_em]
    for r in (bl, ph, gv):
        assert hs.get('/api/yeu-cau/%d' % r.data['id']).status_code == 404
        assert hs.post('/api/yeu-cau/%d/tra-loi' % r.data['id'], {'noi_dung': 'x'},
                       format='json').status_code == 404


def test_phu_huynh_chi_thay_yeu_cau_gui_qua_chinh_link(d, canh):
    """Danh sách trên tờ báo cáo = yêu cầu gửi QUA LINK ẤY (lời giao việc 26/09) — link thứ hai
    của cùng em (bố / mẹ, kỳ khác) không đọc được lời trung tâm trả lời qua link thứ nhất."""
    a = d.link(canh['a'], canh['em'], canh['gv'])
    b = d.link(canh['a'], canh['em'], canh['gv'])
    c = APIClient()
    ya = c.post('/api/public/phu-huynh/%s/yeu-cau' % a, {'loai': 'ht_hoc_tap', 'tieu_de': 'Qua link A'},
                format='json').data['id']
    assert [y['id'] for y in c.get('/api/public/phu-huynh/%s/yeu-cau' % b).data['yeuCau']] == []
    assert [y['id'] for y in c.get('/api/public/phu-huynh/%s/yeu-cau' % a).data['yeuCau']] == [ya]


def test_hoc_vu_phan_loai_ghi_lich_su_giang_vien_khong_duoc(d, canh):
    yid = _tao(d.api(canh['em']), {'loai': 'ht_hoc_tap', 'tieu_de': 'Không vào được phòng Zoom',
                                   'class_id': canh['a']}).data['id']
    duong = '/api/admin/yeu-cau/%d/phan-loai' % yid
    assert d.api(canh['gv']).post(duong, {'loai': 'ht_ky_thuat'}, format='json').status_code == 403
    hv = d.api(canh['hv'])
    r = hv.post(duong, {'loai': 'ht_ky_thuat'}, format='json')
    assert r.status_code == 200 and r.data['loai'] == 'ht_ky_thuat', r.data
    sk = [s for s in r.data['suKien'] if s['kieu'] == 'phan_loai']
    assert len(sk) == 1 and (sk[0]['tu'], sk[0]['den']) == ('ht_hoc_tap', 'ht_ky_thuat')
    # Phân loại là việc của yêu cầu HỖ TRỢ — không biến nó thành một lượt xin–duyệt.
    assert hv.post(duong, {'loai': 'tt_chuyen_lop'}, format='json').status_code == 400
    # Sang "hỗ trợ tài khoản" thì giảng viên / trợ giảng thôi thấy (luật phạm vi đi theo loại).
    assert hv.post(duong, {'loai': 'ht_tai_khoan'}, format='json').status_code == 200
    assert d.api(canh['gv']).get('/api/teach/yeu-cau/%d' % yid).status_code == 404
    assert d.api(canh['em']).get('/api/yeu-cau/%d' % yid).data['loai'] == 'ht_tai_khoan'


def test_mo_lai_yeu_cau_thay_doi_bi_tu_choi_chi_hoc_vu(d, canh):
    yid = _xin(d, canh, 'tt_chuyen_lop')
    hv = d.api(canh['hv'])
    assert hv.post('/api/admin/yeu-cau/%d/tu-choi' % yid, {'ket_qua': 'Lớp kín'}, format='json').status_code == 200
    for ai in (canh['tg'], canh['gv']):
        r = d.api(ai).post('/api/teach/yeu-cau/%d/trang-thai' % yid, {'den': 'dang_xu_ly'}, format='json')
        assert r.status_code == 403, r.data
    r = hv.post('/api/teach/yeu-cau/%d/trang-thai' % yid, {'den': 'dang_xu_ly'}, format='json')
    assert r.status_code == 200 and r.data['trangThai'] == 'dang_xu_ly'


def test_loi_du_lieu_noi_bang_chu_nguoi_dung(d, canh):
    r = _tao(d.api(canh['em']), {'loai': 'ht_lich_hoc', 'tieu_de': 'x', 'du_lieu': {'sdt': '0' * 30}})
    assert r.status_code == 400 and 'Số điện thoại' in r.data['error'], r.data
    assert 'sdt' not in r.data['error'].lower()


def test_duyet_khi_em_da_roi_lop_la_409_khong_phai_404(d, canh):
    """404 ở đường duyệt đọc thành "không có yêu cầu này" — sai: yêu cầu có, chỉ việc không làm được."""
    yid = _xin(d, canh, 'tt_chuyen_lop')
    x("UPDATE class_members SET left_at = now(), leave_reason = 'dropped' WHERE class_id=%s AND user_id=%s",
      (canh['a'], canh['em']))
    r = d.api(canh['hv']).post('/api/admin/yeu-cau/%d/duyet' % yid, {'den_lop_id': canh['b']}, format='json')
    assert r.status_code == 409 and 'không đang học' in r.data['error'], r.data
    assert q1('SELECT trang_thai FROM yeu_cau WHERE id=%s', (yid,))['trang_thai'] == 'moi'


def test_tro_giang_khong_thay_email_em_chua_co_ten(d, canh):
    x("UPDATE users SET name = '' WHERE id = %s", (canh['em'],))
    yid = _tao(d.api(canh['em']), {'loai': 'hoi_dap', 'tieu_de': 'Câu 3 bài tập'}).data['id']
    email = q1('SELECT email FROM users WHERE id=%s', (canh['em'],))['email']
    tg = d.api(canh['tg'])
    ct = tg.get('/api/teach/yeu-cau/%d' % yid).data
    ds = [y for y in tg.get('/api/teach/yeu-cau').data['yeuCau'] if y['id'] == yid]
    assert ds and email not in json.dumps([ct, ds], ensure_ascii=False, default=str)


def test_tro_giang_bao_em_khong_phan_hoi(d, canh):
    r = _tao(d.api(canh['tg']), {'loai': 'bao_cao_len', 'tieu_de': 'Em không phản hồi 3 ngày',
                                 'class_id': canh['a'], 'hoc_vien_id': canh['em'],
                                 'du_lieu': {'khong_phan_hoi': True}}, '/api/teach/yeu-cau')
    assert r.status_code == 201 and r.data['duLieu'].get('khong_phan_hoi') is True, r.data


def test_lua_chon_em_chi_cho_lop_trong_pham_vi_va_khong_lien_lac(d, canh):
    tg = d.api(canh['tg'])
    r = tg.get('/api/teach/yeu-cau/lua-chon', {'class_id': canh['a']})
    assert {h['id'] for h in r.data['hocVien']} == {canh['em'], canh['em2']}, r.data
    assert all(set(h) == {'id', 'ten'} for h in r.data['hocVien']), 'chỉ tên em — không liên lạc'
    # Lớp ngoài phạm vi: không lộ sĩ số.
    assert tg.get('/api/teach/yeu-cau/lua-chon', {'class_id': canh['b']}).data['hocVien'] == []


def test_lich_su_co_nhan_trang_thai_va_loai(d, canh):
    yid = _tao(d.api(canh['em']), {'loai': 'ht_hoc_tap', 'tieu_de': 'x'}).data['id']
    hv = d.api(canh['hv'])
    hv.post('/api/teach/yeu-cau/%d/trang-thai' % yid, {'den': 'dang_xu_ly'}, format='json')
    r = hv.post('/api/admin/yeu-cau/%d/phan-loai' % yid, {'loai': 'ht_lich_hoc'}, format='json')
    sk = {s['kieu']: s for s in r.data['suKien']}
    assert (sk['trang_thai']['tuNhan'], sk['trang_thai']['denNhan']) == ('Mới', 'Đang xử lý')
    assert (sk['phan_loai']['tuNhan'], sk['phan_loai']['denNhan']) == ('Hỗ trợ học tập', 'Hỗ trợ lịch học')


def test_moi_nguon_chi_gui_duoc_loai_cua_minh(d, canh):
    assert _tao(d.api(canh['em']), {'loai': 'bao_cao_len', 'tieu_de': 'x',
                                    'class_id': canh['a']}).status_code == 400
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    r = APIClient().post('/api/public/phu-huynh/%s/yeu-cau' % tk, {'loai': 'ht_tai_khoan', 'tieu_de': 'x'},
                         format='json')
    assert r.status_code == 400
    assert _tao(d.api(canh['tg']), {'loai': 'ht_hoc_tap', 'tieu_de': 'x', 'class_id': canh['a']},
                '/api/teach/yeu-cau').status_code == 400
