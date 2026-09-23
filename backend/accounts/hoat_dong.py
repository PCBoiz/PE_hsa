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

logger = logging.getLogger(__name__)


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
