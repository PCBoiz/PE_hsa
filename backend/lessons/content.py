"""Nội dung bài học HSA: đọc từ DB và kiểm tra cấu trúc trước khi lưu.

BỐI CẢNH (audit 2026-08-14). Toàn bộ 76 bài HSA đang nằm trong
``frontend/public/static/js/lesson_content_hsa.js`` — một file 364 kB phía
client. Cột ``lessons.content_json`` có trong schema nhưng KHÔNG có chỗ nào
phục vụ nó cho engine bài học, nên trang Quản trị tạo bài xong thì học viên
không bao giờ thấy. Hệ quả: muốn nạp giáo trình của đối tác vào thì phải sửa tay
file JS đó.

Module này mở đường: nội dung lưu trong DB, engine đọc qua API, và bài nào DB
chưa có thì vẫn rơi về file JS như cũ — bản demo không gãy trong lúc chuyển đổi.

Hình dạng một bài (giữ NGUYÊN schema mà engine đang dùng, không phát minh lại):

    {
      "id": "ql_01",                 # mã bài, duy nhất trong khoá
      "index": 1,                    # số thứ tự bài, dùng cho ?lesson=N
      "title": "Tỉ lệ & phần trăm",
      "subtitle": "…",               # không bắt buộc
      "topic_tag": "Định lượng · Số học",
      "xp_reward": 50,
      "test":   {"intro": "…", "questions": [ … ]},
      "assess": {"strong_min": 3, "ok_min": 2},
      "theory": {"condensed": {…}, "full": {…}},
      "note":   {…},                 # không bắt buộc
      "drill":  {…}                  # không bắt buộc
    }
"""
import json
import re

from common.db import q, q1
from lessons.grading import bo_dap_an

#: Trường bắt buộc — thiếu một trong số này thì engine sẽ hỏng giữa chừng.
REQUIRED = ('id', 'index', 'title', 'test', 'theory')
#: Trần độ dài để một lần nhập sai không nhét cả cuốn sách vào DB.
MAX_LESSON_BYTES = 400_000

# ── HTML TRONG NỘI DUNG BÀI: CHO PHÉP, NHƯNG CÓ DANH SÁCH ───────────────────
#
# VÌ SAO CẦN (vá 04/09/2026). Engine bài học đổ HAI trường vào `innerHTML` mà
# KHÔNG escape — cố ý, vì người soạn cần in đậm và gõ công thức:
#
#     lesson_hsa.js:33    test.intro
#     lesson_hsa.js:401   theory.{full,condensed}.cards[].body
#
# Chuyện ấy vô hại khi người soạn CHÍNH LÀ quản trị viên. Nhưng từ 04/09 có vai
# `Biên tập nội dung` — vai trò sinh ra để KHÔNG phải cấp quyền quản trị cho
# người gõ bài. Không có bộ lọc thì vai ấy leo thẳng lên quyền quản trị: nhét
# `<img src=x onerror=fetch('/api/admin/users/create', …)>` vào `intro`, rồi đợi
# một quản trị viên mở bài ra xem thử. Mã chạy trên miền Vercel nơi cookie phiên
# sống, nên không cần đọc token — chỉ cần dùng nó.
#
# ĐO TRƯỚC KHI CHỌN DANH SÁCH. Quét cả 76 bài đang có:
#     <strong> 160 lần · <code> 134 · <b> 62 · và KHÔNG một thuộc tính nào.
# Nên danh sách dưới đây rộng hơn thực tế đang dùng, mà vẫn không có chỗ nào
# treo được mã: không thuộc tính = không `onerror`, không `href`, không `style`.
THE_CHO_PHEP = frozenset({
    'b', 'strong', 'i', 'em', 'u', 'code', 'br', 'sub', 'sup',
})

# `<` MỞ THẺ chỉ khi liền sau là chữ cái hoặc `/` — đúng luật của bộ phân tích
# HTML. Nếu bỏ qua chi tiết này thì `0 < a < 1` (có thật trong
# `hsa_quantitative#8`) bị coi là thẻ `<a>` và nội dung toán học bị chặn oan.
# Chính phép đo đầu tiên của tôi đã sập đúng bẫy ấy và báo "có 1 thẻ <a>".
_MO_THE = re.compile(r'<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*)>')


def _kiem_html(chuoi, path, errors):
    """Bắt lỗi thẻ lạ và MỌI thuộc tính trong một chuỗi nội dung."""
    for dong, ten, duoi in _MO_THE.findall(chuoi or ''):
        t = ten.lower()
        if t not in THE_CHO_PHEP:
            errors.append(_err(path, 'không cho phép thẻ <%s>. Chỉ dùng được: %s'
                               % (t, ', '.join('<%s>' % x for x in sorted(THE_CHO_PHEP)))))
        elif not dong and duoi.strip().rstrip('/').strip():
            # Thuộc tính là chỗ treo mã (`onerror`, `href`, `style`), nên cấm
            # HẾT thay vì lọc từng cái — lọc từng cái là một danh sách đen, và
            # danh sách đen luôn thiếu một dòng.
            errors.append(_err(path, 'thẻ <%s> không được mang thuộc tính (thấy: %s)'
                               % (t, duoi.strip()[:60])))


