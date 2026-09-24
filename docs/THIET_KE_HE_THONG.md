# Thiết kế hệ thống TopHSA ERP (pe_hsa) — trang, vai trò, miền, hướng phát triển

Bản 25/09/2026. Dựng từ ĐO trên mã (graphify + `ban_do` + tầng vai mới), không từ trí nhớ; nguồn ngoài
ghi ở cuối. Đọc cùng: `docs/NGHIEM_THU_TOPHSA.md` (32 dòng khách nghiệm thu), `docs/KE_HOACH_TOPHSA_THU_NGHIEM_2026-09-24.md`
(kế hoạch v2), `docs/VAN_HANH.md` (deploy, lược đồ). Hai bản đồ sinh tự động đi kèm: `docs/BAN_DO_MA.md`
(graphify, mức tệp) và `docs/BAN_DO_VAI.md` (trang × vai × API).

## 0. Đọc nhanh

- **Hệ thống là gì**: một ERP cho trung tâm luyện thi HSA — vận hành lớp (lớp, lịch, điểm danh, bài tập, báo
  cáo) + nền học trực tuyến (bài học, lộ trình, bản đồ năng lực, trợ lý AI). Ba tầng: Next.js (Vercel) →
  Django + SQL thuần (Render) → Postgres (Neon).
- **Sáu vai + một cửa**: Quản trị viên (QT), Học vụ (HV), Giảng viên (GV), Trợ giảng (TG), Biên tập nội dung
  (BT), Học viên (HS); **Phụ huynh (PH) không có tài khoản** — vào bằng link riêng (anh chốt 25/09).
- **Điểm yếu cấu trúc số 1**: app `teaching` là cả ERP trong một khối (12.959 dòng mã ngoài test, 35 tệp, 645 cạnh hàm sang
  `common`). Mọi tính năng mới của bảng khách (khung chương trình, thông báo, yêu cầu, Zoom) sẽ phình thêm khối
  này nếu không đặt ranh giới NGAY bây giờ.
- **Điểm yếu cấu trúc số 2**: quyền và menu viết TAY ở 5 nơi (lớp quyền backend, `quyenVai.ts`, `khuTheoVai.ts`,
  tab `quan-tri/vai.ts`, `KhungGiangDay.tsx`) — lệch nhau là loại lỗi khách đã gặp (góp ý số 3: GV thấy nút Đăng
  ký). Đo 25/09: bản dò đầu báo 19 chỗ "trang cho vai vào mà API từ chối"; soi từng chỗ thì 16 là trang ĐÃ
  báo chặn đúng bằng mã API, 2 thiếu móc báo chặn (đã vá), 1 là chặn ở mức nút — thước chưa hiểu, không phải mã
  sai (mục 1.3). Rủi ro thật nằm ở chỗ 5 nơi viết tay có thể trôi xa nhau, không phải ở lỗ hổng hôm nay.
- **Hướng đi đề xuất** (mục 7): giữ monolith nhưng chia MIỀN (modular monolith); một SỔ QUYỀN duy nhất theo mô
  hình "năng lực × phạm vi" (học từ Moodle) sinh ra cả chặn API, menu, trang "Ai làm được gì" và phép kiểm; mỗi
  vai vào thẳng "Việc hôm nay" của mình; kênh tới phụ huynh là Zalo + link (đúng thói quen thị trường VN).

## 1. Hiện trạng đo được

### 1.1 Mã (graphify, 25/09 — chi tiết `docs/BAN_DO_MA.md`)

| Tầng | Nút / cạnh (mức hàm) | Mức tệp (bỏ test) | Nhận xét |
|---|---|---|---|
| Backend (Python) | 3.952 / 10.172, 195 cụm | 131 tệp, 445 cạnh tệp→tệp | không vòng import mức tệp; MỘT vòng giữa app `stats ↔ chatbot` — **đã phá 25/09** (S5: tín hiệu `stats.tin_hieu.nhat_ky_doi`), đo lại: 0 vòng |
| React (`frontend/src`) | 928 / 2.511, 48 cụm | 155 tệp, 467 cạnh | hub lành mạnh: `components/ui/*`, `lib/api.ts`, `lib/server-api.ts` |
| JS cũ (`public/static/js`) | 320 / 680, 25 cụm | 0 cạnh tệp→tệp | nối nhau qua biến toàn cục `window.*` — graphify không thấy; `ban_do` bắc 83 cạnh React → JS cũ |

