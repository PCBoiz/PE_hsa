# SOÁT LẠI BẢNG NGHIỆM THU — đo trên màn thật, 26/09/2026 (agent SOÁT2)

Nền đo: `erp` @ `7e6c4e9` + phần §60 học liệu còn trong thư mục làm việc của lead.
Bản dev chính (Django 9000 · Next 3100), CSDL Neon dev. Năm vai, thẻ cấp bằng
`scripts/cap_the.py`: quản trị (id 7) · học vụ (35743) · giảng viên (11) ·
trợ giảng (35744) · học viên (35695 và 9). Lớp đo: 7322 (lớp mẫu, 28 em, 25 buổi)
và 1 (3 em, có bản ghi Zoom).

Bộ đo: `scripts/do_man_hang_loat.mjs` — **73 lượt mở màn trong 6 phiên trình duyệt**,
không phiên nào để lại Chromium mồ côi (`don_may.ps1` sau mỗi lượt: mục "MỒ CÔI (sạch)").
Ba tệp danh sách màn: `scripts/man/nghiem_thu.json` (34 màn, đã mở rộng từ 9),
`scripts/man/nghiem_thu_sau.json` (21 màn có bấm nút), `scripts/man/nghiem_thu_e1.json` +
`scripts/man/nghiem_thu_con_nghi.json` (các màn còn nghi). Màn `/bc/<chìa>` đo bằng danh sách
để ngoài repo (trong `%TEMP%`) vì chìa phụ huynh là bí mật.

KHÔNG soát: **dòng 20** (agent GD đang dựng màn) và **dòng 27** (đã đóng 12/12).

---

## Phát hiện lớn nhất, nói trước

**Toàn bộ chuỗi E1 (khung chương trình) không có MỘT dòng dữ liệu nào trong CSDL.**
Công cụ của chính dự án nói ra điều đó:

```
python manage.py du_lieu_mau
  khung chương trình mẫu       0
  sổ đầu bài                   0
```

`syllabus_versions` = 0 · `syllabus_sessions` = 0 · `syllabus_items` = 0 · `session_logs` = 0.
`teaching/du_lieu_mau.py:428` CÓ gọi `dung_khung_mau(...)`, nhưng bộ dữ liệu mẫu đang
nằm trong CSDL được dựng TRƯỚC khi E1 về, và chưa ai chạy `du_lieu_mau --lam-moi`.

Hậu quả đo được: mở `/giang-day/chuong-trinh/7322` bằng thẻ giảng viên thì màn chỉ có
**69 từ** — "Lớp chưa nhận khung chương trình". Không phải màn hỏng; là màn đúng của
một lớp chưa có khung. Nhưng nếu khách bấm vào đúng nút "Chương trình" ở màn Lớp học
trong buổi nghiệm thu, đó là thứ họ thấy.

Để tách "tính năng thiếu" khỏi "dữ liệu thiếu", tôi đã dựng một khung thật qua ĐÚNG
các cửa API (không ghi thẳng bảng): `POST /api/admin/courses/hsa_quantitative/syllabus`
→ 3 buổi (`durationMinutes`, `homework`) → mỗi buổi một mục + một học liệu →
`PUT /api/admin/syllabus/468 {"status":"xuat_ban"}` →
`PUT /api/admin/classes/1/chuong-trinh {"versionId":468}` → ghi 2 sổ đầu bài
(`PUT /api/teach/sessions/1542|1543/so-dau-bai`).

Đo lại ngay sau đó, cùng thẻ giảng viên, cùng bộ đo:
`/giang-day/chuong-trinh/1` → **812 từ**, có các chip "1 đã dạy", "0 đã dạy, 1 một phần",
"Chưa ghi — ghi ngay". Toàn trung tâm hiện ô "Lớp chậm tiến độ 1". Thẻ lớp của học viên
hiện "Buổi 3 — nội dung thử" và câu % chương trình kèm kế hoạch.

**Kết luận: E1 CHẠY. Thứ thiếu là một lượt `du_lieu_mau --lam-moi`, không phải mã.**
Khung thử này còn nằm ở lớp 1 (lớp KHÔNG phải lớp mẫu, `is_demo=false`) — tên
"SOAT2 — khung thử 3 buổi", xoá được bất cứ lúc nào.

