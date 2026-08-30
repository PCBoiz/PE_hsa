"""Chuẩn hoá định danh đăng nhập — email và số điện thoại.

VÌ SAO CÓ MODULE NÀY. Học viên không đăng nhập bằng chuỗi mà trợ giảng đã gõ; em
gõ lại theo cách em vẫn viết. Hai chuỗi khác nhau từng ký tự nhưng chỉ cùng một
người thì phải cùng một tài khoản, nếu không thì em bị khoá ngoài hệ thống mà
không hiểu vì sao — và từ khi bỏ tự đăng ký, em cũng không có đường nào tự thoát.

Hai lỗi có thật đã tìm thấy ngày 30/08/2026, cả hai đều nằm ở khe giữa lúc GHI
và lúc ĐỌC:

1. ``AdminCreateUserView`` lưu email đã hạ chữ thường, ``LoginView`` so khớp
   nguyên văn. Bàn phím điện thoại tự viết hoa chữ đầu là đủ để hỏng.
2. ``validate_phone_field`` nhận CẢ ``0912345678`` LẪN ``+84912345678`` là hợp
   lệ, và coi chúng là hai chuỗi khác nhau. Trợ giảng chép số từ phiếu đăng ký
   dạng quốc tế, học viên gõ dạng nội địa — không khớp.

Quy tắc: mọi chỗ GHI và mọi chỗ TRA đều đi qua đây. Chỉ chuẩn hoá ở một phía là
tái tạo đúng cái khe vừa vá.
"""
import re

#: Ký tự phân cách người ta hay chèn vào số điện thoại khi chép tay.
_PHONE_SEPARATORS = re.compile(r'[\s.\-()]')


def norm_email(value):
    """Bỏ khoảng trắng thừa và hạ chữ thường. Trả None nếu rỗng.

    Phần tên miền của email vốn không phân biệt hoa thường, còn phần trước @ thì
    về lý thuyết có — nhưng không nhà cung cấp thư nào ở Việt Nam phân biệt, và
    coi ``An@gmail.com`` khác ``an@gmail.com`` chỉ tạo ra tài khoản trùng.
    """
    if not value:
        return None
    return value.strip().lower() or None


def norm_phone(value):
    """Đưa số điện thoại về dạng nội địa ``0`` + 9 số. Trả None nếu rỗng.

    ``+84 912 345 678``, ``84912345678``, ``0912-345-678`` → ``0912345678``.

    Số không nhận ra được dạng nào thì trả lại nguyên vẹn (đã bỏ dấu phân cách)
    chứ không đoán: đoán sai một chữ số là gán nhầm tài khoản của người khác.
    """
    if not value:
        return None
    s = _PHONE_SEPARATORS.sub('', value.strip())
    if not s:
        return None
    if s.startswith('+'):
        s = s[1:]
    # Mã Việt Nam + 9 số thuê bao. Số nội địa hợp lệ luôn bắt đầu bằng 0 nên
    # không có số 11 chữ số nào bắt đầu bằng '84' mà lại KHÔNG phải dạng quốc tế.
    if s.startswith('84') and len(s) == 11:
        s = '0' + s[2:]
    return s or None


def looks_like_email(value):
    """Người dùng gõ vào ô "email hoặc số điện thoại" — đây là cái gì?"""
    return '@' in (value or '')
