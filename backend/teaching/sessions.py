"""Buổi học & điểm danh — đặc tả ERP §4, schema sql/legacy_schema.sql §33.

Trước khối này ``classes.schedule`` mới chỉ là một dòng MÔ TẢ lịch ("Tối 2-4-6").
Đủ để in lên trang giới thiệu, nhưng không trả lời được câu hỏi vận hành nào:
buổi tới học gì, hôm qua ai vắng, em này nghỉ mấy buổi rồi. Ba câu đó là công
việc hằng ngày của giảng viên TopHSA — lớp online có lịch cố định.

BẢN NÀY LÀ GIẢNG VIÊN TICK TAY. Đặc tả §4 còn để ngỏ câu hỏi cho TopHSA — dạy
trên nền tảng nào (Zoom/Meet/Zalo), có API lấy danh sách người tham dự không —
và ghi rằng "hai thiết kế khác hẳn nhau". Khác ở chỗ ĐIỀN dữ liệu, không phải ở
chỗ CHỨA: hai bảng ``class_sessions``/``attendance`` giữ nguyên khi có API, lúc
đó chỉ thêm một bộ nhập tự động ghi vào cùng chỗ, và ``marked_by IS NULL`` là
dấu hiệu "máy điền". Vì vậy không chờ TopHSA trả lời mới làm được phần này.

QUYỀN THEO NGỮ CẢNH. Vào được khu vực giảng dạy (``IsTeacherOrAdmin``) không có
nghĩa là xem được mọi lớp. Mọi endpoint ở đây nhận ``class_id`` hoặc
``session_id`` đều đi qua ``can_see_class`` và trả **404 chứ không 403** khi
không được xem — 403 là tự thú nhận "lớp đó có tồn tại", tức là rò rỉ danh sách
lớp của trung tâm cho bất kỳ giảng viên nào biết đoán số.

SỐ CÂU TRUY VẤN LÀ THIẾT KẾ, KHÔNG PHẢI TỐI ƯU HOÁ VẶT. Mỗi lượt tới Neon tốn
~245ms thuần đường truyền (teaching/reports.py, nguyên tắc 1). Một lớp 30 học
viên với 24 buổi mà mỗi buổi một câu đếm điểm danh là 24 lượt ≈ 6 giây cho một
màn hình danh sách, và mỗi học viên một câu UPSERT khi tick là 30 lượt ≈ 7 giây
cho một lần bấm Lưu. Nên: mọi endpoint ở đây dùng SỐ CÂU CỐ ĐỊNH (không phụ
thuộc số buổi/số học viên) rồi ghép trong Python, và điểm danh cả lớp là MỘT câu
INSERT nhiều dòng.
"""
import json
from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from common.audit import ATTENDANCE_MARK, SESSION_CREATE, SESSION_DELETE, SESSION_UPDATE, record
from common.clock import local_now
from common.db import q, q1, x
from common.events import KIND_ATTENDANCE, SOURCE_SYSTEM, forget_events, record_events
from common.params import so_nguyen
from common.permissions import IsTeacherOrAdmin, can_see_class
from stats.goals import as_date
from teaching.vocab import chi_hoc_vien

#: Trạng thái một buổi học. Khớp chú thích cột ở legacy_schema.sql §33.
SESSION_STATUS = ('planned', 'done', 'cancelled')

#: Trạng thái điểm danh của một học viên trong một buổi.
ATTENDANCE_STATUS = ('present', 'late', 'absent', 'excused')

#: Nhãn tiếng Việt để dựng câu tóm tắt nhật ký kiểm toán. Dựng câu lúc GHI chứ
#: không lúc đọc — xem lý do ở đầu common/audit.py.
ATTENDANCE_LABEL = {
    'present': 'có mặt', 'late': 'muộn', 'absent': 'vắng', 'excused': 'có phép',
}

#: Độ dài mặc định của một buổi khi giảng viên chưa điền ``duration_minutes``.
#: CHỈ dùng để dò trùng giờ, không bao giờ ghi xuống CSDL. Để lộ thành hằng số ở
#: đây thay vì chôn trong câu SQL vì đây là một GIẢ ĐỊNH về cách TopHSA dạy, và
#: giả định thì phải nhìn thấy được mới sửa được.
DEFAULT_SESSION_MINUTES = 90

#: Chặn trên của ``duration_minutes``. 600 phút = 10 tiếng: dài hơn mọi buổi học
#: thật, nên số vượt mức này gần như chắc chắn là gõ nhầm đơn vị (giây, hoặc
#: thừa số 0) — bắt ngay lúc nhập rẻ hơn nhiều so với đi sửa báo cáo sau.
MAX_SESSION_MINUTES = 600

#: Phân trang danh sách buổi.
DEFAULT_LIMIT = 100
MAX_LIMIT = 500

#: Độ dài tối đa của từng trường chữ, cắt lúc ghi. Cùng cách làm với
#: CLASS_TEXT_FIELDS ở teaching/views.py.
SESSION_TEXT_FIELDS = {
    'topic': 200, 'meeting_url': 400, 'recording_url': 400, 'note': 2000,
}

_NOT_FOUND_CLASS = {'error': 'Không tìm thấy lớp này.'}
_NOT_FOUND_SESSION = {'error': 'Không tìm thấy buổi học này.'}

_STARTS_AT_FORMAT = ('Giờ bắt đầu (starts_at) phải theo ISO 8601, '
                     'ví dụ "2026-09-08T19:30" hoặc "2026-09-08T19:30:00+07:00".')


# ── Đọc & làm sạch dữ liệu vào ─────────────────────────────────────────────

