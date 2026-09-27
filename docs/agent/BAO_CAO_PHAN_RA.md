# Soát bảng phân rã TopHSA — lượt 27/09/2026

Nguồn việc: anh Sơn 27/09/2026 — *"bảng phân rã còn thiếu nhiều tính năng đấy. Và phần nhắn TopHSA cứ
tạm thời bỏ qua, trước mắt cứ tập trung hoàn thiện bản mock production này đã để mình có sản phẩm demo
đưa họ."*

Tệp đã sửa: **chỉ** `docs/NGHIEM_THU_TOPHSA.md` (và tệp báo cáo này). Không chạm mã, không chạm
`docs/VIEC_CUA_ANH.md`, không dựng máy chủ nào.

Mọi con số dưới đây đo ngày **27/09/2026** trên worktree `agent/pr` (gốc `198dc81`), bằng cách mở mã
ra đọc — không lấy từ chú thích cũ, vì chính chú thích cũ là chỗ sai nhiều nhất trong lượt này.

---

## V1 · Dòng thiếu mục phân rã chi tiết

Bảng tóm tắt có **32 dòng** + một dòng `*` (phân hệ thông báo chung). Đếm mục `## Dòng NN — …` bên
dưới: **31 mục**, vì các dòng 1 / 8 / 13 / 19 gộp thành một mục "Tài khoản" — chủ ý cũ, giữ nguyên.

Nên không dòng nào **thiếu hẳn** một mục. Cái thiếu là thứ khác và nặng hơn: **chín dòng có tiêu đề
mục nhưng KHÔNG có bảng phân rã ba cột nào**, tức đọc mục ấy không biết bảng của khách đòi mấy ý và ý
nào đã xong. Một trong chín dòng — **dòng 30** — chỉ có đúng một dòng tiêu đề, bên dưới không một chữ.

| Dòng | Trước lượt này | Đã bổ sung |
|---|---|---|
| 7 — Kế toán · học phí | 4 câu văn | 6 ý |
| 17 — Giáo viên · giao bài | một khối văn dài | 10 ý |
| 23 — Phụ huynh · tài khoản | 2 câu văn | 8 ý |
| 25 — Phụ huynh · gửi yêu cầu | một khối văn + demo | 9 ý |
| 26 — Học sinh · tài khoản | một khối văn + demo | 11 ý |
| 29 — Học sinh · record | 2 câu văn | 7 ý |
| **30 — Học sinh · học liệu** | **CHỈ có tiêu đề, trống hoàn toàn** | 7 ý |
| 31 — Học sinh · bài tập | 1 câu văn | 7 ý |
| 32 — Học sinh · trao đổi | một khối văn + demo | 10 ý |

Tổng **75 ý mới**, mỗi ý một ô bằng chứng `tệp:dòng`. Câu văn cũ giữ nguyên bên trên bảng mới
(RULES §29) — không xoá dòng của người trước, chỉ thêm và ghi rõ chỗ nào đã hết đúng.

Số bảng ba cột trong tài liệu: **19 → 28**. Số dòng tệp: **439 → 633**.

---

## V2 · Tính năng hệ thống CÓ mà bảng của khách không kê

Mục mới ở cuối tài liệu: `## Ngoài bảng — tính năng hệ thống có mà bảng phân rã không kê (27/09/2026)`.
Cách soát: đi theo 16 miền trong `scripts/so_mien.json`, mở từng mô-đun, đối chiếu với 32 dòng.

**25 tính năng** đã tự xác minh trong mã, mỗi dòng có vai dùng + bằng chứng `tệp:dòng`. Những cái đáng
nói nhất ở buổi demo:

1. **Đưa lịch học sang Google Calendar / Lịch iPhone / Outlook** bằng một địa chỉ lịch riêng (§71) —
   `backend/lich/views.py:62,95`, `backend/lich/doc.py:22`. Quyền nằm TRONG câu SQL, không lọc ở
   Python sau khi đã lấy về. Bảng của khách không có một chữ nào về việc này.
2. **Tự nhắc em sắp hết hạn nộp bài** (20–28 giờ trước hạn, một lần duy nhất kể cả khi hai nhịp chồng
   nhau) — `backend/notifications/nhac_han.py:35,58`.
