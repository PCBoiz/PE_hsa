# Ma trận nghiệm thu TopHSA — theo "Bảng phân rã tính năng, Updated 24.9.2026"

Thay cho `docs/DOI_CHIEU_YEU_CAU_TOPHSA_2026-09-23.md` (bản ấy giữ để tra lịch sử). Số dòng ở đây
là ĐÚNG số dòng (cột STT) trong bảng của khách. Cột TRUE của bảng = khách đã nghiệm thu dòng ấy
(anh Sơn xác nhận 25/09) — chỉ khách tick, mình không tick hộ.

**Cách kiểm**: mỗi ô lấy từ MÃ, lược đồ CSDL hoặc lượt chạy trên trình duyệt — không lấy từ chú thích
hay trí nhớ. Bản đo 25/09/2026 (hai lượt dò mã độc lập + các commit tới `bd86d4c`).

**Nhãn**: `CÓ` dùng được ngay · `MỘT PHẦN` có nhưng thiếu điều bảng đòi · `CHƯA` không có ·
`THAY` làm KHÁC chữ trong bảng theo quyết định của anh, **khách phải đồng ý** (việc K2) ·
`BỎ` anh chốt không làm.

**Việc đóng** trỏ tới mục trong `docs/KE_HOACH_TOPHSA_THU_NGHIEM_2026-09-24.md` (kế hoạch v2):
V-a…V-o = mẻ vá rẻ · E1 khung chương trình theo buổi · E2 thông báo chung · E3 hộp "Yêu cầu" ·
E4 Zoom · E5 tự đăng ký · §66 link phụ huynh sống · Đ2 = đợt 2 (§58 đổi GV một buổi, §59 chấm
công khoá tháng, §60 tài liệu R2).

**Spec nghiệm thu**: mỗi dòng sẽ có `frontend/e2e/nghiem-thu/dong-NN.spec.ts` đi đúng kịch bản demo;
một dòng chỉ báo khách "sẵn sàng nghiệm thu" khi spec của nó xanh hai khổ. Cột "Spec" = `—` là chưa có.

## Tóm tắt

| Dòng | Vai · phân hệ | Hiện nay | Việc đóng chính | Spec |
|---|---|---|---|---|
| 1 | Quản trị viên · tài khoản | CÓ — **khách đã nghiệm thu** | — | — |
| 2 | Quản trị viên · người dùng | CÓ — **khách đã nghiệm thu** | — | — |
| 3 | Quản trị viên · tìm kiếm + hồ sơ | MỘT PHẦN (3 ô) | V-m | — |
| 4 | Quản trị viên · lớp học | MỘT PHẦN | V-c, V-j, V-n, V-h, E1 | — |
| 5 | Quản trị viên · khoá học + chương trình | MỘT PHẦN | E1, V-i | — |
| 6 | Quản trị viên · báo cáo | MỘT PHẦN | V-k, V-o, E1 | — |
| 7 | Kế toán · học phí | THAY | V-m (một ô tình trạng) | — |
| 8 | Giáo vụ · tài khoản | CÓ | — | — |
| 9 | Giáo vụ · lớp học | MỘT PHẦN | V-d, E1 | — |
| 10 | Giáo vụ · lịch học | gần đủ | V-g, V-n, E4, Đ2 §58 | — |
| 11 | Giáo vụ · hỗ trợ lớp | CHƯA | E3 | — |
| 12 | Giáo vụ · thay đổi học tập | CHƯA | E3 | — |
| 13 | Giáo viên · tài khoản | CÓ | — | — |
| 14 | Giáo viên · lớp + điểm danh | gần đủ | V-d | — |
| 15 | Giáo viên · chương trình + tiến độ | CHƯA phần lớn | E1, Đ2 §60 | — |
| 16 | Giáo viên · quản lý buổi học | MỘT PHẦN | E1 | — |
| 17 | Giáo viên · giao bài | CÓ (V-e, V-h) | V-e, V-h | — |
| 18 | Giáo viên · theo dõi học sinh | MỘT PHẦN | V-a, V-f | — |
| 19 | Trợ giảng · tài khoản | CÓ | — | — |
| 20 | Trợ giảng · nhắn / nhắc | CHƯA | E3, E2 | — |
| 21 | Trợ giảng · theo dõi | MỘT PHẦN | V-b, V-l, E3 | — |
| 22 | Trợ giảng · record Zoom | MỘT PHẦN | E4, V-l, E3, E2 | — |
| 23 | Phụ huynh · tài khoản | THAY (link riêng) | K2, §66 | — |
| 24 | Phụ huynh · xem | MỘT PHẦN | §66, V-a | — |
| 25 | Phụ huynh · gửi yêu cầu | CHƯA | E3 qua link | — |
| 26 | Học sinh · tài khoản + tự đăng ký | MỘT PHẦN | E5 | — |
| 27 | Học sinh · thông báo | MỘT PHẦN | E2 | — |
| 28 | Học sinh · chương trình + lộ trình | MỘT PHẦN | E1, V-d | — |
| 29 | Học sinh · record | CHƯA | V-l, E4 | — |
| 30 | Học sinh · học liệu | CHƯA | Đ2 §60 | — |
| 31 | Học sinh · bài tập | CÓ (nộp chữ) | Đ2 §60 (nộp tệp) | — |
| 32 | Học sinh · trao đổi | MỘT PHẦN | E3 | — |
| * | Phân hệ thông báo chung | MỘT PHẦN | E2 | — |

