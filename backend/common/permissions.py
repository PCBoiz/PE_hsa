"""Phân quyền.

LỊCH SỬ: bản đầu chỉ có ``is_admin`` (users.role == 'admin') — quyền NHỊ PHÂN,
đúng với một sản phẩm tự học nhưng sai ngay từ gốc với một trung tâm luyện thi:
giảng viên phải thấy học viên CỦA MÌNH và không thấy của người khác.

Từ 24/08/2026 thêm vai trò ``Giảng viên``, và nguyên tắc là quyền theo NGỮ CẢNH
chứ không theo vai trò: quyền xem một lớp = "tôi có phụ trách lớp đó không",
quản trị viên thì xem được tất cả. Kiểm tra ngữ cảnh nằm ở ``can_see_class`` để
mọi endpoint dùng chung đúng một luật — mỗi chỗ tự kiểm một kiểu là cách chắc
chắn để hở dữ liệu học viên.
"""
from rest_framework.permissions import BasePermission

from common.db import q, q1

ROLE_ADMIN = 'admin'
ROLE_ACADEMIC = 'Quản lý học vụ'
ROLE_TEACHER = 'Giảng viên'
ROLE_ASSISTANT = 'Trợ giảng'
ROLE_STUDENT = 'Học viên'
ROLE_EDITOR = 'Biên tập nội dung'
#: Vai trò hợp lệ khi quản trị viên đổi vai trò cho một tài khoản.
#: Thứ tự = từ quyền RỘNG tới HẸP, để ô chọn trên màn hình đọc như một bậc thang.
#: `Biên tập nội dung` đứng RIÊNG ở cuối, không xen vào bậc thang ấy: nó không
#: rộng hơn hay hẹp hơn `Trợ giảng`, nó đứng ở một TRỤC KHÁC (giáo trình, không
#: phải lớp học). Xếp nó vào giữa thang sẽ làm người chọn tưởng nó bao hàm các
#: vai trò dưới.
ASSIGNABLE_ROLES = (ROLE_ADMIN, ROLE_ACADEMIC, ROLE_TEACHER, ROLE_ASSISTANT,
                    ROLE_STUDENT, ROLE_EDITOR)

# ── Hai vai trò thêm 01/09/2026 ──────────────────────────────────────────────
#
# Đặc tả ERP §10 cố ý HOÃN hai chức danh này ("chưa biết TopHSA có những chức
# danh nào"), nên ranh giới dưới đây do anh Sơn chốt 01/09/2026 và cố ý chọn bản
# HẸP — mở rộng một vai trò về sau dễ hơn thu hẹp lại, vì thu hẹp là lấy đi thứ
# người ta đã quen dùng.
#
#   · TRỢ GIẢNG — chỉ trong lớp được gán (một dòng `class_members`, không phải
#     `classes.teacher_id`). Điểm danh và chấm bài được; KHÔNG xoá buổi, và
#     KHÔNG mở báo cáo phụ huynh — trong đó có email và số điện thoại của em.
#     §8 của đặc tả nói thẳng: càng nhiều vai trò thì càng nhiều người nhìn thấy
#     dữ liệu của một đứa trẻ.
#   · QUẢN LÝ HỌC VỤ — xem mọi lớp, quản lý lớp và đợt học. KHÔNG đổi vai trò,
#     KHÔNG đặt lại mật khẩu, KHÔNG mở báo cáo phụ huynh. Ba việc ấy giữ cho
#     quản trị viên.
#
# RANH GIỚI VỀ DỮ LIỆU LIÊN LẠC, nói rõ để lần sau không ai phải đoán:
# **nhìn được khi LÀM VIỆC, nhưng không MANG RA NGOÀI được.**
#
# Trợ giảng vẫn thấy email học viên trên ba màn hình họ phải dùng — bảng điểm
# danh, bảng chấm bài, báo cáo lớp — vì `users.name` có thể rỗng và khi đó email
# là thứ duy nhất để biết đang tick cho em nào. Nhưng hai đường ĐƯA DỮ LIỆU RA
# KHỎI HỆ THỐNG thì bị cắt: báo cáo phụ huynh (403) và hai file CSV của lớp
# (`bo_cot_lien_lac` trong `teaching/exports.py` bỏ cột Email + Số điện thoại).
# Chú thích ở `exports.py` nói thẳng file đó "đi qua Zalo" — tức nó rời khỏi
# tầm kiểm soát ngay khi ai đó bấm tải.
#
# Nếu TopHSA muốn chặt hơn (trợ giảng không thấy email ở đâu cả) thì sửa ở ba
# chỗ trả `'email'` trong `teaching/`, và phải xử luôn trường hợp tên rỗng —
# không thì bảng điểm danh hiện ra một hàng trắng không ai nhận ra là ai.
#
# KHÔNG cần đổi lược đồ: `class_members` vốn chứa được người không phải học
# viên (báo cáo lớp đã có sẵn câu "1 tài khoản khác đang ở trong lớp nhưng không
# mang vai Học viên"), và `chi_hoc_vien` lọc đúng `role = 'Học viên'` nên hai
# vai trò mới tự động không lọt vào sĩ số, bảng điểm danh hay mẫu số tiến độ.


