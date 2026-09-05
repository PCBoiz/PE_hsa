# Gộp `erp` → `master`: đo trước, rồi mới bấm

*Viết 05/09/2026. Mọi con số ở đây là ĐO trên chính CSDL và mã đang chạy, không
phải ước lượng — chỗ nào chưa đo được thì nói rõ là chưa đo.*

`render.yaml` có `autoDeploy: true` và `branch: master`. `DEPLOY.md` ràng buộc
Vercel cũng chỉ deploy từ `master`. Nên **gộp = đẩy cả backend lẫn frontend lên
production ngay lập tức**. Không có bước bấm xác nhận nào ở giữa.

---

## 1 · Quy mô

```
112 commit · 232 tệp · +45.425 / −11.030 dòng
master KHÔNG đi trước erp → fast-forward, không xung đột
```

Đây không phải một bản vá nhỏ. Frontend đổi ~22.000 dòng và **kiến trúc gọi API
đổi hẳn**: `master` gọi thẳng Django từ trình duyệt, `erp` đi qua một lớp trung
gian trên Vercel (`src/lib/proxy.ts`, token trong cookie httpOnly). Mục 3 nói vì
sao điều đó là chuyện lớn nhất của lần deploy này.

---

## 2 · Đã đo: những thứ SẼ chạy khi deploy

### 2.1 · Bước DDL — **an toàn, đã diễn tập trên CSDL thật**

`buildCommand` chạy `bootstrap_schema`, và lệnh ấy **ném ở câu lệnh lỗi đầu
tiên**. Nên tính idempotent là điều kiện sống còn của build.

Đã diễn tập: mở một giao dịch trên chính CSDL production, chạy **cả 193 câu**
của `legacy_schema.sql` + `mockexam_schema.sql`, rồi cuộn lại.

```
TRƯỚC: 53 bảng, 75 khoá ngoại, 167 chỉ mục
193 câu lệnh chạy SẠCH
SAU  : 53 bảng, 75 khoá ngoại, 167 chỉ mục   ← cuộn lại, không đổi gì
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

### 2.2 · Phụ thuộc mới

`django-redis==5.4.0` và `openpyxl>=3.1`. Cả hai thuần Python, không cần trình
biên dịch trên Render.

### 2.3 · Không có bí mật nào lọt vào 112 commit

Quét toàn bộ diff theo đúng hình dạng bí mật của dự án (chuỗi Neon, `sk-…`,
`AIza…`, `GOCSPX-…`). Ba chuỗi tìm thấy đều là **ví dụ trong tài liệu**
(`nguoi:matkhau`, `ep-abc-123`). Tệp bị theo dõi chỉ có `.env.example`, và giá
trị trong đó đều là chỗ trống. `.gitignore` đã chặn `.env`, `.env.*`, `.the/`,
`test-results/`.

### 2.4 · Cổng kiểm — chạy đủ, tại chỗ, đúng những gì CI chạy

| bước | kết quả |
|---|---|
| `ruff check` | 0 |
| `compileall` 16 khu | 0 |
| **`pytest` ĐẦY ĐỦ** | **324/324 xanh** (22 phút, chạy thẳng vào Neon) |
| `pnpm lint` (đã có `no-undef` cho tầng cũ) | 0 |
| `tsc --noEmit` | 0 |
| `node --check` 13 tệp JS cũ | sạch |
| 15 bộ kiểm đơn vị Node | xanh |
| **`next build`** | **thành công, 22 tuyến** |
| e2e Playwright | 11/11, 0 bỏ qua |
| bộ đo giao diện, 2 chủ đề × 32 lượt | 0 vi phạm; tự kiểm ĐẠT 32/32 |
| lượt quét bấm thử, 267 nút / 17 màn | 0 lỗi JS; tự kiểm ĐẠT 17/17 |

`next build` là bước Vercel sẽ chạy, và trước hôm nay tôi chưa lần nào chạy nó.

---

## 3 · CHẶN CỨNG — hai việc phải làm TRƯỚC khi gộp

### 3.1 · Xoay `SECRET_KEY` — nếu quên, **deploy trượt** (không sập)

`config/settings.py` từ chối khởi động ở production với khoá dưới 32 byte. Khoá
hiện tại 19 byte.

Đã đo từng bước của `buildCommand` với khoá ngắn:

```
collectstatic     rc=1  RuntimeError: SECRET_KEY dài 19 byte, cần tối thiểu 32
bootstrap_schema  rc=1  (cùng lỗi)
migrate           rc=1  (cùng lỗi)
```

Cổng nổ ở bước build **đầu tiên**, trước cả khi chạm CSDL và trước khi gunicorn
khởi động. Nên hậu quả của việc quên là *build hỏng, bản cũ vẫn phục vụ* — khó
chịu, không phải sự cố. Nhưng vẫn phải làm trước, nếu không lần gộp ấy vô ích.

```bash
python -c "import secrets;print(secrets.token_urlsafe(48))"
```

Dán vào Render → `pe-hsa-backend` → Environment → `SECRET_KEY`.

**Hệ quả:** mọi người đang đăng nhập bị đăng xuất, phải đăng nhập lại. Mật khẩu
không ảnh hưởng.

### 3.2 · Bí mật proxy — nếu quên, **cả lớp chung một xô giới hạn**

Đây là việc dễ bỏ sót nhất, và là thứ duy nhất trong danh sách có thể gây sự cố
cho người dùng thật ngay ngày đầu.

`master` hôm nay: trình duyệt gọi **thẳng** Django, biên Render nối IP thật vào
`X-Forwarded-For` → mỗi người một khoá giới hạn.

`erp` sau khi gộp: trình duyệt gọi Vercel, `proxy.ts` **cố ý gỡ**
`x-forwarded-for` (để trình duyệt không tự đặt được khoá — lỗ đã đo 30/08: 300
lần đăng nhập kèm XFF ngẫu nhiên thì 300 lần lọt). `fetch` của Node không thêm
lại. Django do đó chỉ thấy **IP egress của Vercel**.

Đo được:

```
qua Vercel, người A   → khoá = 76.76.21.9
qua Vercel, người B   → khoá = 76.76.21.9      ← CÙNG một khoá
```

Trần áp lên khoá ấy, dùng chung cho mọi người:

| trần | khoá có kèm tên endpoint? | hệ quả |
|---|---|---|
| `login` **20/phút** | KHÔNG | lớp 30 em vào cùng giờ → 10 em ăn 429 |
| `register` **10/phút** | KHÔNG | đăng ký hàng loạt bị chặn |
| `ip_hour` 1000/giờ | CÓ | mỗi endpoint một quota, ít khả năng chạm |

Hai trần đầu là thứ cắn thật. Đặt bí mật thì hết:

```
CÓ bí mật, người A qua Vercel            → khoá = 1.1.1.1
CÓ bí mật, người B qua Vercel            → khoá = 2.2.2.2
kẻ gọi THẲNG Render, giả header, sai bí mật → khoá = 9.9.9.9  (IP thật của họ)
```

Tức bí mật vừa trả lại khoá theo từng người, vừa giữ nguyên hàng rào chống giả
header. Đặt **cùng một giá trị** ở hai nơi:

```
Render → pe-hsa-backend → PROXY_SHARED_SECRET
Vercel → PE_PROXY_SECRET        (server-side, TUYỆT ĐỐI không NEXT_PUBLIC_)