Cùng họ với nó: **không có bài nào `kind='kiem_tra'`** trong CSDL, nên nút "Nhập điểm"
(V-h) không bao giờ hiện. Tôi tạo một bài kiểm tra thử ở lớp 7322 → nút "Nhập điểm"
hiện ngay, bảng chấm cả lớp có cột "Vắng" và ô điểm (376 từ) → rồi **đã xoá** bài ấy
(`DELETE /api/teach/assignments/6072` → `{"ok":true}`, đếm lại còn 0 bài kiểm tra).
27 chuông "bài mới" đã bắn ra trong lúc đo, nhưng cả 27 địa chỉ đều là `@example.com`
(đếm theo tên miền trên `class_members` của lớp 7322) — không thư nào ra ngoài.

---

## Bảng 30 dòng

| STT | Tên dòng | Bảng đang ghi | Tôi đo được | Bằng chứng |
|---|---|---|---|---|
| 1 | QTV · tài khoản | CÓ (khách nghiệm thu) | **CÓ** | `/login` (không thẻ), 78 từ: ô nhận email/tên/SĐT · nút `aria-label="Hiện mật khẩu"` · "Ghi nhớ đăng nhập trên máy này" · "Đặt lại qua email". 4/4 ý đo được |
| 2 | QTV · người dùng | CÓ (khách nghiệm thu) | **CÓ** | `/quan-tri/tai-khoan` vai quản trị, 1.400 từ, 6/6: "Mở ô nhập" (dán hàng loạt) · "Tải danh sách" · cột Trạng thái · Khoá/Mở khoá · lọc Vai |
| 3 | QTV · tìm kiếm + hồ sơ | CÓ (chờ e2e) | **CÓ** | `/quan-tri/tai-khoan/35695` vai học vụ, 679 từ, 7/7: Tỉnh/Thành phố · phụ huynh · người tư vấn/nguồn · mục tiêu + nguyện vọng · Tình trạng học · Đã đóng/Sắp hết/Bảo lưu · lớp đang học |
| 4 | QTV · lớp học | MỘT PHẦN | **MỘT PHẦN** (gần đủ hơn bảng ghi) | `/quan-tri/lop-hoc` vai quản trị: sau khi bấm "Lọc thêm" → bộ lọc có **Tạm dừng** (362 từ); sau khi bấm "Học viên" → "Học viên của lớp" · "Nhập học viên từ tệp mẫu" · **"Lịch sử thay đổi của lớp"** · gán Trợ giảng (537 từ). Chip tiến độ chương trình hiện sau khi lớp có khung. Còn thiếu thật: phân công học vụ riêng cho lớp, mốc "Đăng ký" (E5) |
| 5 | QTV · khoá + chương trình | MỘT PHẦN | **MỘT PHẦN — màn đủ, DỮ LIỆU rỗng** | `/giao-trinh/khung-chuong-trinh` trước khi tôi tạo khung: 90 từ, "Môn này chưa có khung nào" (ảnh). Sau khi tạo: chọn môn Toán → bấm "Xem" → có Buổi · Trọng số · Bài về nhà · **"Tài liệu thử.pdf"** · "Tạo bản mới" (222 từ). Thiếu thật: gắn tài liệu cho lớp (Đ2 §60), bài tập lớp chưa trỏ về mục khung |
| 6 | QTV · báo cáo | MỘT PHẦN | **MỘT PHẦN** | `/quan-tri/tong-quan` 687 từ: "6 buổi đã dạy chưa ai điểm danh" · "1 học viên rời lớp chưa ghi lý do" · "2 lớp chưa phân công giảng viên" · "1 học viên ≥14 ngày không vào" · "4 buổi điểm danh muộn" · **"Lớp chậm tiến độ 1"**. `/quan-tri/cham-cong` 197 từ, có Tháng · Giảng viên · Trợ giảng · giờ · Tải Excel. Nút xuất tệp KHÔNG ở màn Tổng quan (nằm ở Tài khoản và Buổi học) |
| 7 | Kế toán · học phí | THAY (V-m xong) | **THAY — đo được** | `/quan-tri/co-so-hoc-phi` vai quản trị, 1.212 từ, có buổi · có mặt/vắng · theo em. KHÔNG có nút tải ở màn này (bảng cũng không hứa) |
| 8 | Giáo vụ · tài khoản | CÓ | **CÓ** | Cùng `/login`; thẻ học vụ 35743 mở được `/quan-tri/tai-khoan`, `/quan-tri/lop-hoc`, `/yeu-cau`, `/giang-day/*` — 982–1.159 từ mỗi màn |
| 9 | Giáo vụ · lớp học | MỘT PHẦN | **CÓ** ⬆ | `/giang-day/buoi-hoc/7322` vai **học vụ**, bấm "Điểm danh" một buổi → 1.159 từ, 6/6: Có mặt · Vắng · Đi muộn · Xin phép · **"Lịch sử sửa điểm danh"** · Lưu. Chậm tiến độ đo được sau khi lớp có khung |
| 10 | Giáo vụ · lịch học | gần đủ | **gần đủ** | `/giang-day/lich` vai học vụ, 272 từ: Tuần trước/này/sau · lọc theo lớp · theo giảng viên · **"Thêm lịch dạy vào điện thoại"** · "Link phòng học". "Tạo buổi bù" có ở màn Buổi học. Cảnh báo trùng KHÔNG đo được (dữ liệu hiện không có lịch trùng). Đổi GV một buổi vẫn CHƯA (Đ2 §58) |
| 11 | Giáo vụ · hỗ trợ lớp | CÓ | **CÓ** | `/yeu-cau` vai học vụ 495 từ (lọc trạng thái, loại, người gửi, "Tạo yêu cầu"); `/yeu-cau/176` 273 từ, nút: "Đã xong…" · "Giao người xử lý…" · "Đổi loại…" · "Từ chối…" · "Gửi trả lời" |
| 12 | Giáo vụ · thay đổi học tập | MỘT PHẦN | **MỘT PHẦN** (đúng như bảng) | `/yeu-cau/177` (xin chuyển lớp) vai học vụ: "Duyệt…" · "Nhận xử lý" · "Giao người xử lý…" · "Từ chối…" · **"Duyệt và thực hiện"**. Xem trước "Hệ thống sẽ…" chỉ hiện sau khi chọn lớp tới — tôi chưa chọn nên chưa đo được câu ấy |
| 13 | Giáo viên · tài khoản | CÓ | **CÓ** | Thẻ giảng viên 11 mở được `/giang-day` (1.045 từ), Buổi học, Bài tập, Báo cáo phụ huynh, Chương trình |
| 14 | Giáo viên · lớp + điểm danh | CÓ | **CÓ** | `/giang-day/buoi-hoc/7322` vai giảng viên, bấm "Điểm danh" → 1.158 từ, 6/6 y như dòng 9. "Việc hôm nay" 1.045 từ có chưa điểm danh · vắng liền · cần hỗ trợ |
| 15 | Giáo viên · chương trình + tiến độ | MỘT PHẦN | **MỘT PHẦN** (đúng, nhưng vì dữ liệu chứ không vì mã) | Sổ đầu bài `/giang-day/so-dau-bai/1542` sau khi lớp 1 có khung: 206 từ, có Đã dạy/Dạy một phần/Chưa dạy · mức tiếp thu · Đề xuất · **"Gửi đề xuất cho học vụ"** · "Lưu sổ đầu bài" · em cần hỗ trợ. Chương trình lớp 812 từ (xem phần đầu). **Không có ô đính kèm tài liệu** → thiếu thật |
| 16 | Giáo viên · quản lý buổi học | CÓ | **CÓ** | Cùng hai màn trên; `/giang-day/buoi-hoc/1` có "Tạo buổi học" · "Sinh lịch cả kỳ" · "Tạo buổi bù" · "Sổ đầu bài" · "Tải bảng tính" · "Báo cáo lớp (PDF)" |
| 17 | Giáo viên · giao bài | CÓ | **CÓ** | `/giang-day/bai-tap/7322` vai giảng viên: "Giao bài mới" · **"Sửa bài"** · "Đổi người nhận" · "Đóng bài"/"Mở nhận bài" · "Xoá" · số đã nộp. Bảng chấm `/giang-day/bai-tap/7322/3358` 1.294 từ. Sau khi tạo một bài `kind='kiem_tra'`: nút **"Nhập điểm"** hiện, bảng chấm có cột "Vắng" (376 từ) |
| 18 | Giáo viên · theo dõi học sinh | CÓ | **CÓ** | `/giang-day/bao-cao/7322/35695` 569 từ, 6/6: Nhận xét · đánh dấu cần hỗ trợ · **Đề xuất hướng học** · lịch sử điểm danh · bài tập + điểm · "có tiến bộ". Nút: "In / Lưu PDF" · "Tạo đường dẫn gửi phụ huynh" · "Chép đường dẫn" · "Thu hồi" |
| 19 | Trợ giảng · tài khoản | CÓ | **CÓ** | `/giang-day` vai trợ giảng 198 từ: "Mở hộp yêu cầu →" · "Điểm danh →" · "Chấm →" — đúng phạm vi lớp mình |
| 21 | Trợ giảng · theo dõi | MỘT PHẦN | **CÓ** ⬆ | "Việc hôm nay" vai TG: 4/4 vắng liền · cần chú ý · "Báo cần hỗ trợ" · chưa điểm danh. `/giang-day/bai-tap/7322` vai TG: thấy bài, thấy ai chưa nộp, "Chấm bài", "Đóng bài", "Mở nhận bài". **Theo dõi việc xem record: đã CÓ** — xem dòng 22 |
| 22 | Trợ giảng · record Zoom | CÓ | **CÓ — và ba ý bảng ghi CHƯA thì đã có** ⬆ | `/giang-day/buoi-hoc/1` (lớp có bản ghi), chờ 9 giây cho khối nạp xong: khối **"Bản ghi buổi học"** hiện "1/2 em đã mở" · `<summary>` "Chưa mở: 1" · nút **"Nhắc em chưa mở"** · dòng **"Chưa có bản ghi: …"**. API kiểm chứng: `GET /api/teach/classes/1/ban-ghi` trả `daMo/chuaMo/dsChuaMo/thieuBanGhi`. Bấm "Sửa" một buổi → ô Bản ghi · Zoom · Phòng · Trực tuyến (365 từ) |
| 23 | Phụ huynh · tài khoản | THAY (link riêng) | **THAY — đo được** | `/bc/<chìa 43 ký tự>` mở được ở ngữ cảnh KHÔNG có thẻ, 643 từ. Chìa cắt cụt → "Không mở được báo cáo này. Đường dẫn này không còn dùng được." (một câu chung cho sai/hết hạn/thu hồi) |
| 24 | Phụ huynh · xem | MỘT PHẦN | **MỘT PHẦN — nhưng cao hơn bảng ghi** ⬆ | Trên chính tờ: chuyên cần · bài tập · nhận xét giảng viên · lớp · giảng viên · **lịch buổi** · tiến độ/% · "có tiến bộ" · bản đồ điểm yếu ("Giải tích 36/100…") · nút "In / Lưu PDF". Thiếu: **trợ giảng** không có trên tờ; khối "Bài kiểm tra" rỗng vì không có bài `kiem_tra` nào |
| 25 | Phụ huynh · gửi yêu cầu | CÓ | **CÓ** | Cuối tờ: "Gửi yêu cầu cho trung tâm" · "Yêu cầu đã gửi qua đường dẫn này" · 5 yêu cầu kèm chip trạng thái "Mới"/"Hỗ trợ lịch học" · trần 5 yêu cầu chờ được nói bằng tiếng người: "Anh / chị đang có 5 yêu cầu chờ trung tâm xử lý…" (ảnh) |
| 26 | Học sinh · tài khoản + tự đăng ký | MỘT PHẦN | **MỘT PHẦN** (đúng) | `/dashboard` vai học viên 496 từ: thẻ lớp · chuông "Thông báo" · menu tên. `/login` KHÔNG có bất kỳ lối đăng ký nào → tự đăng ký vẫn CHƯA (E5) |
| 28 | Học sinh · chương trình + lộ trình | MỘT PHẦN | **CÓ** ⬆ (khi lớp có khung) | `/dashboard` vai học viên lớp 1 (lớp đã nhận khung): 574 từ, có "Buổi 3 — nội dung thử", câu % chương trình kèm kế hoạch, "Điểm danh từng buổi" mở ra được. Lớp 7322 chưa có khung nên câu tiến độ không hiện |
| 29 | Học sinh · record | CÓ | **CÓ** | `/dashboard` vai học viên lớp 1: hai nút **"24/09 ✓"** và **"22/09 ✓"** — dấu ✓ là đã mở, ghi vào `recording_views` |
| 30 | Học sinh · học liệu | CHƯA | **KHÔNG ĐO ĐƯỢC** | Bảng `hoc_lieu` có (0 dòng). `POST /api/teach/classes/7322/hoc-lieu` trả **404** trên Django 9000 vì máy chủ ấy chạy `--noreload` và được bật trước khi §60 về; tôi không có quyền nạp lại máy chủ của lead. Thẻ lớp học viên 496 từ, không có chữ "Tài liệu" — nhưng đó cũng đúng với 0 dòng dữ liệu, nên chưa kết luận được gì |
| 31 | Học sinh · bài tập | CÓ (nộp chữ) | **CÓ (nộp chữ)** | `/bai-tap` vai học viên 431 từ: Hạn · "Nộp bài" · Điểm · Nhận xét. **Không có ô chọn tệp nào** → nộp tệp vẫn CHƯA (Đ2 §60) |
| 32 | Học sinh · trao đổi | CÓ | **CÓ** | `/yeu-cau` vai học viên 560 từ: "Gửi yêu cầu" · "Hỏi giảng viên" · "Hỗ trợ học tập/kỹ thuật" · yêu cầu của chính em kèm trạng thái và "Kết quả: …". KHÔNG thấy ghi chú nội bộ nào |

