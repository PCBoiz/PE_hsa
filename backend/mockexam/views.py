"""Trụ cột ④ — Thi thử CBT. Raw SQL qua common/db (đồng bộ style toàn app).

ĐỒNG HỒ Ở MÁY CHỦ (31/08/2026). Trước đó phòng thi thử không có gì là "thi":
`duration_seconds` do trình duyệt khai (nhận cả **−5000**), không giới hạn lượt,
mỗi lượt cộng tới 100 XP, và phản hồi lúc nộp trả **đủ đáp án của cả đề** —
nghĩa là nộp RỖNG → nhận 9 đáp án → nộp lại → 9/9, +100 XP. Đo được đúng như
vậy trên bản chạy thật.

Ba luật của phòng thi này, cùng tinh thần với `lessons/grading.py`:

1. **Đồng hồ thuộc về máy chủ.** `POST /start` mở một dòng `mock_attempts` với
   `started_at`; thời lượng là hiệu `submitted_at − started_at`, KHÔNG phải con
   số trình duyệt gửi lên.
2. **Đáp án chỉ lộ theo từng câu ĐÃ trả lời.** Câu bỏ trống thì lúc nộp không
   nhận được đáp án của nó — bỏ trống rồi nộp không còn là cách lấy bài giải.
3. **Một lượt vào sổ.** Lượt ĐẦU ĐƯỢC MỞ mới tính điểm — quyết định ấy chốt ngay
   lúc `/start` và ghi vào cột `counted`, chứ không đợi tới lúc nộp. Mở đề rồi bỏ
   là đã dùng mất lượt ấy: đề đã lộ cho em rồi. Nếu chốt lúc nộp thì "mở đề, đọc
   hết, đóng tab, hôm sau bắt đầu lại" là một cách làm lại vô hạn.
   Làm lại vẫn được chấm và xem lại để luyện, nhưng không cộng gì.

4. **Nộp mà không qua `/start` thì KHÔNG vào sổ.** Bài vẫn được chấm và vẫn lưu
   để em không mất công, nhưng không cộng XP và không ghi sự kiện. Nếu không có
   luật này thì cả luật 1 lẫn luật 3 chỉ ràng buộc được trình duyệt tử tế: bỏ
   qua `/start`, ngồi ba tiếng tra đáp án rồi `POST /submit` là 9/9 + 100 XP.

Hai ràng buộc DUY NHẤT ở `sql/mockexam_schema.sql` đỡ lưng cho luật 3 và cho
việc "một lượt đang mở": ở mức cách ly `read committed`, một câu SELECT rồi
INSERT không chặn được năm request song song — chỉ Postgres chặn được.

Chỗ CỐ Ý không siết: nhiệm vụ ngày "Làm 1 đề thi thử" (`mocks_today`) vẫn đếm
MỌI lượt nộp. Đo 31/08/2026: toàn hệ chỉ có **một** đề đã xuất bản, nên nếu
nhiệm vụ ngày cũng chỉ tính lượt đầu thì nó hỏng vĩnh viễn với người đã thi. Nó
là nhiệm vụ THÓI QUEN chứ không phải điểm số, và `user_missions` đã khoá theo
(user, nhiệm vụ, ngày) nên không cày được.
"""
import json
import logging

from django.db import IntegrityError, transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from achievements.services import check_and_award_achievements
from common.clock import local_now, local_today
from common.db import q, q1, x, xn
from common.events import KIND_MOCK, KIND_MOCK_SECTION, record_event
from common.streak import award_xp, touch_streak

logger = logging.getLogger(__name__)

#: XP cho một lượt thi thử: 30 XP công sức + tối đa 70 XP theo tỉ lệ đúng.
#: Trần 100 để một đề không bằng cả buổi học (mỗi bài học 50 XP).
_MOCK_XP_BASE = 30
_MOCK_XP_MAX_BONUS = 70

#: Ân hạn sau khi hết giờ. Trình duyệt tự nộp ở giây 0, và lời gọi đó còn phải
#: đi qua mạng; kẹp đúng 0 giây thì người làm hết giờ tử tế lại bị tính nộp
#: muộn. 2 phút đủ rộng cho mạng kém mà vẫn quá hẹp để đi tra 9 câu.
_AN_HAN_GIAY = 120

