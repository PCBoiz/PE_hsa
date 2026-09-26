"""AI THUỘC MỘT BUỔI — một mệnh đề SQL cho mọi chỗ hỏi "buổi này có phải buổi của em không".

Kế hoạch v2 V-g (bảng TopHSA dòng 10, buổi bù): một buổi có `session_participants`
(§62e) thì chỉ những em ấy thuộc buổi; không có thì cả lớp như trước. Mọi chỗ dựng
danh sách / mẫu số THEO TỪNG EM phải qua đây — không thì một buổi bù cho hai em hiện
thành "chưa điểm danh" của cả lớp, lọt vào mẫu số chuyên cần của em không tham gia (tờ
gửi phụ huynh!), và vào số buổi tính học phí của em ấy. `grep thuoc_buoi` ra đủ chỗ.
"""


def thuoc_buoi(sid, uid):
    """Mệnh đề SQL: em ``uid`` thuộc buổi ``sid``.

    Hai tham số là BIỂU THỨC SQL (tên cột như ``s.id``/``m.user_id``, hoặc ``%s``) —
    chuỗi trong mã, không phải dữ liệu người dùng.

    **TÊN CỘT PHẢI CÓ TIỀN TỐ BẢNG.** Câu con dưới đây có bảng ``sp`` của riêng nó, nên một
    tên trần như ``session_id`` bị Postgres hiểu là cột CỦA ``sp`` — điều kiện thành
    ``sp.session_id = sp.session_id``, luôn đúng, câu con quét cả bảng, và hàm trả "em có
    thuộc buổi NÀO ĐÓ không" thay vì "em có thuộc buổi NÀY không". Không lỗi cú pháp, không
    cảnh báo; chỉ sai lặng lẽ. Đo 27/09/2026: tài liệu gắn vào buổi thường biến mất khỏi thẻ
    lớp của mọi em chưa từng có dòng ``session_participants`` nào — 329 test xanh, đúng một
    test đỏ. Chín chỗ gọi khác trong repo đều đã có tiền tố; chỗ thứ mười thì không. Viết bằng MỘT câu con
    (`bool_or` trên tập rỗng là NULL → COALESCE thành TRUE) để mỗi biểu thức chỉ xuất
    hiện một lần: dùng ``%s`` thì truyền tham số theo thứ tự chữ — ``uid`` TRƯỚC ``sid``.
    """
    return ('COALESCE((SELECT bool_or(sp.user_id = %s) FROM session_participants sp '
            'WHERE sp.session_id = %s), TRUE)' % (uid, sid))