**Năm chỗ DOI_CHIEU 23/09 báo quá tay** (đã sửa trong bảng dưới): (1) "nhận xét học sinh — CÓ": không
màn nào ghi được `class_members.note`, và cột ấy còn bị ghi chú chuyển lớp dùng chung → lỗi rò đã vá
`e328ade`; (2) TG "dấu hiệu bỏ học — MỘT PHẦN": TG không nhận `vangLien`/`canChuY`
(`teaching/viec_hom_nay.py:225`) → với TG là CHƯA; (3) "record — CÓ": chỉ phía nhân sự, API học viên không
trả `recording_url` (`teaching/lop_cua_toi.py`); (4) "soạn nội dung buổi … `lesson_refs`": không màn nào
dùng; (5) "trạng thái khoá — xuất bản/nháp": `is_published` không sửa được qua API
(`courseadmin/views.py:31`).

---

## Dòng 1, 8, 13, 19 — Tài khoản (Quản trị viên, Giáo vụ, Giáo viên, Trợ giảng) · CÓ

| Ý trong bảng | Trạng thái | Bằng chứng | Cách demo |
|---|---|---|---|
| 1.1 Đăng nhập bằng email | CÓ | `accounts/views.py` `LoginView` | `/login` → email + mật khẩu → vào khu của vai |
| 1.2 Đăng nhập bằng username | CÓ | cùng ô nhận email / SĐT / tên đăng nhập (§51) | gõ tên đăng nhập thay email |
| 1.3 Hiện/ẩn mật khẩu | CÓ | nút mắt ở ô mật khẩu | bấm mắt |
| 1.4 Ghi nhớ đăng nhập | CÓ | `accounts/ghi_nho.py` — tick = phiên 30 ngày, không tick = hết khi đóng trình duyệt | tick "Ghi nhớ đăng nhập trên máy này" |
| 1.5 Quên mật khẩu | CÓ | `accounts/quen_mat_khau.py` — link một lần 30 phút tới email của tài khoản (§52) | "Đặt lại qua email" |
| 1.6 Đăng xuất | CÓ | menu tài khoản, thu hồi phiên | menu tên người → Đăng xuất |

## Dòng 2 — Quản lý người dùng · CÓ (khách đã nghiệm thu)

| Ý trong bảng | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Tạo / khoá / mở khoá | CÓ | cấp hàng loạt `api/admin/users/bulk`; khoá/mở `api/admin/users/<id>/status` (chỉ quản trị viên) |
| Phân quyền theo vai | CÓ | 6 vai (`common/permissions.py`), màn "Ai làm được gì" |
| Xoá tài khoản | không làm — đã nghiệm thu | chỉ khoá, giữ lịch sử học tập |
| Xem trạng thái | CÓ | cột trạng thái + lý do khoá |
| Quan hệ Giáo viên – Học sinh | CÓ (qua lớp) | giáo viên ↔ lớp ↔ học viên; người tư vấn trên hồ sơ |
| Thông tin theo loại user | CÓ | trang Hồ sơ theo vai |
| Admin + GV reset mật khẩu | MỘT PHẦN — đã nghiệm thu | quản trị viên + học vụ reset; giảng viên không (`teaching/views.py:806`) |
| Admin + GV import | MỘT PHẦN — đã nghiệm thu | quản trị viên + học vụ (học vụ chỉ vai Học viên); giảng viên không |
| Admin import + export | CÓ | dán danh sách có xem trước (trần 50/lượt); `api/admin/export/users.csv` |

