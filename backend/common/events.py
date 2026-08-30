"""Dòng sự kiện học tập — nơi DUY NHẤT ghi vào ``learning_events``.

Ý tưởng mượn từ Completion API của Moodle: hoạt động (bài học, thi thử, quiz ôn
tập, nhiệm vụ, tự ghi nhận) chỉ việc BÁO CÁO một sự kiện; còn sổ điểm, bản đồ
năng lực, đường cong tiến bộ và kế hoạch học chỉ là những cách ĐỌC khác nhau
trên cùng một bảng. Nhờ vậy thêm một loại hoạt động mới không phải sửa mọi màn
hình hiển thị.

AN TOÀN — đọc kỹ trước khi sửa: ghi sự kiện là việc ĐỌC THÊM, không có tính năng
nào đang phụ thuộc vào nó. Vì thế mọi lời gọi ở đây được bọc trong một savepoint
riêng: bảng chưa tồn tại (mã lên trước khi chạy bootstrap_schema), cột đổi kiểu,
JSON hỏng… đều KHÔNG được phép kéo đổ giao dịch của bên gọi. Học viên học xong
một bài mà mất tiến độ chỉ vì bảng thống kê lỗi là cái giá không đáng.

``dedup_key`` là bắt buộc: nó khiến lệnh nạp dữ liệu cũ chạy lại nhiều lần vẫn
ra đúng một dòng, và học lại một bài thì CẬP NHẬT dòng cũ thay vì đẻ thêm dòng
mới (khớp với lesson_progress — bảng đó cũng chỉ giữ một dòng mỗi cặp
học viên–bài).
"""
import json
import logging

from django.db import DatabaseError, transaction

from common.clock import local_now
from common.db import x

logger = logging.getLogger(__name__)

#: Từ vựng `kind`. Mỗi giá trị mang đúng một nghĩa, xem chú thích ở
#: sql/legacy_schema.sql §26 để biết vì sao `mock` và `mock_section` tách đôi.
KIND_LESSON = 'lesson'
KIND_DRILL = 'drill'
KIND_REVIEW_QUIZ = 'review_quiz'
KIND_MOCK = 'mock'
KIND_MOCK_SECTION = 'mock_section'
KIND_MISSION = 'mission'
KIND_SELF_LOG = 'self_log'
#: Điểm danh buổi học (30/08/2026). KHÔNG nằm trong GRADED_KINDS: có mặt ở lớp
#: không phải bằng chứng năng lực, và trộn nó vào phép tính thành thạo sẽ khiến
#: một em chăm đi học nhưng chưa làm bài trông như đã nắm chủ đề.
KIND_ATTENDANCE = 'attendance'

#: Sự kiện có chấm điểm — nguồn của mọi phép tính năng lực.
GRADED_KINDS = (KIND_LESSON, KIND_DRILL, KIND_REVIEW_QUIZ, KIND_MOCK, KIND_MOCK_SECTION)

SOURCE_SYSTEM = 'system'
SOURCE_SELF = 'self'


