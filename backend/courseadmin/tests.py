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


# ── Xoá một bài là xoá TIẾN ĐỘ ĐÃ HỌC của người thật (vá 04/09/2026) ────────
#
# `lesson_progress_lesson_fk` là ON DELETE CASCADE (đo trên CSDL thật), nên câu
# DELETE một dòng ở `AdminLessonDetailView` kéo theo mọi dòng `lesson_progress`
# trỏ tới bài ấy — điểm, XP, ngày hoàn thành. Đo 04/09: bài id=1 đang treo 4
# dòng của học viên thật.
#
# Cửa xoá KHOÁ đã có hàng rào đúng loại này từ đầu (còn `enrollments` thì 409).
# Cửa xoá BÀI thì không — và từ 04/09 nó mở cho vai `Biên tập nội dung`.

def _bai_co_tien_do(db):
    """Trả id một bài ĐANG có tiến độ học thật, hoặc None."""
    from common.db import q1
    return q1('''SELECT l.id FROM lessons l
                 JOIN lesson_progress p ON p.lesson_id = l.id
                 GROUP BY l.id ORDER BY COUNT(*) DESC LIMIT 1''')


def test_bien_tap_KHONG_xoa_duoc_bai_da_co_nguoi_hoc(bien_tap_api, db):
    """Vai biên tập không bao giờ xoá được số liệu học tập của người thật."""
    from common.db import q1
    bai = _bai_co_tien_do(db)
    if not bai:
        pytest.skip('CSDL chưa có bài nào có tiến độ để dựng cảnh')

    truoc = q1('SELECT COUNT(*) AS n FROM lesson_progress WHERE lesson_id=%s',
               (bai['id'],))['n']
    r = bien_tap_api.delete('/api/admin/lessons/%s' % bai['id'])
    assert r.status_code == 403, r.status_code
    assert 'lượt học' in r.json()['error']
    assert q1('SELECT COUNT(*) AS n FROM lesson_progress WHERE lesson_id=%s',
              (bai['id'],))['n'] == truoc, 'bị từ chối rồi thì KHÔNG được xoá dòng nào'
    assert q1('SELECT id FROM lessons WHERE id=%s', (bai['id'],)), 'bài phải còn'


def test_quan_tri_phai_XAC_NHAN_moi_xoa_duoc_bai_co_tien_do(admin_api, db):
    """Quản trị viên làm được, nhưng phải nói rõ ý định — câu xác nhận trên giao
    diện chỉ hỏi "Xoá bài ...?" và không một chữ nào về tiến độ học viên."""
    from common.db import q1
    bai = _bai_co_tien_do(db)
    if not bai:
        pytest.skip('CSDL chưa có bài nào có tiến độ để dựng cảnh')

    r = admin_api.delete('/api/admin/lessons/%s' % bai['id'])
    assert r.status_code == 409, r.status_code
    assert r.json().get('needsConfirm') is True
    assert r.json().get('progressRows', 0) > 0
    assert q1('SELECT id FROM lessons WHERE id=%s', (bai['id'],)), 'chưa xác nhận thì bài phải còn'


def test_bai_KHONG_co_tien_do_thi_xoa_binh_thuong(bien_tap_api, db):
    """Hàng rào không được chặn việc dọn một bài vừa tạo nhầm."""
    from common.db import q1
    r = bien_tap_api.post('/api/admin/lessons',
                          {'course_id': 'hsa_quantitative', 'title': 'Bài tạo nhầm',
                           'sort_order': 998}, format='json')
    assert r.status_code == 200, r.json()
    moi = q1('SELECT id FROM lessons WHERE course_id=%s AND sort_order=998',
             ('hsa_quantitative',))
    assert moi
    assert bien_tap_api.delete('/api/admin/lessons/%s' % moi['id']).status_code == 200
    assert not q1('SELECT id FROM lessons WHERE id=%s', (moi['id'],))


def test_moi_viec_o_khu_soan_giao_trinh_deu_vao_nhat_ky(bien_tap_api, db):
    """Khu này KHÔNG ghi một dòng nhật ký nào cho tới 04/09.

    Chấp nhận được khi người soạn chính là quản trị viên; sai hẳn từ lúc có vai
    `Biên tập nội dung`. Không ghi thì câu "ai xoá bài này, lúc nào" không trả
    lời được — mà đó đúng là câu sẽ được hỏi.
    """
    from common.db import q1
    truoc = q1('SELECT COUNT(*) AS n FROM admin_audit')['n']
    r = bien_tap_api.post('/api/admin/lessons',
                          {'course_id': 'hsa_quantitative', 'title': 'Bài ghi nhật ký',
                           'sort_order': 997}, format='json')
    assert r.status_code == 200, r.json()
    assert q1('SELECT COUNT(*) AS n FROM admin_audit')['n'] > truoc, \
        'thêm một bài mà nhật ký kiểm toán không có dòng nào'
    dong = q1("SELECT action, target_label, actor_role FROM admin_audit "
              "ORDER BY id DESC LIMIT 1")
    assert dong['action'] == 'lesson.create', dong
    assert dong['target_label'] == 'Bài ghi nhật ký'
    assert dong['actor_role'] == 'Biên tập nội dung', dong


