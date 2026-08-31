"""
seed_data — seed KHUNG nội dung tối thiểu cho bản HSA (ProgrammingEdu x TopHSA).

Idempotent (INSERT ... ON CONFLICT DO NOTHING). Seed:
  - 3 course = 3 hợp phần đề ĐGNL HSA (Định lượng / Định tính / Khoa học).
  - 1 roadmap template (user_id NULL) = lộ trình luyện thi HSA tổng.
Nội dung CHI TIẾT (bài học, câu hỏi, mapping questionnaire→template) đắp ở các
pha sau — đây chỉ là khung để app chạy được end-to-end.
"""
import json

from django.core.management.base import BaseCommand
from django.db import connection

HSA_COURSES = [
    # id, title, subtitle, description, level, duration, tag, color, accent, content_meta
    (
        "hsa_quantitative",
        "Tư duy Định lượng",
        "Hợp phần 1 — ĐGNL HSA (Toán học)",
        "Rèn tư duy định lượng cho kỳ thi Đánh giá năng lực ĐHQG Hà Nội: đại số, "
        "hàm số, hình học, xác suất – thống kê và đọc số liệu. Học theo dạng bài, "
        "có chế độ luyện bấm giờ như thi thật.",
        "Luyện thi HSA",
        "~75 phút/đề",
        "HSA · ĐỊNH LƯỢNG",
        "#4C1D95",
        "#A78BFA",
        {"section": "quantitative", "hsa_part": 1, "question_count": 50, "time_minutes": 75},
    ),
    (
        "hsa_verbal",
        "Tư duy Định tính",
        "Hợp phần 2 — ĐGNL HSA (Ngữ văn – Ngôn ngữ)",
        "Luyện tư duy định tính: đọc hiểu, từ vựng – ngữ pháp tiếng Việt, phân tích "
        "và suy luận ngôn ngữ theo cấu trúc đề HSA. Có chế độ luyện bấm giờ.",
        "Luyện thi HSA",
        "~60 phút/đề",
        "HSA · ĐỊNH TÍNH",
        "#9D174D",
        "#F472B6",
        {"section": "verbal", "hsa_part": 2, "question_count": 50, "time_minutes": 60},
    ),
    (
        "hsa_science",
        "Khoa học & Tiếng Anh",
        "Hợp phần 3 — ĐGNL HSA (Khoa học / Tiếng Anh)",
        "Hợp phần khoa học (Lý, Hóa, Sinh, Sử, Địa) và lựa chọn Tiếng Anh theo cấu "
        "trúc đề HSA. Ôn kiến thức nền + luyện dạng câu hỏi, có chế độ bấm giờ.",
        "Luyện thi HSA",
        "~60 phút/đề",
        "HSA · KHOA HỌC",
        "#065F46",
        "#34D399",
        {"section": "science", "hsa_part": 3, "question_count": 50, "time_minutes": 60,
         "english_option": True},
    ),
]

# Số bài mỗi khoá — khớp khung curriculum (frontend/src/lib/curricula.json, 2026-08-10).
HSA_LESSON_COUNT = {"hsa_quantitative": 27, "hsa_verbal": 23, "hsa_science": 26}

