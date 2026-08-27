# Chi tiết công việc — Sprint 1

Tài liệu này đi kèm [CONG_VIEC_SPRINT1.csv](CONG_VIEC_SPRINT1.csv). File CSV để theo dõi
tiến độ; **file này để hiểu việc mình làm**. Mỗi việc có: bối cảnh (vì sao tồn tại), file
và lệnh cụ thể, các bước gợi ý, cạm bẫy đã biết, và tiêu chí Xong đo được.

Đọc [BAN_GIAO_2026-08-24.md](BAN_GIAO_2026-08-24.md) trước. Chỗ nào tài liệu này mâu thuẫn
với mã nguồn thì **mã nguồn đúng** — báo lại để sửa tài liệu.

**Quy ước đọc:** đường dẫn tính từ gốc repo. Lệnh giả định bạn đang ở gốc repo trừ khi có
`cd`. Ước lượng tính theo mức người mới vào dự án.

---

## Trước tất cả: dựng môi trường (ONB-01 … ONB-05)

Ai cũng làm, ngày đầu tiên, 1 ngày.

```bash
git clone https://github.com/PCBoiz/PE_hsa && cd PE_hsa

# ── Backend ──
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
# Xin file .env từ anh Sơn (KHÔNG có trong repo, KHÔNG được commit)
.venv/Scripts/python manage.py runserver 9000 --noreload
#                                              ^^^^^^^^^^ BẮT BUỘC
# Thiếu --noreload thì autoreload chạy 2 tiến trình → 2 luồng keep-warm
# cùng ping Neon, tốn kết nối và log rối.

# ── Frontend (terminal khác) ──
cd frontend
pnpm install
pnpm dev --port 3100      # 3000 hay bị dự án khác chiếm

# ── Test backend ──
cd backend && .venv/Scripts/python -m pytest -q     # phải xanh, 87 test
```

`backend/.env` phải có `ALLOWED_ORIGINS` chứa đúng cổng frontend
(`http://localhost:3100`), nếu không mọi request chết vì CORS và bạn sẽ tưởng backend hỏng.

**Cạm bẫy chung:** cho tới khi DB-01 xong, `DATABASE_URL` ở máy bạn trỏ vào **Neon
production**. Đọc thoải mái, **đừng chạy lệnh ghi/xoá nào**.

**Xong khi:** đăng nhập được ở máy mình, `pytest` xanh, và nói được `learning_events` dùng
để làm gì (xem BAN_GIAO §4).

---

# NGHĨA — Backend Dev + ML Engineer

## BE-01 · Buổi học và điểm danh · 3 ngày · P0

**Bối cảnh.** Sản phẩm đang có "lớp học" (bảng `classes`, `class_members`) nhưng **không có
buổi học**. Giảng viên TopHSA dạy lớp online theo lịch cố định (vd "Thứ 3, 5 · 19:30–21:00"
— đang lưu dưới dạng chuỗi tự do ở `classes.schedule`), nên hiện không ai biết buổi nào đã
dạy, ai đi ai vắng. Đây là mảnh còn thiếu lớn nhất để sản phẩm thành ERP thật.

**Đọc trước:** [ERP_TOPHSA_2026-08-24.md](ERP_TOPHSA_2026-08-24.md) §4 (đã đặc tả sẵn) ·
`backend/teaching/` (app mẫu, mới viết, sạch — bắt chước cấu trúc của nó) ·
`backend/sql/legacy_schema.sql` mục 27–29 (mẫu viết DDL).

**Phạm vi đợt này.** Chỉ làm **điểm danh tay**: giảng viên mở lớp → thấy danh sách buổi →
bấm điểm danh từng học viên (có mặt / vắng / vắng có phép / vào muộn). **Chưa** nối API
nền tảng họp — TopHSA chưa trả lời họ dạy trên Zoom hay Google Meet hay Zalo, và mỗi nền
tảng một kiểu lấy danh sách người tham dự. Làm phần không phụ thuộc câu trả lời đó trước
là để không phải viết lại.

**Các bước.**
1. Thêm `class_sessions` (id, class_id, session_date, starts_at, ends_at, topic, note,
   status) và `attendance` (session_id, user_id, status, marked_by, marked_at) vào
   `legacy_schema.sql` — luôn `CREATE TABLE IF NOT EXISTS`, kèm chỉ mục
   `(class_id, session_date)`. **Không dùng `makemigrations`** (mọi bảng nghiệp vụ là
   `managed = False`).
2. Chạy `python manage.py bootstrap_schema` để tạo bảng ở máy.
3. API trong `backend/teaching/views.py`, quyền dùng `can_see_class()` sẵn có ở
   `backend/common/permissions.py` — **đừng viết lại kiểm quyền bằng `if user.role ==`**,
   đó là thứ vừa được dọn đi.
4. Giao diện: thêm vào khu Giảng dạy (`frontend/public/static/js/dashboard.js`, IIFE cuối
   file). Nếu FE-07 đã chuyển khối này sang React thì phối hợp với Phương Nam.

**Cạm bẫy.**
- Ngày giờ dùng `common/clock.py` (`local_now()`, `local_today()`). `now()` của SQL là UTC,
  lệch 7 tiếng — đủ để một buổi tối thứ Ba nhảy sang thứ Tư.
- Học viên đã rời lớp (`class_members.left_at` khác NULL) **vẫn phải** xuất hiện trong điểm
  danh của các buổi trước ngày rời. Đừng lọc `left_at IS NULL` một cách máy móc.
- Một buổi có 30 học viên → đừng ghi 30 lệnh INSERT riêng. Ghi một lần nhiều dòng.

**Xong khi:** giảng viên tạo được buổi, điểm danh cả lớp, và số buổi đã đi học hiện trong
báo cáo lớp. Có test cho: giảng viên lớp khác gọi vào bị 404, học viên gọi vào bị 403.

## BE-02 · Điểm danh chảy vào dòng sự kiện · 1 ngày · P1

