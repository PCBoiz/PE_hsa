"""Test cơ bản app accounts (auth/user/follow — domain chưa từng có test ở bản Flask)."""
import pytest

from accounts.hashers import check_werkzeug_password, make_werkzeug_password
from common.db import q1, x

pytestmark = pytest.mark.django_db


def test_werkzeug_hasher_roundtrip():
    """Hasher tương thích werkzeug: hash mới verify được, sai mật khẩu fail."""
    h = make_werkzeug_password('SecretPass123')
    assert h.startswith('scrypt:')
    assert check_werkzeug_password(h, 'SecretPass123') is True
    assert check_werkzeug_password(h, 'WrongPass') is False


def test_register_closed_to_anonymous(api, db):
    """Người lạ KHÔNG tự mở được tài khoản. Đây là phép kiểm giữ chính sách.

    Đổi ngày 27/08/2026: trung tâm cấp tài khoản, học viên không tự đăng ký.
    Trang /register đã xoá và nhánh OAuth cũng đã chặn — nhưng cả hai lần vá đó
    thành vô nghĩa nếu endpoint này hở, vì một lệnh curl thẳng vào backend là có
    tài khoản, kèm quyền gọi /api/chat (mỗi lượt chat là tiền thật).

    Phép kiểm này TRƯỚC ĐÂY khẳng định điều ngược lại — nó đòi 200 cho một lời
    gọi ẩn danh. Giữ nguyên thì nó thành cái chốt giữ lại đúng lỗ vừa bịt.
    """
    res = api.post('/auth/register', {
        'name': 'Reg Tester', 'email': 'dj_reg_test@example.com', 'password': 'SecretPass123',
    }, format='json')
    assert res.status_code in (401, 403), 'tự đăng ký đã mở lại — xem RegisterView'


def test_admin_register_then_login_happy_path(admin_api, db):
    email = 'dj_reg_test@example.com'
    res = admin_api.post('/auth/register', {
        'name': 'Reg Tester', 'email': email, 'password': 'SecretPass123',
    }, format='json')
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert 'access' in data and 'refresh' in data  # JWT thêm vào (MIGRATION_NOTES §Auth)

    # Đăng nhập phải dùng một client SẠCH: `admin_api` đang mang danh tính quản
    # trị viên do force_authenticate, nên gọi /auth/login trên chính nó sẽ đo
    # nhầm — vẫn 200 kể cả khi mật khẩu sai.
    from rest_framework.test import APIClient
    khach = APIClient()
    res2 = khach.post('/auth/login', {'email': email, 'password': 'SecretPass123'}, format='json')
    assert res2.status_code == 200
    assert res2.json()['name'] == 'Reg Tester'

    res3 = khach.post('/auth/login', {'email': email, 'password': 'WrongPass99'}, format='json')
    assert res3.status_code == 401


def test_register_validation_errors(admin_api, db):
    res = admin_api.post('/auth/register',
                         {'name': '', 'email': 'bad', 'password': '1'}, format='json')
    assert res.status_code == 400
    errors = res.json()['errors']
    assert 'name' in errors and 'email' in errors and 'password' in errors


def test_login_empty_fields(api, db):
    res = api.post('/auth/login', {'email': '', 'password': ''}, format='json')
    assert res.status_code == 400
    assert 'errors' in res.json()


def test_get_user_requires_auth(api, db):
    res = api.get('/api/user')
    assert res.status_code == 401
    assert res.json() == {'error': 'Chưa đăng nhập'}  # body y hệt guard Flask


def test_get_user_no_password_leak(auth_api):
    data = auth_api.get('/api/user').json()
    assert 'password' not in data  # vá có chủ đích (MIGRATION_NOTES §Vá bảo mật)
    assert data['is_new_user'] is True


def test_follow_self_rejected(auth_api, temp_user):
    res = auth_api.post(f'/api/users/{temp_user}/follow')
    assert res.status_code == 400


def test_follow_unfollow_flow(auth_api):
    other = q1("INSERT INTO users (name, email, password) VALUES (%s,%s,%s) RETURNING id",
               ('Follow Target', 'dj_follow_target@example.com', 'x'))['id']
    res = auth_api.post(f'/api/users/{other}/follow')
    assert res.status_code == 200 and res.json()['following'] is True
    # idempotent
    assert auth_api.post(f'/api/users/{other}/follow').status_code == 200
    res2 = auth_api.delete(f'/api/users/{other}/follow')
    assert res2.json()['following'] is False


