# RULES — tiêu chuẩn bắt buộc cho mọi thay đổi

Áp cho **mọi** task trong `TODO.md`. Không có ngoại lệ "lần này nhỏ nên bỏ qua".

---

## 1. Kiểm chứng ở tầng NGƯỜI DÙNG, không phải tầng API

**Đây là luật đắt nhất trong tệp này, và nó ra đời từ một thất bại thật.**

Ngày 30/08/2026, một bộ kiểm chứng tự viết đạt **45/45** trong khi cả màn hình
điểm danh **chết hoàn toàn**: frontend đọc `klass` / `starts_at` / `user_id`,
backend trả `class` / `startsAt` / `userId`. Trang luôn hiện "Không mở được lớp
này" và chưa ai từng vào được. 1.212 dòng mã, hai commit, không chạy.

`tsc` xanh. `eslint` xanh. `pytest` xanh. Bộ kiểm chứng xanh. Vì:
- Bộ kiểm chứng gọi thẳng view bằng Python — đúng tầng API, không bao giờ dựng
  trang React với dữ liệu thật.
- Kiểu TypeScript là **lời tự khai** về thứ người viết *tưởng* backend trả.
  `serverJson<T>` ép kiểu mù, không kiểm gì lúc chạy.

**Luật:** mọi màn hình đụng tới phải được **mở thật trong trình duyệt, đã đăng
nhập, với dữ liệu thật, và nhìn bằng mắt** trước khi báo xong. Ảnh chụp phải
được XEM LẠI, không chỉ được tạo ra.

Phiên trình duyệt đã đăng nhập, không cần ghi CSDL: xem `PROGRESS.md` mục
"Công cụ".

## 2. Đo, đừng suy

Mọi khẳng định phải kèm số đo thật.

| Nói | Phải kèm |
|---|---|
| "nhẹ hơn" | bao nhiêu byte, đo bằng gì |
| "đủ tương phản" | tỉ số bao nhiêu, đo trên nền nào, ở bộ màu nào |
| "nhanh hơn" | bao nhiêu câu truy vấn, hoặc bao nhiêu ms, đo thế nào |
| "không ai dùng" | lệnh grep nào, chạy trên phạm vi nào |

Đã có ba lần suy sai: "FontAwesome cho 13 icon" (thật: 193) · "bảng màu đã kiểm
tương phản" (thật: 5 chỗ dưới chuẩn) · "245ms mỗi vòng gọi Neon" (thật: chỉ đúng
khi dev từ VN; production cùng vùng nên dưới 5ms).

## 3. Nghi ngờ chính mình, và nghi ngờ cả agent

Giải pháp vừa chọn là **ứng viên**, không phải kết luận. Trước khi chốt một
thiết kế: tra cách người khác giải bài toán đó, nêu ít nhất một phương án đã
cân nhắc rồi loại và vì sao.

Báo cáo của agent phải được **tự kiểm lại** trước khi tin — agent đã từng báo
sai gấp 15 lần.

## 4. Không cảnh báo nào được để lại

Trước khi báo xong một task:

```bash
cd backend  && ./.venv/Scripts/python.exe manage.py check
cd backend  && ruff check .
cd frontend && npx --yes pnpm@11.12.0 build          # gồm cả tsc
cd frontend && npx --yes pnpm@11.12.0 exec eslint src --max-warnings 0
cd frontend && for f in public/static/js/*.js public/static/js/pages/*.js; do node --check "$f"; done
```

Dòng cuối không thừa: 15 tệp JS thuần trong `public/static` **không đi qua
bundler**, nên `next build` chưa bao giờ đọc tới. Một lỗi cú pháp ở đó lên
thẳng production và đã từng làm chết cả trang quản trị.

## 5. CSDL production — chạm tối thiểu

`DATABASE_URL` trỏ vào Neon **đang dùng thật**, có tài khoản người thật.

