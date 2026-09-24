# Vận hành pe_hsa — deploy, lược đồ, cổng kiểm, lùi bản

Sổ tay ngắn cho người đẩy mã lên production. Chi tiết dựng dịch vụ lần đầu: `DEPLOY.md`.
Mục H8 của kế hoạch (khôi phục, cảnh báo, danh sách bật khi thử nghiệm) viết tiếp vào tệp này.

## 1. Deploy

- Đẩy `master` là deploy: **Render** (backend, `render.yaml`) và **Vercel** (frontend) tự dựng.
- Render chạy `buildCommand`: `pip install` → `collectstatic` → **`bootstrap_schema`** → `migrate`,
  nối bằng `&&` — một bước hỏng là build đỏ, bản đang chạy vẫn phục vụ. Rồi `startCommand` (gunicorn).
- Vercel thường xong TRƯỚC Render: có một lúc frontend mới gọi backend cũ. Vì lược đồ chỉ cộng
  (không xoá/đổi tên cột), backend cũ chạy được trên lược đồ mới; frontend mới phải chịu được API cũ.
- **Cấu hình một nguồn**: mọi thông số gunicorn ở `startCommand`; mọi biến môi trường backend đọc
  đều có tên trong `render.yaml` (bí mật và biến có mặc định để `sync: false` — Blueprint không
  ghi đè giá trị trên dashboard). Thêm `os.environ.get('X')` mới → khai `X` ở `render.yaml` hoặc
  thêm vào danh sách "chỉ dev" kèm lý do; guard `backend/common/tests_cau_hinh.py` đỏ nếu quên.
  Không còn `backend/Procfile` và `backend/gunicorn.conf.py` (gunicorn tự nạp tệp ấy — nguồn thứ hai).

## 2. Lược đồ SQL — `bootstrap_schema`

`backend/sql/*.sql` là nguồn DDL duy nhất của các bảng `managed=False`. Từ 24/09/2026 (H3) lệnh
chia tệp thành MỤC theo dòng tiêu đề và ghi sổ `luoc_do_da_chay` (mục, checksum câu lệnh, lúc chạy):
mỗi lượt chỉ chạy mục mới / đổi câu lệnh **cùng mọi mục đứng sau nó**, mỗi mục một giao dịch
(`lock_timeout` 5 s, bế tắc / hết giờ chờ khoá thì cuộn lại mục và thử lại). Luật và lý do:
`backend/common/luoc_do_sql.py`.

**Thêm một mục** — ở CUỐI `legacy_schema.sql`, tiêu đề `-- ── §NN · TIÊU ĐỀ (ngày) ──`, số lớn
hơn mục cuối. Mọi câu phải chạy lại được (`IF NOT EXISTS`, `DROP … IF EXISTS` rồi `ADD`); không
`DO $$` (bộ tách câu cắt ở mọi `;`), không `CREATE INDEX CONCURRENTLY` (không chạy trong giao dịch).
Thêm dòng kiểm cho mục ở `kiem_luoc_do.py`.

**Trước khi đẩy** (trên nhánh Neon `dev`, `cd backend`):

```bash
python manage.py bootstrap_schema --dien-tap   # CSDL mới toanh trong schema tạm: dựng, chạy lần 2, đối chiếu, cuộn lại
python manage.py bootstrap_schema              # lượt 1: chạy mục mới, ghi sổ
python manage.py bootstrap_schema              # lượt 2: phải in "0/N mục chạy"
python manage.py kiem_luoc_do                  # mọi dòng ✓
```

| Lệnh | Làm gì |
|---|---|
| `bootstrap_schema` | chạy mục chờ, ghi sổ (đúng lệnh Render chạy) |
| `bootstrap_schema --kiem` | liệt kê mục sẽ chạy ở lượt tới, không chạy, không ghi |
| `bootstrap_schema --kiem --ma-loi` | như trên, thoát 1 nếu có mục chờ (cổng pre-push dùng) |
| `bootstrap_schema --tat-ca` | chạy lại MỌI mục như trước H3 rồi ghi sổ |
| `bootstrap_schema --dien-tap` | diễn tập CSDL mới toanh (schema tạm, hai lượt, cuộn lại) |
| `kiem_luoc_do [--ma-loi]` | hỏi thẳng `pg_catalog`: mục nào thật sự có trên CSDL này |

