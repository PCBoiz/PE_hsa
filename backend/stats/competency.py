"""Bản đồ năng lực theo chủ đề — biến số liệu thành lời khuyên cụ thể.

Cả 76 bài HSA đã được gắn chương mục (``lessons.module``) từ lâu: Số học, Hình
học, Đọc hiểu, Vật lý… nhưng chưa lần nào dùng để chấm mạnh–yếu. Đây là thứ
biến "bạn được 62%" thành "Hình học 45% — yếu nhất, ôn tiếp Bài 12".

KHOÁ LÀ CẶP (khoá học, chủ đề), KHÔNG phải mỗi tên chủ đề. "Chiến thuật" là
chủ đề của cả ba hợp phần; gộp theo tên thôi thì chiến thuật làm bài Định lượng
và chiến thuật Khoa học dồn vào một ô, số liệu vô nghĩa. 20 ô = 8 Định lượng +
6 Định tính + 6 Khoa học.

BỐN NGUYÊN TẮC (rút từ đặc tả 19/08, giữ đúng cả bốn):

1. Bốn nguồn, mỗi nguồn đo một thứ khác nhau, gộp theo trọng số:
   kiểm tra đầu vào 30% (nền sẵn có) · phòng luyện 20% (tốc độ) ·
   quiz ôn tập 25% (nhớ lâu) · thi thử 25% (trong điều kiện thi).
2. Thiếu nguồn nào thì CHIA LẠI trọng số cho các nguồn còn lại — không coi
   nguồn chưa có là điểm 0.
3. Điểm gần đây nặng hơn điểm cũ. Người học tiến bộ thì con số phải phản ánh
   hiện tại, không bị bài làm sai từ tháng trước kéo xuống mãi.
4. Chưa đủ dữ liệu thì NÓI LÀ CHƯA ĐỦ. Một con số dựng từ đúng một bài không
   phải là phép đo; hiện nó ra còn tệ hơn để trống.
"""
from django.db import DatabaseError

from common.clock import local_today
from common.db import q
from common.events import (KIND_ASSIGNMENT, KIND_DRILL, KIND_LESSON, KIND_MOCK_SECTION,
                           KIND_REVIEW_QUIZ)

#: Trọng số bốn nguồn. Tổng bằng 1 khi có đủ; thiếu thì chuẩn hoá lại.
SOURCE_WEIGHTS = {
    'test': 0.30,
    'drill': 0.20,
    'review_quiz': 0.25,
    'mock': 0.25,
    # Bài tập chấm tay (31/08/2026). Trọng số cao nhất cùng `test`, và đây là
    # một GIẢ ĐỊNH SẢN PHẨM nên để lộ ra: đó là nguồn duy nhất có một con người
    # đọc bài rồi mới cho điểm, nên nó nói về hiểu biết thật nhiều hơn mọi
    # nguồn chấm máy. Phần Định tính của HSA gần như chỉ đo được bằng cách này.
    #
    # THÊM MỘT NGUỒN KHÔNG LÀM XÊ DỊCH CON SỐ CỦA AI. `compute` chuẩn hoá theo
    # tổng trọng số của những nguồn CÓ dữ liệu (`if mean is None: continue`),
    # nên em nào chưa có bài chấm nào thì mẫu số không đổi. Đã kiểm.
    'assignment': 0.30,
}
#: kind của sự kiện → nguồn tương ứng.
KIND_TO_SOURCE = {
    KIND_LESSON: 'test',
    KIND_DRILL: 'drill',
    KIND_REVIEW_QUIZ: 'review_quiz',
    KIND_MOCK_SECTION: 'mock',
    KIND_ASSIGNMENT: 'assignment',
}
#: Nguồn gắn với ĐÚNG một chủ đề. `mock` không nằm ở đây: đề thi thử chỉ chia
#: theo hợp phần, không biết câu nào thuộc chủ đề nào, nên nó là bối cảnh cấp
#: khoá — dùng để chấm nhưng KHÔNG được tính là bằng chứng về chủ đề.
TOPIC_SOURCES = ('test', 'drill', 'review_quiz', 'assignment')

