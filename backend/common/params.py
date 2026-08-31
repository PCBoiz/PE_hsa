"""Đọc tham số truy vấn từ URL mà không cho một chuỗi rác làm đổ 500.

Tham số trên URL là thứ NGƯỜI DÙNG gõ được — dán nhầm, sửa tay, bot quét — nên
mọi nơi đọc số từ đó phải trả về một giá trị dùng được, không phải một ngoại lệ.

Đo 31/08/2026: bốn endpoint trả **500** với `?limit=abc`, `?weeks=abc`,
`?days=abc`, và cả `?weeks=1e9` (chuỗi ấy `int()` cũng không nuốt được). Ba nơi
khác trong repo đã tự viết đúng khối `try/except` này — `forum/views._paging`,
`teaching/sessions`, `teaching/parent_report` — mà ba bản tự viết là ba bản sẽ
trôi khỏi nhau.
"""


def so_nguyen(raw, mac_dinh, lo=None, hi=None):
    """Số nguyên đọc từ tham số URL, đã kẹp vào ``[lo, hi]``.

    Trả ``mac_dinh`` khi thiếu, rỗng, không phải số, hay là số thực dạng ``1e9``.
    KHÔNG ném ngoại lệ: một tham số hỏng phải cho ra màn hình mặc định, không
    phải một trang lỗi.

    ``bool`` bị từ chối cố ý — ``int(True)`` là 1 trong Python, và một tham số
    truy vấn không bao giờ thật sự mang ý nghĩa ấy.
    """
    if raw is None or isinstance(raw, bool):
        gia_tri = mac_dinh
    else:
        try:
            gia_tri = int(str(raw).strip())
        except (TypeError, ValueError):
            gia_tri = mac_dinh
    if gia_tri is None:
        return None
    if lo is not None:
        gia_tri = max(lo, gia_tri)
    if hi is not None:
        gia_tri = min(hi, gia_tri)
    return gia_tri
