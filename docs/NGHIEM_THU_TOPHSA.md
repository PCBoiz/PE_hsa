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

## ⚠ TRƯỚC BUỔI NGHIỆM THU: chạy `python manage.py du_lieu_mau --lam-moi`

Đo 27/09/2026: `syllabus_versions` = **0**, `syllabus_sessions` = 0, `session_logs` = **0**, không
bài nào `kind='kiem_tra'`. Bộ dữ liệu mẫu trong CSDL cũ hơn mã — `teaching/du_lieu_mau.py` CÓ dựng
khung chương trình, chỉ là chưa ai chạy lại từ khi E1 về.

**Đây không phải lỗi mã, nhưng nó hỏng buổi nghiệm thu y như một lỗi.** Khách bấm nút "Chương
trình" ở màn Lớp học sẽ thấy *"Lớp chưa nhận khung chương trình"* (đo: màn 69 từ), và "Khung chương
trình" thì *"Môn này chưa có khung nào"* — cho SÁU ô của bảng: dòng 5, 15, 16, và ô tiến độ ở dòng
4, 6, 9. Nút "Nhập điểm" (V-h) cũng không bao giờ hiện, vì không có bài kiểm tra nào để nhập.

Đã kiểm tính năng CÓ chạy, bằng cách dựng một khung thật qua đúng các cửa API rồi gắn vào một lớp:
màn nhảy từ 69 lên **812 từ**, hiện "1 đã dạy", "0 đã dạy, 1 một phần", "Chưa ghi — ghi ngay"; "Toàn
trung tâm" hiện "Lớp chậm tiến độ 1"; thẻ lớp của học viên hiện % chương trình kèm kế hoạch.

`--lam-moi` chỉ gỡ dòng `is_demo` và dựng lại trong MỘT giao dịch, nên dựng hỏng thì bộ cũ còn nguyên.

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
| 9 | Giáo vụ · lớp học | **CÓ** | — | Đo 27/09 bằng **thẻ học vụ**, không mượn thẻ quản trị: bấm "Điểm danh" một buổi → màn 1.159 từ, đủ Có mặt · Vắng · Đi muộn · Xin phép · **Lịch sử sửa điểm danh** · Lưu. |
| 10 | Giáo vụ · lịch học | gần đủ — chỉ còn Zoom | V-n, E4 (Zoom) | **§58 xong 27/09**: đổi giảng viên / trợ giảng cho MỘT buổi, để trống = theo lớp. Đo **7/7 bước trên màn thật**, đã soi ảnh. Quan trọng: **chấm công đi theo người dạy thật** (`COALESCE(s.teacher_id, c.teacher_id)`) — dạy thay mà lương chảy về người đứng tên lớp là lỗi chỉ lộ ra vào cuối tháng. Bộ kiểm 10/10, **3/3 đột biến bị giết**, 37 test buổi học cũ vẫn xanh. Còn lại: tạo/quản lý phòng Zoom (E4 — chờ khoá anh Sơn). |
| 11 | Giáo vụ · hỗ trợ lớp | CÓ (E3, chờ khách xem) | — | §65 **đã gộp vào `erp` 26/09** (`61d42ec`). Bảy trên bảy gạch đầu dòng chạy được trên màn thật: `scripts/do_yeu_cau.mjs` **17/17 bước ĐẠT**, bấm chuột chứ không gọi API tay. Kèm ba hàng rào đã đo: học viên không thấy thẻ Xử lý · ghi chú nội bộ ẩn với học viên · phụ huynh gửi được qua link tờ báo cáo. Còn sót (ngoài phạm vi dòng 11): hạn xử lý / cờ quá hạn, ô tìm theo chữ. |
| 12 | Giáo vụ · thay đổi học tập | **CÓ** (7/8 loại tự làm) | — | Duyệt = hệ thống TỰ THỰC HIỆN trong một giao dịch, ghi rõ đã làm gì. Bảy loại tự làm: chuyển lớp, chuyển môn, bảo lưu, huỷ khoá, học lại, **nghỉ học**, **học bù** (hai loại sau thêm 27/09). "Chuyển lịch" để tay có chủ ý — xem mục chi tiết. |
| 13 | Giáo viên · tài khoản | CÓ | — | — |
| 14 | Giáo viên · lớp + điểm danh | CÓ | — | Đo 26/09 trên màn thật: sổ điểm danh có Có mặt · Vắng · Đi muộn · Xin phép, sửa lại được, và **lịch sử sửa từng buổi** (`LichSuDiemDanh`, V-d) hiện ngay dưới sổ. Tỉ lệ chuyên cần + cảnh báo nghỉ nhiều nằm ở tờ báo cáo và "Việc hôm nay". |
| 15 | Giáo viên · chương trình + tiến độ | **CÓ** | — | E1 xong; **đính kèm tài liệu xong 27/09** (§60 — gắn vào buổi hoặc kho chung của lớp). Ô "đề xuất điều chỉnh tiến độ" vẫn là việc của người, không phải của máy: màn Chương trình chỉ ra lớp chậm ở đâu, giảng viên quyết dồn hay giãn. **§74 xong 27/09**: mỗi mục CẦN bài của khung mang "Chưa giao bài" / "Đã giao: &lt;tên&gt;" / "Đang soạn: &lt;tên&gt;" — khung nói "buổi 3 có bài về nhà" và tới hôm nay mới có chỗ trả lời bài ấy đã giao hay chưa. Đo màn thật lớp mẫu **15/15 bước ĐẠT**, đã soi ảnh: 6/42 mục mang chip, 36 mục chủ đề KHÔNG mang (khoá vắng mặt khác danh sách rỗng), giao một bài thì "Chưa giao bài" 6 → 5. Bộ kiểm 7/7, **6/6 đột biến bị giết** (hai loạt). |
| 16 | Giáo viên · quản lý buổi học | CÓ — E1 xong; đề xuất của GV thành yêu cầu gửi học vụ (E3) | — | — |
| 17 | Giáo viên · giao bài | CÓ | — | Đo 26/09 trên màn thật: Giao bài mới · hạn nộp · **Đổi người nhận** (V-e: `target_mode` + `assignment_targets`) · **Sửa bài** (26/09) · Đóng/Mở nhận bài · Xoá · bảng chấm cả lớp ghi rõ từng em "Chưa nộp" / "Nộp 18/09" kèm tổng "9/27 đã nộp" · nhập điểm · nhận xét. **Thêm 27/09 (§74)**: ô "Mục khung chương trình" nối bài vào đúng mục của khung — danh mục do máy chủ trả, nhãn mang số buổi ("Buổi 4 · Bài về nhà: Luyện tập hệ"), **không bắt buộc** vì bắt chọn sẽ chặn đúng giảng viên đang vội giao bài trước giờ lên lớp. |
| 18 | Giáo viên · theo dõi học sinh | CÓ | — | Đo 26/09, đã soi ảnh: trang từng em có ô **Nhận xét** (in lên tờ phụ huynh), ô **Đánh dấu em cần hỗ trợ** (nội bộ — hiện ở "Việc hôm nay"), ô **Đề xuất hướng học** (nội bộ), cùng lịch sử điểm danh, bài tập và điểm từng bài. V-a + V-f xong. |
| 19 | Trợ giảng · tài khoản | CÓ | — | — |
| 20 | Trợ giảng · nhắn / nhắc | **THAY** — anh Sơn chốt 27/09: nhắn qua **Zalo** hoặc **diễn đàn riêng của lớp**, KHÔNG dựng messenger trong ứng dụng | diễn đàn lớp (đang làm) · Zalo chờ pháp nhân **D2** | Ba nửa, đo riêng 26/09. **Nửa báo lên (E3, chạy được):** hộp Yêu cầu của học vụ nhận yêu cầu "Em không phản hồi tin nhắn 3 ngày" · nguồn "Trợ giảng báo" · chip "Em không phản hồi". **Nửa nhắc cả lớp (E2 backend + E2-GD màn — XONG 26/09):** màn `/giang-day/thong-bao/<lớp>`, tab "Thông báo lớp" trong khu Giảng dạy, đo trên màn thật bằng `scripts/do_thong_bao_lop.mjs` với **thẻ TRỢ GIẢNG** — 13/13 bước của màn lớp ĐẠT, **bấm chuột chứ không gọi API tay**: mở được · tab dẫn tới · ô mở khoá sau khi React gắn · xem trước nói "Sẽ báo cho 3 em qua chuông, 3 em nhận email" · bước hỏi lại nêu ĐÚNG SỐ ("Gửi ngay cho 3 em của lớp …?") · gửi xong "Đã báo cho 3 em" · dòng mới vào danh sách (3 → 4) kèm "3 em nhận" · ô soạn được dọn · **lớp KHÔNG phụ trách → "Không mở được lớp này", không hiện ô soạn** · không một mã kỹ thuật nào lọt lên màn. **Còn thiếu (nói thẳng):** trợ giảng vẫn **không nhắn được RIÊNG một em** — hộp Yêu cầu là kênh do HỌC VIÊN mở trước, và thông báo lớp thì cả lớp cùng nhận. Đó là nửa "nhắn" mà anh Sơn chưa quyết. |
| 21 | Trợ giảng · theo dõi | **CÓ** | — | Ô "Theo dõi việc xem record" (V-l) nay có thật — xem dòng 22. Ba ô còn lại đo 27/09 bằng thẻ trợ giảng. E3: TG giải đáp và báo lên trong hộp Yêu cầu, lịch sử trao đổi lưu đủ. |
| 22 | Trợ giảng · record Zoom | **CÓ** | — | Đo 27/09 trên `/giang-day/buoi-hoc/1`: khối "Bản ghi buổi học" hiện **"1/2 em đã mở"** · mục gập "Chưa mở: 1" liệt kê tên · nút **"Nhắc em chưa mở"** · dòng **"Chưa có bản ghi: 17/09 · 15/09"**. Học viên xem lại được và đánh dấu "đã mở" (§72). Bản ghi TỰ vào buổi vẫn chờ khoá Zoom (E4). |
| 23 | Phụ huynh · tài khoản | THAY (link riêng) | K2, §66 | — |
| 24 | Phụ huynh · xem | MỘT PHẦN (**hạ 27/09** — xem mục dưới) | — | Đo 27/09 trên tờ thật: lịch buổi, tiến độ học tập, **và tên trợ giảng** (§66 — thứ cuối cùng còn thiếu, làm xong 27/09). Trợ giảng đã rời lớp không còn trên tờ; lớp có hai người kèm thì cả hai lên. Tên đi qua được cả đường mở bằng chìa của phụ huynh, còn liên lạc của em thì không. Bộ kiểm 7/7. **HẠ xuống MỘT PHẦN 27/09** sau khi đọc lại đúng chữ trong bảng của khách: ô này đòi cả *"Nhận thông báo khi có thay đổi lịch"*, mà chuông đổi lịch chỉ gửi cho HỌC VIÊN (`teaching/bao_doi_lich.py:128,178` lấy người nhận từ `class_members`). Phụ huynh nhận tờ báo cáo định kỳ qua email, không nhận tin đổi lịch. Anh Sơn để ô này TRỐNG trong bảng — anh ấy đúng, bản này sai. |
| 25 | Phụ huynh · gửi yêu cầu | CÓ qua link (E3, chờ khách xem) | — | `e2e/yeu-cau.spec.ts` |
| 26 | Học sinh · tài khoản + tự đăng ký | CÓ (E5) | — | `scripts/do_dang_ky.mjs` 20/20 |
| 27 | Học sinh · thông báo | **CÓ** | — | Màn `/thong-bao` dựng xong 26/09 và đo trên màn thật bằng `scripts/do_thong_bao.mjs` — **12/12 bước ĐẠT, bấm chuột chứ không gọi API tay**: mở được · có dòng · **không một mã kỹ thuật nào lọt lên màn** (nhãn loại do máy chủ trả, `notifications/loai.py`) · lọc theo loại (20 → 15 dòng, mọi dòng đúng loại) · lọc "Chưa đọc" (20 dòng, tất cả chưa đọc) · số trên ô lọc khớp · đánh dấu đã đọc (24 → 23) · đánh dấu **chưa** đọc (23 → 24) · "Xem thêm" nối 20 → 24 dòng, **0 trùng** (phân trang theo khoá). Chuông ở mọi trang có chân "Xem tất cả thông báo" dẫn sang đây. **Chiều GỬI xong nốt 26/09 (E2-GD)**: `/quan-tri/thong-bao` — học vụ soạn, xem trước, lưu nháp, gửi nháp, huỷ nháp; đo bằng thẻ HỌC VỤ, 11/11 bước của màn ấy ĐẠT (ô chọn lớp dựng từ danh mục máy chủ trả — 6 lớp; ba môn mang nhãn tiếng Việt, không mã `hsa_*`; xem trước theo môn đếm 58 em; đổi ô "Gửi kèm email" làm bản xem trước cũ hết hạn; huỷ nháp đổi nhãn sang "Đã huỷ" và mất nút Gửi). |
| 28 | Học sinh · chương trình + lộ trình | **CÓ** (khi lớp đã nhận khung) | — | Đo 27/09: màn 574 từ, "Điểm danh từng buổi" mở được, % chương trình kèm "(kế hoạch tới nay…)". **Điều kiện**: lớp phải có khung chương trình — xem cảnh báo dữ liệu ở đầu tài liệu. |
| 29 | Học sinh · record | **CÓ** — trừ "% đã xem" (chờ Zoom) | Z1 cho phần % | §72 (26/09): thẻ lớp có "Xem lại: 24/09 22/09", bấm là mở và ghi nhận. **Dò lại 27/09**: thẻ lớp chỉ hiện **4 bản ghi gần nhất** (`teaching/lop_cua_toi.py:44` `SO_BAN_GHI = 4`) và không màn nào của em liệt kê ĐỦ bản ghi theo buổi, cũng không có ô tìm — hai thứ bảng đòi ở dòng này. Buổi thứ năm trở về trước em không có đường nào mở lại. | **Đóng chiều 27/09**: trang `/lop/<id>/xem-lai` — danh sách bản ghi THEO BUỔI của cả khoá, ô tìm theo chủ đề / ngày, lọc "Chưa xem lại", "Xem thêm" phân trang theo khoá. Đo trên màn thật **7/7 bước**, đã soi ảnh: **6 dòng** cho lớp mẫu (trần 4 cũ đã hết), chip "Bạn đã mở" / "Chưa xem lại" đúng từng buổi, địa chỉ hiện kèm tên miền, không mã kỹ thuật nào lọt lên màn. Bộ kiểm 27/27, **16/16 đột biến bị giết**. **Còn thiếu đúng một gạch**: bảng đòi "xem được bao nhiêu **%**" — hệ thống mới biết ĐÃ MỞ / CHƯA MỞ, phần trăm phải lấy từ Zoom (việc **Z1**), không dựng thêm màn là có. |
| 30 | Học sinh · học liệu | **CÓ** (liên kết ngoài) | D1 cho tệp tải lên | §60 (27/09), anh Sơn chốt "làm liên kết ngoài trước". Đo **11/11 bước trên màn thật**, đã soi ảnh: giảng viên gắn tài liệu vào **kho chung của lớp** hoặc **một buổi**, ẩn/hiện theo tiến độ, gỡ được; học viên thấy trên thẻ lớp kèm tên miền, mở tab mới có `noopener`. Địa chỉ `javascript:` bị từ chối, câu lỗi tiếng Việt cạnh đúng ô. Bộ kiểm 27/27, **7/7 đột biến bị giết**. Còn thiếu: **tải tệp thẳng lên** — chờ khoá R2 (D1); lược đồ đã chừa sẵn `nguon='r2'`. **Lưu ý thêm (đo 27/09, cùng lý do dòng 29)**: thẻ lớp chỉ hiện **4 tài liệu gần nhất** (`teaching/lop_cua_toi.py:48` `SO_HOC_LIEU = 4`), không có màn danh sách đủ hay lọc theo buổi — lớp học ba tháng thì tài liệu buổi đầu rơi khỏi thẻ. | **Trần 4 đã hết 27/09**: tab "Tài liệu" của trang `/lop/<id>/xem-lai` liệt kê đủ cả khoá, có ô tìm, tách rõ tài liệu của buổi và kho chung của lớp. |
| 31 | Học sinh · bài tập | CÓ (nộp chữ) | Đ2 §60 (nộp tệp) | — |
| 32 | Học sinh · trao đổi | CÓ (E3, chờ khách xem) | — | `e2e/yeu-cau.spec.ts` |
| * | Phân hệ thông báo chung | MỘT PHẦN | E2 | — |

