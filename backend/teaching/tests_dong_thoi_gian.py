"""DÒNG THỜI GIAN HỌC VIÊN — `teaching/dong_thoi_gian.py`.

Dựng một em có đủ mốc qua ĐƯỜNG THẬT khi rẻ (sửa hồ sơ, cấp lại mật khẩu đi qua
view thật để nhật ký do chính view ghi), còn lại chèn thẳng vào bảng gốc. Chạy
trên DB production trong giao dịch cuộn lại (`conftest.py`).
"""
import datetime
import json

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1
from common.permissions import ROLE_ACADEMIC, ROLE_STUDENT, ROLE_TEACHER

f = APIRequestFactory()


def _l(s):
    '''Thời điểm NAIVE giờ Việt Nam — đúng kiểu các cột TIMESTAMP của lược đồ cũ.'''
    return datetime.datetime.fromisoformat(s)


def _goi(view, method, body=None, ai=None, **kw):
    req = getattr(f, method)('/x', body, format='json') if body is not None else getattr(f, method)('/x')
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(ten, vai):
    r = q1("INSERT INTO users (name, email, password, role, streak, created_at) "
           "VALUES (%s, %s, 'x', %s, 0, %s) RETURNING id",
           (ten, '%s_tg@example.com' % ten.replace(' ', '_').lower(), vai, _l('2026-08-01T09:00')))
    return User.objects.get(id=r['id'])


def _lop(ten, gv, **kw):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status, ends_on) "
              "VALUES (%s, 'hsa_quantitative', %s, %s, %s) RETURNING id",
              (ten, gv.id, kw.get('status', 'active'), kw.get('ends_on')))['id']


@pytest.fixture
def canh(db):
    hocvu = _nguoi('HocVu TG', ROLE_ACADEMIC)
    gv = _nguoi('GV TG', ROLE_TEACHER)
    em = _nguoi('Em TG', ROLE_STUDENT)
    a = _lop('Lop A TG', gv)
    b = _lop('Lop B TG', gv, status='finished', ends_on=datetime.date(2026, 9, 20))
    # Chuyển lớp: rời A với lý do, vào B cùng ngày.
    q1("INSERT INTO class_members (class_id, user_id, joined_at, left_at, leave_reason) "
       "VALUES (%s, %s, %s, %s, 'transferred') RETURNING id",
       (a, em.id, _l('2026-08-02T08:00'), _l('2026-08-20T17:00')))
    q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, %s) RETURNING id',
       (b, em.id, _l('2026-08-20T18:00')))
    de = q1('SELECT id FROM mock_exams ORDER BY id LIMIT 1')
    if de:
        q1('INSERT INTO mock_attempts (user_id, exam_id, score, total, started_at, submitted_at) '
           'VALUES (%s, %s, 7, 10, %s, %s) RETURNING id',
           (em.id, de['id'], _l('2026-09-01T08:00'), _l('2026-09-01T09:00')))
    q1("INSERT INTO ket_qua_thi_ngoai (user_id, ngay_thi, dot, tong_diem, tong_toi_da, ten_tren_to) "
       "VALUES (%s, %s, 'HSA đợt 501', 98, 150, 'EM TG') RETURNING id", (em.id, datetime.date(2026, 9, 10)))
    lk = q1("INSERT INTO parent_report_links (token, class_id, user_id, period_from, period_to, created_by, "
            "expires_at) VALUES ('tg-chia-thu-%s', %s, %s, '2026-08-01', '2026-08-31', %s, %s) RETURNING id",
            (em.id, b, em.id, gv.id, _l('2026-12-01T00:00')))['id']
    q1("INSERT INTO parent_report_sends (link_id, phone, email, status, channel, requested_by, sent_at) "
       "VALUES (%s, '0900000999', 'phu.huynh.bi.mat.tg@example.com', 'da_gui', 'email', %s, %s) RETURNING id",
       (lk, gv.id, _l('2026-09-02T20:00')))
    return {'hocvu': hocvu, 'gv': gv, 'em': em, 'a': a, 'b': b, 'co_de': bool(de)}


def _lay(canh, ai=None):
    from teaching.dong_thoi_gian import DongThoiGianView
    return _goi(DongThoiGianView, 'get', ai=ai or canh['hocvu'], user_id=canh['em'].id)


