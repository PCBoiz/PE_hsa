"""Port routes/quizzes.py — FE-06 quiz ôn tập cấp khóa (snapshot server-side)."""
import json
import random

from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from common.clock import local_now, local_today
from common.db import q, q1, x
from common.events import KIND_REVIEW_QUIZ, record_event
from common.streak import award_xp, touch_streak

MIN_QUESTIONS = 5
MAX_QUESTIONS = 10
DEFAULT_QUESTIONS = 8

# ── THƯỞNG CHO QUIZ ÔN TẬP (anh Sơn duyệt 05/09/2026) ───────────────────────
#
# Cùng HÌNH DẠNG với thi thử — một phần cố định cho công sức, một phần theo tỉ lệ
# đúng — vì đó là luật anh đã chốt cho thi thử ngày 14/08 và hai thứ cùng loại
# thì không nên tính hai kiểu.
#
# Mốc để đối chiếu:
#     bài học    50 XP   (lý thuyết + kiểm tra + 8 câu phòng luyện)
#     thi thử    30 + tối đa 70 = 100   (150 câu, một buổi ngồi thật)
#     quiz ôn    10 + tối đa 20 =  30   ← 5–10 câu, ÔN LẠI thứ đã học
#
# Quiz ôn tập phải THẤP HƠN HẲN một bài học: nó bốc câu từ chính những bài em đã
# hoàn thành, tức em đã được thưởng cho việc học chúng lần đầu.
_QUIZ_XP_BASE = 10
_QUIZ_XP_MAX_BONUS = 20

#: Số lượt được TÍNH XP mỗi ngày. TRẦN NÀY LÀ ĐIỀU KIỆN, không phải tuỳ chọn:
#: `GenerateQuizView` không giới hạn số quiz, nên trong hạn mức 1000 request/giờ
#: một em sinh và nộp được hàng TRĂM lượt. Cộng XP mà không có trần là đẻ ra một
#: lỗ tệ hơn lỗ đang vá — bảng xếp hạng thành cuộc thi bấm nút.
#:
#: Ba lượt × 8 câu ≈ một bài học về khối lượng luyện tập, và 3 × 30 = 90 XP vẫn
#: dưới hai bài học. Lượt thứ tư trở đi VẪN được chấm, vẫn vào bản đồ năng lực,
#: vẫn tính chuỗi ngày — chỉ không cộng XP nữa.
_QUIZ_XP_MOI_NGAY = 3


def _xp_quiz(score, total):
    """XP của MỘT lượt quiz ôn tập. Cùng công thức với `mockexam._mock_xp`."""
    if not total:
        return _QUIZ_XP_BASE
    dung = max(0, min(score, total))
    return _QUIZ_XP_BASE + round(_QUIZ_XP_MAX_BONUS * dung / total)


def _con_quota_xp(uid, hom_nay):
    """Lượt này còn được tính XP không? Đếm CẢ lượt vừa ghi.

    Đếm ở `review_quiz_results` chứ không ở `learning_events`: bảng kia mới là sổ
    gốc của "em đã nộp mấy lượt hôm nay", còn dòng sự kiện tách theo CHỦ ĐỀ nên
    một lượt có thể thành nhiều dòng — đếm ở đó là đếm sai theo hướng chặn oan.
    """
    n = q1('SELECT COUNT(*) AS n FROM review_quiz_results '
           'WHERE user_id=%s AND submitted_at::date = %s', (uid, hom_nay))['n']
    return int(n or 0) <= _QUIZ_XP_MOI_NGAY



