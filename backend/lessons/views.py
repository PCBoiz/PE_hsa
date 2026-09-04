"""Port routes/lessons.py — API tiến độ bài học (nguồn thật: lesson_progress)."""
import logging

from django.core.cache import cache
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from achievements.services import check_and_award_achievements
from common.clock import local_now, local_today
from common.db import q1, x
from common.events import KIND_DRILL, KIND_LESSON, SOURCE_SELF, SOURCE_SYSTEM, record_event
from common.streak import award_xp, touch_streak
from common.throttling import (
    DailyIPThrottle,
    DailyUserThrottle,
    HourlyIPThrottle,
    HourlyUserThrottle,
)
from courses.enrollment import tinh_lai as tinh_lai_ghi_danh
from lessons.content import course_content, one_lesson
from lessons.grading import (
    PHAN_CO_CAU_HOI,
    cham,
    cham_phong_luyen,
    dap_an,
    doc_ghi_nhan,
    ghi_nhan,
    gioi_han_giay_drill,
    id_bai,
    phan_tram,
    xoa_ghi_nhan,
    xoa_ghi_nhan_phan,
)

logger = logging.getLogger(__name__)


def _tim_bai(course_id, lesson_no):
    """Tra bài theo (course_id, sort_order). CHỈ ĐỌC — không tạo dòng nào.

    Trả ``(lesson_id, module, title, xp_reward)``, hoặc ``(None, …)`` nếu không
    có bài đó. Trả kèm module vì dòng sự kiện học tập cần chủ đề của bài để chấm
    năng lực; trả kèm title và xp_reward vì cả hai phải lấy từ MÁY CHỦ.

    KHÔNG CÒN TẠO STUB (L5, 31/08/2026). Bản cũ, khi không tìm thấy bài, sẽ
    INSERT một dòng vào bảng ``lessons`` với `title`/`module` **lấy từ thân
    request của học viên** và `sort_order` lấy từ URL. Bảng ``lessons`` là bảng
    DÙNG CHUNG, và `SkillsView` đọc nó không lọc theo người dùng — nên một dòng
    giả do một học viên tạo hiện trong trang Kỹ năng của MỌI học viên. Đo được
    một dòng ``"<b>BAI GIA MAO</b>"`` với ``sort_order 9999``.

    Nhánh tạo stub ấy sinh ra thời nội dung bài còn nằm trong tệp JS 364 kB phía
    client, khi bảng ``lessons`` thật sự chỉ là chỗ giữ khoá ngoại. Nay đo trên
    dữ liệu thật: **cả 76 bài của ba khoá đều đã có ``content_json``**, không
    còn dòng stub nào, và bản dự phòng phía client đã bỏ từ 19/08/2026. Bài học
    viên học được thì luôn có dòng sẵn; nhánh ấy chỉ còn là cái lỗ.
    """
    row = q1("SELECT id, module, title, (content_json->>'xp_reward') AS xp "
             "FROM lessons WHERE course_id=%s AND sort_order=%s LIMIT 1",
             (course_id, lesson_no))
    if not row:
        return None, None, None, None
    try:
        xp = int(row['xp'])
    except (TypeError, ValueError):
        xp = None
    return row['id'], (row.get('module') or None), (row.get('title') or ''), xp


#: Thưởng phòng luyện. Trước 31/08/2026 hai con số này chỉ tồn tại trong
#: `lesson_hsa.js` và kết quả do trình duyệt tự khai; nay máy chủ tự tính nên
#: chúng phải nằm ở đây. Giá trị giữ NGUYÊN như bản JS để không đổi phần thưởng
#: của học viên giữa chừng.
DRILL_XP_MOI_CAU_DUNG = 10
DRILL_XP_MOI_NAC_COMBO = 5