def forget_events(ref_type=None, ref_id=None, *, user_id=None, dedup_key=None):
    """Xoá các sự kiện sinh ra từ một đối tượng đã bị xoá. Trả số dòng đã xoá.

    Đối xứng với ``record_event``: module này là cửa duy nhất GHI vào
    ``learning_events``, nên nó cũng phải là cửa duy nhất XOÁ. Thiếu hàm này thì
    nơi cần dọn sẽ tự viết một câu DELETE riêng, và kỷ luật một-cửa — thứ khiến
    bảng ấy còn tin được — mất ngay từ chỗ đó.

    Dùng khi xoá một buổi học: các sự kiện ``kind='attendance'`` trỏ tới buổi đó
    không còn đối tượng để trỏ về. Chúng vô hại về số liệu (score và minutes đều
    NULL nên không lọt vào năng lực hay sổ điểm) nhưng vẫn tính vào "hoạt động
    gần nhất" — tức một buổi đã xoá vẫn làm học viên trông như còn đang học.

    CỐ Ý HẸP: chỉ nhận hai dạng khoá xác định — cặp ``ref_type``/``ref_id``, hoặc
    cặp ``user_id``/``dedup_key``. KHÔNG nhận điều kiện tự do. Một hàm xoá theo
    điều kiện tuỳ ý đặt ở đây sớm muộn cũng bị dùng để "dọn dẹp" và cuốn theo dữ
    liệu học tập thật, thứ không có đường khôi phục.

    Dạng thứ hai (``user_id`` + ``dedup_key``) thêm ngày 30/08/2026 để kéo nốt
    câu DELETE cuối cùng còn nằm ngoài mô-đun này về đây (``stats/journal.py``
    xoá nhật ký tự ghi). Trước đó nó tự dựng lại chuỗi ``dedup_key``, tức luật
    đặt tên khoá nằm ở HAI nơi — đổi tiền tố ở chỗ ghi mà quên chỗ xoá thì việc
    xoá sẽ im lặng không xoá gì, và dòng sự kiện tự khai sống mãi cho một bản
    ghi đã bị xoá.
    """
    from common.db import q
    if ref_type and ref_id is not None:
        # ``ref_id`` nhận cả MỘT id lẫn một danh sách id cùng ``ref_type``.
        # Dạng danh sách thêm 31/08/2026 cho đường xoá lớp: xoá một lớp là xoá
        # theo tất cả buổi học của nó, và gọi hàm này trong vòng lặp thì một lớp
        # đã dạy hai tháng là vài chục lượt tới Neon ngay giữa một request.
        # Vẫn HẸP đúng như đoạn trên: một loại đối tượng, một danh sách id xác
        # định, không có điều kiện tự do nào lọt vào.
        if isinstance(ref_id, (list, tuple, set)):
            if not ref_id:
                return 0
            sql = ('DELETE FROM learning_events WHERE ref_type=%s AND ref_id = ANY(%s) '
                   'RETURNING id')
            args = (ref_type, [str(i) for i in ref_id])
        else:
            sql = 'DELETE FROM learning_events WHERE ref_type=%s AND ref_id=%s RETURNING id'
            args = (ref_type, str(ref_id))
    elif user_id is not None and dedup_key:
        sql = 'DELETE FROM learning_events WHERE user_id=%s AND dedup_key=%s RETURNING id'
        args = (user_id, dedup_key)
    else:
        return 0
    try:
        with transaction.atomic():
            rows = q(sql, args)
        return len(rows)
    except DatabaseError as exc:
        logger.error('[events] KHÔNG xoá được sự kiện (%s/%s, user=%s, key=%s): %s',
                     ref_type, ref_id, user_id, dedup_key, exc)
        return 0


# ── Câu INSERT dùng chung cho cả ghi lẻ lẫn ghi mẻ ─────────────────────────
#
# Tách ra hằng số để câu lệnh chỉ tồn tại MỘT bản. Nếu ghi lẻ và ghi mẻ mỗi bên
# giữ một bản chép, chỉ cần bản mẻ thiếu một COALESCE là ghi lẻ giữ được điểm cũ
# còn ghi mẻ xoá mất — hai đường ghi cùng một bảng cho hai kết quả khác nhau, và
# không phép kiểm nào bắt được vì cả hai đều "chạy được".
_COLS = ('user_id, dedup_key, occurred_at, event_date, kind, course_id, topic, '
         'ref_type, ref_id, score, max_score, minutes, xp, source, meta')

_ROW = '(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)'

