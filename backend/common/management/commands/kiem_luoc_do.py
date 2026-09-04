"""So `sql/legacy_schema.sql` với CSDL THẬT — mục nào đã tới nơi, mục nào chưa.

── VÌ SAO CÓ LỆNH NÀY (A9, 05/09/2026) ─────────────────────────────────────

`legacy_schema.sql` chỉ chạy qua `bootstrap_schema` ở `buildCommand` của Render,
tức CHỈ KHI `master` được gộp. Mọi mục viết trên nhánh `erp` nằm chờ, và cách
duy nhất để biết mục nào đã tới nơi là đi hỏi `pg_catalog` từng cái một.

Đo 01/09/2026 đã có bằng chứng: `§41` CÓ trên Neon, cả hai khoá của `§42` thì
KHÔNG — chúng vẫn là `NO ACTION`. Tệp lược đồ mô tả một CSDL không tồn tại, và
không có gì nói ra điều đó.

── VÌ SAO KIỂM THỰC TẾ, KHÔNG GHI SỔ Ý ĐỊNH ────────────────────────────────

Cách thường gặp là một bảng `schema_versions` ghi "đã chạy §43". Bảng ấy nói về
Ý ĐỊNH: nó ghi rằng câu lệnh đã được PHÁT, không phải rằng kết quả CÒN Ở ĐÓ. Một
`ALTER` bị người khác đảo ngược, một lần khôi phục từ bản sao lưu cũ, một nhánh
CSDL dựng lại — bảng ấy vẫn nói "đã chạy".

Lệnh này hỏi thẳng `pg_catalog`: khoá ngoại này có `ON DELETE CASCADE` không, chỉ
mục này có tồn tại không. Câu trả lời KHÔNG thể trôi khỏi sự thật, vì nó CHÍNH LÀ
sự thật.

Cái giá: mỗi mục phải viết một câu kiểm. Đó là giá đúng — viết một câu kiểm buộc
người thêm mục phải nói rõ "tới nơi" nghĩa là gì, và một mục không diễn đạt nổi
điều đó thì cũng không kiểm được bằng tay.

    python manage.py kiem_luoc_do          # in bảng
    python manage.py kiem_luoc_do --ma-loi  # thoát khác 0 nếu có mục CHƯA tới

`--ma-loi` để cắm vào CI hoặc một bước sau deploy. Mặc định KHÔNG bật: lệnh này
phải chạy được trên máy dev, nơi CSDL cố tình đi sau, mà không làm đỏ mọi thứ.
"""
from django.core.management.base import BaseCommand

from common.db import q1

#: Chữ cái `confdeltype` của Postgres. Viết ra đây vì `'a'` và `'n'` nhìn không
#: khác gì nhau trong một câu truy vấn, và đoán sai một chữ là đọc ngược kết quả.
_XOA = {'a': 'NO ACTION', 'r': 'RESTRICT', 'c': 'CASCADE',
        'n': 'SET NULL', 'd': 'SET DEFAULT'}


def _fk(bang, ten, mong):
    """Khoá ngoại `ten` trên `bang` có đúng chính sách xoá `mong` không?"""
    r = q1("""SELECT confdeltype FROM pg_constraint
              WHERE conname = %s AND conrelid = %s::regclass AND contype = 'f'""",
           (ten, bang))
    if not r:
        return False, 'không có khoá ngoại này'
    thuc = _XOA.get(r['confdeltype'], r['confdeltype'])
    return thuc == mong, 'đang là %s, cần %s' % (thuc, mong)


def _chi_muc(ten):
    r = q1('SELECT 1 AS c FROM pg_indexes WHERE indexname = %s', (ten,))
    return bool(r), 'chưa có chỉ mục'


def _check_co_gia_tri(ten, gia_tri):
    """Ràng buộc CHECK `ten` có liệt kê `gia_tri` không?"""
    r = q1("SELECT pg_get_constraintdef(oid) AS d FROM pg_constraint WHERE conname = %s",
           (ten,))
    if not r:
        return False, 'không có ràng buộc này'
    return (gia_tri in r['d']), 'chưa liệt kê %r' % gia_tri


def _cot(bang, cot):
    r = q1("""SELECT 1 AS c FROM information_schema.columns
              WHERE table_name = %s AND column_name = %s""", (bang, cot))
    return bool(r), 'chưa có cột'