def _record_quiz_events(uid, quiz_id, course_id, questions, selected_by_no, now, xp=0):
    """Một lượt quiz ôn tập → MỘT sự kiện cho MỖI chủ đề có trong lượt đó.

    Quiz ôn tập bốc câu từ các bài đã học, mỗi bài thuộc một chủ đề khác nhau.
    Ghi gộp cả lượt thành một điểm số sẽ mất chính cái thông tin đáng giá nhất:
    "nhớ Hình học 2/5 nhưng nhớ Số học 4/4". Vì thế tách theo chủ đề ngay lúc
    ghi. Các dòng của cùng một lượt cộng lại vẫn ra đúng điểm tổng.
    """
    ids = {qq.get('lesson_id') for qq in questions if qq.get('lesson_id')}
    if not ids:
        return
    topic_of = {r['id']: r['module'] for r in q(
        'SELECT id, module FROM lessons WHERE id = ANY(%s)', (list(ids),))}

    per_topic = {}
    for qq in questions:
        topic = (topic_of.get(qq.get('lesson_id')) or '').strip()
        if not topic:
            continue           # bài chưa gắn chương mục → không quy được chủ đề
        correct_id = next((o.get('id') for o in qq.get('options', []) if o.get('correct')), None)
        bucket = per_topic.setdefault(topic, [0, 0])
        bucket[1] += 1
        if selected_by_no.get(qq.get('question_no')) == correct_id:
            bucket[0] += 1

    # XP đặt lên ĐÚNG MỘT dòng, không phải mỗi dòng.
    #
    # Một lượt quiz thành nhiều dòng sự kiện (một cho mỗi chủ đề). `xp` là
    # trường "XP của sự kiện này", nên ghi đủ số lên từng dòng là biến một lượt
    # 30 XP thành 90 XP với bất kỳ báo cáo nào cộng cột ấy — hôm nay chưa có báo
    # cáo nào cộng, nhưng cột ấy tồn tại đúng để được cộng.
    #
    # Sắp xếp chủ đề để chọn dòng mang XP một cách XÁC ĐỊNH: thứ tự của `dict`
    # theo thứ tự chèn, tức theo thứ tự câu hỏi bốc ngẫu nhiên — cùng một lượt
    # chạy lại có thể chọn dòng khác, và một con số nhảy chỗ giữa hai lần đọc là
    # thứ không ai truy được.
    for i, topic in enumerate(sorted(per_topic)):
        correct, n = per_topic[topic]
        record_event(
            uid, KIND_REVIEW_QUIZ, f'quiz:{quiz_id}:{topic}',
            occurred_at=now, course_id=course_id, topic=topic,
            ref_type='quiz', ref_id=str(quiz_id),
            score=correct, max_score=n, xp=(xp if i == 0 else 0),
            meta={'quizId': quiz_id},
        )


def pool_cau_hoi(uid, course_id):
    """Kho câu hỏi ôn tập của một học viên trong một khoá.

    NƠI DUY NHẤT trả lời "em đã đủ điều kiện làm quiz ôn tập chưa". Trước
    31/08/2026 câu hỏi ấy có BA câu trả lời khác nhau trong repo:

      · `quizzes/views` kiểm số CÂU HỎI trong kho (`len(pool) < 5`);
      · thông báo lỗi của chính nó nói "hoàn thành ít nhất 5 BÀI";
      · `stats/ReviewQuizStatusView` thì gác bằng CHUỖI NGÀY (`streak >= 5`) —
        một thứ không liên quan gì tới việc em đã học đủ chưa, và endpoint ấy
        cũng không có nơi nào gọi (rà cả frontend: 0 kết quả).

    Ba phát biểu cho một luật là hai phát biểu sai.
    """
    # Câu hỏi lấy từ các bài học viên ĐÃ HOÀN THÀNH trong khoá này.
    #
    # Bản cũ đọc content_json->'step_2' — đó là schema bài học của pe_test
    # (5 bước, MCQ nằm ở step_2). Bài HSA để câu hỏi ở test.questions và
    # drill.questions, nên quiz ôn tập KHÔNG BAO GIỜ tìm thấy câu nào:
    # endpoint luôn trả 400 "available: 0" và tính năng chết hẳn
    # (audit 2026-08-19). Nay đọc đúng chỗ, vẫn giữ nhánh step_2 cho dữ
    # liệu cũ nếu có.
    rows = q('''SELECT l.id AS lesson_id,
                       COALESCE(l.lesson_code, l.content_json->>'id') AS lesson_code,
                       l.content_json AS cj
                FROM lessons l
                JOIN lesson_progress lp
                  ON lp.lesson_id = l.id AND lp.user_id = %s
                 AND lp.status = 'completed'
                WHERE l.course_id = %s
                  AND l.content_json IS NOT NULL''', (uid, course_id))

    pool = []

    def _add_pe_test(lesson, qq):
        """Dạng pe_test: options đã là [{id, text, correct}]."""
        if isinstance(qq, dict) and qq.get('question') and isinstance(qq.get('options'), list):
            pool.append({
                'lesson_id': lesson['lesson_id'],
                'lesson_code': lesson['lesson_code'],
                'question': qq['question'],
                'explain': qq.get('explain'),
                'options': qq['options'],
            })

    def _add_hsa(lesson, qq):
        """Dạng HSA: options là mảng chuỗi + trường answer riêng.

        Quy về dạng [{id, text, correct}] mà phần chấm điểm đang dùng.
        Bỏ câu điền đáp án: quiz ôn tập chỉ chấm trắc nghiệm.
        """
        if not isinstance(qq, dict):
            return
        if qq.get('type') not in (None, 'mcq'):
            return
        opts, ans = qq.get('options'), qq.get('answer')
        if not qq.get('question') or not isinstance(opts, list) or len(opts) < 2:
            return
        if ans is None or ans not in opts:
            return
        pool.append({
            'lesson_id': lesson['lesson_id'],
            'lesson_code': lesson['lesson_code'],
            'question': qq['question'],
            # Lời giải của dạng HSA nằm ở CẤP CÂU HỎI (`explain`), không nằm
            # trong từng lựa chọn như dạng pe_test. Bản cũ chỉ tìm
            # `option.explanation` nên với mọi câu HSA nó LUÔN ra None —
            # tức phần xem lại của quiz ôn tập chưa bao giờ giải thích gì.
            'explain': qq.get('explain'),
            'options': [
                {'id': f'o{i + 1}', 'text': str(o), 'correct': (o == ans)}
                for i, o in enumerate(opts)
            ],
        })

    for r in rows:
        cj = r['cj']
        if isinstance(cj, str):
            try:
                cj = json.loads(cj)
            except ValueError:
                continue
        if not isinstance(cj, dict):
            continue

        for khoi in ('test', 'drill'):
            block = cj.get(khoi)
            if isinstance(block, dict) and isinstance(block.get('questions'), list):
                for item in block['questions']:
                    _add_hsa(r, item)

        s2 = cj.get('step_2')
        if isinstance(s2, dict):
            if isinstance(s2.get('mcq'), list):
                for item in s2['mcq']:
                    _add_pe_test(r, item)
            else:
                _add_pe_test(r, s2)
    return pool


