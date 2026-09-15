# Bàn giao phiên — đọc tệp này đầu tiên khi mở phiên mới

*Cập nhật 15/09/2026 (sau vòng 24). Viết để một phiên mới bắt kịp trong 5 phút mà không phải
đọc lại 5.800 dòng nhật ký. Cách làm học từ `BAN-GIAO-PHIEN.md` của dự án cô
Giang — chỉ học cách, không đụng bên ấy.*

---

## Bốn tệp cần biết

| Tệp | Là gì | Khi nào đọc |
|---|---|---|
| `PROGRESS.md` | Nhật ký. Khối "Đọc trước" ở đầu có **lệnh đang hiệu lực** của anh Sơn và trạng thái mới nhất. Mục mới ở TRÊN vạch `<!-- MỚI NHẤT -->`. | Trước khi bắt tay |
| `docs/VIEC_CUA_ANH.md` | Việc **chỉ anh Sơn** làm được — một bảng ở đầu, xếp theo mức chặn. | Khi cần hỏi anh hoặc báo cáo |
| `TODO.md` | Việc của tôi (backlog T1–T66…). | Khi hết việc đang làm |
| `BAO-CAO-TRANG-THAI.md` | Số đo tự sinh — chỉ đo, không nhận định. `python scripts/kiem_ke_san_pham.py --md BAO-CAO-TRANG-THAI.md` | Trước khi trích bất cứ con số nào |
| `RULES.md` | Tiêu chuẩn bắt buộc. §4 là cổng trước khi báo xong; §5 là luật chạm CSDL. | Trước mỗi commit |

## Cách làm việc đã chốt

- **Đo, không đoán.** Mọi con số báo ra phải do chính mình đo trên dữ liệu thật,
  kèm ngày. Bộ đo giao diện phải chạy `--tu-kiem` trước (nó đã nói dối 12 lần).
- **Test phải đỏ được.** Viết xong test → lùi mã → phải đỏ *đúng cái test ấy* →
  phục hồi → xanh. Lùi một phần mà vẫn xanh = test giả (đã mắc 07/09).
- **Neon là MOCK production** (anh Sơn chốt lại 14/09 tối): dữ liệu không thật
  hoặc đã quá cũ — ghi thử thoải mái, không xin phép, không sao lưu, không bắt
  buộc dọn/đếm. Vẫn giữ: DDL chỉ cộng thêm qua `bootstrap_schema`, không `SET`,
  pytest cuộn lại + lọc về dữ liệu của chính nó, không gửi phụ huynh thật. Thử
  khô cuộn lại KHÔNG chứng minh lệnh chạy được — ràng buộc hoãn chỉ kiểm lúc
  COMMIT (đã mắc 07/09). Xem `RULES.md §5`.
- **Một con số chỉ tính ở một nơi.** Màn hình, CSV, PDF phải nói cùng một chuyện.
- **Đặt câu hỏi trước việc lớn.** Anh Sơn muốn được hỏi; nhưng câu hỏi phải kèm
  con số ĐÚNG — một lời gật xin bằng số sai không phải lời gật.
- **Kịch bản Python tạm: viết ra tệp, chạy `python -P tệp`. KHÔNG heredoc.**
  Heredoc đã phá ba lần: backtick bị bash diễn giải, `\x00` thành byte NUL thật,
  dấu nháy lẻ làm bash chờ vô tận. Cùng lý do: **không backtick trong thông
  điệp commit** trừ khi dùng `-F tệp`.

## Lệnh hay dùng

