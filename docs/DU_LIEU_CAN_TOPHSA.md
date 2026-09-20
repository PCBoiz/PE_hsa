# Dữ liệu và thông tin TopHSA cần cung cấp để bắt đầu thử nghiệm

*Lập 20/09/2026. Viết để anh Sơn gửi thẳng cho người phụ trách học vụ của TopHSA.
Mỗi mục ghi: cần gì, ai ở trung tâm thường giữ, định dạng nào hệ thống nhận được ngay, và
nhập vào đâu. Mọi ràng buộc ở đây lấy từ mã đang chạy, không phải từ mong muốn.*

---

## 0. Phạm vi thử nghiệm đề nghị

**Một lớp thật, một đợt** (việc B1). Lớp có giảng viên thật, 15–40 học viên đang học, lịch
cố định hằng tuần, và ít nhất **một kỳ thi thử** rơi vào trong đợt — vì tờ báo cáo phụ huynh
chỉ thuyết phục khi có điểm thi thật để so.

Trung tâm KHÔNG phải chuẩn bị gì về nội dung học: 76 bài học ba hợp phần, đề thi thử, lịch
sinh tự động, tờ báo cáo, sổ điểm — đã có sẵn. Thứ chỉ TopHSA có là **con người, lịch và
điểm thi**: bảng dưới đây liệt kê đúng những thứ ấy.

---

## 1. Bảng tổng — chín nhóm, theo thứ tự cần tới

| # | Nhóm | Bắt buộc? | Ai ở trung tâm thường giữ | Cần trước khi |
|---|---|---|---|---|
| A | Đợt học và ngày nghỉ | **Bắt buộc** | Học vụ | tạo lớp |
| B | Lớp và lịch tuần | **Bắt buộc** | Học vụ · giảng viên | buổi đầu |
| C | Nhân sự: giảng viên, trợ giảng, học vụ | **Bắt buộc** (ít nhất 1 giảng viên) | Quản lý trung tâm | buổi đầu |
| D | Danh sách học viên | **Bắt buộc** | Học vụ (tệp đăng ký) | buổi đầu |
| E | Liên hệ phụ huynh | Bắt buộc **để gửi báo cáo**; không cần để dạy | Học vụ (tệp đăng ký) | kỳ báo cáo đầu (~tuần 4) |
| F | Tờ PDF kết quả thi thử của từng em | Cần **để có khối "Kỳ thi thử tại trung tâm"** | Người quản lý hệ khảo thí | sau mỗi đợt thi thử |
| G | Kênh gửi báo cáo: email tên miền hoặc Zalo OA | Cần để gửi **tự động**; gửi tay thì không cần | Chủ trung tâm | kỳ báo cáo đầu |
| H | Quy ước vận hành: thang điểm, ai điểm danh, tần suất báo cáo | **Bắt buộc** — vài câu trả lời | Quản lý trung tâm | buổi đầu |
| I | Bảy câu hỏi còn treo (nền tảng dạy, chấm tự luận, thu chi, tuyển sinh…) | Không chặn thử nghiệm | Quản lý trung tâm | khi mở rộng |

---

## 2. Từng nhóm — cần đúng những gì

### A · Đợt học và ngày nghỉ

| Trường | Ví dụ | Ghi chú |
|---|---|---|
| Tên đợt | `Đợt 1/2027` | bắt buộc |
| Mã đợt | `D1-2027` | tuỳ chọn, phải khác các đợt trước |
| Ngày bắt đầu · ngày kết thúc | `06/10/2026` · `28/12/2026` | |
| Ngày thi (mặc định cho các lớp trong đợt) | `10/01/2027` | mỗi lớp có thể có ngày thi riêng |
| **Ngày nghỉ trong đợt** | `20/11 (Ngày Nhà giáo)`, nghỉ Tết… | mỗi ngày một dòng: ngày + tên. Khai TRƯỚC khi sinh lịch — sinh lịch xong mới khai thì phải xoá buổi tay |

Nhập ở: **Vận hành → Đợt học** (quản trị viên hoặc học vụ).

### B · Lớp và lịch tuần

