"""HỌC VIÊN TỰ ĐĂNG KÝ (§73, E5 — bảng TopHSA dòng 26 + mốc "Đăng ký" của dòng 4).

Từ 27/08/2026 mọi tài khoản do trung tâm cấp (`views.RegisterView` đòi `IsAdminRole`).
Dòng 26 đòi ngược lại: em mới tự mở được tài khoản, rồi học vụ duyệt và xếp lớp. Mục này
mở lại cửa ấy mà KHÔNG mở lại lỗ hổng cũ (một lệnh curl là có tài khoản kèm quyền gọi
`/api/chat` — mỗi lượt chat là tiền thật trả cho DeepSeek).

── BA CỬA ──────────────────────────────────────────────────────────────────

  POST /auth/dang-ky           {name, email, phone, password, nguon, truong?,
                                lopOTruong?, mucTieu?}     → luôn cùng MỘT câu trả lời
  POST /auth/xac-thuc-email    {chia}                      → bật `is_verified`, vào hàng chờ
  POST /auth/gui-lai-xac-thuc  {email}                     → luôn cùng MỘT câu trả lời

── VÌ SAO TỪNG CHỖ NHƯ THẾ ─────────────────────────────────────────────────

  · TÀI KHOẢN CHƯA XÁC THỰC LÀ TÀI KHOẢN CHẾT. Không đăng nhập được (hàng rào ở
    `views.LoginView`), nên không có token, không gọi được API nào, không đốt được
    một xu tiền trợ lý AI. Và nó KHÔNG vào hộp việc của học vụ: dòng `yeu_cau`
    (`tk_dang_ky`) chỉ sinh ra ở cửa xác thực email, nên ai bơm địa chỉ bừa cũng
    không làm bẩn hàng chờ xếp lớp — chỉ để lại vài dòng `users` trơ.
  · HÀNG RÀO CHỈ CHẶN `self_registered AND NOT is_verified`. `is_verified` đã có
    trong lược đồ từ đầu nhưng CHƯA AI TỪNG GHI, nên với học viên hiện có nó là
    FALSE/NULL. Chặn theo `is_verified` trần là khoá cửa với toàn bộ TopHSA.
  · KHÔNG LỘ AI CÓ TÀI KHOẢN — cùng luật với `quen_mat_khau.py` và tờ phụ huynh.
    Email đã có tài khoản, số điện thoại đã thuộc người khác, quá trần: cùng MỘT
    câu 200. Nạn nhân của một lượt dò là trẻ vị thành niên, nên "ai học ở TopHSA"
    là dữ liệu đáng bảo vệ; một câu "Email đã được sử dụng" là một công cụ dò.
  · Thư đi qua HỘP THƯ ĐI (§61) trên luồng riêng sau commit, nên THỜI GIAN trả lời
    cũng không khác nhau giữa "có gửi" và "không gửi".
  · TÀI KHOẢN CHƯA XÁC THỰC KHÔNG ĐƯỢC THÀNH CÁI CHỐT CỬA. Ai gõ bừa email của em
    thì em vẫn đăng ký lại được trên chính dòng ấy (họ tên / mật khẩu / hồ sơ ghi
    đè, mã cũ chết) — không có luật này thì bất kỳ ai cũng khoá vĩnh viễn một địa
    chỉ email khỏi TopHSA bằng một lượt POST.
  · CHÌA ĐI TRONG PHẦN `#…` của đường dẫn (như `quen_mat_khau`, `oauth`): phần sau
    dấu `#` không bao giờ được trình duyệt gửi lên máy chủ nào, không vào nhật ký
    truy cập, không đi theo header Referer.
  · GỐC ĐƯỜNG DẪN LẤY TỪ `FRONTEND_URL`, không từ header Host — Host đổi được, và
    một lá thư trỏ về máy của kẻ gửi yêu cầu là lỗ chiếm tài khoản kinh điển.
  · `purpose='verify'` (§73b) tách mã xác thực khỏi mã đặt lại mật khẩu TRÊN CÙNG
    MỘT BẢNG. Cả hai chiều đều phải lọc: mã `verify` không đổi được mật khẩu, và
    một lượt xin đặt lại mật khẩu không được huỷ mã `verify` em chưa bấm.
  · HAI LỚP CHỐNG LẠM DỤNG. Lớp một: `DangKyThrottle` theo IP (mức ở
    `DEFAULT_THROTTLE_RATES`) — bộ đếm nằm trong bộ nhớ, khởi động lại là mất.
    Lớp hai: `TRAN_IP_MOI_NGAY` đếm TRONG CSDL số tài khoản chưa xác thực một IP
    đã mở trong 24 giờ; nó không mất theo tiến trình và không đếm oan những em đã
    xác thực xong (cả một lớp sau một NAT vẫn vào được).
"""
import hashlib
import html
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.hashers import make_werkzeug_password
from accounts.validators import (
    validate_email_field,
    validate_name_field,
    validate_password_field,
    validate_phone_field,
)
from common import audit
from common.clock import local_now
from common.db import q1, x
from common.identity import norm_email, norm_phone
from common.mail import ten_goi_trong_thu
from common.net import client_ip
from common.permissions import ROLE_STUDENT
from common.throttling import DangKyThrottle
from notifications import hop_thu

