"""ĐỐI TƯỢNG NHẬN BÀI — một hàm SQL lọc cho MỌI chỗ đọc bài giao (kế hoạch v2 V-e).

Bảng yêu cầu TopHSA dòng 17: "thiết lập đối tượng nhận bài". Một bài giao cho CẢ LỚP
(`target_mode = 'lop'`, mọi bài cũ) hoặc cho MỘT NHÓM em (`'nhom'` + `assignment_targets`,
§62d).

── VÌ SAO MỘT HÀM ────────────────────────────────────────────────────────────

Bảy chỗ đọc bài (danh sách + sĩ số của bài, bảng chấm đọc và ghi, bài của học viên đọc
và nộp, thẻ lớp "chưa nộp", tờ phụ huynh, "bài chưa chấm" ở Việc hôm nay) và chuông
"bài mới". Chỗ nào tự viết điều kiện riêng thì sớm muộn lệch: em ngoài nhóm bị đếm
"chưa nộp" trên tờ gửi về nhà cho một bài em không hề được giao. Nên mọi chỗ gọi
`giao_cho()`; `grep giao_cho` ra đủ danh sách.
"""
#: Khớp `assignments_target_mode_check` (§62d).
CHE_DO_GIAO = ('lop', 'nhom')
CA_LOP = 'lop'
NHOM = 'nhom'


def giao_cho(a, uid):
    """Mệnh đề SQL: bài mang bí danh ``a`` được giao cho em ``uid``.

    ``uid`` là một BIỂU THỨC SQL (tên cột như ``m.user_id``, hoặc ``%s`` để truyền tham
    số) — không phải giá trị. Hai tham số đều là chuỗi trong mã nguồn, không bao giờ là
    dữ liệu người dùng gửi lên, nên ghép thẳng vào chuỗi SQL là an toàn (cùng lẽ với
    `vocab.chi_hoc_vien`).
    """
    return ("(%(a)s.target_mode = 'lop' OR EXISTS (SELECT 1 FROM assignment_targets gt "
            "WHERE gt.assignment_id = %(a)s.id AND gt.user_id = %(u)s))" % {'a': a, 'u': uid})
