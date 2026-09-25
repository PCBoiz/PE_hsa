"""HỒ SƠ HỌC VIÊN MỞ RỘNG + học vụ cấp tài khoản + đăng nhập bằng username.

Sinh từ bảng yêu cầu của TopHSA (dòng 3 + tab "Nhi" #1, 23/09/2026) và ba quyết
định anh Sơn chốt cùng ngày:

  · mã học viên TỰ SINH (HSA-00001…), không sửa được;
  · người tư vấn chọn từ tài khoản NHÂN SỰ, nguồn tuyển sinh chọn từ danh sách;
  · username tuỳ chọn, học vụ đặt, ô đăng nhập nhận email / SĐT / username;
  · học vụ TẠO được tài khoản và SỬA được hồ sơ — nhưng CHỈ với Học viên.

Chạy trên DB production trong giao dịch cuộn lại (`conftest.py`), lọc về dữ liệu
chính nó dựng.
"""
import pytest
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from accounts.hashers import make_werkzeug_password
from accounts.models import User
from common.db import q1
from common.permissions import ROLE_ACADEMIC, ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER

f = APIRequestFactory()


def _goi(view, method, body=None, ai=None, url='/x', **kw):
    req = (getattr(f, method)(url, body, format='json') if body is not None
           else getattr(f, method)(url))
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(ten, vai, mat_khau='x'):
    r = q1('INSERT INTO users (name, email, password, role, streak) '
           'VALUES (%s, %s, %s, %s, 0) RETURNING id',
           (ten, '%s_hs@example.com' % ten.replace(' ', '_').lower(),
            make_werkzeug_password(mat_khau) if mat_khau != 'x' else 'x', vai))
    return User.objects.get(id=r['id'])


@pytest.fixture
def canh(db):
    from teaching.ho_so import cap_ma_hoc_vien
    hocvu = _nguoi('HocVu HS', ROLE_ACADEMIC)
    gv = _nguoi('GV HS', ROLE_TEACHER)
    tg = _nguoi('TG HS', ROLE_ASSISTANT)
    em = _nguoi('Em HS', ROLE_STUDENT)
    cap_ma_hoc_vien(em.id)
    lop = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
             "VALUES ('Lop HS', 'hsa_quantitative', %s, 'active') RETURNING id", (gv.id,))['id']
    q1('INSERT INTO class_members (class_id, user_id) VALUES (%s, %s) RETURNING id', (lop, em.id))
    return {'hocvu': hocvu, 'gv': gv, 'tg': tg, 'em': em, 'lop': lop}


# ── Hồ sơ: đọc / sửa ─────────────────────────────────────────────────────────

def test_hoc_vu_doc_ho_so_hoc_vien_co_ma_va_danh_sach_chon(canh):
    from teaching.ho_so import HoSoHocVienView
    r = _goi(HoSoHocVienView, 'get', ai=canh['hocvu'], user_id=canh['em'].id)
    assert r.status_code == 200, r.data
    hs = r.data['profile']
    assert hs['studentCode'].startswith('HSA-') and len(hs['studentCode']) == 9
    # Danh sách chọn đi CÙNG phản hồi: giao diện không phải gọi thêm lượt nào.
    assert {s['ma'] for s in r.data['sources']} >= {'facebook', 'gioi_thieu', 'khac'}
    tu_van = {c['id'] for c in r.data['consultants']}
    assert canh['gv'].id in tu_van and canh['hocvu'].id in tu_van
    assert canh['em'].id not in tu_van, 'người tư vấn phải là NHÂN SỰ, không phải học viên'


def test_hoc_vu_sua_ho_so_va_ghi_nhat_ky(canh):
    from teaching.ho_so import HoSoHocVienView
    r = _goi(HoSoHocVienView, 'patch', {
        'school': 'THPT Chu Văn An', 'schoolGrade': '12', 'region': 'Hà Nội',
        'consultantId': canh['gv'].id, 'enrollSource': 'facebook',
        'studyGoal': 'Đạt 100 điểm HSA', 'aspiration': 'ĐH Bách khoa — CNTT',
    }, ai=canh['hocvu'], user_id=canh['em'].id)
    assert r.status_code == 200, r.data
    dong = q1('SELECT school, school_grade, region, consultant_id, enroll_source, study_goal, aspiration '
              'FROM users WHERE id=%s', (canh['em'].id,))
    assert dong == {'school': 'THPT Chu Văn An', 'school_grade': '12', 'region': 'Hà Nội',
                    'consultant_id': canh['gv'].id, 'enroll_source': 'facebook',
                    'study_goal': 'Đạt 100 điểm HSA', 'aspiration': 'ĐH Bách khoa — CNTT'}
    nk = q1("SELECT action FROM admin_audit WHERE target_type='user' AND target_id=%s "
            "ORDER BY id DESC LIMIT 1", (str(canh['em'].id),))
    assert nk and nk['action'] == 'user.profile'