#: Sau ngần này ngày, một kết quả chỉ còn nặng một nửa.
#:
#: BA ĐIỀU PHẢI NÓI RA, vì gộp chúng lại chính là cách con số 45 sống sót suốt
#: mấy tháng mà không ai hỏi (N2, 01/09/2026):
#:
#: 1. **Chưa được kiểm chứng.** 45 không đến từ dữ liệu của pe_hsa, không đến từ
#:    một bài báo nào, và chưa lần nào được đối chiếu với kết quả thật. Nó là
#:    một con số ai đó gõ ra. Muốn kiểm: lấy các cặp (điểm dự đoán hôm nay, điểm
#:    thật ở lần làm tiếp theo) rồi tìm chu kỳ bán rã làm sai số nhỏ nhất. Chưa
#:    đủ dữ liệu để làm việc đó — xem N1, ngưỡng 100 học viên.
#: 2. **Nó KHÔNG vô hại.** Đo 31/08/2026 trên một học viên thật: đổi 45 thành 30
#:    hay 90 làm ô thành thạo xê dịch tới **11 điểm phần trăm**. Ngưỡng xếp lịch
#:    ôn là 60, nên 11 điểm đủ để một chủ đề nhảy qua nhảy lại ranh giới "cần ôn"
#:    — tức con số chưa kiểm chứng này đang QUYẾT ĐỊNH lịch học của người ta.
#: 3. **Nó là trọng số theo ĐỘ MỚI CỦA BẰNG CHỨNG, không phải mô hình quên.**
#:    Nó không nói "em quên mất một nửa sau 45 ngày". Nó nói "bài kiểm tra cách
#:    đây 45 ngày chỉ đáng tin bằng nửa bài hôm nay để đoán trình độ HIỆN TẠI".
#:    Hai mệnh đề đó khác nhau: một cái về người học, một cái về bằng chứng.
#:    Nếu ngày nào muốn mô hình quên thật thì đó là việc khác (FSRS/SM-2), có
#:    tham số riêng, và KHÔNG dùng lại con số này.
HALF_LIFE_DAYS = 45
#: Số HOẠT ĐỘNG khác nhau tối thiểu để dám hiện một con số thành thạo.
#: Đúng một bài học sinh ra 2 sự kiện (kiểm tra + phòng luyện) nhưng vẫn chỉ là
#: một lần chạm vào chủ đề — nên đếm theo hoạt động, không đếm theo sự kiện.
MIN_ACTIVITIES = 2
#: Dưới mức này mà học viên tự đánh dấu "đã nắm" thì hệ thống nói thẳng.
SELF_MARK_CONFLICT_BELOW = 50

#: Thứ tự hiển thị ba hợp phần.
COURSE_ORDER = ('hsa_quantitative', 'hsa_verbal', 'hsa_science')


def _decayed_mean(items, today):
    """Trung bình phần trăm có suy giảm theo thời gian.

    ``items`` là list (phần_trăm, ngày). Kết quả hôm nay nặng 1.0, kết quả cách
    đây một chu kỳ bán rã nặng 0.5, cứ thế.
    """
    num = den = 0.0
    for value, when in items:
        age = (today - when).days if when else 0
        weight = 0.5 ** (max(0, age) / HALF_LIFE_DAYS)
        num += weight * value
        den += weight
    return (num / den) if den else None


#: Câu hỏi danh mục. Tách ra để chạy được cả bản CÓ và KHÔNG có
#: topic_self_marks — bảng đó có thể chưa tồn tại nếu mã lên trước bootstrap_schema,
#: và mất bản đồ năng lực chỉ vì thiếu một cờ tuỳ chọn là cái giá vô lý.
_CATALOG_SQL = """SELECT l.course_id, l.module AS topic, l.sort_order, l.title,
                         c.title AS course_title,
                         (lp.user_id IS NOT NULL) AS done%s
                  FROM lessons l
                  LEFT JOIN courses c ON c.id = l.course_id
                  LEFT JOIN lesson_progress lp
                         ON lp.lesson_id = l.id AND lp.user_id = %%s
                        AND lp.status = 'completed'%s
                  WHERE l.course_id IS NOT NULL
                    AND l.module IS NOT NULL AND l.module <> ''
                  ORDER BY l.course_id, l.sort_order"""

_SELF_COL = ", sm.known AS self_known"
_SELF_JOIN = """
                  LEFT JOIN topic_self_marks sm
                         ON sm.user_id = %s AND sm.course_id = l.course_id
                        AND sm.topic = l.module"""


def _catalog_rows(uid, with_self_marks=True):
    if with_self_marks:
        try:
            return q(_CATALOG_SQL % (_SELF_COL, _SELF_JOIN), (uid, uid))
        except DatabaseError:
            pass
    return q(_CATALOG_SQL % ('', ''), (uid,))


