"""Chấm bài ở MÁY CHỦ — nơi duy nhất biết đáp án đúng.

VÌ SAO TỆP NÀY RA ĐỜI. Đo ngày 31/08/2026, trong trình duyệt thật, ngay khi
trang bài học vừa mở và TRƯỚC khi bấm gì:

    GET /api/courses/hsa_quantitative/content   → 200, 129 843 byte
    số trường "answer" trong phản hồi: 297      (toàn bộ đáp án của cả khoá)

Và điểm thì do chính trình duyệt tự chấm rồi tự khai:

    POST /api/lessons/9999/complete {"quizScore": 999999}  → 200
    lesson_progress: quiz_score = 999999

Nghĩa là con số nuôi bản đồ năng lực, sổ điểm của giảng viên và nhánh lý thuyết
thích ứng là con số HỌC VIÊN TỰ KHAI, và đáp án thì mở DevTools là thấy — kể cả
bài chưa mở khoá, khoá chưa ghi danh. Toàn bộ hệ đo lường của trung tâm không có
giá trị chứng cứ.

BA LUẬT CỦA TỆP NÀY
  1. Đáp án KHÔNG rời máy chủ trước khi học viên trả lời. `bo_dap_an` cắt
     `answer`/`explain` khỏi mọi nội dung gửi xuống.
  2. Điểm được TÍNH, không được NHẬN. Mọi con số vào CSDL đi ra từ `cham`, lấy
     đáp án từ CSDL chứ không từ thân request.
  3. Đáp án đúng chỉ được tiết lộ SAU khi đã nhận câu trả lời cho đúng câu đó.

ĐỆM 60 GIÂY. Phòng luyện chấm từng câu một, tức mỗi câu một lượt tới Neon (~250ms
từ VN) giữa một trò chơi bấm giờ. Bộ đệm biến lượt thứ hai trở đi thành gần như
tức thì. 60 giây là đủ cho một lượt học và đủ ngắn để soạn lại bài không phải
chờ lâu — cùng con số và cùng lý lẽ với `accounts/authentication.py`.
"""
import json
import re
import unicodedata

from django.core.cache import cache

from common.db import q1

#: Các phần có câu hỏi trong `content_json`. Khớp `lessons/content.py`.
PHAN_CO_CAU_HOI = ('test', 'drill')

#: Trường bị cắt trước khi nội dung rời máy chủ.
TRUONG_BI_MAT = ('answer', 'explain')

_KEY = 'dapan:{}:{}'
_TTL = 60


def _chuan(s):
    """Chuẩn hoá một câu trả lời để so sánh.

    Giữ ĐÚNG luật mà engine dùng suốt từ đầu (`norm` trong `lesson_hsa.js`):
    không phân biệt hoa thường, **bỏ hết khoảng trắng**, **bỏ hết dấu `%`**.
    Thêm một thứ engine không làm được: chuẩn hoá Unicode NFC — "đ" gõ bằng bàn
    phím Telex và "đ" dán từ Word là hai chuỗi byte khác nhau nhưng cùng một chữ.

    BỎ `%` KHÔNG PHẢI CHUYỆN NHỎ. Bản đầu ngày 31/08/2026 của hàm này chỉ gộp
    khoảng trắng và GIỮ `%`, kèm một chú thích tự nhận là "giữ đúng luật engine"
    trong khi làm ngược lại. Đo trên nội dung thật: 151 câu dạng điền, trong đó
    **14 câu hỏi "bao nhiêu %" mà đáp án lưu là số trần** — ví dụ *"A = 30,
    B = 70. A chiếm bao nhiêu % tổng? (nhập số)"* với đáp án `"30"`. Em gõ
    `30%` thì trước hôm ấy là ĐÚNG, sau đó thành SAI. Cùng lỗi với `x = 3` gõ
    thành `x=3`.

    KHÔNG bỏ dấu tiếng Việt và KHÔNG bỏ dấu chấm phân cách nghìn: "300.000đ" và
    "300000d" là hai câu trả lời khác nhau — và `norm` cũ cũng không bỏ chúng.
    """
    if s is None:
        return ''
    s = unicodedata.normalize('NFC', str(s)).lower()
    return re.sub(r'\s+', '', s).replace('%', '')


def _noi_dung(course_id, lesson_no):
    """`content_json` của một bài, dạng dict. None nếu không có."""
    row = q1('SELECT content_json FROM lessons '
             'WHERE course_id=%s AND sort_order=%s AND content_json IS NOT NULL',
             (course_id, lesson_no))
    if not row:
        return None
    data = row['content_json']
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except ValueError:
            return None
    return data if isinstance(data, dict) else None