---

## NÂNG HẠNG ĐƯỢC NGAY

Sáu dòng đang ghi thấp hơn thực tế. Bằng chứng đủ để sửa thẳng vào bảng.

1. **Dòng 22 · Trợ giảng · record Zoom: MỘT PHẦN → CÓ** (trong bảng chi tiết còn ghi ba ý là CHƯA).
   Ba ý ấy đều đã dựng và đo được trên `/giang-day/buoi-hoc/1`:
   - "Đã upload / chưa upload" — dòng "Chưa có bản ghi: 17/09 · 15/09" (`BanGhiLop.tsx:135`)
   - "HS đã xem / chưa xem" — "1/2 em đã mở" + `<summary>` "Chưa mở: 1" liệt kê tên
   - "Nhắc HS chưa xem" — nút "Nhắc em chưa mở", gọi API và đổi thành "Đã nhắc N em"
   Nguồn dữ liệu: `GET /api/teach/classes/1/ban-ghi`. **Đây là V-l, bảng vẫn ghi là việc còn phải làm.**

2. **Dòng 21 · Trợ giảng · theo dõi: MỘT PHẦN → CÓ.**
   Ô "Theo dõi việc xem record | CHƯA | V-l" đã hết đúng — xem điểm 1. Ba ý còn lại
   (điểm danh, bài tập, tiến độ · hỗ trợ giải đáp · dấu hiệu bỏ học) đo đủ trên "Việc hôm nay"
   vai trợ giảng và `/giang-day/bai-tap/7322` vai trợ giảng.

