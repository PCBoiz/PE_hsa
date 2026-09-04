# Việc của anh — pe_hsa

Những việc **chỉ anh làm được**: cần khoá bí mật, cần bảng điều khiển Render /
Vercel, cần quyết định sản phẩm, hoặc cần hỏi TopHSA. Mọi thứ khác nằm ở
`TODO.md` và tôi tự làm.

Cập nhật **31/08/2026**. Nhánh `erp` đã push lên
`github.com/PCBoiz/PE_hsa`, **chưa** gộp vào `master`.
Xem đang trước `master` bao nhiêu mốc: `git rev-list --count origin/master..erp`

Đánh dấu `[x]` khi xong để lần sau khỏi đọc lại từ đầu.

---

## A · Ba chốt bảo mật — chặn đường lên production

### [ ] A1. Xoay `SECRET_KEY`

**Vì sao gấp:** khoá hiện tại dài **19 byte**. RFC 7518 §3.2 yêu cầu tối thiểu
32 byte cho HS256 — thuật toán đang ký mọi JWT của hệ thống. Thư viện `pyjwt`
cảnh báo đúng chuyện này mỗi lần sinh token; cảnh báo đó xuất hiện suốt phiên
làm việc 31/08, và vẫn xuất hiện ở phiên 04/09.

> **Đổi 04/09/2026 — nay production KHÔNG KHỞI ĐỘNG với khoá ngắn.**
> `config/settings.py` kiểm độ dài và ném lỗi kèm đúng câu lệnh sinh khoá. Một
> cảnh báo lặp lại mỗi request là một cảnh báo người ta học cách không đọc; đây
> là lý do đổi nó thành điều kiện. Máy dev không chạm vào nhánh này (nó tự sinh
> khoá 64 ký tự khi thiếu).

```bash
python -c "import secrets;print(secrets.token_urlsafe(48))"
```

Dán chuỗi đó vào **hai** nơi:

1. `backend/.env` — dòng `SECRET_KEY=`
2. Render → dịch vụ `pe-hsa-backend` → **Environment** → `SECRET_KEY`

**Tôi cố ý không sinh sẵn khoá cho anh.** Sinh ra trong khung chat là nó nằm lại
trong bản ghi hội thoại — khoá lộ trước khi kịp dùng.

**Hệ quả khi đổi:** mọi người đang đăng nhập bị đăng xuất, phải đăng nhập lại.
Mật khẩu **không** ảnh hưởng — băm werkzeug độc lập với `SECRET_KEY`.

---

### [ ] A2. Đo `NUM_PROXIES` trên production

**Lỗ đã đo được:** xoay header `X-Forwarded-For` thì **300/300 request lọt qua**
giới hạn tần suất; cùng bộ đó với IP cố định thì **200/300 bị chặn**.

*Xác nhận lại độc lập 31/08/2026* bằng một đợt audit riêng, gọi HTTP thật vào
`/auth/login` (chỉ dùng email không tồn tại, không đụng tài khoản nào): XFF cố
định → dính 429 ở lần thứ 101; XFF ngẫu nhiên mỗi lần, chạy ngay sau đó → **60
lần liên tiếp, 0 lần bị chặn**. Mỗi lần thử làm máy chủ chạy scrypt ~126ms —
đúng thứ mà giới hạn tần suất sinh ra để bảo vệ. Nghĩa là
giới hạn đăng nhập, giới hạn tạo tài khoản, giới hạn chat đều vô hiệu với bất kỳ
ai biết đặt một header.

**Nhưng đừng đoán con số.** Đặt sai theo chiều ngược lại thì Django lấy nhầm IP
và **nhốt toàn bộ người dùng vào chung một rọ** — một em bấm nhanh là cả trung
tâm bị chặn.

**Cách đo:**

1. Gọi bất kỳ endpoint nào trên production từ máy anh.
2. Vào Render → `pe-hsa-backend` → **Logs**, tìm dòng của request đó.
3. Đếm số IP trong header `X-Forwarded-For` (chúng ngăn nhau bằng dấu phẩy).

Con số đó chính là `NUM_PROXIES`. Cho tôi biết, tôi đặt vào `settings.py`.