def test_survey_generates_roadmap(auth_api, temp_user):
    res = auth_api.post('/api/survey', {'career_target': 'Backend Developer'}, format='json')
    assert res.status_code == 200
    user = q1('SELECT questionnaire_completed FROM users WHERE id=%s', (temp_user,))
    assert user['questionnaire_completed'] == 1
    rm = q1('SELECT id, source FROM roadmaps WHERE id=%s', (f'u{temp_user}_generated',))
    assert rm is not None and rm['source'] == 'generated'


# ── memory-plan T4.2: đổi email trùng phải trả 400 (không phải 500 IntegrityError) ──
def test_update_profile_duplicate_email_returns_400(auth_api, temp_user):
    """users.email có UNIQUE constraint. Đổi email sang email người khác phải báo
    400 'Email đã được sử dụng' như /auth/register — hiện tại rơi vào 500 vì
    IntegrityError không được bắt trước."""
    taken = 'dj_taken_email@example.com'
    q1("INSERT INTO users (name, email, password) VALUES (%s,%s,%s) RETURNING id",
       ('Email Owner', taken, 'x'))
    res = auth_api.put('/api/user', {'name': 'Me', 'email': taken, 'phone': ''}, format='json')
    assert res.status_code == 400
    assert 'email' in res.json().get('errors', {})


def test_update_profile_same_email_ok(auth_api, temp_user):
    """Giữ nguyên email của chính mình (không đổi) phải OK — không tự coi là trùng."""
    x("UPDATE users SET email=%s WHERE id=%s", ('dj_self_email@example.com', temp_user))
    res = auth_api.put('/api/user',
                       {'name': 'Me', 'email': 'dj_self_email@example.com', 'phone': ''},
                       format='json')
    assert res.status_code == 200


# ── Hàng rào `must_change_password` (31/08/2026) ────────────────────────────

