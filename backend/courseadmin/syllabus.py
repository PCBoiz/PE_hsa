"""KHUNG CHƯƠNG TRÌNH THEO BUỔI (E1, §64, 25/09/2026) — quản lý khóa học 5.2.

Yêu cầu TopHSA: "tiến trình học tập gồm số buổi kèm tên bài", "thời lượng buổi
học", "quản lý phiên bản/chỉnh sửa chương trình", "học liệu", "gán khóa học
cho lớp". Bốn tầng — xem chú thích §64 trong `sql/legacy_schema.sql`:

    syllabus_versions  (1 khóa, NHIỀU phiên bản: nháp / xuất bản / ngừng)
      └─ syllabus_sessions   (buổi học THEO KẾ HOẠCH — tái dùng cho nhiều lớp)
           ├─ syllabus_items     (nội dung buổi: bài học/chuyên đề/bài tập/kiểm tra)
           └─ syllabus_materials (học liệu — `file_url` để trống, chờ dữ liệu thật)

QUYỀN: soạn khung (mọi thao tác CRUD trên bốn bảng trên) dùng `IsCurriculumPlanner`
— quản trị viên, học vụ, biên tập nội dung (lead chốt 25/09/2026: học vụ soạn được
khung, vì khung là thứ họ giao cho từng lớp và đối chiếu tiến độ). Bản đầu (3f47421)
dùng `IsContentEditor`, tức học vụ không soạn được. GÁN một phiên bản CHO một lớp là
việc VẬN HÀNH LỚP — `IsAdminOrAcademic`, nay ở `chuong_trinh/lop.py::NhanKhungView`
(cùng đường dẫn `api/admin/classes/<id>/chuong-trinh`; bản ghép theo vị trí ở đây đã
bỏ — xem docstring `chuong_trinh/dich_vu.py::nhan_khung`).

CHUỖI PHIÊN BẢN (§64g): một môn có nhiều khung độc lập; các bản nhân bản từ nhau là
MỘT chuỗi (`lineage_id`). Mỗi chuỗi nhiều nhất MỘT bản nháp và MỘT bản đang dùng — hai
chỉ mục duy nhất ở CSDL; ở đây vấp chỉ mục thì trả 409 thay vì 500. Xuất bản một bản =
bản đang dùng cũ của CHUỖI ẤY chuyển sang 'ngung' trong cùng giao dịch; lớp đang ở bản
cũ giữ nguyên (lớp ghim phiên bản đã nhận).

SỬA CHỈ Ở BẢN NHÁP: một khi `status != 'nhap'` (đã xuất bản/ngừng), toàn bộ cây
(sessions/items/materials) bị KHOÁ SỬA/XOÁ — 409, kèm gợi ý nhân bản. Không
khoá thì một lớp đã nhận khung có thể thấy nội dung đổi dưới chân giữa học kỳ,
trong khi báo cáo/tiến độ đã tính theo bản cũ.
"""
from django.db import IntegrityError, transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from chuong_trinh.tu_vung import BAN_NGUNG, BAN_NHAP, BAN_XUAT_BAN, LOAI_MUC, TRANG_THAI_BAN
from common import audit
from common.db import q, q1, x
from common.permissions import IsCurriculumPlanner
from lessons.content import loi_html

#: Một nguồn cho hai bộ từ vựng: `chuong_trinh/tu_vung.py` (khớp CHECK §64).
KIND = LOAI_MUC
STATUS = TRANG_THAI_BAN
_MOT_NHAP = ('Chuỗi khung này đã có một bản nháp — sửa tiếp bản nháp ấy, hoặc xuất bản '
             'nó rồi mới nhân bản tiếp.')


def _trong_so(gia_tri):
    """Trọng số một nội dung → (số, lỗi). Thiếu = 1; phải lớn hơn 0 (§64h — tiến độ lớp
    chia cho trọng số trung bình một buổi, số 0 làm phép chia vô nghĩa)."""
    if gia_tri is None or gia_tri == '':
        return 1, None
    try:
        w = float(gia_tri)
    except (TypeError, ValueError):
        return None, 'weight phải là số.'
    if not w > 0 or w > 100:
        return None, 'weight phải lớn hơn 0 và không quá 100.'
    return w, None
_DAI_TEN = 200
_DAI_GHI_CHU = 2000


