# Thiết kế hệ thống pe_hsa — bản as-built 27/09/2026

**Ai đọc tệp này**: người cần hiểu hệ thống đang *thật sự* được dựng thế nào — anh Sơn, một lập
trình viên mới vào, hay bên kỹ thuật của TopHSA. Tệp này mô tả **bản đang chạy trên production**
(`master` = `198dc81`), không mô tả dự định.

**Quan hệ với các tài liệu khác** — tệp này gom lại, không thay thế:

| Tệp | Trả lời câu gì |
|---|---|
| `docs/SYSTEM_DESIGN.md` (tệp này) | Hệ thống được dựng thế nào, và **vì sao từng quyết định** |
| `docs/THIET_KE_HE_THONG.md` | Vai, trang theo vai, hướng phát triển |
| `docs/KIEN_TRUC/C4.md` · `ERD.md` · `USE_CASE.md` · `LUONG_CHAM_DIEM.md` | Sơ đồ chi tiết từng lớp |
| `docs/CAU_TRUC_MA.md` · `CAU_TRUC_DU_LIEU.md` | **Tự sinh** — tệp nào thuộc miền nào, bảng nào có cột nào |
| `docs/VAN_HANH.md` | Deploy, sổ lược đồ, cổng kiểm |
| `docs/TINH_NANG_DA_LAM.md` | Người dùng bấm được gì |
| `RULES.md` | Luật bắt buộc, kèm lý do từng luật |

---

## 1 · Ràng buộc định hình mọi quyết định

Thiết kế này không tối ưu cho "quy mô lớn". Nó tối ưu cho bốn ràng buộc thật:

1. **Hạ tầng gói miễn phí.** Render free: 512 MB, ngủ sau ~15 phút không dùng (cold start 30–50 s).
   Neon free: scale-to-zero, đóng kết nối trong pool khi rỗi. Vercel hobby. → Mọi thứ phải chịu
   được việc *máy chủ vừa ngủ dậy* và *kết nối CSDL vừa chết*.
2. **Một người làm, cộng các agent.** → Kỷ luật máy đọc được (cổng kiểm, sổ lược đồ, sổ miền)
   quan trọng hơn quy ước con người phải nhớ.
3. **Dữ liệu hiện tại đều là GIẢ** — TopHSA chưa đưa dữ liệu thật nào. → Được ghi thử thoả thích,
   **nhưng hạ tầng, bảo mật, phân quyền phải làm như thật**, vì đổi sang dữ liệu thật thì không
   có đợt sửa thứ hai. Riêng **thư và tin nhắn** thì khác: ra khỏi hệ thống là không cuộn lại
   được → có hàng rào chặn ở mã, không dựa vào việc người vận hành cẩn thận.
4. **Repo CÔNG KHAI.** → Không bí mật, không khoá, không JWT, không đường dẫn mang tên tài khoản
   Windows trong mã. Có bước quét tự động canh chỗ này trước mỗi lượt đẩy.

## 2 · Bức tranh chạy

```
     Trình duyệt
         │  (cookie HttpOnly — JavaScript trên trang KHÔNG chạm được token)
         ▼
  ┌──────────────────────┐
  │  Next.js 16 · Vercel │  React 19 · Tailwind v4 · zod-mini
  │  43 trang            │  • Server Component tải dữ liệu lượt đầu
  │  /api/[...path]      │  • MỘT cửa proxy cho mọi lời gọi /api/*
  └──────────┬───────────┘     – ép tiền tố /api/ (chặn ..%2f đi xuyên sang /auth/)
             │ HTTPS + Bearer  – bóc token ra khỏi thân phản hồi, cất vào cookie
             ▼
  ┌──────────────────────┐
  │  Django 5.2 · Render │  DRF · gunicorn 2 worker × 12 thread
  │  203 cửa API         │  • SQL THUẦN (common/db.py), không ORM cho nghiệp vụ
  │  16 miền             │  • hộp chờ thư (outbox), không gửi trong lời gọi API
  └──────────┬───────────┘
             │ psycopg pool, cùng vùng us-east (RTT < 5 ms)
             ▼
  ┌──────────────────────┐
  │  Neon Postgres       │  59 bảng · 72 mục lược đồ §NN
  │  scale-to-zero       │  DDL chỉ cộng thêm, chạy lúc build
  └──────────────────────┘

  Đang chừa sẵn, chưa nối: Cloudflare R2 (tệp) · Zoom (bản ghi) · Zalo ZNS (tin nhắn)
```