@pytest.mark.django_db
def test_mat_khau_tam_chi_di_duoc_bon_duong(db, api):
    """Trước 31/08/2026 cờ này chỉ được ép ở màn hình đăng nhập.

    Backend không view nào đọc nó: đăng nhập cấp JWT đầy đủ, gõ thẳng URL khác
    là dùng được cả ứng dụng mà không bao giờ đổi mật khẩu tạm — mật khẩu mà
    trợ giảng vừa đọc to cho học viên nghe.
    """
    from rest_framework_simplejwt.tokens import RefreshToken

    from accounts.authentication import invalidate_user_cache
    from accounts.models import User
    from common.db import q1

    row = q1("INSERT INTO users (name, email, password, streak, must_change_password) "
             "VALUES ('MK Tam','mk_tam_tmp@example.com','x',0,TRUE) RETURNING id")
    u = User.objects.get(id=row['id'])
    invalidate_user_cache(u.id)
    # TOKEN THẬT, không `force_authenticate`: hàng rào nằm trong lớp XÁC THỰC,
    # mà `force_authenticate` gán thẳng `request.user` và bỏ qua lớp đó — phép
    # kiểm dùng nó sẽ luôn xanh và không kiểm được gì. (Cùng cái bẫy đã gặp với
    # fixture `admin_api` hôm 30/08: đăng nhập sai mật khẩu vẫn ra 200.)
    def dat_token(user):
        api.credentials(HTTP_AUTHORIZATION='Bearer %s'
                        % RefreshToken.for_user(user).access_token)

    dat_token(u)

    # Đường bị chặn — 403 chứ KHÔNG 401 (401 làm lớp refresh của frontend quay vòng)
    r = api.get('/api/stats')
    assert r.status_code == 403, r.status_code
    assert 'mật khẩu tạm' in str(r.data), 'phải NÓI RA lý do, không phải 403 câm: %s' % r.data
    assert r.data.get('mustChangePassword') is True, 'và phải máy đọc được để tự điều hướng'

    # Bốn đường được phép
    assert api.get('/api/user').status_code == 200
    # Tên trường là `current`/`new` — KHÔNG phải `current_password`/`new_password`.
    # Bản đầu của phép kiểm này gõ sai tên, nên 400 nhận được là "thiếu trường",
    # không phải "sai mật khẩu hiện tại": nó vẫn xanh kể cả khi PasswordView
    # hỏng hẳn. Một phép kiểm xanh vì lý do sai thì tệ hơn không có.
    r2 = api.put('/api/user/password', {'current': 'sai-be-be', 'new': 'MatKhauMoi123'},
                 format='json')
    assert r2.status_code == 401, r2.data
    assert 'hiện tại' in str(r2.data), (
        'phải tới được VIEW và bị từ chối vì sai mật khẩu, chứ không phải bị hàng '
        'rào chặn: %s' % r2.data)

    # `/api/users/...` (số NHIỀU) bắt đầu bằng chuỗi `/api/user` — bản đầu so
    # bằng `startswith` nên nó LỌT. Tài khoản còn mật khẩu tạm vẫn theo dõi
    # người khác được. Nhẹ về nghiệp vụ, nhưng nó chứng minh tiền tố không giữ
    # nổi lời hứa "đúng bốn thứ": mọi URL `/api/user*` thêm sau này sẽ tự động
    # lọt mà không ai nhận ra.
    nguoi_khac = q1("INSERT INTO users (name, email, password, streak) "
                    "VALUES ('MK Tam Khac','mk_tam_khac_tmp@example.com','x',0) RETURNING id")
    r3 = api.post('/api/users/%d/follow' % nguoi_khac['id'], {}, format='json')
    assert r3.status_code == 403, 'đường số NHIỀU phải bị chặn: %s' % r3.status_code
    # (`/api/user/` có dấu gạch cuối trả 404 từ bộ định tuyến Django, chứ không
    #  phải từ hàng rào — `rstrip('/')` trong danh sách cho phép là phòng thủ
    #  cho một trường hợp không tới được. Không khẳng định gì ở đây: khẳng định
    #  về routing của Django không phải việc của phép kiểm này.)

    # Gỡ cờ thì đi lại được ngay, KHÔNG phải đợi 60 giây bộ đệm
    q1('UPDATE users SET must_change_password=FALSE WHERE id=%s RETURNING id', (u.id,))
    invalidate_user_cache(u.id)
    dat_token(User.objects.get(id=u.id))
    assert api.get('/api/stats').status_code == 200


# ── T67 · Đổi mật khẩu CẮT phiên đang mở (31/08/2026) ───────────────────────

