"""Kế hoạch học có lịch — vế System-Guided của sản phẩm.

Học viên vẫn là người tư duy và làm bài; lộ trình, mục tiêu từng giai đoạn và
việc theo dõi là do hệ thống lo. Nguyên liệu đã có sẵn từ bốn việc trước: ngày
thi và sức học (khảo sát), 76 bài chia 20 chủ đề, bản đồ năng lực, và mục tiêu
tuần thích ứng.

BỐN QUYẾT ĐỊNH, và vì sao:

1. **Giáo trình làm xương sống, chen bài ôn của chủ đề yếu.** Đi tuần tự theo
   giáo trình (Số học → Đại số → Hàm số…) vì kiến thức có thứ tự phụ thuộc —
   nhảy vào Hình học khi chưa xong Số học là dạy sai. Vế thích ứng nằm ở chỗ
   CHEN THÊM: chủ đề nào điểm thấp thì xen một buổi ôn vào giữa. Học viên mới
   chưa có dữ liệu vẫn có lịch chạy được ngay.

2. **Ba hợp phần xếp xen kẽ, không học hết khoá này mới sang khoá khác.** Đề
   HSA thi cả ba trong một buổi; ôn xong Định lượng rồi bỏ quên nửa năm là cách
   chắc chắn để quên.

3. **`week_start` là tuần DỰ KIẾN lúc sinh, không bao giờ ghi đè.** Lúc đọc,
   mục chưa xong được dồn vào tuần này trở đi theo sức chứa. Tách hai thứ đó ra
   mới đo được ĐỘ CHẬM — ghi đè là mất thước đo, lịch lúc nào cũng trông đúng hạn.

4. **Không đủ thời gian thì nói thẳng bỏ bài nào.** Và bỏ bài của chủ đề học
   viên ĐANG MẠNH trước, giữ lại bài của chủ đề yếu — im lặng cắt từ cuối danh
   sách là vừa nói dối vừa cắt nhầm.
"""
import json
import logging
from datetime import timedelta

from django.db import DatabaseError, transaction

from common.clock import local_now, local_today
from common.db import q, q1, x
from common.events import KIND_DRILL, KIND_LESSON, KIND_MOCK, KIND_REVIEW_QUIZ
from stats import competency, journal
from stats.goals import read_goals

logger = logging.getLogger(__name__)

KIND_LESSON_ITEM = 'lesson'
KIND_MOCK_ITEM = 'mock'
KIND_REVIEW_ITEM = 'review'

#: Dưới mức thành thạo này thì chủ đề được xen thêm một buổi ôn.
REVIEW_BELOW = 60
#: Cứ ngần này bài mới thì chen một buổi ôn — đủ để không quên, không đủ để
#: lịch biến thành ôn đi ôn lại.
REVIEW_EVERY = 4
#: Trần số tuần một kế hoạch trải ra, chống sinh vài nghìn dòng khi ngày thi xa.
MAX_PLAN_WEEKS = 40
#: Chưa biết ngày thi thì trải ngần này tuần.
FALLBACK_WEEKS = 12
#: Số tuần hiển thị mặc định ở màn hình gọn.
DEFAULT_VIEW_WEEKS = 4
#: Số mục tối đa nhét vào MỘT câu INSERT khi lưu kế hoạch.
#:
#: Postgres chặn ở 65535 tham số mỗi câu lệnh, mỗi mục ở đây chiếm 9 tham số.
#: Trần lý thuyết của kế hoạch là MAX_PLAN_WEEKS × (100 bài + 25 buổi ôn + 20
#: đề) = 5.800 mục = 52.200 tham số — vẫn dưới ngưỡng, nhưng sát đến mức không
#: nên gửi nguyên khối, và trần đó phụ thuộc TARGET_LIMITS ở một tệp khác nên
#: một ngày nào đó nó nới ra mà không ai nhớ tới chỗ này.
ITEM_CHUNK = 500

STATUS_TODO = 'todo'
STATUS_SKIPPED = 'skipped'


def _monday(d):
    return d - timedelta(days=d.weekday())


# ── Sinh kế hoạch ───────────────────────────────────────────────────────────

