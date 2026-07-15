"""
Port NGUYÊN VĂN validators.py của bản Flask (message tiếng Việt giữ y hệt).
Mỗi hàm trả chuỗi lỗi (str) nếu không hợp lệ, hoặc None nếu OK.
"""
import re

from email_validator import EmailNotValidError, validate_email


def validate_email_field(value: str) -> str | None:
    """Validate email: bắt buộc + RFC 5322 format."""
    if not value:
        return 'Email không được để trống'
    try:
        validate_email(value, check_deliverability=False)
    except EmailNotValidError:
        return 'Email không hợp lệ'
    return None


def validate_password_field(value: str, label: str = 'Mật khẩu') -> str | None:
    """Validate password: bắt buộc + 8-128 ký tự."""
    if not value:
        return f'{label} không được để trống'
    length = len(value)
    if length < 8:
        return f'{label} phải có ít nhất 8 ký tự'
    if length > 128:
        return f'{label} không được vượt quá 128 ký tự'
    return None


def validate_name_field(value: str) -> str | None:
    """Validate name: bắt buộc + tối đa 100 ký tự."""
    if not value:
        return 'Tên không được để trống'
    if len(value) > 100:
        return 'Tên không được vượt quá 100 ký tự'
    return None


def validate_phone_field(value: str) -> str | None:
    """
    Validate phone: tùy chọn (rỗng → OK).
    Nội địa: đúng 10 chữ số bắt đầu bằng 0; quốc tế: +<mã 1-3 số><9 số>.
    """
    if not value:
        return None
    if re.fullmatch(r'0\d{9}', value):
        return None
    if re.fullmatch(r'\+\d{1,3}\d{9}', value):
        return None
    return ('Số điện thoại phải có 10 số (VD: 0912345678) '
            'hoặc mã quốc gia + 9 số (VD: +84912345678)')
