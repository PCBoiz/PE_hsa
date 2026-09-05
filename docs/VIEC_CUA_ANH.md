# Việc của anh — pe_hsa

Những việc **chỉ anh làm được**: cần khoá bí mật, cần bảng điều khiển Render /
Vercel, cần quyết định sản phẩm, hoặc cần hỏi TopHSA. Mọi thứ khác nằm ở
`TODO.md` và tôi tự làm.

*Gộp lại thành MỘT tệp ngày 05/09/2026. Trước đó việc của anh nằm rải ở sáu mục
A/B/C/D/D+/D++ mọc dần theo thời gian, cộng một tệp `GOP_MASTER.md` riêng — đọc
xong không biết cái nào còn, cái nào đã xong.*

**Mọi con số trong tệp này là ĐO trên chính CSDL và mã đang chạy.** Chỗ nào chưa
đo được thì có một dòng nói rõ là chưa đo — đó là thông tin, không phải chỗ trống.

Đánh dấu `[x]` khi xong để lần sau khỏi đọc lại từ đầu.

---

## Đọc 3 phút — nếu chỉ có ngần ấy thời gian

| | việc | mất bao lâu | không làm thì sao |
|---|---|---|---|
| 1 | Xoay `SECRET_KEY` trên Render | 2 phút | Gộp `master` xong **deploy trượt** (không sập) |
| 2 | Đặt bí mật proxy ở Render + Vercel | 5 phút | **Lớp 30 em vào cùng giờ, 10 em ăn lỗi 429** |
| 3 | Gộp `master` | 1 phút | — |

Ba việc ấy là **Phần 1** và **Phần 2**. Mọi thứ còn lại đọc lúc nào cũng được.

Nhánh `erp` đang đi trước `master` **112 commit**. Bộ kiểm đầy đủ xanh:
`pytest 324/324`, `next build` thành công, bốn lượt quét giao diện đều sạch
(bảng đầy đủ ở Phần 8).

---

## Mục lục

- **Phần 1 — Ba việc phải làm trước khi gộp** (SECRET_KEY · bí mật proxy · Redis)
- **Phần 2 — Gộp `master`: từng bước, và cách biết nó chạy đúng**
- **Phần 3 — Sau khi gộp: đo `NUM_PROXIES` thật**
- **Phần 4 — Quyết định của riêng anh** (đợt học · vai biên tập · phút ngồi lớp)
- **Phần 5 — Năm câu hỏi cho TopHSA**
- **Phần 6 — Nên làm, không gấp** (nhánh Neon cho CI · bốn câu DDL · `/thiet-ke`)
- **Phần 7 — Công cụ: chạy thế nào**
- **Phần 8 — Trạng thái hiện tại, đo ngày 05/09**
- **Phần 9 — Dữ liệu tôi đã tạo và đã xoá trên CSDL thật**

---

# Phần 1 — Ba việc phải làm trước khi gộp

## [ ] 1.1 · Xoay `SECRET_KEY` — 2 phút

### Vì sao

Khoá hiện tại dài **19 byte**. RFC 7518 §3.2 đòi tối thiểu 32 byte cho HS256 —
đúng thuật toán đang ký mọi JWT của hệ thống. `pyjwt` cảnh báo chuyện này ở mỗi
lượt sinh token, và cảnh báo ấy in ra suốt nhiều ngày mà không ai làm gì. Nên từ
04/09 nó thành một **điều kiện chặn**, không còn là lời khuyên: production không
khởi động với khoá ngắn.

### Quên thì sao — đã đo, và nhẹ hơn anh tưởng

Chạy từng bước của `buildCommand` với khoá 19 byte:

```
collectstatic     rc=1   RuntimeError: SECRET_KEY dài 19 byte, cần tối thiểu 32
bootstrap_schema  rc=1   (cùng lỗi)
migrate           rc=1   (cùng lỗi)
```

Cổng nổ ở bước build **đầu tiên** — trước khi chạm CSDL, trước khi gunicorn khởi
động. Render giữ nguyên bản build cũ. Nên hậu quả là *deploy trượt*, không phải
*production sập*. Vẫn phải làm trước, nếu không lần gộp ấy vô ích.

### Làm

```bash
python -c "import secrets;print(secrets.token_urlsafe(48))"
```

