"""backfill_learning_events — nạp dữ liệu học tập ĐÃ CÓ vào dòng sự kiện.

``learning_events`` ra đời sau khi học viên đã học bài, thi thử và nhận nhiệm
vụ. Không nạp lại thì bản đồ năng lực mở ra trống trơn với đúng những người đã
dùng sản phẩm lâu nhất — ấn tượng tệ nhất có thể.

An toàn khi chạy lại: mọi sự kiện có ``dedup_key`` cố định suy ra từ khoá chính
của dữ liệu gốc, nên lần chạy thứ hai chỉ cập nhật lại đúng những dòng cũ.

    python manage.py backfill_learning_events            # cả hệ thống
    python manage.py backfill_learning_events --user 3   # một học viên
    python manage.py backfill_learning_events --dry-run  # chỉ đếm, không ghi

KHÔNG nạp được (và cố ý không đoán):
  · Phòng luyện tốc độ trước 24/08 — kết quả chưa từng được gửi về máy chủ.
  · Chủ đề của quiz ôn tập mà bài nguồn chưa gắn chương mục.
Thà thiếu dữ liệu còn hơn bịa ra số đo.
"""
import json
from datetime import datetime

from django.core.management.base import BaseCommand

from common.clock import local_now
from common.db import q
from common.events import (KIND_LESSON, KIND_MISSION, KIND_MOCK,
                           KIND_MOCK_SECTION, KIND_REVIEW_QUIZ, record_event)

#: Nhãn hợp phần trong section_scores_json → khoá học. PHẢI khớp
#: mockexam/views.py:SECTION_LABELS; lệch một dấu là cả hợp phần biến mất.
LABEL_COURSE = {
    'Định lượng': 'hsa_quantitative',
    'Định tính': 'hsa_verbal',
    'Khoa học': 'hsa_science',
    # Khoá tiếng Anh cũng nhận, phòng dữ liệu ghi trước khi có nhãn tiếng Việt.
    'quantitative': 'hsa_quantitative',
    'verbal': 'hsa_verbal',
    'science': 'hsa_science',
}


