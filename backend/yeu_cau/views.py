"""Tuyến của hộp Yêu cầu (E3). Mỏng: đọc thân, gọi `dich_vu`, đổi `LoiYeuCau` thành HTTP.

- học viên   `/api/yeu-cau…`                          (`LaHocVien`)
- nhân sự    `/api/teach/yeu-cau…`                    (`IsTeachingStaff`, lọc `pham_vi_yeu_cau`)
- học vụ     `/api/admin/yeu-cau/<id>/(giao|duyet|tu-choi)` (`IsAdminOrAcademic`)
- phụ huynh  `/api/public/phu-huynh/<token>/yeu-cau`  (không tài khoản, tra chìa như tờ báo cáo)
"""
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from common.clock import local_now
from common.db import q
from common.permissions import (
    ROLE_ACADEMIC,
    ROLE_ADMIN,
    ROLE_ASSISTANT,
    ROLE_STUDENT,
    ROLE_TEACHER,
    IsAdminOrAcademic,
    IsTeachingStaff,
    visible_class_ids,
)
from common.throttling import _IPKhach
from teaching.parent_link import _cua_ai
from yeu_cau import dich_vu as dv
from yeu_cau import loai as L

KHONG_CON_DUNG = 'Đường dẫn này không còn dùng được. Liên hệ trung tâm để nhận đường dẫn mới.'


class LaHocVien(BasePermission):
    """Khu "Hỏi / Yêu cầu" của học viên. Nhân sự đi `/api/teach/yeu-cau`."""

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.role == ROLE_STUDENT)


def _loi(e):
    return Response({'error': e.cau}, status=e.ma)


def _body(request):
    return request.data if isinstance(request.data, dict) else {}


def _tao_tu_body(nguoi, body, request):
    return dv.tao(nguoi, loai=body.get('loai'), tieu_de=body.get('tieu_de'),
                  noi_dung=body.get('noi_dung'), class_id=body.get('class_id'),
                  session_id=body.get('session_id'), hoc_vien_id=body.get('hoc_vien_id'),
                  du_lieu=body.get('du_lieu'), request=request)


def _lua_chon_loai(nguon):
    return [{'code': k, 'nhan': L.LOAI[k]['nhan'], 'nhom': L.LOAI[k]['nhom'],
             'canLop': bool(L.LOAI[k].get('can_lop')), 'canBuoi': bool(L.LOAI[k].get('can_buoi')),
             'canDuyet': L.la_thay_doi(k)} for k in L.TAO_DUOC[nguon]]


def _loc(request):
    p = request.query_params
    loai = p.get('loai') if p.get('loai') in L.LOAI else None
    tt = p.get('trang_thai') if p.get('trang_thai') in L.TRANG_THAI else None
    try:
        lop = int(p.get('class_id')) if p.get('class_id') else None
    except ValueError:
        lop = None
    return {'loai': loai, 'trang_thai': tt, 'class_id': lop, 'cua_toi': p.get('cua_toi') == '1',
            'mo': p.get('mo') == '1'}


# ── Học viên ──────────────────────────────────────────────────────────────

class YeuCauCuaToiView(APIView):
    """GET/POST /api/yeu-cau — yêu cầu về em / do em tạo; tạo mới."""
    permission_classes = [LaHocVien]

    def get(self, request):
        return Response({'yeuCau': dv.danh_sach(dv.NguoiLam(user=request.user))})

    def post(self, request):
        try:
            return Response(_tao_tu_body(dv.NguoiLam(user=request.user), _body(request), request), status=201)
        except dv.LoiYeuCau as e:
            return _loi(e)


class LuaChonHocVienView(APIView):
    """GET /api/yeu-cau/lua-chon — loại em gửi được, lớp của em, buổi gần đây (báo lỗi bản ghi)."""
    permission_classes = [LaHocVien]

    def get(self, request):
        lop = q('''SELECT DISTINCT ON (c.id) c.id, c.name, (m.left_at IS NULL) AS dang_hoc
                   FROM class_members m JOIN classes c ON c.id = m.class_id
                   WHERE m.user_id = %s ORDER BY c.id, (m.left_at IS NULL) DESC''', (request.user.id,))
        dang = [r['id'] for r in lop if r['dang_hoc']]
        buoi = q('''SELECT s.id, s.class_id, s.starts_at, s.topic, (s.recording_url IS NOT NULL
                           AND s.recording_url <> '') AS co_ban_ghi
                    FROM class_sessions s
                    WHERE s.class_id = ANY(%s) AND s.starts_at <= %s AND s.status <> 'cancelled'
                    ORDER BY s.starts_at DESC LIMIT 30''', (dang, local_now())) if dang else []
        return Response({
            'loai': _lua_chon_loai('hoc_vien'),
            'lop': [{'id': r['id'], 'ten': r['name'], 'dangHoc': r['dang_hoc']} for r in lop],
            'buoi': [{'id': r['id'], 'classId': r['class_id'], 'luc': r['starts_at'].isoformat(),
                      'chuDe': r['topic'], 'coBanGhi': r['co_ban_ghi']} for r in buoi],
        })