def _loi_chu(gia_tri, ten, toi_da=_DAI_TEN, bat_buoc=True):
    v = (gia_tri or '').strip()
    if not v:
        return v, ('"%s" không được để trống.' % ten) if bat_buoc else None
    if len(v) > toi_da:
        return v, '"%s" dài %d ký tự, tối đa %d.' % (ten, len(v), toi_da)
    e = loi_html(v, ten)
    if e:
        return v, e[0]
    return v, None


def _phien_ban(vid):
    return q1('SELECT * FROM syllabus_versions WHERE id=%s', (vid,))


def _buoi(sid):
    return q1('''SELECT s.*, v.course_id, v.status AS trang_thai_ban
                   FROM syllabus_sessions s JOIN syllabus_versions v ON v.id = s.version_id
                  WHERE s.id=%s''', (sid,))


def _khoa_neu_khong_nhap(trang_thai):
    """Response 409 nếu phiên bản KHÔNG còn là nháp, None nếu sửa được."""
    if trang_thai != 'nhap':
        return Response({'error': 'Phiên bản đã xuất bản/ngừng — không sửa được. '
                                  'Nhân bản (POST kèm duplicate_from) rồi sửa bản mới.'},
                        status=409)
    return None


def _cay(version_id):
    """Toàn bộ buổi → nội dung + học liệu của MỘT phiên bản, ĐÚNG BA câu SQL
    bất kể phiên bản có bao nhiêu buổi (không vòng lặp gọi từng buổi)."""
    buoi = q('SELECT * FROM syllabus_sessions WHERE version_id=%s ORDER BY sort_order',
             (version_id,))
    ids = [b['id'] for b in buoi]
    items, tai_lieu = {}, {}
    if ids:
        for it in q('SELECT * FROM syllabus_items WHERE session_id = ANY(%s) ORDER BY session_id, sort_order',
                    (ids,)):
            items.setdefault(it['session_id'], []).append({
                'id': it['id'], 'sortOrder': it['sort_order'], 'kind': it['kind'],
                'lessonId': it['lesson_id'], 'title': it['title'], 'weight': float(it['weight']),
            })
        for m in q('SELECT * FROM syllabus_materials WHERE session_id = ANY(%s) ORDER BY session_id, sort_order',
                  (ids,)):
            tai_lieu.setdefault(m['session_id'], []).append({
                'id': m['id'], 'title': m['title'], 'fileUrl': m['file_url'],
                'fileType': m['file_type'], 'sortOrder': m['sort_order'],
            })
    return [{
        'id': b['id'], 'sortOrder': b['sort_order'], 'name': b['name'],
        'durationMinutes': b['duration_minutes'], 'homework': b['homework'],
        'items': items.get(b['id'], []), 'materials': tai_lieu.get(b['id'], []),
    } for b in buoi]