HSA_ROADMAP_ID = "hsa_master"
HSA_ROADMAP_MERMAID = (
    "flowchart TD\n"
    '    hsa_start["1. Chẩn đoán đầu vào"]\n'
    '    hsa_ql["2. Tư duy Định lượng"]\n'
    '    hsa_qt["3. Tư duy Định tính"]\n'
    '    hsa_kh["4. Khoa học & Tiếng Anh"]\n'
    '    hsa_mock["5. Luyện đề tổng (CBT)"]\n'
    '    hsa_goal["6. Về đích"]\n'
    "    hsa_start --> hsa_ql\n"
    "    hsa_start --> hsa_qt\n"
    "    hsa_ql --> hsa_kh\n"
    "    hsa_qt --> hsa_kh\n"
    "    hsa_kh --> hsa_mock\n"
    "    hsa_mock --> hsa_goal\n"
)
HSA_ROADMAP_NODES = {
    "hsa_start": {"title": "1. Chẩn đoán đầu vào",
                  "desc": "Làm bài questionnaire + mini-test để định vị điểm mạnh/yếu 3 hợp phần."},
    "hsa_ql": {"title": "2. Tư duy Định lượng",
               "desc": "Đại số, hàm số, hình học, xác suất–thống kê, đọc số liệu."},
    "hsa_qt": {"title": "3. Tư duy Định tính",
               "desc": "Đọc hiểu, từ vựng–ngữ pháp, suy luận ngôn ngữ."},
    "hsa_kh": {"title": "4. Khoa học & Tiếng Anh",
               "desc": "Lý–Hóa–Sinh–Sử–Địa hoặc lựa chọn Tiếng Anh."},
    "hsa_mock": {"title": "5. Luyện đề tổng (CBT)",
                 "desc": "Thi thử đầy đủ 150 câu trên máy, chấm điểm + phân tích."},
    "hsa_goal": {"title": "6. Về đích",
                 "desc": "Rà soát điểm yếu còn lại, chốt chiến lược làm bài."},
}

# Đề thi thử CBT mẫu (ngắn) — 9 câu, 3 hợp phần, MCQ + điền đáp án.
HSA_MOCK_EXAM = {
    "title": "Đề thi thử HSA — Bản rút gọn (demo)",
    "description": "Đề mẫu ngắn 9 câu (3 hợp phần) để trải nghiệm định dạng thi CBT. "
                   "Đề đầy đủ 150 câu sẽ do TopHSA cung cấp.",
    "duration_minutes": 20,
    "questions": [
        {"id": "q_ql_1", "section": "quantitative", "type": "mcq",
         "question": "Giá trị của biểu thức 2³ + 3² bằng bao nhiêu?",
         "options": ["15", "16", "17", "18"], "answer": "17"},
        {"id": "q_ql_2", "section": "quantitative", "type": "fill",
         "question": "Một số tăng 20% rồi giảm 20%. Số mới bằng bao nhiêu phần trăm số ban đầu? (nhập số)",
         "answer": "96"},
        {"id": "q_ql_3", "section": "quantitative", "type": "mcq",
         "question": "Nghiệm của phương trình 2x + 6 = 0 là?",
         "options": ["x = 3", "x = -3", "x = 2", "x = -2"], "answer": "x = -3"},
        {"id": "q_qt_1", "section": "verbal", "type": "mcq",
         "question": "Từ nào KHÁC loại với các từ còn lại?",
         "options": ["Bàn", "Ghế", "Tủ", "Chạy"], "answer": "Chạy"},
        {"id": "q_qt_2", "section": "verbal", "type": "mcq",
         "question": "Từ nào TRÁI nghĩa với “lạc quan”?",
         "options": ["Vui vẻ", "Bi quan", "Tự tin", "Hạnh phúc"], "answer": "Bi quan"},
        {"id": "q_qt_3", "section": "verbal", "type": "fill",
         "question": "Điền từ còn thiếu: “Có công mài sắt, có ngày nên ___”.",
         "answer": "kim"},
        {"id": "q_kh_1", "section": "science", "type": "mcq",
         "question": "Ở áp suất thường, nước sôi ở nhiệt độ nào?",
         "options": ["90°C", "100°C", "110°C", "120°C"], "answer": "100°C"},
        {"id": "q_kh_2", "section": "science", "type": "mcq",
         "question": "Hành tinh nào gần Mặt Trời nhất?",
         "options": ["Kim Tinh", "Trái Đất", "Thủy Tinh", "Hỏa Tinh"], "answer": "Thủy Tinh"},
        {"id": "q_kh_3", "section": "science", "type": "fill",
         "question": "Công thức hoá học của nước là gì?",
         "answer": "H2O"},
    ],
}


