"""Chuyển lớp MỘT thao tác (§55, mục 1.2c — 24/09/2026).

`POST /api/admin/classes/<A>/members/<em>/transfer {to_class_id}`: đóng lượt ở A với lý
do 'transferred', mở lượt ở B, lượt A trỏ tới lượt B — MỘT giao dịch. Đi qua VIEW THẬT;
CSDL trong giao dịch cuộn lại (`conftest.py`); dữ liệu của mỗi test mang tiền tố riêng.
"""
import uuid
from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.clock import local_today
from common.db import q, q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER

f = APIRequestFactory()
pytestmark = pytest.mark.django_db


def _chuyen(tu, em, body, ai):
    from teaching.chuyen_lop import ChuyenLopView
    req = f.post('/x', body, format='json')
    force_authenticate(req, user=ai)
    return ChuyenLopView.as_view()(req, class_id=tu, user_id=em.id)


def _nguoi(ten, vai):
    r = q1('INSERT INTO users (name, email, password, role, streak) VALUES (%s, %s, %s, %s, 0) RETURNING id',
           (ten, 'cl_%s@example.com' % uuid.uuid4().hex[:10], 'x', vai))
    return User.objects.get(id=r['id'])


def _lop(ten, mon='hsa_quantitative', loai='nhom', status='active'):
    return q1('INSERT INTO classes (name, course_id, status, class_type) VALUES (%s, %s, %s, %s) RETURNING id',
              (ten, mon, status, loai))['id']


def _vao(lop, u, luc='now()'):
    return q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, ' + luc + ') RETURNING id',
              (lop, u.id))['id']


def _luot(lop, u):
    return q('SELECT id, joined_at, left_at, leave_reason, note, transferred_to FROM class_members '
             'WHERE class_id=%s AND user_id=%s ORDER BY id', (lop, u.id))


@pytest.fixture
def canh():
    tt = 'CL%s' % uuid.uuid4().hex[:6]
    em = _nguoi('%s Em' % tt, ROLE_STUDENT)
    a = _lop('%s Lop A' % tt)
    b = _lop('%s Lop B' % tt, mon='hsa_verbal')
    _vao(a, em, "now() - interval '30 days'")
    return {'tt': tt, 'hv': _nguoi('HocVu CL', ROLE_ACADEMIC), 'em': em, 'a': a, 'b': b}


def test_chuyen_giu_hai_luot_va_noi_lai(canh):
    nk = q1("SELECT count(*) AS n FROM admin_audit WHERE action = 'class.member.transfer'")['n']
    r = _chuyen(canh['a'], canh['em'], {'to_class_id': canh['b'], 'note': 'Xin đổi ca'}, canh['hv'])
    assert r.status_code == 200, r.data
    (cu,), (moi,) = _luot(canh['a'], canh['em']), _luot(canh['b'], canh['em'])
    assert cu['left_at'] is not None and cu['leave_reason'] == 'transferred'
    assert cu['transferred_to'] == moi['id'] and cu['note'] == 'Xin đổi ca'
    assert moi['left_at'] is None and moi['joined_at'] == cu['left_at'], 'vào B đúng lúc rời A'
    assert (r.data['fromMemberId'], r.data['toMemberId']) == (cu['id'], moi['id'])
    assert any('Môn của lớp mới khác' in w for w in r.data['warnings']), r.data['warnings']
    assert q1("SELECT count(*) AS n FROM admin_audit WHERE action = 'class.member.transfer'")['n'] == nk + 1


def test_em_da_o_lop_moi_409_va_lop_cu_nguyen(canh):
    _vao(canh['b'], canh['em'])
    r = _chuyen(canh['a'], canh['em'], {'to_class_id': canh['b']}, canh['hv'])
    assert r.status_code == 409, r.data
    assert _luot(canh['a'], canh['em'])[0]['left_at'] is None


def test_ghi_lop_moi_hong_giua_chung_thi_lop_cu_khong_dong(canh, monkeypatch):
    """Một lượt thêm em vào B chen vào giữa lúc kiểm và lúc ghi → INSERT không ra dòng.
    Lệnh đóng A đã chạy trước đó phải CUỘN LẠI — không thì em rơi khỏi mọi lớp."""
    from teaching import chuyen_lop
    goc = chuyen_lop.q1

    def gia_chen(sql, *a, **kw):
        if sql.lstrip().startswith('INSERT INTO class_members'):
            return None
        return goc(sql, *a, **kw)

    monkeypatch.setattr(chuyen_lop, 'q1', gia_chen)
    r = _chuyen(canh['a'], canh['em'], {'to_class_id': canh['b']}, canh['hv'])
    assert r.status_code == 409, r.data
    cu = _luot(canh['a'], canh['em'])[0]
    assert cu['left_at'] is None and cu['leave_reason'] is None, 'lớp cũ bị đóng dù chuyển hỏng'


