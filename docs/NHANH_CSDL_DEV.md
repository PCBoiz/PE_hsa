# Tách cơ sở dữ liệu: nhánh `dev` và nhánh `ci`

**Vấn đề:** máy lập trình và production đang dùng **chung một cơ sở dữ liệu**.

Cụ thể là `DATABASE_URL` trong `backend/.env` ở máy và `DATABASE_URL` trên Render trỏ vào
đúng một chỗ. Hệ quả:

- Chạy `manage.py` ở máy là **ghi thẳng vào dữ liệu học viên thật**.
- Bộ 87 test tự động cũng chạy trên đó (`backend/conftest.py` có rollback cuối mỗi test,
  nhưng rollback không cứu được một lệnh `bootstrap_schema` hay một script chạy sai).
- Thêm cột, sửa bảng, thử nghiệm — tất cả đều diễn ra trên dữ liệu đang chạy thật.

Một người cẩn thận thì còn kiểm soát được. Nhưng ngay lúc này, việc thêm cột
`must_change_password` cho tính năng tài khoản đang bị chặn vì lý do đó.

---

## Neon branch là gì (nói cho gọn)

Neon cho **tách nhánh cơ sở dữ liệu** giống hệt cách Git tách nhánh mã nguồn:

- Nhánh mới có **toàn bộ dữ liệu** tại đúng thời điểm tách.
- Nó **gần như không tốn thêm dung lượng** — Neon chỉ lưu phần khác biệt kể từ lúc tách
  (cơ chế copy-on-write), nên tách một cơ sở dữ liệu 2 GB không tốn thêm 2 GB.
- Ghi vào nhánh **không chạm** nhánh chính. Xoá nhầm cả bảng ở nhánh `dev` thì production
  vẫn nguyên vẹn.
- Tách xong trong khoảng 10 giây, và **xoá nhánh rồi tách lại** cũng nhanh như vậy — nên
  khi dữ liệu dev lệch quá xa thì cứ làm mới, đừng ngồi đồng bộ tay.

Gói miễn phí của Neon có giới hạn số nhánh, nhưng hai nhánh thì thoải mái.

---

## Các bước — khoảng 5 phút

### 1. Tạo hai nhánh

1. Vào [console.neon.tech](https://console.neon.tech) → chọn project pe_hsa.
2. Vào mục **Branches** → **New Branch**.
3. Tạo nhánh thứ nhất:
   - **Name**: `dev`
   - **Parent branch**: `main` (hoặc `production` — tên nhánh gốc đang có)
   - **Include data up to**: *Current point in time*
4. Lặp lại, tạo nhánh thứ hai tên `ci`.

> Vì sao tách riêng nhánh cho CI: mỗi lần push mã, GitHub chạy 87 test. Nếu chúng dùng
> chung nhánh `dev` thì bạn đang gõ lệnh còn CI xoá dữ liệu dưới chân bạn — vừa khó hiểu
> vừa làm test đỏ oan.

### 2. Lấy chuỗi kết nối của từng nhánh

Trong Neon Console → **Connection Details** → chọn đúng **Branch** ở ô trên cùng → chép
chuỗi *Connection string*.

**Hai điều bắt buộc phải đúng:**

- Chuỗi phải có **`-pooler`** trong tên máy chủ. Ví dụ:
  `postgresql://…@ep-abc-123-pooler.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require`
  Thiếu `-pooler` thì mỗi tiến trình chiếm một kết nối thật và rất nhanh chạm trần.
- Phải có **`?sslmode=require`** ở cuối.

### 3. Đổi ở máy lập trình

Mở `backend/.env`, thay giá trị `DATABASE_URL` bằng chuỗi của nhánh **`dev`**.

```
DATABASE_URL=postgresql://…-pooler….neon.tech/neondb?sslmode=require
```

Rồi khởi động lại backend. **Không đổi gì trên Render** — production giữ nguyên nhánh chính.

### 4. Đổi cho CI

GitHub → repo `PCBoiz/PE_hsa` → **Settings** → **Secrets and variables** → **Actions** →
sửa secret `DATABASE_URL` thành chuỗi của nhánh **`ci`**.

(`.github/workflows/ci.yml` đang đọc đúng secret này, không phải sửa file workflow.)

### 5. Kiểm chứng đã tách thật

Chạy ở máy:

```bash
cd backend
.venv/Scripts/python manage.py bootstrap_schema
```

Rồi vào Neon Console xem **nhánh `main` không có gì thay đổi**, còn nhánh `dev` đã có cột
mới. Nếu nhánh `main` cũng đổi theo thì `.env` chưa được đổi đúng.

---

## Sau khi xong thì đưa tôi cái gì

Chỉ cần **chuỗi kết nối nhánh `dev`**. Tôi sẽ:

1. Chạy `bootstrap_schema` để thêm hai cột mới cho tính năng tài khoản
   (`must_change_password`, `password_changed_at`).
2. Kiểm luồng thật: quản trị đặt lại mật khẩu → học viên đăng nhập bằng mật khẩu tạm →
   bị buộc đổi → vào học được.
3. Chạy 87 test trên nhánh `ci` mà không lo đụng dữ liệu thật.

---

## Production thì thêm cột lúc nào

**Tự động, không phải làm gì.** `render.yaml` đã có `bootstrap_schema` trong bước dựng bản:

```yaml
buildCommand: >-
  pip install -r requirements.txt &&
  python manage.py collectstatic --noinput &&
  python manage.py bootstrap_schema &&
  python manage.py migrate --noinput
```

Lệnh này **idempotent** — mọi câu lệnh đều là `CREATE TABLE IF NOT EXISTS` hoặc
`ALTER TABLE … ADD COLUMN IF NOT EXISTS`, nên chạy lại bao nhiêu lần cũng không sao. Nó
chạy **trước** khi ứng dụng khởi động, nên không có khoảnh khắc nào mã mới gặp bảng cũ.

---

## Khi dữ liệu nhánh dev lệch quá xa

Đừng ngồi đồng bộ tay. Xoá nhánh `dev` trong Neon Console rồi tạo lại từ `main` — mất chưa
tới một phút và bạn có lại bản sao dữ liệu thật mới nhất. Nhớ chép lại chuỗi kết nối mới
vào `.env` (chuỗi đổi theo nhánh).

---

## Vài cái bẫy

| Bẫy | Dấu hiệu | Cách xử lý |
|---|---|---|
| Quên `-pooler` | Sau một lúc báo hết kết nối | Lấy lại chuỗi, chọn đúng bản có `-pooler` |
| Đổi nhầm `DATABASE_URL` trên Render | Học viên thật mất dữ liệu mới | Render **không được đổi**; chỉ đổi `.env` ở máy và secret của CI |
| Neon ngủ (gói miễn phí) | Truy vấn đầu tiên chậm vài giây | Bình thường; có sẵn cơ chế thử lại trong `common/db.py` |
| Chạy `bootstrap_schema` khi `.env` còn trỏ production | Cột mới xuất hiện ở production sớm hơn dự định | Không hỏng gì (lệnh idempotent), nhưng nên đổi `.env` trước |

---

*Viết 27/08/2026. Việc này là hạng mục P0 trong [CONG_VIEC_SPRINT1.csv](CONG_VIEC_SPRINT1.csv)
(mã DB-01) và là rủi ro cao nhất trong [BAN_GIAO_2026-08-24.md](BAN_GIAO_2026-08-24.md) §9.*