class YeuCauCuaToiChiTietView(APIView):
    """GET /api/yeu-cau/<id> — chi tiết + luồng trả lời (không có ghi chú nội bộ)."""
    permission_classes = [LaHocVien]

    def get(self, request, yc_id):
        try:
            return Response(dv.chi_tiet(dv.NguoiLam(user=request.user), yc_id))
        except dv.LoiYeuCau as e:
            return _loi(e)


class HocVienTraLoiView(APIView):
    """POST /api/yeu-cau/<id>/tra-loi {noi_dung}."""
    permission_classes = [LaHocVien]

    def post(self, request, yc_id):
        try:
            return Response(dv.tra_loi(dv.NguoiLam(user=request.user), yc_id, _body(request).get('noi_dung'),
                                       request=request))
        except dv.LoiYeuCau as e:
            return _loi(e)


class HocVienHuyView(APIView):
    """POST /api/yeu-cau/<id>/huy — rút yêu cầu khi còn "Mới"."""
    permission_classes = [LaHocVien]

    def post(self, request, yc_id):
        try:
            return Response(dv.chuyen_trang_thai(dv.NguoiLam(user=request.user), yc_id, 'da_huy',
                                                 request=request))
        except dv.LoiYeuCau as e:
            return _loi(e)


# ── Nhân sự ───────────────────────────────────────────────────────────────

def _nguon_nhan_su(user):
    return dv.NguoiLam(user=user).nguon


class YeuCauNhanSuView(APIView):
    """GET/POST /api/teach/yeu-cau — danh sách theo phạm vi (lọc loai, trang_thai, class_id,
    cua_toi=1, mo=1); tạo (TG/GV: báo lên, báo lỗi bản ghi, thay đổi cho em trong lớp)."""
    permission_classes = [IsTeachingStaff]

    def get(self, request):
        nguoi = dv.NguoiLam(user=request.user)
        return Response({'yeuCau': dv.danh_sach(nguoi, **_loc(request)),
                         'coTheDuyet': nguoi.la_duyet})

    def post(self, request):
        try:
            return Response(_tao_tu_body(dv.NguoiLam(user=request.user), _body(request), request), status=201)
        except dv.LoiYeuCau as e:
            return _loi(e)


class LuaChonNhanSuView(APIView):
    """GET /api/teach/yeu-cau/lua-chon — loại tạo được, lớp trong phạm vi, nhãn trạng thái."""
    permission_classes = [IsTeachingStaff]

    def get(self, request):
        ids = visible_class_ids(request.user)
        lop = q('SELECT id, name FROM classes WHERE id = ANY(%s) ORDER BY name', (ids,)) if ids else []
        return Response({
            'loai': _lua_chon_loai(_nguon_nhan_su(request.user)),
            'tatCaLoai': [{'code': k, 'nhan': v['nhan'], 'canDuyet': L.la_thay_doi(k)}
                          for k, v in L.LOAI.items()],
            'trangThai': [{'code': k, 'nhan': L.NHAN_TRANG_THAI[k]} for k in L.TRANG_THAI],
            'lop': [{'id': r['id'], 'ten': r['name']} for r in lop],
        })


class YeuCauNhanSuChiTietView(APIView):
    """GET /api/teach/yeu-cau/<id> — chi tiết + mọi sự kiện (kể cả nội bộ); ngoài phạm vi 404."""
    permission_classes = [IsTeachingStaff]

    def get(self, request, yc_id):
        try:
            return Response(dv.chi_tiet(dv.NguoiLam(user=request.user), yc_id))
        except dv.LoiYeuCau as e:
            return _loi(e)


