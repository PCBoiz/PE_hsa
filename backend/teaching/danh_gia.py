"""ĐÁNH GIÁ MỘT EM TRONG LỚP — nhận xét gửi phụ huynh, cờ "cần hỗ trợ", đề xuất hướng học.

── VÌ SAO CÓ (25/09/2026, kế hoạch v2 V-a + V-f) ─────────────────────────────

Bảng yêu cầu TopHSA dòng 18 ("Giáo viên · theo dõi học sinh"): ghi nhận xét học sinh,
đánh dấu cần hỗ trợ, đề xuất hướng học. Tới hôm nay không màn nào ghi được nhận xét —
cột duy nhất tờ phụ huynh in (`class_members.note`) lại là ghi chú NỘI BỘ bị chuyển lớp
dùng chung (lỗi rò đã vá ở e328ade bằng cột riêng `teacher_comment`, §62a). Dòng 21
("Trợ giảng · theo dõi"): trợ giảng báo được em nào cần hỗ trợ.

── AI GHI ĐƯỢC GÌ ─────────────────────────────────────────────────────────────

  · nhận xét (`teacherComment`) và đề xuất hướng học (`deXuatHuongHoc`):
    `IsSeniorTeachingStaff` — giảng viên lớp mình, học vụ, quản trị. Nhận xét IN LÊN tờ
    gửi phụ huynh (`parent_report.dung_bao_cao` → `membership.teacherNote`), nên cùng
    cổng với chính tờ ấy.
  · cờ cần hỗ trợ (`canHoTro` + `lyDo`): cả trợ giảng của lớp (`IsTeachingStaff`).
Trợ giảng gửi kèm một trường không phải của mình → 403 cho CẢ yêu cầu, không ghi nửa
chừng phần cờ: một yêu cầu bị từ chối mà vẫn đổi dữ liệu là thứ người gửi không biết.

── GHI VÀO ĐÂU ────────────────────────────────────────────────────────────────

Lượt học ĐANG MỞ của em ở lớp ấy; em đã rời thì lượt MỚI NHẤT (nhận xét tổng kết cuối
khoá vẫn ghi được). Tờ phụ huynh đọc nhận xét muộn nhất qua mọi lượt, nên hai bên khớp.
KHÔNG BAO GIỜ ghi `note` — đó là ghi chú nội bộ (lý do rời, ghi chú chuyển lớp).

Cờ và hướng học là NỘI BỘ: không vào tờ phụ huynh, không vào đường dẫn công khai. Chúng
hiện ở "Việc hôm nay" (`viec_hom_nay.canHoTro`) và dòng thời gian của em (đọc từ nhật
ký hành động `class.member.assess` — thấy được CẢ lịch sử ai đánh dấu, lúc nào).
"""
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from common import audit
from common.clock import local_now
from common.db import q1, x
from common.permissions import IsSeniorTeachingStaff, IsTeachingStaff, can_see_class
from teaching.vocab import chi_hoc_vien

#: Độ dài tối đa từng ô. Nhận xét là một đoạn văn gửi về nhà; lý do và hướng học ngắn hơn.
DAI = {'teacherComment': 2000, 'lyDo': 500, 'deXuatHuongHoc': 1000}
#: Trường chỉ vai trên trợ giảng ghi được.
CHI_GIANG_VIEN = ('teacherComment', 'deXuatHuongHoc')

_KHONG_THAY_LOP = {'error': 'Không tìm thấy lớp này.'}
_KHONG_THAY_EM = {'error': 'Không tìm thấy học viên này trong lớp.'}


def _luot(class_id, user_id, khoa=False):
    """Lượt học để ghi: đang mở trước, rồi mới nhất. Chỉ tài khoản vai Học viên."""
    return q1('''SELECT m.id, m.teacher_comment, m.teacher_comment_at, m.can_ho_tro,
                        m.can_ho_tro_ly_do, m.can_ho_tro_at, m.de_xuat_huong_hoc,
                        m.de_xuat_huong_hoc_at,
                        u.name AS em, c.name AS lop,
                        tb.name AS teacher_comment_boi, cb.name AS can_ho_tro_boi,
                        hb.name AS de_xuat_boi
                   FROM class_members m
                   JOIN users u ON u.id = m.user_id
                   JOIN classes c ON c.id = m.class_id
                   LEFT JOIN users tb ON tb.id = m.teacher_comment_by
                   LEFT JOIN users cb ON cb.id = m.can_ho_tro_by
                   LEFT JOIN users hb ON hb.id = m.de_xuat_huong_hoc_by
                  WHERE m.class_id = %s AND m.user_id = %s AND ''' + chi_hoc_vien('u') + '''
                  ORDER BY (m.left_at IS NULL) DESC, m.joined_at DESC, m.id DESC
                  LIMIT 1''' + (' FOR UPDATE OF m' if khoa else ''), (class_id, user_id))


def _iso(v):
    return v.isoformat() if v else None


def _ra(r, cap_tren):
    """Phản hồi. Trợ giảng chỉ nhận phần cờ — nhận xét và hướng học không phải việc của vai ấy."""
    ra = {'canHoTro': bool(r['can_ho_tro']), 'lyDo': r['can_ho_tro_ly_do'],
          'canHoTroAt': _iso(r['can_ho_tro_at']), 'canHoTroBy': r['can_ho_tro_boi'],
          'quyen': {'nhanXet': cap_tren}}
    if cap_tren:
        ra.update({
            'teacherComment': r['teacher_comment'], 'teacherCommentAt': _iso(r['teacher_comment_at']),
            'teacherCommentBy': r['teacher_comment_boi'],
            'deXuatHuongHoc': r['de_xuat_huong_hoc'], 'deXuatHuongHocAt': _iso(r['de_xuat_huong_hoc_at']),
            'deXuatHuongHocBy': r['de_xuat_boi'],
        })
    return ra


