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

── TỪ 24/09/2026 CÓ CẢ SỔ, VÀ LỆNH NÀY VẪN LÀ THƯỚC ĐO SỰ THẬT (H3) ─────────

`bootstrap_schema` nay ghi sổ `luoc_do_da_chay` để QUYẾT ĐỊNH chạy mục nào — hết
cảnh dỡ-dựng lại ràng buộc mỗi deploy. Sổ ấy đúng là loại "ghi ý định" nói ở trên,
nên nó không thay lệnh này: sổ nói "đã chạy" mà ở đây báo ✗ → có người đảo tay →
`bootstrap_schema --tat-ca`. `bootstrap_schema --dien-tap` gọi lại MỌI dòng dưới
đây trong một schema tạm, nên mỗi câu kiểm hỏi SCHEMA ĐANG DÙNG (`current_schema()`,
`::regclass` theo `search_path`) chứ không hỏi cả CSDL — nếu không, `public` "chấm
đỗ" hộ một mục chưa hề được dựng trong schema ấy. Trên production hai cách hỏi cho
cùng kết quả (mọi bảng ở `public`).

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
    r = q1('SELECT 1 AS c FROM pg_indexes WHERE indexname = %s AND schemaname = current_schema()',
           (ten,))
    return bool(r), 'chưa có chỉ mục'


def _check_co_gia_tri(ten, gia_tri):
    """Ràng buộc CHECK `ten` có liệt kê `gia_tri` không?"""
    r = q1("""SELECT pg_get_constraintdef(oid) AS d FROM pg_constraint
              WHERE conname = %s AND connamespace = current_schema()::regnamespace""",
           (ten,))
    if not r:
        return False, 'không có ràng buộc này'
    return (gia_tri in r['d']), 'chưa liệt kê %r' % gia_tri


def _cot(bang, cot):
    r = q1("""SELECT 1 AS c FROM information_schema.columns
              WHERE table_schema = current_schema() AND table_name = %s AND column_name = %s""",
           (bang, cot))
    return bool(r), 'chưa có cột'


def _khong_con(sql, vi_sao):
    """Mục DỮ LIỆU (không DDL): tới nơi = câu `sql` không còn trả dòng nào."""
    return (not q1(sql)), vi_sao


