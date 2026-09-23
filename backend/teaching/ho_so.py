"""HỒ SƠ HỌC VIÊN MỞ RỘNG — mã học viên, trường/lớp/khu vực, người tư vấn,
nguồn tuyển sinh, mục tiêu, nguyện vọng; và username để đăng nhập.

── VÌ SAO CÓ TỆP NÀY (23/09/2026) ────────────────────────────────────────────

Bảng yêu cầu của TopHSA (dòng 3 và tab "Nhi" — người dùng thử) đòi hồ sơ học
viên có đủ các trường trên; `users` chưa có trường nào. Lược đồ: §51 trong
`sql/legacy_schema.sql`. Ba quyết định anh Sơn chốt cùng ngày nằm trong mã:

  · MÃ HỌC VIÊN tự sinh, không sửa được → không API nào nhận `studentCode`.
  · NGƯỜI TƯ VẤN chọn từ tài khoản NHÂN SỰ → kiểm vai của id gửi lên.
  · NGUỒN TUYỂN SINH chọn từ `NGUON_TUYEN_SINH` → cùng danh sách với CHECK
    trong lược đồ; hai nơi lệch nhau thì CSDL từ chối và API trả 400.

── AI SỬA ĐƯỢC GÌ ──────────────────────────────────────────────────────────

  Quản trị viên   mọi trường, mọi tài khoản học viên.
  Quản lý học vụ  mọi trường — nhưng CHỈ với tài khoản vai Học viên. Hồ sơ nhân
                  sự không thuộc việc của họ (đổi username của một giảng viên là
                  đổi cách người đó đăng nhập).
  Giảng viên      CHỈ `studyGoal` + `aspiration`, CHỈ em đang học lớp mình phụ
                  trách — đúng dòng 14 của bảng: "cập nhật hồ sơ học sinh trong
                  lớp (thông tin về mục tiêu, nguyện vọng)". Trường khác gửi kèm
                  bị BỎ QUA chứ không báo lỗi: màn hình của giảng viên chỉ gửi đúng
                  hai trường ấy, thêm gì là do người gọi tay.
  Trợ giảng       không sửa. Ô sửa nằm trên tờ báo cáo phụ huynh của em, trang
                  trợ giảng vốn không vào được (`IsSeniorTeachingStaff`, anh Sơn
                  chốt 01/09) — mở API rộng hơn màn hình là quyền không ai dùng.

Email và số điện thoại của EM không sửa ở đây: đó là hai cách ĐĂNG NHẬP, em tự
đổi ở Cài đặt (có kiểm trùng). Tên đăng nhập thì học vụ đặt được — đó là đường
để học vụ cấp lối vào cho em không nhớ email nào.
"""
import datetime
import re

from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.validators import validate_email_field, validate_name_field, validate_phone_field
from common import audit
from common.clock import local_now, local_today
from common.db import q, q1, x
from common.identity import norm_email, norm_phone
from common.permissions import (
    ROLE_ACADEMIC,
    ROLE_ADMIN,
    ROLE_ASSISTANT,
    ROLE_EDITOR,
    ROLE_STUDENT,
    ROLE_TEACHER,
    IsAdminOrAcademic,
    IsSeniorTeachingStaff,
    can_see_class,
    is_admin,
)

#: Khớp CHECK `users_enroll_source_check` (§51). Thứ tự = thứ tự trên ô chọn.
NGUON_TUYEN_SINH = (
    ('facebook', 'Facebook'),
    ('tiktok', 'TikTok'),
    ('zalo', 'Zalo'),
    ('website', 'Website'),
    ('gioi_thieu', 'Người quen giới thiệu'),
    ('truong_hoc', 'Trường học'),
    ('su_kien', 'Sự kiện / hội thảo'),
    ('khac', 'Khác'),
)
_MA_NGUON = {m for m, _ in NGUON_TUYEN_SINH}

#: Vai được chọn làm người tư vấn: mọi vai NHÂN SỰ.
VAI_NHAN_SU = (ROLE_ADMIN, ROLE_ACADEMIC, ROLE_TEACHER, ROLE_ASSISTANT, ROLE_EDITOR)

#: Khớp CHECK `users_username_format_check` (§51): 3–30 ký tự, chữ thường/số/
#: dấu chấm, không mở đầu bằng dấu chấm, và PHẢI có ít nhất một chữ cái — để
#: username không bao giờ trùng dạng với một số điện thoại ở ô đăng nhập.
USERNAME_RE = re.compile(r'^[a-z0-9][a-z0-9.]{2,29}$')

