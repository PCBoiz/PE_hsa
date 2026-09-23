"""DÒNG THỜI GIAN HỌC VIÊN — bảng yêu cầu TopHSA mục 4 (tab "Nhi" #2), 23/09/2026.

"Đăng ký → xếp lớp → … → hoàn thành" và "lịch sử chuyển lớp": dữ liệu đã có đủ
ở bảy nơi, chỉ chưa ai gom lại. View này CHỈ ĐỌC và không lưu gì mới — mỗi sự
kiện đọc thẳng từ bảng gốc của nó, nên không có bản sao nào để lệch.

  users.created_at            được cấp tài khoản (người cấp: nhật ký `user.create`)
  surveys                     làm khảo sát đầu vào (lần đầu)
  enrollments                 bắt đầu / hoàn thành một khoá
  class_members + classes     vào lớp · rời lớp (kèm lý do) · lớp kết thúc khi em còn học
  mock_attempts + mock_exams  nộp bài thi thử (điểm)
  ket_qua_thi_ngoai           kết quả kỳ thi ở hệ thống khảo thí ngoài
  parent_report_sends         gửi báo cáo cho phụ huynh (kênh — KHÔNG kèm địa chỉ)
  admin_audit (target = em)   cấp lại mật khẩu, tự đặt lại, sửa hồ sơ, khoá/mở,
                              đổi vai, cấp/thu hồi đường dẫn báo cáo

Quyền: cùng hàng rào với trang hồ sơ (`ho_so.chan_pham_vi`) — quản trị viên mọi
tài khoản, học vụ chỉ học viên.

Sự kiện nào cũng có `luc` (ISO). Cột DATE (ngày thi, ngày lớp kết thúc) trả dạng
ngày trơn và `caNgay: true` — màn hình không được bịa ra giờ 00:00 cho chúng.
"""
import datetime
import json

from rest_framework.response import Response
from rest_framework.views import APIView

from common.db import q
from common.permissions import IsAdminOrAcademic
from teaching.ho_so import _doc, chan_pham_vi
from teaching.vocab import LEAVE_LABEL

#: Trần số sự kiện trả về — một em học lâu có thể có hàng trăm lượt thi thử.
TRAN = 300

#: Cột hồ sơ → tên đọc được, cho sự kiện "Hồ sơ được cập nhật".
_TEN_COT = {
    'name': 'họ tên', 'birthday': 'ngày sinh', 'username': 'tên đăng nhập', 'school': 'trường',
    'school_grade': 'lớp ở trường', 'region': 'khu vực', 'consultant_id': 'người tư vấn',
    'enroll_source': 'nguồn tuyển sinh', 'study_goal': 'mục tiêu học tập',
    'aspiration': 'nguyện vọng', 'parent_name': 'tên phụ huynh', 'parent_phone': 'số Zalo phụ huynh',
    'parent_email': 'email phụ huynh',
}

_KENH = {'email': 'email', 'zalo': 'Zalo', 'zns': 'Zalo', 'sms': 'tin nhắn'}


def _su_kien(ds, luc, loai, tieu_de, chi_tiet=None, boi=None):
    if luc is None:
        return
    ca_ngay = isinstance(luc, datetime.date) and not isinstance(luc, datetime.datetime)
    khoa = datetime.datetime.combine(luc, datetime.time()) if ca_ngay else luc
    ds.append((khoa, {'loai': loai, 'luc': luc.isoformat(), 'caNgay': ca_ngay,
                      'tieuDe': tieu_de, 'chiTiet': chi_tiet or None, 'boi': boi or None}))


def _doc_luc_chu(s):
    """`surveys.created_at` là cột TEXT — đọc được thì dùng, không thì bỏ."""
    try:
        return datetime.datetime.fromisoformat(str(s).replace('Z', '+00:00')).replace(tzinfo=None)
    except (TypeError, ValueError):
        return None