SECTION_LABELS = {
    'quantitative': 'Định lượng',
    'verbal': 'Định tính',
    'science': 'Khoa học',
}

#: Hợp phần của đề thi → khoá học tương ứng. Bản đồ năng lực cần biết điểm thi
#: thử thuộc khoá nào mới quy được về chủ đề của khoá đó.
SECTION_COURSE = {
    'quantitative': 'hsa_quantitative',
    'verbal': 'hsa_verbal',
    'science': 'hsa_science',
}


def _norm(s):
    """Chuẩn hoá đáp án điền để so khớp: bỏ hoa/thường, khoảng trắng, '%'."""
    return str(s if s is not None else '').strip().lower().replace(' ', '').replace('%', '')


def _questions(exam):
    qs = exam.get('questions_json')
    if isinstance(qs, str):
        qs = json.loads(qs)
    return qs or []


def _de_cong_khai(items):
    """Câu hỏi gửi xuống trình duyệt — ĐÃ bỏ `answer` và mọi trường lời giải."""
    return [{
        'id': it.get('id'),
        'section': it.get('section'),
        'section_label': SECTION_LABELS.get(it.get('section'), it.get('section')),
        'type': it.get('type', 'mcq'),
        'question': it.get('question'),
        'options': it.get('options', []),
    } for it in items]


def _gioi_han_giay(exam):
    return int(exam.get('duration_minutes') or 20) * 60


def _luot_dang_mo(uid, exam_id):
    """Lượt đã mở mà chưa nộp. Đây là vật mang ĐỒNG HỒ của máy chủ.

    `uq_mock_attempt_dang_mo` bảo đảm nhiều nhất một dòng; `ORDER BY id DESC`
    giữ lại phòng khi chỉ mục chưa kịp có trên một CSDL cũ.
    """
    return q1("SELECT id, started_at, counted, answers_json FROM mock_attempts "
              "WHERE user_id=%s AND exam_id=%s AND submitted_at IS NULL "
              "ORDER BY id DESC LIMIT 1", (uid, exam_id))


def _doc_answers(row):
    """`answers_json` của một dòng, luôn ra dict."""
    a = (row or {}).get('answers_json')
    if isinstance(a, str):
        try:
            a = json.loads(a)
        except ValueError:
            return {}
    return a if isinstance(a, dict) else {}


def _cham_de(exam, answers):
    """Chấm một bộ câu trả lời trên một đề. CHỈ ĐỌC, không đụng CSDL.

    Trả ``(score, total, section_scores, sec_correct, sec_total, weakest,
    results)``. Tách ra vì có HAI nơi chấm: đường nộp bình thường, và đường đóng
    một lượt đã cạn giờ — hai bản chấm khác nhau là hai bản sẽ trôi khỏi nhau.
    """
    items = _questions(exam)
    sec_total, sec_correct, results, score = {}, {}, [], 0
    for it in items:
        qid, sec = it.get('id'), it.get('section', '')
        correct, ua = it.get('answer'), answers.get(qid)
        da_tra_loi = ua is not None and str(ua).strip() != ''
        ok = da_tra_loi and _norm(ua) == _norm(correct)
        sec_total[sec] = sec_total.get(sec, 0) + 1
        if ok:
            score += 1
            sec_correct[sec] = sec_correct.get(sec, 0) + 1
        # Luật 2: câu bỏ trống thì KHÔNG kèm đáp án. Nộp rỗng để lấy bài giải là
        # cách khai thác đã đo được trên bản chạy thật.
        results.append({
            'id': qid, 'correct': ok,
            'your': ua if da_tra_loi else None,
            'answer': correct if da_tra_loi else None,
            'answered': da_tra_loi,
        })
    section_scores = {
        SECTION_LABELS.get(s, s): {'correct': sec_correct.get(s, 0), 'total': sec_total.get(s, 0)}
        for s in sec_total
    }
    weakest = None
    if section_scores:
        weakest = min(section_scores.items(),
                      key=lambda kv: (kv[1]['correct'] / kv[1]['total']) if kv[1]['total'] else 1.0)[0]
    return score, len(items), section_scores, sec_correct, sec_total, weakest, results