def _cham_drill(drill, course_id, lesson_no, uid, lesson_id):
    """Chấm phòng luyện Ở MÁY CHỦ. Trả dict kết quả, hoặc None nếu không chấm được.

    CHỈ ĐỌC, không ghi — để nơi gọi biết số XP trước khi cộng.

    Bản cũ nhận thẳng `correct` / `maxCombo` / `total` từ thân request rồi kẹp
    biên. Kẹp biên không cứu được gì ở đây: `{"correct": 8, "maxCombo": 8}` là
    một kết quả HỢP LỆ về mặt biên, đáng 120 XP, và nó nuôi cả bản đồ năng lực
    (`KIND_DRILL` nằm trong `stats/competency.KIND_TO_SOURCE`). Nay chỉ nhận CÂU
    TRẢ LỜI; số câu đúng và chuỗi combo do máy chủ dựng lại từ bảng đáp án.
    """
    # B15 · thân request chỉ là BẢN SAO LƯU, không phải điều kiện. Em làm đủ 8
    # câu (mỗi câu một `/check` đã ghi nhận) rồi TẢI LẠI TRANG trước khi bấm
    # Hoàn thành: `drill` phía client về `undefined`, thân gửi `"drill": null`,
    # và bản cũ trả `None` ngay — máy chủ có sẵn bài làm nhưng không dùng, rồi
    # `xoa_ghi_nhan` xoá luôn. Đúng cái mà A12 tuyên bố đã sửa.
    if not isinstance(drill, dict):
        drill = {}
    tra_loi = drill.get('answers')
    if not isinstance(tra_loi, dict):
        tra_loi = doc_ghi_nhan(uid, lesson_id, 'drill')
        if tra_loi:
            logger.info('[lessons] uid=%s bài %s/%s: thân request không có phần phòng '
                        'luyện — chấm trên %d câu đã ghi nhận qua /check',
                        uid, course_id, lesson_no, len(tra_loi))
    if not isinstance(tra_loi, dict) or not tra_loi:
        # Engine bản CŨ gửi `correct`/`maxCombo` tự khai. Không ghi gì cả: một
        # dòng năng lực dựng từ con số người dùng khai còn tệ hơn không có dòng
        # nào — cùng lý lẽ với `quizScore` ở `CompleteLessonView`.
        if drill.get('correct') is not None:
            logger.info('[lessons] bài %s/%s: engine bản CŨ gửi kết quả phòng luyện '
                        'tự khai (correct=%r) — BỎ QUA', course_id, lesson_no,
                        drill.get('correct'))
        return None
    # Cùng luật với bài kiểm tra: chấm trên phần ĐÃ GHI NHẬN qua `/check`,
    # thân request chỉ bù cho những câu chưa kịp qua đó.
    tra_loi = ghi_nhan(uid, lesson_id, 'drill', tra_loi)
    ket = cham_phong_luyen(course_id, lesson_no, tra_loi)
    if not ket:
        return None
    # LƯỢT ĐẦU VÀO SỔ (anh Sơn chốt 01/09/2026), cùng luật với thi thử. Lượt sau
    # vẫn được chấm và vẫn hiện kết quả để luyện, nhưng không cộng XP và không
    # ghi dòng năng lực — nếu không thì `reset` + `/check` là một máy dò đáp án
    # cho 120 XP và một ô năng lực 8/8.
    lan_dau = not _da_ghi_drill(uid, lesson_id)
    dung, tong, combo = ket
    try:
        # `OverflowError` phải nằm trong đây: `json.loads('{"seconds": 1e400}')`
        # cho `inf` — một số thực bình thường, không phải hằng `Infinity` nên
        # `STRICT_JSON` của DRF không chặn — và `int(inf)` ném `OverflowError`,
        # thứ không phải TypeError cũng không phải ValueError. Kết quả trước khi
        # thêm: 500, và học viên mất cả bài vừa học.
        seconds = int(drill.get('seconds') or 0)
    except (TypeError, ValueError, OverflowError):
        seconds = 0
    # KẸP VỀ TRẦN ĐỒNG HỒ CỦA CHÍNH BÀI ẤY (vá 04/09/2026).
    #
    # `seconds` là con số CLIENT KHAI, và nó đi thẳng vào
    # `learning_events.minutes` với `source='system'` — trong khi `gradebook.py`
    # tách hai xô `minutes` / `selfMinutes` đúng theo cột `source` ấy. Toàn bộ ý
    # nghĩa của phép tách là "cái này máy đo, cái kia học viên tự khai", và con
    # số học viên khai đang nằm trong xô của máy.
    #
    # Trần cũ `min(120, …)` là 120 PHÚT cho một bài luyện 75 GIÂY: khai được 120
    # phút mỗi bài × 76 bài = 152 giờ tự học giả, hiện trong bảng giảng viên đọc
    # và trong báo cáo gửi phụ huynh.
    #
    # Ba chú thích ngay trên đây đã nói vì sao không tin số client khai —
    # `correct`, `maxCombo`, `da_lam` đều dựng lại ở máy chủ. `seconds` lọt qua
    # vì nó trông như một con số vô hại.
    #
    # Không có trần trong giáo trình thì KHÔNG ghi phút nào: một ô trống đọc
    # được là "chưa đo", còn một con số bịa thì không ai biết là bịa.
    gioi_han = gioi_han_giay_drill(course_id, lesson_no)
    seconds = min(seconds, gioi_han) if gioi_han else 0
    return {
        'dung': dung, 'tong': tong, 'combo': combo,
        # Số câu KỊP làm = số câu thật sự nhận được, không phải con số client
        # khai. Trả lời rỗng không tính là đã làm. Kẹp về `tong`: gửi 500 khoá
        # rác cho một drill 4 câu thì "đã làm 500 / tổng 4" là một con số nói
        # dối nằm ngay trong bảng giảng viên đọc.
        'da_lam': min(tong, sum(1 for v in tra_loi.values()
                                if v is not None and str(v).strip() != '')),
        'phut': max(0, min(120, round(seconds / 60))) or None,
        'lan_dau': lan_dau,
        'xp': (dung * DRILL_XP_MOI_CAU_DUNG + combo * DRILL_XP_MOI_NAC_COMBO
               if lan_dau else 0),
    }