@pytest.mark.django_db
def test_dat_lai_mat_khau_cat_phien_dang_mo(db, api):
    """Trợ giảng bấm "Đặt lại mật khẩu" vì nghi tài khoản bị người khác dùng.

    Trước §39, token cũ VẪN SỐNG: người đang chiếm tài khoản thao tác bình
    thường thêm 30 phút — đúng lúc trợ giảng tưởng mình vừa đuổi được họ ra.
    Danh sách đen của SimpleJWT không cứu được, vì nó chỉ chặn REFRESH token
    còn ACCESS token kiểm bằng chữ ký chứ không tra CSDL.
    """
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    from accounts.authentication import invalidate_user_cache
    from accounts.models import User
    from common.clock import local_now
    from common.db import q1
    from common.permissions import ROLE_ADMIN
    from teaching.views import AdminResetPasswordView

    hv = q1("INSERT INTO users (name, email, password, streak) "
            "VALUES ('Bi Chiem','bi_chiem_tmp@example.com','x',0) RETURNING id")
    ad = q1("INSERT INTO users (name, email, password, role, streak) "
            "VALUES ('Ad Reset','ad_reset_tmp@example.com','x',%s,0) RETURNING id",
            (ROLE_ADMIN,))
    u = User.objects.get(id=hv['id'])
    invalidate_user_cache(u.id)

    # "Người đang chiếm tài khoản" cầm một access token hợp lệ.
    tok = str(RefreshToken.for_user(u).access_token)
    api.credentials(HTTP_AUTHORIZATION='Bearer %s' % tok)
    assert api.get('/api/user').status_code == 200, 'trước khi reset thì đi được'

    # Trợ giảng đặt lại mật khẩu.
    from rest_framework.test import APIRequestFactory, force_authenticate
    req = APIRequestFactory().post('/x', {}, format='json')
    force_authenticate(req, user=User.objects.get(id=ad['id']))
    kq = AdminResetPasswordView.as_view()(req, user_id=u.id)
    assert kq.status_code == 200, kq.data
    assert q1('SELECT tokens_valid_from FROM users WHERE id=%s',
              (u.id,))['tokens_valid_from'] is not None, 'phải đặt mốc thu hồi'

    # CÙNG token đó, NGAY sau đó → phải bị từ chối.
    #
    # KHÔNG gọi `invalidate_user_cache` ở đây. Bản trước có gọi, và vì thế phép
    # kiểm này KHÔNG kiểm gì cả: `CachedJWTAuthentication` giữ đối tượng user 60
    # giây, nên thứ quyết định 401 hay 200 là việc `AdminResetPasswordView` có
    # tự xoá bộ đệm hay không — mà bộ kiểm lại tự tay xoá hộ nó.
    #
    # Đo 01/09/2026: xoá hẳn dòng `invalidate_user_cache(user_id)` khỏi
    # `teaching/views.py` rồi chạy lại → **15 passed**. Tức phép kiểm mang tên
    # "cắt phiên đang mở" vẫn xanh trong khi phiên KHÔNG bị cắt, và thứ nó canh
    # là một hàng rào an ninh: trợ giảng bấm đặt lại mật khẩu vì nghi tài khoản
    # bị chiếm, mà người đang chiếm vẫn thao tác bình thường thêm một phút.
    #
    # Cùng loại lỗi với RULES §"test phải đi đúng đường thật": đỏ-trước chưa đủ,
    # phép kiểm còn phải đi qua ĐÚNG đoạn mã mà nó nói là đang canh.
    r = api.get('/api/user')
    assert r.status_code == 401, 'token cũ phải chết ngay, không đợi hết hạn: %s' % r.status_code

    # Token cấp SAU mốc thì đi được (không khoá cứng tài khoản).
    moi = APIClient()
    moi.credentials(HTTP_AUTHORIZATION='Bearer %s'
                    % RefreshToken.for_user(User.objects.get(id=u.id)).access_token)
    r2 = moi.get('/api/user')
    # Cờ must_change_password nay là TRUE nên `/api/user` vẫn nằm trong danh
    # sách cho phép → 200. Điều cần khẳng định là KHÔNG phải 401.
    assert r2.status_code == 200, 'token mới phải đi được: %s %s' % (r2.status_code, r2.data)
    assert local_now() is not None


@pytest.mark.django_db
def test_moc_thu_hoi_so_bang_EPOCH_chu_khong_lech_7_tieng(db):
    """`iat` của token là giây UTC; `tokens_valid_from` là naive giờ VIỆT NAM.

    So thẳng hai thứ đó lệch đúng 7 tiếng — chính cái bẫy `common/clock.py`
    được viết ra để dập. Lệch theo hướng nào cũng hỏng: hoặc token mới bị giết
    oan, hoặc token cũ sống thêm 7 tiếng sau khi đã thu hồi.
    """
    from datetime import timedelta

    from rest_framework_simplejwt.tokens import RefreshToken

    from accounts.authentication import CachedJWTAuthentication
    from accounts.models import User
    from common.clock import local_now
    from common.db import q1

    row = q1("INSERT INTO users (name, email, password, streak) "
             "VALUES ('Moc Epoch','moc_epoch_tmp@example.com','x',0) RETURNING id")
    u = User.objects.get(id=row['id'])
    tok = RefreshToken.for_user(u).access_token

    # Mốc đặt 1 phút TRƯỚC lúc cấp token → token còn hiệu lực.
    u.tokens_valid_from = local_now() - timedelta(minutes=1)
    assert CachedJWTAuthentication._da_thu_hoi(u, tok) is False, (
        'lệch 7 tiếng sẽ làm câu này thành True — token mới bị giết oan')

    # Mốc đặt 1 phút SAU → token bị thu hồi.
    u.tokens_valid_from = local_now() + timedelta(minutes=1)
    assert CachedJWTAuthentication._da_thu_hoi(u, tok) is True, (
        'lệch 7 tiếng sẽ làm câu này thành False — token cũ sống thêm 7 tiếng')

    # Chưa từng thu hồi thì không đụng tới ai.
    u.tokens_valid_from = None
    assert CachedJWTAuthentication._da_thu_hoi(u, tok) is False