**ĐO LẠI 04/09/2026 — và bảng cũ ở đây SAI, đã thay.**

Bảng ghi ngày 31/08 nói `=1` khiến lời gọi THẲNG có giả header bị quy về IP
thật. Không đúng. Đo lại bằng `SimpleRateThrottle.get_ident` với `RequestFactory`
thật của Django (IP khách thật là `203.0.113.9`):

| kịch bản | `None` (cũ) | `=0` | `=1` | `=2` |
|---|---|---|---|---|
| gọi thẳng, không header | 203.0.113.9 | 203.0.113.9 | 203.0.113.9 | 203.0.113.9 |
| gọi thẳng, **giả** 1 chặng | 9.9.9.9 ✗ | **203.0.113.9 ✓** | 9.9.9.9 ✗ | 9.9.9.9 ✗ |
| gọi thẳng, **giả** 3 chặng | cả chuỗi ✗ | **203.0.113.9 ✓** | 3.3.3.3 ✗ | 2.2.2.2 ✗ |
| qua 1 proxy thật | 203.0.113.9 | ip proxy | **203.0.113.9 ✓** | 203.0.113.9 |
| qua 1 proxy, khách **giả** thêm | 9.9.9.9 ✗ | ip proxy | **203.0.113.9 ✓** | 9.9.9.9 ✗ |
| qua 2 proxy thật | cả chuỗi | ip proxy | ip proxy 2 | **203.0.113.9 ✓** |

Ba điều rút ra:

1. **`=1` vẫn là con số đúng cho production — nhưng vì lý do KHÁC với lý do ghi
   ở bảng cũ.** Nó không "phát hiện ra header giả"; nó lấy phần tử CUỐI, và trên
   production phần tử cuối là thứ *tầng biên của Render nối vào*, không phải thứ
   khách viết. Không gì tới được Django mà không qua tầng ấy.
2. **Trên máy dev thì `=1` không bảo vệ gì** (không có chặng nào để nối IP thật)
   — nên mã nay mặc định `0` ở dev và `1` ở production, đọc được từ biến môi
   trường `NUM_PROXIES` nếu anh đo ra chuỗi proxy dài hơn. **Đừng đặt `2` khi
   chỉ có một chặng**: khi đó khoá lại rơi vào phần khách tự viết.
3. **Đường qua Vercel vẫn gộp chung MỘT xô**, và `NUM_PROXIES` không sửa được:
   `proxy.ts` cố ý gỡ `x-forwarded-for`, `fetch` của Node không thêm lại, nên
   Django chỉ thấy IP egress của Vercel. Với trần đăng nhập 5 lượt/phút, người
   thứ sáu đăng nhập trong cùng một phút bị chặn dù ở đầu kia đất nước. Đây là
   việc RIÊNG, đã ghi vào `TODO.md`.

> **Phần mã đã xong 04/09/2026.** `common/net.py` nay là nơi DUY NHẤT trả lời
> "request này đến từ đâu"; cả hàng rào tần suất lẫn nhật ký kiểm toán đều gọi
> nó. Trước đó chúng lấy hai đầu ĐỐI NGHỊCH của cùng chuỗi header — cùng một
> request bị chặn vì IP này lại vào sổ dưới IP kia. Có phép kiểm canh đúng bất
> biến ấy, đã chứng minh ĐỎ khi lùi lại bản cũ.
>
> **KIỂM LẠI 05/09/2026 — câu "duy nhất" ở trên khi ấy đang SAI, đã vá.**
> Còn một người đọc thứ ba: `common/logging.py::log_5xx` lấy thẳng
> `META['REMOTE_ADDR']`. Đo với `NUM_PROXIES=1` và một chặng biên:
> cửa chung trả `203.0.113.9` (học viên thật), còn dòng nhật ký ghi `10.0.0.7`
> (chặng biên) — **giống nhau ở mọi request**, và mâu thuẫn với dòng
> `admin_audit` của chính request đó. Đi truy một sự cố mà gặp hai con số cho
> cùng một request thì tệ hơn không có số nào.
> Nay `log_5xx` cũng đi qua cửa chung, và có phép kiểm QUÉT TOÀN BỘ mã nguồn
> (`common/tests.py::test_khong_ai_doc_IP_khach_ngoai_common_net`) để người đọc
> thứ tư không lặng lẽ xuất hiện. Bản đầu của phép kiểm ấy cho ba dương tính
> giả vì nó bắt CHỮ chứ không bắt hành vi đọc — đã siết lại.
>
> **Việc còn của anh:** đo chuỗi proxy thật của Render (cách đo ở trên). Ra `1`
> thì không phải làm gì — mã đã mặc định thế. Ra số khác thì đặt biến môi trường
> `NUM_PROXIES` trên Render, không cần sửa mã.
>
> **Cách kiểm nhanh nhất (05/09):** `/api/admin/do-proxy` nay trả thêm
> `ipHienTai` và `numProxiesHienTai` — tức KẾT LUẬN với cấu hình đang chạy, chứ
> không chỉ nguyên liệu để anh tự suy. Mở nó bằng trình duyệt: `ipHienTai` bằng
> IP thật của anh (đối chiếu whatismyip) thì con số đang đúng, không phải sửa gì.