def _da_ghi_drill(uid, lesson_id):
    """Bài này đã có LƯỢT PHÒNG LUYỆN nào vào sổ chưa?

    Hỏi thẳng dòng sự kiện — `dedup_key = 'drill:<lesson_id>'` vốn đã là duy
    nhất cho mỗi (học viên, bài), nên không cần thêm cột nào để nhớ.
    """
    return bool(q1("SELECT 1 AS co FROM learning_events "
                   "WHERE user_id=%s AND dedup_key=%s LIMIT 1",
                   (uid, 'drill:%s' % lesson_id)))


def _chot_luot_drill(uid, lesson_id, course_id, lesson_no, topic=None):
    """Chốt lượt phòng luyện ĐANG DỞ vào sổ, nếu đây là lượt đầu của bài.

    Gọi từ đường `reset` — tức lúc học viên bấm "Bắt đầu" lại. Không có chỗ này
    thì "lượt đầu vào sổ" không đóng được máy dò đáp án: em cứ trả lời → xem
    đúng/sai → bấm Bắt đầu → thử khác, **không bao giờ gọi `/complete`**, cho
    tới khi biết hết đáp án; rồi mới làm một lượt sạch và lượt SẠCH ấy trở thành
    "lượt đầu". Chốt ngay lúc bỏ dở thì lượt dò CHÍNH LÀ lượt đầu.

    Cùng luật với thi thử anh Sơn đã chốt: mở đề là đã thấy đề.

    ── CHỦ ĐỀ PHẢI TỰ TRA (vá 04/09/2026) ─────────────────────────────────

    Đường `/check` gọi hàm này KHÔNG truyền `topic`, nên mọi lượt phòng luyện bỏ
    dở vào `learning_events` với `topic = NULL`. Mà `stats/competency.py` khoá
    bản đồ năng lực theo `(course_id, topic)` — một dòng không có chủ đề là một
    dòng VÔ HÌNH với bản đồ ấy.

    Tức lượt dò đáp án — thứ mà cả cơ chế "chốt lượt đang dở" sinh ra để bắt —
    được ghi vào sổ nhưng không đếm vào đâu cả. Nửa mục đích bị mất.

    `/check` không truyền được là ĐÚNG: nó chạy MỖI CÂU và cố ý dùng `id_bai`
    (một con số, có đệm 60 giây) thay vì `_tim_bai`. Nên tra ở ĐÂY, và tra SAU
    các cửa thoát sớm — nhánh này chỉ chạy đúng một lần cho mỗi bài, lúc học
    viên bấm "Bắt đầu" lại và thật sự có bài làm để chốt.
    """
    if _da_ghi_drill(uid, lesson_id):
        return
    da_chot = doc_ghi_nhan(uid, lesson_id, 'drill')
    if not da_chot:
        return                      # chưa trả lời câu nào thì không có gì để chốt
    ket = cham_phong_luyen(course_id, lesson_no, da_chot)
    if not ket:
        return
    if topic is None:
        topic = _tim_bai(course_id, lesson_no)[1]
    dung, tong, combo = ket
    _record_drill(uid, {'dung': dung, 'tong': tong, 'combo': combo,
                        'da_lam': len(da_chot), 'phut': None},
                  lesson_id, lesson_no, course_id, topic, local_now())
    logger.info('[lessons] uid=%s bài %s/%s: chốt lượt phòng luyện đang dở (%s/%s) '
                'vì bấm Bắt đầu lại', uid, course_id, lesson_no, dung, tong)


def _record_drill(uid, ket, lesson_id, lesson_no, course_id, topic, now):
    """Ghi kết quả phòng luyện tốc độ thành một sự kiện riêng.

    Phòng luyện đo thứ mà bài kiểm tra đầu vào không đo được: TỐC ĐỘ xử lý dưới
    đồng hồ đếm ngược — đúng thứ kỳ thi HSA chấm. Trước đây kết quả này chỉ hiện
    trên màn hình rồi biến mất, không có nơi nào lưu.

    Chấm trên TỔNG số câu chứ không phải số câu kịp làm: hết giờ mà chưa xong
    cũng là một kết quả trong bài thi tính giờ, và đó chính là thứ phòng luyện
    đo. Số câu kịp làm vẫn giữ trong meta để đọc lại được.

    KHÔNG ghi `xp` vào sự kiện này: sự kiện bài học đã mang tổng XP của cả lượt
    hoàn thành (gồm cả phần phòng luyện), ghi thêm ở đây là đếm hai lần.
    """
    if not ket or ket.get('lan_dau') is False:
        return
    record_event(
        uid, KIND_DRILL, f'drill:{lesson_id}',
        occurred_at=now, course_id=course_id, topic=topic,
        ref_type='lesson', ref_id=str(lesson_id),
        score=ket['dung'], max_score=ket['tong'], minutes=ket['phut'],
        meta={'lessonNo': lesson_no, 'maxCombo': ket['combo'],
              # Số câu KỊP làm: phân biệt "làm chậm" với "làm sai" khi đọc lại.
              'answered': ket['da_lam']},
    )


