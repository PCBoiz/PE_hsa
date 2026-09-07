"""ĐÚNG VAI, SAI NGƯỜI — hàng rào thứ hai, thứ ma trận vai không bắt được.

Chạy trên DB thật, mọi thứ nằm trong giao dịch được CUỘN LẠI (xem `conftest.py`).

── VÌ SAO CẦN TỆP RIÊNG (07/09/2026) ────────────────────────────────────────

`tests_ma_tran_quyen.py` trả lời câu "vai này có vào được cửa này không". Nó
KHÔNG trả lời được câu nguy hiểm hơn: **hai người CÙNG VAI thì có chạm được vào
đồ của nhau không.**

Với sản phẩm này câu ấy nặng hơn câu kia. Sáu mươi view chỉ khai
`IsAuthenticated` — đúng như thiết kế, vì chúng phục vụ dữ liệu của chính người
đăng nhập. Nhưng nhiều view trong số đó nhận MỘT ID trên đường dẫn
(`quizzes/<id>`, `study-plan/items/<id>`, `posts/<id>`), và với chúng thì
"đúng người" không nằm ở tầng quyền — nó nằm trong thân view, ở một mệnh đề
`WHERE user_id = %s` mà quên thì không có gì kêu lên.

Cùng lối ấy ở khu giảng dạy: `IsTeachingStaff` cho giảng viên đi qua cửa, còn
`can_see_class` mới là thứ giữ giảng viên A khỏi lớp của giảng viên B.

── HAI HỌ LỖI ĐỀU TRẢ HTTP 200 KHI HỎNG ────────────────────────────────────

Không cái nào đổ lỗi. Học viên B mở được bài quiz của học viên A thì màn hình
hiện ra một bài quiz bình thường. Giảng viên B mở hồ sơ học viên lớp khác thì
thấy một hồ sơ bình thường. Người phát hiện ra sẽ không phải là mình.

── VÌ SAO Ở ĐÂY CÓ GHI, KHÁC `tests_ma_tran_quyen` ─────────────────────────

Ma trận vai chỉ gửi GET vì nó không cần đối tượng thật. Ở đây thì cần: phải có
bài quiz CỦA A thì mới thử được việc B mở nó. Mọi dòng ghi nằm trong giao dịch
`conftest.py` cuộn lại — cùng cơ chế `tests_parent_link.py` đã dùng từ đầu.
"""
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.clock import local_now
from common.db import q1
from common.permissions import ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER
from notifications.views import FeedReadView
from quizzes.views import QuizView
from stats.views import StudyPlanItemView
from teaching.parent_report import ParentReportView
from teaching.views import TeachClassDetailView, TeachStudentView

f = APIRequestFactory()


