"""CHUYỂN LỚP MỘT THAO TÁC (mục 1.2c kế hoạch thử nghiệm, §55 — 24/09/2026).

Ghi chú họp TopHSA có dòng "chuyển lớp". Trước hôm nay chuyển lớp là HAI thao tác rời
tay: cho rời lớp A với lý do "chuyển lớp", rồi sang lớp B xếp em vào. Không gì nối
hai lượt — báo cáo rời lớp không trả lời được "em sang lớp nào", và làm dở giữa chừng
(rời A rồi quên xếp B) là một em biến khỏi mọi lớp mà không ai biết.

Ở đây là MỘT lượt, MỘT giao dịch: đóng lượt ở A (`leave_reason='transferred'`) → mở
lượt ở B → lượt A trỏ tới lượt B (`transferred_to`). Bước nào hỏng thì không bước nào
còn lại.
"""
from datetime import date, datetime, time

from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from common import audit
from common.clock import local_now, local_today
from common.db import q1, x
from common.permissions import ROLE_STUDENT, IsAdminOrAcademic
from teaching.vocab import TRAN_GIA_SU, chi_hoc_vien

#: Cùng trần với ghi chú khác của `class_members` ở màn Lớp học.
TRAN_GHI_CHU = 500


class _Huy(Exception):
    """Thoát giữa giao dịch kèm phản hồi — `atomic()` cuộn lại mọi thứ đã ghi."""

    def __init__(self, phan_hoi):
        super().__init__()
        self.phan_hoi = phan_hoi


def _ngay_vn(d):
    return d.strftime('%d/%m/%Y')


def _ten_mon(lop):
    return lop['course_title'] or ('cả ba môn' if not lop['course_id'] else lop['course_id'])


