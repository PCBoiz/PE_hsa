# Những gì hệ thống làm được — bản chốt 27/09/2026

**Ai đọc tệp này**: anh Sơn, và dùng được để đưa TopHSA xem. Mỗi dòng nói **người dùng bấm được
gì**, không nói mã làm thế nào. Chỗ nào chưa làm được thì viết thẳng là chưa.

**Bản đang chạy**: production (`master`) = commit `198dc81`, đẩy 27/09/2026 — 63 commit từ bản
trước. Đã kiểm sau khi đẩy: `pe-hsa-backend.onrender.com/api/health` trả 200, `pe-hsa.vercel.app`
mở được, và cửa mới nhất trong lượt đẩy (`/auth/dang-ky` của §73) trả 200 — nghĩa là build xanh
và lược đồ CSDL đã chạy xong.

**Trước buổi demo phải chạy một lệnh**: `python manage.py du_lieu_mau --lam-moi` trên production.
Không chạy thì khách bấm "Chương trình" sẽ thấy *"Lớp chưa nhận khung chương trình"* — sáu ô của
bảng phân rã trông như chưa làm, dù mã đúng hết. Lệnh chỉ gỡ và dựng lại dữ liệu mẫu trong MỘT
giao dịch, mất khoảng hai phút.

**Cảnh báo dữ liệu**: mọi dữ liệu đang có, kể cả trên production, đều là GIẢ. Chưa có một dòng
dữ liệu thật nào của TopHSA.

---

## 1 · Quản trị viên

| Làm được gì | Bấm ở đâu | Ghi chú thật |
|---|---|---|
| Tạo / sửa / khoá tài khoản, đổi vai, đặt lại mật khẩu | Quản trị → Tài khoản | 6 vai: quản trị, quản lý học vụ, giảng viên, trợ giảng, học viên, biên tập nội dung |
| Tìm người theo tên / email / SĐT, mở hồ sơ | Quản trị → Tài khoản → ô tìm | |
| Tải danh sách tài khoản (.xlsx / .csv), lọc theo đợt học, môn, ngày cấp | Quản trị → Tài khoản → "Tải danh sách" | **Chỉ quản trị viên thấy hộp này** — học vụ mở cùng trang thì không có. Chờ anh quyết (việc C8) |
| Nhập học viên hàng loạt | Quản trị → Tài khoản | trần 50 dòng một lượt |
| Mở / sửa / đóng lớp, xếp giảng viên, trợ giảng, học vụ phụ trách | Quản trị → Lớp học | |
| Mở khoá học, soạn **khung chương trình theo buổi** (buổi → mục → trọng số) | Giáo trình → Khung chương trình | mục có nhiều loại: chủ đề, bài tập, kiểm tra, ôn tập |
| Cho một lớp **nhận khung**, xem trước buổi nào gắn vào đâu rồi mới lưu | Quản trị → Lớp học → Chương trình | xem trước không ghi gì |
| Xem toàn trung tâm: số học viên, số lớp, lớp chậm tiến độ, lớp chưa ghi sổ đầu bài | Quản trị → Toàn trung tâm | |
| **Chấm công giảng viên và trợ giảng theo tháng** | Vận hành → Chấm công | buổi đã dạy, tổng giờ, tự điểm danh, điểm danh muộn, **bài đã chấm**, **thông báo đã gửi**; tải .xlsx |
| Soạn và gửi **thông báo chung** cho lớp / môn / cả trung tâm, lưu nháp, xem trước số người nhận | Quản trị → Thông báo | xem trước nói rõ "Sẽ báo cho 3 em qua chuông, 3 em nhận email" |
| Nhật ký kiểm toán mọi thao tác đổi dữ liệu | — | ghi tự động, kèm bản cũ |

## 2 · Quản lý học vụ