**Bối cảnh.** Đây là chỗ thể hiện rõ nhất vì sao kiến trúc `learning_events` đáng giá: bạn
**không phải viết lại một dòng hiển thị nào**. Ghi thêm một loại sự kiện, thế là số buổi
vắng tự động chảy vào cảnh báo sớm của báo cáo lớp, vào đường cong tiến bộ, vào hồ sơ học
viên — vì tất cả những chỗ đó đều chỉ là **cách đọc khác nhau trên cùng một bảng**.

**Đọc trước:** `backend/common/events.py` (toàn bộ, 1 file ngắn) · BAN_GIAO §4.

**Các bước.**
1. Thêm `kind='attendance'` vào từ vựng, ghi chú nghĩa của nó vào phần bình luận đầu bảng
   trong `legacy_schema.sql` (chỗ đó đang liệt kê đủ 7 `kind`, giữ cho danh sách đúng).
2. Trong luồng điểm danh của BE-01, gọi `record_event(...)` với
   `dedup_key = f'attend:{session_id}:{user_id}'`. **`dedup_key` là bắt buộc và duy nhất
   theo từng học viên** — nhờ nó, sửa lại điểm danh sẽ *cập nhật* dòng cũ chứ không đẻ dòng
   mới.
3. `event_date` = ngày của **buổi học**, không phải ngày người ta bấm nút. Hàm
   `record_event` có sẵn tham số `event_date` cho đúng tình huống này (trước đây nhiệm vụ
   ngày đã sai lệch một ngày vì lý do này).
4. Kiểm ở `backend/teaching/reports.py` xem cảnh báo sớm có nhận diện được chuỗi vắng không;
   nếu chưa, thêm ngưỡng (đề nghị: vắng 2 buổi liên tiếp → mức `high`).

**Cạm bẫy.** `record_event` được bọc savepoint riêng và **trả về `False` khi lỗi thay vì
ném exception** — cố ý như vậy để thống kê hỏng không kéo đổ việc điểm danh. Đừng "sửa" nó
thành ném lỗi.

**Xong khi:** một học viên vắng 2 buổi liên tiếp thì tự xuất hiện trong danh sách "cần chú ý
ngay" của lớp, mà bạn không sửa file hiển thị nào.

## BE-03 · Bù test cho teaching và stats mới · 1,5 ngày · P1

**Bối cảnh.** Repo có 87 test ở 11 app, nhưng **`teaching` (633 dòng) không có file test
nào**, và các endpoint mới của `stats` cũng chưa được phủ. Đây đúng là phần **nguy hiểm
nhất** nếu sai: nó quyết định giảng viên nào thấy dữ liệu học viên nào.

**Đọc trước:** `backend/conftest.py` (cách test nối DB và rollback) · `backend/stats/tests.py`
(mẫu viết test của dự án) · `backend/common/permissions.py`.

**Phải phủ, tối thiểu.**

| Tình huống | Kỳ vọng |
|---|---|
| Giảng viên gọi lớp **của mình** | 200, đúng danh sách học viên |
| Giảng viên gọi lớp **không phải của mình** | **404** (không phải 403 — không được để lộ là lớp đó có tồn tại) |
| Học viên gọi bất kỳ `/api/teach/*` | 403 |
| Quản trị gọi lớp bất kỳ | 200 |
| Quản trị tự hạ vai trò chính mình | bị từ chối |
| Đổi vai trò sang giá trị lạ | bị từ chối |
| `competency` khi học viên có **1** hoạt động ở một chủ đề | **không** trả điểm cho chủ đề đó |
| `progress-curve` khi trộn dữ liệu `source='self'` | số tự khai **không** vào đường đo được |

Hai dòng cuối là quy tắc số liệu của sản phẩm, không phải chi tiết kỹ thuật — xem
BAN_GIAO §7.

**Cạm bẫy.** Test đang chạy trên **CSDL thật**; phối hợp với Nhân (DB-01) để chuyển sang
nhánh Neon riêng trước, nếu không bạn tạo lớp giả trên dữ liệu production.

**Xong khi:** 8 endpoint của `teaching` + 6 endpoint mới của `stats` có test, CI xanh.

## ML-01 · Đặc tả và baseline dự đoán điểm HSA · 3 ngày · P2

**Bối cảnh.** Đây là **nghiên cứu**, không phải tính năng — đừng vội đưa lên sản phẩm. Câu
hỏi cần trả lời: *với dữ liệu đang có, có dự đoán nổi điểm thi HSA thật không, và còn thiếu
gì?* Trả lời trung thực "chưa đủ dữ liệu, cần thêm X" là một kết quả **hợp lệ và có giá
trị**, không phải thất bại.

**Dữ liệu bạn có.** Bảng `learning_events` — mỗi dòng một hoạt động, có `kind`, `course_id`,
`topic`, `score`/`max_score`, `minutes`, `occurred_at`, `source`. Cách chấm năng lực hiện
tại nằm ở `backend/stats/competency.py` (trọng số theo nguồn, suy giảm nửa đời 45 ngày) —
đọc để hiểu sản phẩm **đang** ước lượng năng lực thế nào trước khi đề xuất cách khác.

**Đặc trưng gợi ý.** Năng lực từng chủ đề · số bài đã học · số đề đã làm · độ đều đặn (số
ngày hoạt động / số ngày kể từ khi vào học) · tốc độ (phút mỗi bài) · xu hướng điểm mock.
**Nhãn:** điểm `mock` gần nhất, hoặc điểm thi thật nếu TopHSA cung cấp được.

**Cảnh báo phải nói rõ trong báo cáo.**
- Dữ liệu hiện tại **rất nhỏ** (5 tài khoản, phần lớn là tài khoản thử). Mọi con số độ chính
  xác lúc này đều vô nghĩa — nêu rõ cần bao nhiêu học viên thật để có ý nghĩa.
- Không trộn `source='self'` (tự khai) vào đặc trưng cùng với số đo được, hoặc nếu có trộn
  thì phải tách thành hai đặc trưng riêng.
- Điểm mock trong DB đang là 0% ở nhiều lượt — kiểm xem đó là dữ liệu thử hay lỗi chấm
  trước khi dùng làm nhãn.

**Xong khi:** một notebook chạy được trên dữ liệu đã ẩn danh + tài liệu 1–2 trang nêu: dùng
được đặc trưng nào, baseline sai số bao nhiêu, **thiếu dữ liệu gì**, và đề nghị làm gì tiếp.

