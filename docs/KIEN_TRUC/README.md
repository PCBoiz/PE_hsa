# Kiến trúc pe_hsa — đọc theo thứ tự này

Bốn tài liệu, mỗi cái trả lời một câu hỏi khác nhau. Đọc từ trên xuống nếu bạn
mới vào; nhảy thẳng vào cái cần nếu bạn đã quen.

| Tài liệu | Trả lời câu hỏi | Sinh ra hay viết tay |
|---|---|---|
| [C4.md](C4.md) | Hệ này gồm những gì, chạy ở đâu, ai gọi ai? | viết tay |
| [ERD.md](ERD.md) | Dữ liệu nằm ở đâu, nối với nhau thế nào? | **SINH RA** từ CSDL |
| [USE_CASE.md](USE_CASE.md) | Ai làm được gì? | viết tay |
| [LUONG_CHAM_DIEM.md](LUONG_CHAM_DIEM.md) | Một câu trả lời của học viên đi đường nào để thành con số trên bản đồ năng lực? | viết tay |

## Giữ cho tài liệu KHÔNG nói dối

Một sơ đồ vẽ sai còn tệ hơn không có sơ đồ: nó tắt phản xạ đi đọc mã. Cả bộ này
được viết sau khi một chú thích sai làm hỏng một bản vá thật (xem `RULES.md`
§20), nên quy tắc ở đây chặt hơn bình thường.

**ERD.md được SINH RA.** Đừng sửa tay. Đổi lược đồ thì chạy lại:

```bash
cd backend && python manage.py ve_erd > ../docs/KIEN_TRUC/ERD.md
```

Nó đọc `information_schema` của chính CSDL đang chạy, nên không thể lệch. Phần
DUY NHẤT phải bảo trì tay là bảng phân miền `MIEN` trong
`backend/common/management/commands/ve_erd.py` — thêm bảng mới mà quên xếp miền
thì tài liệu tự in ra một cảnh báo, không im lặng bỏ qua.

**Ba tài liệu còn lại viết tay**, nên chúng có hạn dùng. Mỗi con số trong đó đều
kèm ngày đo. Khi sửa kiến trúc, sửa luôn tài liệu trong CÙNG lượt — chú thích và
mã trôi khỏi nhau đúng lúc người viết đang tập trung vào việc khác.

## Số liệu nền (đo 01/09/2026)

| | |
|---|---:|
| Bảng trong CSDL | 53 (38 nghiệp vụ + 15 khung) |
| Khoá ngoại trong khối nghiệp vụ | 57 |
| Endpoint (`path(...)` trong `urls.py`) | 298 |
| App Django | 16 |
| Route Next.js | 20 |
| Bài học có nội dung | 76 |
| Phép kiểm tự động | 220 |
| Tài khoản thật | 5 |

Con số cuối cùng là con số quan trọng nhất khi đọc mọi tài liệu ở đây: **hệ này
đang phục vụ 5 người**. Mọi quyết định "làm cho đúng quy mô" phải nhìn nó trước.
Xem `TODO.md` mục N1 để biết vì sao chưa nên xây mô hình năng lực kiểu Elo.
