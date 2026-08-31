"""Đợt học — schema `sql/legacy_schema.sql` §36.

Bảng `terms` dựng ngày 31/08/2026 nhưng chưa có đường nào tạo hay đọc nó, tức
nửa tính năng: lược đồ đã sẵn sàng còn trung tâm vẫn không dùng được. Mô-đun này
đóng nốt phần còn lại.

VÌ SAO CẦN ĐỢT HỌC. Không có nó thì "đợt 1/2027 so với đợt 2/2027" phải suy từ
`classes.starts_on` và ĐỌC TÊN LỚP — thông tin nghiệp vụ nằm trong một chuỗi tự
do, nên mọi báo cáo về sau đều phải đoán lại nó, và đoán sai thì không ai biết.
Đó đúng là cái bẫy Moodle mắc rồi phải vá bằng lồng thư mục.

MỘT TẦNG, cố ý. openSIS lồng bốn tầng (năm học → học kỳ → kỳ nhỏ → đợt) cho
trường phổ thông; một trung tâm luyện thi mở lớp theo mùa thi thì tầng thứ hai
đã là chỗ để trống. Thêm tầng sau này rẻ hơn nhiều so với gỡ tầng thừa.

XOÁ ĐỢT KHÔNG XOÁ LỚP. Khoá ngoại là `ON DELETE SET NULL` (§36), nên xoá một đợt
chỉ gỡ nhãn khỏi các lớp thuộc đợt đó — lớp, học viên, buổi học và điểm danh còn
nguyên. Nhưng vẫn phải hỏi trước, vì gán lại nhãn cho hai chục lớp bằng tay là
việc không ai muốn làm hai lần.
"""
from rest_framework.response import Response
from rest_framework.views import APIView

from common import audit
from common.db import q, q1, x
from common.permissions import IsAdminRole, IsTeacherOrAdmin
from stats.goals import as_date

#: Vòng đời một đợt. Khớp `terms_status_check` ở §36 — hai nơi lệch nhau thì một
#: giá trị hợp lệ trên giao diện sẽ bị CSDL từ chối, và câu lỗi hiện ra là câu
#: của Postgres chứ không phải câu viết cho người đọc.
TERM_STATUS = ('active', 'finished', 'cancelled')

TERM_TEXT_FIELDS = {'code': 40, 'name': 160, 'note': 1000}
TERM_DATE_FIELDS = ('starts_on', 'ends_on', 'exam_date')


def _clean(body):
    """Body → (dict cột CSDL, lỗi). Chỉ lấy trường thật sự được gửi.

    Dùng chung cho POST và PATCH, cùng lý do với `_clean_class_payload`: hai
    đường kiểm tra riêng thì sớm muộn tạo được thứ mà sửa lại không được.
    """
    data = {}
    for field, limit in TERM_TEXT_FIELDS.items():
        if field in body:
            # `body[field] is not None` PHẢI kiểm trước. Thiếu vế đó thì
            # `str(None)` ra chuỗi "None" — bốn ký tự, truthy — và nó đi thẳng
            # vào CSDL. Giao diện gửi `code: code.trim() || null` cho ô để
            # trống, nên đây không phải trường hợp hiếm mà là đường đi THƯỜNG
            # NHẤT. Đo 31/08/2026: tạo hai đợt học đều bỏ trống mã thì cái thứ
            # hai bị chặn bằng câu 'Mã đợt "None" đã có rồi.'
            # Và `PATCH {note: null}` KHÔNG xoá được ghi chú mà ghi đè thành
            # chữ "None".
            val = (str(body[field]).strip() or None) if body[field] is not None else None
            data[field] = val[:limit] if val else None
    for field in TERM_DATE_FIELDS:
        if field in body:
            raw = body[field]
            if raw in (None, ''):
                data[field] = None
            else:
                d = as_date(raw)
                if not d:
                    return None, 'Ngày "%s" không hợp lệ (định dạng YYYY-MM-DD).' % field
                data[field] = d
    if 'status' in body:
        # `str(...)` trước khi `.strip()`: gửi `{"status": 5}` thì
        # `(5 or '').strip()` ném AttributeError, và DRF biến nó thành 500
        # "Lỗi máy chủ nội bộ" — một dữ liệu vào sai lại hiện ra như hệ thống
        # hỏng. Dữ liệu vào sai phải là 400 kèm câu chữ đọc được.
        st = str(body['status'] or '').strip()
        if st not in TERM_STATUS:
            return None, 'Trạng thái phải là một trong: %s.' % ', '.join(TERM_STATUS)
        data['status'] = st

    # Ngày kết thúc trước ngày bắt đầu là gõ nhầm, và nó lặng lẽ làm mọi báo cáo
    # theo đợt trả về rỗng. Bắt ngay lúc nhập rẻ hơn nhiều so với đi tìm sau.
    tu, den = data.get('starts_on'), data.get('ends_on')
    if tu and den and tu > den:
        return None, 'Ngày kết thúc phải sau ngày bắt đầu.'
    return data, None


