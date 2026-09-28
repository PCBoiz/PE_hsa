# Kỹ năng của pe_hsa — và SOLID áp vào chúng thế nào

Mỗi thư mục con là một kỹ năng: một việc lặp đi lặp lại trong dự án này, viết ra
để agent nào vào cũng làm giống nhau. Anh Sơn 26/09: *"Áp dụng SOLID vào xây
dựng các Agent Skills"*.

SOLID sinh ra cho lớp và mô-đun, nhưng năm câu hỏi của nó hỏi được về bất cứ thứ
gì có ranh giới — và một kỹ năng thì có ranh giới. Đây là cách đọc chúng ở đây,
kèm chỗ đã sai trước khi có tệp này.

## S — một kỹ năng, một việc

Một kỹ năng trả lời ĐÚNG MỘT câu hỏi "làm việc X thế nào". Ôm hai việc thì người
đọc phải lướt qua nửa không liên quan, và mỗi lần sửa nửa này lại sợ hỏng nửa kia.

Ranh giới lấy theo VIỆC, không theo công cụ: `do-man-that` là "đo một màn thật",
dù nó chạm tới ba script và hai cổng. Tách thành "cấp thẻ", "mở trình duyệt",
"đọc số" thì không ai tách rời làm được từng cái.

## O — mở để nới, đóng để sửa

Thêm một màn cần đo, một loại bí mật cần quét, một vai mới: **thêm dữ liệu, không
sửa quy trình**. Kỹ năng nào cũng phải chỉ ra chỗ nới ấy nằm đâu — `MAN` trong
`scripts/do_mat_do_chu.mjs`, `LUAT` trong `scripts/quet_bi_mat.py`, `QUY_TAC`
trong `scripts/don_may.ps1`.

Dấu hiệu hỏng: kỹ năng liệt kê từng trường hợp trong thân bài. Sáu tháng sau nó
liệt kê thiếu, và không ai biết nó thiếu.

## L — thay được cho nhau

Mọi kỹ năng ở đây cùng một khuôn: *khi nào dùng · các bước · cổng kiểm · bẫy đã
có người vấp*. Agent đọc kỹ năng thứ hai không phải học lại cách đọc.

Cùng lẽ ấy ở tầng công cụ: mọi bộ đo nhận cùng một `page` từ `scripts/lib/phien_do.mjs`,
nên bộ đo viết cho vai học viên chạy nguyên xi cho vai giáo vụ.

## I — đừng bắt ai đọc thứ họ không dùng

SKILL.md giữ ngắn: đủ để làm việc thường gặp. Phần sâu — danh sách quy tắc đầy đủ,
lịch sử vì sao có luật này — nằm ở tệp riêng, ai cần mới mở.

## D — phụ thuộc vào lệnh ổn định, không vào cách làm

Kỹ năng gọi `python scripts/quet_bi_mat.py`, không chép regex vào bài. Đổi cách
quét thì sửa script; kỹ năng đứng yên. Chép logic vào kỹ năng là tạo ra bản sao
thứ hai, và bản sao thứ hai bao giờ cũng là bản sai sau vài tháng.

**Đây là lỗi đã mắc**: ngày 26/09, bảy bộ đo trong `scripts/` tự gọi
`chromium.launch()`, mỗi cái tự lo đóng — và sáu cái quên `finally`. Một lỗi
giữa chừng là Chromium sống tới lúc tắt máy; trưa hôm ấy máy anh Sơn có 11 tiến
trình Chromium giữ 788 MB cho một tab trống, cộng 22 tiến trình Node và Python
mồ côi. Vòng đời trình duyệt lẽ ra là MỘT chỗ, không phải bảy.

## Hai nguồn ngoài đã đọc để viết những kỹ năng này

- **cloudflare/security-audit-skill** — sáu pha, và hai ý đáng lấy: *người tìm
  khác người xác minh*, *phát hiện không có vết nguồn thì chưa phải phát hiện*.
  Xem `soat-bao-mat/`.
- **browser-use/jev-ultrafast** — tái dùng thay vì mở mới, chờ theo dấu hiệu có
  trần, không chụp ảnh khi không cần. Xem `do-man-that/` và `scripts/lib/phien_do.mjs`.
