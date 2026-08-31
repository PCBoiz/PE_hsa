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

from common.db import q, q1
from lessons.grading import bo_dap_an

#: Trường bắt buộc — thiếu một trong số này thì engine sẽ hỏng giữa chừng.
REQUIRED = ('id', 'index', 'title', 'test', 'theory')
#: Trần độ dài để một lần nhập sai không nhét cả cuốn sách vào DB.
MAX_LESSON_BYTES = 400_000


def _err(path, msg):
    return f'{path}: {msg}'


def validate_lesson(obj, path='bài'):
    """Trả về danh sách lỗi (rỗng = hợp lệ). Thông báo bằng tiếng Việt, nêu rõ
    đường dẫn tới chỗ sai để người soạn sửa được ngay."""
    errors = []
    if not isinstance(obj, dict):
        return [_err(path, 'phải là một object JSON')]

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