def _parse_starts_at(raw):
    """Chuỗi ISO 8601 → ``datetime`` NGÂY THƠ theo giờ Việt Nam, hoặc None.

    Cột ``class_sessions.starts_at`` là TIMESTAMP WITHOUT TIME ZONE và cả hệ
    thống quy ước chứa giờ Việt Nam (xem common/clock.py). Nên chuỗi có múi giờ
    phải ĐỔI VỀ giờ Việt Nam rồi mới bỏ tzinfo. Nếu cứ cắt phăng phần offset,
    một buổi 20h tối do trình duyệt gửi lên dạng UTC ("2026-09-08T13:00:00Z") sẽ
    nằm ở 13h trưa trong CSDL — lệch đúng 7 tiếng, và tệ hơn là buổi tối muộn
    nhảy hẳn sang ngày hôm sau, kéo theo ``event_date`` của điểm danh sai ngày.
    """
    if isinstance(raw, datetime):
        dt = raw
    else:
        s = str(raw or '').strip().replace(' ', 'T')
        if not s:
            return None
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            return None
    if dt.tzinfo is not None:
        dt = timezone.localtime(dt).replace(tzinfo=None)
    return dt


def _clean_session_payload(body):
    """Body → (dict cột CSDL, lỗi). CHỈ lấy những trường thật sự được gửi.

    Dùng chung cho POST (tạo) và PATCH (sửa) để hai đường không lệch luật kiểm
    tra. PATCH chỉ đụng vào trường có mặt trong body, nên sửa chủ đề không vô
    tình xoá link phòng học.
    """
    data = {}

    if 'starts_at' in body:
        dt = _parse_starts_at(body['starts_at'])
        if dt is None:
            return None, _STARTS_AT_FORMAT
        data['starts_at'] = dt

    if 'duration_minutes' in body:
        raw = body['duration_minutes']
        if raw in (None, ''):
            data['duration_minutes'] = None
        else:
            try:
                minutes = int(raw)
            except (TypeError, ValueError):
                return None, 'Độ dài buổi học (duration_minutes) phải là số phút nguyên.'
            if minutes <= 0 or minutes > MAX_SESSION_MINUTES:
                return None, ('Độ dài buổi học phải trong khoảng 1–%d phút.'
                              % MAX_SESSION_MINUTES)
            data['duration_minutes'] = minutes

    for field, limit in SESSION_TEXT_FIELDS.items():
        if field in body:
            val = (str(body[field]).strip() or None) if body[field] is not None else None
            data[field] = val[:limit] if val else None

    if 'lesson_refs' in body:
        refs = body['lesson_refs']
        if refs in (None, '', [], {}):
            data['lesson_refs'] = None
        elif isinstance(refs, (list, dict)):
            data['lesson_refs'] = json.dumps(refs, ensure_ascii=False)
        else:
            return None, ('lesson_refs phải là danh sách id bài học, '
                          'ví dụ ["hsa_q_01", "hsa_q_02"].')

    if 'status' in body:
        st = str(body['status'] or '').strip()
        if st not in SESSION_STATUS:
            return None, ('Trạng thái buổi học phải là một trong: %s.'
                          % ', '.join(SESSION_STATUS))
        data['status'] = st

    return data, None


def _sql_values(cols):
    """Placeholder cho từng cột, ép kiểu jsonb ở đúng chỗ cần.

    ``lesson_refs`` là JSONB còn tham số gửi lên là chuỗi: psycopg gửi kiểu
    ``text`` và Postgres KHÔNG tự ép text→jsonb, nên thiếu ``::jsonb`` là lỗi
    "column is of type jsonb but expression is of type text" ngay câu INSERT
    đầu tiên. Cùng lý do với ``%s::jsonb`` ở common/events.py.
    """
    return ['%s::jsonb' if c == 'lesson_refs' else '%s' for c in cols]


# ── Truy vấn dùng chung ────────────────────────────────────────────────────

def _class_row(class_id):
    """Lớp + sĩ số đang học trong MỘT câu (subselect thay cho một lượt Neon nữa)."""
    return q1('''SELECT c.id, c.code, c.name, c.course_id, c.meeting_url, c.schedule,
                        (SELECT COUNT(*) FROM class_members m
                           JOIN users mu ON mu.id = m.user_id
                          WHERE m.class_id = c.id AND m.left_at IS NULL
                            AND ''' + chi_hoc_vien('mu') + ''') AS members
                 FROM classes c WHERE c.id = %s''', (class_id,))


def _session_row(session_id):
    """Buổi học kèm thông tin lớp — một câu, vì bước sau luôn cần cả hai.

    ``class_id`` trả về ở đây chính là thứ dùng để gọi ``can_see_class``: không
    có nó thì không kiểm quyền được, nên hai thứ phải về cùng một lượt.
    """
    return q1('''SELECT s.*, c.name AS class_name, c.code AS class_code,
                        c.course_id AS class_course_id
                 FROM class_sessions s
                 JOIN classes c ON c.id = s.class_id
                 WHERE s.id = %s''', (session_id,))