3. **Hộp thư đi bền** với thử lại giãn cách 1 / 5 / 30 / 120 / 360 phút và ưu tiên việc gấp trước việc
   hàng loạt — `backend/notifications/hop_thu.py:75,84,120`. Sáu mô-đun đang đi qua nó.
4. **Hàng rào chặn thư ra địa chỉ thật trên máy thử** — `backend/notifications/hang_rao_thu.py:98,108`.
   Đây là thứ giữ cho luật "chỉ gửi tới địa chỉ thử" không phụ thuộc vào việc ai còn nhớ.
5. **Hướng dẫn vận hành ngay trong ứng dụng, 18 bài, in ra được, lọc theo vai**, mỗi bài có mục "hỏng
   thì sao"; đường dẫn trong bài được phép kiểm đối chiếu với tuyến thật nên không dạy sai lặng lẽ —
   `frontend/src/lib/huongDan.ts:1`, `frontend/e2e/unit/huong-dan.test.mjs`.
6. **Đọc tờ PDF kết quả thi của hệ thống khảo thí ngoài thành dữ liệu** —
   `backend/teaching/nhap_ket_qua_thi.py:1`, `backend/teaching/nhap_ket_qua_view.py:241,272`.
7. **Cả khu học trực tuyến** mà bảng chỉ nhắc đúng một câu "diễn đàn và trợ lý AI": khoá + bài học +
   trắc nghiệm ôn, lộ trình, sổ điểm, bản đồ năng lực, nhật ký + kế hoạch học, nhiệm vụ + XP + bảng
   xếp hạng — `backend/stats/views.py:151,366,412,480` và sáu mô-đun cùng miền.

Còn lại: xem trước "Hệ thống sẽ làm gì" trước khi duyệt, sổ loại yêu cầu có máy trạng thái viết thành
bảng, "Việc hôm nay", cảnh báo trùng lịch, gợi ý ngày lễ, đợt học + ngày nghỉ của đợt, lớp gia sư trần
3 em, dán liên hệ phụ huynh cả lớp, gửi tờ báo cáo cả lớp, báo cáo lớp PDF, cơ sở học phí, nhật ký
"ai đã làm gì", màn "Ai làm được gì", cài đặt nhận tin của từng người, nhãn loại chuông do máy chủ
trả, ghi .xlsx không biến ô chữ thành công thức, đăng nhập Google / Facebook, kênh Zalo ZNS đã đấu
sẵn chờ khoá.

**Ba thứ CỐ Ý không kê** (ghi luôn trong tài liệu để lần sau khỏi đi tìm lại):
`parent_report_optout` §50 (lược đồ có, mã không), thi thử trực tuyến (miền đóng băng, đã tháo tuyến),
chuông cảnh báo tiến độ (tính được nhưng không ai gửi).

---

## V3 · Ô bảng đòi mà thực ra chưa có, hoặc chỉ có cho một vai

### 3.1 · Mười ba tiêu đề mục ghi nhãn đã lỗi

Bảng tóm tắt được cập nhật sau các lượt đo 26–27/09, tiêu đề mục chi tiết thì không. Người đọc tài
liệu từ trên xuống gặp "Dòng 27 · MỘT PHẦN" ở tiêu đề trong khi bảng tóm tắt ngay trên đã ghi "CÓ" kèm
12/12 bước đo — đúng loại mâu thuẫn làm khách thôi tin cả tài liệu. Đã sửa cho khớp, mỗi tiêu đề nói
rõ sửa ngày nào và vì cái gì đóng:

dòng 9, 12, 14, 16, 17, 18, 21, 22, 24, 27, 28 (nhãn nâng lên CÓ) và dòng 29, 30 (nhãn "CHƯA" đã lỗi —
xem 3.3, 3.4).

### 3.2 · Dòng 17 "Chỉnh sửa bài tập" — ô ghi CHƯA mà mã làm được

Tài liệu ghi (26/09): *"sau khi đã giao, màn của giảng viên chỉ gửi được hai thứ — đổi người nhận và
đóng/mở bài (`AssignmentsClient.tsx:176, 238` — đo 26/09, không có lời gọi nào mang `title`/`dueAt`/
thang điểm)."*