---

# NHÂN — DB Design + AI Engineer + Backend Dev

## DB-01 · Tách CSDL dev khỏi production · 1,5 ngày · P0 · làm trước tất cả

**Bối cảnh.** `DATABASE_URL` ở máy lập trình và `DATABASE_URL` trên Render **đang trỏ cùng
một cơ sở dữ liệu Neon**. Nghĩa là: ai chạy `manage.py` ở máy là ghi vào dữ liệu thật; và
`backend/conftest.py` cho **bộ test** chạy trên chính DB đó (có rollback cuối mỗi test,
nhưng rollback không cứu được một lệnh `bootstrap_schema` hay một script sai). Một người thì
còn kiểm soát được. **Năm người mới vào thì không.** Đây là việc chặn cả nhóm — làm xong
trước rồi hãy làm việc khác.

**Cách làm (Neon branching).** Neon cho tạo *nhánh* cơ sở dữ liệu kiểu copy-on-write: nhánh
mới có toàn bộ dữ liệu tại thời điểm tách, gần như không tốn thêm dung lượng, và ghi vào
nhánh không chạm nhánh chính.

**Các bước.**
1. Neon Console → project pe_hsa → Branches → tạo `dev` và `ci` từ `main`.
2. Lấy chuỗi kết nối **có `-pooler`** và `sslmode=require` của từng nhánh.
3. Mỗi người đổi `backend/.env` → `DATABASE_URL` = nhánh `dev`.
4. GitHub → repo Settings → Secrets → đổi `DATABASE_URL` của CI sang nhánh `ci`
   (`.github/workflows/ci.yml` đang đọc secret này).
5. Cập nhật [DEPLOY.md](../DEPLOY.md) và [BAN_GIAO_2026-08-24.md](BAN_GIAO_2026-08-24.md)
   §2: nêu rõ nhánh nào dùng ở đâu, và **cách làm mới nhánh dev** khi dữ liệu lệch quá xa.
6. Kiểm chứng: ghi một dòng ở máy → vào Neon xem nhánh `main` **không** đổi.

**Cạm bẫy.**
- Vẫn phải dùng endpoint `-pooler`; `workers × DB_POOL_MAX` không được vượt trần kết nối
  của Neon.
- Đừng đổi `DATABASE_URL` trên Render — production giữ nguyên nhánh chính.
- Nhánh dev sẽ dần lệch dữ liệu so với production; viết luôn cách tạo lại nhánh, đừng để
  nửa năm sau không ai nhớ.

**Xong khi:** chạy lệnh ghi ở máy không còn chạm dữ liệu thật · CI chạy trên nhánh riêng ·
tài liệu đã sửa · cả 5 người đã đổi `.env`.

## AI-01 · Trợ lý AI trích dẫn được bài học · 3 ngày · P1

**Bối cảnh.** Trợ lý AI (DeepSeek) hiện đã đọc được hồ sơ thật của học viên — năng lực từng
chủ đề, nhật ký 14 ngày, kết quả thi thử — nhờ `backend/chatbot/profile.py` nạp vào system
prompt. Nhưng nó **không biết nội dung 76 bài**, nên khi học viên hỏi kiến thức thì nó trả
lời bằng kiến thức chung của mô hình: đúng thì cũng lệch cách trình bày của giáo trình, sai
thì học viên tin nhầm. Việc này cho nó **dẫn nguồn**: "phần này ở Bài 12 — Hàm số bậc hai,
mục Lý thuyết".

**Đọc trước:** `backend/chatbot/views.py` và `profile.py` (cách prompt đang được ghép, có
cache 5 phút) · `docs/NHAP_GIAO_TRINH.md` (cấu trúc một bài) · `lessons.content_json` trong
DB.

**Hướng đề nghị (từ rẻ tới đắt — thử theo thứ tự này).**
1. **Tìm kiếm toàn văn của Postgres** trên `content_json` (tiếng Việt, `unaccent` + `tsvector`).
   76 bài là tập rất nhỏ; nhiều khả năng đã đủ tốt và không thêm hạ tầng nào.
2. Nếu chưa đủ: nhúng vector từng *thẻ lý thuyết* (không phải cả bài — bài quá dài làm loãng),
   lưu ngay trong Postgres.
3. Chỉ khi cả hai không đạt mới bàn tới dịch vụ vector riêng — thêm hạ tầng là thêm thứ phải
   nuôi.

**Ràng buộc.**
- Mỗi vòng truy vấn Neon ≈ 245 ms. Trợ lý đang phải chờ sẵn nhiều thứ, **đừng thêm 5 truy
  vấn** cho mỗi câu hỏi; gộp lại và cân nhắc cache như `profile.py` đang làm.
- Hỏi thứ **ngoài** giáo trình thì trợ lý phải **nói thẳng là không có trong bài**, không
  được bịa số bài. Đây là tiêu chí Xong quan trọng nhất — đã có tiền lệ trợ lý nói sai về dữ
  liệu học viên, và mỗi lần như vậy là mất niềm tin.
- Giữ nguyên giọng tiếng Việt và cách xưng hô hiện tại.

**Xong khi:** hỏi 10 khái niệm bất kỳ lấy từ giáo trình → dẫn đúng bài ở ít nhất 8 câu; hỏi
3 thứ ngoài giáo trình → cả 3 lần đều nói không có, không bịa.

## DB-02 · Thiết kế bảng giao bài và nộp bài · 2 ngày · P1

**Bối cảnh.** Giảng viên hiện không giao được bài tập về nhà qua hệ thống. Đây là **thiết
kế**, chưa code API — vì có một câu hỏi chưa ai trả lời: **TopHSA có chấm tự luận bằng tay
không?** Nếu có, phải có luồng nộp file/ảnh + giao diện chấm + thang điểm; nếu không, chỉ
cần trắc nghiệm tự chấm và mọi thứ đơn giản hơn nhiều. Đừng đoán — thiết kế cả hai nhánh và
đánh dấu rõ chỗ nào phụ thuộc câu trả lời.

