"""Xem trước — hoặc gửi thật — MỘT tin ZNS báo cáo phụ huynh.

── VÌ SAO CÓ LỆNH NÀY (07/09/2026) ─────────────────────────────────────────

Anh Sơn muốn thử ZNS bằng số của mình trước khi bật cho cả lớp. Đường gửi hàng
loạt (`ParentReportSendAllView`) thì cần một lớp có thật, học viên có thật, và
số phụ huynh đã khai — quá nhiều thứ phải dựng chỉ để xem một tin trông thế nào.

Lệnh này đi ĐÚNG hàm mà đường hàng loạt gọi (`zalo.gui_zns`), nên thứ nó in ra
là thứ sẽ đi thật. Nó KHÔNG dựng một bản xem trước riêng — bản xem trước riêng
sẽ trôi khỏi bản gửi thật, và khi ấy người duyệt nội dung duyệt nhầm một thứ
khác với thứ phụ huynh nhận.

── HAI CHẾ ĐỘ, VÀ MẶC ĐỊNH LÀ CHẾ ĐỘ AN TOÀN ──────────────────────────────

    ZALO_CHE_DO_THU=1     → in ra thân request, KHÔNG gọi Zalo, không mất phí
    (không đặt biến)      → gửi THẬT, cần ZALO_OA_ACCESS_TOKEN + ZALO_ZNS_TEMPLATE_ID

Lệnh KHÔNG ghi gì vào CSDL ở cả hai chế độ: nó không thuộc một lượt gửi nào của
một lớp nào, nên không có dòng nào trong `parent_report_sends` để thuộc về.

    python manage.py thu_zns --so 0812315276
    python manage.py thu_zns --so 0812315276 --ten "Nguyễn Văn A" --lop "Ca tối"

── VÌ SAO IN CẢ ĐƯỜNG DẪN GIẢ ─────────────────────────────────────────────

Tham số `duong_dan` là thứ phụ huynh sẽ bấm. Trong lần thử, không có chìa thật
nào để đưa vào (cấp chìa là ghi CSDL), nên lệnh dựng một đường dẫn MẪU và nói
rõ nó là mẫu. Nhìn được độ dài và hình dạng của link trong tin là đủ cho việc
duyệt mẫu ZNS — Zalo đếm ký tự.
"""
import json

from django.core.management.base import BaseCommand

from common import zalo
from teaching.parent_send import THAM_SO_MAU


class Command(BaseCommand):
    help = 'Xem trước hoặc gửi thật một tin ZNS báo cáo phụ huynh.'

    def add_arguments(self, ap):
        ap.add_argument('--so', required=True, help='số Zalo người nhận, ví dụ 0812315276')
        ap.add_argument('--ten', default='Nguyễn Văn A', help='tên học viên trong tin')
        ap.add_argument('--lop', default='Luyện HSA đợt 1/2027 — Ca tối', help='tên lớp')
        ap.add_argument('--ky', default='10/08/2026 – 07/09/2026', help='kỳ báo cáo')
        ap.add_argument('--goc', default='https://tophsa.vn',
                        help='gốc đường dẫn báo cáo (mặc định là tên miền dự kiến)')

    def handle(self, *a, **o):
        tham_so = {
            'ten_hoc_vien': o['ten'],
            'ten_lop': o['lop'],
            'ky': o['ky'],
            # Chìa MẪU — dài đúng bằng chìa thật (32 byte urlsafe = 43 ký tự)
            # để con số ký tự trong tin sát thực tế lúc nộp mẫu cho Zalo duyệt.
            'duong_dan': '%s/bc/%s' % (o['goc'].rstrip('/'), 'M' * 43),
        }

        # Bốn tham số phải khớp `THAM_SO_MAU` — nếu mẫu Zalo đổi thì lệnh này
        # phải đổi theo, và chỗ duy nhất giữ danh sách ấy là `parent_send.py`.
        thieu = [k for k in THAM_SO_MAU if k not in tham_so]
        if thieu:
            self.stderr.write('Thiếu tham số mẫu: %s' % ', '.join(thieu))
            return

        thu = zalo.che_do_thu()
        self.stdout.write('')
        self.stdout.write('  chế độ        : %s' % ('THỬ — không gọi Zalo, không mất phí'
                                                    if thu else 'GỬI THẬT'))
        self.stdout.write('  cấu hình thật : %s%s' % (
            zalo.da_cau_hinh(),
            '' if zalo.da_cau_hinh() else '  (thiếu: %s)' % ', '.join(zalo.thieu_gi())))
        self.stdout.write('  người nhận    : %s' % o['so'])
        self.stdout.write('')
        self.stdout.write('  ── THÂN REQUEST SẼ GỬI ──')
        for d in json.dumps(zalo.soan_zns(o['so'], tham_so),
                            ensure_ascii=False, indent=2).split('\n'):
            self.stdout.write('  ' + d)
        self.stdout.write('')

        if not thu and not zalo.da_cau_hinh():
            self.stderr.write(
                'DỪNG: chưa có cấu hình để gửi thật. Đặt ZALO_CHE_DO_THU=1 để chỉ xem '
                'trước, hoặc điền ZALO_OA_ACCESS_TOKEN và ZALO_ZNS_TEMPLATE_ID.')
            return

        ok, ma, loi = zalo.gui_zns(o['so'], tham_so)
        self.stdout.write('  ── KẾT QUẢ ──')
        self.stdout.write('  thành công : %s' % ok)
        self.stdout.write('  mã tin     : %s' % (ma or '—'))
        self.stdout.write('  lỗi        : %s' % (loi or '—'))
        if thu:
            self.stdout.write('')
            self.stdout.write('  Mã bắt đầu bằng "THU:" nghĩa là KHÔNG có tin nào rời khỏi '
                              'máy chủ. Bỏ ZALO_CHE_DO_THU rồi chạy lại để gửi thật.')
        self.stdout.write('')