**Nút trung tâm (god nodes)** backend: `q1` 556 cạnh, `x` 226, `q` 218 (lớp truy cập CSDL), `local_now` 209,
`local_today` 117 (đồng hồ giờ VN), `User` 103, `NguoiDungView` 77, `can_see_class` 46, `chia_muc` 44 (sổ lược đồ),
`chi_hoc_vien` 42. Đây là "hạt nhân dùng chung" đúng nghĩa — ổn định, ít đổi; không cần tách.

**Tệp lớn nhất của `teaching`** (dòng): `views.py` 1.026 · `sessions.py` 980 · `admin_users.py` 955 ·
`assignments.py` 850 · `exports.py` 745 · `reports.py` 731 · `overview.py` 729 · `du_lieu_mau.py` 725 ·
`parent_report.py` 672 · `bao_cao_pdf.py` 607. Frontend: `DashboardClient.tsx` 1.031, `AppShell.tsx` 671.

**Ma trận phụ thuộc giữa app** (số cạnh hàm): `teaching → common` 645, `teaching → accounts` 46,
`teaching → stats` 42, `teaching → courses` 16, `teaching → notifications` 8, `teaching → mockexam` 2;
`stats → common` 127; mọi app khác chỉ dựa `common`. Tức là: `common` là hạt nhân, `teaching` là cục ERP, phần
còn lại là sản phẩm học trực tuyến (bài học, lộ trình, năng lực, diễn đàn, trợ lý).

### 1.2 Chỗ nối giữa tầng (`ban_do`, 25/09)

403 nút, 1.324 cạnh: frontend → API 209 · tuyến → view 120 · view → lớp quyền 116 · view → bảng 698 · khoá
ngoại 75 · React → JS cũ 83. **0 lời gọi không khớp, 0 tuyến không ai gọi chưa có lý do, 0 cầu JS cũ gãy.**
(Graphify đo 23/09: 0 cạnh ở đúng ba chỗ nối này — lý do có `ban_do`.)

### 1.3 Tầng vai (mới — `docs/BAN_DO_VAI.md`)

32 trang. Cổng vai hiện có ở trang: khu Vận hành (`quan-tri/*`: QT+HV; Nhật ký + Cơ sở học phí: QT), Giáo trình
(QT+BT). Khu Giảng dạy (`giang-day/*`) **cố ý không chặn theo vai ở trang** (chú thích layout: chặn thật là
"người này có phụ trách LỚP ấy không", nằm ở API) — thay vào đó mỗi trang DỊCH mã API thành màn chặn
(`lib/chanTu.ts`: 403 → `data-chan="vai"` "Khu … dành cho …", 404 → "không thấy"), và `e2e/vai-tro-cong.spec.ts` canh.

Bản dò đầu (chưa hiểu `chanTu`) báo 19 chỗ lệch. Soi tay từng chỗ (25/09):
- 16: trang đã báo chặn theo vai đúng nghĩa qua `chanTu` — thước sai, không phải mã sai;
- 2: tờ từng em (`giang-day/bao-cao/[classId]/[userId]`) và bảng chấm (`giang-day/bai-tap/[classId]/[assignmentId]`)
  hiện câu lỗi của máy chủ nhưng KHÔNG gắn móc chặn → đã vá cùng ngày (thêm `data-chan={chanTu(...)}` + câu theo vai),
  e2e đỏ trên bản cũ, 22/22 sau vá;
- 1: HV ở Tài khoản — trang gọi 3 API chỉ-QT nhưng nút đã ẩn theo cờ `chiHocVien` máy chủ trả (chặn mức NÚT).

Thước nay hiểu `chanTu` + trang chuyển hướng, có danh sách "đã giải thích" kèm lý do → **0 chỗ lệch**; tắt phần
nhận `chanTu` thì nó báo lại 18 (thước còn đỏ được).

**Kết luận thiết kế**: hệ thống hôm nay dùng cổng khu "theo mã API" — đúng và an toàn, nhưng mỗi trang phải tự nhớ
gắn móc (2 trang đã quên). Luật ở mục 2.3 đưa việc ấy về MỘT chỗ.