# ── Trường khoá học đổ THÔ vào innerHTML, kể cả TRANG CHỦ (vá 04/09/2026) ───
#
# `main.js:817` `'<img src="/' + c.image + '" alt="' + c.title + '"'`,
# `main.js:828` `c.tag`, `:832` `c.description`, `:819` `c.color` vào
# `linear-gradient(...)`, và `pages/landing.inline.js:74` `c.title` —
# TRANG CHỦ, không cần đăng nhập, khách vãng lai cũng chạy.
#
# `PUT /api/admin/courses/<id>` mở cho vai `Biên tập nội dung` từ 04/09 — vai
# sinh ra để KHÔNG phải cấp quyền quản trị cho người gõ nội dung. Không kiểm ở
# đường ghi thì vai ấy leo thẳng lên quyền quản trị qua trình duyệt người khác.
#
# Chặn ở ĐƯỜNG GHI là đòn bẩy: `c.color` một mình xuất hiện ở SÁU chỗ dựng CSS
# trong `main.js`. Ép nó là hex thì cả sáu an toàn cùng lúc, và chỗ thứ bảy mọc
# ra ngày mai cũng thế.

def _khoa_con_nguyen(cid, truoc):
    from common.db import q1
    assert q1('SELECT title FROM courses WHERE id=%s', (cid,))['title'] == truoc, \
        'bị từ chối rồi thì KHÔNG được ghi gì'


def test_the_treo_ma_trong_ten_khoa_bi_chan(bien_tap_api):
    from common.db import q1
    cid = 'hsa_quantitative'
    truoc = q1('SELECT title FROM courses WHERE id=%s', (cid,))['title']
    r = bien_tap_api.put('/api/admin/courses/%s' % cid,
                         {'title': '<img src=x onerror=alert(1)>'}, format='json')
    assert r.status_code == 400, r.status_code
    _khoa_con_nguyen(cid, truoc)


def test_mau_phai_la_hex(bien_tap_api):
    """`color` đi thẳng vào `linear-gradient(...)`, tức là CSS. Một chuỗi tự do
    ở đó đóng được dấu ngoặc rồi viết tiếp luật CSS của riêng nó."""
    from common.db import q1
    cid = 'hsa_quantitative'
    truoc = q1('SELECT title FROM courses WHERE id=%s', (cid,))['title']
    for xau in ('red;}body{display:none', 'url(javascript:alert(1))', '#12345678901'):
        r = bien_tap_api.put('/api/admin/courses/%s' % cid, {'color': xau}, format='json')
        assert r.status_code == 400, '%r lọt qua' % xau
    _khoa_con_nguyen(cid, truoc)


def test_duong_dan_anh_khong_duoc_thoat_ra_ngoai(bien_tap_api):
    """`image` nằm trong `src="/…"`. Chặn cả lược đồ lẫn đi lùi thư mục."""
    for xau in ('x" onerror="alert(1)', 'javascript:alert(1)',
                '../../etc/passwd', 'https://kẻ-khác/x.png'):
        r = bien_tap_api.put('/api/admin/courses/hsa_quantitative',
                             {'image': xau}, format='json')
        assert r.status_code == 400, '%r lọt qua' % xau


def test_ba_khoa_dang_chay_VAN_hop_le(bien_tap_api):
    """Bộ lọc không được chặn oan dữ liệu đang chạy — đó là cách một hàng rào
    an toàn biến thành một sự cố."""
    from common.db import q1
    from courseadmin.views import _COURSE_FIELDS, _clean_course_payload
    rows = q1('SELECT COUNT(*) AS n FROM courses')['n']
    assert rows >= 3

    from common.db import q
    for row in q('SELECT id, %s FROM courses' % ', '.join(_COURSE_FIELDS)):
        cid = row.pop('id')
        _, loi = _clean_course_payload(row)
        assert not loi, 'chặn oan khoá %s: %s' % (cid, loi)


def test_sua_khoa_binh_thuong_van_chay(bien_tap_api):
    """Hàng rào không được cản việc sửa nội dung thật — có in đậm là bình thường."""
    from common.db import q1
    cid = 'hsa_quantitative'
    cu = q1('SELECT title, subtitle FROM courses WHERE id=%s', (cid,))
    r = bien_tap_api.put('/api/admin/courses/%s' % cid,
                         {'subtitle': 'Toán & xử lý <strong>số liệu</strong>',
                          'color': '#4C1D95'}, format='json')
    assert r.status_code == 200, r.json()
    assert q1('SELECT subtitle FROM courses WHERE id=%s', (cid,))['subtitle'] \
        == 'Toán & xử lý <strong>số liệu</strong>'
    # Trả lại như cũ trong cùng giao dịch (conftest cuộn lại, nhưng nói rõ ý định).
    bien_tap_api.put('/api/admin/courses/%s' % cid,
                     {'subtitle': cu['subtitle'] or ''}, format='json')
