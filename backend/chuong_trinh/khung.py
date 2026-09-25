"""SOẠN KHUNG CHƯƠNG TRÌNH theo buổi — bảng yêu cầu TopHSA dòng 5 + "Quản lý chương trình học".

Khung của một MÔN (`syllabi`) có nhiều PHIÊN BẢN; mỗi phiên bản là danh sách buổi khung
1..N, mỗi buổi có tên, thời lượng, bài về nhà, bài kiểm tra và các MỤC (bài học / chủ
đề / bài về nhà / kiểm tra) mang trọng số — thứ tiến độ lớp đo trên đó (`tien_do.py`).

── LUẬT PHIÊN BẢN ──────────────────────────────────────────────────────────────

  · Chỉ bản NHÁP sửa được. Sửa bản đang dùng / đã thay → 409, kèm cách làm đúng: "Tạo
    bản mới". Lý do: lớp GHIM phiên bản đã nhận; sửa tại chỗ bản ấy là đổi kế hoạch
    của mọi lớp đang học nó mà không ai quyết định việc đó.
  · "Tạo bản mới" chép bản MỚI NHẤT (buổi + mục) thành bản nháp kế tiếp, trong MỘT
    giao dịch bằng `INSERT … SELECT` — không có lúc nào bản nháp chỉ có một nửa buổi.
  · Xuất bản một bản = bản đang dùng trước đó chuyển sang "đã thay", cùng giao dịch.
    Lớp đang ở bản cũ KHÔNG đổi; chỉ lớp nhận khung từ nay mới lấy bản mới.
  · Bản (hay cả khung) đang có lớp dùng thì không xoá được → 409.

Hai chỉ mục duy nhất một phần (§63b) giữ "một nháp, một đang dùng" ở chính CSDL; hai
lượt bấm song song thì một lượt vấp chỉ mục và nhận 409 thay vì tạo hai bản nháp.

Quyền: `IsCurriculumPlanner` (quản trị viên, học vụ, biên tập nội dung). Mọi lượt ghi
vào nhật ký kiểm toán.
"""
import json
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from chuong_trinh.tu_vung import (
    BAN_NGUNG,
    BAN_NHAP,
    BAN_XUAT_BAN,
    DAI,
    LOAI_MUC,
    NHAN_TRANG_THAI_BAN,
    TRAN_BUOI,
    TRAN_MUC_MOT_BUOI,
    TRAN_TRONG_SO,
)
from common.audit import (
    SYLLABUS_CREATE,
    SYLLABUS_DELETE,
    SYLLABUS_UPDATE,
    SYLLABUS_VERSION_CREATE,
    SYLLABUS_VERSION_DELETE,
    SYLLABUS_VERSION_EDIT,
    SYLLABUS_VERSION_PUBLISH,
    record,
)
from common.clock import local_now
from common.db import q, q1, x
from common.permissions import IsCurriculumPlanner

_KHONG_THAY_KHUNG = {'error': 'Không tìm thấy khung chương trình này.'}
_KHONG_THAY_BAN = {'error': 'Không tìm thấy phiên bản này.'}
_CHI_SUA_NHAP = ('Chỉ sửa được BẢN NHÁP. Bản này đang dùng (hoặc đã được thay) — lớp đang '
                 'học theo nó không được đổi ngầm. Bấm "Tạo bản mới" để sửa trên một bản nháp.')


def _than(request):
    return request.data if isinstance(request.data, dict) else {}


def _chu(v, tran):
    """Chuỗi đã cắt khoảng trắng, None nếu rỗng, cắt ở `tran` ký tự."""
    if v is None:
        return None
    s = str(v).strip()
    return s[:tran] if s else None


def _ban_dict(r, lop_dung=None):
    return {
        'id': r['id'], 'version': r['version'], 'status': r['status'],
        'statusLabel': NHAN_TRANG_THAI_BAN.get(r['status'], r['status']),
        'note': r.get('note'),
        'createdAt': r['created_at'].isoformat() if r.get('created_at') else None,
        'publishedAt': r['published_at'].isoformat() if r.get('published_at') else None,
        'soBuoi': r.get('so_buoi') or 0,
        'soMuc': r.get('so_muc') or 0,
        # Lớp đang theo bản này — hiện để người soạn biết xuất bản bản mới KHÔNG đổi họ.
        'lopDung': lop_dung if lop_dung is not None else (r.get('lop_dung') or []),
    }