# ── Thành tích ──────────────────────────────────────────────────────────────
# achievements/services.py đã có đủ logic trao thưởng và chạy trong transaction
# của lessons.complete — nhưng bảng RỖNG nên vòng lặp không chạy lần nào, không
# học viên nào từng nhận được gì (audit 2026-08-14).
# condition_type phải là một trong 4 khoá mà _get_metrics() trả về:
#   lesson_count · streak_days · xp_total · course_complete
HSA_ACHIEVEMENTS = [
    # code, tên, mô tả, icon, condition_type, condition_value
    ("first_lesson", "Bước đầu tiên", "Hoàn thành bài học đầu tiên của bạn.",
     "🌱", "lesson_count", 1),
    ("ten_lessons", "Vào guồng", "Hoàn thành 10 bài học.",
     "📚", "lesson_count", 10),
    ("half_way", "Nửa chặng đường", "Hoàn thành 38/76 bài — quá nửa chương trình HSA.",
     "⛰️", "lesson_count", 38),
    ("all_lessons", "Cày hết 76 bài", "Hoàn thành toàn bộ chương trình 3 hợp phần.",
     "🏆", "lesson_count", 76),
    ("streak_3", "Ba ngày liền", "Học 3 ngày liên tiếp.",
     "🔥", "streak_days", 3),
    ("streak_7", "Trọn một tuần", "Học 7 ngày liên tiếp.",
     "🔥", "streak_days", 7),
    ("streak_30", "Kỷ luật thép", "Học 30 ngày liên tiếp.",
     "💎", "streak_days", 30),
    ("xp_500", "500 XP", "Tích lũy 500 XP.",
     "⭐", "xp_total", 500),
    ("xp_2000", "2.000 XP", "Tích lũy 2.000 XP.",
     "🌟", "xp_total", 2000),
    ("finish_section", "Xong một hợp phần", "Hoàn thành trọn vẹn một hợp phần của đề HSA.",
     "🎓", "course_complete", 1),
]

# ── Nhiệm vụ hằng ngày ──────────────────────────────────────────────────────
# Chấm bằng SỐ LIỆU THẬT trong ngày, không phải cặp (điều kiện, hành động) SQL
# của pe_test. condition_type khớp với stats.views._today_metrics().
HSA_MISSIONS = [
    # code, tiêu đề, mô tả, xp thưởng, condition_type, condition_value, thứ tự
    ("daily_lesson", "Học xong 1 bài hôm nay",
     "Bất kỳ bài nào trong 3 hợp phần đều tính.", 20, "lessons_today", 1, 1),
    ("daily_xp", "Kiếm 100 XP hôm nay",
     "Cộng dồn từ bài học và đề thi thử.", 30, "xp_today", 100, 2),
    ("daily_mock", "Làm 1 đề thi thử",
     "Quen áp lực thời gian là nửa phần thắng.", 50, "mocks_today", 1, 3),
]