Dán chuỗi đó vào **hai** nơi:

1. `backend/.env` — dòng `SECRET_KEY=` (để máy anh chạy giống production)
2. Render → dịch vụ `pe-hsa-backend` → **Environment** → `SECRET_KEY`

**Tôi cố ý không sinh sẵn khoá.** Sinh ra trong khung chat là nó nằm lại trong
bản ghi hội thoại — khoá lộ trước khi kịp dùng.

### Hệ quả

Mọi người đang đăng nhập bị **đăng xuất**, phải đăng nhập lại. Mật khẩu không
ảnh hưởng (băm werkzeug độc lập với `SECRET_KEY`).

### Kiểm đã xong chưa

Sau khi deploy, mở `https://pe-hsa-backend.onrender.com/health` →
`{"status":"ok"}`. Build log không có dòng `RuntimeError: SECRET_KEY`.

---

## [ ] 1.2 · Bí mật proxy — 5 phút. **Đây là việc dễ bỏ sót nhất**

### Vì sao — thứ duy nhất có thể gây sự cố cho học viên ngay ngày đầu

Hôm nay (`master`): trình duyệt gọi **thẳng** Django. Biên của Render nối IP thật
vào `X-Forwarded-For`, nên mỗi người một khoá giới hạn tần suất.

Sau khi gộp (`erp`): trình duyệt gọi Vercel, và lớp trung gian `proxy.ts` **cố ý
gỡ** `x-forwarded-for`. Việc gỡ ấy là đúng — đo ngày 30/08: gửi 300 lần đăng nhập
kèm một `X-Forwarded-For` ngẫu nhiên mỗi lần thì **300 lần đều lọt**, tức hàng
rào "5 lần đăng nhập/phút" không chặn gì với người biết đổi một header.

Nhưng `fetch` của Node không thêm header ấy lại. Nên Django chỉ thấy **IP egress
của Vercel**. Đo được:

```
qua Vercel, người A   → khoá giới hạn = 76.76.21.9
qua Vercel, người B   → khoá giới hạn = 76.76.21.9      ← CÙNG một khoá
```

Trần áp lên khoá ấy, **dùng chung cho toàn bộ người dùng**:

| trần | khoá có kèm tên endpoint? | hệ quả thật |
|---|---|---|
| `login` **20/phút** | KHÔNG | lớp 30 em vào cùng giờ → **10 em ăn 429** |
| `register` **10/phút** | KHÔNG | đăng ký hàng loạt bị chặn giữa chừng |
| `ip_hour` 1000/giờ | CÓ | mỗi endpoint một quota riêng — ít khả năng chạm |

*(Tôi suýt viết "1000/giờ cho toàn bộ người dùng" ở bản trước. Sai: khoá throttle
có kèm tên view nên `ip_hour` là mỗi-endpoint. Nhưng `LoginThrottle` thì không
kèm, nên 20 lượt/phút dùng chung là thật.)*

### Đặt bí mật thì hết — đã kiểm cả hai chiều

```
CÓ bí mật, người A qua Vercel                 → khoá = 1.1.1.1
CÓ bí mật, người B qua Vercel                 → khoá = 2.2.2.2     ← tách ra rồi
kẻ gọi THẲNG Render, giả header, bí mật SAI   → khoá = 9.9.9.9     ← IP thật của họ
```

Tức bí mật vừa trả lại khoá theo từng người, vừa **không** nới hàng rào chống giả
header.

### Làm — cùng MỘT giá trị ở hai nơi

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

```
Render → pe-hsa-backend → Environment → PROXY_SHARED_SECRET
Vercel → Project Settings → Environment Variables → PE_PROXY_SECRET
```

Trên Vercel phải là biến **server-side**. Đặt tên bắt đầu bằng `NEXT_PUBLIC_` là
nhúng bí mật vào gói JavaScript gửi cho mọi trình duyệt.

Bí mật phải dài **≥ 16 ký tự**. Ngắn hơn thì `common/net.py` coi như chưa cấu
hình và bỏ qua header — cố ý, để một cấu hình nửa vời không mở toang cửa.

### Kiểm đã xong chưa

Phần 3 (mở `/api/admin/do-proxy` và so `ipHienTai` với IP thật của anh).

---