class GenerateQuizView(APIView):
    def post(self, request, course_id):
        data = request.data if isinstance(request.data, dict) else {}
        num_questions = data.get('num_questions')
        if not isinstance(num_questions, int):
            num_questions = DEFAULT_QUESTIONS
        num_questions = max(MIN_QUESTIONS, min(MAX_QUESTIONS, num_questions))

        uid = request.user.id
        course = q1('SELECT id FROM courses WHERE id=%s', (course_id,))
        if not course:
            return Response({'error': 'Không tìm thấy khóa học'}, status=404)

        pool = pool_cau_hoi(uid, course_id)

        if len(pool) < MIN_QUESTIONS:
            # Nói đúng thứ đang được kiểm (SỐ CÂU, không phải số bài) và nói em
            # đang có bao nhiêu. Câu cũ — "hoàn thành ít nhất 5 bài có câu hỏi"
            # — sai theo cả hai chiều: một bài có 8 câu là đủ, còn 5 bài mỗi bài
            # một câu điền cũng vẫn không đủ.
            return Response({
                'error': 'Cần ít nhất %d câu trắc nghiệm từ các bài đã học để tạo quiz ôn '
                         'tập. Hiện có %d — học thêm vài bài nữa rồi quay lại.'
                         % (MIN_QUESTIONS, len(pool)),
                'available': len(pool),
                'needed': MIN_QUESTIONS,
            }, status=400)

        n = min(num_questions, len(pool))
        picked = random.sample(pool, n)
        questions = [
            {
                'question_no': i + 1,
                'lesson_id': p['lesson_id'],
                'lesson_code': p['lesson_code'],
                'question': p['question'],
                'explain': p.get('explain'),
                'options': p['options'],
            }
            for i, p in enumerate(picked)
        ]

        row = q1('''INSERT INTO quizzes (user_id, course_id, status, questions_json)
                    VALUES (%s, %s, 'generated', %s::jsonb) RETURNING id''',
                 (uid, course_id, json.dumps(questions, ensure_ascii=False)))
        quiz_id = row['id']

        # PHẢI lọc bỏ field "correct" trước khi trả cho FE
        safe_questions = [
            {
                'question_no': qq['question_no'],
                'lesson_code': qq['lesson_code'],
                'question': qq['question'],
                'options': [{'id': o.get('id'), 'text': o.get('text')} for o in qq['options']],
            }
            for qq in questions
        ]
        return Response({
            'quiz_id': quiz_id,
            'course_id': course_id,
            'total': len(safe_questions),
            'questions': safe_questions,
        })


