"""Nạp bộ minh hoạ soạn sẵn (`lessons/minh_hoa/`) vào `lessons.content_json`.

    python manage.py nap_minh_hoa --thu    # kiểm tra từng bài, KHÔNG ghi
    python manage.py nap_minh_hoa --nap    # ghi trong MỘT giao dịch

Mỗi minh hoạ gắn vào thẻ ĐẦY ĐỦ đã chỉ định VÀ một thẻ TÓM TẮT (xem docstring
`lessons/minh_hoa/__init__.py` — vì sao cả hai). Đi đúng cửa ghi của quản trị viên
(`courseadmin/views.py::put`): `validate_lesson` trước khi ghi, `quen_dap_an` sau.
Chạy lại được: giống thì giữ, khác thì cập nhật (xem `_gan`).
"""
import json
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from common.db import q, x
from lessons.content import validate_lesson
from lessons.grading import quen_dap_an
from lessons.minh_hoa import BO_MINH_HOA, THE_TOM_TAT, THE_TOM_TAT_CO_SAN


def _tu(s):
    return {w for w in re.findall(r'\w+', (s or '').lower()) if len(w) > 2}


def _co_hinh(card):
    return isinstance(card.get('visual'), dict) and bool(card['visual'].get('type'))


def chon_the_tom_tat(khoa, so, the_day_du, cards_tom_tat, ghi_tay=THE_TOM_TAT, chi_trong=False):
    """Thẻ tóm tắt nhận bản sao: ghi tay nếu có, không thì thẻ trùng nhiều từ nhất.

    `chi_trong=True`: chỉ xét thẻ CHƯA có hình (cho lượt sao hình có sẵn — bài #7
    có hai đồ thị, hình thứ hai phải rơi vào thẻ còn trống chứ không chồng lên).
    """
    if (khoa, so) in ghi_tay:
        return ghi_tay[(khoa, so)]
    ung_vien = [i for i, k in enumerate(cards_tom_tat) if not (chi_trong and _co_hinh(k))]
    if not ung_vien:
        return None
    goc = _tu(the_day_du.get('title'))
    return max(ung_vien, key=lambda i: len(goc & (_tu(cards_tom_tat[i].get('title'))
                                                 | _tu(cards_tom_tat[i].get('body')))))


def _gan(card, visual):
    """Gắn (hoặc cập nhật) minh hoạ. Trả True khi có đổi.

    Ghi đè khi khác: bộ này không chạm 9 bài đã có minh hoạ soạn tay
    (`tests_minh_hoa` giữ điều đó), nên trong các bài của bộ, minh hoạ đang có
    chỉ có thể là bản cũ của chính bộ — sửa dữ liệu rồi chạy lại là cập nhật.
    """
    if card.get('visual') == visual:
        return False
    card['visual'] = visual
    return True


