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

## Số liệu nền (đo lại 17/09/2026)

Bảng này từng ghi số đo 01/09/2026 và đứng yên trong khi hệ đi tiếp — "53 bảng ·
220 phép kiểm" đọc lúc 17/09 đã sai gần một nửa. Nên mỗi dòng nay kèm **lệnh đo
ra nó**: số cũ không tự dán nhãn là cũ, nhưng lệnh thì chạy lại được.

| | | đo bằng |
|---|---:|---|
| Bảng trong CSDL | 57 (42 nghiệp vụ + 15 khung) | `python manage.py ve_erd` |
| Khoá ngoại trong khối nghiệp vụ | 67 | `ve_erd` |
| Tuyến API thật | 122 | 137 `path(...)` trừ 15 `include(...)` trong 15 tệp `urls.py` |
| App Django của dự án | 15 (+ gói `config`) | `INSTALLED_APPS` |
| Trang Next.js | 28 (+ 4 route handler) | đếm `page.tsx` / `route.ts` trong `src/app` |
| Bài học có nội dung | 76 (158 hình) | `SELECT count(*) FROM lessons` |
| Phép kiểm phía máy chủ | 792 (42 tệp) | `pytest --collect-only -q` |
| Phép kiểm phía giao diện | 27 tệp đơn vị + 11 kịch bản Playwright | `node --test "e2e/unit/*.test.mjs"` |
| Tài khoản | 53, trong đó 48 là dữ liệu trình diễn | `SELECT is_demo, count(*) FROM users GROUP BY 1` |

Con số **298 endpoint** ở bản cũ không tái lập được bằng cách đếm nào ở trên; nhiều
khả năng nó đếm cả `path()` của Django admin và allauth. Nếu cần so với bản cũ thì
so bằng lệnh, đừng so bằng con số.

Dòng cuối là dòng quan trọng nhất khi đọc mọi tài liệu ở đây. 53 tài khoản nghe
như một hệ đang chạy, nhưng **48 trong đó là dữ liệu trình diễn**: hệ này đang
phục vụ **5 người thật**. Mọi quyết định "làm cho đúng quy mô" phải nhìn con số 5,
không nhìn con số 53. Xem `TODO.md` mục N1 để biết vì sao chưa nên xây mô hình
năng lực kiểu Elo.

## Bản đọc một lượt cho người tiếp nhận

Bốn tài liệu trên viết cho người sửa mã hằng ngày. Người mới nhận bàn giao cần một
bản đi hết một lượt — kiến trúc, hạ tầng, dữ liệu, phân quyền, luồng, quy trình,
cổng kiểm, rủi ro — có sơ đồ vẽ sẵn. Bản ấy là **hồ sơ kỹ thuật dạng PDF**, dựng
17/09/2026, 27 trang, 16 sơ đồ. Tệp không nằm trong kho (đi kèm khi bàn giao); kịch
bản dựng ra nó không phải một phần của mã sản phẩm.
