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
| 3 | Quản trị viên · tìm kiếm + hồ sơ | CÓ (V-m xong, chờ e2e) | V-m | — |
| 4 | Quản trị viên · lớp học | MỘT PHẦN | V-c, V-j, V-n, V-h, E1 | — |
| 5 | Quản trị viên · khoá học + chương trình | MỘT PHẦN | E1, V-i | — |
| 6 | Quản trị viên · báo cáo | MỘT PHẦN | V-k, V-o, E1 | — |
| 7 | Kế toán · học phí | THAY (V-m xong) | V-m (một ô tình trạng), K2 | — |
| 8 | Giáo vụ · tài khoản | CÓ | — | — |
| 9 | Giáo vụ · lớp học | MỘT PHẦN | V-d, E1 | — |
| 10 | Giáo vụ · lịch học | gần đủ | V-g, V-n, E4, Đ2 §58 | — |
| 11 | Giáo vụ · hỗ trợ lớp | CÓ (E3, chờ khách xem) | E3 | `e2e/yeu-cau.spec.ts` (một phần) |
| 12 | Giáo vụ · thay đổi học tập | MỘT PHẦN (E3: duyệt = tự làm 5/8 loại) | E3 | — |
| 13 | Giáo viên · tài khoản | CÓ | — | — |
| 14 | Giáo viên · lớp + điểm danh | gần đủ | V-d | — |
| 15 | Giáo viên · chương trình + tiến độ | MỘT PHẦN — E1 xong, còn tài liệu | Đ2 §60, E3 | — |
| 16 | Giáo viên · quản lý buổi học | CÓ (E1 + E3 đề xuất → yêu cầu) | — | — |
| 17 | Giáo viên · giao bài | MỘT PHẦN — không sửa được bài đã giao | V-e, V-h + ô sửa bài | — |
| 18 | Giáo viên · theo dõi học sinh | MỘT PHẦN | V-a, V-f | — |
| 19 | Trợ giảng · tài khoản | CÓ | — | — |
| 20 | Trợ giảng · nhắn / nhắc | MỘT PHẦN (E3: báo lên, em không phản hồi) | E3 (TG nhắn HS — chờ quyết), E2 | — |
| 21 | Trợ giảng · theo dõi | MỘT PHẦN (E3 giải đáp xong) | V-l, E4 | — |
| 22 | Trợ giảng · record Zoom | MỘT PHẦN | E4, V-l, E3, E2 | — |
| 23 | Phụ huynh · tài khoản | THAY (link riêng) | K2, §66 | — |
| 24 | Phụ huynh · xem | MỘT PHẦN | §66, V-a | — |
| 25 | Phụ huynh · gửi yêu cầu | CÓ qua link (E3, chờ khách xem) | — | `e2e/yeu-cau.spec.ts` |
| 26 | Học sinh · tài khoản + tự đăng ký | MỘT PHẦN | E5 | — |
| 27 | Học sinh · thông báo | MỘT PHẦN | E2 | — |
| 28 | Học sinh · chương trình + lộ trình | MỘT PHẦN | E1, V-d | — |
| 29 | Học sinh · record | CHƯA | V-l, E4 | — |
| 30 | Học sinh · học liệu | CHƯA | Đ2 §60 | — |
| 31 | Học sinh · bài tập | CÓ (nộp chữ) | Đ2 §60 (nộp tệp) | — |
| 32 | Học sinh · trao đổi | CÓ (E3, chờ khách xem) | — | `e2e/yeu-cau.spec.ts` |
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