log = logging.getLogger(__name__)

#: Mã xác thực sống lâu hơn mã đặt lại mật khẩu (30 phút) rất nhiều: em đăng ký lúc 11 giờ
#: đêm rồi sáng mai mới mở hộp thư là chuyện thường, còn "đặt lại mật khẩu" thì em đang
#: ngồi trước máy chờ. Quá hạn vẫn xin lại được ở cửa "gửi lại thư xác nhận".
HAN_GIO = 72
#: Số mã một tài khoản được xin trong một giờ (gồm cả lượt đăng ký lại).
TRAN_MOI_GIO = 5
#: Số tài khoản CHƯA xác thực mà MỘT địa chỉ mạng mở được trong 24 giờ.
TRAN_IP_MOI_NGAY = 5
SO_BYTE = 32
VIEC = 'verify'

CAU_CHUNG = ('Đã nhận thông tin đăng ký. Nếu địa chỉ email này chưa có tài khoản TopHSA, '
             'hệ thống vừa gửi tới đó một thư xác nhận — bấm vào đường dẫn trong thư để '
             'kích hoạt tài khoản. Không thấy thư thì xem cả mục Thư rác. '
             'Sau %d giờ mà chưa bấm thì xin gửi lại thư ở trang đăng nhập.' % HAN_GIO)
CAU_HET_HAN = ('Đường dẫn xác nhận này đã hết hạn hoặc đã được dùng. Xin một thư mới ở '
               'trang đăng nhập, mục "Gửi lại thư xác nhận".')
#: Câu ở cửa đăng nhập khi tài khoản tự đăng ký chưa bấm thư. Nói CÁCH SỬA (RULES §10).
CAU_CHUA_XAC_THUC = ('Tài khoản này chưa xác nhận địa chỉ email. Mở hộp thư của bạn và bấm '
                     'vào đường dẫn trong thư TopHSA vừa gửi. Thư đã quá hạn hoặc không tới '
                     'thì xin gửi lại thư xác nhận ngay dưới đây.')

#: Phép kiểm đặt True để gửi thư ĐỒNG BỘ và đọc được lá thư ngay sau lời gọi.
GUI_NGAY = False


def _bam(chia):
    return hashlib.sha256(chia.encode('utf-8')).hexdigest()


def _goc():
    return (getattr(settings, 'FRONTEND_URL', '') or '').rstrip('/')


def chua_xac_thuc(user) -> bool:
    """Dòng `users` này đang bị hàng rào §73 chặn ở cửa đăng nhập?

    MỘT nơi quyết định, cho cả `LoginView` lẫn cửa gửi lại thư — hai chỗ hỏi cùng
    câu hỏi thì không được có hai câu trả lời (RULES §7).
    """
    return bool(user.get('self_registered')) and not bool(user.get('is_verified'))