- `SELECT`, `EXPLAIN`: thoải mái.
- `INSERT` / `UPDATE` / `DELETE`: **không**, trừ khi người dùng cho phép từng lần.
- DDL: chỉ dạng cộng thêm (`CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT
  EXISTS`), qua `sql/legacy_schema.sql` + `manage.py bootstrap_schema`.
- Cần phiên đăng nhập để kiểm giao diện → **tự cấp JWT cho tài khoản đã có**
  (`accounts.views._tokens_for`), đừng tạo tài khoản kiểm thử.

**Bẫy:** `bootstrap_schema` tách câu theo dấu `;`, nên khối `DO $$ … $$` bị xé
nát. Dùng `DROP CONSTRAINT IF EXISTS` rồi `ADD CONSTRAINT`.

## 6. Một cửa duy nhất — không được phá

| Bảng / khái niệm | Cửa duy nhất |
|---|---|
| `learning_events` | `common/events.py` (`record_event`, `forget_events`) |
| `admin_audit` | `common/audit.py` (`record`) |
| Email và số điện thoại | `common/identity.py` (`norm_email`, `norm_phone`) |
| Màu, cỡ chữ, nhịp, bo góc | `frontend/src/app/tailwind.css` → `theme.css` |
| Giờ nghiệp vụ | `common/clock.py` (`local_now`, `local_today`) — SQL `now()` là UTC, lệch 7 tiếng |

Chuẩn hoá **một phía** là tái tạo đúng cái khe vừa vá. Mọi chỗ GHI *và* mọi chỗ
TRA đều phải đi qua cùng một cửa.

## 7. Không hai nguồn sự thật

Cùng một con số hoặc cùng một luật được tính ở hai nơi thì **chắc chắn sẽ lệch**,
và không ai biết bản nào đúng. Đã xảy ra bốn lần: mã màu chép lại · trần 50 tài
khoản khai ở cả backend lẫn frontend · bộ lọc tài khoản của màn hình khác của
file xuất · ngưỡng bậc thành thạo 80/60/40 nằm ở hai chỗ trong cùng một tệp JS.

## 8. Không nuốt lỗi im lặng

`except Exception: pass`, `.catch(() => null)`, `except DatabaseError: return {}`
— mỗi chỗ như vậy phải trả lời được: **điều gì hỏng mà không ai biết?**

Một báo cáo nói "cả lớp đúng tiến độ" vì bảng hỏng còn tệ hơn một báo cáo báo
lỗi. Ô trống nói "không đọc được" luôn tốt hơn số 0 nói "ổn".

## 9. Chú thích giải thích TẠI SAO, và phải đúng

Mã nguồn này chú thích dày bằng tiếng Việt, nêu hệ quả thật và dẫn ngày tháng —
đó là điểm mạnh, giữ nguyên. Nhưng **chú thích sai còn tệ hơn không có**: đã có
chú thích khẳng định hai mô-đun dùng chung bộ lọc trong khi chúng không hề.

Sửa mã thì đọc lại chú thích quanh đó.

## 10. Ngôn ngữ trên giao diện

Người đọc là trợ giảng và học sinh cấp 3, không phải lập trình viên. Không để
lọt ra màn hình: mã lỗi, tên bảng, tên trường, chuỗi kiểu `user.password_reset`.
Câu lỗi phải nói được **cách sửa**, không chỉ nói là sai.

## 11. Trước mỗi commit

```bash
git diff --cached --name-only | grep -i "\.env$"   # phải RỖNG
```

Thông điệp commit ghi **vì sao**, không chỉ ghi *cái gì* — gồm cả lỗi tự gây ra,
để sau này đọc `git log` là hiểu được quyết định.

`master` có `autoDeploy: true` (xem `render.yaml`) nên push lên đó là **deploy
production ngay**, và `buildCommand` chạy luôn `bootstrap_schema`. Làm việc trên
nhánh khác; gộp vào `master` là một quyết định riêng, phải hỏi.

