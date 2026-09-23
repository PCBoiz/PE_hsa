# Kế hoạch đợt thử nghiệm TopHSA — 24/09/2026

Bản SỐNG: mọi tiến độ ghi vào tệp này (tick + commit + số đo), song song với `PROGRESS.md`.
Nguồn: góp ý của TopHSA sau khi dùng thử + ghi chú họp + 4 lượt dò mã (24/09) + các quyết định
anh Sơn chốt cùng ngày. Repo công khai — tệp này KHÔNG ghi giá, hợp đồng hay dữ liệu khách.

## Cách tiếp tục nếu bị ngắt

1. Tìm mục `[~]` đầu tiên trong bảng dưới (không có thì `[ ]` đầu tiên).
2. `git status` + `git log -5` — đối chiếu với dòng ghi của mục ấy.
3. Bật lại máy dev:
   - Django: `$env:EMAIL_CHE_DO_THU='1'; $env:EMAIL_THU_MUC_THU='D:\pe_hsa\.thu_email';
     $env:FRONTEND_URL='http://localhost:3100'` rồi `backend/.venv/Scripts/python.exe manage.py
     runserver 9000 --noreload` (bật lại SAU MỖI lần sửa backend).
   - Next: dừng máy chủ → `npx next build` → `npx next start -p 3100`.
4. Chạy lại test của mục dở TRƯỚC khi viết tiếp.

**Luật ghi**: xong một mục → `[x]` + hash commit + một dòng số đo ngay trên dòng đó; đang dở →
`[~]` + dừng ở tệp/bước nào. Mỗi luật mới: pytest ĐỎ TRƯỚC + đột biến (kịch bản phải đòi nền xanh
và MÃ THOÁT 1 — test không tồn tại cũng trả mã ≠ 0, bài học 24/09).

## Bảng theo dõi

| ID | Việc | Trạng thái |
|---|---|---|
| K0 | Chép kế hoạch vào repo (tệp này) | [x] `63554b0` |
| B0 | Chốt lịch học §53: e2e `lich-hoc` 2 khổ, đo giao diện + axe, soi ảnh, commit | [x] `ad3b299` — e2e 8/8 có ghi, đột biến 18/18 đỏ thật, do_giao_dien 70 lượt = 0, axe 102 = 0 |
| H1 | Tách CSDL: anh tạo nhánh Neon `dev`/`ci`; hàng rào chặn test/dev chạy vào production | [~] `b1ed6bc` — mã xong (6/6, pytest thoát 3 khi giả lập production); CHỜ anh thêm `PE_DB_HOST_PRODUCTION` vào .env (VIEC_CUA_ANH N2) |
| 1.1a | Ghi nhớ đăng nhập 30 ngày + trình duyệt lưu mật khẩu | [x] `6502a1a` + `ad3b299` — backend 9/9, 5 đột biến đỏ, guard cookie 9/9, e2e cookie thật 4/4 |
| 1.1b | Đường đi theo vai + khu Giáo trình (`/admin` → `/giao-trinh`) + "Môn học" chỉ-xem cho nhân sự | [x] `ad3b299` — `TRANG_DAU` + guard đối chiếu cổng thật (đột biến đỏ); e2e vai/khung 64/64. "Môn học" chỉ-xem đi cùng 1.3 |
| 1.1c | Trang gốc = cổng đăng nhập TopHSA, bỏ "ProgrammingEdu ×" | [x] `ad3b299` — `/` 307 → khu của vai / `/login`; trang quảng cáo + `landing.inline.js` gỡ |
| 1.1d | Màn học viên: ẩn bảng xếp hạng, bỏ popup giữ chuỗi, bỏ đồ thừa sản phẩm cũ | [~] `ad3b299` — xong phần chính; còn chữ "Miễn phí/Chứng chỉ" ở chi tiết khoá (làm trong 1.3) + CSS chết `.rm-ai-btn` (mục U) |
| 1.2a | §54 loại lớp + `/classes/options` + danh sách lớp lọc/phân trang | [x] (commit này) — pytest 9/9 + liên quan, đột biến 10/10 đỏ + 2 test khoá đỏ-trước, e2e mới 8/8 hai khổ có ghi, đo giao diện sáng sạch, axe 100 = 0 |
| 1.2b | Tạo nhanh lớp gia sư | [ ] |
| 1.2c | §55 chuyển lớp một thao tác | [ ] |
| 1.3 | Mở môn qua lớp, gỡ mọi nút Đăng ký, nhân sự xem chỉ-đọc | [ ] |
| 1.4a | §56 `last_seen_at` + tổng quan v2 (lớp, rời lớp, điểm danh GV, tài khoản ngủ) | [ ] |
| 1.4b | Danh sách học viên: lớp, lần cuối hoạt động, tiến độ, lọc | [ ] |
| 1.5A | Bỏ thi pha A: ẩn + tháo tuyến + §57 dữ liệu | [ ] |
| 1.5B | Bỏ thi pha B: thay bằng tiến trình học tập | [ ] |
| 1.5C | Bỏ thi pha C: xoá mã (GIỮ bảng) | [ ] |
| 1.6 | "Môn học"/"phân môn", bỏ "Mọi …", guard thuật ngữ | [ ] |
| U1–U6 | DESIGN.md, guard câu chữ, luật 7 đo chữ, CardHead gập, emoji → SVG, soi ảnh | [ ] |
| H2–H8 | Cấu hình 1 nguồn, lược đồ ghi mục đã chạy, outbox, Sentry/health, pre-push, sao lưu, sổ tay vận hành | [ ] |
| G1–G3 | `ban_do`: tác động thay đổi, tầng vai, god nodes | [ ] |
| Đ2 | Quyền TG, §58 đổi GV một buổi, §59 chấm công, §60 tài liệu R2, §61 gửi hàng loạt | [ ] |
| Đ3 | Diễn đàn công khai | [ ] |

**Mốc**: trước buổi TopHSA xem lại (1–2 tuần kể từ 24/09) PHẢI xong K0, B0, H1, 1.1a–d, 1.2a–c,
1.3, 1.4a–b, 1.5A, 1.6 và U2/U4 cho các màn khách đã xem. 1.5B–C, phần U còn lại, H, G làm xen
kẽ, được trượt sau buổi xem.

---

## Bối cảnh

Góp ý của TopHSA sau khi thử nhiều tài khoản: (1) đăng nhập không có "lưu mật khẩu"; (2) nhiều
chữ, "Mọi vai trò/lớp/trạng thái/hành động" → bỏ "Mọi", "Hợp phần" → "Môn học", màn đầu rối;
(3) mục Học không rõ để đăng ký hay quản lý, GV/TG cũng thấy nút đăng ký; (4) soạn giáo trình nằm
trong "Khu vận hành". Ghi chú họp: **quản lý lớp là ưu tiên số 1**, rồi quản lý học sinh; báo cáo
tổng cho quản trị (số lớp, rời lớp, điểm danh của GV, tài khoản lâu không hoạt động — cập nhật
tức thời); chuyển lớp; chấm công GV/TG; GV tạo tài liệu (link/slide/video) cho ~400 lớp gia sư
cá nhân hoá; TG làm như GV trừ dạy; gửi email/Zalo hàng loạt (ZNS 200đ/tin); bỏ HẾT tính năng thi,
thay bằng tiến trình học tập; bảo mật tài liệu theo quyền; diễn đàn mở cho người ngoài. Quy trình:
thử nghiệm với dữ liệu thật → đạt nhu cầu → bàn giao.

