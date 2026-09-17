# Kịch bản trình diễn pe_hsa — bản 17/09/2026

Viết cho anh Sơn cầm khi ngồi trước người mua. Mỗi mục: **bấm gì → nói gì**, và
những chỗ *đừng* mở. Dữ liệu trên màn là **bộ trình diễn** (hai lớp mẫu), đánh
dấu rõ trong hệ thống và không bao giờ gửi tin cho ai.

---

## 0. Mười lăm phút trước khi bắt đầu

| # | Việc | Vì sao |
|---|---|---|
| 1 | Mở `https://pe-hsa.vercel.app` và để đó **2–3 phút** trước giờ | Máy chủ ngủ sau một lúc không ai dùng. Đo 17/09 lúc 09:51: lượt gọi đầu **76,3 giây**, hai lượt ngay sau đó **0,97 s** và **0,50 s**. Mở sớm là nó thức sẵn. (Việc A1 — gắn cron-job.org thì hết hẳn.) |
| 2 | **Đăng nhập lại** bằng tài khoản quản trị | Khoá ký phiên vừa được tách khỏi máy phát triển (A6), nên mọi phiên cũ đã bị đăng xuất. Đừng để tới lúc demo mới phát hiện. |
| 3 | Làm mới dữ liệu trình diễn: `python manage.py du_lieu_mau --lam-moi` (≈60 giây), hoặc nhắn tôi làm | Bộ dữ liệu neo vào ngày dựng. Để quá 2 ngày, màn hình bắt đầu hiện "buổi đã dạy chưa ai điểm danh" và "N ngày không mở bài" — trông như trung tâm ngừng hoạt động. Muốn biết có cần không: chạy `python manage.py du_lieu_mau`, nó tự báo *"Hoạt động mẫu gần nhất … (N ngày trước)"*. |
| 4 | Mở sẵn hai thẻ trình duyệt: **Quản trị · tổng quan** và **một bài học** | Đỡ phải gõ đường dẫn giữa buổi. |

**Tình trạng dữ liệu lúc 10:40 ngày 17/09** (nếu anh demo CHIỀU NAY thì không phải làm gì
thêm): đã làm mới lúc 08:02, hoạt động gần nhất là hôm qua — mọi màn hình sạch, lớp mẫu Ca chiều
đã điểm danh đủ 14/14 buổi. Em **Đỗ Đức Tùng** (lớp Ca chiều) nay có **ba** kỳ thi thử tại trung
tâm, kỳ gần nhất 98/150 **tăng 10 điểm** so với kỳ trước — mở tờ báo cáo của em này khi tới phần
"Thứ phụ huynh nhận được". Demo sang ngày khác thì chạy `--lam-moi` (lưu ý: lệnh ấy dựng lại từ
đầu nên ba kỳ thi kia trở về hai kỳ).

**Đừng mở trong buổi demo:** lớp *"Luyện HSA đợt 1/2027 — Ca tối"* (lớp thử
nghiệm cũ, có hai tài khoản tên "a" và "Test Reg"). Hai tài khoản ấy cũng là
thứ đang hiện ở mục "Cần chú ý ngay" của màn Việc hôm nay — nếu người mua hỏi,
nói thẳng: *"đó là tài khoản thử của giai đoạn phát triển, sẽ xoá trước khi
chạy thật"*.

---

## 1. Mở đầu: một trung tâm đang chạy (2 phút)

**Màn:** Quản trị → **Tổng quan**.

- Trên cùng: *"Hôm nay cần làm gì"* — hệ thống tự nêu việc còn tồn và nói rõ
  việc ấy đang làm sai con số nào bên dưới.
- Khối **Toàn trung tâm**: lớp đang chạy, học viên đang học, chuyên cần.
- Bảng **Từng lớp**: sĩ số · buổi đã dạy · chuyên cần · tiến độ · điểm thi thử.

> Nói: *"Đây là toàn bộ trung tâm trên một màn. Cùng một cách tính với báo cáo
> từng lớp — nếu hai bên lệch nhau thì đó là lỗi, không phải hai cách đo."*

## 2. Một ngày của giảng viên (2 phút)

**Màn:** **Giảng dạy → Việc hôm nay**.

- Buổi trong 24 giờ tới · buổi chưa điểm danh · bài chưa chấm · em vắng liền
  ≥ 2 buổi · em cần chú ý.
- Bấm **Điểm danh →** của một buổi lớp mẫu để cho thấy sổ điểm danh; bấm
  **Chấm →** để cho thấy bảng chấm cả lớp trên một màn.

> Nói: *"Giảng viên không phải đi tìm việc. Màn này là danh sách việc, mỗi việc
> một nút."*

## 3. Buổi học và điểm danh (1 phút)

**Màn:** lớp mẫu → **Buổi học**.

- Lịch cả kỳ sinh sẵn theo thứ trong tuần, bỏ ngày nghỉ của đợt.
- Buổi đã dạy hiện **có mặt / muộn / vắng / có phép** và giờ điểm danh.

## 4. Thứ phụ huynh nhận được (4 phút — phần quan trọng nhất)

**Màn:** lớp mẫu → **Báo cáo phụ huynh** → mở **tờ của một em**.

Đi từ trên xuống, dừng ở bốn khối:

1. **Con có đi học không** — bốn ô cộng lại đúng bằng số buổi đã điểm danh;
   buổi giảng viên quên tick được nói ra riêng, không âm thầm chia nhỏ mẫu số.
2. **Kỳ thi thử tại trung tâm** — điểm THẬT nhập từ tờ PDF của hệ thống khảo
   thí, có so với kỳ trước và ba đơn vị kiến thức yếu nhất.
3. **Con có học đều không** — bảng nhịp từng tuần: đi học · bài học · luyện tập
   · bài tập đã nộp. *(Thêm 17/09 — đây là câu trả lời cho "thấy con tiến bộ
   từng tuần".)*
4. **Con cần giúp chỗ nào** — chủ đề đo được, kèm mức thành thạo.

Rồi bấm **Tạo đường dẫn gửi phụ huynh** → mở đường dẫn ấy **trên điện thoại**:
cùng tờ báo cáo, không cần đăng nhập, không có email/số điện thoại của ai, có
hạn dùng và **thu hồi được**.

> Nói: *"Phụ huynh không cần tài khoản. Trung tâm giữ quyền: hết hạn, thu hồi
> được, và tờ gửi đi mỏng hơn tờ giảng viên xem."*

## 5. Điểm thi thử thật vào báo cáo (2 phút)

**Màn:** lớp mẫu → **Nhập kết quả thi thử từ PDF**.

- Kéo cả xấp tờ kết quả của hệ thống khảo thí vào; hệ thống đọc tên, ngày thi,
  điểm ba phần, tổng điểm và **24 đơn vị kiến thức**, rồi tự khớp với học viên
  của lớp. Trùng tên hoặc không tìm thấy thì **không đoán** — học vụ chọn tay.
- Nhấn mạnh: không cần bên khảo thí mở kết nối gì.

*(Nếu không có tờ PDF trong tay thì chỉ mở màn hình và kể; đừng thử tải tệp lạ
giữa buổi.)*

## 6. Bài học — thứ học viên dùng hằng ngày (3 phút)

**Màn:** **Bài học** → chọn một bài, ví dụ *Đọc bảng số liệu* (Định lượng) hoặc
*Hàm bậc hai & parabol*.

- Bước 1: bài kiểm tra đầu bài → nộp.
- Bước 2: hệ thống đánh giá mức và **chọn bản lý thuyết theo mức ấy**.
- Bước 3: lý thuyết có **hình minh hoạ** — bảng, đồ thị, sơ đồ, dòng thời gian…
  **76/76 bài đều có hình** (158 hình, 8 kiểu), và hình có ở cả bản đầy đủ lẫn
  bản rút gọn.
- Nếu người mua cầm điện thoại: mở đúng bài ấy trên điện thoại — bảng vừa khít
  màn hình, đồ thị đọc được (sửa 17/09).

## 7. Kết: chốt bằng ba câu (1 phút)

- *"Học viên tự luyện đúng chỗ yếu — hệ thống đo theo từng chủ đề, không gộp
  thành một điểm trung bình."*
- *"Giảng viên vận hành lớp trên một màn: điểm danh, giao bài, chấm, báo cáo."*
- *"Phụ huynh thấy con tiến bộ từng tuần, bằng tờ báo cáo gửi về điện thoại."*

---

## Câu hỏi khó và cách trả lời thẳng

| Người mua hỏi | Trả lời |
|---|---|
| "Số liệu này là thật à?" | *"Không — đây là bộ dữ liệu trình diễn, hệ thống đánh dấu rõ và gỡ bằng một lệnh. Trung tâm chưa chạy lớp thật trên hệ thống; đó là việc đầu tiên của 30 ngày tới."* |
| "Có gửi nhầm cho phụ huynh không?" | *"Không gửi được: tài khoản mẫu bị chặn ở tầng máy chủ, nút gửi hiện 'Dữ liệu mẫu — không gửi'."* |
| "Phụ huynh xem được những gì?" | *"Tiến độ, chuyên cần, điểm. Nhật ký riêng của học viên thì không — đó là chính sách, đang chờ trung tâm chốt."* |
| "Sao trang đầu tiên hơi lâu?" | *"Máy chủ gói rẻ ngủ khi không ai dùng; bật gói giữ ấm là hết, khoảng 7 đô một tháng."* |
| "Đã có ai dùng thật chưa?" | *"Chưa. Đó là lý do đề xuất chạy một lớp thật trong tháng đầu — mọi thứ khác dễ hơn sau khi một lớp đi qua một lần."* |
| "Bảo mật thế nào?" | *"Phân quyền theo vai, mọi thao tác sửa dữ liệu có nhật ký, đường dẫn phụ huynh có hạn và thu hồi được, khoá ký của hệ thống chạy thật vừa tách khỏi máy phát triển."* |

---

## Sau buổi demo

- Nếu có bật/tắt gì trong lúc demo (tạo đường dẫn phụ huynh chẳng hạn), không
  cần dọn: chúng thuộc dữ liệu mẫu và biến mất ở lần `--lam-moi` sau.
- Ghi lại câu hỏi người mua hỏi mà mình phải nói "để kiểm tra lại" — đó là danh
  sách việc thật cho vòng sau.