class SyllabusVersionsView(APIView):
    """GET/POST /api/admin/courses/<course_id>/syllabus — danh sách / tạo phiên bản.

    POST nhận ``{"name": ..., "duplicateFrom": <id tuỳ chọn>}``. Có ``duplicateFrom``
    thì CHÉP TOÀN BỘ cây (buổi + nội dung + học liệu) của bản đó trong MỘT giao
    dịch — "tạo bản mới = chép bản mới nhất", cách DUY NHẤT để sửa một bản đã
    xuất bản.
    """
    permission_classes = [IsCurriculumPlanner]

    def get(self, request, course_id):
        if not q1('SELECT 1 FROM courses WHERE id=%s', (course_id,)):
            return Response({'error': 'Không tìm thấy khóa học'}, status=404)
        rows = q('''SELECT v.id, v.name, v.status, v.created_at, v.updated_at, v.is_demo,
                           COALESCE(v.lineage_id, v.id) AS chuoi,
                           (SELECT count(*) FROM classes c
                             WHERE c.syllabus_version_id = v.id) AS so_lop_dang_dung,
                           (SELECT count(*) FROM syllabus_sessions s
                             WHERE s.version_id = v.id) AS so_buoi
                      FROM syllabus_versions v
                     WHERE v.course_id=%s ORDER BY v.created_at DESC''', (course_id,))
        return Response({'versions': [{
            'id': r['id'], 'name': r['name'], 'status': r['status'],
            'createdAt': r['created_at'], 'updatedAt': r['updated_at'],
            'soLopDangDung': r['so_lop_dang_dung'], 'soBuoi': r['so_buoi'],
            # Khoá CHUỖI (§64g): các bản nhân bản từ nhau cùng khoá — màn hình gom theo nó.
            'chuoi': r['chuoi'], 'isDemo': r['is_demo'],
        } for r in rows]})

    def post(self, request, course_id):
        if not q1('SELECT 1 FROM courses WHERE id=%s', (course_id,)):
            return Response({'error': 'Không tìm thấy khóa học'}, status=404)
        body = request.data if isinstance(request.data, dict) else {}
        ten, loi = _loi_chu(body.get('name'), 'name')
        if loi:
            return Response({'error': loi}, status=400)

        nguon = None
        nguon_id = body.get('duplicateFrom')
        if nguon_id:
            nguon = q1('SELECT id, COALESCE(lineage_id, id) AS chuoi FROM syllabus_versions '
                       'WHERE id=%s AND course_id=%s', (nguon_id, course_id))
            if not nguon:
                return Response({'error': 'Không tìm thấy phiên bản nguồn để nhân bản.'}, status=404)

        # Nhân bản = MỘT giao dịch, BA câu `INSERT … SELECT` (buổi, nội dung, học liệu) cho
        # mọi số buổi — bản đầu chép từng dòng (1 + 3 câu mỗi buổi). Nội dung và học liệu
        # nối về buổi MỚI qua `sort_order` (duy nhất trong một phiên bản — §64).
        # Bản mới cùng CHUỖI với bản nguồn (§64g); không nhân bản = một chuỗi mới.
        try:
            with transaction.atomic():
                v = q1('''INSERT INTO syllabus_versions (course_id, name, status, created_by,
                                                         lineage_id)
                            VALUES (%s, %s, %s, %s, %s) RETURNING id''',
                       (course_id, ten, BAN_NHAP, request.user.id,
                        nguon['chuoi'] if nguon else None))
                if nguon:
                    x('''INSERT INTO syllabus_sessions (version_id, sort_order, name,
                                                        duration_minutes, homework)
                         SELECT %s, sort_order, name, duration_minutes, homework
                           FROM syllabus_sessions WHERE version_id = %s''', (v['id'], nguon['id']))
                    x('''INSERT INTO syllabus_items (session_id, sort_order, kind, lesson_id, title,
                                                     weight)
                         SELECT sm.id, i.sort_order, i.kind, i.lesson_id, i.title, i.weight
                           FROM syllabus_items i
                           JOIN syllabus_sessions sc ON sc.id = i.session_id
                           JOIN syllabus_sessions sm ON sm.version_id = %s
                                                    AND sm.sort_order = sc.sort_order
                          WHERE sc.version_id = %s''', (v['id'], nguon['id']))
                    x('''INSERT INTO syllabus_materials (session_id, title, file_url, file_type,
                                                         sort_order, uploaded_by)
                         SELECT sm.id, m.title, m.file_url, m.file_type, m.sort_order, %s
                           FROM syllabus_materials m
                           JOIN syllabus_sessions sc ON sc.id = m.session_id
                           JOIN syllabus_sessions sm ON sm.version_id = %s
                                                    AND sm.sort_order = sc.sort_order
                          WHERE sc.version_id = %s''', (request.user.id, v['id'], nguon['id']))
        except IntegrityError:
            # Vấp `idx_syllabus_versions_mot_nhap`: chuỗi đã có bản nháp (§64g).
            return Response({'error': _MOT_NHAP}, status=409)

        audit.record(request, audit.SYLLABUS_CREATE, target_type='syllabus_version',
                     target_id=str(v['id']), target_label=ten,
                     summary='Tạo phiên bản chương trình "%s" cho khóa %s%s.' % (
                         ten, course_id, (' (nhân bản từ #%s)' % nguon_id) if nguon else ''))
        return Response({'ok': True, 'id': v['id']}, status=201)


