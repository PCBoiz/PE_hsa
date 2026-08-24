"""Mục tiêu HSA của học viên: điểm nhắm tới và ngày thi còn cách bao xa.

Tách khỏi ``stats/views.py`` vì cả thẻ đếm ngược ở Bảng điều khiển lẫn đường
cong tiến bộ ở Trang của tôi đều cần đúng những con số này. Hai bản sao của một
phép tính ngày tháng là cách chắc chắn để chúng lệch nhau sau vài lần sửa.
"""
import json
import re
from datetime import date, datetime, timedelta

from common.clock import local_today
from common.db import q1

#: Câu "Bạn dự định thi HSA khi nào?" trong khảo sát trả về KHOẢNG thời gian
#: tương đối chứ không phải năm ("Trong 1 tháng", "1–3 tháng"...). Quy mỗi
#: khoảng về số ngày tới CUỐI khoảng đó.
_TIMING_DAYS = (
    (re.compile(r'trong\s*1\s*th[áa]ng', re.I), 30),
    (re.compile(r'1\s*[-–—]\s*3\s*th[áa]ng', re.I), 90),
    (re.compile(r'3\s*[-–—]\s*6\s*th[áa]ng', re.I), 180),
    (re.compile(r'tr[êe]n\s*6\s*th[áa]ng', re.I), 240),
)

#: Thang điểm chính thức của kỳ thi Đánh giá năng lực ĐHQG Hà Nội.
HSA_MAX_SCORE = 150

#: Bốn mốc mục tiêu trong khảo sát → khoảng ĐIỂM (trên thang 150).
#: Đề HSA có 150 câu, mỗi câu 1 điểm, nên điểm và số câu đúng là một — quy về
#: phần trăm là phép chia thẳng, không phải bảng quy đổi. Cái CHƯA chắc là đề
#: rút gọn đang dùng trong sản phẩm có đại diện được cho đề 150 câu hay không;
#: đó là điều phải nói rõ ở giao diện, không phải phép quy đổi.
_TARGET_BANDS = (
    (re.compile(r'd[ưu][ớơo]i\s*75', re.I), (None, 75)),
    (re.compile(r'75\s*[-–—]\s*90', re.I), (75, 90)),
    (re.compile(r'90\s*[-–—]\s*105', re.I), (90, 105)),
    (re.compile(r'tr[êe]n\s*105', re.I), (105, None)),
)


def as_date(value):
    """date/datetime/chuỗi 'YYYY-MM-DD' (hoặc ISO) → date. Không parse được → None."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)[:19].replace(' ', 'T')).date()
    except ValueError:
        return None


def days_to_exam(exam_timing, exam_date=None, answered_at=None):
    """Số ngày còn lại tới kỳ thi, theo thứ tự ưu tiên nguồn dữ liệu.

    1. ``exam_date`` — ngày thi học viên tự nhập ở Cài đặt → chính xác tuyệt đối.
    2. ``exam_timing`` có ghi năm ("đợt 1/2027") → quy ước kỳ thi đợt đầu cuối
       tháng 3 của năm đó (năm sau nếu đã qua).
    3. ``exam_timing`` là khoảng tương đối → neo vào NGÀY LÀM KHẢO SÁT rồi cộng
       độ dài khoảng. Neo vào hôm nay thì con số đứng yên mãi mãi, không bao giờ
       đếm ngược — người trả lời "Trong 1 tháng" từ nửa năm trước vẫn thấy 30.

    Không suy ra được → None để thẻ hiện dấu gạch kèm nút sửa mốc thi, thay vì
    một con số bịa.
    """
    today = local_today()

    d = as_date(exam_date)
    if d:
        delta = (d - today).days
        return delta if delta >= 0 else None

    if not exam_timing:
        return None
    s = str(exam_timing)

    m = re.search(r'20\d{2}', s)
    if m:
        for y in (int(m.group()), int(m.group()) + 1):
            try:
                delta = (date(y, 3, 31) - today).days
            except ValueError:
                return None
            if delta >= 0:
                return delta
        return None

    anchor = as_date(answered_at) or today
    for rx, days in _TIMING_DAYS:
        if rx.search(s):
            delta = (anchor + timedelta(days=days) - today).days
            return delta if delta >= 0 else None
    return None


def target_band(target_score):
    """Mốc mục tiêu dạng chữ → dải phần trăm để vẽ lên biểu đồ.

    Trả None khi học viên chưa đặt mục tiêu — biểu đồ bỏ dải đích, KHÔNG vẽ một
    dải mặc định. Đích do hệ thống tự nghĩ ra thì không phải đích của ai cả.
    """
    if not target_score:
        return None
    s = str(target_score)
    for rx, (lo, hi) in _TARGET_BANDS:
        if rx.search(s):
            return {
                'raw': s,
                'minScore': lo,
                'maxScore': hi,
                'minPct': round(lo * 100 / HSA_MAX_SCORE) if lo is not None else None,
                'maxPct': round(hi * 100 / HSA_MAX_SCORE) if hi is not None else None,
                'maxScoreScale': HSA_MAX_SCORE,
            }
    return None


#: "Mỗi ngày bạn ôn được bao lâu?" trong khảo sát → số PHÚT mỗi ngày, lấy mốc
#: THẬN TRỌNG (đầu khoảng) chứ không lấy mốc lạc quan: kế hoạch dựng trên con số
#: đẹp nhất là kế hoạch trượt ngay tuần đầu.
_STUDY_MINUTES = (
    (re.compile(r'd[ưu][ớơo]i\s*1\s*gi[ờo]', re.I), 40),
    (re.compile(r'1\s*[-–—]\s*2\s*gi[ờo]', re.I), 60),
    (re.compile(r'2\s*[-–—]\s*3\s*gi[ờo]', re.I), 120),
    (re.compile(r'tr[êe]n\s*3\s*gi[ờo]', re.I), 180),
)


def daily_minutes(study_time):
    """Số phút ôn mỗi ngày học viên tự khai. Không khai → None (không đoán hộ)."""
    if not study_time:
        return None
    s = str(study_time)
    for rx, mins in _STUDY_MINUTES:
        if rx.search(s):
            return mins
    return None


def read_goals(uid):
    """Mục tiêu + mốc thi từ bản khảo sát gần nhất, kèm số ngày còn lại."""
    out = {'targetScore': None, 'examTiming': None, 'examDate': None,
           'daysToExam': None, 'studyTime': None, 'dailyMinutes': None}
    row = q1("SELECT data_json, created_at FROM surveys WHERE user_id=%s "
             "ORDER BY id DESC LIMIT 1", (uid,))
    data, timing_set_at = {}, None
    if row and row.get('data_json'):
        data = row['data_json']
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                data = {}
        if not isinstance(data, dict):
            data = {}
        out['targetScore'] = data.get('target_score')
        out['examTiming'] = data.get('exam_timing')
        out['examDate'] = data.get('exam_date')
        out['studyTime'] = data.get('study_time')
        out['dailyMinutes'] = daily_minutes(out['studyTime'])
        timing_set_at = data.get('exam_timing_set_at')
    out['daysToExam'] = days_to_exam(out['examTiming'], out['examDate'],
                                     timing_set_at or (row or {}).get('created_at'))
    return out
