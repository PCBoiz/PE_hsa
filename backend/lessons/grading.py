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

from common.db import q1, x

#: Các phần có câu hỏi trong `content_json`. Khớp `lessons/content.py`.
PHAN_CO_CAU_HOI = ('test', 'drill')

#: Trường bị cắt trước khi nội dung rời máy chủ.
TRUONG_BI_MAT = ('answer', 'explain')

#: Trần cho một bộ câu trả lời gửi lên. Bài dài nhất hiện có 8 câu drill và
#: vài câu kiểm tra; 200 khoá là rộng gấp hơn mười lần.
#:
#: VÌ SAO PHẢI CÓ. `ghi_nhan` GỘP THÊM chứ không thay thế (luật lần-đầu-thắng
#: chỉ giữ khoá đã có, khoá mới luôn được nhận), nên không trần thì mỗi request
#: nạp thêm tới 2,5 MB khoá rác vào ĐÚNG MỘT dòng `lesson_progress`. Sau vài
#: chục lượt, mỗi lần chấm kéo cả trăm MB từ Neon về rồi giải mã JSON trong tiến
#: trình — một tài khoản học viên đủ giết một worker 512 MB của Render.
MAX_CAU_TRA_LOI = 200
#: Trần độ dài một câu trả lời. Đáp án dài nhất trong nội dung thật là một chuỗi
#: tiền tệ ngắn; 500 ký tự là rộng thừa.
MAX_DAI_TRA_LOI = 500

_KEY = 'dapan:{}:{}'
_KEY_ID = 'baiid:{}:{}'
_KEY_GIAY = 'drillgiay:{}:{}'
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


def id_bai(course_id, lesson_no):
    """`lessons.id` của một bài, có đệm 60 giây. `None` nếu không có bài đó.

    CÓ ĐỆM vì phòng luyện gọi `/check` MỖI CÂU, và mỗi lượt tới Neon tốn ~270ms
    thuần đường truyền. Đo 31/08/2026 khi mới thêm việc ghi nhận câu trả lời:
    ba câu SQL mỗi lời gọi → **810ms mỗi câu drill**, trong một trò bấm giờ 75
    giây cho 8 câu. Bỏ đệm này là trả lại 270ms ấy cho mỗi câu.

    Cùng đệm và cùng vòng đời với `dap_an`: `quen_dap_an` xoá cả hai.
    """
    key = _KEY_ID.format(course_id, lesson_no)
    ra = cache.get(key)
    if ra is not None:
        return ra or None
    row = q1('SELECT id FROM lessons WHERE course_id=%s AND sort_order=%s LIMIT 1',
             (course_id, lesson_no))
    ra = (row or {}).get('id') or 0
    cache.set(key, ra, _TTL)
    return ra or None


def gioi_han_giay_drill(course_id, lesson_no):
    """Trần đồng hồ của phòng luyện, tính bằng GIÂY, **theo giáo trình**.

    Trả ``None`` khi bài không có phòng luyện hoặc không khai ``time_seconds``.

    VÌ SAO CẦN (vá 04/09/2026). `_cham_drill` nhận `drill.seconds` từ THÂN
    REQUEST rồi đổi ra phút và ghi vào ``learning_events.minutes`` với
    ``source = 'system'``. Mà `stats/gradebook.py` tách hai xô ``minutes`` và
    ``selfMinutes`` đúng theo cột ``source`` ấy — toàn bộ ý nghĩa của phép tách
    là "cái này máy đo, cái kia học viên tự khai". Con số học viên khai đang
    nằm trong xô của máy.

    Đo mức thổi phồng: trần cũ là ``min(120, …)`` PHÚT cho một bài luyện 75
    GIÂY. Tức khai được 120 phút mỗi bài, và `dedup_key` cho một lượt mỗi bài
    × 76 bài = **152 giờ tự học giả**, hiện thẳng trong bảng giảng viên đọc và
    trong báo cáo gửi phụ huynh.

    Trần thật thì máy chủ BIẾT: `time_seconds` nằm trong giáo trình và
    `lessons/content.py` bắt buộc nó là số nguyên 5–3600. Kẹp về trần ấy thì
    client chỉ khai được ÍT hơn sự thật, không nhiều hơn — mà khai ít thì không
    đổi được gì có lợi cho ai.

    Ba chú thích ngay trong `_cham_drill` đã nói vì sao không tin số client khai
    (`correct`, `maxCombo`, `da_lam` đều dựng lại ở máy chủ). `seconds` lọt qua
    vì nó trông như một con số vô hại.
    """
    key = _KEY_GIAY.format(course_id, lesson_no)
    ra = cache.get(key)
    if ra is not None:
        # `-1` là "đã tra, bài này KHÔNG có trần". Phải phân biệt với đệm trượt,
        # nếu không thì mỗi lần chấm một bài không có drill lại tra CSDL lại.
        return None if ra == -1 else ra
    data = _noi_dung(course_id, lesson_no) or {}
    drill = data.get('drill')
    ts = drill.get('time_seconds') if isinstance(drill, dict) else None
    ra = (int(ts) if isinstance(ts, (int, float)) and not isinstance(ts, bool)
          and 0 < ts <= 3600 else None)
    cache.set(key, -1 if ra is None else ra, _TTL)
    return ra