**Đọc trước:** [ERP_TOPHSA_2026-08-24.md](ERP_TOPHSA_2026-08-24.md) §5 · cách `quizzes` đang
chấm trắc nghiệm · `legacy_schema.sql` mục 26 (mẫu bình luận: **giải thích vì sao**, không
chỉ liệt kê cột).

**Phải quyết và ghi rõ lý do.**
- Giao cho **lớp** hay cho **từng học viên**? (Đề nghị: cho lớp, có ngoại lệ theo cá nhân.)
- Nộp muộn: chặn, hay nhận và đánh dấu muộn? (Đề nghị: nhận + đánh dấu — dữ liệu thật quý
  hơn kỷ luật giả.)
- Nộp lại nhiều lần: giữ lần cuối hay giữ hết? (Đề nghị: giữ hết, hiển thị lần cuối.)
- Bài đã chấm có đẻ `learning_events` không? (Đề nghị: **có**, `kind='assignment'` — cùng lý
  do như BE-02.)

**Xong khi:** DDL idempotent trong `legacy_schema.sql` + tài liệu luồng giao → nộp → chấm →
trả điểm, trong đó **đánh dấu rõ** phần nào đang chờ TopHSA trả lời.

## DB-03 · Nhật ký kiểm toán và chính sách quyền riêng tư · 1,5 ngày · P2

**Bối cảnh.** Giảng viên xem được nhật ký học của học viên — kể cả những dòng học viên tự
viết về việc học của mình. Học viên **chưa từng được cho biết điều đó**. Trước khi mở rộng
ra phụ huynh (mục tiêu sau), phải có hai thứ: một là ghi lại ai đã xem gì, hai là nói với
học viên chuyện đó bằng tiếng người.

**Đọc trước:** [ERP_TOPHSA_2026-08-24.md](ERP_TOPHSA_2026-08-24.md) §8 ·
`backend/teaching/views.py` (các điểm cần ghi log).

**Các bước.**
1. Bảng `audit_log` (actor_id, action, target_type, target_id, class_id, at, meta) + chỉ mục
   `(target_type, target_id, at DESC)`.
2. Ghi log ở các endpoint `teaching` đọc dữ liệu cá nhân — nhất là xem hồ sơ một học viên.
3. Viết chính sách bằng tiếng Việt dễ hiểu: giảng viên thấy được gì, không thấy được gì, và
   học viên có quyền gì. **Không viết kiểu điều khoản pháp lý** — người đọc là học sinh 17
   tuổi.
4. Hiện một dòng ngắn ngay trên khối nhật ký của học viên: "giảng viên lớp bạn xem được
   mục này".

**Cạm bẫy.** Log không được làm chậm đường đọc chính. Ghi log lỗi thì **không** được làm hỏng
request — dùng cùng kiểu savepoint như `common/events.py`.

**Xong khi:** mở hồ sơ một học viên → có dòng log; học viên nhìn thấy dòng thông báo; có tài
liệu chính sách.

---

# PHƯƠNG NAM — Frontend Dev

## FE-02 · Bộ component lõi · 3 ngày · P0 · chặn Trí Thành, làm sớm nhất

**Bối cảnh.** Frontend hiện là **vỏ Next.js bọc JavaScript thuần**: 15.668 dòng trong
`frontend/public/static/js/`, riêng `dashboard.js` **4.173 dòng**. Mỗi tính năng mới lại nối
thêm một IIFE vào cuối file đó, và mỗi khối tự chế lại thẻ, nút, bảng của riêng nó. Hệ quả
trực tiếp cho nhóm: **ba frontend dev không thể làm song song trong một file 4.000 dòng**.
Bộ component này là thứ gỡ nút thắt đó, nên nó là việc đầu tiên và mọi việc frontend khác
chờ nó.

**Đọc trước.** `frontend/public/static/css/theme.css` (**bộ token màu — nguồn duy nhất**,
`:root` cho sáng và `body.dark` ghi đè cho tối) · `frontend/public/static/css/a11y.css`
(sàn vùng chạm) · `frontend/public/static/css/dashboard.css` (các lớp `.tc-*`, `.pl-*`,
`.jr-*` — đây chính là hình dáng bạn phải giữ) · `frontend/src/components/Topbar.tsx` (mẫu
component đang có).

**Làm gì.** Tám component: `Button` · `Card` · `Tile` (ô số thống kê) · `Table` ·
`Modal` · `Toast` · `Chip` · `EmptyState`. Dùng **CSS Modules**, mọi màu qua
`var(--token)`.

**Quyết định đã chốt, đừng đổi mà không bàn cả nhóm.**
> **Chưa thêm Tailwind ở giai đoạn này.** Hệ token đã có, đang chạy, và đã kiểm tương phản.
> Thêm framework thứ hai giữa lúc đang chuyển đổi nghĩa là nuôi hai hệ thống song song đúng
> lúc bận nhất. Cân nhắc lại **sau khi** file legacy cuối cùng biến mất.

**Ràng buộc bắt buộc** (mỗi cái là một lần đã sai và đã sửa — xem BAN_GIAO §7):
- Vùng chạm ≥ 44×44 với con trỏ thô, ≥ 24×24 với mọi con trỏ; ô nhập cỡ chữ ≥ 16px (nhỏ hơn
  là iOS tự phóng to trang).
- Lưới dùng `minmax(0, 1fr)`, **không** `1fr` — nội dung dài sẽ làm tràn ngang.
- Không hex cứng. Không emoji làm icon (đã có bộ SVG ở
  `frontend/public/static/js/icons.js`).
- Mỗi component phải đúng ở **cả hai theme**. Kiểm bằng cách bật/tắt `body.dark`.

**Xong khi:** 8 component có props rõ ràng, chạy đúng ở cả sáng và tối, **và đã thay được ít
nhất một chỗ dùng thật** (không phải chỉ nằm trong thư mục chờ). Đợi FE-01 xong thì đối
chiếu ảnh chuẩn để chắc chắn không lệch pixel.

## FE-03 · Chuyển trang Quản trị sang React · 3 ngày · P1

