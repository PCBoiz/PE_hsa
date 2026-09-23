# Đối chiếu bảng yêu cầu của TopHSA với hệ thống — 23/09/2026

Nguồn: bảng "Bản sao của Bảng phân rã tính năng" (tab *Trang tính1* + tab *Nhi*). Bỏ dòng 7
(Kế toán — học phí) và phần doanh thu ở dòng 6, theo chỉ đạo của anh Sơn.

**Cách kiểm:** mỗi ô dưới đây lấy từ MÃ, LƯỢC ĐỒ CSDL hoặc lượt chạy trên trình duyệt — không lấy từ chú
thích hay trí nhớ. Cột "Bằng chứng" chỉ nơi kiểm lại được.

**Nhãn:** `CÓ` — dùng được ngay · `MỘT PHẦN` — có nhưng thiếu điều bảng đòi · `CHƯA` — không có.

## Kết luận nhanh

- Cột ô tick của bảng (TRUE ở dòng 1, 2, 8, 9, 13, 14, 18, 19) **không khớp thực tế**: cả tám dòng ấy
  đều chỉ `MỘT PHẦN`. Chi tiết ở từng mục.
- Phần hệ thống ĐÃ mạnh: lớp học, điểm danh 4 trạng thái, sinh lịch theo tuần + ngày nghỉ, giao bài –
  chấm – nhận xét, báo cáo lớp và tờ phụ huynh, phân quyền theo vai, nhật ký kiểm toán.
- Bốn nhóm anh chốt làm trước (hồ sơ học viên, lịch học, dòng thời gian học viên, tài khoản) phủ phần
  lớn các ô `CHƯA` mà khách nhắc nhiều nhất — đặc biệt bốn đòi hỏi ở tab *Nhi*.

---

## 1 · Tài khoản — dòng 1, 8, 13, 19 (cả bốn vai giống nhau) · bảng tick TRUE

| Yêu cầu | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| 1.1 Đăng nhập bằng email | CÓ | `auth/login` |
| 1.2 Đăng nhập bằng username | CÓ (23/09) | ô đăng nhập nhận email / SĐT / tên đăng nhập; tên do học vụ đặt ở trang Hồ sơ, không phân biệt hoa thường (`users.username`, §51) |
| 1.3 Hiện/ẩn mật khẩu | CÓ | `.toggle-eye` ở màn đăng nhập |
| 1.4 Ghi nhớ đăng nhập | CÓ (24/09) | ô "Ghi nhớ đăng nhập trên máy này": tick → phiên 30 ngày (giữ qua mỗi lần xoay thẻ), không tick → cookie phiên; trình duyệt được nhờ lưu mật khẩu (`accounts/ghi_nho.py`) |
| 1.5 Quên mật khẩu | CÓ (23/09) | màn đăng nhập → "Đặt lại qua email": đường dẫn một lần, 30 phút, tới chính email của tài khoản; chỉ lưu băm của chìa; mọi phiên cũ bị cắt khi đặt xong (§52). Tài khoản không có email vẫn nhờ học vụ |
| 1.6 Đăng xuất | CÓ | menu tài khoản, mọi khu |

## 2 · Quản lý người dùng — dòng 2 · bảng tick TRUE

| Yêu cầu | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Tạo tài khoản | CÓ | ô cấp hàng loạt `api/admin/users/bulk` (một người = một dòng). Từ 23/09 học vụ cấp được — chỉ vai Học viên. `api/admin/users/create` không màn hình nào gọi (ứng viên gỡ trong `scripts/ban_do.mjs`) |
| Khoá / mở khoá | CÓ | `api/admin/users/<id>/status`, có ghi lý do |
| Phân quyền theo vai | CÓ | 6 vai, `common/permissions.py`, bảng "Ai làm được gì" |
| Xoá tài khoản | CHƯA | có chủ ý: chỉ khoá, không xoá (giữ lịch sử học tập) — cần anh xác nhận với khách |
| Xem trạng thái tài khoản | CÓ | cột `status`, `status_note` |
| Quan hệ phụ huynh – học sinh | MỘT PHẦN | tên/SĐT/email phụ huynh nằm trên hồ sơ em; phụ huynh không có tài khoản riêng |
| Thông tin chi tiết theo loại user | MỘT PHẦN | xem mục 3 |
| Đặt lại mật khẩu | CÓ | quản trị viên mọi tài khoản; học vụ với học viên và trợ giảng; lần đăng nhập sau bắt đổi |
| Nhập danh sách hàng loạt | CÓ | dán danh sách, xem trước bắt buộc, trần 50/lượt |
| Xuất danh sách | CÓ | `api/admin/export/users.csv` |

