"""Đường CÔNG KHAI tới báo cáo phụ huynh — mở bằng chìa, không cần tài khoản.

── VÌ SAO CÓ TỆP NÀY (07/09/2026) ──────────────────────────────────────────

Anh Sơn chốt: gửi phụ huynh một tin Zalo ZNS **kèm link** báo cáo. Nhưng
`ParentReportView` đứng sau `IsSeniorTeachingStaff`, mà phụ huynh không có tài
khoản trong hệ thống — bấm vào link là rơi thẳng về màn đăng nhập.

ZNS không đính kèm được tệp (nó là tin theo MẪU đã duyệt), nên "gửi file PDF
qua ZNS" là điều không tồn tại. Đường duy nhất còn lại là gửi một địa chỉ web,
và địa chỉ ấy phải tự mang quyền xem của nó.

── BỐN RANH GIỚI, ĐỌC TRƯỚC KHI SỬA ───────────────────────────────────────

1. **AI CÓ LINK LÀ XEM ĐƯỢC.** Đó là bản chất của việc gửi một link qua tin
   nhắn, không phải sơ suất. Chìa 32 byte ngẫu nhiên nên không dò được; bù
   thêm bằng HẠN DÙNG, thu hồi được, và `noindex` ở trang.

2. **Kỳ báo cáo GHIM CỨNG vào chìa.** Không đọc `?from=/?to=` ở đường công
   khai. Nếu đọc thì ai cầm link cũng đổi được kỳ, tức xem được cả lịch sử học
   ngoài đúng kỳ mà trung tâm định gửi — một quyền mà chính giảng viên tạo
   link cũng không định trao.

3. **Tờ đi qua đây MỎNG HƠN tờ giảng viên xem** (`rut_gon_cho_link`). Cổng của
   `ParentReportView` là `IsSeniorTeachingStaff` chứ không phải cửa chung
   CHÍNH VÌ tờ ấy in email và số điện thoại của học viên — trợ giảng còn không
   được xem. Một đường KHÔNG CÓ VAI NÀO thì càng phải bỏ.

4. **Không ghi IP, không ghi user agent.** Chỉ đếm số lượt mở và thời điểm mở
   gần nhất, đủ để trung tâm biết phụ huynh đã xem chưa. Người mở link không
   phải người dùng của hệ thống; thu thập dấu vết của họ là một quyết định
   khác hẳn, và chưa ai quyết.

── VÌ SAO KHÔNG DÙNG JWT KÝ SẴN ───────────────────────────────────────────

Một token ký (JWT/itsdangerous) không cần bảng, nhưng cũng **không thu hồi
được**: phụ huynh chuyển tiếp nhầm vào nhóm lớp thì không có cách nào rút lại
trước khi nó hết hạn. Một dòng trong bảng thì `revoked_at = now()` là xong.
Thu hồi được là thứ đáng giá hơn một bảng.
"""
import secrets
from datetime import timedelta

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.clock import local_now, local_today
from common.db import q, q1, x
from common.permissions import IsSeniorTeachingStaff, can_see_class
from teaching.parent_report import (
    DEFAULT_WEEKS,
    dung_bao_cao,
    rut_gon_cho_link,
)

#: Chìa sống bao lâu. 45 ngày vì trung tâm gửi báo cáo theo THÁNG: hạn phải
#: qua được kỳ sau một chút để phụ huynh mở lại tờ cũ mà đối chiếu, nhưng
#: không dài tới mức một link cũ còn mở được sau khi em đã nghỉ học.
HAN_NGAY = 45

#: Số byte ngẫu nhiên của chìa. 32 byte = 256 bit; `token_urlsafe` cho ra 43
#: ký tự. Dò cạn là điều không xảy ra trong vũ trụ này, nên phần cần lo là
#: link BỊ CHUYỂN TIẾP — và đó là việc của hạn dùng + thu hồi, không phải của
#: độ dài chìa.
SO_BYTE = 32


def _cua_ai(token):
    """Đọc chìa. Trả `(dòng, lý_do_từ_chối)`.

    Gộp ba câu trả lời "không xem được" thành MỘT thông báo cho người ngoài:
    chìa sai, chìa hết hạn và chìa bị thu hồi đều trả về cùng một câu. Nói rõ
    "chìa này đã bị thu hồi" là xác nhận với người cầm link rằng chìa ấy TỪNG
    đúng — một mẩu tin nhỏ, nhưng nó chỉ có ích cho người không nên cầm nó.

    Bên trong thì vẫn phân biệt được, qua `revoked_at`/`expires_at` trong bảng.
    """
    d = q1('SELECT * FROM parent_report_links WHERE token = %s', (token,))
    if not d:
        return None, 'khong_thay'
    if d['revoked_at'] is not None:
        return None, 'khong_thay'
    if d['expires_at'] <= local_now().replace(tzinfo=None):
        return None, 'khong_thay'
    return d, None