def _soan_thu(ten, duong_dan):
    """(chữ thuần, html) của thư xác nhận địa chỉ email."""
    # MỘT DÒNG NGẮN, không phải chuỗi thô: `ten` ở cửa này là chữ người chưa đăng
    # nhập tự gõ, và địa chỉ nhận cũng vậy — xem `common/mail.ten_goi_trong_thu`.
    goi = ten_goi_trong_thu(ten)
    chu = ('Chào %s,\n\n'
           'Bạn vừa đăng ký tài khoản học tại TopHSA. Bấm vào đường dẫn dưới đây để xác '
           'nhận đây đúng là địa chỉ email của bạn:\n\n%s\n\n'
           'Đường dẫn dùng được một lần, trong %d giờ. Xác nhận xong là bạn đăng nhập '
           'được ngay; học vụ TopHSA sẽ liên hệ để xếp lớp phù hợp.\n\n'
           'Nếu không phải bạn đăng ký thì cứ bỏ qua thư này — không có tài khoản nào '
           'được kích hoạt.\n\n'
           'Thân mến,\nTopHSA\n' % (goi, duong_dan, HAN_GIO))
    trang = ('<p>Chào %s,</p>'
             '<p>Bạn vừa đăng ký tài khoản học tại TopHSA. Bấm nút dưới đây để xác nhận '
             'đây đúng là địa chỉ email của bạn:</p>'
             '<p><a href="%s" style="display:inline-block;padding:10px 18px;border-radius:8px;'
             'background:#4f46e5;color:#fff;text-decoration:none;font-weight:600">'
             'Xác nhận email</a></p>'
             '<p style="color:#6b7280">Đường dẫn dùng được một lần, trong %d giờ. Xác nhận '
             'xong là bạn đăng nhập được ngay; học vụ TopHSA sẽ liên hệ để xếp lớp phù hợp.</p>'
             '<p>Nếu không phải bạn đăng ký thì cứ bỏ qua thư này — không có tài khoản nào '
             'được kích hoạt.</p>'
             '<p style="color:#6b7280">Thân mến,<br>TopHSA</p>'
             % (html.escape(goi), html.escape(duong_dan, quote=True), HAN_GIO))
    return chu, trang


def _soan_thu_da_co(ten):
    """Thư gửi khi địa chỉ này ĐÃ có tài khoản. Không nói gì về vai, lớp hay tình trạng —
    chỉ chỉ đường về. Gửi tới địa chỉ CỦA CHÍNH tài khoản ấy nên không phải một đường
    bơm thư tới người lạ."""
    # MỘT DÒNG NGẮN, không phải chuỗi thô: `ten` ở cửa này là chữ người chưa đăng
    # nhập tự gõ, và địa chỉ nhận cũng vậy — xem `common/mail.ten_goi_trong_thu`.
    goi = ten_goi_trong_thu(ten)
    goc = _goc()
    chu = ('Chào %s,\n\n'
           'Vừa có một lượt đăng ký tài khoản TopHSA bằng địa chỉ email này, nhưng địa chỉ '
           'này đã có tài khoản rồi nên không có tài khoản mới nào được tạo.\n\n'
           'Nếu là bạn: cứ đăng nhập như bình thường ở %s/login. Không nhớ mật khẩu thì '
           'dùng "Quên mật khẩu" ngay tại trang đó.\n\n'
           'Nếu không phải bạn: bỏ qua thư này, tài khoản của bạn không bị ảnh hưởng gì.\n\n'
           'Thân mến,\nTopHSA\n' % (goi, goc))
    trang = ('<p>Chào %s,</p>'
             '<p>Vừa có một lượt đăng ký tài khoản TopHSA bằng địa chỉ email này, nhưng địa '
             'chỉ này đã có tài khoản rồi nên không có tài khoản mới nào được tạo.</p>'
             '<p><b>Nếu là bạn:</b> cứ đăng nhập như bình thường tại '
             '<a href="%s/login">%s/login</a>. Không nhớ mật khẩu thì dùng “Quên mật khẩu” '
             'ngay tại trang đó.</p>'
             '<p style="color:#6b7280"><b>Nếu không phải bạn:</b> bỏ qua thư này, tài khoản '
             'của bạn không bị ảnh hưởng gì.</p>'
             '<p style="color:#6b7280">Thân mến,<br>TopHSA</p>'
             % (html.escape(goi), html.escape(goc, quote=True), html.escape(goc)))
    return chu, trang