def test_ma_hoc_vien_khong_sua_duoc(canh):
    from teaching.ho_so import HoSoHocVienView
    truoc = q1('SELECT student_code FROM users WHERE id=%s', (canh['em'].id,))['student_code']
    r = _goi(HoSoHocVienView, 'patch', {'studentCode': 'HSA-99999', 'region': 'Huế'},
             ai=canh['hocvu'], user_id=canh['em'].id)
    assert r.status_code == 200
    assert q1('SELECT student_code FROM users WHERE id=%s', (canh['em'].id,))['student_code'] == truoc


@pytest.mark.parametrize('than,truong', [
    ({'enrollSource': 'tivi'}, 'enrollSource'),
    ({'username': 'ab'}, 'username'),                    # quá ngắn
    ({'username': 'Nguyen Van A'}, 'username'),          # có khoảng trắng
    ({'username': '0912345678'}, 'username'),            # toàn số — lẫn với SĐT
    ({'name': '   '}, 'name'),                            # tên bắt buộc
    ({'birthday': '31/12/2008'}, 'birthday'),             # sai dạng ngày
    ({'birthday': '2099-01-01'}, 'birthday'),             # ngày trong tương lai
    ({'birthday': '20080517'}, 'birthday'),               # `fromisoformat` 3.11 nhận dạng này
    ({'parentPhone': '12345'}, 'parentPhone'),
    ({'parentEmail': 'khong-phai-email'}, 'parentEmail'),
])
def test_tu_choi_gia_tri_khong_hop_le(canh, than, truong):
    from teaching.ho_so import HoSoHocVienView
    r = _goi(HoSoHocVienView, 'patch', than, ai=canh['hocvu'], user_id=canh['em'].id)
    assert r.status_code == 400 and truong in r.data.get('errors', {}), r.data


def test_hoc_vu_sua_ten_ngay_sinh_lien_he_phu_huynh_thi_khoa_lien_he(canh):
    """Liên hệ phụ huynh do TRUNG TÂM nhập thì khoá (§47) — cùng luật với ô dán
    cả lớp: từ đây em chỉ điền được ô còn trống, sửa phải qua học vụ."""
    from teaching.ho_so import HoSoHocVienView
    r = _goi(HoSoHocVienView, 'patch', {
        'name': 'Nguyễn Văn Em', 'birthday': '2008-05-17',
        'parentName': 'Mẹ Em', 'parentPhone': '0912 345 678', 'parentEmail': 'Me.Em@Example.com',
    }, ai=canh['hocvu'], user_id=canh['em'].id)
    assert r.status_code == 200, r.data
    d = q1('SELECT name, birthday, parent_name, parent_phone, parent_email, '
           'parent_contact_locked_at, parent_contact_locked_by FROM users WHERE id=%s', (canh['em'].id,))
    # `birthday` là cột TEXT — cùng dạng chuỗi mà Cài đặt ghi.
    assert d['name'] == 'Nguyễn Văn Em' and d['birthday'] == '2008-05-17'
    # Đọc lại qua GET: bản đầu gọi `.isoformat()` trên chuỗi và trả 500.
    g = _goi(HoSoHocVienView, 'get', ai=canh['hocvu'], user_id=canh['em'].id)
    assert g.status_code == 200 and g.data['profile']['birthday'] == '2008-05-17'
    # Ghi bản ĐÃ chuẩn hoá — cùng luật với Cài đặt và ô dán cả lớp.
    assert (d['parent_name'], d['parent_phone'], d['parent_email']) == \
        ('Mẹ Em', '0912345678', 'me.em@example.com')
    assert d['parent_contact_locked_at'] is not None
    assert d['parent_contact_locked_by'] == canh['hocvu'].id