#: Độ dài tối đa của trường chữ tự do.
_DAI = {'school': 200, 'school_grade': 20, 'region': 100, 'study_goal': 500, 'aspiration': 500}

#: Khoá API (camelCase) ↔ cột CSDL cho các trường chữ tự do.
_TRUONG_CHU = {'school': 'school', 'schoolGrade': 'school_grade', 'region': 'region',
               'studyGoal': 'study_goal', 'aspiration': 'aspiration'}


def cap_ma_hoc_vien(user_id):
    """Cấp mã HSA-xxxxx cho một tài khoản HỌC VIÊN chưa có mã. Trả mã (cũ hoặc mới).

    Gọi ở MỌI đường tạo học viên. Chỉ chạm dòng còn NULL, nên gọi thừa cũng vô
    hại — và `nextval` chỉ bị tiêu khi thật sự cấp. Nhân sự không bao giờ có mã.
    """
    r = q1("UPDATE users SET student_code = 'HSA-' || lpad(nextval('student_code_seq')::text, 5, '0') "
           "WHERE id=%s AND role=%s AND student_code IS NULL RETURNING student_code",
           (user_id, ROLE_STUDENT))
    if r:
        return r['student_code']
    d = q1('SELECT student_code FROM users WHERE id=%s', (user_id,))
    return d['student_code'] if d else None


def kiem_username(u, bo_qua_id=None):
    """Chuẩn hoá + kiểm một username. Trả `(giá_trị, lỗi)`; `''` nghĩa là gỡ."""
    u = (u or '').strip().lower()
    if not u:
        return None, None
    if not USERNAME_RE.match(u) or not re.search(r'[a-z]', u):
        return None, ('Tên đăng nhập 3–30 ký tự, chỉ gồm chữ thường, số và dấu chấm, '
                      'có ít nhất một chữ cái (để không lẫn với số điện thoại).')
    trung = q1('SELECT id FROM users WHERE lower(username)=%s AND id <> %s', (u, bo_qua_id or 0))
    if trung:
        return None, 'Tên đăng nhập này đã có người dùng.'
    return u, None


def _dict(r):
    return {
        'id': r['id'],
        'name': r['name'],
        'email': r['email'],
        'phone': r['phone'],
        # Cột TEXT (`DEFAULT ''`), không phải DATE — Cài đặt ghi nguyên chuỗi
        # 'YYYY-MM-DD' của ô chọn ngày. Gọi `.isoformat()` là 500 với em đầu
        # tiên tự điền ngày sinh (phép kiểm bắt được 23/09/2026).
        'birthday': r['birthday'] or None,
        'role': r['role'],
        'status': r['status'],
        'studentCode': r['student_code'],
        'username': r['username'],
        'school': r['school'],
        'schoolGrade': r['school_grade'],
        'region': r['region'],
        'consultantId': r['consultant_id'],
        'consultantName': r.get('consultant_name'),
        'enrollSource': r['enroll_source'],
        'studyGoal': r['study_goal'],
        'aspiration': r['aspiration'],
        'parentName': r['parent_name'],
        'parentPhone': r['parent_phone'],
        'parentEmail': r['parent_email'],
    }


def _doc(user_id):
    return q1('''SELECT u.*, c.name AS consultant_name
                   FROM users u LEFT JOIN users c ON c.id = u.consultant_id
                  WHERE u.id=%s''', (user_id,))


def _nhan(r):
    return r['name'] or r['email'] or r['phone'] or ('#%s' % r['id'])