*Vì sao vẫn cần anh đo:* mọi số liệu trên là đo ở máy — toàn bộ 32 dòng
`admin_audit` hiện có đều là `::1`/`127.0.0.1`, chưa request production nào được
ghi. Hình dạng chuỗi proxy thật của Render **chưa từng được đo**.

*(Nếu Render không log sẵn header đó, báo tôi — tôi thêm một endpoint chẩn đoán
tạm, chỉ quản trị viên gọi được, đo xong gỡ đi.)*

---

### [ ] A3. Redis cho bộ đếm giới hạn tần suất

**Vấn đề:** `render.yaml` dòng 27 chạy `--workers 2`. Mỗi worker giữ một
`LocMemCache` **riêng**, mà bộ đếm giới hạn tần suất nằm trong đó. Nên **mọi
giới hạn đang bị nhân đôi** — đặt 5 lần/phút thì thực tế là 10.

**Việc của anh:** Render → **New** → **Key Value** (Redis), rồi đặt biến
`REDIS_URL` cho service `pe-hsa-backend`.

> **Phần mã ĐÃ XONG từ trước** (`config/settings.py`, khối `REDIS_URL`): có biến
> thì dùng Redis, không có thì chạy y như cũ bằng `LocMemCache`. Không cần đưa
> URL cho tôi, và không cần sửa một dòng mã nào — chỉ cần đặt biến rồi deploy
> lại. `django-redis` đã nằm trong `requirements.txt`.

---

## B · Gộp vào `master` và deploy

**Cảnh báo:** `render.yaml` có `autoDeploy: true` và `branch: master` — **gộp là
deploy production ngay lập tức**, không có bước xác nhận nào.

### [ ] B1. Thứ tự đề nghị

1. Làm xong **A1** (khoá bí mật) — đây là thứ duy nhất thực sự chặn.
2. Gộp `erp` → `master`.
3. Mở Render → Logs, xem lượt build.
4. Rồi mới làm A2 và A3.

### Deploy sẽ chạy gì

`buildCommand` gọi `manage.py bootstrap_schema`. Các mục lược đồ §35–§37 tôi đã
áp tay lên Neon rồi, nên lượt đó là vô hại — đã chứng minh bằng cách chạy **cả
tệp hai lượt liên tiếp** trong transaction rồi cuộn lại: 310 câu, 0 hỏng.

### [ ] B2. Để mắt lần deploy đầu

`frontend/src/middleware.ts` khai `runtime = 'nodejs'`. Nó chạy tốt ở máy và
`pnpm build` xanh, nhưng đây là **lần đầu nó lên Vercel**. Nếu phiên đăng nhập
hết hạn sớm bất thường sau khi deploy, đó là chỗ cần nhìn trước tiên.

---

## C · Năm câu hỏi cho TopHSA

Anh chốt 31/08 là **vẫn theo đặc tả `docs/ERP_TOPHSA_2026-08-24.md` §9**, nên
đây là đường găng thật — không phải chuyện code chậm, mà là chưa biết phải code
cái gì.

### [ ] C1. Dạy trên nền tảng nào? Có API lấy danh sách người tham dự không?