Đã đo trong mã (24/09):
- Nhân sự nào đăng nhập cũng rơi vào `/dashboard` (trang thẻ `KhuNhanSu`), không vào khu làm việc.
- `EnrollView` (`courses/views.py:221-264`) cho MỌI tài khoản tự ghi danh; xếp lớp KHÔNG mở môn;
  nhân sự phải bấm "Đăng ký" mới xem được bài (`lessons/views.py:251-270, 601-617`).
- Nút "Quản trị" (`AppShell.tsx:493-497`) dẫn tới `/admin` = soạn giáo trình; Vận hành có tab
  "Soạn giáo trình" (`quan-tri/vai.ts:84`); khu soạn có link ngược "Khu vận hành" (`admin/page.tsx:121`).
- Chữ nhiều chủ yếu vì GHI CHÚ LẬP TRÌNH VIÊN in ra màn (ngày, tên người, §, đường dẫn mã — trái
  RULES §10): Hướng dẫn ~12.500 ký tự, "Ai làm được gì" ~7.500, 69 `hint=` xám 13px.
- Hai hệ CSS (Tailwind vs `dashboard.css` 4.843 dòng, 160 mã màu), 57 emoji làm biểu tượng, đồ
  thừa sản phẩm lập trình cũ (bài diễn đàn GIẢ C++/Git `dashboard.js:968-1040`, "AI Premium",
  "Chứng chỉ hoàn thành", "ProgrammingEdu ×").
- Hạ tầng: Render gói free (ngủ, chờ ~84 s), CI/sao lưu/giữ ấm nằm trên GitHub Actions bị khoá
  (chưa chạy lần nào), không Sentry, thư gửi trên luồng rời không thử lại, DDL chạy lại mỗi deploy,
  dev + production CHUNG một Neon, cấu hình chạy máy chủ lệch ở `render.yaml`/`Procfile`/
  `gunicorn.conf.py`, `GET /api/admin/classes` trả TẤT CẢ lớp không phân trang, không có cột "lần
  cuối hoạt động".

## Quyết định đã chốt (anh Sơn, 24/09/2026)

| Việc | Chốt |
|---|---|
| Thi | Bỏ MỌI thứ về thi (thi thử online `/mock`, nhập kết quả kỳ thi tại trung tâm, khối điểm thi); thay bằng tiến trình học tập; GIỮ ngày thi HSA; KHÔNG xoá bảng |
| Mục Học | Trung tâm mở môn QUA LỚP; học viên không tự đăng ký; nhân sự xem bài chỉ-đọc |
| Đăng nhập | Ô "Ghi nhớ đăng nhập" 30 ngày (không tick = cookie phiên, hết khi đóng trình duyệt) + trình duyệt lưu mật khẩu |
| Giáo trình | Khu riêng "Giáo trình" (Quản trị viên + Biên tập nội dung) |
| Từ ngữ | "Môn học" = 3 phần thi (Tư duy định lượng, Tư duy định tính, Khoa học); "phân môn" = Lý/Hoá/Sinh/Sử/Địa; bỏ "Mọi …" |
| Trang gốc | Cổng đăng nhập TopHSA; bỏ "ProgrammingEdu ×" |
| Màn học viên | Ẩn bảng xếp hạng; bỏ popup "Giữ chuỗi"; GIỮ lộ trình + kỹ năng; bỏ đồ thừa sản phẩm cũ |
| Loại lớp | "Lớp nhóm" / "Gia sư" (1–3 em); 400+ lớp → tìm/lọc/phân trang |
| Trợ giảng | Như GV (sinh lịch, xoá/sửa buổi, giao/xoá bài tập, mục tiêu em, tài liệu lớp), TRỪ liên hệ + báo cáo phụ huynh |
| Nội dung GV | Tài liệu riêng từng lớp/buổi; PDF/slide/ảnh lên Cloudflare R2 (link ký số ngắn hạn, chỉ thành viên lớp), video bằng link YouTube/Drive |
| Chấm công | Tự động từ buổi học + đổi GV/TG cho một buổi + học vụ chỉnh tay + khoá tháng + xuất Excel |
| Gửi hàng loạt | Email học viên + email phụ huynh + Zalo phụ huynh + Zalo học viên; hiện tổng phí trước khi gửi; ZNS chỉ điền MẪU đã duyệt, chờ OA xác minh |
| Diễn đàn | Đọc công khai, viết phải đăng nhập (Google + email có xác minh); tên hiển thị tự đặt (học viên chưa thành niên); duyệt bài đầu của người mới; học vụ + GV kiểm duyệt; cựu học viên VẪN bị khoá, muốn vào thì tự đăng ký thành viên |
| Giao diện | Gọt từng màn, giao theo đợt, giữ bộ màu/phông |
| Hạ tầng trả phí | Render Starter, Neon Launch, Sentry, UptimeRobot, R2: nối mã sẵn, bật bằng biến môi trường khi bắt đầu thử nghiệm dữ liệu thật; không dựa vào GitHub Actions |
| CSDL | Tách dev khỏi production bằng Neon branch NGAY |
| Thứ tự | Đợt 1 góp ý + lớp + HS + tổng quan + bỏ thi → Đợt 2 quyền TG/tài liệu/công/gửi → Đợt 3 diễn đàn; hạ tầng xen kẽ |

Mặc định tôi tự chọn (anh sửa nếu khác): lớp `finished` vẫn mở bài cho em chưa bị cho rời lớp;
nhật ký kiểm toán giữ nhãn tiếng Việt cho các dòng thi CŨ (bảng `VIEC_CU`).

**Quy ước xuyên suốt**: DDL chỉ cộng (§54+ vào `backend/sql/legacy_schema.sql` + `kiem_luoc_do.MUC`;
không `;` trong chú thích, không `--` trong chuỗi); frontend chịu thiếu khoá TRƯỚC rồi backend mới
bỏ khoá (Vercel và Render deploy riêng); request snake_case, response camelCase, phân trang
`total/page/per_page`; `quyenVai.ts`/`huongDan.ts`/DOI_CHIEU/Cẩm nang cập nhật cùng mẻ; tầng JS cũ
chỉ được co (hạ `TRAN_DONG_MA` sau mỗi lần gỡ).

---

## B0 — Chốt việc đang dở (lịch học §53, chưa commit)
Mã + 18 đột biến đỏ thật đã xong (lich 10, sinh lịch 5, lớp của tôi 3). Còn: `e2e/lich-hoc.spec.ts`
2 khổ với `E2E_GHI=1`, `do_giao_dien` + `do_axe` cho `/giang-day/lich`, soi ảnh, PROGRESS, commit.
(`/giang-day/ket-qua-thi` sẽ bị gỡ ở 1.5 — không sửa gì thêm ở đó.)

## H1 — Tách CSDL (trước mọi test ghi của Đợt 1)
Anh tạo nhánh `dev` (và `ci`) từ production trong Neon console theo `docs/NHANH_CSDL_DEV.md`, dán
chuỗi vào `backend/.env` máy dev (tôi không sửa .env). Tôi thêm hàng rào: `conftest.py` +
`runserver` từ chối chạy khi host CSDL trùng `PE_DB_HOST_PRODUCTION` (biến trong .env, không
commit) trừ khi `CHO_PHEP_PRODUCTION=1` — đỏ trước.

