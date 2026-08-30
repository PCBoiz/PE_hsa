"""
Port routes/auth.py + routes/user.py (Flask) — giữ nguyên body/status từng response.
Khác biệt DUY NHẤT (có chủ đích, MIGRATION_NOTES §Auth): login/register trả thêm
cặp JWT access/refresh thay vì set session cookie (frontend ở domain khác).
"""
import json
from datetime import datetime

import logging

from django.db import DatabaseError, IntegrityError, transaction
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.hashers import check_werkzeug_password, make_werkzeug_password
from accounts.validators import (validate_email_field, validate_name_field,
                                 validate_password_field, validate_phone_field)
from common.clock import local_now
from common.identity import looks_like_email, norm_email, norm_phone
from common.permissions import IsAdminRole
from common.db import q, q1, x
from common.throttling import LoginThrottle, RegisterThrottle


logger = logging.getLogger(__name__)

#: Hash để bằm đối chứng khi không tìm thấy tài khoản (xem LoginView).
#: Tính sẵn một lần ở tầm module: tính lúc chạy sẽ tự nó thành một chênh lệch
#: thời gian mới, đúng thứ đang muốn xoá.
_DUMMY_HASH = make_werkzeug_password('khong-phai-mat-khau-cua-ai')


def _tokens_for(user_id):
    """Cấp cặp JWT cho user id (SimpleJWT)."""
    from accounts.models import User
    refresh = RefreshToken.for_user(User(id=user_id))
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


# ─────────────────────────── /auth/* ───────────────────────────