## Dòng 3 — Tìm kiếm + hồ sơ học viên · MỘT PHẦN

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Tìm theo họ tên, email, username, SĐT | CÓ | `q` ở `teaching/admin_users.py:113` (chuẩn hoá SĐT, khớp mã HSA) |
| Mã học viên, họ tên, ngày sinh, trường, lớp, SĐT, email | CÓ | `users.*` (§51), trang Hồ sơ |
| Tỉnh/Thành phố | CÓ (V-m) | ô chọn 34 tỉnh/thành sau sáp nhập 2025 (`teaching/tinh_thanh.py` = `src/lib/tinhThanh.ts`, guard `tinh-thanh.test.mjs`); giá trị cũ gõ tay vẫn hiện nguyên văn tới khi chọn lại |
| Thông tin / SĐT / email phụ huynh | CÓ | `parent_name/phone/email` |
| Người tư vấn, nguồn tuyển sinh | CÓ | chọn từ danh sách (§51) |
| Khoá học đã đăng ký | CÓ | môn mở theo lớp (1.3) |
| Mục tiêu học tập, nguyện vọng trường/ngành | CÓ | `study_goal`, `aspiration` |
| Tình trạng học tập | CÓ (V-m) | TÍNH, không lưu: đang học / tạm dừng / đã học xong / bảo lưu / đã nghỉ / chưa xếp lớp (`teaching/tinh_trang.py`, một biểu thức SQL cho hồ sơ, cột + ô lọc ở Tài khoản, tệp xuất); hồ sơ kèm lớp đang học (sĩ số thật) + môn mở qua lớp — `teaching/tests_tinh_trang_hoc_vien.py` |
| Tình trạng học phí | THAY (V-m làm xong) | một ô chọn tay trên hồ sơ (Đã đóng / Sắp hết / Hết / Bảo lưu; `users.tuition_status`, CHECK §63 lưu mã), có nhật ký, lọc được ở Tài khoản — khách phải đồng ý (K2) |

## Dòng 4 — Quản lý lớp học (Quản trị viên) · MỘT PHẦN

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Tạo / sửa / xoá lớp | CÓ | `api/admin/classes`; xoá có xác nhận |
| Thêm từng HS / import DS theo **biểu mẫu** | CÓ (V-j) | dán email CÓ; "Nhập học viên từ tệp mẫu" ở Học viên của lớp: tải mẫu .xlsx → kiểm tra từng dòng → nhập (em có sẵn vào lớp, em mới được cấp tài khoản qua cùng hàm `cap_tai_khoan` với ô dán; trần 50, lớp gia sư 3) — `teaching/nhap_hoc_vien.py`, `teaching/tests_nhap_hoc_vien.py` |
| Thêm / xoá HS khỏi lớp | CÓ | `api/admin/classes/<id>/members` |
| Chuyển HS giữa các lớp | CÓ | một thao tác (1.2c, `teaching/chuyen_lop.py`) |
| Thiết lập môn, thời gian bắt đầu / kết thúc | CÓ | `course_id`, `starts_on`, `ends_on` |
| Trạng thái đang học / kết thúc / **tạm dừng** | CÓ (V-c) | `classes_status_check` §35 thêm `paused`; `teaching/vocab.py::TRANG_THAI_LOP`; nhãn "Tạm dừng" `quan-tri/lop-hoc/lop.ts`. Em giữ quyền môn (`courses/truy_cap.py` chỉ chặn lớp huỷ — test `courses/tests_truy_cap.py::test_lop_tam_dung_van_giu_quyen_mon`); không vào "chưa điểm danh" (`teaching/viec_hom_nay.py::_chua_diem_danh`); không sinh lịch (`teaching/sinh_buoi.py` 409). Demo: học vụ → Lớp học → Sửa lớp → Trạng thái "Tạm dừng" → bộ lọc Trạng thái có "Tạm dừng"; giảng viên mở Buổi học của lớp ấy thấy "Lớp đang tạm dừng…" thay khối sinh lịch |
| Phân công GV, giáo vụ, TG | MỘT PHẦN | GV + TG CÓ; học vụ thấy mọi lớp, không gán riêng |
| Lịch sử thay đổi / phân công lớp | CÓ (V-n) | "Lịch sử thay đổi của lớp" ở Học viên của lớp: sửa lớp, xếp / cho rời / chuyển em, gán trợ giảng, tạo / sửa / huỷ buổi, mới nhất trước — chỉ phần của lớp ấy (`GET /api/admin/classes/<id>/lich-su`, IsAdminOrAcademic; nhật ký đầy đủ vẫn chỉ quản trị viên) — `teaching/tests_lich_su_lop.py` |
| Dòng thời gian Đăng ký → … → Hoàn thành | MỘT PHẦN | "Kiểm tra / Thi thử / Kết quả" CÓ (V-h): mốc "Bài kiểm tra: …" theo NGÀY làm bài, điểm hoặc "Vắng" (`teaching/dong_thoi_gian.py`, loại `kiem-tra`); "Đăng ký" tự đăng ký → **E5** |
| Đang học lớp nào, đã học / nghỉ bao nhiêu buổi, có phép / không | CÓ | tờ báo cáo từng em (`present/late/absent/excused`) |
| Tiến độ chương trình | CHƯA | → **E1** |
| Bài đã / chưa hoàn thành, điểm mạnh / yếu, lịch sử chuyển lớp | CÓ | bài tập + bản đồ kỹ năng + dòng thời gian |
| Điểm kiểm tra, điểm thi thử | CÓ (V-h; thi thử online đã bỏ) | Bài kiểm tra trên lớp = một loại bài giao: `assignments.kind = 'kiem_tra'` + `held_on`, `submissions.absent` (§62f). Giảng viên / trợ giảng nhập điểm cả lớp trên một bảng, ghi "Vắng" (`teaching/assignments.py::AssignmentGradingView`); học viên không nộp được (409) và không bị tính "chưa nộp". Điểm lên sổ điểm (loại "Bài kiểm tra", `stats/gradebook.py`), dòng thời gian hồ sơ, tờ phụ huynh khối "Bài kiểm tra" (`teaching/parent_report.py::_kiem_tra_lop`, PDF `teaching/bao_cao_pdf.py`). Test `teaching/tests_kiem_tra.py` (6) + `tests_bao_cao_pdf.py` (2). Demo: giảng viên → Bài tập của lớp → "Giao bài mới" → Loại "Bài kiểm tra trên lớp (nhập điểm)" + ngày → "Nhập điểm" → gõ điểm / tick "Vắng" → Lưu → mở tờ báo cáo của em |