#: MỘT DÒNG MỘT MỤC của `legacy_schema.sql`. Thêm mục mới thì thêm dòng ở đây —
#: nếu không, lệnh này im lặng báo "sạch" cho một mục nó chưa hề nhìn tới, đúng
#: cái bẫy mà bộ đo giao diện đã mắc (danh sách trang thiếu ba màn).
MUC = [
    ('§41', 'notification_settings có khoá ngoại tới users',
     lambda: _fk('notification_settings', 'notification_settings_user_fk', 'CASCADE')),
    ('§42a', 'roadmaps.user_id ON DELETE CASCADE',
     lambda: _fk('roadmaps', 'roadmaps_user_id_fkey', 'CASCADE')),
    # Mục thứ hai của §42 là `roadmaps.generated_from_survey_id`, KHÔNG phải
    # `roadmap_progress`. Bản đầu của tệp này tra nhầm bảng VÀ nhầm tên ràng
    # buộc (`roadmap_progress_user_id_fkey`), nên nó báo "không có khoá ngoại
    # này" cho một khoá đang tồn tại và đã là CASCADE.
    #
    # Một dương tính giả ở đây đắt hơn ở chỗ khác: lệnh này sinh ra để trả lời
    # "còn phải chạy gì trên production", nên một dòng đỏ giả là một người đi
    # chạy DDL không cần chạy trên CSDL thật.
    ('§42b', 'roadmaps.generated_from_survey_id ON DELETE SET NULL',
     lambda: _fk('roadmaps', 'roadmaps_generated_from_survey_id_fkey', 'SET NULL')),
    ('§43a', 'courses.instructor_id ON DELETE SET NULL',
     lambda: _fk('courses', 'courses_instructor_id_fkey', 'SET NULL')),
    ('§43b', 'missions.course_id ON DELETE CASCADE',
     lambda: _fk('missions', 'missions_course_id_fkey', 'CASCADE')),
    ('§44', 'users_role_check có vai "Biên tập nội dung"',
     lambda: _check_co_gia_tri('users_role_check', 'Biên tập nội dung')),
    ('§45', 'chỉ mục learning_events(ref_type, ref_id)',
     lambda: _chi_muc('idx_levents_ref')),
    ('§36', 'class_members.leave_reason',
     lambda: _cot('class_members', 'leave_reason')),
    ('§40', 'lesson_progress.answers_json',
     lambda: _cot('lesson_progress', 'answers_json')),
]


class Command(BaseCommand):
    help = 'So legacy_schema.sql với CSDL thật: mục nào đã tới nơi, mục nào chưa.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ma-loi', action='store_true',
            help='Thoát khác 0 nếu có mục chưa tới nơi (dùng cho CI / sau deploy).')

    def handle(self, *args, **opt):
        thieu = []
        self.stdout.write('Đối chiếu legacy_schema.sql với CSDL đang nối:\n')
        for ma, mo_ta, kiem in MUC:
            try:
                ok, vi_sao = kiem()
            except Exception as e:            # noqa: BLE001 — bảng chưa tồn tại…
                ok, vi_sao = False, 'không kiểm được: %s' % e
            if ok:
                self.stdout.write('  ✓ %-6s %s' % (ma, mo_ta))
            else:
                thieu.append((ma, mo_ta, vi_sao))
                self.stdout.write(self.style.WARNING(
                    '  ✗ %-6s %s — %s' % (ma, mo_ta, vi_sao)))

        self.stdout.write('')
        if not thieu:
            self.stdout.write(self.style.SUCCESS(
                '%d/%d mục đã tới nơi.' % (len(MUC), len(MUC))))
            return

        self.stdout.write(self.style.WARNING(
            '%d/%d mục CHƯA tới CSDL này.' % (len(thieu), len(MUC))))
        self.stdout.write(
            'Trên máy dev thì bình thường — lược đồ đi trước là chuyện có chủ ý.\n'
            'Trên production thì đây là danh sách việc phải chạy: gộp vào `master`\n'
            '(buildCommand của Render tự chạy `bootstrap_schema`), hoặc áp tay\n'
            'từng câu trong `backend/sql/legacy_schema.sql`.')
        if opt.get('ma_loi'):
            raise SystemExit(1)
