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


def doc_trang(params, mac_dinh_moi_trang, tran_moi_trang):
    """``page``/``per_page`` từ query string → ``(page, per_page, offset)``.

    Tham số rác (``page=abc``, ``per_page=-3``, ``per_page=100000``) được KẸP về
    khoảng hợp lệ chứ không trả 400: đây là tham số của thanh phân trang, người
    dùng không gõ tay. Một liên kết cũ hay một lần sửa URL nhầm mà làm hỏng cả
    màn hình thì lỗi nằm ở phía ta.

    GOM 01/09/2026 (T20): trước đó có hai bản — `forum/views._paging` (nhận
    `request`, trần cứng 50) và `teaching/admin_users._paging` (nhận `params`,
    trần truyền vào, tự viết lại khối try/except mà `so_nguyen` ngay trên đã
    làm). Hai bản của một phép đọc phân trang là hai bản sẽ trôi — và cái trôi
    ở đây là TRẦN, tức là bao nhiêu dòng một lượt tới Neon phải bốc về.
    """
    page = so_nguyen(params.get('page'), 1, 1, None)
    per_page = so_nguyen(params.get('per_page'), mac_dinh_moi_trang, 1, tran_moi_trang)
    return page, per_page, (page - 1) * per_page