def _cap_chia(uid, ten, dia_chi, ip, *, bay_gio=None):
    """Cấp một mã `verify` mới cho `uid` và xếp lá thư. Gọi TRONG giao dịch của việc chính.

    Trả `(id_dòng_outbox | None, đã_cấp)`. Quá trần giờ → `(None, False)`, im lặng: trần
    này không được thành một cách phân biệt "có tài khoản" với "không".
    """
    bay_gio = bay_gio or local_now()
    da_xin = q1('SELECT count(*) AS n FROM password_reset_tokens '
                'WHERE user_id=%s AND purpose=%s AND created_at > %s',
                (uid, VIEC, bay_gio - timedelta(hours=1)))['n']
    if da_xin >= TRAN_MOI_GIO:
        return None, False
    chia = secrets.token_urlsafe(SO_BYTE)
    chu, trang = _soan_thu(ten, '%s/xac-thuc-email#chia=%s' % (_goc(), chia))
    het_han = bay_gio + timedelta(hours=HAN_GIO)
    # Mã MỚI giết mã cũ — em bấm lá thư cũ thì nhận câu "hết hạn", không phải hai mã
    # cùng sống. CHỈ chạm `purpose='verify'`: mã đặt lại mật khẩu của em là việc khác.
    x('UPDATE password_reset_tokens SET used_at=%s '
      'WHERE user_id=%s AND purpose=%s AND used_at IS NULL', (bay_gio, uid, VIEC))
    x('INSERT INTO password_reset_tokens '
      '(user_id, token_hash, purpose, created_at, expires_at, requested_ip) '
      'VALUES (%s, %s, %s, %s, %s, %s)',
      (uid, _bam(chia), VIEC, bay_gio, het_han, ip))
    # Thư chưa đi được trong hạn của mã thì bỏ; đi hay bỏ xong là thân có mã bị xoá.
    oid = hop_thu.xep('email', dia_chi, 'Xác nhận email tài khoản TopHSA', chu,
                      user_id=uid, source=('verify_email', None),
                      params={'html': trang, 'xoa_than': True,
                              'het_han': (timezone.now()
                                          + timedelta(hours=HAN_GIO)).isoformat()})
    return oid, True


def _qua_tran_ip(ip):
    """Địa chỉ mạng này đã mở quá nhiều tài khoản CHƯA xác thực trong 24 giờ?

    Đếm qua `password_reset_tokens.requested_ip` (mã `verify` nào cũng ghi IP lúc cấp) —
    không cần thêm cột nào vào `users`. Em nào đã xác thực xong thì KHÔNG bị đếm: một lớp
    35 em cùng đăng ký sau một NAT vẫn đi được, chỉ không để lại 35 dòng trơ.
    """
    if not ip:
        return False
    n = q1('''SELECT count(DISTINCT t.user_id) AS n
                FROM password_reset_tokens t JOIN users u ON u.id = t.user_id
               WHERE t.purpose = %s AND t.requested_ip = %s AND t.created_at > %s
                 AND u.self_registered AND NOT coalesce(u.is_verified, FALSE)''',
            (VIEC, ip, local_now() - timedelta(days=1)))['n']
    return n >= TRAN_IP_MOI_NGAY


def _can_dong_ho(mat_khau):
    """Bằm mật khẩu rồi VỨT ĐI — chỉ để cân đồng hồ, như `_DUMMY_HASH` ở `LoginView`.

    ĐO ĐƯỢC 27/09/2026 trên máy dev (VN → Neon us-east-2, mỗi vòng ~250 ms): nhánh TẠO
    tài khoản mất 3,82–4,00 s, nhánh "email đã có tài khoản" mất 1,43–1,96 s. Chênh gần
    HAI GIÂY, ổn định qua ba lượt — tức nội dung phản hồi giống hệt nhau nhưng ĐỒNG HỒ
    thì khai ra địa chỉ nào đã có tài khoản ở TopHSA. Câu này trả lại phần chi phí CPU
    (scrypt) cho nhánh không tạo gì.

    KHÔNG xoá hết chênh lệch, và không được nói dối là đã xoá: phần còn lại là số vòng
    gọi CSDL (nhánh tạo đi ~6 vòng, nhánh kia 2). Trên production, Render `ohio` cùng
    vùng với Neon nên mỗi vòng chỉ vài mili giây và phần dư ấy nhỏ hơn nhiễu mạng, còn
    phần scrypt (~126 ms, đo ở `LoginView`) thì không — nên đây là chỗ đáng cân nhất.
    Cùng khe hở còn ở `quen_mat_khau.QuenMatKhauView` (4 vòng khi có tài khoản, 1 khi
    không) — chưa vá, đã ghi vào báo cáo E5.
    """
    make_werkzeug_password(mat_khau)


def _chu(v, tran):
    s = str(v or '').strip()
    return s[:tran] or None