**Bối cảnh.** `frontend/public/static/js/pages/admin.inline.js` — 678 dòng JS thuần, nạp qua
`LegacyScripts` từ `frontend/src/app/(standalone)/admin/page.tsx`. **Chọn trang này đi đầu
là có tính toán:** nó nhiều thao tác CRUD nhất (học được nhiều về cách chuyển đổi) nhưng ít
người dùng cuối nhìn thấy nhất (vỡ thì hậu quả nhẹ). Đây là bài tập để cả nhóm rút ra quy
trình chuyển đổi cho các trang sau.

**Trang này gồm:** quản lý khoá học · quản lý bài học · soạn nội dung bài · **lớp học** ·
**học viên trong lớp** · **tài khoản & vai trò** (ba mục cuối mới thêm 24/08).

**Cách làm.**
1. Đọc `admin.inline.js` hết một lượt, ghi ra các global và phần tử DOM nó phụ thuộc.
2. Chuyển từng mục sang component, dùng bộ FE-02. Gọi API qua `frontend/src/lib/api.ts`
   (`apiFetch` — đã tự gắn JWT), **không** gọi `fetch` trần.
3. Xoá `admin.inline.js` và bỏ nó khỏi mảng `srcs` của `LegacyScripts` **ngay trong cùng
   PR**. Để bản cũ nằm lại "cho chắc" chính là cách sinh ra file 4.000 dòng thứ hai.
4. Đối chiếu ảnh chuẩn của FE-01 trước và sau.

**Cạm bẫy.**
- Xoá lớp học sẽ mất luôn danh sách thành viên — hộp xác nhận hiện đang nói rõ điều đó,
  **giữ nguyên lời cảnh báo**.
- Cho học viên rời lớp là đánh dấu `left_at`, **không xoá dòng**. Học viên nghỉ giữa chừng
  vẫn phải còn trong báo cáo của kỳ đó.
- Danh sách thành viên đang đọc qua `/api/teach/classes/<id>` (quản trị xem được mọi lớp) —
  cố ý dùng lại endpoint có sẵn thay vì đẻ thêm endpoint chỉ để liệt kê.

**Xong khi:** trang Quản trị chạy hoàn toàn bằng React · `admin.inline.js` đã xoá khỏi repo ·
ảnh so sánh không lệch · thao tác được đủ 6 mục ở trên.

## FE-07 · Chuyển khối Giảng dạy sang React · 2,5 ngày · P1

**Bối cảnh.** Khối bảng điều khiển lớp trong `dashboard.js` (tìm phần `tc-*`) và CSS ở
`dashboard.css`. Đây là màn hình **mật độ cao** — giảng viên quét mắt tìm "ai cần gọi điện
hôm nay" — khác hẳn màn học viên (thoáng, mỗi lúc một việc). **Giữ nguyên sự khác biệt đó**,
đừng đồng bộ hoá hai bên cho "nhất quán".

**Vì sao giao cho bạn:** nó nhiều bảng nhất, nên là chỗ thử component `Table` của chính bạn
trước khi các trang khác dùng theo.

**Đọc trước:** `backend/teaching/reports.py` (hiểu từng con số nghĩa là gì trước khi hiển thị
lại) · phần `.tc-*` trong `dashboard.css`.

**Giữ đúng:**
- Ô cảnh báo **chỉ đổi màu khi số > 0**. Một bảng lúc nào cũng đỏ thì mắt bỏ qua, và cảnh
  báo mất tác dụng.
- Bảng bậc thành thạo (`is-l1`…`is-l4`) dùng **chung** với bản đồ năng lực phía học viên —
  một chủ đề phải trông giống nhau ở cả hai bên.
- Bảng học viên cuộn ngang **trong khung riêng** (`overflow-x` của chính nó), trang không bao
  giờ được trượt ngang.

**Xong khi:** khối Giảng dạy chạy bằng React · phần legacy tương ứng đã xoá · ảnh so sánh
không lệch · thử với tài khoản giảng viên thật (`sonthaiha07@gmail.com`, vai trò
`Giảng viên`) và tài khoản quản trị.

---

# THÁI — Frontend Dev + Web Designer

## DS-01 · Kiểm kê và viết tài liệu design system · 2 ngày · P0 · chặn FE-02

**Bối cảnh.** `theme.css` đã là nguồn màu duy nhất và làm khá tử tế: `:root` cho theme sáng,
`body.dark` ghi đè cùng tên token cho theme tối, mọi cặp màu đã kiểm tương phản ≥ 4.5:1, và
có ghi chú giải thích vì sao từng quyết định (đọc phần bình luận đầu file — nó kể lại các lần
đã sai). **Nhưng chưa ai viết ra** thang chữ, thang khoảng cách, độ nổi, các trạng thái. Thiếu
tài liệu này thì bộ component của Phương Nam sẽ tự chế lại mỗi thứ một kiểu, và sáu tháng nữa
lại có một `theme.css` thứ hai.

**Đọc trước:** `frontend/public/static/css/theme.css` (đọc **cả** phần bình luận) ·
`a11y.css` · `dashboard.css` (`.tc-*`, `.pl-*`, `.jr-*` — đọc để biết token thực sự **đang**
được dùng thế nào, không phải nên dùng thế nào).

**Đầu ra.**
1. Tài liệu `docs/DESIGN_SYSTEM.md`: bảng token màu (sáng/tối kèm ý nghĩa, không chỉ mã hex),
   thang chữ (cỡ + độ đậm + độ cao dòng đang dùng thật), thang khoảng cách, bán kính bo, độ
   nổi, và các trạng thái (mặc định / rê chuột / nhấn / vô hiệu / lỗi).
2. Một **trang HTML mẫu** hiển thị toàn bộ token, mở được ở cả hai theme — để frontend tra
   cứu bằng mắt thay vì đọc CSS.
3. Ghi lại **những chỗ đang lệch chuẩn** mà bạn phát hiện (cỡ chữ lẻ, khoảng cách không theo
   thang, màu hex cứng còn sót) — đó là danh sách việc cho sprint sau.

**Xong khi:** Phương Nam dựng được 8 component mà **không phải mở `theme.css`** lần nào.

## DS-02 · Hai phương án thị giác cho ba màn hình chủ chốt · 3 ngày · P1

**Bối cảnh.** Đây là phần "redesign" thật sự. Ba màn hình: **Trang của tôi** (dashboard),
**Bài học** (luồng 5 bước), **Lộ trình**.