class ParentReportLinkView(APIView):
    """POST/GET /api/teach/classes/<id>/students/<uid>/parent-report/link

    POST — cấp chìa mới cho kỳ đang xem. GET — liệt kê chìa còn sống, để giảng
    viên thấy mình đã gửi gì và thu hồi được.

    Cùng cổng với chính tờ báo cáo: ai xem được tờ thì mới cấp được đường xem
    tờ ấy cho người khác. Cấp một đường vào KHÔNG CẦN TÀI KHOẢN là một hành vi
    nặng hơn xem, nên tuyệt đối không nới cổng này rộng hơn cổng kia.
    """
    permission_classes = [IsSeniorTeachingStaff]

    def get(self, request, class_id, user_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        ds = q('''SELECT id, token, period_from, period_to, created_at, expires_at,
                         opened_count, last_opened_at
                  FROM parent_report_links
                  WHERE class_id = %s AND user_id = %s AND revoked_at IS NULL
                    AND expires_at > now()
                  ORDER BY created_at DESC''', (class_id, user_id))
        return Response({'links': [{
            'id': d['id'],
            'token': d['token'],
            'from': d['period_from'].isoformat(),
            'to': d['period_to'].isoformat(),
            'createdAt': d['created_at'].isoformat(),
            'expiresAt': d['expires_at'].isoformat(),
            'openedCount': d['opened_count'],
            'lastOpenedAt': d['last_opened_at'].isoformat() if d['last_opened_at'] else None,
        } for d in ds]})

    def post(self, request, class_id, user_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)

        # Dựng thử báo cáo TRƯỚC khi cấp chìa. Cấp một đường vào rồi mới phát
        # hiện nó dẫn tới lỗi 404 là gửi cho phụ huynh một link hỏng — và
        # người phát hiện ra sẽ là họ, không phải mình.
        den = local_today()
        tu = den - timedelta(weeks=DEFAULT_WEEKS)
        data, loi = dung_bao_cao(class_id, user_id, tu, den)
        if loi:
            return Response({'error': loi}, status=404)

        token = secrets.token_urlsafe(SO_BYTE)
        x('''INSERT INTO parent_report_links
                 (token, class_id, user_id, period_from, period_to,
                  created_by, expires_at)
             VALUES (%s, %s, %s, %s, %s, %s, now() + %s * INTERVAL '1 day')''',
          (token, class_id, user_id, tu, den, request.user.id, HAN_NGAY))
        return Response({
            'token': token,
            'from': tu.isoformat(),
            'to': den.isoformat(),
            'expiresDays': HAN_NGAY,
            # Số để gửi tới, trả kèm để màn hình không phải hỏi thêm một lượt.
            'parentPhone': data['parent']['phone'],
            'parentName': data['parent']['name'],
        }, status=201)


class ParentReportLinkRevokeView(APIView):
    """POST /api/teach/parent-report/links/<id>/revoke — thu hồi một chìa.

    Không XOÁ dòng: xoá là mất luôn bằng chứng đã từng gửi cho ai, lúc nào, và
    phụ huynh có mở không. Đặt `revoked_at` thì chìa chết ngay mà lịch sử còn.
    """
    permission_classes = [IsSeniorTeachingStaff]

    def post(self, request, link_id):
        d = q1('SELECT class_id FROM parent_report_links WHERE id = %s', (link_id,))
        if not d or not can_see_class(request.user, d['class_id']):
            return Response({'error': 'Không tìm thấy đường dẫn này.'}, status=404)
        x('''UPDATE parent_report_links SET revoked_at = now()
             WHERE id = %s AND revoked_at IS NULL''', (link_id,))
        return Response({'ok': True})


class PublicParentReportView(APIView):
    """GET /api/public/parent-report/<token> — phụ huynh mở, không cần tài khoản.

    `authentication_classes = []` chứ không chỉ `AllowAny`: để trống thì DRF
    vẫn CHẠY bộ xác thực JWT, và một cookie `pe_at` hết hạn nằm sẵn trong trình
    duyệt sẽ làm cả request đổ 401 — tức phụ huynh nào từng đăng nhập thử trên
    máy đó sẽ không mở nổi link, còn người khác thì mở được. Một lỗi chỉ xảy ra
    với vài người là một lỗi rất khó được báo lại.

    Giới hạn tần suất đi theo mặc định của dự án (`DailyIPThrottle` +
    `HourlyIPThrottle`, đếm RIÊNG cho từng view) — không cần khai thêm ở đây.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, token):
        d, tu_choi = _cua_ai(token)
        if tu_choi:
            # Một câu cho cả ba lý do — xem chú thích ở `_cua_ai`.
            return Response({'error': 'Đường dẫn này không còn dùng được. '
                                      'Liên hệ trung tâm để nhận đường dẫn mới.'},
                            status=404)

        # Kỳ lấy TỪ CHÌA, không từ query — ranh giới 2 ở đầu tệp.
        data, loi = dung_bao_cao(d['class_id'], d['user_id'],
                                 d['period_from'], d['period_to'])
        if loi:
            return Response({'error': loi}, status=404)

        # Đếm lượt mở. Đặt SAU khi dựng xong: một lượt dựng lỗi không phải một
        # lượt phụ huynh đã đọc, và đếm nhầm ở đây sẽ làm trung tâm tưởng đã
        # gửi tới nơi rồi.
        x('''UPDATE parent_report_links
             SET opened_count = opened_count + 1, last_opened_at = now()
             WHERE id = %s''', (d['id'],))

        return Response(rut_gon_cho_link(data))