## [ ] 1.3 · Redis — nên làm, không chặn

### Vì sao

`render.yaml` chạy `--workers 2`. Mỗi worker giữ một `LocMemCache` **riêng**, mà
bộ đếm giới hạn tần suất nằm trong đó. Nên **mọi trần đang bị nhân đôi**: đặt 20
lượt đăng nhập/phút thì thực tế là 40.

### Làm

Render → **New** → **Key Value** (Redis), cùng region `ohio`. Copy *Internal
Redis URL*, thêm biến `REDIS_URL` cho `pe-hsa-backend`, deploy lại.

Phần mã **đã xong sẵn**: có biến thì dùng Redis, không có thì chạy y như cũ bằng
`LocMemCache`. `django-redis` đã nằm trong `requirements.txt`. Không cần đưa URL
cho tôi và không phải sửa một dòng mã nào.

### Đã đo

| `REDIS_URL` | kết quả |
|---|---|
| không đặt | `LocMemCache` |
| toàn dấu cách | `LocMemCache` (nhờ `.strip()`) |
| có URL | `RedisCache`, `IGNORE_EXCEPTIONS=True` |

`IGNORE_EXCEPTIONS` nghĩa là Redis chết cũng không làm chết app — bộ đệm ở đây
chỉ để nhanh hơn và đếm quota, không phải nguồn sự thật nào.

---

# Phần 2 — Gộp `master`: từng bước

## Trước hết: gộp là deploy NGAY

`render.yaml` có `autoDeploy: true` và `branch: master`. `DEPLOY.md` ràng buộc
Vercel cũng chỉ deploy từ `master`. Nên **gộp = đẩy cả backend lẫn frontend lên
production tức thì**, không có bước bấm xác nhận nào ở giữa.

## Quy mô

```
112 commit · 232 tệp · +45.425 / −11.030 dòng
master KHÔNG đi trước erp  →  fast-forward, không xung đột
```

Đây không phải một bản vá nhỏ. Frontend đổi ~22.000 dòng, và **kiến trúc gọi API
đổi hẳn**: `master` gọi thẳng Django từ trình duyệt, `erp` đi qua lớp trung gian
trên Vercel với token nằm trong cookie httpOnly. Đó chính là lý do việc 1.2 tồn
tại.

## Deploy sẽ chạy gì — và tôi đã diễn tập phần nguy hiểm nhất

`buildCommand` chạy bốn bước: `pip install` → `collectstatic` →
`bootstrap_schema` → `migrate`.

**`bootstrap_schema` là bước đáng lo nhất**: nó chạy toàn bộ DDL trong
`backend/sql/*.sql` và **ném ở câu lệnh lỗi đầu tiên**. Một câu không idempotent
là một lần build hỏng.

Nên tôi diễn tập: DDL của Postgres có giao dịch, nên mở một giao dịch trên
**chính CSDL production**, chạy cả 193 câu, rồi cuộn lại.

```
TRƯỚC: 53 bảng, 75 khoá ngoại, 167 chỉ mục
193 câu lệnh chạy SẠCH
SAU  : 53 bảng, 75 khoá ngoại, 167 chỉ mục     ← cuộn lại, không đổi gì
```

Trong giao dịch, bốn khoá ngoại đang chờ thành đúng chính sách mong muốn:

| khoá ngoại | sau khi deploy |
|---|---|
| `roadmaps_user_id_fkey` | CASCADE |
| `roadmaps_generated_from_survey_id_fkey` | SET NULL |
| `courses_instructor_id_fkey` | SET NULL |
| `missions_course_id_fkey` | CASCADE |

Chúng viết theo lối `DROP CONSTRAINT IF EXISTS` rồi `ADD ... NOT VALID`:
idempotent, và `NOT VALID` nghĩa là **không quét lại bảng**, nên không khoá bảng
lâu.

`migrate --noinput`: **không có migration nào chờ**.

**Phụ thuộc mới**: `django-redis==5.4.0` và `openpyxl>=3.1`. Cả hai thuần Python,
không cần trình biên dịch trên Render.

