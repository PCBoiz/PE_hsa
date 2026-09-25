"""API THÔNG BÁO TRUNG TÂM (E2).

  GET/POST /api/admin/thong-bao                 — học vụ + quản trị: danh sách / soạn (nháp hoặc gửi luôn)
  POST     /api/admin/thong-bao/preview         — đếm người nhận theo kênh, ai thiếu email
  POST     /api/admin/thong-bao/<id>/gui        — gửi bản nháp (409 nếu đã gửi / đã huỷ)
  POST     /api/admin/thong-bao/<id>/huy        — huỷ bản nháp
  POST     /api/teach/classes/<id>/thong-bao    — giảng viên (và học vụ) gửi cho MỘT lớp mình thấy
  POST     /api/teach/classes/<id>/thong-bao/preview

Học vụ gửi được MỌI đối tượng (`IsAdminOrAcademic`). Giảng viên chỉ lớp mình
(`IsSeniorTeachingStaff` + `can_see_class`; lớp khác → 404, không lộ lớp có tồn tại).
Trợ giảng không gửi thông báo (nhắn/nhắc hai chiều của trợ giảng là việc của E3).
"""
import json

from rest_framework.response import Response
from rest_framework.views import APIView

from common import audit
from common.db import q1
from common.permissions import IsAdminOrAcademic, IsSeniorTeachingStaff, can_see_class
from notifications import thong_bao as tb


def _body(request):
    return request.data if isinstance(request.data, dict) else {}


def _doc_noi_dung(d):
    """(tiêu đề, nội dung, lỗi) — lỗi là dict `errors` theo ô."""
    tieu_de = str(d.get('title') or '').strip()
    noi_dung = str(d.get('body') or '').strip()
    loi = {}
    if not tieu_de:
        loi['title'] = 'Nhập tiêu đề thông báo.'
    elif len(tieu_de) > tb.TRAN_TIEU_DE:
        loi['title'] = 'Tiêu đề dài quá %d ký tự.' % tb.TRAN_TIEU_DE
    if len(noi_dung) > tb.TRAN_NOI_DUNG:
        loi['body'] = 'Nội dung dài quá %d ký tự.' % tb.TRAN_NOI_DUNG
    return tieu_de, noi_dung, loi


def _hinh(a):
    aud = a['audience'] if isinstance(a['audience'], dict) else json.loads(a['audience'] or '{}')
    return {'id': a['id'], 'title': a['title'], 'body': a['body'], 'audience': aud,
            'sendEmail': a['send_email'], 'sendZalo': a['send_zalo'], 'status': a['status'],
            'recipientCount': a['recipient_count'], 'createdAt': a['created_at'], 'sentAt': a['sent_at'],
            'createdByName': a.get('created_by_name') or '', 'daGuiThu': a.get('da_gui_thu') or 0,
            'daDoc': a.get('da_doc') or 0}


def _soan(request, aud, gui_ngay):
    """Tạo (và gửi nếu `gui_ngay`) — dùng chung cho học vụ và giảng viên."""
    d = _body(request)
    tieu_de, noi_dung, loi = _doc_noi_dung(d)
    if gui_ngay and tb.rong(aud):
        loi['audience'] = 'Chọn ít nhất một lớp, một môn hoặc một người nhận.'
    gui_zalo = bool(d.get('sendZalo'))
    if gui_zalo and not tb.zalo_san_sang()[0]:
        loi['sendZalo'] = tb.zalo_san_sang()[1]
    if loi:
        return Response({'errors': loi}, status=400)
    aid = tb.tao(tieu_de, noi_dung, aud, bool(d.get('sendEmail')), gui_zalo, request.user.id)
    so = tb.gui(aid) if gui_ngay else None
    if so is not None:
        audit.record(request, audit.ANNOUNCEMENT_SEND, target_type='announcement', target_id=aid,
                     target_label=tieu_de, summary='Gửi thông báo "%s" tới %d người.' % (tieu_de, so),
                     detail={'audience': aud, 'email': bool(d.get('sendEmail')), 'zalo': gui_zalo})
    return Response({'id': aid, 'status': 'sent' if so is not None else 'draft',
                     'recipientCount': so or 0}, status=201)


class AdminThongBaoView(APIView):
    permission_classes = [IsAdminOrAcademic]

    def get(self, request):
        return Response({'items': [_hinh(a) for a in tb.danh_sach()],
                         'zalo': dict(zip(('sanSang', 'lyDo'), tb.zalo_san_sang(), strict=True))})

    def post(self, request):
        return _soan(request, tb.doi_tuong(_body(request).get('audience')), bool(_body(request).get('gui')))


class AdminThongBaoXemTruocView(APIView):
    permission_classes = [IsAdminOrAcademic]

    def post(self, request):
        d = _body(request)
        return Response(tb.xem_truoc(tb.doi_tuong(d.get('audience')), bool(d.get('sendEmail', True))))


class AdminThongBaoGuiView(APIView):
    permission_classes = [IsAdminOrAcademic]

    def post(self, request, aid):
        a = q1('SELECT title FROM announcements WHERE id = %s', (aid,))
        if not a:
            return Response({'error': 'Không tìm thấy thông báo này.'}, status=404)
        so = tb.gui(aid)
        if so is None:
            return Response({'error': 'Thông báo này đã gửi hoặc đã huỷ.'}, status=409)
        audit.record(request, audit.ANNOUNCEMENT_SEND, target_type='announcement', target_id=aid,
                     target_label=a['title'], summary='Gửi thông báo "%s" tới %d người.' % (a['title'], so))
        return Response({'id': aid, 'status': 'sent', 'recipientCount': so})


class AdminThongBaoHuyView(APIView):
    permission_classes = [IsAdminOrAcademic]

    def post(self, request, aid):
        if not q1('''UPDATE announcements SET status = 'cancelled' WHERE id = %s AND status = 'draft'
                     RETURNING id''', (aid,)):
            return Response({'error': 'Chỉ huỷ được bản nháp.'}, status=409)
        return Response({'id': aid, 'status': 'cancelled'})


class LopThongBaoView(APIView):
    """Giảng viên gửi cho LỚP MÌNH — đối tượng cố định là lớp trên đường dẫn."""
    permission_classes = [IsSeniorTeachingStaff]

    def get(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        ds = tb.danh_sach(gioi_han=30, lop=class_id)
        return Response({'items': [_hinh(a) for a in ds]})

    def post(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        return _soan(request, {'classIds': [class_id]}, True)


class LopThongBaoXemTruocView(APIView):
    permission_classes = [IsSeniorTeachingStaff]

    def post(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        return Response(tb.xem_truoc({'classIds': [class_id]}, bool(_body(request).get('sendEmail', True))))