def test_xoa_trong_lien_he_phu_huynh_ghi_chuoi_rong(canh):
    """Ba cột phụ huynh là `NOT NULL DEFAULT ''` (khác các cột §51). Bản đầu ghi
    None khi xoá trống một ô → 500 — e2e bắt được lúc trả lại hồ sơ 23/09/2026."""
    from teaching.ho_so import HoSoHocVienView
    assert _goi(HoSoHocVienView, 'patch', {'parentName': 'Mẹ', 'parentPhone': '0912345678',
                                           'parentEmail': 'me@example.com'},
                ai=canh['hocvu'], user_id=canh['em'].id).status_code == 200
    r = _goi(HoSoHocVienView, 'patch', {'parentName': '', 'parentPhone': '', 'parentEmail': None},
             ai=canh['hocvu'], user_id=canh['em'].id)
    assert r.status_code == 200, r.data
    d = q1('SELECT parent_name, parent_phone, parent_email FROM users WHERE id=%s', (canh['em'].id,))
    assert d == {'parent_name': '', 'parent_phone': '', 'parent_email': ''}


def test_sua_truong_khac_khong_khoa_lien_he_phu_huynh(canh):
    from teaching.ho_so import HoSoHocVienView
    assert _goi(HoSoHocVienView, 'patch', {'region': 'Huế'},
                ai=canh['hocvu'], user_id=canh['em'].id).status_code == 200
    d = q1('SELECT parent_contact_locked_at FROM users WHERE id=%s', (canh['em'].id,))
    assert d['parent_contact_locked_at'] is None, 'không đụng liên hệ phụ huynh thì không được khoá'


def test_nguoi_tu_van_phai_la_nhan_su(canh):
    from teaching.ho_so import HoSoHocVienView
    em2 = _nguoi('Em Hai HS', ROLE_STUDENT)
    r = _goi(HoSoHocVienView, 'patch', {'consultantId': em2.id}, ai=canh['hocvu'], user_id=canh['em'].id)
    assert r.status_code == 400 and 'consultantId' in r.data['errors']


def test_username_trung_khong_phan_biet_hoa_thuong(canh):
    from teaching.ho_so import HoSoHocVienView
    em2 = _nguoi('Em Ba HS', ROLE_STUDENT)
    assert _goi(HoSoHocVienView, 'patch', {'username': 'an.nguyen'},
                ai=canh['hocvu'], user_id=canh['em'].id).status_code == 200
    r = _goi(HoSoHocVienView, 'patch', {'username': 'AN.Nguyen'}, ai=canh['hocvu'], user_id=em2.id)
    assert r.status_code == 400 and 'username' in r.data['errors']


def test_hoc_vu_khong_dung_duoc_ho_so_nhan_su(canh):
    from teaching.ho_so import HoSoHocVienView
    for ai_bi_sua in (canh['gv'], canh['tg']):
        assert _goi(HoSoHocVienView, 'get', ai=canh['hocvu'], user_id=ai_bi_sua.id).status_code == 403
        assert _goi(HoSoHocVienView, 'patch', {'region': 'x'},
                    ai=canh['hocvu'], user_id=ai_bi_sua.id).status_code == 403


def test_giang_vien_khong_vao_duoc_duong_quan_tri(canh):
    from teaching.ho_so import HoSoHocVienView
    assert _goi(HoSoHocVienView, 'get', ai=canh['gv'], user_id=canh['em'].id).status_code == 403


# ── Giảng viên: chỉ mục tiêu + nguyện vọng, chỉ em trong lớp mình ────────────

def test_giang_vien_sua_muc_tieu_nguyen_vong_cua_em_trong_lop(canh):
    from teaching.ho_so import MucTieuHocVienView
    r = _goi(MucTieuHocVienView, 'patch',
             {'studyGoal': 'Lên 90 điểm', 'aspiration': 'Y Hà Nội', 'region': 'KHÔNG ĐƯỢC ĐỔI'},
             ai=canh['gv'], class_id=canh['lop'], user_id=canh['em'].id)
    assert r.status_code == 200, r.data
    d = q1('SELECT study_goal, aspiration, region FROM users WHERE id=%s', (canh['em'].id,))
    assert d['study_goal'] == 'Lên 90 điểm' and d['aspiration'] == 'Y Hà Nội'
    assert d['region'] is None, 'giảng viên KHÔNG được sửa trường ngoài mục tiêu/nguyện vọng'


