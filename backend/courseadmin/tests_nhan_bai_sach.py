"""Nhãn bài giảng KHÔNG được chứa HTML — phòng tuyến thứ hai của một lỗ XSS thật.

Chạy trên DB thật, mọi thứ nằm trong giao dịch được CUỘN LẠI (xem `conftest.py`).

── LỖ HỔNG ĐÃ TÌM RA (audit 07/09/2026) ─────────────────────────────────────

`/api/skills` trả `lessons.module` và `lessons.title` lên tab Kỹ năng, và
`dashboard.js::renderSkills` nối thẳng chúng vào `innerHTML`. Đo bằng cách viết
lại phản hồi API ở trình duyệt (không ghi CSDL): **payload chạy 3 lần, tạo 102
thẻ thật**.

Cùng lúc, `loi_html` — bộ lọc HTML dùng chung của dự án — trước hôm nay CHỈ
được gọi cho trường KHOÁ HỌC (`_clean_course_payload`). Đường ghi BÀI GIẢNG
không lọc gì.

Ghép hai điều lại: một tài khoản **Biên tập nội dung** đặt
`<img src=x onerror=...>` vào tên một bài giảng, và mã ấy chạy trong trình
duyệt của **mọi học viên** mở tab Kỹ năng — đủ để đọc phiên của các em.

Điều đó phá đúng lời hứa in trong bảng phân quyền: *"Biên tập nội dung đứng ở
TRỤC KHÁC với bốn vai trên — không đụng tới con người."* Chạy được script trong
phiên của một học viên chính là đụng tới con người.

── ĐÃ VÁ HAI ĐẦU, VÀ VÌ SAO CẦN CẢ HAI ─────────────────────────────────────

  · thoát chuỗi lúc VẼ (`renderSkills`) — phòng tuyến thật, vì nó đúng ở mọi
    nguồn dữ liệu, kể cả nguồn chưa ai nghĩ tới;
  · lọc HTML lúc GHI (tệp này canh) — giữ cho DỮ LIỆU sạch chứ không chỉ màn
    hình sạch. Nhãn bài giảng còn đi tới CSV xuất ra, tờ báo cáo phụ huynh, và
    tệp Excel — những chỗ `escHtml` của trình duyệt không với tới.

Bỏ một trong hai đều để lại đường sống cho cùng một lỗi.
"""
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1
from common.permissions import ROLE_EDITOR
from courseadmin.views import AdminLessonDetailView, AdminLessonsView

f = APIRequestFactory()

#: Payload thật đã dùng trong lần đo bằng trình duyệt.
DOC = '<img src=x onerror="window.__XSS=1">'


def _goi(view, method, ai, body, **kw):
    req = getattr(f, method)('/x', body, format='json')
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


@pytest.fixture
def canh(db):
    row = q1('INSERT INTO users (name, email, password, role, streak) '
             "VALUES ('BT Sach','bt_sach@example.com','x',%s,0) RETURNING id",
             (ROLE_EDITOR,))
    bt = User.objects.get(id=row['id'])
    c = q1("INSERT INTO courses (id, title) VALUES ('kh_sach','Khoa sach') "
           'RETURNING id')
    l = q1("INSERT INTO lessons (course_id, module, title, content, sort_order) "
           "VALUES (%s,'M1','Bai 1','', 1) RETURNING id", (c['id'],))
    return {'bt': bt, 'khoa': c['id'], 'bai': l['id']}


@pytest.mark.django_db
@pytest.mark.parametrize('truong', ['title', 'module'])
def test_khong_tao_duoc_bai_co_HTML_trong_nhan(canh, truong):
    than = {'course_id': canh['khoa'], 'title': 'Bai moi', 'module': 'M2'}
    than[truong] = DOC
    kq = _goi(AdminLessonsView, 'post', canh['bt'], than)
    assert kq.status_code == 400, (truong, kq.status_code, kq.data)

    # Và KHÔNG có dòng nào lọt vào CSDL. Kiểm mã trả về thôi thì chưa đủ: một
    # view có thể ghi xong rồi mới báo lỗi.
    con = q1('SELECT id FROM lessons WHERE course_id=%s AND (title=%s OR module=%s)',
             (canh['khoa'], DOC, DOC))
    assert con is None, con


@pytest.mark.django_db
@pytest.mark.parametrize('truong', ['title', 'module'])
def test_khong_sua_duoc_nhan_bai_thanh_HTML(canh, truong):
    kq = _goi(AdminLessonDetailView, 'put', canh['bt'], {truong: DOC},
              lesson_id=canh['bai'])
    assert kq.status_code == 400, (truong, kq.status_code, kq.data)

    con = q1('SELECT module, title FROM lessons WHERE id=%s', (canh['bai'],))
    assert DOC not in (con['module'], con['title']), con


@pytest.mark.django_db
def test_nhan_binh_thuong_van_ghi_duoc(canh):
    """Bộ lọc phải KHÔNG chặn nhãn thật.

    Một phép kiểm chỉ chứng minh "chặn được" thì `return 400` cho mọi thứ cũng
    xanh. Dấu `<` trong toán học ("Hàm số y < 0") là thứ giáo trình HSA dùng
    thật, nên nó phải qua được — `loi_html` bắt THẺ, không bắt ký tự.
    """
    kq = _goi(AdminLessonDetailView, 'put', canh['bt'],
              {'title': 'Bất phương trình y < 0 & x > 1', 'module': 'Đại số'},
              lesson_id=canh['bai'])
    assert kq.status_code == 200, kq.data
    con = q1('SELECT module, title FROM lessons WHERE id=%s', (canh['bai'],))
    assert con['title'] == 'Bất phương trình y < 0 & x > 1', con