class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]   # 5 per minute (Flask @limiter.limit)

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        identifier = (data.get('email') or data.get('phone') or '').strip()
        password = data.get('password', '')
        errors = {}
        if not identifier:
            errors['email'] = 'Email hoặc số điện thoại không được để trống'
        elif looks_like_email(identifier):
            if err := validate_email_field(identifier):
                errors['email'] = err
        # Kiểm SỐ ĐÃ CHUẨN HOÁ, không kiểm chuỗi người dùng gõ.
        #
        # `validate_phone_field` chỉ nhận '0' + 9 số hoặc '+' + mã nước + 9 số,
        # nên '0912 345 678' — cách gần như ai cũng viết khi chép từ phiếu đăng
        # ký — bị chặn ngay tại đây với câu "số điện thoại phải có 10 số", trong
        # khi `norm_phone` phía dưới thừa sức đưa nó về đúng dạng. Người dùng bị
        # từ chối vì mấy dấu cách, và câu lỗi thì bảo họ sai thứ họ không sai.
        elif err := validate_phone_field(norm_phone(identifier) or identifier):
            errors['email'] = err
        if not password:
            errors['password'] = 'Mật khẩu không được để trống'
        if errors:
            return Response({'errors': errors}, status=400)

        # Tra theo bản ĐÃ CHUẨN HOÁ, không theo chuỗi người dùng gõ.
        # Trước 30/08/2026 chỗ này so khớp nguyên văn trong khi bên tạo tài
        # khoản lại lưu email hạ chữ thường — bàn phím điện thoại tự viết hoa
        # chữ đầu là đủ để học viên nhận "sai mật khẩu" dù tài khoản nằm ngay
        # đó, và từ khi bỏ tự đăng ký thì em không có đường nào tự thoát.
        # Số điện thoại cùng một lỗi: +84912345678 và 0912345678 là một người.
        # `lower(email)` và `phone` đều có chỉ mục duy nhất (schema §31) nên
        # câu này vẫn tra theo chỉ mục, không quét bảng.
        if looks_like_email(identifier):
            user = q1('SELECT * FROM users WHERE lower(email)=%s', (norm_email(identifier),))
        else:
            user = q1('SELECT * FROM users WHERE phone=%s', (norm_phone(identifier),))
        if not user:
            # Vẫn bằm một lần dù biết chắc sẽ hỏng — để cân thời gian phản hồi.
            #
            # Nội dung và mã trạng thái đã giống hệt nhau cho mọi trường hợp,
            # nhưng ĐỒNG HỒ thì không: tìm thấy tài khoản mới chạy scrypt
            # (~126ms), không tìm thấy thì trả về ngay. Đo được chênh lệch
            # +134,8ms rất ổn định (audit 30/08/2026) — đủ để dò xem một email
            # có từng học ở TopHSA hay không mà không cần biết mật khẩu. Nạn
            # nhân là trẻ vị thành niên, nên danh sách "ai học ở đây" là dữ liệu
            # đáng bảo vệ. Chênh lệch này còn nguyên ở production vì nó đến từ
            # chi phí bằm, không phải từ độ trễ CSDL.
            check_werkzeug_password(_DUMMY_HASH, password)
            return Response({'error': 'Email/số điện thoại hoặc mật khẩu không đúng'}, status=401)

        stored = user['password']
        if not stored:
            return Response({'error': 'Email/số điện thoại hoặc mật khẩu không đúng'}, status=401)
        is_hashed = stored.startswith(('pbkdf2:', 'scrypt:'))
        if is_hashed:
            ok = check_werkzeug_password(stored, password)
        else:
            # Legacy plaintext (nếu còn sót): so trực tiếp rồi nâng cấp lên hash
            ok = (stored == password)
            if ok:
                x('UPDATE users SET password=%s WHERE id=%s',
                  (make_werkzeug_password(password), user['id']))

        if not ok:
            return Response({'error': 'Email/số điện thoại hoặc mật khẩu không đúng'}, status=401)

        # Tài khoản trung tâm đã khoá (học xong hoặc nghỉ giữa chừng, schema §31).
        # Đặt SAU khi kiểm mật khẩu là cố ý: trả lời "tài khoản đã khoá" trước
        # khi biết người gõ có đúng là chủ tài khoản không thì bất kỳ ai cũng
        # dò được email nào từng học ở TopHSA.
        # Vẫn phải chặn ở đây dù `User.is_active` đã cắt mọi lời gọi API sau đó:
        # không có câu này thì đăng nhập vẫn "thành công", cấp token, rồi màn
        # hình kế tiếp mới đổ 401 — học viên không hiểu chuyện gì xảy ra.
        if (user.get('status') or 'active') != 'active':
            return Response({'error': 'Tài khoản này đã được trung tâm khoá. '
                                      'Liên hệ TopHSA nếu bạn cần mở lại.'}, status=403)

        needs_questionnaire = not bool(user['questionnaire_completed'])
        return Response({
            'ok': True,
            'name': user['name'],
            'needs_questionnaire': needs_questionnaire,
            # Tài khoản do trung tâm cấp kèm mật khẩu tạm — trợ giảng biết mật
            # khẩu đó, nên phải bắt đổi ngay lần đăng nhập đầu tiên.
            # Dùng `.get()` chứ không phải `user['...']`: cột này thêm ngày
            # 27/08/2026 và bootstrap_schema chạy lúc dựng bản; đọc kiểu này thì
            # mã mới vẫn chạy trên CSDL chưa kịp thêm cột, thay vì làm hỏng đăng
            # nhập của tất cả mọi người.
            'must_change_password': bool(user.get('must_change_password')),
            **_tokens_for(user['id']),
        })