def dap_an(course_id, lesson_no):
    """Bảng đáp án của một bài: ``{phan: {id_cau: {answer, explain}}}``.

    Trả `{}` khi bài không tồn tại — bên gọi phân biệt bằng cách kiểm rỗng, và
    `cham` sẽ từ chối chứ không chấm bừa 0 điểm.
    """
    key = _KEY.format(course_id, lesson_no)
    ra = cache.get(key)
    if ra is not None:
        return ra
    data = _noi_dung(course_id, lesson_no)
    ra = {}
    if data:
        for phan in PHAN_CO_CAU_HOI:
            khoi = data.get(phan)
            cau = khoi.get('questions') if isinstance(khoi, dict) else khoi
            if not isinstance(cau, list):
                continue
            ra[phan] = {
                str(c.get('id')): {'answer': c.get('answer'), 'explain': c.get('explain')}
                for c in cau if isinstance(c, dict) and c.get('id') is not None
            }
    cache.set(key, ra, _TTL)
    return ra


def quen_dap_an(course_id, lesson_no):
    """Xoá đệm khi nội dung bài vừa được sửa. Gọi từ đường soạn bài."""
    cache.delete(_KEY.format(course_id, lesson_no))


def bo_dap_an(data):
    """Cắt `answer`/`explain` khỏi nội dung một bài, TẠI CHỖ. Trả lại chính nó.

    Cắt ở đây, không ở từng view: một endpoint mới quên cắt là lộ lại toàn bộ.
    Ba đường hiện có (`CourseContentView`, `one_lesson`, `all_lessons`) đều đi
    qua hàm này.
    """
    if not isinstance(data, dict):
        return data
    for phan in PHAN_CO_CAU_HOI:
        khoi = data.get(phan)
        cau = khoi.get('questions') if isinstance(khoi, dict) else khoi
        if not isinstance(cau, list):
            continue
        for c in cau:
            if isinstance(c, dict):
                for t in TRUONG_BI_MAT:
                    c.pop(t, None)
    return data


def cham(course_id, lesson_no, phan, tra_loi):
    """Chấm một tập câu trả lời. Trả ``(ket_qua, tong_dung, tong_cau)``.

    ``tra_loi`` là dict ``{id_cau: cau_tra_loi}``. ``ket_qua`` là dict
    ``{id_cau: {'correct': bool, 'answer': ..., 'explain': ...}}``.

    Đáp án đúng CHỈ nằm trong kết quả của những câu ĐÃ NHẬN được câu trả lời —
    gửi lên một dict rỗng thì không moi được gì. Đây là điều kiện để endpoint
    chấm không trở thành cửa sau thay cho lỗ vừa bịt.

    ``tong_cau`` là số câu trong ĐỀ, không phải số câu đã trả lời: bỏ trống một
    câu vẫn là sai, không phải là không tính.

    Trả ``(None, 0, 0)`` khi bài hoặc phần không tồn tại — KHÔNG trả 0 điểm, vì
    "không tìm thấy đề" và "làm sai hết" là hai chuyện khác nhau.
    """
    bang = dap_an(course_id, lesson_no).get(phan)
    if not bang:
        return None, 0, 0
    if not isinstance(tra_loi, dict):
        tra_loi = {}
    ket_qua = {}
    dung = 0
    for cid, khoa in bang.items():
        if cid not in tra_loi:
            continue
        ok = _chuan(tra_loi[cid]) == _chuan(khoa['answer'])
        if ok:
            dung += 1
        ket_qua[cid] = {'correct': ok, 'answer': khoa['answer'],
                        'explain': khoa.get('explain')}
    return ket_qua, dung, len(bang)


def phan_tram(dung, tong):
    """Điểm phần trăm 0–100. Đề rỗng → None, KHÔNG phải 0."""
    if not tong:
        return None
    return max(0, min(100, round(dung * 100 / tong)))


def cham_phong_luyen(course_id, lesson_no, tra_loi):
    """Chấm phòng luyện tốc độ. Trả ``(dung, tong, combo_dai_nhat)``.

    Trả ``None`` khi bài hoặc phần `drill` không tồn tại — cùng luật với `cham`.

    VÌ SAO CHUỖI COMBO TÍNH Ở ĐÂY. Combo là số câu ĐÚNG LIÊN TIẾP, nên muốn tính
    nó phải biết THỨ TỰ câu trong đề — thứ chỉ bảng đáp án mới giữ. Trước
    31/08/2026 con số này do trình duyệt tự đếm rồi tự khai, mà nó đáng 5 XP mỗi
    nấc; nay máy chủ dựng lại từ chính các câu trả lời nhận được.

    Câu bỏ trống ĐỨT chuỗi và tính là sai: hết giờ mà chưa kịp làm cũng là một
    kết quả trong bài luyện tính giờ, và đó chính là thứ phòng luyện đo.
    """
    bang = dap_an(course_id, lesson_no).get('drill')
    if not bang:
        return None
    if not isinstance(tra_loi, dict):
        tra_loi = {}
    dung = combo = dai_nhat = 0
    for cid, khoa in bang.items():
        if cid in tra_loi and _chuan(tra_loi[cid]) == _chuan(khoa['answer']):
            dung += 1
            combo += 1
            if combo > dai_nhat:
                dai_nhat = combo
        else:
            combo = 0
    return dung, len(bang), dai_nhat