def quen_dap_an(course_id, lesson_no):
    """Xoá đệm khi nội dung bài vừa được sửa. Gọi từ đường soạn bài."""
    cache.delete(_KEY.format(course_id, lesson_no))
    cache.delete(_KEY_ID.format(course_id, lesson_no))
    # Trần đồng hồ nằm TRONG nội dung bài, nên sửa bài là nó đổi được. Quên
    # dòng này thì trần cũ còn sống thêm 60 giây sau khi người soạn đã đổi.
    cache.delete(_KEY_GIAY.format(course_id, lesson_no))


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


def kep_tra_loi(tra_loi):
    """Kẹp một bộ câu trả lời về kích thước dùng được. Trả (bộ đã kẹp, có_cắt).

    Cắt lặng lẽ chứ không từ chối cả request: một engine cũ hay một bài dài bất
    thường không đáng làm học viên mất bài. Nhưng phải BÁO ra để nơi gọi ghi
    nhật ký — nếu chuyện này xảy ra thật thì hoặc có bài dài quá dự kiến, hoặc
    có người đang thử phá.
    """
    if not isinstance(tra_loi, dict):
        return {}, False
    ra, cat = {}, False
    for k, v in tra_loi.items():
        if len(ra) >= MAX_CAU_TRA_LOI:
            cat = True
            break
        khoa = str(k)[:64]
        if v is None:
            ra[khoa] = None
            continue
        gia_tri = str(v)
        if len(gia_tri) > MAX_DAI_TRA_LOI:
            gia_tri, cat = gia_tri[:MAX_DAI_TRA_LOI], True
        ra[khoa] = gia_tri
    if len(tra_loi) > MAX_CAU_TRA_LOI:
        cat = True
    return ra, cat


def ghi_nhan(uid, lesson_id, phan, tra_loi):
    """GHI NHẬN câu trả lời cho một phần. LẦN ĐẦU THẮNG. Trả lại bộ đã chốt.

    Đây là mảnh còn thiếu của luật "điểm được TÍNH, không được NHẬN". Chấm ở máy
    chủ mới chỉ bỏ được con số client tự khai; chừng nào `/complete` còn chấm
    trên CÂU TRẢ LỜI TRONG THÂN REQUEST thì cả bản vá vẫn đi vòng được bằng hai
    lời gọi: `/check` với đáp án bừa để moi bảng đáp án, rồi `/complete` với bộ
    đáp án vừa lấy.

    LẦN ĐẦU THẮNG là toàn bộ ý nghĩa của hàm này: một câu chỉ được trả lời một
    lần trong một lượt học. Ai xem đáp án bằng cách gửi bừa thì con số bừa ấy
    chính là bài làm của họ.

    Dòng `lesson_progress` được tạo nếu chưa có, với `status='in_progress'` — mọi
    bên đọc tiến độ đều lọc `status='completed'` nên dòng ấy vô hình với chúng.
    """
    if not isinstance(tra_loi, dict) or not tra_loi:
        return _da_ghi_nhan(uid, lesson_id).get(phan, {})
    tra_loi, _cat = kep_tra_loi(tra_loi)
    if not tra_loi:
        return _da_ghi_nhan(uid, lesson_id).get(phan, {})
    moi = json.dumps({phan: tra_loi}, ensure_ascii=False)
    # `||` của jsonb là gộp NÔNG: bên phải thắng ở cấp khoá thứ nhất. Muốn "lần
    # đầu thắng" ở cấp CÂU thì phải đặt bộ MỚI bên trái và bộ CŨ bên phải trong
    # phép gộp con, rồi mới gán lại vào khoá `phan`.
    #
    # `RETURNING` chứ không SELECT lại: phòng luyện gọi đường này mỗi câu, và
    # mỗi lượt tới Neon tốn ~270ms thuần đường truyền.
    # `course_id` PHẢI được điền ngay ở câu chèn này. Trước 01/09/2026 đường
    # DUY NHẤT tạo dòng `lesson_progress` là `CompleteLessonView`, và nó luôn
    # điền cột ấy. Từ khi `/check` ghi nhận câu trả lời, đường này chèn TRƯỚC —
    # nên nếu để trống thì lần chèn đầu không có `course_id`, mọi lần sau rơi
    # vào `DO UPDATE` (không đụng cột ấy), và cột ở NULL VĨNH VIỄN.
    #
    # Bảy chỗ đọc lọc/gộp theo `lp.course_id`: tính lại `enrollments` ngay sau
    # khi hoàn thành bài (→ tiến độ đứng ở 0%), XP theo khoá, dải tiến độ ba hợp
    # phần, báo cáo lớp của giảng viên, và lệnh nạp lại dòng sự kiện. Đáng sợ
    # hơn cả: `learning_events` KHÔNG hỏng, nên bản đồ năng lực vẫn đúng — hai
    # màn hình cùng nói về một em sẽ lệch nhau mà không ai biết vì sao.
    row = q1('''INSERT INTO lesson_progress (user_id, lesson_id, course_id, status, answers_json)
                VALUES (%s, %s, (SELECT course_id FROM lessons WHERE id = %s),
                        'in_progress', %s::jsonb)
                ON CONFLICT (user_id, lesson_id) DO UPDATE SET
                    answers_json = COALESCE(lesson_progress.answers_json, '{}'::jsonb)
                        || jsonb_build_object(
                               %s,
                               (%s::jsonb -> %s)
                               || COALESCE(lesson_progress.answers_json -> %s, '{}'::jsonb))
                RETURNING answers_json''',
             (uid, lesson_id, lesson_id, moi, phan, moi, phan, phan))
    return _tach(row).get(phan, {})