Đo lại 27/09: **sai**. Màn giảng viên có form sửa đầy đủ —
`frontend/src/app/(standalone)/giang-day/bai-tap/[classId]/AssignmentsClient.tsx:457` (tên bài),
`:471` (hạn nộp), `:478` (thang điểm), gửi `PATCH` mang `title` / `due_at` / `max_score` ở `:232`, thân
khai ở `:54`, vào cửa backend `backend/teaching/assignments.py:549`. Bảng tóm tắt đã ghi "**Sửa bài**
(26/09)" nhưng mục chi tiết không được sửa theo. Đã sửa, giữ nguyên câu cũ bên dưới để còn tra lịch sử.

### 3.3 · Dòng 29 "Học sinh · record" — bảng tóm tắt ghi CÓ là quá tay

Bảng của khách đòi *"danh sách record theo buổi, tìm kiếm, đã xem / chưa xem"*. Đo 27/09:

* em mở lại bản ghi được, và hệ thống ghi nhận "đã mở" — CÓ (§72,
  `backend/teaching/ban_ghi.py:71`, `frontend/src/components/LopCuaToi.tsx:400`);
* **danh sách đủ: KHÔNG**. Thẻ lớp chỉ lấy **4 bản ghi gần nhất** —
  `backend/teaching/lop_cua_toi.py:44` (`SO_BAN_GHI = 4`). Không tuyến nào và không màn nào của học
  viên liệt kê đủ bản ghi theo buổi. Lớp học ba tháng thì buổi thứ năm trở về trước em không còn
  đường nào mở lại;
* **ô tìm: KHÔNG**. `lop_cua_toi.py` không nhận tham số tìm nào.

→ đã sửa ô tóm tắt **CÓ → MỘT PHẦN**, ghi rõ hai thứ còn thiếu và con số 4.

### 3.4 · Dòng 30 "Học sinh · học liệu" — giữ CÓ nhưng phải nói trần 4

Cùng một chỗ, cùng một lý do: `backend/teaching/lop_cua_toi.py:48` (`SO_HOC_LIEU = 4`). Nhân sự có
danh sách đủ (`backend/teaching/hoc_lieu.py:120` trả hết), học viên thì chỉ thấy 4 tài liệu mới nhất.
Lớp ba tháng thì tài liệu buổi đầu rơi khỏi thẻ. Đã thêm lưu ý vào ô tóm tắt và vào bảng chi tiết;
giữ nhãn "CÓ (liên kết ngoài)" vì anh Sơn chốt làm liên kết ngoài trước.

### 3.5 · Mục `*` "Phân hệ thông báo chung" — gần như toàn bộ đã lỗi

Câu cũ (25/09) liệt tám thứ còn thiếu và một câu về nền gửi. Đo 27/09 thì **bảy trên tám đã xong**, và
câu về nền thì ngược hẳn với thực tế:

| Câu cũ nói thiếu | Thực tế 27/09 |
|---|---|
| lịch mới | CÓ — `buoi_moi` (`backend/notifications/loai.py:26`), gộp cả kỳ thành MỘT chuông (`backend/teaching/bao_doi_lich.py:153`) |
| học bù | CÓ — `hoc_bu` (`loai.py:25`) |
| hạn nộp | CÓ — `backend/notifications/nhac_han.py:35` |
| nghỉ học | CÓ một nửa — người xin nhận chuông khi được duyệt (`backend/yeu_cau/dich_vu.py:705`); giảng viên của lớp thì KHÔNG |
| thông báo trung tâm | CÓ — `backend/notifications/thong_bao.py:107,113` |
| gửi theo lớp / môn / nhóm / cá nhân | CÓ — `announcements.audience` nhận `classIds` / `courseIds` / `userIds` (`thong_bao.py:67`) |
| chưa đọc | CÓ — `backend/notifications/views.py:95` |
| lịch sử đầy đủ (trần 30 dòng) | CÓ — phân trang theo khoá `id`, không trùng không sót (`views.py:95`) |
| *"hộp thư đi: hiện thư gửi trên luồng rời, lỗi chỉ ghi log"* | **ngược hẳn** — hộp thư đi đã dựng và sáu mô-đun đang dùng (`backend/notifications/hop_thu.py:120`) |