**Bí mật lọt vào repo**: không. Quét cả 112 commit theo đúng hình dạng bí mật của
dự án (chuỗi Neon, `sk-…`, `AIza…`, `GOCSPX-…`); ba chuỗi tìm thấy đều là ví dụ
trong tài liệu (`nguoi:matkhau`, `ep-abc-123`). Tệp bị theo dõi chỉ có
`.env.example`, giá trị bên trong đều là chỗ trống.

## [ ] Các bước

```bash
# 1-3. Làm xong Phần 1 (SECRET_KEY, bí mật proxy, Redis)

# 4. Ghi lại đường lùi
git rev-parse origin/master          # chép con số này ra chỗ nào đó

# 5. Gộp
cd D:\pe_hsa
git checkout master
git merge --ff-only origin/erp
git push origin master
```

## [ ] Nhìn gì trong lúc deploy

| bước | dấu hiệu ĐÚNG |
|---|---|
| Render → Build log | `[bootstrap_schema] public base tables: 53 -> 53 (193 statements OK)` |
| Render → Build log | KHÔNG có `RuntimeError: SECRET_KEY` |
| `/health` | `{"status":"ok"}` |
| Vercel → Deployment | build thành công, 22 tuyến |
| Đăng nhập thử | vào được (mọi người đã bị đăng xuất ở bước 1.1) |

## Nếu hỏng thì lùi thế nào

Build hỏng ở bước `bootstrap_schema` **không làm sập gì** — Render giữ bản build
trước, người dùng không thấy khác biệt.

Nếu bản mới lên rồi mới lộ vấn đề:

```bash
git reset --hard <commit ghi ở bước 4>
git push --force-with-lease origin master
```

**Một điều DDL không tự lùi:** bốn khoá ngoại ở trên vẫn ở chính sách mới. Chúng
không phá dữ liệu — chỉ đổi hành vi khi **xoá** một tài khoản, mà hiện không có
đường nào trong mã xoá `users` (đã đo; khu quản trị đổi `status`, không xoá).

---

# Phần 3 — Sau khi gộp: đo `NUM_PROXIES` thật

## Vì sao vẫn cần đo

`NUM_PROXIES` quyết định Django lấy phần tử nào của chuỗi `X-Forwarded-For` làm
IP khách. Đặt sai một chiều thì hàng rào tần suất vô hiệu; đặt sai chiều kia thì
**mọi người dùng dồn vào chung một rọ**.

Mã đang mặc định `1` ở production và `0` ở dev. Con số `1` đúng theo bảng đo dưới
đây — nhưng **mọi số liệu ấy đo ở máy**, chưa lượt nào đo hình dạng chuỗi proxy
thật của Render.

| kịch bản | `None` | `=0` | `=1` | `=2` |
|---|---|---|---|---|
| gọi thẳng, không header | 203.0.113.9 | 203.0.113.9 | 203.0.113.9 | 203.0.113.9 |
| gọi thẳng, **giả** 1 chặng | 9.9.9.9 ✗ | **203.0.113.9 ✓** | 9.9.9.9 ✗ | 9.9.9.9 ✗ |
| gọi thẳng, **giả** 3 chặng | cả chuỗi ✗ | **203.0.113.9 ✓** | 3.3.3.3 ✗ | 2.2.2.2 ✗ |
| qua 1 proxy thật | 203.0.113.9 | ip proxy | **203.0.113.9 ✓** | 203.0.113.9 |
| qua 1 proxy, khách **giả** thêm | 9.9.9.9 ✗ | ip proxy | **203.0.113.9 ✓** | 9.9.9.9 ✗ |
| qua 2 proxy thật | cả chuỗi | ip proxy | ip proxy 2 | **203.0.113.9 ✓** |

`=1` đúng cho production **nhưng không phải vì nó "phát hiện header giả"** — nó
lấy phần tử CUỐI, và trên production phần tử cuối là thứ *tầng biên của Render
nối vào*. Không gì tới được Django mà không qua tầng ấy.

## [ ] Cách đo — một lần bấm

Đăng nhập bằng tài khoản quản trị rồi mở:

```
https://pe-hsa-backend.onrender.com/api/admin/do-proxy
```

Nhìn hai trường:

```json
{ "numProxiesHienTai": 1, "ipHienTai": "…" }
```

**`ipHienTai` có bằng IP thật của anh không** (đối chiếu whatismyip)?

