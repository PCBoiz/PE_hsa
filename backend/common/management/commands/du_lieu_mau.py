"""Dữ liệu TRÌNH DIỄN (§49) — xem, dựng, gỡ. Logic nằm ở `teaching/du_lieu_mau.py`.

    python manage.py du_lieu_mau            # chỉ đếm, không ghi gì
    python manage.py du_lieu_mau --tao      # dựng hai lớp mẫu + mọi hoạt động
    python manage.py du_lieu_mau --go       # gỡ sạch mọi thứ có is_demo
"""
import time

from django.core.management.base import BaseCommand, CommandError

from teaching.du_lieu_mau import LoiDuLieuMau, dem, go, tao


class Command(BaseCommand):
    help = 'Dữ liệu trình diễn (§49): không cờ = chỉ đếm; --tao để dựng; --go để gỡ sạch.'

    def add_arguments(self, parser):
        viec = parser.add_mutually_exclusive_group()
        viec.add_argument('--tao', action='store_true',
                          help='Dựng hai lớp mẫu, học viên, buổi học, điểm danh, bài chấm, '
                               'bài học, thi thử, kết quả thi tại trung tâm.')
        viec.add_argument('--go', action='store_true',
                          help='Gỡ SẠCH mọi tài khoản và lớp có is_demo (cùng mọi dòng treo vào).')
        parser.add_argument('--giang-vien', type=int, default=None,
                            help='id tài khoản phụ trách hai lớp mẫu (mặc định: Giảng viên đầu tiên).')
        parser.add_argument('--so-em', type=int, default=None,
                            help='Số học viên MỖI lớp (mặc định 26 và 22).')

    def _in(self, tieu_de, so):
        self.stdout.write(tieu_de)
        for ten, n in so.items():
            self.stdout.write('  %-28s %d' % (ten, n))

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
            else:
                self._in('Dữ liệu mẫu hiện có (chỉ đếm, không ghi gì):', dem())
        except LoiDuLieuMau as e:
            raise CommandError(str(e)) from None
        self.stdout.write(self.style.SUCCESS('Xong sau %.1f giây.' % (time.monotonic() - bat)))