```
# máy chủ dev — --noreload là BẮT BUỘC, nên THÊM TUYẾN MỚI thì phải dừng rồi bật lại
# (không thì tuyến vừa viết trả 404 và trông như lỗi định tuyến)
cd backend  && ALLOWED_ORIGINS="http://localhost:3100" ./.venv/Scripts/python.exe manage.py runserver 9000 --noreload
cd frontend && npm run dev                              # cổng 3100

# cổng trước khi báo xong (RULES §4)
cd backend  && ./.venv/Scripts/python.exe -m ruff check .
cd backend  && ./.venv/Scripts/python.exe -m pytest -q  # ~29 phút, vào Neon thật
cd frontend && ./node_modules/.bin/eslint src e2e --max-warnings 0 && ./node_modules/.bin/tsc --noEmit
cd frontend && for f in e2e/unit/*.test.mjs; do node "$f" >/dev/null || echo "ĐỎ $f"; done   # 25 unit Node (đếm 14/09 tối, sau vòng 18)
python scripts/cap_the.py                               # thẻ 30 phút, không ghi CSDL
PE_TOKENS="D:\pe_hsa\.the\tokens_ad.json" node scripts/do_giao_dien.mjs --tu-kiem   # phải ĐẠT
PE_TOKENS="D:\pe_hsa\.the\tokens_ad.json" node scripts/do_giao_dien.mjs             # rồi đo thật

# hiệu năng — cần BẢN DỰNG production (next build && next start -p 3100), không đo trên dev.
# Từ 14/09 tệp này tự làm nóng trình duyệt, đo 3 lượt lấy trung vị, tắt bộ đệm mỗi lượt.
cd frontend && node node_modules/next/dist/bin/next build && node node_modules/next/dist/bin/next start -p 3100
MSYS_NO_PATHCONV=1 node scripts/do_hieu_nang.mjs        # Git Bash: thiếu MSYS_NO_PATHCONV là /dashboard bị đổi thành đường Windows

# xem trước / gửi thư báo cáo (App Password ở backend/.env, thuộc sonthaiha07@gmail.com)
EMAIL_CHE_DO_THU=1 python manage.py thu_email --toi ai@example.com
python manage.py thu_email --toi ai@example.com --lop 1 --em 9    # dữ liệu thật, chỉ đọc

# hồ sơ gửi TopHSA
python scripts/kiem_ke_san_pham.py --ra ho_so.json --md BAO-CAO-TRANG-THAI.md
cd frontend && node ../scripts/ho_so_tophsa.mjs ../ho_so.json "../docs/Ho so san pham PE_HSA.pdf"

# lược đồ: mục nào của legacy_schema.sql đã tới Neon (thêm § mới thì thêm dòng MUC)
cd backend  && ./.venv/Scripts/python.exe manage.py kiem_luoc_do

# header bảo mật + CSP, đo HAI chiều (máy: next start -p 3100; production: PE_URL=https://pe-hsa.vercel.app)
PE_TOKENS=.the/tokens_ad.json node scripts/do_dau_bao_mat.mjs

# trước MỖI commit — phải rỗng
git diff --cached --name-only | grep -i "\.env$"
```

`master` = deploy production ngay (Render autoDeploy). Gộp vào `master` khi anh
Sơn nói; hiện anh đã cho phép merge trực tiếp cho các đợt sửa. Đẩy `erp` tự do.

## Trạng thái ngay lúc bàn giao — 14/09/2026, cuối ngày

- **Production**: Vercel `pe-hsa.vercel.app` + Render đều đã nhận bản vá
  bảng xếp hạng (`e93c66c`, xác nhận 18:32 bằng thẻ học viên thật); Render
  `pe-hsa-backend` khoẻ (0,35 s/lượt khi thức) nhưng **vẫn ngủ đông, dậy mất
  71–87 s**. Đã thử nghiệm đúng cảnh ấy trên production (vòng 16b): Vercel giữ
  hàm ≥ 71 s, trang chảy (`/dashboard`) và trang chặn đều về đủ nội dung —
  dựng ở máy chủ không làm cảnh ngủ tệ hơn; hết hẳn vẫn cần **A1** của anh.
- **CSDL**: 5 tài khoản, 1 lớp (3 học viên đang học), 1 đợt, 16 buổi (15/09–
  05/11), 0 điểm danh, 0 bài tập, 0 link báo cáo. Dữ liệu thử của mọi lượt rà
  trong ngày đã xoá, đếm 9 bảng khớp mốc đầu phiên. `admin_audit` có thêm các
  dòng THẬT do lượt rà tạo (giao/xoá bài, phát hành/thu hồi link) — để nguyên.
- **Cổng chất lượng (14/09)**: pytest **537/537** (một ERROR thoáng qua, chạy
  lại xanh) · **24/24 unit Node (đính chính: bản đầu ghi 25/25; 25 tệp là sau vòng 18)** · giao diện 22 trang × 2 khổ = 0/0/0/0 · eslint
  / tsc / ruff / build sạch · hiệu năng **6/6 màn đạt** (Trang của tôi LCP 1,9–
  2,4 s, CLS 0,007; còn cảnh báo 2.111 nút DOM).