**Người dùng là học sinh lớp 11–12 đang lo thi.** Hai cái bẫy ngược nhau, tránh cả hai:
- Đừng biến sản phẩm thành SaaS dashboard xám — người dùng không phải nhân viên văn phòng.
- Đừng gamify mọi thứ. Bài học là chỗ học thật; huy hiệu, streak, XP chỉ là lớp vỏ động viên
  **bên ngoài** phần học. Ranh giới này đã trả giá để rút ra ở dự án trước: gamify vào đúng
  bề mặt làm việc thì mất chất, người học thấy trò trẻ con.

Và nhớ: **hai khu vực có ngôn ngữ thiết kế khác nhau một cách có chủ đích** — màn học viên
thoáng, mỗi lúc một việc; màn giảng viên mật độ cao. Phương án của bạn phải tôn trọng sự khác
biệt đó.

**Cách trình bày (quan trọng).** Dựng bằng **HTML tĩnh dùng token thật**, không phải ảnh
mockup — vì ảnh không cho biết phương án có sống được với nội dung thật, chữ tiếng Việt có
dấu, và hai theme hay không. Mỗi phương án đủ **cả sáng lẫn tối**, kèm ghi chú lý do cho từng
lựa chọn lớn.

**Kiểm bằng nội dung thật, không phải chữ giả.** Tên chủ đề dài nhất trong giáo trình, học
viên chưa có dữ liệu (trạng thái rỗng), lớp có 1 học viên và lớp có 30 học viên.

**Xong khi:** hai phương án mở được trên trình duyệt ở cả hai theme, có ghi chú lý do, đủ để
cả nhóm bỏ phiếu chọn một.

## DS-03 · Xoá mã chết và gộp bộ icon · 1,5 ngày · P1

**Bối cảnh.** **17.086 dòng không file nào nạp** — tôi đã kiểm bằng cách dò ngược mọi tham
chiếu từ `frontend/src`:

| File | Dòng | Vì sao chết |
|---|---|---|
| `public/static/js/lesson_content_hsa.js` | 5.847 | 76 bài đã chuyển vào CSDL từ 19/08; `LessonHsa.tsx` đã bỏ nạp file này |
| `public/static/css/lesson_db_design.css` | 11.061 | Di sản sản phẩm dạy SQL cũ |
| `public/static/css/lesson.css` | 178 | Không trang nào nạp |

Thêm nữa: trang bài học nạp **FontAwesome từ CDN** (`LessonHsa.tsx`) trong khi dự án đã có bộ
SVG riêng ở `public/static/js/icons.js`. Hai bộ icon cùng lúc = tải thừa + hai phong cách nét
khác nhau trên cùng một màn hình.

**Cách làm an toàn.**
1. Với mỗi file, `grep` toàn `frontend/src` **và** toàn `public/static` (file legacy có thể
   gọi nhau) trước khi xoá.
2. Xoá **từng file một, mỗi file một commit** — sai thì `git revert` gọn.
3. Sau mỗi lần xoá, đối chiếu ảnh chuẩn của FE-01.
4. FontAwesome: liệt kê các icon đang dùng ở trang bài học, đối chiếu với `icons.js`, bổ
   sung icon còn thiếu vào bộ SVG rồi mới gỡ thẻ `<link>` CDN.

**Cạm bẫy.** `lesson_chrome.css` và `lesson_hsa.css` **vẫn đang dùng** — đừng xoá nhầm. Chỉ
xoá đúng ba file trong bảng trên.

**Xong khi:** ba file đã xoá · không trang nào vỡ (đối chiếu ảnh) · trang bài học không còn
gọi CDN icon · kích thước tải của trang bài học giảm (ghi lại con số trước/sau).

## DS-04 · Rà tương phản và vùng chạm · 1,5 ngày · P2

**Bối cảnh.** Sau khi chốt phương án thị giác, mọi màu mới phải được đo lại. Đây không phải
việc "làm cho đẹp" mà là **ngưỡng sản phẩm**: học viên dùng điện thoại là chính.

**Ngưỡng.** Tương phản chữ/nền ≥ 4.5:1 · vùng chạm ≥ 44×44 với con trỏ thô, ≥ 24×24 với mọi
con trỏ · ô nhập cỡ chữ ≥ 16px.

**Cạm bẫy đã mất thời gian một lần rồi — đọc kỹ.** Đo vùng chạm bằng Playwright thì
`elementHandle.screenshot()` **phá mô phỏng cảm ứng**: cùng một nút, lượt có chụp ảnh đo ra
26×26, lượt không chụp đo ra 44×44. **Đo trong một lượt chạy không chụp ảnh nào.**

**Xong khi:** báo cáo đo trên đủ 10 màn hình của FE-01 · không còn vùng chạm dưới sàn · không
còn cặp màu dưới 4.5:1 · các con số ghi lại được để lần sau so.

---

# TRÍ THÀNH — Frontend Dev

## FE-01 · Lưới an toàn kiểm thị giác · 2 ngày · P0

> Đây là việc Trí đã hỏi lại. Bản CSV đầu tiên viết hụt hai chỗ — dưới đây là bản đủ.

**Bối cảnh.** Sprint này cả nhóm sẽ chuyển hàng nghìn dòng JS thuần sang React. Không có ảnh
chuẩn để so thì **mỗi lần chuyển đều là đoán**: "trông vẫn thế thì chắc là được". Lưới an
toàn này phải xong **trước** khi Phương Nam và bạn bắt đầu chuyển khối, nếu không cả sprint
không ai chứng minh được mình không làm vỡ gì.

### Về `@playwright/test` — có sẵn thật, nhưng không ở chỗ Trí tìm

`@playwright/test@^1.61.1` nằm trong **`frontend/package.json`** (devDependencies), không phải
`package.json` ở gốc repo. Đã commit trên `master`.

```bash
cd frontend
pnpm install
pnpm exec playwright install chromium   # tải trình duyệt, lần đầu bắt buộc
```

### Và còn hơn thế: `frontend/e2e/` đã có sẵn — nhưng phần lớn là **mã chết**

