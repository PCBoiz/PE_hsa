# MIGRATION_NOTES.md — những gì cố ý thay đổi (và vì sao)

> Đối chiếu với ràng buộc "không tự ý đổi": mọi khác biệt so với bản Flask được
> liệt kê ở đây kèm lý do. Những gì không nêu = giữ nguyên 1:1.

## §Auth — JWT thay session cookie (bắt buộc)

- **Vì sao đổi**: frontend Next.js chạy ở domain khác backend. Session cookie
  Flask với `SESSION_COOKIE_SAMESITE='Lax'` không gửi kèm fetch cross-site →
  auth gãy hoàn toàn. Chọn JWT (djangorestframework-simplejwt).
- Access token 30 phút; **refresh token 8 giờ** = đúng `PERMANENT_SESSION_LIFETIME`
  cũ (UX "đăng nhập được 8 tiếng" giữ nguyên).
- `POST /auth/login`, `POST /auth/register` trả body y hệt cũ **cộng thêm** 2 field
  `access`, `refresh`.
- **Endpoint MỚI** `POST /auth/refresh` (bắt buộc phải có với JWT).
- `GET /auth/logout`: Flask clear session + redirect `/`; bản mới trả `{ok:true}`
  và blacklist refresh token nếu client gửi kèm — redirect do frontend tự làm.
- **CSRF**: Flask cũ đặt `WTF_CSRF_CHECK_DEFAULT=False` + `csrf.exempt` cho auth/oauth.
  Bản Django: API dùng JWT qua header `Authorization` → CSRF middleware của Django
  **không áp** lên các request này (CSRF chỉ áp cho auth dạng cookie). Không route
  nào cố tình giữ CSRF; nếu sau này chuyển refresh-token sang cookie thì phải bật lại
  CSRF cho riêng `/auth/refresh`.

## §OAuth — django-allauth thay flask-dance

- Luồng nghiệp vụ `_login_or_create` giữ nguyên 3 bước (match provider-id → link
  theo email → tạo mới) trong `accounts/oauth.py::LegacySocialAccountAdapter`.
- **Callback → JWT handoff**: sau callback, backend KHÔNG render trang mà redirect
  `{FRONTEND_URL}/auth/callback#access=...&refresh=...`. Dùng URL **fragment** thay
  query string vì fragment không bị ghi vào access log / không gửi trong Referer.
- Khác biệt nhỏ: Flask cũ Google → `/dashboard`, Facebook → `/`; bản mới trang
  `/auth/callback` của Next lưu token rồi luôn về `/dashboard` (thống nhất 1 đích —
  `/` landing với user đã đăng nhập cũng chỉ dẫn về dashboard).
- URL bắt đầu OAuth đổi: `/auth/google` (flask-dance) → `/accounts/google/login/`
  (allauth). Frontend cập nhật đúng 2 href ở trang login.

## §SQL — giữ raw SQL, không viết lại bằng ORM

Toàn bộ logic nghiệp vụ (XP, streak, achievement, upsert ON CONFLICT, quiz snapshot)
port **nguyên văn từng câu SQL** qua helper `common/db.py` (q/q1/x). Lý do: viết lại
bằng ORM là chỗ dễ lệch hành vi nhất (điểm, streak sai không lộ ngay). Models Django
vẫn được khai đủ 22 bảng (managed=False) để làm schema contract + dùng dần về sau.

## §Models — managed=False thay vì migrate --fake-initial

Prompt gợi ý `--fake-initial`; chọn `managed=False` cho TẤT CẢ bảng legacy vì an toàn
hơn tuyệt đối: Django không bao giờ sinh DDL cho các bảng này, kể cả khi ai đó lỡ tay
`migrate` sau khi đổi model. Kết quả tương đương (bảng không bị tạo lại).

## §Bảng MỚI thêm vào NeonDB dùng chung (chỉ THÊM, không sửa bảng cũ)

`django_migrations`, `django_session`, `django_content_type`, `django_site`,
`auth_permission`, `auth_group*`, `account_emailaddress*` (allauth),
`socialaccount_*` (allauth), `token_blacklist_*` (JWT blacklist).

