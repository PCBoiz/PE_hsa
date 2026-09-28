# Hướng giao diện — gọt chữ, giảm rối (26/09/2026)

Viết sau góp ý của chị phụ trách bên TopHSA ngày 23/09: *"giao diện đang hơi nhiều chữ, ngay màn hình đầu đã
khá nhiều thông tin nên đọc hơi rối, các bạn xem cân nhắc rút gọn và ưu tiên các thông tin/chức năng chính
để dễ nhìn hơn"*. Tệp này là LUẬT cho mục 1.6 và cho mọi màn mới, không phải gợi ý.

## 1. Số đo thật, không phải cảm tính (đo 26/09, khổ 1440, tài khoản thật đã đăng nhập)

| Màn | Số từ | Nút / liên kết | Ô số | Dòng dài hơn 12 từ | Chiều cao trang |
|---|---|---|---|---|---|
| Giảng dạy | **1.146** | **72** | 6 | **40** | 3.416 px (≈ 4 màn hình) |
| Vận hành · Tổng quan | 644 | **73** | **45** | 13 | 2.609 px |
| Học viên · Trang của tôi | 456 | 25 | 6 | 9 | 2.010 px |
| Lịch học | 250 | 20 | 0 | 1 | 1.455 px |

Cách đo: `scripts/do_mat_do_chu.mjs` — đếm trên `main` đã dựng xong, chỉ tính phần tử đang hiện.

## 2. Chuẩn bên ngoài đang dùng làm mốc

- **3–7 ô số ở phần trên màn**, vùng hiệu quả 5–9; **quá 12 là dấu hiệu một màn đang phục vụ nhiều loại
  người dùng và phải tách**. Màn Vận hành · Tổng quan đang có **45**.
- **Bóc lớp dần (progressive disclosure) ba tầng**: *Tổng quan* (vài con số) → *Ngữ cảnh* (mở ra khi cần) →
  *Chi tiết* (trang riêng). Người ta quét trước, đào sâu sau.
- Ngoại lệ hợp lệ: màn **giám sát vận hành** cần mật độ cao. Khi ấy giữ mật độ nhưng phải có cấu trúc —
  hàng gọn, ít khung viền, không thêm câu giải thích dài.

Nguồn: [Dashboard UI design](https://www.setproduct.com/blog/dashboard-ui-design) ·
[Progressive disclosure in SaaS dashboards](https://pixxen.com/progressive-disclosure-saas/) ·
[Dashboard design principles](https://www.aufaitux.com/blog/dashboard-design-principles/)

## 3. Luật gọt chữ (áp cho mọi màn)

1. **Mỗi màn có ĐÚNG MỘT việc chính.** Việc ấy là nút nổi bật duy nhất ở đầu màn. Mọi nút khác hạ xuống
   `ghost` hoặc đưa vào trang con.
2. **Câu giải thích dưới tiêu đề: bỏ, trừ khi nó ngăn được một lỗi.** "Lớp bạn hướng dẫn, và hồ sơ học tập
   của từng học viên" không ngăn lỗi nào — giảng viên biết mình đang ở đâu.
3. **Không câu nào dài quá 12 từ** trong nhãn, tiêu đề, ô trống. Câu dài chuyển thành: một cụm ngắn + phần
   "Vì sao?" bung ra khi bấm.
4. **Số đứng trước, nhãn đứng sau, và nhãn không quá 3 từ.** "0 ngày lại 7 ngày" là câu không đọc được —
   viết "7 ngày qua: 0 buổi".
5. **Ô số trên màn đầu: tối đa 6 cho mỗi vai.** Còn lại đưa xuống mục bung ra hoặc trang báo cáo.
6. **Một khái niệm một tên.** "Tổ hợp", "hợp phần" → **Môn học**. Bỏ chữ "Mọi …" trong ô lọc ("Mọi lớp" →
   "Tất cả lớp").
7. **Chỗ trống không phải chỗ để dạy.** Ô trống viết một dòng + một nút, không viết đoạn văn.
8. **Chữ giải thích cơ chế bên trong thì bỏ.** "Chưa ghi thì hệ thống không đoán, nên các em đó không nằm
   trong tỉ lệ giữ chân" là ghi chú dành cho người viết mã, không dành cho học vụ.

## 4. Áp vào từng màn (thứ tự nên làm)

**Giảng dạy** (nặng nhất: 1.146 từ, 72 nút, 40 câu dài)
- Việc chính: *vào lớp hôm nay*. Giữ một khối "Hôm nay" ở trên cùng: giờ bắt đầu – giờ kết thúc, tên lớp,
  nút "Vào phòng học".
- Khách đòi thêm, phải có: **giờ bắt đầu – giờ kết thúc**, **số buổi đã học / tổng số buổi khoá**,
  **nhận xét từng học sinh**.
- Bảng học viên: giữ 4 cột (Học viên · Tiến độ · Chuyên cần · Việc cần làm), các cột còn lại đưa vào trang
  chi tiết từng em. Nút "Xem" và "Báo cáo PH" gộp thành một cột cuối.
- Danh sách 6 lớp đang nối nhau bằng dấu "·" trong một dòng → xuống thành danh sách chọn.

**Vận hành · Tổng quan** (45 ô số)
- Chọn 6 ô cho học vụ: sĩ số đang học · buổi hôm nay · buổi chưa điểm danh · em vắng liên tiếp · lớp chậm
  tiến độ · học phí sắp hết. Phần còn lại xuống mục "Xem thêm" hoặc trang báo cáo.

**Học viên · Trang của tôi**
- Giữ: buổi kế tiếp, bài phải nộp, tiến độ lớp. Ba khối này trả lời đúng ba câu em mở trang ra để hỏi.
- Câu "Hệ thống đề xuất 8 bài · 1 đề · 250 phút mỗi tuần — còn 75 bài chưa học (chưa đặt mốc thi nên tạm
  tính 12 tuần)" → "Tuần này: 8 bài, 1 đề" + phần "Vì sao?" bung ra.

## 5. Kiểm lại bằng số, không bằng mắt

Sau khi gọt, chạy lại `scripts/do_mat_do_chu.mjs` và ghi bảng mới cạnh bảng cũ. Mục tiêu cho lượt này:

| Màn | Số từ | Ô số | Câu dài >12 từ |
|---|---|---|---|
| Giảng dạy | ≤ 450 | ≤ 6 | 0 |
| Vận hành · Tổng quan | ≤ 350 | ≤ 6 | 0 |
| Học viên · Trang của tôi | ≤ 300 | ≤ 6 | 0 |

Gọt chữ mà làm mất một chức năng thì KHÔNG đạt — `do_axe.mjs` phải giữ 0 vi phạm, `do_giao_dien.mjs` 0 mọi
luật, và các spec e2e sẵn có phải còn xanh (chúng tìm nút theo tên; đổi tên nút thì sửa spec trong cùng lượt).