class NhanSuTraLoiView(APIView):
    """POST /api/teach/yeu-cau/<id>/tra-loi {noi_dung, noi_bo}."""
    permission_classes = [IsTeachingStaff]

    def post(self, request, yc_id):
        b = _body(request)
        try:
            return Response(dv.tra_loi(dv.NguoiLam(user=request.user), yc_id, b.get('noi_dung'),
                                       noi_bo=bool(b.get('noi_bo')), request=request))
        except dv.LoiYeuCau as e:
            return _loi(e)


class NhanSuTrangThaiView(APIView):
    """POST /api/teach/yeu-cau/<id>/trang-thai {den, ket_qua}."""
    permission_classes = [IsTeachingStaff]

    def post(self, request, yc_id):
        b = _body(request)
        try:
            return Response(dv.chuyen_trang_thai(dv.NguoiLam(user=request.user), yc_id, b.get('den'),
                                                 ket_qua=b.get('ket_qua'), request=request))
        except dv.LoiYeuCau as e:
            return _loi(e)


class ChuyenTiepView(APIView):
    """POST /api/teach/yeu-cau/<id>/chuyen-tiep {nguoi_xu_ly_id | null, ghi_chu}."""
    permission_classes = [IsTeachingStaff]

    def post(self, request, yc_id):
        b = _body(request)
        try:
            return Response(dv.giao(dv.NguoiLam(user=request.user), yc_id, b.get('nguoi_xu_ly_id'),
                                    ghi_chu=b.get('ghi_chu'), request=request))
        except dv.LoiYeuCau as e:
            return _loi(e)


class NguoiNhanView(APIView):
    """GET /api/teach/yeu-cau/<id>/nguoi-nhan — ai nhận được yêu cầu này (GV + TG của lớp,
    học vụ). Hỗ trợ tài khoản: chỉ học vụ."""
    permission_classes = [IsTeachingStaff]

    def get(self, request, yc_id):
        nguoi = dv.NguoiLam(user=request.user)
        try:
            yc = dv.chi_tiet(nguoi, yc_id)
        except dv.LoiYeuCau as e:
            return _loi(e)
        ds = q("SELECT id, name, email, role FROM users WHERE role = ANY(%s) "
               "AND COALESCE(status, 'active') = 'active' ORDER BY role, name",
               ([ROLE_ACADEMIC, ROLE_ADMIN],))
        if yc['lop'] and yc['loai'] != 'ht_tai_khoan':
            ds += q('''SELECT u.id, u.name, u.email, u.role FROM users u
                       WHERE u.id = (SELECT teacher_id FROM classes WHERE id = %s)
                       UNION
                       SELECT u.id, u.name, u.email, u.role FROM class_members m
                       JOIN users u ON u.id = m.user_id
                       WHERE m.class_id = %s AND m.left_at IS NULL AND u.role = %s''',
                    (yc['lop']['id'], yc['lop']['id'], ROLE_ASSISTANT))
        vai = {ROLE_ADMIN: 'Quản trị viên', ROLE_ACADEMIC: 'Học vụ', ROLE_TEACHER: 'Giảng viên',
               ROLE_ASSISTANT: 'Trợ giảng'}
        return Response({'nguoi': [{'id': r['id'], 'ten': r['name'] or r['email'],
                                    'vai': vai.get(r['role'], r['role'])} for r in ds]})


# ── Học vụ / quản trị ────────────────────────────────────────────────────

class GiaoView(APIView):
    """POST /api/admin/yeu-cau/<id>/giao {nguoi_xu_ly_id | null, ghi_chu}."""
    permission_classes = [IsAdminOrAcademic]

    def post(self, request, yc_id):
        b = _body(request)
        try:
            return Response(dv.giao(dv.NguoiLam(user=request.user), yc_id, b.get('nguoi_xu_ly_id'),
                                    ghi_chu=b.get('ghi_chu'), request=request))
        except dv.LoiYeuCau as e:
            return _loi(e)


