"""
bootstrap_schema — dựng lược đồ SQL thô (các bảng `managed=False`) từ `sql/*.sql`.

Render chạy lệnh này ở MỖI deploy (`render.yaml` buildCommand: pip → collectstatic →
`bootstrap_schema` → `migrate`). Đây là nguồn DDL DUY NHẤT cho các bảng `managed=False`:
`migrate` không đụng tới chúng. KHÔNG seed nội dung (seed nằm ở lệnh `seed_data`).

Từ 24/09/2026 (H3) lệnh chia tệp thành MỤC (`-- ── §NN · …`) và ghi sổ `luoc_do_da_chay`:
mỗi lượt chỉ chạy mục mới / đã đổi cùng mọi mục đứng sau nó, mỗi mục một giao dịch.
Luật và lý do: `common/luoc_do_sql.py`.

    python manage.py bootstrap_schema                  # chạy mục chờ, ghi sổ
    python manage.py bootstrap_schema --kiem           # liệt kê mục chờ, KHÔNG chạy gì
    python manage.py bootstrap_schema --kiem --ma-loi  # … và thoát 1 nếu có mục chờ (pre-push)
    python manage.py bootstrap_schema --tat-ca         # chạy lại MỌI mục như trước H3 (bỏ qua sổ)
    python manage.py bootstrap_schema --tu §57         # chạy lại TỪ một mục tới hết (sổ lệch thực tế)
    python manage.py bootstrap_schema --dien-tap       # dựng từ SỐ KHÔNG vào schema tạm, hai
                                                       # lượt, đối chiếu kiem_luoc_do, cuộn lại
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from common.luoc_do_sql import (
    SO,
    LoiLuocDo,
    _split_statements,  # noqa: F401 — phép kiểm cũ nhập từ đây
    chay_ke_hoach,
    dem_bang,
    dien_tap,
    doc_so,
    doc_tat_ca,
    lap_ke_hoach,
    mo_coi,
    tao_so,
    tim_muc,
)


class Command(BaseCommand):
    help = ('Dựng lược đồ SQL thô từ sql/*.sql theo MỤC; chỉ chạy mục chưa ghi sổ '
            '`luoc_do_da_chay` hoặc đã đổi (cùng mọi mục sau nó).')

    def add_arguments(self, parser):
        parser.add_argument('--kiem', action='store_true',
                            help='Liệt kê mục sẽ chạy ở lượt tới; không chạy, không ghi gì.')
        parser.add_argument('--ma-loi', action='store_true',
                            help='Đi cùng --kiem: thoát 1 nếu có mục chờ.')
        parser.add_argument('--tat-ca', action='store_true',
                            help='Chạy lại MỌI mục (bỏ qua sổ), rồi ghi sổ. Dùng khi kiem_luoc_do '
                                 'thấy thiếu mà sổ nói đã chạy.')
        parser.add_argument('--tu', metavar='MUC',
                            help='Chạy lại TỪ mục này (vd §57 hoặc "legacy_schema.sql §57") tới hết, '
                                 'giữ luật hậu tố. Dùng khi kiem_luoc_do báo một mục thiếu.')
        parser.add_argument('--dien-tap', action='store_true',
                            help='Diễn tập CSDL mới toanh trong một schema tạm: hai lượt, đối '
                                 'chiếu kiem_luoc_do, rồi cuộn lại.')

    def handle(self, *args, **opt):
        try:
            cac_muc = doc_tat_ca()
        except LoiLuocDo as e:
            raise CommandError(str(e)) from e

        try:
            tu = tim_muc(cac_muc, opt['tu']) if opt['tu'] else None
        except LoiLuocDo as e:
            raise CommandError(str(e)) from e

        if opt['dien_tap']:
            return self._dien_tap()
        if opt['kiem']:
            return self._kiem(cac_muc, opt['ma_loi'], opt['tat_ca'], tu)

        with connection.cursor() as cur:
            truoc = dem_bang(cur)
            tao_so(cur)
            so = doc_so(cur)
        viec = lap_ke_hoach(cac_muc, so, tat_ca=opt['tat_ca'], tu=tu)
        if not so and not opt['tat_ca']:
            self.stdout.write('  Sổ %s còn trống — lượt đầu chạy MỌI mục một lần rồi ghi sổ.' % SO)
        try:
            chay_ke_hoach(viec, ghi=self.stdout.write)
        except LoiLuocDo as e:
            raise CommandError(str(e)) from e
        with connection.cursor() as cur:
            sau = dem_bang(cur)
        self.stdout.write(self.style.SUCCESS(
            '[bootstrap_schema] %d/%d mục chạy (%d câu) · bảng: %d -> %d'
            % (len(viec), len(cac_muc), sum(len(v.muc.cau) for v in viec), truoc, sau)))

    def _kiem(self, cac_muc, ma_loi, tat_ca, tu):
        with connection.cursor() as cur:
            so = doc_so(cur)
        viec = lap_ke_hoach(cac_muc, so, tat_ca=tat_ca, tu=tu)
        if so is None:
            self.stdout.write('Sổ %s CHƯA có trên CSDL này — lượt bootstrap tới chạy MỌI mục '
                              '(%d mục) một lần rồi ghi sổ.' % (SO, len(cac_muc)))
        else:
            self.stdout.write('Sổ %s: %d mục đã ghi; tệp có %d mục.' % (SO, len(so), len(cac_muc)))
        if viec:
            self.stdout.write(self.style.WARNING(
                'Mục sẽ chạy ở lượt bootstrap tới (%d):' % len(viec)))
            for v in viec:
                self.stdout.write('  · %-26s %3d câu — %s' % (v.muc.khoa, len(v.muc.cau), v.ly_do))
        else:
            self.stdout.write(self.style.SUCCESS('Không mục nào chờ.'))
        coi = mo_coi(cac_muc, so)
        if coi:
            self.stdout.write('Có trong sổ mà không còn trong tệp (đổi số / nhánh khác — vô hại): '
                              + ', '.join(coi))
        if ma_loi and viec:
            raise SystemExit(1)

    def _dien_tap(self):
        self.stdout.write('Diễn tập CSDL mới toanh (schema tạm, cuộn lại khi xong)…')
        ket = dien_tap()
        self.stdout.write(
            '  lượt 1: sổ ghi %d/%d mục · %d bảng · lượt 2: %d mục chạy lại, %d ràng buộc/chỉ mục '
            'bị dỡ-dựng' % (ket['so_dong_so'], ket['so_muc'], ket['so_bang'],
                            len(ket['chay_lai_luot2']), len(ket['doi_luot2'])))
        self.stdout.write('  kiem_luoc_do: %d/%d mục tới nơi'
                          % (ket['kiem_tong'] - len(ket['kiem_thieu']), ket['kiem_tong']))
        for t in ket['loi']:
            self.stdout.write('    ✗ ' + t)
        if ket['loi']:
            raise CommandError('Diễn tập KHÔNG ĐẠT (%d lỗi) — đã cuộn lại.' % len(ket['loi']))
        self.stdout.write(self.style.SUCCESS('Diễn tập ĐẠT — đã cuộn lại, CSDL không đổi.'))