| Trường | Ví dụ | Ghi chú |
|---|---|---|
| Tên lớp | `Luyện HSA đợt 1/2027 — Ca tối` | bắt buộc |
| Mã lớp | `HSA-T1-01` | tuỳ chọn |
| Hợp phần ôn | *Định lượng* / *Định tính* / *Khoa học* / **cả ba** | quyết định bản đồ năng lực và bài tập gợi ý của lớp |
| Giảng viên phụ trách | tên + email đã có tài khoản | **một** người; trợ giảng thêm sau qua danh sách lớp |
| Lịch tuần | `Thứ 3, Thứ 5 · 19:30 · 90 phút` | hệ thống **tự sinh mọi buổi** trong đợt từ ba con số này, bỏ ngày nghỉ ở A |
| Ngày học đầu · cuối | `07/10/2026` · `25/12/2026` | mặc định theo đợt |
| Sĩ số tối đa | `30` | |
| Link phòng học online | `https://meet.google.com/…` | nếu dạy online; học viên bấm "Vào phòng học" ngay trên trang của mình |
| Ngày thi của lớp | | nếu khác ngày thi của đợt |

Nhập ở: **Vận hành → Lớp học** → tạo lớp → **Buổi học → Sinh lịch cả kỳ** (xem trước rồi mới ghi).

### C · Nhân sự

Mỗi người một dòng: **Họ tên · email · số điện thoại · vai**. Email là tên đăng nhập, nên
**phải là email người ấy thật sự mở** — mật khẩu tạm gửi về đó.

| Vai trong hệ thống | Làm được gì | Cần mấy người cho thử nghiệm |
|---|---|---|
| Giảng viên | Lớp mình phụ trách: điểm danh, giao bài, chấm, báo cáo phụ huynh | **1**, bắt buộc |
| Trợ giảng | Điểm danh, chấm giúp trong lớp được gán; **không** thấy liên hệ phụ huynh, không xoá buổi | 0–1 |
| Quản lý học vụ | Mọi lớp: xếp lớp, đợt, tổng quan trung tâm, nhập PDF thi thử, báo cáo phụ huynh | 1, nên có |
| Biên tập nội dung | Soạn/sửa bài học và đề. Không thấy học viên | 0 — giáo trình đã có |
| Quản trị viên | Mọi việc, kể cả cấp tài khoản và đặt lại mật khẩu | anh Sơn giữ trong thời gian thử |

Cấp ở: **Vận hành → Tài khoản → Cấp tài khoản** (quản trị viên). Tài khoản do trung tâm cấp,
không có tự đăng ký.

### D · Danh sách học viên — mẫu dán được ngay

Dán thẳng từ Excel/Google Sheets (cột ngăn bằng tab, phẩy hoặc chấm phẩy đều được; có dòng
tiêu đề cũng được). Mỗi dòng: **Họ tên, email, số điện thoại** — email và số điện thoại **ít
nhất một trong hai** (nhiều em lớp 12 chưa có email: số điện thoại là đủ để đăng nhập).

```
Họ tên	Email	Số điện thoại
Nguyễn Văn An	an.nguyen@gmail.com	0912345678
Trần Thị Bình		0987654321
Lê Minh Cường	cuong.le@gmail.com
```

| Ràng buộc | Vì sao |
|---|---|
| **Tối đa 50 em một lượt dán** | băm mật khẩu tốn ~0,13 s CPU mỗi em; lớp 80 em thì dán hai lượt |
| Email và số điện thoại **không trùng** với tài khoản đã có | hệ thống báo đúng dòng trùng ở bước xem trước, không ghi gì |
| **Họ tên phải VIẾT ĐÚNG NHƯ TRÊN HỆ KHẢO THÍ** (tờ PDF thi thử) | tờ PDF được khớp vào học viên **theo tên**; lệch một chữ đệm là học vụ phải chọn tay từng tờ |
| Ngày vào lớp | hiện hệ thống ghi = ngày nhập. Em đang học dở từ trước cần **ngày vào lớp thật** — anh Sơn đang quyết (câu 11.4); nếu chọn "cho nhập" thì thêm một cột `Ngày vào lớp` |

Luôn bấm **Xem trước** trước khi **Cấp**: tạo nhầm không có nút hoàn tác (email đã bị chiếm).
Sau khi cấp, hệ thống đưa ra **danh sách mật khẩu tạm** để gửi từng em — chỉ hiện một lần.

Nhập ở: **Vận hành → Tài khoản → Cấp hàng loạt**, chọn sẵn lớp để xếp luôn.

### E · Liên hệ phụ huynh — mẫu dán được ngay

Dán **kèm dòng tiêu đề** (bắt buộc khi bảng có cả số của em lẫn số của phụ huynh — hai số
trông y hệt nhau, chỉ tên cột phân biệt được):

