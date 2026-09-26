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
    trần hay chưa — phản hồi y hệt nhau. Thư gửi trên một LUỒNG RIÊNG, để thời
    gian trả lời cũng không khác nhau (SMTP Gmail mất 1–3 giây; chênh chừng ấy
    là đủ để dò danh sách học viên).
  · CHỈ LƯU BĂM của chìa (§52). Chìa nguyên văn chỉ nằm trong lá thư.
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
import threading
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.hashers import make_werkzeug_password
from accounts.models import User
from accounts.validators import validate_email_field, validate_password_field
from common import audit, mail
from common.clock import local_now
from common.db import q1, x
from common.identity import norm_email
from common.net import client_ip
from common.throttling import QuenMatKhauThrottle

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


def _gui_thu(den, ten, duong_dan):
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
    ok, _, loi = mail.gui(den, 'Đặt lại mật khẩu TopHSA', chu, trang)
    if not ok:
        # Ghi ĐỊA CHỈ ĐÃ CHE, không ghi đường dẫn: nhật ký ứng dụng đọc được
        # nhiều người hơn hộp thư của em.
        log.warning('[quen_mat_khau] không gửi được thư tới %s: %s', _che(den), loi)


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
            da_xin = q1('SELECT count(*) AS n FROM password_reset_tokens '
                        'WHERE user_id=%s AND created_at > %s',
                        (u['id'], bay_gio - timedelta(hours=1)))['n']
            if da_xin < TRAN_MOI_GIO:
                chia = secrets.token_urlsafe(SO_BYTE)
                with transaction.atomic():
                    # Chìa MỚI thay chìa cũ: chỉ đường dẫn trong lá thư gần nhất
                    # còn dùng được — em bấm nhầm thư cũ thì nhận câu "hết hạn".
                    x('UPDATE password_reset_tokens SET used_at=%s '
                      'WHERE user_id=%s AND used_at IS NULL', (bay_gio, u['id']))
                    x('INSERT INTO password_reset_tokens '
                      '(user_id, token_hash, created_at, expires_at, requested_ip) '
                      'VALUES (%s, %s, %s, %s, %s)',
                      (u['id'], _bam(chia), bay_gio, bay_gio + timedelta(minutes=HAN_PHUT),
                       client_ip(request)))
                duong_dan = '%s/dat-lai-mat-khau#chia=%s' % (_goc(), chia)
                if GUI_NGAY:
                    _gui_thu(u['email'], u['name'], duong_dan)
                else:
                    threading.Thread(target=_gui_thu, args=(u['email'], u['name'], duong_dan),
                                     daemon=True).start()
        return Response({'ok': True, 'message': CAU_CHUNG})


def _chia_con_dung(chia):
    """Dòng chìa còn dùng được (chưa dùng, chưa hết hạn, tài khoản chưa khoá), hoặc None."""
    if not chia or len(chia) > 200:
        return None
    return q1('''SELECT t.id, t.user_id, t.expires_at, u.email, u.name, u.status
                   FROM password_reset_tokens t JOIN users u ON u.id = t.user_id
                  WHERE t.token_hash=%s AND t.used_at IS NULL AND t.expires_at > %s''',
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
                       WHERE u.id = t.user_id AND t.token_hash=%s AND t.used_at IS NULL
                         AND t.expires_at > %s AND coalesce(u.status, 'active') <> 'suspended'
                   RETURNING t.user_id''',
                   (bay_gio, _bam(chia), bay_gio)) if chia and len(chia) <= 200 else None
            if not d:
                return Response({'error': CAU_HET_HAN}, status=400)
            uid = d['user_id']
            x('UPDATE users SET password=%s, must_change_password=FALSE, '
              'password_changed_at=%s, tokens_valid_from=%s WHERE id=%s',
              (make_werkzeug_password(mat_khau), bay_gio, bay_gio, uid))
            # Mọi chìa khác của em (thư cũ hơn) cũng chết theo.
            x('UPDATE password_reset_tokens SET used_at=%s WHERE user_id=%s AND used_at IS NULL',
              (bay_gio, uid))

        from accounts.authentication import invalidate_user_cache
        invalidate_user_cache(uid)
        ai = User.objects.get(id=uid)
        audit.record(request, audit.USER_PASSWORD_SELF_RESET, actor=ai,
                     target_type='user', target_id=uid,
                     target_label=ai.name or ai.email or str(uid),
                     summary='Tự đặt lại mật khẩu qua đường dẫn trong email.')
        return Response({'ok': True})
