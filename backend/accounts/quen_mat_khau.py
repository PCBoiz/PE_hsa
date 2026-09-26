"""QUÊN MẬT KHẨU QUA EMAIL — §52, bảng yêu cầu TopHSA mục 1.5 (23/09/2026).

Anh Sơn chốt: đường dẫn DÙNG MỘT LẦN, hạn 30 PHÚT, gửi tới email CỦA CHÍNH tài
khoản. Tài khoản không có email (chỉ số điện thoại / tên đăng nhập) vẫn đi đường
cũ: nhờ học vụ cấp lại mật khẩu tạm.

── BA CỬA ──────────────────────────────────────────────────────────────────

  POST /auth/quen-mat-khau          {email}           → luôn cùng MỘT câu trả lời
  POST /auth/dat-lai-mat-khau/kiem  {chia}            → chìa còn dùng được không
  POST /auth/dat-lai-mat-khau       {chia, password}  → đặt mật khẩu mới

── NHỮNG ĐIỀU CỐ Ý ─────────────────────────────────────────────────────────

  · KHÔNG LỘ AI CÓ TÀI KHOẢN. Email có hay không, bị khoá hay không, đã quá
    trần hay chưa — phản hồi y hệt nhau. Thư đi qua HỘP THƯ ĐI (§61, E2): ghi
    cùng giao dịch với chìa, gửi sau commit trên một LUỒNG RIÊNG, để thời gian
    trả lời cũng không khác nhau (SMTP Gmail mất 1–3 giây; chênh chừng ấy là đủ
    để dò danh sách học viên). SMTP sập thì thư được thử lại — nhưng chỉ trong
    hạn của chìa (`het_han`): quá 30 phút thì bỏ, đường dẫn trong đó đã chết.
  · CHỈ LƯU BĂM của chìa (§52). Chìa nguyên văn chỉ nằm trong lá thư — và trong
    thân thư CHỜ GỬI ở hộp thư đi; gửi xong (hoặc bỏ) là thân bị xoá (`xoa_than`).
  · Chìa đi trong phần `#…` của đường dẫn, không trong `?…`: phần sau dấu `#`
    không bao giờ được trình duyệt gửi lên máy chủ nào, không vào nhật ký truy
    cập, không đi theo header Referer — cùng lý do `oauth.py` dùng fragment.
  · Gốc đường dẫn lấy từ `FRONTEND_URL`, KHÔNG từ header Host của yêu cầu —
    kẻ gửi yêu cầu đổi được Host, và thư đặt lại mật khẩu trỏ về máy của kẻ ấy
    là lỗ chiếm tài khoản kinh điển (cùng lý do `parent_send._goc`).
  · Đặt xong thì MỌI phiên cũ hết hiệu lực (`tokens_valid_from`) — người lạ
    đang giữ phiên của em (lý do em phải đổi mật khẩu) bị đẩy ra ngay.
  · `authentication_classes = []`: người quên mật khẩu hay còn một thẻ HẾT HẠN
    trong cookie; kiểm thẻ ấy là 401 đúng ở cửa họ cần vào.
"""
import hashlib
import html
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.hashers import make_werkzeug_password
from accounts.models import User
from accounts.validators import validate_email_field, validate_password_field
from common import audit
from common.clock import local_now
from common.db import q1, x
from common.identity import norm_email
from common.net import client_ip
from common.throttling import QuenMatKhauThrottle
from notifications import hop_thu

log = logging.getLogger(__name__)

HAN_PHUT = 30
#: Số chìa một tài khoản được xin trong một giờ. Quá trần thì im lặng không cấp
#: — vẫn trả đúng câu chung, để trần này không thành cách dò tài khoản.
TRAN_MOI_GIO = 3
SO_BYTE = 32

CAU_CHUNG = ('Nếu email này thuộc một tài khoản đang hoạt động, hệ thống vừa gửi tới đó một '
             'đường dẫn đặt lại mật khẩu. Đường dẫn dùng được một lần, trong %d phút. '
             'Không thấy thư thì xem cả mục Thư rác.' % HAN_PHUT)
CAU_HET_HAN = ('Đường dẫn này đã hết hạn hoặc đã được dùng. Xin một đường dẫn mới '
               'ở trang "Quên mật khẩu".')