def _ds_khung(dieu_kien, tham):
    """Khung kèm mọi phiên bản (số buổi, số mục, lớp đang dùng) — MỘT câu."""
    rows = q('''SELECT s.id, s.course_id, co.title AS course_title, s.name, s.created_at,
                       s.archived_at, s.is_demo,
                       COALESCE((SELECT json_agg(json_build_object(
                                    'id', v.id, 'version', v.version, 'status', v.status,
                                    'note', v.note, 'created_at', v.created_at,
                                    'published_at', v.published_at,
                                    'so_buoi', (SELECT COUNT(*) FROM syllabus_sessions ss
                                                 WHERE ss.version_id = v.id),
                                    'so_muc', (SELECT COUNT(*) FROM syllabus_items i
                                                 JOIN syllabus_sessions ss ON ss.id = i.syl_session_id
                                                WHERE ss.version_id = v.id),
                                    'lop_dung', COALESCE((SELECT json_agg(json_build_object(
                                                   'id', c.id, 'name', c.name) ORDER BY c.name)
                                                  FROM classes c
                                                 WHERE c.syllabus_version_id = v.id), '[]'::json))
                                  ORDER BY v.version DESC)
                                   FROM syllabus_versions v WHERE v.syllabus_id = s.id),
                                '[]'::json) AS versions
                  FROM syllabi s
                  LEFT JOIN courses co ON co.id = s.course_id
                 WHERE ''' + dieu_kien + '''
                 ORDER BY s.archived_at NULLS FIRST, co.title, s.name, s.id''', tham)
    ra = []
    for r in rows:
        vs = r['versions'] if isinstance(r['versions'], list) else json.loads(r['versions'] or '[]')
        ban = []
        for v in vs:
            # json_build_object trả thời điểm dạng chuỗi ISO — giữ nguyên, đừng đoán múi giờ.
            ban.append({
                'id': v['id'], 'version': v['version'], 'status': v['status'],
                'statusLabel': NHAN_TRANG_THAI_BAN.get(v['status'], v['status']),
                'note': v['note'], 'createdAt': v['created_at'], 'publishedAt': v['published_at'],
                'soBuoi': v['so_buoi'], 'soMuc': v['so_muc'], 'lopDung': v['lop_dung'],
            })
        ra.append({
            'id': r['id'], 'courseId': r['course_id'], 'courseTitle': r['course_title'],
            'name': r['name'], 'isDemo': r['is_demo'],
            'createdAt': r['created_at'].isoformat() if r['created_at'] else None,
            'archivedAt': r['archived_at'].isoformat() if r['archived_at'] else None,
            'versions': ban,
            'dangDung': next((b for b in ban if b['status'] == BAN_XUAT_BAN), None),
            'banNhap': next((b for b in ban if b['status'] == BAN_NHAP), None),
        })
    return ra


def _doc_ban(version_id, khoa=False):
    """Phiên bản + khung + môn. `khoa=True`: khoá dòng phiên bản tới hết giao dịch."""
    return q1('''SELECT v.*, s.name AS syllabus_name, s.course_id, s.archived_at,
                        co.title AS course_title
                   FROM syllabus_versions v
                   JOIN syllabi s ON s.id = v.syllabus_id
                   LEFT JOIN courses co ON co.id = s.course_id
                  WHERE v.id = %s''' + (' FOR UPDATE OF v' if khoa else ''), (version_id,))


def noi_dung_ban(version_id):
    """Buổi khung + mục của một phiên bản, theo thứ tự — MỘT câu. Dùng cả ở màn lớp."""
    rows = q('''SELECT ss.id, ss.so_buoi, ss.title, ss.duration_minutes, ss.homework,
                       ss.test_title,
                       COALESCE(json_agg(json_build_object(
                           'id', i.id, 'sort', i.sort, 'kind', i.kind, 'lessonId', i.lesson_id,
                           'lessonTitle', l.title, 'label', i.label, 'weight', i.weight)
                           ORDER BY i.sort, i.id) FILTER (WHERE i.id IS NOT NULL),
                         '[]'::json) AS items
                  FROM syllabus_sessions ss
                  LEFT JOIN syllabus_items i ON i.syl_session_id = ss.id
                  LEFT JOIN lessons l ON l.id = i.lesson_id
                 WHERE ss.version_id = %s
                 GROUP BY ss.id
                 ORDER BY ss.so_buoi''', (version_id,))
    ra = []
    for r in rows:
        items = r['items'] if isinstance(r['items'], list) else json.loads(r['items'] or '[]')
        for i in items:
            i['weight'] = float(i['weight'])
        ra.append({'id': r['id'], 'soBuoi': r['so_buoi'], 'title': r['title'],
                   'durationMinutes': r['duration_minutes'], 'homework': r['homework'],
                   'testTitle': r['test_title'], 'items': items,
                   'trongSo': round(sum(i['weight'] for i in items), 2)})
    return ra