def test_giang_vien_khong_sua_duoc_em_ngoai_lop(canh):
    from teaching.ho_so import MucTieuHocVienView
    em_ngoai = _nguoi('Em Ngoai HS', ROLE_STUDENT)
    r = _goi(MucTieuHocVienView, 'patch', {'studyGoal': 'x'},
             ai=canh['gv'], class_id=canh['lop'], user_id=em_ngoai.id)
    assert r.status_code == 404


def test_giang_vien_doc_muc_tieu_cua_em_trong_lop(canh):
    """Màn hình của giảng viên phải ĐỌC được giá trị hiện có — không thì ô sửa
    luôn trống và một lần Lưu là xoá trắng điều học vụ đã ghi."""
    from teaching.ho_so import MucTieuHocVienView
    q1("UPDATE users SET study_goal='95 điểm', aspiration='Ngoại thương' WHERE id=%s RETURNING id",
       (canh['em'].id,))
    r = _goi(MucTieuHocVienView, 'get', ai=canh['gv'], class_id=canh['lop'], user_id=canh['em'].id)
    assert r.status_code == 200, r.data
    assert (r.data['studyGoal'], r.data['aspiration']) == ('95 điểm', 'Ngoại thương')
    assert r.data['studentCode'].startswith('HSA-')
    em_ngoai = _nguoi('Em Ngoai Doc HS', ROLE_STUDENT)
    assert _goi(MucTieuHocVienView, 'get', ai=canh['gv'], class_id=canh['lop'],
                user_id=em_ngoai.id).status_code == 404


def test_tro_giang_trong_lop_khong_sua_duoc_muc_tieu(canh):
    """Trợ giảng THẤY lớp (là thành viên) nhưng không sửa hồ sơ em — cùng cổng
    với báo cáo phụ huynh, nơi đặt ô sửa này (`IsSeniorTeachingStaff`)."""
    from teaching.ho_so import MucTieuHocVienView
    q1('INSERT INTO class_members (class_id, user_id) VALUES (%s, %s) RETURNING id',
       (canh['lop'], canh['tg'].id))
    r = _goi(MucTieuHocVienView, 'patch', {'studyGoal': 'TG ghi'},
             ai=canh['tg'], class_id=canh['lop'], user_id=canh['em'].id)
    assert r.status_code == 403
    assert q1('SELECT study_goal FROM users WHERE id=%s', (canh['em'].id,))['study_goal'] is None


# ── Học vụ cấp tài khoản — CHỈ học viên, và mã được cấp ngay ─────────────────

def test_hoc_vu_tao_hoc_vien_va_co_ma_ngay(canh):
    from teaching.views import AdminCreateUserView
    r = _goi(AdminCreateUserView, 'post', {'name': 'Em Moi HS', 'email': 'em_moi_hs@example.com'},
             ai=canh['hocvu'])
    assert r.status_code in (200, 201), r.data
    d = q1("SELECT role, student_code FROM users WHERE lower(email)='em_moi_hs@example.com'")
    assert d['role'] == ROLE_STUDENT and (d['student_code'] or '').startswith('HSA-')


def test_hoc_vu_khong_tao_duoc_nhan_su(canh):
    from teaching.views import AdminCreateUserView
    r = _goi(AdminCreateUserView, 'post',
             {'name': 'GV Lau HS', 'email': 'gv_lau_hs@example.com', 'role': ROLE_TEACHER},
             ai=canh['hocvu'])
    assert r.status_code == 403
    assert not q1("SELECT 1 FROM users WHERE lower(email)='gv_lau_hs@example.com'")


def test_hoc_vu_nhap_hang_loat_hoc_vien_co_ma(canh):
    from teaching.admin_users import AdminBulkCreateUsersView
    r = _goi(AdminBulkCreateUsersView, 'post',
             {'text': 'Em Lo Mot, em_lo1_hs@example.com\nEm Lo Hai, em_lo2_hs@example.com',
              'role': ROLE_STUDENT, 'dry_run': False}, ai=canh['hocvu'])
    assert r.status_code in (200, 201), r.data
    ma = [d['student_code'] for d in __import__('common.db', fromlist=['q']).q(
        "SELECT student_code FROM users WHERE lower(email) IN ('em_lo1_hs@example.com','em_lo2_hs@example.com')")]
    assert len(ma) == 2 and all((m or '').startswith('HSA-') for m in ma)