def _attendance_counts(class_id, session_ids):
    """Số liệu điểm danh của TOÀN BỘ buổi trong một câu ``GROUP BY session_id``.

    Hai phép đếm khác nhau, cố ý:

    · ``present/late/absent/excused`` đếm MỌI dòng điểm danh của buổi — kể cả
      học viên sau đó đã rời lớp. Đó là BẢN GHI LỊCH SỬ: buổi hôm ấy có 12 em
      ngồi học là 12, không thể tụt xuống 11 chỉ vì tháng sau một em chuyển lớp.

    · ``marked_active`` chỉ đếm học viên ĐANG trong lớp, vì nó dùng để tính
      ``unmarked`` = còn bao nhiêu em chưa tick. Lấy tổng số dòng mà trừ thì em
      đã rời lớp sẽ ăn gian một suất, và giảng viên thấy "đã điểm danh xong"
      trong khi vẫn còn người chưa tick.
    """
    if not session_ids:
        return {}
    rows = q('''SELECT a.session_id,
                       COUNT(*) FILTER (WHERE a.status = 'present')   AS present,
                       COUNT(*) FILTER (WHERE a.status = 'late')      AS late,
                       COUNT(*) FILTER (WHERE a.status = 'absent')    AS absent,
                       COUNT(*) FILTER (WHERE a.status = 'excused')   AS excused,
                       COUNT(*) FILTER (WHERE m.user_id IS NOT NULL)  AS marked_active
                FROM attendance a
                LEFT JOIN class_members m
                       ON m.class_id = %s AND m.user_id = a.user_id
                      AND m.left_at IS NULL
                WHERE a.session_id = ANY(%s)
                GROUP BY a.session_id''', (class_id, list(session_ids)))
    return {r['session_id']: r for r in rows}


def _overlap_warning(class_id, starts_at, minutes, exclude_id=None):
    """Câu cảnh báo nếu lớp đã có buổi khác trùng giờ, hoặc None.

    CẢNH BÁO CHỨ KHÔNG CHẶN. Một lớp hoàn toàn có thể tách hai nhóm học cùng
    khung giờ, nên chặn là chặn nhầm việc có thật. Nhưng im lặng cũng sai: giảng
    viên tạo nhầm buổi thứ hai rồi tick điểm danh vào buổi rỗng, và lúc phát
    hiện thì phải gỡ tay từng dòng ``attendance`` — sửa sau đắt hơn cảnh báo
    trước rất nhiều.

    Buổi đã HUỶ không tính là trùng: nó không chiếm giờ của ai nữa.
    """
    dur = minutes or DEFAULT_SESSION_MINUTES
    sql = ('''SELECT id, starts_at, topic FROM class_sessions
              WHERE class_id = %s AND status <> 'cancelled'
                AND starts_at < %s + (%s::int * INTERVAL '1 minute')
                AND starts_at + (COALESCE(duration_minutes, %s::int)
                                 * INTERVAL '1 minute') > %s''')
    params = [class_id, starts_at, dur, DEFAULT_SESSION_MINUTES, starts_at]
    if exclude_id is not None:
        sql += ' AND id <> %s'
        params.append(exclude_id)
    sql += ' ORDER BY starts_at LIMIT 3'
    rows = q(sql, tuple(params))
    if not rows:
        return None
    which = ', '.join('#%d %s (%s)'
                      % (r['id'], r['topic'] or 'chưa đặt chủ đề',
                         r['starts_at'].strftime('%d/%m %H:%M'))
                      for r in rows)
    return ('Lớp này đã có buổi trùng giờ: %s. Buổi mới vẫn được tạo — '
            'kiểm tra lại nếu không cố ý.' % which)


def _session_dict(r, counts=None, member_count=None):
    """Một buổi học ở dạng JSON. Khoá camelCase cho khớp teaching/reports.py."""
    out = {
        'id': r['id'],
        'classId': r['class_id'],
        'startsAt': r['starts_at'].isoformat() if r['starts_at'] else None,
        'durationMinutes': r['duration_minutes'],
        'topic': r['topic'],
        'lessonRefs': r['lesson_refs'],
        'meetingUrl': r['meeting_url'],
        'recordingUrl': r['recording_url'],
        'status': r['status'],
        'note': r['note'],
        'createdAt': r['created_at'].isoformat() if r.get('created_at') else None,
        'updatedAt': r['updated_at'].isoformat() if r.get('updated_at') else None,
        # Có con dấu này thì "0 dòng điểm danh" mới đọc được: chưa có dấu là
        # giảng viên CHƯA tick, có dấu mà 0 vắng là cả lớp đi đủ. Hai chuyện đó
        # trước đây trông y hệt nhau trên màn hình.
        'attendanceTakenAt': (r['attendance_taken_at'].isoformat()
                              if r.get('attendance_taken_at') else None),
        'attendanceTakenBy': r.get('attendance_taken_by'),
    }
    if 'class_name' in r:
        out['className'] = r['class_name']
        out['classCode'] = r['class_code']
    if counts is not None or member_count is not None:
        c = counts or {}
        marked_active = int(c.get('marked_active') or 0)
        out['attendance'] = {
            'present': int(c.get('present') or 0),
            'late': int(c.get('late') or 0),
            'absent': int(c.get('absent') or 0),
            'excused': int(c.get('excused') or 0),
            # Con số giảng viên cần nhất: "buổi hôm qua tôi điểm danh xong chưa?".
            # max(0, …) vì lớp có thể bớt người sau khi đã tick.
            'unmarked': max(0, int(member_count or 0) - marked_active),
        }
    return out


# ── 1. Danh sách & tạo buổi học ────────────────────────────────────────────