# ── Bài mồi cho diễn đàn ────────────────────────────────────────────────────
# Diễn đàn có đủ tính năng (đăng bài, bình luận, 6 cảm xúc, theo dõi) nhưng 0
# bài — với bản demo thì trông như tính năng chết. Mồi vài bài ĐÚNG CHẤT HSA,
# mỗi bài gắn thẻ đúng bài học tương ứng.
#
# is_sample = TRUE để giao diện dán nhãn rõ: người xem KHÔNG được phép nhầm đây
# là bài của học viên thật. Xoá sạch bằng:
#   DELETE FROM posts WHERE is_sample;
HSA_SAMPLE_POSTS = [
    # category, tiêu đề, nội dung, course_id, lesson_no
    ('question', 'Câu tính phần trăm giảm giá hai lần — làm sao cho nhanh?',
     'Mình gặp dạng "giảm 20% rồi giảm tiếp 10%". Mình cứ tính từng bước nên mất '
     'gần 1 phút. Có mẹo nào nhân thẳng hệ số một lần không ạ?',
     'hsa_quantitative', 1),
    ('share', 'Mẹo đọc bảng số liệu: khoanh đơn vị TRƯỚC khi tính',
     'Mình từng sai 3 câu liên tiếp chỉ vì bảng ghi "nghìn tỉ" mà mình đọc thành '
     '"tỉ". Giờ mình luôn khoanh tròn dòng đơn vị ngay khi nhìn bảng, sai kiểu này '
     'gần như biến mất.',
     'hsa_quantitative', 20),
    ('question', 'Phân biệt hư từ với động từ trong câu — mình hay nhầm',
     'Ví dụ chữ "của" trong "sách của tôi" và "được" trong "được điểm cao". Có cách '
     'thử nhanh nào để biết đâu là hư từ không ạ?',
     'hsa_verbal', 3),
    ('discuss', 'Đọc lướt trước hay đọc câu hỏi trước với bài đọc hiểu dài?',
     'Mình thấy hai trường phái. Đọc câu hỏi trước thì biết cần tìm gì nhưng dễ bỏ '
     'sót ý chính. Mọi người làm cách nào và mất bao lâu mỗi bài đọc?',
     'hsa_verbal', 20),
    ('share', 'Cách mình nhớ mốc lịch sử: gom theo giai đoạn thay vì học từng năm',
     'Thay vì học rời từng mốc, mình chia thành 4 giai đoạn rồi mới nhét mốc vào. '
     'Đề hay hỏi thứ tự và khoảng cách giữa các mốc nên nhớ theo cụm dễ hơn hẳn.',
     'hsa_science', 16),
    ('question', 'Cơ cấu GDP thì chọn biểu đồ tròn hay biểu đồ miền ạ?',
     'Đề cho số liệu cơ cấu của 3 năm. Mình phân vân giữa tròn và miền. Dấu hiệu nào '
     'để chọn đúng ngay từ đầu?',
     'hsa_science', 23),
    ('discuss', 'Chọn 3 trong 5 môn Khoa học theo thế mạnh hay theo độ dễ của đề?',
     'Mình khá Sinh nhưng nghe nói phần Địa thường dễ ăn điểm hơn. Mọi người chọn '
     'theo tiêu chí nào ạ?',
     'hsa_science', 24),
    ('share', 'Lịch ôn 8 tuần mình đang chạy — chia theo hợp phần',
     'Tuần 1–3 Định lượng, tuần 4–5 Định tính, tuần 6 Khoa học, 2 tuần cuối chỉ luyện '
     'đề bấm giờ. Mỗi ngày 1 bài + 1 lượt luyện tốc độ, cuối tuần 1 đề đầy đủ.',
     None, None),
]


