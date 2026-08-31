# -*- coding: utf-8 -*-
"""Sinh ERD (Mermaid) TỪ CHÍNH CSDL, không vẽ tay.

    python manage.py ve_erd

VÌ SAO SINH RA CHỨ KHÔNG VẼ. Một sơ đồ vẽ tay đúng đúng một ngày — ngày người ta
vẽ nó. Sau đó mỗi lần thêm cột, đổi khoá ngoại, bỏ bảng là nó lệch thêm một
chút, và không ai biết nó đã lệch. Sơ đồ vẽ SAI còn tệ hơn không có sơ đồ: nó
tắt phản xạ đi đọc mã (RULES §20).

Bản này đọc `information_schema` nên nó không thể lệch với CSDL tại thời điểm
chạy. Đổi lược đồ thì chạy lại lệnh này và commit tệp mới — một dòng trong quy
trình, thay cho một buổi ngồi vẽ lại.
"""
import io
import os

from django.core.management.base import BaseCommand

from common.db import q

#: Bảng của Django / allauth / SimpleJWT — hạ tầng, không phải mô hình nghiệp
#: vụ. Vẽ chung vào thì sơ đồ có 53 hộp và không ai đọc nổi.
TIEN_TO_KHUNG = ('django_', 'auth_', 'account_', 'socialaccount_',
                 'token_blacklist_')

#: Chia bảng nghiệp vụ theo MIỀN. Đây là phần DUY NHẤT phải bảo trì tay — nó là
#: một nhận định về sản phẩm, không suy ra được từ lược đồ. Bảng không nằm trong
#: bảng phân miền nào sẽ hiện ở nhóm "chưa xếp miền", để nó không im lặng biến
#: mất khỏi sơ đồ.
MIEN = {
    'Tài khoản & hồ sơ': ['users', 'user_follows', 'notification_settings',
                          'notifications', 'admin_audit'],
    'Nội dung & khoá học': ['courses', 'lessons', 'enrollments', 'course_ratings'],
    'Học & đo lường': ['lesson_progress', 'learning_events', 'topic_self_marks',
                       'study_logs', 'study_plans', 'study_plan_items',
                       'surveys', 'roadmaps', 'roadmap_progress'],
    'Kiểm tra & thi': ['quizzes', 'review_quiz_results', 'mock_exams',
                       'mock_attempts'],
    'Trò chơi hoá': ['achievements', 'user_achievements', 'missions',
                     'user_missions', 'user_daily_xp_logs'],
    'Lớp học (ERP)': ['terms', 'classes', 'class_members', 'class_sessions',
                      'attendance', 'assignments', 'submissions'],
    'Diễn đàn': ['posts', 'comments', 'post_likes', 'comment_likes'],
}


def _la_khung(ten):
    return ten.startswith(TIEN_TO_KHUNG)


#: Nơi ghi mặc định. Lệnh TỰ GHI TỆP chứ không in ra stdout để người dùng
#: chuyển hướng: trên Windows, `OutputWrapper` của Django đổi xuống dòng thành
#: CRLF, nên tệp sinh ra lệch dòng với cả repo (LF) và mọi biểu thức tìm khối
#: ```mermaid đều trượt — kể cả bộ kiểm cú pháp sơ đồ. Đo được 01/09/2026: 8
#: khối của ERD lọt hết khỏi bộ kiểm mà không ai biết.
DUONG_DAN = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', '..', 'docs', 'KIEN_TRUC', 'ERD.md'))