## Dòng 3 — Tìm kiếm + hồ sơ học viên · CÓ (V-m, chờ e2e hai khổ)

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
| Tiến độ chương trình | CÓ (E1) | màn **Chương trình lớp** `/giang-day/chuong-trinh/<lớp>` (đã dạy / kế hoạch / trễ / chưa ghi sổ, % từng em) — `chuong_trinh/tien_do.py`; chip ở Lớp học. Demo: học vụ → Lớp học → nút "Chương trình" |
| Bài đã / chưa hoàn thành, điểm mạnh / yếu, lịch sử chuyển lớp | CÓ | bài tập + bản đồ kỹ năng + dòng thời gian |
| Điểm kiểm tra, điểm thi thử | CÓ (V-h; thi thử online đã bỏ) | Bài kiểm tra trên lớp = một loại bài giao: `assignments.kind = 'kiem_tra'` + `held_on`, `submissions.absent` (§62f). Giảng viên / trợ giảng nhập điểm cả lớp trên một bảng, ghi "Vắng" (`teaching/assignments.py::AssignmentGradingView`); học viên không nộp được (409) và không bị tính "chưa nộp". Điểm lên sổ điểm (loại "Bài kiểm tra", `stats/gradebook.py`), dòng thời gian hồ sơ, tờ phụ huynh khối "Bài kiểm tra" (`teaching/parent_report.py::_kiem_tra_lop`, PDF `teaching/bao_cao_pdf.py`). Test `teaching/tests_kiem_tra.py` (6) + `tests_bao_cao_pdf.py` (2). Demo: giảng viên → Bài tập của lớp → "Giao bài mới" → Loại "Bài kiểm tra trên lớp (nhập điểm)" + ngày → "Nhập điểm" → gõ điểm / tick "Vắng" → Lưu → mở tờ báo cáo của em |

## Dòng 5 + "Quản lý chương trình học" — Khoá học + chương trình · MỘT PHẦN

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Quản lý môn trong khoá, chuyên đề / bài học, thứ tự | CÓ | khu Giáo trình (Biên tập nội dung) |
| **Tiến trình theo số buổi kèm tên bài**, chia theo buổi | CÓ (E1) | §64 + màn **Khung chương trình** `/giao-trinh/khung-chuong-trinh` (học vụ, biên tập, quản trị): buổi, nội dung từng buổi, trọng số, học liệu |
| Thời lượng buổi | CÓ (E1) | `syllabus_sessions.duration_minutes`, ô "Thời lượng (phút)" ở màn Khung chương trình |
| Gán khoá cho lớp | CÓ | `classes.course_id` |
| Trạng thái khoá | CÓ (V-i) | nút "Chuyển về nháp / Mở cho học viên" + cột Trạng thái ở khu Giáo trình (`courseadmin/views.py`, nhật ký `course.publish`); cổng `courses/truy_cap.py` giấu khoá nháp với học viên NGAY (quên đệm), nhân sự vẫn xem — `courses/tests_khoa_nhap.py` |
| Phiên bản / lịch sử chỉnh sửa chương trình | CÓ (E1) | bản nháp → xuất bản (bản cũ cùng chuỗi "Đã thay"), "Tạo bản mới" chép cả cây, lớp giữ bản đã nhận; mọi thao tác vào Nhật ký (`syllabus.*`). Test `tests_khung_chuoi.py` |
| Gắn bài giảng | CÓ | bài học trực tuyến |
| Gắn video record | MỘT PHẦN | link theo buổi, học viên không thấy → **V-l**, **E4** |
| Gắn tài liệu | CHƯA | → **Đ2 §60** |
| Gắn bài tập, bài kiểm tra | MỘT PHẦN | khung có mục loại "Bài về nhà" / "Kiểm tra" và ô bài về nhà mỗi buổi (E1); bài tập giao cho lớp chưa trỏ về mục khung; điểm kiểm tra → **V-h** |
| Điều kiện hoàn thành | MỘT PHẦN | % chương trình theo sổ đầu bài (đã dạy 1, một phần 0,5, trọng số) (E1); chưa có ngưỡng "hoàn thành khoá" riêng |

