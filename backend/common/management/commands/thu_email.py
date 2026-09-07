"""Xem trước — hoặc gửi thật — MỘT thư báo cáo phụ huynh.

── VÌ SAO CÓ LỆNH NÀY (07/09/2026) ─────────────────────────────────────────

Song sinh với `thu_zns`, và vì cùng lý do: đường gửi hàng loạt cần một lớp có
thật, học viên có thật, buổi học có thật và điểm danh có thật — quá nhiều thứ
phải dựng chỉ để xem một lá thư trông thế nào. Trung tâm hiện có 0 đợt học và
0 lượt điểm danh, nên đường ấy chưa chạy được lần nào.

Lệnh này đi ĐÚNG hàm mà đường hàng loạt sẽ gọi (`thu_bao_cao.soan_thu` →
`common.mail.gui`), nên thứ nó dựng ra là thứ sẽ đi thật. Nó KHÔNG dựng một
bản xem trước riêng — bản riêng sẽ trôi khỏi bản gửi thật, và khi ấy người
duyệt nội dung duyệt nhầm một thứ khác với thứ phụ huynh nhận.

    python manage.py thu_email --toi ai-do@gmail.com

── HAI CHẾ ĐỘ, MẶC ĐỊNH LÀ CHẾ ĐỘ AN TOÀN ─────────────────────────────────

    EMAIL_CHE_DO_THU=1   → ghi tệp .eml ra đĩa, KHÔNG gửi, không cần mật khẩu
    (không đặt biến)     → gửi THẬT, cần EMAIL_USER + EMAIL_APP_PASSWORD

Tệp `.eml` mở được bằng Outlook, Thunderbird, hoặc kéo thẳng vào cửa sổ soạn
thư Gmail — tức xem được ĐÚNG bố cục và ĐÚNG tệp đính kèm mà phụ huynh sẽ
thấy, chứ không phải một bản tóm tắt trong terminal.

── DỮ LIỆU: MẶC ĐỊNH LÀ MẪU, MUỐN THẬT THÌ PHẢI NÓI RÕ ────────────────────

Không có `--lop`/`--em` thì lệnh dùng một học viên KHÔNG CÓ THẬT. Đó là mặc
định đúng cho việc duyệt bố cục: gửi số liệu của một em thật vào hộp thư của
người đang thử nghiệm là chuyện khác hẳn, và nó phải là một hành động cố ý.
"""
import os

from django.core.management.base import BaseCommand

from common import mail

#: Học viên KHÔNG CÓ THẬT, dùng khi không truyền --lop/--em.
#:
#: Số cố ý KHÔNG đẹp: em vắng một buổi, có một buổi giảng viên quên tick, và
#: có chủ đề dưới 40%. Một tờ báo cáo toàn màu xanh không kiểm được chuyện gì
#: — nhánh "còn N buổi chưa điểm danh" và dải "Cần học lại từ gốc" sẽ không
#: bao giờ chạy, mà đó đúng là hai chỗ dễ sai nhất.
MAU = {
    'student': {'id': 0, 'name': 'Nguyễn Minh An'},
    'parent': {'name': 'Nguyễn Thị Hà'},
    'class': {'id': 0, 'name': 'Luyện HSA đợt 1/2027 — Ca tối', 'code': 'HSA-01',
              'teacher': 'Thầy Hà Thái Sơn'},
    'membership': {'joinedAt': '2026-08-10', 'leftAt': None, 'status': 'Đang học',
                   'teacherNote': 'Định lượng tiến bộ rõ. Định tính cần đọc thêm '
                                  'mỗi ngày 20 phút.'},
    'period': {'from': '2026-08-10', 'to': '2026-09-07', 'weeks': 4},
    'attendance': {'sessionsTotal': 9, 'sessionsCounted': 8, 'sessionsUnmarked': 1,
                   'present': 6, 'late': 1, 'absent': 1, 'excused': 0, 'noRecord': 0,
                   'attendedPct': 88},
    'study': {'lessonsDone': 19, 'mockCount': 3, 'mockAvg': 82, 'mockBest': 91,
              'mockTrend': 'up'},
    'topics': {
        'weak': [
            {'course': 'hsa_verbal', 'courseTitle': 'Tư duy Định tính',
             'topic': 'Đọc hiểu', 'mastery': 34},
            {'course': 'hsa_science', 'courseTitle': 'Khoa học & Tiếng Anh',
             'topic': 'Ngữ pháp', 'mastery': 41},
            {'course': 'hsa_quantitative', 'courseTitle': 'Tư duy Định lượng',
             'topic': 'Xác suất', 'mastery': 57},
        ],
        'strong': [
            {'course': 'hsa_quantitative', 'courseTitle': 'Tư duy Định lượng',
             'topic': 'Hàm số', 'mastery': 88},
            {'course': 'hsa_quantitative', 'courseTitle': 'Tư duy Định lượng',
             'topic': 'Xử lý số liệu', 'mastery': 81},
        ],
        'measured': 9, 'total': 19,
        'courses': [
            {'id': 'hsa_quantitative', 'title': 'Tư duy Định lượng',
             'lessonsDone': 11, 'lessonsTotal': 27, 'pct': 41},
            {'id': 'hsa_verbal', 'title': 'Tư duy Định tính',
             'lessonsDone': 5, 'lessonsTotal': 23, 'pct': 22},
            {'id': 'hsa_science', 'title': 'Khoa học & Tiếng Anh',
             'lessonsDone': 3, 'lessonsTotal': 26, 'pct': 12},
        ]},
    'warnings': [],
}