## 3 · Tìm kiếm + hồ sơ học viên — dòng 3 + tab *Nhi* #1

| Yêu cầu | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Tìm theo họ tên, email, SĐT | CÓ | tham số `q` của `api/admin/users` |
| Tìm theo username | CÓ (23/09) | ô tìm ở Tài khoản khớp cả tên đăng nhập và mã học viên |
| Mã học viên | CÓ (23/09) | HSA-00001… tự sinh lúc tạo, không sửa được; 55 em có sẵn đã được cấp mã |
| Họ tên · SĐT · email · ngày sinh | CÓ | `users.name/phone/email/birthday` |
| Trường · lớp · khu vực | CÓ (23/09) | trang Hồ sơ (`/quan-tri/tai-khoan/<id>`) |
| Thông tin / SĐT / email phụ huynh | CÓ | `parent_name/phone/email` |
| Người tư vấn · nguồn tuyển sinh | CÓ (23/09) | chọn từ danh sách: người tư vấn = tài khoản nhân sự đang hoạt động; tám nguồn cố định |
| Khoá học đã đăng ký | CÓ | bảng `enrollments` |
| Mục tiêu học tập | CÓ (23/09) | ô chữ trên hồ sơ (học vụ) và trên tờ báo cáo của em (giảng viên). Điểm mục tiêu em tự đặt (`target_score`) vẫn là chuyện riêng |
| Nguyện vọng trường / ngành | CÓ (23/09) | như trên |
| Tình trạng học tập | MỘT PHẦN | trạng thái tài khoản + trong lớp nào; chưa có một ô tổng hợp |
| Tình trạng học phí | BỎ | thuộc phần kế toán |

## 4 · Quản lý lớp — dòng 4 + dòng 9 (Giáo vụ) + tab *Nhi* #2 · dòng 9 tick TRUE