def _goi(view, method, ai, body=None, **kw):
    req = (getattr(f, method)('/x', body, format='json') if body is not None
           else getattr(f, method)('/x'))
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(ten, vai):
    row = q1('INSERT INTO users (name, email, password, role, streak) '
             "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             (ten, '%s_dck@example.com' % ten.replace(' ', '_'), vai))
    return User.objects.get(id=row['id'])


# ══ HỌC VIÊN B vs ĐỒ CỦA HỌC VIÊN A ═════════════════════════════════════════

@pytest.fixture
def hai_em(db):
    return {'a': _nguoi('Em A', ROLE_STUDENT), 'b': _nguoi('Em B', ROLE_STUDENT)}


@pytest.mark.django_db
def test_hoc_vien_khong_mo_duoc_quiz_cua_ban(hai_em):
    """Bài quiz mang câu hỏi VÀ đáp án. Mở được của người khác là lộ đề."""
    d = q1("""INSERT INTO quizzes (user_id, course_id, status, questions_json)
              VALUES (%s, 'hsa_quantitative', 'active', '[]'::jsonb)
              RETURNING id""", (hai_em['a'].id,))

    cua_minh = _goi(QuizView, 'get', hai_em['a'], quiz_id=d['id'])
    assert cua_minh.status_code == 200, cua_minh.data

    cua_ban = _goi(QuizView, 'get', hai_em['b'], quiz_id=d['id'])
    assert cua_ban.status_code == 404, (cua_ban.status_code, cua_ban.data)


@pytest.mark.django_db
def test_hoc_vien_khong_sua_duoc_ke_hoach_cua_ban(hai_em):
    """`PUT items/<id>` nhận ID của MỘT mục, không nhận ID của người sở hữu."""
    # `weekly_target` và `basis` đều là jsonb (đã tra `information_schema`
    # thay vì đoán từ tên cột — đoán sai hai lượt trước đó).
    p = q1("""INSERT INTO study_plans
                  (user_id, exam_date, weekly_target, basis, generated_at, is_active)
              VALUES (%s, CURRENT_DATE + 60, '{}'::jsonb, '{}'::jsonb, now(), TRUE)
              RETURNING id""",
           (hai_em['a'].id,))
    i = q1("""INSERT INTO study_plan_items
                  (plan_id, week_start, kind, topic, title, status)
              VALUES (%s, CURRENT_DATE, 'topic', 'x', 'Muc cua A', 'todo')
              RETURNING id""",
           (p['id'],))

    kq = _goi(StudyPlanItemView, 'put', hai_em['b'], {'status': 'skipped'},
              item_id=i['id'])
    assert kq.status_code == 400, (kq.status_code, kq.data)

    # Và mục ấy KHÔNG được đổi. Kiểm mã trả về thôi thì chưa đủ: một view có thể
    # ghi xong rồi mới báo lỗi, và đó đúng là kiểu hỏng khó thấy nhất.
    con = q1('SELECT status FROM study_plan_items WHERE id=%s', (i['id'],))
    assert con['status'] == 'todo', con


@pytest.mark.django_db
def test_hoc_vien_khong_danh_dau_doc_thong_bao_cua_ban(hai_em):
    n = q1("""INSERT INTO notifications (user_id, type, title, body, is_read)
              VALUES (%s, 'test', 'Cua A', '', FALSE) RETURNING id""",
           (hai_em['a'].id,))

    _goi(FeedReadView, 'post', hai_em['b'], {}, notif_id=n['id'])
    # Đường này trả 200 dù không đổi gì (nó chỉ UPDATE ... AND user_id=%s), nên
    # KHÔNG kiểm mã trả về — kiểm thứ duy nhất có nghĩa: dòng có bị đổi không.
    con = q1('SELECT is_read FROM notifications WHERE id=%s', (n['id'],))
    assert con['is_read'] is False, con


# ══ GIẢNG VIÊN B vs LỚP CỦA GIẢNG VIÊN A ════════════════════════════════════

@pytest.fixture
def hai_lop(db):
    """Hai giảng viên, mỗi người một lớp; một học viên nằm trong lớp của A."""
    ga = _nguoi('GV A', ROLE_TEACHER)
    gb = _nguoi('GV B', ROLE_TEACHER)
    qt = _nguoi('QT DCK', ROLE_ADMIN)
    em = _nguoi('Em cua A', ROLE_STUDENT)

    la = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
            "VALUES ('Lop A','hsa_quantitative',%s,'active') RETURNING id", (ga.id,))
    lb = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
            "VALUES ('Lop B','hsa_quantitative',%s,'active') RETURNING id", (gb.id,))
    q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) '
       'RETURNING id', (la['id'], em.id, local_now()))
    return {'ga': ga, 'gb': gb, 'qt': qt, 'em': em, 'la': la['id'], 'lb': lb['id']}


@pytest.mark.django_db
def test_giang_vien_khong_mo_duoc_lop_cua_dong_nghiep(hai_lop):
    cua_minh = _goi(TeachClassDetailView, 'get', hai_lop['ga'], class_id=hai_lop['la'])
    assert cua_minh.status_code == 200, cua_minh.data

    cua_ban = _goi(TeachClassDetailView, 'get', hai_lop['gb'], class_id=hai_lop['la'])
    assert cua_ban.status_code == 404, (cua_ban.status_code, cua_ban.data)