| Làm được gì | Bấm ở đâu | Ghi chú thật |
|---|---|---|
| Mọi việc lớp học, xếp lịch, điểm danh bằng **thẻ học vụ của mình** | Học vụ → Lớp học | đo 27/09: bấm "Điểm danh" một buổi → đủ Có mặt · Vắng · Đi muộn · Xin phép · **lịch sử sửa điểm danh** |
| Xếp lịch cả khoá: sinh buổi theo tuần, tránh trùng phòng / trùng người, bỏ ngày lễ | Học vụ → Lịch học | |
| **Đổi giảng viên / trợ giảng cho MỘT buổi** (dạy thay) | Lịch học → buổi → Đổi người dạy | để trống = theo lớp. Chấm công đi theo **người dạy thật**, không theo người đứng tên lớp |
| Chuông tự báo cho học viên khi lịch lớp có buổi mới | — | một lượt xếp lịch = một chuông, không phải mười |
| **Hộp Yêu cầu**: nhận việc từ học viên, phụ huynh, trợ giảng; ghi chú nội bộ; lịch sử trao đổi | Học vụ → Yêu cầu | học viên không thấy thẻ Xử lý, không thấy ghi chú nội bộ |
| **Duyệt là hệ thống TỰ LÀM** — bảy loại thay đổi học tập | Yêu cầu → Duyệt | chuyển lớp, chuyển môn, bảo lưu, huỷ khoá, học lại, **nghỉ học**, **học bù**; mỗi lượt ghi rõ đã làm gì, trong một giao dịch |
| Xem trước khi duyệt: "sẽ làm gì cho em" | Yêu cầu → Xem trước | |
| Duyệt **học bù**: xếp em vào buổi bù mà không phải thêm em vào lớp khác | Yêu cầu → Duyệt | |

## 3 · Giảng viên

| Làm được gì | Bấm ở đâu | Ghi chú thật |
|---|---|---|
| Sổ điểm danh từng buổi, sửa lại được, **lịch sử sửa** hiện ngay dưới sổ | Giảng dạy → Buổi học | |
| **Sổ đầu bài**: từng mục của khung đánh "đã dạy / một phần / chưa dạy", mức tiếp thu 1–5, đề xuất, đánh dấu em cần hỗ trợ | Giảng dạy → Sổ đầu bài | hai người cùng mở sổ thì người sau bị chặn, không đè lặng lẽ |
| Màn **Chương trình lớp**: % đã dạy từng buổi khung, lớp chậm ở đâu, tiến độ từng em | Giảng dạy → Chương trình | |
| **Giao bài** (tự luận / kiểm tra trên lớp), hạn nộp, đổi người nhận (cả lớp hoặc một nhóm), sửa bài, đóng/mở nhận bài | Giảng dạy → Bài tập | |
| Bảng chấm cả lớp: từng em "Chưa nộp" / "Nộp 18/09", tổng "9/27 đã nộp", nhập điểm, nhận xét | Giảng dạy → Bài tập → bài | thang điểm của riêng từng bài, hệ thống quy về % |
| Theo dõi từng em: nhận xét (in lên tờ phụ huynh), đánh dấu **cần hỗ trợ** (nội bộ), đề xuất hướng học | Giảng dạy → Học viên | |
| **Đính kèm học liệu** vào kho chung của lớp hoặc vào một buổi, ẩn/hiện theo tiến độ | Giảng dạy → Học liệu | liên kết ngoài (Drive, YouTube…). Tải tệp thẳng lên còn chờ khoá R2 |
| Đề xuất đổi buổi → thành Yêu cầu gửi học vụ | Giảng dạy → Buổi học | |
| Nhắc cả lớp bằng thông báo | Giảng dạy → Thông báo lớp | |

## 4 · Trợ giảng

| Làm được gì | Bấm ở đâu | Ghi chú thật |
|---|---|---|
| Vào đúng lớp mình phụ trách (lớp khác: không mở được) | Giảng dạy | |
| **Nhắc cả lớp** bằng thông báo lớp | Giảng dạy → Thông báo lớp | đo 13/13 bước bằng thẻ trợ giảng |
| **Theo dõi việc xem bản ghi**: "1/2 em đã mở", tên em chưa mở, nút "Nhắc em chưa mở" | Giảng dạy → Buổi học | |
| Báo lên học vụ: "Em không phản hồi tin nhắn 3 ngày" | Giảng dạy → Yêu cầu | nguồn "Trợ giảng báo" |
| Giải đáp cho học viên trong hộp Yêu cầu, lịch sử trao đổi lưu đủ | Giảng dạy → Yêu cầu | |
| **Chưa làm được: nhắn RIÊNG một em** | — | chờ anh quyết (việc E3) — hộp Yêu cầu là kênh do học viên mở trước, còn thông báo lớp thì cả lớp cùng nhận |

## 5 · Phụ huynh

| Làm được gì | Bấm ở đâu | Ghi chú thật |
|---|---|---|
| Xem tờ báo cáo của con bằng **link riêng**, không cần tài khoản | link học vụ gửi | lịch buổi, tiến độ học tập, nhận xét, **tên trợ giảng** |
| Gửi yêu cầu / phản hồi cho trung tâm qua chính link ấy | tờ báo cáo → Gửi yêu cầu | vào hộp Yêu cầu của học vụ |
| Liên lạc của học viên **không** lên tờ phụ huynh | — | có chủ ý |