class RegisterView(APIView):
    """Tạo tài khoản. CHỈ QUẢN TRỊ VIÊN, từ 27/08/2026.

    Đổi chính sách: học viên không tự mở tài khoản nữa. Trung tâm lấy email/số
    điện thoại lúc học viên đăng ký học rồi tạo tài khoản và đưa mật khẩu tạm
    tận tay — nhờ vậy trung tâm biết chính xác ai đang có mặt trong hệ thống.

    Trang /register phía người dùng đã xoá và nhánh OAuth cũng đã chặn tạo tài
    khoản mới (accounts/oauth.py). Nếu để endpoint này ở `AllowAny` thì cả hai
    lần vá kia thành vô nghĩa: một lệnh curl thẳng vào backend là có tài khoản,
    kèm quyền gọi /api/chat — mỗi lượt chat là tiền thật trả cho DeepSeek.
    """
    permission_classes = [IsAdminRole]
    throttle_classes = [RegisterThrottle]   # 3 per minute

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        name = (data.get('name') or '').strip()
        # Chuẩn hoá NGAY tại đây, không phải lúc tra CSDL.
        #
        # Bản trước kiểm trùng bằng `norm_email`/`norm_phone` nhưng lại INSERT
        # chuỗi THÔ. Ai đăng ký bằng '+84912345678' sẽ có một dòng users mang
        # đúng chuỗi đó, trong khi `LoginView` tra bằng `norm_phone(...)` tức
        # '0912345678' — không bao giờ khớp. Tài khoản khoá ngoài vĩnh viễn, mà
        # từ khi bỏ tự đăng ký thì cũng không còn đường nào tự lấy lại.
        # Chuẩn hoá một phía là tái tạo đúng cái khe common/identity.py sinh ra
        # để bịt; chuẩn hoá ở đầu vào thì mọi bước sau tự động dùng chung một
        # giá trị và không còn chỗ cho hai bên lệch nhau.
        email = norm_email(data.get('email')) or ''
        phone = norm_phone(data.get('phone')) or ''
        password = data.get('password', '')

        errors = {}
        if err := validate_name_field(name):
            errors['name'] = err
        if not email and not phone:
            msg = 'Vui lòng nhập email hoặc số điện thoại'
            errors['email'] = msg
            errors['phone'] = msg
        else:
            if email:
                if err := validate_email_field(email):
                    errors['email'] = err
            if phone:
                if err := validate_phone_field(phone):
                    errors['phone'] = err
        if err := validate_password_field(password):
            errors['password'] = err
        if errors:
            return Response({'errors': errors}, status=400)

        if email and q1('SELECT id FROM users WHERE lower(email)=%s', (email,)):
            return Response({'errors': {'email': 'Email đã được sử dụng'}}, status=400)
        if phone and q1('SELECT id FROM users WHERE phone=%s', (phone,)):
            return Response({'errors': {'phone': 'Số điện thoại đã được sử dụng'}}, status=400)

        try:
            user = q1(
                'INSERT INTO users (name, email, phone, password, role) '
                'VALUES (%s, %s, %s, %s, %s) RETURNING id, questionnaire_completed',
                (name, email or None, phone or None,
                 make_werkzeug_password(password), 'Học viên'))
        except IntegrityError:
            # Đụng chỉ mục duy nhất — hai người cùng gửi một email trong khoảng
            # giữa câu kiểm trùng ở trên và câu ghi này. Hiếm, nhưng có thật, và
            # đúng ra phải là 400 chứ không phải 500: người dùng sửa được.
            return Response({'errors': {'email': 'Email hoặc số điện thoại này vừa '
                                                 'được người khác dùng. Thử lại.'}},
                            status=400)
        # KHÔNG bắt `Exception` ở đây nữa.
        #
        # Bản trước trả `f'Lỗi hệ thống khi đăng ký: {str(e)}'` — mà `str(e)` của
        # psycopg chứa tên bảng, tên cột, đôi khi cả câu SQL và giá trị tham số,
        # gửi thẳng cho client. Nó còn nuốt luôn `Http404`/`PermissionDenied` và
        # biến chúng thành 500. `common/errors.py` đã lo việc này tử tế: ghi log
        # kèm request_id rồi trả một câu tiếng Việt trung tính — bắt ở đây chỉ
        # vô hiệu hoá nó.

        needs_questionnaire = not bool(user['questionnaire_completed'])
        return Response({'ok': True, 'needs_questionnaire': needs_questionnaire,
                         **_tokens_for(user['id'])})


