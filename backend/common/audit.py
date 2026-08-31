"""Nhật ký kiểm toán — nơi DUY NHẤT ghi vào ``admin_audit``.

Cùng kỷ luật một-nơi-ghi như ``common/events.py``, và vì cùng một lý do: khi mọi
lời ghi đi qua một cửa thì thêm một loại hành động chỉ là thêm một hằng số, chứ
không phải đi sửa mười chỗ và bỏ sót chỗ thứ mười một.

PHẠM VI (anh chốt 30/08/2026): chỉ ghi hành động SỬA. Hành động XEM — giảng viên
mở hồ sơ ai, đọc nhật ký tự ghi của ai — để sau, khi TopHSA chốt chính sách
quyền riêng tư (đặc tả ERP §8.3).

CHÉP CHỨ KHÔNG THAM CHIẾU. ``actor_name``, ``actor_role``, ``target_label`` đều
là bản chép tại thời điểm xảy ra. Nếu chỉ giữ khoá ngoại rồi nối lại lúc đọc thì
một trợ giảng nghỉ việc, bị xoá tài khoản, sẽ biến mọi dòng của mình thành
"NULL đã đặt lại mật khẩu của NULL" — mà đó đúng là lúc người ta cần đọc nhật ký
nhất. Cùng lý do với ``learning_events.topic``.

VÌ SAO KHÔNG NÉM LỖI RA NGOÀI. Đây là đánh đổi có ý thức, không phải sơ suất:
một hệ kiểm toán nghiêm ngặt sẽ CHẶN hành động khi không ghi được nhật ký. Ở đây
chọn ngược lại — trợ giảng đang cấp tài khoản cho học viên đứng đợi trước mặt mà
thao tác đổ vỡ vì bảng nhật ký trục trặc là cái giá đắt hơn. Bù lại, mọi lần ghi
hỏng đều được đẩy ra logger ở mức ERROR kèm nguyên nội dung dòng định ghi, nên
vết vẫn còn trong log ứng dụng (Render giữ stdout) chứ không biến mất hẳn.
"""
import json
import logging

from django.db import DatabaseError, transaction

from common.clock import local_now
from common.db import x

logger = logging.getLogger(__name__)

# ── Từ vựng `action`. Dạng `<đối tượng>.<việc>`, máy đọc được để lọc. ──
USER_CREATE = 'user.create'
USER_ROLE = 'user.role'
USER_STATUS = 'user.status'
USER_PASSWORD_RESET = 'user.password_reset'

CLASS_CREATE = 'class.create'
CLASS_UPDATE = 'class.update'
CLASS_DELETE = 'class.delete'
CLASS_MEMBER_ADD = 'class.member.add'
CLASS_MEMBER_REMOVE = 'class.member.remove'

SESSION_CREATE = 'session.create'
SESSION_UPDATE = 'session.update'
SESSION_DELETE = 'session.delete'
ATTENDANCE_MARK = 'attendance.mark'

#: Đợt học (§36, 31/08/2026). Vòng đời một đợt là thông tin tổ chức của trung
#: tâm, không phải dữ liệu học của em nào — nhưng xoá một đợt gỡ nhãn khỏi hàng
#: chục lớp, nên vẫn thuộc nhóm việc SỬA phải ghi lại.
TERM_CREATE = 'term.create'
TERM_UPDATE = 'term.update'
TERM_DELETE = 'term.delete'

#: Giao bài & chấm tay (§38, 31/08/2026). Chấm điểm PHẢI vào nhật ký: nó là con
#: số theo em suốt khoá, đi thẳng vào bản đồ năng lực và báo cáo gửi phụ huynh —
#: nên khi phụ huynh hỏi "điểm này ai cho, cho lúc nào" thì phải trả lời được.
ASSIGNMENT_CREATE = 'assignment.create'
ASSIGNMENT_UPDATE = 'assignment.update'
ASSIGNMENT_DELETE = 'assignment.delete'
ASSIGNMENT_GRADE = 'assignment.grade'


