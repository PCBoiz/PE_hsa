---
name: soat-bao-mat
description: Soát bảo mật pe_hsa — dùng trước khi đẩy lên nhánh công khai, khi thêm tuyến API hay quyền mới, khi đụng vào xác thực/phân quyền/tải tệp, khi mở một cửa cho người chưa đăng nhập, hoặc khi anh Sơn hỏi "chỗ này có an toàn không". Cũng dùng để quét bí mật lọt vào repo (repo này CÔNG KHAI). Không dùng cho việc đổi chữ hay sửa giao diện thuần tuý.
---

# Soát bảo mật

Repo này **công khai**, và hạ tầng phải làm như thật dù mọi dữ liệu còn là giả
(anh Sơn 26/09). Cách làm dưới đây rút từ `cloudflare/security-audit-skill`, giữ
hai nguyên tắc cốt lõi của nó và bỏ phần quá nặng cho một dự án cỡ này.

## Hai nguyên tắc không được bỏ

1. **Người tìm khác người xác minh.** Ai nêu ra một lỗ thì KHÔNG phải người kết
   luận nó có thật. Trong dự án này: agent làm việc và agent soát là hai agent
   khác nhau (anh Sơn chốt trần 2 agent). Một mình thì đổi vai có ý thức: viết
   phát hiện ra giấy, rồi quay lại **cố chứng minh nó sai**.
2. **Không có vết nguồn thì chưa phải phát hiện.** Mỗi mục phải có `tệp:dòng`,
   đường đi từ đầu vào của người dùng tới chỗ nguy hiểm, và **một kết quả quan
   sát được** — mã trả về, dòng trong CSDL, ảnh chụp. "Có vẻ thiếu kiểm tra" là
   một câu hỏi, không phải một phát hiện.

## Các bước

### 1 · Quét bí mật (luôn chạy, < 2 giây)

```bash
python scripts/quet_bi_mat.py            # tệp sắp đẩy
python scripts/quet_bi_mat.py --tat-ca   # toàn repo
python scripts/quet_bi_mat.py --tu-kiem  # đòi bộ quét phải đỏ được
```

Đã nằm trong `pre-push` (bước f8). Chạy tay khi vừa dán gì đó từ nơi khác vào.

### 2 · Khoanh vùng đã đổi

Chỉ soát phần khác `origin/master`, theo bốn hướng — nhiều hơn thì loãng:

| Hướng | Câu hỏi | Chỗ xem |
|---|---|---|
| Xác thực | Tuyến mới có `IsAuthenticated` chưa? Có tuyến nào `AllowAny` không? | `backend/*/views.py` |
| Phân quyền | Người vai R gọi được API của vai khác không? | `backend/common/permissions.py` |
| Cách ly dữ liệu | Câu SQL có buộc `user_id`/`class_id` của chính người gọi không? | mọi `q(...)` mới |
| Cửa mở | Có gì nhận đầu vào mà không giới hạn nhịp? | `throttle_classes` |

### 3 · Đo, đừng suy

```bash
python scripts/quet_quyen.py             # ma trận vai × tuyến
node scripts/tang_vai.py --kiem          # trang cho vai R mà API từ chối R
node scripts/do_dau_bao_mat.mjs          # dấu bảo mật ở tầng trình duyệt
```

Nghi một tuyến hở thì **gọi thử bằng thẻ của vai không được phép** và chép lại mã
trả về. Đó là "kết quả quan sát được".

### 4 · Viết ra

Mỗi phát hiện: *đường đi từ đầu vào tới chỗ nguy hiểm · `tệp:dòng` · thứ đã quan
sát được · sửa thế nào*. Xếp theo tác động thật, không theo nhãn "cao/trung/thấp"
lấy từ danh sách nào đó.

## Cổng kiểm

- `python scripts/quet_bi_mat.py` sạch
- `bash .githooks/pre-push < /dev/null` ĐẠT — không `--no-verify`
- Tuyến mới có phép kiểm chứng minh nó **từ chối đúng người cần từ chối**, không
  chỉ phép kiểm đường thuận

## Chỗ nới

Thêm loại bí mật: thêm một `Luat` vào `LUAT` trong `scripts/quet_bi_mat.py`.
`--tu-kiem` tự phủ luôn quy tắc mới vì nó đọc `mau_gia`.

## Ranh giới

- Không đọc, in, sửa hay commit `.env`, khoá, mật khẩu.
- Thư và tin nhắn ra khỏi hệ thống là không thu lại được: chỉ gửi tới địa chỉ thử
  (`@example.com`, tài khoản e2e).
- Không dựng công cụ tấn công, không dò quét dịch vụ của người ngoài. Phạm vi là
  mã của chính dự án này.