3. **Dòng 9 · Giáo vụ · lớp học: MỘT PHẦN → CÓ.**
   Cả năm ô của dòng này đo được bằng **thẻ học vụ**, không mượn thẻ quản trị:
   sổ điểm danh bốn trạng thái + "Lịch sử sửa điểm danh" (1.159 từ), tạo/sửa lớp,
   chuyên cần, cảnh báo chậm tiến độ. Việc đóng ghi "V-d, E1" — cả hai đã về.

4. **Dòng 28 · Học sinh · chương trình + lộ trình: MỘT PHẦN → CÓ.**
   Bốn ô đều đo được trên `/dashboard` của một em thuộc lớp ĐÃ nhận khung: đếm buổi,
   "Điểm danh từng buổi" mở ra được, "% chương trình", "(kế hoạch tới nay: …)".
   Việc đóng ghi "E1, V-d" — cả hai đã về. Cái còn thiếu là **dữ liệu**, không phải mã.

5. **Dòng 24 · Phụ huynh · xem: nâng hai ô.**
   Bảng ghi "Lịch học, lớp, môn, GV, TG | MỘT PHẦN | tờ báo cáo có lớp + GV; **không lịch**".
   Đo được: tờ CÓ lịch buổi. Ô "Tiến độ học tập" cũng đo được. Còn đúng một thứ thiếu
   thật: **trợ giảng không xuất hiện trên tờ**.