def _kiem(body):
    """`(giá_trị, errors)` — mọi ô của phiếu đăng ký, đã chuẩn hoá.

    Chuẩn hoá NGAY tại đây chứ không lúc tra CSDL: bản đầu của `RegisterView` kiểm trùng
    bằng `norm_*` nhưng INSERT chuỗi THÔ, và ai đăng ký bằng '+84912345678' bị khoá ngoài
    vĩnh viễn vì `LoginView` tra bằng '0912345678'.

    Danh mục nguồn biết tới trung tâm KHÔNG gõ lại ở đây — lấy từ `teaching/ho_so.py`
    (`NGUON_TUYEN_SINH`, khớp CHECK `users_enroll_source_check` §51). Gõ lại là bản thứ
    hai sẽ trôi, rồi một lựa chọn trên màn sẽ bị CSDL từ chối (RULES §7).
    """
    from teaching.ho_so import NGUON_TUYEN_SINH

    ten = str(body.get('name') or '').strip()
    email = norm_email(body.get('email')) or ''
    phone = norm_phone(body.get('phone')) or ''
    mat_khau = str(body.get('password') or '')
    nguon = str(body.get('nguon') or '').strip()

    e = {}
    if loi := validate_name_field(ten):
        e['name'] = loi
    if not email:
        e['email'] = 'Nhập địa chỉ email của bạn — thư xác nhận sẽ gửi tới đó.'
    elif loi := validate_email_field(email):
        e['email'] = loi
    if not phone:
        e['phone'] = 'Nhập số điện thoại để học vụ gọi lại xếp lớp.'
    elif loi := validate_phone_field(phone):
        e['phone'] = loi
    if loi := validate_password_field(mat_khau):
        e['password'] = loi
    if nguon not in {m for m, _ in NGUON_TUYEN_SINH}:
        e['nguon'] = 'Chọn một mục trong danh sách.'
    return ({'ten': ten, 'email': email, 'phone': phone, 'mat_khau': mat_khau, 'nguon': nguon,
             'truong': _chu(body.get('truong'), 200),
             'lop_o_truong': _chu(body.get('lopOTruong'), 40),
             'muc_tieu': _chu(body.get('mucTieu'), 500)}, e)