def _lop_dung(version_id):
    return [{'id': r['id'], 'name': r['name']} for r in q(
        'SELECT id, name FROM classes WHERE syllabus_version_id = %s ORDER BY name', (version_id,))]


def _lam_sach_noi_dung(body, course_id):
    """Thân PUT nội dung → (danh sách buổi đã làm sạch, lỗi). Số buổi = thứ tự trong mảng.

    Bài học gắn vào mục phải thuộc CÙNG môn với khung — kiểm bằng một câu cho mọi id.
    """
    buoi = body.get('sessions')
    if not isinstance(buoi, list):
        return None, 'Cần danh sách buổi (sessions).'
    if len(buoi) > TRAN_BUOI:
        return None, 'Một khung tối đa %d buổi.' % TRAN_BUOI
    ra, bai = [], set()
    for so, b in enumerate(buoi, 1):
        if not isinstance(b, dict):
            return None, 'Buổi %d không đọc được.' % so
        ten = _chu(b.get('title'), DAI['tieu_de'])
        if not ten:
            return None, 'Buổi %d chưa có tên.' % so
        phut = b.get('duration_minutes')
        if phut in (None, ''):
            phut = None
        else:
            try:
                phut = int(phut)
            except (TypeError, ValueError):
                return None, 'Thời lượng buổi %d phải là số phút.' % so
            if not 1 <= phut <= 600:
                return None, 'Thời lượng buổi %d phải trong khoảng 1–600 phút.' % so
        muc_vao = b.get('items') or []
        if not isinstance(muc_vao, list):
            return None, 'Mục của buổi %d không đọc được.' % so
        if len(muc_vao) > TRAN_MUC_MOT_BUOI:
            return None, 'Buổi %d có quá %d mục.' % (so, TRAN_MUC_MOT_BUOI)
        muc = []
        for k, m in enumerate(muc_vao, 1):
            if not isinstance(m, dict):
                return None, 'Mục %d của buổi %d không đọc được.' % (k, so)
            loai = m.get('kind') or 'topic'
            if loai not in LOAI_MUC:
                return None, 'Loại mục "%s" không có (buổi %d).' % (loai, so)
            nhan = _chu(m.get('label'), DAI['nhan_muc'])
            if not nhan:
                return None, 'Mục %d của buổi %d chưa có tên.' % (k, so)
            try:
                w = Decimal(str(m.get('weight', 1) if m.get('weight') not in (None, '') else 1))
            except (InvalidOperation, ValueError):
                return None, 'Trọng số mục "%s" (buổi %d) phải là số.' % (nhan, so)
            if not (w.is_finite() and Decimal('0') < w <= TRAN_TRONG_SO):
                return None, 'Trọng số mục "%s" (buổi %d) phải lớn hơn 0 và không quá %s.' % (
                    nhan, so, TRAN_TRONG_SO)
            bai_id = m.get('lesson_id')
            if bai_id in (None, ''):
                bai_id = None
            else:
                try:
                    bai_id = int(bai_id)
                except (TypeError, ValueError):
                    return None, 'Bài học gắn vào mục "%s" không hợp lệ.' % nhan
                bai.add(bai_id)
            muc.append({'sort': k, 'kind': loai, 'label': nhan, 'weight': w.quantize(Decimal('0.01')),
                        'lesson_id': bai_id})
        ra.append({'so_buoi': so, 'title': ten, 'duration_minutes': phut,
                   'homework': _chu(b.get('homework'), DAI['bai_ve_nha']),
                   'test_title': _chu(b.get('test_title'), DAI['kiem_tra']), 'items': muc})
    if bai:
        co = {r['id'] for r in q('SELECT id FROM lessons WHERE id = ANY(%s) AND course_id = %s',
                                 (sorted(bai), course_id))}
        la = sorted(bai - co)
        if la:
            return None, 'Bài học #%s không thuộc môn của khung này.' % ', #'.join(map(str, la))
    return ra, None