- **Bằng** → con số đang đúng, không phải làm gì.
- **Không bằng** → báo tôi con số `soChang` trong cùng phản hồi; đặt biến
  `NUM_PROXIES` trên Render, không phải sửa mã.

Đường này cũng trả về `xff`, `chang`, `soChang`, `remoteAddr` nếu anh muốn nhìn
nguyên liệu thô.

---

# Phần 4 — Quyết định của riêng anh

## [ ] 4.1 · Tạo đợt học đầu tiên

Màn hình **đã xong**: vào `/quan-tri/dot-hoc` → **Tạo đợt**. Việc còn lại là
quyết định của anh:

- Đợt đầu tên gì (ví dụ "Đợt 1/2027") và mã đợt nếu trung tâm có quy ước
- Ngày bắt đầu / kết thúc / ngày thi
- Rồi gán lớp `Luyện HSA đợt 1/2027 — Ca tối` vào đợt đó

Tạo xong báo tôi — lúc ấy mới làm được **báo cáo so sánh giữa các đợt** (tỉ lệ bỏ
học, điểm trung bình theo đợt), thứ trước đây không có dữ liệu để làm.

## [ ] 4.2 · Cấp vai "Biên tập nội dung" cho một tài khoản

Khu **Soạn giáo trình** (`/admin`) xong 04/09 và mở cho vai này. Nhưng **chưa tài
khoản nào mang vai ấy**, nên đường đi của người biên tập mới chỉ được kiểm ở tầng
API và ở nhánh rẽ của thanh điều hướng.

Thứ **chưa đo được**: hàng rào phía máy chủ của `/admin` với một tài khoản thật
mang vai ấy — nó gọi `/api/user` từ tiến trình Next chứ không qua trình duyệt,
nên không chặn từ ngoài để giả lập được.

Anh vào `/quan-tri/tai-khoan`, đổi vai một tài khoản sang **Biên tập nội dung**.
Báo tôi thì tôi chạy nốt lượt kiểm đầu-cuối. Tôi không tự làm vì đó là một câu
UPDATE trên CSDL thật.

## [ ] 4.3 · Phút ngồi lớp có tính vào chỉ tiêu tự học không?

Đây cũng là câu C5 hỏi TopHSA (Phần 5) — ghi ở cả hai chỗ vì nó vừa là câu hỏi
nghiệp vụ, vừa là một công tắc trong mã.

Điểm danh đang **cố ý** ghi `learning_events.minutes = NULL`, nhưng **giữ nguyên
số phút thật trong `meta.minutes`**. Đo 05/09: hiện có **0 sự kiện điểm danh**
trong CSDL — chưa lớp nào chạy, nên chưa có gì để trộn nhầm.

Đổ phút vào cột chính bây giờ là âm thầm thổi phồng một chỉ số đang tranh luận,
và **gỡ ra thì không gỡ được**. Chốt xong thì bật lên là một dòng mã cộng một câu
UPDATE cho dữ liệu cũ.

## Không cần làm gì — chỉ để anh biết

**Tài khoản quản trị đang nằm trong lớp 1.** Anh chốt giữ (để xem giao diện). Tôi
đã ghi T51: báo cáo lớp nên lọc theo **vai trò**, để tài khoản quản trị nằm trong
lớp bao nhiêu lần cũng không làm lệch sĩ số / bảng điểm danh / mẫu số tiến độ.
Con số hiện tại đang cộng cả tài khoản đó.

---

# Phần 5 — Năm câu hỏi cho TopHSA

Anh chốt 31/08 là **vẫn theo đặc tả `docs/ERP_TOPHSA_2026-08-24.md` §9**, nên đây
là đường găng thật — không phải chuyện code chậm, mà là chưa biết phải code cái gì.

## [ ] C1 · Dạy trên nền tảng nào? Có API lấy danh sách người tham dự không?

→ Quyết định **điểm danh tự động hay tick tay** — hai thiết kế khác hẳn nhau.
Tôi đã dựng đường tick tay và để sẵn cột `attendance.minutes` cho đường tự động,
nên câu trả lời "có API" sẽ không phải đập đi làm lại.

## [ ] C2 · Có chấm tự luận không? Thang điểm nào? Ai chấm?