def _ca(*kiem):
    """Nhiều phép kiểm cho MỘT tiểu mục: tới nơi khi mọi phép tới nơi. Nhận HÀM (gọi
    lần lượt, dừng ở phép đầu hỏng) — phép sau có thể cần bảng mà phép trước kiểm."""
    for k in kiem:
        ok, vi_sao = k()
        if not ok:
            return ok, vi_sao
    return True, ''


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
    # Kiểm CỘT trước khoá ngoại: bảng chưa có thì `::regclass` ném lỗi, và dòng
    # đầu nói "chưa có cột" dễ hiểu hơn một câu lỗi của Postgres.
    ('§46a', 'bảng term_holidays (ngày nghỉ theo đợt)',
     lambda: _cot('term_holidays', 'on_date')),
    ('§46b', 'term_holidays.term_id ON DELETE CASCADE',
     lambda: _fk('term_holidays', 'term_holidays_term_id_fkey', 'CASCADE')
     if _cot('term_holidays', 'on_date')[0] else (False, 'chưa có bảng')),
    ('§46c', 'chỉ mục duy nhất term_holidays(term_id, on_date)',
     lambda: _chi_muc('idx_term_holidays_term_day')),
    ('§47a', 'users.parent_contact_locked_at',
     lambda: _cot('users', 'parent_contact_locked_at')),
    ('§47b', 'chỉ mục users(parent_contact_locked_by)',
     lambda: _chi_muc('idx_users_parent_contact_locked_by')),
    ('§48a', 'bảng ket_qua_thi_ngoai (kết quả thi thử nhập từ PDF)',
     lambda: _cot('ket_qua_thi_ngoai', 'don_vi')),
    # Chỉ mục duy nhất là thứ giữ "nhập lại thì GHI ĐÈ": thiếu nó thì
    # `ON CONFLICT (user_id, ngay_thi, COALESCE(dot, ''))` ném lỗi ngay lượt ghi đầu.
    ('§48b', 'chỉ mục duy nhất ket_qua_thi_ngoai(user_id, ngay_thi, đợt)',
     lambda: _chi_muc('idx_kqtn_mot_luot')),
    ('§48c', 'chỉ mục ket_qua_thi_ngoai(user_id, ngay_thi DESC)',
     lambda: _chi_muc('idx_kqtn_user_ngay')),
    ('§48d', 'chỉ mục ket_qua_thi_ngoai(nhap_boi)',
     lambda: _chi_muc('idx_kqtn_nhap_boi')),
    ('§49a', 'users.is_demo (dữ liệu trình diễn)',
     lambda: _cot('users', 'is_demo')),
    ('§49b', 'classes.is_demo (dữ liệu trình diễn)',
     lambda: _cot('classes', 'is_demo')),
    ('§49c', 'chỉ mục users(id) WHERE is_demo',
     lambda: _chi_muc('idx_users_is_demo')),
    ('§49d', 'chỉ mục classes(id) WHERE is_demo',
     lambda: _chi_muc('idx_classes_is_demo')),
    # §50–§53 THÊM 24/09/2026: bốn mục ấy lên CSDL mà chưa ai thêm dòng ở đây — lệnh
    # này đã báo "sạch" cho chúng suốt bốn ngày mà không hề nhìn tới.
    ('§50', 'bảng parent_report_optout (phụ huynh từ chối nhận báo cáo)',
     lambda: _cot('parent_report_optout', 'by_user_id')),
    ('§51a', 'users.student_code (mã HSA-xxxxx)', lambda: _cot('users', 'student_code')),
    ('§51b', 'users.username (tên đăng nhập)', lambda: _cot('users', 'username')),
    ('§51c', 'chỉ mục duy nhất users(student_code)', lambda: _chi_muc('idx_users_student_code')),
    ('§51d', 'chỉ mục duy nhất users(lower(username))', lambda: _chi_muc('idx_users_username')),
    ('§52a', 'bảng password_reset_tokens (quên mật khẩu)',
     lambda: _cot('password_reset_tokens', 'user_id')),
    ('§52b', 'chỉ mục password_reset_tokens(user_id, created_at)', lambda: _chi_muc('idx_prt_user')),
    ('§53a', 'classes.mode + room', lambda: _cot('classes', 'room')),
    ('§53b', 'class_sessions.mode + room', lambda: _cot('class_sessions', 'room')),
    ('§53c', 'CHECK classes_mode_check nhận offline',
     lambda: _check_co_gia_tri('classes_mode_check', 'offline')),
    ('§54a', 'classes.class_type (nhóm / gia sư)', lambda: _cot('classes', 'class_type')),
    ('§54b', 'CHECK classes_class_type_check nhận gia_su',
     lambda: _check_co_gia_tri('classes_class_type_check', 'gia_su')),
    ('§55a', 'class_members.transferred_to (chuyển lớp một bước)',
     lambda: _cot('class_members', 'transferred_to')),
    ('§55b', 'FK class_members.transferred_to ON DELETE SET NULL',
     lambda: _fk('class_members', 'class_members_transferred_to_fk', 'SET NULL')),
    ('§55c', 'chỉ mục class_members(transferred_to)',
     lambda: _chi_muc('idx_class_members_transferred_to')),
    ('§55d', 'CHECK chỉ lượt "transferred" mới được trỏ',
     lambda: _check_co_gia_tri('class_members_transfer_reason_check', 'transferred')),
    ('§56', 'users.last_seen_at (lần cuối thấy tài khoản)', lambda: _cot('users', 'last_seen_at')),
    # §57 là mục DỮ LIỆU (bỏ thi, pha A): "tới nơi" = không còn dòng mang chữ cũ.
    ('§57a', 'nhiệm vụ "Làm 1 đề thi thử" (daily_mock) đã tắt',
     lambda: _khong_con("SELECT 1 AS c FROM missions WHERE code = 'daily_mock' AND is_active",
                        'nhiệm vụ còn bật')),
    ('§57b', 'không lộ trình nào còn chặng "Luyện đề tổng (CBT)"',
     lambda: _khong_con("""SELECT 1 AS c FROM roadmaps
                           WHERE strpos(mermaid_def, 'Luyện đề tổng (CBT)') > 0
                              OR strpos(nodes_json::text, 'Luyện đề tổng (CBT)') > 0
                           LIMIT 1""", 'còn lộ trình mang nhãn cũ')),
    ('§62a', 'class_members.teacher_comment (nhận xét GV gửi phụ huynh)',
     lambda: _cot('class_members', 'teacher_comment')),
    # §62b–§62f: luồng A1 (V-a…V-h, 25/09/2026). Mã dòng = mã tiểu mục (một chữ cái
    # cuối — `tests_luoc_do_muc` đòi thế), nên mỗi tiểu mục một dòng gom mọi phép kiểm.
    ('§62b', 'class_members.can_ho_tro + de_xuat_huong_hoc + chỉ mục cờ (cần hỗ trợ, hướng học)',
     lambda: _ca(lambda: _cot('class_members', 'de_xuat_huong_hoc_at'),
                 lambda: _chi_muc('idx_class_members_can_ho_tro'))),
    ('§62c', 'bảng attendance_history + khoá ngoại tới buổi ON DELETE CASCADE',
     lambda: _ca(lambda: _cot('attendance_history', 'nguon'),
                 lambda: _fk('attendance_history', 'attendance_history_session_id_fkey',
                             'CASCADE'))),
    ('§62d', 'assignments.target_mode (CHECK nhận nhom) + bảng assignment_targets',
     lambda: _ca(lambda: _cot('assignment_targets', 'user_id'),
                 lambda: _check_co_gia_tri('assignments_target_mode_check', 'nhom'))),
    ('§62e', 'class_sessions.makeup_for ON DELETE SET NULL + bảng session_participants',
     lambda: _ca(lambda: _cot('session_participants', 'user_id'),
                 lambda: _fk('class_sessions', 'class_sessions_makeup_for_fkey', 'SET NULL'))),
    ('§62f', 'assignments.kind (CHECK nhận kiem_tra) + held_on, submissions.absent',
     lambda: _ca(lambda: _cot('submissions', 'absent'),
                 lambda: _check_co_gia_tri('assignments_kind_check', 'kiem_tra'))),
    # Sửa TẠI CHỖ ở §35 (V-c): nhánh khác chạy lại §35 bản cũ thì mất 'paused' — dòng
    # này nói ra ngay, trước khi màn Lớp học trả 500 khi chọn "Tạm dừng".
    ('§35p', 'CHECK classes_status_check nhận paused (lớp tạm dừng)',
     lambda: _check_co_gia_tri('classes_status_check', 'paused')),
    ('§63a', 'users.tuition_status (tình trạng học phí)',
     lambda: _cot('users', 'tuition_status')),
    ('§63b', 'CHECK users_tuition_status_check nhận bao_luu (lưu MÃ, nhãn ở teaching/tinh_trang.py)',
     lambda: _check_co_gia_tri('users_tuition_status_check', 'bao_luu')),
    # 'reserved' sửa TẠI CHỖ ở §36 (25/09 tối) — thay dòng §63d cũ; 'paused' đã có dòng §35p ở trên.
    ('§36r', 'CHECK class_members_leave_reason_check nhận "reserved" (bảo lưu)',
     lambda: _check_co_gia_tri('class_members_leave_reason_check', 'reserved')),
    ('§64a', 'bảng syllabus_versions (phiên bản chương trình)',
     lambda: _cot('syllabus_versions', 'status')),
    ('§64b', 'bảng syllabus_sessions (buổi học theo kế hoạch)',
     lambda: _cot('syllabus_sessions', 'sort_order')),
    ('§64c', 'bảng syllabus_items (nội dung từng buổi)',
     lambda: _cot('syllabus_items', 'kind')),
    ('§64d', 'bảng syllabus_materials (học liệu)',
     lambda: _cot('syllabus_materials', 'file_url')),
    ('§64e', 'classes.syllabus_version_id (lớp nhận khung nào)',
     lambda: _cot('classes', 'syllabus_version_id')),
    ('§64f', 'class_sessions.syllabus_session_id (buổi thật khớp buổi khung)',
     lambda: _cot('class_sessions', 'syllabus_session_id')),
    ('§69b', 'chỉ mục admin_audit(detail->>class_id) cho lịch sử một lớp (V-n)',
     lambda: _chi_muc('idx_audit_lop_buoi')),
    # §64g–h sửa TẠI CHỖ (E1, 25/09/2026): chuỗi phiên bản + trọng số bắt buộc > 0.
    ('§64g', 'syllabus_versions: mỗi chuỗi nhiều nhất một bản nháp, một bản đang dùng',
     lambda: _ca(lambda: _cot('syllabus_versions', 'lineage_id'),
                 lambda: _chi_muc('idx_syllabus_versions_mot_nhap'),
                 lambda: _chi_muc('idx_syllabus_versions_mot_xuat_ban'))),
    ('§64h', 'syllabus_items.weight bắt buộc, CHECK > 0',
     lambda: _check_co_gia_tri('syllabus_items_weight_check', 'weight > ')),
    # §70: sổ đầu bài (E1). Kiểm cột trước khoá ngoại — bảng chưa có thì `::regclass` ném lỗi.
    ('§70a', 'bảng session_logs (sổ đầu bài, mức tiếp thu 1–5), xoá theo buổi',
     lambda: _fk('session_logs', 'session_logs_session_id_fkey', 'CASCADE')
     if _cot('session_logs', 'comprehension')[0] else (False, 'chưa có bảng')),
    ('§70b', 'session_log_items → syllabus_items ON DELETE SET NULL',
     lambda: _fk('session_log_items', 'session_log_items_item_id_fkey', 'SET NULL')
     if _cot('session_log_items', 'item_id')[0] else (False, 'chưa có bảng')),
    ('§70c', 'bảng session_support (em cần hỗ trợ sau buổi)',
     lambda: _chi_muc('idx_session_support_user')),
    # §71: địa chỉ lịch riêng (.ics). Chìa chỉ lưu BĂM; một chìa còn sống mỗi (người, phạm vi).
    ('§71a', 'bảng calendar_links (chìa lịch, chỉ lưu băm), xoá theo người',
     lambda: _fk('calendar_links', 'calendar_links_user_id_fkey', 'CASCADE')
     if _cot('calendar_links', 'token_hash')[0] else (False, 'chưa có bảng')),
    ('§71b', 'calendar_links.scope CHECK toi | trung_tam',
     lambda: _check_co_gia_tri('calendar_links_scope_check', 'trung_tam')),
    ('§71c', 'mỗi người mỗi phạm vi chỉ MỘT chìa còn sống',
     lambda: _chi_muc('idx_calendar_links_mot_chia_song')),
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