```
frontend/e2e/
├── playwright.config.ts      ⚠ baseURL mặc định localhost:3000 (dự án chạy 3100)
├── helpers.ts                ✅ login() dùng lại được  ⚠ openLesson()/expectEngineReady() chết
├── pe-run-sql.spec.ts        ❌ CHẾT — test engine chấm SQL của sản phẩm dạy lập trình cũ
├── drag-regression.spec.ts   ❌ CHẾT — kéo thả khoá chính, "Bài 6 composite PK"
├── mobile-responsive.spec.ts ⚠ còn dùng được ý tưởng, nhưng tham chiếu tab/trang không còn
└── unit/forum-xss.test.mjs   ✅ không liên quan, để yên
```

Hai spec chết tham chiếu `PE_runSQL`, `/lesson/db_design`, "Bài 6 composite PK" — **toàn bộ
là di sản của `PE_test`, sản phẩm dạy lập trình**. TopHSA chỉ dạy HSA; thấy dấu vết lập trình
ở đâu thì đó là lỗi còn sót. `helpers.openLesson()` cũng hardcode `/lesson/db_design` và chờ
`LESSON_CONTENT['db_design']` — trên HSA nó treo tới hết thời gian chờ.

Ba thứ phải sửa trước khi viết gì mới:
1. `baseURL` mặc định `3000` → `3100` (hoặc bắt buộc đặt `E2E_BASE_URL`).
2. Tài khoản test mặc định trong `helpers.ts` là `audit@example.com` — **không tồn tại trong
   CSDL**. Xin anh Sơn một tài khoản test riêng, hoặc tạo trên nhánh Neon dev sau khi DB-01
   xong.
3. Xoá `pe-run-sql.spec.ts` và `drag-regression.spec.ts`; giữ `login()`, xoá `openLesson()`
   và `expectEngineReady()`.

### "8 trang" là con số tôi viết ẩu — đây là danh sách đúng, **10 màn hình**

| # | Màn hình | Đường dẫn | Ghi chú |
|---|---|---|---|
| 1 | Trang chủ | `/` | chưa đăng nhập |
| 2 | Đăng nhập | `/login` | chưa đăng nhập |
| 3 | Đăng ký | `/register` | chưa đăng nhập |
| 4 | Trang của tôi | `/dashboard` | mặc định sau khi đăng nhập |
| 5 | Kế hoạch | `/dashboard` → `window.navigate('plan')` | tab trong dashboard, không phải route riêng |
| 6 | Lộ trình | `/dashboard` → `navigate('roadmap')` | |
| 7 | Giảng dạy | `/dashboard` → `navigate('teach')` | **cần tài khoản vai trò `Giảng viên`** |
| 8 | Chi tiết khoá | `/courses/hsa_quantitative` | |
| 9 | Bài học | `/lesson/hsa_quantitative` | luồng 5 bước, chụp ít nhất bước 1 và bước 3 |
| 10 | Thi thử | `/mock` | |

Trang **Quản trị** (`/admin`) nên chụp thêm nếu kịp — Phương Nam sẽ chuyển nó ở FE-03 nên có
ảnh chuẩn thì tốt. Bỏ qua `/questionaire` và `/auth/*` (màn hình thoáng qua, không ổn định).

**10 màn hình × 2 theme × 2 khổ = 40 ảnh chuẩn.**

- Theme: sáng (mặc định) và tối — bật bằng `document.body.classList.add('dark')`, hoặc đặt
  `localStorage.theme = 'dark'` trước khi vào trang.
- Khổ: desktop 1400×1100 và mobile 390×844.

### Các bước

1. Dọn `frontend/e2e/` như trên.
2. Viết `frontend/e2e/visual.spec.ts`: đăng nhập → duyệt 10 màn hình × 2 theme × 2 khổ →
   `expect(page).toHaveScreenshot()`.
3. Chạy lần đầu để sinh ảnh chuẩn, commit thư mục ảnh.
4. Viết vào `README` của thư mục e2e: cách chạy, cách cập nhật ảnh chuẩn khi **cố ý** đổi
   giao diện (`--update-snapshots`), và cách đọc báo cáo lệch.

### Cạm bẫy

- **Chờ đúng thứ, đừng chờ theo giây.** Trang nạp JS legacy bất đồng bộ; `waitForTimeout`
  cho ảnh chập chờn. Chờ `typeof window.navigate === 'function'`, hoặc chờ đúng phần tử của
  khối cần chụp.
- Vài khối vẽ bằng `requestAnimationFrame` nên **treo trong chế độ headless** — nếu gặp,
  chạy `--headed` hoặc chờ đúng phần tử cuối cùng được vẽ.
- Số liệu thay đổi theo ngày (streak, "9 ngày không mở bài nào") sẽ làm ảnh lệch giả. Hoặc
  chốt dữ liệu tài khoản test, hoặc che vùng đó bằng tuỳ chọn `mask` của Playwright.
- Backend phải chạy **trước** frontend. Backend chết giữa lúc trang đang tải thì Next dev tự
  thoát và bạn sẽ tưởng test hỏng.

**Xong khi:** một lệnh chạy ra báo cáo so sánh · **cố tình đổi một màu trong `theme.css` thì
script phải báo lệch** (đây là phép thử quan trọng nhất — lưới an toàn không bắt được lỗi thì
vô dụng) · README đã viết · hai spec chết đã xoá.

## FE-04 · Bản đồ dashboard.js · 1,5 ngày · P0

**Bối cảnh.** `frontend/public/static/js/dashboard.js` — 4.173 dòng, khoảng 7 khối tính năng
nối đuôi nhau, mỗi khối là một IIFE ở cuối file. Ba người sắp cùng mổ file này. Không có bản
đồ thì sẽ đụng nhau, hoặc tệ hơn: hai người cùng sửa một global mà không biết.

**Việc của bạn là đọc và ghi lại, không sửa code.** Với mỗi khối, ghi:
- Tên khối và khoảng dòng.
- API nó gọi.
- Biến `window.*` nó tạo ra / đọc vào — **đây là chỗ dễ đụng nhau nhất**.
- ID/lớp DOM nó cần (khai ở `frontend/src/app/(base)/dashboard/page.tsx`).
- File CSS tương ứng (`dashboard.css`, `pages.css`).
- Phụ thuộc chéo sang khối khác.