def _as_json(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return None
    return value


def _when(value, fallback):
    return value if isinstance(value, datetime) else fallback


class Command(BaseCommand):
    help = ('Nạp lesson_progress / mock_attempts / review_quiz_results / user_missions '
            'vào learning_events. Chạy lại được nhiều lần.')

    def add_arguments(self, parser):
        parser.add_argument('--user', type=int, default=None, help='Chỉ nạp cho một user_id.')
        parser.add_argument('--dry-run', action='store_true', help='Chỉ đếm, không ghi gì.')

    def handle(self, *args, **opts):
        self.uid_filter = opts.get('user')
        self.dry = opts.get('dry_run')
        self.now = local_now()
        self.counts = {}

        self._lessons()
        self._mocks()
        self._quizzes()
        self._missions()

        for kind, n in sorted(self.counts.items()):
            self.stdout.write('  · %s: %d' % (kind, n))
        head = '[DRY-RUN] ' if self.dry else ''
        self.stdout.write(self.style.SUCCESS(
            '%sbackfill_learning_events: %d sự kiện' % (head, sum(self.counts.values()))))

    # ── tiện ích ────────────────────────────────────────────────────────────
    def _emit(self, kind, *a, **kw):
        self.counts[kind] = self.counts.get(kind, 0) + 1
        if not self.dry:
            record_event(*a, **kw)

    def _where_user(self, col):
        return (' AND %s=%%s' % col, (self.uid_filter,)) if self.uid_filter else ('', ())

    # ── nguồn 1: bài học ────────────────────────────────────────────────────
    def _lessons(self):
        cond, params = self._where_user('lp.user_id')
        rows = q('''SELECT lp.user_id, lp.lesson_id, lp.course_id, lp.quiz_score,
                           lp.xp_earned, lp.completed_at,
                           l.module, l.title, l.sort_order, l.estimated_minutes
                    FROM lesson_progress lp
                    LEFT JOIN lessons l ON l.id = lp.lesson_id
                    WHERE lp.status = 'completed' ''' + cond, params)
        for r in rows:
            self._emit(
                KIND_LESSON, r['user_id'], KIND_LESSON, 'lesson:%s' % r['lesson_id'],
                occurred_at=_when(r['completed_at'], self.now),
                course_id=r['course_id'], topic=(r['module'] or None),
                ref_type='lesson', ref_id=str(r['lesson_id']),
                score=r['quiz_score'],
                max_score=(100 if r['quiz_score'] is not None else None),
                minutes=r['estimated_minutes'], xp=r['xp_earned'] or 0,
                meta={'lessonNo': r['sort_order'], 'title': r['title'] or '', 'backfill': True},
            )

    # ── nguồn 2: thi thử ────────────────────────────────────────────────────
    def _mocks(self):
        cond, params = self._where_user('user_id')
        rows = q('''SELECT id, user_id, exam_id, score, total, section_scores_json,
                           duration_seconds, submitted_at
                    FROM mock_attempts WHERE TRUE''' + cond, params)
        for r in rows:
            when = _when(r['submitted_at'], self.now)
            minutes = max(1, round((r['duration_seconds'] or 0) / 60)) or None
            self._emit(
                KIND_MOCK, r['user_id'], KIND_MOCK, 'mock:%s' % r['id'],
                occurred_at=when, ref_type='mock_attempt', ref_id=str(r['id']),
                score=r['score'], max_score=r['total'], minutes=minutes,
                meta={'examId': r['exam_id'], 'backfill': True},
            )
            sections = _as_json(r['section_scores_json'])
            if not isinstance(sections, dict):
                continue
            for label, sc in sections.items():
                course_id = LABEL_COURSE.get(label)
                if not course_id or not isinstance(sc, dict) or not sc.get('total'):
                    continue
                # dedup_key dùng course_id (không dùng nhãn) để trùng khớp với
                # bản ghi trực tiếp của mockexam/views.py, kể cả khi nhãn đổi.
                self._emit(
                    KIND_MOCK_SECTION, r['user_id'], KIND_MOCK_SECTION,
                    'mocksec:%s:%s' % (r['id'], course_id),
                    occurred_at=when, course_id=course_id,
                    ref_type='mock_attempt', ref_id=str(r['id']),
                    score=sc.get('correct', 0), max_score=sc['total'],
                    meta={'examId': r['exam_id'], 'section': label, 'backfill': True},
                )

    # ── nguồn 3: quiz ôn tập ────────────────────────────────────────────────
    def _quizzes(self):
        cond, params = self._where_user('r.user_id')
        rows = q('''SELECT r.quiz_id, r.user_id, r.answers_json, r.submitted_at,
                           z.course_id, z.questions_json
                    FROM review_quiz_results r
                    JOIN quizzes z ON z.id = r.quiz_id
                    WHERE TRUE''' + cond, params)
        for r in rows:
            questions = _as_json(r['questions_json']) or []
            answers = _as_json(r['answers_json']) or []
            if not questions:
                continue
            # answers_json đã giữ sẵn is_correct — khỏi chấm lại, khỏi lệch luật.
            correct_by_no = {a.get('question_no'): bool(a.get('is_correct'))
                             for a in answers if isinstance(a, dict)}
            ids = [qq.get('lesson_id') for qq in questions if qq.get('lesson_id')]
            topic_of = {}
            if ids:
                topic_of = {t['id']: t['module'] for t in q(
                    'SELECT id, module FROM lessons WHERE id = ANY(%s)', (list(set(ids)),))}

            per_topic = {}
            for qq in questions:
                topic = (topic_of.get(qq.get('lesson_id')) or '').strip()
                if not topic:
                    continue
                bucket = per_topic.setdefault(topic, [0, 0])
                bucket[1] += 1
                if correct_by_no.get(qq.get('question_no')):
                    bucket[0] += 1
            for topic, (ok, n) in per_topic.items():
                self._emit(
                    KIND_REVIEW_QUIZ, r['user_id'], KIND_REVIEW_QUIZ,
                    'quiz:%s:%s' % (r['quiz_id'], topic),
                    occurred_at=_when(r['submitted_at'], self.now),
                    course_id=r['course_id'], topic=topic,
                    ref_type='quiz', ref_id=str(r['quiz_id']),
                    score=ok, max_score=n,
                    meta={'quizId': r['quiz_id'], 'backfill': True},
                )

    # ── nguồn 4: nhiệm vụ ngày ──────────────────────────────────────────────
    def _missions(self):
        cond, params = self._where_user('um.user_id')
        rows = q('''SELECT um.user_id, um.mission_id, um.mission_date, um.xp_earned,
                           um.claimed_at, m.code, m.title
                    FROM user_missions um
                    LEFT JOIN missions m ON m.id = um.mission_id
                    WHERE TRUE''' + cond, params)
        for r in rows:
            self._emit(
                KIND_MISSION, r['user_id'], KIND_MISSION,
                'mission:%s:%s' % (r['mission_id'], r['mission_date']),
                occurred_at=_when(r['claimed_at'], self.now),
                # claimed_at cũ ghi bằng now() của Postgres = UTC, lệch giờ Việt
                # Nam 7 tiếng nên nhận thưởng lúc 1h sáng bị đẩy về hôm trước.
                # mission_date thì đã đi qua local_today() — dùng nó làm ngày.
                event_date=r['mission_date'],
                ref_type='mission', ref_id=str(r['mission_id']),
                xp=r['xp_earned'] or 0,
                meta={'code': r['code'], 'title': r['title'], 'backfill': True},
            )