## Dòng 6 — Báo cáo · MỘT PHẦN

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| 6.1 Tổng quan học tập, số học sinh, số lớp | CÓ | "Toàn trung tâm" (`teaching/overview.py`) |
| 6.2 Doanh thu | BỎ | anh chốt 23/09 |
| 6.3 Chấm công GV/TG | CÓ, chỉ xem (V-o) | trang "Chấm công" (Vận hành, quản trị viên + học vụ): theo tháng, từng giảng viên VÀ trợ giảng — buổi đã dạy, tổng giờ, tự điểm danh, điểm danh muộn, tải Excel (`teaching/cham_cong.py`, `teaching/tests_cham_cong.py`). Khoá tháng + chỉnh tay → **Đ2 §59** |
| Điểm danh HS, tiến độ, kết quả theo lớp | CÓ | CSV điểm danh + tiến độ; báo cáo lớp PDF |
| Kết quả theo môn, hoàn thành bài tập (tổng) | MỘT PHẦN | theo khoá / từng bài; chưa báo cáo chéo |
| Hoạt động GV/TG | MỘT PHẦN | buổi dạy / điểm danh theo tháng CÓ (V-o); các hoạt động khác (chấm bài, nhắn tin) chưa gộp |
| HS nghỉ nhiều / chậm tiến độ | CÓ (E1) | nghỉ nhiều CÓ; lớp chậm tiến độ + lớp chưa ghi sổ: ô "Tiến độ chương trình" ở Toàn trung tâm (`overview.py` khoá `chuongTrinh`) |
| Bộ lọc thời gian / lớp / môn / khoá | CÓ (V-k) | tổng quan lọc đợt + ngày; tải chuyên cần lọc khoảng ngày; tải danh sách tài khoản lọc thêm đợt học, môn, ngày cấp (`teaching/exports.py`, `admin_users.build_user_filters`) — `teaching/tests_xuat_excel.py` |
| Xuất Excel / CSV | CÓ (V-k) | hộp "Tải bảng tính" (sổ buổi học của lớp) và "Tải danh sách" (Tài khoản): chọn Excel (.xlsx) hoặc CSV; một bộ ghi `common/bangtinh.ghi_xlsx` (ô chữ không bao giờ thành công thức), trợ giảng không nhận cột liên lạc |

## Dòng 7 — Kế toán · học phí · THAY

Anh chốt 25/09: không sổ tiền, không doanh thu, không vai Kế toán. Thay bằng ô "Tình trạng học phí"
trên hồ sơ (**V-m — đã làm**: ô chọn Đã đóng / Sắp hết / Hết / Bảo lưu ở khối "Tình trạng" của hồ sơ,
học vụ / quản trị viên đặt, có nhật ký, lọc + cột ở Tài khoản, cột "Học phí" trong tệp xuất). Khách phải đồng ý (K2). Dữ liệu "cơ sở tính học phí" (buổi đã học / có mặt / vắng
theo em) đã có cho quản trị viên ở "Cơ sở học phí".

## Dòng 9 — Giáo vụ · lớp học · MỘT PHẦN

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Tạo / cập nhật lớp, thông tin HS, xếp lớp, điều chuyển | CÓ | như dòng 4 |
| Theo dõi tham gia, thống kê tỉ lệ, cảnh báo nghỉ nhiều | CÓ | báo cáo lớp; "Việc hôm nay" (vắng liền ≥ 2 buổi) |
| Điểm danh có mặt / vắng / muộn, cập nhật | CÓ | 4 trạng thái (`teaching/sessions.py:57`) |
| Xem lịch sử điểm danh | CÓ (V-d) | bảng `attendance_history` (§62c) ghi trong cùng giao dịch lưu điểm danh (`teaching/sessions.py::SessionAttendanceView.post`), điền ngược từ nhật ký; `GET /api/teach/sessions/<id>/attendance/history` (`SessionAttendanceHistoryView`). Test `teaching/tests_lich_su_diem_danh.py` (4). Demo: học vụ/giảng viên → Buổi học → Điểm danh một buổi → sửa một em, Lưu → mở "Lịch sử sửa điểm danh" dưới sổ |
| Tiến độ lớp so với khung, cảnh báo chậm | CÓ (E1) | chậm = trễ ≥ 2 buổi HOẶC xong < 80 % phần phải xong (`chuong_trinh/tu_vung.py`); chip đỏ ở Lớp học, ô ở Toàn trung tâm, màn Chương trình lớp |

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