def _da_ghi_danh(uid, course_id):
    """Học viên đã ghi danh khoá này chưa?

    Một câu tra, dùng chung cho đường ĐỌC nội dung và đường CHẤM. Hai hàng rào
    tự viết là hai hàng rào sẽ trôi khỏi nhau.

    CÓ ĐỆM 60 GIÂY vì phòng luyện gọi đường chấm MỖI CÂU: đo 31/08/2026, không
    đệm thì mỗi lần chấm mất 257ms mà gần hết là một lượt tới Neon chỉ để hỏi
    lại đúng câu này. Trong một trò chơi bấm giờ thì đó là độ trễ người dùng cảm
    thấy được. Cùng con số và cùng lý lẽ với đệm user ở
    `accounts/authentication.py`; huỷ ghi danh có hiệu lực chậm tối đa một phút,
    và đây không phải cửa thu hồi quyền.
    """
    key = 'ghidanh:%s:%s' % (uid, course_id)
    co = cache.get(key)
    if co is None:
        co = bool(q1('SELECT 1 FROM enrollments WHERE user_id=%s AND course_id=%s',
                     (uid, course_id)))
        cache.set(key, co, 60)
    return co


def quen_ghi_danh(uid, course_id):
    """Xoá đệm ghi danh. Gọi ngay sau khi ghi danh hoặc huỷ ghi danh."""
    cache.delete('ghidanh:%s:%s' % (uid, course_id))