**Câu này KHÔNG còn chặn đường** (cập nhật 31/08). Khối §5 (giao bài & chấm tay)
đã dựng xong theo cách mà cả ba câu trả lời đều không đổi cấu trúc: "có chấm
không" đổi việc mô-đun có được DÙNG hay không · "thang nào" thì mỗi bài tự khai
`max_score` và hệ thống quy về % · "ai chấm" đổi đúng một dòng
`permission_classes`. Vẫn nên hỏi, nhưng để **cấu hình** chứ không để viết lại.

## [ ] C3 · Báo cáo phụ huynh gửi qua kênh nào? Tần suất? Ai duyệt trước khi gửi?

→ Nội dung báo cáo **đã làm xong** (`/giang-day/bao-cao/<lớp>/<em>`), in PDF
được. Còn thiếu đúng phần **gửi tự động**, mà phần đó phụ thuộc câu trả lời này
(Zalo OA? email? ai bấm nút gửi?).

## [ ] C4 · Quy trình thu chi kế toán thật? Có phần mềm kế toán đang dùng không?

→ Khối §7 (học phí, công nợ, thù lao, CRM). Đặc tả ghi rõ đây là khối **lớn
nhất** và *"không tận dụng được gì đã dựng"*. Khuyến nghị: cân nhắc **nối** với
phần mềm họ đang dùng thay vì viết lại — sai một chi tiết là sai sổ sách.

## [ ] C5 · Phút ngồi lớp có tính vào chỉ tiêu tự học hằng tuần không?

Xem 4.3 ở trên.

---

# Phần 6 — Nên làm, không gấp

## [ ] 6.1 · Nhánh Neon riêng cho CI

`pytest` đang chạy thẳng vào **CSDL học viên thật** mỗi lần push. Bộ test cuộn
lại ở cuối mỗi test, nhưng "cuộn lại" không phải "không đụng": nó vẫn chiếm kết
nối, vẫn giữ khoá, và một test viết ngoài giao dịch thì cuộn lại không cứu.

1. Neon → **Branches** → tạo nhánh từ `main`, đặt tên `ci`
2. Copy connection string của nhánh ấy
3. GitHub → repo → *Settings › Secrets and variables › Actions* → thêm secret
   **`DATABASE_URL_CI`**

Không phải sửa mã: job pytest đã đọc `DATABASE_URL_CI` trước, rơi về
`DATABASE_URL` khi chưa có. Mỗi lượt CI nay **in ra nó đang nối vào máy chủ nào**
(che mật khẩu), nên nhìn log là biết đã chuyển hay chưa.

*Vì sao không đổi thẳng `DATABASE_URL` sang nhánh: một tên secret cho hai nghĩa
là cách chắc chắn để một hôm nào đó ai đó trỏ nhầm nó về production.*

## [ ] 6.2 · Bốn câu DDL còn chờ — KHÔNG gấp

```bash
cd D:\pe_hsa\backend && .venv\Scripts\python.exe manage.py kiem_luoc_do
```

Đo 05/09: **4/9 mục chưa tới** — bốn khoá ngoại `§42`/`§43` vẫn là `NO ACTION`.

**Và đây là số đo, không phải câu trấn an.** `NO ACTION` nghĩa là xoá một tài
khoản sẽ bị chặn thay vì dọn theo — nhưng **không có đường nào trong mã xoá
`users`** (khu quản trị đổi `status`). Tức bốn mục này chưa chặn tính năng nào
đang chạy; chúng chỉ là chỗ CSDL còn lệch so với lược đồ đã khai.

Ngoài bốn mục ấy, còn **5 khoá ngoại khác** trỏ vào `users` cũng đang `NO ACTION`
(`account_emailaddress`, `socialaccount_socialaccount`,
`token_blacklist_outstandingtoken`, …). Nên nếu sau này anh muốn có nút "xoá hẳn
tài khoản", việc phải làm rộng hơn bốn câu này.

**Gộp `master` là xong luôn** (Render tự chạy `bootstrap_schema`). Tôi không tự
chạy — đổi chính sách xoá của một khoá ngoại là đổi ngữ nghĩa xoá trên CSDL thật,
không thuộc phần "DDL bổ sung" anh đã cho phép.

## [ ] 6.3 · `/thiet-ke` sẽ công khai