def loi_html(chuoi, ten_truong):
    """Trả danh sách lỗi HTML của MỘT chuỗi. Cửa dùng chung cho mọi đường ghi.

    Bộ lọc này ra đời cho nội dung bài học, nhưng bài toán thì giống hệt ở mọi
    trường chữ do người dùng nhập rồi được đổ vào `innerHTML`. Mở ra để
    `courseadmin` dùng lại — chép sang một bản thứ hai là cách chắc chắn để hai
    danh sách trắng trôi khỏi nhau.
    """
    e = []
    _kiem_html(chuoi, ten_truong, e)
    return e


def _duyet_chuoi(o, path, errors):
    """Đi hết mọi chuỗi trong nội dung bài rồi soi HTML của từng chuỗi.

    Duyệt TOÀN BỘ chứ không chỉ hai trường đang được đổ vào `innerHTML`: chỗ
    hiển thị có thể mọc thêm (bản in, ứng dụng di động), và lúc ấy không ai nhớ
    quay lại nới bộ lọc. Chặn ở đường GHI thì chỉ phải đúng một lần.
    """
    if isinstance(o, str):
        _kiem_html(o, path, errors)
    elif isinstance(o, dict):
        for k, v in o.items():
            _duyet_chuoi(v, f'{path}.{k}', errors)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            _duyet_chuoi(v, f'{path}[{i}]', errors)


def _err(path, msg):
    return f'{path}: {msg}'


def validate_lesson(obj, path='bài'):
    """Trả về danh sách lỗi (rỗng = hợp lệ). Thông báo bằng tiếng Việt, nêu rõ
    đường dẫn tới chỗ sai để người soạn sửa được ngay."""
    errors = []
    if not isinstance(obj, dict):
        return [_err(path, 'phải là một object JSON')]

    # HTML trước tiên: một thẻ <script> lọt qua thì mọi phép kiểm cấu trúc phía
    # dưới có đúng cũng không cứu được ai.
    _duyet_chuoi(obj, path, errors)

    for key in REQUIRED:
        if key not in obj or obj[key] in (None, '', [], {}):
            errors.append(_err(path, f'thiếu trường bắt buộc "{key}"'))

    idx = obj.get('index')
    if idx is not None and (not isinstance(idx, int) or idx < 1):
        errors.append(_err(path, '"index" phải là số nguyên ≥ 1'))

    xp = obj.get('xp_reward')
    if xp is not None and (not isinstance(xp, int) or not 0 <= xp <= 500):
        errors.append(_err(path, '"xp_reward" phải là số nguyên trong khoảng 0–500'))

    test = obj.get('test')
    if isinstance(test, dict):
        qs = test.get('questions')
        if not isinstance(qs, list) or not qs:
            errors.append(_err(path + '.test', '"questions" phải là mảng có ít nhất 1 câu'))
        else:
            for i, qq in enumerate(qs, 1):
                p = f'{path}.test.questions[{i}]'
                if not isinstance(qq, dict):
                    errors.append(_err(p, 'phải là object')); continue
                if not qq.get('question'):
                    errors.append(_err(p, 'thiếu "question"'))
                if qq.get('answer') in (None, ''):
                    errors.append(_err(p, 'thiếu "answer"'))
                qtype = qq.get('type', 'mcq')
                if qtype == 'mcq':
                    opts = qq.get('options')
                    if not isinstance(opts, list) or len(opts) < 2:
                        errors.append(_err(p, 'câu trắc nghiệm cần "options" từ 2 lựa chọn trở lên'))
                    elif qq.get('answer') not in opts:
                        errors.append(_err(p, '"answer" phải nằm trong "options"'))
    elif test is not None:
        errors.append(_err(path + '.test', 'phải là object'))

    theory = obj.get('theory')
    if isinstance(theory, dict):
        # Engine chọn condensed hay full theo kết quả kiểm tra đầu vào; thiếu cả
        # hai thì bước Lý thuyết hiện trắng.
        if not theory.get('condensed') and not theory.get('full'):
            errors.append(_err(path + '.theory', 'cần ít nhất một trong "condensed" hoặc "full"'))
        for variant in ('condensed', 'full'):
            v = theory.get(variant)
            if v is None:
                continue
            if not isinstance(v, dict):
                errors.append(_err(f'{path}.theory.{variant}', 'phải là object')); continue
            if not isinstance(v.get('cards'), list) or not v.get('cards'):
                errors.append(_err(f'{path}.theory.{variant}', '"cards" phải là mảng có ít nhất 1 thẻ'))
    elif theory is not None:
        errors.append(_err(path + '.theory', 'phải là object'))

    # ── Phòng luyện tốc độ ──────────────────────────────────────────────────
    # Trước 31/08/2026 khối này KHÔNG được kiểm một chữ nào, dù XP phòng luyện
    # (tối đa 120, gấp 2,4 lần phần thưởng cả bài) và một trong bốn nguồn của
    # bản đồ năng lực đều dựng từ nó. Ba thứ dưới đây là ba cách nó hỏng câm:
    #
    #   · thiếu `id`   → `grading.dap_an` lọc câu đó ra khỏi bảng đáp án; thiếu
    #     hết thì bảng rỗng, mọi câu hiện "Chưa chấm được câu này — vẫn tính khi
    #     bạn hoàn thành bài", và câu an ủi ấy là nói dối vì lúc hoàn thành cũng
    #     không có gì để tính.
    #   · `id` TRÙNG   → dict đáp án giữ câu SAU, `max_score` ngắn đi; phía
    #     trình duyệt `drill.answers[q.id]` cũng ghi đè câu trước.
    #   · sai tên khoá thời lượng → `remaining` là `undefined`, `NaN <= 0` luôn
    #     sai nên đồng hồ CHẠY MÃI. Mẫu nhập chính thức từng ghi `seconds`
    #     trong khi engine đọc `time_seconds`.
    drill = obj.get('drill')
    if isinstance(drill, dict):
        cau = drill.get('questions')
        if not isinstance(cau, list) or not cau:
            errors.append(_err(path + '.drill', '"questions" phải là mảng có ít nhất 1 câu'))
        else:
            da_thay = set()
            for i, c in enumerate(cau, 1):
                pd = f'{path}.drill.questions[{i}]'
                if not isinstance(c, dict):
                    errors.append(_err(pd, 'phải là object')); continue
                cid = c.get('id')
                if not cid:
                    errors.append(_err(pd, 'thiếu "id" — thiếu nó thì câu này không chấm được'))
                elif cid in da_thay:
                    errors.append(_err(pd, f'"id" trùng với câu trước ("{cid}")'))
                else:
                    da_thay.add(cid)
                if c.get('answer') in (None, ''):
                    errors.append(_err(pd, 'thiếu "answer"'))
                if not str(c.get('question') or '').strip():
                    errors.append(_err(pd, 'thiếu "question"'))
                if c.get('type', 'mcq') == 'mcq' and not isinstance(c.get('options'), list):
                    errors.append(_err(pd, 'câu trắc nghiệm cần "options" là mảng'))
        if 'seconds' in drill and 'time_seconds' not in drill:
            errors.append(_err(path + '.drill',
                               'dùng "time_seconds" chứ không phải "seconds" — '
                               'sai tên thì đồng hồ phòng luyện chạy mãi không hết giờ'))
        ts = drill.get('time_seconds')
        if ts is not None and (not isinstance(ts, int) or not 5 <= ts <= 3600):
            errors.append(_err(path + '.drill', '"time_seconds" phải là số nguyên 5–3600'))
    elif drill is not None:
        errors.append(_err(path + '.drill', 'phải là object'))

    try:
        size = len(json.dumps(obj, ensure_ascii=False).encode('utf-8'))
        if size > MAX_LESSON_BYTES:
            errors.append(_err(path, f'nội dung quá lớn ({size:,} byte, tối đa {MAX_LESSON_BYTES:,})'))
    except (TypeError, ValueError):
        errors.append(_err(path, 'không chuyển được sang JSON (có giá trị không hợp lệ)'))

    return errors