## Dòng 5 + "Quản lý chương trình học" — Khoá học + chương trình · MỘT PHẦN

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Quản lý môn trong khoá, chuyên đề / bài học, thứ tự | CÓ | khu Giáo trình (Biên tập nội dung) |
| **Tiến trình theo số buổi kèm tên bài**, chia theo buổi | CHƯA | không có bảng khung chương trình → **E1** |
| Thời lượng buổi | MỘT PHẦN | có ở LỚP (sinh lịch), không ở khoá → **E1** |
| Gán khoá cho lớp | CÓ | `classes.course_id` |
| Trạng thái khoá | CÓ (V-i) | nút "Chuyển về nháp / Mở cho học viên" + cột Trạng thái ở khu Giáo trình (`courseadmin/views.py`, nhật ký `course.publish`); cổng `courses/truy_cap.py` giấu khoá nháp với học viên NGAY (quên đệm), nhân sự vẫn xem — `courses/tests_khoa_nhap.py` |
| Phiên bản / lịch sử chỉnh sửa chương trình | CHƯA | → **E1** (bản nháp / xuất bản, lớp giữ bản đã nhận) |
| Gắn bài giảng | CÓ | bài học trực tuyến |
| Gắn video record | MỘT PHẦN | link theo buổi, học viên không thấy → **V-l**, **E4** |
| Gắn tài liệu | CHƯA | → **Đ2 §60** |
| Gắn bài tập, bài kiểm tra | MỘT PHẦN | bài tập theo lớp, không gắn vào khung → **E1** + **V-h** |
| Điều kiện hoàn thành | MỘT PHẦN | cố định trong mã (bài xong / khoá 100%) → **E1** |