class Command(BaseCommand):
    help = ("Seed khung nội dung HSA tối thiểu (3 course + 1 roadmap template + "
            "thành tích + nhiệm vụ ngày). Idempotent.")

    def handle(self, *args, **options):
        with connection.cursor() as cur:
            n_courses = 0
            for (cid, title, subtitle, desc, level, duration, tag,
                 color, accent, meta) in HSA_COURSES:
                cur.execute(
                    """
                    INSERT INTO courses
                        (id, title, subtitle, description, image, level, duration,
                         students, rating, lessons, color, accent_color, tag,
                         xp_reward, is_published, content_meta)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO UPDATE SET
                        lessons = EXCLUDED.lessons,
                        content_meta = EXCLUDED.content_meta
                    """,
                    [cid, title, subtitle, desc, f"static/images/{cid}.svg", level,
                     duration, "0", 5.0, HSA_LESSON_COUNT.get(cid, 0), color, accent, tag, 0, True,
                     json.dumps(meta, ensure_ascii=False)],
                )
                n_courses += cur.rowcount

            cur.execute(
                """
                INSERT INTO roadmaps
                    (id, user_id, source, title, icon, color,
                     nodes_json, edges_json, mermaid_def)
                VALUES (%s, NULL, 'template', %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                [HSA_ROADMAP_ID, "Lộ trình luyện thi HSA", "🎯", "#4C1D95",
                 json.dumps(HSA_ROADMAP_NODES, ensure_ascii=False),
                 json.dumps({}, ensure_ascii=False),
                 HSA_ROADMAP_MERMAID],
            )
            n_roadmap = cur.rowcount

            # Đề thi thử mẫu — idempotent theo title.
            cur.execute("SELECT 1 FROM mock_exams WHERE title=%s", (HSA_MOCK_EXAM["title"],))
            n_exam = 0
            if not cur.fetchone():
                cur.execute(
                    """
                    INSERT INTO mock_exams
                        (title, description, duration_minutes, total_questions, questions_json, is_published)
                    VALUES (%s,%s,%s,%s,%s::jsonb, TRUE)
                    """,
                    [HSA_MOCK_EXAM["title"], HSA_MOCK_EXAM["description"],
                     HSA_MOCK_EXAM["duration_minutes"], len(HSA_MOCK_EXAM["questions"]),
                     json.dumps(HSA_MOCK_EXAM["questions"], ensure_ascii=False)],
                )
                n_exam = cur.rowcount

            # ON CONFLICT DO UPDATE (không phải DO NOTHING): sửa tên/mô tả/ngưỡng
            # rồi seed lại là cập nhật được, khỏi phải xoá tay.
            for code, name, desc, icon, ctype, cvalue in HSA_ACHIEVEMENTS:
                cur.execute(
                    """
                    INSERT INTO achievements
                        (code, name, description, icon, condition_type, condition_value)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (code) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        icon = EXCLUDED.icon,
                        condition_type = EXCLUDED.condition_type,
                        condition_value = EXCLUDED.condition_value
                    """,
                    [code, name, desc, icon, ctype, cvalue],
                )

            for code, title, desc, xp, ctype, cvalue, order in HSA_MISSIONS:
                cur.execute(
                    """
                    INSERT INTO missions
                        (code, title, description, xp_reward, condition_type,
                         condition_value, sort_order, is_active)
                    VALUES (%s,%s,%s,%s,%s,%s,%s, TRUE)
                    ON CONFLICT (code) DO UPDATE SET
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        xp_reward = EXCLUDED.xp_reward,
                        condition_type = EXCLUDED.condition_type,
                        condition_value = EXCLUDED.condition_value,
                        sort_order = EXCLUDED.sort_order,
                        is_active = TRUE
                    """,
                    [code, title, desc, xp, ctype, cvalue, order],
                )

            # Bài mồi: gán cho tài khoản quản trị (tài khoản duy nhất chắc chắn
            # tồn tại). Idempotent theo tiêu đề để chạy lại không nhân đôi.
            cur.execute("SELECT id FROM users ORDER BY id LIMIT 1")
            row = cur.fetchone()
            n_posts = 0
            if row:
                author_id = row[0]
                for cat, title, body, cid, lno in HSA_SAMPLE_POSTS:
                    cur.execute("SELECT 1 FROM posts WHERE title=%s AND is_sample", [title])
                    if cur.fetchone():
                        continue
                    cur.execute(
                        """INSERT INTO posts
                               (user_id, category, title, content, course_id, lesson_no, is_sample)
                           VALUES (%s,%s,%s,%s,%s,%s, TRUE)""",
                        [author_id, cat, title, body, cid, lno],
                    )
                    n_posts += cur.rowcount

            cur.execute("SELECT count(*) FROM achievements")
            total_ach = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM missions WHERE is_active")
            total_mis = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM courses")
            total_courses = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM roadmaps")
            total_roadmaps = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM mock_exams")
            total_exams = cur.fetchone()[0]

        self.stdout.write(self.style.SUCCESS(
            f"[seed_data] +{n_courses} course, +{n_roadmap} roadmap template, +{n_exam} đề thi thử "
            f"(tổng: {total_courses} course, {total_roadmaps} roadmap, {total_exams} đề, "
            f"{total_ach} thành tích, {total_mis} nhiệm vụ ngày, +{n_posts} bài mồi diễn đàn)"
        ))