class SyllabusVersionDetailView(APIView):
    """GET/PUT/DELETE /api/admin/syllabus/<version_id> — cây đầy đủ / sửa tên+xuất
    bản / xoá. Xuất bản (``status: "xuat_ban"``) là đường DUY NHẤT khoá sửa —
    không có đường "mở khoá lại", đúng ý "chỉ sửa được bản nháp"."""
    permission_classes = [IsCurriculumPlanner]

    def get(self, request, version_id):
        v = _phien_ban(version_id)
        if not v:
            return Response({'error': 'Không tìm thấy phiên bản'}, status=404)
        return Response({
            'id': v['id'], 'courseId': v['course_id'], 'name': v['name'],
            'status': v['status'], 'createdAt': v['created_at'], 'updatedAt': v['updated_at'],
            'sessions': _cay(version_id),
        })

    def put(self, request, version_id):
        v = _phien_ban(version_id)
        if not v:
            return Response({'error': 'Không tìm thấy phiên bản'}, status=404)
        body = request.data if isinstance(request.data, dict) else {}
        doi = {}

        if 'name' in body:
            chan = _khoa_neu_khong_nhap(v['status'])
            if chan:
                return chan
            ten, loi = _loi_chu(body['name'], 'name')
            if loi:
                return Response({'error': loi}, status=400)
            doi['name'] = ten

        if 'status' in body:
            moi = (body['status'] or '').strip()
            if moi not in STATUS:
                return Response({'error': 'status phải là một trong %s.' % (STATUS,)}, status=400)
            # nháp → xuất bản: phải có ít nhất một buổi, không thì gán cho lớp
            # xong không có gì để dạy. xuất bản → ngừng: được (lớp đang dùng vẫn
            # giữ nguyên nội dung, chỉ không cho gán MỚI — kiểm ở view gán bên dưới).
            # Không cho NGỪNG → NHÁP hay XUẤT BẢN → NHÁP: nội dung coi như đã khoá vĩnh viễn.
            if v['status'] == 'nhap' and moi == 'xuat_ban':
                if not q1('SELECT 1 FROM syllabus_sessions WHERE version_id=%s', (version_id,)):
                    return Response({'error': 'Chưa có buổi học nào — thêm ít nhất một buổi '
                                              'trước khi xuất bản.'}, status=400)
            elif v['status'] == 'xuat_ban' and moi == 'ngung':
                pass
            elif v['status'] == moi:
                pass
            else:
                return Response({'error': 'Không đổi được trạng thái từ "%s" sang "%s".' %
                                          (v['status'], moi)}, status=409)
            doi['status'] = moi

        if not doi:
            return Response({'ok': True})
        doi['updated_at'] = None  # đặt lại bằng now() ở câu SQL, không truyền chuỗi Python
        set_clause = ', '.join(
            ('updated_at = now()' if k == 'updated_at' else '%s=%%s' % k) for k in doi)
        vals = tuple(v2 for k, v2 in doi.items() if k != 'updated_at')
        xuat_ban = doi.get('status') == BAN_XUAT_BAN and v['status'] == BAN_NHAP
        thay = None
        try:
            with transaction.atomic():
                if xuat_ban:
                    # Bản đang dùng CÙNG CHUỖI → 'ngung', TRƯỚC khi xuất bản bản này: chỉ mục
                    # "một bản đang dùng mỗi chuỗi" (§64g) kiểm từng câu. Lớp đang ở bản cũ
                    # giữ nguyên — chỉ lớp nhận khung từ nay mới lấy bản mới.
                    thay = q1('''UPDATE syllabus_versions SET status = %s, updated_at = now()
                                  WHERE COALESCE(lineage_id, id) = %s AND status = %s AND id <> %s
                                  RETURNING id, name''',
                              (BAN_NGUNG, v['lineage_id'] or v['id'], BAN_XUAT_BAN, version_id))
                x('UPDATE syllabus_versions SET %s WHERE id=%%s' % set_clause, vals + (version_id,))
        except IntegrityError:
            return Response({'error': 'Chuỗi khung này vừa có một bản khác được xuất bản — tải '
                                      'lại trang rồi thử lại.'}, status=409)

        if xuat_ban:
            audit.record(request, audit.SYLLABUS_PUBLISH, target_type='syllabus_version',
                         target_id=str(version_id), target_label=v['name'],
                         summary='Xuất bản phiên bản chương trình "%s"%s.' % (
                             v['name'], (' — thay bản "%s"' % thay['name']) if thay else ''))
            return Response({'ok': True, 'thayBan': thay['id'] if thay else None})
        else:
            audit.record(request, audit.SYLLABUS_UPDATE, target_type='syllabus_version',
                         target_id=str(version_id), target_label=v['name'],
                         summary='Sửa phiên bản chương trình "%s" (%s).' % (
                             v['name'], ', '.join(k for k in doi if k != 'updated_at')))
        return Response({'ok': True})

    def delete(self, request, version_id):
        v = _phien_ban(version_id)
        if not v:
            return Response({'error': 'Không tìm thấy phiên bản'}, status=404)
        if q1('SELECT 1 FROM classes WHERE syllabus_version_id=%s', (version_id,)):
            return Response({'error': 'Đang có lớp dùng phiên bản này — không xoá được. '
                                      'Đổi lớp sang phiên bản khác trước.'}, status=409)
        x('DELETE FROM syllabus_versions WHERE id=%s', (version_id,))
        audit.record(request, audit.SYLLABUS_DELETE, target_type='syllabus_version',
                     target_id=str(version_id), target_label=v['name'],
                     summary='Xoá phiên bản chương trình "%s".' % v['name'])
        return Response({'ok': True})