## Dòng 11 — Hỗ trợ lớp học · CÓ (E3, 26/09/2026 — chờ khách xem)

Hộp "Yêu cầu" chung (`backend/yeu_cau/`, bảng §65 `yeu_cau` + `yeu_cau_su_kien`), màn `/yeu-cau`
(học vụ: tab "Yêu cầu" ở khu Vận hành; GV / TG: tab "Yêu cầu" ở khu Giảng dạy; "Việc hôm nay" có ô
"yêu cầu đang mở" + số chờ duyệt).

| Ý trong bảng | Trạng thái | Bằng chứng |
|---|---|---|
| Tiếp nhận yêu cầu hỗ trợ | CÓ | học viên (`/api/yeu-cau`), phụ huynh qua link (dòng 25), trợ giảng / giảng viên báo lên, học vụ tạo thay khi em gọi điện (`dich_vu.tao`) |
| Phân loại học tập / lịch học / kỹ thuật / tài khoản | CÓ | người gửi chọn loại; học vụ "Đổi loại…" (`dich_vu.phan_loai`, sự kiện `phan_loai`) — sang "hỗ trợ tài khoản" thì GV / TG thôi thấy |
| Phân công người xử lý | CÓ | "Giao người xử lý…" (`/api/admin/yeu-cau/<id>/giao`) — chỉ GV / TG của lớp, hoặc học vụ |
| Theo dõi trạng thái | CÓ | Mới → Đang xử lý → Đã xong / Từ chối; mở lại; người gửi rút khi còn "Mới" (`loai.CHUYEN`, một hàm `chuyen_trang_thai`) |
| Ghi nhận kết quả | CÓ | "Đã xong…" kèm kết quả — người gửi đọc được |
| Chuyển cho GV / TG | CÓ | "Chuyển tiếp…" (GV / TG) và "Giao…" (học vụ) — ghi chú giao việc là nội bộ |
| Lưu lịch sử | CÓ | `yeu_cau_su_kien`: mọi trả lời, ghi chú nội bộ, đổi trạng thái, giao, duyệt, việc hệ thống đã làm — ai, lúc nào; nhật ký `request.*` |

Test `yeu_cau/tests_yeu_cau.py` (36, Neon dev 26/09); đột biến `scripts/dot_bien_e3.py`; e2e
`frontend/e2e/yeu-cau.spec.ts` hai khổ. **Demo** (≈3 phút): học viên → "Hỏi & yêu cầu" → chọn "Hỗ trợ
học tập", gõ tóm tắt → Gửi yêu cầu. Học vụ → Vận hành → tab "Yêu cầu" → mở yêu cầu → "Đổi loại…"
sang "Hỗ trợ lịch học" → "Giao người xử lý…" cho trợ giảng lớp → trợ giảng (khu Giảng dạy → Yêu cầu)
tick "Ghi chú nội bộ" ghi một dòng, bỏ tick rồi trả lời → "Đã xong…" kèm kết quả. Học viên mở lại:
thấy trả lời + kết quả, KHÔNG thấy dòng nội bộ.

## Dòng 12 — Quản lý thay đổi học tập · MỘT PHẦN (E3, 26/09/2026)

Xin → duyệt → ghi người duyệt → hệ thống tự làm, trong MỘT giao dịch (`yeu_cau/dich_vu.py::duyet`:
khoá dòng, kiểm trạng thái, thực thi, ghi `nguoi_duyet` + `duyet_luc`; xoá đệm quyền môn + thông báo
SAU commit). Chỉ học vụ / quản trị viên duyệt (`IsAdminOrAcademic` + kiểm lại ở dịch vụ); duyệt hai
lần chỉ làm một lần (409). Xem trước "Hệ thống sẽ…" trước khi bấm (GET, không ghi).