## 2. Mô hình vai, năng lực, phạm vi

### 2.1 Vai (ai là ai)

| Vai | Ai | Đăng nhập | Phạm vi mặc định |
|---|---|---|---|
| QT Quản trị viên | chủ trung tâm, IT | tài khoản | toàn hệ thống |
| HV Học vụ (giáo vụ) | điều phối lớp, tuyển sinh | tài khoản | toàn trung tâm, CHỈ tài khoản Học viên |
| GV Giảng viên | người dạy | tài khoản | lớp mình phụ trách (+ buổi dạy thay — Đ2 §58) |
| TG Trợ giảng | hỗ trợ lớp | tài khoản | lớp được gán; không liên hệ PH, không xoá |
| BT Biên tập nội dung | soạn khoá, bài, khung chương trình | tài khoản | nội dung, không đụng con người |
| HS Học viên | người học | tài khoản (tự đăng ký = chờ xếp lớp — E5) | chính mình + lớp đang học |
| PH Phụ huynh | cha mẹ | **link riêng, không mật khẩu** (§66) | MỘT em, trong hạn link |
| (sau) Thành viên diễn đàn | người ngoài | tài khoản xác minh email | chỉ diễn đàn (Đ3) |

### 2.2 Năng lực × phạm vi (học từ Moodle)

Moodle không hỏi "anh là vai gì" mà hỏi "anh có NĂNG LỰC X ở PHẠM VI Y không" — vai chỉ là một gói năng lực,
gán ở một phạm vi (hệ thống → danh mục → khoá → hoạt động), phạm vi con kế thừa phạm vi cha. Áp về đây, phạm vi
tự nhiên là: **Trung tâm → Đợt → Lớp → Buổi**, cộng hai phạm vi riêng: **Bản thân** (HS) và **Link** (PH).

Hiện 6 lớp quyền DRF (`IsAdminRole`, `IsAdminOrAcademic`, `IsSeniorTeachingStaff`, `IsTeachingStaff`,
`IsContentEditor`, `IsCourseOwner`) + `can_see_class` là một phiên bản thô của đúng mô hình ấy: lớp quyền = gói
vai, `can_see_class` = phạm vi Lớp. Thiếu: tên năng lực (hiện ngầm trong tên lớp quyền), phạm vi Buổi (dạy thay),
phạm vi Link.

**Đề xuất — SỔ QUYỀN một nguồn** (`backend/common/so_quyen.py` + sinh ra JSON cho frontend):

```
NANG_LUC = {
  'lop.xem':               {'vai': [QT, HV, GV, TG], 'pham_vi': 'lop'},
  'lop.sua':               {'vai': [QT, HV],          'pham_vi': 'trung_tam'},
  'diem_danh.ghi':         {'vai': [QT, HV, GV, TG], 'pham_vi': 'lop'},
  'nhan_xet.ghi':          {'vai': [QT, HV, GV],     'pham_vi': 'lop'},      # V-a
  'lien_he_ph.xem':        {'vai': [QT, HV, GV],     'pham_vi': 'lop'},
  'bao_cao_ph.gui':        {'vai': [QT, HV, GV],     'pham_vi': 'lop'},
  'khung_ct.soan':         {'vai': [QT, HV, BT],     'pham_vi': 'trung_tam'}, # E1
  'so_dau_bai.ghi':        {'vai': [QT, HV, GV, TG], 'pham_vi': 'buoi'},     # E1
  'yeu_cau.duyet':         {'vai': [QT, HV],          'pham_vi': 'trung_tam'}, # E3
  'thong_bao.gui_lop':     {'vai': [QT, HV, GV],     'pham_vi': 'lop'},      # E2
  'thong_bao.gui_tt':      {'vai': [QT, HV],          'pham_vi': 'trung_tam'},
  'cham_cong.xem':         {'vai': [QT, HV],          'pham_vi': 'trung_tam'}, # V-o
  'tai_khoan.doi_vai':     {'vai': [QT],              'pham_vi': 'he_thong'},
  ...
}
```

