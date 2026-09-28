"""MA TRẬN QUYỀN — sáu vai × mọi view có hàng rào, đi qua bộ định tuyến thật.

Chạy trên DB thật, mọi thứ nằm trong giao dịch được CUỘN LẠI (xem `conftest.py`).

── VÌ SAO CÓ TỆP NÀY (07/09/2026) ───────────────────────────────────────────

Anh Sơn yêu cầu kiểm "tất cả các luồng có thể xảy ra giữa quản trị viên, giảng
viên và học viên". Bảng `/quan-tri/vai-tro` và `lib/quyenVai.ts` đã nói vai nào
làm được việc gì — nhưng cả hai đều đọc `permissions.py`, tức chúng chứng minh
**mã nhất quán với chính mã**, không chứng minh **máy chủ thật sự chặn**.

Tệp này hỏi câu khác hẳn: cầm thẻ của từng vai, gõ vào từng cửa, xem cửa có mở
không. Nó không đọc `permissions.py` để biết kết quả mong đợi — nó đọc để biết
kết quả mong đợi, rồi ĐỐI CHIẾU với thứ máy chủ thật sự trả về.

── VÌ SAO CHỈ GỬI GET, VÀ VÌ SAO THẾ LÀ ĐỦ ─────────────────────────────────

DRF kiểm quyền trong `initial()`, chạy TRƯỚC khi chọn hàm xử lý theo method.
Nên một view chỉ có `post()` vẫn trả 403 cho vai không đủ quyền, và trả 405 cho
vai đủ quyền. Tức GET dựng được TRỌN ma trận quyền mà không gọi một hàm ghi nào.

Đó không phải chuyện tiện: Neon là CSDL production với tài khoản học viên thật.
Một bộ kiểm quyền mà bản thân nó gửi POST/DELETE vào từng cửa là một bộ kiểm
nguy hiểm hơn thứ nó đi tìm.

── THAM SỐ ĐƯỜNG DẪN CỐ Ý VÔ NGHĨA ─────────────────────────────────────────

`<int:class_id>` được điền số 1, `<str:course_id>` điền 'x'. Không cần chúng
trỏ tới gì có thật: hàng rào vai trò chạy trước khi view kịp tra CSDL. View đủ
quyền sẽ trả 404/405/500 tuỳ nó — mọi thứ KHÔNG PHẢI 403 đều tính là "cửa mở",
và đó đúng là điều đang được đo.
"""
import pytest
from django.urls import get_resolver
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1
from common.permissions import (
    ROLE_ACADEMIC,
    ROLE_ADMIN,
    ROLE_ASSISTANT,
    ROLE_EDITOR,
    ROLE_STUDENT,
    ROLE_TEACHER,
)

f = APIRequestFactory()

#: Vai → tên đọc được, để thông điệp lỗi nói tiếng người.
VAI = {
    ROLE_ADMIN: 'Quản trị viên',
    ROLE_ACADEMIC: 'Quản lý học vụ',
    ROLE_TEACHER: 'Giảng viên',
    ROLE_ASSISTANT: 'Trợ giảng',
    ROLE_EDITOR: 'Biên tập nội dung',
    ROLE_STUDENT: 'Học viên',
}

#: Lớp quyền → vai qua được. BẢN GỐC là `common/permissions.py`; bảng này chép
#: lại để phép kiểm có một kỳ vọng ĐỘC LẬP với thứ đang được kiểm.
#:
#: Chép tay ở đây là CÓ CHỦ Ý, ngược hẳn với luật ở `lib/quyenVai.ts` (nơi cấm
#: chép). Ở đó bảng chỉ để HIỂN THỊ nên chép là dựng một sự thật thứ hai sẽ
#: trôi. Ở đây bảng là KỲ VỌNG: suy nó ra từ chính `permissions.py` thì phép
#: kiểm chỉ chứng minh `permissions.py` bằng chính nó, và một thay đổi sai ở
#: đó sẽ kéo theo kỳ vọng đổi theo, xanh im lặng.
MONG_DOI = {
    'IsAdminRole': {ROLE_ADMIN},
    'IsCourseOwner': {ROLE_ADMIN},
    'IsAdminOrAcademic': {ROLE_ADMIN, ROLE_ACADEMIC},
    'IsSeniorTeachingStaff': {ROLE_ADMIN, ROLE_ACADEMIC, ROLE_TEACHER},
    'IsTeachingStaff': {ROLE_ADMIN, ROLE_ACADEMIC, ROLE_TEACHER, ROLE_ASSISTANT},
    'IsContentEditor': {ROLE_ADMIN, ROLE_EDITOR},
    # Khung chương trình theo buổi (E1, 25/09/2026): cắt ngang hai trục lớp và giáo trình.
    'IsCurriculumPlanner': {ROLE_ADMIN, ROLE_ACADEMIC, ROLE_EDITOR},
}


