"""Test cơ bản app courseadmin (admin API — 0-test ở bản Flask)."""
import pytest

from common.db import q1

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_api(api, db):
    from accounts.models import User
    row = q1("INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s) RETURNING id",
             ('Admin Tester', 'dj_admin_test@example.com', 'x', 'admin'))
    api.force_authenticate(user=User.objects.get(id=row['id']))
    return api


def test_non_admin_forbidden(auth_api):
    res = auth_api.get('/api/admin/courses')
    assert res.status_code == 403
    assert res.json() == {'error': 'Không có quyền truy cập'}


def test_admin_list_courses(admin_api):
    res = admin_api.get('/api/admin/courses')
    assert res.status_code == 200
    # Bản cũ đòi có khoá 'python' — khoá của ProgrammingEdu, CSDL HSA không có.
    khoa = res.json()['courses']
    assert khoa, 'phải trả về ít nhất một khoá học'
    assert all('id' in c and 'title' in c for c in khoa)


def test_admin_course_crud(admin_api):
    # create
    r = admin_api.post('/api/admin/courses',
                       {'id': 'zz_test_course', 'title': 'Khóa test'}, format='json')
    assert r.status_code == 200
    # duplicate id → 400
    assert admin_api.post('/api/admin/courses',
                          {'id': 'zz_test_course', 'title': 'X'}, format='json').status_code == 400
    # update
    assert admin_api.put('/api/admin/courses/zz_test_course',
                         {'subtitle': 'Sub'}, format='json').status_code == 200
    # lesson create + sync count
    assert admin_api.post('/api/admin/lessons',
                          {'course_id': 'zz_test_course', 'title': 'Bài 1'},
                          format='json').status_code == 200
    assert q1("SELECT lessons FROM courses WHERE id='zz_test_course'")['lessons'] == 1
    # delete course không được khi... (không có enrollment → xóa được sau khi xóa lesson)
    lesson = q1("SELECT id FROM lessons WHERE course_id='zz_test_course' LIMIT 1")
    assert admin_api.delete(f"/api/admin/lessons/{lesson['id']}").status_code == 200
    assert admin_api.delete('/api/admin/courses/zz_test_course').status_code == 200


def test_admin_delete_unknown_404(admin_api):
    assert admin_api.delete('/api/admin/courses/does-not-exist').status_code == 404


# ── Vai trò "Biên tập nội dung" (04/09/2026) ────────────────────────────────
#
# Vai trò này đứng ở một TRỤC KHÁC với Giảng viên / Trợ giảng / Quản lý học vụ:
# ba vai kia định nghĩa theo LỚP, vai này chạm vào GIÁO TRÌNH. Nên bộ kiểm dưới
# đây canh hai chiều, và chiều thứ hai mới là chiều dễ hở:
#
#   ① người biên tập LÀM ĐƯỢC việc soạn bài (nếu không thì vai trò vô dụng);
#   ② người biên tập KHÔNG làm được hai việc vòng đời khoá học, và các vai trò
#      khác KHÔNG lọt vào khu này chỉ vì họ "cũng là nhân sự".
#
# Việc ② quan trọng vì cách hỏng tự nhiên của phân quyền là mở quá tay: đổi
# `IsAdminRole` thành một phép kiểm rộng hơn là cách nhanh nhất để `Giảng viên`
# đọc được luôn mọi thứ khác nằm dưới cùng tiền tố `/api/admin/`.

def _tai_khoan(api, ten, email, vai):
    from accounts.models import User
    row = q1('INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s) '
             'RETURNING id', (ten, email, 'x', vai))
    api.force_authenticate(user=User.objects.get(id=row['id']))
    return api


@pytest.fixture
def bien_tap_api(api, db):
    from common.permissions import ROLE_EDITOR
    return _tai_khoan(api, 'BT Nội dung', 'dj_bientap_tmp@example.com', ROLE_EDITOR)


@pytest.fixture
def giang_vien_api(api, db):
    from common.permissions import ROLE_TEACHER
    return _tai_khoan(api, 'GV Test', 'dj_gv_soan_tmp@example.com', ROLE_TEACHER)