## Đợt 1

### 1.1 Bốn góp ý nhìn thấy ngay
- **1.1a Ghi nhớ đăng nhập**: ô tick ở `login/LoginForm.tsx`; `LoginView` (`accounts/views.py:58`)
  nhận `nho`; refresh token mang claim `nho` + hạn 30 ngày (serializer làm mới GIỮ claim + hạn khi
  xoay; vẫn xoay + blacklist như `settings.py:367-374`); `lib/auth.ts:45-88` đặt `pe_rt` `maxAge`
  30 ngày khi `nho`, KHÔNG `maxAge` khi không; `src/proxy.ts` (làm mới trước khi dựng trang) +
  `lib/proxy.ts:197-225` (làm mới khi 401) + `lib/server-api.ts:46-101` giữ đúng chế độ. Lưu mật
  khẩu: thử thật Chrome/Edge (form đã `autoComplete="username"/"current-password"`); thiếu thì
  `navigator.credentials.store(new PasswordCredential(...))`.
- **1.1b Đường đi theo vai**: `LoginForm.tsx:164-170` — GV/TG → `/giang-day`, học vụ/admin →
  `/quan-tri/tong-quan`, Biên tập → `/giao-trinh`, học viên → `/dashboard`. `/admin` → `/giao-trinh`
  (chuyển hướng giữ link cũ; gate `admin/page.tsx:46,81`); nút "Quản trị" → "Giáo trình"; bỏ tab
  "Soạn giáo trình" (`quan-tri/vai.ts:84`) và link "Khu vận hành" (`admin/page.tsx:121`); mục "Học"
  của nhân sự (`navMuc.ts:60-95`) → "Môn học" chỉ-xem. Nút "Giảng dạy" hết hai đích (`/dashboard#teach`
  vs `/giang-day`) — luôn `/giang-day`.
- **1.1c Trang gốc** `(base)/page.tsx` → cổng đăng nhập TopHSA (một dòng mô tả + ô đăng nhập);
  tên hiển thị "TopHSA" (`AppShell.tsx:238`); favicon không dùng emoji.
- **1.1d Màn học viên**: ẩn bảng xếp hạng, bỏ popup giữ chuỗi (`dashboard.js:2214-2277`), bỏ bài
  diễn đàn giả (`dashboard.js:968-1040`), "AI Premium"/"Thêm node" (`RoadmapSection.tsx:38,47`),
  "Chứng chỉ hoàn thành"/"Truy cập vĩnh viễn"/"Miễn phí" (`courses/[courseId]/page.tsx:324-373`),
  nhãn Cài đặt "Học viên" cứng cho nhân sự (`DashboardClient.tsx:623`).

### 1.2 Quản lý lớp (ưu tiên số 1) — xem Phụ lục A bước 1–3
- **1.2a** §54 `classes.class_type` + `GET /api/admin/classes/options` (ra TRƯỚC phân trang) +
  `GET /api/admin/classes` lọc/phân trang/đếm + trang lớp lọc bằng form GET.
- **1.2b** `POST /api/admin/classes/gia-su` tạo nhanh (1 em + 1 GV + lịch, một giao dịch).
- **1.2c** §55 `class_members.transferred_to` + `POST …/members/<uid>/transfer`.

### 1.3 Mở môn qua lớp (góp ý 3) — Phụ lục A bước 5
`courses/truy_cap.py` là cổng duy nhất; `EnrollView` → 410; gỡ mọi nút Đăng ký/Huỷ ở tầng cũ và
React; nhân sự xem chỉ-đọc (chấm không ghi, hoàn thành 403). **Xếp lớp cho học viên hiện có TRƯỚC
khi deploy**, nếu không các em mất quyền vào bài.

### 1.4 Quản lý học sinh + tổng quan — Phụ lục A bước 6
- **1.4a** §56 `users.last_seen_at`; `teaching/overview.py` v2; `tong-quan/page.tsx` 4 thẻ mới.
- **1.4b** `quan-tri/tai-khoan` (học vụ chỉ thấy học viên): thêm cột lớp hiện tại + loại, lần cuối
  hoạt động, tiến độ; lọc "chưa xếp lớp", "không hoạt động ≥ N ngày"; nút chuyển lớp.

### 1.5 Bỏ thi — Phụ lục A bước 7–9 (ba pha, không xoá bảng)

### 1.6 Từ ngữ + gọt chữ — Phụ lục A bước 10 (làm SAU 1.5 vì 1.5 xoá nửa số chỗ "hợp phần")

## Giao diện U — gọt từng màn, đo được
- **U1 `frontend/DESIGN.md`** theo google-labs-code/design.md (front matter token lấy từ
  `tailwind.css` `@theme` + `theme.css`; 8 mục Overview/Colors/Typography/Layout/Elevation &
  Depth/Shapes/Components/Do's and Don'ts; luật câu chữ nằm trong "Do's and Don'ts" vì định dạng
  không có mục giọng văn). Guard so token DESIGN.md ↔ `theme.css`; `npx @google/design.md lint`.
- **U2 `e2e/unit/chu-nguoi-dung.test.mjs`**: cấm trong chuỗi HIỂN THỊ (không phải chú thích) — ngày
  `dd/mm/2026`, `§`, `.py`, `.ts`, `::`, "Anh Sơn", `permission_classes`, RULES/PROGRESS,
  "ProgrammingEdu", "Premium"; `hint` ≤ 90 ký tự. Đỏ trên mã hiện tại, xanh sau khi gọt.
- **U3 luật 7 của `do_giao_dien`**: tổng chữ giải thích trong khung nhìn đầu mỗi màn ≤ ngân sách,
  cho mọi vai, cả hai khổ.
- **U4 `CardHead`** (`components/ui/Card.tsx`): `hint` một dòng; giải thích dài vào `chiTiet` gập sau
  "ⓘ" (`<details>`, không JS) hoặc chuyển sang bài Hướng dẫn — một chỗ sửa, 69 thẻ hưởng.
- **U5** emoji → SVG `bieuTuong.tsx` (thêm qua `icons.js` + `scripts/sinh_bieu_tuong.py`); bỏ Font
  Awesome CDN.
- **U6** soi ảnh 1440 + 390 cho từng vai trước khi báo xong.

## Hạ tầng H — xen kẽ, nối sẵn chờ bật
- **H2** `render.yaml` khai đủ tên biến (sync:false); bỏ/đồng bộ `backend/Procfile` +
  `backend/gunicorn.conf.py`; guard: mọi `os.environ` backend đọc phải có trong `render.yaml` hoặc
  danh sách "chỉ dev".
- **H3** `bootstrap_schema` ghi mục đã chạy (bảng `luoc_do_da_chay`: §, checksum, lúc) → chỉ chạy mục
  mới; hết cảnh ADD lại CHECK + UPDATE backfill mỗi deploy; `--kiem` liệt kê mục chờ.