def _tach(row):
    a = (row or {}).get('answers_json')
    if isinstance(a, str):
        try:
            a = json.loads(a)
        except ValueError:
            return {}
    return a if isinstance(a, dict) else {}


def _da_ghi_nhan(uid, lesson_id):
    return _tach(q1('SELECT answers_json FROM lesson_progress '
                    'WHERE user_id=%s AND lesson_id=%s', (uid, lesson_id)))


def doc_ghi_nhan(uid, lesson_id, phan):
    """Bộ câu trả lời ĐÃ CHỐT của một phần. `{}` nếu chưa ghi nhận câu nào."""
    ra = _da_ghi_nhan(uid, lesson_id).get(phan)
    return ra if isinstance(ra, dict) else {}


def xoa_ghi_nhan_phan(uid, lesson_id, phan):
    """Xoá phần đã ghi nhận của MỘT phần — dùng khi phòng luyện bắt đầu lại.

    VÌ SAO PHÒNG LUYỆN ĐƯỢC LÀM LẠI MÀ BÀI KIỂM TRA ĐẦU VÀO THÌ KHÔNG. Bài kiểm
    tra đầu vào có đúng một lượt: nó quyết định nhánh lý thuyết và điểm vào sổ,
    và `/check` của nó TRẢ ĐÁP ÁN cho phần xem lại — nên khoá lần đầu là thứ duy
    nhất ngăn "gửi bừa để moi đáp án rồi gửi lại bộ đúng".

    Phòng luyện thì nút "Bắt đầu" vốn là nút LÀM LẠI, và `/check` của nó chỉ trả
    đúng/sai chứ không trả đáp án. Không xoá thì lần luyện thứ hai hỏng hẳn: em
    bấm một lựa chọn khác mà màn hình vẫn tô theo câu trả lời lần trước — đo
    được đúng vậy trong trình duyệt 31/08/2026 (5/8 thay vì 6/8 vì một câu bị
    khoá bằng đáp án sai của lần bỏ dở).

    RỦI RO CÒN LẠI, nói thẳng: xoá được thì cũng dò được — trả lời, xem đúng/sai,
    bắt đầu lại, trả lời khác. Với câu trắc nghiệm 4 lựa chọn thì việc ấy rẻ.
    Cái chặn nó là XP chỉ cộng ở LẦN HOÀN THÀNH ĐẦU của bài (`existed` trong
    `CompleteLessonView`). Chưa đủ kín cho bản đồ năng lực — xem TODO A18.
    """
    x("""UPDATE lesson_progress
            SET answers_json = COALESCE(answers_json, '{}'::jsonb) - %s
          WHERE user_id=%s AND lesson_id=%s""", (phan, uid, lesson_id))


def xoa_ghi_nhan(uid, lesson_id):
    """Xoá phần đã ghi nhận — gọi khi `/complete` chấm xong.

    Để lần học lại bài đó bắt đầu từ giấy trắng: bài đã hoàn thành rồi thì câu
    trả lời cũ không còn việc gì để làm, mà giữ lại thì em ôn lại sẽ bị kẹt với
    đúng những câu đã trả lời hôm trước.
    """
    x('UPDATE lesson_progress SET answers_json = NULL '
      'WHERE user_id=%s AND lesson_id=%s', (uid, lesson_id))