- **Trần tầng cũ**: 7.076 dòng / 13 tệp (sáng 7.385 → "Học tiếp" −30 →
  "Nhiệm vụ hôm nay" −53 → "Bảng xếp hạng" −123 → thẻ số + tiến độ −103).
- Lớp 1: 16 buổi T3/T5 19:30 **từ 15/09** (ngày mai), ngày thi 06/12/2026.
- Commit ngày 14/09: vòng 10–21; xem `git log --since=2026-09-14` cho hash
  cuối (bàn giao này viết trước commit cuối của vòng 21). **26 unit Node**
  (thêm `gio-vn` ở vòng 21).

### Hôm nay đã làm gì (chi tiết: PROGRESS vòng 10–24)

- **T18 mức 2 — zod cho MỌI màn đọc** (16 trang) và cho **chiều ghi**
  (`ghiJson`, 4 nút đọc phản hồi). Máy chủ đổi tên khoá thì màn hình nói ra,
  không im. `lib/kiemDang.ts` là bộ luật chung hai phía.
- **Nhật ký** ghi phát hành/thu hồi link báo cáo phụ huynh và gửi cả lớp.
- **Trang của tôi**: bỏ Font Awesome khỏi trợ lý AI (SVG riêng), `latin-ext`
  vào phông, hai khối đầu ("Lớp của bạn", "Học tiếp") dựng ở MÁY CHỦ và chảy
  qua Suspense với khung chờ đúng chiều cao, máy chủ đưa luôn hai phản hồi
  xuống tầng cũ (15 → 11 lượt API). `renderContinue` rời `dashboard.js`.
- **Rà luồng HỌC VIÊN đầu-cuối** trên dev: tìm ra **học viên không nộp được
  bài / giảng viên không chấm được (415 — thiếu Content-Type ở `apiFetch`)**
  và màn bài học đổ lỗi cho máy chủ khi em chưa ghi danh. Cả hai đã vá.
- **Tối (vòng 17–20):** rà cả **bốn vai trên PRODUCTION** trước buổi học
  15/09 — đúng như dev, hai bản vá đã lên. "Nhiệm vụ hôm nay" và "Bảng xếp
  hạng" sang React máy chủ/client. Phát hiện `zod` đầy đủ ở mã trình duyệt
  làm gói JS phình — đo A/B bằng thước đã sửa: Thi thử **956 → 608 kB** giải
  nén khi đổi sang `zod/mini` (nay có phép kiểm chặn). **Bảng xếp hạng
  xếp cả nhân viên** — quản trị viên từng hạng 1 trên production; nay chỉ học
  viên (`chi_hoc_vien`), nhân viên xem thì không có hạng. Câu hỏi sản phẩm
  về tên thật học sinh cấp 3 trên bảng: **C6** trong `VIEC_CUA_ANH.md`.
  Vòng 21: hàng bốn thẻ số + dải tiến độ ba hợp phần sang React máy chủ, dùng
  chung hai lượt API với "Học tiếp" qua `cache()` (`lib/duLieuHsa.ts`); "hôm
  nay" của dải 7 ngày tính theo `Asia/Ho_Chi_Minh` (`lib/gioVN.ts`) — máy chủ
  Vercel chạy UTC. **Trang của tôi nay chỉ còn tầng cũ cho: lộ trình rút gọn,
  nhật ký/mục tiêu tuần, chuông thông báo, và tám "trang" SPA ẩn.**
- **Thước đo tự sửa**: `do_hieu_nang` làm nóng + trung vị 3 lượt + tắt bộ đệm
  (số cũ 2,7 s và 0,6 s đều ảo); ba phép kiểm backend đếm tổng `admin_audit`
  nay lọc theo `actor_id` (bảng thật dùng chung, đỏ khi có người thao tác
  song song); `bieu-tuong-khop` bắt tên `BieuTuong` không có hình; cột JS
  của `do_hieu_nang` **chỉ đếm được khoảng MỘT tệp mỗi trang từ lâu** (báo
  "222 kB" cho màn thật 529 kB) — nay chờ đọc xong, in số lượt hỏng, ghi rõ
  byte giải nén. Mọi số JS(kB) trong PROGRESS trước 14/09 tối: chỉ so tương đối. **Đừng đo
  hiệu năng khi bộ pytest đang chạy** — cùng máy, số nhiễu cả LCP lẫn JS.