class SyllabusSessionsView(APIView):
    """POST /api/admin/syllabus/<version_id>/sessions — thêm một buổi vào CUỐI
    (sort_order = lớn nhất + 1). Chỉ khi phiên bản còn nháp."""
    permission_classes = [IsCurriculumPlanner]

    def post(self, request, version_id):
        v = _phien_ban(version_id)
        if not v:
            return Response({'error': 'Không tìm thấy phiên bản'}, status=404)
        chan = _khoa_neu_khong_nhap(v['status'])
        if chan:
            return chan
        body = request.data if isinstance(request.data, dict) else {}
        ten, loi = _loi_chu(body.get('name'), 'name')
        if loi:
            return Response({'error': loi}, status=400)
        thoi_luong = body.get('durationMinutes')
        if thoi_luong is not None:
            try:
                thoi_luong = int(thoi_luong)
            except (TypeError, ValueError):
                return Response({'error': 'durationMinutes phải là số phút.'}, status=400)
            if thoi_luong <= 0:
                return Response({'error': 'durationMinutes phải lớn hơn 0.'}, status=400)
        bai_ve_nha, loi = _loi_chu(body.get('homework'), 'homework', _DAI_GHI_CHU, bat_buoc=False)
        if loi:
            return Response({'error': loi}, status=400)

        ke = q1('SELECT COALESCE(MAX(sort_order), 0) + 1 AS n FROM syllabus_sessions WHERE version_id=%s',
               (version_id,))
        s = q1('''INSERT INTO syllabus_sessions (version_id, sort_order, name, duration_minutes, homework)
                    VALUES (%s,%s,%s,%s,%s) RETURNING id''',
              (version_id, ke['n'], ten, thoi_luong, bai_ve_nha or None))
        audit.record(request, audit.SYLLABUS_UPDATE, target_type='syllabus_version',
                     target_id=str(version_id), target_label=v['name'],
                     summary='Thêm buổi %d "%s" vào "%s".' % (ke['n'], ten, v['name']))
        return Response({'ok': True, 'id': s['id'], 'sortOrder': ke['n']}, status=201)


class SyllabusSessionDetailView(APIView):
    """PUT/DELETE /api/admin/syllabus-sessions/<session_id>. Xoá một buổi giữa
    chừng KHÔNG dồn số — buổi 1,2,4 vẫn hợp lệ, thứ tự đọc từ `sort_order` chứ
    không đếm dòng."""
    permission_classes = [IsCurriculumPlanner]

    def put(self, request, session_id):
        s = _buoi(session_id)
        if not s:
            return Response({'error': 'Không tìm thấy buổi học'}, status=404)
        chan = _khoa_neu_khong_nhap(s['trang_thai_ban'])
        if chan:
            return chan
        body = request.data if isinstance(request.data, dict) else {}
        doi = {}
        if 'name' in body:
            ten, loi = _loi_chu(body['name'], 'name')
            if loi:
                return Response({'error': loi}, status=400)
            doi['name'] = ten
        if 'durationMinutes' in body:
            tl = body['durationMinutes']
            if tl is None:
                doi['duration_minutes'] = None
            else:
                try:
                    tl = int(tl)
                except (TypeError, ValueError):
                    return Response({'error': 'durationMinutes phải là số phút.'}, status=400)
                if tl <= 0:
                    return Response({'error': 'durationMinutes phải lớn hơn 0.'}, status=400)
                doi['duration_minutes'] = tl
        if 'homework' in body:
            bvn, loi = _loi_chu(body['homework'], 'homework', _DAI_GHI_CHU, bat_buoc=False)
            if loi:
                return Response({'error': loi}, status=400)
            doi['homework'] = bvn or None
        if not doi:
            return Response({'ok': True})
        x('UPDATE syllabus_sessions SET %s WHERE id=%%s' %
          ', '.join('%s=%%s' % k for k in doi), tuple(doi.values()) + (session_id,))
        audit.record(request, audit.SYLLABUS_UPDATE, target_type='syllabus_version',
                     target_id=str(s['version_id']),
                     summary='Sửa buổi %d của "%s".' % (s['sort_order'], s['name']))
        return Response({'ok': True})

    def delete(self, request, session_id):
        s = _buoi(session_id)
        if not s:
            return Response({'error': 'Không tìm thấy buổi học'}, status=404)
        chan = _khoa_neu_khong_nhap(s['trang_thai_ban'])
        if chan:
            return chan
        x('DELETE FROM syllabus_sessions WHERE id=%s', (session_id,))
        audit.record(request, audit.SYLLABUS_UPDATE, target_type='syllabus_version',
                     target_id=str(s['version_id']),
                     summary='Xoá buổi %d "%s".' % (s['sort_order'], s['name']))
        return Response({'ok': True})