def is_admin(user) -> bool:
    return bool(user and user.is_authenticated and user.role == ROLE_ADMIN)


def is_teacher(user) -> bool:
    return bool(user and user.is_authenticated and user.role == ROLE_TEACHER)


def is_academic(user) -> bool:
    return bool(user and user.is_authenticated and user.role == ROLE_ACADEMIC)


def is_assistant(user) -> bool:
    return bool(user and user.is_authenticated and user.role == ROLE_ASSISTANT)


def is_editor(user) -> bool:
    return bool(user and user.is_authenticated and user.role == ROLE_EDITOR)


def _la_tro_giang_cua_lop(user, class_id) -> bool:
    """Trợ giảng có được gán vào ĐÚNG lớp này không (và chưa rời)?

    `left_at IS NULL` không phải chi tiết vặt: gỡ một trợ giảng khỏi lớp là ghi
    `left_at`, nên thiếu vế đó thì gỡ xong họ vẫn xem được.
    """
    if not is_assistant(user):
        return False
    return bool(q1('SELECT 1 FROM class_members '
                   'WHERE class_id=%s AND user_id=%s AND left_at IS NULL',
                   (class_id, user.id)))


class IsAdminRole(BasePermission):
    """@api_admin_required — 403 'Không có quyền truy cập' (message do errors.py)."""

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsContentEditor(BasePermission):
    """Soạn giáo trình: quản trị viên hoặc `Biên tập nội dung`.

    VAI TRÒ NÀY ĐỨNG Ở MỘT TRỤC KHÁC với bốn vai trò kia (04/09/2026). Trợ
    giảng, giảng viên, quản lý học vụ đều được định nghĩa theo LỚP — ai dạy lớp
    nào, ai xem được lớp nào. Biên tập nội dung thì không dính tới lớp nào cả:
    họ chạm vào GIÁO TRÌNH, thứ dùng chung cho mọi lớp.

    Hệ quả cố ý: người biên tập KHÔNG thấy học viên, không thấy điểm, không thấy
    email hay số điện thoại của ai. Đó là lý do tách vai trò riêng thay vì mở
    `/api/admin/*` cho `Giảng viên` — mở như thế là cho luôn quyền xem mọi thứ
    khác nằm dưới cùng tiền tố ấy.

    KHÔNG bao gồm việc XOÁ một khoá học: xem `IsCourseOwner` ngay dưới.
    """

    def has_permission(self, request, view):
        return is_admin(request.user) or is_editor(request.user)


class IsCourseOwner(BasePermission):
    """Việc chỉ quản trị viên làm được: TẠO và XOÁ một khoá học.

    Xoá một khoá là xoá cả `lessons` treo dưới nó, và `lesson_progress` của mọi
    học viên trỏ tới các bài ấy — tức xoá tiến độ đã học của người thật, không
    phải xoá một bản nháp. Tạo khoá thì rẻ nhưng một khoá rỗng hiện ngay trên
    danh sách của mọi học viên.

    Sửa NỘI DUNG thì thoải mái (`IsContentEditor`) — sai thì sửa lại được.
    """

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsTeachingStaff(BasePermission):
    """CỬA VÀO khu giảng dạy — bốn vai trò. Vào được KHÔNG có nghĩa là xem được
    mọi lớp: từng endpoint vẫn phải gọi ``can_see_class``.

    Đổi tên từ ``IsTeachingStaff`` ngày 01/09/2026, khi thêm trợ giảng và quản
    lý học vụ. Giữ tên cũ là để lại một cái tên NÓI DỐI về thứ nó cho qua, và
    người đọc tin cái tên rồi thôi không mở ra xem (RULES §20).
    """

    def has_permission(self, request, view):
        u = request.user
        return (is_admin(u) or is_academic(u) or is_teacher(u) or is_assistant(u))