class LogoutView(APIView):
    """GET /auth/logout — bản JWT: blacklist refresh token nếu client gửi kèm.

    Flask cũ clear session rồi redirect '/'; với JWT client tự xoá token là chính,
    endpoint này để thu hồi refresh token (POST body {'refresh': ...} tùy chọn).
    """
    permission_classes = [AllowAny]

    def _logout(self, request):
        token = None
        if isinstance(request.data, dict):
            token = request.data.get('refresh')
        revoked = False
        if token:
            try:
                RefreshToken(token).blacklist()
                revoked = True
            except TokenError as exc:
                # Token đã hết hạn hoặc đã thu hồi rồi — bình thường, không đáng
                # báo động, nhưng vẫn phải để lại vết.
                logger.info('[logout] không thu hồi được refresh token: %s', exc)
            except DatabaseError as exc:
                # Bảng blacklist hỏng. ĐÂY mới là chuyện nghiêm trọng: người dùng
                # bấm "đăng xuất", cookie bị xoá nên trông như đã ra, NHƯNG refresh
                # token còn sống tới 8 tiếng (SIMPLE_JWT.REFRESH_TOKEN_LIFETIME).
                # Ai chép được chuỗi đó vẫn cấp lại access token được — mà trung
                # tâm thì dùng máy chung. `except Exception: pass` của bản trước
                # giấu kín đúng tình huống này.
                logger.error('[logout] KHÔNG thu hồi được refresh token, '
                             'phiên vẫn sống tới 8 tiếng: %s', exc)
        # `revoked` để bên gọi và log biết chuyện gì thật sự xảy ra. Vẫn luôn
        # trả ok: người bấm đăng xuất phải luôn được đăng xuất, kể cả khi backend
        # đang trục trặc — cookie do lớp trung gian Next xoá, không phụ thuộc câu này.
        return Response({'ok': True, 'revoked': revoked})

    def get(self, request):
        return self._logout(request)

    def post(self, request):
        return self._logout(request)


# ─────────────────────────── /api/user ───────────────────────────

