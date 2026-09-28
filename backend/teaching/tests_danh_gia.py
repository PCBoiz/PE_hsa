"""Đánh giá một em trong lớp — `PUT /api/teach/classes/<c>/students/<u>/danh-gia`.

Kế hoạch v2 V-a + V-f (bảng yêu cầu TopHSA dòng 18, 21): nhận xét của giảng viên
gửi phụ huynh (§62a `teacher_comment`), cờ "cần hỗ trợ" đánh tay kèm lý do, đề xuất
hướng học (§62b). Chạy trên DB thật, giao dịch CUỘN LẠI (`conftest.py`); mọi lời gọi
đi qua URL thật.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Nhận xét + hướng học: CHỈ giảng viên / học vụ / quản trị (IsSeniorTeachingStaff)
     của lớp mình. Trợ giảng CHỈ đặt được cờ cần hỗ trợ — gửi kèm nhận xét là 403 và
     KHÔNG ghi gì (không ghi nửa chừng phần cờ).
  2. Ghi vào lượt học ĐANG MỞ của em, không có thì lượt MỚI NHẤT.
  3. Nhận xét lên tờ phụ huynh; ghi chú NỘI BỘ `note` không bị đụng, không lên tờ.
  4. Cờ hiện ở "Việc hôm nay" (giảng viên + trợ giảng của lớp) và dòng thời gian.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q, q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db


def _nguoi(ten, vai):
    row = q1("INSERT INTO users (name, email, password, role, streak) "
             "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             (ten, '%s_dg@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=row['id'])


def _lop(ten, gv):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status) "
              "VALUES (%s, 'hsa_quantitative', %s, 'active') RETURNING id", (ten, gv.id))['id']


def _vao(lop, u, cach_ngay=20, roi_cach_ngay=None):
    nay = local_now()
    return q1('INSERT INTO class_members (class_id, user_id, joined_at, left_at, leave_reason) '
              'VALUES (%s, %s, %s, %s, %s) RETURNING id',
              (lop, u.id, nay - timedelta(days=cach_ngay),
               nay - timedelta(days=roi_cach_ngay) if roi_cach_ngay is not None else None,
               'dropped' if roi_cach_ngay is not None else None))['id']


def _api(ai):
    a = APIClient()
    if ai is not None:
        a.force_authenticate(user=ai)
    return a


def _url(lop, em):
    return '/api/teach/classes/%d/students/%d/danh-gia' % (lop, em.id)


def _put(ai, lop, em, body):
    return _api(ai).put(_url(lop, em), body, format='json')


@pytest.fixture
def canh(db):
    gv = _nguoi('GV DG', ROLE_TEACHER)
    gv_khac = _nguoi('GV Khac DG', ROLE_TEACHER)
    tg = _nguoi('TG DG', ROLE_ASSISTANT)
    hoc_vu = _nguoi('HocVu DG', ROLE_ACADEMIC)
    em = _nguoi('Em DG', ROLE_STUDENT)
    ngoai = _nguoi('Ngoai DG', ROLE_STUDENT)
    lop = _lop('Lop DG', gv)
    luot = _vao(lop, em)
    _vao(lop, tg)
    # Ghi chú NỘI BỘ (lý do rời, chuyển lớp…) — không được bị đụng, không lên tờ.
    x("UPDATE class_members SET note = 'ghi chu noi bo DG' WHERE id = %s", (luot,))
    return {'gv': gv, 'gv_khac': gv_khac, 'tg': tg, 'hoc_vu': hoc_vu, 'em': em,
            'ngoai': ngoai, 'lop': lop, 'luot': luot}


def _dong(luot):
    return q1('SELECT * FROM class_members WHERE id = %s', (luot,))


# ── 1. Ai ghi được gì ───────────────────────────────────────────────────────

def test_giang_vien_ghi_nhan_xet_len_to_phu_huynh_khong_dung_ghi_chu_noi_bo(canh):
    r = _put(canh['gv'], canh['lop'], canh['em'], {'teacherComment': '  Con tiến bộ rõ ở phần tỉ lệ.  '})
    assert r.status_code == 200, r.json()
    assert r.json()['teacherComment'] == 'Con tiến bộ rõ ở phần tỉ lệ.'
    d = _dong(canh['luot'])
    assert d['teacher_comment'] == 'Con tiến bộ rõ ở phần tỉ lệ.'
    assert d['teacher_comment_by'] == canh['gv'].id and d['teacher_comment_at'] is not None
    assert d['note'] == 'ghi chu noi bo DG', 'ghi đè ghi chú NỘI BỘ (bài học e328ade)'
    to = _api(canh['gv']).get('/api/teach/classes/%d/students/%d/parent-report'
                              % (canh['lop'], canh['em'].id))
    assert to.status_code == 200, to.json()
    assert to.json()['membership']['teacherNote'] == 'Con tiến bộ rõ ở phần tỉ lệ.'
    assert 'ghi chu noi bo DG' not in str(to.json())
    # Xoá nhận xét: chuỗi rỗng → NULL, tờ thôi in.
    assert _put(canh['gv'], canh['lop'], canh['em'], {'teacherComment': ''}).status_code == 200
    assert _dong(canh['luot'])['teacher_comment'] is None


def test_tro_giang_chi_dat_duoc_co_can_ho_tro(canh):
    tg, lop, em = canh['tg'], canh['lop'], canh['em']
    for body in ({'teacherComment': 'x'}, {'deXuatHuongHoc': 'x'},
                 {'canHoTro': True, 'lyDo': 'vắng', 'teacherComment': 'x'}):
        r = _put(tg, lop, em, body)
        assert r.status_code == 403, (body, r.json())
    d = _dong(canh['luot'])
    assert d['teacher_comment'] is None and d['de_xuat_huong_hoc'] is None
    assert d['can_ho_tro'] is False, 'bị 403 mà vẫn ghi nửa chừng phần cờ'

    r = _put(tg, lop, em, {'canHoTro': True, 'lyDo': ' Hai buổi liền không vào phòng '})
    assert r.status_code == 200, r.json()
    d = _dong(canh['luot'])
    assert d['can_ho_tro'] is True and d['can_ho_tro_ly_do'] == 'Hai buổi liền không vào phòng'
    assert d['can_ho_tro_by'] == tg.id and d['can_ho_tro_at'] is not None
    # Đọc lại: trợ giảng KHÔNG nhận nhận xét / hướng học (không phải việc của vai này).
    g = _api(tg).get(_url(lop, em)).json()
    assert g['canHoTro'] is True and g['lyDo'] == 'Hai buổi liền không vào phòng'
    assert 'teacherComment' not in g and 'deXuatHuongHoc' not in g
    assert g['quyen'] == {'nhanXet': False}
    # Bỏ đánh dấu xoá luôn lý do.
    assert _put(tg, lop, em, {'canHoTro': False}).status_code == 200
    d = _dong(canh['luot'])
    assert d['can_ho_tro'] is False and d['can_ho_tro_ly_do'] is None


def test_giang_vien_de_xuat_huong_hoc_va_doc_lai(canh):
    r = _put(canh['gv'], canh['lop'], canh['em'],
             {'deXuatHuongHoc': 'Ôn lại phần hình trước, rồi mới luyện tốc độ.', 'canHoTro': True,
              'lyDo': 'Điểm kiểm tra giảm'})
    assert r.status_code == 200, r.json()
    g = _api(canh['gv']).get(_url(canh['lop'], canh['em'])).json()
    assert g['deXuatHuongHoc'] == 'Ôn lại phần hình trước, rồi mới luyện tốc độ.'
    assert g['deXuatHuongHocBy'] == 'GV DG' and g['canHoTroBy'] == 'GV DG'
    assert g['quyen'] == {'nhanXet': True}
    # Hướng học là NỘI BỘ: không lên tờ phụ huynh.
    to = _api(canh['gv']).get('/api/teach/classes/%d/students/%d/parent-report'
                              % (canh['lop'], canh['em'].id)).json()
    assert 'Ôn lại phần hình' not in str(to) and 'Điểm kiểm tra giảm' not in str(to)


def test_cua_chan(canh):
    lop, em = canh['lop'], canh['em']
    assert _put(None, lop, em, {'canHoTro': True}).status_code == 401
    assert _put(em, lop, em, {'canHoTro': True}).status_code == 403, 'học viên'
    assert _put(canh['gv_khac'], lop, em, {'canHoTro': True}).status_code == 404, 'lớp người khác'
    assert _put(canh['gv'], lop, canh['ngoai'], {'canHoTro': True}).status_code == 404, 'em ngoài lớp'
    assert _put(canh['gv'], lop, canh['tg'], {'canHoTro': True}).status_code == 404, 'không phải học viên'
    assert _put(canh['gv'], lop, em, {}).status_code == 400
    assert _put(canh['gv'], lop, em, {'canHoTro': 'co'}).status_code == 400
    assert _put(canh['gv'], lop, em, {'teacherComment': 'x' * 2001}).status_code == 400
    assert _dong(canh['luot'])['can_ho_tro'] is False
    assert _put(canh['hoc_vu'], lop, em, {'teacherComment': 'Học vụ ghi'}).status_code == 200


def test_ghi_vao_luot_dang_mo_khong_thi_luot_moi_nhat(canh):
    gv, lop = canh['gv'], canh['lop']
    hai = _nguoi('Hai Luot DG', ROLE_STUDENT)
    cu = _vao(lop, hai, cach_ngay=60, roi_cach_ngay=40)
    mo = _vao(lop, hai, cach_ngay=10)
    assert _put(gv, lop, hai, {'teacherComment': 'Đợt hai'}).status_code == 200
    assert _dong(mo)['teacher_comment'] == 'Đợt hai' and _dong(cu)['teacher_comment'] is None

    da_roi = _nguoi('Da Roi DG', ROLE_STUDENT)
    xa = _vao(lop, da_roi, cach_ngay=90, roi_cach_ngay=70)
    gan = _vao(lop, da_roi, cach_ngay=50, roi_cach_ngay=30)
    assert _put(gv, lop, da_roi, {'teacherComment': 'Tổng kết'}).status_code == 200
    assert _dong(gan)['teacher_comment'] == 'Tổng kết' and _dong(xa)['teacher_comment'] is None


# ── 2. Cờ đi tới đâu ────────────────────────────────────────────────────────

def test_co_hien_o_viec_hom_nay_cua_lop_ay(canh):
    _vao(canh['lop'], _nguoi('Ban Cung Lop DG', ROLE_STUDENT))    # KHÔNG bị đánh dấu
    assert _put(canh['tg'], canh['lop'], canh['em'],
                {'canHoTro': True, 'lyDo': 'Không làm bài tuần này'}).status_code == 200
    for ai in (canh['gv'], canh['tg']):
        d = _api(ai).get('/api/teach/viec-hom-nay').json()
        assert [(e['userId'], e['classId'], e['lyDo'], e['boi']) for e in d['canHoTro']] == [
            (canh['em'].id, canh['lop'], 'Không làm bài tuần này', 'TG DG')], d.get('canHoTro')
    khac = _api(canh['gv_khac']).get('/api/teach/viec-hom-nay').json()
    assert khac['canHoTro'] == []


def test_nhat_ky_va_dong_thoi_gian(canh):
    assert _put(canh['tg'], canh['lop'], canh['em'],
                {'canHoTro': True, 'lyDo': 'Vắng hai buổi'}).status_code == 200
    assert _put(canh['gv'], canh['lop'], canh['em'],
                {'deXuatHuongHoc': 'Học lại bài 3'}).status_code == 200
    nk = q("SELECT actor_id, action, target_type, target_id FROM admin_audit "
           "WHERE actor_id = ANY(%s) ORDER BY id", ([canh['tg'].id, canh['gv'].id],))
    assert [(r['action'], r['target_type'], r['target_id']) for r in nk] == [
        ('class.member.assess', 'user', str(canh['em'].id))] * 2, nk
    ev = _api(canh['hoc_vu']).get('/api/admin/users/%d/timeline' % canh['em'].id).json()['events']
    co = next(e for e in ev if e['tieuDe'] == 'Được đánh dấu cần hỗ trợ')
    assert co['chiTiet'] == 'Lớp Lop DG · Vắng hai buổi' and co['boi'] == 'TG DG', co
    huong = next(e for e in ev if e['tieuDe'] == 'Đề xuất hướng học')
    assert huong['chiTiet'] == 'Lớp Lop DG · Học lại bài 3' and huong['boi'] == 'GV DG', huong