**Năm chỗ DOI_CHIEU 23/09 báo quá tay** (đã sửa trong bảng dưới): (1) "nhận xét học sinh — CÓ": không
màn nào ghi được `class_members.note`, và cột ấy còn bị ghi chú chuyển lớp dùng chung → lỗi rò đã vá
`e328ade`; (2) TG "dấu hiệu bỏ học — MỘT PHẦN": lúc ấy TG không nhận `vangLien`/`canChuY`
— **đã vá; đo lại 26/09 thì TG thấy đúng như giảng viên trên cùng lớp: dựng một em vắng 3 buổi liền ở lớp 7322, cả hai vai đều nhận `vangLien=1`, và màn TG hiện "Vắng liền từ 2 buổi (1)" kèm nút "Báo cần hỗ trợ"** (dữ liệu đã hoàn nguyên sau khi đo); (3) "record — CÓ": chỉ phía nhân sự, API học viên không
trả `recording_url` — **đã vá 26/09, §72**; (4) "soạn nội dung buổi … `lesson_refs`": không màn nào
dùng; (5) "trạng thái khoá — xuất bản/nháp": `is_published` không sửa được qua API
(`courseadmin/views.py:31`).

**Soát lại 27/09/2026 (anh Sơn: "bảng phân rã còn thiếu nhiều tính năng đấy")**: chín dòng chỉ có một ô
trong bảng tóm tắt mà không có bảng phân rã chi tiết (7, 17, 23, 25, 26, 29, 30, 31, 32 — dòng 30 trước
đó chỉ có đúng một tiêu đề, không một chữ nào bên dưới) nay đã có đủ. Mười ba tiêu đề mục còn ghi nhãn
cũ trong khi bảng tóm tắt đã đổi sau các lượt đo 26–27/09 đã được sửa cho khớp. Và **những gì hệ thống
làm được mà bảng của khách không kê** gom ở mục cuối tài liệu: [Ngoài bảng](#ngoài-bảng--tính-năng-hệ-thống-có-mà-bảng-phân-rã-không-kê-27092026).
Chi tiết lượt soát + câu hỏi chờ anh quyết: `docs/agent/BAO_CAO_PHAN_RA.md`.

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
| Admin + GV reset mật khẩu | THAY — **chờ anh quyết, không phải thiếu mã** | Quản trị viên + học vụ reset được; giảng viên thì không (`teaching/views.py`). Mở cho giảng viên là quyết định về QUYỀN chứ không phải việc viết thêm mã: reset mật khẩu của một em kéo theo quyền chạm tài khoản ấy. Cùng nhóm câu hỏi với **C8**. Khách đã nghiệm thu ô này ở trạng thái hiện tại. |
| Admin + GV import | THAY — **chờ anh quyết, không phải thiếu mã** | Quản trị viên + học vụ nhập được (học vụ chỉ vai Học viên); giảng viên thì không. Cùng lý do trên. Khách đã nghiệm thu ô này. |
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
| Phân công GV, giáo vụ, TG | **CÓ** | GV + TG có từ trước; **học vụ phụ trách thêm 27/09**: khối "Học vụ phụ trách" ở màn Lớp học, gán / gỡ như trợ giảng (cùng cơ chế `class_members`, không bảng mới). **Gán là phân công, KHÔNG cắt quyền** — học vụ vẫn thấy mọi lớp; cái còn thiếu chỉ là câu trả lời "lớp này ai phụ trách" khi trung tâm có nhiều người. Sĩ số lớp không đổi khi gán (có phép kiểm riêng: một học vụ lọt vào sĩ số sẽ chảy vào mẫu số chuyên cần và tờ phụ huynh). Bộ kiểm 6/6, bộ đo màn thật 6/6 bước. |
| Lịch sử thay đổi / phân công lớp | CÓ (V-n) | "Lịch sử thay đổi của lớp" ở Học viên của lớp: sửa lớp, xếp / cho rời / chuyển em, gán trợ giảng, tạo / sửa / huỷ buổi, mới nhất trước — chỉ phần của lớp ấy (`GET /api/admin/classes/<id>/lich-su`, IsAdminOrAcademic; nhật ký đầy đủ vẫn chỉ quản trị viên) — `teaching/tests_lich_su_lop.py` |
| Dòng thời gian Đăng ký → … → Hoàn thành | CÓ | "Kiểm tra / Thi thử / Kết quả" (V-h): mốc "Bài kiểm tra: …" theo NGÀY làm bài, điểm hoặc "Vắng" (`teaching/dong_thoi_gian.py`, loại `kiem-tra`). Mốc **"Đăng ký"** (E5, §73): em tự mở tài khoản → "Tự đăng ký tài khoản trên website" thay cho "Được cấp tài khoản", rồi "Xác nhận địa chỉ email" (nhật ký `user.self_register` / `user.verify_email`). Hai mốc chứ không một — khoảng cách giữa chúng là thứ học vụ đọc khi một lượt đăng ký trông đáng ngờ |
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
| Gắn video record | CÓ | link theo buổi; học viên xem lại được (§72, 26/09). Bản ghi tự gắn từ Zoom vẫn chờ khoá (Z1) |
| Gắn tài liệu | **CÓ** | **§60 xong 27/09** — giảng viên gắn liên kết ngoài (Drive, YouTube, link đề) vào **kho chung của lớp** hoặc **một buổi cụ thể**, ẩn/hiện theo tiến độ, gỡ được; học viên thấy trên thẻ lớp. Đo 11/11 bước trên màn thật, 27/27 test, 7/7 đột biến bị giết. Còn thiếu: **tải TỆP thẳng lên** — chờ khoá R2 (việc D1 của anh); lược đồ đã chừa sẵn `nguon='r2'`. |
| Gắn bài tập, bài kiểm tra | **CÓ** | Khung có mục loại "Bài về nhà" / "Kiểm tra" và ô bài về nhà mỗi buổi (E1). **§74 (27/09)**: bài giao cho lớp nay TRỎ VỀ mục khung — màn Chương trình trả lời được "bài về nhà của buổi 3 đã giao chưa" (`baiDaGiao` mỗi mục). NULL vẫn là trạng thái bình thường: phần lớn bài giao rời, và bắt buộc trường này sẽ chặn giảng viên đang vội. Xoá mục khung KHÔNG kéo mất bài đã giao (§29). Bộ kiểm 5/5 + 57 test chương trình vẫn xanh. |
| Điều kiện hoàn thành | MỘT PHẦN — **chờ con số của anh Sơn** | % chương trình theo sổ đầu bài (đã dạy 1, một phần 0,5, trọng số) (E1). Dò lại 27/09: hệ thống có BỐN ngưỡng bằng số, và KHÔNG ngưỡng nào là "hoàn thành khoá". (1) lớp chậm tiến độ — trễ ≥ **2** buổi khung HOẶC xong < **80 %** phần phải xong tới hôm nay (`backend/chuong_trinh/tu_vung.py:34`; chú thích ngay đó ghi đây là GIẢ ĐỊNH của mình, để lộ ra để còn bàn lại); (2) vắng liền ≥ **2** buổi, bài chấm quá **5** ngày (`backend/teaching/viec_hom_nay.py:52`); (3) không hoạt động **7 / 14 / 30** ngày (`backend/teaching/overview.py:85`); (4) chủ đề yếu = dưới **60** điểm (`backend/teaching/reports.py:75`). "Đã học xong" hôm nay do NGƯỜI chọn chứ không do máy tính: học vụ cho em rời lớp với lý do "học xong" (`backend/teaching/vocab.py:44`), hoặc lớp đã qua ngày kết thúc mà em chưa bị cho rời (`backend/teaching/tinh_trang.py:64`). Cần anh cho ba con số: **% buổi có mặt tối thiểu**, **% chương trình tối thiểu**, và **có bắt buộc điểm bài kiểm tra hay không** — câu hỏi đầy đủ ở `docs/agent/BAO_CAO_PHAN_RA.md` |

## Dòng 6 — Báo cáo · MỘT PHẦN (còn báo cáo chéo môn × lớp)

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| 6.1 Tổng quan học tập, số học sinh, số lớp | CÓ | "Toàn trung tâm" (`teaching/overview.py`) |
| 6.2 Doanh thu | BỎ | anh chốt 23/09 |
| 6.3 Chấm công GV/TG | CÓ, chỉ xem (V-o) | trang "Chấm công" (Vận hành, quản trị viên + học vụ): theo tháng, từng giảng viên VÀ trợ giảng — buổi đã dạy, tổng giờ, tự điểm danh, điểm danh muộn, tải Excel (`teaching/cham_cong.py`, `teaching/tests_cham_cong.py`). Khoá tháng + chỉnh tay → **Đ2 §59** |
| Điểm danh HS, tiến độ, kết quả theo lớp | CÓ | CSV điểm danh + tiến độ; báo cáo lớp PDF |
| Kết quả theo môn, hoàn thành bài tập (tổng) | MỘT PHẦN | theo khoá / từng bài; chưa báo cáo chéo |
| Hoạt động GV/TG | **CÓ** | Buổi dạy / điểm danh theo tháng (V-o) + **bài đã chấm** và **thông báo đã gửi** (27/09) — cùng MỘT câu SQL, cùng bảng, và cùng có trong bản tải .xlsx. Với trợ giảng thì hai cột sau mới là phần lớn công việc. Mốc là NGÀY CHẤM (`graded_at`), không phải hạn nộp; bản nháp chưa gửi không tính. Người không làm gì vẫn có dòng, số 0 — dòng biến mất trông như đã nghỉ việc. Bộ kiểm 6/6. |
| HS nghỉ nhiều / chậm tiến độ | CÓ (E1) | nghỉ nhiều CÓ; lớp chậm tiến độ + lớp chưa ghi sổ: ô "Tiến độ chương trình" ở Toàn trung tâm (`overview.py` khoá `chuongTrinh`) |
| Bộ lọc thời gian / lớp / môn / khoá | CÓ (V-k) | tổng quan lọc đợt + ngày; tải chuyên cần lọc khoảng ngày; tải danh sách tài khoản lọc thêm đợt học, môn, ngày cấp (`teaching/exports.py`, `admin_users.build_user_filters`) — `teaching/tests_xuat_excel.py` |
| Xuất Excel / CSV | CÓ (V-k) | hộp "Tải bảng tính" (sổ buổi học của lớp) và "Tải danh sách" (Tài khoản): chọn Excel (.xlsx) hoặc CSV; một bộ ghi `common/bangtinh.ghi_xlsx` (ô chữ không bao giờ thành công thức), trợ giảng không nhận cột liên lạc **Lưu ý (đo 27/09)**: hộp "Tải danh sách" ở trang Tài khoản CHỈ quản trị viên thấy — học vụ mở cùng trang thì không có hộp ấy (`exports.py` là `IsAdminRole`). Có chủ ý hay không thì chờ anh quyết ở mục **C8** (học vụ có được xem liên hệ phụ huynh không); bảng không được ghi "CÓ" trống như thể mọi vai đều tải được. |

## Dòng 7 — Kế toán · học phí · THAY

Anh chốt 25/09: không sổ tiền, không doanh thu, không vai Kế toán. Thay bằng ô "Tình trạng học phí"
trên hồ sơ (**V-m — đã làm**: ô chọn Đã đóng / Sắp hết / Hết / Bảo lưu ở khối "Tình trạng" của hồ sơ,
học vụ / quản trị viên đặt, có nhật ký, lọc + cột ở Tài khoản, cột "Học phí" trong tệp xuất). Khách phải đồng ý (K2). Dữ liệu "cơ sở tính học phí" (buổi đã học / có mặt / vắng
theo em) đã có cho quản trị viên ở "Cơ sở học phí".

Phân rã chi tiết (bổ sung 27/09/2026 — trước đây dòng này chỉ có đoạn văn trên):

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Thu học phí, phiếu thu, sổ tiền | BỎ — **khách phải đồng ý (K2)** | anh chốt 25/09: không sổ tiền, không vai Kế toán. Lý do dừng ở đây viết trong `backend/teaching/co_so_hoc_phi.py:1` — "sai một chi tiết là sai sổ sách", nên nối với phần mềm kế toán TopHSA đang dùng rẻ hơn viết lại |
| Báo cáo doanh thu | BỎ | như trên; xem ô 6.2 ở dòng 6 |
| Tình trạng học phí của từng em | THAY (V-m) | ô chọn tay Đã đóng / Sắp hết / Hết / Bảo lưu, mã lưu theo CHECK §63 (`backend/teaching/tinh_trang.py:41`); ô lọc + cột ở Tài khoản, cột "Học phí" trong tệp xuất |
| Ai đổi ô ấy, lúc nào | CÓ — **chỉ quản trị viên đọc được** | nhật ký quản trị (`backend/teaching/admin_users.py:985`); tab "Nhật ký" chỉ mở cho vai quản trị (`frontend/src/app/(standalone)/quan-tri/vai.ts:81`) |
| Cơ sở tính học phí theo em (buổi đã học / có mặt / vắng) | CÓ — **chỉ quản trị viên, học vụ không thấy** | `backend/teaching/co_so_hoc_phi.py:114` là `IsAdminRole`, và tab "Cơ sở học phí" chỉ liệt vai quản trị (`frontend/src/app/(standalone)/quan-tri/vai.ts:74`). Cùng nhóm câu hỏi với **C8**: ở TopHSA ai tính học phí thật |
| Nối với phần mềm kế toán | CHƯA — chờ anh | không mã nào làm; `co_so_hoc_phi.py:1` nêu đây là khuyến nghị có chủ ý, không phải việc bỏ sót |

## Dòng 9 — Giáo vụ · lớp học · CÓ (sửa nhãn 27/09: bảng tóm tắt đã là CÓ từ lượt đo 27/09)

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
| Đổi GV / TG cho một buổi | **CÓ** | **§58 xong 27/09**: ô "Giảng viên buổi này" / "Trợ giảng buổi này" ở form sửa buổi, để trống = theo lớp. **Chấm công đi theo người dạy thật** (`COALESCE(buổi, lớp)`). Đo 7/7 bước trên màn thật, 10/10 test, 3/3 đột biến bị giết. |
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

## Dòng 12 — Quản lý thay đổi học tập · CÓ, 7 trên 8 loại tự làm (E3; sửa nhãn 27/09 sau khi §65d thêm nghỉ học + học bù)

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
| Chuyển lịch, học bù, nghỉ học | **CÓ** (2 trên 3 tự làm) | **27/09**: duyệt "xin nghỉ học" → hệ thống ghi **"có phép"** cho mọi buổi trong khoảng ngày và nói rõ đã ghi đè mấy lượt điểm danh; duyệt "xin học bù" → học vụ **chọn buổi bù** rồi bấm, em vào `session_participants` của buổi ấy. Đo 6/6 bước trên màn thật, 10/10 test. **"Chuyển lịch" vẫn để tay có chủ ý**: đổi giờ cho một em phụ thuộc lớp nào còn chỗ, giờ nào em học được, giảng viên nào dạy — ba thứ hệ thống không biết, và tự đoán rồi xếp em vào là làm hỏng nhiều hơn làm được. |

**Demo**: học viên → "Hỏi & yêu cầu" → "Xin chuyển lớp", gõ lớp mong muốn → Gửi. Học vụ → Yêu cầu →
mở → "Duyệt…" → chọn lớp tới → đọc "Hệ thống sẽ: Chuyển … sang lớp …" → "Duyệt và thực hiện". Mở
Lớp học: em đã ở lớp mới; lịch sử yêu cầu có dòng "Duyệt yêu cầu" + "Hệ thống đã làm"; học viên
nhận chuông. Bấm duyệt lần hai → báo đã duyệt, không chuyển thêm.

## Dòng 14 — Giáo viên · lớp + điểm danh · CÓ (sửa nhãn 27/09: lịch sử sửa điểm danh V-d đã đóng ô cuối)

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Danh sách lớp được phân công | CÓ | "Việc hôm nay", khu Giảng dạy |
| Cập nhật mục tiêu, nguyện vọng HS | CÓ | tờ báo cáo từng em (`teaching/ho_so.py`) |
| Điểm danh có mặt / vắng / muộn / xin phép, cập nhật | CÓ | màn Buổi học |
| Người được phép sửa | CÓ | GV lớp mình, TG lớp được gán, học vụ, quản trị viên |
| Lưu lịch sử chỉnh sửa | CÓ (V-d) | như dòng 9: mỗi lần ĐỔI một dòng (ai, từ gì → gì, lúc nào); lưu lại y hệt ghi 0 dòng. Demo: giảng viên/trợ giảng → Buổi học → Điểm danh → "Lịch sử sửa điểm danh" |
| Thống kê tỉ lệ, cảnh báo nghỉ nhiều | CÓ | |

## Dòng 15 — Giáo viên · chương trình + tiến độ · CÓ

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| Soạn / chuẩn bị nội dung buổi | CÓ (E1) | buổi học gắn buổi khung (tự động theo ngày, gắn tay được); sổ đầu bài hiện nội dung kế hoạch + bài về nhà |
| Đính kèm tài liệu | **CÓ** | **§60 xong 27/09** — giảng viên gắn liên kết ngoài (Drive, YouTube, link đề) vào **kho chung của lớp** hoặc **một buổi cụ thể**, ẩn/hiện theo tiến độ, gỡ được; học viên thấy trên thẻ lớp. Đo 11/11 bước trên màn thật, 27/27 test, 7/7 đột biến bị giết. Còn thiếu: **tải TỆP thẳng lên** — chờ khoá R2 (việc D1 của anh); lược đồ đã chừa sẵn `nguon='r2'`. |
| Nội dung đã / chưa hoàn thành | CÓ (E1) | **Sổ đầu bài** `/giang-day/so-dau-bai/<buổi>`: từng nội dung đã dạy / một phần / chưa dạy + ghi chú |
| Ghi chú sau buổi | CÓ (`class_sessions.note`) | — |
| Tiến độ thực tế vs kế hoạch, đề xuất điều chỉnh | MỘT PHẦN (E1) | tiến độ vs kế hoạch CÓ (màn Chương trình lớp); ô "Đề xuất" trong sổ là chữ tự do — biến thành yêu cầu ở **E3** |

## Dòng 16 — Giáo viên · quản lý buổi học · CÓ (sửa nhãn 27/09: E1 + E3 đã đóng ô đề xuất)

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| Buổi đã diễn ra, tình hình lớp | CÓ (trạng thái `done`, điểm danh, `note`) | — |
| Nội dung thực tế / chưa hoàn thành, mức tiếp thu | CÓ (E1) | sổ đầu bài: từng nội dung + mức tiếp thu 1–5 |
| Đề xuất HS cần hỗ trợ | CÓ (E1) | sổ đầu bài: đánh dấu em cần hỗ trợ + ghi chú (`session_support`, nội bộ); cờ theo em **V-f** |
| Đề xuất học bù / điều chỉnh tiến độ | CÓ (E1 + E3) | ô "Đề xuất" trong sổ đầu bài + nút "Gửi đề xuất cho học vụ" → một yêu cầu "Báo lên" gắn buổi (`components/YeuCauDeXuat.tsx`); học vụ trả lời / tạo buổi bù ở hộp Yêu cầu. Demo: sổ đầu bài một buổi → gõ Đề xuất → "Gửi đề xuất cho học vụ" → "Xem yêu cầu →" |

## Dòng 17 — Giáo viên · giao bài · CÓ (sửa nhãn 27/09 — ô "sửa bài" đã đóng, xem bảng dưới)

Tạo, hạn lúc TẠO, xoá / đóng / mở lại, danh sách, xem bài nộp, chấm, nhập điểm, nhận xét, trả bài, ai chưa nộp:
CÓ (`teaching/assignments.py`). **"Chỉnh sửa bài tập"**: ô này ghi "CHƯA" hôm 26/09 — câu cũ giữ nguyên bên dưới theo RULES §29 — và nó
**đã hết đúng**: dò lại 27/09 thì màn giảng viên có form sửa thật, với ô tên bài
(`giang-day/bai-tap/[classId]/AssignmentsClient.tsx:457`), ô hạn nộp (`:471`) và ô thang điểm (`:478`), gửi bằng
`PATCH /api/teach/assignments/<id>` mang `title` / `due_at` / `max_score` (`:232`, thân khai ở `:54`) vào đúng cửa
backend `teaching/assignments.py:549`. Gõ nhầm hạn nộp nay sửa được, không phải xoá bài rồi giao lại.
*Câu cũ (26/09, để tra lịch sử):* "sau khi đã giao, màn của giảng viên chỉ gửi được hai thứ — đổi người nhận và
đóng/mở bài; backend nhận sửa đầy đủ nhưng KHÔNG màn nào gọi tới". **Thiết lập đối tượng nhận bài** (một nhóm em): CÓ (V-e) —
`assignments.target_mode` + `assignment_targets` (§62d); MỘT hàm lọc `teaching/nhan_bai.giao_cho` ở mọi chỗ
đọc bài (danh sách + sĩ số từng bài, bảng chấm, bài của học viên, nộp bài, thẻ lớp, tờ phụ huynh, Việc hôm
nay, chuông "bài mới"). Test `teaching/tests_nhan_bai.py` (10). Demo: giảng viên → Bài tập của lớp → "Giao bài
mới" → "Giao cho: Chọn học viên" → tick 2 em → Giao bài; em thứ ba không thấy bài ở mục Bài tập.
Bài kiểm tra ngoại tuyến GV nhập điểm: CÓ (V-h) — Loại "Bài kiểm tra trên lớp (nhập điểm)" khi giao bài,
nút "Nhập điểm" mở bảng cả lớp có ô "Vắng" (xem dòng 4, "Điểm kiểm tra"). Test `teaching/tests_kiem_tra.py` (6).

Phân rã chi tiết (bổ sung 27/09/2026 — trước đây dòng này chỉ có đoạn văn trên):

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Giao bài mới, hạn nộp, thang điểm | CÓ | `backend/teaching/assignments.py:450`, cửa tạo ở `:500` |
| Sửa bài đã giao | **CÓ** (sửa ô 27/09) | `AssignmentsClient.tsx:457` (tên bài), `:471` (hạn nộp), `:478` (thang điểm), gửi ở `:232`; cửa backend `backend/teaching/assignments.py:549` |
| Đóng / mở lại nhận bài, xoá bài | CÓ | `AssignmentsClient.tsx:282` (đóng / mở), `:253` (xoá — có bước hỏi lại khi đã có em nộp) |
| Chọn người nhận bài (một nhóm em) | CÓ (V-e) | `assignments.target_mode` + `assignment_targets` (§62d); MỘT hàm lọc `backend/teaching/nhan_bai.py` dùng ở mọi chỗ đọc bài. Test `backend/teaching/tests_nhan_bai.py` (10) |
| Xem bài nộp, biết ai chưa nộp | CÓ | `backend/teaching/assignments.py:664` (bảng chấm cả lớp), `:1021` (một bài nộp) |
| Chấm điểm, nhận xét, trả bài | CÓ | `backend/teaching/assignments.py:664`; chấm KHÔNG đụng `submitted_at` (`:835`) — chấm không phải là nộp |
| Bài kiểm tra trên lớp: nhập điểm cả lớp, ghi "Vắng" | CÓ (V-h) | `assignments.kind = 'kiem_tra'` + `submissions.absent` (§62f); test `backend/teaching/tests_kiem_tra.py` (6) |
| Trợ giảng chấm bài được nhưng không xoá bài | CÓ — có chủ ý | `backend/teaching/assignments.py:505` kiểm vai trong thân view, không đổi `permission_classes` |
| Nối bài giao với buổi trong khung chương trình | CÓ (§74, 27/09) | trả lời được "bài về nhà của buổi 3 đã giao chưa" — xem dòng 5 |
| Nhận bài bằng TỆP tải lên | CHƯA → D1 (chờ khoá R2) | cửa nộp của em chỉ ghi chữ (`backend/teaching/assignments.py:998` chỉ INSERT `content`); cột `submissions.file_url` đã chừa sẵn và bảng chấm đã trả `fileUrl` (`:711`) |

## Dòng 18 — Giáo viên · theo dõi học sinh · CÓ (sửa nhãn 27/09: V-a + V-f xong, đo màn thật 26/09)

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Lịch sử học tập, điểm danh, bài tập, kết quả từng bài | CÓ | tờ báo cáo từng em |
| **Ghi nhận nhận xét học sinh** | CÓ (V-a) | `PUT …/students/<u>/danh-gia` (`teaching/danh_gia.py::DanhGiaHocVienView`) ghi `class_members.teacher_comment` (§62a) vào lượt đang mở, không đụng `note`; tờ phụ huynh in `membership.teacherNote`. Test `teaching/tests_danh_gia.py` (7). Demo: giảng viên → Báo cáo phụ huynh → Xem tờ của em → khối "Đánh giá của giảng viên" → ô "Nhận xét gửi phụ huynh" → Lưu đánh giá → tờ bên dưới in "Nhận xét của giảng viên" |
| Đánh giá mức độ tiến bộ | CÓ | "Con có tiến bộ không" trên tờ |
| Đánh dấu cần hỗ trợ | CÓ (V-f) | `class_members.can_ho_tro` + lý do (§62b), cùng đường `danh-gia` (trợ giảng đặt được); hiện ở "Việc hôm nay" khối "Cần hỗ trợ" (`viec_hom_nay._can_ho_tro`) và dòng thời gian (`dong_thoi_gian._danh_gia`, nhật ký `class.member.assess`). Demo: giảng viên tick "Đánh dấu em cần hỗ trợ" trên tờ của em, hoặc trợ giảng bấm "Báo cần hỗ trợ" trên dòng em vắng liền ở Việc hôm nay |
| Đề xuất hướng học tập | CÓ (V-f) | `class_members.de_xuat_huong_hoc` (§62b), chỉ giảng viên trở lên, nội bộ (không lên tờ phụ huynh). Demo: ô "Đề xuất hướng học" trong khối "Đánh giá của giảng viên"; học vụ thấy mốc "Đề xuất hướng học" trên dòng thời gian của em |

## Dòng 20 — Trợ giảng · nhắn tin / nhắc · THAY (anh Sơn chốt 27/09)

**QUYẾT ĐỊNH CỦA CHỦ DỰ ÁN, 27/09/2026** — nguyên văn:

> *"Những phần như này thì mình biến thành nhắn tin qua Zalo hoặc qua diễn đàn riêng của lớp,
> không làm thành 1 messenger trong ứng dụng mình đâu"*

Tức tám gạch đầu dòng của ô này KHÔNG đóng bằng một hộp chat trong ứng dụng. Hai kênh thay thế:

| Kênh | Đóng được gạch nào | Trạng thái |
|---|---|---|
| **Diễn đàn riêng của lớp** | nhắn tin cho học sinh · nhận tin nhắn · theo dõi lịch sử trao đổi | **máy chủ XONG 27/09 (§75)**, màn còn thiếu — xem dưới |
| **Zalo** | nhắn riêng ngoài giờ, nhắc gấp | chờ **D2** (pháp nhân để mở Zalo OA) — mã ZNS đã có, chưa bật |

Ba gạch "nhắc học bài / làm bài / tham gia lớp" đã chạy bằng **thông báo lớp** (E2-GD) và chuông tự
động nhắc hạn nộp — không cần chat. Hai gạch "ghi nhận em không phản hồi" và "chuyển vấn đề cho
GV/giáo vụ" đã chạy bằng hộp Yêu cầu (E3).

**§75 · máy chủ đã khoanh diễn đàn theo lớp (27/09)**. `posts.class_id`: NULL = bài sân chung
(mọi bài đang có), có số = bài riêng của lớp ấy. Một hàng rào duy nhất
(`forum/views.py::vao_duoc_dien_dan_lop`) quyết ai vào được: người phụ trách lớp (hỏi
`can_see_class`, không viết lại luật) và học viên **đang** học lớp (`class_members.left_at IS
NULL`). Người ngoài nhận **404**, không 403 — không lộ lớp nào tồn tại.

Ba chỗ dễ rò, mỗi chỗ một phép kiểm và một đột biến:
· sân chung `/api/posts` KHÔNG kèm `lop` chỉ trả bài không thuộc lớp nào — bỏ điều kiện ấy là
  mọi trao đổi riêng của mọi lớp hiện nguyên văn cho bất kỳ ai đăng nhập;
· đoán id bài qua `/api/posts/<id>` — mọi cửa con của một bài (xem, bình luận, thả cảm xúc)
  đều đi qua cùng hàng rào, không sót cửa nào;
· em **đã rời lớp** không đọc tiếp được.

Bộ kiểm `forum/tests_dien_dan_lop.py` **7/7**, **5/5 đột biến bị giết**, 20 test diễn đàn cũ vẫn
xanh. Lược đồ: `bootstrap_schema` hai lượt (lượt 2 = 0 mục), `kiem_luoc_do` §75a/§75b ✓.

**Còn thiếu**: MÀN. Chưa có chỗ nào trên giao diện mở diễn đàn của lớp — cửa API chạy rồi nhưng
người dùng chưa bấm được, nên ô này CHƯA đóng.

Danh sách lớp + thông tin HS: CÓ (cắt liên lạc — có chủ ý).

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Nhận tin, lịch sử trao đổi | CÓ (E3) | câu hỏi học viên gửi lớp → GV + TG lớp nhận chuông; trả lời + lịch sử ở `/yeu-cau/<id>` |
| Ghi nhận HS không phản hồi | CÓ (E3) | "Tạo yêu cầu" → "Báo lên", chọn lớp + em, tick "Em không phản hồi" (`du_lieu.khong_phan_hoi`, chip trên hộp) |
| Chuyển vấn đề cho GV / giáo vụ | CÓ (E3) | "Báo lên" tới GV lớp + học vụ; "Chuyển tiếp…" một yêu cầu đang cầm |
| TG CHỦ ĐỘNG nhắn một HS | **THAY** (anh chốt 27/09) | không làm messenger trong ứng dụng. Nhắn riêng đi qua **Zalo** (chờ D2); trao đổi có lưu vết đi qua **diễn đàn riêng của lớp** (đang làm). Câu hỏi cũ trong `docs/agent/BAO_CAO_E3.md` coi như đã trả lời. |

SĐT phụ huynh để lại trong yêu cầu ẩn với trợ giảng (test `test_tro_giang_khong_thay_sdt_phu_huynh`).
**Demo**: trợ giảng → khu Giảng dạy → Yêu cầu → "Tạo yêu cầu" → loại "Báo lên", lớp, em, tick "Em
không phản hồi" → Gửi. Học vụ thấy yêu cầu với chip "Em không phản hồi".

## Dòng 21 — Trợ giảng · theo dõi · CÓ (sửa nhãn 27/09: ô theo dõi việc xem bản ghi V-l đã có)

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| Điểm danh, theo dõi bài tập, tiến độ | CÓ | — |
| Hỗ trợ giải đáp | CÓ (E3) | câu hỏi của em tới hộp Yêu cầu của GV + TG lớp; TG trả lời, chuyển tiếp hoặc báo lên. Demo: như dòng 32 rồi đăng nhập trợ giảng lớp → Yêu cầu |
| Theo dõi việc xem record | **CÓ** | Đo 27/09 trên `/giang-day/buoi-hoc/1`: khối "Bản ghi buổi học" hiện "1/2 em đã mở", mục gập "Chưa mở: 1" liệt kê tên. |
| Dấu hiệu bỏ học, danh sách cần nhắc / cần báo | CÓ phần theo dõi (V-b) + báo "cần hỗ trợ" (V-f); trao đổi hai chiều chờ **E3** | `teaching/viec_hom_nay.py` `ViecHomNayView.get` trả `vangLien` + `canChuY` cho mọi vai, phạm vi `_lop_cua`; test `tests_viec_hom_nay.py::test_tro_giang_thay_vang_lien_chi_lop_minh`. Demo: đăng nhập trợ giảng → "Việc hôm nay" → khối "Vắng liền" / "Cần chú ý ngay" của lớp mình, dòng dẫn về sổ buổi học |

## Dòng 22 — Trợ giảng · record Zoom · CÓ trừ phần Zoom tự nối (sửa nhãn 27/09 sau §72)

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| TG dán link record vào buổi, record thuộc buổi nào, link, giáo vụ / TG cập nhật | CÓ | `class_sessions.recording_url` (màn Buổi học) |
| Đã upload / chưa upload | **CÓ** | §72 — dòng "Chưa có bản ghi: 17/09 · 15/09" trên màn Buổi học, đo 27/09. |
| HS đã xem / chưa xem | **CÓ** | §72 — bảng "ai đã mở" theo từng buổi, đo được "1/2 em đã mở" (27/09). |
| Nhắc HS chưa xem | **CÓ** | §72 — nút "Nhắc em chưa mở" trên màn Buổi học, gửi chuông cho đúng những em chưa mở. |
| Báo lỗi record | **CÓ** | §72 — nút "Không mở được?" trên thẻ lớp của học viên; chuông gộp nói rõ mấy em báo. Chỗ nhận báo (chuông hay hộp Yêu cầu) còn chờ anh chốt — mục K4. |

## Dòng 23 — Phụ huynh · tài khoản · THAY

Anh chốt 25/09: phụ huynh KHÔNG có tài khoản; dùng link riêng (không mật khẩu, thu hồi được, có hạn).
Khách phải đồng ý (K2). Nâng link thành "link theo dõi" sống → **§66**.

Phân rã chi tiết (bổ sung 27/09/2026 — trước đây dòng này chỉ có đoạn văn trên):

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Phụ huynh có tài khoản riêng, đăng nhập / đăng xuất | THAY — **khách phải đồng ý (K2)** | không làm; thay bằng đường dẫn riêng cấp từ màn Báo cáo phụ huynh (`backend/teaching/parent_link.py:89`) |
| Quên mật khẩu cho phụ huynh | THAY | không có mật khẩu nào để quên |
| Nối phụ huynh với đúng con mình | CÓ — theo cách khác | mỗi chìa gắn CHẶT một em + một lớp + một kỳ; máy chủ lấy từ chìa, không từ biểu mẫu (`backend/teaching/parent_link.py:216`) |
| Hạn dùng của đường dẫn | CÓ — **45 ngày** | `HAN_NGAY = 45` (`backend/teaching/parent_link.py:60`), chọn theo nhịp gửi báo cáo hằng tháng |
| Thu hồi khi cần | CÓ | `revoked_at` (`backend/teaching/parent_link.py:164`); chìa lạ / hết hạn / đã thu hồi đều nhận CÙNG một câu 404 (`:69`) — không để ai dò xem chìa nào có thật |
| Biết phụ huynh đã mở chưa | CÓ | `opened_count` + `last_opened_at` (`backend/teaching/parent_link.py:104`), đếm SAU khi dựng xong tờ để một lượt lỗi không thành một lượt "đã đọc" |
| Phụ huynh tự tắt nhận báo cáo | CHƯA — **bảng có, mã chưa** | bảng `parent_report_optout` §50 dựng sẵn (`backend/sql/legacy_schema.sql:1645`), có cả dòng kiểm lược đồ (`backend/common/management/commands/kiem_luoc_do.py:167`), nhưng đo 27/09 thì KHÔNG tệp mã nào đọc hay ghi nó. Nửa tính năng — đừng kể là đã có |
| Link "sống" (số liệu tới hôm nay, không cố định theo kỳ) | CHƯA → §66 | kỳ nằm trong chìa (`backend/teaching/parent_link.py:216`) |

## Dòng 24 — Phụ huynh · xem · CÓ (sửa nhãn 27/09: §66 đã thêm tên trợ giảng, ô cuối còn thiếu)

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Lịch học, lớp, môn, GV, TG | **CÓ** | Tờ phụ huynh có lịch buổi, lớp, môn, giảng viên — và **trợ giảng** (thêm 27/09, §66). Trợ giảng đã rời lớp không còn trên tờ. |
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

Phân rã chi tiết (bổ sung 27/09/2026 — trước đây dòng này chỉ có đoạn văn trên):

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Phụ huynh gửi được yêu cầu / thắc mắc | CÓ qua link | khối "Gửi yêu cầu cho trung tâm" ở cuối tờ `/bc/<chìa>`; cửa `backend/yeu_cau/views.py:416` (`PhuHuynhYeuCauView`) |
| Chọn loại (liên hệ giáo vụ / liên hệ giảng viên) | CÓ | loại mở cho nguồn `phu_huynh` khai ở `backend/yeu_cau/loai.py:140`; "hỗ trợ" tới học vụ, "Hỏi giảng viên" tới giảng viên + trợ giảng của lớp |
| Máy chủ biết đây là phụ huynh của em nào | CÓ — không tin biểu mẫu | em + lớp lấy từ chìa (`backend/yeu_cau/views.py:428`), không lấy từ trường ẩn nào |
| Theo dõi trạng thái, đọc trả lời | CÓ | mở lại chính đường dẫn: khối "Yêu cầu đã gửi qua đường dẫn này" (`backend/yeu_cau/views.py:436`) kèm trạng thái, kết quả và trả lời |
| Không thấy ghi chú nội bộ của trung tâm | CÓ — đã kiểm | phạm vi người đọc theo `NguoiLam(link=…)`; test `backend/yeu_cau/tests_yeu_cau.py` |
| Chống gửi tràn | CÓ | tối đa **5** yêu cầu đang mở mỗi đường dẫn (`backend/yeu_cau/loai.py:174` `TRAN_MO_PHU_HUYNH = 5`) + trần lượt gửi theo giờ / theo máy (`GuiYeuCauPhuHuynhThrottle`, `backend/yeu_cau/views.py:426`) |
| Chìa lạ / hết hạn / đã thu hồi | CÓ — cùng một câu 404 | `backend/yeu_cau/views.py:419`, dùng chung `_cua_ai` với tờ báo cáo |
| Phụ huynh trả lời TIẾP trong một yêu cầu | CHƯA | phải gửi yêu cầu mới; cửa trả lời tiếp chỉ mở cho học viên đã đăng nhập (`backend/yeu_cau/views.py:130`) |
| Đường dẫn "sống" sau buổi xem | CHƯA → §66 | như dòng 23 |

## Dòng 26 — Học sinh · tài khoản · CÓ

Đăng nhập / ghi nhớ / quên mật khẩu / đăng xuất: CÓ (như dòng 1).

**Tự đăng ký + email xác nhận: CÓ** (E5, §73 — 27/09/2026). Trang `/dang-ky` không cần đăng nhập:
họ tên, email, số điện thoại, mật khẩu, "biết TopHSA từ đâu" (danh mục §51, máy chủ trả), trường /
lớp / mục tiêu (không bắt buộc). Máy chủ gửi thư xác nhận (hộp thư đi §61, mã băm trong
`password_reset_tokens.purpose='verify'`, hạn 72 giờ, dùng một lần, đi trong `#…`).

**Tài khoản chưa bấm thư là tài khoản chết**: `LoginView` chặn `self_registered AND NOT is_verified`
(tài khoản trung tâm cấp không đổi hành vi), và dòng `yeu_cau` chỉ sinh ra KHI ĐÃ xác nhận — hộp
việc của học vụ không có rác. Không lộ ai có tài khoản: email trùng, số điện thoại trùng, quá trần
đều nhận CÙNG một câu 200.

**Hàng chờ "Đăng ký mới" = hộp Yêu cầu (§65)**, loại `tk_dang_ky` — không dựng hộp mới. Học vụ mở
yêu cầu → Duyệt → chọn lớp → "Duyệt và thực hiện" xếp em vào lớp trong MỘT giao dịch
(`yeu_cau/thuc_thi.py`, qua `_ghi_thanh_vien` nên trần lớp gia sư vẫn nguyên); duyệt hai lần chỉ xếp
một lần. Mốc "Tự đăng ký tài khoản trên website" + "Xác nhận địa chỉ email" lên dòng thời gian của em.

Bằng chứng: `backend/accounts/tu_dang_ky.py`, `backend/accounts/tests_tu_dang_ky.py` (28 phép kiểm),
`scripts/do_dang_ky.mjs` (20/20 bước ĐẠT, 27/09/2026).

**Demo**: mở `/dang-ky` ở cửa sổ ẩn danh → điền phiếu → Gửi → thử đăng nhập ngay (bị chặn, có nút
"Gửi lại thư xác nhận") → mở đường dẫn trong thư → "Đã xác nhận email" → đăng nhập được → học vụ →
Yêu cầu thấy "Đăng ký mới: <tên em>" → Duyệt → chọn lớp → Duyệt và thực hiện.

Phân rã chi tiết (bổ sung 27/09/2026 — trước đây dòng này chỉ có đoạn văn trên):

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Đăng nhập bằng email / số điện thoại / tên đăng nhập | CÓ | một ô nhận cả ba (§51) — `backend/accounts/views.py:60` |
| Hiện / ẩn mật khẩu, ghi nhớ đăng nhập | CÓ | nút mắt ở ô mật khẩu; tick ghi nhớ = phiên **30 ngày**, không tick = hết khi đóng trình duyệt (`backend/accounts/ghi_nho.py:32`) |
| Quên mật khẩu | CÓ | đường dẫn DÙNG MỘT LẦN, hạn **30 phút**, chỉ gửi tới email của chính tài khoản (`backend/accounts/quen_mat_khau.py:60`, `:115`) |
| Đăng xuất | CÓ | `backend/accounts/views.py:273`, thu hồi phiên |
| Đăng nhập bằng Google / Facebook | CÓ — **bảng không kê** | `backend/accounts/oauth.py:24`, tuyến `backend/config/urls.py:49`; email trùng tài khoản thường thì tự LIÊN KẾT chứ không tạo tài khoản thứ hai |
| Học sinh tự đăng ký trên website | CÓ (E5, §73) | trang `/dang-ky` không cần đăng nhập; `backend/accounts/tu_dang_ky.py` |
| Thư xác nhận email | CÓ | mã băm trong `password_reset_tokens.purpose='verify'`, hạn **72 giờ**, dùng một lần (`backend/accounts/tu_dang_ky.py:83`, `:175`) |
| Tài khoản chưa bấm thư thì không vào được | CÓ | `LoginView` chặn `self_registered AND NOT is_verified` (`backend/accounts/views.py:157`); tài khoản trung tâm cấp không đổi hành vi |
| Không lộ ai đã có tài khoản | CÓ | email trùng, số điện thoại trùng, quá trần đều nhận CÙNG một câu 200; trần theo máy ở `backend/accounts/tu_dang_ky.py:207` |
| Hàng chờ xếp lớp cho em mới đăng ký | CÓ — dùng lại hộp Yêu cầu | loại `tk_dang_ky`, chỉ hệ thống sinh ra (`backend/yeu_cau/loai.py:51`), chỉ học vụ / quản trị thấy (`:56`); duyệt xếp em vào lớp trong MỘT giao dịch (`backend/yeu_cau/thuc_thi.py:202`) |
| Dòng thời gian ghi mốc tự đăng ký + xác nhận email | CÓ | nhật ký `user.self_register` / `user.verify_email`, hai mốc chứ không một — xem dòng 4 |

## Dòng 27 — Học sinh · thông báo · CÓ (sửa nhãn 27/09: §61 + chuông buổi mới đã đóng cả bốn ô)

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| Thay đổi lịch, bài tập mới, kết quả | CÓ (`lich_doi`, `assignment_new`, `assignment_graded`) | — |
| Lịch học (buổi mới) | **CÓ** | **27/09** — chuông `buoi_moi` khi lịch lớp có buổi mới. Tạo lẻ một buổi thì nói đúng ngày giờ buổi ấy; **sinh lịch cả kỳ thì MỘT chuông nói số buổi**, không phải mỗi buổi một chuông (12–30 chuông trong một giây thì cái thứ hai đã đủ làm em thôi đọc chuông nữa). Em đã rời lớp không nhận; buổi tạo sẵn ở trạng thái huỷ không báo. Bộ kiểm 5/5. |
| Thông báo từ trung tâm | **CÓ** | §61 — học vụ soạn và gửi ở `/quan-tri/thong-bao` (11/11 bước đo được); học viên đọc ở `/thong-bao` (12/12 bước). |
| Đánh dấu đã đọc / chưa đọc | **CÓ** | Trang `/thong-bao`: đánh dấu đã đọc **và chưa đọc** từng dòng, đo được số trên ô lọc tụt 24 → 23 rồi về lại 24. |

## Dòng 28 — Học sinh · chương trình + lộ trình · CÓ khi lớp đã nhận khung (sửa nhãn 27/09)

| Ý trong bảng | Trạng thái | Việc đóng |
|---|---|---|
| Buổi tham gia / vắng / muộn (số đếm) | CÓ ("Lớp của tôi") | — |
| Lịch sử điểm danh từng buổi, tổng số buổi | CÓ (V-d) | `GET /api/lop-cua-toi` → `lop[].diemDanh` (`teaching/lop_cua_toi.py`, cùng `_buoi_cua_em` với chuyên cần); thẻ "Lớp của bạn" → "Điểm danh từng buổi" (`components/LopCuaToi.tsx`). Demo: học viên → Trang của tôi → thẻ lớp → mở "Điểm danh từng buổi" |
| % hoàn thành chương trình, bài / chuyên đề đã / chưa, tiến độ theo môn | CÓ (E1) | "Lớp của tôi": "Đã học X% chương trình" — chỉ buổi em có mặt / muộn, buổi bù tính cho buổi gốc; tờ phụ huynh cùng dòng |
| So sánh thực tế với kế hoạch | CÓ (E1) | cùng dòng: "(kế hoạch tới nay: Y%)" |

## Dòng 29 — Học sinh · record · MỘT PHẦN (sửa nhãn 27/09: §72 đã mở phần xem lại; danh sách đủ + ô tìm thì chưa)

Câu cũ (25/09, giữ theo RULES §29): "CHƯA → V-l, E4 — danh sách record theo buổi, tìm kiếm, đã xem /
chưa xem (**V-l**), % đã xem cho TG (**E4** — thử trên tài khoản Zoom thật trước: Zoom chỉ trả tên
người xem khi người xem đăng nhập Zoom)". §72 (26/09) đã mở phần em xem lại; phần danh sách đủ và ô
tìm thì dò lại 27/09 vẫn chưa có.

Phân rã chi tiết (bổ sung 27/09/2026 — trước đây dòng này không có bảng phân rã):

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Em mở lại được bản ghi buổi đã học | CÓ (§72) | thẻ lớp hiện "Xem lại: 24/09 22/09" (`frontend/src/components/LopCuaToi.tsx:400`), dữ liệu từ `backend/teaching/lop_cua_toi.py:107` |
| Đánh dấu "đã xem" | CÓ | bảng `recording_views`, cửa `backend/teaching/ban_ghi.py:71` (`GhiLuotMoView`); tuyến `backend/teaching/urls.py:97`. Lưu ý: "đã MỞ" chứ không phải "đã xem hết" — bản ghi nằm trên Zoom, ngoài tầm đo |
| **Danh sách bản ghi theo buổi (đủ, không chỉ mấy buổi cuối)** | **CHƯA** — sửa ô 27/09 | thẻ lớp chỉ lấy **4 bản ghi gần nhất** (`backend/teaching/lop_cua_toi.py:44` `SO_BAN_GHI = 4`); không tuyến nào và không màn nào của em liệt kê đủ. Lớp học ba tháng thì buổi thứ năm trở về trước em không còn đường mở lại |
| **Tìm kiếm bản ghi** | **CHƯA** | không ô tìm nào ở phía em; `lop_cua_toi.py` không nhận tham số tìm |
| Em báo "không mở được bản ghi" | CÓ (§72) | nút "Không mở được?" trên thẻ lớp → `backend/teaching/ban_ghi.py:211` (`BaoLoiBanGhiView`); chuông gộp nói rõ mấy em báo. Chỗ nhận báo (chuông hay hộp Yêu cầu) còn chờ anh chốt — **K4** |
| Bản ghi TỰ vào buổi từ Zoom | CHƯA → E4 | hôm nay trợ giảng / học vụ dán link tay vào buổi (`class_sessions.recording_url`); chờ khoá Zoom của anh |
| % đã xem cho trợ giảng | MỘT PHẦN | đếm được "ai đã MỞ" (`backend/teaching/ban_ghi.py:99`, xem dòng 22); % thời lượng đã xem thì Zoom mới trả được, và chỉ khi em đăng nhập Zoom → E4 |

## Dòng 30 — Học sinh · học liệu · CÓ liên kết ngoài (sửa nhãn 27/09: §60 xong 27/09, nhãn "CHƯA → Đ2 §60" là chưa cập nhật)

Phân rã chi tiết (bổ sung 27/09/2026 — trước đây dòng này không có bảng phân rã):

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Em thấy tài liệu giảng viên gắn cho lớp | CÓ (§60) | thẻ lớp hiện tên tài liệu kèm tên miền (`frontend/src/components/LopCuaToi.tsx:418`), dữ liệu từ `backend/teaching/lop_cua_toi.py:123` |
| Tài liệu gắn theo BUỔI, không chỉ theo lớp | CÓ | `hoc_lieu.session_id` — để trống là kho chung của lớp (`backend/teaching/hoc_lieu.py:120`) |
| Giảng viên ẩn / hiện theo tiến độ | CÓ | cột `hoc_lieu.an`; em chỉ thấy `NOT an` (`backend/teaching/lop_cua_toi.py:128`) |
| Tài liệu của buổi bù không lộ cho cả lớp | CÓ — có chủ ý | cùng hàng rào `thuoc_buoi` với bản ghi (`backend/teaching/lop_cua_toi.py:137`) |
| Mở tài liệu an toàn | CÓ | mở tab mới có `noopener`; địa chỉ `javascript:` bị từ chối kèm câu lỗi tiếng Việt cạnh đúng ô (`backend/teaching/hoc_lieu.py`, bộ kiểm 27/27, 7/7 đột biến bị giết) |
| **Danh sách tài liệu đủ của lớp / lọc theo buổi (phía em)** | **CHƯA** — ghi rõ 27/09 | thẻ lớp chỉ lấy **4 tài liệu gần nhất** (`backend/teaching/lop_cua_toi.py:48` `SO_HOC_LIEU = 4`). Nhân sự có danh sách đủ (`backend/teaching/hoc_lieu.py:120` trả hết), em thì không |
| Tải TỆP thẳng lên (không phải liên kết) | CHƯA → D1 | chờ khoá R2; lược đồ đã chừa sẵn `hoc_lieu.nguon='r2'` |

## Dòng 31 — Học sinh · bài tập · CÓ (nộp chữ)

Nhận bài, làm và nộp, xem kết quả + nhận xét: CÓ (`/bai-tap`, chuông). Nộp chữ; nộp tệp → **Đ2 §60** (nay là **D1**, chờ khoá R2).

Phân rã chi tiết (bổ sung 27/09/2026 — trước đây dòng này không có bảng phân rã):

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Em thấy bài được giao cho mình | CÓ | `backend/teaching/assignments.py:924` (`MyAssignmentsView`); bài giao cho một nhóm em thì em ngoài nhóm không thấy (V-e, `backend/teaching/nhan_bai.py`) |
| Chuông khi có bài mới, khi bài đã chấm | CÓ | loại `assignment_new` / `assignment_graded` (`backend/notifications/loai.py:17-18`) |
| **Nhắc trước khi hết hạn nộp** | CÓ — **bảng không kê, hệ thống tự làm** | quét mỗi nhịp, bài còn **20–28 giờ** tới hạn mà em chưa nộp thì một chuông + một thư (`backend/notifications/nhac_han.py:35`, `:58`); tôn trọng ô tắt nhắc của em. **Lỗi mã đang mở**: loại này chưa có nhãn tiếng Việt nên trên trang Thông báo nó hiện là "Khác" — xem `docs/agent/BAO_CAO_PHAN_RA.md` |
| Nộp bài | CÓ — **chỉ nộp chữ** | `backend/teaching/assignments.py:962`, ghi `submissions.content` (`:998`); không đường nào ghi `file_url` từ phía em |
| Xem điểm, nhận xét của giảng viên | CÓ | `backend/teaching/assignments.py:943` trả `score`, `feedback`, `graded_at` |
| Học xong khoá vẫn xem lại được bài và nhận xét | CÓ — có chủ ý | đường ĐỌC không lọc `left_at` (`backend/teaching/assignments.py:924`, chú thích nêu rõ lý do và §29); đường NỘP thì vẫn chặn em đã rời lớp |
| Bài kiểm tra trên lớp không bị tính là "chưa nộp" | CÓ (V-h) | em không nộp được (409) và không vào mẫu số; `submissions.absent` (§62f) |
| Nộp bằng TỆP | CHƯA → D1 | như dòng 17, chờ khoá R2 |

## Dòng 32 — Học sinh · trao đổi · CÓ (E3, 26/09/2026 — chờ khách xem)

Mục "Hỏi & yêu cầu" trên thanh học viên (`/yeu-cau`): "Hỏi giảng viên" (tới GV + TG của lớp em —
GV lớp khác không thấy, test `test_hoi_dap_toi_gv_lop_minh_khong_toi_gv_lop_khac`), "Hỗ trợ học tập
/ lịch / kỹ thuật / tài khoản" (tới học vụ), báo lỗi bản ghi một buổi, xin thay đổi (dòng 12). Em chỉ
thấy yêu cầu mình gửi, không thấy ghi chú nội bộ; trả lời tiếp được khi yêu cầu còn mở; rút được khi
còn "Mới". Diễn đàn và trợ lý AI giữ nguyên.

**Demo**: học viên → "Hỏi & yêu cầu" → "Hỏi giảng viên" → Gửi. Trợ giảng lớp → Yêu cầu → trả lời.
Học viên mở lại: thấy trả lời, gõ tiếp một câu.

Phân rã chi tiết (bổ sung 27/09/2026 — trước đây dòng này chỉ có đoạn văn trên):

| Ý trong bảng | Trạng thái | Bằng chứng / việc đóng |
|---|---|---|
| Em hỏi giảng viên của lớp mình | CÓ | `backend/yeu_cau/views.py:78`; giảng viên lớp khác KHÔNG thấy — test `test_hoi_dap_toi_gv_lop_minh_khong_toi_gv_lop_khac` |
| Em gửi yêu cầu hỗ trợ học tập / lịch / kỹ thuật / tài khoản | CÓ | loại mở cho nguồn `hoc_vien` khai ở `backend/yeu_cau/loai.py:140`; "hỗ trợ tài khoản" thì giảng viên / trợ giảng thôi thấy |
| Em xin thay đổi (chuyển lớp, bảo lưu, nghỉ, học bù…) | CÓ | xem dòng 12; duyệt là hệ thống tự làm (`backend/yeu_cau/thuc_thi.py:202`) |
| Em báo lỗi bản ghi một buổi | CÓ (§72) | `backend/teaching/ban_ghi.py:211` |
| Trả lời tiếp trong một yêu cầu còn mở | CÓ | `backend/yeu_cau/views.py:130` (`HocVienTraLoiView`) |
| Rút yêu cầu khi còn "Mới" | CÓ | `backend/yeu_cau/views.py:142` (`HocVienHuyView`); bảng chuyển trạng thái hợp lệ ở `backend/yeu_cau/loai.py:82` |
| Em chỉ thấy yêu cầu của mình | CÓ | phạm vi theo `NguoiLam`; test `backend/yeu_cau/tests_yeu_cau.py` (36) |
| Em KHÔNG thấy ghi chú nội bộ của trung tâm | CÓ — đã đo | `scripts/do_yeu_cau.mjs` 17/17 bước, đo bằng chuột |
| Chuông khi trung tâm trả lời | CÓ | `backend/yeu_cau/dich_vu.py:517` |
| Diễn đàn, trợ lý AI | CÓ — giữ nguyên, **bảng không kê** | xem mục "Ngoài bảng" ở cuối tài liệu |

## * Phân hệ thông báo chung · CÓ phần nền, còn thiếu hai loại chuông (viết lại 27/09/2026)

**Câu cũ (25/09) giữ theo RULES §29**: "Có: chuông + email cho đổi / huỷ lịch, bài tập mới, bài đã
chấm. Thiếu: lịch mới, học bù, hạn nộp, nghỉ học, cảnh báo tiến độ, thông báo trung tâm; gửi theo lớp /
môn / nhóm / cá nhân; chưa đọc; lịch sử đầy đủ (nay 30 dòng gần nhất). Nền cho gửi tin cậy: hộp thư đi
(outbox) — hiện thư gửi trên luồng rời, lỗi chỉ ghi log."

**Dò lại 27/09: bảy trên tám thứ ấy đã xong, câu trên không còn đúng một chỗ nào ngoài hai loại
chuông.** Đây là ô dễ nói sai nhất khi trình bày với khách, nên liệt bằng bảng:

| Việc trong câu cũ | Hôm nay | Bằng chứng |
|---|---|---|
| Chuông "lịch mới" | CÓ (27/09) | loại `buoi_moi` (`backend/notifications/loai.py:26`), gộp cả kỳ thành MỘT chuông (`backend/teaching/bao_doi_lich.py:153`) |
| Chuông "học bù" | CÓ | loại `hoc_bu` (`backend/notifications/loai.py:25`), gửi sau khi lưu buổi bù (`backend/teaching/buoi_bu.py`) |
| Nhắc "hạn nộp" | CÓ | quét tự động 20–28 giờ trước hạn (`backend/notifications/nhac_han.py:35`), nối vào nhịp ở `backend/notifications/hop_thu.py:350` |
| Báo "nghỉ học" | CÓ một nửa | người XIN nghỉ nhận chuông khi được duyệt (`backend/yeu_cau/dich_vu.py:705`); **giảng viên của lớp thì KHÔNG được báo** — đó là nửa còn thiếu |
| Thông báo trung tâm | CÓ (§61) | `backend/notifications/thong_bao.py:107` (soạn) + `:113` (gửi); màn `/quan-tri/thong-bao`, đo 11/11 bước |
| Gửi theo lớp / môn / nhóm chọn tay / cá nhân | CÓ | `announcements.audience` nhận `classIds` / `courseIds` / `userIds` (`backend/notifications/thong_bao.py:67`) |
| Lọc "chưa đọc", đánh dấu đã / chưa đọc | CÓ | `backend/notifications/views.py:95` |
| Lịch sử đầy đủ, không còn trần 30 dòng | CÓ | phân trang THEO KHOÁ `id` giảm dần, không trùng không sót (`backend/notifications/views.py:95`); trần cũ 30 dòng chỉ còn là trang đầu của panel chuông |
| Hộp thư đi (nền gửi tin cậy) | CÓ (§61a) | `backend/notifications/hop_thu.py:120` xếp dòng trong CÙNG giao dịch với việc chính; thử lại có giãn cách **1 / 5 / 30 / 120 / 360 phút** (`:75`); việc gấp đi trước việc hàng loạt (`:84`). Sáu mô-đun đang dùng: quên mật khẩu, tự đăng ký, nhắc hạn, thông báo trung tâm, báo đổi lịch, gửi báo cáo phụ huynh |
| Cảnh báo tiến độ bằng chuông | **CHƯA** — còn lại thật | hệ thống TÍNH được lớp chậm tiến độ (`backend/chuong_trinh/tien_do.py:107`) và hiện ở "Toàn trung tâm" + chip lớp, nhưng không loại chuông nào đẩy nó tới người; không mã nào gửi |

---

## Ngoài bảng — tính năng hệ thống có mà bảng phân rã không kê (27/09/2026)

Anh Sơn 27/09: *"bảng phân rã còn thiếu nhiều tính năng đấy"*. Mục này là chiều NGƯỢC với cả tài liệu
trên: không phải "bảng đòi gì mình có chưa", mà **"mình có gì mà bảng không nhắc tới"** — thứ buổi demo
nên nói ra, vì khách không biết để hỏi.

Cách soát: đi theo 16 miền trong `scripts/so_mien.json` và `docs/CAU_TRUC_MA.md`, mở từng mô-đun rồi
đối chiếu với 32 dòng của bảng. **Chỉ ghi thứ đã mở mã ra xác minh trong lượt 27/09** — không lấy từ
chú thích hay từ trí nhớ; thứ nào chỉ có bảng trong CSDL mà chưa có mã thì KHÔNG nằm ở đây (xem ô "phụ
huynh tự tắt nhận báo cáo" ở dòng 23 — đó là nửa tính năng, không phải tính năng).

| Tính năng | Vai nào dùng | Bằng chứng `tệp:dòng` |
|---|---|---|
| **Đưa lịch học sang Google Calendar / Lịch iPhone / Outlook** bằng một địa chỉ lịch riêng: dán một lần, buổi mới / buổi dời / buổi huỷ tự về máy. Địa chỉ chỉ hiện MỘT lần (máy chủ giữ băm), thu hồi được | mọi vai — học viên thấy lớp mình đang học, giảng viên / trợ giảng thấy buổi mình phụ trách, quản trị thấy cả trung tâm | `backend/lich/views.py:62` (cấp / thu hồi), `:95` (tệp `.ics`), `backend/lich/doc.py:22` (quyền nằm TRONG câu SQL), `backend/lich/chia.py:35`, `frontend/src/components/ThemVaoLich.tsx:9` |
| **Tự nhắc em sắp hết hạn nộp bài** — quét mỗi nhịp, bài còn 20–28 giờ tới hạn mà em chưa nộp thì một chuông + một thư; một lần duy nhất kể cả khi hai nhịp chồng nhau | học viên | `backend/notifications/nhac_han.py:35`, `:58`; nối vào nhịp ở `backend/notifications/hop_thu.py:350` |
| **Hộp thư đi bền**: thư xếp một dòng trong CÙNG giao dịch với việc chính (việc cuộn lại thì không có thư về một việc không xảy ra), luồng nền gửi, thử lại giãn cách 1 / 5 / 30 / 120 / 360 phút, việc gấp đi trước việc hàng loạt, trần gửi hàng loạt theo ngày | nền cho mọi thư của mọi vai | `backend/notifications/hop_thu.py:120` (xếp), `:75` (giãn cách), `:84` (ưu tiên), `:88` (trần ngày), `:251` (gửi một việc) |
| **Hàng rào chặn thư ra địa chỉ thật khi chạy trên máy thử** — CSDL dev là bản chép của production nên trong đó có email thật; hàng rào chỉ cho thư đi tới địa chỉ thử | nền (bảo vệ học viên / phụ huynh thật) | `backend/notifications/hang_rao_thu.py:108`, `:98` |
| **Kênh Zalo ZNS đã đấu sẵn trong hộp thư đi** — cùng một cửa với email, chờ Zalo OA của TopHSA thì bật được, không phải viết lại | phụ huynh (khi có khoá) | `backend/notifications/hop_thu.py:239`, `backend/teaching/parent_send.py:309` |
| **Nhãn tiếng Việt cho từng loại chuông do MÁY CHỦ trả**, màn hình không gõ lại danh mục; thêm loại chuông mà quên nhãn thì phép kiểm đỏ ngay | mọi vai | `backend/notifications/loai.py:17`, `backend/notifications/views.py:62`, phép kiểm `backend/notifications/tests_loai.py` |
| **Mỗi người tự bật / tắt nhận thư, nhắc học, tin nội dung** | mọi vai | `backend/notifications/views.py:13`; `nhac_han` tôn trọng ô này (`backend/notifications/nhac_han.py:47`) |
| **"Việc hôm nay"** — một bảng mở đầu ngày: buổi sắp tới, buổi chưa điểm danh, bài chưa chấm quá 5 ngày, em vắng liền ≥ 2 buổi, em cần chú ý, em được đánh dấu cần hỗ trợ, yêu cầu đang mở | giảng viên, trợ giảng, học vụ, quản trị — mỗi vai chỉ thấy lớp của mình | `backend/teaching/viec_hom_nay.py:247`, phạm vi ở `:62`, ngưỡng ở `:52` |
| **Cảnh báo trùng giảng viên / trùng phòng / trùng lớp / trùng học viên** khi xếp lịch — cảnh báo chứ không chặn, và kiểm cả một loạt buổi khi sinh lịch cả kỳ | học vụ, giảng viên | `backend/teaching/trung_lich.py:32` (một buổi), `:83` (cả loạt), `:136` (câu cảnh báo) |
| **Gợi ý ngày lễ cố định** để bỏ ra khi sinh lịch cả kỳ | học vụ | `backend/teaching/ngay_le.py:23` |
| **Đợt học + ngày nghỉ của đợt** — một tầng, cố ý: "đợt 1/2027 so với đợt 2/2027" trả lời được mà không phải đọc tên lớp | quản trị, học vụ | `backend/teaching/terms.py:110` (đợt), `:250` (ngày nghỉ của đợt), lý do ở `:1` |
| **Lớp gia sư** — trần 3 em, có lịch riêng; trần ấy được giữ ở MỌI cửa xếp em vào lớp, kể cả khi hệ thống tự xếp lúc duyệt yêu cầu | học vụ, quản trị | `backend/teaching/lop_gia_su.py:59`, trần ở `:90` (`TRAN_GIA_SU`) |
| **Dán liên hệ phụ huynh cho CẢ LỚP** — nhập từ tệp đăng ký học vụ đang giữ, xem trước từng dòng rồi mới ghi | giảng viên, học vụ | `backend/teaching/lien_he_phu_huynh.py:302`, lý do ở `:1` |
| **Gửi tờ báo cáo phụ huynh cho cả lớp** — hệ thống soạn sẵn, NGƯỜI bấm gửi (anh Sơn chốt 07/09); hai bước là hai phương thức khác nhau có chủ ý | giảng viên, học vụ | `backend/teaching/parent_send.py:146`, cửa gửi `:306` |
| **Báo cáo CẢ LỚP dạng PDF** mang đi họp, có biểu đồ — khác hai tệp CSV (CSV để lọc / tính, PDF để đọc) | giảng viên, học vụ | `backend/teaching/bao_cao_lop_pdf.py:1`, tuyến `backend/teaching/exports.py:814` |
| **Đọc tờ PDF "Báo cáo kết quả thi" của hệ thống khảo thí ngoài thành dữ liệu** — hệ thống ấy không có API, anh Sơn 15/09 nói "chỉ xem được trên web" | học vụ, quản trị | `backend/teaching/nhap_ket_qua_thi.py:1`, cửa `backend/teaching/nhap_ket_qua_view.py:241` (đọc thử), `:272` (ghi) |
| **Cơ sở tính học phí theo em** (buổi đã học / có mặt / vắng) — dừng đúng ở mức "cơ sở", không làm sổ tiền | **chỉ quản trị viên** | `backend/teaching/co_so_hoc_phi.py:114` (`IsAdminRole`), lý do ở `:1` |
| **Nhật ký "ai đã làm gì"** toàn hệ thống, lọc được | **chỉ quản trị viên** (học vụ có bản rút gọn theo từng lớp — xem dòng 4) | `backend/teaching/admin_users.py:985`, màn `/quan-tri/nhat-ky` |
| **Màn "Ai làm được gì"** — bảng quyền nhìn thấy được, để học vụ trả lời được cho giảng viên mới mà không phải đi hỏi quản trị viên | quản trị, học vụ | `frontend/src/app/(standalone)/quan-tri/vai-tro/page.tsx:6`, tab ở `frontend/src/app/(standalone)/quan-tri/vai.ts:87` |
| **Hướng dẫn vận hành NGAY TRONG ứng dụng**, in ra được, xếp theo VIỆC chứ theo màn hình, lọc theo vai — **18 bài**, mỗi bài có mục "hỏng thì sao"; đường dẫn trong bài được phép kiểm đối chiếu với tuyến thật nên không thể dạy sai lặng lẽ | mọi vai (`/huong-dan`); bản đầy đủ cho quản trị + học vụ | `frontend/src/lib/huongDan.ts:1` (18 mục `tieu_de`), `frontend/src/app/(standalone)/quan-tri/huong-dan/page.tsx:7`, phép kiểm `frontend/e2e/unit/huong-dan.test.mjs` |
| **Xem trước "Hệ thống sẽ làm gì"** trước khi duyệt một yêu cầu — một lượt ĐỌC, không ghi gì | học vụ, quản trị | `backend/yeu_cau/thuc_thi.py:129` (xem trước), `:202` (thực hiện) |
| **Sổ loại yêu cầu có máy trạng thái viết ra thành bảng**: nguồn (học viên / phụ huynh / trợ giảng / giảng viên / học vụ), loại nào nguồn nào được tạo, chuyển trạng thái nào là hợp lệ và AI được làm | học vụ, giảng viên, trợ giảng | `backend/yeu_cau/loai.py:68` (nguồn), `:82` (bảng chuyển), `:110` (đổi loại), `:140` (nguồn nào tạo loại nào), `:150` (liên lạc phụ huynh ẩn với trợ giảng) |
| **Ghi tệp .xlsx qua MỘT cửa duy nhất**: ô chữ không bao giờ bị Excel hiểu thành công thức (cùng bộ ký tự với bản `.csv`) | mọi vai tải tệp | `backend/common/bangtinh.py:1`, `backend/teaching/exports.py` |
| **Đăng nhập bằng Google / Facebook** — email trùng một tài khoản thường thì tự LIÊN KẾT, không tạo tài khoản thứ hai | mọi vai | `backend/accounts/oauth.py:24`, tuyến `backend/config/urls.py:49` |
| **Cả khu học trực tuyến** mà bảng chỉ nhắc đúng một câu "diễn đàn và trợ lý AI": khoá + bài học + trắc nghiệm ôn, lộ trình học, sổ điểm, bản đồ năng lực theo chủ đề, nhật ký + kế hoạch học, nhiệm vụ hằng ngày + XP + bảng xếp hạng, diễn đàn, trợ lý AI | học viên | sổ điểm `backend/stats/views.py:412`, năng lực `:366`, nhiệm vụ `:151`, kế hoạch `:480`; `backend/roadmap/views.py`, `backend/achievements/views.py`, `backend/leaderboard/views.py`, `backend/forum/views.py`, `backend/chatbot/views.py`, `backend/quizzes/views.py` |

**Ba thứ CỐ Ý không kê ở đây**, để lần sau khỏi đi tìm lại: (1) bảng `parent_report_optout` §50 — lược
đồ có, mã không (xem dòng 23); (2) thi thử trực tuyến — đã tháo tuyến, miền đóng băng
(`scripts/so_mien.json` miền `thi_cu`); (3) chuông cảnh báo tiến độ — tính được nhưng không ai gửi
(xem mục thông báo chung ở trên).
