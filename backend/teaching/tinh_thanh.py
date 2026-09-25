"""34 đơn vị hành chính cấp tỉnh sau sáp nhập 2025 — ô "Tỉnh/Thành phố" của hồ sơ học viên.

Bảng TopHSA dòng 3 đòi "Tỉnh/Thành phố"; `users.region` tới 25/09/2026 là ô chữ tự do, nên
cùng một nơi hiện ra "HN", "Ha Noi", "Hà Nội" — không lọc, không đếm được. Nay chọn từ danh
sách này (V-m). Giá trị CŨ gõ tay vẫn giữ và vẫn hiện nguyên văn cho tới khi có người chọn
lại — máy chủ nhận "giữ nguyên giá trị đang có" dù nó ngoài danh sách (`teaching/ho_so.py`).

Nguồn: Nghị quyết 202/2025/QH15 về sắp xếp đơn vị hành chính cấp tỉnh (năm 2025): 6 thành
phố trực thuộc trung ương + 28 tỉnh. Thứ tự: sáu thành phố trước, rồi các tỉnh theo vần chữ
cái. Tên ghi không kèm chữ "tỉnh" / "thành phố" (trừ Thành phố Hồ Chí Minh — tên riêng).

MỘT BẢN CHÉP ở `frontend/src/lib/tinhThanh.ts` (ô chọn dựng ở trình duyệt). Hai danh sách
phải GIỐNG HỆT — `frontend/e2e/unit/tinh-thanh.test.mjs` đọc cả hai tệp và so từng tên.
"""

TINH_THANH = (
    'Hà Nội',
    'Thành phố Hồ Chí Minh',
    'Hải Phòng',
    'Đà Nẵng',
    'Cần Thơ',
    'Huế',
    'An Giang',
    'Bắc Ninh',
    'Cà Mau',
    'Cao Bằng',
    'Đắk Lắk',
    'Điện Biên',
    'Đồng Nai',
    'Đồng Tháp',
    'Gia Lai',
    'Hà Tĩnh',
    'Hưng Yên',
    'Khánh Hòa',
    'Lai Châu',
    'Lạng Sơn',
    'Lào Cai',
    'Lâm Đồng',
    'Nghệ An',
    'Ninh Bình',
    'Phú Thọ',
    'Quảng Ngãi',
    'Quảng Ninh',
    'Quảng Trị',
    'Sơn La',
    'Tây Ninh',
    'Thái Nguyên',
    'Thanh Hóa',
    'Tuyên Quang',
    'Vĩnh Long',
)
