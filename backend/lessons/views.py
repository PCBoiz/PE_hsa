"""Port routes/lessons.py — API tiến độ bài học (nguồn thật: lesson_progress)."""
import logging

from django.core.cache import cache
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from achievements.services import check_and_award_achievements
from common.clock import local_now, local_today
from common.db import q1, x
from common.events import KIND_DRILL, KIND_LESSON, record_event
from lessons.content import course_content, one_lesson
from lessons.grading import PHAN_CO_CAU_HOI, cham, phan_tram
from common.streak import award_xp, touch_streak

logger = logging.getLogger(__name__)


def _resolve_lesson_id(course_id, lesson_no, title, module=None):
    """Tìm lesson theo (course_id, sort_order); chưa có thì tạo stub giữ FK hợp lệ.

    Trả về ``(lesson_id, module)``. Trả kèm module vì dòng sự kiện học tập cần
    chủ đề của bài để chấm năng lực, mà client không phải lúc nào cũng gửi lên
    (bài cũ, hoặc engine khác).

    Nội dung bài HSA nằm trong JS phía client, bảng ``lessons`` chỉ giữ stub cho
    khoá ngoại. Vẫn phải ghi ``module``: trang Kỹ năng lọc
    ``WHERE module <> '' AND module IS NOT NULL``, nên stub thiếu module khiến
    trang đó rỗng vĩnh viễn dù học viên học bao nhiêu bài (audit 2026-08-15).
    """
    module = (module or '').strip()[:120] or None
    row = q1('SELECT id, module FROM lessons WHERE course_id=%s AND sort_order=%s LIMIT 1',
             (course_id, lesson_no))
    if row:
        # Stub tạo trước khi client biết gửi module → bổ sung ngược lại.
        if module and not row.get('module'):
            x('UPDATE lessons SET module=%s WHERE id=%s', (module, row['id']))
        return row['id'], (module or row.get('module') or None)
    row = q1('INSERT INTO lessons (course_id, title, sort_order, module) '
             'VALUES (%s, %s, %s, %s) RETURNING id',
             (course_id, title or f'Bài {lesson_no}', lesson_no, module))
    return row['id'], module