Còn thiếu thật: **chuông cảnh báo tiến độ**. Hệ thống TÍNH được lớp chậm tiến độ
(`backend/chuong_trinh/tien_do.py:107`) và hiện ở "Toàn trung tâm" + chip lớp, nhưng không loại chuông
nào đẩy nó tới người. Mục đã viết lại thành bảng, câu cũ giữ nguyên bên trên.

### 3.6 · Ba ô "CÓ" mà chỉ MỘT vai dùng được

Tiền lệ đã có trong tài liệu (hộp "Tải danh sách" chỉ quản trị viên thấy). Dò 27/09 thấy thêm hai chỗ
cùng họ, đã ghi vào bảng chi tiết dòng 7:

| Cửa | Quyền thật | Hệ quả |
|---|---|---|
| Tải danh sách tài khoản (.xlsx / .csv) | `IsAdminRole` — `backend/teaching/exports.py:732` | học vụ mở CÙNG trang Tài khoản thì không có hộp ấy |
| Cơ sở tính học phí | `IsAdminRole` — `backend/teaching/co_so_hoc_phi.py:114`; tab chỉ liệt vai quản trị (`frontend/src/app/(standalone)/quan-tri/vai.ts:74`) | học vụ không xem được, trong khi học vụ là người làm việc hằng ngày với học phí |
| Nhật ký "ai đã làm gì" | `IsAdminRole` — `backend/teaching/admin_users.py:985`; tab ở `vai.ts:81` | học vụ chỉ có bản rút gọn theo từng lớp (`IsAdminOrAcademic`, dòng 4) |

Cả ba cùng một câu hỏi: **C8 — học vụ được xem tới đâu**. Không tự đổi quyền; đây là quyết định của
anh, không phải việc viết thêm mã.

---

## V4 · Dòng 5 "Điều kiện hoàn thành"

Đã dò `grep -rn "hoan_thanh\|completion\|nguong" backend` rồi mở từng chỗ.

**Hiện có bốn ngưỡng bằng số, và KHÔNG ngưỡng nào là "hoàn thành khoá":**

| Ngưỡng | Con số | Ở đâu | Dùng để làm gì |
|---|---|---|---|
| Lớp chậm tiến độ | trễ ≥ **2** buổi khung HOẶC xong < **80 %** phần phải xong tới hôm nay | `backend/chuong_trinh/tu_vung.py:34-35` | chip đỏ ở Lớp học, ô ở Toàn trung tâm |
| Vắng liền / chấm muộn | vắng liền ≥ **2** buổi; bài chấm quá **5** ngày | `backend/teaching/viec_hom_nay.py:52,54` | "Việc hôm nay" |
| Không hoạt động | **7 / 14 / 30** ngày | `backend/teaching/overview.py:85` | Toàn trung tâm |
| Chủ đề yếu | dưới **60** điểm | `backend/teaching/reports.py:75`, `parent_report.py:50` | chọn chủ đề ôn lại |

Chú thích ngay tại `chuong_trinh/tu_vung.py:29-33` tự nói ra rằng hai số 2 và 80 % là **GIẢ ĐỊNH của
mình về cách TopHSA quản lớp**, để lộ ra để còn bàn lại — chưa phải con số của khách.

**"Đã học xong" hôm nay do NGƯỜI chọn, không do máy tính:** tình trạng `da_hoc_xong` được suy ra khi
lượt học gần nhất của em đóng với lý do "học xong" (`class_members.leave_reason = 'completed'`,
`backend/teaching/vocab.py:44`), hoặc khi lớp đã qua ngày kết thúc mà em chưa bị cho rời
(`backend/teaching/tinh_trang.py:64`). Tức hệ thống ghi được *kết luận*, chưa *kiểm* được điều kiện.

**Còn cần của anh Sơn — ba con số** (gom lại ở mục cuối).

---

## Việc còn sót trong lượt này