class SyllabusItemsView(APIView):
    """POST /api/admin/syllabus-sessions/<session_id>/items — thêm nội dung vào
    CUỐI buổi. `lessonId` tuỳ chọn: chuyên đề không phải lúc nào cũng khớp đúng
    một bài trong `lessons`."""
    permission_classes = [IsCurriculumPlanner]

    def post(self, request, session_id):
        s = _buoi(session_id)
        if not s:
            return Response({'error': 'Không tìm thấy buổi học'}, status=404)
        chan = _khoa_neu_khong_nhap(s['trang_thai_ban'])
        if chan:
            return chan
        body = request.data if isinstance(request.data, dict) else {}
        ten, loi = _loi_chu(body.get('title'), 'title')
        if loi:
            return Response({'error': loi}, status=400)
        kind = (body.get('kind') or '').strip()
        if kind not in KIND:
            return Response({'error': 'kind phải là một trong %s.' % (KIND,)}, status=400)
        lesson_id = body.get('lessonId')
        if lesson_id is not None:
            if not q1('SELECT 1 FROM lessons WHERE id=%s AND course_id=%s', (lesson_id, s['course_id'])):
                return Response({'error': 'lessonId phải là một bài học của đúng khóa này.'},
                                status=400)
        weight, loi = _trong_so(body.get('weight'))
        if loi:
            return Response({'error': loi}, status=400)

        ke = q1('SELECT COALESCE(MAX(sort_order), 0) + 1 AS n FROM syllabus_items WHERE session_id=%s',
               (session_id,))
        it = q1('''INSERT INTO syllabus_items (session_id, sort_order, kind, lesson_id, title, weight)
                     VALUES (%s,%s,%s,%s,%s,%s) RETURNING id''',
               (session_id, ke['n'], kind, lesson_id, ten, weight))
        audit.record(request, audit.SYLLABUS_UPDATE, target_type='syllabus_version',
                     target_id=str(s['version_id']),
                     summary='Thêm nội dung "%s" vào buổi %d.' % (ten, s['sort_order']))
        return Response({'ok': True, 'id': it['id'], 'sortOrder': ke['n']}, status=201)