class DangKyView(APIView):
    """POST /auth/dang-ky — học viên mới tự mở tài khoản (§73).

    `authentication_classes = []`: người đăng ký có thể còn một thẻ HẾT HẠN trong cookie
    (máy dùng chung, em khác vừa dùng), và kiểm thẻ ấy là 401 đúng ở cửa họ cần vào.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [DangKyThrottle]

    def get(self, request):
        """GET /auth/dang-ky — danh mục cho ô chọn trên phiếu (RULES §7: màn KHÔNG gõ lại
        danh mục). Chỉ trả nhãn, không trả gì về ai đã có tài khoản."""
        from teaching.ho_so import NGUON_TUYEN_SINH
        return Response({'nguon': [{'ma': m, 'nhan': n} for m, n in NGUON_TUYEN_SINH]})

    def post(self, request):
        body = request.data if isinstance(request.data, dict) else {}
        v, loi = _kiem(body)
        # Sai DẠNG thì nói ngay — đó là lỗi gõ, không lộ gì về ai có tài khoản.
        if loi:
            return Response({'errors': loi}, status=400)

        ip = client_ip(request)
        oid = None
        cu = q1('SELECT id, name, email, self_registered, is_verified, status '
                'FROM users WHERE lower(email)=%s', (v['email'],))
        if cu is not None and not chua_xac_thuc(cu):
            # Địa chỉ đã thuộc một tài khoản THẬT: không tạo gì, chỉ chỉ đường về. Thư
            # đi tới địa chỉ CỦA CHÍNH tài khoản ấy nên không phải đường bơm thư.
            _can_dong_ho(v['mat_khau'])
            if (cu['status'] or 'active') != 'suspended':
                chu, trang = _soan_thu_da_co(cu['name'])
                with transaction.atomic():
                    oid = hop_thu.xep('email', cu['email'], 'Địa chỉ này đã có tài khoản TopHSA',
                                      chu, user_id=cu['id'], source=('verify_email', None),
                                      params={'html': trang})
        elif _qua_tran_ip(ip):
            # Quá trần: im lặng. Không 429 — mã trạng thái khác nhau cũng là tín hiệu,
            # và ở đây nó còn nói thẳng "trần này đếm theo IP", tức chỉ đường cho kẻ dò.
            _can_dong_ho(v['mat_khau'])
            log.warning('[dang-ky] quá trần %d tài khoản chưa xác thực / 24h từ một địa chỉ mạng',
                        TRAN_IP_MOI_NGAY)
        else:
            oid = self._mo_tai_khoan(request, v, cu, ip)
        if oid:
            hop_thu.day_di([oid], ngay=GUI_NGAY)
        # MỘT câu cho mọi nhánh — xem docstring module.
        return Response({'ok': True, 'message': CAU_CHUNG})

    @staticmethod
    def _mo_tai_khoan(request, v, cu, ip):
        """Tạo (hoặc nhận lại) dòng `users` chưa xác thực rồi cấp mã. Trả id dòng thư."""
        from teaching.ho_so import cap_ma_hoc_vien

        bam = make_werkzeug_password(v['mat_khau'])
        try:
            with transaction.atomic():
                if cu is not None:
                    # Nhận lại một dòng CHƯA XÁC THỰC (xem docstring module). Khoá dòng:
                    # hai lượt đăng ký cùng lúc trên một email thì chỉ một cấp mã cuối.
                    q1('SELECT id FROM users WHERE id=%s FOR UPDATE', (cu['id'],))
                    uid = cu['id']
                    x('''UPDATE users SET name=%s, phone=%s, password=%s, role=%s,
                                          enroll_source=%s, school=%s, school_grade=%s,
                                          study_goal=%s, self_registered=TRUE,
                                          is_verified=FALSE, must_change_password=FALSE
                          WHERE id=%s''',
                      (v['ten'], v['phone'], bam, ROLE_STUDENT, v['nguon'], v['truong'],
                       v['lop_o_truong'], v['muc_tieu'], uid))
                else:
                    uid = q1('''INSERT INTO users
                                    (name, email, phone, password, role, self_registered,
                                     is_verified, must_change_password, enroll_source, school,
                                     school_grade, study_goal, streak)
                                VALUES (%s, %s, %s, %s, %s, TRUE, FALSE, FALSE, %s, %s, %s, %s, 0)
                                RETURNING id''',
                             (v['ten'], v['email'], v['phone'], bam, ROLE_STUDENT, v['nguon'],
                              v['truong'], v['lop_o_truong'], v['muc_tieu']))['id']
                cap_ma_hoc_vien(uid)
                oid, _ = _cap_chia(uid, v['ten'], v['email'], ip)
        except IntegrityError:
            # Đụng chỉ mục duy nhất: số điện thoại (hay email) đã thuộc người khác, hoặc
            # vừa được người khác dùng trong khoảng giữa câu tra ở trên và câu ghi này.
            # KHÔNG nói ô nào — "Số điện thoại đã được sử dụng" là một công cụ dò xem ai
            # học ở TopHSA. Người thật gặp ca này sẽ nhắn học vụ (câu chung nói cách đó).
            log.info('[dang-ky] trùng chỉ mục duy nhất — không tạo, trả câu chung')
            return None
        audit.record(request, audit.USER_SELF_REGISTER, target_type='user', target_id=uid,
                     target_label=v['ten'] or v['email'],
                     summary='Tự đăng ký tài khoản học viên ở trang /dang-ky.',
                     detail={'nguon': v['nguon']})
        return oid


class XacThucEmailView(APIView):
    """POST /auth/xac-thuc-email {chia} — bật `is_verified` và đưa em vào hàng chờ xếp lớp.

    POST chứ không GET: mã không được nằm trên URL của bất kỳ lời gọi nào. Trang
    `/xac-thuc-email` đọc mã từ `location.hash` rồi gọi cửa này.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [DangKyThrottle]

    def post(self, request):
        body = request.data if isinstance(request.data, dict) else {}
        chia = str(body.get('chia') or '').strip()
        bay_gio = local_now()
        with transaction.atomic():
            # Tiêu mã bằng MỘT câu UPDATE có điều kiện: hai lần bấm cùng lúc thì đúng một
            # lần trả về dòng, lần kia nhận "hết hạn". Đọc rồi mới ghi là để hở một khe.
            d = q1('''UPDATE password_reset_tokens t SET used_at=%s
                        FROM users u
                       WHERE u.id = t.user_id AND t.token_hash=%s AND t.purpose=%s
                         AND t.used_at IS NULL AND t.expires_at > %s
                         AND coalesce(u.status, 'active') <> 'suspended'
                   RETURNING t.user_id, u.name, u.email,
                             coalesce(u.is_verified, FALSE) AS da''',
                   (bay_gio, _bam(chia), VIEC, bay_gio)) if chia and len(chia) <= 200 else None
            if not d:
                return Response({'error': CAU_HET_HAN}, status=400)
            uid = d['user_id']
            x('UPDATE users SET is_verified=TRUE WHERE id=%s', (uid,))
            if not d['da']:
                # Hàng chờ "Đăng ký mới" = hộp Yêu cầu §65, KHÔNG phải một hộp mới. Chỉ
                # sinh dòng ấy KHI ĐÃ xác thực, nên hộp việc của học vụ không có rác.
                _vao_hang_cho(request, uid, d['name'], d['email'])
        from accounts.authentication import invalidate_user_cache
        invalidate_user_cache(uid)
        audit.record(request, audit.USER_VERIFY_EMAIL, target_type='user', target_id=uid,
                     target_label=d['name'] or d['email'] or str(uid),
                     summary='Xác nhận địa chỉ email qua đường dẫn trong thư đăng ký.',
                     luc=bay_gio)
        return Response({'ok': True,
                         'message': 'Đã xác nhận email. Bạn đăng nhập được ngay bây giờ. '
                                    'Học vụ TopHSA sẽ liên hệ để xếp lớp.'})