# ── 1. Danh sách + tạo khung ───────────────────────────────────────────────────

class KhungListView(APIView):
    """GET/POST /api/admin/khung-chuong-trinh — mọi khung (lọc `course_id`), tạo khung mới."""
    permission_classes = [IsCurriculumPlanner]

    def get(self, request):
        dk, tham = ['TRUE'], []
        mon = (request.query_params.get('course_id') or '').strip()
        if mon:
            dk.append('s.course_id = %s')
            tham.append(mon)
        if request.query_params.get('luu_tru') not in ('1', 'true'):
            dk.append('s.archived_at IS NULL')
        mon_hoc = q('SELECT id, title FROM courses ORDER BY title')
        return Response({'khung': _ds_khung(' AND '.join(dk), tuple(tham)),
                         'monHoc': [{'id': m['id'], 'title': m['title']} for m in mon_hoc],
                         'loaiMuc': list(LOAI_MUC)})

    def post(self, request):
        body = _than(request)
        mon = _chu(body.get('course_id'), 100)
        ten = _chu(body.get('name'), DAI['ten_khung'])
        if not mon or not ten:
            return Response({'error': 'Cần chọn môn và đặt tên khung.'}, status=400)
        mh = q1('SELECT id, title FROM courses WHERE id = %s', (mon,))
        if not mh:
            return Response({'error': 'Không có môn học này.'}, status=400)
        nay = local_now()
        with transaction.atomic():
            k = q1('''INSERT INTO syllabi (course_id, name, created_by, created_at)
                      VALUES (%s, %s, %s, %s) RETURNING id''', (mon, ten, request.user.id, nay))
            v = q1('''INSERT INTO syllabus_versions (syllabus_id, version, status, created_by,
                                                     created_at)
                      VALUES (%s, 1, %s, %s, %s) RETURNING id''',
                   (k['id'], BAN_NHAP, request.user.id, nay))
            record(request, SYLLABUS_CREATE, target_type='syllabus', target_id=k['id'],
                   target_label=ten, summary='Tạo khung "%s" (môn %s)' % (ten, mh['title']),
                   detail={'course_id': mon, 'version_id': v['id']})
        return Response({'ok': True, 'id': k['id'], 'versionId': v['id']}, status=201)


# ── 2. Một khung ───────────────────────────────────────────────────────────────

class KhungDetailView(APIView):
    """GET/PATCH/DELETE /api/admin/khung-chuong-trinh/<id>.

    PATCH: `name`, `archived` (cất đi khỏi danh sách — lớp đang dùng vẫn chạy). DELETE:
    chỉ khi KHÔNG lớp nào dùng bất kỳ phiên bản nào của nó.
    """
    permission_classes = [IsCurriculumPlanner]

    def get(self, request, syllabus_id):
        ds = _ds_khung('s.id = %s', (syllabus_id,))
        if not ds:
            return Response(_KHONG_THAY_KHUNG, status=404)
        return Response({'khung': ds[0]})

    def patch(self, request, syllabus_id):
        body = _than(request)
        k = q1('SELECT id, name, archived_at FROM syllabi WHERE id = %s', (syllabus_id,))
        if not k:
            return Response(_KHONG_THAY_KHUNG, status=404)
        doi = {}
        if 'name' in body:
            ten = _chu(body.get('name'), DAI['ten_khung'])
            if not ten:
                return Response({'error': 'Tên khung không được để trống.'}, status=400)
            doi['name'] = ten
        if 'archived' in body:
            doi['archived_at'] = local_now() if body.get('archived') else None
        if not doi:
            return Response({'error': 'Không có gì để sửa.'}, status=400)
        sets = ', '.join('%s = %%s' % c for c in doi)
        x('UPDATE syllabi SET ' + sets + ' WHERE id = %s', tuple(doi.values()) + (syllabus_id,))
        record(request, SYLLABUS_UPDATE, target_type='syllabus', target_id=syllabus_id,
               target_label=doi.get('name', k['name']),
               summary='Sửa khung "%s" (%s)' % (k['name'], ', '.join(sorted(doi))),
               detail={'truoc': {'name': k['name'],
                                 'archived_at': k['archived_at'].isoformat()
                                 if k['archived_at'] else None},
                       'fields': sorted(doi)})
        return Response({'ok': True})

    def delete(self, request, syllabus_id):
        with transaction.atomic():
            k = q1('SELECT id, name FROM syllabi WHERE id = %s FOR UPDATE', (syllabus_id,))
            if not k:
                return Response(_KHONG_THAY_KHUNG, status=404)
            dung = q('''SELECT c.id, c.name FROM classes c
                          JOIN syllabus_versions v ON v.id = c.syllabus_version_id
                         WHERE v.syllabus_id = %s ORDER BY c.name LIMIT 20''', (syllabus_id,))
            if dung:
                return Response({'error': 'Khung đang có %s lớp dùng (%s) — không xoá được. Cất '
                                          'khung đi (lưu trữ) nếu không muốn thấy nó nữa.'
                                          % (len(dung), ', '.join(r['name'] for r in dung[:5])),
                                 'lopDung': dung}, status=409)
            x('DELETE FROM syllabi WHERE id = %s', (syllabus_id,))
            record(request, SYLLABUS_DELETE, target_type='syllabus', target_id=syllabus_id,
                   target_label=k['name'], summary='Xoá khung "%s"' % k['name'])
        return Response({'ok': True})