## 6 · Học viên

| Làm được gì | Bấm ở đâu | Ghi chú thật |
|---|---|---|
| **Tự đăng ký** tài khoản, xác thực qua email, gửi lại thư xác thực | `/dang-ky` | §73, đo 20/20 bước |
| Đăng nhập bằng email / SĐT / tên đăng nhập, ghi nhớ 30 ngày, quên mật khẩu qua email | `/login` | link đặt lại sống 30 phút, dùng một lần |
| Thẻ lớp của em: lịch buổi, % chương trình kèm kế hoạch, điểm danh từng buổi | Trang chủ | |
| **Trang Thông báo** đầy đủ: lọc theo loại, lọc chưa đọc, đánh dấu đã / chưa đọc, "Xem thêm" | `/thong-bao` | 12/12 bước đo trên màn thật, không một mã kỹ thuật nào lọt lên màn |
| Xem lại **bản ghi buổi học**, hệ thống ghi nhận em đã mở | thẻ lớp → "Xem lại" | |
| Mở **học liệu** của lớp / của buổi, thấy tên miền trước khi bấm | thẻ lớp → Học liệu | |
| Nộp bài tự luận, xem điểm và nhận xét từng bài | `/bai-tap` | nộp bằng chữ; nộp tệp chờ khoá R2 |
| Gửi yêu cầu (nghỉ học, học bù, chuyển lớp…) và trao đổi tới khi đóng | `/yeu-cau` | |

## 7 · Phần nền không ai bấm thấy nhưng sai là chặn cả hệ thống

- **Thư đi qua hộp chờ (outbox)**, không gửi thẳng trong lời gọi API — máy chủ gói miễn phí ngủ thì thư nằm chờ, không mất.
- **Hàng rào thư**: chỉ gửi tới địa chỉ thử (`@example.com`, tài khoản e2e). Ra khỏi hệ thống là không cuộn lại được, nên hàng rào này không được nới trong lúc chưa có dữ liệu thật.
- **Nhãn loại chuông bằng tiếng Việt**, do máy chủ trả — màn không tự dịch, và không mã kỹ thuật nào lọt lên màn.
- **Phân quyền**: lớp không phụ trách trả 404 chứ không 403 — không lộ lớp nào tồn tại.
- **Lược đồ CSDL chỉ cộng thêm**, chạy khi build. Mục nào hỏng thì build đỏ và **bản cũ vẫn phục vụ** — không có cửa sổ production nửa sống nửa chết.
- **Nhật ký kiểm toán** cho mọi thao tác đổi dữ liệu, kèm bản cũ.

## 8 · Đang chờ, nói thẳng

| Thứ chưa làm được | Chờ gì | Mã việc |
|---|---|---|
| Tải **tệp** thẳng lên (học liệu, nộp bài bằng tệp) | khoá Cloudflare R2 của anh — lược đồ đã chừa sẵn | D1 |
| Bản ghi Zoom **tự** vào buổi, % đã xem | khoá Zoom của anh | Z1 |
| Trợ giảng **nhắn riêng** một em | anh quyết có mở kênh ấy không | E3 |
| Học vụ có xem được liên hệ phụ huynh / tải danh sách tài khoản không | anh quyết | C8 |
| Ngưỡng "hoàn thành khoá" | con số của anh / của TopHSA | — |
| Học phí, công nợ | bốn câu hỏi đang chờ TopHSA | K2 |
| Báo cáo chéo môn × lớp | đang làm, không chờ ai | — |
| Khung chương trình **thật** của một môn | TopHSA đưa | K1 |

## 9 · Số đo của bản này (27/09/2026)

| Đo gì | Số |
|---|---|
| Bảng trong CSDL | 59 |
| Mục lược đồ `§NN` | 72 |
| Cửa API | 203 |
| Trang màn (Next) | 43 |
| Phép kiểm backend | **1.262** trong 101 tệp |
| Phép kiểm đơn vị phía màn · e2e | 39 · 27 |
| Bộ đo màn thật | 15 |
| Miền mã | 16, nợ ghi chéo còn 11 chỗ |
| Dòng mã | backend 66.025 · frontend 34.148 |
| Cổng kiểm trước khi đẩy | 15 bước, 153 giây |

Mọi số ở bảng này đo bằng lệnh, không lấy từ trí nhớ. Cách đo ghi ở `docs/SYSTEM_DESIGN.md` §9.