class HoSoHocVienView(APIView):
    """GET/PATCH /api/admin/users/<id>/profile — hồ sơ đầy đủ của một học viên.

    GET trả kèm hai danh sách chọn (nguồn tuyển sinh, người tư vấn) để màn hình
    dựng form trong MỘT lượt gọi.
    """
    permission_classes = [IsAdminOrAcademic]

    def _chan(self, request, r):
        if not r:
            return Response({'error': 'Không tìm thấy tài khoản này.'}, status=404)
        if not is_admin(request.user) and r['role'] != ROLE_STUDENT:
            # 403 chứ không 404: học vụ vốn thấy giảng viên/trợ giảng trong danh
            # sách lớp — giấu không bảo vệ gì, chỉ gây khó hiểu.
            return Response({'error': 'Quản lý học vụ chỉ xem và sửa hồ sơ HỌC VIÊN. '
                                      'Hồ sơ nhân sự cần quản trị viên.'}, status=403)
        return None

    def get(self, request, user_id):
        r = _doc(user_id)
        chan = self._chan(request, r)
        if chan:
            return chan
        tu_van = q('SELECT id, name, email, role FROM users WHERE role = ANY(%s) '
                   "AND coalesce(status, 'active') <> 'suspended' "
                   "ORDER BY lower(coalesce(name, '')), id", (list(VAI_NHAN_SU),))
        return Response({
            'profile': _dict(r),
            'sources': [{'ma': m, 'nhan': n} for m, n in NGUON_TUYEN_SINH],
            'consultants': [{'id': c['id'], 'name': c['name'] or c['email'], 'role': c['role']}
                            for c in tu_van],
        })

    def patch(self, request, user_id):
        r = _doc(user_id)
        chan = self._chan(request, r)
        if chan:
            return chan
        body = request.data if isinstance(request.data, dict) else {}
        doi, errors = {}, {}

        for khoa, cot in _TRUONG_CHU.items():
            if khoa in body:
                v = (str(body[khoa]).strip() if body[khoa] is not None else '')
                doi[cot] = v[:_DAI[cot]] or None

        if 'enrollSource' in body:
            v = (body['enrollSource'] or '').strip() or None
            if v and v not in _MA_NGUON:
                errors['enrollSource'] = 'Nguồn tuyển sinh phải chọn từ danh sách.'
            else:
                doi['enroll_source'] = v

        if 'consultantId' in body:
            v = body['consultantId']
            if v in (None, ''):
                doi['consultant_id'] = None
            else:
                try:
                    v = int(v)
                except (TypeError, ValueError):
                    v = 0
                nv = q1('SELECT id, role FROM users WHERE id=%s', (v,))
                if not nv or nv['role'] not in VAI_NHAN_SU:
                    errors['consultantId'] = 'Người tư vấn phải là một tài khoản nhân sự.'
                else:
                    doi['consultant_id'] = v

        if 'username' in body:
            v, loi = kiem_username(body['username'], bo_qua_id=user_id)
            if loi:
                errors['username'] = loi
            else:
                doi['username'] = v

        if 'name' in body:
            v = str(body['name'] or '').strip()
            if loi := validate_name_field(v):
                errors['name'] = loi
            else:
                doi['name'] = v

        if 'birthday' in body:
            # Ghi CHUỖI 'YYYY-MM-DD', rỗng là '' — đúng quy ước cột TEXT mà Cài
            # đặt đang ghi. Khuôn chặt trước `fromisoformat`: từ Python 3.11 nó
            # nhận cả '20080517' hay '2008-W20-6'.
            v = str(body['birthday'] or '').strip()
            if not v:
                doi['birthday'] = ''
            else:
                ngay = None
                if re.fullmatch(r'\d{4}-\d{2}-\d{2}', v):
                    try:
                        ngay = datetime.date.fromisoformat(v)
                    except ValueError:
                        pass
                if not ngay or not datetime.date(1900, 1, 1) <= ngay <= local_today():
                    errors['birthday'] = 'Ngày sinh không hợp lệ.'
                else:
                    doi['birthday'] = ngay.isoformat()

        # Liên hệ phụ huynh — cùng luật chuẩn hoá + kiểm với Cài đặt và ô dán cả
        # lớp (`lien_he_phu_huynh._chuan_hoa`): số đưa về 0xxxxxxxxx rồi mới
        # kiểm, email hạ chữ thường. KHÔNG kiểm trùng: hai anh em dùng chung số
        # của mẹ là chuyện thường (xem `ProfileView.put`).
        # Rỗng ghi '' chứ KHÔNG ghi None: ba cột này là `NOT NULL DEFAULT ''`
        # (khác các cột §51) — ghi None là 500 (e2e bắt được 23/09/2026).
        ph = {}
        if 'parentName' in body:
            v = str(body['parentName'] or '').strip()
            if len(v) > 100:
                errors['parentName'] = 'Tên phụ huynh dài quá 100 ký tự.'
            else:
                ph['parent_name'] = v
        if 'parentPhone' in body:
            v = norm_phone(str(body['parentPhone'] or '').strip()) or ''
            if loi := validate_phone_field(v):
                errors['parentPhone'] = 'Số Zalo của phụ huynh: ' + loi
            else:
                ph['parent_phone'] = v
        if 'parentEmail' in body:
            v = norm_email(str(body['parentEmail'] or '').strip()) or ''
            if v and validate_email_field(v):
                errors['parentEmail'] = 'Email của phụ huynh không hợp lệ.'
            else:
                ph['parent_email'] = v

        # `studentCode` cố ý KHÔNG đọc: mã học viên tự sinh và không sửa được.
        if errors:
            return Response({'errors': errors}, status=400)
        # Chỉ giữ ô THẬT SỰ đổi: gửi lại nguyên giá trị cũ không phải một lần sửa
        # — nhất là với liên hệ phụ huynh, nơi "có sửa" kéo theo khoá (§47).
        doi.update({k: v for k, v in ph.items() if v != r[k]})
        doi = {k: v for k, v in doi.items() if v != r[k]}
        if not doi:
            return Response({'ok': True, 'profile': _dict(r)})

        cu = {k: r[k] for k in doi}
        moi = dict(doi)
        if any(k in doi for k in ph):
            # §47: trung tâm đã nhập thì KHOÁ — từ đây em chỉ điền được ô còn
            # trống ở Cài đặt. `locked_by` = người sửa LẦN NÀY, cùng luật với ô
            # dán cả lớp: phụ huynh bảo số sai thì hỏi ngay được ai nhập.
            doi['parent_contact_locked_at'] = local_now()
            doi['parent_contact_locked_by'] = request.user.id
        x('UPDATE users SET %s WHERE id=%%s' % ', '.join('%s=%%s' % k for k in doi),
          tuple(doi.values()) + (user_id,))
        audit.record(request, audit.USER_PROFILE, target_type='user', target_id=user_id,
                     target_label=_nhan(r),
                     summary='Sửa hồ sơ "%s": %s.' % (_nhan(r), ', '.join(sorted(moi))),
                     # GIÁ TRỊ CŨ — đường hoàn tác duy nhất của một lần sửa nhầm.
                     detail={'cu': {k: (str(v) if v is not None else None) for k, v in cu.items()},
                             'moi': {k: (str(v) if v is not None else None) for k, v in moi.items()}})
        return Response({'ok': True, 'profile': _dict(_doc(user_id))})


