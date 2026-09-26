# Ba nguồn anh Sơn gửi 26/09 — đọc gì, lấy gì, bỏ gì

Anh Sơn 26/09: *"nghiên cứu + áp dụng thêm các repos/skills này nếu phù hợp"*,
kèm *"Áp dụng SOLID vào xây dựng các Agent Skills"*. Tệp này trả lời cho từng
nguồn: đã lấy gì, đặt vào đâu, và chỗ nào **không lấy** cùng lý do.

Nguyên tắc chung: một nguồn chỉ đáng lấy khi nó giải một vấn đề ĐANG CÓ ở đây,
đo được. Lấy vì nó hay là cách nhanh nhất để dựng thêm thứ phải nuôi.

---

## 1 · browser-use/jev-ultrafast — LẤY, và đúng lúc

**Nguồn giải quyết gì**: tự động hoá trình duyệt chậm và tốn. Bên ấy hạ số lời
gọi giao thức trình duyệt từ **1.092 xuống 101** cho cùng một việc, bằng cách
gom quyết định, đọc trạng thái có cấu trúc thay vì chụp ảnh, và chờ theo dấu
hiệu với trần thời gian.

**Vấn đề đang có ở đây**: trưa 26/09 máy anh Sơn đứng — 11 Chromium giữ 788 MB
cho một tab trống, 22 tiến trình Node/Python mồ côi. Gốc rễ: 8 trên 9 bộ đo
trong `scripts/` mở trình duyệt mà không có `finally`.

**Đã lấy ba kỹ thuật**, đặt ở `scripts/lib/phien_do.mjs`:

| Kỹ thuật bên ấy | Thành gì ở đây |
|---|---|
| Tái dùng thay vì mở mới | Một trình duyệt cho cả lượt, mỗi vai một trang dùng lại (cũ: 4 ngữ cảnh + 4 trang cho 4 màn) |
| Không chụp ảnh khi không cần | Ảnh tắt mặc định, bật bằng `--anh` |
| Chờ theo dấu hiệu, có trần | Chờ `main` có chữ và chiều cao thôi đổi, trần 4 s (cũ: ngủ cứng 6 s mỗi màn) |

**Đo sau khi áp**: 5 màn trong **17,8 s**, Chromium còn sót **0** — kể cả khi cố
tình trỏ bộ đo vào một cổng chết.

**Không lấy**: phần lõi của họ — mô hình chọn thao tác và phần tử trong một vòng
mạng. Bộ đo ở đây không cần agent điều khiển trình duyệt; nó biết trước phải mở
màn nào và đếm gì.

---

## 2 · cloudflare/security-audit-skill — LẤY hai nguyên tắc, bỏ sáu pha

**Nguồn giải quyết gì**: biến agent thành người soát bảo mật, qua sáu pha
(trinh sát → săn theo sổ bao phủ → xác minh → kết quả có cấu trúc → kiểm chéo →
báo cáo), với bộ xác thực JSON bằng Node và hơn 12 nhóm tấn công.

**Đã lấy hai nguyên tắc**, đặt ở `.claude/skills/soat-bao-mat/SKILL.md`:

1. **Người tìm khác người xác minh.** Trùng khít với mô hình anh Sơn đang yêu
   cầu: một agent làm, một agent soát. Một mình thì đổi vai có ý thức — viết
   phát hiện ra giấy rồi quay lại cố chứng minh nó sai.
2. **Không có vết nguồn thì chưa phải phát hiện.** Mỗi mục phải có `tệp:dòng`,
   đường đi từ đầu vào tới chỗ nguy hiểm, và một kết quả quan sát được. "Có vẻ
   thiếu kiểm tra" là câu hỏi, không phải phát hiện. Đây đúng là RULES §2 của
   dự án, nói bằng chữ khác.

**Thành sản phẩm**: `scripts/quet_bi_mat.py` + bước **f8** của `pre-push`. Repo
này CÔNG KHAI, mà 13 bước trước đó không bước nào đọc nội dung tệp sắp đẩy.