- **H4 Hộp thư đi (outbox)**, nền cho gửi hàng loạt: ghi cùng giao dịch với việc chính; nhận việc
  bằng `FOR UPDATE SKIP LOCKED` (KHÔNG advisory lock — Neon đi qua pooler, khoá phiên có thể sống
  lâu hơn worker); việc treo >10 phút nhận lại; backoff 1'→5'→30'→2h→6h; lỗi vĩnh viễn không thử
  lại; luồng nền mỗi worker (như `common/keepalive.py`, bật bằng `ENABLE_OUTBOX`, đánh thức bằng
  `threading.Event`) + `manage.py gui_hop_thu` cho cron. Chuyển `bao_doi_lich.py`,
  `quen_mat_khau.py`, `parent_send.py` (đang lặp đồng bộ), `thu_bao_cao.py`.
- **H5 Giám sát**: `sentry-sdk` + `@sentry/nextjs` chỉ bật khi có `SENTRY_DSN`, `send_default_pii=False`
  + lọc email/SĐT (dữ liệu trẻ vị thành niên); `/health/live` (không CSDL) + `/health/ready` (timeout
  ngắn, không vòng thử 19 s) cho UptimeRobot; log JSON ở production (`common/logging.JsonFormatter`
  đã có, chưa dùng); `X-Request-ID` của khách chỉ nhận khi đúng dạng.
- **H6 Cổng kiểm thay CI**: `.githooks/pre-push` (`core.hooksPath`) — ruff, `manage.py check`,
  compileall, tsc, eslint, unit guards, `ban_do --kiem`, pytest THEO TÁC ĐỘNG (G1); <3 phút. Bộ đủ
  (~54 phút) chạy tay trước mỗi mốc giao. `ci.yml` giữ nguyên.
- **H7 Sao lưu**: `scripts/sao_luu.py` (pg_dump host trực tiếp → mã hoá → khôi phục thử vào postgres
  tạm → so số dòng; tái dùng logic `sao-luu.yml`) chạy tay hằng tuần tới khi có PITR của Neon.
- **H8 `docs/VAN_HANH.md`**: deploy, rollback (Render rollback + lược đồ chỉ cộng), khôi phục, cảnh
  báo, danh sách bật khi bắt đầu thử nghiệm (Render Starter, Neon Launch, `SENTRY_DSN`, UptimeRobot,
  R2, Zalo OA, `FRONTEND_URL` = URL Vercel thật).
- Nhỏ: `conftest.py` `temp_admin` còn email cố định (`:126`) — chuyển sang uuid như `temp_user`.

## Graphify G — mở rộng `scripts/ban_do.mjs` (tất định, không gọi mô hình)
- **G1 `--anh-huong <range>`** (như `get_pr_impact` của graphify): tệp đổi → tuyến/view/bảng/trang/vai
  bị chạm → module pytest + spec e2e + màn cần soi lại; dùng trong H6 và mô tả mỗi mẻ commit.
- **G2 tầng VAI**: mục menu theo vai (`navMuc.ts`, `KhungGiangDay.tsx`, `quan-tri/vai.ts`,
  `khuTheoVai.ts`) → trang → API → lớp quyền → vai được phép; `--kiem` đỏ khi mục hiện cho vai R dẫn
  tới API từ chối R (đúng loại lỗi góp ý 3); xuất ma trận vai × màn để sinh bảng "Ai làm được gì".
- **G3 god nodes**: xếp hạng tệp nối nhiều nhất (`sessions.py`, `dashboard.js`, `AppShell.tsx` …)
  → thứ tự tách nhỏ; ghi số vào PROGRESS mỗi đợt.

## Đợt 2 — Phụ lục B
Quyền TG · §58 đổi GV/TG một buổi · §59 chấm công · §60 tài liệu lớp trên R2 · §61 gửi hàng loạt.

## Đợt 3 — diễn đàn công khai
- Vai mới "Thành viên diễn đàn" (chỉ diễn đàn: không trợ lý AI — mỗi lượt chat là tiền DeepSeek —
  không môn/lớp). Sửa `users_role_check` cẩn thận: đủ MỌI vai trong một câu (bài học deploy 18/09).
- Tạo tài khoản: Google (allauth có sẵn; mở nhánh tạo mới CHỈ cho vai này ở `accounts/oauth.py`) +
  email có link xác minh (tái dùng cơ chế chìa một lần của §52). `RegisterView` vẫn chỉ admin.
- Tên hiển thị diễn đàn (mặc định "An N."), tên thật/lớp/mã HSA không bao giờ lộ công khai; huy hiệu
  "Giảng viên TopHSA" / "Học viên TopHSA".
- Chuyên mục theo HSA (hỏi đáp theo môn, kinh nghiệm ôn thi, chọn trường, thông báo trung tâm).
- Kiểm duyệt: bài đầu của thành viên mới chờ duyệt; học viên/nhân sự đăng ngay; báo cáo, ẩn, khoá,
  ghim, chặn người; học vụ + GV kiểm duyệt; giới hạn tốc độ + lọc link rác; nhật ký kiểm toán.
- Đọc công khai: GET `forum/views.py` (450 dòng, đang `NguoiDungView`) thêm cổng công khai có giới hạn
  tốc độ; trang React dựng ở máy chủ `/dien-dan`, `/dien-dan/[id]` (metadata, sitemap) — gỡ diễn đàn
  khỏi `dashboard.js` (hạ trần tầng cũ).

## Kiểm chứng (mọi mục)
- pytest ĐỎ TRƯỚC + đột biến; `common/tests_hop_dong.py` cho mọi hình dạng mới; `tests_khai_cong` +
  `tests_ma_tran_quyen` tự phủ view mới; test lọc về dữ liệu của chính nó (tiền tố riêng).
- Unit guards (`node e2e/unit/*.test.mjs`), `ban_do --kiem` (+ G2), tsc, eslint `--max-warnings 0`,
  ruff, `next build`.
- E2E hai khổ (`may-tinh` 1440, `dien-thoai` 390), phần ghi sau `E2E_GHI=1`, tài khoản `audit2009.*`:
  học vụ tạo lớp gia sư → lọc → chuyển em sang lớp nhóm → quyền môn đổi; học viên không thấy
  "Đăng ký"/"Thi thử"; nhân sự mở bài chế độ xem; tổng quan 4 thẻ + "Cập nhật lúc"; đăng nhập có /
  không tick ghi nhớ (kiểm cookie có/không `Max-Age`); TG sinh lịch, xoá buổi, sửa mục tiêu, 403 ở
  báo cáo phụ huynh.
- `do_giao_dien` (+ luật 7) + `do_axe` 0 vi phạm; soi ảnh từng vai.
- Cập nhật `quyenVai.ts`, `huongDan.ts`, `DOI_CHIEU_YEU_CAU_TOPHSA_2026-09-23.md`, Cẩm nang bốn vai
  trò, PROGRESS sau mỗi mục.

---

## Phụ lục A — Thiết kế chi tiết Đợt 1 (từ lượt dò mã 24/09)

**Chín phát hiện chi phối thiết kế**
1. `GET /api/admin/classes` trả mọi lớp (`teaching/views.py:260-268` → `reports.class_list`
   `:566-605`); trang tài khoản dùng nó cho ô lọc lớp (`tai-khoan/page.tsx:55`) → phân trang trước
   là ô lọc lặng lẽ chỉ còn 25 lớp. `options` phải ra trước.
2. Giới hạn của TG là kiểm TRONG view, không phải lớp quyền: `sinh_buoi.py:239,246`,
   `sessions.py:423,592`, `assignments.py:374,457`, `viec_hom_nay.py:216`; `MucTieuHocVienView`
   dùng `IsSeniorTeachingStaff` (`ho_so.py:332`).