def _dong_luot_qua_gio(uid, mo, exam, now):
    """Đóng một lượt đã cạn giờ mà chưa ai nộp — chấm đúng những câu đã lưu.

    Đây chính xác là điều đáng lẽ xảy ra lúc đồng hồ về 0 nếu trình duyệt còn
    mở: máy tính sập, mạng rớt hay em đóng tab thì kết quả vẫn phải là kết quả
    của bài làm dở, không phải một lượt biến mất.

    KHÔNG cộng XP và KHÔNG ghi sự kiện dù lượt có `counted`: XP thưởng cho việc
    làm xong một lượt thi, mà lượt này em không có mặt lúc nó kết thúc. Cột
    `counted` vẫn giữ nguyên nên lượt tính điểm ĐÃ BỊ TIÊU — mở đề là đã thấy đề.
    """
    answers = _doc_answers(mo)
    score, total, section_scores, _sc, _st, _w, _r = _cham_de(exam, answers)
    xn("UPDATE mock_attempts SET score=%s, total=%s, section_scores_json=%s::jsonb, "
       "    duration_seconds=%s, submitted_at=%s "
       "  WHERE id=%s AND user_id=%s AND submitted_at IS NULL",
       (score, total, json.dumps(section_scores, ensure_ascii=False),
        _gioi_han_giay(exam), now, mo['id'], uid))
    logger.info('[mockexam] uid=%s đóng lượt %s vì cạn giờ mà chưa nộp — chấm %s/%s '
                'trên phần đã lưu', uid, mo['id'], score, total)


def _da_dung_luot_tinh_diem(uid, exam_id):
    """Học viên này đã MỞ lượt tính điểm cho đề này chưa?

    Đếm cả lượt đang mở và lượt đã nộp — vì lượt tính điểm bị tiêu ngay khi mở,
    không phải khi nộp. `started_at IS NOT NULL` để năm dòng lịch sử (không dòng
    nào có started_at) nằm ngoài luật mới, khớp với ghi chú "không hồi tố" ở
    `sql/mockexam_schema.sql`.
    """
    return bool(q1("SELECT 1 AS co FROM mock_attempts "
                   "WHERE user_id=%s AND exam_id=%s AND counted "
                   "AND started_at IS NOT NULL LIMIT 1", (uid, exam_id)))


def _mock_xp(score, total):
    if not total:
        return _MOCK_XP_BASE
    return _MOCK_XP_BASE + round(_MOCK_XP_MAX_BONUS * max(0, min(score, total)) / total)


def _record_mock_events(uid, attempt_id, exam_id, score, total,
                        sec_correct, sec_total, duration, xp, now):
    """Một lượt thi thử → 1 sự kiện tổng + 1 sự kiện cho mỗi hợp phần."""
    if not attempt_id:
        return
    minutes = max(1, round(duration / 60)) if duration else None
    record_event(
        uid, KIND_MOCK, f'mock:{attempt_id}',
        occurred_at=now, ref_type='mock_attempt', ref_id=str(attempt_id),
        score=score, max_score=total, minutes=minutes, xp=xp,
        meta={'examId': exam_id},
    )
    for sec, n in sec_total.items():
        course_id = SECTION_COURSE.get(sec)
        if not course_id or not n:
            continue
        # Khoá chống trùng dùng COURSE_ID, không dùng mã hợp phần: lệnh
        # backfill_learning_events chỉ suy ra được khoá học từ nhãn trong
        # section_scores_json. Hai bên ghi khác khoá thì nạp lại dữ liệu cũ sẽ
        # đẻ thêm một dòng nữa cho CÙNG một lượt thi, và hợp phần đó bị đếm hai
        # lần trong bản đồ năng lực.
        record_event(
            uid, KIND_MOCK_SECTION, f'mocksec:{attempt_id}:{course_id}',
            occurred_at=now, course_id=course_id,
            ref_type='mock_attempt', ref_id=str(attempt_id),
            score=sec_correct.get(sec, 0), max_score=n,
            meta={'examId': exam_id, 'section': SECTION_LABELS.get(sec, sec)},
        )