class Command(BaseCommand):
    help = 'Sinh ERD dạng Mermaid từ information_schema (không vẽ tay).'

    def add_arguments(self, parser):
        parser.add_argument('--ra', default=DUONG_DAN,
                            help='Tệp đích (mặc định docs/KIEN_TRUC/ERD.md)')

    def handle(self, *args, **options):
        self._dong = []
        bang = [r['table_name'] for r in q(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' ORDER BY table_name")]
        nghiep_vu = [t for t in bang if not _la_khung(t)]
        khung = [t for t in bang if _la_khung(t)]

        cot = {}
        for r in q("""SELECT table_name, column_name, data_type, is_nullable
                      FROM information_schema.columns WHERE table_schema='public'
                      ORDER BY table_name, ordinal_position"""):
            cot.setdefault(r['table_name'], []).append(r)

        khoa_chinh = {}
        for r in q("""SELECT tc.table_name, kcu.column_name
                      FROM information_schema.table_constraints tc
                      JOIN information_schema.key_column_usage kcu
                        ON kcu.constraint_name = tc.constraint_name
                      WHERE tc.constraint_type='PRIMARY KEY'
                        AND tc.table_schema='public'"""):
            khoa_chinh.setdefault(r['table_name'], set()).add(r['column_name'])

        fk = q("""SELECT tc.table_name AS tu_bang, kcu.column_name AS tu_cot,
                         ccu.table_name AS toi_bang, rc.delete_rule
                  FROM information_schema.table_constraints tc
                  JOIN information_schema.key_column_usage kcu
                    ON kcu.constraint_name = tc.constraint_name
                  JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                  JOIN information_schema.referential_constraints rc
                    ON rc.constraint_name = tc.constraint_name
                  WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public'
                  ORDER BY 1, 2""")
        fk_nv = [r for r in fk
                 if not _la_khung(r['tu_bang']) and not _la_khung(r['toi_bang'])]

        so_dong = {}
        for t in nghiep_vu:
            so_dong[t] = q('SELECT COUNT(*) AS n FROM "%s"' % t)[0]['n']

        da_xep = {t for ds in MIEN.values() for t in ds}
        chua_xep = [t for t in nghiep_vu if t not in da_xep]

        ra = self._dong.append
        ra('<!-- TỆP NÀY ĐƯỢC SINH RA. Đừng sửa tay.\n'
           '     Chạy lại sau mỗi lần đổi lược đồ:\n'
           '         cd backend && python manage.py ve_erd\n'
           '     Nguồn: information_schema của chính CSDL đang chạy. -->\n')
        ra('# ERD — sinh từ CSDL\n')
        ra('**%d bảng** trong lược đồ `public`: **%d bảng nghiệp vụ** + %d bảng khung '
           '(Django/allauth/SimpleJWT). **%d khoá ngoại** trong khối nghiệp vụ.\n'
           % (len(bang), len(nghiep_vu), len(khung), len(fk_nv)))

        if chua_xep:
            ra('> ⚠ **%d bảng chưa được xếp miền** trong `ve_erd.MIEN`: %s.\n'
               '> Chúng vẫn hiện trong sơ đồ dưới, nhưng hãy xếp miền cho chúng —\n'
               '> một bảng không thuộc miền nào là một bảng không ai nhớ ra lúc\n'
               '> thiết kế tính năng mới.\n' % (len(chua_xep), ', '.join('`%s`' % t for t in chua_xep)))

        # ── Sơ đồ tổng: chỉ miền và quan hệ giữa các miền ──
        ra('\n## 1. Bản đồ MIỀN — đọc cái này trước\n')
        ra('Sơ đồ đầy đủ có %d hộp; không ai đọc nổi một bức như thế. Đây là bản đồ '
           'miền, và mỗi mũi tên là "có ít nhất một khoá ngoại".\n' % len(nghiep_vu))
        thuoc_mien = {}
        for m, ds in MIEN.items():
            for t in ds:
                thuoc_mien[t] = m
        canh = set()
        for r in fk_nv:
            a, b = thuoc_mien.get(r['tu_bang']), thuoc_mien.get(r['toi_bang'])
            if a and b and a != b:
                canh.add((a, b))
        ra('\n```mermaid\nflowchart LR\n')
        ma = {m: 'M%d' % i for i, m in enumerate(MIEN, 1)}
        for m, k in ma.items():
            ra('  %s["%s<br/><small>%d bảng</small>"]\n'
               % (k, m, len([t for t in MIEN[m] if t in nghiep_vu])))
        for a, b in sorted(canh):
            ra('  %s --> %s\n' % (ma[a], ma[b]))
        ra('```\n')

        # ── ERD chi tiết theo từng miền ──
        ra('\n## 2. ERD chi tiết, theo miền\n')
        ra('Cột hiển thị: khoá chính (PK), khoá ngoại (FK), và cột NOT NULL. '
           'Cột tuỳ chọn được lược để sơ đồ còn đọc được — mở `sql/*.sql` khi cần đủ.\n')
        fk_cot = {(r['tu_bang'], r['tu_cot']): r for r in fk_nv}
        for m, ds in MIEN.items():
            trong_mien = [t for t in ds if t in nghiep_vu]
            if not trong_mien:
                continue
            ra('\n### %s\n\n' % m)
            ra('```mermaid\nerDiagram\n')
            for t in trong_mien:
                ra('  %s {\n' % t)
                for c in cot.get(t, []):
                    ten, kieu = c['column_name'], c['data_type'].replace(' ', '_')
                    la_pk = ten in khoa_chinh.get(t, set())
                    la_fk = (t, ten) in fk_cot
                    if not (la_pk or la_fk or c['is_nullable'] == 'NO'):
                        continue
                    nhan = 'PK' if la_pk else ('FK' if la_fk else '')
                    ra('    %s %s %s\n' % (kieu, ten, nhan))
                ra('  }\n')
            for r in fk_nv:
                if r['tu_bang'] in trong_mien and r['toi_bang'] in trong_mien:
                    ra('  %s ||--o{ %s : "%s (%s)"\n'
                       % (r['toi_bang'], r['tu_bang'], r['tu_cot'], r['delete_rule']))
            ra('```\n')
            ra('\n| bảng | dòng | khoá ngoại ra ngoài miền |\n|---|---:|---|\n')
            for t in trong_mien:
                ngoai = ['`%s` → `%s`' % (r['tu_cot'], r['toi_bang'])
                         for r in fk_nv
                         if r['tu_bang'] == t and r['toi_bang'] not in trong_mien]
                ra('| `%s` | %s | %s |\n' % (t, so_dong[t], ', '.join(ngoai) or '—'))

        # ── Những thứ chỉ đọc số mới thấy ──
        ra('\n## 3. Đọc từ số liệu, không từ trí nhớ\n')
        rong = [t for t in nghiep_vu if so_dong[t] == 0]
        ra('\n**%d bảng đang RỖNG** — tính năng đã dựng nhưng chưa ai dùng, hoặc dựng '
           'thừa. Đáng rà lại trước khi thêm tính năng mới:\n\n%s\n'
           % (len(rong), ', '.join('`%s`' % t for t in rong) or '(không có)'))
        khong_fk = ({r['tu_bang'] for r in fk_nv} | {r['toi_bang'] for r in fk_nv})
        co_don = [t for t in nghiep_vu if t not in khong_fk]
        ra('\n**Bảng không dính khoá ngoại nào**: %s\n'
           % (', '.join('`%s`' % t for t in co_don) or '(không có — tốt)'))
        luat = {}
        for r in fk_nv:
            luat.setdefault(r['delete_rule'], []).append(
                '%s.%s' % (r['tu_bang'], r['tu_cot']))
        ra('\n**Luật xoá của khoá ngoại** — trộn nhiều luật trong một hệ là cách dữ '
           'liệu mồ côi sinh ra:\n\n')
        for k, ds in sorted(luat.items(), key=lambda kv: -len(kv[1])):
            ra('- `%s`: %d khoá%s\n'
               % (k, len(ds), ('' if len(ds) > 6 else ' — ' + ', '.join('`%s`' % x for x in ds))))

        duong_dan = os.path.abspath(options['ra'])
        os.makedirs(os.path.dirname(duong_dan), exist_ok=True)
        noi_dung = ''.join(self._dong)
        with io.open(duong_dan, 'w', encoding='utf-8', newline=chr(10)) as f:
            f.write(noi_dung)
        self.stdout.write('Đã ghi %s (%d dòng)'
                          % (duong_dan, noi_dung.count(chr(10)) + 1))