def dong_thoi_gian(uid, tao_luc):
    ds = []

    tao = q("SELECT actor_name FROM admin_audit WHERE action='user.create' AND target_id=%s "
            'ORDER BY id LIMIT 1', (str(uid),))
    _su_kien(ds, tao_luc, 'tai-khoan', 'Được cấp tài khoản', boi=tao[0]['actor_name'] if tao else None)

    ks = q('SELECT created_at FROM surveys WHERE user_id=%s ORDER BY id LIMIT 1', (uid,))
    if ks:
        _su_kien(ds, _doc_luc_chu(ks[0]['created_at']), 'khao-sat', 'Làm khảo sát đầu vào')

    for r in q('''SELECT e.enrolled_at, e.completed_at, coalesce(c.title, e.course_id) AS ten
                    FROM enrollments e LEFT JOIN courses c ON c.id = e.course_id
                   WHERE e.user_id=%s''', (uid,)):
        _su_kien(ds, r['enrolled_at'], 'khoa-hoc', 'Bắt đầu khoá %s' % r['ten'])
        _su_kien(ds, r['completed_at'], 'khoa-hoc', 'Hoàn thành khoá %s' % r['ten'])

    luot = q('''SELECT m.id, m.joined_at, m.left_at, m.leave_reason, m.note, m.transferred_to,
                       c.name, c.status, c.ends_on, cb.name AS sang_lop
                  FROM class_members m JOIN classes c ON c.id = m.class_id
                  LEFT JOIN class_members mb ON mb.id = m.transferred_to
                  LEFT JOIN classes cb ON cb.id = mb.class_id
                 WHERE m.user_id=%s''', (uid,))
    # Chuyển lớp MỘT bước (§55): lượt ở lớp cũ trỏ tới lượt ở lớp mới. Hiện MỘT sự kiện
    # "Chuyển từ A sang B" thay cho cặp "Rời lớp A" + "Vào lớp B" cùng một thời điểm.
    dich_chuyen = {r['transferred_to'] for r in luot if r['transferred_to']}
    for r in luot:
        if r['id'] not in dich_chuyen:
            _su_kien(ds, r['joined_at'], 'lop-hoc', 'Vào lớp %s' % r['name'])
        if r['left_at'] is not None and r['sang_lop']:
            _su_kien(ds, r['left_at'], 'lop-hoc', 'Chuyển từ lớp %s sang lớp %s' % (r['name'], r['sang_lop']),
                     chi_tiet=('Ghi chú: %s' % r['note']) if r['note'] else None)
        elif r['left_at'] is not None:
            # `leave_reason` lưu MÃ (completed | dropped | transferred) — dịch bằng
            # đúng bảng nhãn mà màn Lớp học dùng, không in mã trần ra màn hình.
            ly_do = ' · '.join(x for x in (LEAVE_LABEL.get(r['leave_reason'], r['leave_reason']), r['note']) if x)
            _su_kien(ds, r['left_at'], 'lop-hoc', 'Rời lớp %s' % r['name'],
                     chi_tiet=('Lý do: %s' % ly_do) if ly_do else None)
        elif r['status'] == 'finished' and r['ends_on']:
            # Lớp đã kết thúc khi em CÒN học — đây là mốc "hoàn thành" của em.
            _su_kien(ds, r['ends_on'], 'lop-hoc', 'Học hết lớp %s' % r['name'])

    for r in q('''SELECT a.submitted_at, a.score, a.total, coalesce(x.title, 'đề #' || a.exam_id) AS ten
                    FROM mock_attempts a LEFT JOIN mock_exams x ON x.id = a.exam_id
                   WHERE a.user_id=%s AND a.submitted_at IS NOT NULL''', (uid,)):
        diem = ('%s/%s điểm' % (r['score'], r['total'])) if r['score'] is not None else None
        _su_kien(ds, r['submitted_at'], 'thi', 'Nộp bài thi thử: %s' % r['ten'], chi_tiet=diem)

    for r in q('''SELECT ngay_thi, dot, hinh_thuc, dia_diem, tong_diem, tong_toi_da
                    FROM ket_qua_thi_ngoai WHERE user_id=%s''', (uid,)):
        diem = ('%s/%s điểm' % (r['tong_diem'], r['tong_toi_da'])) if r['tong_diem'] is not None else None
        noi = ' · '.join(x for x in (diem, r['hinh_thuc'], r['dia_diem']) if x)
        # Tên đợt thường ĐÃ mở đầu bằng "Thi…" ("Thi thử tại trung tâm lần 2") —
        # ghép thêm chữ "Thi" là ra "Thi Thi thử…" (soi ảnh 23/09/2026).
        dot = (r['dot'] or '').strip() or 'đánh giá năng lực'
        tieu_de = dot if dot.lower().startswith(('thi', 'kỳ thi')) else 'Thi %s' % dot
        _su_kien(ds, r['ngay_thi'], 'thi', tieu_de[:1].upper() + tieu_de[1:], chi_tiet=noi or None)

    for r in q('''SELECT s.sent_at, s.created_at, s.status, s.channel
                    FROM parent_report_sends s JOIN parent_report_links l ON l.id = s.link_id
                   WHERE l.user_id=%s''', (uid,)):
        kenh = _KENH.get((r['channel'] or '').lower(), r['channel'] or 'kênh chưa rõ')
        # Trạng thái theo CHECK của bảng `parent_report_sends` (`legacy_schema.sql`):
        # 'cho' | 'da_gui' | 'loi' — KHÔNG phải tiếng Anh. Bản nháp đầu so với
        # 'sent' và sẽ báo mọi lượt gửi được là hỏng.
        if r['status'] == 'da_gui':
            _su_kien(ds, r['sent_at'] or r['created_at'], 'bao-cao', 'Gửi báo cáo cho phụ huynh qua %s' % kenh)
        elif r['status'] == 'loi':
            _su_kien(ds, r['created_at'], 'bao-cao', 'Gửi báo cáo cho phụ huynh không thành công',
                     chi_tiet='Kênh %s' % kenh)
        else:
            _su_kien(ds, r['created_at'], 'bao-cao', 'Báo cáo cho phụ huynh đang chờ gửi',
                     chi_tiet='Kênh %s' % kenh)

    for r in q('''SELECT action, actor_name, summary, detail, occurred_at FROM admin_audit
                   WHERE target_type='user' AND target_id=%s AND action = ANY(%s)''',
               (str(uid), ['user.password_reset', 'user.password_self_reset', 'user.profile',
                           'user.status', 'user.role', 'parent_link.create', 'parent_link.revoke'])):
        a = r['action']
        if a == 'user.password_reset':
            _su_kien(ds, r['occurred_at'], 'tai-khoan', 'Được cấp lại mật khẩu tạm', boi=r['actor_name'])
        elif a == 'user.password_self_reset':
            _su_kien(ds, r['occurred_at'], 'tai-khoan', 'Tự đặt lại mật khẩu qua email')
        elif a == 'user.profile':
            d = r['detail'] if isinstance(r['detail'], dict) else json.loads(r['detail'] or '{}')
            o = [_TEN_COT.get(k, k) for k in (d.get('moi') or {})]
            _su_kien(ds, r['occurred_at'], 'ho-so', 'Hồ sơ được cập nhật',
                     chi_tiet=(', '.join(o)).capitalize() if o else None, boi=r['actor_name'])
        elif a == 'user.status':
            _su_kien(ds, r['occurred_at'], 'tai-khoan', 'Khoá / mở tài khoản', chi_tiet=r['summary'],
                     boi=r['actor_name'])
        elif a == 'user.role':
            _su_kien(ds, r['occurred_at'], 'tai-khoan', 'Đổi vai trò', chi_tiet=r['summary'], boi=r['actor_name'])
        elif a == 'parent_link.create':
            _su_kien(ds, r['occurred_at'], 'bao-cao', 'Cấp đường dẫn báo cáo cho phụ huynh', boi=r['actor_name'])
        elif a == 'parent_link.revoke':
            _su_kien(ds, r['occurred_at'], 'bao-cao', 'Thu hồi đường dẫn báo cáo', boi=r['actor_name'])

    ds.sort(key=lambda t: t[0], reverse=True)
    return [e for _, e in ds]


class DongThoiGianView(APIView):
    """GET /api/admin/users/<id>/timeline — mới nhất ở trên. Chỉ đọc."""
    permission_classes = [IsAdminOrAcademic]

    def get(self, request, user_id):
        r = _doc(user_id)
        chan = chan_pham_vi(request, r)
        if chan:
            return chan
        ds = dong_thoi_gian(user_id, r['created_at'])
        return Response({'events': ds[:TRAN], 'tong': len(ds), 'catBot': len(ds) > TRAN})
