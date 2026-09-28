"""HỌC LIỆU CỦA LỚP (§60, Đ2 — bảng TopHSA dòng 30, và phần tài liệu của dòng 15).

  GET    /api/teach/classes/<id>/hoc-lieu        — xem (giảng viên / trợ giảng / học viên)
  POST   /api/teach/classes/<id>/hoc-lieu        — gắn tài liệu (khu giảng dạy)
  PATCH  /api/teach/classes/<id>/hoc-lieu/<tid>  — sửa tên / mô tả / ẩn–hiện
  DELETE /api/teach/classes/<id>/hoc-lieu/<tid>  — gỡ

Anh Sơn chốt 26/09: làm **liên kết ngoài** trước (Drive, YouTube, link đề) — nó không chờ
khoá Cloudflare R2 — và gắn được vào **cả kho chung của lớp lẫn từng buổi**.

── MỘT CỬA CHO HAI PHÍA, VÀ VÌ SAO ──────────────────────────────────────────

Cùng một đường dẫn phục vụ cả người gắn lẫn người xem, chỉ khác NỘI DUNG trả về: giảng
viên thấy cả tài liệu đang ẩn, học viên chỉ thấy phần đã mở và chỉ những buổi mình thuộc.
Hai đường riêng thì luật "ai thấy cái gì" nằm ở hai chỗ, và một ngày nào đó chúng lệch
nhau — đúng chuyện đã xảy ra với §72 (bốn cửa, ba cửa quên buổi bù).

── HAI CHỖ DỄ HỎNG, ĐÃ CÓ NGƯỜI CANH ────────────────────────────────────────

① **Buổi bù.** Tài liệu gắn vào một buổi chỉ tới em THUỘC buổi ấy — dùng `thuoc_buoi`
  (§62e) chứ không phải "cùng lớp là thấy". Đây là lỗ agent soát tìm ra trong §72 ngày
  26/09; lần này phép kiểm viết TRƯỚC khi viết mã (`tests_hoc_lieu.py` §4).

② **Địa chỉ nhập tay.** Ô này là chữ người dùng gõ, rồi màn dựng thành `<a href>` cho
  người KHÁC bấm. `javascript:` và `data:` trong `href` chạy mã ngay trong phiên của
  người bấm — đúng hình dạng của hai lỗ stored-XSS từng nằm trong tầng JS cũ của repo.
  Nên: danh sách CHO PHÉP (`http`, `https`), không phải danh sách cấm. Danh sách cấm bao
  giờ cũng thiếu một lược đồ nào đó, và `vbscript:` hay `data:` chỉ là hai cái nhớ ra được.
"""
from urllib.parse import urlsplit

from rest_framework.response import Response
from rest_framework.views import APIView

from common.db import q, q1, x
from common.permissions import IsTeachingStaff, can_see_class
from common.views import NguoiDungView
from teaching.nguoi_buoi import thuoc_buoi

#: Lược đồ địa chỉ cho phép. DANH SÁCH CHO PHÉP, không phải danh sách cấm.
LUOC_DO = ('http', 'https')

TRAN_TEN = 200
TRAN_MO_TA = 2000
TRAN_URL = 2000


def _body(request):
    return request.data if isinstance(request.data, dict) else {}


def dia_chi_hop_le(url: str) -> bool:
    """`url` có phải một địa chỉ web bấm được không?

    Đòi có lược đồ trong `LUOC_DO` VÀ có tên miền. Thiếu tên miền thì `https:///x` lọt
    qua phép kiểm lược đồ mà chẳng trỏ đi đâu.
    """
    try:
        p = urlsplit((url or '').strip())
    except ValueError:
        return False
    return p.scheme.lower() in LUOC_DO and bool(p.netloc)


def _doc(d, cu=None):
    """(giá trị đã làm sạch, lỗi theo ô). `cu` có nghĩa là đang SỬA — ô vắng thì giữ nguyên."""
    loi = {}
    ten = str(d.get('ten', cu['ten'] if cu else '') or '').strip()
    if not ten:
        loi['ten'] = 'Nhập tên tài liệu.'
    elif len(ten) > TRAN_TEN:
        loi['ten'] = 'Tên dài quá %d ký tự.' % TRAN_TEN

    mo_ta = str(d.get('moTa', cu['mo_ta'] if cu else '') or '').strip()
    if len(mo_ta) > TRAN_MO_TA:
        loi['moTa'] = 'Mô tả dài quá %d ký tự.' % TRAN_MO_TA

    url = str(d.get('url', cu['url'] if cu else '') or '').strip()
    if len(url) > TRAN_URL:
        loi['url'] = 'Địa chỉ dài quá %d ký tự.' % TRAN_URL
    elif not dia_chi_hop_le(url):
        # Câu này hiện thẳng trên màn nên nói bằng lời người dùng, không nói "scheme"
        # hay "URL scheme" (RULES §10).
        loi['url'] = 'Dán địa chỉ bắt đầu bằng http:// hoặc https:// (ví dụ link Google Drive).'
    return {'ten': ten, 'mo_ta': mo_ta or None, 'url': url}, loi