def _nguoi(vai, hau_to):
    row = q1('INSERT INTO users (name, email, password, role, streak) '
             "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             ('MT ' + hau_to, 'mt_%s@example.com' % hau_to, vai))
    return User.objects.get(id=row['id'])


@pytest.fixture
def sau_vai(db):
    """Một tài khoản cho mỗi vai."""
    return {v: _nguoi(v, str(i)) for i, v in enumerate(VAI)}


def _cac_view():
    """(đường dẫn, lớp view, tên lớp quyền) cho mọi view api/ CÓ hàng rào vai."""
    def di(res, tien_to=''):
        for p in res.url_patterns:
            if hasattr(p, 'url_patterns'):
                yield from di(p, tien_to + str(p.pattern))
            else:
                yield tien_to + str(p.pattern), p

    ra = []
    for duong, p in di(get_resolver()):
        if not duong.startswith('api/'):
            continue
        cls = getattr(p.callback, 'cls', None) or getattr(p.callback, 'view_class', None)
        if cls is None:
            continue
        for c in getattr(cls, 'permission_classes', []):
            if c.__name__ in MONG_DOI:
                ra.append((duong, cls, c.__name__))
                break
    return ra


def _tham_so(duong):
    """Điền tham số đường dẫn bằng giá trị vô nghĩa — xem chú thích đầu tệp."""
    kw = {}
    for phan in duong.split('/'):
        if phan.startswith('<') and phan.endswith('>'):
            kieu, ten = phan[1:-1].split(':') if ':' in phan[1:-1] else ('str', phan[1:-1])
            kw[ten] = 1 if kieu == 'int' else 'x'
    return kw


@pytest.mark.django_db
def test_moi_view_co_hang_rao_chan_dung_sau_vai(sau_vai):
    """Sáu vai × mọi view có hàng rào. Chỉ GET, không ghi gì."""
    views = _cac_view()
    assert len(views) >= 20, 'đọc được quá ít view có hàng rào: %d' % len(views)

    sai = []
    for duong, cls, ten_quyen in views:
        cho_phep = MONG_DOI[ten_quyen]
        for vai, ai in sau_vai.items():
            req = f.get('/x')
            force_authenticate(req, user=ai)
            try:
                kq = cls.as_view()(req, **_tham_so(duong))
                ma = kq.status_code
            except Exception:  # noqa: BLE001 — bắt RỘNG là đúng ở đây:
                # phép kiểm đang hỏi "cửa có mở không", và một view nổ vì
                # tham số vô nghĩa nghĩa là cửa ĐÃ mở. Bắt hẹp lại thì mọi
                # kiểu nổ chưa lường trước sẽ làm ĐỎ phép kiểm thay vì
                # được ghi nhận là "lọt", tức đổi một phát hiện thành một
                # lỗi công cụ.
                # View đủ quyền mà nổ vì tham số vô nghĩa: cửa ĐÃ mở, và đó
                # đúng là thứ đang đo. Cửa đóng thì DRF trả 403 chứ không ném.
                ma = 500
            mo = ma != 403
            nen_mo = vai in cho_phep
            if mo != nen_mo:
                sai.append('%-46s %-22s %-18s HTTP %s (%s)' % (
                    duong, ten_quyen, VAI[vai], ma,
                    'MỞ mà không được phép' if mo else 'ĐÓNG mà đáng lẽ mở'))

    assert not sai, ('\n%d ô sai trong ma trận quyền:\n  ' % len(sai)) + '\n  '.join(sai)


#: Cửa dưới `api/teach/` CỐ Ý gác trong THÂN HÀM, không bằng `permission_classes`.
#:
#: Mỗi mục phải nêu VÌ SAO, và phép kiểm bên dưới vẫn đòi cửa ấy TỪ CHỐI học viên
#: lạ — chỉ nới đúng một điểm: nó được từ chối bằng **404** thay vì 403. Danh sách
#: rỗng là trạng thái mong muốn; thêm một dòng vào đây là một quyết định, không
#: phải một cách làm cho phép kiểm hết đỏ.
#:
#: Thêm 27/09/2026 (audit bảo mật). Trước hôm nay phép kiểm coi MỌI mã khác 403 là
#: "lọt", nên `hoc-lieu` — cửa cố ý dùng chung cho cả người dạy lẫn em đang học, và
#: trả 404 đúng như luật của dự án — làm nó ĐỎ trên HEAD. Một phép kiểm đỏ thường
#: trực thì không canh được gì nữa: người sau đọc nó như một tiếng ồn, và cửa THẬT
#: sự quên hàng rào sẽ lẫn vào đấy.
CONG_TRONG_THAN = {
    'api/teach/classes/<int:class_id>/hoc-lieu':
        'Một cửa cho hai phía (teaching/hoc_lieu.py): người dạy thấy cả tài liệu đang '
        'ẩn, em đang học chỉ thấy phần đã mở và chỉ buổi mình thuộc. `permission_classes` '
        'không phân biệt nổi "giảng viên CỦA LỚP" với "em HỌC lớp", nên cổng nằm trong '
        'thân hàm và trả 404 cho cả hai kiểu người ngoài.',
}

#: Mã tính là "đã từ chối" cho một cửa gác trong thân hàm. 404 chứ không 403 là luật
#: của dự án cho cửa mang `class_id` (`docs/ERP_TOPHSA_2026-08-24.md` dòng 48).
MA_TU_CHOI = (403, 404)


@pytest.mark.django_db
def test_khong_view_nao_bo_trong_hang_rao_o_khu_quan_tri(sau_vai):
    """Đường `admin/` hay `teach/` mà chỉ có `IsAuthenticated` là một lỗ hổng.

    `DEFAULT_PERMISSION_CLASSES` của dự án là `IsAuthenticated`, nên một view
    QUÊN khai `permission_classes` không đổ lỗi, không cảnh báo — nó lặng lẽ mở
    cho MỌI tài khoản đăng nhập, kể cả học viên. Không có triệu chứng nào: màn
    hình chạy đúng, phép kiểm khác vẫn xanh.

    Phép kiểm này bắt đúng lúc thêm view mới, chứ không phải lúc có người khai
    thác. Nó KHÔNG đọc mã: nó cầm thẻ học viên gõ vào từng cửa.
    """
    hoc_vien = sau_vai[ROLE_STUDENT]
    def di(res, tien_to=''):
        for p in res.url_patterns:
            if hasattr(p, 'url_patterns'):
                yield from di(p, tien_to + str(p.pattern))
            else:
                yield tien_to + str(p.pattern), p

    lot = []
    for duong, p in di(get_resolver()):
        if not (duong.startswith('api/admin/') or duong.startswith('api/teach/')):
            continue
        cls = getattr(p.callback, 'cls', None) or getattr(p.callback, 'view_class', None)
        if cls is None:
            continue
        req = f.get('/x')
        force_authenticate(req, user=hoc_vien)
        try:
            ma = cls.as_view()(req, **_tham_so(duong)).status_code
        except Exception:  # noqa: BLE001 — xem chú thích ở khối trên
            ma = 500
        cho_phep = MA_TU_CHOI if duong in CONG_TRONG_THAN else (403,)
        if ma not in cho_phep:
            lot.append('%s → HTTP %s (%s)%s' % (
                duong, ma, cls.__name__,
                '' if duong in CONG_TRONG_THAN else
                ' — thiếu `permission_classes`? Cửa cố ý gác trong thân hàm thì khai vào '
                '`CONG_TRONG_THAN` kèm lý do.'))

    assert not lot, ('học viên KHÔNG bị chặn ở %d đường quản trị:\n  ' % len(lot)
                     + '\n  '.join(lot))


@pytest.mark.django_db
def test_cua_gac_trong_than_van_con_that(sau_vai):
    """`CONG_TRONG_THAN` không được thành một danh sách miễn trừ đã chết.

    Hai điều phải còn đúng cho mỗi dòng trong đó, nếu không thì dòng ấy là một lỗ
    hổng đang được phép kiểm che: cửa phải CÒN TỒN TẠI (đổi tên đường rồi mà danh
    sách vẫn giữ tên cũ là miễn trừ cho một thứ không có), và cửa phải THẬT SỰ từ
    chối học viên lạ (không phải trả 200 rồi được tha vì có tên trong danh sách).
    """
    hoc_vien = sau_vai[ROLE_STUDENT]
    def di(res, tien_to=''):
        for p in res.url_patterns:
            if hasattr(p, 'url_patterns'):
                yield from di(p, tien_to + str(p.pattern))
            else:
                yield tien_to + str(p.pattern), p

    co = {duong: p for duong, p in di(get_resolver())}
    thieu = [d for d in CONG_TRONG_THAN if d not in co]
    assert not thieu, ('`CONG_TRONG_THAN` còn giữ đường không tồn tại: %s' % thieu)

    lot = []
    for duong in CONG_TRONG_THAN:
        cls = (getattr(co[duong].callback, 'cls', None)
               or getattr(co[duong].callback, 'view_class', None))
        req = f.get('/x')
        force_authenticate(req, user=hoc_vien)
        try:
            ma = cls.as_view()(req, **_tham_so(duong)).status_code
        except Exception:  # noqa: BLE001 — xem chú thích ở khối trên
            ma = 500
        if ma not in MA_TU_CHOI:
            lot.append('%s → HTTP %s (%s)' % (duong, ma, cls.__name__))
    assert not lot, ('cửa gác trong thân hàm KHÔNG từ chối học viên lạ:\n  '
                     + '\n  '.join(lot))