## Dòng 6 — Báo cáo · MỘT PHẦN

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| 6.1 Tổng quan học tập, số học sinh, số lớp | CÓ | "Toàn trung tâm" (`teaching/overview.py`) |
| 6.2 Doanh thu | BỎ | anh chốt 23/09 |
| 6.3 Chấm công GV/TG | CÓ, chỉ xem (V-o) | trang "Chấm công" (Vận hành, quản trị viên + học vụ): theo tháng, từng giảng viên VÀ trợ giảng — buổi đã dạy, tổng giờ, tự điểm danh, điểm danh muộn, tải Excel (`teaching/cham_cong.py`, `teaching/tests_cham_cong.py`). Khoá tháng + chỉnh tay → **Đ2 §59** |
| Điểm danh HS, tiến độ, kết quả theo lớp | CÓ | CSV điểm danh + tiến độ; báo cáo lớp PDF |
| Kết quả theo môn, hoàn thành bài tập (tổng) | MỘT PHẦN | theo khoá / từng bài; chưa báo cáo chéo |
| Hoạt động GV/TG | MỘT PHẦN | buổi dạy / điểm danh theo tháng CÓ (V-o); các hoạt động khác (chấm bài, nhắn tin) chưa gộp |
| HS nghỉ nhiều / chậm tiến độ | MỘT PHẦN | nghỉ nhiều CÓ; chậm tiến độ → **E1** |
| Bộ lọc thời gian / lớp / môn / khoá | CÓ (V-k) | tổng quan lọc đợt + ngày; tải chuyên cần lọc khoảng ngày; tải danh sách tài khoản lọc thêm đợt học, môn, ngày cấp (`teaching/exports.py`, `admin_users.build_user_filters`) — `teaching/tests_xuat_excel.py` |
| Xuất Excel / CSV | CÓ (V-k) | hộp "Tải bảng tính" (sổ buổi học của lớp) và "Tải danh sách" (Tài khoản): chọn Excel (.xlsx) hoặc CSV; một bộ ghi `common/bangtinh.ghi_xlsx` (ô chữ không bao giờ thành công thức), trợ giảng không nhận cột liên lạc |

## Dòng 7 — Kế toán · học phí · THAY

Anh chốt 25/09: không sổ tiền, không doanh thu, không vai Kế toán. Thay bằng ô "Tình trạng học phí"
trên hồ sơ (**V-m**). Khách phải đồng ý (K2). Dữ liệu "cơ sở tính học phí" (buổi đã học / có mặt / vắng
theo em) đã có cho quản trị viên ở "Cơ sở học phí".

## Dòng 9 — Giáo vụ · lớp học · MỘT PHẦN

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Tạo / cập nhật lớp, thông tin HS, xếp lớp, điều chuyển | CÓ | như dòng 4 |
| Theo dõi tham gia, thống kê tỉ lệ, cảnh báo nghỉ nhiều | CÓ | báo cáo lớp; "Việc hôm nay" (vắng liền ≥ 2 buổi) |
| Điểm danh có mặt / vắng / muộn, cập nhật | CÓ | 4 trạng thái (`teaching/sessions.py:57`) |
| Xem lịch sử điểm danh | CÓ (V-d) | bảng `attendance_history` (§62c) ghi trong cùng giao dịch lưu điểm danh (`teaching/sessions.py::SessionAttendanceView.post`), điền ngược từ nhật ký; `GET /api/teach/sessions/<id>/attendance/history` (`SessionAttendanceHistoryView`). Test `teaching/tests_lich_su_diem_danh.py` (4). Demo: học vụ/giảng viên → Buổi học → Điểm danh một buổi → sửa một em, Lưu → mở "Lịch sử sửa điểm danh" dưới sổ |
| Tiến độ lớp so với khung, cảnh báo chậm | CHƯA | → **E1** |

## Dòng 10 — Giáo vụ · lịch học · gần đủ

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Tạo / sửa / huỷ / dời, định kỳ, tự sinh buổi, bỏ ngày nghỉ | CÓ | `sinh_buoi.py`, màn Buổi học |
| Tạo lịch học bù | CÓ (V-g) | `POST /api/teach/sessions/<id>/buoi-bu` (`teaching/buoi_bu.py::BuoiBuView`): `class_sessions.makeup_for` + `session_participants` (§62e); sổ điểm danh, chuyên cần, "chưa điểm danh", học phí, lịch em, báo đổi lịch chỉ tính các em của buổi (`teaching/nguoi_buoi.thuoc_buoi`); chuông + thư `hoc_bu` sau khi lưu. Test `teaching/tests_buoi_bu.py` (5). Demo: giáo vụ/giảng viên → Buổi học của lớp → "Tạo buổi bù" trên buổi gốc → chọn giờ + em (em vắng tick sẵn) → dòng mới mang chip "học bù · N em" |
| Đổi GV / TG cho một buổi | CHƯA | GV gắn theo lớp → **Đ2 §58** |
| Đổi phòng, online / offline | CÓ | ở lớp làm mặc định, buổi đặt riêng |
| Tạo / quản lý Zoom | MỘT PHẦN | dán link (lớp + buổi) → **E4** |
| Lịch theo lớp / GV / HS / toàn trung tâm | CÓ | màn "Lịch học" |
| Thông báo khi lịch đổi | CÓ | chuông + email học viên (không gửi phụ huynh — anh chốt) |
| Lưu lịch sử thay đổi | CÓ (V-n) | lịch sử thay đổi của lớp cho học vụ (tạo / sửa / huỷ / sinh buổi) — như dòng 4 |
| Cảnh báo trùng GV / phòng / lớp / HS | CÓ | `teaching/trung_lich.py` (cảnh báo, không chặn) |