def _dict(r):
    """Một đợt ở dạng JSON. Khoá camelCase cho khớp phần còn lại của teaching/."""
    def ngay(k):
        v = r.get(k)
        return v.isoformat() if v else None

    out = {
        'id': r['id'], 'code': r['code'], 'name': r['name'],
        'startsOn': ngay('starts_on'), 'endsOn': ngay('ends_on'),
        'examDate': ngay('exam_date'), 'status': r['status'], 'note': r['note'],
    }
    if 'classes' in r:
        out['classes'] = r['classes'] or 0
    if 'students' in r:
        out['students'] = r['students'] or 0
    return out


class AdminTermsView(APIView):
    """GET/POST /api/admin/terms — danh sách & tạo đợt."""
    permission_classes = [IsAdminRole]

    def get(self, request):
        # Đếm lớp VÀ học viên trong cùng một câu. Đây là hai con số đầu tiên ai
        # mở màn hình này cũng muốn biết ("đợt vừa rồi có bao nhiêu em"), và gọi
        # thêm một câu cho mỗi đợt là đúng cái N+1 mà module teaching/ cấm.
        rows = q('''SELECT t.*,
                           (SELECT COUNT(*) FROM classes c WHERE c.term_id = t.id) AS classes,
                           (SELECT COUNT(*) FROM class_members m
                              JOIN classes c ON c.id = m.class_id
                              JOIN users u ON u.id = m.user_id
                             WHERE c.term_id = t.id AND m.left_at IS NULL
                               AND u.role = %s) AS students
                    FROM terms t
                    ORDER BY COALESCE(t.starts_on, DATE '1900-01-01') DESC, t.id DESC''',
                 ('Học viên',))
        return Response({'terms': [_dict(r) for r in rows], 'statuses': list(TERM_STATUS)})

    def post(self, request):
        body = request.data if isinstance(request.data, dict) else {}
        data, err = _clean(body)
        if err:
            return Response({'error': err}, status=400)
        if not data.get('name'):
            return Response({'error': 'Đợt học phải có tên, ví dụ "Đợt 1/2027".'}, status=400)

        if data.get('code') and q1('SELECT 1 FROM terms WHERE code=%s', (data['code'],)):
            return Response({'error': 'Mã đợt "%s" đã có rồi.' % data['code']}, status=409)

        cols = list(data)
        row = q1('INSERT INTO terms (%s) VALUES (%s) RETURNING id'
                 % (', '.join(cols), ', '.join(['%s'] * len(cols))),
                 tuple(data[c] for c in cols))

        audit.record(request, audit.TERM_CREATE, target_type='term', target_id=row['id'],
                     target_label=data['name'],
                     summary='Tạo đợt học "%s".' % data['name'],
                     detail={k: (v.isoformat() if hasattr(v, 'isoformat') else v)
                             for k, v in data.items()})
        return Response({'ok': True, 'id': row['id']}, status=201)