def test_hoc_vu_khong_nhap_hang_loat_nhan_su(canh):
    from teaching.admin_users import AdminBulkCreateUsersView
    r = _goi(AdminBulkCreateUsersView, 'post',
             {'text': 'GV Lo, gv_lo_hs@example.com', 'role': ROLE_TEACHER, 'dry_run': False},
             ai=canh['hocvu'])
    assert r.status_code == 403


def test_hoc_vu_xem_danh_sach_chi_thay_hoc_vien_va_tim_theo_ma(canh):
    from teaching.admin_users import AdminUsersView
    ma = q1('SELECT student_code FROM users WHERE id=%s', (canh['em'].id,))['student_code']
    r = _goi(AdminUsersView, 'get', ai=canh['hocvu'], url='/x?q=%s' % ma)
    assert r.status_code == 200, r.data
    assert [u['id'] for u in r.data['users']] == [canh['em'].id]
    r2 = _goi(AdminUsersView, 'get', ai=canh['hocvu'], url='/x?q=HS')
    assert r2.status_code == 200
    assert all(u['role'] == ROLE_STUDENT for u in r2.data['users']), \
        'học vụ chỉ được thấy tài khoản học viên ở màn Tài khoản'


# ── Đăng nhập bằng username ──────────────────────────────────────────────────

# ── §63: lớp trung tâm, khóa đã mở, tình trạng học tập/học phí (25/09/2026) ──

def test_ho_so_co_lop_khoa_da_mo_va_trang_thai_hoc_tap(canh):
    """Yêu cầu TopHSA 3.2: "Lớp" = lớp TRUNG TÂM (không phải lớp ở trường),
    "Khóa học đã đăng ký" lấy QUA LỚP (không phải `enrollments`, đã đổi nghĩa
    từ 1.3), "Tình trạng học tập" tính từ `class_members`/`classes`."""
    from teaching.ho_so import HoSoHocVienView
    r = _goi(HoSoHocVienView, 'get', ai=canh['hocvu'], user_id=canh['em'].id)
    assert r.status_code == 200, r.data
    hs = r.data['profile']
    assert [c['id'] for c in hs['classes']] == [canh['lop']]
    lop = hs['classes'][0]
    assert lop['name'] == 'Lop HS'
    assert lop['classType'] == 'nhom'
    assert lop['siSo'] == 1
    assert lop['teacherId'] == canh['gv'].id
    assert {c['id'] for c in hs['enrolledCourses']} == {'hsa_quantitative'}
    assert hs['studyStatus'] == 'Đang học'
    assert hs['tuitionStatus'] is None
    assert set(r.data['tuitionStatuses']) == {'Đã đóng', 'Sắp hết', 'Hết', 'Bảo lưu'}


def test_ho_so_khong_co_lop_thi_chua_xep_lop(canh):
    from teaching.ho_so import HoSoHocVienView
    em2 = _nguoi('Em Chua Xep HS', ROLE_STUDENT)
    r = _goi(HoSoHocVienView, 'get', ai=canh['hocvu'], user_id=em2.id)
    assert r.status_code == 200, r.data
    hs = r.data['profile']
    assert hs['classes'] == [] and hs['enrolledCourses'] == []
    assert hs['studyStatus'] == 'Chưa xếp lớp'


def test_lop_tam_dung_thi_hoc_vien_tam_dung(canh):
    q1("UPDATE classes SET status='paused' WHERE id=%s RETURNING id", (canh['lop'],))
    from teaching.ho_so import HoSoHocVienView
    r = _goi(HoSoHocVienView, 'get', ai=canh['hocvu'], user_id=canh['em'].id)
    assert r.data['profile']['studyStatus'] == 'Tạm dừng'


@pytest.mark.parametrize('leave_reason,ky_vong', [
    ('completed', 'Đã xong'),
    ('reserved', 'Bảo lưu'),
    ('dropped', 'Đã nghỉ học'),
])
def test_trang_thai_hoc_tap_theo_ly_do_roi_lop(canh, leave_reason, ky_vong):
    q1("UPDATE class_members SET left_at=now(), leave_reason=%s "
       "WHERE class_id=%s AND user_id=%s RETURNING id",
       (leave_reason, canh['lop'], canh['em'].id))
    from teaching.ho_so import HoSoHocVienView
    r = _goi(HoSoHocVienView, 'get', ai=canh['hocvu'], user_id=canh['em'].id)
    assert r.data['profile']['studyStatus'] == ky_vong
    assert r.data['profile']['classes'] == [], 'đã rời lớp thì không còn trong danh sách lớp hiện tại'