_ON_CONFLICT = '''ON CONFLICT (user_id, dedup_key) DO UPDATE SET
        occurred_at = EXCLUDED.occurred_at,
        event_date  = EXCLUDED.event_date,
        course_id   = EXCLUDED.course_id,
        topic       = EXCLUDED.topic,
        -- COALESCE chứ không ghi đè thẳng: học lại một bài mà lần này không làm
        -- quiz sẽ gửi score = NULL, và ghi đè thẳng thì XOÁ MẤT điểm đã đo được
        -- lần trước — ô năng lực tụt về "chưa đủ dữ liệu", sổ điểm mất dòng,
        -- đường cong mất điểm, không có đường khôi phục. Cùng lý do với COALESCE
        -- của `minutes` và GREATEST của `xp` ngay dưới. Có điểm mới thì vẫn ghi
        -- đè như cũ.
        score       = COALESCE(EXCLUDED.score, learning_events.score),
        max_score   = COALESCE(EXCLUDED.max_score, learning_events.max_score),
        minutes     = COALESCE(EXCLUDED.minutes, learning_events.minutes),
        xp          = GREATEST(EXCLUDED.xp, learning_events.xp),
        meta        = EXCLUDED.meta'''

#: Số dòng tối đa trong một câu INSERT. Postgres chặn ở 65535 tham số cho mỗi
#: câu lệnh, mà mỗi dòng ở đây chiếm 15 tham số → trần cứng là 4369 dòng. Lấy
#: 500 để còn xa ngưỡng đó, và để một câu lệnh không phình tới mức khó đọc khi
#: nó xuất hiện trong log lỗi.
_CHUNK = 500


def _params(uid, kind, dedup_key, when, day, course_id, topic, ref_type, ref_id,
            score, max_score, minutes, xp, source, meta):
    """Xếp tham số đúng thứ tự ``_COLS``. Đây là chỗ DUY NHẤT biết thứ tự đó."""
    return (uid, dedup_key, when, day, kind, course_id, topic, ref_type, ref_id,
            score, max_score, minutes, xp or 0, source,
            json.dumps(meta, ensure_ascii=False) if meta is not None else None)


def _write(rows):
    """Ghi ``rows`` (danh sách tuple từ ``_params``) bằng MỘT câu INSERT.

    Ném lỗi ra ngoài — bên gọi tự bọc savepoint và tự nuốt, xem phần AN TOÀN ở
    đầu module.
    """
    x('INSERT INTO learning_events (' + _COLS + ') VALUES '
      + ', '.join([_ROW] * len(rows)) + ' ' + _ON_CONFLICT,
      tuple(v for r in rows for v in r))


def record_event(uid, kind, dedup_key, *, occurred_at=None, event_date=None, course_id=None,
                 topic=None, ref_type=None, ref_id=None, score=None, max_score=None,
                 minutes=None, xp=0, source=SOURCE_SYSTEM, meta=None):
    """Ghi (hoặc cập nhật) một sự kiện học tập. Trả về True nếu ghi được.

    Không bao giờ ném lỗi ra ngoài: xem phần AN TOÀN ở đầu module.

    ``event_date`` mặc định là ngày của ``occurred_at``, nhưng cho phép truyền
    riêng: dữ liệu cũ có mốc giờ ghi bằng ``now()`` của Postgres (tức UTC) trong
    khi ngày nghiệp vụ đã tính theo giờ Việt Nam — hai thứ lệch nhau đúng một
    ngày trong khung 0h–7h sáng. Chỗ nào biết chắc ngày nghiệp vụ thì đưa vào
    đây thay vì để suy lại từ mốc giờ sai.

    Ghi NHIỀU sự kiện một lúc thì dùng ``record_events`` — vòng lặp gọi hàm này
    tốn ba lượt gọi CSDL cho mỗi sự kiện (đo 30/08/2026: 3 học viên = 9 lượt).
    """
    when = occurred_at or local_now()
    day = event_date or when.date()
    try:
        # Savepoint riêng: hỏng ở đây thì chỉ cuộn lại đúng câu INSERT này,
        # giao dịch của bên gọi (ghi tiến độ, cộng XP, chuỗi ngày) đi tiếp.
        with transaction.atomic():
            _write([_params(uid, kind, dedup_key, when, day, course_id, topic,
                            ref_type, ref_id, score, max_score, minutes, xp,
                            source, meta)])
        return True
    except DatabaseError as exc:
        # Điển hình: bảng chưa tồn tại vì mã lên trước bootstrap_schema.
        logger.warning('learning_events: bỏ qua sự kiện %s/%s — %s', kind, dedup_key, exc)
        return False
    except Exception as exc:                                  # noqa: BLE001
        logger.warning('learning_events: lỗi không lường trước ở %s — %s', dedup_key, exc)
        return False