3. Không có cột lần cuối đăng nhập/hoạt động (`accounts/models.py:27-28`) → §56.
4. `_da_ghi_danh` (`lessons/views.py:251-270`) gác `CheckAnswersView` (`:575`) + `CourseContentView`
   (`:612`); `CompleteLessonView` KHÔNG gác và tự tạo ghi danh (`:428-451`); cache theo worker.
5. Neon qua pooler (`settings.py:196`), RULES §5 cấm `SET` → không advisory lock phiên; outbox dùng
   `FOR UPDATE SKIP LOCKED`.
6. `openpyxl` đã có (`requirements.txt:21`); bộ ghi duy nhất ở `mockexam/quan_tri.py:98` → dời sang
   `common/bangtinh.py` trước khi xoá app thi.
7. Kế hoạch học đã lưu chứa mục mock (`stats/plan.py:240-250`) → hết sự kiện mock thì mục ấy không
   bao giờ xong và số "chậm" (`plan.py:505-548`) phình.
8. `seed_data` bật lại mọi nhiệm vụ mỗi lần chạy (`seed_data.py:297-312`) → bỏ `daily_mock` cần cả
   UPDATE dữ liệu lẫn sửa mã.
9. Frontend/backend deploy riêng; nhiều hình dạng trang đòi khoá như `mockCount` (`tong-quan/page.tsx:38-39`)
   → frontend chịu thiếu trước, backend bỏ sau.

Chuyển `_page_with_total`/`_like` từ `teaching/admin_users.py:73-116` sang `common/params.py` (giữ
tên cũ làm bí danh) để tránh vòng `views → admin_users → views`.

### Bước 1 — Loại lớp + danh sách lớp mở rộng được (1.2a)
```sql
-- §54 · Loại lớp: nhóm hoặc gia sư (1 tới 3 em). Lớp cũ nhận 'nhom' qua DEFAULT.
ALTER TABLE classes ADD COLUMN IF NOT EXISTS class_type TEXT NOT NULL DEFAULT 'nhom';
ALTER TABLE classes DROP CONSTRAINT IF EXISTS classes_class_type_check;
ALTER TABLE classes ADD CONSTRAINT classes_class_type_check
    CHECK (class_type IN ('nhom', 'gia_su'));
```
- `teaching/vocab.py`: `LOAI_LOP`, `NHAN_LOAI_LOP`, `TRAN_GIA_SU = 3`.
- `views._clean_class_payload` (`views.py:160-250`) nhận `class_type` (`null` = không gửi); đổi sang
  `gia_su` khi đang >3 em → 400. `_ghi_thanh_vien` (`views.py:448-566`): lớp gia sư đầy → 409 (lẻ) /
  nhóm `full: []` (hàng loạt).
- `GET /api/admin/classes` (`IsAdminOrAcademic`): `q` (tên/mã lớp, tên GV, tên hoặc mã HSA của em
  đang học), `type`, `term_id`, `teacher_id` (GV chính HOẶC TG đang gán), `status`, `course_id`,
  `page`, `per_page` (25, tối đa 100) → `{classes:[… + classType, studentNames (gia_su),
  assistantNames], total, page, per_page, counts:{byType, byStatus}, teachers, assistants, statuses,
  classTypes}`; cố định 3 câu (`reports.class_page` mới).
- MỚI `GET /api/admin/classes/options?q=&status=` → `{classes:[{id,name,code,classType,status,termName}]}`;
  khai TRƯỚC `classes/<int:class_id>` (`teaching/urls.py:109-111`).
- Frontend: `lop-hoc/page.tsx` đọc `searchParams` (`q, loai, dot, gv, tt, khoa, trang`), lọc bằng form
  GET (khuôn `nhat-ky/page.tsx:185-230`), chip đếm theo loại; `LopHocClient.tsx` cột "Loại" + tên em
  dưới lớp gia sư, `nap()` → `router.refresh()`, phân trang, nhãn "Môn học"; `lop.ts` thêm
  `classType` vào `TRUONG`, `formRong()` → `'nhom'`; `tai-khoan/page.tsx:55` → `/options`.
- Test: CHECK chặn giá trị lạ; lọc theo loại/GV/TG/trạng thái (đột biến: bỏ nhánh TG); tổng không mất
  ở trang rỗng; em thứ 4 lớp gia sư → 409; PUT `class_type: null` không ghi NULL; `options` không
  phân trang; hợp đồng `{classes,total,page,per_page,counts}`. Guard `lop-hoc.test.mjs` ④ mặc định.

### Bước 2 — Tạo nhanh lớp gia sư (1.2b)
- Tách vòng chèn của `GenerateSessionsView.post` (`sinh_buoi.py:262-322`) thành
  `sinh_buoi.tao_buoi(request, class_id, lop, ts, dry_run)`.
- MỚI `POST /api/admin/classes/gia-su` (`teaching/lop_gia_su.py`, `IsAdminOrAcademic`): trường lớp như
  `_clean_class_payload` + `student_id|student_email` + `weekdays,start_time,duration_minutes`
  (`_doc_than`) + `generate` + `dry_run`; em phải là Học viên, GV phải là Giảng viên/admin; tên tự
  đặt "Gia sư · {em} · {GV}", lịch chữ tự sinh, `capacity=3`; MỘT `transaction.atomic()` (lớp → thành
  viên → buổi); dry-run trả xem trước + trùng GV/em/phòng (`tim_trung_nhieu`); 201
  `{ok, classId, name, memberUserId, sessions:{dem, ids, canhBao}}`; audit dùng lại CLASS_CREATE,
  CLASS_MEMBER_ADD, SESSION_GENERATE.
- Frontend `lop-hoc/TaoLopGiaSu.tsx` (tìm em qua `/api/admin/users?role=Học viên&q=`) + helper thuần
  `lop-hoc/giaSu.ts` + `e2e/unit/lop-gia-su.test.mjs`.
- Test: ép lỗi trong `tao_buoi` → không còn lớp/thành viên (đột biến: bỏ `atomic`); dry-run không ghi;
  người không phải Học viên → 400; GV trùng giờ lớp khác → cảnh báo nhưng vẫn tạo.

### Bước 3 — Chuyển lớp một thao tác (1.2c)
```sql
-- §55 · Chuyển lớp MỘT bước: lượt ở lớp A trỏ tới lượt mới ở lớp B.
ALTER TABLE class_members ADD COLUMN IF NOT EXISTS transferred_to INTEGER;
ALTER TABLE class_members DROP CONSTRAINT IF EXISTS class_members_transferred_to_fk;
ALTER TABLE class_members ADD CONSTRAINT class_members_transferred_to_fk
    FOREIGN KEY (transferred_to) REFERENCES class_members(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_class_members_transferred_to
    ON class_members (transferred_to) WHERE transferred_to IS NOT NULL;
ALTER TABLE class_members DROP CONSTRAINT IF EXISTS class_members_transfer_reason_check;
ALTER TABLE class_members ADD CONSTRAINT class_members_transfer_reason_check
    CHECK (transferred_to IS NULL OR leave_reason = 'transferred');
```
- MỚI `POST /api/admin/classes/<class_id>/members/<user_id>/transfer` (`teaching/chuyen_lop.py`,
  `IsAdminOrAcademic`): `{to_class_id, effective_date?, note?}` (không ở tương lai, không trước
  `joined_at` ở A); một `atomic()`: đóng A (`leave_reason='transferred'`, 404 nếu không có lượt mở) →
  mở B (409 nếu đã ở B; B gia sư đầy → 409; B huỷ → 400; B đã kết thúc → cho kèm cảnh báo) → nối
  `transferred_to`; trả `{ok, fromClassId, toClassId, fromMemberId, toMemberId, at, warnings}`
  (cảnh báo "Em sẽ không còn mở được môn X" khi `course_id` khác).