**Các khối đã biết** (kiểm lại và bổ sung): tổng quan/thẻ số · bản đồ năng lực (`cmp-*`) ·
đường cong tiến bộ + sổ điểm (`cv-*`, `bk-*`) · nhật ký + mục tiêu tuần (`jr-*`) · kế hoạch
học (`pl-*`) · khu giảng dạy (`tc-*`) · lộ trình (file riêng `roadmap.js`).

**Đầu ra.** Một tài liệu ngắn trong `docs/` + đề xuất **thứ tự tách** kèm lý do. Đưa cả nhóm
xem để thống nhất trước khi ai đó bắt đầu.

**Xong khi:** đủ 7 khối, mỗi khối có đủ 6 mục trên; cả nhóm đồng ý thứ tự tách.

## FE-05 · Chuyển khối Kế hoạch sang React · 3 ngày · P0

**Bối cảnh.** Khối phức tạp nhất trong `dashboard.js` (tìm `pl-*`). Nó hiển thị kế hoạch học
sinh tự động từ nay tới ngày thi: mỗi tuần một nhóm bài, xen kẽ ba khoá, chèn bài ôn cho chủ
đề yếu. Backend ở `backend/stats/plan.py` — **đọc file đó trước khi viết giao diện**, vì có
hai quy tắc dễ vô tình phá:

1. **Tuần đã lên lịch là bất biến.** Việc chưa làm được dồn sang tuần hiện tại lúc *đọc*,
   chứ không phải ghi đè `week_start` trong CSDL. Nhờ vậy hệ thống mới đo được **độ trễ** —
   học viên chậm bao nhiêu bài so với kế hoạch gốc. Nếu bạn "tiện tay" ghi lại tuần cho gọn,
   con số độ trễ vĩnh viễn bằng 0 và không ai phát hiện ra.
2. **Trạng thái hoàn thành được suy ra từ `learning_events` lúc đọc**, không lưu cột riêng.
   Đừng thêm state hoàn thành ở phía trình duyệt rồi tự cập nhật.

**Chi tiết giao diện phải giữ.**
- Trang từng dài 7562px, đã sửa xuống 2887px bằng cách **thu gọn các tuần từ tuần thứ 7 trở
  đi**. Giữ cách thu gọn đó.
- Mục tiêu tuần có **ba trạng thái khác nhau**: chưa đặt · đặt bằng 0 · đặt số dương. Đừng
  gộp "chưa đặt" với "bằng 0" — bản cũ từng vẽ ra một cột trống vô nghĩa vì lỗi này.
- Lý do chèn bài ôn phải nói **số điểm thật và ngưỡng** ("Số học 42/100, dưới ngưỡng 60"),
  không phải câu chung chung "thấp nhất trong nhóm" — câu đó chỉ đúng với mục đầu tiên và đã
  bị sửa một lần rồi.
- Nút bỏ qua một mục phải ≥ 44×44 (bản cũ là 29px, đã sửa).

**Xong khi:** khối chạy bằng React · phần legacy đã xoá · ảnh so sánh không lệch · **độ trễ
vẫn tính đúng** (thử: bỏ trống một tuần, sang tuần sau xem con số chậm có tăng không).

## FE-06 · Chuyển khối Nhật ký và mục tiêu tuần sang React · 1,5 ngày · P1

**Bối cảnh.** Khối `jr-*` trong `dashboard.js`. Học viên tự ghi hôm nay học gì, bao nhiêu
phút, cảm thấy thế nào; và đặt mục tiêu số bài cho tuần. Backend: `backend/stats/journal.py`.

**Ranh giới quan trọng nhất — đọc kỹ.** Số học viên **tự khai** (`source='self'`) và số hệ
thống **đo được** (`source='system'`) **không bao giờ được trộn vào cùng một biểu đồ hay
cùng một phép tính**. Trộn hai loại là cách nhanh nhất giết niềm tin vào toàn bộ số liệu:
một học viên khai 300 phút rồi thấy đường tiến bộ vọt lên sẽ hiểu ngay là số này vô nghĩa,
và từ đó không tin con số nào nữa. Ranh giới này đang được giữ ở **ba nơi** (cột `source`
trong CSDL, phép tính ở backend, cách hiển thị ở giao diện) — bạn chịu trách nhiệm nơi thứ
ba.

**Mục tiêu tuần là adaptive**, không phải ô nhập trơn: hệ thống tự đề nghị một con số dựa
trên số bài còn lại, số ngày tới kỳ thi và sức chứa thời gian mỗi ngày; và khi lịch **không
vừa**, nó nói thẳng phải bỏ bớt bao nhiêu bài thay vì im lặng đặt một con số bất khả thi.
Giữ nguyên phần nói thẳng đó — nó là điểm khác biệt của sản phẩm, không phải chỗ để làm cho
"tích cực" hơn.

**Xong khi:** khối chạy bằng React · phần legacy đã xoá · số tự khai vẫn hiển thị tách bạch ·
lời cảnh báo khi lịch không vừa vẫn hiện đúng.

---

## Phụ lục — trả lời câu hỏi của Trí

**Hỏi:** *"chụp ảnh 8 trang là những trang nào, và nó ghi repo đã sẵn playwright/test mà tôi
không thấy trên repo?"*

1. **"8 trang"** là con số tôi viết mà không liệt kê — sai. Danh sách đúng là **10 màn hình**,
   xem bảng ở FE-01.
2. **`@playwright/test` có thật**, ở `frontend/package.json` chứ không phải `package.json`
   gốc. Chạy `cd frontend && pnpm install && pnpm exec playwright install chromium`.
3. **Thêm một thứ bản CSV không nói:** `frontend/e2e/` đã có sẵn config + helpers + 3 spec,
   nhưng 2 spec là di sản của sản phẩm dạy SQL cũ và không chạy được trên HSA. Dọn chúng là
   một phần của FE-01.

Gặp chỗ nào khác thiếu ngữ cảnh như thế này thì hỏi tiếp — tài liệu sai thì sửa tài liệu,
đừng đoán rồi làm.