→ Quyết định **điểm danh tự động hay tick tay** — hai thiết kế khác hẳn nhau.
Hiện tôi đã dựng đường tick tay và để sẵn cột `attendance.minutes` cho đường tự
động, nên câu trả lời "có API" sẽ không phải đập đi làm lại.

### [ ] C2. Có chấm tự luận không? Thang điểm nào? Ai chấm — giảng viên hay trợ giảng?

> **Cập nhật 31/08/2026 — câu này KHÔNG còn chặn đường.** Tôi đã dựng xong §5
> (giao bài & chấm tay) theo cách mà cả ba câu trả lời đều không đổi cấu trúc:
> "có chấm không" đổi việc mô-đun có được DÙNG hay không · "thang nào" thì mỗi
> bài tự khai `max_score` và hệ thống quy về % · "ai chấm" đổi đúng một dòng
> `permission_classes`. Vẫn nên hỏi, nhưng để cấu hình chứ không để viết lại.

→ Quyết định khối §5 (giao bài & chấm tay). Đặc tả đã phác sẵn hai bảng
`assignments` / `submissions`, chấm xong đẻ `learning_events` nên điểm tự luận
vào thẳng bản đồ năng lực, không cần luật riêng.

### [ ] C3. Báo cáo phụ huynh gửi qua kênh nào? Tần suất? Ai duyệt trước khi gửi?

→ Nội dung báo cáo **đã làm xong** (T27, xem `/giang-day/bao-cao/<lớp>/<em>`),
in ra PDF được. Còn thiếu đúng phần **gửi tự động**, mà phần đó phụ thuộc câu
trả lời này (Zalo OA? email? ai bấm nút gửi?).

### [ ] C4. Quy trình thu chi kế toán thật? Có phần mềm kế toán đang dùng không?

→ Khối §7 (học phí, công nợ, thù lao, CRM). Đặc tả ghi rõ đây là khối **lớn
nhất** và *"không tận dụng được gì đã dựng"*. Khuyến nghị trong đặc tả: cân nhắc
nối với phần mềm họ đang dùng thay vì viết lại — sai một chi tiết là sai sổ sách.

### [ ] C5. Phút ngồi lớp có tính vào chỉ tiêu tự học hằng tuần không?

→ Điểm danh đang **cố ý** để `learning_events.minutes = NULL` chờ đúng câu này
(xem chú thích ở `teaching/sessions.py:_emit_events`). Đổ phút vào bây giờ là âm
thầm thổi phồng một chỉ số đang tranh luận, và **gỡ ra thì không gỡ được**. Số
phút vẫn được giữ nguyên trong `meta`, nên chốt xong chỉ là một câu UPDATE.

---

## D · Hai quyết định nhỏ của anh

### [ ] D1. Tạo đợt học đầu tiên

Màn hình **đã xong** — vào `/quan-tri/dot-hoc`, bấm **Tạo đợt**. Việc còn lại là
quyết định của anh, không phải của tôi:

- Đợt đầu tên gì? (ví dụ "Đợt 1/2027") và mã đợt nếu trung tâm có quy ước.
- Ngày bắt đầu / kết thúc / ngày thi.
- Rồi gán lớp `Luyện HSA đợt 1/2027 — Ca tối` vào đợt đó.

Tạo xong báo tôi — lúc ấy mới làm được **báo cáo so sánh giữa các đợt** (tỉ lệ
bỏ học, điểm trung bình theo đợt), thứ trước đây không có dữ liệu để làm.

### [ ] D3. Cấp vai "Biên tập nội dung" cho một tài khoản

Khu **Soạn giáo trình** (`/admin`) xong 04/09 và mở cho vai trò này. Nhưng hiện
CHƯA tài khoản nào mang vai ấy, nên đường đi của người biên tập mới chỉ được
kiểm ở tầng API (`courseadmin/tests.py`) và ở nhánh rẽ của thanh điều hướng
(đã đo trên trình duyệt bằng cách chặn `/api/user` rồi đổi mỗi trường `role`).

Thứ CHƯA đo được: hàng rào phía máy chủ của trang `/admin` với một tài khoản
thật mang vai ấy — nó gọi `/api/user` từ tiến trình Next chứ không qua trình
duyệt, nên không chặn từ ngoài được.