class AdminTermDetailView(APIView):
    """PATCH/DELETE /api/admin/terms/<id>."""
    permission_classes = [IsAdminRole]

    def patch(self, request, term_id):
        before = q1('SELECT * FROM terms WHERE id=%s', (term_id,))
        if not before:
            return Response({'error': 'Không tìm thấy đợt học này.'}, status=404)

        body = request.data if isinstance(request.data, dict) else {}
        data, err = _clean(body)
        if err:
            return Response({'error': err}, status=400)
        if not data:
            return Response({'error': 'Không có trường hợp lệ để cập nhật.'}, status=400)

        # Ghép với giá trị ĐANG CÓ trước khi kiểm khoảng ngày: PATCH chỉ gửi một
        # trường, nên sửa mỗi `ends_on` mà không so với `starts_on` cũ là để lọt
        # đúng cái sai mà `_clean` sinh ra để chặn.
        tu = data.get('starts_on', before['starts_on'])
        den = data.get('ends_on', before['ends_on'])
        if tu and den and tu > den:
            return Response({'error': 'Ngày kết thúc phải sau ngày bắt đầu.'}, status=400)

        if data.get('code') and data['code'] != before['code'] and \
                q1('SELECT 1 FROM terms WHERE code=%s AND id<>%s', (data['code'], term_id)):
            return Response({'error': 'Mã đợt "%s" đã có rồi.' % data['code']}, status=409)

        cols = list(data)
        x('UPDATE terms SET %s WHERE id=%%s' % ', '.join('%s=%%s' % c for c in cols),
          tuple(data[c] for c in cols) + (term_id,))

        audit.record(request, audit.TERM_UPDATE, target_type='term', target_id=term_id,
                     target_label=data.get('name') or before['name'],
                     summary='Sửa đợt học "%s".' % (data.get('name') or before['name']),
                     detail={k: (v.isoformat() if hasattr(v, 'isoformat') else v)
                             for k, v in data.items()})
        after = q1('SELECT * FROM terms WHERE id=%s', (term_id,))
        return Response({'ok': True, 'term': _dict(after)})

    def delete(self, request, term_id):
        before = q1('SELECT * FROM terms WHERE id=%s', (term_id,))
        if not before:
            return Response({'error': 'Không tìm thấy đợt học này.'}, status=404)

        n = q1('SELECT COUNT(*) AS n FROM classes WHERE term_id=%s', (term_id,))['n']
        confirm = str(request.query_params.get('confirm') or '').strip().lower() \
            in ('1', 'true', 'yes')
        if n and not confirm:
            # 409 chứ không 400: yêu cầu hợp lệ, chỉ đang xung đột với dữ liệu đã
            # có. Nói RÕ là lớp không mất — người đọc câu này đang sợ mất dữ liệu,
            # và câu trả lời đúng là "không mất, chỉ mất nhãn".
            return Response({
                'error': ('Đợt này đang gắn %d lớp. Xoá đợt KHÔNG xoá lớp nào — các lớp '
                          'đó chỉ mất nhãn đợt và phải gán lại bằng tay. Gửi lại kèm '
                          '?confirm=1 nếu vẫn muốn xoá.' % n),
                'classes': n,
                'needsConfirm': True,
            }, status=409)

        x('DELETE FROM terms WHERE id=%s', (term_id,))
        audit.record(request, audit.TERM_DELETE, target_type='term', target_id=term_id,
                     target_label=before['name'],
                     summary='Xoá đợt học "%s" — %d lớp mất nhãn đợt, dữ liệu giữ nguyên.'
                             % (before['name'], n),
                     detail={'classes': n, 'confirmed': confirm})
        return Response({'ok': True, 'unlinkedClasses': n})


class TermsLiteView(APIView):
    """GET /api/teach/terms — danh sách đợt gọn, cho ô chọn khi tạo/sửa lớp.

    Tách khỏi `AdminTermsView` vì giảng viên cũng cần đọc để lọc lớp theo đợt,
    mà họ KHÔNG được vào khu quản trị. Trả đúng những gì một ô chọn cần, không
    kèm con số thống kê.
    """
    permission_classes = [IsTeacherOrAdmin]

    def get(self, request):
        rows = q('''SELECT id, code, name, starts_on, ends_on, exam_date, status, note
                    FROM terms
                    ORDER BY COALESCE(starts_on, DATE '1900-01-01') DESC, id DESC''')
        return Response({'terms': [_dict(r) for r in rows]})