### Vì sao proxy ở Next chứ không gọi thẳng Django

Token không bao giờ nằm trong tầm với của JavaScript trên trang: trình duyệt chỉ giữ cookie
`HttpOnly`, proxy mới gắn `Authorization`. Đổi lại phải trả một chặng mạng — chấp nhận được, và
nó cũng khiến tầng JavaScript cũ trong `frontend/public/static/js` gọi `/api/...` bằng đường dẫn
tương đối là chạy đúng, không cần lớp viết lại URL nào.

### Vì sao SQL thuần, không ORM

Nghiệp vụ mang sang từ bản Flask cũ (XP, streak, huy hiệu, `ON CONFLICT`) phải giữ **nguyên từng
câu SQL** để không lệch hành vi. Ba hàm trong `backend/common/db.py` là toàn bộ API: `q` (nhiều
dòng), `q1` (một dòng), `x` (ghi). Chúng trả `dict`, và **tự chịu được kết nối chết**: Neon đóng
kết nối trong pool khi rỗi, câu kế tiếp bốc phải kết nối chết và ném lỗi SSL. `q/q1/x` bắt lỗi
ấy, **huỷ cả pool** (`close_pool()` — `close()` chỉ trả kết nối chết về pool, retry lại bốc phải
cái khác) rồi thử lại. Không retry khi đang trong giao dịch, để không phá tính nguyên tử.

## 3 · Miền — modular monolith

16 miền, khai trong `scripts/so_mien.json`: lớp học · lịch · điểm danh · bài tập · chương trình ·
báo cáo · phụ huynh · hồ sơ · yêu cầu · thông báo · tài khoản · học trực tuyến · diễn đàn · thi
cử · công cụ · chung.

**Luật S4 — miền này không INSERT/UPDATE/DELETE bảng của miền khác**; cần thì gọi hàm dịch vụ của
miền sở hữu. Lý do: khi một cột đổi ý nghĩa, chỉ có một chỗ phải sửa, và chỗ ấy là chỗ hiểu cột
đó. Vi phạm còn sót được ghi thành **sổ nợ ghi chéo** (hiện 11 chỗ, mỗi chỗ có lý do viết ra) —
sổ này **chỉ được co**, và `python scripts/cau_truc.py --kiem` làm cổng canh.

Đọc bảng của miền khác thì được, nhưng nếu đã có hàm dịch vụ trả đúng số ấy thì gọi hàm.

## 4 · Lược đồ CSDL — sổ mục, chỉ cộng thêm

`backend/sql/legacy_schema.sql` là **nguồn DDL duy nhất** cho các bảng SQL thuần (`managed=False`,
`migrate` không đụng tới). Bốn luật:

1. Mục mới ghi ở **cuối** tệp, có tiêu đề `-- ── §NN · Tên (ngày) ──`. Hiện tới §74.
2. **Chỉ cộng thêm**: `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`,
   `DROP CONSTRAINT IF EXISTS` rồi `ADD`. Không `DO $$`, không `SET`.
3. `python manage.py bootstrap_schema` ghi sổ `luoc_do_da_chay` và **chỉ chạy mục mới hoặc đã
   đổi**, mỗi mục một giao dịch. Chạy hai lượt: lượt hai phải báo "0/N mục chạy".
4. Mỗi mục có một dòng kiểm trong `kiem_luoc_do.py` — `python manage.py kiem_luoc_do` phải ✓ hết.