| Loại | Duyệt xong hệ thống làm gì | Qua hàm của miền lớp học |
|---|---|---|
| Chuyển lớp, chuyển môn | CÓ — đóng lượt lớp cũ (`transferred`), mở lượt lớp mới, nối hai lượt; giữ trần lớp gia sư 3 em | `teaching/chuyen_lop.py::ChuyenLopView._chuyen` |
| Bảo lưu | CÓ — rời lớp lý do "bảo lưu" + `reserve_until` (§65c); em mất quyền vào môn | `teaching/roi_lop.py::roi_lop` |
| Huỷ khoá | CÓ — rời lớp lý do "bỏ giữa chừng" | `roi_lop` |
| Học lại | CÓ — lượt học mới ở lớp cũ (giữ trần gia sư) | `AdminClassMembersView._ghi_thanh_vien` |
| Chuyển lịch, học bù, nghỉ học | MỘT PHẦN — duyệt ghi QUYẾT ĐỊNH + người duyệt; học vụ tự làm trên màn Buổi học (buổi bù / đổi lịch / "có phép") rồi bấm "Đã xong…" | — (tự động hoá: việc sót, xem báo cáo E3) |

**Demo**: học viên → "Hỏi & yêu cầu" → "Xin chuyển lớp", gõ lớp mong muốn → Gửi. Học vụ → Yêu cầu →
mở → "Duyệt…" → chọn lớp tới → đọc "Hệ thống sẽ: Chuyển … sang lớp …" → "Duyệt và thực hiện". Mở
Lớp học: em đã ở lớp mới; lịch sử yêu cầu có dòng "Duyệt yêu cầu" + "Hệ thống đã làm"; học viên
nhận chuông. Bấm duyệt lần hai → báo đã duyệt, không chuyển thêm.

## Dòng 14 — Giáo viên · lớp + điểm danh · gần đủ

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Danh sách lớp được phân công | CÓ | "Việc hôm nay", khu Giảng dạy |
| Cập nhật mục tiêu, nguyện vọng HS | CÓ | tờ báo cáo từng em (`teaching/ho_so.py`) |
| Điểm danh có mặt / vắng / muộn / xin phép, cập nhật | CÓ | màn Buổi học |
| Người được phép sửa | CÓ | GV lớp mình, TG lớp được gán, học vụ, quản trị viên |
| Lưu lịch sử chỉnh sửa | CÓ (V-d) | như dòng 9: mỗi lần ĐỔI một dòng (ai, từ gì → gì, lúc nào); lưu lại y hệt ghi 0 dòng. Demo: giảng viên/trợ giảng → Buổi học → Điểm danh → "Lịch sử sửa điểm danh" |
| Thống kê tỉ lệ, cảnh báo nghỉ nhiều | CÓ | |

## Dòng 15 — Giáo viên · chương trình + tiến độ · MỘT PHẦN

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| Soạn / chuẩn bị nội dung buổi | CÓ (E1) | buổi học gắn buổi khung (tự động theo ngày, gắn tay được); sổ đầu bài hiện nội dung kế hoạch + bài về nhà |
| Đính kèm tài liệu | CHƯA | **Đ2 §60** |
| Nội dung đã / chưa hoàn thành | CÓ (E1) | **Sổ đầu bài** `/giang-day/so-dau-bai/<buổi>`: từng nội dung đã dạy / một phần / chưa dạy + ghi chú |
| Ghi chú sau buổi | CÓ (`class_sessions.note`) | — |
| Tiến độ thực tế vs kế hoạch, đề xuất điều chỉnh | MỘT PHẦN (E1) | tiến độ vs kế hoạch CÓ (màn Chương trình lớp); ô "Đề xuất" trong sổ là chữ tự do — biến thành yêu cầu ở **E3** |

## Dòng 16 — Giáo viên · quản lý buổi học · gần đủ

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| Buổi đã diễn ra, tình hình lớp | CÓ (trạng thái `done`, điểm danh, `note`) | — |
| Nội dung thực tế / chưa hoàn thành, mức tiếp thu | CÓ (E1) | sổ đầu bài: từng nội dung + mức tiếp thu 1–5 |
| Đề xuất HS cần hỗ trợ | CÓ (E1) | sổ đầu bài: đánh dấu em cần hỗ trợ + ghi chú (`session_support`, nội bộ); cờ theo em **V-f** |
| Đề xuất học bù / điều chỉnh tiến độ | CÓ (E1 + E3) | ô "Đề xuất" trong sổ đầu bài + nút "Gửi đề xuất cho học vụ" → một yêu cầu "Báo lên" gắn buổi (`components/YeuCauDeXuat.tsx`); học vụ trả lời / tạo buổi bù ở hộp Yêu cầu. Demo: sổ đầu bài một buổi → gõ Đề xuất → "Gửi đề xuất cho học vụ" → "Xem yêu cầu →" |