Anh vào `/quan-tri/tai-khoan`, đổi vai một tài khoản (hoặc cấp một tài khoản
mới) sang **Biên tập nội dung**. Báo tôi thì tôi chạy nốt lượt kiểm end-to-end.
Tôi không tự làm vì đó là một câu UPDATE trên CSDL thật.

---

### [ ] D2. Tài khoản quản trị viên đang nằm trong lớp 1

Anh chốt **giữ** (để xem giao diện). Tôi đã ghi T51: báo cáo lớp nên lọc theo
**vai trò**, để tài khoản quản trị nằm trong lớp bao nhiêu lần cũng không làm
lệch sĩ số / bảng điểm danh / mẫu số tiến độ. Không cần anh làm gì thêm — chỉ để
anh biết con số hiện tại đang cộng cả tài khoản đó.

---

## D+ · Ba việc cấu hình mới (05/09/2026)

Cả ba đều là **phần mã đã xong**, chỉ còn thao tác trên bảng điều khiển.

### [ ] D4. Bí mật giữa Vercel và Render — tách xô giới hạn tần suất

Hiện **mọi người dùng thật chung MỘT xô**: `proxy.ts` gỡ `x-forwarded-for` của
khách (đúng — để khách không tự đặt khoá giới hạn), nhưng `fetch` của Node không
thêm lại, nên Django chỉ thấy IP egress của Vercel. Với trần **5 lượt đăng
nhập/phút**, người thứ sáu bị chặn dù ngồi ở đầu kia đất nước — một lớp 30 em
vào học cùng giờ là một sự cố.

Mã đã sẵn: `proxy.ts` gửi IP khách trong header riêng kèm bí mật, Django chỉ tin
khi bí mật khớp. **Chưa đặt biến thì mọi thứ chạy y như trước** (mặc định đóng).

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Dán CÙNG một giá trị vào hai nơi:

| Nơi | Tên biến | Ghi chú |
|---|---|---|
| Render | `PROXY_SHARED_SECRET` | |
| Vercel | `PE_PROXY_SECRET` | **KHÔNG** đặt tên `NEXT_PUBLIC_…` — Next nhúng mọi biến như thế vào gói JavaScript gửi cho mọi trình duyệt |

Kiểm sau khi đặt: đăng nhập sai mật khẩu 6 lần từ một máy → lần thứ 6 bị chặn;
từ một máy khác (hoặc mạng khác) vẫn vào được ngay.

### [ ] D5. Nhánh Neon riêng cho CI

`pytest` đang chạy thẳng vào **CSDL học viên thật** mỗi lần push. Bộ test cuộn
lại ở cuối mỗi test, nhưng "cuộn lại" không phải "không đụng": nó vẫn chiếm kết
nối, vẫn giữ khoá, và một test viết ngoài giao dịch thì cuộn lại không cứu.

1. Neon → **Branches** → tạo nhánh từ `main`, đặt tên `ci`.
2. Copy connection string của nhánh ấy.
3. GitHub → repo → *Settings › Secrets and variables › Actions* → thêm secret
   **`DATABASE_URL_CI`**.

Không phải sửa mã: job pytest đã đọc `DATABASE_URL_CI` trước, rơi về
`DATABASE_URL` khi chưa có. Mỗi lượt CI nay in ra nó đang nối vào máy chủ nào
(che mật khẩu), nên nhìn log là biết đã chuyển hay chưa.

### [ ] D6. Chạy bốn câu DDL còn chờ, hoặc gộp `master`

`python manage.py kiem_luoc_do` trả lời "còn phải chạy gì". Đo 05/09: **4/9 mục
chưa tới** — bốn khoá ngoại `§42`/`§43` vẫn là `NO ACTION`, tức xoá một tài
khoản sẽ bị chặn thay vì dọn theo. Gộp `master` là Render tự chạy
`bootstrap_schema`; hoặc áp tay từng câu trong `backend/sql/legacy_schema.sql`.

---

## D++ · Công cụ mới, và MỘT dòng dữ liệu tôi đã tạo (05/09/2026)

### Tài khoản kiểm thử — ĐÃ TẠO, anh có thể xoá bất cứ lúc nào