class CompleteLessonView(APIView):
    def post(self, request, lesson_no):
        data = request.data if isinstance(request.data, dict) else {}
        course_id = data.get('courseId') or data.get('course_id')
        if not course_id:
            return Response({'error': 'Thiếu courseId'}, status=400)

        # ĐIỂM ĐƯỢC TÍNH, KHÔNG ĐƯỢC NHẬN.
        #
        # Bản cũ lấy thẳng `quizScore` từ thân request và chỉ kiểm `isinstance
        # (int)` — không có biên. Đo 31/08/2026: `{"quizScore": 999999}` → 200,
        # `lesson_progress.quiz_score = 999999`. Con số đó nuôi bản đồ năng lực,
        # sổ điểm của giảng viên và nhánh lý thuyết thích ứng.
        #
        # Nay máy chủ chấm từ CÂU TRẢ LỜI (`answers`), lấy đáp án từ CSDL. Thân
        # request KHÔNG còn quyết định được điểm.
        #
        # `quizScore` cũ vẫn nhận, CHỈ khi không gửi `answers` — engine bản cũ
        # đang chạy trên máy học viên không tự cập nhật ngay khi ta deploy, và
        # để nó gãy hẳn là làm mất bài của người đang học giữa chừng. Có kẹp
        # biên 0–100, và có ghi nhật ký để biết còn bao nhiêu máy dùng bản cũ.
        answers = data.get('answers')
        answers = answers if isinstance(answers, dict) else None
        if answers is None and data.get('quizScore') is not None:
            # Engine bản CŨ còn nằm trong bộ nhớ đệm trình duyệt của học viên
            # đang học dở. KHÔNG để nó gãy — bài vẫn hoàn thành, XP vẫn cộng —
            # nhưng điểm thì để TRỐNG chứ không nhận con số nó tự khai.
            #
            # "Không biết điểm" và "điểm 100 vì người dùng nói thế" là hai
            # chuyện khác nhau, và chỉ một trong hai là sự thật. Ô trống trên sổ
            # điểm đọc ra là "chưa đo được"; con số 100 giả thì không ai đọc ra
            # được là giả.
            logger.info('[lessons] bài %s/%s: engine bản CŨ gửi quizScore=%r — BỎ QUA, '
                        'ghi bài xong nhưng không ghi điểm',
                        course_id, lesson_no, data.get('quizScore'))
        quiz_score = None
        uid = request.user.id
        with transaction.atomic():
            course = q1('SELECT id, lessons FROM courses WHERE id=%s', (course_id,))
            if not course:
                return Response({'error': 'Không tìm thấy khóa học'}, status=404)

            lesson_id, topic, lesson_title, xp_bai = _tim_bai(course_id, lesson_no)
            if lesson_id is None:
                # Bài không tồn tại trong khoá. Bản cũ ĐẺ RA nó ở đây; nay nói
                # thẳng là không có, vì đó là sự thật.
                return Response({'error': 'Không tìm thấy bài học'}, status=404)

            # XP ĐƯỢC TÍNH, KHÔNG ĐƯỢC NHẬN — cùng luật với điểm ở trên.
            # Bản cũ lấy `xpEarned` từ thân request, kẹp 0–500 rồi cộng thẳng.
            # Phần thưởng thật mỗi bài là 50, nên `{"xpEarned": 500}` cho 76 bài
            # là 38.000 XP thay vì 3.800 — mà bảng xếp hạng thì các em thi nhau
            # thật. Nay lấy `xp_reward` do người soạn bài ghi trong nội dung bài
            # (đã kiểm 0–500 lúc nhập, `content.validate_lesson`).
            # CHẤM TRÊN PHẦN ĐÃ GHI NHẬN, không trên thân request (A12).
            # `/check` đã chốt từng câu ngay lúc học viên trả lời; thân request
            # chỉ còn là bản sao lưu cho những câu chưa kịp qua `/check` (mất
            # mạng giữa chừng, hoặc engine bản cũ chưa gọi nó). Lần đầu vẫn
            # thắng, nên gửi lại một bộ đáp án "đẹp" ở bước này không đổi được gì.
            test_chot = ghi_nhan(uid, lesson_id, 'test', answers or {})
            if test_chot:
                _, dung, tong = cham(course_id, lesson_no, 'test', test_chot)
                quiz_score = phan_tram(dung, tong)

            xp_bai = xp_bai if isinstance(xp_bai, int) and 0 <= xp_bai <= 500 else 50
            # Phòng luyện chấm TRƯỚC khi cộng XP: phần thưởng của nó là một phần
            # của tổng, mà tổng thì phải biết trước lúc `award_xp`.
            drill_ket = _cham_drill(data.get('drill'), course_id, lesson_no,
                                    uid, lesson_id)
            xp_earned = xp_bai + (drill_ket['xp'] if drill_ket else 0)

            # ── HOÀN THÀNH PHẢI CÓ BẰNG CHỨNG (anh Sơn chốt 04/09/2026) ──────
            #
            # Trước hôm nay đường này KHÔNG đòi gì cả: gọi thẳng 76 lần là được
            # 76 bài "đã hoàn thành", 3.800 XP và chuỗi ngày học, không trả lời
            # một câu nào. Mọi hàng rào chống gian lận phía trên — chấm ở máy
            # chủ, "lần đầu thắng", "lượt đầu vào sổ" — đều canh chuyện TRẢ LỜI
            # THẾ NÀO, và không cái nào canh chuyện CÓ TRẢ LỜI KHÔNG.
            #
            # Với một sản phẩm bán bằng số đo thì một dòng "đã hoàn thành" không
            # có gì đứng sau làm hỏng mọi báo cáo đọc nó.
            #
            # HAI NHÁNH, vì hai tình huống khác hẳn nhau:
            #
            #   bài CÓ câu hỏi mà chưa trả lời câu nào → CHẶN (400)
            #   bài KHÔNG có câu hỏi nào               → cho qua, nhưng ghi
            #                                            `source='self'`
            #
            # Nhánh hai dùng đúng cơ chế repo đã có: `stats/gradebook.py` tách
            # hai xô `minutes` / `selfMinutes` theo cột `source`, nghĩa là "máy
            # đo" và "học viên tự khai". Một bài không có gì để đo thì hoàn
            # thành nó LÀ một lời tự khai — nói thế trong dữ liệu là trung thực,
            # không phải là phạt.
            #
            # `existed` được miễn: bài đã hoàn thành từ trước (kể cả những bài
            # hoàn thành trước bản vá này) thì gọi lại không bị chặn — đường này
            # vốn nhận cú bấm lặp, và chặn ở đó là phạt người dùng vì lỗi cũ.
            co_cau_hoi = any(dap_an(course_id, lesson_no).get(p)
                             for p in ('test', 'drill'))
            da_lam = bool(test_chot) or bool(doc_ghi_nhan(uid, lesson_id, 'drill'))
            # MỘT câu tra cho MỘT sự thật. `existed` vừa là cửa miễn ở đây,
            # vừa là điều kiện "đã cộng XP rồi" ở dưới — hai tên cho cùng một
            # dòng CSDL là cách chúng trôi khỏi nhau.
            existed = q1("SELECT 1 FROM lesson_progress "
                         "WHERE user_id=%s AND lesson_id=%s AND status='completed'",
                         (uid, lesson_id))
            if co_cau_hoi and not da_lam and not existed:
                return Response({'error': (
                    'Bài này có phần luyện tập — làm ít nhất một câu rồi mới '
                    'đánh dấu hoàn thành được.')}, status=400)
            nguon = SOURCE_SYSTEM if da_lam else SOURCE_SELF
            if data.get('xpEarned') is not None and data.get('xpEarned') != xp_earned:
                logger.info('[lessons] bài %s/%s: client khai xpEarned=%r — BỎ QUA, '
                            'cộng %s (bài %s + phòng luyện %s)',
                            course_id, lesson_no, data.get('xpEarned'), xp_earned,
                            xp_bai, xp_earned - xp_bai)

            # `existed` (tra ở khối kiểm bằng chứng phía trên) cũng là cửa
            # chống cộng XP hai lần khi học viên bấm F5 trên hộp chúc mừng.

            x('''INSERT INTO lesson_progress
                     (user_id, lesson_id, course_id, status, quiz_score, xp_earned, completed_at)
                 VALUES (%s, %s, %s, 'completed', %s, %s, %s)
                 ON CONFLICT (user_id, lesson_id) DO UPDATE SET
                     status       = 'completed',
                     -- Vá lại dòng cũ có `course_id` NULL. `COALESCE` chứ không
                     -- ghi đè thẳng: dòng đã đúng thì không đụng, dòng hỏng thì
                     -- lành lại ngay lần hoàn thành kế tiếp.
                     course_id    = COALESCE(lesson_progress.course_id, EXCLUDED.course_id),
                     -- ĐIỂM VÀO SỔ LÀ ĐIỂM CỦA LẦN ĐẦU ĐO ĐƯỢC. Đảo thứ tự
                     -- COALESCE so với bản cũ: ô đã có số thì giữ, ô còn trống
                     -- thì điền.
                     --
                     -- Vì sao BUỘC phải thế, chứ không phải một sở thích: `/check`
                     -- trả đáp án cho câu đã trả lời (phần xem lại cần), và
                     -- `/complete` XOÁ khoá "lần đầu thắng" để lần ôn sau bắt
                     -- đầu từ giấy trắng. Hai thứ ấy cộng lại cho một đường
                     -- vòng: gửi bừa để moi đáp án → hoàn thành (điểm 0 vào sổ)
                     -- → hoàn thành lại bằng bộ vừa moi → điểm 100 GHI ĐÈ số 0.
                     -- Giữ điểm cao nhất cũng không chặn được, vì 0 → 100 là đi
                     -- LÊN. Chỉ "lần đầu thắng" mới đóng được.
                     quiz_score   = COALESCE(lesson_progress.quiz_score, EXCLUDED.quiz_score),
                     xp_earned    = GREATEST(EXCLUDED.xp_earned, lesson_progress.xp_earned),
                     completed_at = COALESCE(lesson_progress.completed_at, EXCLUDED.completed_at)''',
              (uid, lesson_id, course_id, quiz_score, xp_earned, local_now()))

            # TỰ GHI DANH khi bắt đầu học. Không có dòng này thì câu UPDATE ngay
            # dưới khớp 0 dòng và IM LẶNG — tiến độ của em vô hình.
            #
            # Đo trên dữ liệu thật 31/08/2026: HAI trong bốn học viên đang ở đúng
            # trạng thái đó. Em id 9 học xong 5 bài nhưng `enrollments` rỗng, nên
            # "Khoá học của tôi" trống, trang khoá hiện 0% và khoá cứng mọi bài,
            # quiz ôn tập (điều kiện `enrollment && completed >= 5`) khoá vĩnh
            # viễn — trong khi trang Kỹ năng nói 19%. Hai màn hình, hai câu trả
            # lời cho cùng một câu hỏi.
            #
            # Lý do gốc: đường DUY NHẤT tạo dòng `enrollments` trong cả repo là
            # nút "Đăng ký học" ở trang chi tiết khoá. Vào thẳng `/lesson/<khoá>`
            # thì học được nhưng không bao giờ ghi danh — mà đó chính là đường
            # mà mọi liên kết "Học tiếp" dẫn tới.
            #
            # `ON CONFLICT DO NOTHING`: em đã ghi danh rồi thì không đụng gì,
            # nhất là không đặt lại `enrolled_at`.
            x('''INSERT INTO enrollments (user_id, course_id, progress, completed_lessons,
                                          time_spent, last_lesson, next_lesson, enrolled_at)
                 VALUES (%s, %s, 0, 0, '0h', '', '', %s)
                 ON CONFLICT (user_id, course_id) DO NOTHING''',
              (uid, course_id, local_now()))
            quen_ghi_danh(uid, course_id)

            # Tính lại cache enrollments từ nguồn thật lesson_progress.
            # MỘT bản duy nhất, dùng chung với đường ghi danh lại — xem
            # `courses/enrollment.py` để biết hai bản trước đây lệch ở đâu.
            dem = tinh_lai_ghi_danh(uid, course_id, course['lessons'])
            completed_count = dem['completed_lessons']
            progress = dem['progress']

            gained = 0
            new_streak, used_freeze = None, False
            if not existed:
                gained = xp_earned
                today = local_today()
                # Chuỗi + XP dùng chung common/streak.py để thi thử tính y hệt
                # (và để luật bảo hiểm chuỗi chỉ có một bản duy nhất).
                award_xp(uid, gained, today)
                new_streak, used_freeze = touch_streak(uid, today)

            # ── Dòng sự kiện học tập ────────────────────────────────────
            # Bản đồ năng lực theo chủ đề đọc ở đây chứ không đọc lesson_progress:
            # bảng đó không giữ điểm phòng luyện, không giữ chủ đề, và sẽ không
            # bao giờ giữ được sự kiện của thi thử hay quiz ôn tập.
            now = local_now()
            # Điểm ghi vào DÒNG SỰ KIỆN phải là đúng con số vừa vào sổ, không
            # phải con số vừa chấm. Nếu không thì `lesson_progress` giữ điểm lần
            # đầu còn `learning_events` (nguồn của bản đồ năng lực) bị ghi đè
            # bằng lần sau — hai bảng nói hai điều về cùng một bài, và đường
            # vòng moi đáp án vẫn nâng được ô năng lực.
            da_vao_so = (q1('SELECT quiz_score FROM lesson_progress '
                            'WHERE user_id=%s AND lesson_id=%s', (uid, lesson_id))
                         or {}).get('quiz_score')
            record_event(
                uid, KIND_LESSON, f'lesson:{lesson_id}',
                occurred_at=now, course_id=course_id, topic=topic,
                ref_type='lesson', ref_id=str(lesson_id),
                # quiz_score đã là PHẦN TRĂM đúng của bài kiểm tra đầu vào
                # (engine gửi lên round(score/total*100)), nên mốc tối đa là 100.
                score=da_vao_so, max_score=(100 if da_vao_so is not None else None),
                xp=xp_earned,
                # `self` khi KHÔNG có bằng chứng nào (bài không có câu hỏi, hoặc
                # bài đã xong từ trước nên được miễn cửa chặn). `gradebook.py`
                # đọc đúng cột này để tách "máy đo" khỏi "học viên tự khai" —
                # xem chú thích dài ở chỗ kiểm bằng chứng phía trên.
                source=nguon,
                # Tiêu đề lấy từ dòng `lessons` chứ không từ thân request: đây
                # là thứ hiện lại trong nhật ký học tập của em.
                meta={'lessonNo': lesson_no, 'title': lesson_title or ''},
            )
            _record_drill(uid, drill_ket, lesson_id, lesson_no, course_id, topic, now)

            # Xoá phần đã ghi nhận: bài xong rồi thì câu trả lời cũ không còn
            # việc gì, mà giữ lại thì em ôn lại sẽ kẹt với đúng những câu hôm
            # trước. Xoá SAU khi đã chấm xong cả hai phần.
            xoa_ghi_nhan(uid, lesson_id)

            newly_awarded = check_and_award_achievements(uid)

        return Response({
            'ok': True,
            'completedLessons': completed_count,
            'progress': progress,
            'xpGained': gained,
            # Tách ra để màn chúc mừng nói đúng "bài 50 + phòng luyện 70" thay vì
            # một con số trần mà học viên không biết ở đâu ra.
            'xpLesson': xp_bai,
            'xpDrill': (drill_ket['xp'] if drill_ket else 0),
            'drill': ({'correct': drill_ket['dung'], 'total': drill_ket['tong'],
                       'maxCombo': drill_ket['combo'], 'answered': drill_ket['da_lam']}
                      if drill_ket else None),
            'streak': new_streak,
            'usedStreakFreeze': used_freeze,
            'newAchievements': newly_awarded,
        })