class BanMoiView(APIView):
    """POST /api/admin/khung-chuong-trinh/<id>/ban-moi — chép bản MỚI NHẤT thành bản nháp.

    Ba câu `INSERT … SELECT` (phiên bản, buổi, mục) trong MỘT giao dịch. Mục nối với buổi
    MỚI qua số buổi — `UNIQUE (version_id, so_buoi)` làm cặp ấy duy nhất. Đã có bản nháp
    → 409 (chỉ mục §63b; hai lượt bấm song song cũng chỉ ra một bản).
    """
    permission_classes = [IsCurriculumPlanner]

    def post(self, request, syllabus_id):
        k = q1('SELECT id, name FROM syllabi WHERE id = %s', (syllabus_id,))
        if not k:
            return Response(_KHONG_THAY_KHUNG, status=404)
        nay = local_now()
        try:
            with transaction.atomic():
                cu = q1('''SELECT id, version FROM syllabus_versions WHERE syllabus_id = %s
                           ORDER BY version DESC LIMIT 1''', (syllabus_id,))
                moi = q1('''INSERT INTO syllabus_versions (syllabus_id, version, status,
                                                           created_by, created_at)
                            VALUES (%s, %s, %s, %s, %s) RETURNING id, version''',
                         (syllabus_id, (cu['version'] if cu else 0) + 1, BAN_NHAP,
                          request.user.id, nay))
                if cu:
                    x('''INSERT INTO syllabus_sessions (version_id, so_buoi, title,
                                                        duration_minutes, homework, test_title)
                         SELECT %s, so_buoi, title, duration_minutes, homework, test_title
                           FROM syllabus_sessions WHERE version_id = %s''', (moi['id'], cu['id']))
                    x('''INSERT INTO syllabus_items (syl_session_id, sort, kind, lesson_id, label,
                                                     weight)
                         SELECT sm.id, i.sort, i.kind, i.lesson_id, i.label, i.weight
                           FROM syllabus_items i
                           JOIN syllabus_sessions sc ON sc.id = i.syl_session_id
                           JOIN syllabus_sessions sm ON sm.version_id = %s
                                                    AND sm.so_buoi = sc.so_buoi
                          WHERE sc.version_id = %s''', (moi['id'], cu['id']))
                record(request, SYLLABUS_VERSION_CREATE, target_type='syllabus',
                       target_id=syllabus_id, target_label=k['name'],
                       summary='Tạo bản %d của khung "%s"%s' % (
                           moi['version'], k['name'],
                           ' (chép từ bản %d)' % cu['version'] if cu else ''),
                       detail={'version_id': moi['id'], 'tu_ban': cu['id'] if cu else None})
        except IntegrityError:
            return Response({'error': 'Khung này đã có một bản nháp — sửa tiếp bản nháp ấy, hoặc '
                                      'xuất bản nó rồi mới tạo bản mới.'}, status=409)
        return Response({'ok': True, 'versionId': moi['id'], 'version': moi['version']},
                        status=201)


# ── 3. Một phiên bản ───────────────────────────────────────────────────────────

