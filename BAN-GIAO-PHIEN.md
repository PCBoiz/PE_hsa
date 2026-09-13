# Bàn giao phiên — đọc tệp này đầu tiên khi mở phiên mới

*Cập nhật 13/09/2026. Viết để một phiên mới bắt kịp trong 5 phút mà không phải
đọc lại 5.800 dòng nhật ký. Cách làm học từ `BAN-GIAO-PHIEN.md` của dự án cô
Giang — chỉ học cách, không đụng bên ấy.*

---

## Bốn tệp cần biết

| Tệp | Là gì | Khi nào đọc |
|---|---|---|
| `PROGRESS.md` | Nhật ký. Khối "Đọc trước" ở đầu có **lệnh đang hiệu lực** của anh Sơn và trạng thái mới nhất. Mục mới ở TRÊN vạch `<!-- MỚI NHẤT -->`. | Trước khi bắt tay |
| `docs/VIEC_CUA_ANH.md` | Việc **chỉ anh Sơn** làm được — một bảng ở đầu, xếp theo mức chặn. | Khi cần hỏi anh hoặc báo cáo |
| `TODO.md` | Việc của tôi (backlog T1–T66…). | Khi hết việc đang làm |
| `BAO-CAO-TRANG-THAI.md` | Số đo tự sinh — chỉ đo, không nhận định. `python scripts/kiem_ke_san_pham.py --md BAO-CAO-TRANG-THAI.md` | Trước khi trích bất cứ con số nào |
| `RULES.md` | Tiêu chuẩn bắt buộc. §4 là cổng trước khi báo xong; §5 là luật chạm CSDL. | Trước mỗi commit |

## Cách làm việc đã chốt

- **Đo, không đoán.** Mọi con số báo ra phải do chính mình đo trên dữ liệu thật,
  kèm ngày. Bộ đo giao diện phải chạy `--tu-kiem` trước (nó đã nói dối 12 lần).
- **Test phải đỏ được.** Viết xong test → lùi mã → phải đỏ *đúng cái test ấy* →
  phục hồi → xanh. Lùi một phần mà vẫn xanh = test giả (đã mắc 07/09).
- **Neon là production thật.** SELECT thoải mái; ghi thì hỏi từng lần; DDL chỉ
  cộng thêm. Thử khô cuộn lại KHÔNG chứng minh lệnh chạy được — ràng buộc hoãn
  chỉ kiểm lúc COMMIT (đã mắc 07/09). Sao lưu ra tệp trước khi xoá.
- **Một con số chỉ tính ở một nơi.** Màn hình, CSV, PDF phải nói cùng một chuyện.
- **Đặt câu hỏi trước việc lớn.** Anh Sơn muốn được hỏi; nhưng câu hỏi phải kèm
  con số ĐÚNG — một lời gật xin bằng số sai không phải lời gật.
- **Kịch bản Python tạm: viết ra tệp, chạy `python -P tệp`. KHÔNG heredoc.**
  Heredoc đã phá ba lần: backtick bị bash diễn giải, `\x00` thành byte NUL thật,
  dấu nháy lẻ làm bash chờ vô tận. Cùng lý do: **không backtick trong thông
  điệp commit** trừ khi dùng `-F tệp`.

## Lệnh hay dùng

```
# máy chủ dev — --noreload là BẮT BUỘC, nên THÊM TUYẾN MỚI thì phải dừng rồi bật lại
# (không thì tuyến vừa viết trả 404 và trông như lỗi định tuyến)
cd backend  && ALLOWED_ORIGINS="http://localhost:3100" ./.venv/Scripts/python.exe manage.py runserver 9000 --noreload
cd frontend && npm run dev                              # cổng 3100

# cổng trước khi báo xong (RULES §4)
cd backend  && ./.venv/Scripts/python.exe -m ruff check .
cd backend  && ./.venv/Scripts/python.exe -m pytest -q  # ~29 phút, vào Neon thật
cd frontend && npm run lint && npx tsc --noEmit
python scripts/cap_the.py                               # thẻ 30 phút, không ghi CSDL
PE_TOKENS="D:\pe_hsa\.the\tokens_ad.json" node scripts/do_giao_dien.mjs --tu-kiem   # phải ĐẠT
PE_TOKENS="D:\pe_hsa\.the\tokens_ad.json" node scripts/do_giao_dien.mjs             # rồi đo thật

# xem trước / gửi thư báo cáo (App Password ở backend/.env, thuộc sonthaiha07@gmail.com)
EMAIL_CHE_DO_THU=1 python manage.py thu_email --toi ai@example.com
python manage.py thu_email --toi ai@example.com --lop 1 --em 9    # dữ liệu thật, chỉ đọc

# hồ sơ gửi TopHSA
python scripts/kiem_ke_san_pham.py --ra ho_so.json --md BAO-CAO-TRANG-THAI.md
cd frontend && node ../scripts/ho_so_tophsa.mjs ../ho_so.json "../docs/Ho so san pham PE_HSA.pdf"

# lược đồ: mục nào của legacy_schema.sql đã tới Neon (thêm § mới thì thêm dòng MUC)
cd backend  && ./.venv/Scripts/python.exe manage.py kiem_luoc_do

# trước MỖI commit — phải rỗng
git diff --cached --name-only | grep -i "\.env$"
```