sinh: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Bí mật phải dài **≥ 16 ký tự**; ngắn hơn thì `common/net.py` coi như chưa cấu
hình và bỏ qua header — cố ý, để một cấu hình nửa vời không mở toang.

---

## 4 · Nên làm, không chặn

- **Redis** (`REDIS_URL` trên Render). `render.yaml` chạy `--workers 2`, mỗi
  worker giữ một `LocMemCache` riêng, nên mọi trần hiện đang bị **nhân đôi** —
  đặt 20 lượt đăng nhập/phút thì thực tế là 40. Có biến thì dùng Redis, không có
  thì chạy y như cũ; không phải sửa dòng mã nào.
- **Đo `NUM_PROXIES` thật** sau khi deploy: mở `/api/admin/do-proxy` bằng trình
  duyệt và xem `ipHienTai` có bằng IP thật của anh không. Bằng thì con số đang
  đúng. Đường này nay trả thẳng kết luận chứ không bắt anh tự suy.
- `/thiet-ke` là trang trưng bày component, **không gác quyền** — vô hại (không
  có dữ liệu) nhưng sẽ công khai. Nếu không muốn thì xoá tuyến ấy trước.

---

## 5 · Trình tự đề nghị

```
1. Đặt SECRET_KEY mới trên Render                    (§3.1)
2. Đặt PROXY_SHARED_SECRET + PE_PROXY_SECRET         (§3.2)
3. (nên) tạo Key Value trên Render → REDIS_URL       (§4)
4. Ghi lại commit master hiện tại — đường lùi:
       git rev-parse origin/master
5. Gộp:
       git checkout master && git merge --ff-only origin/erp && git push
6. Nhìn Render Build log: `bootstrap_schema` phải in
       "public base tables: 53 -> 53 (193 statements OK)"
7. Nhìn /health → {"status":"ok"}
8. Mở /api/admin/do-proxy, kiểm `ipHienTai`
9. Đăng nhập bằng một tài khoản thật (mọi người đã bị đăng xuất ở bước 1)
```

**Đường lùi** nếu deploy hỏng: Render giữ bản build trước, nên build hỏng ở bước
6 KHÔNG làm sập gì. Nếu bản mới lên rồi mới lộ vấn đề thì
`git reset --hard <commit ghi ở bước 4> && git push --force-with-lease` — nhưng
lưu ý DDL của §2.1 **không tự lùi** (bốn khoá ngoại vẫn ở chính sách mới). Chúng
không phá dữ liệu, chỉ đổi hành vi khi XOÁ tài khoản, mà hiện **không có đường
nào trong mã xoá `users`** (đã đo — khu quản trị đổi `status`).

---

## 6 · Chưa đo được, nói thẳng

- **Số chặng proxy thật của Render** — mọi số liệu `NUM_PROXIES` đều đo ở máy.
  Bước 8 ở trên là để đo nó lần đầu.
- **Hành vi dưới tải thật.** Bộ đo giao diện và lượt quét bấm thử đều chạy với
  một người dùng; chưa có phép đo nào cho 30 người cùng lúc.
- **Thời gian build trên Render.** Thêm `openpyxl` + `django-redis` làm bước
  `pip install` dài thêm, chưa đo là bao nhiêu.