class PhienBanView(APIView):
    """GET/PATCH/PUT/DELETE /api/admin/khung-chuong-trinh/phien-ban/<id>.

    GET: phiên bản + buổi + mục + lớp đang dùng. PATCH `note` (chỉ nháp). PUT nội dung
    (chỉ nháp): THAY TOÀN BỘ buổi + mục bằng danh sách gửi lên, trong một giao dịch — bộ
    soạn sửa tại chỗ rồi lưu một lần, không có lúc nào nửa cũ nửa mới. DELETE: không lớp
    nào dùng mới xoá được.
    """
    permission_classes = [IsCurriculumPlanner]

    def get(self, request, version_id):
        v = _doc_ban(version_id)
        if not v:
            return Response(_KHONG_THAY_BAN, status=404)
        buoi = noi_dung_ban(version_id)
        return Response({
            'khung': {'id': v['syllabus_id'], 'name': v['syllabus_name'],
                      'courseId': v['course_id'], 'courseTitle': v['course_title']},
            'phienBan': _ban_dict(dict(v, so_buoi=len(buoi),
                                       so_muc=sum(len(b['items']) for b in buoi)),
                                  _lop_dung(version_id)),
            'sessions': buoi,
            'suaDuoc': v['status'] == BAN_NHAP,
            'loaiMuc': list(LOAI_MUC),
        })

    def patch(self, request, version_id):
        body = _than(request)
        with transaction.atomic():
            v = _doc_ban(version_id, khoa=True)
            if not v:
                return Response(_KHONG_THAY_BAN, status=404)
            if v['status'] != BAN_NHAP:
                return Response({'error': _CHI_SUA_NHAP}, status=409)
            ghi_chu = _chu(body.get('note'), DAI['ghi_chu_ban'])
            x('UPDATE syllabus_versions SET note = %s WHERE id = %s', (ghi_chu, version_id))
        return Response({'ok': True})

    def put(self, request, version_id):
        body = _than(request)
        with transaction.atomic():
            v = _doc_ban(version_id, khoa=True)
            if not v:
                return Response(_KHONG_THAY_BAN, status=404)
            if v['status'] != BAN_NHAP:
                return Response({'error': _CHI_SUA_NHAP}, status=409)
            buoi, loi = _lam_sach_noi_dung(body, v['course_id'])
            if loi:
                return Response({'error': loi}, status=400)
            truoc = q1('''SELECT COUNT(DISTINCT ss.id) AS b, COUNT(i.id) AS m
                            FROM syllabus_sessions ss
                            LEFT JOIN syllabus_items i ON i.syl_session_id = ss.id
                           WHERE ss.version_id = %s''', (version_id,))
            x('DELETE FROM syllabus_sessions WHERE version_id = %s', (version_id,))
            if buoi:
                id_theo_so = {r['so_buoi']: r['id'] for r in q(
                    '''INSERT INTO syllabus_sessions (version_id, so_buoi, title, duration_minutes,
                                                      homework, test_title)
                       SELECT %s, t.so, t.ten, t.phut, t.bvn, t.kt
                         FROM unnest(%s::int[], %s::text[], %s::int[], %s::text[], %s::text[])
                              AS t(so, ten, phut, bvn, kt)
                       RETURNING id, so_buoi''',
                    (version_id, [b['so_buoi'] for b in buoi], [b['title'] for b in buoi],
                     [b['duration_minutes'] for b in buoi], [b['homework'] for b in buoi],
                     [b['test_title'] for b in buoi]))}
                muc = [(id_theo_so[b['so_buoi']], m) for b in buoi for m in b['items']]
                if muc:
                    x('''INSERT INTO syllabus_items (syl_session_id, sort, kind, lesson_id, label,
                                                     weight)
                         SELECT t.ss, t.sx, t.loai, t.bai, t.nhan, t.w
                           FROM unnest(%s::int[], %s::int[], %s::text[], %s::int[], %s::text[],
                                       %s::numeric[]) AS t(ss, sx, loai, bai, nhan, w)''',
                      ([s for s, _ in muc], [m['sort'] for _, m in muc],
                       [m['kind'] for _, m in muc], [m['lesson_id'] for _, m in muc],
                       [m['label'] for _, m in muc], [m['weight'] for _, m in muc]))
            so_muc = sum(len(b['items']) for b in buoi)
            record(request, SYLLABUS_VERSION_EDIT, target_type='syllabus',
                   target_id=v['syllabus_id'], target_label=v['syllabus_name'],
                   summary='Sửa bản nháp %d của khung "%s": %d buổi, %d mục (trước: %d buổi, %d mục)'
                           % (v['version'], v['syllabus_name'], len(buoi), so_muc,
                              truoc['b'], truoc['m']),
                   detail={'version_id': version_id})
        return Response({'ok': True, 'sessions': noi_dung_ban(version_id)})

    def delete(self, request, version_id):
        with transaction.atomic():
            v = _doc_ban(version_id, khoa=True)
            if not v:
                return Response(_KHONG_THAY_BAN, status=404)
            dung = _lop_dung(version_id)
            if dung:
                return Response({'error': 'Bản này đang có %d lớp dùng (%s) — không xoá được.'
                                          % (len(dung), ', '.join(r['name'] for r in dung[:5])),
                                 'lopDung': dung}, status=409)
            x('DELETE FROM syllabus_versions WHERE id = %s', (version_id,))
            record(request, SYLLABUS_VERSION_DELETE, target_type='syllabus',
                   target_id=v['syllabus_id'], target_label=v['syllabus_name'],
                   summary='Xoá bản %d (%s) của khung "%s"' % (
                       v['version'], NHAN_TRANG_THAI_BAN.get(v['status'], v['status']).lower(),
                       v['syllabus_name']),
                   detail={'version_id': version_id, 'status': v['status']})
        return Response({'ok': True})