class SyllabusItemDetailView(APIView):
    """PUT/DELETE /api/admin/syllabus-items/<item_id>."""
    permission_classes = [IsCurriculumPlanner]

    def _doc(self, item_id):
        return q1('''SELECT it.*, v.status AS trang_thai_ban, v.id AS version_id, v.course_id
                       FROM syllabus_items it
                       JOIN syllabus_sessions s ON s.id = it.session_id
                       JOIN syllabus_versions v ON v.id = s.version_id
                      WHERE it.id=%s''', (item_id,))

    def put(self, request, item_id):
        it = self._doc(item_id)
        if not it:
            return Response({'error': 'Không tìm thấy nội dung'}, status=404)
        chan = _khoa_neu_khong_nhap(it['trang_thai_ban'])
        if chan:
            return chan
        body = request.data if isinstance(request.data, dict) else {}
        doi = {}
        if 'title' in body:
            ten, loi = _loi_chu(body['title'], 'title')
            if loi:
                return Response({'error': loi}, status=400)
            doi['title'] = ten
        if 'kind' in body:
            kind = (body['kind'] or '').strip()
            if kind not in KIND:
                return Response({'error': 'kind phải là một trong %s.' % (KIND,)}, status=400)
            doi['kind'] = kind
        if 'lessonId' in body:
            lid = body['lessonId']
            if lid is not None and not q1('SELECT 1 FROM lessons WHERE id=%s AND course_id=%s',
                                          (lid, it['course_id'])):
                return Response({'error': 'lessonId phải là một bài học của đúng khóa này.'},
                                status=400)
            doi['lesson_id'] = lid
        if 'weight' in body:
            w, loi = _trong_so(body['weight'])
            if loi:
                return Response({'error': loi}, status=400)
            doi['weight'] = w
        if not doi:
            return Response({'ok': True})
        x('UPDATE syllabus_items SET %s WHERE id=%%s' %
          ', '.join('%s=%%s' % k for k in doi), tuple(doi.values()) + (item_id,))
        audit.record(request, audit.SYLLABUS_UPDATE, target_type='syllabus_version',
                     target_id=str(it['version_id']), summary='Sửa nội dung "%s".' % it['title'])
        return Response({'ok': True})

    def delete(self, request, item_id):
        it = self._doc(item_id)
        if not it:
            return Response({'error': 'Không tìm thấy nội dung'}, status=404)
        chan = _khoa_neu_khong_nhap(it['trang_thai_ban'])
        if chan:
            return chan
        x('DELETE FROM syllabus_items WHERE id=%s', (item_id,))
        audit.record(request, audit.SYLLABUS_UPDATE, target_type='syllabus_version',
                     target_id=str(it['version_id']), summary='Xoá nội dung "%s".' % it['title'])
        return Response({'ok': True})


class SyllabusMaterialsView(APIView):
    """POST /api/admin/syllabus-sessions/<session_id>/materials — thêm một học
    liệu. `fileUrl` TUỲ CHỌN (bỏ trống khi chưa có file thật — chờ bàn giao)."""
    permission_classes = [IsCurriculumPlanner]

    def post(self, request, session_id):
        s = _buoi(session_id)
        if not s:
            return Response({'error': 'Không tìm thấy buổi học'}, status=404)
        chan = _khoa_neu_khong_nhap(s['trang_thai_ban'])
        if chan:
            return chan
        body = request.data if isinstance(request.data, dict) else {}
        ten, loi = _loi_chu(body.get('title'), 'title')
        if loi:
            return Response({'error': loi}, status=400)
        file_url = (body.get('fileUrl') or '').strip() or None
        file_type = (body.get('fileType') or '').strip() or None
        ke = q1('SELECT COALESCE(MAX(sort_order), -1) + 1 AS n FROM syllabus_materials WHERE session_id=%s',
               (session_id,))
        m = q1('''INSERT INTO syllabus_materials
                    (session_id, title, file_url, file_type, sort_order, uploaded_by)
                  VALUES (%s,%s,%s,%s,%s,%s) RETURNING id''',
              (session_id, ten, file_url, file_type, ke['n'], request.user.id))
        audit.record(request, audit.SYLLABUS_UPDATE, target_type='syllabus_version',
                     target_id=str(s['version_id']),
                     summary='Thêm học liệu "%s" vào buổi %d.' % (ten, s['sort_order']))
        return Response({'ok': True, 'id': m['id']}, status=201)


class SyllabusMaterialDetailView(APIView):
    """DELETE /api/admin/syllabus-materials/<material_id>. KHÔNG có PUT: đổi học
    liệu là xoá rồi thêm lại (bảng còn mỏng, chưa cần sửa tại chỗ)."""
    permission_classes = [IsCurriculumPlanner]

    def delete(self, request, material_id):
        m = q1('''SELECT m.*, v.status AS trang_thai_ban, v.id AS version_id
                    FROM syllabus_materials m
                    JOIN syllabus_sessions s ON s.id = m.session_id
                    JOIN syllabus_versions v ON v.id = s.version_id
                   WHERE m.id=%s''', (material_id,))
        if not m:
            return Response({'error': 'Không tìm thấy học liệu'}, status=404)
        chan = _khoa_neu_khong_nhap(m['trang_thai_ban'])
        if chan:
            return chan
        x('DELETE FROM syllabus_materials WHERE id=%s', (material_id,))
        audit.record(request, audit.SYLLABUS_UPDATE, target_type='syllabus_version',
                     target_id=str(m['version_id']), summary='Xoá học liệu "%s".' % m['title'])
        return Response({'ok': True})