## Dòng 11 — Hỗ trợ lớp học · CHƯA → E3

Tiếp nhận, phân loại (học tập / lịch học / kỹ thuật / tài khoản), phân công, trạng thái, kết quả,
chuyển GV/TG, lịch sử — không có bảng hay màn nào. **E3** hộp "Yêu cầu".

## Dòng 12 — Quản lý thay đổi học tập · CHƯA → E3

Có thao tác TRỰC TIẾP (chuyển lớp một thao tác, rời lớp kèm lý do `completed/dropped/transferred`)
nhưng không có luồng xin → duyệt → ghi người duyệt. **E3**: chuyển lớp, chuyển lịch, chuyển môn, bảo
lưu, học bù, học lại, nghỉ học, huỷ khoá — duyệt xong hệ thống tự làm việc ấy.

## Dòng 14 — Giáo viên · lớp + điểm danh · gần đủ

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Danh sách lớp được phân công | CÓ | "Việc hôm nay", khu Giảng dạy |
| Cập nhật mục tiêu, nguyện vọng HS | CÓ | tờ báo cáo từng em (`teaching/ho_so.py`) |
| Điểm danh có mặt / vắng / muộn / xin phép, cập nhật | CÓ | màn Buổi học |
| Người được phép sửa | CÓ | GV lớp mình, TG lớp được gán, học vụ, quản trị viên |
| Lưu lịch sử chỉnh sửa | CÓ (V-d) | như dòng 9: mỗi lần ĐỔI một dòng (ai, từ gì → gì, lúc nào); lưu lại y hệt ghi 0 dòng. Demo: giảng viên/trợ giảng → Buổi học → Điểm danh → "Lịch sử sửa điểm danh" |
| Thống kê tỉ lệ, cảnh báo nghỉ nhiều | CÓ | |

## Dòng 15 — Giáo viên · chương trình + tiến độ · CHƯA phần lớn

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| Soạn / chuẩn bị nội dung buổi | MỘT PHẦN (`topic`, `note`) | **E1** |
| Đính kèm tài liệu | CHƯA | **Đ2 §60** |
| Nội dung đã / chưa hoàn thành | CHƯA | **E1** sổ đầu bài |
| Ghi chú sau buổi | CÓ (`class_sessions.note`) | — |
| Tiến độ thực tế vs kế hoạch, đề xuất điều chỉnh | CHƯA | **E1** (+ **E3** cho đề xuất) |

## Dòng 16 — Giáo viên · quản lý buổi học · MỘT PHẦN

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| Buổi đã diễn ra, tình hình lớp | CÓ (trạng thái `done`, điểm danh, `note`) | — |
| Nội dung thực tế / chưa hoàn thành, mức tiếp thu | CHƯA | **E1** |
| Đề xuất HS cần hỗ trợ | MỘT PHẦN (hệ thống tự báo) | **E1** / **V-f** |
| Đề xuất học bù / điều chỉnh tiến độ | CHƯA | **E1** + **E3** |

## Dòng 17 — Giáo viên · giao bài · CÓ

Tạo, hạn, sửa, xoá / đóng, danh sách, xem bài nộp, chấm, nhập điểm, nhận xét, trả bài, ai chưa nộp:
CÓ (`teaching/assignments.py`). **Thiết lập đối tượng nhận bài** (một nhóm em): CÓ (V-e) —
`assignments.target_mode` + `assignment_targets` (§62d); MỘT hàm lọc `teaching/nhan_bai.giao_cho` ở mọi chỗ
đọc bài (danh sách + sĩ số từng bài, bảng chấm, bài của học viên, nộp bài, thẻ lớp, tờ phụ huynh, Việc hôm
nay, chuông "bài mới"). Test `teaching/tests_nhan_bai.py` (10). Demo: giảng viên → Bài tập của lớp → "Giao bài
mới" → "Giao cho: Chọn học viên" → tick 2 em → Giao bài; em thứ ba không thấy bài ở mục Bài tập.
Bài kiểm tra ngoại tuyến GV nhập điểm: CÓ (V-h) — Loại "Bài kiểm tra trên lớp (nhập điểm)" khi giao bài,
nút "Nhập điểm" mở bảng cả lớp có ô "Vắng" (xem dòng 4, "Điểm kiểm tra"). Test `teaching/tests_kiem_tra.py` (6).