def test_lop_moi_gia_su_day_huy_hay_da_ket_thuc(canh):
    gs = _lop('%s Gia su' % canh['tt'], loai='gia_su')
    for i in range(3):
        _vao(gs, _nguoi('%s Ban%d' % (canh['tt'], i), ROLE_STUDENT))
    r = _chuyen(canh['a'], canh['em'], {'to_class_id': gs}, canh['hv'])
    assert r.status_code == 409 and 'gia sư' in r.data['error'], r.data
    huy = _lop('%s Huy' % canh['tt'], status='cancelled')
    r = _chuyen(canh['a'], canh['em'], {'to_class_id': huy}, canh['hv'])
    assert r.status_code == 400 and 'huỷ' in r.data['error'], r.data
    assert _luot(canh['a'], canh['em'])[0]['left_at'] is None
    xong = _lop('%s Xong' % canh['tt'], status='finished')
    r = _chuyen(canh['a'], canh['em'], {'to_class_id': xong}, canh['hv'])
    assert r.status_code == 200 and any('đã kết thúc' in w for w in r.data['warnings']), r.data


def test_ngay_chuyen(canh):
    mai = (local_today() + timedelta(days=1)).isoformat()
    r = _chuyen(canh['a'], canh['em'], {'to_class_id': canh['b'], 'effective_date': mai}, canh['hv'])
    assert r.status_code == 400 and 'tương lai' in r.data['error'], r.data
    xa = (local_today() - timedelta(days=60)).isoformat()
    r = _chuyen(canh['a'], canh['em'], {'to_class_id': canh['b'], 'effective_date': xa}, canh['hv'])
    assert r.status_code == 400 and 'từ ngày em vào lớp' in r.data['error'], r.data
    tuan_truoc = local_today() - timedelta(days=7)
    r = _chuyen(canh['a'], canh['em'], {'to_class_id': canh['b'], 'effective_date': tuan_truoc.isoformat()},
                canh['hv'])
    assert r.status_code == 200, r.data
    moi = _luot(canh['b'], canh['em'])[0]
    assert moi['joined_at'].date() == tuan_truoc and moi['joined_at'].hour == 0


def test_chi_hoc_vien_dang_hoc_va_chi_hoc_vu(canh):
    tg = _nguoi('%s TG' % canh['tt'], ROLE_ASSISTANT)
    _vao(canh['a'], tg)
    r = _chuyen(canh['a'], tg, {'to_class_id': canh['b']}, canh['hv'])
    assert r.status_code == 400, r.data
    la = _nguoi('%s La' % canh['tt'], ROLE_STUDENT)
    r = _chuyen(canh['a'], la, {'to_class_id': canh['b']}, canh['hv'])
    assert r.status_code == 404, r.data
    r = _chuyen(canh['a'], canh['em'], {'to_class_id': canh['a']}, canh['hv'])
    assert r.status_code == 400, r.data
    r = _chuyen(canh['a'], canh['em'], {'to_class_id': canh['b']}, _nguoi('GV CL', ROLE_TEACHER))
    assert r.status_code == 403


def test_check_chi_luot_chuyen_moi_duoc_tro(canh):
    b_id = _vao(canh['b'], canh['em'])
    with pytest.raises(IntegrityError), transaction.atomic():
        x("UPDATE class_members SET left_at = now(), leave_reason = 'dropped', transferred_to = %s "
          'WHERE class_id = %s AND user_id = %s', (b_id, canh['a'], canh['em'].id))


def test_dong_thoi_gian_hien_mot_su_kien_chuyen(canh):
    from teaching.dong_thoi_gian import dong_thoi_gian
    assert _chuyen(canh['a'], canh['em'], {'to_class_id': canh['b']}, canh['hv']).status_code == 200
    tieu_de = [e['tieuDe'] for e in dong_thoi_gian(canh['em'].id, None)]
    assert 'Chuyển từ lớp %s Lop A sang lớp %s Lop B' % (canh['tt'], canh['tt']) in tieu_de, tieu_de
    assert 'Vào lớp %s Lop B' % canh['tt'] not in tieu_de, 'sự kiện chuyển đã nói — không lặp "Vào lớp B"'
    assert 'Vào lớp %s Lop A' % canh['tt'] in tieu_de


def test_ghi_chu_chuyen_lop_khong_thanh_nhan_xet_gui_phu_huynh(canh):
    """Ghi chú chuyển lớp là ghi chú NỘI BỘ của học vụ (ở lại `class_members.note`).
    Tờ phụ huynh chỉ in nhận xét GIẢNG VIÊN viết cho phụ huynh (`teacher_comment`, §62) —
    trước 25/09 tờ in thẳng `note`, nên phụ huynh lớp cũ đọc được lý do chuyển lớp."""
    from teaching.parent_report import dung_bao_cao
    r = _chuyen(canh['a'], canh['em'], {'to_class_id': canh['b'], 'note': 'Ghi chú nội bộ XYZ'}, canh['hv'])
    assert r.status_code == 200, r.data
    hom_nay = local_today()
    bc, loi = dung_bao_cao(canh['a'], canh['em'].id, hom_nay - timedelta(days=30), hom_nay)
    assert loi is None, loi
    assert bc['membership']['teacherNote'] is None, bc['membership']
    assert _luot(canh['a'], canh['em'])[0]['note'] == 'Ghi chú nội bộ XYZ', 'ghi chú nội bộ vẫn giữ cho nhân sự'