**Chỗ này đẻ ra một tính chất quan trọng cho vận hành**: `bootstrap_schema` chạy trong
`buildCommand` của Render. Mục nào hỏng thì **build đỏ và bản cũ vẫn phục vụ** — không bao giờ có
cửa sổ mà production chạy mã mới trên lược đồ cũ.

## 5 · Phân quyền

Sáu vai: `admin` · Quản lý học vụ · Giảng viên · Trợ giảng · Học viên · Biên tập nội dung
(`backend/common/permissions.py`).

Hai luật đáng nhớ:

- **`can_see_class` là cửa duy nhất** quyết định ai xem được lớp nào. Giảng viên thấy lớp mình
  dạy, trợ giảng thấy lớp mình kèm, học vụ thấy lớp mình phụ trách, quản trị thấy hết.
- **Lớp không được xem trả 404, không trả 403.** 403 là câu trả lời "lớp này có thật, chỉ là anh
  không được vào" — nó lộ ra thứ không nên lộ. Áp cho mọi cửa buổi học, không có ngoại lệ.

`python scripts/tang_vai.py --kiem` và `backend/common/tests_ma_tran_quyen.py` quét toàn bộ tuyến
`api/admin/*` và `api/teach/*` để chắc học viên bị chặn ở mọi đường quản trị — nên **thêm tuyến
mới là tự động bị kiểm**, không cần ai nhớ.

## 6 · Thư, chuông, tin nhắn — chỗ duy nhất không cuộn lại được

Mọi thứ khác sai thì sửa dữ liệu rồi chạy lại. Thư đã gửi thì không.

- **Hộp chờ (outbox)**: lời gọi API ghi một dòng chờ gửi rồi trả về ngay; một nhịp riêng mới đẩy
  đi. Máy chủ gói miễn phí ngủ giữa lúc gửi thì thư nằm chờ, không mất.
- **Hàng rào** (`backend/notifications/hang_rao_thu.py`): chỉ gửi tới địa chỉ thử
  (`@example.com`, tài khoản e2e). Trong lúc chưa có dữ liệu thật, **hàng rào này không được
  nới** — kể cả để chạy một phép kiểm cho xanh. Phép kiểm nào cần gửi thật thì mở hàng rào ở
  phía *bộ kiểm*, không hạ hàng rào ở phía mã.
- **Nhãn loại chuông do máy chủ trả** (`backend/notifications/loai.py`), tiếng Việt của người
  dùng. Màn không tự dịch, và có bộ quét AST bắt lỗi "gửi chuông với loại chưa khai" — nếu không
  thì một mã như `assignment_new` sẽ lọt lên màn học viên.
- **Zalo ZNS**: mã đã có, chưa bật — cần pháp nhân để đăng ký Zalo OA (việc D2).

## 7 · Nền chung

| Thứ | Ở đâu | Vì sao có |
|---|---|---|
| Nhật ký kiểm toán | `common/audit.py` | mọi thao tác đổi dữ liệu ghi kèm **bản cũ** — tranh chấp "ai sửa điểm em" trả lời được |
| Dòng sự kiện học tập | `common/events.py` | bản đồ năng lực đọc từ dòng sự kiện, không đọc bảng nguồn → thêm loại hoạt động mới không phải sửa màn nào |
| Giờ Việt Nam | `common/clock.py` `local_now()` | một chỗ duy nhất biết múi giờ |
| Xuất bảng tính | `common/bangtinh.py` `ghi_xlsx` | ô chữ **không bao giờ** thành công thức |
| Hộp tham số | `common/params.py` | mọi cửa đọc tham số một kiểu |

## 8 · Kỷ luật kiểm — vì sao tin được con số

1. **Test ĐỎ trước.** Viết phép kiểm trên mã cũ, xem nó đỏ, rồi mới sửa. Một phép kiểm chưa từng
   đỏ thì không biết nó kiểm cái gì. Ngày 27/09 hai phép kiểm buổi bù **xanh vì lý do sai** suốt
   nhiều giờ — cái bắt được lỗi là một phép kiểm khác, và chỉ khi chạy cả 330 test của miền.
