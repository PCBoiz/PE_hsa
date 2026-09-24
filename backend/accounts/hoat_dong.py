"""LẦN CUỐI THẤY TÀI KHOẢN — §56 `users.last_seen_at` (24/09/2026).

Ghi chú họp TopHSA: học vụ muốn biết "bao nhiêu tài khoản lâu không hoạt động".
`learning_events` chỉ trả lời được cho người LÀM BÀI; nhân sự gần như không sinh
sự kiện học nào, và một em vào xem lịch rồi thoát cũng không để lại dấu gì.

Đóng dấu ở BA cửa cấp token — đăng nhập mật khẩu (`views.LoginView`), OAuth
(`oauth.oauth_complete`), làm mới token (`ghi_nho.LamMoiView`) — chứ KHÔNG ở mỗi
request. Access token sống 30 phút (`SIMPLE_JWT`), nên người đang dùng thật sự
được đóng dấu lại ít nhất nửa giờ một lần: đủ mịn cho mốc 7/14/30 ngày của trang
Tổng quan, và không biến mọi lượt ĐỌC thành một lượt GHI vào bảng `users` (một
middleware đóng dấu mỗi request là thêm một câu UPDATE cho từng lời gọi API).

KHÔNG đóng dấu ở `RegisterView`: token ở đó cấp cho tài khoản VỪA TẠO, người bấm
là quản trị viên — chủ tài khoản chưa hề vào.
"""
import logging

from django.db import DatabaseError, transaction

from common.clock import local_now
from common.db import x
from common.events import KIND_ATTENDANCE

logger = logging.getLogger(__name__)


def sql_hoat_dong(u='u', nay='%s', cot=('thay', 'moc')):
    """Định nghĩa DUY NHẤT của "hoạt động" của một tài khoản — câu SQL con MỘT dòng.

    Hai nơi đọc, phải ra CÙNG con số (1.4b, 24/09/2026): thẻ "Tài khoản lâu không vào"
    ở Tổng quan (`teaching.overview.tai_khoan_ngu`) và danh sách + ô lọc "không hoạt
    động ≥ N ngày" ở màn Tài khoản (`teaching.admin_users`). Học vụ bấm từ "12 em" trên
    thẻ sang danh sách mà thấy 15 em thì không ai biết bên nào đúng.

    Cột trả về, cho bảng ``users`` mang bí danh ``u``:
      · ``thay`` = GREATEST(`last_seen_at` §56, sự kiện học gần nhất) — NULL khi chưa
        thấy cả hai ("chưa vào");
      · ``moc``  = ``thay``, chưa có thì ``created_at``: tài khoản cấp 60 ngày chưa ai vào
        là ngủ 60 ngày, cấp hôm qua thì chưa.
    Sự kiện học BỎ ``attendance`` (giảng viên điểm danh cho em, kể cả ghi "vắng" — tính nó
    thì em bỏ học mà vẫn bị tick vắng đều sẽ không bao giờ lọt danh sách) và bỏ sự kiện ở
    tương lai (``occurred_at <= nay`` — sổ điểm danh mở được cho buổi chưa diễn ra).

    ``nay`` là CHỖ ĐẶT tham số giờ hiện tại theo kiểu của câu gọi (``'%s'`` hay
    ``'%(nay)s'``) — truyền `common.clock.local_now()`, KHÔNG dùng `now()` của SQL (UTC,
    lệch 7 tiếng). Hằng `KIND_ATTENDANCE` nhúng thẳng: hằng trong mã, không phải dữ liệu
    người dùng — cùng lý lẽ với `teaching.vocab.chi_hoc_vien`.

    Câu gộp (MAX, không GROUP BY) LUÔN trả đúng một dòng kể cả khi không có sự kiện nào,
    nên dùng được cả làm ``LEFT JOIN LATERAL (…) h ON TRUE`` lẫn làm câu con vô hướng
    ``(…) <= %s`` trong WHERE (khi đó ``cot`` chỉ một cột).
    """
    bieu = {
        'thay': 'GREATEST({u}.last_seen_at, MAX(e.occurred_at))',
        'moc': 'COALESCE(GREATEST({u}.last_seen_at, MAX(e.occurred_at)), {u}.created_at)',
    }
    chon = ', '.join('%s AS %s' % (bieu[c], c) for c in cot).format(u=u)
    return ("SELECT %s FROM learning_events e WHERE e.user_id = %s.id AND e.kind <> '%s' "
            'AND e.occurred_at <= %s' % (chon, u, KIND_ATTENDANCE, nay))


def danh_dau(user_id):
    """Ghi `last_seen_at = bây giờ` (giờ VN, naive — `common/clock.py`).

    Hỏng thì GHI LOG rồi thôi, không ném: dấu này là số liệu phụ, còn đăng nhập
    là cửa chính — cột chưa kịp có (mã lên trước `bootstrap_schema`) không được
    phép khoá cả trung tâm ngoài cửa. Cái giá khi hỏng: trang Tổng quan đếm người
    ấy "lâu không vào" nhiều hơn thật; lỗi nằm trong log `accounts.hoat_dong`.

    Savepoint riêng (`atomic`): bên gọi mà đang trong giao dịch thì một câu hỏng
    ở đây không được kéo đổ giao dịch của họ — cùng lý do với `common/events.py`.
    """
    try:
        with transaction.atomic():
            x('UPDATE users SET last_seen_at = %s WHERE id = %s', (local_now(), user_id))
    except DatabaseError:
        logger.error('[hoat_dong] KHÔNG đóng dấu được last_seen_at cho user %s', user_id,
                     exc_info=True)