- **Khuya (vòng 22) — tổng duyệt hạ tầng.** `next` 16.2.11 dính **hai lỗ
  CRITICAL** mà không cửa kiểm nào hỏi tới → 16.3.5, và CI nay chạy `pnpm audit
  --prod` + `pip-audit`. Vercel **không gửi header bảo mật nào** (chỉ HSTS) →
  `next.config.ts` gửi CSP + nosniff + X-Frame-Options + Referrer-Policy +
  Permissions-Policy + COOP, tắt `X-Powered-By`. `scripts/do_dau_bao_mat.mjs`
  đo hai chiều (cho phép thứ sản phẩm dùng / chặn thứ kẻ tấn công cần), đã đỏ
  đúng 9 mục trên production cũ. `do_giao_dien` đếm thêm vi phạm CSP. Luật
  eslint mới của Next 16.3 → `lib/dieuHuong.ts::taiTrang` cho 12 lần tải lại
  cả trang có chủ ý. **Phát hiện đắt nhất vòng: GitHub Actions chưa từng chạy
  một bước nào** (243/244 lượt, khoá thanh toán; lượt còn lại là Dependabot) → A0. Proxy `/api/*` thôi chép
  CSP/X-Frame-Options của Django (production lộ ra, máy không thấy).
- **Vòng 23:** `src/middleware.ts` → `src/proxy.ts` theo Next 16 (hàm `proxy`, gỡ
  `runtime`). Kiểm bằng luồng làm mới phiên CHẠY THẬT trước/sau, không bằng tên
  tệp. Một commit thiếu nửa (`39dbe93`) lên master vì `git add` huỷ cả lệnh khi
  gặp đường dẫn đã đổi tên — Vercel build hỏng, production không bị ảnh hưởng.
- **15/09 (vòng 24) — kiểm kĩ lại:** ba THƯỚC ĐO sai đã sửa (mục CHẶN của
  `do_dau_bao_mat` chấp nhận mất mạng; eval đo qua DevTools thì Chromium không chặn —
  phải đo từ `<script>` của chính trang; phép kiểm bài thật nhầm `lessons.id` với
  `sort_order`). Production gỡ `'unsafe-eval'`: đồ thị bài học do máy chủ tính
  (`lessons/do_thi.py`). A/B hiệu năng cùng lúc: sau nâng Next, "Trang của tôi" chậm
  thêm ~0,2 s ở phía trình duyệt, máy chủ như nhau. **Phát hiện: production nhận JWT
  ký bằng khoá trong `backend/.env` → A6.**

## Việc đang chờ, không ai làm được thay

Xem bảng đầu `docs/VIEC_CUA_ANH.md`. Sáu việc chặn: **A0 gỡ khoá thanh toán GitHub —
CI, sao lưu, giữ ấm CHƯA TỪNG CHẠY lượt nào (đo 14/09)** · **A6 tách khoá ký production
khỏi máy dev (đo 15/09: thẻ cấp ở máy được production nhận)** · A1 giữ ấm · A2 bí mật proxy
(mọi người chung một xô đăng nhập) · A3 nhánh Neon cho CI (chỉ có nghĩa sau A0)
· B1 một lớp thật.

## Việc tôi làm tiếp được ngay (không cần anh)

*Xong 13–14/09:* ~~sao lưu CSDL tự động~~ (chờ A5) · ~~khai cổng tường minh 60
view~~ · ~~nhập liên hệ phụ huynh~~ · ~~sinh lịch cả kỳ + ngày nghỉ~~ · ~~bảng
"Việc hôm nay"~~ · ~~khoá liên hệ phụ huynh (C5)~~.

~~Rà luồng trợ giảng đầu-cuối~~ (14/09, vòng 6) · ~~T18 mức 2~~ (vòng 10, 14) ·
~~rà luồng học viên đầu-cuối~~ (vòng 13) · ~~LCP Trang của tôi~~ (vòng 11–16).

**Ba hướng đã đưa anh Sơn chọn tối 14/09; anh bảo dừng tổng kết — phiên sau
HỎI LẠI trước khi làm:**
1. *Dựng lười 8 "trang" SPA cũ* — Trang của tôi dựng sẵn cả 9 tab (2.111 nút,
   8 tab `display:none`) nên hydrate ~1,6 s; dựng tab khi bấm tới lần đầu qua
   một cầu `window.__moTrang(page)` mà `main.js::navigate` chờ. Đo trước/sau.
