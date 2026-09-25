"""LỊCH SỬ THAY ĐỔI CỦA MỘT LỚP — cho học vụ (V-n, bảng TopHSA dòng 4 + 10).

Bảng khách đòi "lịch sử thay đổi / phân công lớp" và "lưu lịch sử thay đổi lịch". Dữ liệu
đã có từ 30/08/2026 trong `admin_audit` — nhưng màn Nhật ký chỉ quản trị viên đọc được
(`AdminAuditView`, `IsAdminRole`), và mở CẢ nhật ký cho học vụ là mở luôn các dòng đặt lại
mật khẩu, đổi vai, khoá tài khoản của nhân sự. Ở đây chỉ mở ĐÚNG phần của một lớp.

CÁC DÒNG CỦA MỘT LỚP (đọc `common/audit.py` + từng chỗ gọi `audit.record`):

  · `target_type = 'class'`, `target_id = <lớp>` — tạo/sửa/xoá lớp, thêm/cho rời/gán trợ
    giảng (`class.member.*`), chuyển lớp VÀO lớp này, nhập học viên từ tệp, sinh buổi
    hàng loạt, dán liên hệ phụ huynh, gửi báo cáo cả lớp;
  · chuyển lớp RA khỏi lớp này — dòng ấy đích là lớp MỚI, lớp cũ nằm ở `detail.fromClassId`;
  · buổi học (`session.create/update/delete`) — đích là BUỔI, lớp nằm ở `detail.class_id`.

KHÔNG gồm điểm danh từng buổi (`attendance.mark`): một lớp 3 buổi/tuần là hàng chục dòng mỗi
tháng che mất mọi thay đổi khác — lịch sử điểm danh có màn riêng (V-d). Không trả `ip` và
`detail` (liên hệ phụ huynh cũ nằm trong `detail`); câu tóm tắt đã dựng sẵn lúc ghi.

MỘT câu (đếm + trang, `trang_kem_tong`); ba nhánh OR đi ba chỉ mục (`idx_audit_target`,
`idx_audit_lop_buoi` của §69b, `idx_audit_action`).
"""
from rest_framework.response import Response
from rest_framework.views import APIView

from common.audit import ATTENDANCE_MARK, CLASS_MEMBER_TRANSFER
from common.db import q1
from common.params import doc_trang, trang_kem_tong
from common.permissions import IsAdminOrAcademic


class LichSuLopView(APIView):
    """GET /api/admin/classes/<id>/lich-su?page=&per_page= — mới nhất trước."""
    permission_classes = [IsAdminOrAcademic]

    def get(self, request, class_id):
        if not q1('SELECT 1 AS c FROM classes WHERE id=%s', (class_id,)):
            # Lớp đã XOÁ vẫn có lịch sử trong nhật ký — nhưng màn này mở từ một lớp đang có;
            # tra lớp đã xoá là việc của quản trị viên ở Nhật ký.
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        page, per_page, offset = doc_trang(request.query_params, 20, 100)
        lop = str(class_id)
        total, rows = trang_kem_tong(
            '''SELECT id, actor_name, actor_role, action, target_type, target_label, summary, occurred_at
                 FROM admin_audit
                WHERE (target_type = 'class' AND target_id = %s)
                   OR (target_type = 'class_session' AND detail->>'class_id' = %s AND action <> %s)
                   OR (action = %s AND detail->>'fromClassId' = %s)''',
            'ORDER BY occurred_at DESC, id DESC',
            [lop, lop, ATTENDANCE_MARK, CLASS_MEMBER_TRANSFER, lop], per_page, offset)
        return Response({
            'entries': [{
                'id': r['id'], 'actorName': r['actor_name'], 'actorRole': r['actor_role'],
                'action': r['action'], 'summary': r['summary'] or r['target_label'],
                'occurredAt': r['occurred_at'].isoformat() if r['occurred_at'] else None,
            } for r in rows],
            'total': total, 'page': page, 'per_page': per_page,
        })
