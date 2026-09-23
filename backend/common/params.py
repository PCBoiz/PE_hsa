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


#: Lược đồ URL cho phép ở những trường người dùng NHẬP rồi hệ thống đổ vào
#: `href`. Danh sách TRẮNG, không phải danh sách đen: `javascript:`, `data:`,
#: `vbscript:` chỉ là ba cái nghĩ ra được hôm nay.
LUOC_DO_CHO_PHEP = ('https://', 'http://')


def kiem_lien_ket(gia_tri, ten_hien_thi):
    """``None`` nếu hợp lệ (hoặc để trống), ngược lại trả CÂU BÁO LỖI.

    Chặn ở ĐẦU VÀO chứ không ở chỗ hiển thị: chỗ hiển thị có thể mọc thêm (bản
    in, email nhắc lịch, ứng dụng di động), còn đường ghi thì chỉ có một.

    Đo 31/08/2026 trên link phòng học của LỚP: `javascript:alert(1)` đi qua
    nguyên vẹn, và thứ duy nhất chặn nó lúc chạy là `target="_blank"` — một
    thuộc tính đặt vào vì lý do KHÁC HẲN (mở link ở tab mới). Ai bỏ nó đi để
    sửa một chuyện về bố cục sẽ mở lại lỗ này mà không hề biết.
    """
    if not gia_tri:
        return None
    if not str(gia_tri).lower().startswith(LUOC_DO_CHO_PHEP):
        return ('%s phải bắt đầu bằng https:// hoặc http:// (đang nhận: "%s").'
                % (ten_hien_thi, str(gia_tri)[:40]))
    return None


# ── Tìm kiếm + phân trang dùng chung (dời từ teaching/admin_users.py, 24/09/2026) ──

def mau_like(term):
    """Bọc chuỗi tìm kiếm thành mẫu LIKE, VÔ HIỆU HOÁ ký tự đại diện.

    Không thoát ``%`` và ``_`` thì trợ giảng gõ một dấu ``%`` vào ô tìm kiếm sẽ
    nhận về TOÀN BỘ bảng users và tưởng là mình vừa tìm ra đúng người.
    """
    safe = term.replace('\\', '\\\\').replace('%', r'\%').replace('_', r'\_')
    return '%' + safe.lower() + '%'


def trang_kem_tong(body_sql, order_sql, args, per_page, offset):
    """MỘT câu SQL trả về CẢ tổng số dòng khớp LẪN đúng một trang.

    ``body_sql`` là câu SELECT đầy đủ (đã có WHERE) cho toàn bộ tập khớp; nó
    BẮT BUỘC phải chọn cột ``id`` — xem lý do ở cuối docstring. Trả (total, rows).

    Vì sao một câu chứ không hai: xem "NGÂN SÁCH VÒNG GỌI" ở đầu
    `teaching/admin_users.py`. Đếm
    riêng rồi lấy trang riêng là nhân đôi một lần đi-về mạng ở MỌI lần bấm sang
    trang — 246ms khi phát triển, và vẫn là một chuyến đi thừa khi chạy thật.

    Vì sao không dùng ``COUNT(*) OVER ()`` gắn thẳng vào câu lấy trang — cách
    ngắn hơn và ai cũng nghĩ tới đầu tiên: nó không trả dòng NÀO khi trang rỗng,
    mà "trang rỗng" không đồng nghĩa với "không có kết quả". Bấm sang trang 9
    của danh sách 8 trang (hoặc lọc lại khi đang đứng ở trang cuối) là trang
    rỗng, tổng khi đó tụt về 0, thanh phân trang tự sập và người dùng kẹt lại
    không còn nút nào quay về trang 1. ``LEFT JOIN LATERAL`` luôn trả ít nhất
    một dòng — dòng tổng, mọi cột dữ liệu NULL — nên tổng không bao giờ mất.
    Dòng mồi đó nhận ra bằng ``id IS NULL``: id là khoá chính, dòng thật không
    bao giờ NULL.
    """
    sql = ('WITH khop AS (%s), tong AS (SELECT count(*) AS __total FROM khop) '
           'SELECT tong.__total, trang.* FROM tong '
           'LEFT JOIN LATERAL (SELECT * FROM khop %s LIMIT %%s OFFSET %%s) trang ON TRUE'
           % (body_sql, order_sql))
    from common.db import q
    rows = q(sql, tuple(args) + (per_page, offset))
    if not rows:
        return 0, []
    total = rows[0]['__total'] or 0
    out = []
    for row in rows:
        if row.get('id') is None:
            continue                      # dòng mồi của trang rỗng
        row = dict(row)
        row.pop('__total', None)
        out.append(row)
    return total, out