def _remaining_lessons(uid):
    """Bài chưa hoàn thành, gom theo khoá, giữ đúng thứ tự giáo trình."""
    rows = q('''SELECT l.course_id, l.sort_order, l.title, l.module AS topic,
                       c.title AS course_title
                FROM lessons l
                LEFT JOIN courses c ON c.id = l.course_id
                LEFT JOIN lesson_progress lp
                       ON lp.lesson_id = l.id AND lp.user_id = %s
                      AND lp.status = 'completed'
                WHERE l.course_id IS NOT NULL
                  AND l.module IS NOT NULL AND l.module <> ''
                  AND lp.user_id IS NULL
                ORDER BY l.course_id, l.sort_order''', (uid,))
    by_course = {}
    for r in rows:
        by_course.setdefault(r['course_id'], []).append(r)
    return by_course


def _interleave(by_course, order):
    """Xen kẽ ba hợp phần theo vòng, mỗi vòng lấy bài kế tiếp của từng khoá.

    Đề HSA thi cả ba hợp phần trong một buổi; học dứt điểm khoá này rồi mới sang
    khoá khác là cách chắc chắn để quên phần học trước.
    """
    queues = [list(by_course.get(cid, [])) for cid in order]
    queues += [list(v) for k, v in by_course.items() if k not in order]
    out = []
    while any(queues):
        for qq in queues:
            if qq:
                out.append(qq.pop(0))
    return out


def _diem_chu_de(t):
    """Điểm dùng để QUYẾT ĐỊNH xếp lịch — chỉ từ bằng chứng thật của chủ đề.

    `mastery` gộp cả điểm thi thử, mà đề thi thử chỉ chia theo hợp phần chứ
    không biết câu nào thuộc chủ đề nào: nó bị rải đều 25% vào MỌI ô của khoá.
    Đo 31/08/2026: Đại số của em id 9 đáng lẽ 62, hiện 42 vì bị kéo xuống —
    dưới ngưỡng 60 nên hệ xếp 17 buổi "Ôn lại Đại số" vào lịch của em.

    `mastery` vẫn giữ nguyên để HIỆN (anh Sơn chốt "giữ nhưng tách hiển thị");
    chỉ QUYẾT ĐỊNH mới chuyển sang con số này.
    """
    return t.get('masteryTopic', t.get('mastery'))


def _weak_topics(comp):
    """Chủ đề đã ĐO ĐƯỢC và đang dưới ngưỡng, yếu nhất trước.

    Chỉ lấy chủ đề có điểm: chưa đủ dữ liệu mà đã xếp lịch ôn là đoán mò.
    """
    measured = [t for t in (comp.get('topics') or [])
                if _diem_chu_de(t) is not None and _diem_chu_de(t) < REVIEW_BELOW]
    return sorted(measured, key=_diem_chu_de)


def _drop_priority(lesson, mastery_by_cell):
    """Điểm ưu tiên khi buộc phải cắt bớt: CÀNG MẠNH CÀNG BỊ CẮT TRƯỚC.

    Chủ đề chưa đo được xếp giữa — không có cơ sở để bỏ, cũng không có cơ sở để
    ưu tiên giữ.
    """
    m = mastery_by_cell.get((lesson['course_id'], lesson['topic']))
    return 50 if m is None else m