2. **Đột biến phải giết được.** Sửa một chỗ trong mã cho sai đi, bộ kiểm phải đỏ. Chạy bằng
   `scripts/dot_bien.py` với loạt JSON — **không** sửa tay rồi khôi phục ở lệnh sau: lệnh ấy
   không chạy nếu phiên đứt, và tệp nằm lại ở trạng thái đột biến.
3. **Test chạy trong giao dịch cuộn lại**, trên CSDL thật, và chỉ đếm dữ liệu của chính nó (CSDL
   dev dùng chung với luồng khác).
4. **Đo trên màn thật, không suy.** 15 bộ đo mở màn trong trình duyệt đã đăng nhập, **bấm chuột
   chứ không gọi API tay**, và đếm bằng số. Một tính năng chỉ được gọi là xong khi đã soi ảnh
   chụp. Mọi bộ đo gọi `chay()` của `scripts/lib/phien_do.mjs` — nó đóng trình duyệt cả khi lỗi
   lẫn khi bị Ctrl-C (đã có hôm 22 tiến trình mồ côi làm máy đứng).
5. **Cổng trước khi đẩy** (`.githooks/pre-push`, 15 bước, 153 giây): ruff · `manage.py check` ·
   compileall · guard pytest · `bootstrap_schema --kiem` · `tsc --noEmit` · eslint 0 cảnh báo ·
   `node --check` tầng JS cũ · 39 phép kiểm đơn vị Node · bản đồ · tầng vai · cấu trúc ·
   **quét bí mật** · đột biến còn sót.

## 9 · Số đo, và cách đo lại

| Đo gì | Số (27/09/2026) | Lệnh |
|---|---|---|
| Bảng | 59 | `grep -c "^CREATE TABLE IF NOT EXISTS" backend/sql/legacy_schema.sql` |
| Mục lược đồ | 72 | `grep -oE "§[0-9]+[a-z]?" backend/sql/legacy_schema.sql \| sort -u \| wc -l` |
| Cửa API | 203 | `grep -rh "    path(" backend/*/urls.py \| wc -l` |
| Trang màn | 43 | `find frontend/src/app -name page.tsx \| wc -l` |
| Phép kiểm backend | 1.262 / 101 tệp | `grep -rh "^def test_\|^    def test_" backend/*/tests*.py \| wc -l` |
| Dòng mã | 66.025 + 34.148 | `wc -l` theo `backend/**/*.py`, `frontend/src/**/*.ts{,x}` |

## 10 · Nợ đã biết — viết ra để không ai tưởng là đã xong

- **Tầng JavaScript cũ** `frontend/public/static/js` chỉ được **CO**, không được phình (có trần
  ở `e2e/unit/chot-ham-tang-cu.test.mjs`). Chạm mục học viên nào thì dời mục ấy sang React.
- **11 chỗ ghi chéo miền** còn lại, mỗi chỗ có lý do; sổ chỉ được co.
- **`teaching/views.py` trộn ba việc** (lớp + thành viên, tạo tài khoản / đổi vai, hồ sơ học viên
  cho giảng viên) — tách khi chạm.
- **Chưa nối**: R2 (tải tệp), Zoom (bản ghi tự vào buổi), ZNS. Lược đồ đã chừa sẵn chỗ
  (`nguon='r2'`), nên nối vào là việc cấu hình, không phải việc thiết kế lại.
- **Đồng hồ cửa quên mật khẩu chưa cân**: 2,04 s khi email có tài khoản so với 0,254 s khi không —
  một người đo được thời gian vẫn suy ra được ai có tài khoản. Đã chặn phần lộ rõ nhất, phần còn
  lại nằm ở 9 vòng gọi CSDL; ghi ở đây vì nó **chưa** xong, không phải đã xong.
- **Học phí, công nợ** chưa làm — đang chờ bốn câu trả lời của TopHSA (việc K2).