def _vao_hang_cho(request, uid, ten, dia_chi):
    """Một dòng `tk_dang_ky` trong hộp Yêu cầu (§65) — cửa DUY NHẤT là `yeu_cau.dich_vu.tao`
    (luật S4: miền `tai_khoan` không ghi bảng của miền `yeu_cau`)."""
    from accounts.models import User
    from teaching.ho_so import NGUON_TUYEN_SINH
    from yeu_cau import dich_vu as dv

    r = q1('SELECT phone, enroll_source, school, school_grade, study_goal FROM users WHERE id=%s',
           (uid,)) or {}
    # NHÃN chứ không mã: `du_lieu` hiện nguyên trên thẻ chi tiết của học vụ, và
    # "facebook" / "gioi_thieu" là mã kỹ thuật (RULES §10).
    nhan_nguon = dict(NGUON_TUYEN_SINH).get(r.get('enroll_source'))
    try:
        dv.tao(dv.NguoiLam(user=User.objects.get(id=uid)), loai='tk_dang_ky',
               tieu_de='Đăng ký mới: %s' % (ten or dia_chi or 'học viên'),
               noi_dung=r.get('study_goal'),
               du_lieu={'sdt': r.get('phone'), 'nguon': nhan_nguon,
                        'truong': r.get('school'), 'lop_o_truong': r.get('school_grade')},
               request=request, he_thong=True)
    except dv.LoiYeuCau:
        # Không nuốt im lặng (RULES §8): em ĐÃ xác thực xong, không được vì hộp Yêu cầu
        # trục trặc mà chặn luôn đường đăng nhập của em. Vết đi vào log kèm id để học vụ
        # còn dựng lại được việc bằng tay.
        log.exception('[dang-ky] không đưa được em #%s vào hàng chờ xếp lớp', uid)


class GuiLaiXacThucView(APIView):
    """POST /auth/gui-lai-xac-thuc {email} — gửi lại thư cho tài khoản chưa xác thực.

    Luôn cùng MỘT câu trả lời, kể cả khi email không có tài khoản, tài khoản đã xác thực
    rồi, hay đã quá trần — cùng lý lẽ với `QuenMatKhauView`.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [DangKyThrottle]

    def post(self, request):
        body = request.data if isinstance(request.data, dict) else {}
        email = norm_email(str(body.get('email') or '').strip()) or ''
        if not email or validate_email_field(email):
            return Response({'errors': {'email': 'Nhập đúng địa chỉ email của tài khoản.'}},
                            status=400)
        u = q1('SELECT id, name, email, status, self_registered, is_verified '
               'FROM users WHERE lower(email)=%s', (email,))
        oid = None
        if u and chua_xac_thuc(u) and (u['status'] or 'active') != 'suspended':
            with transaction.atomic():
                oid, _ = _cap_chia(u['id'], u['name'], u['email'], client_ip(request))
        if oid:
            hop_thu.day_di([oid], ngay=GUI_NGAY)
        return Response({'ok': True, 'message': CAU_CHUNG})