Một sổ ấy SINH RA: (1) lớp quyền DRF `CoNangLuc('diem_danh.ghi')` + hàm phạm vi dùng lại `can_see_class`;
(2) menu mọi vai (mỗi mục menu khai năng lực nó cần); (3) trang "Ai làm được gì" (hết 7.500 ký tự gõ tay);
(4) phép kiểm ma trận quyền (`tests_ma_tran_quyen`) và G2. Không đập lại: bước 1 chỉ là sổ + lớp quyền mới cho
MỌI view MỚI (E1–E5, V); view cũ chuyển dần khi chạm tới. Sáu lớp quyền cũ trở thành bí danh của sổ.

### 2.3 Hai tầng chặn — luật

| Tầng | Hỏi gì | Ở đâu | Khi sai |
|---|---|---|---|
| Cổng KHU (thô) | vai này có được vào khu này không | `layout.tsx` của khu, đọc từ sổ quyền | trang "Khu này dành cho …" + đường về khu của mình |
| Cổng ĐỐI TƯỢNG (mịn) | năng lực X ở phạm vi của đối tượng này? | API (`CoNangLuc` + hàm phạm vi) | 404 (không lộ đối tượng tồn tại) / 403 |
| Nút | người này có làm được việc nút gọi không | máy chủ trả sẵn cờ năng lực theo đối tượng (vd `coTheSua`) | không vẽ nút |

Việc cụ thể: giữ cổng "theo mã API" hiện có (`chanTu` — đúng vì câu hỏi thật là phạm vi lớp), nhưng đưa móc chặn
về MỘT chỗ: một hàm dựng màn lỗi dùng chung cho mọi trang khu (thay vì mỗi trang tự viết `<main data-chan>` — hai
trang đã quên, vá 25/09); thêm cổng khu thô ở `layout.tsx` từ sổ quyền để HS/BT không thấy khung giảng dạy bao quanh
màn chặn. Nút đọc cờ năng lực máy chủ trả (đã đúng ở Tài khoản với `chiHocVien`); thước G2 có danh sách "đã giải
thích" cho chặn mức nút.

## 3. Trang theo vai (kiến trúc thông tin)

**Nguyên tắc** (NN/g + thực tế trung tâm): mỗi vai có MỘT trang đầu là **"Việc hôm nay"** — danh sách việc phải
làm, xếp theo mức gấp, mỗi dòng dẫn thẳng tới chỗ làm; sau đó 3–6 khu cấp một, đặt tên theo VIỆC của người ấy
(không theo bảng dữ liệu); cái hiếm dùng vào "Thêm". Menu SINH từ sổ quyền + một danh mục trang (`lib/khuTheoVai.ts`
mở rộng thành danh mục MỌI trang), không viết tay ở từng khung.

| Vai | Trang đầu ("Việc hôm nay" gồm) | Khu cấp một (✓ có · ◐ một phần · ✚ mới theo kế hoạch) |
|---|---|---|
| **HV** | yêu cầu chờ duyệt ✚E3 · đăng ký mới chờ xếp lớp ✚E5 · lớp chậm tiến độ ✚E1 · buổi chưa điểm danh ✓ · em vắng liền / lâu không vào ✓ · học phí sắp hết ✚V-m | Toàn trung tâm ✓ · Học viên ✓(1.4b) · Lớp học ✓ · Lịch học ✓ · Chương trình ✚E1 · Yêu cầu ✚E3 · Thông báo ✚E2 · Báo cáo ◐(✚V-k, V-o) · Hướng dẫn ✓ |
| **GV** | buổi hôm nay + chưa điểm danh ✓ · chưa ghi sổ đầu bài ✚E1 · bài chưa chấm ✓ · em cần chú ý ✓ · yêu cầu/câu hỏi của em ✚E3 | Lịch dạy ✓ · Lớp của tôi → (Buổi học + Sổ đầu bài ✚, Bài tập & kiểm tra ◐V-h, Học viên & tờ báo cáo ✓, Chương trình lớp ✚E1) · Thông báo lớp ✚E2 · Xem môn học ✓ |
| **TG** | như GV (đã có vắng liền/cần chú ý ✚V-b) + em chưa xem record ✚E4 + nhắc cần gửi ✚E2 | như GV, bỏ Báo cáo phụ huynh/liên hệ; thêm Record ✚E4 |
| **BT** | bài nháp · câu hỏi bị báo lỗi | Giáo trình ✓ · Khung chương trình ✚E1 |
| **HS** | buổi sắp tới + link phòng ✓ · bài đến hạn ✓ · record buổi vừa rồi ✚ · thông báo mới ✚E2 | Trang của tôi (lớp, lịch, tiến độ chương trình ✚E1) · Bài tập ✓ · Môn học ✓ · Record ✚ · Hỏi / Yêu cầu ✚E3 · Diễn đàn ✓ |
| **PH** (link) | lịch 14 ngày + thay đổi ✚§66 · điểm danh, bài tập, nhận xét ✓/◐ · tiến độ chương trình ✚E1 | một trang duy nhất + "Gửi yêu cầu" ✚E3 |
| **QT** | như HV + cảnh báo hệ thống (thư lỗi, lược đồ lệch) ✚E2/H | như HV + Nhật ký · Cơ sở học phí · Vai trò · Vận hành (sổ lược đồ, hộp thư đi) |