```
Họ tên em	Email của em	Tên phụ huynh	SĐT phụ huynh	Email phụ huynh
Nguyễn Văn An	an.nguyen@gmail.com	Nguyễn Thị Hoa	0903111222	hoa.nguyen@gmail.com
Trần Thị Bình		Trần Văn Nam	0903333444	
```

| Ràng buộc | Vì sao |
|---|---|
| Chỉ khớp em **đang học đúng lớp đó** | dán nhầm lớp thì không ghi đè được liên hệ của em lớp khác |
| Ô trống **giữ nguyên** giá trị cũ | dán thiếu cột không xoá email đang có |
| Số phụ huynh phải là **số có Zalo** nếu định gửi qua Zalo | |
| Học vụ nhập rồi thì **học viên không tự sửa** được liên hệ phụ huynh | chính sách đã chốt 14/09: chặn em đổi email bố mẹ thành email mình để chặn báo cáo |

Nhập ở: lớp → **Báo cáo phụ huynh → Nhập liên hệ phụ huynh** → Kiểm tra trước → Lưu.

### F · Tờ PDF kết quả thi thử

| Cần | Ghi chú |
|---|---|
| Tờ **"Báo cáo kết quả thi"** của hệ khảo thí (uranustech), **mỗi em một tệp PDF**, xuất sau mỗi đợt thi thử | hệ thống đọc mục *III. Phân tích kết quả thi*: tên, ngày thi, ba điểm phần, tổng /150, 24 đơn vị kiến thức |
| Tên trên tờ = tên tài khoản (xem D) | lệch thì học vụ chọn tay em đúng — không đoán |
| Kéo **từng lượt tối đa 5 tệp** vào ô đọc, ghi **tối đa 60 tờ** một lần | một tờ đọc mất ~0,75 s |
| Nhập lại cùng tờ → **ghi đè**, không đẻ thêm kỳ thi | khoá theo (em, ngày thi, đợt) |

Nhập ở: lớp → **Nhập kết quả thi thử từ PDF** (giảng viên phụ trách hoặc học vụ).
**Không cần** bên khảo thí mở kết nối hay xuất bảng gì thêm.

### G · Kênh gửi báo cáo

| Kênh | Cần từ TopHSA | Trạng thái |
|---|---|---|
| **Email** (đề nghị làm trước) | Một hộp thư tên miền `@tophsa.vn` (Google Workspace ~6 USD/tháng) hoặc tài khoản dịch vụ gửi thư; app password | Mã đã gửi thử thành công từ hộp thư cá nhân; chờ hộp thư của trung tâm (B2) |
| **Zalo ZNS** | Zalo OA **đã xác thực** (cần giấy phép kinh doanh / hộ kinh doanh) + một mẫu tin được Zalo duyệt với bốn tham số `ten_hoc_vien, ten_lop, ky, duong_dan` | Chế độ thử đã dựng; chưa gửi thật |
| **Không kênh nào** | Không cần gì | Giảng viên bấm *Tạo đường dẫn* rồi gửi tay qua Zalo cá nhân — dùng được ngay hôm nay |

### H · Quy ước vận hành — sáu câu, trả lời một dòng mỗi câu

1. **Thang điểm bài tập** giảng viên chấm: thang 10 hay thang 100? (hệ thống nhận thang riêng
   từng bài, quy về % khi vào bản đồ năng lực)
2. **Ai điểm danh và lúc nào**: giảng viên ngay sau buổi, hay trợ giảng, hay cuối tuần gom một
   lần? (tờ báo cáo chỉ tính buổi ĐÃ điểm danh; buổi quên tick được nêu riêng, không tính là vắng)
3. **Chủ đề mỗi buổi**: có sổ đầu bài/giáo án theo buổi không? (mỗi buổi có ô "chủ đề", nuôi
   khối "Con cần giúp chỗ nào"; không có thì bỏ trống được)
4. **Báo cáo phụ huynh** gửi **bao lâu một lần** (đề nghị: sau mỗi đợt thi thử, tức ~4 tuần),
   và **ai duyệt** trước khi gửi?
5. **Phụ huynh xem được gì**: hiện tiến độ, chuyên cần, điểm — không có nhật ký em tự ghi.
   Đồng ý giữ như vậy? (câu C3)
6. **Học viên đang học dở** có đưa vào hệ thống không, hay chỉ em mới? (quyết định 11.4)

### I · Bảy câu còn treo — không chặn thử nghiệm