Đó là trang trưng bày component (design system), **không gác quyền**. Vô hại —
không có dữ liệu nào — nhưng sau khi gộp thì ai cũng mở được. Không muốn thì báo
tôi xoá tuyến ấy trước.

## [ ] 6.4 · Tuỳ chọn — cho tôi tự push

Lệnh `git push` bị bộ lọc quyền của chế độ auto chặn. Ba cách:

- **Anh tự chạy** `git push` khi cần — không đổi thiết lập gì
- **Cấp quyền hẹp:** tạo `D:\pe_hsa\.claude\settings.json`

  ```json
  { "permissions": { "allow": ["Bash(git push -u origin erp:*)"] } }
  ```

  Cố ý **hẹp**. Luật rộng `"Bash(git push:*)"` cho phép luôn `git push origin
  master`, tức là tôi deploy production được mà không hỏi ai.
- **Rời chế độ auto:** gõ `/permissions`, hoặc Shift+Tab

---

# Phần 7 — Công cụ: chạy thế nào

Cần hai máy chủ chạy sẵn:

```bash
cd D:\pe_hsa\backend  && .venv\Scripts\python.exe manage.py runserver 9000 --noreload
cd D:\pe_hsa\frontend && pnpm dev          # cổng 3100
```

`--noreload` là bắt buộc — thiếu nó thì sửa mã xong máy chủ vẫn chạy bản cũ, và
đã có một lần tôi đo nhầm vì đúng chuyện đó.

## Bộ kiểm

```bash
cd D:\pe_hsa\backend
.venv\Scripts\python.exe -m pytest -q            # 324 phép, ~22 phút, chạy vào Neon thật
.venv\Scripts\python.exe -m ruff check .

cd D:\pe_hsa\frontend
pnpm lint && pnpm exec tsc --noEmit
for %f in (e2e\unit\*.test.mjs) do node "%f"     # 15 bộ kiểm đơn vị
```

## Bộ đo giao diện — tương phản, vùng chạm, tràn ngang

```bash
python scripts\cap_the.py                  # thẻ sống 30 phút, KHÔNG ghi CSDL
cd scripts
node do_giao_dien.mjs --tu-kiem            # NÓ CÓ ĐỎ ĐƯỢC KHÔNG — chạy trước
node do_giao_dien.mjs                      # chủ đề sáng
node do_giao_dien.mjs --toi                # chủ đề tối
```

**Luôn chạy `--tu-kiem` trước khi tin số.** Nó nhét một quy tắc CSS hỏng vào rồi
đòi bộ đo phải bắt được; một bộ đo không đỏ được là một bộ đo giả. Hôm 05/09
chính phép tự kiểm ấy đã lộ ra hai trang mà bộ đo **chưa từng đo nổi** trong khi
vẫn ghi "0 vi phạm" cho chúng.

Thẻ hết hạn thì chạy lại `cap_the.py`.

## Bộ kiểm đầu-cuối và lượt quét bấm thử

```bash
cd D:\pe_hsa\frontend
set E2E_BASE_URL=http://localhost:3100 && pnpm e2e     # 11 phép, ~1 phút

cd D:\pe_hsa\scripts
node go_moi_nut.mjs --tu-kiem              # nó có bắt được lỗi không
node go_moi_nut.mjs                        # bấm 267 nút trên 17 màn
```

`go_moi_nut.mjs` chặn mọi lời gọi không phải GET, nên nó **không đổi được gì**
trong CSDL dù bấm trúng nút nào. Nó chính là thứ tìm ra hai lỗi ngày 05/09.

## Đối chiếu lược đồ với CSDL thật

```bash
cd D:\pe_hsa\backend && .venv\Scripts\python.exe manage.py kiem_luoc_do
```

---

# Phần 8 — Trạng thái hiện tại, đo ngày 05/09