`master` = deploy production ngay (Render autoDeploy). Gộp vào `master` khi anh
Sơn nói; hiện anh đã cho phép merge trực tiếp cho các đợt sửa. Đẩy `erp` tự do.

## Trạng thái ngay lúc bàn giao — 13/09/2026

- Production Render **sống nhưng ngủ đông**, thức dậy mất ~85 giây. Workflow giữ
  ấm trên GitHub **không có tác dụng** (GitHub chạy 3–5 giờ/lần, 8/8 thất bại);
  đã sửa cho đúng vai đồng hồ sức khoẻ. Giữ ấm thật = việc A1 của anh Sơn.
- CSDL: 5 tài khoản, 1 lớp, 1 đợt, 16 buổi đều ở tương lai (sinh 13/09), 0 lượt
  điểm danh — buổi mẫu cũ đã xoá có duyệt, sao lưu ở `.sao_luu/`. 0 em có liên
  lạc phụ huynh. Tài khoản `id 9` (kiểm thử) giữ >½ lịch sử học — chờ anh quyết.
- Cổng chất lượng lần cuối 13/09: `teaching` + `common` **267/267** pytest, bộ
  `accounts` + gửi báo cáo + đọc-của-người-khác 61/61, eslint/tsc/ruff sạch, ô
  nhập tràn khung 0 trên 14 trang × 2 khổ. **Chưa chạy lại** trọn bộ pytest mọi
  app (lần cuối 07/09: 453/453) và bộ đo giao diện `do_giao_dien.mjs` — làm
  trước khi báo một mốc lớn.
- Hồ sơ gửi TopHSA: `docs/Ho so san pham PE_HSA.pdf`, 26 trang, sinh bằng mã;
  ma trận quyền B.8 sửa 13/09 (ba ô sai).
- `master` = `erp`, đẩy sau mỗi vòng. 13/09 có bốn vòng: sao lưu CSDL · khai cổng
  60 view · email phụ huynh (ô Cài đặt + dán cả lớp) · sinh lịch cả kỳ + ngày nghỉ.

## Việc đang chờ, không ai làm được thay

Xem bảng đầu `docs/VIEC_CUA_ANH.md`. Bốn việc chặn: A1 giữ ấm · A2 bí mật proxy
(mọi người chung một xô đăng nhập) · A3 nhánh Neon cho CI (đang pytest thẳng
vào production) · B1 một lớp thật.

## Việc tôi làm tiếp được ngay (không cần anh)

*Xong 13/09:* ~~sao lưu CSDL tự động~~ (chờ A5) · ~~khai cổng tường minh 60
view~~ · ~~nhập liên hệ phụ huynh~~ · ~~sinh lịch cả kỳ + ngày nghỉ~~.

Còn lại, HỎI anh Sơn trước khi làm: bảng nhắc việc giảng viên (buổi chưa điểm
danh, bài chưa chấm, em vắng liền) → khoá liên hệ phụ huynh theo C5 nếu anh
chọn (b) → bộ nhập kết quả thi từ PDF (chờ B4) → T18 mức 2 (`zod` cho payload
màn quản trị). T40 (bộ đếm tần suất) nay chỉ còn là đặt `REDIS_URL` — mã đã sẵn.

## Bài học đắt nhất ba tuần qua

1. **Chú thích sai nguy hiểm ngang mã sai.** `gui()` ghi "không ném ngoại lệ"
   mà ném — một tên học viên có xuống dòng làm hỏng lượt gửi của 24 em còn lại.
2. **Bộ đo tự viết phải đối chiếu với bộ đo đã có** trước khi tin. Bộ kiểm kê
   đếm "0 đường chỉ cần đăng nhập" khi công cụ cũ đếm 60 — sai cách phân loại.
3. **Chạy trên dữ liệu thật lộ ra thứ dữ liệu mẫu giấu.** "Điểm thi thử trung
   bình: 0%" cho một em thi đúng một lần — số đúng, chữ sai.
4. **Mở tệp ra nhìn.** Ba lỗi bố cục PDF không hiện trong chữ trích xuất.