**Tầng JS cũ** (Trang của tôi, Môn học — `dashboard.js`/`main.js`, 6.449 dòng, chỉ được co): đích là khu học viên
bằng React; mỗi lần chạm một mục HS thì dời mục ấy sang React thay vì vá JS cũ.

## 4. Miền backend (modular monolith)

Ngoài: "gom những thứ ĐỔI CÙNG NHAU vào một mô-đun; phép thử: một thay đổi nghiệp vụ điển hình chỉ chạm MỘT
mô-đun; hệ cỡ này thường 4–10 mô-đun; mỗi mô-đun sở hữu bảng của nó, mô-đun khác đi qua hàm dịch vụ chứ không
ghi thẳng bảng". Áp vào `teaching`:

| Miền (thư mục đích) | Sở hữu bảng | Tệp hiện tại | Hàm dịch vụ công khai (ví dụ) |
|---|---|---|---|
| `lop_hoc` | `classes`, `class_members`, `terms` | `views.py` (phần lớp), `chuyen_lop.py`, `lop_gia_su.py`, `terms.py` | `chuyen_lop()`, `them_hoc_vien()`, `roi_lop()` |
| `lich` | `class_sessions`, `session_participants` | `sessions.py` (phần buổi), `sinh_buoi.py`, `trung_lich.py`, `lich.py`, `ngay_le.py` | `tao_buoi()`, `tao_buoi_bu()`, `tim_trung()` |
| `diem_danh` | `attendance`, `attendance_history` | `sessions.py` (phần điểm danh), `attendance.py` | `ghi_diem_danh()`, `ti_le()` |
| `bai_tap` | `assignments`, `submissions`, `assignment_targets` | `assignments.py` | `giao_bai()`, `cham()` |
| `chuong_trinh` ✚E1 | `syllabi*`, `session_logs*` | mới | `nhan_khung()`, `tien_do_lop()`, `tien_do_em()` |
| `bao_cao` | (chỉ đọc) | `reports.py`, `overview.py`, `exports.py`, `bao_cao_*pdf.py`, `co_so_hoc_phi.py` | đọc qua dịch vụ các miền trên |
| `phu_huynh` | `parent_report_*` | `parent_report.py`, `parent_link.py`, `parent_send.py`, `lien_he_phu_huynh.py`, `thu_bao_cao.py` | `dung_bao_cao()`, `cap_link()` |
| `ho_so` | cột hồ sơ trên `users` | `ho_so.py`, `admin_users.py`, `dong_thoi_gian.py` | `cap_tai_khoan()`, `dong_thoi_gian()` |
| `yeu_cau` ✚E3 | `yeu_cau*` | mới | `tao()`, `duyet()` — gọi `lop_hoc.chuyen_lop()`, `lich.tao_buoi_bu()` |
| `thong_bao` ✚E2 | `notifications`, `announcements`, `outbox` | `notifications/`, `bao_doi_lich.py` | `gui()` / `gui_sau_commit()` (đã có, `60d33a9`) |