class SubmitQuizView(APIView):
    def post(self, request, quiz_id):
        data = request.data if isinstance(request.data, dict) else {}
        answers = data.get('answers')
        if not isinstance(answers, list):
            return Response({'error': 'Thiếu hoặc sai định dạng answers'}, status=400)

        selected_by_no = {}
        for a in answers:
            if isinstance(a, dict) and isinstance(a.get('question_no'), int):
                selected_by_no[a['question_no']] = a.get('selected')

        uid = request.user.id
        with transaction.atomic():
            quiz = q1('SELECT id, user_id, course_id, status, questions_json '
                      'FROM quizzes WHERE id=%s', (quiz_id,))
            if not quiz:
                return Response({'error': 'Không tìm thấy quiz'}, status=404)
            if quiz['user_id'] != uid:
                return Response({'error': 'Quiz này không thuộc về bạn'}, status=403)
            if quiz['status'] == 'submitted':
                return Response({'error': 'Quiz này đã nộp rồi'}, status=409)

            questions = quiz['questions_json'] or []
            if isinstance(questions, str):
                questions = json.loads(questions)
            score = 0
            review = []
            answers_json = []
            for qq in questions:
                qno = qq.get('question_no')
                selected = selected_by_no.get(qno)
                correct_answer = next(
                    (o.get('id') for o in qq.get('options', []) if o.get('correct')), None)
                # Lời giải: cấp CÂU HỎI trước (dạng HSA), rồi mới tới cấp lựa
                # chọn (dạng pe_test). Bản cũ chỉ có vế sau nên câu HSA nào cũng
                # ra None.
                explanation = qq.get('explain') or next(
                    (o.get('explanation') for o in qq.get('options', [])
                     if o.get('id') == (selected if selected is not None else correct_answer)),
                    None)
                is_correct = selected is not None and selected == correct_answer
                if is_correct:
                    score += 1
                # CHỮ chứ không phải MÃ lựa chọn. Bản cũ trả `o1`/`o2` và giao
                # diện in thẳng ra: "Bạn chọn: o1 — Đáp án đúng: o2". Không ai
                # đọc được đó là gì, kể cả người vừa làm bài xong.
                chu = {o.get('id'): o.get('text') for o in qq.get('options', [])}
                review.append({
                    'question_no': qno,
                    'question': qq.get('question'),
                    'your_answer': selected,
                    'correct_answer': correct_answer,
                    'your_answer_text': chu.get(selected),
                    'correct_answer_text': chu.get(correct_answer),
                    'is_correct': is_correct,
                    'explanation': explanation,
                })
                answers_json.append({
                    'question_no': qno,
                    'question': qq.get('question'),
                    'selected': selected,
                    'correct_answer': correct_answer,
                    'is_correct': is_correct,
                })

            total = len(questions)
            # submitted_at ghi thẳng giờ Việt Nam thay vì để DEFAULT now() của
            # Postgres (Neon trả UTC — lệch 7 tiếng, đúng cái bẫy từng làm nhiệm
            # vụ ngày đếm sai hồi 14/08).
            now = local_now()
            x('INSERT INTO review_quiz_results '
              '(quiz_id, user_id, score, total, answers_json, submitted_at) '
              'VALUES (%s, %s, %s, %s, %s::jsonb, %s)',
              (quiz_id, uid, score, total,
               json.dumps(answers_json, ensure_ascii=False), now))
            x("UPDATE quizzes SET status='submitted' WHERE id=%s", (quiz_id,))

            # ── XP, CÓ TRẦN THEO NGÀY (anh Sơn duyệt 05/09/2026) ───────────
            #
            # Trần đếm ở `review_quiz_results`, SAU khi dòng của lượt này đã ghi
            # — nên lượt thứ tư trong ngày là lượt đầu tiên không được cộng.
            #
            # Lượt quá trần VẪN được chấm, vẫn vào bản đồ năng lực, vẫn tính
            # chuỗi ngày. Chỉ XP dừng lại. Ôn thêm là việc tốt; thưởng thêm cho
            # việc bấm nút thì không.
            hom_nay = local_today()
            xp = _xp_quiz(score, total) if _con_quota_xp(uid, hom_nay) else 0

            _record_quiz_events(uid, quiz_id, quiz.get('course_id'), questions,
                                selected_by_no, now, xp=xp)
            award_xp(uid, xp, hom_nay)

            # ── LÀM QUIZ ÔN TẬP LÀ CÓ HỌC HÔM NAY (vá 04/09/2026) ───────────
            #
            # Ba đường chấm điểm anh em, và trước hôm nay chỉ hai đường đếm vào
            # chuỗi ngày:
            #
            #     lessons/views.py   award_xp + touch_streak
            #     mockexam/views.py  award_xp + touch_streak
            #     quizzes/views.py   — KHÔNG GỌI CÁI NÀO
            #
            # Đây KHÔNG phải luật mới: ĐÚNG lỗi này đã vá cho thi thử ngày
            # 14/08/2026, kèm nguyên văn lý do — "làm trọn một đề 150 câu vẫn
            # mất chuỗi nếu hôm đó không mở bài học". Quiz ôn tập là anh em thứ
            # ba và bị bỏ sót. `touch_streak` tự khai nghĩa của nó: "ghi nhận
            # HÔM NAY CÓ HỌC".
            #
            # CHỈ chuỗi, CHƯA XP. `GenerateQuizView` không có trần theo ngày —
            # trong hạn mức 1000 request/giờ, một em sinh và nộp được hàng trăm
            # quiz. Cộng XP khi chưa có trần là đẻ ra lỗ tệ hơn lỗ đang vá; con
            # số thưởng và hình dạng trần là quyết định của anh Sơn (mọi mốc XP
            # khác trong repo đều do anh chốt). Đã ghi TODO.
            #
            # `touch_streak` KHÔNG cần trần: nó chỉ đặt "đã học hôm nay", gọi
            # bao nhiêu lần trong ngày cũng ra cùng một kết quả.
            touch_streak(uid, hom_nay)

        return Response({
            'score': score,
            'total': total,
            'percentage': round(score * 100 / total) if total else 0,
            # Trả XP về để màn hình nói ĐÚNG con số máy chủ vừa cộng, thay vì tự
            # đoán. `xpDaTran` cho phép giao diện giải thích vì sao lượt này 0 XP
            # — im lặng cho 0 XP trông y hệt một lỗi.
            'xpGained': xp,
            'xpDaTran': xp == 0,
            'xpMoiNgay': _QUIZ_XP_MOI_NGAY,
            'review': review,
        })