⚠️ **Ràng buộc mới phát sinh**: `token_blacklist_outstandingtoken.user_id` FK →
`users.id` KHÔNG cascade. Muốn xóa user phải xóa outstanding token của user đó trước.
(Bản Flask không có tính năng xóa user nên không ảnh hưởng hành vi hiện tại.)

## §Rate limit — semantics per-endpoint được giữ có chủ đích

Flask-Limiter đếm **mỗi endpoint một quota riêng** (50/hour/IP/route). DRF throttle
mặc định đếm GỘP mọi endpoint — nếu port ngây thơ, một lần load dashboard (~20 API
call) sẽ tự đốt quota → tái diễn lớp bug 429 mà AUDIT-FIX 2026-07-07 từng vá.
→ `common/throttling.py` đưa tên view vào cache key để quota tính riêng từng endpoint.
Static/asset giờ do Next.js serve, không đi qua Django → bug "429 file tĩnh" không thể
tái diễn về mặt kiến trúc (đừng bao giờ thêm throttle vào tầng serve static của Next).
Lưu ý: throttle dùng Django cache (mặc định LocMemCache per-process — tương đương
`memory://` của Flask-Limiter cũ); production nhiều worker thì trỏ CACHES sang Redis.

## §Neon cold-start — chọn phương án (b)

`CONN_MAX_AGE=240` + `conn_health_checks=True` + TCP keepalive (y hệt tham số
db/connection.py cũ) thay cho thread `start_keepalive()`. Lý do: thread nền trong
process web không tin được ở môi trường serverless/multi-worker; connection tái sử
dụng 240s đã loại phần lớn chi phí reconnect. Bổ sung endpoint `GET /health`
(SELECT 1) để cron ngoài (GitHub Actions schedule / cron của platform) ping giữ
compute ấm nếu muốn — tương đương keepalive 240s cũ.

## §Error contract

- 401 chưa đăng nhập: `{"error": "Chưa đăng nhập"}` — khớp guard cũ.
- 403: `{"error": "Không có quyền truy cập"}` — khớp guard cũ.
- 400/404/429/500: format `{"error": {"status","message","detail"}, "request_id"}`
  y hệt `_error_response` của app.py.
- Khác biệt nhỏ: datetime trong JSON giờ là ISO-8601 (DRF) thay vì RFC-1123 (Flask
  jsonify). `new Date(...)` của JS parse được cả hai — không ảnh hưởng UI.

## §Vá bảo mật có chủ đích (1 chỗ duy nhất)

`GET /api/user` bản Flask `SELECT *` trả về **cả cột password (hash)** cho client.
Bản Django loại field `password` khỏi response. Đây là sửa lỗi lộ dữ liệu, không
phải đổi tính năng; frontend không dùng field này.

## §Logging

`setup_logging`/`init_request_id` bản Flask đang bị comment TẮT. Theo quyết định
chủ dự án (2026-07-14): bản Django BẬT — request-id middleware + header
`X-Request-ID` + log 5xx kèm stack trace + JSON formatter tương đương.

## §Django admin site

Không cài `django.contrib.admin` — trang quản trị là `/admin` của frontend (port từ
admin.html) + API `/api/admin/*` (app `courseadmin`), đúng như bản Flask.

## §Seed / init_db

`init_db()` Flask là lịch sử migration tích lũy chạy mỗi startup — KHÔNG port nguyên.
DB thật đã ở trạng thái cuối. Phần seed idempotent (courses/roadmaps/missions/
achievements khi bảng rỗng + upsert lessons metadata) sẽ nằm trong
`manage.py seed_data` (làm cùng Giai đoạn 4 với content pipeline) — chỉ cần khi
dựng DB mới từ đầu, không chạy tự động.

## §Điểm còn mở (làm tay khi deploy)

- OAuth credentials thật (Google/Facebook) phải khai vào `.env` backend + cấu hình
  redirect URI mới (`https://<backend>/accounts/google/login/callback/`).
- `FRONTEND_URL`, `ALLOWED_HOSTS`, `ALLOWED_ORIGINS`, `SECRET_KEY` production.
- Cron ping `/health` (nếu muốn giữ Neon ấm 24/7).
- CACHES → Redis khi chạy nhiều worker (throttle chính xác).