| Yêu cầu | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Tạo / sửa / xoá lớp | CÓ | `api/admin/classes`, xoá có xác nhận kèm số dòng sẽ mất |
| Loại lớp: lớp nhóm / **gia sư 1–3 em** (họp 24/09: ~400 lớp gia sư) | CÓ (24/09) | `classes.class_type` (§54); lớp gia sư nhận tối đa 3 học viên (trợ giảng không tính) — thêm em thứ 4, dán hàng loạt, cấp tài khoản hàng loạt, đổi loại lớp đều bị chặn kèm lý do. **Tạo nhanh** (24/09): một biểu mẫu — em + giảng viên + thứ/giờ → lớp, em vào lớp, buổi sinh sẵn trong một lượt; xem trước báo trùng giờ giảng viên / em / phòng |
| Tìm / lọc / phân trang danh sách lớp | CÓ (24/09) | tìm theo tên lớp, giáo viên, tên hoặc mã HSA của em; chip đếm theo loại; lọc giáo viên (kể cả lớp người ấy trợ giảng), trạng thái, đợt; 25 lớp/trang; bộ lọc nằm trên đường dẫn |
| Phân công giảng viên | CÓ | `classes.teacher_id` |
| Phân công trợ giảng | CÓ | trợ giảng là thành viên lớp |
| Phân công giáo vụ cho lớp | MỘT PHẦN | học vụ thấy MỌI lớp nên không cần gán; không gán được một học vụ phụ trách riêng |
| Thêm / xoá học sinh, danh sách theo lớp | CÓ | `api/admin/classes/<id>/members` |
| Chuyển học sinh giữa lớp | MỘT PHẦN | rời lớp với lý do "Chuyển lớp" rồi xếp vào lớp mới — hai bước, chưa một thao tác |
| Thiết lập môn / khoá của lớp | CÓ | `classes.course_id` |
| Thời gian bắt đầu / kết thúc | CÓ | `starts_on`, `ends_on`, ngày thi `exam_date` |
| Trạng thái đang học / kết thúc / **tạm dừng** | MỘT PHẦN | có `active`, `finished`, `cancelled`; chưa có "tạm dừng" |
| Lịch sử thay đổi / phân công lớp | MỘT PHẦN | có trong Nhật ký — nhưng chỉ quản trị viên xem được |
| Theo dõi tham gia, thống kê tỷ lệ, cảnh báo nghỉ nhiều | CÓ | báo cáo lớp; "Việc hôm nay": em vắng liền ≥ 2 buổi |
| Tiến độ lớp so với khung chương trình, cảnh báo chậm tiến độ | CHƯA | chưa có "khung chương trình" theo buổi để so |
| **Dòng thời gian học viên** (đăng ký → xếp lớp → … → hoàn thành) | CÓ (23/09) | cuối trang Hồ sơ: cấp tài khoản → khảo sát → vào lớp → chuyển/rời lớp kèm lý do → thi thử / thi ngoài → báo cáo phụ huynh → sửa hồ sơ; chỉ đọc, gom từ nơi ghi gốc (`teaching/dong_thoi_gian.py`) |
| Số buổi đã học / đã nghỉ, có phép / không phép | CÓ | tờ báo cáo: `present/late/absent/excused` |
| Bài đã / chưa hoàn thành, điểm kiểm tra, điểm thi thử | CÓ | bài tập + `mock_attempts` + kết quả thi ngoài |
| Điểm mạnh / yếu | CÓ | bản đồ kỹ năng, bản đồ năng lực |
| Lịch sử chuyển lớp | CÓ (23/09) | trên dòng thời gian: "Rời lớp A — lý do: chuyển lớp" rồi "Vào lớp B". Thao tác chuyển vẫn là hai bước (xem dòng "Chuyển học sinh giữa lớp") |

## 5 · Khoá học + chương trình — dòng 5 + tab *Nhi* #3

| Yêu cầu | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Tạo / quản lý khoá học, chuyên đề / bài học | CÓ | vai Biên tập nội dung, `/admin` |
| Thứ tự nội dung, gán khoá cho lớp | CÓ | thứ tự bài trong khoá; `classes.course_id` |
| Số buổi, thời lượng buổi | MỘT PHẦN | có ở LỚP (sinh lịch), không ở khoá |
| Trạng thái khoá, phiên bản chương trình | MỘT PHẦN | có xuất bản / nháp; không có lịch sử phiên bản |
| Chia chương trình theo **buổi**, gắn bài giảng / tài liệu / bài tập / bài kiểm tra vào buổi | MỘT PHẦN | buổi học có `lesson_refs`, `recording_url`; chưa có "khung chương trình" dựng sẵn theo buổi |
| Gắn video record | MỘT PHẦN | link record theo buổi (`class_sessions.recording_url`) |
| Điều kiện hoàn thành | MỘT PHẦN | có cho bài học trực tuyến; không có cho khoá / chương trình |

## 6 · Báo cáo — dòng 6 (bỏ doanh thu)

| Yêu cầu | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Tổng quan học tập, số học sinh, số lớp | CÓ | "Toàn trung tâm" |
| Báo cáo điểm danh, tiến độ | CÓ | CSV điểm danh + tiến độ theo lớp |
| Kết quả theo lớp | CÓ | báo cáo lớp PDF |
| Kết quả theo môn | MỘT PHẦN | có theo khoá, chưa có báo cáo chéo nhiều lớp |
| Hoàn thành bài tập | MỘT PHẦN | có theo từng bài; chưa có báo cáo tổng |
| Hoạt động / chấm công giảng viên, trợ giảng | CHƯA (dữ liệu có) | `attendance_taken_by`, `graded_by` đã ghi sẵn |
| Học sinh nghỉ nhiều / chậm tiến độ | MỘT PHẦN | nghỉ nhiều: có; chậm tiến độ: cần khung chương trình |
| Bộ lọc thời gian / lớp / khoá | MỘT PHẦN | có theo lớp và đợt; chưa đủ bộ lọc |
| Xuất Excel / CSV | MỘT PHẦN | CSV có; Excel (.xlsx) chưa |