class CheckAnswersView(APIView):
    """POST /api/courses/<course_id>/lessons/<lesson_no>/check — chấm ở máy chủ.

    Thân: ``{"phan": "test"|"drill", "answers": {"t1": "300.000đ", ...}}``
    Trả : ``{"results": {"t1": {"correct": true, "answer": ..., "explain": ...}},
             "correct": 2, "total": 3, "scorePct": 67}``

    ĐÁP ÁN CHỈ VỀ CÙNG KẾT QUẢ CỦA CÂU ĐÃ TRẢ LỜI. Gửi `answers` rỗng thì không
    moi được gì — nếu không, endpoint chấm chính là cửa sau thay cho lỗ vừa bịt.

    VÀ CÂU TRẢ LỜI BỊ GHI NHẬN, LẦN ĐẦU THẮNG (A12, 31/08/2026). Không có phần
    này thì hàng rào trên vẫn đi vòng được bằng hai lời gọi: gửi bừa cả 8 câu để
    lấy trọn bảng đáp án, rồi `/complete` với bộ đáp án vừa lấy. Nay bộ gửi bừa
    ấy CHÍNH LÀ bài làm, và `/complete` chấm trên nó.

    Phòng luyện KHÔNG nhận `answer`: giao diện của nó chỉ cần biết đúng hay sai
    để tô màu, còn đáp án thì phần xem lại sau khi nộp mới cần. Trả ít hơn mức
    cần là cách rẻ nhất để một endpoint không thành cửa sau.

    Có ghi danh mới chấm được: cùng hàng rào với đường đọc nội dung.

    Quota đếm theo NGƯỜI DÙNG chứ không theo IP: cả phòng máy của trung tâm đi
    ra bằng một địa chỉ NAT, mà đường này bị gọi 10 lần mỗi bài. Xem
    `common/throttling._PerViewUserThrottle`.
    """

    # BỐN lớp, không phải hai. Đặt `throttle_classes` trên view là GHI ĐÈ
    # `DEFAULT_THROTTLE_CLASSES` chứ không bổ sung — cùng cái bẫy với
    # `permission_classes`. Bản đầu chỉ để hai lớp theo NGƯỜI DÙNG, nên endpoint
    # này mất hẳn trần theo MÁY: một máy giữ N tài khoản đẩy được N × 600
    # request/giờ vào đúng đường ghi `jsonb`.
    #
    # Giữ cả hai trục: theo người dùng để cả phòng NAT không chia nhau một
    # quota (đó là lý do sinh ra hai lớp kia), và theo IP để một máy không thay
    # mặt cả trăm tài khoản.
    throttle_classes = [DailyUserThrottle, HourlyUserThrottle,
                        DailyIPThrottle, HourlyIPThrottle]

    def post(self, request, course_id, lesson_no):
        data = request.data if isinstance(request.data, dict) else {}
        phan = str(data.get('phan') or 'test')
        if phan not in PHAN_CO_CAU_HOI:
            return Response({'error': 'Phần phải là một trong: %s.'
                                      % ', '.join(PHAN_CO_CAU_HOI)}, status=400)
        answers = data.get('answers')
        if not isinstance(answers, dict):
            if not data.get('reset'):
                return Response({'error': 'Thiếu answers.'}, status=400)
            answers = {}
        if not _da_ghi_danh(request.user.id, course_id):
            return Response({'error': 'Bạn chưa ghi danh khoá này.'}, status=403)

        # `id_bai` chứ không `_tim_bai`: đường này bị gọi MỖI CÂU trong phòng
        # luyện, và nó chỉ cần đúng một con số. Có đệm 60 giây.
        lesson_id = id_bai(course_id, lesson_no)
        if lesson_id is None:
            return Response({'error': 'Chưa có nội dung cho bài này.'}, status=404)

        # `reset` chỉ dành cho phòng luyện — nút "Bắt đầu" của nó là nút LÀM
        # LẠI. Bài kiểm tra đầu vào KHÔNG được reset: `/check` của nó trả đáp án,
        # nên cho reset là mở lại đúng cửa vừa bịt.
        if data.get('reset') and phan == 'drill':
            _chot_luot_drill(request.user.id, lesson_id, course_id, lesson_no)
            xoa_ghi_nhan_phan(request.user.id, lesson_id, phan)

        da_chot = ghi_nhan(request.user.id, lesson_id, phan, answers)
        ket_qua, dung, tong = cham(course_id, lesson_no, phan, da_chot)
        if ket_qua is None:
            return Response({'error': 'Chưa có nội dung cho bài này.'}, status=404)
        # Chỉ trả kết quả của những câu LẦN NÀY gửi lên. Bộ đã chốt gồm cả các
        # câu trước đó; nhắc lại chúng mỗi lượt gọi là phát lại đáp án cũ không
        # ai hỏi, và trong phòng luyện thì đó là toàn bộ những câu đã qua.
        ket_qua = {k: v for k, v in ket_qua.items() if k in answers}
        if phan == 'drill':
            ket_qua = {k: {'correct': v['correct']} for k, v in ket_qua.items()}
        return Response({'results': ket_qua, 'correct': dung, 'total': tong,
                         'scorePct': phan_tram(dung, tong)})