def ghep(rows, ghi, bo=None):
    """Trả (số bài đã đổi, dòng báo cáo, lỗi). `ghi=True` thì UPDATE.

    `bo`: bộ minh hoạ soạn sẵn (mặc định `BO_MINH_HOA`; phép kiểm truyền bộ nhỏ)."""
    bo = BO_MINH_HOA if bo is None else bo
    theo_khoa = {}
    for r in rows:
        theo_khoa.setdefault(r['course_id'], {})[r['sort_order']] = r
    bao_cao, loi, doi = [], [], 0
    for khoa, bo_khoa in bo.items():
        for so, (the, visual) in sorted(bo_khoa.items()):
            r = theo_khoa.get(khoa, {}).get(so)
            if not r:
                loi.append('%s #%d: không có bài này trong CSDL' % (khoa, so))
                continue
            c = r['content_json']
            c = json.loads(c) if isinstance(c, str) else c
            th = (c or {}).get('theory') or {}
            full = (th.get('full') or {}).get('cards') or []
            cond = (th.get('condensed') or {}).get('cards') or []
            if not 0 <= the < len(full):
                loi.append('%s #%d: thẻ đầy đủ %d không tồn tại (bài có %d thẻ)' % (khoa, so, the, len(full)))
                continue
            tt = chon_the_tom_tat(khoa, so, full[the], cond)
            if tt is not None and not 0 <= tt < len(cond):
                loi.append('%s #%d: thẻ tóm tắt %d không tồn tại (bài có %d thẻ)' % (khoa, so, tt, len(cond)))
                continue
            da_full = _gan(full[the], visual)
            da_cond = tt is not None and _gan(cond[tt], visual)
            if not (da_full or da_cond):
                bao_cao.append('  giữ     %-17s #%2d không đổi' % (khoa, so))
                continue
            errs = validate_lesson(c, path='%s #%d' % (khoa, so))
            if errs:
                loi.extend(errs)
                continue
            doi += 1
            bao_cao.append('  %-7s %-17s #%2d %-8s đầy đủ[%d]%s "%s" · tóm tắt[%s]%s "%s"' % (
                'GHI' if ghi else 'sẽ ghi', khoa, so, visual['type'],
                the, '' if da_full else '(đã có)', full[the].get('title', '')[:26],
                tt, '' if da_cond else '(đã có)', (cond[tt].get('title', '') if tt is not None else '—')[:26]))
            if ghi:
                x('UPDATE lessons SET content_json=%s::jsonb WHERE id=%s',
                  (json.dumps(c, ensure_ascii=False), r['id']))
                quen_dap_an(khoa, so)

    # ── Lượt hai: 9 bài có hình soạn tay từ trước — sao sang thẻ tóm tắt còn trống ──
    for khoa, theo_so in theo_khoa.items():
        for so, r in sorted(theo_so.items()):
            if so in bo.get(khoa, {}):
                continue
            c = r['content_json']
            c = json.loads(c) if isinstance(c, str) else c
            th = (c or {}).get('theory') or {}
            full = (th.get('full') or {}).get('cards') or []
            cond = (th.get('condensed') or {}).get('cards') or []
            hinh = [k for k in full if _co_hinh(k)]
            if not hinh or not cond:
                continue
            da_sao = []
            for i, k in enumerate(hinh):
                # Hình này đã nằm ở bản tóm tắt thì thôi. Không có dòng này, lần chạy
                # thứ hai thấy thẻ đã nhận hình là "hết trống" và sao CÙNG hình ấy sang
                # thẻ trống còn lại — `--thu` ngay sau `--nap` đã báo 4 bài (17/09).
                if any(cd.get('visual') == k['visual'] for cd in cond):
                    continue
                tt = chon_the_tom_tat(khoa, so, k, cond, ghi_tay=THE_TOM_TAT_CO_SAN if i == 0 else {},
                                      chi_trong=True)
                if tt is None or _co_hinh(cond[tt]):
                    continue
                cond[tt]['visual'] = k['visual']
                da_sao.append('%s → tóm tắt[%d] "%s"' % (k['visual']['type'], tt, (cond[tt].get('title') or '')[:24]))
            if not da_sao:
                bao_cao.append('  giữ     %-17s #%2d hình có sẵn đã ở cả hai bản' % (khoa, so))
                continue
            errs = validate_lesson(c, path='%s #%d' % (khoa, so))
            if errs:
                loi.extend(errs)
                continue
            doi += 1
            bao_cao.append('  %-7s %-17s #%2d có sẵn: %s' % ('GHI' if ghi else 'sẽ ghi', khoa, so, ' · '.join(da_sao)))
            if ghi:
                x('UPDATE lessons SET content_json=%s::jsonb WHERE id=%s',
                  (json.dumps(c, ensure_ascii=False), r['id']))
                quen_dap_an(khoa, so)
    return doi, bao_cao, loi


class Command(BaseCommand):
    help = 'Nạp bộ minh hoạ soạn sẵn vào bài học. --thu chỉ kiểm; --nap ghi thật.'

    def add_arguments(self, parser):
        g = parser.add_mutually_exclusive_group(required=True)
        g.add_argument('--thu', action='store_true', help='Kiểm tra, không ghi.')
        g.add_argument('--nap', action='store_true', help='Ghi vào CSDL trong một giao dịch.')

    def handle(self, *args, **opt):
        rows = q('SELECT id, course_id, sort_order, content_json FROM lessons '
                 'WHERE course_id = ANY(%s)', (list(BO_MINH_HOA),))
        with transaction.atomic():
            doi, bao_cao, loi = ghep(rows, ghi=opt['nap'])
            for d in bao_cao:
                self.stdout.write(d)
            if loi:
                for e in loi:
                    self.stdout.write(self.style.ERROR('  LỖI ' + e))
                raise CommandError('%d lỗi — không ghi gì (giao dịch đã cuộn lại).' % len(loi))
        self.stdout.write(self.style.SUCCESS('%s %d bài.' % ('Đã ghi' if opt['nap'] else 'Sẽ ghi', doi)))