def _catalog(uid):
    """Danh mục (khoá, chủ đề) kèm số bài đã xong, bài kế tiếp, tên khoá và cờ
    học viên tự đánh dấu đã nắm.

    Đọc thẳng từ ``lessons`` chứ không cứng hoá danh sách chủ đề: giáo trình sẽ
    được soạn lại theo TopHSA, lúc đó bản đồ tự đổi theo mà không phải sửa mã.

    Tên khoá và cờ tự đánh dấu ĐƯỢC JOIN VÀO ĐÂY thay vì hỏi riêng hai lượt: mỗi
    lượt truy vấn tới Neon tốn ~245ms thuần đường truyền, nên gộp được câu nào là
    cắt thẳng ngần ấy khỏi thời gian chờ của người dùng (đo 24/08: 4 lượt = 0,98s
    → 2 lượt = 0,49s).
    """
    rows = _catalog_rows(uid)
    cells = {}
    for r in rows:
        key = (r['course_id'], r['topic'])
        cell = cells.setdefault(key, {
            'total': 0, 'done': 0, 'next': None,
            'courseTitle': r['course_title'] or r['course_id'],
            'known': bool(r.get('self_known')),
        })
        cell['total'] += 1
        if r['done']:
            cell['done'] += 1
        elif cell['next'] is None:
            cell['next'] = {'lessonIndex': r['sort_order'], 'title': r['title'] or ''}
    return cells


def _events(uid):
    """Sự kiện có chấm điểm, gom sẵn theo (khoá, chủ đề) và theo khoá.

    Bảng chưa tồn tại (mã lên trước khi chạy bootstrap_schema) thì trả rỗng: bản
    đồ hiện "chưa đủ dữ liệu" — đúng sự thật — thay vì làm hỏng cả Trang của tôi.
    """
    try:
        # `occurred_at` chứ KHÔNG `event_date`: phép suy giảm hỏi "kết quả này
        # ĐO ĐƯỢC bao lâu rồi", mà từ 31/08/2026 `event_date` giữ NGÀY ĐẦU. Em
        # ôn lại một bài từ hai tháng trước thì bằng chứng là của HÔM NAY, không
        # phải của hai tháng trước — dùng nhầm cột là đánh tụt trọng số của đúng
        # phần em vừa ôn.
        rows = q('''SELECT kind, course_id, topic, score, max_score,
                           occurred_at::date AS event_date,
                           ref_type, ref_id
                    FROM learning_events
                    WHERE user_id = %s AND kind = ANY(%s)
                      AND max_score IS NOT NULL AND max_score > 0''',
                 (uid, list(KIND_TO_SOURCE)))
    except DatabaseError:
        return {}, {}
    by_cell, by_course = {}, {}
    for r in rows:
        source = KIND_TO_SOURCE.get(r['kind'])
        if not source:
            continue
        try:
            value = max(0.0, min(100.0, float(r['score'] or 0) * 100.0 / float(r['max_score'])))
        except (TypeError, ValueError, ZeroDivisionError):
            continue
        item = (value, r['event_date'], (r['ref_type'], r['ref_id']))
        if source == 'mock':
            by_course.setdefault(r['course_id'], []).append(item)
        elif r['topic']:
            by_cell.setdefault((r['course_id'], r['topic']), {}) \
                   .setdefault(source, []).append(item)
    return by_cell, by_course


def _mastery(sources, today, chi_chu_de=False):
    """Gộp các nguồn có dữ liệu thành một điểm 0–100, chuẩn hoá lại trọng số.

    ``chi_chu_de=True`` thì BỎ QUA nguồn không gắn với chủ đề (hiện chỉ có điểm
    thi thử). Xem `compute` để biết vì sao cần cả hai con số.
    """
    parts, weight_sum = 0.0, 0.0
    detail = {}
    for name, items in sources.items():
        if chi_chu_de and name not in TOPIC_SOURCES:
            continue
        mean = _decayed_mean([(v, d) for v, d, _ in items], today)
        if mean is None:
            continue
        weight = SOURCE_WEIGHTS.get(name, 0)
        parts += weight * mean
        weight_sum += weight
        detail[name] = {'pct': round(mean), 'n': len(items)}
    if not weight_sum:
        return None, detail
    return round(parts / weight_sum), detail