class XuatBanView(APIView):
    """POST /api/admin/khung-chuong-trinh/phien-ban/<id>/xuat-ban.

    Bản nháp → đang dùng; bản đang dùng trước đó → đã thay. Cùng giao dịch, NGỪNG trước
    rồi mới xuất bản (chỉ mục "một bản đang dùng" §63b). Lớp đang ở bản cũ giữ nguyên.
    Mọi buổi phải có ít nhất một mục: buổi không mục nặng 0, tiến độ không đo được nó.
    """
    permission_classes = [IsCurriculumPlanner]

    def post(self, request, version_id):
        nay = local_now()
        try:
            with transaction.atomic():
                v = _doc_ban(version_id, khoa=True)
                if not v:
                    return Response(_KHONG_THAY_BAN, status=404)
                if v['status'] != BAN_NHAP:
                    return Response({'error': 'Chỉ xuất bản được bản nháp — bản này đã %s.'
                                              % NHAN_TRANG_THAI_BAN[v['status']].lower()},
                                    status=409)
                buoi = q('''SELECT ss.so_buoi, COUNT(i.id) AS n FROM syllabus_sessions ss
                              LEFT JOIN syllabus_items i ON i.syl_session_id = ss.id
                             WHERE ss.version_id = %s GROUP BY ss.so_buoi ORDER BY ss.so_buoi''',
                         (version_id,))
                if not buoi:
                    return Response({'error': 'Bản nháp chưa có buổi nào.'}, status=400)
                rong = [b['so_buoi'] for b in buoi if not b['n']]
                if rong:
                    return Response({'error': 'Buổi %s chưa có mục nào — mỗi buổi cần ít nhất một '
                                              'mục để đo tiến độ.'
                                              % ', '.join(map(str, rong))}, status=400)
                cu = q1('''UPDATE syllabus_versions SET status = %s
                            WHERE syllabus_id = %s AND status = %s RETURNING id, version''',
                        (BAN_NGUNG, v['syllabus_id'], BAN_XUAT_BAN))
                x('''UPDATE syllabus_versions SET status = %s, published_by = %s, published_at = %s
                      WHERE id = %s''', (BAN_XUAT_BAN, request.user.id, nay, version_id))
                record(request, SYLLABUS_VERSION_PUBLISH, target_type='syllabus',
                       target_id=v['syllabus_id'], target_label=v['syllabus_name'],
                       summary='Xuất bản bản %d của khung "%s" (%d buổi)%s' % (
                           v['version'], v['syllabus_name'], len(buoi),
                           ' — thay bản %d' % cu['version'] if cu else ''),
                       detail={'version_id': version_id, 'thay': cu['id'] if cu else None})
        except IntegrityError:
            return Response({'error': 'Khung vừa được xuất bản ở một lượt khác — tải lại trang.'},
                            status=409)
        return Response({'ok': True, 'thayBan': cu['version'] if cu else None})