6. **Dòng 17 · Giáo viên · giao bài: bỏ câu "Chỉnh sửa bài tập thì CHƯA" ở mục chi tiết.**
   Bảng tóm tắt đã ghi CÓ (Sửa bài 26/09) nhưng **mục "Dòng 17" bên dưới vẫn còn nguyên
   đoạn dài giải thích rằng sửa bài CHƯA có**. Đo 26/09: nút "Sửa bài" có trên
   `/giang-day/bai-tap/7322`, mở ra biểu mẫu có Tiêu đề · Hạn · thang điểm · Lưu
   (`AssignmentsClient.tsx:423`). Hai chỗ trong cùng một tệp đang nói ngược nhau —
   khách đọc mục chi tiết sẽ tin cái sai.

**Cùng loại với điểm 6 — bốn mục chi tiết đang lạc hậu so với bảng tóm tắt:**
- "## Dòng 14" ghi "gần đủ", tóm tắt ghi CÓ.
- "## Dòng 17" ghi "MỘT PHẦN (sửa 26/09: trước ghi CÓ là quá tay)", tóm tắt ghi CÓ.
- "## Dòng 27" ghi MỘT PHẦN với bốn ô, tóm tắt ghi **CÓ** và dòng 27 đã đóng hôm nay.
- "## Dòng 29" ghi "CHƯA → V-l, E4", tóm tắt ghi CÓ và tôi đo được "24/09 ✓ 22/09 ✓".
Đây là loại sai nguy hiểm thứ hai sau hạ hạng: một tài liệu tự mâu thuẫn thì khách
không biết tin nửa nào.