Dạy trên nền tảng nào và có API danh sách người tham dự không · có chấm tự luận không, thang
nào, ai chấm · quy trình thu chi và phần mềm kế toán đang dùng · quy trình tuyển sinh · phút
ngồi lớp có tính vào chỉ tiêu tự học tuần không · có định thay hệ ngân hàng câu hỏi của
uranustech không · tần suất và người duyệt báo cáo (trùng H.4). Chi tiết ở `VIEC_CUA_ANH.md`, C4.

---

## 3. Ngày đầu tiên — thứ tự nhập, ai làm, mất bao lâu

| Bước | Ai | Màn | Ước lượng |
|---|---|---|---|
| 1. Tạo đợt + khai ngày nghỉ | học vụ | Vận hành → Đợt học | 5 phút |
| 2. Cấp tài khoản giảng viên, trợ giảng, học vụ | quản trị viên | Vận hành → Tài khoản | 5 phút |
| 3. Tạo lớp, gán giảng viên, lịch tuần | học vụ | Vận hành → Lớp học | 5 phút |
| 4. Sinh lịch cả kỳ (xem trước → ghi) | học vụ | lớp → Buổi học | 2 phút |
| 5. Dán danh sách học viên, chọn lớp, xem trước → cấp | quản trị viên | Vận hành → Tài khoản → Cấp hàng loạt | 10 phút / 50 em |
| 6. Gửi mật khẩu tạm cho từng em (Zalo lớp) | trợ giảng | ngoài hệ thống | 15 phút |
| 7. Dán liên hệ phụ huynh (khi có) | học vụ | lớp → Báo cáo phụ huynh → Nhập liên hệ | 5 phút |
| 8. Sau đợt thi thử: kéo xấp PDF vào | học vụ | lớp → Nhập kết quả thi thử | 10 phút / 30 tờ |
| 9. Mở tờ báo cáo một em, tạo đường dẫn, gửi thử cho **một** phụ huynh đồng ý trước | giảng viên | lớp → Báo cáo phụ huynh | 5 phút |

Tổng ngày đầu: **dưới một giờ** nếu dữ liệu A–D đã có trong tay. Bước 3 nay có ô **"Trợ giảng của
lớp"** (gán/gỡ tại chỗ) và bước 5 có thể **dán cả cột email** vào lớp một lượt (rà luồng 20/09/2026,
đi trọn bằng chuột với 7 tài khoản thử — xem `PROGRESS.md` 20/09 trưa).

### Trước khi cho dữ liệu THẬT vào — làm một lần

1. `python manage.py du_lieu_mau --go` — gỡ hai lớp mẫu và tài khoản mẫu; không gỡ thì tổng quan
   học vụ mở ra là "3 buổi chưa điểm danh" của lớp mẫu.
2. Xoá 7 tài khoản `audit2009.*@example.com`, đợt `AUDIT-2009`, lớp `AUDIT-01` (dữ liệu của lượt rà
   20/09) — hoặc giữ làm lớp thử của trung tâm.
3. Quyết định về **bản nháp cho bài học**: khu Soạn giáo trình hiện "Lưu nội dung" = học viên thấy
   ngay. Đề thi thử thì có "đang hiện / ẩn đi", bài học thì chưa.
4. Việc chỉ anh Sơn làm được: A0 (GitHub Actions), A1, A5, A7 — `docs/VIEC_CUA_ANH.md`.

---

## 4. Những gì TopHSA KHÔNG phải cung cấp

Nội dung 76 bài học ba hợp phần (đã có, có hình minh hoạ) · đề thi thử trên hệ thống · lịch
buổi học (tự sinh) · tờ báo cáo phụ huynh, sổ điểm, bản đồ năng lực (tự dựng từ hoạt động) ·
điểm thi thử **không cần nhập tay** — chỉ cần tờ PDF · tài khoản phụ huynh — **phụ huynh
không cần tài khoản**, chỉ mở đường dẫn.

---

## 5. Sau khi nhận dữ liệu, tôi làm gì

Nhập thử **toàn bộ** trên bản chạy thật với đúng tệp của trung tâm (không phải dữ liệu mẫu),
đi trọn đường một em từ cấp tài khoản → học một bài → điểm danh một buổi → nộp một bài tập →
nhập một tờ PDF → tờ báo cáo phụ huynh, rồi báo lại chỗ nào tệp của trung tâm không dán
được ngay (tên cột lạ, số điện thoại viết kiểu khác…) và sửa công cụ nhập cho khớp tệp thật
— thay vì bắt trung tâm sửa tệp cho khớp công cụ.