def _hinh(r):
    return {'id': r['id'], 'ten': r['ten'], 'moTa': r['mo_ta'], 'nguon': r['nguon'],
            'url': r['url'], 'an': bool(r['an']), 'sessionId': r['session_id'],
            'buoiLuc': r.get('buoi_luc'), 'nguoiTao': r.get('nguoi_tao_ten'),
            'luc': r['created_at']}


def _la_hoc_vien_dang_hoc(user, class_id) -> bool:
    """Em CÒN trong lớp. `left_at IS NULL` — rời lớp là hết quyền xem, như §72."""
    return bool(q1('''SELECT 1 FROM class_members
                       WHERE class_id = %s AND user_id = %s AND left_at IS NULL''',
                   (class_id, user.id)))


def danh_sach(class_id, user, day_du: bool):
    """Tài liệu của lớp. `day_du` = người của khu giảng dạy (thấy cả phần đang ẩn).

    Học viên: bỏ phần đang ẩn, và bỏ tài liệu của buổi mình KHÔNG thuộc (buổi bù).
    """
    dieu_kien = '' if day_du else (
        ' AND NOT h.an AND (h.session_id IS NULL OR ' + thuoc_buoi('h.session_id', '%s') + ')')
    tham = (class_id,) if day_du else (user.id, class_id)
    return q('''SELECT h.id, h.ten, h.mo_ta, h.nguon, h.url, h.an, h.session_id,
                       h.created_at, s.starts_at AS buoi_luc, u.name AS nguoi_tao_ten
                  FROM hoc_lieu h
                  LEFT JOIN class_sessions s ON s.id = h.session_id
                  LEFT JOIN users u ON u.id = h.nguoi_tao
                 WHERE h.class_id = %s''' + dieu_kien + '''
              ORDER BY h.session_id NULLS FIRST, h.created_at DESC''',
             tham[::-1] if not day_du else tham)


class HocLieuLopView(NguoiDungView):
    """Xem thì mọi vai liên quan; gắn thì chỉ khu giảng dạy.

    `NguoiDungView` (chỉ đòi đăng nhập) chứ không phải `IsTeachingStaff`: học viên cũng
    gọi đúng đường dẫn này. Cổng quyền nằm trong thân hàm, nơi phân biệt được "giảng viên
    của lớp" với "em đang học lớp" — hai thứ `permission_classes` không nói nổi.
    """

    def get(self, request, class_id):
        day_du = can_see_class(request.user, class_id)
        if not day_du and not _la_hoc_vien_dang_hoc(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        return Response({'items': [_hinh(r) for r in danh_sach(class_id, request.user, day_du)],
                         'coTheGan': day_du})

    def post(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        if not IsTeachingStaff().has_permission(request, self):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        d = _body(request)
        gia_tri, loi = _doc(d)
        buoi = d.get('sessionId') or None
        if buoi and not q1('SELECT 1 FROM class_sessions WHERE id = %s AND class_id = %s',
                           (buoi, class_id)):
            # Buổi của lớp KHÁC: nói "không thuộc lớp này", đừng nói "không tồn tại" —
            # câu sau là một cách dò xem buổi nào có thật.
            loi['sessionId'] = 'Buổi học này không thuộc lớp.'
        if loi:
            return Response({'errors': loi}, status=400)
        r = q1('''INSERT INTO hoc_lieu (class_id, session_id, ten, mo_ta, nguon, url, an, nguoi_tao)
                  VALUES (%s, %s, %s, %s, 'link', %s, %s, %s)
                  RETURNING id, ten, mo_ta, nguon, url, an, session_id, created_at''',
               (class_id, buoi, gia_tri['ten'], gia_tri['mo_ta'], gia_tri['url'],
                bool(d.get('an')), request.user.id))
        return Response(_hinh(r), status=201)


class HocLieuMotView(APIView):
    """Sửa / gỡ MỘT tài liệu. Chỉ khu giảng dạy, và chỉ trong lớp mình."""
    permission_classes = [IsTeachingStaff]

    def _cua_lop(self, class_id, tid):
        return q1('SELECT * FROM hoc_lieu WHERE id = %s AND class_id = %s', (tid, class_id))

    def patch(self, request, class_id, tid):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        cu = self._cua_lop(class_id, tid)
        if not cu:
            return Response({'error': 'Không tìm thấy tài liệu này.'}, status=404)
        d = _body(request)
        gia_tri, loi = _doc(d, cu)
        if loi:
            return Response({'errors': loi}, status=400)
        r = q1('''UPDATE hoc_lieu SET ten = %s, mo_ta = %s, url = %s, an = %s, updated_at = now()
                   WHERE id = %s
               RETURNING id, ten, mo_ta, nguon, url, an, session_id, created_at''',
               (gia_tri['ten'], gia_tri['mo_ta'], gia_tri['url'],
                bool(d.get('an', cu['an'])), tid))
        return Response(_hinh(r))

    def delete(self, request, class_id, tid):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        if not self._cua_lop(class_id, tid):
            # Số id đúng nhưng lớp trên đường dẫn sai cũng vào đây — không xoá gì cả.
            return Response({'error': 'Không tìm thấy tài liệu này.'}, status=404)
        x('DELETE FROM hoc_lieu WHERE id = %s AND class_id = %s', (tid, class_id))
        return Response({'ok': True})
