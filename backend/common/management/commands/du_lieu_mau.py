"""Dữ liệu TRÌNH DIỄN (§49) — xem, dựng, gỡ. Logic nằm ở `teaching/du_lieu_mau.py`.

    python manage.py du_lieu_mau            # chỉ đếm, không ghi gì
    python manage.py du_lieu_mau --tao      # dựng hai lớp mẫu + mọi hoạt động
    python manage.py du_lieu_mau --go       # gỡ sạch mọi thứ có is_demo
    python manage.py du_lieu_mau --lam-moi  # gỡ + dựng lại neo vào HÔM NAY, một giao dịch
                                            # — chạy trước mỗi buổi trình diễn
"""
import time

from django.core.management.base import BaseCommand, CommandError

from common.clock import local_today
from teaching.du_lieu_mau import (
    CU_SAU_NGAY,
    LoiDuLieuMau,
    dem,
    go,
    hoat_dong_gan_nhat,
    lam_moi,
    tao,
)


class Command(BaseCommand):
    help = 'Dữ liệu trình diễn (§49): không cờ = chỉ đếm; --tao để dựng; --go để gỡ sạch.'

    def add_arguments(self, parser):
        viec = parser.add_mutually_exclusive_group()
        viec.add_argument('--tao', action='store_true',
                          help='Dựng hai lớp mẫu, học viên, buổi học, điểm danh, bài chấm, '
                               'bài học, thi thử, kết quả thi tại trung tâm.')
        viec.add_argument('--go', action='store_true',
                          help='Gỡ SẠCH mọi tài khoản và lớp có is_demo (cùng mọi dòng treo vào).')
        viec.add_argument('--lam-moi', action='store_true',
                          help='Gỡ rồi dựng lại neo vào hôm nay, trong MỘT giao dịch (dựng hỏng '
                               'thì bộ cũ còn nguyên). Giữ giảng viên đang phụ trách lớp mẫu.')
        parser.add_argument('--giang-vien', type=int, default=None,
                            help='id tài khoản phụ trách hai lớp mẫu (mặc định: Giảng viên đầu tiên).')
        parser.add_argument('--so-em', type=int, default=None,
                            help='Số học viên MỖI lớp (mặc định 26 và 22).')

    def _in(self, tieu_de, so):
        self.stdout.write(tieu_de)
        for ten, n in so.items():
            self.stdout.write('  %-28s %d' % (ten, n))

    def _tuoi(self):
        ngay = hoat_dong_gan_nhat()
        if ngay is None:
            return
        n = (local_today() - ngay).days
        dong = 'Hoạt động mẫu gần nhất: %s (%d ngày trước).' % (ngay.strftime('%d/%m/%Y'), n)
        if n >= CU_SAU_NGAY:
            self.stdout.write(self.style.WARNING(
                dong + ' Dữ liệu đã cũ — màn hình sẽ hiện buổi chưa điểm danh và học viên '
                       '"lâu không mở bài". Chạy --lam-moi trước buổi trình diễn.'))
        else:
            self.stdout.write(dong)

    def handle(self, *args, **opt):
        bat = time.monotonic()
        try:
            if opt['tao']:
                self._in('Đã dựng dữ liệu mẫu:', tao(giang_vien_id=opt['giang_vien'],
                                                      so_em_moi_lop=opt['so_em']))
            elif opt['go']:
                truoc, sau = go()
                self._in('Trước khi gỡ:', truoc)
                self._in('Sau khi gỡ:', sau)
            elif opt['lam_moi']:
                truoc, sau = lam_moi(giang_vien_id=opt['giang_vien'], so_em_moi_lop=opt['so_em'])
                self._in('Trước khi làm mới:', truoc)
                self._in('Sau khi làm mới:', sau)
                self._tuoi()
            else:
                self._in('Dữ liệu mẫu hiện có (chỉ đếm, không ghi gì):', dem())
                self._tuoi()
        except LoiDuLieuMau as e:
            raise CommandError(str(e)) from None
        self.stdout.write(self.style.SUCCESS('Xong sau %.1f giây.' % (time.monotonic() - bat)))
