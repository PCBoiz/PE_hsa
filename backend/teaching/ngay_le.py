"""Ngày lễ dương lịch CỐ ĐỊNH của Việt Nam — để GỢI Ý, không tự bỏ buổi nào.

Bộ luật Lao động 2019, Điều 112 cho nghỉ các ngày dương lịch cố định dưới đây.
Phần còn lại — Tết Nguyên đán, Giỗ Tổ Hùng Vương (âm lịch), ngày nghỉ liền kề
Quốc khánh và các ngày nghỉ bù — được công bố TỪNG NĂM, nên KHÔNG có ở đây:
đoán sai một ngày là cả lớp vào phòng học trống. Học vụ khai chúng theo thông
báo chính thức ở màn Đợt học (bảng `term_holidays`, §46).

Dùng chung cho HAI chỗ và phải là một: màn Đợt học (gợi ý thêm vào danh sách)
và sinh buổi hàng loạt (cảnh báo ngày lễ đợt chưa khai). Hai bảng chép tay sẽ
trôi, và khi đó màn này gợi ý một ngày mà màn kia không cảnh báo.
"""
from datetime import date

LE_CO_DINH = (
    (1, 1, 'Tết Dương lịch'),
    (4, 30, 'Ngày Giải phóng miền Nam'),
    (5, 1, 'Quốc tế Lao động'),
    (9, 2, 'Quốc khánh'),
)


def le_co_dinh_trong(tu, den):
    """``{date: tên}`` cho mọi lễ cố định nằm trong ``[tu, den]`` (tính cả hai đầu).

    Thiếu một đầu thì trả rỗng: đợt không có ngày bắt đầu/kết thúc thì không có
    khoảng nào để gợi ý, và đoán một khoảng là gợi ý bừa.
    """
    if not tu or not den or tu > den:
        return {}
    ra = {}
    for nam in range(tu.year, den.year + 1):
        for thang, ngay, ten in LE_CO_DINH:
            d = date(nam, thang, ngay)
            if tu <= d <= den:
                ra[d] = ten
    return ra
