"""TÌNH TRẠNG HỌC TẬP (tính) và TÌNH TRẠNG HỌC PHÍ (chọn tay) của một học viên — V-m.

Bảng TopHSA dòng 3 ("tình trạng học tập", "tình trạng học phí") + dòng 7 (kế toán — anh Sơn
chốt 25/09: không sổ tiền, chỉ MỘT ô tình trạng chọn tay).

── TÌNH TRẠNG HỌC TẬP: TÍNH, KHÔNG LƯU ──────────────────────────────────────

Lưu một cột "đang học / đã nghỉ" là thêm một sự thật thứ hai cạnh `class_members` — và nó sẽ
lệch ngay lần đầu có người cho em rời lớp mà quên sửa ô kia. Nên đây là MỘT biểu thức SQL
đọc thẳng các lượt học của em (`sql_tinh_trang_hoc`), dùng chung cho hồ sơ, danh sách tài
khoản (cột + ô lọc) và tệp xuất. Thứ tự ưu tiên:

  1. ``dang_hoc``     còn lượt học (chưa rời) ở một lớp ĐANG HỌC (`active`);
  2. ``tam_dung``     không có (1), nhưng còn lượt học ở lớp TẠM DỪNG (`paused`, V-c);
  3. ``chua_xep_lop`` chưa từng có lượt học nào ở lớp không huỷ;
  4. ``da_hoc_xong``  lượt học GẦN NHẤT kết thúc bằng "học xong", hoặc lớp ấy đã kết thúc
                      mà em chưa bị cho rời;
  5. ``bao_luu``      lượt học GẦN NHẤT đóng với lý do BẢO LƯU (`leave_reason = 'reserved'`,
                      luồng C / §63) — em tạm nghỉ có hẹn quay lại, KHÁC bỏ học;
  6. ``da_nghi``      còn lại — lượt gần nhất là bỏ giữa chừng, chuyển lớp (không còn lớp
                      nào đang học) hay rời không ghi lý do.

Lớp đã HUỶ không tính ở mọi bước — như cổng mở môn (`courses/truy_cap.LOP_DANG_HOC`).
Nhân sự: ``NULL`` (không áp dụng). Chữ `'paused'` viết trần: giá trị ấy do V-c thêm vào
CHECK §35; trước khi có thì nhánh (2) không bao giờ khớp — vô hại.
"""
from common.permissions import ROLE_STUDENT

#: Mã → nhãn. Thứ tự = thứ tự trên ô lọc.
TINH_TRANG_HOC = (
    ('dang_hoc', 'Đang học'),
    ('tam_dung', 'Tạm dừng'),
    ('da_hoc_xong', 'Đã học xong'),
    ('bao_luu', 'Bảo lưu'),
    ('da_nghi', 'Đã nghỉ'),
    ('chua_xep_lop', 'Chưa xếp lớp'),
)
NHAN_TINH_TRANG_HOC = dict(TINH_TRANG_HOC)

#: Tình trạng học phí — khớp CHECK `users_tuition_status_check` (§69a). Thứ tự = ô chọn.
HOC_PHI = (
    ('da_dong', 'Đã đóng'),
    ('sap_het', 'Sắp hết'),
    ('het', 'Hết'),
    ('bao_luu', 'Bảo lưu'),
)
MA_HOC_PHI = tuple(m for m, _ in HOC_PHI)
NHAN_HOC_PHI = dict(HOC_PHI)


def sql_tinh_trang_hoc(u='u'):
    """Biểu thức SQL (một giá trị) — tình trạng học tập của tài khoản bí danh ``u``.

    Câu con TƯƠNG QUAN theo ``u.id`` — chạy trong câu đọc trang (25 dòng) hay câu xuất tệp,
    không thêm vòng gọi nào. Có chỉ mục `idx_class_members_user`."""
    lop = ('FROM class_members m JOIN classes c ON c.id = m.class_id '
           "WHERE m.user_id = {u}.id AND c.status <> 'cancelled'").format(u=u)
    return ('''CASE
        WHEN {u}.role <> '{hv}' THEN NULL
        WHEN EXISTS (SELECT 1 {lop} AND m.left_at IS NULL AND c.status = 'active') THEN 'dang_hoc'
        WHEN EXISTS (SELECT 1 {lop} AND m.left_at IS NULL AND c.status = 'paused') THEN 'tam_dung'
        WHEN NOT EXISTS (SELECT 1 {lop}) THEN 'chua_xep_lop'
        WHEN (SELECT (m.left_at IS NULL OR m.leave_reason = 'completed') {lop}
               ORDER BY COALESCE(m.left_at, m.joined_at) DESC NULLS LAST, m.id DESC LIMIT 1)
             THEN 'da_hoc_xong'
        WHEN (SELECT m.leave_reason = 'reserved' {lop}
               ORDER BY COALESCE(m.left_at, m.joined_at) DESC NULLS LAST, m.id DESC LIMIT 1)
             THEN 'bao_luu'
        ELSE 'da_nghi'
    END''').format(u=u, hv=ROLE_STUDENT, lop=lop)