## Dòng 18 — Giáo viên · theo dõi học sinh · MỘT PHẦN

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Lịch sử học tập, điểm danh, bài tập, kết quả từng bài | CÓ | tờ báo cáo từng em |
| **Ghi nhận nhận xét học sinh** | CÓ (V-a) | `PUT …/students/<u>/danh-gia` (`teaching/danh_gia.py::DanhGiaHocVienView`) ghi `class_members.teacher_comment` (§62a) vào lượt đang mở, không đụng `note`; tờ phụ huynh in `membership.teacherNote`. Test `teaching/tests_danh_gia.py` (7). Demo: giảng viên → Báo cáo phụ huynh → Xem tờ của em → khối "Đánh giá của giảng viên" → ô "Nhận xét gửi phụ huynh" → Lưu đánh giá → tờ bên dưới in "Nhận xét của giảng viên" |
| Đánh giá mức độ tiến bộ | CÓ | "Con có tiến bộ không" trên tờ |
| Đánh dấu cần hỗ trợ | CÓ (V-f) | `class_members.can_ho_tro` + lý do (§62b), cùng đường `danh-gia` (trợ giảng đặt được); hiện ở "Việc hôm nay" khối "Cần hỗ trợ" (`viec_hom_nay._can_ho_tro`) và dòng thời gian (`dong_thoi_gian._danh_gia`, nhật ký `class.member.assess`). Demo: giảng viên tick "Đánh dấu em cần hỗ trợ" trên tờ của em, hoặc trợ giảng bấm "Báo cần hỗ trợ" trên dòng em vắng liền ở Việc hôm nay |
| Đề xuất hướng học tập | CÓ (V-f) | `class_members.de_xuat_huong_hoc` (§62b), chỉ giảng viên trở lên, nội bộ (không lên tờ phụ huynh). Demo: ô "Đề xuất hướng học" trong khối "Đánh giá của giảng viên"; học vụ thấy mốc "Đề xuất hướng học" trên dòng thời gian của em |

## Dòng 20 — Trợ giảng · nhắn tin / nhắc · CHƯA

Danh sách lớp + thông tin HS: CÓ (cắt liên lạc — có chủ ý). Nhắn tin / nhận / lịch sử, ghi nhận em
không phản hồi, chuyển vấn đề cho GV / giáo vụ → **E3**. Nhắc học bài / làm bài / vào lớp → **E2**.
Chat thời gian thực: không làm (anh chốt 25/09 — Zalo vẫn để chat).

## Dòng 21 — Trợ giảng · theo dõi · MỘT PHẦN

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| Điểm danh, theo dõi bài tập, tiến độ | CÓ | — |
| Hỗ trợ giải đáp | CHƯA | **E3** |
| Theo dõi việc xem record | CHƯA | **V-l** (mở / chưa mở), **E4** (% đã xem) |
| Dấu hiệu bỏ học, danh sách cần nhắc / cần báo | CÓ phần theo dõi (V-b) + báo "cần hỗ trợ" (V-f); trao đổi hai chiều chờ **E3** | `teaching/viec_hom_nay.py` `ViecHomNayView.get` trả `vangLien` + `canChuY` cho mọi vai, phạm vi `_lop_cua`; test `tests_viec_hom_nay.py::test_tro_giang_thay_vang_lien_chi_lop_minh`. Demo: đăng nhập trợ giảng → "Việc hôm nay" → khối "Vắng liền" / "Cần chú ý ngay" của lớp mình, dòng dẫn về sổ buổi học |

## Dòng 22 — Trợ giảng · record Zoom · MỘT PHẦN

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| TG dán link record vào buổi, record thuộc buổi nào, link, giáo vụ / TG cập nhật | CÓ | `class_sessions.recording_url` (màn Buổi học) |
| Đã upload / chưa upload | MỘT PHẦN (suy từ link có / không) | **E4** tự gắn từ Zoom + danh sách buổi thiếu record |
| HS đã xem / chưa xem | CHƯA | **V-l**, **E4** |
| Nhắc HS chưa xem | CHƯA | **E2** |
| Báo lỗi record | CHƯA | **E3** |

## Dòng 23 — Phụ huynh · tài khoản · THAY

Anh chốt 25/09: phụ huynh KHÔNG có tài khoản; dùng link riêng (không mật khẩu, thu hồi được, có hạn).
Khách phải đồng ý (K2). Nâng link thành "link theo dõi" sống → **§66**.