* Chưa mở màn thật trong trình duyệt. Việc này chỉ đọc mã và sửa một tài liệu, và brief yêu cầu không
  dựng máy chủ; các con số "đo màn thật" trong tài liệu là của những lượt trước, giữ nguyên, không
  thêm số mới nào tự nhận là đã đo màn.
* Mục `Dòng 1, 8, 13, 19` vẫn gộp. Nếu khách soi theo từng STT thì cần tách bốn mục; chưa tách vì bốn
  dòng ấy là CÙNG một bộ tính năng và khách đã nghiệm thu dòng 1 + 2.
* Chưa soát bảng chi tiết dòng 2, 3, 4, 5, 6, 10, 11, 20 xem còn ô nào ghi quá tay — lượt này dồn vào
  chín dòng không có bảng và mục `*`. Đây là việc còn lại rõ ràng nhất cho lượt sau.
* Cột H của bảng khách: không đụng, theo brief.

---

## LỖI MÃ phát hiện — KHÔNG tự vá, lead xử

### L1 · Chuông "Sắp hết hạn nộp" hiện nhãn "Khác" trên màn học viên

Loại chuông `nhac_han` **không có trong sổ nhãn**. Đo bằng lệnh, không suy:

```
>>> from notifications import loai
>>> loai.nhan('nhac_han')
'Khác'
>>> 'nhac_han' in loai.NHAN,  'nhac_han' in loai.GUI_NOI_KHAC
(False, False)
```

* thiếu ở `backend/notifications/loai.py:17` (dict `NHAN`) và cũng không có ngoại lệ ở `:33`
  (`GUI_NOI_KHAC`);
* màn hình lấy nhãn từ máy chủ (`backend/notifications/views.py:62`, `:108`), nên ô lọc của trang
  Thông báo và panel chuông đều hiện **"Khác"** cho lời nhắc hạn nộp;
* **vì sao phép kiểm không bắt**: `backend/notifications/tests_loai.py` quét bằng AST các lời gọi
  `notify` / `gui` / `gui_sau_commit`, còn `nhac_han` ghi THẲNG vào `notifications` bằng một câu
  `INSERT` (`backend/notifications/nhac_han.py:64`) để một lượt quét là một câu lệnh. Thước không
  thấy cửa này — đúng cái bẫy mà chính `loai.py:33` dựng `GUI_NOI_KHAC` để bịt, nhưng `nhac_han`
  chưa được ghim vào đó.

Hệ quả cho buổi demo: dòng "Sắp hết hạn nộp: …" trên trang Thông báo của học viên mang nhãn "Khác", và
ô lọc có một mục "Khác" không ai hiểu. Đây là loại chuông TỰ ĐỘNG, tức nó sẽ xuất hiện mà không cần ai
bấm gì.

Đề nghị (một dòng nhãn + một dòng ghim thước, không đổi hành vi): thêm `'nhac_han': 'Nhắc hạn nộp'` vào
`NHAN`, và ghim `nhac_han.LOAI` trong `tests_loai.py` như `thong_bao.LOAI` đang được ghim ở `:158`.

### L2 · Bảng `parent_report_optout` §50 — lược đồ có, không mã nào dùng

`grep -rn "parent_report_optout"` trên cả repo cho đúng **bốn** kết quả, không một kết quả nào là mã
chạy: `backend/sql/legacy_schema.sql:1645` (tạo bảng), `:1651` (chỉ mục),
`backend/common/management/commands/kiem_luoc_do.py:167-168` (dòng kiểm lược đồ).

Tức "phụ huynh từ chối nhận báo cáo" là **nửa tính năng**: bảng đứng đó, dòng kiểm xanh mỗi lượt
`kiem_luoc_do`, và không đường nào ghi hay đọc nó. Đúng cái bẫy mà `backend/teaching/terms.py:3` đã tự
kể là đã từng mắc với bảng `terms`. Không tự vá (đây là mã, và còn là câu hỏi nghiệp vụ: phụ huynh tắt
ở đâu, tắt cho một em hay mọi em). Đã ghi vào bảng chi tiết dòng 23 là CHƯA để không ai kể nó như một
tính năng đã có.

### L3 · Không phải lỗi, nhưng là khoảng trống có thể hỏng buổi demo