def test_du_moc_va_moi_nhat_o_tren(canh):
    from teaching.ho_so import HoSoHocVienView
    # Sửa hồ sơ qua VIEW THẬT — nhật ký do chính view ghi.
    assert _goi(HoSoHocVienView, 'patch', {'school': 'THPT TG'}, ai=canh['hocvu'],
                user_id=canh['em'].id).status_code == 200
    r = _lay(canh)
    assert r.status_code == 200, r.data
    ev = r.data['events']
    tieu_de = [e['tieuDe'] for e in ev]
    for can in ('Được cấp tài khoản', 'Vào lớp Lop A TG', 'Rời lớp Lop A TG', 'Vào lớp Lop B TG',
                'Học hết lớp Lop B TG', 'Thi HSA đợt 501', 'Gửi báo cáo cho phụ huynh qua email',
                'Hồ sơ được cập nhật'):
        assert can in tieu_de, (can, tieu_de)
    if canh['co_de']:
        thi = next(e for e in ev if e['tieuDe'].startswith('Nộp bài thi thử'))
        assert thi['chiTiet'] == '7/10 điểm'
    # Mới nhất ở trên, cũ nhất (cấp tài khoản 01/08) ở dưới cùng.
    assert tieu_de[0] == 'Hồ sơ được cập nhật' and tieu_de[-1] == 'Được cấp tài khoản'
    roi = next(e for e in ev if e['tieuDe'] == 'Rời lớp Lop A TG')
    assert roi['chiTiet'] == 'Lý do: chuyển lớp', 'phải dịch mã transferred, không in mã trần'
    ho_so = next(e for e in ev if e['tieuDe'] == 'Hồ sơ được cập nhật')
    assert ho_so['boi'] == 'HocVu TG' and 'Trường' in (ho_so['chiTiet'] or '')


def test_moc_chi_co_ngay_khong_bia_ra_gio(canh):
    ev = _lay(canh).data['events']
    het = next(e for e in ev if e['tieuDe'] == 'Học hết lớp Lop B TG')
    assert het['caNgay'] is True and het['luc'] == '2026-09-20'
    thi = next(e for e in ev if e['tieuDe'] == 'Thi HSA đợt 501')
    assert thi['caNgay'] is True and thi['chiTiet'].startswith('98/150 điểm')
    vao = next(e for e in ev if e['tieuDe'] == 'Vào lớp Lop A TG')
    assert vao['caNgay'] is False


def test_ten_dot_da_mo_dau_bang_thi_khong_bi_ghep_hai_lan(canh):
    """Soi ảnh 23/09/2026: "Thi Thi thử tại trung tâm lần 2"."""
    q1("INSERT INTO ket_qua_thi_ngoai (user_id, ngay_thi, dot, tong_diem, tong_toi_da, ten_tren_to) "
       "VALUES (%s, '2026-09-17', 'Thi thử tại trung tâm lần 2', 103, 150, 'EM TG') RETURNING id",
       (canh['em'].id,))
    tieu_de = [e['tieuDe'] for e in _lay(canh).data['events']]
    assert 'Thi thử tại trung tâm lần 2' in tieu_de, tieu_de
    assert not any(t.startswith('Thi Thi') for t in tieu_de)
    assert 'Thi HSA đợt 501' in tieu_de, 'tên đợt KHÔNG mở đầu bằng "Thi" thì vẫn phải ghép'


def test_khong_lo_dia_chi_phu_huynh(canh):
    """Dòng thời gian nói "đã gửi qua email", KHÔNG nói gửi tới địa chỉ nào."""
    toan_bo = json.dumps(_lay(canh).data, ensure_ascii=False)
    assert 'phu.huynh.bi.mat.tg@example.com' not in toan_bo
    assert '0900000999' not in toan_bo


def test_gui_loi_va_dang_cho_duoc_goi_dung_ten(canh):
    lk = q1('SELECT id FROM parent_report_links WHERE user_id=%s', (canh['em'].id,))['id']
    q1("INSERT INTO parent_report_sends (link_id, phone, status, channel, requested_by) "
       "VALUES (%s, '0900000998', 'loi', 'zalo', %s) RETURNING id", (lk, canh['gv'].id))
    tieu_de = [e['tieuDe'] for e in _lay(canh).data['events']]
    assert 'Gửi báo cáo cho phụ huynh không thành công' in tieu_de
    assert tieu_de.count('Gửi báo cáo cho phụ huynh qua email') == 1


def test_hoc_vu_khong_xem_duoc_nhan_su_va_giang_vien_khong_vao(canh):
    from teaching.dong_thoi_gian import DongThoiGianView
    assert _goi(DongThoiGianView, 'get', ai=canh['hocvu'], user_id=canh['gv'].id).status_code == 403
    assert _goi(DongThoiGianView, 'get', ai=canh['gv'], user_id=canh['em'].id).status_code == 403
    assert _goi(DongThoiGianView, 'get', ai=canh['hocvu'], user_id=999999999).status_code == 404