@pytest.mark.django_db
def test_giang_vien_khong_doc_duoc_ho_so_hoc_vien_lop_khac(hai_lop):
    """Hồ sơ học tập của một đứa trẻ — nặng hơn thông tin lớp."""
    cua_minh = _goi(TeachStudentView, 'get', hai_lop['ga'],
                    class_id=hai_lop['la'], user_id=hai_lop['em'].id)
    assert cua_minh.status_code == 200, cua_minh.data

    cua_ban = _goi(TeachStudentView, 'get', hai_lop['gb'],
                   class_id=hai_lop['la'], user_id=hai_lop['em'].id)
    assert cua_ban.status_code == 404, (cua_ban.status_code, cua_ban.data)


@pytest.mark.django_db
def test_giang_vien_khong_doc_duoc_to_bao_cao_phu_huynh_lop_khac(hai_lop):
    """Tờ này in email và số điện thoại của học viên — bề mặt nhạy nhất."""
    kq = _goi(ParentReportView, 'get', hai_lop['gb'],
              class_id=hai_lop['la'], user_id=hai_lop['em'].id)
    assert kq.status_code == 404, (kq.status_code, kq.data)


@pytest.mark.django_db
def test_404_chu_khong_phai_403_de_khong_lo_lop_co_ton_tai(hai_lop):
    """Hai câu trả lời phải GIỐNG HỆT nhau: lớp không có, và lớp không phải của bạn.

    Trả 403 cho lớp của người khác và 404 cho lớp không tồn tại là một kênh rò:
    dò id từ 1 tới n rồi đọc mã trả về là biết trung tâm có bao nhiêu lớp.
    `can_see_class` đã ghi rõ ý này trong chú thích; đây là chỗ canh nó.
    """
    khong_co = _goi(TeachClassDetailView, 'get', hai_lop['gb'], class_id=99999999)
    cua_ban = _goi(TeachClassDetailView, 'get', hai_lop['gb'], class_id=hai_lop['la'])
    assert khong_co.status_code == cua_ban.status_code == 404
    assert khong_co.data == cua_ban.data, (khong_co.data, cua_ban.data)


# ══ TỰ NÂNG VAI CHO CHÍNH MÌNH ══════════════════════════════════════════════

@pytest.mark.django_db
def test_hoc_vien_khong_tu_nang_vai_qua_ho_so(hai_em):
    """Gửi kèm `role` vào lời sửa hồ sơ — cột kinh điển của mass assignment.

    `UserView.put` hiện đọc ĐÚNG SÁU trường có tên (name, email, phone,
    birthday, parent_name, parent_phone), nên `role` rơi xuống đất. Nhưng đó là
    một tính chất của cách viết, không phải một hàng rào có tên — ai đó đổi
    sang `for k, v in data.items()` cho gọn là mở toang, và không có gì kêu lên
    vì màn hình hồ sơ vẫn chạy y hệt.

    Đường đổi vai HỢP LỆ duy nhất là `AdminUserRoleView` (IsAdminRole), và nó
    còn chặn tự hạ vai của chính mình lẫn xoá quản trị viên cuối cùng.
    """
    from accounts.views import UserView

    truoc = q1('SELECT role FROM users WHERE id=%s', (hai_em['b'].id,))['role']
    _goi(UserView, 'put', hai_em['b'], {
        'name': 'Em B', 'email': 'em_b_moi_dck@example.com',
        'role': ROLE_ADMIN, 'is_staff': True, 'is_superuser': True,
    })
    sau = q1('SELECT role FROM users WHERE id=%s', (hai_em['b'].id,))['role']
    assert sau == truoc == ROLE_STUDENT, (truoc, sau)