---

## HẠ HẠNG

**Không có dòng nào đang ghi CÓ mà màn thật không chạy.** Tôi đã đi hết 30 dòng và
không tìm được một dòng nào phải hạ. Nhưng có ba cảnh báo phải nói ra, vì chúng biến
một dòng CÓ thành một buổi nghiệm thu hỏng:

1. **Dòng 5 · 15 · 16 · và ô "Tiến độ chương trình" của dòng 4/6/9 — đúng nhưng
   KHÔNG DEMO ĐƯỢC trên dữ liệu hiện tại.** `syllabus_versions` = 0, `session_logs` = 0.
   Bấm "Chương trình" ở màn Lớp học trong buổi nghiệm thu → "Lớp chưa nhận khung chương
   trình". Mở "Khung chương trình" → "Môn này chưa có khung nào".
   Sửa: `cd backend && python manage.py du_lieu_mau --lam-moi` trước buổi trình diễn —
   chính lệnh mà `du_lieu_mau.py` đã cảnh báo ("Dữ liệu đã cũ — chạy --lam-moi trước
   buổi trình diễn"), chỉ là chưa ai chạy.

2. **Dòng 4 ô "Điểm kiểm tra, điểm thi thử" và dòng 17 ô "Bài kiểm tra ngoại tuyến"
   (V-h) — cũng không demo được**: không có bài nào `kind='kiem_tra'`, nên nút
   "Nhập điểm" không tồn tại trên màn. Tôi đã chứng minh nó hiện ngay khi có một bài
   như vậy, rồi xoá bài đi.

3. **Dòng 30 — bảng ghi CHƯA, nhưng nay đã khác và tôi KHÔNG đo được.** §60 backend
   đã về trong thư mục làm việc của lead; Django 9000 chạy `--noreload` từ trước nên
   tuyến `/api/teach/classes/<id>/hoc-lieu` vẫn 404. Đừng nâng dòng 30 dựa trên bản
   đo này — phải nạp lại backend rồi đo lại.

---

## CÒN THIẾU THẬT

| Dòng | Thiếu đúng cái gì | Còn bao nhiêu việc |
|---|---|---|
| 4 | Phân công học vụ cho TỪNG lớp (nay học vụ thấy mọi lớp) | một cột + một ô chọn ở biểu mẫu Sửa lớp, cộng một cổng quyền — nửa ngày |
| 4 · 26 | Mốc "Đăng ký" trên dòng thời gian, tự đăng ký + email xác nhận | **E5**, một tuyến mới + hàng chờ "Đăng ký mới" cho giáo vụ — một màn + một tuyến |
| 5 · 15 · 30 | Đính kèm / gắn tài liệu cho buổi và cho lớp | backend §60 ĐÃ xong (lead, 27 test xanh); còn **màn cho giảng viên** — một màn |
| 5 | Bài tập giao cho lớp chưa trỏ về mục khung; ngưỡng "hoàn thành khoá" | một khoá ngoại + một ô chọn khi giao bài; ngưỡng là một quyết định của anh Sơn trước, rồi một ô cấu hình |
| 6 | Hoạt động GV/TG gộp (chấm bài, nhắn tin); báo cáo chéo môn × lớp | một màn tổng hợp — chưa có tuyến nào; ước một ngày |
| 10 | Đổi GV / TG cho MỘT buổi | **Đ2 §58** — một cột `class_sessions.teacher_id` + cổng quyền + màn; nửa ngày |
| 10 | Tạo / quản lý Zoom (nay chỉ dán link) | **E4** — **chờ khoá Zoom của anh Sơn**, không làm trước được |
| 12 | Chuyển lịch / học bù / nghỉ học: duyệt xong hệ thống TỰ làm (nay học vụ tự thao tác rồi bấm "Đã xong") | ba nhánh trong `yeu_cau/dich_vu.py::duyet`, mỗi nhánh gọi một hàm dịch vụ đã có — một ngày |
| 22 | Bản ghi TỰ vào buổi từ Zoom; % đã xem | **E4** — **chờ khoá Zoom** |
| 24 | Trợ giảng không có trên tờ phụ huynh; link "sống" | **§66** — một truy vấn thêm cho TG (một giờ); link sống là một màn |
| 25 | Phụ huynh trả lời tiếp TRONG một yêu cầu (nay phải gửi yêu cầu mới) | một tuyến POST + một ô nhập ở cuối tờ — nửa ngày |
| 31 | Nộp TỆP (nay chỉ nộp chữ) | **Đ2 §60** — dựa trên cùng kho tệp với học liệu; một tuyến + một ô |
| * | Thông báo chung (E2) | agent GD đang làm |

---

## LỖI TÌM ĐƯỢC TRONG MÃ

Tất cả đều có số đo, không phải suy đoán.

### 1. `scripts/nap_lai_be.ps1:34` — script cứu worktree lại chết ở đúng worktree

```powershell
$chung = (& git -C $goc rev-parse --git-common-dir 2>$null)
$chung = (Resolve-Path (Join-Path (Join-Path $goc $chung) '..') ...)
```

`--git-common-dir` trả đường **tuyệt đối** ở worktree và **tương đối** ở repo thường.
Đo: ở `D:/pe_hsa_wt/soat` nó trả `D:/pe_hsa/.git`, `Join-Path` cho
`…\soat\D:/pe_hsa/.git`, `Resolve-Path` trả **rỗng**, script thoát với
"Không thấy python của backend (thử cả repo chính)".

Chú thích ngay trên hai dòng ấy (dòng 27–29) viết: *"Thiếu bước này thì script chạy ở
gốc mà đổ ở mọi worktree — tức đổ đúng chỗ agent cần nó nhất"*. Bước ấy có, nhưng sai.
`.githooks/pre-push:24` làm cùng việc bằng `cd "$(git rev-parse --git-common-dir)/.."`
nên đúng cho cả hai kiểu. **Đã vá trong nhánh này.**

### 2. `scripts/do_man_hang_loat.mjs` — bốn lỗ làm bộ đo báo "thiếu tính năng" cho thứ nó không đo được

Chính tệp này viết rằng dương tính giả là "nguy hiểm nhất". Bốn lỗ đã đo được:

- **`/login` bị gạch là hỏng.** `khongDoDuoc` trả "bị đẩy về màn đăng nhập" cho MỌI url
  chứa `/login`, kể cả khi màn mình XIN chính là `/login`. Đo: dòng 1 ra
  "KHÔNG ĐO ĐƯỢC" trong khi trang dựng đủ 78 từ. Dòng 1 · 8 · 13 · 19 của bảng nghiệm
  thu đều đo ở màn ấy.
- **Đi lạc sang màn khác không bị bắt.** Chỉ bắt `d.url === '/'`. `phien.man` dùng lại
  MỘT trang cho mỗi vai, nên một `goto` bị huỷ để trang nằm lại màn trước. Đo: xin
  `/giao-trinh`, đo được `/quan-tri/lop-hoc`, và bộ đo in "dòng 5 THIẾU: chuyenDeBaiHoc,
  khungChuongTrinh" — hai tính năng đang chạy, bị chấm thiếu, dưới tên một màn khác.
- **Mã 500 bị chấm như tính năng thiếu.** `phien.man` nuốt cả lỗi lẫn mã trạng thái
  (`.catch(() => {})`). Đo: `/giang-day/bai-tap/7322` trả **500**
  (`TypeError: __webpack_modules__[moduleId] is not a function`) mà bộ đo vẫn in
  "✗ THIẾU: theoDoiXemRecord".
- **Nhãn nút chỉ đọc `textContent`.** Nút mắt ở ô mật khẩu chỉ có
  `aria-label="Hiện mật khẩu"` (`LoginForm.tsx:253`), nên ý 1.3 của bảng bị chấm "không có".

**Đã vá cả bốn**, cộng ba thứ mới cho việc soát: `bam` (bấm nút, có chờ hết `disabled`
— đúng cái bẫy "nút hiện trước khi React gắn vào"), `chon` (chọn mục trong ô thả xuống),
và tên ảnh mang số thứ tự.

### 3. `scripts/do_man_hang_loat.mjs` (bản cũ) — ảnh đè nhau

Tên ảnh là `man_<dòng>_<vai>.png`. Một dòng nghiệm thu thường cần hai màn (dòng 15 =
Chương trình lớp + Sổ đầu bài) → ảnh sau đè ảnh trước, soát lại chỉ còn một nửa bằng
chứng. Đo: 24 tệp ảnh cho 34 màn. **Đã vá** (thêm số thứ tự vào tên).

### 4. `backend/chuong_trinh/so_dau_bai.py:152-154` — câu lỗi chỉ người dùng đi vào chỗ sai

```python
return None, 'Trạng thái mục phải là một trong: %s.' % ', '.join(
    NHAN_TRANG_THAI_MUC[k] for k in TRANG_THAI_MUC)
```

Câu lỗi liệt kê **nhãn tiếng Việt** ("Đã dạy, Dạy một phần, Chưa dạy") trong khi API
chỉ nhận **mã** (`done`, `partial`, `not_done` — `chuong_trinh/tu_vung.py:21`).
Đo: gửi `"status":"da_day"` → lỗi ấy; gửi đúng nhãn "Đã dạy" mà câu lỗi bảo cũng sẽ
hỏng. Ai đọc câu lỗi rồi làm theo thì vẫn sai. Sửa: in mã, hoặc nhận cả hai.

### 5. `chuong_trinh/du_lieu_mau.py` có mà chưa chạy — dữ liệu mẫu tụt lại sau mã

`teaching/du_lieu_mau.py:428` gọi `dung_khung_mau(...)`, `:204` đếm
`syllabus_versions WHERE is_demo`. Đếm thật: **0**. Sổ đầu bài: **0**.
Bộ dữ liệu mẫu trong CSDL cũ hơn E1. Không phải lỗi mã, nhưng nó làm sáu ô của
bảng nghiệm thu không demo được, nên nó tốn đúng bằng một lỗi.

### 6. `frontend/src/app/(standalone)/quan-tri/tai-khoan/AccountsClient.tsx:441`

```tsx
action={ chiHocVien ? undefined : <XuatTaiKhoan loc={loc().toString()} /> }
```

Ở chế độ "chỉ học viên" — chế độ của **học vụ** — hộp "Tải danh sách" biến mất. Đo:
vai quản trị thấy "Tải danh sách", vai học vụ không thấy (982 từ, không có nút ấy).
Backend cũng chặn (`teaching/exports.py:732` là `IsAdminRole`), nên đây có thể là chủ
ý. Nhưng dòng 6 của bảng ghi "Xuất Excel / CSV | CÓ (V-k) | … 'Tải danh sách' (Tài
khoản)" mà không nói **chỉ quản trị viên** — khách đọc sẽ tưởng giáo vụ tải được.