def generate(uid):
    """Sinh lại kế hoạch đang hoạt động. Trả về (tóm tắt, lỗi)."""
    goals = read_goals(uid)
    comp = competency.compute(uid)
    suggestion = journal.suggest_target(uid, goals)
    target = journal.read_target(uid) or {}

    per_week = target.get('lessons') or suggestion['lessons']
    mocks_per_week = target.get('mocks')
    if mocks_per_week is None:
        mocks_per_week = suggestion['mocks']

    days = goals.get('daysToExam')
    # `is not None` chứ KHÔNG phải `if days`: ngày thi HÔM NAY cho `days = 0`,
    # mà `0` là falsy. Hệ quả đo được: còn 1 ngày → chế độ báo động (3 đề/tuần,
    # cảnh báo "bỏ N bài"); còn 0 ngày → chế độ thư thả (1 đề/tuần, cảnh báo
    # biến mất, lịch trải 12 tuần). Đúng cái ngày cần siết nhất thì hệ nới ra.
    weeks_total = max(1, min(-(-days // 7) if days is not None else FALLBACK_WEEKS,
                             MAX_PLAN_WEEKS))
    drill_weeks = min(journal.FINAL_DRILL_WEEKS, max(0, weeks_total - 1))
    build_weeks = max(1, weeks_total - drill_weeks)

    by_course = _remaining_lessons(uid)
    lessons = _interleave(by_course, competency.COURSE_ORDER)

    # Sức chứa cho bài mới trong cả kế hoạch.
    capacity = per_week * build_weeks
    dropped = []
    if len(lessons) > capacity:
        mastery_by_cell = {(t['course'], t['topic']): _diem_chu_de(t)
                           for t in (comp.get('topics') or [])}
        # Cắt bài của chủ đề ĐANG MẠNH trước; giữ bài của chủ đề yếu.
        ranked = sorted(range(len(lessons)),
                        key=lambda i: (-_drop_priority(lessons[i], mastery_by_cell), -i))
        cut = set(ranked[:len(lessons) - capacity])
        dropped = [lessons[i] for i in sorted(cut)]
        lessons = [l for i, l in enumerate(lessons) if i not in cut]

    weak = _weak_topics(comp)
    first_monday = _monday(local_today())

    items = []
    order = 0
    idx = 0
    weak_i = 0
    for w in range(weeks_total):
        week_start = first_monday + timedelta(weeks=w)
        in_drill_phase = w >= build_weeks

        if not in_drill_phase:
            placed = 0
            while placed < per_week and idx < len(lessons):
                l = lessons[idx]; idx += 1; placed += 1
                order += 1
                items.append({
                    'week_start': week_start, 'sort_order': order,
                    'kind': KIND_LESSON_ITEM, 'course_id': l['course_id'],
                    'lesson_no': l['sort_order'], 'topic': l['topic'],
                    'title': l['title'],
                    'reason': None,
                })
                # Chen buổi ôn cho chủ đề yếu — vế thích ứng của lịch.
                if weak and placed % REVIEW_EVERY == 0:
                    t = weak[weak_i % len(weak)]; weak_i += 1
                    order += 1
                    items.append({
                        'week_start': week_start, 'sort_order': order,
                        'kind': KIND_REVIEW_ITEM, 'course_id': t['course'],
                        'lesson_no': None, 'topic': t['topic'],
                        'title': 'Ôn lại: ' + t['topic'],
                        # KHÔNG viết "thấp nhất": chỉ chủ đề đầu tiên mới thấp
                        # nhất, các chủ đề sau đều là câu nói sai.
                        # In ĐÚNG con số đã quyết định (`masteryTopic`), không
                        # in con số đã trộn điểm đề. Bản cũ in `t['mastery']`,
                        # nên một chủ đề có bằng chứng 45 mà điểm đề 100 cho ra
                        # câu "Điểm thành thạo đang 62/100, dưới ngưỡng 60" —
                        # tự mâu thuẫn, in thẳng cho học viên đọc.
                        'reason': ('Điểm thành thạo đang %d/100, dưới ngưỡng %d.'
                                   % (_diem_chu_de(t), REVIEW_BELOW)),
                    })

            # Hết bài mà vẫn còn tuần: lấp bằng buổi ôn chủ đề yếu, đừng để
            # tuần chỉ có mỗi một đề. Học xong giáo trình rồi ngồi không hai
            # tháng là cách chắc chắn để quên phần đã học.
            if placed == 0 and weak:
                for _ in range(2):
                    t = weak[weak_i % len(weak)]; weak_i += 1
                    order += 1
                    items.append({
                        'week_start': week_start, 'sort_order': order,
                        'kind': KIND_REVIEW_ITEM, 'course_id': t['course'],
                        'lesson_no': None, 'topic': t['topic'],
                        'title': 'Ôn lại: ' + t['topic'],
                        'reason': 'Đã hết bài mới — giai đoạn này dành để ôn và luyện đề.',
                    })

        n_mocks = max(mocks_per_week, 3) if in_drill_phase else mocks_per_week
        for _ in range(n_mocks):
            order += 1
            items.append({
                'week_start': week_start, 'sort_order': order,
                'kind': KIND_MOCK_ITEM, 'course_id': None, 'lesson_no': None,
                'topic': None, 'title': 'Làm một đề thi thử',
                'reason': ('Hai tuần cuối chỉ luyện đề, không nạp bài mới.'
                           if in_drill_phase else None),
            })

    basis = {
        'perWeek': per_week, 'mocksPerWeek': mocks_per_week,
        'weeksTotal': weeks_total, 'buildWeeks': build_weeks,
        'drillWeeks': drill_weeks,
        'lessonsPlanned': idx, 'lessonsDropped': len(dropped),
        'usedTarget': bool(target.get('lessons')),
        'weakTopics': [t['topic'] for t in weak[:3]],
        # Tên vài bài bị bỏ, lưu luôn vào kế hoạch: "bỏ 63 bài" mà không nói bài
        # nào thì học viên không kiểm chứng được, và cũng không tự bù lại được.
        'droppedSample': [l['title'] for l in dropped[:5]],
    }

    now = local_now()
    with transaction.atomic():
        plan = q1('SELECT id FROM study_plans WHERE user_id=%s AND is_active LIMIT 1', (uid,))
        if plan:
            plan_id = plan['id']
            x('DELETE FROM study_plan_items WHERE plan_id=%s', (plan_id,))
            x('''UPDATE study_plans SET generated_at=%s, updated_at=%s,
                        exam_date=%s, basis=%s::jsonb WHERE id=%s''',
              (now, now, goals.get('examDate'), json.dumps(basis, ensure_ascii=False), plan_id))
        else:
            plan_id = q1('''INSERT INTO study_plans
                                (user_id, created_at, updated_at, generated_at,
                                 exam_date, basis, is_active)
                            VALUES (%s,%s,%s,%s,%s,%s::jsonb,TRUE) RETURNING id''',
                         (uid, now, now, now, goals.get('examDate'),
                          json.dumps(basis, ensure_ascii=False)))['id']
        # MỘT câu cho cả mẻ thay vì một câu mỗi mục. Đo 31/08/2026: sinh lại kế
        # hoạch cho một học viên tốn 147 lượt gọi Neon, trong đó 136 là INSERT
        # từng mục một. Cả vòng lặp nằm trong transaction.atomic() nên mỗi lượt
        # là một chặng khứ hồi phải chờ xong mới đi tiếp — và người dùng đang
        # nhìn nút "Sinh lại kế hoạch" quay.
        for i in range(0, len(items), ITEM_CHUNK):
            me = items[i:i + ITEM_CHUNK]
            x('INSERT INTO study_plan_items '
              '(plan_id, week_start, sort_order, kind, course_id, lesson_no, '
              'topic, title, reason) VALUES '
              + ', '.join(['(%s,%s,%s,%s,%s,%s,%s,%s,%s)'] * len(me)),
              tuple(v for it in me for v in
                    (plan_id, it['week_start'], it['sort_order'], it['kind'],
                     it['course_id'], it['lesson_no'], it['topic'], it['title'],
                     it['reason'])))

    return basis, None


# ── Đọc kế hoạch ────────────────────────────────────────────────────────────

def _truoc_moc_san(moc, floor):
    """Sự kiện xảy ra TRƯỚC mốc sàn của kế hoạch?

    `floor` là `date` khi kế hoạch cũ chưa có `generated_at`, và là `datetime`
    khi có — so đúng kiểu ở từng nhánh thay vì cắt tất cả về ngày.
    """
    if hasattr(floor, 'hour') and hasattr(moc, 'hour'):
        return moc < floor
    ngay = moc.date() if hasattr(moc, 'date') else moc
    san = floor.date() if hasattr(floor, 'date') else floor
    return ngay < san


def _moc_san(rows, generated_at):
    """Mốc sàn: hoạt động TRƯỚC mốc này không được tick mục nào trong kế hoạch.

    Phải là lúc SINH kế hoạch, không phải tuần đầu của kế hoạch. Kế hoạch sinh
    hôm thứ Tư nhưng bắt đầu từ thứ Hai cùng tuần thì hai ngày thứ Hai–thứ Ba
    nằm TRƯỚC lúc nó tồn tại — mà bản cũ vẫn cho chúng tick, nên kế hoạch vừa
    lập ra đã có sẵn mục "đã xong". Việc em làm trước khi có kế hoạch là việc
    thật, nhưng nó không phải là tiến độ của kế hoạch này.

    Lùi về tuần đầu khi chưa có `generated_at` (kế hoạch cũ trước khi cột này
    được ghi) — thà rộng tay còn hơn tick nhầm về phía ngược lại.
    """
    tuan_dau = min((r['week_start'] for r in rows), default=local_today())
    if not generated_at:
        return tuan_dau
    # Giữ NGUYÊN `datetime` chứ không cắt về `date`: cắt đi thì kế hoạch sinh
    # lúc 00:30 vẫn bị tick bởi việc làm lúc 00:10 cùng ngày. Chỉ lùi về `date`
    # khi tuần đầu muộn hơn ngày sinh (kế hoạch bắt đầu ở tương lai).
    ngay_sinh = generated_at.date() if hasattr(generated_at, 'date') else generated_at
    if tuan_dau > ngay_sinh:
        return tuan_dau
    return generated_at


def _done_lookup(uid, floor):
    """Những gì học viên ĐÃ làm, đủ để suy ra mục nào trong lịch đã xong.

    Suy lúc đọc chứ không ghi 'done' vào bảng: không bao giờ lệch với thực tế,
    và không cần tác vụ đồng bộ nào.

    ``floor`` là tuần đầu của kế hoạch — hoạt động TRƯỚC đó không tính, nếu
    không thì một đề thi từ hai tháng trước lại tick xong một mục vừa mới xếp.

    Việc quá hạn phải được tha thứ: một mục dự kiến tuần trước mà học viên làm
    tuần này thì vẫn là XONG. Nên mốc so sánh là "từ tuần dự kiến trở đi", không
    phải "đúng tuần dự kiến".
    """
    try:
        rows = q("""SELECT e.kind, e.course_id, e.topic, e.event_date,
                           e.occurred_at, e.meta
                    FROM learning_events e
                    WHERE e.user_id = %s AND e.kind = ANY(%s)""",
                 (uid, [KIND_LESSON, KIND_MOCK, KIND_REVIEW_QUIZ]))
    except DatabaseError:
        return set(), [], {}
    return _gom_hoat_dong(rows, floor)


#: Loại sự kiện KHÔNG được tính là "đã ôn lại chủ đề".
#:
#: Học một bài mới trong chủ đề X không phải là ôn lại chủ đề X — và học viên
#: cũng không hề làm hai việc. Bản cũ để chúng vào chung một rổ, nên MỘT lần
#: hoàn thành bài tick xong HAI mục kế hoạch: mục "học bài N" (qua
#: `done_lessons`) và mục "Ôn lại X" (qua `topic_dates`). Phòng luyện cùng lý
#: do: nó sinh ra từ đúng lần hoàn thành bài ấy, đếm nó là đếm lần thứ ba.
#:
#: Còn lại được tính là ôn: quiz ôn tập (đúng tên nó).
#:
#: CHÚ THÍCH NÀY TỪNG NÓI THÊM "điểm hợp phần đề thi thử, và bài tập giảng viên
#: chấm" — SAI. Hai đường đọc sự kiện (`_done_lookup` và `do_cham_theo_hoc_vien`)
#: chỉ lấy `[KIND_LESSON, KIND_MOCK, KIND_REVIEW_QUIZ]`, nên `mock_section` và
#: `assignment` không bao giờ tới được nhánh `topic_dates`. Nói một luật mà truy
#: vấn không thi hành là cách chắc chắn để người đọc sau tin nhầm.
#:
#: HỆ QUẢ ĐANG CHẤP NHẬN: mục "Ôn lại X" chỉ có MỘT cách được tick — làm quiz ôn
#: tập có câu thuộc chủ đề X. Mà quiz ôn tập cần đủ 5 câu trong kho mới mở được,
#: nên em chưa học đủ sẽ thấy mọi mục "Ôn lại" đứng `todo` vĩnh viễn và cộng vào
#: con số "đang chậm N việc". Nới ra là một quyết định sản phẩm (bài tập chấm
#: tay có tính là ôn không?) — chưa chốt, xem TODO.
KHONG_TINH_LA_ON_LAI = (KIND_LESSON, KIND_DRILL)


def _gom_hoat_dong(rows, floor):
    """Phan THUAN TINH cua `_done_lookup`, tach ra de dung lai theo me.

    Tach vi `teaching/reports` can con so "cham" cho CA LOP: goi `_done_lookup`
    trong vong lap la mot luot toi Neon cho moi em. Nhung luat suy "muc nao da
    xong" thi phai y het — hai ban chep tay la hai ban se troi khoi nhau, ma
    dung do la loi T62 dang va.
    """
    # BẢNG TRA ngày, không phải tập hợp: `read` cần biết mục được hoàn thành
    # TUẦN NÀO để đặt nó vào đúng tuần hiển thị. Giữ ngày SỚM NHẤT — cùng luật
    # `event_date = LEAST(...)` mà anh chốt cho việc học lại (L7).
    done_lessons = {}
    mock_dates = []
    topic_dates = {}
    for r in rows:
        # So ở mức GIỜ khi có `occurred_at`, không chỉ mức ngày. Mốc sàn cắt về
        # `date` thì kế hoạch sinh lúc 00:30 vẫn bị tick bởi việc làm lúc 00:10
        # cùng ngày — tức 20 phút TRƯỚC khi nó tồn tại. `event_date` giữ lại làm
        # đường lùi cho dòng cũ chưa có `occurred_at`.
        day = r['event_date']
        moc = r.get('occurred_at') or day
        if r['kind'] == KIND_LESSON:
            # Bài đã học là đã học, bất kể học lúc nào — không áp mốc floor.
            meta = r['meta']
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except ValueError:
                    meta = {}
            no = (meta or {}).get('lessonNo')
            if r['course_id'] and no is not None:
                k = (r['course_id'], int(no))
                if k not in done_lessons or day < done_lessons[k]:
                    done_lessons[k] = day
        if _truoc_moc_san(moc, floor):
            continue
        if r['kind'] == KIND_MOCK:
            mock_dates.append(day)
        elif r['topic'] and r['kind'] not in KHONG_TINH_LA_ON_LAI:
            topic_dates.setdefault((r['course_id'], r['topic']), []).append(day)
    mock_dates.sort()
    for v in topic_dates.values():
        v.sort()
    return done_lessons, mock_dates, topic_dates


def _duyet_muc(rows, done_lessons, mock_dates, topic_dates, this_monday):
    """Từng mục kế hoạch → trạng thái, và đếm việc QUÁ HẠN chưa xong.

    NƠI DUY NHẤT định nghĩa "chậm mấy việc" (T62, anh chốt 31/08/2026: đếm MỌI
    loại việc quá hạn, không chỉ bài học).

    Trước đó có HAI phép tính chạy song song: màn hình học viên đi qua hàm này,
    còn báo cáo lớp của giảng viên chạy một câu SQL riêng chỉ đếm `kind='lesson'`
    VÀ hỏi một bảng khác (`lesson_progress` thay vì `learning_events`) để biết
    "bài này xong chưa". Đo trên dữ liệu thật: học viên id 12 mở app thấy **14**,
    giảng viên mở báo cáo thấy **12**. Giảng viên gọi điện nói một số, em mở máy
    thấy số khác — mất tin vào cả hai.

    Vòng duyệt này CÓ TRẠNG THÁI (`mock_i`, `topic_used` chạy theo `sort_order`),
    nên không viết lại được bằng một câu SQL. Đó chính là lý do bản cũ ở
    `teaching/reports` phải tự chế một phép tính khác — và vì sao cách sửa đúng
    là gọi lại hàm này chứ không phải sửa câu SQL kia cho giống.
    """
    pending, finished, lag = [], [], 0
    mock_i = 0
    topic_used = {}
    for r in rows:
        item = dict(r)
        item['plannedWeek'] = r['week_start'].isoformat()
        if r['status'] == STATUS_SKIPPED:
            item['state'] = STATUS_SKIPPED
        elif r['kind'] == KIND_LESSON_ITEM:
            ngay = done_lessons.get((r['course_id'], r['lesson_no']))
            item['state'] = 'done' if ngay else STATUS_TODO
            item['doneDate'] = ngay
        elif r['kind'] == KIND_MOCK_ITEM:
            # Mỗi lượt thi thử chỉ tick xong ĐÚNG MỘT mục, và chỉ tick được mục
            # có tuần dự kiến không muộn hơn ngày thi. Duyệt theo sort_order nên
            # mục sớm nhất được tick trước — đúng cảm giác "đã làm 3 đề rồi".
            if mock_i < len(mock_dates) and mock_dates[mock_i] >= r['week_start']:
                item['doneDate'] = mock_dates[mock_i]
                mock_i += 1
                item['state'] = 'done'
            else:
                item['state'] = STATUS_TODO
        else:                                     # buổi ôn chủ đề
            key = (r['course_id'], r['topic'])
            days = topic_dates.get(key) or []
            used = topic_used.get(key, 0)
            if used < len(days) and days[used] >= r['week_start']:
                item['doneDate'] = days[used]
                topic_used[key] = used + 1
                item['state'] = 'done'
            else:
                item['state'] = STATUS_TODO

        if item['state'] == STATUS_TODO:
            # Việc quá hạn mà chưa xong = độ chậm. Đo trên tuần DỰ KIẾN, nên
            # việc dồn lịch phía dưới không làm con số này đẹp lên.
            if r['week_start'] < this_monday:
                lag += 1
            pending.append(item)
        else:
            item['week'] = item['plannedWeek']
            finished.append(item)
    return pending, finished, lag


def do_cham_theo_hoc_vien(uids):
    """Độ chậm của NHIỀU học viên trong BA câu SQL. Trả ``(dict, ok)``.

    Cùng phép tính với màn hình của chính học viên (`read`) — cả hai đi qua
    `_duyet_muc`. Đó là toàn bộ mục đích của hàm này: `teaching/reports` trước
    đây tự chế một câu SQL riêng và cho ra con số khác.

    BA câu cho cả lớp, không phải ba câu cho mỗi em: gọi `read()` trong vòng lặp
    là đúng cái N+1 mà cả khu `teaching/` cấm — một lớp 30 em sẽ là 90 lượt tới
    Neon cho một lần mở báo cáo.

    ``ok=False`` nghĩa là KHÔNG ĐỌC ĐƯỢC, khác hẳn "không ai chậm" — bên gọi
    phải phân biệt được, nếu không màn hình sẽ nói "cả lớp đúng tiến độ" đúng
    vào lúc nó không biết gì cả.
    """
    if not uids:
        return {}, True
    uids = list(uids)
    try:
        ke_hoach = q('SELECT id, user_id, generated_at FROM study_plans '
                     'WHERE user_id = ANY(%s) AND is_active', (uids,))
        if not ke_hoach:
            return {}, True
        theo_plan = {r['id']: r['user_id'] for r in ke_hoach}
        # Mốc sàn phải giống hệt bên màn hình học viên — hai bản chép tay là hai
        # bản sẽ trôi khỏi nhau, đúng lỗi T62 vừa vá.
        sinh_luc = {r['user_id']: r['generated_at'] for r in ke_hoach}
        muc = q('SELECT plan_id, id, week_start, sort_order, kind, course_id, '
                '       lesson_no, topic, title, reason, status '
                '  FROM study_plan_items WHERE plan_id = ANY(%s) '
                ' ORDER BY plan_id, sort_order', (list(theo_plan),))
        su_kien = q('SELECT user_id, kind, course_id, topic, event_date, '
                    '       occurred_at, meta '
                    '  FROM learning_events '
                    ' WHERE user_id = ANY(%s) AND kind = ANY(%s)',
                    (uids, [KIND_LESSON, KIND_MOCK, KIND_REVIEW_QUIZ]))
    except DatabaseError:
        logger.error('[plan] KHÔNG đọc được kế hoạch của %d học viên', len(uids))
        return {}, False

    muc_theo_uid = {}
    for r in muc:
        muc_theo_uid.setdefault(theo_plan[r['plan_id']], []).append(r)
    sk_theo_uid = {}
    for r in su_kien:
        sk_theo_uid.setdefault(r['user_id'], []).append(r)

    this_monday = _monday(local_today())
    ra = {}
    for uid, rows in muc_theo_uid.items():
        floor = _moc_san(rows, sinh_luc.get(uid))
        done_lessons, mock_dates, topic_dates = _gom_hoat_dong(
            sk_theo_uid.get(uid, []), floor)
        _, _, lag = _duyet_muc(rows, done_lessons, mock_dates, topic_dates, this_monday)
        if lag:
            ra[uid] = lag
    return ra, True


def read(uid, weeks=DEFAULT_VIEW_WEEKS, all_weeks=False):
    """Kế hoạch đã DỒN LẠI theo thực tế, kèm độ chậm và lý do từng mục."""
    plan = q1('''SELECT id, generated_at, basis, exam_date
                 FROM study_plans WHERE user_id=%s AND is_active LIMIT 1''', (uid,))
    if not plan:
        return {'hasPlan': False, 'weeks': [], 'lag': 0,
                'hint': 'Chưa có kế hoạch. Bấm "Lập kế hoạch" để hệ thống xếp lịch từ '
                        'ngày thi, sức học và chủ đề bạn đang yếu.'}

    rows = q('''SELECT id, week_start, sort_order, kind, course_id, lesson_no,
                       topic, title, reason, status
                FROM study_plan_items WHERE plan_id=%s ORDER BY sort_order''',
             (plan['id'],))
    floor = _moc_san(rows, plan['generated_at'])
    done_lessons, mock_dates, topic_dates = _done_lookup(uid, floor)
    basis = plan['basis']
    if isinstance(basis, str):
        try:
            basis = json.loads(basis)
        except ValueError:
            basis = {}
    basis = basis or {}
    per_week = basis.get('perWeek') or 3

    this_monday = _monday(local_today())

    pending, finished, lag = _duyet_muc(rows, done_lessons, mock_dates, topic_dates,
                                        this_monday)
    # Dồn việc chưa xong vào tuần này trở đi, theo sức chứa mỗi tuần.
    # `week_start` trong DB giữ nguyên (để đo độ chậm); `week` là tuần HIỂN THỊ.
    all_by_week = {}
    cur, room = this_monday, per_week
    for item in pending:
        if item['kind'] == KIND_MOCK_ITEM:
            # Đề thi giữ nguyên tuần dự kiến nếu còn ở tương lai; quá hạn thì đẩy
            # về tuần này. Không dồn đề theo sức chứa bài học — nhồi bốn đề vào
            # một tuần chỉ tổ khiến người ta bỏ cuộc.
            wk = max(item['week_start'], this_monday)
        else:
            if room <= 0:
                cur = cur + timedelta(weeks=1)
                room = per_week
            wk = cur
            room -= 1
        item['week'] = wk.isoformat()
        all_by_week.setdefault(item['week'], []).append(item)

    # Mục đã xong / đã bỏ qua hiện ở tuần MUỘN HƠN giữa tuần dự kiến và tuần
    # thực sự hoàn thành.
    #
    # Trước đây luôn dùng tuần DỰ KIẾN, nên một bài lên lịch tuần trước mà học
    # xong hôm nay bị đặt vào tuần đã qua — và tuần đã qua thì không hiện. Người
    # học tick xong thì mục ấy BIẾN MẤT thay vì hiện ra, trong khi `totals.done`
    # vẫn đếm nó: hai con số trên cùng màn hình không khớp nhau.
    #
    # `max` chứ không phải tuần hoàn thành trần: mục làm SỚM vẫn nằm ở tuần dự
    # kiến của nó (kế hoạch nhìn về phía trước). Phép này chỉ TĂNG độ hiện, không
    # bao giờ giảm.
    for item in finished:
        ngay = item.get('doneDate')
        if ngay:
            item['week'] = max(item['week'], _monday(ngay).isoformat())
        all_by_week.setdefault(item['week'], []).append(item)

    # Tuần đã qua không hiện: kế hoạch là thứ nhìn về phía trước. Việc quá hạn
    # đã được dồn vào tuần này rồi, và độ chậm nằm ở con số `lag`.
    today_key = this_monday.isoformat()
    keys = [k for k in sorted(all_by_week) if k >= today_key]
    if not all_weeks:
        keys = keys[:max(1, int(weeks or DEFAULT_VIEW_WEEKS))]
    weeks_out = []
    for k in keys:
        its = sorted(all_by_week[k], key=lambda i: i['sort_order'])
        weeks_out.append({
            'weekStart': k,
            'isThisWeek': k == today_key,
            'items': [_item_out(i) for i in its],
            'total': len(its),
            'done': sum(1 for i in its if i['state'] == 'done'),
        })

    total_items = len(rows)
    done_items = total_items - len(pending) - sum(
        1 for r in rows if r['status'] == STATUS_SKIPPED)
    return {
        'hasPlan': True,
        'weeks': weeks_out,
        'lag': lag,
        'perWeek': per_week,
        'basis': basis,
        'generatedAt': plan['generated_at'].isoformat() if plan['generated_at'] else None,
        'examDate': plan['exam_date'].isoformat() if plan['exam_date'] else None,
        'totals': {'all': total_items, 'done': done_items,
                   'todo': len(pending),
                   'skipped': sum(1 for r in rows if r['status'] == STATUS_SKIPPED)},
        'hint': None,
    }


def _item_out(i):
    return {
        'id': i['id'], 'kind': i['kind'], 'course': i['course_id'],
        'lessonNo': i['lesson_no'], 'topic': i['topic'], 'title': i['title'],
        'reason': i['reason'], 'state': i['state'],
        'plannedWeek': i['plannedWeek'], 'week': i.get('week'),
    }


def set_item_status(uid, item_id, status):
    if status not in (STATUS_TODO, STATUS_SKIPPED):
        return None, 'Trạng thái phải là "todo" hoặc "skipped".'
    row = q1('''SELECT i.id FROM study_plan_items i
                JOIN study_plans p ON p.id = i.plan_id
                WHERE i.id=%s AND p.user_id=%s''', (item_id, uid))
    if not row:
        return None, 'Không tìm thấy mục này trong kế hoạch của bạn.'
    x('UPDATE study_plan_items SET status=%s, skipped_at=%s WHERE id=%s',
      (status, local_now() if status == STATUS_SKIPPED else None, item_id))
    return status, None