class Command(BaseCommand):
    help = 'Xem trước hoặc gửi thật một thư báo cáo phụ huynh (kèm PDF).'

    def add_arguments(self, ap):
        ap.add_argument('--toi', required=True, help='địa chỉ email người nhận')
        ap.add_argument('--lop', type=int, help='id lớp — DÙNG DỮ LIỆU THẬT')
        ap.add_argument('--em', type=int, help='id học viên — DÙNG DỮ LIỆU THẬT')
        ap.add_argument('--goc', default=os.environ.get('FRONTEND_URL') or 'https://tophsa.vn',
                        help='gốc đường dẫn báo cáo trong thư')

    def handle(self, *a, **o):
        from teaching.thu_bao_cao import soan_thu

        bc, nguon = MAU, 'MẪU — học viên không có thật'
        if o.get('lop') and o.get('em'):
            # Đường dữ liệu thật: đi qua đúng hàm mà API dùng, không viết lại
            # truy vấn ở đây. Hai bản dựng payload sẽ trôi khỏi nhau.
            from datetime import timedelta

            from common.clock import local_today
            from teaching.parent_report import DEFAULT_WEEKS, dung_bao_cao
            den = local_today()
            tu = den - timedelta(weeks=DEFAULT_WEEKS)
            bc, loi = dung_bao_cao(o['lop'], o['em'], tu, den)
            if loi:
                self.stderr.write('DỪNG: %s' % loi)
                return
            nguon = 'THẬT — lớp %s, học viên %s' % (o['lop'], o['em'])
        elif o.get('lop') or o.get('em'):
            self.stderr.write('DỪNG: --lop và --em phải đi cùng nhau.')
            return

        # Đường dẫn MẪU khi chưa có chìa thật: cấp chìa là ghi CSDL, mà lệnh
        # xem trước thì không được ghi gì. Dài đúng bằng chìa thật (32 byte
        # urlsafe = 43 ký tự) để bố cục nút trong thư sát thực tế.
        duong_dan = '%s/bc/%s' % (o['goc'].rstrip('/'), 'M' * 43)

        tieu_de, chu, html, dinh_kem = soan_thu(bc, duong_dan)

        thu = mail.che_do_thu()
        self.stdout.write('')
        self.stdout.write('  chế độ        : %s' % ('THỬ — ghi .eml, không gửi'
                                                    if thu else 'GỬI THẬT'))
        self.stdout.write('  cấu hình thật : %s%s' % (
            mail.da_cau_hinh(),
            '' if mail.da_cau_hinh() else '  (thiếu: %s)' % ', '.join(mail.thieu_gi())))
        self.stdout.write('  dữ liệu       : %s' % nguon)
        self.stdout.write('  người nhận    : %s' % o['toi'])
        self.stdout.write('  tiêu đề       : %s' % tieu_de)
        for ten_tep, kieu, du_lieu in dinh_kem:
            self.stdout.write('  đính kèm      : %s  (%s, %.1f KB)'
                              % (ten_tep, kieu, len(du_lieu) / 1024))
        self.stdout.write('')
        self.stdout.write('  ── PHẦN CHỮ THUẦN ──')
        for dong in chu.split('\n'):
            self.stdout.write('  | ' + dong)
        self.stdout.write('')

        if not thu and not mail.da_cau_hinh():
            self.stderr.write(
                'DỪNG: chưa có cấu hình để gửi thật. Đặt EMAIL_CHE_DO_THU=1 để chỉ '
                'xem trước, hoặc điền EMAIL_USER và EMAIL_APP_PASSWORD (App Password '
                '16 ký tự của Google, KHÔNG phải mật khẩu thường).')
            return

        ok, dau_vet, loi = mail.gui(o['toi'], tieu_de, chu, html, dinh_kem)
        self.stdout.write('  ── KẾT QUẢ ──')
        self.stdout.write('  thành công : %s' % ok)
        self.stdout.write('  dấu vết    : %s' % (dau_vet or '—'))
        self.stdout.write('  lỗi        : %s' % (loi or '—'))
        if ok and str(dau_vet or '').startswith('THU:'):
            self.stdout.write('')
            self.stdout.write('  Dấu vết bắt đầu bằng "THU:" nghĩa là KHÔNG có thư nào rời '
                              'khỏi máy. Mở tệp .eml ấy bằng Outlook / Thunderbird, hoặc '
                              'kéo vào cửa sổ soạn thư Gmail, để xem đúng thứ phụ huynh '
                              'sẽ thấy. Bỏ EMAIL_CHE_DO_THU rồi chạy lại để gửi thật.')
        self.stdout.write('')
