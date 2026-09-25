"""Từ vựng của miền chương trình — nơi DUY NHẤT đặt tên trạng thái và ngưỡng.

Ba bộ giá trị ở đây phải KHỚP từng chữ với `CHECK` của `sql/legacy_schema.sql` §63–§64
(`tests_tu_vung.py` đọc thẳng ràng buộc trên CSDL). Lệch một bên là màn hình hiện mã
máy, hoặc CSDL từ chối một giá trị mã cho là hợp lệ.
"""
from decimal import Decimal

#: Trạng thái một phiên bản khung. Chỉ `draft` sửa được.
BAN_NHAP, BAN_XUAT_BAN, BAN_NGUNG = 'draft', 'published', 'retired'
TRANG_THAI_BAN = (BAN_NHAP, BAN_XUAT_BAN, BAN_NGUNG)
NHAN_TRANG_THAI_BAN = {BAN_NHAP: 'Bản nháp', BAN_XUAT_BAN: 'Đang dùng', BAN_NGUNG: 'Đã thay'}

#: Loại mục của một buổi khung.
LOAI_MUC = ('lesson', 'topic', 'homework', 'test')
NHAN_LOAI_MUC = {'lesson': 'Bài học', 'topic': 'Chủ đề', 'homework': 'Bài về nhà',
                 'test': 'Kiểm tra'}

#: Sổ đầu bài: mỗi mục đã dạy / dạy một phần / chưa dạy.
MUC_XONG, MUC_MOT_PHAN, MUC_CHUA = 'done', 'partial', 'not_done'
TRANG_THAI_MUC = (MUC_XONG, MUC_MOT_PHAN, MUC_CHUA)
NHAN_TRANG_THAI_MUC = {MUC_XONG: 'Đã dạy', MUC_MOT_PHAN: 'Dạy một phần', MUC_CHUA: 'Chưa dạy'}

#: Phần trọng số một mục được tính là ĐÃ XONG theo trạng thái trong sổ. Một mục ghi ở
#: nhiều buổi (dạy dở rồi dạy tiếp) lấy mức CAO NHẤT, không cộng dồn — xem `tien_do.py`.
TIN_CHI = {MUC_XONG: Decimal('1'), MUC_MOT_PHAN: Decimal('0.5'), MUC_CHUA: Decimal('0')}

#: Lớp CHẬM TIẾN ĐỘ khi (a) trễ từ ngần này buổi khung trở lên, HOẶC (b) phần đã xong
#: dưới tỉ lệ này của phần phải xong tới hôm nay. Hai vế vì hai kiểu chậm khác nhau:
#: lớp dài trễ vài buổi mà tỉ lệ vẫn cao (a bắt), lớp mới học ba buổi đã hụt một nửa
#: mà chưa đủ hai buổi (b bắt). Là GIẢ ĐỊNH về cách TopHSA quản lớp — để lộ ở đây để
#: còn bàn lại, màn hình đọc từ phản hồi chứ không gõ lại số.
NGUONG_TRE_BUOI = Decimal('2')
NGUONG_TI_LE = Decimal('0.8')

#: Trần nhập liệu của bộ soạn khung — chặn một lượt dán nhầm cả giáo trình vào một ô.
TRAN_BUOI = 200
TRAN_MUC_MOT_BUOI = 30
TRAN_TRONG_SO = Decimal('100')
DAI = {'ten_khung': 200, 'tieu_de': 200, 'bai_ve_nha': 2000, 'kiem_tra': 300,
       'nhan_muc': 300, 'ghi_chu_ban': 1000, 'ghi_chu_muc': 500, 'de_xuat': 2000,
       'ghi_chu_ho_tro': 500}