- Audit mới `CLASS_MEMBER_TRANSFER = 'class.member.transfer'` + nhãn ở `nhat-ky` (guard
  `nhan-nhat-ky.test.mjs` đỏ tới khi có nhãn); `quen_truy_cap(uid)`; `dong_thoi_gian.py:88-96` hiện
  "Chuyển từ A sang B".
- Frontend: lựa chọn lý do rời lớp (`LopHocClient.tsx:829-855`) thêm "Chuyển sang lớp khác…" mở
  `ChuyenLop.tsx` (tìm lớp qua `/options?q=`, ngày, ghi chú); tuỳ chọn thêm nút ở hồ sơ em.
- Test: giữ lịch sử hai lượt + liên kết + lý do; em đã ở B → 409 và A KHÔNG bị đóng (đột biến: bỏ
  `atomic`); CHECK chỉ với `transferred`; nhật ký có một dòng.

### Bước 5 — Mở môn qua lớp (1.3)
- MỚI `courses/truy_cap.py`: `quyen_khoa(user) -> {course_id: 'hoc'|'xem'}` — nhân sự (admin, học vụ,
  GV, TG, Biên tập) → mọi môn `'xem'`; học viên → `'hoc'` cho môn của lớp `left_at IS NULL AND
  status <> 'cancelled'` (`course_id IS NULL` = `stats.competency.COURSE_ORDER`). Cache 60 s
  `truycap:<uid>`; `quen_truy_cap(uid)` khi thêm/rời/chuyển lớp, tạo nhanh gia sư, PUT lớp đổi
  `course_id`/`status` (quên cả lớp), xoá lớp. Giới hạn đã biết: cache theo worker → trễ ≤60 s.
- `lessons/views.py`: `CourseContentView` (`:601-617`) — nhân sự 200 + `cheDo:'xem'`, học viên không
  quyền 403 "Môn này chưa mở cho lớp của em — học vụ xếp em vào lớp có môn này thì bài mở ngay.";
  `CheckAnswersView` (`:575`) nhân sự chấm KHÔNG `ghi_nhan`; `CompleteLessonView` (`:314`) thêm cổng
  (nhân sự 403 "Tài khoản nhân sự chỉ xem bài, không ghi tiến độ"; học viên không quyền 403); giữ
  chèn `enrollments` (`:442-450`) làm bộ nhớ tiến độ.
- `courses/views.py`: `EnrollView` POST/DELETE → 410 "Trung tâm mở môn học theo lớp"; `CoursesView`,
  `CourseDetailView`, `CoursesEnrolledView`, `EnrolledView` (`:28-218`) trả `access` + `enrolled :=
  access is not null`; `RateCourseView` (`:281`) cổng theo `truy_cap`. `stats/views.py:58,236`.
- Tầng cũ (chỉ co): `main.js:877` nút → nhãn "Chưa mở cho lớp của em"; xoá `toggleEnroll`,
  `_applyEnrollState`, huỷ đăng ký (`main.js:1123-~1220`); `course_detail.js` xoá `enroll()/unenroll()`;
  `lesson_hsa.js:904` nhãn. React: `courses/[courseId]/page.tsx:358-363` bỏ hai nút, nhân sự thấy
  "Chế độ xem"; `DashboardClient.tsx:421` "Chưa mở", xoá modal `:927-939`; `HocTiep.tsx:113`. Hạ
  `TRAN_DONG_MA`.
- Test: lớp môn X mở X không mở Y; `course_id NULL` mở cả ba; rời lớp mất quyền sau quên cache;
  complete không quyền 403 (đột biến: bỏ cổng); nhân sự mọi vai xem được + complete 403; chấm của
  nhân sự không đổi `lesson_progress.answers_json`; enroll 410; chuyển lớp đổi quyền môn.

### Bước 6 — Tổng quan v2 (1.4a)
```sql
-- §56 · Lần cuối thấy tài khoản — đóng dấu lúc đăng nhập và lúc làm mới token,
-- KHÔNG ở mỗi request.
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP;
```
- `accounts/hoat_dong.py::danh_dau(uid)` gọi từ `LoginView` (sau khi thành công), `oauth_complete`,
  `LamMoiView(TokenRefreshView)` mới ở `accounts/urls.py:10` (đọc `user_id` từ refresh sau
  `super().post`). Chính xác ~30 phút — đủ cho mốc 7/14/30 ngày.
- `teaching/overview.py::tong_quan(term_id, tu, den, loai)` (~9 câu, cố định):
  `summary.classesByType`; `roiLop` {tu, den mặc định đầu tháng → hôm nay; `theoLyDo`
  (completed/dropped/transferred/chuaGhi), `theoLoai`, `theoThang` 6 tháng, `ds` 50 dòng kèm
  `sangLop` qua `transferred_to`}; `giangVien` [{soLop, buoiDaDay, daDiemDanh, chuaDiemDanh,
  diemDanhMuon (> kết thúc + 24 h), tiLe}] theo `c.teacher_id` (Đợt 2 → COALESCE buổi); `taiKhoanNgu`
  {nguong [7,14,30], hocVien/nhanSu {d7,d14,d30,chuaTungVao}, ds 50 em lâu nhất} với hoạt động =
  `GREATEST(last_seen_at, MAX(learning_events.occurred_at))`, chỉ tài khoản đang mở; `generatedAt`;
  bảng từng lớp tối đa 50 dòng xếp theo vấn đề + `classesTotal`; BỎ cột thi thử (`:192-206`,
  `:263-264`, `:283-299`) → `activeLearners7d`.
- Frontend `tong-quan/page.tsx`: TRƯỚC HẾT cho `mockCount`/`mockAvg` thành tuỳ chọn và thôi vẽ
  (`:17-74`, `:334`, `:388-409`), rồi 4 thẻ mới (Lớp theo loại · Rời lớp trong kỳ (form GET tu/den) ·
  Điểm danh của GV · Tài khoản không hoạt động, dòng dẫn tới hồ sơ) + "Cập nhật lúc …";
  `ViecCanLam.suyViec` thêm "N học viên ≥14 ngày không vào", "N buổi điểm danh muộn".
- Test: rời lớp chỉ đếm trong khoảng; điểm danh muộn theo ngưỡng; `last_seen` đóng dấu khi login +
  refresh (đột biến: bỏ ở `LamMoiView`); tài khoản khoá không tính ngủ; số câu cố định với 2 vs 20
  lớp (`django_assert_max_num_queries`); hợp đồng tổng quan. Rủi ro: lúc mới triển khai
  `last_seen_at` rỗng → rơi về learning events + `created_at`, giao diện ghi "đo từ ngày …".

