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


class Command(BaseCommand):
    help = "Seed khung nội dung HSA tối thiểu (3 course + 1 roadmap template). Idempotent."

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

            cur.execute("SELECT count(*) FROM courses")
            total_courses = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM roadmaps")
            total_roadmaps = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM mock_exams")
            total_exams = cur.fetchone()[0]

        self.stdout.write(self.style.SUCCESS(
            f"[seed_data] +{n_courses} course, +{n_roadmap} roadmap template, +{n_exam} đề thi thử "
            f"(tổng: {total_courses} course, {total_roadmaps} roadmap, {total_exams} đề)"
        ))