class ChuyenLopView(APIView):
    """POST /api/admin/classes/<class_id>/members/<user_id>/transfer.

    Thân: `to_class_id` (bắt buộc), `effective_date` (YYYY-MM-DD, tuỳ chọn — mặc định
    hôm nay; không ở tương lai, không trước ngày em vào lớp A), `note` (tuỳ chọn).
    200 `{ok, fromClassId, toClassId, fromMemberId, toMemberId, at, warnings}`.
    """
    permission_classes = [IsAdminOrAcademic]

    def post(self, request, class_id, user_id):
        body = request.data if isinstance(request.data, dict) else {}
        try:
            den_id = int(body.get('to_class_id'))
        except (TypeError, ValueError):
            return Response({'error': 'Chọn lớp chuyển tới.'}, status=400)
        if den_id == int(class_id):
            return Response({'error': 'Lớp chuyển tới phải khác lớp em đang học.'}, status=400)

        ngay = None
        if body.get('effective_date') not in (None, ''):
            try:
                ngay = date.fromisoformat(str(body['effective_date'])[:10])
            except ValueError:
                return Response({'error': 'Ngày chuyển phải ở dạng YYYY-MM-DD.'}, status=400)
            if ngay > local_today():
                return Response({'error': 'Ngày chuyển không được ở tương lai.'}, status=400)
        # Hôm nay → giờ hiện tại: buổi sáng nay em còn học ở A vẫn tính cho A. Ngày trước
        # → đầu ngày ấy: đó là ngày ĐẦU TIÊN em học ở B.
        luc = local_now() if ngay in (None, local_today()) else datetime.combine(ngay, time.min)
        ghi_chu = (str(body.get('note') or '').strip() or None)
        if ghi_chu and len(ghi_chu) > TRAN_GHI_CHU:
            return Response({'error': 'Ghi chú tối đa %d ký tự.' % TRAN_GHI_CHU}, status=400)

        em = q1('SELECT id, name, email, role FROM users WHERE id=%s', (user_id,))
        if not em:
            return Response({'error': 'Không có tài khoản này.'}, status=404)
        if em['role'] != ROLE_STUDENT:
            return Response({'error': 'Chỉ chuyển lớp cho học viên. Trợ giảng thì gỡ khỏi lớp này '
                                      'rồi gán vào lớp kia.'}, status=400)
        ten_em = em['name'] or em['email']

        try:
            with transaction.atomic():
                ket_qua = self._chuyen(request, int(class_id), den_id, em, ten_em, luc, ghi_chu)
        except _Huy as h:
            return h.phan_hoi
        return Response(ket_qua)

    @staticmethod
    def _chuyen(request, tu_id, den_id, em, ten_em, luc, ghi_chu):
        cot = ('SELECT c.id, c.name, c.status, c.class_type, c.course_id, co.title AS course_title '
               'FROM classes c LEFT JOIN courses co ON co.id = c.course_id WHERE c.id = %s')
        tu = q1(cot, (tu_id,))
        if not tu:
            raise _Huy(Response({'error': 'Không tìm thấy lớp này.'}, status=404))
        # Khoá dòng lớp B: cùng khoá mà lượt THÊM em dùng (`_ghi_thanh_vien`), nên hai lượt
        # cùng lúc vào một lớp gia sư không cùng đếm được "còn 1 chỗ".
        den = q1(cot + ' FOR UPDATE OF c', (den_id,))
        if not den:
            raise _Huy(Response({'error': 'Không tìm thấy lớp chuyển tới.'}, status=404))
        if den['status'] == 'cancelled':
            raise _Huy(Response({'error': 'Lớp "%s" đã huỷ — không chuyển vào được.' % den['name']},
                                status=400))

        luot = q1('SELECT id, joined_at FROM class_members WHERE class_id=%s AND user_id=%s '
                  'AND left_at IS NULL FOR UPDATE', (tu_id, em['id']))
        if not luot:
            raise _Huy(Response({'error': 'Em không đang học lớp "%s".' % tu['name']}, status=404))
        if luot['joined_at'] and luc < luot['joined_at']:
            raise _Huy(Response({'error': 'Ngày chuyển phải từ ngày em vào lớp "%s" (%s) trở đi.'
                                          % (tu['name'], _ngay_vn(luot['joined_at']))}, status=400))
        if q1('SELECT 1 AS c FROM class_members WHERE class_id=%s AND user_id=%s AND left_at IS NULL',
              (den_id, em['id'])):
            raise _Huy(Response({'error': 'Em đã ở trong lớp "%s" rồi.' % den['name']}, status=409))
        if den['class_type'] == 'gia_su':
            dang_hoc = q1('SELECT count(*) AS n FROM class_members m JOIN users mu ON mu.id = m.user_id '
                          'WHERE m.class_id = %s AND m.left_at IS NULL AND ' + chi_hoc_vien('mu'),
                          (den_id,))['n']
            if dang_hoc >= TRAN_GIA_SU:
                raise _Huy(Response({'error': 'Lớp gia sư "%s" đã đủ %d em.' % (den['name'], TRAN_GIA_SU)},
                                    status=409))

        x("UPDATE class_members SET left_at=%s, leave_reason='transferred', note=COALESCE(%s, note) "
          'WHERE id=%s', (luc, ghi_chu, luot['id']))
        moi = q1('''INSERT INTO class_members (class_id, user_id, joined_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (class_id, user_id) WHERE left_at IS NULL DO NOTHING
                    RETURNING id''', (den_id, em['id'], luc))
        if not moi:
            # Một lượt thêm em vào B chen vào giữa lúc kiểm và lúc ghi. Ném → `atomic()`
            # cuộn lại cả lệnh đóng lượt ở A — em không bị rơi khỏi mọi lớp.
            raise _Huy(Response({'error': 'Em vừa được xếp vào lớp "%s" ở nơi khác — tải lại để xem.'
                                          % den['name']}, status=409))
        x('UPDATE class_members SET transferred_to=%s WHERE id=%s', (moi['id'], luot['id']))

        canh_bao = []
        if den['status'] == 'finished':
            canh_bao.append('Lớp "%s" đã kết thúc — kiểm lại nếu không cố ý.' % den['name'])
        if (tu['course_id'] or None) != (den['course_id'] or None):
            canh_bao.append('Môn của lớp mới khác lớp cũ: %s thay cho %s.' % (_ten_mon(den), _ten_mon(tu)))

        audit.record(request, audit.CLASS_MEMBER_TRANSFER, target_type='class', target_id=den_id,
                     target_label=den['name'],
                     summary='Chuyển "%s" từ lớp "%s" sang lớp "%s".' % (ten_em, tu['name'], den['name']),
                     detail={'userId': em['id'], 'userName': ten_em, 'fromClassId': tu_id,
                             'toClassId': den_id, 'fromMemberId': luot['id'], 'toMemberId': moi['id'],
                             'at': luc.isoformat(), 'note': ghi_chu})
        return {'ok': True, 'fromClassId': tu_id, 'toClassId': den_id, 'fromMemberId': luot['id'],
                'toMemberId': moi['id'], 'at': luc.isoformat(), 'warnings': canh_bao}