def _em_trong_lop(class_id, user_id):
    """Em ĐANG học lớp này (`left_at IS NULL`, vai Học viên), hoặc None."""
    return q1('''SELECT u.id, u.name, u.email, u.phone, u.student_code, u.study_goal, u.aspiration
                   FROM class_members m JOIN users u ON u.id = m.user_id
                  WHERE m.class_id=%s AND m.user_id=%s AND m.left_at IS NULL AND u.role=%s''',
              (class_id, user_id, ROLE_STUDENT))


class MucTieuHocVienView(APIView):
    """GET/PATCH /api/teach/classes/<cid>/students/<uid>/profile — giảng viên đọc
    và cập nhật MỤC TIÊU + NGUYỆN VỌNG của một em trong lớp mình (dòng 14 của
    bảng yêu cầu).

    Chỉ hai trường ấy. Em phải ĐANG học lớp ấy (`left_at IS NULL`); không thì 404
    — cùng một câu cho "không có em này" và "em không ở lớp của bạn", để không lộ
    ra em ấy học ở đâu. GET cần có: không đọc được giá trị hiện có thì ô sửa luôn
    trống, và một lần Lưu là xoá trắng điều học vụ đã ghi.
    """
    permission_classes = [IsSeniorTeachingStaff]

    def get(self, request, class_id, user_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        em = _em_trong_lop(class_id, user_id)
        if not em:
            return Response({'error': 'Không tìm thấy học viên này trong lớp.'}, status=404)
        return Response({'studentCode': em['student_code'], 'studyGoal': em['study_goal'],
                         'aspiration': em['aspiration']})

    def patch(self, request, class_id, user_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        em = _em_trong_lop(class_id, user_id)
        if not em:
            return Response({'error': 'Không tìm thấy học viên này trong lớp.'}, status=404)
        body = request.data if isinstance(request.data, dict) else {}
        doi = {}
        for khoa, cot in (('studyGoal', 'study_goal'), ('aspiration', 'aspiration')):
            if khoa in body:
                v = (str(body[khoa]).strip() if body[khoa] is not None else '')
                doi[cot] = v[:_DAI[cot]] or None
        if not doi:
            return Response({'ok': True})
        cu = {k: em[k] for k in doi}
        x('UPDATE users SET %s WHERE id=%%s' % ', '.join('%s=%%s' % k for k in doi),
          tuple(doi.values()) + (user_id,))
        audit.record(request, audit.USER_PROFILE, target_type='user', target_id=user_id,
                     target_label=_nhan(em),
                     summary='Cập nhật mục tiêu/nguyện vọng của "%s" (lớp #%s).' % (_nhan(em), class_id),
                     detail={'cu': cu, 'moi': doi, 'class_id': class_id})
        return Response({'ok': True, 'studyGoal': doi.get('study_goal', em['study_goal']),
                         'aspiration': doi.get('aspiration', em['aspiration'])})