```
users id=13231   e2e-kiem-thu@example.com   "KIỂM THỬ TỰ ĐỘNG (không phải học viên)"
```

Nó sẽ hiện trong danh sách tài khoản khu Quản trị — cố ý đặt tên như vậy để nhìn
là biết. XP = 0 nên không lọt bảng xếp hạng. Sau một lượt chạy đủ bộ kiểm, nó để
lại **0 dòng** ở `lesson_progress`, `learning_events`, `review_quiz_results`,
`admin_audit`, `notifications` (đã đo).

    python scripts/tai_khoan_e2e.py              # xem trước, không ghi
    python scripts/tai_khoan_e2e.py --that       # tạo / đặt lại mật khẩu
    python scripts/tai_khoan_e2e.py --xoa --that # gỡ sạch

Mật khẩu ngẫu nhiên, nằm ở `.the/e2e.json` (không vào git). Repo không còn mật
khẩu mặc định nào.

**Tôi cũng đã chèn NHẦM 6 dòng** vào `token_blacklist_outstandingtoken` khi viết
`scripts/cap_the.py` — tôi tin một suy luận thay vì đo, và tuyên bố sai rằng nó
"không ghi CSDL". Đã xoá sạch (493 → 487, 0 dòng mồ côi, dữ liệu người khác
nguyên vẹn) và sửa script thành access-only.

### Chạy bộ đo giao diện

```
python scripts/cap_the.py                    # thẻ 30 phút, KHÔNG ghi CSDL
cd scripts
node do_giao_dien.mjs --tu-kiem              # bộ đo có ĐỎ ĐƯỢC không (chạy trước)
node do_giao_dien.mjs                        # chủ đề sáng
node do_giao_dien.mjs --toi                  # chủ đề tối
```

Số đo 05/09: **cả hai chủ đề × 2 khổ × 16 trang = 0 vi phạm** tương phản, 0 vùng
chạm dưới 44px, 0 tràn ngang, 0 lỗi JS. Tự kiểm ĐẠT 32/32.

### Chạy bộ kiểm giao diện đầu-cuối

```
cd frontend && E2E_BASE_URL=http://localhost:3100 pnpm e2e
```

8/8 xanh, không phép kiểm nào bị bỏ qua.

---

## E · Tuỳ chọn — cho tôi tự push

Suốt phiên 30–31/08, lệnh `git push` bị bộ lọc quyền của chế độ auto chặn (không
phải lỗi git: `git push --dry-run` chạy lọt bình thường). Ba cách:

- **Anh tự chạy** `git push` khi cần — không đổi thiết lập gì.
- **Cấp quyền hẹp:** tạo `D:\pe_hsa\.claude\settings.json`

  ```json
  { "permissions": { "allow": ["Bash(git push -u origin erp:*)"] } }
  ```

  Cố ý **hẹp**. Luật rộng `"Bash(git push:*)"` cho phép luôn `git push origin
  master`, tức là tôi deploy production được mà không hỏi ai.
- **Rời chế độ auto:** gõ `/permissions`, hoặc Shift+Tab — khi đó nó hiện hộp xác
  nhận thay vì chặn thẳng.

---

## Phụ lục — trạng thái hiện tại

| | |
|---|---|
| Nhánh | `erp`, đã push, chưa gộp vào `master` |
| Bộ kiểm backend | **94 đạt / 0 hỏng** (trước 31/08: 18 hỏng / 15 lỗi) |
| `pnpm build` · `tsc` · `eslint` | xanh (2 cảnh báo có sẵn ở `layout.tsx`, `Chatbot.tsx`) |
| CSDL Neon | 51 bảng · 5 tài khoản · 1 lớp · 4 dòng ghi danh · 37 sự kiện |
| ERP §9 | khối 1, 2, 5 xong · khối 3 xong phần báo cáo, còn phần gửi · khối 4, 6, 7 chờ TopHSA |

**Chạy bộ kiểm:** `pytest` không có sẵn trong venv.

```bash
cd D:\pe_hsa\backend
.venv\Scripts\python.exe -m pip install pytest pytest-django
.venv\Scripts\python.exe -m pytest -q        # ~5 phút, chạy trên CSDL thật rồi cuộn lại
```