class CourseContentView(APIView):
    """GET /api/courses/<course_id>/content — nội dung bài đã soạn trong DB.

    Engine bài học gọi endpoint này trước, rồi mới rơi về file JS cho những bài
    DB chưa có (xem lessons/content.py để biết vì sao).
    """

    def get(self, request, course_id):
        if not q1('SELECT 1 FROM courses WHERE id=%s', (course_id,)):
            return Response({'error': 'Không tìm thấy khoá học'}, status=404)
        # CÓ GHI DANH MỚI ĐỌC ĐƯỢC. Đo 31/08/2026: một giảng viên chưa ghi danh
        # và một học viên chỉ ghi danh khoá KHÁC đều tải được nguyên nội dung
        # khoá này. Nay `CompleteLessonView` tự ghi danh khi bắt đầu học, nên
        # hàng rào này không chặn ai đang học thật.
        if not _da_ghi_danh(request.user.id, course_id):
            return Response({'error': 'Bạn chưa ghi danh khoá này. Vào trang khoá học '
                                      'và bấm "Đăng ký học" để bắt đầu.'}, status=403)

        # ?lesson=N → chỉ bài đó. Trang bài học dùng đường này; trả cả khoá chỉ
        # tốn băng thông cho 75 bài học viên không mở.
        want = request.query_params.get('lesson')
        if want and str(want).isdigit():
            lesson, total = one_lesson(course_id, int(want))
            if lesson is None:
                return Response({'error': 'Chưa có nội dung cho bài này',
                                 'courseId': course_id, 'total': total}, status=404)
            return Response({'courseId': course_id, 'total': total, 'lesson': lesson})

        lessons = course_content(course_id)
        return Response({'courseId': course_id, 'count': len(lessons), 'lessons': lessons})
