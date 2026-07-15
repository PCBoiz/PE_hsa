"""Port routes/quizzes.py — FE-06 quiz ôn tập cấp khóa (snapshot server-side)."""
import json
import random

from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from common.db import q, q1, x

MIN_QUESTIONS = 5
MAX_QUESTIONS = 10
DEFAULT_QUESTIONS = 8


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

        # step_2 của các bài user đã completed trong khóa này
        rows = q('''SELECT l.id AS lesson_id, l.lesson_code,
                           l.content_json->'step_2' AS q
                    FROM lessons l
                    JOIN lesson_progress lp
                      ON lp.lesson_id = l.id AND lp.user_id = %s
                     AND lp.status = 'completed'
                    WHERE l.course_id = %s
                      AND l.content_json IS NOT NULL
                      AND jsonb_exists(l.content_json, 'step_2')''', (uid, course_id))

        # step_2 có 2 dạng: {"mcq":[{question,options},...]} hoặc {question,options}
        pool = []

        def _add(lesson, qq):
            if isinstance(qq, dict) and qq.get('question') and isinstance(qq.get('options'), list):
                pool.append({
                    'lesson_id': lesson['lesson_id'],
                    'lesson_code': lesson['lesson_code'],
                    'question': qq['question'],
                    'options': qq['options'],
                })

        for r in rows:
            s2 = r['q']
            if isinstance(s2, str):
                try:
                    s2 = json.loads(s2)
                except ValueError:
                    continue
            if not isinstance(s2, dict):
                continue
            if isinstance(s2.get('mcq'), list):
                for item in s2['mcq']:
                    _add(r, item)
            else:
                _add(r, s2)

        if len(pool) < MIN_QUESTIONS:
            return Response({
                'error': 'Cần hoàn thành ít nhất 5 bài có câu hỏi để tạo quiz ôn tập.',
                'available': len(pool),
            }, status=400)

        n = min(num_questions, len(pool))
        picked = random.sample(pool, n)
        questions = [
            {
                'question_no': i + 1,
                'lesson_id': p['lesson_id'],
                'lesson_code': p['lesson_code'],
                'question': p['question'],
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
            quiz = q1('SELECT id, user_id, status, questions_json FROM quizzes WHERE id=%s',
                      (quiz_id,))
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
                explanation = next(
                    (o.get('explanation') for o in qq.get('options', [])
                     if o.get('id') == (selected if selected is not None else correct_answer)),
                    None)
                is_correct = selected is not None and selected == correct_answer
                if is_correct:
                    score += 1
                review.append({
                    'question_no': qno,
                    'question': qq.get('question'),
                    'your_answer': selected,
                    'correct_answer': correct_answer,
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
            x('INSERT INTO review_quiz_results (quiz_id, user_id, score, total, answers_json) '
              'VALUES (%s, %s, %s, %s, %s::jsonb)',
              (quiz_id, uid, score, total, json.dumps(answers_json, ensure_ascii=False)))
            x("UPDATE quizzes SET status='submitted' WHERE id=%s", (quiz_id,))

        return Response({
            'score': score,
            'total': total,
            'percentage': round(score * 100 / total) if total else 0,
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