def _record_drill(uid, drill, lesson_id, lesson_no, course_id, topic, now):
    """Ghi kết quả phòng luyện tốc độ thành một sự kiện riêng.

    Phòng luyện đo thứ mà bài kiểm tra đầu vào không đo được: TỐC ĐỘ xử lý dưới
    đồng hồ đếm ngược — đúng thứ kỳ thi HSA chấm. Trước đây kết quả này chỉ hiện
    trên màn hình rồi biến mất, không có nơi nào lưu.

    Chấm trên TỔNG số câu chứ không phải số câu kịp làm: hết giờ mà chưa xong
    cũng là một kết quả trong bài thi tính giờ, và đó chính là thứ phòng luyện
    đo. Số câu kịp làm vẫn giữ trong meta để đọc lại được.

    Dữ liệu do client gửi nên phải kẹp biên: số câu đúng không vượt tổng số câu,
    tổng số câu có trần, thời lượng không âm.
    """
    if not isinstance(drill, dict):
        return
    try:
        total = int(drill.get('total') or 0)
        correct = int(drill.get('correct') or 0)
    except (TypeError, ValueError):
        return
    if total <= 0 or total > 100:
        return
    correct = max(0, min(correct, total))
    try:
        seconds = int(drill.get('seconds') or 0)
    except (TypeError, ValueError):
        seconds = 0
    minutes = max(0, min(120, round(seconds / 60))) or None
    record_event(
        uid, KIND_DRILL, f'drill:{lesson_id}',
        occurred_at=now, course_id=course_id, topic=topic,
        ref_type='lesson', ref_id=str(lesson_id),
        score=correct, max_score=total, minutes=minutes,
        meta={'lessonNo': lesson_no, 'maxCombo': drill.get('maxCombo'),
              # Số câu KỊP làm: phân biệt "làm chậm" với "làm sai" khi đọc lại.
              'answered': drill.get('answered')},
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
        quiz_score = None
        if isinstance(answers, dict):
            _, dung, tong = cham(course_id, lesson_no, 'test', answers)
            quiz_score = phan_tram(dung, tong)
        elif data.get('quizScore') is not None:
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
        xp_earned = data.get('xpEarned')
        if not isinstance(xp_earned, int) or xp_earned < 0 or xp_earned > 500:
            xp_earned = 50  # mặc định an toàn, chống client gửi XP tùy ý

        uid = request.user.id
        with transaction.atomic():
            course = q1('SELECT id, lessons FROM courses WHERE id=%s', (course_id,))
            if not course:
                return Response({'error': 'Không tìm thấy khóa học'}, status=404)

            lesson_id, topic = _resolve_lesson_id(course_id, lesson_no,
                                                  data.get('lessonTitle'), data.get('module'))

            # Đã completed rồi thì không cộng XP lần nữa (chống spam F5 modal)
            existed = q1("SELECT 1 FROM lesson_progress "
                         "WHERE user_id=%s AND lesson_id=%s AND status='completed'",
                         (uid, lesson_id))

            x('''INSERT INTO lesson_progress
                     (user_id, lesson_id, course_id, status, quiz_score, xp_earned, completed_at)
                 VALUES (%s, %s, %s, 'completed', %s, %s, %s)
                 ON CONFLICT (user_id, lesson_id) DO UPDATE SET
                     status       = 'completed',
                     quiz_score   = COALESCE(EXCLUDED.quiz_score, lesson_progress.quiz_score),
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

            # Tính lại cache enrollments từ nguồn thật lesson_progress
            done_row = q1('''SELECT COUNT(*) AS n,
                                    COALESCE(SUM(COALESCE(l.estimated_minutes, 15)), 0) AS minutes
                             FROM lesson_progress lp
                             JOIN lessons l ON l.id = lp.lesson_id
                             WHERE lp.user_id=%s AND lp.course_id=%s AND lp.status='completed' ''',
                          (uid, course_id))
            completed_count = done_row['n']
            time_spent = str(round(done_row['minutes'] / 60, 1)) + 'h'
            total_lessons = course['lessons'] or 0
            progress = min(100, round(completed_count * 100 / total_lessons)) if total_lessons else 0
            x('''UPDATE enrollments
                 SET completed_lessons = %s,
                     progress          = %s,
                     time_spent        = %s,
                     completed_at      = CASE WHEN %s >= 100 THEN COALESCE(completed_at, %s)
                                              ELSE completed_at END
                 WHERE user_id=%s AND course_id=%s''',
              (completed_count, progress, time_spent, progress, local_now(), uid, course_id))

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
            record_event(
                uid, KIND_LESSON, f'lesson:{lesson_id}',
                occurred_at=now, course_id=course_id, topic=topic,
                ref_type='lesson', ref_id=str(lesson_id),
                # quiz_score đã là PHẦN TRĂM đúng của bài kiểm tra đầu vào
                # (engine gửi lên round(score/total*100)), nên mốc tối đa là 100.
                score=quiz_score, max_score=(100 if quiz_score is not None else None),
                xp=xp_earned,
                meta={'lessonNo': lesson_no, 'title': data.get('lessonTitle') or ''},
            )
            _record_drill(uid, data.get('drill'), lesson_id, lesson_no, course_id, topic, now)

            newly_awarded = check_and_award_achievements(uid)

        return Response({
            'ok': True,
            'completedLessons': completed_count,
            'progress': progress,
            'xpGained': gained,
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

    Có ghi danh mới chấm được: cùng hàng rào với đường đọc nội dung.
    """

    def post(self, request, course_id, lesson_no):
        data = request.data if isinstance(request.data, dict) else {}
        phan = str(data.get('phan') or 'test')
        if phan not in PHAN_CO_CAU_HOI:
            return Response({'error': 'Phần phải là một trong: %s.'
                                      % ', '.join(PHAN_CO_CAU_HOI)}, status=400)
        answers = data.get('answers')
        if not isinstance(answers, dict):
            return Response({'error': 'Thiếu answers.'}, status=400)
        if not _da_ghi_danh(request.user.id, course_id):
            return Response({'error': 'Bạn chưa ghi danh khoá này.'}, status=403)

        ket_qua, dung, tong = cham(course_id, lesson_no, phan, answers)
        if ket_qua is None:
            return Response({'error': 'Chưa có nội dung cho bài này.'}, status=404)
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