class QuizView(APIView):
    def get(self, request, quiz_id):
        """Đọc lại 1 quiz của chính user — kèm kết quả nếu đã nộp."""
        uid = request.user.id
        quiz = q1('SELECT id, user_id, course_id, status, questions_json, created_at '
                  'FROM quizzes WHERE id=%s', (quiz_id,))
        if not quiz or quiz['user_id'] != uid:
            # 404 cho cả quiz người khác — không lộ quiz nào tồn tại
            return Response({'error': 'Không tìm thấy quiz'}, status=404)

        out = {
            'quiz_id': quiz['id'],
            'course_id': quiz['course_id'],
            'status': quiz['status'],
            'created_at': quiz['created_at'].isoformat() if quiz['created_at'] else None,
        }
        questions_json = quiz['questions_json'] or []
        if isinstance(questions_json, str):
            questions_json = json.loads(questions_json)
        if quiz['status'] == 'submitted':
            result = q1('''SELECT score, total, answers_json, submitted_at
                           FROM review_quiz_results WHERE quiz_id=%s
                           ORDER BY submitted_at DESC LIMIT 1''', (quiz_id,))
            if result:
                out['result'] = {
                    'score': result['score'],
                    'total': result['total'],
                    'percentage': round(result['score'] * 100 / result['total'])
                                  if result['total'] else 0,
                    'review': result['answers_json'],
                    'submitted_at': result['submitted_at'].isoformat()
                                    if result['submitted_at'] else None,
                }
        else:
            out['questions'] = [
                {
                    'question_no': qq.get('question_no'),
                    'lesson_code': qq.get('lesson_code'),
                    'question': qq.get('question'),
                    'options': [{'id': o.get('id'), 'text': o.get('text')}
                                for o in qq.get('options', [])],
                }
                for qq in questions_json
            ]
            out['total'] = len(questions_json)
        return Response(out)


class QuizHistoryView(APIView):
    def get(self, request, course_id):
        """Lịch sử các lượt quiz ôn tập đã nộp của user trong 1 khóa."""
        rows = q('''SELECT r.quiz_id, r.score, r.total, r.submitted_at
                    FROM review_quiz_results r
                    JOIN quizzes q ON q.id = r.quiz_id
                    WHERE r.user_id = %s AND q.course_id = %s
                    ORDER BY r.submitted_at DESC
                    LIMIT 50''', (request.user.id, course_id))
        return Response({'history': [
            {
                'quiz_id': r['quiz_id'],
                'score': r['score'],
                'total': r['total'],
                'percentage': round(r['score'] * 100 / r['total']) if r['total'] else 0,
                'submitted_at': r['submitted_at'].isoformat() if r['submitted_at'] else None,
            }
            for r in rows
        ]})