2. *Chuyển tiếp các khối còn lại sang React máy chủ* (nhiệm vụ hôm nay, bảng
   xếp hạng, thông báo) theo khuôn `HocTiep`/`LopCuaToiNguon`.
3. *Rà lại 4 vai trên PRODUCTION* (`pe-hsa.vercel.app`) trước/ngay sau buổi
   học đầu 15/09 — tài khoản thử, rà xong xoá.
Ngoài ra: bộ nhập kết quả thi từ PDF (chờ B4); T40 chỉ còn đặt `REDIS_URL`.

**Hạ tầng còn lại sau vòng 22** (chi tiết cuối mục vòng 22 trong PROGRESS):
~~`middleware.ts` → `proxy.ts`~~ (vòng 23) · ~~gỡ `'unsafe-eval'`~~ (vòng 24,
máy chủ tính điểm đồ thị) · gom cấu hình gunicorn về một chỗ
(`render.yaml` và `gunicorn.conf.py` đang ghi số khác nhau).

**Cân nhắc rồi bỏ (đừng làm lại):** gỡ Font Awesome khỏi màn bài học — nội
dung 76 bài trong CSDL gọi 190 tên biểu tượng; đó là phụ thuộc tầng nội dung.
Cho tầng JS cũ chạy trước hydrate — React dựng lại và xoá DOM tầng cũ vừa ghi,
không đều (đã thấy bằng mắt qua lỗi #418 ở vòng 15).

**Cách rà một vai trên trình duyệt thật** (dùng lại; từ 14/09 anh cho GHI thật
trên đối tượng vứt đi vì đây là mock production): tạo tài khoản thử qua API
quản trị → **đăng nhập THẬT bằng mật khẩu tạm máy chủ sinh** (đổi mật khẩu →
bị đá về `/login?vua-doi-mat-khau=1` → đăng nhập lại là CÓ CHỦ Ý) → Playwright
ghi lại mọi lời gọi không-GET và mọi phản hồi ≥ 400 → xoá bằng kịch bản tự liệt
kê khoá ngoại (kể cả `token_blacklist_*`), đếm 9 bảng trước/sau. Hai bẫy của
thước: `textContent({timeout})` trả rỗng ngay khi phần tử có mặt (đợi CHỮ bằng
vòng lặp); màn `/login` cũng chứa "TopHSA" nên phải chắc URL không rơi về
`/login` trước khi so chữ.

## Bài học đắt nhất ba tuần qua

1. **Chú thích sai nguy hiểm ngang mã sai.** `gui()` ghi "không ném ngoại lệ"
   mà ném — một tên học viên có xuống dòng làm hỏng lượt gửi của 24 em còn lại.
2. **Bộ đo tự viết phải đối chiếu với bộ đo đã có** trước khi tin. Bộ kiểm kê
   đếm "0 đường chỉ cần đăng nhập" khi công cụ cũ đếm 60 — sai cách phân loại.
3. **Chạy trên dữ liệu thật lộ ra thứ dữ liệu mẫu giấu.** "Điểm thi thử trung
   bình: 0%" cho một em thi đúng một lần — số đúng, chữ sai.
4. **Mở tệp ra nhìn.** Ba lỗi bố cục PDF không hiện trong chữ trích xuất.
5. **(14/09) Phép kiểm backend xanh không nói gì về giao diện.** Cả tính năng
   bài tập chết qua giao diện (415) trong khi 537 phép kiểm xanh — chúng gọi
   thẳng view với `format='json'`. Chỉ đi thật bằng trình duyệt mới thấy.
6. **(14/09) Thước tự viết nói dối ba lần một ngày** — đo màn đầu trong trình
   duyệt lạnh, đọc DOM trước khi toast hiện, đếm tổng bảng dùng chung. Mỗi số
   báo ra phải hỏi: thước có thể nói dối theo hướng nào?
7. **(14/09) Tối ưu phải đo lại ngay** — dựng ở máy chủ không Suspense làm LCP
   xấu đi từ 2,5 lên 4,3 s; không đo thì đã đẩy lên production như một "tối ưu".