def course_content(course_id):
    """Nội dung mọi bài CÓ content_json của một khoá, sắp theo index.

    Bài chưa soạn trong DB không xuất hiện ở đây — engine tự lấy bản trong file
    JS cho những bài đó.
    """
    rows = q("SELECT sort_order, content_json FROM lessons "
             "WHERE course_id=%s AND content_json IS NOT NULL "
             "ORDER BY sort_order", (course_id,))
    out = []
    for r in rows:
        data = r['content_json']
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                continue
        if not isinstance(data, dict):
            continue
        # sort_order là nguồn thứ tự thật; index trong JSON chỉ để hiển thị.
        data.setdefault('index', r['sort_order'])
        # CẮT ĐÁP ÁN. Cắt ở đây chứ không ở view: hai đường đọc nội dung
        # (`course_content` và `one_lesson`) đều đi qua tệp này, và một endpoint
        # mới quên cắt là lộ lại toàn bộ. Xem `lessons/grading.py`.
        out.append(bo_dap_an(data))
    return out


def one_lesson(course_id, index):
    """Nội dung ĐÚNG MỘT bài + tổng số bài của khoá.

    Trang bài học trước đây nạp cả 76 bài (87 kB nén / 440 kB gốc) chỉ để hiển
    thị một bài. Đọc lẻ từng bài cắt gần hết phần đó.
    """
    row = q1("SELECT content_json FROM lessons "
             "WHERE course_id=%s AND sort_order=%s AND content_json IS NOT NULL",
             (course_id, index))
    total = (q1("SELECT COUNT(*) AS n FROM lessons "
                "WHERE course_id=%s AND content_json IS NOT NULL", (course_id,)) or {}).get('n', 0)
    if not row:
        return None, total
    data = row['content_json']
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except ValueError:
            return None, total
    if not isinstance(data, dict):
        return None, total
    data.setdefault('index', index)
    return bo_dap_an(data), total