## Dòng 24 — Phụ huynh · xem · MỘT PHẦN

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Lịch học, lớp, môn, GV, TG | MỘT PHẦN | tờ báo cáo có lớp + GV; không lịch, không TG → **§66** |
| Thông báo khi lịch đổi | THAY | không gửi phụ huynh (anh chốt); link sống hiện "thay đổi gần đây" → **§66** |
| Tình trạng tham gia | CÓ (tổng số theo kỳ) | `parent_report.py::_chuyen_can` |
| Bài tập, hạn, đã / chưa nộp; điểm | CÓ | `_bai_tap_lop` |
| Nhận xét của GV | CÓ (V-a) | nhận xét bài CÓ; nhận xét chung = `membership.teacherNote` từ `teacher_comment` (giảng viên ghi ở khối "Đánh giá của giảng viên"), đi cả đường dẫn phụ huynh (`rut_gon_cho_link` giữ khoá này) |
| Tiến độ học tập | CÓ (theo kỳ cố định của link) | → link sống **§66** |

## Dòng 25 — Phụ huynh · gửi yêu cầu · CHƯA → E3 qua link

## Dòng 26 — Học sinh · tài khoản · MỘT PHẦN

Đăng nhập / ghi nhớ / quên mật khẩu / đăng xuất: CÓ (như dòng 1). **Tự đăng ký + email xác nhận**:
CHƯA (`RegisterView` chỉ quản trị viên, `users.is_verified` chưa ai ghi) → **E5**: tài khoản chờ xếp
lớp, nguồn "Tự đăng ký", hàng chờ "Đăng ký mới" cho giáo vụ.

## Dòng 27 — Học sinh · thông báo · MỘT PHẦN

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| Thay đổi lịch, bài tập mới, kết quả | CÓ (`lich_doi`, `assignment_new`, `assignment_graded`) | — |
| Lịch học (buổi mới) | CHƯA | **E2** |
| Thông báo từ trung tâm | CHƯA | **E2** |
| Đánh dấu đã đọc / chưa đọc | MỘT PHẦN (chỉ "đã đọc") | **E2** |

## Dòng 28 — Học sinh · chương trình + lộ trình · MỘT PHẦN

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| Buổi tham gia / vắng / muộn (số đếm) | CÓ ("Lớp của tôi") | — |
| Lịch sử điểm danh từng buổi, tổng số buổi | CÓ (V-d) | `GET /api/lop-cua-toi` → `lop[].diemDanh` (`teaching/lop_cua_toi.py`, cùng `_buoi_cua_em` với chuyên cần); thẻ "Lớp của bạn" → "Điểm danh từng buổi" (`components/LopCuaToi.tsx`). Demo: học viên → Trang của tôi → thẻ lớp → mở "Điểm danh từng buổi" |
| % hoàn thành chương trình, bài / chuyên đề đã / chưa, tiến độ theo môn | MỘT PHẦN (bài tự học trực tuyến) | **E1** (theo khung của lớp) |
| So sánh thực tế với kế hoạch | MỘT PHẦN (kế hoạch tự học cá nhân) | **E1** |

## Dòng 29 — Học sinh · record · CHƯA → V-l, E4

Danh sách record theo buổi, tìm kiếm, đã xem / chưa xem (**V-l**), % đã xem cho TG (**E4** — thử trên
tài khoản Zoom thật trước: Zoom chỉ trả tên người xem khi người xem đăng nhập Zoom).

## Dòng 30 — Học sinh · học liệu · CHƯA → Đ2 §60

## Dòng 31 — Học sinh · bài tập · CÓ

Nhận bài, làm và nộp, xem kết quả + nhận xét: CÓ (`/bai-tap`, chuông). Nộp chữ; nộp tệp → **Đ2 §60**.

## Dòng 32 — Học sinh · trao đổi · MỘT PHẦN → E3

Có diễn đàn (mục câu hỏi) và trợ lý AI; không có kênh gửi thẳng GV / TG, không yêu cầu hỗ trợ.

## * Phân hệ thông báo chung · MỘT PHẦN → E2

Có: chuông + email cho đổi / huỷ lịch, bài tập mới, bài đã chấm. Thiếu: lịch mới, học bù, hạn nộp,
nghỉ học, cảnh báo tiến độ, thông báo trung tâm; gửi theo lớp / môn / nhóm / cá nhân; chưa đọc; lịch sử
đầy đủ (nay 30 dòng gần nhất). Nền cho gửi tin cậy: hộp thư đi (outbox) — hiện thư gửi trên luồng rời,
lỗi chỉ ghi log.