**Luật**: (1) miền MỚI (E1, E2, E3, E4) là thư mục riêng ngay từ đầu, không vào `teaching/views.py`; (2) miền
khác chỉ gọi hàm dịch vụ, không `UPDATE` bảng của miền khác; (3) việc phụ (thông báo, cache quyền, nhật ký) đi
SAU commit qua `gui_sau_commit` / `on_commit`; (4) tách tệp cũ chỉ khi đang sửa chính chỗ ấy ("chạm đâu dọn đó"),
ưu tiên theo điểm nối cao (`views.py`, `sessions.py`, `admin_users.py`); (5) không vòng giữa miền — `stats ↔ chatbot` đã phá 25/09 bằng tín hiệu (`stats` báo, `chatbot` nghe).

Khoá ngoại giữa miền: GIỮ (một CSDL, một nhóm người, một lần deploy — tách CSDL là giá của microservice mà
trung tâm này không cần); chỉ cấm GHI chéo miền.

## 5. Luồng then chốt

1. **Mở lớp → dạy → tiến độ**: HV tạo lớp (✓) → nhận khung chương trình (✚E1) → sinh buổi (✓) → GV/TG điểm danh
   (✓) + ghi sổ đầu bài (✚E1) → tiến độ lớp/em tính sống (✚E1) → lớp chậm → "Việc hôm nay" HV + thông báo
   (✚E2) → tờ phụ huynh có dòng tiến độ.
2. **Yêu cầu → duyệt → thực thi**: HS/PH/TG gửi (✚E3) → HV duyệt trong MỘT giao dịch → gọi dịch vụ miền (chuyển
   lớp, tạo buổi bù, bảo lưu) → dòng thời gian em + thông báo người gửi (sau commit).
3. **Tự đăng ký → xếp lớp**: đăng ký + xác nhận email (✚E5) → hàng chờ "Đăng ký mới" của HV, nguồn = "Tự đăng
   ký" → xếp lớp → môn mở (cổng `truy_cap`, ✓).
4. **Record Zoom**: buổi có link Zoom (✓) → webhook `recording.completed` (✚E4) → gắn record vào buổi → HS mở qua
   đường ghi nhận (✚) → TG thấy ai chưa xem → nhắc (✚E2).
5. **Tin tới phụ huynh**: sự kiện (điểm danh, tiến độ, báo cáo kỳ) → hộp thư đi (outbox, ✚E2) → email / Zalo
   ZNS theo MẪU đã duyệt (chờ OA) → link theo dõi (✚§66). Thị trường VN đi đúng đường này (Zalo ngay sau buổi học).

## 6. Hạ tầng và vận hành (đã có / đang có)

- Nhánh: làm trên `erp` (thử nghiệm, Preview Vercel tự dựng); `master` = production, chỉ anh gộp.
- Lược đồ: `legacy_schema.sql` + **sổ mục lược đồ** (H3, `9c484f6`): mỗi mục một giao dịch, chỉ chạy mục mới/đổi
  và mọi mục sau nó; mục dữ liệu gắn `-- chạy: mỗi lượt`. `kiem_luoc_do` đối chiếu thực tế.
- Cổng kiểm trước khi đẩy (H6): ruff, tsc, eslint, guard, `ban_do --kiem` (~1 phút).
- Chưa có tiền → nối sẵn, bật bằng biến: Render Starter, Neon Launch (khôi phục 7 ngày), Sentry, UptimeRobot, R2,
  Zalo OA. Giữ máy chủ thức + chạy việc nền: luồng trong tiến trình + máy gọi ngoài miễn phí (T6).

## 7. Hướng phát triển

**Đối chiếu thị trường** (phần mềm quản lý trung tâm ở VN — DotB EMS, Eduspace, OMT CenterOnline): gói chuẩn =
lớp + điểm danh + kết quả + **học phí/công nợ** + **CRM tuyển sinh** + **thông báo phụ huynh qua Zalo/ZNS** + app
di động. pe_hsa khác ở chỗ sâu về HỌC (bài học trực tuyến, lộ trình, bản đồ năng lực HSA, trợ lý AI) — lợi thế
thật, vì các phần mềm kia dừng ở vận hành.