#: Phép kiểm đặt True để gửi thư ĐỒNG BỘ và đọc được lá thư ngay sau lời gọi.
GUI_NGAY = False


def _bam(chia):
    return hashlib.sha256(chia.encode('utf-8')).hexdigest()


def _goc():
    return (getattr(settings, 'FRONTEND_URL', '') or '').rstrip('/')


def _che(email):
    """`an.nguyen@gmail.com` → `a***@gmail.com` — đủ để em nhận ra tài khoản
    mình, không đủ để người cầm nhầm đường dẫn biết địa chỉ của em."""
    ten, _, mien = (email or '').partition('@')
    return '%s***@%s' % (ten[:1], mien) if mien else '***'


def _soan_thu(ten, duong_dan):
    """(chữ thuần, html) của thư đặt lại mật khẩu."""
    goi = (ten or '').strip() or 'bạn'
    chu = ('Chào %s,\n\n'
           'Mình nhận được yêu cầu đặt lại mật khẩu cho tài khoản TopHSA của bạn. '
           'Bấm vào đường dẫn dưới đây để chọn mật khẩu mới:\n\n%s\n\n'
           'Đường dẫn dùng được một lần và sống trong %d phút. Quá giờ thì bạn xin lại '
           'một cái mới, cũng nhanh thôi.\n\n'
           'Nếu không phải bạn xin thì cứ bỏ qua thư này — mật khẩu cũ vẫn dùng bình thường.\n\n'
           'Thân mến,\nTopHSA\n' % (goi, duong_dan, HAN_PHUT))
    trang = ('<p>Chào %s,</p>'
             '<p>Mình nhận được yêu cầu đặt lại mật khẩu cho tài khoản TopHSA của bạn. '
             'Bấm nút dưới đây để chọn mật khẩu mới:</p>'
             '<p><a href="%s" style="display:inline-block;padding:10px 18px;border-radius:8px;'
             'background:#4f46e5;color:#fff;text-decoration:none;font-weight:600">'
             'Đặt mật khẩu mới</a></p>'
             '<p style="color:#6b7280">Đường dẫn dùng được một lần và sống trong %d phút. '
             'Quá giờ thì bạn xin lại một cái mới, cũng nhanh thôi.</p>'
             '<p>Nếu không phải bạn xin thì cứ bỏ qua thư này — mật khẩu cũ vẫn dùng bình thường.</p>'
             '<p style="color:#6b7280">Thân mến,<br>TopHSA</p>'
             % (html.escape(goi), html.escape(duong_dan, quote=True), HAN_PHUT))
    return chu, trang