# ── Hai mốc còn thiếu trong chuỗi khách yêu cầu (bảng phân rã dòng 4, 26/09) ──
#
# Khách viết rõ hành trình phải theo dõi được: "Đăng ký → Xếp lớp → **Khai giảng**
# → **Làm bài** → Kiểm tra → Thi thử → Kết quả → Báo cáo → Hoàn thành khóa học".
#
# Đối chiếu 26/09: bảy mốc đã có. Hai mốc in đậm thì chưa — dòng thời gian biết
# em VÀO lớp và biết lớp KẾT THÚC, nhưng không biết lớp bắt đầu dạy hôm nào; và
# biết điểm bài KIỂM TRA mà không biết em có làm bài tập hay không.

def _buoi(lop, luc, huy=False):
    return q1("INSERT INTO class_sessions (class_id, starts_at, duration_minutes, topic, status) "
              "VALUES (%s, %s, 90, 'Buổi đầu', %s) RETURNING id",
              (lop, luc, 'cancelled' if huy else 'planned'))['id']


def _bai_tap(lop, gv, tieu_de, kind='bai_tap'):
    return q1("INSERT INTO assignments (class_id, title, kind, created_by, max_score) "
              "VALUES (%s, %s, %s, %s, 10) RETURNING id", (lop, tieu_de, kind, gv.id))['id']


def test_moc_khai_giang_lay_buoi_dau_tien_khong_tinh_buoi_da_huy(canh):
    """"Khai giảng" = buổi học ĐẦU TIÊN của lớp thật sự diễn ra."""
    _buoi(canh['b'], _l('2026-08-21T19:30'), huy=True)   # buổi huỷ: không phải khai giảng
    _buoi(canh['b'], _l('2026-08-23T19:30'))             # buổi đầu THẬT
    _buoi(canh['b'], _l('2026-08-25T19:30'))
    ev = _lay(canh).data['events']
    kg = [e for e in ev if e['tieuDe'].startswith('Lớp Lop B TG khai giảng')]
    assert len(kg) == 1, ('phải có đúng một mốc khai giảng', [e['tieuDe'] for e in ev])
    assert kg[0]['luc'].startswith('2026-08-23'), 'buổi đã huỷ không được tính là khai giảng'


def test_moc_lam_bai_dem_bai_em_da_nop(canh):
    """"Làm bài" = lần em nộp bài tập ĐẦU TIÊN, kèm số bài đã nộp."""
    b1 = _bai_tap(canh['b'], canh['gv'], 'Bài 1 — hàm số')
    b2 = _bai_tap(canh['b'], canh['gv'], 'Bài 2 — logarit')
    kt = _bai_tap(canh['b'], canh['gv'], 'Kiểm tra giữa kỳ', kind='kiem_tra')
    q1('INSERT INTO submissions (assignment_id, user_id, submitted_at) VALUES (%s, %s, %s) '
       'RETURNING user_id', (b1, canh['em'].id, _l('2026-08-26T21:00')))
    q1('INSERT INTO submissions (assignment_id, user_id, submitted_at) VALUES (%s, %s, %s) '
       'RETURNING user_id', (b2, canh['em'].id, _l('2026-08-28T21:00')))
    # Bài KIỂM TRA không đếm vào "làm bài": nó đã là mốc "Kiểm tra" riêng.
    q1('INSERT INTO submissions (assignment_id, user_id, submitted_at) VALUES (%s, %s, %s) '
       'RETURNING user_id', (kt, canh['em'].id, _l('2026-08-30T21:00')))

    ev = _lay(canh).data['events']
    lb = [e for e in ev if e['tieuDe'].startswith('Bắt đầu làm bài')]
    assert len(lb) == 1, ('phải có đúng một mốc làm bài', [e['tieuDe'] for e in ev])
    assert lb[0]['luc'].startswith('2026-08-26'), 'mốc là lần nộp ĐẦU TIÊN'
    assert '2 bài' in (lb[0]['chiTiet'] or ''), \
        'đếm bài tập đã nộp, KHÔNG tính bài kiểm tra (đã có mốc riêng)'


def test_em_chua_nop_bai_nao_thi_khong_bia_ra_moc_lam_bai(canh):
    ev = _lay(canh).data['events']
    assert not [e for e in ev if e['tieuDe'].startswith('Bắt đầu làm bài')]