class UserView(APIView):
    def get(self, request):
        # Liệt kê cột TRẮNG, không `SELECT *`.
        #
        # Bản trước lấy hết rồi chỉ `pop('password')`, nên trả về 25 cột — trong
        # đó có `status_note`: GHI CHÚ NỘI BỘ của quản trị viên về học viên, ví
        # dụ lý do khoá tài khoản. Chính em đó đọc được ghi chú viết về mình.
        # Và mọi cột thêm vào bảng `users` sau này sẽ tự động rò ra API mà không
        # ai phải làm gì cả — đó mới là phần nguy hiểm lâu dài.
        user = q1('''SELECT id, name, email, phone, birthday, role, avatar,
                            streak, streak_freezes, certificates, gems, xp,
                            questionnaire_completed, last_study_date,
                            is_verified, created_at, status,
                            must_change_password, password_changed_at
                     FROM users WHERE id=%s''', (request.user.id,))
        if not user:
            return Response({}, status=404)
        user['is_new_user'] = not bool(user.get('questionnaire_completed'))
        user['first_login'] = user['is_new_user']
        return Response(user)

    def put(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        phone = (data.get('phone') or '').strip()
        birthday = (data.get('birthday') or '').strip()

        errors = {}
        if err := validate_name_field(name):
            errors['name'] = err
        if err := validate_email_field(email):
            errors['email'] = err
        if err := validate_phone_field(phone):
            errors['phone'] = err
        if errors:
            return Response({'errors': errors}, status=400)

        # Trùng email/phone của người khác → 400 như /auth/register (tránh 500 do
        # IntegrityError khi vi phạm UNIQUE constraint users.email). Loại trừ chính mình.
        uid = request.user.id
        if email and q1('SELECT id FROM users WHERE lower(email)=%s AND id<>%s',
                        (norm_email(email), uid)):
            return Response({'errors': {'email': 'Email đã được sử dụng'}}, status=400)
        if phone and q1('SELECT id FROM users WHERE phone=%s AND id<>%s',
                        (norm_phone(phone), uid)):
            return Response({'errors': {'phone': 'Số điện thoại đã được sử dụng'}}, status=400)

        # Ghi bản ĐÃ chuẩn hoá. Chỉ chuẩn hoá lúc TRA mà không chuẩn hoá lúc
        # GHI là tái tạo đúng cái khe vừa vá: người dùng tự sửa hồ sơ thành
        # "An@Gmail.com", lần đăng nhập sau không khớp nữa.
        x('UPDATE users SET name=%s, email=%s, phone=%s, birthday=%s WHERE id=%s',
          (name, norm_email(email), norm_phone(phone), birthday, uid))
        return Response({'ok': True})


class PasswordView(APIView):
    def put(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        current = data.get('current', '')
        new_pw = data.get('new', '')
        errors = {}
        if err := validate_password_field(new_pw, label='Mật khẩu mới'):
            errors['new'] = err
        if errors:
            return Response({'errors': errors}, status=400)
        user = q1('SELECT password FROM users WHERE id=%s', (request.user.id,))
        stored = user['password'] if user else None
        if not stored:
            return Response({'error': 'Mật khẩu hiện tại không đúng'}, status=401)
        is_hashed = stored.startswith(('pbkdf2:', 'scrypt:'))
        pw_ok = check_werkzeug_password(stored, current) if is_hashed else (stored == current)
        if not pw_ok:
            return Response({'error': 'Mật khẩu hiện tại không đúng'}, status=401)

        # Mật khẩu mới KHÔNG được trùng mật khẩu hiện tại.
        #
        # Trước 31/08/2026 chỉ giao diện kiểm điều này, nên gọi thẳng API là đặt
        # lại đúng mật khẩu tạm cũ VÀ được gỡ cờ `must_change_password`. Kết
        # quả: hệ thống ghi nhận "em đã đổi mật khẩu rồi", trong khi mật khẩu
        # vẫn là chuỗi trợ giảng đọc qua điện thoại — và trợ giảng đó vẫn nhớ
        # nó. Cả cơ chế bắt đổi mật khẩu lần đầu bị vô hiệu bằng một lời gọi.
        #
        # So sánh ở đây thay vì so hai chuỗi thô: mật khẩu trong CSDL đã băm,
        # nên "trùng hay không" chỉ trả lời được bằng chính hàm kiểm băm.
        trung = check_werkzeug_password(stored, new_pw) if is_hashed else (stored == new_pw)
        if trung:
            return Response(
                {'errors': {'new': 'Mật khẩu mới phải khác mật khẩu hiện tại.'}},
                status=400)

        # Đổi xong thì gỡ cờ bắt buộc: mật khẩu tạm do trợ giảng đặt nay đã
        # được thay bằng mật khẩu chỉ học viên biết.
        # `local_now()` chứ không phải `now()` của SQL: giờ máy chủ là UTC, lệch
        # 7 tiếng so với giờ Việt Nam — đủ để ghi sai ngày.
        x('UPDATE users SET password=%s, must_change_password=FALSE, '
          'password_changed_at=%s WHERE id=%s',
          (make_werkzeug_password(new_pw), local_now(), request.user.id))
        return Response({'ok': True})


# ─────────────── Follow (nguồn thật cho leaderboard "friends") ───────────────

class FollowView(APIView):
    def post(self, request, user_id):
        uid = request.user.id
        if user_id == uid:
            return Response({'error': 'Không thể tự follow chính mình'}, status=400)
        target = q1('SELECT id FROM users WHERE id=%s', (user_id,))
        if not target:
            return Response({'error': 'Không tìm thấy người dùng'}, status=404)
        x('INSERT INTO user_follows (follower_id, followee_id) '
          'VALUES (%s, %s) ON CONFLICT DO NOTHING', (uid, user_id))
        return Response({'ok': True, 'following': True})

    def delete(self, request, user_id):
        x('DELETE FROM user_follows WHERE follower_id=%s AND followee_id=%s',
          (request.user.id, user_id))
        return Response({'ok': True, 'following': False})


class FollowingView(APIView):
    """Danh sách người mà MÌNH đang theo dõi.

    `user_id` trên đường dẫn phải là chính mình. Trước 30/08/2026 endpoint này
    nhận bất kỳ id nào, nên một học viên đọc được đồ thị theo dõi của học viên
    khác (kèm tên, XP, chuỗi ngày). Giữ tham số trên đường dẫn để không phá
    đường gọi cũ, nhưng chặn ở đây.
    """

    def get(self, request, user_id):
        if int(user_id) != request.user.id:
            return Response({'error': 'Không xem được danh sách của người khác.'},
                            status=403)
        rows = q('''SELECT u.id, u.name, u.xp, u.streak, f.created_at
                    FROM user_follows f
                    JOIN users u ON u.id = f.followee_id
                    WHERE f.follower_id = %s
                    ORDER BY f.created_at DESC''', (user_id,))
        result = []
        for d in rows:
            created_at = d.pop('created_at')
            d['followedAt'] = created_at.isoformat() if created_at else None
            result.append(d)
        return Response({'following': result})


# ─────────────────────────── /api/survey ───────────────────────────

# Đáp án đúng mini-test chẩn đoán (khớp questionaire/page.tsx).
_HSA_DIAG_KEY = {
    'dq_ql_1': 'C', 'dq_ql_2': 'C',   # Định lượng
    'dq_qt_1': 'D', 'dq_qt_2': 'B',   # Định tính
    'dq_kh_1': 'B', 'dq_kh_2': 'C',   # Khoa học
}

# 3 hợp phần HSA: (nhãn, mô tả gốc).
_HSA_SECTIONS = {
    'ql': ('Tư duy Định lượng', 'Đại số, hàm số, hình học, xác suất – thống kê, đọc số liệu.'),
    'qt': ('Tư duy Định tính', 'Đọc hiểu, từ vựng – ngữ pháp, suy luận ngôn ngữ.'),
    'kh': ('Khoa học & Tiếng Anh', 'Lý – Hoá – Sinh – Sử – Địa hoặc lựa chọn Tiếng Anh.'),
}


def _pick_roadmap_template(data):
    """HSA chỉ có 1 template gốc — luôn dùng hsa_master làm nền."""
    return 'hsa_master'


def _hsa_section_scores(data):
    """Chấm mini-test theo hợp phần (0–2 mỗi phần), hạ nhẹ nếu user tự nhận yếu.
    Điểm THẤP = yếu hơn → ưu tiên luyện trước."""
    scores = {'ql': 0, 'qt': 0, 'kh': 0}
    for qid, correct in _HSA_DIAG_KEY.items():
        sec = qid.split('_')[1]            # dq_<sec>_<n>
        if str(data.get(qid, '')).strip().upper() == correct:
            scores[sec] += 1
    self_weak = (data.get('self_weak') or '').lower()
    if 'định lượng' in self_weak or 'toán' in self_weak:
        scores['ql'] = max(0, scores['ql'] - 1)
    if 'định tính' in self_weak or 'ngôn ngữ' in self_weak or 'văn' in self_weak:
        scores['qt'] = max(0, scores['qt'] - 1)
    if 'khoa học' in self_weak or 'tiếng anh' in self_weak:
        scores['kh'] = max(0, scores['kh'] - 1)
    return scores


def _generate_user_roadmap(uid, survey_id, data):
    """Dựng lộ trình HSA CÁ NHÂN HOÁ: hợp phần yếu lên trước, gắn mục tiêu điểm.
    Idempotent theo id 'u<uid>_generated'."""
    scores = _hsa_section_scores(data)
    base_order = ['ql', 'qt', 'kh']
    order = sorted(base_order, key=lambda s: (scores[s], base_order.index(s)))
    weakest = order[0]
    target = data.get('target_score') or '—'

    nodes = {
        'hsa_start': {'title': '1. Chẩn đoán năng lực',
                      'desc': f'Đã đánh giá năng lực đầu vào. Mục tiêu của bạn: {target} điểm.'},
    }
    lines = ['flowchart TD', '    hsa_start["1. Chẩn đoán năng lực"]']
    ids = ['hsa_start']
    for i, sec in enumerate(order, start=2):
        title, desc = _HSA_SECTIONS[sec]
        nid = f'hsa_{sec}'
        prio = ' ⚠ ƯU TIÊN' if sec == weakest else ''
        label = f'{i}. {title}{prio}'
        note = (f' (mini-test {scores[sec]}/2 — tập trung phần này)'
                if sec == weakest else f' (mini-test {scores[sec]}/2)')
        nodes[nid] = {'title': label, 'desc': desc + note}
        lines.append(f'    {nid}["{label}"]')
        ids.append(nid)
    n_mock, n_goal = len(order) + 2, len(order) + 3
    nodes['hsa_mock'] = {'title': f'{n_mock}. Luyện đề tổng (CBT)',
                         'desc': 'Thi thử đầy đủ 150 câu trên máy, chấm điểm và phân tích.'}
    nodes['hsa_goal'] = {'title': f'{n_goal}. Về đích ({target})',
                         'desc': 'Rà soát điểm yếu còn lại, chốt chiến lược làm bài.'}
    lines.append(f'    hsa_mock["{n_mock}. Luyện đề tổng (CBT)"]')
    lines.append(f'    hsa_goal["{n_goal}. Về đích ({target})"]')
    ids += ['hsa_mock', 'hsa_goal']
    for a, b in zip(ids, ids[1:]):
        lines.append(f'    {a} --> {b}')
    mermaid_def = '\n'.join(lines) + '\n'

    rid = f'u{uid}_generated'
    x('''INSERT INTO roadmaps
             (id, user_id, source, generated_from_survey_id,
              title, icon, color, nodes_json, edges_json, mermaid_def, updated_at)
         VALUES (%s, %s, 'generated', %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, now())
         ON CONFLICT (id) DO UPDATE SET
             generated_from_survey_id = EXCLUDED.generated_from_survey_id,
             title       = EXCLUDED.title,
             icon        = EXCLUDED.icon,
             color       = EXCLUDED.color,
             nodes_json  = EXCLUDED.nodes_json,
             edges_json  = EXCLUDED.edges_json,
             mermaid_def = EXCLUDED.mermaid_def,
             updated_at  = now()''',
      (rid, uid, survey_id, 'Lộ trình luyện thi HSA của bạn', '🎯', '#8B5CF6',
       json.dumps(nodes, ensure_ascii=False), json.dumps({}, ensure_ascii=False),
       mermaid_def))


class SurveyView(APIView):
    def post(self, request):
        data = request.data
        if not isinstance(data, dict):
            return Response({'error': 'Dữ liệu khảo sát không hợp lệ'}, status=400)
        uid = request.user.id
        with transaction.atomic():
            survey = q1(
                'INSERT INTO surveys (user_id, data_json, created_at) '
                'VALUES (%s,%s,%s) RETURNING id',
                (uid, json.dumps(data, ensure_ascii=False), local_now().isoformat()))
            x('UPDATE users SET questionnaire_completed=1 WHERE id=%s', (uid,))
            _generate_user_roadmap(uid, survey['id'], data)
        return Response({'ok': True})