* **Cảnh báo tiến độ tính được mà không ai gửi**: `backend/chuong_trinh/tien_do.py:107` cho ra "lớp
  chậm tiến độ", hiện trên màn, nhưng không loại chuông nào đẩy tới giảng viên hay học vụ. Người
  không mở màn Toàn trung tâm thì không biết.
* **Duyệt "xin nghỉ học" không báo giảng viên của lớp**: `backend/yeu_cau/dich_vu.py:705` chỉ báo
  người GỬI. Giảng viên đứng lớp buổi ấy không nhận gì, trong khi điểm danh của em đã bị ghi đè thành
  "có phép".
* **Học viên chỉ thấy 4 bản ghi và 4 tài liệu gần nhất** (`backend/teaching/lop_cua_toi.py:44,48`).
  Nếu buổi demo dùng bộ dữ liệu mẫu có nhiều buổi, khách sẽ hỏi "còn các buổi trước đâu".

---

## CÂU HỎI CẦN ANH SƠN QUYẾT

**Q1 · "Hoàn thành khoá" là bao nhiêu?** (V4 — đang chặn ô cuối của dòng 5). Cần ba con số:

  a. **% buổi có mặt tối thiểu** để coi là hoàn thành (ví dụ 80 % số buổi của lớp)?
  b. **% chương trình tối thiểu** theo sổ đầu bài?
  c. **Có bắt buộc điểm bài kiểm tra** không, và nếu có thì ngưỡng nào?

  Kèm một câu hỏi về hành vi: khi em đủ ngưỡng thì hệ thống **tự** đánh "đã học xong", hay chỉ **gợi ý**
  cho học vụ bấm? Hôm nay hoàn toàn là người bấm, và đó là thứ khách sẽ hỏi "vậy máy làm gì".

**Q2 · Hai con số 2 buổi / 80 % của "lớp chậm tiến độ" có đúng cách TopHSA quản lớp không?**
  (`backend/chuong_trinh/tu_vung.py:34-35` — mình tự đặt, chú thích tại chỗ đã ghi là giả định). Nếu
  khách thấy lạ thì đây là hai số đổi rẻ nhất trong cả hệ thống, vì màn hình đọc chúng từ phản hồi chứ
  không gõ lại.

**Q3 · C8 — học vụ được xem tới đâu?** Ba cửa hôm nay chỉ quản trị viên vào được, và cả ba đều là
  việc hằng ngày của học vụ: tải danh sách tài khoản (`exports.py:732`), cơ sở tính học phí
  (`co_so_hoc_phi.py:114`), nhật ký toàn hệ thống (`admin_users.py:985`). Mở hay không mở là quyết
  định về QUYỀN — mở cửa đầu tiên là mở cả liên hệ phụ huynh của toàn trung tâm.

**Q4 · Phụ huynh tự tắt nhận báo cáo — còn làm không?** (L2). Bảng `parent_report_optout` §50 dựng từ
  lâu mà chưa có mã. Nếu còn làm thì cần biết: tắt ở đâu (một nút cuối tờ báo cáo?), tắt cho một em
  hay cho mọi em của phụ huynh ấy, và tắt rồi thì trung tâm thấy gì.

**Q5 · Chuông cảnh báo tiến độ gửi cho ai?** (L3). Giảng viên của lớp, học vụ, hay cả hai — và mấy
  ngày một lần? Gửi mỗi ngày một lần cho một lớp chậm suốt tháng là 30 chuông về cùng một việc.

**Q6 · Duyệt "xin nghỉ học" có báo giảng viên của lớp không?** Nghiêng về CÓ — điểm danh của em bị ghi
  đè thành "có phép" mà người đứng lớp không biết là chỗ dễ sinh tranh luận nhất về sau. Nhưng đó là
  một loại chuông mới, nên chờ anh.

**Q7 · Học viên có cần màn danh sách ĐỦ bản ghi + học liệu không?** (3.3, 3.4 — trần 4 hôm nay). Bảng
  của khách đòi "danh sách record theo buổi, tìm kiếm" ở dòng 29, nên nghiêng về CÓ, nhưng nó là một
  màn mới cho học viên chứ không phải một ô sửa.