def _chu(v, ten):
    """Ô chữ: None/'' → None (xoá); cắt khoảng trắng; quá dài → lỗi (KHÔNG cắt im)."""
    if v is None:
        return None, None
    if not isinstance(v, str):
        return None, 'Ô "%s" phải là chữ.' % ten
    v = v.strip()
    if len(v) > DAI[ten]:
        return None, 'Ô "%s" dài quá %d ký tự.' % (ten, DAI[ten])
    return v or None, None


class DanhGiaHocVienView(APIView):
    """GET/PUT /api/teach/classes/<class_id>/students/<user_id>/danh-gia."""
    permission_classes = [IsTeachingStaff]

    def _cap_tren(self, request):
        return IsSeniorTeachingStaff().has_permission(request, self)

    def get(self, request, class_id, user_id):
        # 404 chứ không 403 cho lớp không phụ trách — quy ước cả `teaching/`.
        if not can_see_class(request.user, class_id):
            return Response(_KHONG_THAY_LOP, status=404)
        r = _luot(class_id, user_id)
        if not r:
            return Response(_KHONG_THAY_EM, status=404)
        return Response(_ra(r, self._cap_tren(request)))

    def put(self, request, class_id, user_id):
        if not can_see_class(request.user, class_id):
            return Response(_KHONG_THAY_LOP, status=404)
        body = request.data if isinstance(request.data, dict) else {}
        cap_tren = self._cap_tren(request)
        if not cap_tren and any(k in body for k in CHI_GIANG_VIEN):
            return Response({'error': 'Trợ giảng chỉ đánh dấu được "cần hỗ trợ". Nhận xét gửi phụ '
                                      'huynh và đề xuất hướng học do giảng viên phụ trách lớp ghi.'},
                            status=403)

        doi, loi = {}, None
        if 'teacherComment' in body:
            doi['teacher_comment'], loi = _chu(body['teacherComment'], 'teacherComment')
        if not loi and 'deXuatHuongHoc' in body:
            doi['de_xuat_huong_hoc'], loi = _chu(body['deXuatHuongHoc'], 'deXuatHuongHoc')
        if not loi and 'canHoTro' in body:
            if not isinstance(body['canHoTro'], bool):
                loi = 'canHoTro phải là true hoặc false.'
            else:
                doi['can_ho_tro'] = body['canHoTro']
                # Bỏ đánh dấu thì bỏ luôn lý do — lý do cũ treo trên một em không còn
                # bị đánh dấu là câu không ai biết còn đúng không.
                doi['can_ho_tro_ly_do'], loi = ((_chu(body.get('lyDo'), 'lyDo'))
                                                if body['canHoTro'] else (None, None))
        elif not loi and 'lyDo' in body:
            loi = 'Gửi lý do kèm canHoTro: true.'
        if loi:
            return Response({'error': loi}, status=400)
        if not doi:
            return Response({'error': 'Không có ô nào để lưu (teacherComment, canHoTro, lyDo, '
                                      'deXuatHuongHoc).'}, status=400)

        nay = local_now()
        with transaction.atomic():
            r = _luot(class_id, user_id, khoa=True)
            if not r:
                return Response(_KHONG_THAY_EM, status=404)
            cot = dict(doi)
            # Người ghi + lúc ghi đi theo TỪNG nhóm ô, không chung một dấu: trợ giảng đánh
            # dấu không được thành "người viết nhận xét".
            for nhom, dau in (('teacher_comment', 'teacher_comment'),
                              ('de_xuat_huong_hoc', 'de_xuat_huong_hoc'),
                              ('can_ho_tro', 'can_ho_tro')):
                if nhom in doi:
                    cot[dau + '_by'] = request.user.id
                    cot[dau + '_at'] = nay
            x('UPDATE class_members SET %s WHERE id = %%s' % ', '.join('%s = %%s' % k for k in cot),
              tuple(cot.values()) + (r['id'],))

        # Nhật ký SAU giao dịch — `record` tự bọc savepoint và không bao giờ ném.
        chi_tiet = {'classId': class_id, 'className': r['lop']}
        if 'can_ho_tro' in doi:
            chi_tiet.update(canHoTro=doi['can_ho_tro'], lyDo=doi['can_ho_tro_ly_do'])
        if 'de_xuat_huong_hoc' in doi:
            chi_tiet['deXuatHuongHoc'] = doi['de_xuat_huong_hoc']
        if 'teacher_comment' in doi:
            chi_tiet['teacherComment'] = doi['teacher_comment']
        audit.record(request, audit.CLASS_MEMBER_ASSESS, target_type='user', target_id=user_id,
                     target_label=r['em'],
                     summary='Đánh giá "%s" lớp %s: %s.' % (
                         r['em'], r['lop'], ', '.join(ten for k, ten in (
                             ('teacher_comment', 'nhận xét gửi phụ huynh'),
                             ('can_ho_tro', 'cần hỗ trợ'),
                             ('de_xuat_huong_hoc', 'đề xuất hướng học')) if k in doi) or '—'),
                     detail=chi_tiet)
        return Response(_ra(_luot(class_id, user_id), cap_tren))