class ClassSessionsView(APIView):
    """GET/POST /api/teach/classes/<class_id>/sessions — sổ buổi học của một lớp.

    Đây là màn hình giảng viên mở đầu tiên mỗi tối: buổi nào sắp tới, buổi nào
    đã dạy mà chưa điểm danh. Vì thế mỗi buổi trả kèm luôn số liệu điểm danh đã
    tổng hợp — bắt giao diện gọi thêm một lượt cho từng buổi là đúng cái lỗi
    N+1 mà nguyên tắc 1 của teaching/reports.py đặt ra để tránh.
    """
    permission_classes = [IsTeacherOrAdmin]

    def get(self, request, class_id):
        if not can_see_class(request.user, class_id):
            # 404 chứ không 403: không tiết lộ lớp đó có tồn tại hay không.
            return Response(_NOT_FOUND_CLASS, status=404)
        info = _class_row(class_id)
        if not info:
            return Response(_NOT_FOUND_CLASS, status=404)

        where, params = ['class_id = %s'], [class_id]

        raw_from = (request.query_params.get('from') or '').strip()
        if raw_from:
            d = as_date(raw_from)
            if not d:
                return Response({'error': 'Tham số "from" phải có dạng YYYY-MM-DD.'},
                                status=400)
            where.append('starts_at >= %s')
            params.append(datetime.combine(d, time.min))

        raw_to = (request.query_params.get('to') or '').strip()
        if raw_to:
            d = as_date(raw_to)
            if not d:
                return Response({'error': 'Tham số "to" phải có dạng YYYY-MM-DD.'},
                                status=400)
            # Lấy tới HẾT ngày đó. Giảng viên gõ "đến 30/08" là có ý gồm cả buổi
            # tối 30/08, mà `starts_at <= '30-08 00:00'` thì loại đúng buổi ấy —
            # lỗi im lặng, chỉ lộ ra khi có người đếm thiếu một buổi.
            where.append('starts_at < %s')
            params.append(datetime.combine(d + timedelta(days=1), time.min))

        raw_status = (request.query_params.get('status') or '').strip()
        if raw_status:
            if raw_status not in SESSION_STATUS:
                return Response({'error': 'Trạng thái phải là một trong: %s.'
                                          % ', '.join(SESSION_STATUS)}, status=400)
            where.append('status = %s')
            params.append(raw_status)

        limit = so_nguyen(request.query_params.get('limit'), DEFAULT_LIMIT, 1, MAX_LIMIT)

        rows = q(f'''SELECT * FROM class_sessions
                     WHERE {' AND '.join(where)}
                     ORDER BY starts_at DESC, id DESC
                     LIMIT %s''', tuple(params) + (limit,))

        # MỘT câu đếm cho TOÀN BỘ buổi vừa lấy, không phải mỗi buổi một câu.
        counts = _attendance_counts(class_id, [r['id'] for r in rows])
        members = int(info['members'] or 0)

        return Response({
            'class': {
                'id': info['id'], 'code': info['code'], 'name': info['name'],
                'course': info['course_id'], 'schedule': info['schedule'],
                'meetingUrl': info['meeting_url'], 'members': members,
            },
            'sessions': [_session_dict(r, counts.get(r['id']), members) for r in rows],
            'statuses': list(SESSION_STATUS),
            'attendanceStatuses': list(ATTENDANCE_STATUS),
        })

    def post(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response(_NOT_FOUND_CLASS, status=404)
        info = _class_row(class_id)
        if not info:
            return Response(_NOT_FOUND_CLASS, status=404)

        body = request.data if isinstance(request.data, dict) else {}
        data, err = _clean_session_payload(body)
        if err:
            return Response({'error': err}, status=400)
        if not data.get('starts_at'):
            return Response({'error': 'Buổi học phải có giờ bắt đầu. ' + _STARTS_AT_FORMAT},
                            status=400)

        if not data.get('meeting_url'):
            # KẾ THỪA link phòng của lớp. Lớp online của TopHSA có phòng cố định
            # cả khoá; bắt giảng viên dán lại link mỗi buổi chỉ tạo ra những buổi
            # thiếu link, và học viên thì phát hiện điều đó lúc 19h58.
            data['meeting_url'] = info['meeting_url']
        data.setdefault('status', 'planned')

        warning = _overlap_warning(class_id, data['starts_at'],
                                   data.get('duration_minutes'))

        data['class_id'] = class_id
        data['created_by'] = request.user.id
        data['created_at'] = local_now()          # local_now, không phải now() của SQL
        cols = list(data)
        row = q1('INSERT INTO class_sessions (%s) VALUES (%s) RETURNING *'
                 % (', '.join(cols), ', '.join(_sql_values(cols))), tuple(data.values()))

        record(request, SESSION_CREATE,
               target_type='class_session', target_id=row['id'],
               target_label=row['topic'] or row['starts_at'].strftime('%d/%m/%Y %H:%M'),
               summary='Tạo buổi %s lớp %s (%s)'
                       % (row['topic'] or 'chưa đặt chủ đề', info['name'],
                          row['starts_at'].strftime('%d/%m/%Y %H:%M')),
               detail={'class_id': class_id, 'starts_at': row['starts_at'].isoformat(),
                       'duration_minutes': row['duration_minutes'],
                       'status': row['status'], 'warning': warning})

        out = {'ok': True, 'id': row['id'], 'session': _session_dict(row)}
        if warning:
            out['warning'] = warning
        return Response(out, status=201)


# ── 2. Chi tiết một buổi ───────────────────────────────────────────────────

class ClassSessionDetailView(APIView):
    """GET/PATCH/DELETE /api/teach/sessions/<session_id> — một buổi cụ thể.

    Định tuyến theo ``session_id`` chứ không kèm ``class_id``, nên quyền phải
    suy ngược: nạp buổi → lấy ``class_id`` → ``can_see_class``. Không tìm thấy
    buổi và không được xem lớp trả CÙNG một 404, để không dò được id buổi của
    lớp người khác bằng cách so sánh mã lỗi.
    """
    permission_classes = [IsTeacherOrAdmin]

    def _load(self, request, session_id):
        row = _session_row(session_id)
        if not row or not can_see_class(request.user, row['class_id']):
            return None
        return row

    def get(self, request, session_id):
        row = self._load(request, session_id)
        if not row:
            return Response(_NOT_FOUND_SESSION, status=404)
        # Không kèm bảng điểm danh ở đây: /sessions/<id>/attendance đã trả danh
        # sách đầy đủ kèm số liệu. Hai nơi cùng tính một con số là hai nơi sẽ
        # lệch nhau sau vài lần sửa.
        return Response({'session': _session_dict(row)})

    def patch(self, request, session_id):
        row = self._load(request, session_id)
        if not row:
            return Response(_NOT_FOUND_SESSION, status=404)

        body = request.data if isinstance(request.data, dict) else {}
        data, err = _clean_session_payload(body)
        if err:
            return Response({'error': err}, status=400)
        if not data:
            return Response({'error': 'Không có trường hợp lệ để cập nhật.'}, status=400)

        # Dời giờ cũng phải cảnh báo trùng như lúc tạo: dời vào đúng khung giờ
        # một buổi khác là cách phổ biến nhất để tạo ra trùng lịch.
        warning = None
        if 'starts_at' in data:
            warning = _overlap_warning(
                row['class_id'], data['starts_at'],
                data.get('duration_minutes', row['duration_minutes']),
                exclude_id=session_id)

        # `strict=True`: lệch một phần tử là ghép nhầm tên cột với placeholder
        # của cột khác — câu UPDATE vẫn chạy, và ghi giá trị sang sai cột.
        sets = ', '.join('%s = %s' % (c, p)
                         for c, p in zip(data, _sql_values(data), strict=True))
        after = q1('UPDATE class_sessions SET %s, updated_at = %%s WHERE id = %%s '
                   'RETURNING *' % sets,
                   tuple(data.values()) + (local_now(), session_id))

        record(request, SESSION_UPDATE,
               target_type='class_session', target_id=session_id,
               target_label=after['topic'] or after['starts_at'].strftime('%d/%m/%Y %H:%M'),
               summary='Sửa buổi %s lớp %s (%s)'
                       % (after['topic'] or 'chưa đặt chủ đề', row['class_name'],
                          ', '.join(sorted(data))),
               # Chép cả giá trị CŨ: nhật ký chỉ ghi giá trị mới thì đọc lại
               # không biết đã đổi từ đâu, mà "đổi từ đâu" mới là thứ cần khi
               # phải dựng lại một buổi bị sửa nhầm.
               detail={'fields': sorted(data),
                       'before': {k: (row[k].isoformat()
                                      if hasattr(row.get(k), 'isoformat') else row.get(k))
                                  for k in data},
                       'warning': warning})

        out = {'ok': True, 'session': _session_dict(after)}
        if warning:
            out['warning'] = warning
        return Response(out)

    def delete(self, request, session_id):
        row = self._load(request, session_id)
        if not row:
            return Response(_NOT_FOUND_SESSION, status=404)

        marked = q1('SELECT COUNT(*) AS n FROM attendance WHERE session_id = %s',
                    (session_id,))
        n = int((marked or {}).get('n') or 0)
        confirm = str(request.query_params.get('confirm') or '').strip().lower() \
            in ('1', 'true', 'yes')

        if n and not confirm:
            # 409 chứ không 400: yêu cầu hợp lệ, chỉ là đang xung đột với dữ liệu
            # đã có. FK của attendance là ON DELETE CASCADE nên xoá buổi là xoá
            # trắng chuyên cần cả lớp buổi đó, không có bản sao nào để khôi phục.
            # Bắt bấm xác nhận một lần là hàng rào rẻ nhất cho việc không lùi được.
            return Response({
                'error': 'Buổi này đã có %d dòng điểm danh — xoá là mất luôn bản ghi '
                         'chuyên cần của cả lớp buổi đó. Gửi lại kèm ?confirm=1 nếu '
                         'vẫn muốn xoá.' % n,
                'attendanceRows': n,
                'needsConfirm': True,
            }, status=409)

        x('DELETE FROM class_sessions WHERE id = %s', (session_id,))

        record(request, SESSION_DELETE,
               target_type='class_session', target_id=session_id,
               target_label=row['topic'] or row['starts_at'].strftime('%d/%m/%Y %H:%M'),
               summary='Xoá buổi %s lớp %s (%s), mất %d dòng điểm danh'
                       % (row['topic'] or 'chưa đặt chủ đề', row['class_name'],
                          row['starts_at'].strftime('%d/%m/%Y %H:%M'), n),
               detail={'class_id': row['class_id'],
                       'starts_at': row['starts_at'].isoformat(),
                       'attendance_rows': n, 'confirmed': confirm})

        # Dọn luôn các sự kiện điểm danh trỏ tới buổi vừa xoá. Để lại thì buổi
        # đã biến mất vẫn tính vào "hoạt động gần nhất" của học viên — em trông
        # như còn đang học nhờ một buổi không còn tồn tại.
        # Đi qua common/events.py chứ không tự viết DELETE: đó là cửa duy nhất
        # được đụng vào learning_events, cả ghi lẫn xoá.
        forgotten = forget_events('class_session', session_id)
        return Response({'ok': True, 'deletedAttendance': n, 'deletedEvents': forgotten})


# ── 3. Điểm danh ───────────────────────────────────────────────────────────

class SessionAttendanceView(APIView):
    """GET/POST /api/teach/sessions/<session_id>/attendance — bảng tick của một buổi.

    GET trả DANH SÁCH ĐẦY ĐỦ học viên đang trong lớp kèm trạng thái hiện tại
    (``null`` nếu chưa tick), chứ không phải chỉ những dòng đã nằm trong bảng
    ``attendance``. Lý do rất thực dụng: giảng viên mở màn hình ra là để tick cả
    lớp. Trả về mỗi dòng đã có thì giao diện phải tự đối chiếu hai danh sách để
    biết còn ai chưa điểm danh — đúng việc mà máy chủ vừa làm xong và làm chính
    xác hơn, vì nó biết ai đã rời lớp.
    """
    permission_classes = [IsTeacherOrAdmin]

    def _load(self, request, session_id):
        row = _session_row(session_id)
        if not row or not can_see_class(request.user, row['class_id']):
            return None
        return row

    def get(self, request, session_id):
        row = self._load(request, session_id)
        if not row:
            return Response(_NOT_FOUND_SESSION, status=404)
        class_id = row['class_id']

        # Câu 1: danh sách lớp LEFT JOIN điểm danh của buổi này. LEFT JOIN chứ
        # không INNER: người chưa tick phải hiện ra với status = null, đó mới là
        # việc cần làm của màn hình này.
        roster = q('''SELECT m.user_id, m.joined_at, u.name, u.email, u.phone,
                             a.status, a.minutes, a.note, a.marked_by, a.marked_at,
                             mb.name AS marked_by_name
                      FROM class_members m
                      JOIN users u ON u.id = m.user_id
                      LEFT JOIN attendance a
                             ON a.session_id = %s AND a.user_id = m.user_id
                      LEFT JOIN users mb ON mb.id = a.marked_by
                      WHERE m.class_id = %s AND m.left_at IS NULL
                        AND ''' + chi_hoc_vien('u') + '''
                      ORDER BY u.name, m.user_id''', (session_id, class_id))

        # Câu 2: chuyên cần luỹ kế trong CHÍNH lớp này, một câu cho cả lớp.
        # Bỏ buổi đã HUỶ: lớp nghỉ vì giảng viên ốm mà tính vào số buổi vắng của
        # học viên là đổ lỗi nhầm người, và con số đó lại đang dùng để gọi điện
        # cho phụ huynh.
        history = {r['user_id']: r for r in q(
            '''SELECT a.user_id,
                      COUNT(*)                                    AS marked,
                      COUNT(*) FILTER (WHERE a.status = 'absent')  AS absent,
                      COUNT(*) FILTER (WHERE a.status = 'late')    AS late,
                      COUNT(*) FILTER (WHERE a.status = 'excused') AS excused
               FROM attendance a
               JOIN class_sessions s ON s.id = a.session_id
               WHERE s.class_id = %s AND s.status <> 'cancelled'
               GROUP BY a.user_id''', (class_id,))}

        students, tally = [], {s: 0 for s in ATTENDANCE_STATUS}
        unmarked = 0
        for r in roster:
            h = history.get(r['user_id']) or {}
            if r['status'] in tally:
                tally[r['status']] += 1
            else:
                unmarked += 1
            students.append({
                'userId': r['user_id'],
                'name': r['name'] or r['email'],
                'email': r['email'],
                'phone': r['phone'],
                'status': r['status'],                 # None = chưa điểm danh
                'minutes': r['minutes'],
                'note': r['note'],
                'markedAt': r['marked_at'].isoformat() if r['marked_at'] else None,
                # marked_by NULL trên một dòng ĐÃ CÓ nghĩa là "máy điền" (xem
                # legacy_schema.sql §33) — để dành cho bộ nhập tự động sau này.
                'markedBy': r['marked_by'],
                'markedByName': r['marked_by_name'],
                'absentTotal': int(h.get('absent') or 0),
                'lateTotal': int(h.get('late') or 0),
                'excusedTotal': int(h.get('excused') or 0),
                'sessionsMarked': int(h.get('marked') or 0),
            })

        return Response({
            'session': _session_dict(row),
            'students': students,
            'summary': dict(tally, unmarked=unmarked, total=len(students)),
            'statuses': list(ATTENDANCE_STATUS),
            'labels': dict(ATTENDANCE_LABEL),
        })

    def post(self, request, session_id):
        row = self._load(request, session_id)
        if not row:
            return Response(_NOT_FOUND_SESSION, status=404)

        body = request.data if isinstance(request.data, dict) else {}
        marks = body.get('marks')
        if not isinstance(marks, list) or not marks:
            return Response({'error': 'Cần danh sách marks: '
                                      '[{"user_id": 12, "status": "present"}, ...].'},
                            status=400)

        # CÙNG bộ lọc với bảng tick ở trên: danh sách hiện ra và danh sách
        # chấp nhận được phải là MỘT. Lệch nhau thì có người hiện trên màn hình
        # mà gửi lên lại bị báo "không thuộc lớp này" — hoặc ngược lại, tick
        # được cho người không hề hiện ra.
        members = {r['user_id'] for r in q(
            'SELECT m.user_id FROM class_members m JOIN users u ON u.id = m.user_id '
            'WHERE m.class_id = %s AND m.left_at IS NULL AND ' + chi_hoc_vien('u'),
            (row['class_id'],))}

        clean, skipped = {}, []
        for m in marks:
            if not isinstance(m, dict):
                return Response({'error': 'Mỗi phần tử của marks phải là một đối tượng '
                                          '{user_id, status}.'}, status=400)
            try:
                uid = int(m.get('user_id'))
            except (TypeError, ValueError):
                return Response({'error': 'user_id phải là số.'}, status=400)
            status = str(m.get('status') or '').strip()
            if status not in ATTENDANCE_STATUS:
                return Response({'error': 'Trạng thái điểm danh phải là một trong: %s.'
                                          % ', '.join(ATTENDANCE_STATUS)}, status=400)
            if uid not in members:
                # KHÔNG ghi bừa id lạ: attendance không ràng buộc user phải thuộc
                # lớp, nên một id gõ nhầm sẽ nằm im trong bảng chuyên cần của lớp
                # khác và không màn hình nào hiện ra. Bỏ qua và BÁO LẠI, để người
                # gửi biết chứ không tưởng là đã lưu.
                skipped.append(uid)
                continue
            minutes = m.get('minutes')
            if minutes in ('', None):
                minutes = None
            else:
                try:
                    minutes = max(0, int(minutes))
                except (TypeError, ValueError):
                    return Response({'error': 'minutes phải là số phút nguyên.'},
                                    status=400)
            note = str(m.get('note') or '').strip()[:500] or None
            # Trùng user_id trong cùng một mẻ: giữ dòng CUỐI. Bắt buộc phải gộp
            # ở đây — Postgres ném "ON CONFLICT DO UPDATE command cannot affect
            # row a second time" nếu một câu INSERT chạm hai lần vào cùng một
            # khoá, tức là một cú double-click ở giao diện sẽ thành lỗi 500.
            clean[uid] = {'user_id': uid, 'status': status,
                          'minutes': minutes, 'note': note}

        if not clean:
            return Response({'error': 'Không có học viên hợp lệ nào trong danh sách '
                                      '(không ai trong số đó đang học lớp này).',
                             'skipped': skipped}, status=400)

        rows = list(clean.values())
        now = local_now()

        # Đọc trạng thái CŨ trước khi ghi đè. Đây là thứ nhật ký kiểm toán đang
        # thiếu: hôm nay nó chỉ nói "buổi X: 12 có mặt, 3 vắng", nên khi phụ
        # huynh khiếu nại "hôm đó cháu có đi học" thì không đối chiếu được ai đã
        # sửa trạng thái của em từ gì sang gì. openSIS giữ cả `attendance_code`
        # lẫn `attendance_teacher_code` chính vì tình huống này.
        truoc = {r['user_id']: r['status'] for r in
                 q('SELECT user_id, status FROM attendance WHERE session_id=%s', (session_id,))}

        params = []
        for m in rows:
            params += [session_id, m['user_id'], m['status'], m['minutes'], m['note'],
                       request.user.id, now]
        values = ', '.join(['(%s, %s, %s, %s, %s, %s, %s)'] * len(rows))

        with transaction.atomic():
            # MỘT câu cho cả lớp: 30 câu UPSERT riêng là 30 lượt Neon ≈ 7 giây
            # cho một lần bấm Lưu.
            #
            # UPSERT chứ không INSERT: điểm danh lại là SỬA. Tick nhầm rồi tick
            # lại phải đè lên dòng cũ, không đẻ dòng thứ hai (khoá chính
            # (session_id, user_id) cũng không cho đẻ).
            #
            # `minutes`/`note` dùng COALESCE chứ không đè thẳng: khi có API lấy
            # danh sách người tham dự, máy sẽ điền số phút đo được; giảng viên
            # sau đó sửa tay một trạng thái mà gửi thiếu `minutes` thì đè thẳng
            # sẽ XOÁ số đo ấy đi, không lấy lại được. Cùng lý do với COALESCE ở
            # common/events.py. Muốn xoá thật thì gửi minutes = 0.
            x('INSERT INTO attendance '
              '(session_id, user_id, status, minutes, note, marked_by, marked_at) '
              'VALUES ' + values +
              ' ON CONFLICT (session_id, user_id) DO UPDATE SET '
              '  status    = EXCLUDED.status,'
              '  minutes   = COALESCE(EXCLUDED.minutes, attendance.minutes),'
              '  note      = COALESCE(EXCLUDED.note, attendance.note),'
              '  marked_by = EXCLUDED.marked_by,'
              '  marked_at = EXCLUDED.marked_at', tuple(params))

            # Đóng dấu "buổi này ĐÃ được điểm danh". Không có hai cột này thì
            # "buổi X không có dòng attendance nào" mơ hồ giữa hai chuyện khác
            # hẳn nhau — cả lớp có mặt hết, hay giảng viên quên tick — nên không
            # dựng nổi báo cáo "tối nay ai chưa điểm danh", thứ trung tâm cần
            # mỗi ngày. Nằm trong cùng khối atomic với câu ghi ở trên là bắt
            # buộc: đóng dấu mà dòng điểm danh không vào được thì con dấu nói dối.
            x('UPDATE class_sessions SET attendance_taken_at=%s, attendance_taken_by=%s, '
              'updated_at=%s WHERE id=%s', (now, request.user.id, now, session_id))

        # Sự kiện học tập nằm NGOÀI khối atomic ở trên, có chủ đích. record_event
        # tự bọc savepoint và không bao giờ ném lỗi, nhưng common/db.py từ chối
        # thử lại mọi câu chạy TRONG một atomic block (để không phá tính nguyên
        # tử). Gộp cả vòng lặp vào trong khối đó nghĩa là một cú rớt kết nối
        # Neon giữa chừng sẽ cuộn lại CẢ mẻ điểm danh vừa lưu — mất công tick
        # của giảng viên để đổi lấy một bảng thống kê. Ưu tiên ngược lại: dòng
        # điểm danh đã chốt, sự kiện là việc ghi thêm.
        so_su_kien = self._emit_events(row, rows)

        counts = {}
        for m in rows:
            counts[m['status']] = counts.get(m['status'], 0) + 1
        parts = ', '.join('%d %s' % (counts[s], ATTENDANCE_LABEL[s])
                          for s in ATTENDANCE_STATUS if counts.get(s))
        label = row['topic'] or row['starts_at'].strftime('%d/%m/%Y %H:%M')
        summary = 'Điểm danh buổi %s lớp %s: %s' % (label, row['class_name'], parts)

        # MỘT dòng nhật ký cho CẢ MẺ. Mỗi học viên một dòng thì một lớp 30 em là
        # 30 dòng cho một thao tác, và nhật ký kiểm toán ngập tới mức không ai
        # đọc nữa — tức là mất tác dụng đúng lúc cần dùng.
        #
        # `changed` chỉ chép những em THẬT SỰ đổi trạng thái, kèm giá trị cũ.
        # Chép cả mẻ thì một lần bấm "đánh dấu cả lớp có mặt" đẻ ra 30 dòng
        # không có tin tức gì, và phần đáng đọc chìm nghỉm. Ai sửa và sửa lúc
        # nào thì `audit.record` đã tự ghi.
        changed = [{'userId': m['user_id'], 'from': truoc.get(m['user_id']),
                    'to': m['status']}
                   for m in rows if truoc.get(m['user_id']) != m['status']]
        record(request, ATTENDANCE_MARK,
               target_type='class_session', target_id=session_id,
               target_label=label, summary=summary,
               detail={'class_id': row['class_id'], 'counts': counts,
                       'marked': len(rows), 'skipped': skipped,
                       'firstTime': not truoc, 'changed': changed})

        return Response({
            'ok': True,
            'marked': len(rows),
            'counts': counts,
            'summary': summary,
            # Báo lại id bị bỏ qua để giao diện nói được "3 em không thuộc lớp
            # này nên chưa lưu", thay vì im lặng báo thành công.
            'skipped': skipped,
            # Số sự kiện học tập ghi được. Bằng `marked` là đủ; ít hơn nghĩa là
            # dòng điểm danh ĐÃ lưu nhưng đường cong tiến bộ thiếu — bên gọi cần
            # biết để nói ra, thay vì báo "đã lưu" trơn.
            'events': so_su_kien,
        })

    @staticmethod
    def _emit_events(session, marks):
        """Mỗi dòng điểm danh đẻ một ``learning_events`` (đặc tả ERP §4).

        Nhờ vậy số buổi đi học vào thẳng đường cong tiến bộ và cảnh báo sớm mà
        không phải viết lại phép tính nào — cùng ý tưởng Completion API đã dùng
        cho bài học và thi thử (xem đầu common/events.py).

        Hai mốc thời gian cố ý lấy theo BUỔI HỌC chứ không theo lúc bấm nút:
        ``occurred_at`` = giờ bắt đầu buổi, ``event_date`` = ngày của buổi. Giảng
        viên thường tick bù hôm sau; lấy ngày tick thì buổi tối thứ Sáu rơi vào
        thống kê thứ Bảy, chuỗi ngày và biểu đồ tuần đều lệch.

        CỐ Ý ĐỂ ``minutes=None``, KỂ CẢ KHI DÒNG ĐIỂM DANH CÓ SỐ PHÚT.
        stats/journal.py đang cộng ``sys_min + self_min`` để ra chỉ tiêu tuần
        (journal.py:343), và việc có nên tính phút ngồi lớp vào chỉ tiêu tự học
        hay không LÀ MỘT QUYẾT ĐỊNH SẢN PHẨM CÒN ĐANG MỞ với chủ sản phẩm. Đổ
        phút điểm danh vào cột đó bây giờ là âm thầm thổi phồng một chỉ số đang
        tranh luận, mà không dấu vết nào cho thấy nó đã bị trộn. Số phút vẫn
        được giữ nguyên trong ``meta``: chuyển sang cột ``minutes`` sau này là
        MỘT câu UPDATE, còn gỡ số liệu đã trộn ra thì không gỡ được.
        """
        when = session['starts_at']
        # MỘT câu cho cả lớp, cùng lý do với câu UPSERT ở trên: vòng lặp
        # record_event tốn ba lượt gọi Neon mỗi em (SAVEPOINT / INSERT /
        # RELEASE) — đo 31/08/2026, 3 em = 9 lượt, tức lớp 30 em là 90 lượt cho
        # một lần bấm Lưu, trong khi giảng viên đang đứng chờ trước cả lớp.
        return record_events([{
            'uid': m['user_id'], 'kind': KIND_ATTENDANCE,
            # dedup_key đã duy nhất theo từng học viên (UNIQUE
            # (user_id, dedup_key)), nên khoá theo buổi là đủ — và nhờ vậy
            # điểm danh lại chỉ CẬP NHẬT đúng dòng cũ.
            'dedup_key': f'attendance:{session["id"]}',
            'occurred_at': when,
            'event_date': when.date() if when else None,
            'course_id': session['class_course_id'],
            'topic': session['topic'],
            'ref_type': 'class_session', 'ref_id': session['id'],
            'minutes': None,                        # xem docstring — cố ý
            'xp': 0, 'source': SOURCE_SYSTEM,
            'meta': {'attendance': m['status'], 'minutes': m['minutes'],
                     'class_id': session['class_id']},
        } for m in marks])