def compute(uid):
    """Bản đồ năng lực đầy đủ của một học viên."""
    today = local_today()
    cells = _catalog(uid)
    by_cell, by_course = _events(uid)

    topics = []
    for (course_id, topic), cell in cells.items():
        sources = dict(by_cell.get((course_id, topic), {}))
        mock_items = by_course.get(course_id)
        if mock_items:
            sources['mock'] = mock_items

        # Đếm theo HOẠT ĐỘNG, và chỉ đếm nguồn gắn với chủ đề — điểm thi thử là
        # bối cảnh cấp khoá, không phải bằng chứng chủ đề.
        #
        # Khoá là CẶP `(ref_type, ref_id)`, không phải `ref_id` trần. Mỗi loại
        # tham chiếu có KHÔNG GIAN ID RIÊNG: bài học #2 và quiz ôn tập #2 là hai
        # hoạt động khác nhau, chỉ trùng số thứ tự trong CSDL. Đo 31/08/2026
        # trên dữ liệu thật: em id 9 có `ref_id='2'` cho cả `lesson` lẫn `quiz`,
        # và cặp ấy bị đếm thành MỘT — đủ để một ô chủ đề tụt xuống dưới ngưỡng
        # `MIN_ACTIVITIES` và hiện "chưa đủ dữ liệu" thay vì một con số có thật.
        #
        # Cặp này vẫn giữ đúng chỗ CỐ Ý gộp: sự kiện `lesson` và `drill` của
        # cùng một bài dùng chung `ref_type='lesson'` VÀ chung `ref_id`, nên
        # chúng vẫn là một lần chạm vào chủ đề, đúng như chú thích ở
        # `MIN_ACTIVITIES`.
        activities = {ref for name in TOPIC_SOURCES
                      for _, _, ref in sources.get(name, []) if ref and ref[1]}
        confidence = len(activities)

        # HAI con số, không phải một (L8, anh Sơn chốt 31/08/2026 "giữ nhưng
        # tách hiển thị"). `mastery` gộp cả điểm thi thử — đề thi thử chỉ chia
        # theo HỢP PHẦN chứ không biết câu nào thuộc chủ đề nào, nên nó là bối
        # cảnh cấp khoá được rải đều 25% vào MỌI ô chủ đề của khoá đó.
        #
        # Đo được cái giá của việc trộn: Đại số của em id 9 đáng lẽ 62, hiện 42
        # vì bị kéo xuống bởi điểm đề — dưới ngưỡng 60 nên hệ xếp 17 buổi "Ôn
        # lại Đại số" vào lịch của em.
        #
        # Nên: `mastery` để HIỆN (giữ như anh chốt), `masteryTopic` chỉ từ bằng
        # chứng thật của chủ đề, và mọi quyết định XẾP LỊCH dùng con số sau.
        mastery, detail = _mastery(sources, today)
        mastery_topic, _ = _mastery(sources, today, chi_chu_de=True)
        if confidence < MIN_ACTIVITIES:
            # Có thể tính ra số, nhưng nói ra thì thành nói dối về độ chắc chắn.
            mastery = None
            mastery_topic = None
        known = cell['known']
        topics.append({
            'course': course_id,
            'courseTitle': cell['courseTitle'],
            'topic': topic,
            'mastery': mastery,
            'masteryTopic': mastery_topic,
            'confidence': confidence,
            'status': 'ok' if mastery is not None else (
                'no_data' if confidence == 0 else 'low_data'),
            'sources': detail,
            'lessonsDone': cell['done'],
            'lessonsTotal': cell['total'],
            'selfMarked': bool(known),
            # Tự nhận đã nắm nhưng bài làm thật nói khác — phải nói thẳng ra.
            'conflict': bool(known) and mastery is not None
                        and mastery < SELF_MARK_CONFLICT_BELOW,
            'suggestion': cell['next'],
        })

    order = {c: i for i, c in enumerate(COURSE_ORDER)}
    topics.sort(key=lambda t: (order.get(t['course'], 9), t['topic']))

    # Tóm tắt cấp hợp phần đi kèm luôn, để giao diện không phải dựng một khối
    # riêng nói cùng một chuyện ở ngay bên cạnh bản đồ (audit 24/08).
    courses = []
    for cid in COURSE_ORDER:
        cells_of = [t for t in topics if t['course'] == cid]
        if not cells_of:
            continue
        mock_items = by_course.get(cid) or []
        done = sum(t['lessonsDone'] for t in cells_of)
        total = sum(t['lessonsTotal'] for t in cells_of)
        courses.append({
            'id': cid,
            'title': cells_of[0]['courseTitle'],
            'lessonsDone': done,
            'lessonsTotal': total,
            'pct': round(done * 100 / total) if total else 0,
            # Độ chính xác thi thử của hợp phần: trung bình có suy giảm theo thời
            # gian, giống hệt cách chấm chủ đề — hai nơi lệch cách tính thì cùng
            # một lượt thi lại ra hai con số khác nhau.
            'mockPct': (round(_decayed_mean([(v, d) for v, d, _ in mock_items], today))
                        if mock_items else None),
            'mockCount': len(mock_items),
        })

    measured = [t for t in topics if t['mastery'] is not None]
    weakest = sorted(measured, key=lambda t: t['mastery'])[:3]
    return {
        'topics': topics,
        'courses': courses,
        'weakest': weakest,
        'measuredCount': len(measured),
        'minActivities': MIN_ACTIVITIES,
        # Bên hiển thị cần câu chữ trung thực khi bản đồ còn trống, chứ không
        # phải một ô "0%" trông như đã đo được.
        'hint': ('Học xong %d bài trong cùng một chủ đề để mở phần đánh giá chủ đề đó.'
                 % MIN_ACTIVITIES) if not measured else None,
    }