| | |
|---|---|
| Nhánh | `erp`, đã push, **chưa gộp** vào `master` |
| Đi trước `master` | 112 commit · 232 tệp · +45.425 / −11.030 dòng |
| **`pytest` đầy đủ** | **324 đạt / 0 hỏng** (~22 phút) |
| `ruff` · `compileall` | 0 · 0 |
| **`next build`** | **thành công, 22 tuyến** |
| `pnpm lint` · `tsc` | 0 · 0 |
| `node --check` 13 tệp JS cũ | sạch |
| 15 bộ kiểm đơn vị Node | xanh |
| e2e Playwright | **11/11**, 0 phép bị bỏ qua |
| Bộ đo giao diện | 2 chủ đề × 32 lượt: **0 vi phạm**; tự kiểm ĐẠT 32/32 |
| Lượt quét bấm thử | 267 nút / 17 màn: **0 lỗi JS**; tự kiểm ĐẠT 17/17 |
| CSDL Neon | 53 bảng · 6 tài khoản · 1 lớp · 7 dòng ghi danh |
| Tầng JS cũ (không bundler) | 13 tệp · 7.383 dòng mã (đầu phiên 05/09: 15.134 dòng) |
| ERP §9 | khối 1, 2, 5 xong · khối 3 xong phần báo cáo, còn phần gửi · khối 4, 6, 7 chờ TopHSA |

## Chưa đo được — nói thẳng

- **Số chặng proxy thật của Render.** Mọi số liệu `NUM_PROXIES` đều đo ở máy;
  Phần 3 là để đo nó lần đầu.
- **Hành vi dưới tải thật.** Mọi lượt đo đều chạy với một người dùng; chưa có
  phép đo nào cho 30 người cùng lúc.
- **Thời gian build trên Render** sau khi thêm `openpyxl` + `django-redis`.
- **Hàng rào `/admin` với một tài khoản vai "Biên tập nội dung" thật** (xem 4.2).

---

# Phần 9 — Dữ liệu tôi đã tạo và đã xoá trên CSDL thật

Ghi ở đây vì đây là CSDL production và anh có quyền biết chính xác tôi đã chạm
vào cái gì.

## Đã TẠO — tài khoản kiểm thử, anh xoá lúc nào cũng được

```
users id=13231   e2e-kiem-thu@example.com   "KIỂM THỬ TỰ ĐỘNG (không phải học viên)"
```

- Tên đặt như vậy **cố ý**: nó sẽ hiện trong danh sách tài khoản khu Quản trị,
  và người nhìn phải biết ngay đó không phải học viên thật.
- XP = 0 nên không lọt bảng xếp hạng (bảng ấy sắp theo `xp` giảm dần).
- Sau một lượt chạy đủ bộ kiểm, nó để lại **0 dòng** ở `lesson_progress`,
  `learning_events`, `review_quiz_results`, `admin_audit`, `notifications`.
- Mật khẩu ngẫu nhiên, nằm ở `.the/e2e.json` (không vào git). Repo **không còn
  mật khẩu mặc định nào**.

```bash
python scripts\tai_khoan_e2e.py              # xem trước, không ghi
python scripts\tai_khoan_e2e.py --that       # tạo / đặt lại mật khẩu
python scripts\tai_khoan_e2e.py --xoa --that # gỡ sạch
```

## Đã chèn NHẦM rồi đã dọn — 6 dòng

Khi viết `scripts/cap_the.py` tôi tuyên bố nó "không ghi gì vào CSDL", dựa trên
suy luận "ký JWT thì cần gì CSDL". **Câu ấy sai.** `RefreshToken` của SimpleJWT
mang `BlacklistMixin`, và `for_user()` tạo một dòng
`token_blacklist_outstandingtoken`. Đếm trước/sau một lượt chạy: 490 → 491.

Bốn lượt chạy của tôi cộng hai lượt thử nghiệm đã chèn 6 dòng (id 821–826, đều
`user_id=7` — tài khoản quản trị). **Đã xoá sạch** trong một giao dịch có bảo
hiểm (số dòng xoá khác dự kiến thì cuộn lại):

```
493 → 487 · id lớn nhất còn lại 820 · 0 dòng mồ côi · dữ liệu người khác nguyên vẹn
```

`cap_the.py` nay mặc định **chỉ cấp thẻ access** (đo lại 491 → 491, không ghi
gì); muốn kèm refresh thì phải gõ `--co-refresh` và nó in cảnh báo trước.

Luật anh đặt là SELECT tự do, DDL bổ sung được, **ghi thì phải hỏi**. Tôi đã ghi
mà không hỏi. Bài học ghi lại ngay trong `cap_the.py`: một câu khẳng định về tác
dụng phụ mà chưa đo thì đúng bằng một dòng mã sai.