## Dòng 17 — Giáo viên · giao bài · MỘT PHẦN (sửa 26/09: trước ghi "CÓ" là quá tay)

Tạo, hạn lúc TẠO, xoá / đóng / mở lại, danh sách, xem bài nộp, chấm, nhập điểm, nhận xét, trả bài, ai chưa nộp:
CÓ (`teaching/assignments.py`). **"Chỉnh sửa bài tập" thì CHƯA**: sau khi đã giao, màn của giảng viên chỉ gửi
được hai thứ — đổi người nhận và đóng/mở bài (`giang-day/bai-tap/[classId]/AssignmentsClient.tsx:176, 238` —
đo 26/09, không có lời gọi nào mang `title`/`dueAt`/thang điểm). Backend `assignments.py:530` nhận sửa đầy đủ
nhưng KHÔNG màn nào gọi tới, nên gõ nhầm hạn nộp là phải xoá bài giao lại. Việc đóng dòng này: thêm ô sửa bài
đã giao trên màn giảng viên. **Thiết lập đối tượng nhận bài** (một nhóm em): CÓ (V-e) —
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

## Dòng 20 — Trợ giảng · nhắn tin / nhắc · MỘT PHẦN

Danh sách lớp + thông tin HS: CÓ (cắt liên lạc — có chủ ý). Chat thời gian thực: không làm (anh chốt
25/09 — Zalo vẫn để chat). Nhắc học bài / làm bài / vào lớp → **E2**.

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Nhận tin, lịch sử trao đổi | CÓ (E3) | câu hỏi học viên gửi lớp → GV + TG lớp nhận chuông; trả lời + lịch sử ở `/yeu-cau/<id>` |
| Ghi nhận HS không phản hồi | CÓ (E3) | "Tạo yêu cầu" → "Báo lên", chọn lớp + em, tick "Em không phản hồi" (`du_lieu.khong_phan_hoi`, chip trên hộp) |
| Chuyển vấn đề cho GV / giáo vụ | CÓ (E3) | "Báo lên" tới GV lớp + học vụ; "Chuyển tiếp…" một yêu cầu đang cầm |
| TG CHỦ ĐỘNG nhắn một HS | CHƯA — **cần anh quyết** | hộp hiện chỉ cho HS gửi trước; xem câu hỏi trong `docs/agent/BAO_CAO_E3.md` |

SĐT phụ huynh để lại trong yêu cầu ẩn với trợ giảng (test `test_tro_giang_khong_thay_sdt_phu_huynh`).
**Demo**: trợ giảng → khu Giảng dạy → Yêu cầu → "Tạo yêu cầu" → loại "Báo lên", lớp, em, tick "Em
không phản hồi" → Gửi. Học vụ thấy yêu cầu với chip "Em không phản hồi".

## Dòng 21 — Trợ giảng · theo dõi · MỘT PHẦN

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| Điểm danh, theo dõi bài tập, tiến độ | CÓ | — |
| Hỗ trợ giải đáp | CÓ (E3) | câu hỏi của em tới hộp Yêu cầu của GV + TG lớp; TG trả lời, chuyển tiếp hoặc báo lên. Demo: như dòng 32 rồi đăng nhập trợ giảng lớp → Yêu cầu |
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

## Dòng 25 — Phụ huynh · gửi yêu cầu · CÓ qua link (E3, 26/09/2026 — chờ khách xem)