class QuenMatKhauView(APIView):
    """POST /auth/quen-mat-khau {email} — xin đường dẫn đặt lại mật khẩu."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [QuenMatKhauThrottle]

    def post(self, request):
        body = request.data if isinstance(request.data, dict) else {}
        email = norm_email(str(body.get('email') or '').strip()) or ''
        # Sai DẠNG thì nói ngay — đó là lỗi gõ, không lộ gì về ai có tài khoản.
        if not email or validate_email_field(email):
            return Response({'errors': {'email': 'Nhập đúng địa chỉ email của tài khoản.'}}, status=400)

        u = q1('SELECT id, name, email, status FROM users WHERE lower(email)=%s', (email,))
        if u and (u['status'] or 'active') != 'suspended':
            bay_gio = local_now()
            # `purpose='reset'` KHÔNG phải trang trí (§73b, 27/09/2026): bảng này nay
            # giữ cả mã XÁC THỰC EMAIL của người mới đăng ký. Không lọc thì mã xác thực
            # bị tính vào trần 3 chìa/giờ của việc khác.
            da_xin = q1('SELECT count(*) AS n FROM password_reset_tokens '
                        "WHERE user_id=%s AND purpose='reset' AND created_at > %s",
                        (u['id'], bay_gio - timedelta(hours=1)))['n']
            if da_xin < TRAN_MOI_GIO:
                chia = secrets.token_urlsafe(SO_BYTE)
                chu, trang = _soan_thu(u['name'], '%s/dat-lai-mat-khau#chia=%s' % (_goc(), chia))
                with transaction.atomic():
                    # Chìa MỚI thay chìa cũ: chỉ đường dẫn trong lá thư gần nhất
                    # còn dùng được — em bấm nhầm thư cũ thì nhận câu "hết hạn".
                    # LỌC `purpose` (§73b): không có nó thì một lượt xin đặt lại mật
                    # khẩu HUỶ luôn mã xác thực email em chưa bấm, và em vừa đăng ký
                    # xong mất đường vào. `accounts/tests_tu_dang_ky.py` giữ chỗ này.
                    x("UPDATE password_reset_tokens SET used_at=%s "
                      "WHERE user_id=%s AND purpose='reset' AND used_at IS NULL",
                      (bay_gio, u['id']))
                    x('INSERT INTO password_reset_tokens '
                      "(user_id, token_hash, purpose, created_at, expires_at, requested_ip) "
                      "VALUES (%s, %s, 'reset', %s, %s, %s)",
                      (u['id'], _bam(chia), bay_gio, bay_gio + timedelta(minutes=HAN_PHUT),
                       client_ip(request)))
                    # Thư chưa đi được trong hạn của chìa thì bỏ (`het_han`); đi hay bỏ
                    # xong là thân có chìa bị xoá (`xoa_than`). Địa chỉ không tự ghi
                    # nhật ký ở đây — lỗi gửi nằm ở `outbox.error`, không kèm đường dẫn.
                    oid = hop_thu.xep('email', u['email'], 'Đặt lại mật khẩu TopHSA', chu,
                                      user_id=u['id'], source=('password_reset', None),
                                      params={'html': trang, 'xoa_than': True,
                                              'het_han': (timezone.now()
                                                          + timedelta(minutes=HAN_PHUT)).isoformat()})
                hop_thu.day_di([oid], ngay=GUI_NGAY)
        else:
            _can_dong_ho()
        return Response({'ok': True, 'message': CAU_CHUNG})


def _can_dong_ho():
    """Soạn một lá thư rồi VỨT ĐI — chỉ để cân đồng hồ, như `_DUMMY_HASH` ở `LoginView`.

    ĐO ĐƯỢC 27/09/2026 (máy dev, VN → Neon us-east-2): email CÓ tài khoản mất 2,03–2,29 s,
    email KHÔNG có mất 0,25–0,36 s. Thân phản hồi giống hệt nhau — đó là chủ ý — nhưng
    ĐỒNG HỒ thì khai ra địa chỉ nào đã có tài khoản ở TopHSA. Người dùng ở đây là trẻ vị
    thành niên, và danh sách "em nào học TopHSA" không phải thứ để ai cầm đồng hồ bấm giây
    cũng lấy được.

    Câu này trả lại phần CPU (dựng HTML lá thư) cho nhánh không gửi gì.

    ĐO LẠI SAU KHI VÁ, và con số nói thẳng rằng câu này CHƯA ĐỦ: có tài khoản 2,04–2,54 s,
    không có 0,254–0,263 s (ba lượt mỗi bên, email khác nhau để không chạm trần 3 chìa/giờ).
    Phần nặng KHÔNG phải CPU mà là SỐ VÒNG gọi CSDL — nhánh có tài khoản đi khoảng chín
    vòng (đếm chìa, huỷ chìa cũ, ghi chìa mới, xếp hộp thư, đánh thức luồng gửi), nhánh này
    đi một. Trên máy dev mỗi vòng VN → Neon us-east-2 mất ~250 ms, nên chín vòng thành hơn
    hai giây.

    Vì sao vẫn giữ câu này: nó đúng hướng và rẻ, và trên production phần CPU mới là phần
    KHÔNG tự nhỏ đi — Render `ohio` cùng vùng với Neon nên mỗi vòng chỉ vài mili giây và
    chín vòng chìm dưới nhiễu mạng, còn thời gian dựng HTML thì y nguyên.

    Vì sao CHƯA xoá hết: xoá nốt nghĩa là đưa cả nhánh gửi (sinh chìa, ghi, xếp thư) ra
    khỏi đường trả lời để hai nhánh cùng đúng MỘT vòng CSDL. Việc ấy làm được, nhưng nó
    đổi thứ tự bảo đảm của một cửa đang chạy — và nên làm khi có số đo TỪ production, vì
    số đo dev ở đây đo độ trễ đường truyền VN → Mỹ chứ không đo cái sẽ xảy ra với người
    dùng thật. Ghi ra để không ai đọc hàm này rồi tưởng khe hở đã đóng.

    Cùng khe hở này đã được cân ở cửa tự đăng ký §73 (`tu_dang_ky._can_dong_ho`), nơi phần
    nặng là scrypt chứ không phải HTML.
    """
    _soan_thu('Người dùng', '%s/dat-lai-mat-khau#chia=%s' % (_goc(), 'x' * SO_BYTE))


def _chia_con_dung(chia):
    """Dòng chìa còn dùng được (chưa dùng, chưa hết hạn, tài khoản chưa khoá), hoặc None."""
    if not chia or len(chia) > 200:
        return None
    return q1('''SELECT t.id, t.user_id, t.expires_at, u.email, u.name, u.status
                   FROM password_reset_tokens t JOIN users u ON u.id = t.user_id
                  WHERE t.token_hash=%s AND t.purpose='reset'
                    AND t.used_at IS NULL AND t.expires_at > %s''',
              (_bam(chia), local_now()))


class KiemChiaView(APIView):
    """POST /auth/dat-lai-mat-khau/kiem {chia} — trang đặt lại hỏi TRƯỚC khi hiện
    ô mật khẩu, để em không gõ xong hai ô rồi mới biết đường dẫn đã chết.

    POST chứ không GET: chìa không được nằm trên URL của bất kỳ lời gọi nào.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [QuenMatKhauThrottle]

    def post(self, request):
        body = request.data if isinstance(request.data, dict) else {}
        d = _chia_con_dung(str(body.get('chia') or '').strip())
        if not d or (d['status'] or 'active') == 'suspended':
            return Response({'hopLe': False, 'error': CAU_HET_HAN})
        return Response({'hopLe': True, 'email': _che(d['email']),
                         'hetHanLuc': d['expires_at'].isoformat()})