### Bước 7–9 — Bỏ thi (1.5), giữ ngày thi HSA + mọi bảng
**Pha A (đảo được) — frontend trước**: `navMuc.ts:84` bỏ "Thi thử"; `mock/page.tsx` → redirect
`/dashboard`; `ket-qua-thi/[classId]/page.tsx` → redirect `buoi-hoc`, bỏ link
`bao-cao/[classId]/page.tsx:186`; `admin/SoanClient.tsx:21,205` + `admin/page.tsx:11,99` bỏ tab Đề thi;
`TheSoHsaClient.tsx:134` bỏ nút; `DashboardClient.tsx:461` bỏ chip; `dashboard.js:2783,3023,3051` bỏ
link `/mock`, `main.js:47` bỏ gợi ý; trang gốc + `ThuMotCau.tsx:136,144,222` + `layout.tsx:58`;
`quyenVai.ts:72,77,301-304`; `huongDan.ts:408-414`; `ToBaoCao.tsx:248-320` ẩn khối "Kỳ thi thử tại
trung tâm" + ô thi thử. **Rồi backend**: `config/urls.py:39` bỏ `include('mockexam.urls')` (giữ app
trong INSTALLED_APPS lúc này); `teaching/urls.py:63-66` + import `:14` bỏ tuyến ket-qua-thi;
`seed_data.py:171-172` bỏ `daily_mock`; dữ liệu:
```sql
-- §57 · Bỏ thi thử: tắt nhiệm vụ "Làm 1 đề thi thử", đổi nhãn nút lộ trình đã lưu.
UPDATE missions SET is_active = FALSE WHERE code = 'daily_mock' AND is_active;
UPDATE roadmaps
   SET mermaid_def = replace(mermaid_def, 'Luyện đề tổng (CBT)', 'Ôn tổng hợp'),
       nodes_json  = replace(nodes_json::text, 'Luyện đề tổng (CBT)', 'Ôn tổng hợp')::jsonb
 WHERE mermaid_def LIKE '%Luyện đề tổng (CBT)%';
```
Bộ sinh: `accounts/views.py:602-609`, `seed_data.py:70-97`, `roadmapData.js:29,95-97` → "Ôn tổng hợp".
E2E cần sửa: `dieu-huong-la-lien-ket`, `khung-chung`, `vai-tro-cong`, `huong-dan-moi-vai`,
`nhat-ky-phan-hoi-thieu`.

**Pha B — thay bằng tiến trình học tập.** Frontend chịu thiếu trước: `hinhDang.ts:48-51`,
`ToBaoCao.tsx:44-60,128-130,290-320,459` (ô mới: bài xong trong kỳ, phút học đo được, số ngày có
hoạt động, tiến độ theo môn), `PhuHuynhNhanGi.tsx:84-87`, `duLieuHsa.ts:28-42` +
`TheSoHsaClient.tsx:34-46,130-134` ("Tiến độ chương trình X/76 bài"), `dashboard.js` (`mockPct`
`:2656-2735`, đường tiến bộ `:2934-3051` → `lessonPct` + phút, chỉ tiêu tuần "mocks" `:3209-3275`, mục kế
hoạch "mock" `:3512-3519` ghi là mục cũ). Rồi backend: `stats/competency.py:32,41,57,224,264-266,
333-347`; `stats/gradebook.py:28,51,55,92,106` + `progress_curve` (`:197-282`) theo bài học;
`stats/journal.py:43,51,272-312,351-365` (PUT còn gửi `mocks` thì BỎ QUA, không 400); `stats/plan.py`
(thôi sinh mục mock `:240-250`; `_duyet_muc` `:432-470` + `read()` `:568-590` BỎ QUA mục mock cũ —
không tính chờ, không tính chậm; bỏ KIND_MOCK ở `:356,:530`); `stats/views.py:115-121,279-301` →
`lessonsThisWeek`, `progressPct`; `teaching/reports.py:53,211-240,292-309,354-359,461-463,545` (cảnh
báo "Chưa hoàn thành bài nào của môn lớp", `noMock` → `noLesson`); `parent_report.py:335-372`
(`_hoc_tap` dựng lại theo bài học), `:374-420` xoá `_thi_tai_trung_tam`, `:597-601`,
`rut_gon_cho_link`; `bao_cao_pdf.py:300-330,370-420,505`; `bao_cao_lop_pdf.py:196,254-255,296`;
`exports.py:346-398` ("Bài học 7 ngày qua"); `thu_bao_cao.py:96-114`; `dong_thoi_gian.py:11-12,
96-110`; `chatbot/profile.py:97-107`; `du_lieu_mau.py:28,212,634`. Giữ `common/events.py:36-37`,
bỏ khỏi `GRADED_KINDS` (`:60`).
Test: sự kiện mock không còn vào năng lực/sổ điểm/kế hoạch (đỏ trước pha B); kế hoạch cũ có mục mock
không làm tăng "chậm" (đột biến: bỏ phép bỏ qua).

**Pha C — xoá mã (bảng giữ)**: dời bộ ghi xlsx sang `common/bangtinh.py` TRƯỚC; xoá `backend/mockexam/`
+ `'mockexam'` khỏi `settings.py:122`, `teaching/nhap_ket_qua_thi.py`, `nhap_ket_qua_view.py` + test,
`backfill_learning_events._mocks`, tuyến `EnrollView` (`courses/urls.py:11`); frontend xoá
`MockExam.tsx`, `mock/`, `ket-qua-thi/`, `admin/DeThi.tsx`, `mock.css`; `common/audit.py:78-82,119-125`
bỏ hằng thi, nhãn cũ chuyển sang `VIEC_CU` ở `nhat-ky`. GIỮ `sql/mockexam_schema.sql`, DDL §48
`ket_qua_thi_ngoai`, mục §48 trong `kiem_luoc_do`, `pypdf`. Guard: `hinh-dang`, `nhan-nhat-ky`,
`huong-dan`, `kieu-noi-dung`, `global-mo-coi`, `font-awesome-tu-nap`; hạ `TRAN_DONG_MA`/`TRAN_TEP`;
bỏ hợp đồng `/api/mock-exams` (`tests_hop_dong.py:73`).

### Bước 10 — Từ ngữ (1.6)
- "Hợp phần" → "Môn học": 64 chỗ frontend / 17 tệp + chuỗi backend tới người dùng (`parent_report`,
  `bao_cao_pdf.py:423-449`, `thu_bao_cao.py:180`, `overview`, lý do trong `plan`, `chatbot/graph.py:101`,
  `profile.py:102`, `lop_cua_toi`) + dữ liệu seed đã nằm trong CSDL (`seed_data.py:20-215` dùng
  `ON CONFLICT DO NOTHING` → cần UPDATE). Test đang khẳng định chuỗi: `tests_bao_cao_pdf.py:236,246`,
  `courses/tests_so_lieu_landing.py:51-54`. Lý/Hoá/Sinh/Sử/Địa → "phân môn"
  (`lessons/minh_hoa/hsa_science.py:288-304`, `roadmapData.js:57`). Tên định danh (`BaHopPhan.tsx`) giữ.
- "Mọi …": `AccountsClient.tsx:373,382,387` (ô không có nhãn hiện) → "Vai trò"/"Trạng thái"/"Lớp";
  `nhat-ky/page.tsx:194`, `giang-day/lich/page.tsx:210,224` → "Tất cả".
