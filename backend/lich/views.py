"""TUYẾN cho địa chỉ lịch riêng — §71, 26/09/2026.

  GET    /api/lich/dia-chi          — tôi đã có địa chỉ lịch chưa (KHÔNG trả chìa)
  POST   /api/lich/dia-chi          — cấp / cấp lại, trả địa chỉ đầy đủ MỘT lần
  DELETE /api/lich/dia-chi          — thu hồi
  GET    /lich/<chìa>.ics           — CÔNG KHAI, ứng dụng lịch gọi

Tuyến `.ics` KHÔNG nằm dưới `/api/`: Google Calendar và Lịch iPhone thích một địa
chỉ kết thúc bằng `.ics`, và lớp proxy `/api/*` của frontend sẽ thêm một chặng
không cần thiết vào đường vốn bị gọi lại nhiều lần mỗi ngày.

BẢO MẬT — tuyến công khai nên phải tự đứng vững:
 · `authentication_classes = []` + `permission_classes = [AllowAny]`: không có
   phiên đăng nhập nào ở đây, và để nguyên mặc định thì lớp xác thực vẫn chạy rồi
   trả 401 cho ứng dụng lịch (nó sẽ im lặng bỏ lịch).
 · Chìa sai, chìa đã thu hồi, chìa của tài khoản đã khoá: CÙNG trả 404, không nói
   khác nhau.
 · Có giới hạn tốc độ theo chìa: ứng dụng lịch hỏi lại vài giờ một lần, nên ai gõ
   hàng trăm lượt một phút là đang dò.
 · `X-Robots-Tag: noindex` và `Cache-Control: private`: địa chỉ này không được lọt
   vào bộ nhớ đệm dùng chung hay công cụ tìm kiếm.
"""
from django.http import HttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from common import audit
from common.db import q1
from common.permissions import is_admin
from common.throttling import HourlyIPThrottle

from . import chia as chia_mod
from .doc import buoi_cua
from .ics import dung_ics

#: Vai được cấp địa chỉ lịch TOÀN TRUNG TÂM (mọi buổi của mọi lớp).
VAI_TRUNG_TAM = ('admin', 'Quản lý học vụ')


def _co_the_trung_tam(user):
    return is_admin(user) or getattr(user, 'role', None) in VAI_TRUNG_TAM


def _ten_lich(scope, ten_nguoi):
    if scope == 'trung_tam':
        return 'TopHSA — lịch toàn trung tâm'
    return 'TopHSA — lịch của %s' % (ten_nguoi or 'tôi')


class NhipDocLich(SimpleRateThrottle):
    """Giới hạn theo CHÌA, không theo địa chỉ mạng: nhiều em cùng một wifi nhà
    trọ đi chung một địa chỉ mạng, chặn theo đó là chặn oan cả nhóm."""
    scope = 'lich_ics'   # mức nằm ở settings.DEFAULT_THROTTLE_RATES, một nguồn

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope,
                                    'ident': (view.kwargs or {}).get('chia', '')[:64]}


class DiaChiLichView(APIView):
    """Người dùng tự cấp / xem / thu hồi địa chỉ lịch của chính mình."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        co = chia_mod.dang_co(request.user.id)
        return Response({
            'daCo': 'toi' in co,
            'daCoTrungTam': 'trung_tam' in co,
            'duocTrungTam': _co_the_trung_tam(request.user),
        })

    def post(self, request):
        body = request.data if isinstance(request.data, dict) else {}
        scope = 'trung_tam' if body.get('scope') == 'trung_tam' else 'toi'
        if scope == 'trung_tam' and not _co_the_trung_tam(request.user):
            return Response({'error': 'Chỉ quản trị viên và quản lý học vụ mới lấy được '
                                      'lịch toàn trung tâm.'}, status=403)
        chia = chia_mod.cap(request.user.id, scope)
        audit.record(request, audit.CALENDAR_LINK_NEW, target_type='user',
                     target_id=request.user.id,
                     summary='Cấp địa chỉ lịch (%s).' % ('toàn trung tâm' if scope == 'trung_tam' else 'cá nhân'))
        return Response({'duongDan': '/lich/%s.ics' % chia, 'scope': scope}, status=201)

    def delete(self, request):
        scope = 'trung_tam' if request.query_params.get('scope') == 'trung_tam' else 'toi'
        if not chia_mod.thu_hoi(request.user.id, scope):
            return Response({'error': 'Chưa có địa chỉ lịch nào để thu hồi.'}, status=404)
        audit.record(request, audit.CALENDAR_LINK_REVOKE, target_type='user',
                     target_id=request.user.id, summary='Thu hồi địa chỉ lịch.')
        return Response({'ok': True})


class TepLichView(APIView):
    """GET /lich/<chìa>.ics — ứng dụng lịch gọi, không đăng nhập."""
    authentication_classes = []
    permission_classes = [AllowAny]
    # Theo chìa VÀ theo địa chỉ mạng: khai `throttle_classes` là THAY hẳn bộ
    # mặc định, nên phải nêu lại lớp theo IP, không thì tuyến công khai này
    # thành cửa duy nhất không có trần chung.
    throttle_classes = [NhipDocLich, HourlyIPThrottle]

    def get(self, request, chia):
        link = chia_mod.tra(chia)
        if not link:
            return HttpResponse('Không tìm thấy lịch này.', status=404,
                                content_type='text/plain; charset=utf-8')
        nguoi = q1('SELECT name, status FROM users WHERE id = %s', (link['user_id'],))
        if not nguoi or nguoi['status'] != 'active':
            # Tài khoản bị khoá thì lịch tắt theo, và tắt GIỐNG chìa sai.
            return HttpResponse('Không tìm thấy lịch này.', status=404,
                                content_type='text/plain; charset=utf-8')
        buoi = buoi_cua(link['user_id'], link['scope'])
        chia_mod.ghi_luot_doc(link['id'])
        r = HttpResponse(dung_ics(buoi, _ten_lich(link['scope'], nguoi['name'])),
                         content_type='text/calendar; charset=utf-8')
        r['Content-Disposition'] = 'inline; filename="tophsa.ics"'
        r['Cache-Control'] = 'private, max-age=600'
        r['X-Robots-Tag'] = 'noindex, nofollow'
        return r