| Giai đoạn | Làm | Vì sao |
|---|---|---|
| Tới buổi khách xem | V (A1, A2), E1, 1.6 | vận hành lớp là ưu tiên số 1 của khách; E1 là thứ khách hỏi kỹ nhất |
| Ngay sau | E2 (outbox + thông báo + Zalo ZNS khi có OA), E3 (yêu cầu), link PH sống | kênh phụ huynh là thứ thị trường cạnh tranh; E3 đóng 5 dòng bảng |
| Tiếp | E4 Zoom, E5 tự đăng ký → **hàng chờ tuyển sinh** (CRM gọn: nguồn, người tư vấn, trạng thái), Đ2 (tài liệu R2, chấm công khoá tháng, dạy thay) | CRM gọn dựng trên E5 + hồ sơ (§51 đã có nguồn tuyển sinh, người tư vấn) |
| Sau | diễn đàn công khai (Đ3), PWA cho HS/PH (thông báo đẩy) thay app gốc | rẻ hơn app, dùng lại toàn bộ React |
| Không làm (đã chốt) | kế toán / học phí đầy đủ, tài khoản phụ huynh | chỉ một ô tình trạng học phí; phụ huynh qua link |

**Việc kiến trúc cụ thể** (thêm vào bảng theo dõi): **S1** sổ quyền một nguồn + `CoNangLuc` cho view mới ·
**S2** một hàm màn chặn dùng chung cho mọi trang khu + cổng khu thô ở `layout.tsx` từ sổ quyền (hai trang đã quên móc chặn, vá 25/09) · **S3** G2 thành guard: `ban_do --kiem` đỏ khi
trang/menu cho vai R mà API từ chối R, có chú thích nút ↔ API · **S4** miền mới là thư mục riêng (E1 `chuong_trinh`,
E2 `thong_bao`, E3 `yeu_cau`) · **S5** phá vòng `stats ↔ chatbot` · **S6** danh mục trang một nguồn sinh menu mọi
khung · **S7** graphify chạy lại mỗi mốc gộp, số god node / tệp lớn ghi PROGRESS (theo dõi `teaching` có co không).

## 8. Luật thiết kế (tóm)

1. Một nguồn cho quyền, một nguồn cho danh mục trang — mọi nơi khác SINH từ đó.
2. Hai tầng chặn: khu theo vai ở trang, đối tượng theo phạm vi ở API; nút đọc cờ năng lực máy chủ trả.
3. Mỗi vai vào "Việc hôm nay" của mình; khu đặt tên theo việc, không theo bảng.
4. Miền mới = thư mục mới + hàm dịch vụ; không ghi chéo bảng; việc phụ sau commit.
5. Phụ huynh: link + Zalo/email, không mật khẩu; mọi tin qua hộp thư đi.
6. Mỗi dòng bảng khách có kịch bản demo + e2e xanh mới báo "sẵn sàng nghiệm thu".
7. Đo trước khi tin: graphify/ban_do/tầng vai chạy lại ở mỗi mốc; số đo vào PROGRESS.

## Nguồn

- Đo trên mã: graphify (Graphify-Labs, chạy `graphify update` chế độ AST, không gọi mô hình) — `docs/BAN_DO_MA.md`;
  `scripts/ban_do.mjs` — `ban_do/BAO_CAO.md`; `scripts/tang_vai.py` — `docs/BAN_DO_VAI.md`.
- Moodle — Roles, capabilities, contexts: https://docs.moodle.org/502/en/Roles_FAQ ,
  https://moodledev.io/docs/5.0/apis/subsystems/roles
- Modular monolith / bounded contexts: https://milanjovanovic.tech/blog/module-boundaries-bounded-contexts ,
  https://makimo.com/blog/modular-monolith-in-django/ ,
  https://handbook.gitlab.com/handbook/engineering/architecture/design-documents/modular_monolith/decisions/002_bounded_contexts_definition
- Transactional outbox (Django): https://github.com/juntossomosmais/django-outbox-pattern
- Thị trường VN: https://dotb.vn/phan-mem-quan-ly-trung-tam-dao-tao/ , https://eduspace.vn/phan-mem-quan-ly-trung-tam ,
  https://emis.misa.vn/emis-kindergarten/phan-mem-quan-ly-trung-tam-nang-khieu/
- Giao diện theo vai: https://design.gitlab.com/patterns/navigation-sidebar/ , https://uxpilot.ai/blogs/dashboard-design-principles