## 7 · Lịch học — dòng 10 + tab *Nhi* #4

| Yêu cầu | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Tạo / sửa / huỷ buổi, dời buổi | CÓ | `planned/done/cancelled`, sửa giờ có cảnh báo |
| Lịch định kỳ, tự sinh buổi, bỏ ngày nghỉ | CÓ | sinh theo tuần + ngày nghỉ theo đợt |
| Tạo buổi học bù | MỘT PHẦN | thêm được buổi lẻ; chưa đánh dấu "buổi bù cho buổi nào" |
| Link Zoom theo lớp / theo buổi | CÓ | `meeting_url` ở cả hai |
| Đổi giảng viên / trợ giảng cho MỘT buổi | CHƯA | giảng viên gắn theo lớp, không theo buổi |
| Đổi phòng, hình thức online / offline | CÓ (24/09) | đặt ở lớp làm mặc định, buổi để trống là theo lớp; buổi lệch (học bù online, mượn phòng) đặt riêng. Học viên thấy phòng trên thẻ "Lớp của bạn" |
| Lịch theo lớp | CÓ | màn Buổi học |
| Lịch theo giảng viên / học viên / toàn trung tâm | CÓ (24/09) | màn "Lịch học" (khu Giảng dạy) theo tuần; học vụ lọc theo giảng viên, lớp, một em (mở từ hồ sơ em). Phạm vi = lớp người xem thấy |
| Thông báo khi lịch đổi | CÓ (24/09) | dời giờ / huỷ / xoá / đổi phòng, hình thức, link của buổi SẮP TỚI → chuông + email cho học viên đang học lớp (anh chốt: không gửi phụ huynh). Em tắt email thì chỉ có chuông |
| Lưu lịch sử thay đổi | MỘT PHẦN | có trong Nhật ký (ghi cả giá trị cũ) — chỉ quản trị viên xem |
| Cảnh báo trùng: lớp | CÓ | trong cùng một lớp (đã có) + giữa các lớp (dòng dưới) |
| Cảnh báo trùng: giảng viên / học viên / phòng | CÓ (24/09) | khi tạo, sửa buổi và khi sinh lịch cả kỳ (từng dòng xem trước). CẢNH BÁO chứ không chặn — có ca trùng cố ý. Phòng chỉ so buổi tại trung tâm, không phân biệt hoa thường |

## 8 · Giáo viên — dòng 14 (tick TRUE), 15, 16, 17, 18 (tick TRUE)

| Yêu cầu | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Danh sách lớp được phân công | CÓ | "Việc hôm nay", khu Giảng dạy |
| Cập nhật hồ sơ học sinh trong lớp (mục tiêu, nguyện vọng) | CÓ (23/09) | khối "Mục tiêu và nguyện vọng" trên tờ báo cáo từng em; chỉ em đang học lớp mình; không in, không gửi phụ huynh; trợ giảng không sửa |
| Điểm danh có mặt / vắng / muộn / xin phép, cập nhật | CÓ | 4 trạng thái; e2e `luong-giang-day.spec.ts` |
| Ai được sửa điểm danh | CÓ | giảng viên, trợ giảng, học vụ, quản trị viên |
| Lịch sử chỉnh sửa điểm danh | MỘT PHẦN | lưu người sửa CUỐI + Nhật ký; chưa có màn lịch sử theo buổi |
| Soạn nội dung buổi, ghi chú sau buổi | CÓ | `class_sessions.topic`, `note`, `lesson_refs` |
| Đính kèm tài liệu cho buổi | CHƯA | chỉ có link record; bài tập thì có `attachment_url` |
| Ghi nhận nội dung đã / chưa hoàn thành, tiến độ thực tế vs kế hoạch | CHƯA | cần khung chương trình |
| Đánh giá mức tiếp thu, đề xuất học bù | CHƯA | |
| Giao bài: tạo, hạn, sửa, xoá / đóng, xem bài nộp, chấm, điểm, nhận xét, trả bài, ai chưa nộp | CÓ | `teaching/assignments.py` |
| Giao bài cho MỘT NHÓM học sinh | CHƯA | bài giao cho cả lớp |
| Lịch sử học tập, điểm danh, kết quả từng bài của một em | CÓ | tờ báo cáo từng em |
| Nhận xét học sinh | CÓ | nhận xét của giảng viên trên tờ (`class_members.note`) |
| Đánh giá tiến bộ | CÓ | "Con có tiến bộ không" trên tờ |
| Đánh dấu học sinh cần hỗ trợ | MỘT PHẦN | hệ thống tự báo "em cần chú ý"; giảng viên chưa tự đánh dấu được |
| Đề xuất hướng học | CHƯA | |