Phụ huynh KHÔNG có tài khoản (anh chốt 25/09): cuối tờ báo cáo `/bc/<chìa>` có khối "Gửi yêu cầu cho
trung tâm" + "Yêu cầu đã gửi qua đường dẫn này" kèm trạng thái, kết quả và trả lời (không có ghi chú
nội bộ). Máy chủ lấy em + lớp từ chìa, không từ biểu mẫu; chìa lạ / hết hạn / thu hồi → cùng một câu
404; tối đa 5 yêu cầu đang chờ mỗi link; giới hạn 20 lượt gửi / giờ / máy (`PhuHuynhYeuCauView`).
Liên hệ giáo vụ = loại hỗ trợ (tới học vụ); liên hệ GV / TG = "Hỏi giảng viên" (tới GV + TG lớp).
Theo dõi + nhận phản hồi: mở lại chính link. Chưa có: phụ huynh trả lời tiếp trong một yêu cầu (gửi
yêu cầu mới), link "sống" §66 (sau buổi xem).

**Demo**: giảng viên → Báo cáo phụ huynh → tờ một em → cấp đường dẫn → mở đường dẫn ở trình duyệt
khác → cuối trang chọn "Hỗ trợ lịch học", gõ tóm tắt, số điện thoại → Gửi yêu cầu. Học vụ → Yêu cầu
thấy "Phụ huynh gửi"; trả lời → phụ huynh tải lại link thấy trả lời.

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
| % hoàn thành chương trình, bài / chuyên đề đã / chưa, tiến độ theo môn | CÓ (E1) | "Lớp của tôi": "Đã học X% chương trình" — chỉ buổi em có mặt / muộn, buổi bù tính cho buổi gốc; tờ phụ huynh cùng dòng |
| So sánh thực tế với kế hoạch | CÓ (E1) | cùng dòng: "(kế hoạch tới nay: Y%)" |

## Dòng 29 — Học sinh · record · CHƯA → V-l, E4

Danh sách record theo buổi, tìm kiếm, đã xem / chưa xem (**V-l**), % đã xem cho TG (**E4** — thử trên
tài khoản Zoom thật trước: Zoom chỉ trả tên người xem khi người xem đăng nhập Zoom).

## Dòng 30 — Học sinh · học liệu · CHƯA → Đ2 §60

## Dòng 31 — Học sinh · bài tập · CÓ

Nhận bài, làm và nộp, xem kết quả + nhận xét: CÓ (`/bai-tap`, chuông). Nộp chữ; nộp tệp → **Đ2 §60**.

## Dòng 32 — Học sinh · trao đổi · CÓ (E3, 26/09/2026 — chờ khách xem)

Mục "Hỏi & yêu cầu" trên thanh học viên (`/yeu-cau`): "Hỏi giảng viên" (tới GV + TG của lớp em —
GV lớp khác không thấy, test `test_hoi_dap_toi_gv_lop_minh_khong_toi_gv_lop_khac`), "Hỗ trợ học tập
/ lịch / kỹ thuật / tài khoản" (tới học vụ), báo lỗi bản ghi một buổi, xin thay đổi (dòng 12). Em chỉ
thấy yêu cầu mình gửi, không thấy ghi chú nội bộ; trả lời tiếp được khi yêu cầu còn mở; rút được khi
còn "Mới". Diễn đàn và trợ lý AI giữ nguyên.

**Demo**: học viên → "Hỏi & yêu cầu" → "Hỏi giảng viên" → Gửi. Trợ giảng lớp → Yêu cầu → trả lời.
Học viên mở lại: thấy trả lời, gõ tiếp một câu.

## * Phân hệ thông báo chung · MỘT PHẦN → E2

Có: chuông + email cho đổi / huỷ lịch, bài tập mới, bài đã chấm. Thiếu: lịch mới, học bù, hạn nộp,
nghỉ học, cảnh báo tiến độ, thông báo trung tâm; gửi theo lớp / môn / nhóm / cá nhân; chưa đọc; lịch sử
đầy đủ (nay 30 dòng gần nhất). Nền cho gửi tin cậy: hộp thư đi (outbox) — hiện thư gửi trên luồng rời,
lỗi chỉ ghi log.