Bản đầu kêu oan cả **7 chỗ** (`user:password@`, `u:matkhau@`,
`postgres:tam@localhost` — toàn mật khẩu mẫu). Siết lại: **0 báo oan trên 698
tệp**, vẫn bắt đủ 4 loại bí mật thật trên tệp thử. Một cổng kêu oan là một cổng
sắp bị tắt đi.

**Tìm được thật**: `PROGRESS.md` trên GitHub — cả `erp` lẫn `master` — mang
đường dẫn `C:/Users/<tên tài khoản>/…` ở hai chỗ. Không phải khoá, nhưng RULES
§10 cấm.

**Không lấy**: sáu pha đầy đủ và bộ xác thực JSON. Quy mô ấy hợp với một tổ chức
soát mã của người lạ. Ở đây phần đắt nhất là quét bí mật và bốn câu hỏi về xác
thực / phân quyền / cách ly dữ liệu / cửa mở — đã nằm trong kỹ năng.

---

## 3 · HKUDS/LightRAG — ĐỌC, và CHƯA dựng

**Nguồn giải quyết gì**: RAG dựa trên đồ thị tri thức. Trích thực thể và quan hệ
từ tài liệu, truy hồi hai tầng (cục bộ theo thực thể, toàn cục theo chủ đề), cập
nhật tăng dần thay vì lập chỉ mục lại. Rẻ và nhanh hơn GraphRAG vì bỏ phần báo
cáo cộng đồng.

**Vấn đề nó nhắm tới có ở đây không**: có một nửa. Tài liệu dự án đã **19.019
dòng** (`PROGRESS.md` một mình 9.500), và mỗi phiên mới đều tốn token đọc lại —
đúng điều anh Sơn muốn giảm.

**Vì sao vẫn chưa dựng**:

- **Phần MÃ NGUỒN đã có đồ thị tốt hơn.** `scripts/ban_do.mjs` dựng **477 nút,
  1.586 cạnh** (tuyến → view → quyền → bảng, khoá ngoại, cầu sang JS cũ) từ cây
  cú pháp — **tất định và đúng**. Đồ thị của LightRAG do mô hình trích ra, nên
  có thể sai và không ai biết nó sai. Thay một thứ đúng bằng một thứ có thể sai
  là đi lùi.
- **Chỉ mục cũ đi nhanh hơn ta lập lại.** Mã ở đây đổi hàng ngày; lập chỉ mục
  lại cần gọi mô hình cho từng tài liệu, tức đúng khoản token anh Sơn muốn tiết
  kiệm.
- **Thêm một hạ tầng phải nuôi**: kho vector, khoá API, một chỗ nữa để hỏng lúc
  deploy.

**Điều kiện dựng lại** (viết ra để lần sau khỏi cãi nhau bằng cảm tính): khi
người trong nhóm phải tra cứu chéo tài liệu nhiều lần mỗi ngày mà `grep` và
`BAN-GIAO-PHIEN.md` không đủ, **hoặc** khi tài liệu vượt chừng 40.000 dòng.
Lúc ấy Postgres đã có sẵn (Neon), nên phần hạ tầng rẻ đi nhiều.

**Lấy được ngay mà không cần dựng**: ý *truy hồi hai tầng*. Đây chính là cái
`BAN-GIAO-PHIEN.md` (tổng quan) + `PROGRESS.md` (chi tiết) đang làm — và cũng
là luật **bóc lớp dần** của `docs/HUONG_GIAO_DIEN_2026-09-26.md`. Cùng một ý,
ba chỗ khác nhau.

---

## 4 · SOLID cho Agent Skills — LÀM

`.claude/skills/README.md` viết ra năm câu hỏi SOLID hỏi về một kỹ năng, kèm chỗ
đã sai. Ba kỹ năng đầu: `do-man-that`, `soat-bao-mat`, `giao-viec-agent`.

Chữ **D** là chữ đắt nhất ở đây, và là chữ đã trả giá: kỹ năng gọi
`python scripts/quet_bi_mat.py` chứ không chép regex vào bài, vì bản sao thứ hai
bao giờ cũng là bản sai sau vài tháng. Đúng lỗi mà bảy bộ đo đã mắc khi mỗi cái
tự lo vòng đời trình duyệt.