class MockExamsView(APIView):
    """GET /api/mock-exams — danh sách đề đã xuất bản."""
    def get(self, request):
        rows = q("SELECT id, title, description, duration_minutes, total_questions "
                 "FROM mock_exams WHERE is_published = TRUE ORDER BY id")
        return Response({'exams': rows})


class MockStartView(APIView):
    """POST /api/mock-exams/<id>/start — mở đồng hồ Ở MÁY CHỦ rồi trả đề.

    Tải lại trang giữa chừng thì NỐI TIẾP lượt đang mở: đúng số giây còn lại VÀ
    đúng những câu đã trả lời (`/save` lưu chúng dọc đường). Nếu không thì một
    lần lỡ F5 ở phút thứ 15 là mất trắng bài làm mà không xin lại được lượt.

    Lượt đang mở đã CẠN GIỜ thì được ĐÓNG LẠI như một lần nộp — chấm chính
    những câu đã lưu, y như lúc đồng hồ về 0 mà trình duyệt tự nộp. Bản đầu ngày
    31/08/2026 XOÁ dòng ấy rồi mở lượt mới; như thế "mở đề, đọc hết 9 câu, đóng
    tab, hôm sau bắt đầu lại" là một cách làm lại vô hạn mà vẫn được tính điểm.
    """
    def post(self, request, exam_id):
        exam = q1("SELECT id, title, description, duration_minutes, total_questions, questions_json "
                  "FROM mock_exams WHERE id=%s AND is_published=TRUE", (exam_id,))
        if not exam:
            return Response({'error': 'Không tìm thấy đề thi'}, status=404)

        uid = request.user.id
        gioi_han = _gioi_han_giay(exam)
        now = local_now()
        attempt_id, con_lai, tinh_diem, da_luu = None, gioi_han, None, {}

        mo = _luot_dang_mo(uid, exam_id)
        if mo and mo.get('started_at'):
            con = gioi_han - int((now - mo['started_at']).total_seconds())
            if con > 0:
                attempt_id, con_lai = mo['id'], con
                tinh_diem = mo['counted']
                da_luu = _doc_answers(mo)
            else:
                _dong_luot_qua_gio(uid, mo, exam, now)

        if attempt_id is None:
            attempt_id, tinh_diem = self._mo_luot(uid, exam_id, now)
            if attempt_id is None:
                # Một request /start song song vừa mở lượt trước ta một nhịp.
                mo = _luot_dang_mo(uid, exam_id)
                if not mo:
                    return Response({'error': 'Không mở được lượt thi, thử lại'}, status=409)
                attempt_id, tinh_diem = mo['id'], mo['counted']
                da_luu = _doc_answers(mo)
                if mo.get('started_at'):
                    con_lai = max(0, gioi_han - int((now - mo['started_at']).total_seconds()))

        items = _de_cong_khai(_questions(exam))
        return Response({
            'attemptId': attempt_id,
            'secondsLeft': con_lai,
            'counts': bool(tinh_diem),
            'savedAnswers': da_luu,
            'id': exam['id'], 'title': exam['title'], 'description': exam['description'],
            'duration_minutes': exam['duration_minutes'],
            'total_questions': exam['total_questions'] or len(items),
            'questions': items,
        })

    @staticmethod
    def _mo_luot(uid, exam_id, now):
        """Mở một lượt mới. Trả ``(id, counted)``, hoặc ``(None, None)`` nếu đụng
        ràng buộc duy nhất — tức một request song song vừa mở trước.

        Thử `counted=TRUE` trước; đụng `uq_mock_attempt_tinh_diem` thì nghĩa là
        lượt tính điểm đã có người giữ, mở tiếp một lượt LUYỆN. Để Postgres trả
        lời câu "đã có lượt tính điểm chưa" thay vì tự canh bằng một câu SELECT
        không khoá — ở `read committed`, SELECT-rồi-INSERT không chặn được gì.
        """
        for muon_tinh in (not _da_dung_luot_tinh_diem(uid, exam_id), False):
            try:
                with transaction.atomic():
                    row = q1("INSERT INTO mock_attempts "
                             "(user_id, exam_id, started_at, submitted_at, counted) "
                             "VALUES (%s,%s,%s,NULL,%s) RETURNING id",
                             (uid, exam_id, now, muon_tinh))
                return (row or {}).get('id'), muon_tinh
            except IntegrityError:
                continue
        return None, None