## 12. Ghi `PROGRESS.md` sau MỖI task

Không phải sau mỗi chặng. Hết hạn mức giữa chừng thì chỉ mất đúng một task.

## 13. "CI xanh" chưa phải bằng chứng — phải biết bộ kiểm CÓ CHẠY

Thêm 31/08/2026, sau khi phát hiện bộ kiểm backend đã đỏ sẵn trên `master`:
18 hỏng / 15 lỗi, và suốt cả đợt ERP không ai chạy nó lần nào vì `pytest` không
có trong venv.

Nguy hơn "fail" là **"error"**: một phép kiểm chết ở khâu dựng dữ liệu trông
giống hệt một phép kiểm chưa viết xong, nên mắt lướt qua. Sáu phép kiểm chuỗi
ngày đã ở trạng thái đó kể từ lần đổi hệ nhiệm vụ, tức tính năng lõi ấy không có
ai canh trong nhiều tháng.

**Bắt buộc:**
- Chạy `python -m pytest -q` TRƯỚC khi kết luận một thay đổi không gây hồi quy,
  và ghi lại con số đạt/hỏng — không nói "CI sẽ chạy".
- So với mốc gốc trên `master` (dùng `git worktree`) trước khi đổ lỗi cho nhánh
  mình. Nhớ xoá worktree kèm mọi bản sao `.env` trong đó.
- Phép kiểm hỏng vì **dữ liệu mẫu đổi** thì sửa phép kiểm sang kiểm HÌNH DẠNG,
  đừng ghim tên dữ liệu. Phép kiểm hỏng vì **luật sản phẩm đổi** thì viết lại
  cho khớp luật mới, ĐỪNG XOÁ — một phép kiểm khẳng định luật cũ chính là cái
  chốt giữ lại lỗ vừa bịt.


---

## §14 · Nối lệnh qua `| head`/`| tail` thì mã thoát KHÔNG còn là của lệnh đó

`npx tsc --noEmit | head -30` rồi đọc `$?` là đọc mã thoát của `head`, **luôn
bằng 0**. Ngày 31/08/2026 tôi kết luận "tsc sạch" hai lần liên tiếp trong khi nó
đang báo hai lỗi TS2783 — và một lần trong số đó chạy nền, nên cái tôi thấy chỉ
là dòng "completed (exit code 0)" của trình chạy nền.

**Bắt buộc:** với mọi lệnh mà điều mình quan tâm là ĐẠT hay HỎNG — `tsc`,
`pytest`, `build`, `flake8` — ghi ra tệp rồi mới lọc:

```
npx tsc --noEmit > /tmp/tsc.log 2>&1; echo "exit=$?"; grep ... /tmp/tsc.log
```

Cùng họ với §13: "CI xanh" không phải bằng chứng nếu chưa tự xác nhận bộ kiểm đã
CHẠY. Ở đây còn tệ hơn — bộ kiểm có chạy, có báo lỗi, và tôi đã nhìn thẳng vào
con số 0 do một lệnh khác sinh ra.

---

## §15 · Chú thích nói "đo được X" thì X phải do CHÍNH MÌNH đo, trên dữ liệu thật

Ngày 31/08/2026 tôi chép hai con số từ báo cáo của một agent tìm lỗi vào chú
thích `teaching/overview.py` kèm chữ *"đo 31/08/2026"* — như thể tự tay đo. Agent
phản biện đo lại: lớp thật đi từ **13% → 11%**, không phải "11% hiện 85%"; và
cảnh "học xuyên khoá" **không thể xảy ra** trên dữ liệu hiện có (100% sự kiện
`kind='lesson'` đều thuộc một khoá). Bộ lọc vẫn đúng, chỉ chú thích nói dối.