def record_events(events):
    """Ghi MỘT MẺ sự kiện. Trả về số dòng đã ghi.

    Mỗi phần tử là một dict nhận đúng các tham số của ``record_event``
    (``uid``, ``kind``, ``dedup_key`` bắt buộc; phần còn lại tuỳ chọn).

    VÌ SAO CÓ HÀM NÀY: gọi ``record_event`` trong vòng lặp tốn ba lượt gọi CSDL
    cho mỗi sự kiện — SAVEPOINT, INSERT, RELEASE — vì mỗi lời gọi tự mở một
    savepoint riêng. Đo được ngày 31/08/2026 trên đường điểm danh: 3 học viên =
    9 lượt. Một lớp 30 em là 90 lượt cho một lần bấm Lưu, mà giảng viên đang
    đứng chờ trước mặt cả lớp.

    TRÙNG TRONG CÙNG MẺ được gộp, giữ dòng CUỐI. Bắt buộc phải gộp: Postgres ném
    "ON CONFLICT DO UPDATE command cannot affect row a second time" nếu một câu
    INSERT chạm hai lần vào cùng một khoá ``(user_id, dedup_key)`` — tức một
    danh sách gửi lên có id lặp sẽ thành lỗi 500 thay vì ghi được. Cùng cái bẫy
    đã gặp ở đường lưu điểm danh (teaching/sessions.py).

    ĐÁNH ĐỔI ĐÃ NHẬN: một câu INSERT thì một dòng hỏng làm hỏng cả mẻ, trong khi
    vòng lặp cũ chỉ mất đúng dòng đó. Nên khi mẻ hỏng, hàm này QUAY VỀ ghi lẻ
    từng dòng — chậm, nhưng chỉ chậm trên đường lỗi, và giữ đúng tính chất cũ là
    một sự kiện hỏng không kéo theo những sự kiện còn lại.
    """
    # Giữ CẢ tham số lẫn dict gốc, cùng một thứ tự: nhánh dự phòng ở dưới cần
    # gọi lại record_event trên đúng những dòng của mẻ vừa hỏng, mà sau khi gộp
    # trùng thì chỉ số không còn khớp với `events` ban đầu nữa.
    gom = {}
    for e in events:
        when = e.get('occurred_at') or local_now()
        day = e.get('event_date') or when.date()
        gom[(e['uid'], e['dedup_key'])] = (_params(
            e['uid'], e['kind'], e['dedup_key'], when, day,
            e.get('course_id'), e.get('topic'), e.get('ref_type'), e.get('ref_id'),
            e.get('score'), e.get('max_score'), e.get('minutes'), e.get('xp', 0),
            e.get('source', SOURCE_SYSTEM), e.get('meta')), e)

    rows = [p for p, _ in gom.values()]
    goc = [e for _, e in gom.values()]
    da_ghi = 0
    for i in range(0, len(rows), _CHUNK):
        me = rows[i:i + _CHUNK]
        try:
            with transaction.atomic():
                _write(me)
            da_ghi += len(me)
        except Exception as exc:                              # noqa: BLE001
            logger.warning('learning_events: mẻ %d dòng hỏng, ghi lẻ từng dòng — %s',
                           len(me), exc)
            for e in goc[i:i + _CHUNK]:
                if record_event(e['uid'], e['kind'], e['dedup_key'],
                                **{k: v for k, v in e.items()
                                   if k not in ('uid', 'kind', 'dedup_key')}):
                    da_ghi += 1
    return da_ghi


def pct(score, max_score):
    """Quy về phần trăm 0–100. Không tính được → None (KHÔNG trả 0: "chưa có dữ
    liệu" và "làm sai hết" là hai chuyện khác nhau)."""
    try:
        score, max_score = float(score), float(max_score)
    except (TypeError, ValueError):
        return None
    if max_score <= 0:
        return None
    return max(0.0, min(100.0, score * 100.0 / max_score))