### 7. Một cảnh báo về bí mật, không phải lỗi mã

Đo dòng 24/25 cần một chìa phụ huynh còn sống (43 ký tự, `parent_link.py:134`).
Chìa ấy là bí mật: cầm nó là xem được hồ sơ một em mà không cần tài khoản. Tôi để
danh sách màn có chìa **ngoài repo** (`%TEMP%`), không commit. Ai soát dòng 24/25
sau này xin làm đúng như vậy — `scripts/man/*.json` là tệp công khai.

---

## Những gì tôi đã đổi trong nhánh này

- `scripts/nap_lai_be.ps1` — vá lỗi 1.
- `scripts/lib/phien_do.mjs` — giữ mã HTTP của `goto`; thêm vai `hv2` (học viên thứ hai,
  cần vì bản ghi Zoom chỉ có ở lớp 1).
- `scripts/do_man_hang_loat.mjs` — vá lỗi 2 và 3; thêm `bam`, `chon`, `chapNhan`.
- `scripts/man/nghiem_thu.json` — 9 màn → 34 màn, phủ 30 dòng và năm vai.
- `scripts/man/nghiem_thu_sau.json`, `scripts/man/nghiem_thu_e1.json`, `scripts/man/nghiem_thu_con_nghi.json` —
  các màn phải BẤM mới tới được, và các màn đo lại sau khi có khung chương trình.
- `docs/agent/BAO_CAO_SOAT2.md` — tệp này.

Dữ liệu thử còn để lại trong CSDL dev (đều là dữ liệu giả, xoá lúc nào cũng được):
khung "SOAT2 — khung thử 3 buổi" (`syllabus_versions` #468) gắn vào **lớp 1** —
lớp KHÔNG phải lớp mẫu — cùng hai sổ đầu bài ở buổi 1542 và 1543. Bài kiểm tra thử
đã xoá. Không có thư nào ra ngoài `@example.com`.