**Vì sao đây là lỗi nặng hơn một con số sai.** Một con số sai thì người sau đo
lại là ra. Một chú thích tự nhận đã đo thì người sau TIN nó và KHÔNG đo lại —
nó tắt đúng cái phản xạ mà cả tệp RULES này dựng lên.

**Bắt buộc:**
- Chữ "đo được", "đã kiểm", kèm ngày tháng, chỉ được viết cho phép đo mình tự
  chạy và tự nhìn thấy kết quả.
- Số của agent hay của người khác: ghi rõ nguồn, hoặc tự chạy lại rồi mới ghi.
- Kịch bản DỰNG RA để minh hoạ (chưa xảy ra trên dữ liệu thật) phải nói thẳng
  là "chưa đo được trên dữ liệu thật" — nó vẫn là lý do chính đáng để giữ bản
  vá, chỉ là không được đội lốt số đo.

---

## §16 · Sửa xong một tầng thì phải hỏi "tầng KIA có đi qua đây không"

Ngày 31/08/2026 tôi thêm hàng rào `must_change_password` và cho `apiFetch` tự
điều hướng khi gặp 403. `apiFetch` là cửa của mã Next mới. Nhưng trang
`/dashboard` và `/courses/*` là mã cũ, gọi `fetch` thô hơn 60 chỗ — **không chỗ
nào đi qua nó**. Kết quả không phải một bức tường 403 câm mà là một dashboard
trông bình thường của người mới: "0 ngày học liên tiếp", "0/76 bài", "Bạn chưa
đăng ký khoá nào". Học viên sẽ tưởng tài khoản mình bị xoá sạch.

Cùng ngày, cùng lỗi hình dạng: tôi thêm một mục vào thanh điều hướng và không
đo lại phần bên phải — chip người dùng bị đẩy ra ngoài khung, **giảng viên và
quản trị viên còn 0 pixel** để bấm vào menu, mất luôn nút Đăng xuất.

**Bắt buộc, cho mọi thay đổi chạm vào tầng dùng chung** (xác thực, xử lý lỗi,
bố cục khung, CSS token):
- Liệt kê MỌI đường đi qua tầng đó, kể cả mã cũ. `grep` tên hàm mới là chưa đủ —
  phải `grep` cả thứ nó thay thế (`fetch(`, `<div class=`…).
- Đo lại phần KHÔNG sửa nằm cạnh phần vừa sửa. Thêm một mục vào hàng ngang thì
  đo cả hàng, không chỉ mục vừa thêm.
- Hỏi "nếu hàng rào này chặn, người dùng NHÌN THẤY GÌ" — và đi xem tận mắt. Một
  hàng rào im lặng ở đúng chỗ dữ liệu được vẽ ra sẽ trông y hệt "không có dữ
  liệu", và đó là kiểu nói dối khó phát hiện nhất.

---

## §17 · Sao lưu bằng `basename` thì hai tệp cùng tên sẽ đè nhau

Ngày 31/08/2026, để chứng minh test đỏ-trên-mã-cũ tôi sao lưu ba tệp bằng
`cp $f scratchpad/$(basename $f)`. Hai trong ba là `views.py`
(`backend/teaching/` và `backend/accounts/`), nên bản sau đè bản trước — rồi tôi
khôi phục nội dung của `accounts/views.py` **đè lên** `teaching/views.py`. Bắt
được vì đã kiểm `head -3` ngay sau đó, chứ không phải vì lệnh nào báo lỗi.

**Bắt buộc:** để chứng minh test đỏ trên mã cũ thì dùng **`git stash`** hoặc
`git worktree`, đừng tự chép tay. Nếu vẫn phải chép, đặt tên theo ĐƯỜNG DẪN đầy
đủ đã thay `/` bằng `_`, không dùng `basename`. Và sau mọi lần khôi phục, kiểm
lại bằng `git diff --stat` — con số dòng thêm/bớt phải khớp với thứ mình định
làm, không phải "trông có vẻ ổn".