**Sổ và thực tế lệch nhau** (sổ ghi đã chạy mà `kiem_luoc_do` báo ✗ — có người ALTER tay, khôi
phục một phần): `bootstrap_schema --tat-ca`.

**Build Render đỏ ở `bootstrap_schema`**: log có dòng `[legacy_schema.sql §NN · câu i/n …] LỖI ở: …`.
Mục ấy đã cuộn lại trọn, không ghi sổ; các mục trước nó đã chạy và ghi sổ; bản cũ vẫn phục vụ. Sửa,
chạy lại trên `dev` như trên, đẩy lại — lượt sau chạy tiếp từ mục hỏng tới hết. Lưu ý: trong khoảng
giữa, CSDL có thể THIẾU đồ của một mục SAU mục hỏng mà một mục trước đã gỡ (ví dụ thật: §36 gỡ khoá
ngoại của §55 bằng CASCADE) — `kiem_luoc_do` chỉ ra; sổ không ghi mục ấy nên lượt sau dựng lại.

## 3. Cổng kiểm trước khi đẩy — `.githooks/pre-push`

GitHub Actions đang khoá (A0), nên cổng chạy trên máy người đẩy. Bật một lần cho mỗi bản sao repo:

```bash
git config core.hooksPath .githooks
```

Chạy: ruff · `manage.py check` · compileall · pytest guard không CSDL (`tests_cau_hinh`,
`tests_luoc_do_muc`) · `bootstrap_schema --kiem --ma-loi` (khi có `backend/.env`; không nối được
CSDL thì bỏ qua) · tsc · eslint `--max-warnings 0` · `node --check` các tệp JS thuần trong `public/static` (11 tệp, đếm 24/09) · mọi
`e2e/unit/*.test.mjs` · `ban_do --kiem`. Hai nhóm backend | frontend chạy song song; đo 24/09 trên
máy dev: **51 s** khi đạt. Hỏng thì in bảng ✓/✗ và 25 dòng cuối của bước hỏng, chặn đẩy.

- Bỏ qua một lần có chủ ý: `git push --no-verify`.
- Chạy tay: `bash .githooks/pre-push < /dev/null`.
- `PE_PYTHON=<python>` nếu venv không ở `backend/.venv` (worktree phụ tự tìm venv của worktree chính).
- `PE_PUSH_PYTEST=1`: thêm pytest cho mô-đun backend có tệp đổi so với `origin/master` — chạm CSDL
  dev và có thể lâu; bộ đủ (~54 phút) vẫn chạy tay trước mỗi mốc giao (RULES §4).

## 4. Lùi bản (rollback)

- **Backend (Render)**: Dashboard → `pe-hsa-backend` → Events/Deploys → deploy cũ → *Rollback*.
  Render DÙNG LẠI bản dựng cũ, KHÔNG chạy lại `buildCommand` (nên không chạy `bootstrap_schema`),
  và **tự TẮT auto-deploy** — nhớ bật lại, nếu không lần đẩy `master` sau không lên
  (render.com/docs/rollbacks).
- **Frontend (Vercel)**: Deployments → bản cũ → *Instant Rollback* / *Promote to Production*.
- **Lược đồ: KHÔNG lùi.** DDL chỉ cộng, mã cũ chạy được trên lược đồ mới. Đừng xoá tay cột/bảng mới
  "cho sạch" (xoá một dòng sổ thì vô hại: mục ấy và mọi mục sau chạy lại ở lượt tới). Một mục làm
  hỏng DỮ LIỆU thì khôi phục nhánh Neon về một thời điểm trước đó
  (trong hạn lưu lịch sử của gói Neon) — việc của chủ dự án, xem `docs/VIEC_CUA_ANH.md`.
- Lùi bằng mã: `git revert <commit>` trên `master` rồi đẩy (qua cổng pre-push như thường).