## 9 · Trợ giảng — dòng 20, 21, 22

| Yêu cầu | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Danh sách lớp được phân công, thông tin học sinh | CÓ | chỉ lớp được gán; cắt dữ liệu liên lạc (có chủ ý) |
| Điểm danh, theo dõi bài tập, tiến độ | CÓ | |
| Nhắn tin với học sinh, lịch sử trao đổi | CHƯA | mô-đun mới |
| Nhắc học sinh học / làm bài / vào lớp | CHƯA | |
| Học sinh có dấu hiệu bỏ học, danh sách cần nhắc / cần báo | MỘT PHẦN | "Việc hôm nay" báo em vắng liền, bài chưa chấm |
| Record thuộc buổi nào, link, đã / chưa upload, cập nhật | CÓ | `class_sessions.recording_url` |
| Học sinh đã xem record chưa, xem bao lâu | CHƯA | record là link ngoài — không đo được nếu không tự nhúng trình phát |
| Nhắc chưa xem, báo lỗi record | CHƯA | |

## 10 · Hỗ trợ lớp + thay đổi học tập — dòng 11, 12

| Yêu cầu | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Tiếp nhận / phân loại / phân công / theo dõi yêu cầu hỗ trợ | CHƯA | mô-đun ticket mới |
| Chuyển lớp · chuyển lịch · chuyển môn · bảo lưu · học bù · học lại · nghỉ học · huỷ khoá — có duyệt, ghi người duyệt | CHƯA | có "rời lớp kèm lý do" nhưng không có luồng xin – duyệt |

---

## Phân loại những ô CHƯA / MỘT PHẦN

**Làm được ngay, không phụ thuộc ai** — nằm trong bốn nhóm anh chốt:
hồ sơ học viên mở rộng · tìm kiếm theo username · lịch gộp theo giảng viên / học viên / toàn trung tâm ·
cảnh báo trùng lịch giữa các lớp · online / offline + phòng · thông báo khi lịch đổi · dòng thời gian
học viên + lịch sử chuyển lớp · quên mật khẩu qua email · đăng nhập bằng username.
*(24/09/2026: cả bốn nhóm đã xong — các dòng tương ứng ở trên đã chuyển sang CÓ kèm ngày.)*

**Làm được, cỡ vừa, nên làm sau bốn nhóm:** trạng thái lớp "tạm dừng" · chuyển lớp một thao tác ·
báo cáo hoạt động giảng viên / trợ giảng · xuất Excel · giao bài cho một nhóm · giảng viên tự đánh dấu
"cần hỗ trợ" · lịch sử điểm danh theo buổi · đính kèm tài liệu cho buổi.

**Cần một khối mới lớn:** khung chương trình theo buổi (mở khoá cả "tiến độ vs kế hoạch" và "cảnh báo
chậm tiến độ") · ticket hỗ trợ · luồng xin – duyệt thay đổi học tập · nhắn tin trợ giảng ↔ học viên.

**Không làm được nếu không đổi hạ tầng:** đo thời lượng xem record (cần tự nhúng trình phát thay cho
link ngoài).

**Cần anh xác nhận với khách:** "Xoá tài khoản" — hệ thống cố ý chỉ khoá để giữ lịch sử học tập.