class DuyetView(APIView):
    """GET  /api/admin/yeu-cau/<id>/duyet?den_lop_id=&den_ngay= — xem trước việc sẽ làm.
    POST /api/admin/yeu-cau/<id>/duyet {den_lop_id?, den_ngay?, ket_qua?} — duyệt = thực thi."""
    permission_classes = [IsAdminOrAcademic]

    def get(self, request, yc_id):
        p = request.query_params
        try:
            return Response(dv.xem_truoc(dv.NguoiLam(user=request.user), yc_id,
                                         {'den_lop_id': p.get('den_lop_id'), 'den_ngay': p.get('den_ngay')}))
        except dv.LoiYeuCau as e:
            return _loi(e)

    def post(self, request, yc_id):
        b = _body(request)
        try:
            return Response(dv.duyet(dv.NguoiLam(user=request.user), yc_id,
                                     {'den_lop_id': b.get('den_lop_id'), 'den_ngay': b.get('den_ngay')},
                                     ket_qua=b.get('ket_qua'), request=request))
        except dv.LoiYeuCau as e:
            return _loi(e)


class TuChoiView(APIView):
    """POST /api/admin/yeu-cau/<id>/tu-choi {ket_qua}."""
    permission_classes = [IsAdminOrAcademic]

    def post(self, request, yc_id):
        try:
            return Response(dv.chuyen_trang_thai(dv.NguoiLam(user=request.user), yc_id, 'tu_choi',
                                                 ket_qua=_body(request).get('ket_qua'), request=request))
        except dv.LoiYeuCau as e:
            return _loi(e)


class LopChuyenToiView(APIView):
    """GET /api/admin/yeu-cau/<id>/lop — lớp đang mở để chọn khi duyệt chuyển lớp / môn."""
    permission_classes = [IsAdminOrAcademic]

    def get(self, request, yc_id):
        try:
            dv.chi_tiet(dv.NguoiLam(user=request.user), yc_id)
        except dv.LoiYeuCau as e:
            return _loi(e)
        rows = q('''SELECT c.id, c.name, c.class_type, c.status, co.title AS mon
                    FROM classes c LEFT JOIN courses co ON co.id = c.course_id
                    WHERE c.status NOT IN ('cancelled', 'finished') ORDER BY c.name''')
        return Response({'lop': [{'id': r['id'], 'ten': r['name'], 'giaSu': r['class_type'] == 'gia_su',
                                  'mon': r['mon']} for r in rows]})


# ── Phụ huynh (link, không tài khoản) ─────────────────────────────────────

class GuiYeuCauPhuHuynhThrottle(_IPKhach, SimpleRateThrottle):
    """Trần GỬI theo IP cho đường phụ huynh — chỉ tính POST (đọc đi theo trần mặc định)."""
    scope = 'yeu_cau_ph'
    rate = '20/hour'

    def allow_request(self, request, view):
        if request.method != 'POST':
            return True
        return super().allow_request(request, view)

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class PhuHuynhYeuCauView(APIView):
    """GET/POST /api/public/phu-huynh/<token>/yeu-cau.

    Tra chìa ĐÚNG như tờ báo cáo phụ huynh (`teaching/parent_link.py::_cua_ai`): chìa lạ, hết
    hạn, bị thu hồi → CÙNG MỘT câu 404. `authentication_classes = []` vì cùng lý do với tờ báo
    cáo (cookie hết hạn trên máy phụ huynh không được làm đổ 401).
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_throttles(self):
        return super().get_throttles() + [GuiYeuCauPhuHuynhThrottle()]

    def _link(self, token):
        d, tu_choi = _cua_ai(token)
        return None if tu_choi else d

    def get(self, request, token):
        d = self._link(token)
        if not d:
            return Response({'error': KHONG_CON_DUNG}, status=404)
        nguoi = dv.NguoiLam(link=d)
        return Response({'yeuCau': [dict(y, suKien=dv.su_kien_cua(nguoi, y['id']))
                                    for y in dv.danh_sach(nguoi, tran=20)],
                         'loai': _lua_chon_loai('phu_huynh'), 'tranMo': L.TRAN_MO_PHU_HUYNH})

    def post(self, request, token):
        d = self._link(token)
        if not d:
            return Response({'error': KHONG_CON_DUNG}, status=404)
        b = _body(request)
        du_lieu = b.get('du_lieu') if isinstance(b.get('du_lieu'), dict) else {}
        try:
            # Phụ huynh không chọn lớp / em / buổi — lấy từ chìa (`dich_vu.tao`).
            return Response(dv.tao(dv.NguoiLam(link=d), loai=b.get('loai'), tieu_de=b.get('tieu_de'),
                                   noi_dung=b.get('noi_dung'), du_lieu=du_lieu, request=request),
                            status=201)
        except dv.LoiYeuCau as e:
            return _loi(e)