class IsSeniorTeachingStaff(BasePermission):
    """Khu giảng dạy TRỪ trợ giảng — cho việc XOÁ và cho dữ liệu liên lạc của em.

    Hai thứ trợ giảng không được chạm (anh Sơn chốt 01/09/2026): xoá buổi học
    (mất luôn các dòng điểm danh của buổi đó) và báo cáo phụ huynh (email + số
    điện thoại).
    """

    def has_permission(self, request, view):
        u = request.user
        return is_admin(u) or is_academic(u) or is_teacher(u)


class IsAdminOrAcademic(BasePermission):
    """Quản lý LỚP và ĐỢT HỌC. Không gồm đổi vai trò / đặt lại mật khẩu — hai
    việc đó vẫn ``IsAdminRole``."""

    def has_permission(self, request, view):
        return is_admin(request.user) or is_academic(request.user)


def can_see_class(user, class_id) -> bool:
    """Quản trị viên xem mọi lớp; giảng viên chỉ xem lớp mình phụ trách.

    Trả False khi lớp không tồn tại — endpoint trả 404 cho cả hai trường hợp để
    không lộ ra rằng lớp đó có tồn tại hay không.
    """
    if is_admin(user) or is_academic(user):
        return bool(q1('SELECT 1 FROM classes WHERE id=%s', (class_id,)))
    if is_teacher(user):
        return bool(q1('SELECT 1 FROM classes WHERE id=%s AND teacher_id=%s',
                       (class_id, user.id)))
    return _la_tro_giang_cua_lop(user, class_id)


def visible_class_ids(user):
    """Danh sách lớp người dùng được xem. Dùng cho màn hình danh sách."""
    if is_admin(user) or is_academic(user):
        return [r['id'] for r in q('SELECT id FROM classes ORDER BY id')]
    if is_teacher(user):
        return [r['id'] for r in q('SELECT id FROM classes WHERE teacher_id=%s '
                                   'ORDER BY id', (user.id,))]
    if is_assistant(user):
        # Cùng luật với `_la_tro_giang_cua_lop`, viết ở dạng danh sách. Lệch
        # nhau thì màn hình danh sách và trang chi tiết nói hai chuyện.
        return [r['class_id'] for r in
                q('SELECT class_id FROM class_members '
                  'WHERE user_id=%s AND left_at IS NULL ORDER BY class_id', (user.id,))]
    return []


def last_active_admin(user_id) -> bool:
    """Tài khoản này có phải quản trị viên ĐANG HOẠT ĐỘNG cuối cùng không?

    Bất biến duy nhất mà hệ thống không tự phục hồi được khi vỡ: còn không một
    quản trị viên nào thì không ai vào được trang quản trị để phong lại quyền
    cho ai — đường duy nhất là sửa tay trong CSDL, thứ mà trung tâm không làm
    được và cũng không nên làm được.

    Trước 30/08/2026 mỗi endpoint tự chặn một nửa: đổi vai trò thì cấm tự hạ
    quyền MÌNH, khoá tài khoản thì cấm tự khoá MÌNH. Cả hai đều đúng nhưng cùng
    bỏ sót một trường hợp — hai quản trị viên hạ quyền hoặc khoá LẪN NHAU, và
    hệ thống về không mà không câu lệnh nào bị từ chối.

    Đặt luật ở đây chứ không ở từng view vì đây là luật về QUYỀN, và
    `common/permissions.py` vốn đã là chỗ giữ đúng một bản của mọi luật quyền —
    mỗi chỗ tự kiểm một kiểu là cách chắc chắn nhất để hở.
    """
    row = q1("SELECT COUNT(*) AS n FROM users "
             "WHERE role=%s AND COALESCE(status, 'active')='active' AND id<>%s",
             (ROLE_ADMIN, user_id))
    return (row['n'] if row else 0) == 0
