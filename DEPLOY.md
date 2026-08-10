# Deploy — ProgrammingEdu × TopHSA (phương án A)

**Kiến trúc:** Frontend Next.js → **Vercel** · Backend Django → **Render** (region `ohio`) · DB → **NeonDB** (giữ nguyên, us-east-2).

```
Browser ──► Vercel (Next.js, static)
   │  pe-bridge.js rewrite /api/* + /auth/*  →  NEXT_PUBLIC_API_URL
   └──────────────────────────────► Render (Django + gunicorn) ──► NeonDB
```

> Backend **cố ý KHÔNG lên Vercel serverless**: có connection-pool + luồng keep-warm + rate-limit in-memory → cần tiến trình chạy dài.

---

## Thứ tự (tránh chicken-egg URL)
1. Deploy **Backend/Render** trước (tạm chưa biết URL Vercel) → lấy `https://pe-hsa-backend.onrender.com`.
2. Deploy **Frontend/Vercel** với `NEXT_PUBLIC_API_URL` = URL backend → lấy `https://<app>.vercel.app`.
3. **Cập nhật lại** env backend (`FRONTEND_URL`, `ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`) = URL Vercel → redeploy backend.
4. Cập nhật **OAuth redirect URI** (Google/Facebook) nếu dùng đăng nhập MXH.

---

## Phần 1 — Backend trên Render

Repo đã có sẵn **`render.yaml`** (Blueprint) — không phải cấu hình tay từng ô.

1. [dashboard.render.com](https://dashboard.render.com) → **New → Blueprint** → chọn repo **PCBoiz/PE_hsa** → Render đọc `render.yaml`.
2. Render hỏi các biến `sync:false` (bí mật) — nhập:

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `SECRET_KEY` | chuỗi ngẫu nhiên ≥32 ký tự | `python -c "import secrets;print(secrets.token_hex(32))"` |
| `DATABASE_URL` | `postgresql://…-pooler…neon.tech/neondb?sslmode=require` | dùng endpoint **-pooler** của Neon |
| `FRONTEND_URL` | tạm `https://example.com` | **sửa lại ở bước 3** |
| `ALLOWED_ORIGINS` | tạm `https://example.com` | **sửa lại ở bước 3** |
| `CSRF_TRUSTED_ORIGINS` | tạm để trống | **sửa lại ở bước 3** |
| `DEEPSEEK_API_KEY` | key DeepSeek | bỏ trống nếu chưa cần chatbot |
| `GOOGLE_CLIENT_ID/SECRET` | OAuth Google | bỏ trống nếu chưa dùng |
| `FACEBOOK_CLIENT_ID/SECRET` | OAuth Facebook | bỏ trống nếu chưa dùng |

3. **Apply** → Render tự: `pip install` → `collectstatic` → `migrate` → chạy `gunicorn`.
   `ALLOWED_HOSTS` tự thêm domain `.onrender.com` (qua `RENDER_EXTERNAL_HOSTNAME`).
4. Xong → kiểm `https://pe-hsa-backend.onrender.com/health` trả `{"status":"ok"}`.

**Biến không bí mật đã set sẵn trong `render.yaml`:** `DJANGO_ENV=production`, `DJANGO_DEBUG=0`, `PYTHON_VERSION=3.12.7`, `WEB_CONCURRENCY=2`, `ENABLE_KEEPALIVE=1`, `DB_POOL_MIN=2`, `DB_POOL_MAX=14`.

---

## Phần 2 — Frontend trên Vercel

1. [vercel.com/new](https://vercel.com/new) → import **PCBoiz/PE_hsa**.
2. **Root Directory = `frontend`** ⚠️ (monorepo — bắt buộc trỏ đúng). Framework tự nhận **Next.js**.
3. **Environment Variables** (cả Production + Preview):

| Biến | Giá trị |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://pe-hsa-backend.onrender.com` (URL backend ở Phần 1) |

4. **Deploy** → lấy `https://<app>.vercel.app`.

> Không cần `vercel.json`. `public/static/*` (JS/CSS legacy) được serve tĩnh tự động.

---

## Phần 3 — Nối 2 đầu (bắt buộc)

Về **Render → service → Environment**, sửa 3 biến cho khớp URL Vercel rồi **Save (auto-redeploy)**:

```
FRONTEND_URL          = https://<app>.vercel.app
ALLOWED_ORIGINS       = https://<app>.vercel.app
CSRF_TRUSTED_ORIGINS  = https://<app>.vercel.app,https://pe-hsa-backend.onrender.com
```
(Muốn cho cả URL preview `*.vercel.app` gọi API thì thêm từng domain preview vào `ALLOWED_ORIGINS`.)

**OAuth (nếu dùng):** thêm redirect URI ở Google/Facebook console:
`https://pe-hsa-backend.onrender.com/accounts/google/login/callback/` (và facebook tương tự).

---

## Kiểm thử sau deploy
- [ ] `GET https://…onrender.com/health` → 200 `{"status":"ok"}`
- [ ] Mở `https://<app>.vercel.app/login` → đăng nhập `admin@pe-hsa.vn` → vào Dashboard (không 500, không lỗi CORS ở Console)
- [ ] Khóa học hiện 3 khóa · Lộ trình render · Vào 1 bài chạy 5 bước
- [ ] DevTools → Network: request `/auth/login` đi tới **onrender.com** (không phải localhost)

## Gotchas
- **Render free ngủ sau ~15' idle** → request đầu chờ cold-start ~30-50s. Muốn luôn sẵn sàng: nâng plan hoặc ping ngoài (UptimeRobot gọi `/health` mỗi ~10'). *Keep-warm nội bộ chỉ giữ **Neon** ấm, không chống Render ngủ.*
- **Neon free scale-to-zero**: đã có retry + keep-warm (`ENABLE_KEEPALIVE=1`) → tự đánh thức.
- **Pool vs Neon**: `workers × DB_POOL_MAX` phải ≤ ~56. Tăng worker thì giảm `DB_POOL_MAX` tương ứng.
- **Region**: giữ Render `ohio` cùng vùng Neon `us-east-2` — đổi vùng làm chậm mọi query.
- **`.env` không commit** (đã gitignore) → nhập env thủ công ở cả Render lẫn Vercel.
- Ràng buộc dự án: chỉ deploy từ **PCBoiz/PE_hsa**, branch `master`.