class MockSaveView(APIView):
    """POST /api/mock-exams/<id>/save — lưu tạm câu trả lời của lượt đang mở.

    Có đường này thì tải lại trang, rớt mạng hay trình duyệt di động thu hồi tab
    không còn làm mất bài làm; và lượt bị bỏ dở tới lúc cạn giờ vẫn chấm được
    đúng những gì em đã kịp làm, y như lúc đồng hồ về 0.

    KHÔNG chấm, KHÔNG trả gì ngoài `ok`: đây không phải cửa sau của `/submit`.
    """
    def post(self, request, exam_id):
        data = request.data if isinstance(request.data, dict) else {}
        answers = data.get('answers')
        if not isinstance(answers, dict):
            return Response({'error': 'Thiếu answers'}, status=400)
        n = xn("UPDATE mock_attempts SET answers_json=%s::jsonb "
               "  WHERE user_id=%s AND exam_id=%s AND submitted_at IS NULL",
               (json.dumps(answers, ensure_ascii=False), request.user.id, exam_id))
        return Response({'ok': bool(n), 'saved': n or 0})


class MockSubmitView(APIView):
    """POST /api/mock-exams/<id>/submit — body {answers:{qid:val}}.

    Chấm điểm, đóng lượt, trả điểm + phân tích hợp phần + hợp phần yếu nhất.
    """
    def post(self, request, exam_id):
        exam = q1("SELECT id, duration_minutes, questions_json FROM mock_exams "
                  "WHERE id=%s AND is_published=TRUE", (exam_id,))
        if not exam:
            return Response({'error': 'Không tìm thấy đề thi'}, status=404)
        data = request.data if isinstance(request.data, dict) else {}
        answers = data.get('answers')
        if not isinstance(answers, dict):
            answers = {}

        uid = request.user.id
        gioi_han = _gioi_han_giay(exam)
        now = local_now()
        mo = _luot_dang_mo(uid, exam_id)

        if mo and mo.get('started_at'):
            # Đồng hồ THẬT: hiệu hai mốc do chính máy chủ ghi.
            duration = max(0, int((now - mo['started_at']).total_seconds()))
            het_gio = duration > gioi_han + _AN_HAN_GIAY
            ly_do = 'het_gio' if het_gio else (None if mo['counted'] else 'da_lam_roi')
            tinh_diem = bool(mo['counted']) and not het_gio
        else:
            # KHÔNG có lượt đang mở — bài này không đi qua đồng hồ nào cả.
            # Vẫn chấm và vẫn lưu để em không mất công, nhưng KHÔNG vào sổ: nếu
            # nhánh này tính điểm thì bỏ qua /start là bỏ qua toàn bộ giới hạn
            # giờ, và luật "đồng hồ thuộc máy chủ" chỉ còn ràng buộc được trình
            # duyệt tử tế. Đo được: GET đề → ngồi ba tiếng tra đáp án →
            # POST /submit → 9/9 + 100 XP.
            logger.info('[mockexam] uid=%s exam=%s nộp mà KHÔNG có lượt đang mở '
                        '— chấm nhưng không vào sổ', uid, exam_id)
            duration, het_gio, tinh_diem, ly_do = 0, False, False, 'khong_qua_dong_ho'

        score, total, section_scores, sec_correct, sec_total, weakest, results =             _cham_de(exam, answers)

        streak, used_freeze, newly, attempt_id = None, False, [], None
        with transaction.atomic():
            sec_json = json.dumps(section_scores, ensure_ascii=False)
            ans_json = json.dumps(answers, ensure_ascii=False)
            if mo:
                # `xn` chứ không `x`: mệnh đề `submitted_at IS NULL` là hàng rào
                # chống nộp hai lần, và một hàng rào không ai đọc kết quả là
                # hàng rào trên giấy. Trượt hết mọi dòng nghĩa là lượt vừa bị
                # một tab khác đóng — khi ấy KHÔNG được cộng XP.
                n = xn("UPDATE mock_attempts SET score=%s, total=%s, section_scores_json=%s::jsonb, "
                       "    answers_json=%s::jsonb, duration_seconds=%s, submitted_at=%s, counted=%s "
                       "  WHERE id=%s AND user_id=%s AND submitted_at IS NULL",
                       (score, total, sec_json, ans_json, duration, now, tinh_diem,
                        mo['id'], uid))
                if n:
                    attempt_id = mo['id']
                else:
                    logger.info('[mockexam] uid=%s lượt %s đã bị đóng bởi một lời gọi khác '
                                '— lưu lại thành lượt luyện, không cộng gì', uid, mo['id'])
                    tinh_diem, ly_do = False, 'da_dong_o_noi_khac'
            if attempt_id is None:
                row = q1("INSERT INTO mock_attempts "
                         "(user_id, exam_id, score, total, section_scores_json, answers_json, "
                         " duration_seconds, started_at, submitted_at, counted) "
                         "VALUES (%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,NULL,%s,FALSE) RETURNING id",
                         (uid, exam_id, score, total, sec_json, ans_json, duration, now))
                attempt_id = (row or {}).get('id')

            # Trước 2026-08-14 thi thử KHÔNG cộng XP và KHÔNG tính vào chuỗi:
            # làm trọn một đề 150 câu vẫn mất chuỗi nếu hôm đó không mở bài học.
            # Thưởng gồm phần cố định cho công sức + phần theo số câu đúng.
            xp = _mock_xp(score, total) if tinh_diem else 0
            if tinh_diem:
                today = local_today()
                award_xp(uid, xp, today)
                streak, used_freeze = touch_streak(uid, today)

                # ── Dòng sự kiện học tập ────────────────────────────────────
                # Hai loại sự kiện cho CÙNG một lượt thi, mỗi loại một người
                # đọc:
                #   · `mock`         — tổng cả đề, nuôi đường cong tiến bộ.
                #   · `mock_section` — điểm từng hợp phần, nuôi bản đồ năng lực.
                # Bên đọc chọn đúng một loại nên không cộng trùng một lượt.
                # Lượt LUYỆN không ghi vào đây: bản đồ năng lực và đường cong
                # tiến bộ là sổ điểm, mà sổ điểm chỉ nhận lượt đầu.
                _record_mock_events(uid, attempt_id, exam_id, score, total,
                                    sec_correct, sec_total, duration, xp, now)

                newly = check_and_award_achievements(uid)

        return Response({
            'score': score, 'total': total,
            'section_scores': section_scores, 'weakest': weakest, 'results': results,
            'durationSeconds': duration,
            'counted': tinh_diem, 'notCountedReason': ly_do,
            'xpGained': xp, 'streak': streak, 'usedStreakFreeze': used_freeze,
            'newAchievements': newly,
        })


class MockAttemptsView(APIView):
    """GET /api/mock-attempts — lịch sử làm bài của user."""
    def get(self, request):
        # section_scores_json: Trang của tôi dựng "độ chính xác theo hợp phần"
        # từ đây, khỏi phải gọi lại từng lượt thi (audit 2026-08-15).
        # `submitted_at IS NOT NULL`: từ 31/08/2026 có dòng ĐANG MỞ (đã bấm bắt
        # đầu, chưa nộp) — nó chưa phải một kết quả, không được vào lịch sử.
        rows = q("SELECT a.id, a.exam_id, e.title, a.score, a.total, a.duration_seconds, "
                 "a.section_scores_json, a.counted, a.submitted_at "
                 "FROM mock_attempts a JOIN mock_exams e ON e.id = a.exam_id "
                 "WHERE a.user_id=%s AND a.submitted_at IS NOT NULL "
                 "ORDER BY a.submitted_at DESC LIMIT 20", (request.user.id,))
        for r in rows:
            sa = r.get('submitted_at')
            r['submitted_at'] = sa.isoformat() if sa else None
        return Response({'attempts': rows})