def _client_ip(request):
    """IP thật sau proxy. Render và Vercel đều đứng trước ứng dụng nên
    ``REMOTE_ADDR`` luôn là IP của proxy — vô dụng cho kiểm toán."""
    if request is None:
        return None
    fwd = request.META.get('HTTP_X_FORWARDED_FOR')
    if fwd:
        # Chuỗi dạng "client, proxy1, proxy2" — phần tử đầu là máy khách.
        #
        # CẢNH BÁO CHƯA VÁ (T66, 31/08/2026): phần tử ĐẦU là thứ người gọi TỰ
        # ĐẶT được. Ai gọi thẳng vào Render kèm `X-Forwarded-For: 1.2.3.4` thì
        # cột `ip` của nhật ký kiểm toán ghi 1.2.3.4 — tức bằng chứng kiểm toán
        # giả mạo được, ở đúng chỗ sinh ra để làm bằng chứng.
        #
        # KHÔNG sửa vội thành phần tử CUỐI: đúng vị trí phụ thuộc số chặng proxy
        # thật, mà con số đó CHƯA ĐO trên production (mọi dòng `admin_audit`
        # hiện có đều là ::1 / 127.0.0.1 — chưa request thật nào đi qua
        # Render/Vercel). Sửa mù ở đây rồi đặt `NUM_PROXIES` theo chiều khác là
        # hàng rào tần suất và nhật ký kiểm toán chỉ vào HAI IP khác nhau cho
        # cùng một request — tệ hơn hiện trạng.
        #
        # Vá cùng lúc với `REST_FRAMEWORK['NUM_PROXIES']`, sau khi anh đo xong
        # (xem `docs/VIEC_CUA_ANH.md` mục A2). Hai chỗ phải dùng CÙNG một quy
        # ước chọn phần tử.
        return fwd.split(',')[0].strip()[:60]
    addr = request.META.get('REMOTE_ADDR')
    return addr[:60] if addr else None


def record(request, action, *, target_type=None, target_id=None, target_label=None,
           summary=None, detail=None, actor=None):
    """Ghi một hành động sửa. Trả True nếu ghi được; không bao giờ ném lỗi.

    ``request`` để lấy người thực hiện và IP. Truyền ``actor`` riêng khi hành
    động do lệnh quản trị chạy nền gây ra (không có request).
    """
    who = actor if actor is not None else getattr(request, 'user', None)
    actor_id = getattr(who, 'id', None) if getattr(who, 'is_authenticated', False) else None
    actor_name = getattr(who, 'name', None) if actor_id else None
    actor_role = getattr(who, 'role', None) if actor_id else None

    try:
        # Savepoint riêng: bảng chưa tồn tại (mã lên Render trước khi chạy
        # bootstrap_schema), JSON hỏng… đều không được kéo đổ giao dịch của bên
        # gọi. Xem phần "VÌ SAO KHÔNG NÉM LỖI RA NGOÀI" ở đầu module.
        with transaction.atomic():
            x('''INSERT INTO admin_audit
                     (actor_id, actor_name, actor_role, action, target_type, target_id,
                      target_label, summary, detail, ip, occurred_at)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)''',
              (actor_id, actor_name, actor_role, action, target_type,
               None if target_id is None else str(target_id), target_label, summary,
               json.dumps(detail, ensure_ascii=False) if detail is not None else None,
               _client_ip(request), local_now()))
        return True
    except (DatabaseError, TypeError, ValueError) as exc:
        # Mức ERROR kèm nguyên nội dung: nhật ký kiểm toán mất một dòng thì ít
        # nhất log ứng dụng còn giữ được nó.
        logger.error('[audit] KHÔNG ghi được: %s | action=%s actor=%s target=%s/%s | %s',
                     exc, action, actor_id, target_type, target_id, summary)
        return False