def test_bien_tap_soan_duoc_bai_va_noi_dung(bien_tap_api):
    """① Vai trò phải LÀM ĐƯỢC việc của nó, nếu không nó chỉ là một cái tên.

    ĐỪNG THÊM `admin_api` VÀO THAM SỐ. Bản đầu của phép kiểm này nhận cả hai
    fixture, mà chúng gọi `force_authenticate` trên CÙNG một `APIClient` — nên
    client kết thúc ở vai admin và phép kiểm xanh kể cả khi lùi về mô hình
    chỉ-admin. Đo 04/09: lùi `AdminBase` về `IsCourseOwner` → vẫn 9 passed.
    Một phép kiểm xanh dưới cả hai mô hình là một phép kiểm không kiểm gì.
    """
    r = bien_tap_api.get('/api/admin/courses')
    assert r.status_code == 200, r.json()

    khoa = r.json()['courses'][0]['id']
    assert bien_tap_api.get('/api/admin/courses/%s/lessons' % khoa).status_code == 200

    # Thêm một bài mới rồi sửa lại tiêu đề — đường soạn bài cơ bản nhất.
    r = bien_tap_api.post('/api/admin/lessons',
                          {'course_id': khoa, 'title': 'Bài do biên tập tạo',
                           'sort_order': 999}, format='json')
    assert r.status_code == 200, r.json()
    moi = q1('SELECT id FROM lessons WHERE course_id=%s AND sort_order=999', (khoa,))
    assert moi, 'bài mới phải có trong CSDL'
    assert bien_tap_api.put('/api/admin/lessons/%s' % moi['id'],
                            {'title': 'Đổi tên'}, format='json').status_code == 200
    assert bien_tap_api.get('/api/admin/lessons/%s/content' % moi['id']).status_code == 200


def test_bien_tap_KHONG_tao_va_KHONG_xoa_duoc_khoa(bien_tap_api):
    """② Hai việc vòng đời khoá học giữ cho quản trị viên.

    Xoá một khoá kéo theo `lessons` và tiến độ đã học của người thật; tạo một
    khoá rỗng thì hiện ngay trên danh sách của mọi học viên.
    """
    r = bien_tap_api.post('/api/admin/courses',
                          {'id': 'zz_bt_khong_duoc', 'title': 'X'}, format='json')
    assert r.status_code == 403, r.status_code
    assert not q1("SELECT id FROM courses WHERE id='zz_bt_khong_duoc'"), \
        'bị từ chối rồi thì KHÔNG được ghi gì'

    khoa = q1('SELECT id FROM courses ORDER BY id LIMIT 1')['id']
    assert bien_tap_api.delete('/api/admin/courses/%s' % khoa).status_code == 403
    assert q1('SELECT id FROM courses WHERE id=%s', (khoa,)), 'khoá phải còn nguyên'


def test_bien_tap_KHONG_dat_duoc_tong_so_bai(bien_tap_api):
    """`total_lessons` là đường DUY NHẤT hạ được tổng số bài — mẫu số của mọi
    phần trăm tiến độ. Nhập 10 bài kèm `total_lessons: 10` cho một khoá 27 bài
    là kéo tiến độ của mọi học viên lên gần gấp ba, im lặng."""
    khoa = q1("SELECT id, lessons FROM courses WHERE id='hsa_quantitative'")
    truoc = khoa['lessons']
    r = bien_tap_api.post('/api/admin/courses/%s/import' % khoa['id'],
                          {'lessons': [], 'total_lessons': 3}, format='json')
    assert r.status_code == 403, r.status_code
    assert q1('SELECT lessons FROM courses WHERE id=%s', (khoa['id'],))['lessons'] == truoc, \
        'tổng số bài phải KHÔNG đổi'


def test_giang_vien_KHONG_vao_duoc_khu_soan_giao_trinh(giang_vien_api):
    """Mở quyền cho một vai trò mới KHÔNG được kéo theo các vai trò khác.

    `Giảng viên` là nhân sự của trung tâm và có quyền ở khu Giảng dạy, nhưng khu
    này là giáo trình dùng chung cho MỌI lớp — một người dạy một lớp không vì thế
    mà được sửa bài của cả trung tâm.
    """
    assert giang_vien_api.get('/api/admin/courses').status_code == 403
    assert giang_vien_api.post('/api/admin/lessons',
                               {'course_id': 'hsa_quantitative', 'title': 'X'},
                               format='json').status_code == 403


def test_hoc_vien_van_bi_chan(auth_api):
    """Phép kiểm cũ `test_non_admin_forbidden` nay kiểm một câu YẾU hơn trước:
    trước 04/09 "không phải admin" là một tập, nay là hai. Giữ riêng câu này cho
    Học viên để việc nới quyền không âm thầm nới luôn cho người học."""
    assert auth_api.get('/api/admin/courses').status_code == 403
    assert auth_api.get('/api/admin/lessons/1/content').status_code == 403