class DatLaiMatKhauView(APIView):
    """POST /auth/dat-lai-mat-khau {chia, password} — đặt mật khẩu mới."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [QuenMatKhauThrottle]

    def post(self, request):
        body = request.data if isinstance(request.data, dict) else {}
        chia = str(body.get('chia') or '').strip()
        mat_khau = str(body.get('password') or '')
        # Kiểm mật khẩu TRƯỚC khi tiêu chìa: gõ mật khẩu yếu không được đốt mất
        # đường dẫn — em sửa lại mật khẩu rồi bấm tiếp trên cùng trang.
        if loi := validate_password_field(mat_khau, label='Mật khẩu mới'):
            return Response({'errors': {'password': loi}}, status=400)

        bay_gio = local_now()
        with transaction.atomic():
            # Tiêu chìa bằng MỘT câu UPDATE có điều kiện: hai lần bấm cùng lúc
            # thì đúng một lần trả về dòng, lần kia nhận "hết hạn". Đọc rồi mới
            # ghi (hai câu) là để hở một khe cho cả hai cùng qua.
            d = q1('''UPDATE password_reset_tokens t SET used_at=%s
                        FROM users u
                       WHERE u.id = t.user_id AND t.token_hash=%s AND t.purpose='reset'
                         AND t.used_at IS NULL AND t.expires_at > %s
                         AND coalesce(u.status, 'active') <> 'suspended'
                   RETURNING t.user_id''',
                   (bay_gio, _bam(chia), bay_gio)) if chia and len(chia) <= 200 else None
            if not d:
                return Response({'error': CAU_HET_HAN}, status=400)
            uid = d['user_id']
            x('UPDATE users SET password=%s, must_change_password=FALSE, '
              'password_changed_at=%s, tokens_valid_from=%s WHERE id=%s',
              (make_werkzeug_password(mat_khau), bay_gio, bay_gio, uid))
            # Mọi chìa khác của em (thư cũ hơn) cũng chết theo.
            x("UPDATE password_reset_tokens SET used_at=%s "
              "WHERE user_id=%s AND purpose='reset' AND used_at IS NULL", (bay_gio, uid))

        from accounts.authentication import invalidate_user_cache
        invalidate_user_cache(uid)
        ai = User.objects.get(id=uid)
        audit.record(request, audit.USER_PASSWORD_SELF_RESET, actor=ai,
                     target_type='user', target_id=uid,
                     target_label=ai.name or ai.email or str(uid),
                     summary='Tự đặt lại mật khẩu qua đường dẫn trong email.')
        return Response({'ok': True})