def test_khoa_hoc_da_dang_ky_khi_lop_khong_gan_mon_la_ca_ba_mon(canh):
    """`classes.course_id IS NULL` = lớp học cả ba môn (`courses/truy_cap.py`
    `BA_MON`) — hồ sơ phải liệt kê đủ ba, không chỉ một."""
    q1("UPDATE classes SET course_id=NULL WHERE id=%s RETURNING id", (canh['lop'],))
    from teaching.ho_so import HoSoHocVienView
    r = _goi(HoSoHocVienView, 'get', ai=canh['hocvu'], user_id=canh['em'].id)
    assert {c['id'] for c in r.data['profile']['enrolledCourses']} == \
        {'hsa_quantitative', 'hsa_verbal', 'hsa_science'}


def test_hoc_vu_sua_tinh_trang_hoc_phi(canh):
    from teaching.ho_so import HoSoHocVienView
    r = _goi(HoSoHocVienView, 'patch', {'tuitionStatus': 'Sắp hết'},
             ai=canh['hocvu'], user_id=canh['em'].id)
    assert r.status_code == 200, r.data
    assert q1('SELECT tuition_status FROM users WHERE id=%s',
              (canh['em'].id,))['tuition_status'] == 'Sắp hết'
    assert r.data['profile']['tuitionStatus'] == 'Sắp hết'


def test_tinh_trang_hoc_phi_tu_choi_gia_tri_ngoai_danh_sach(canh):
    from teaching.ho_so import HoSoHocVienView
    r = _goi(HoSoHocVienView, 'patch', {'tuitionStatus': 'Nợ nần'},
             ai=canh['hocvu'], user_id=canh['em'].id)
    assert r.status_code == 400 and 'tuitionStatus' in r.data['errors']
    assert q1('SELECT tuition_status FROM users WHERE id=%s', (canh['em'].id,))['tuition_status'] is None


def test_hai_lop_gia_su_khac_si_so_khong_lam_lan_nhau(canh):
    """Yêu cầu 25/09: lớp gia sư 1 dạy 1/1 dạy 3/1 dạy 6 và lớp nhóm ~20 em CÙNG
    tồn tại — `si_so` phải đếm ĐÚNG cho từng lớp, không đọc nhầm `capacity`."""
    gv2 = _nguoi('GV Gia Su HS', ROLE_TEACHER)
    lop_1_1 = q1("INSERT INTO classes (name, course_id, teacher_id, status, class_type) "
                 "VALUES ('1-1 HS', 'hsa_verbal', %s, 'active', 'gia_su') RETURNING id", (gv2.id,))['id']
    em2 = _nguoi('Em Gia Su HS', ROLE_STUDENT)
    q1('INSERT INTO class_members (class_id, user_id) VALUES (%s, %s) RETURNING id', (lop_1_1, em2.id))

    from teaching.ho_so import HoSoHocVienView
    r_nhom = _goi(HoSoHocVienView, 'get', ai=canh['hocvu'], user_id=canh['em'].id)
    r_gs = _goi(HoSoHocVienView, 'get', ai=canh['hocvu'], user_id=em2.id)
    lop_nhom = r_nhom.data['profile']['classes'][0]
    lop_gs = r_gs.data['profile']['classes'][0]
    assert lop_nhom['classType'] == 'nhom' and lop_nhom['siSo'] == 1
    assert lop_gs['classType'] == 'gia_su' and lop_gs['siSo'] == 1


def test_dang_nhap_bang_username(canh):
    em = _nguoi('Em Dang Nhap HS', ROLE_STUDENT, mat_khau='MatKhau#2026')
    q1("UPDATE users SET username='em.dangnhap' WHERE id=%s RETURNING id", (em.id,))
    c = APIClient()
    r = c.post('/auth/login', {'email': 'EM.DangNhap', 'password': 'MatKhau#2026'}, format='json')
    assert r.status_code == 200, r.content
    r_sai = c.post('/auth/login', {'email': 'em.dangnhap', 'password': 'sai'}, format='json')
    assert r_sai.status_code == 401