- Guard MỚI `e2e/unit/thuat-ngu.test.mjs`: đỏ khi "hợp phần" (không phân biệt hoa thường) xuất hiện
  trong chuỗi không phải chú thích ở `src/` hoặc `public/static/js`, hoặc `<option>` bắt đầu "Mọi ".

## Phụ lục B — Thiết kế Đợt 2

**Quyền TG (không thêm lớp quyền mới).** Lớp `IsClassManager` sẽ cho đúng bằng `IsTeachingStaff` →
không thêm. Gỡ chặn: `sinh_buoi.py:239,246-249` (`coTheSinh=True`), `sessions.py:423-431`
(`quyen.xoaBuoi=True`, `baoCaoPhuHuynh` vẫn senior), `sessions.py:592-595`, `assignments.py:374,457`,
`viec_hom_nay.py:216-228`; `ho_so.MucTieuHocVienView` → `IsTeachingStaff`. GIỮ chặn:
`exports.bo_cot_lien_lac` (`:155`), `ParentReport*`, `ParentReportLink*`, `ParentReportSendAll`,
`ParentContactsImport`. Test mới ở `common/tests_ma_tran_quyen.py`: `IsSeniorTeachingStaff` gác ĐÚNG
tập view dữ liệu phụ huynh (đột biến: trả `MucTieuHocVienView` về Senior → đỏ); TG ở lớp mình: sinh
lịch 200/201, xoá buổi 200/409, sửa mục tiêu 200, báo cáo phụ huynh 403; lớp không được gán: 404.
Frontend: tab "Tiến độ" (`giang-day/tien-do/[classId]`, `[userId]` dùng `TeachStudentView`), dời
`MucTieuEm.tsx` sang `components/`; `quyenVai.ts` + `huongDan.ts` cho TG.

**§58 đổi GV/TG một buổi.** `class_sessions.teacher_id` (FK users SET NULL; NULL = GV của lớp, index
riêng phần), `class_sessions.assistants_override BOOLEAN NOT NULL DEFAULT FALSE`, bảng
`session_assistants(session_id, user_id, created_by, created_at, PK(session_id,user_id))` có index mọi
FK. `teaching/nhan_su_buoi.py::nhan_su(session_ids)` một câu (GV = `COALESCE(s.teacher_id,
c.teacher_id)`; TG = hàng `session_assistants` nếu override, không thì TG của lớp đang hoạt động tại
`starts_at`). `PATCH /api/teach/sessions/<id>` thêm `teacher_id`, `assistant_ids` (chỉ học vụ/admin);
`can_see_session()` cho người dạy thay; đổi `trung_lich.py:44-45,106-107`, `lich.py:66-89`, overview.

**§59 chấm công.** Buổi tính công trong tháng M: `starts_at` thuộc M, không huỷ, `status='done'` HOẶC
`attendance_taken_at IS NOT NULL`; phút = `COALESCE(duration_minutes, 90)`. Bảng
`timesheet_months(month PK, locked_at, locked_by, note)`, `timesheet_lines` (ảnh chụp khi khoá:
user, session, class, class_name, role `giang_vien|tro_giang`, starts_at, minutes),
`timesheet_adjustments` (sessions_delta, minutes_delta, reason bắt buộc). API: `GET
/api/admin/timesheet?month=&user_id=` (tháng chưa khoá tính trực tiếp, đã khoá đọc ảnh chụp), `GET
/api/teach/timesheet/me`, `POST/DELETE /api/admin/timesheet/adjustments` (409 khi đã khoá), `POST
/api/admin/timesheet/lock` (mở khoá chỉ admin), `GET /api/admin/timesheet/export.xlsx` (Tổng hợp / Chi
tiết / Điều chỉnh). Audit `timesheet.adjust/lock/unlock`; tab mới ở `quan-tri/vai.ts` (guard
`cong-quan-tri.test.mjs`).

**§60 tài liệu lớp (R2).** `class_materials(id, class_id, session_id NULL, kind link|video|file, title,
url, r2_key UNIQUE, file_name, mime, size_bytes, state pending|ready, created_by, created_at,
hidden_at)`, `class_material_views(material_id, user_id, viewed_at)`. `GET/POST
/api/teach/classes/<id>/materials` (link/video: `kiem_lien_ket` + danh sách YouTube/Drive; tệp:
presigned PUT 10 phút, khoá content-type, pdf/ppt/pptx/docx/png/jpg/webp, ≤50 MB); `POST
/api/teach/materials/<id>/confirm` (HEAD trên R2 → ready); `DELETE` ẩn mềm; `GET
/api/materials/<id>/open` (nhân sự `can_see_class` hoặc thành viên ĐANG học → ghi nhật ký xem → 302
presigned GET 5 phút). `lop_cua_toi` trả `taiLieu` theo lớp/buổi. `common/r2.py` ký SigV4 thuần Python
(~60 dòng, kiểm bằng véc-tơ thử công bố của AWS), không boto3. Biến `R2_ACCOUNT_ID`,
`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`; bucket cần CORS cho PUT từ miền Vercel; CSP
thêm miền R2.

**§61 gửi hàng loạt (trên H4).** `message_campaigns(title, body, zns_template, recipients
students|parents|both, audience JSONB, send_email, send_zns, recipient_count, cost_vnd, status
draft|sending|done|cancelled, …)` + `outbox(campaign_id, channel email|zns, to_addr, user_id, subject,
body, params JSONB, dedup_key UNIQUE, status queued|sending|sent|failed|dropped, attempts,
next_try_at, error, provider_id, claimed_at, …)` index riêng phần `(next_try_at) WHERE status IN
('queued','failed')`. API (`IsAdminOrAcademic`): `POST /api/admin/messages/preview` → người nhận theo
kênh, thiếu liên hệ, tổng phí ZNS, bị loại (từ chối nhận/demo/thiếu liên hệ), mẫu; `POST
/api/admin/messages` (nháp) → `POST /api/admin/messages/<id>/send {confirmCostVnd}` phải bằng phí
tính lại lúc gửi; danh sách + nhật ký giao. Tôn trọng `parent_report_optout`, `is_demo`, chế độ thử.
ZNS KHÔNG gửi được chữ tự do — chỉ điền tham số mẫu đã duyệt; kênh Zalo tắt kèm lý do tới khi OA
xác minh.

## Phụ lục C — Nguồn đã tra (24/09)
- graphify (Graphify-Labs): tree-sitter tất định, cạnh EXTRACTED/INFERRED, god nodes,
  `get_pr_impact`/`triage_prs`, git hook cập nhật tăng dần. Lượt chạy 23/09 trên repo này: 0 cạnh ở
  các chỗ nối giữa tầng → sinh ra `scripts/ban_do.mjs`.
- OWASP Session Management Cheat Sheet: token ghi nhớ xoay mỗi lần làm mới, phát hiện dùng lại →
  thu hồi hết, không để token ở localStorage.
- Neon branching (tài liệu Neon): nhánh copy-on-write tức thì, gói Free 10 nhánh/dự án.
- Việc nền không Redis: `django-tasks` + `django-tasks-db` chạy được trên Django 5.2 nhưng cần tiến
  trình worker riêng → chọn outbox + luồng trong tiến trình.
- google-labs-code/design.md: token YAML + 8 mục + CLI `lint`/`diff`/`export`.
