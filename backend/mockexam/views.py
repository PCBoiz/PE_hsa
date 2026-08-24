"""Trụ cột ④ — Thi thử CBT. Raw SQL qua common/db (đồng bộ style toàn app)."""
import json
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from achievements.services import check_and_award_achievements
from common.clock import local_now, local_today
from common.db import q, q1, x
from common.events import KIND_MOCK, KIND_MOCK_SECTION, record_event
from common.streak import award_xp, touch_streak

#: XP cho một lượt thi thử: 30 XP công sức + tối đa 70 XP theo tỉ lệ đúng.
#: Trần 100 để một đề không bằng cả buổi học (mỗi bài học 50 XP).
_MOCK_XP_BASE = 30
_MOCK_XP_MAX_BONUS = 70


def _mock_xp(score, total):
    if not total:
        return _MOCK_XP_BASE
    return _MOCK_XP_BASE + round(_MOCK_XP_MAX_BONUS * max(0, min(score, total)) / total)

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


class MockExamDetailView(APIView):
    """GET /api/mock-exams/<id> — câu hỏi (ĐÃ bỏ đáp án đúng)."""
    def get(self, request, exam_id):
        exam = q1("SELECT id, title, description, duration_minutes, total_questions, questions_json "
                  "FROM mock_exams WHERE id=%s AND is_published=TRUE", (exam_id,))
        if not exam:
            return Response({'error': 'Không tìm thấy đề thi'}, status=404)
        items = []
        for it in _questions(exam):
            items.append({
                'id': it.get('id'),
                'section': it.get('section'),
                'section_label': SECTION_LABELS.get(it.get('section'), it.get('section')),
                'type': it.get('type', 'mcq'),
                'question': it.get('question'),
                'options': it.get('options', []),
            })
        return Response({
            'id': exam['id'], 'title': exam['title'], 'description': exam['description'],
            'duration_minutes': exam['duration_minutes'],
            'total_questions': exam['total_questions'] or len(items),
            'questions': items,
        })


class MockSubmitView(APIView):
    """POST /api/mock-exams/<id>/submit — body {answers:{qid:val}, duration_seconds}.
    Chấm điểm, lưu attempt, trả điểm + phân tích theo hợp phần + hợp phần yếu nhất."""
    def post(self, request, exam_id):
        exam = q1("SELECT id, questions_json FROM mock_exams WHERE id=%s", (exam_id,))
        if not exam:
            return Response({'error': 'Không tìm thấy đề thi'}, status=404)
        data = request.data if isinstance(request.data, dict) else {}
        answers = data.get('answers') or {}
        try:
            duration = int(data.get('duration_seconds') or 0)
        except (TypeError, ValueError):
            duration = 0

        items = _questions(exam)
        sec_total, sec_correct, results, score = {}, {}, [], 0
        for it in items:
            qid, sec = it.get('id'), it.get('section', '')
            correct, ua = it.get('answer'), answers.get(it.get('id'))
            ok = ua is not None and str(ua) != '' and _norm(ua) == _norm(correct)
            sec_total[sec] = sec_total.get(sec, 0) + 1
            if ok:
                score += 1
                sec_correct[sec] = sec_correct.get(sec, 0) + 1
            results.append({'id': qid, 'correct': ok, 'answer': correct, 'your': ua})

        total = len(items)
        section_scores = {
            SECTION_LABELS.get(s, s): {'correct': sec_correct.get(s, 0), 'total': sec_total.get(s, 0)}
            for s in sec_total
        }
        weakest = None
        if section_scores:
            weakest = min(
                section_scores.items(),
                key=lambda kv: (kv[1]['correct'] / kv[1]['total']) if kv[1]['total'] else 1.0,
            )[0]

        uid = request.user.id
        with transaction.atomic():
            now = local_now()
            attempt = q1("INSERT INTO mock_attempts "
                         "(user_id, exam_id, score, total, section_scores_json, answers_json, "
                         " duration_seconds, submitted_at) "
                         "VALUES (%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s) RETURNING id",
                         (uid, exam_id, score, total,
                          json.dumps(section_scores, ensure_ascii=False),
                          json.dumps(answers, ensure_ascii=False), duration, now))
            attempt_id = (attempt or {}).get('id')

            # Trước 2026-08-14 thi thử KHÔNG cộng XP và KHÔNG tính vào chuỗi:
            # làm trọn một đề 150 câu vẫn mất chuỗi nếu hôm đó không mở bài học.
            # Thưởng gồm phần cố định cho công sức + phần theo số câu đúng.
            xp = _mock_xp(score, total)
            today = local_today()
            award_xp(uid, xp, today)
            streak, used_freeze = touch_streak(uid, today)

            # ── Dòng sự kiện học tập ────────────────────────────────────────
            # Hai loại sự kiện cho CÙNG một lượt thi, mỗi loại một người đọc:
            #   · `mock`         — tổng cả đề, nuôi đường cong tiến bộ.
            #   · `mock_section` — điểm từng hợp phần, nuôi bản đồ năng lực.
            # Bên đọc chọn đúng một loại nên không bao giờ cộng trùng một lượt.
            _record_mock_events(uid, attempt_id, exam_id, score, total,
                                sec_correct, sec_total, duration, xp, now)

            newly = check_and_award_achievements(uid)

        return Response({
            'score': score, 'total': total,
            'section_scores': section_scores, 'weakest': weakest, 'results': results,
            'xpGained': xp, 'streak': streak, 'usedStreakFreeze': used_freeze,
            'newAchievements': newly,
        })


class MockAttemptsView(APIView):
    """GET /api/mock-attempts — lịch sử làm bài của user."""
    def get(self, request):
        # section_scores_json: Trang của tôi dựng "độ chính xác theo hợp phần"
        # từ đây, khỏi phải gọi lại từng lượt thi (audit 2026-08-15).
        rows = q("SELECT a.id, a.exam_id, e.title, a.score, a.total, a.duration_seconds, "
                 "a.section_scores_json, a.submitted_at "
                 "FROM mock_attempts a JOIN mock_exams e ON e.id = a.exam_id "
                 "WHERE a.user_id=%s ORDER BY a.submitted_at DESC LIMIT 20", (request.user.id,))
        for r in rows:
            sa = r.get('submitted_at')
            r['submitted_at'] = sa.isoformat() if sa else None
        return Response({'attempts': rows})
