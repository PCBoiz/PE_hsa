"""Hồ sơ học tập bơm vào trợ lý AI.

Trước 24/08 trợ lý chỉ biết TÊN học viên và "hợp phần yếu nhất" suy từ lượt thi
thử gần nhất — tức một phép tính THỨ BA về điểm yếu, thô hơn hẳn và có thể mâu
thuẫn với con số Trang của tôi đang hiện. Nay dùng chung đúng bản đồ năng lực:
một nguồn sự thật, và trợ lý nói được "Hình học 45%" thay vì "Định lượng".

Vì sao có bộ nhớ đệm: dựng hồ sơ tốn 3 lượt truy vấn tới Neon (RTT ~245ms mỗi
lượt). Trò chuyện đi theo tràng — hỏi liên tiếp vài câu — nên chỉ câu đầu của
mỗi tràng nên phải trả cái giá đó. 5 phút là đủ ngắn để vừa học xong một bài,
mở lại trợ lý là thấy số mới; đủ dài để cả một buổi trò chuyện không lặp lại.
"""
import time

from stats import competency
from stats.goals import read_goals

#: Thời gian sống của một hồ sơ trong bộ nhớ đệm (giây).
TTL_SECONDS = 300
#: Trần số hồ sơ giữ trong bộ nhớ, chống phình khi đông người dùng.
MAX_ENTRIES = 200
#: Số chủ đề yếu / vững nêu tên trong hồ sơ.
TOP_N = 3
#: Từ mức này trở lên coi là đã vững.
STRONG_FROM = 75

_cache = {}


def _fmt_courses(courses):
    bits = []
    for c in courses:
        if not c.get('lessonsTotal'):
            continue
        bits.append('%s %d/%d' % (c['title'], c['lessonsDone'], c['lessonsTotal']))
    return ', '.join(bits)


def _build(uid):
    lines = []

    goals = read_goals(uid)
    goal_bits = []
    if goals.get('targetScore'):
        goal_bits.append('mục tiêu %s/150 điểm' % goals['targetScore'])
    if goals.get('daysToExam') is not None:
        goal_bits.append('còn %d ngày tới kỳ thi' % goals['daysToExam'])
    if goal_bits:
        lines.append('- Mục tiêu: ' + ' · '.join(goal_bits))

    data = competency.compute(uid)
    courses = data.get('courses') or []
    done = sum(c.get('lessonsDone') or 0 for c in courses)
    total = sum(c.get('lessonsTotal') or 0 for c in courses)
    if total:
        lines.append('- Tiến độ: %d/%d bài (%s)' % (done, total, _fmt_courses(courses)))

    topics = data.get('topics') or []
    measured = [t for t in topics if t.get('mastery') is not None]
    if measured:
        weak = sorted(measured, key=lambda t: t['mastery'])[:TOP_N]
        lines.append('- Chủ đề yếu nhất (điểm thành thạo 0-100 do hệ thống chấm): '
                     + ', '.join('%s %d' % (t['topic'], t['mastery']) for t in weak))
        strong = [t for t in measured if t['mastery'] >= STRONG_FROM]
        if strong:
            strong.sort(key=lambda t: -t['mastery'])
            lines.append('- Chủ đề đã vững: '
                         + ', '.join('%s %d' % (t['topic'], t['mastery'])
                                     for t in strong[:TOP_N]))
        # Tự nhận đã nắm nhưng bài làm nói khác — trợ lý cần biết để nói thẳng.
        conflict = [t['topic'] for t in measured if t.get('conflict')]
        if conflict:
            lines.append('- Học viên TỰ đánh dấu đã nắm nhưng bài làm thật còn thấp: '
                         + ', '.join(conflict[:TOP_N]))

    unmeasured = len(topics) - len(measured)
    if unmeasured > 0:
        lines.append('- Còn %d/%d chủ đề CHƯA ĐỦ DỮ LIỆU để chấm — không được nói '
                     'học viên mạnh hay yếu ở những chủ đề đó.' % (unmeasured, len(topics)))

    mock_bits = [c for c in courses if c.get('mockPct') is not None and c.get('mockCount')]
    if mock_bits:
        # SỐ LƯỢT phải đi kèm phần trăm. Thiếu nó, "0%" vừa có thể là "chưa thi
        # lần nào" vừa có thể là "thi rồi và sai hết" — và trợ lý đã đoán nhầm
        # đúng chỗ này khi thử (nói học viên chưa làm đề, trong khi họ đã làm).
        lines.append('- Kết quả thi thử theo hợp phần (đã làm đề rồi): '
                     + ', '.join('%s %d%% đúng qua %d lượt'
                                 % (c['title'], c['mockPct'], c['mockCount'])
                                 for c in mock_bits))
    else:
        lines.append('- Học viên CHƯA làm đề thi thử nào.')

    return '\n'.join(lines)


def learner_profile(uid, name=None):
    """Khối bối cảnh cho system prompt. Lỗi ở đây KHÔNG được chặn cuộc trò chuyện:
    trợ lý thiếu hồ sơ vẫn trả lời được, còn trợ lý chết thì không."""
    now = time.monotonic()
    hit = _cache.get(uid)
    if hit and now - hit[0] < TTL_SECONDS:
        body = hit[1]
    else:
        try:
            body = _build(uid)
        except Exception:                                     # noqa: BLE001
            body = ''
        if len(_cache) >= MAX_ENTRIES:
            _cache.clear()          # đủ dùng: hồ sơ dựng lại rẻ, không cần LRU
        _cache[uid] = (now, body)

    head = ('Tên: %s' % name) if name else ''
    if not body:
        return head
    return (head + '\n' + body) if head else body


def invalidate(uid):
    """Xoá hồ sơ khỏi bộ nhớ đệm (dùng khi có thay đổi cần thấy ngay)."""
    _cache.pop(uid, None)
