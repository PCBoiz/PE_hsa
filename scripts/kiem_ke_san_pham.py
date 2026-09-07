"""Kiểm kê sản phẩm — sinh dữ liệu THẬT cho hồ sơ gửi TopHSA.

── VÌ SAO CÓ TỆP NÀY (07/09/2026) ──────────────────────────────────────────

Anh Sơn cần một hồ sơ tổng hợp gửi TopHSA: tính năng, vai trò, phân quyền, kiến
trúc, luồng hoạt động, và những gì cần từ phía họ.

Một tài liệu như thế viết tay xong là bắt đầu SAI DẦN: thêm một endpoint, đổi
một vai trò, bỏ một màn hình — không ai nhớ mở lại tệp .pdf để sửa. Và một hồ sơ
gửi đối tác mà nói sai con số thì nó hỏng đúng thứ nó sinh ra để làm.

Nên mọi CON SỐ trong hồ sơ đến từ đây, và đây thì đọc thẳng từ mã nguồn + CSDL.
Phần chữ (diễn giải, bối cảnh) vẫn viết tay — máy không viết thay được — nhưng
số thì máy đếm.

    python scripts/kiem_ke_san_pham.py --ra ho_so.json

CHỈ ĐỌC. Không ghi một dòng nào vào CSDL.
"""
import argparse
import io
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
CWD_GOI = Path.cwd()          # nhớ trước khi đổi thư mục — xem `cap_the.py`
sys.path.insert(0, str(GOC / 'backend'))
os.chdir(GOC / 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django  # noqa: E402
django.setup()

from django.urls import get_resolver  # noqa: E402

from common.db import q, q1  # noqa: E402


def _duong_dan_api():
    """Mọi đường `api/` kèm lớp phân quyền — cùng lối `scripts/quet_quyen.py`."""
    ra = []
    for m in get_resolver().url_patterns:
        for p in getattr(m, 'url_patterns', [m]):
            duong = str(getattr(p, 'pattern', ''))
            cls = getattr(getattr(p, 'callback', None), 'cls', None)
            if not duong.startswith('api/') or cls is None:
                continue
            quyen = [c.__name__ for c in getattr(cls, 'permission_classes', [])]
            xac_thuc = getattr(cls, 'authentication_classes', None)
            # `khaiTay`: view có TỰ viết `permission_classes` hay không. DRF trả
            # về danh sách MẶC ĐỊNH (`[IsAuthenticated]`) cho cả view không khai
            # gì, nên nhìn `permission_classes` không phân biệt được hai trường
            # hợp — mà đó đúng là chỗ nguy hiểm: quên khai thì cửa mở cho MỌI
            # người đã đăng nhập, im lặng, trông y hệt một quyết định có chủ ý.
            khai_tay = 'permission_classes' in vars(cls)
            ra.append({
                'duong': duong, 'view': cls.__name__,
                'quyen': quyen or ['(không có lớp nào)'],
                'khaiTay': khai_tay,
                'congKhai': 'AllowAny' in quyen or xac_thuc == [],
            })
    return sorted(ra, key=lambda r: r['duong'])


def _bang_csdl():
    """Bảng trong lược đồ `public` kèm số dòng. Số dòng cho thấy phần nào của
    sản phẩm đã CHẠY THẬT và phần nào mới chỉ dựng xong."""
    ten = [r['table_name'] for r in q(
        """SELECT table_name FROM information_schema.tables
           WHERE table_schema='public' AND table_type='BASE TABLE'
           ORDER BY table_name""")]
    ra = []
    for t in ten:
        try:
            ra.append({'bang': t, 'dong': q1('SELECT count(*) AS n FROM "%s"' % t)['n']})
        except Exception:
            ra.append({'bang': t, 'dong': None})
    return ra


def _vai_tro():
    from common import permissions as pm
    return {
        'danhSach': list(pm.ASSIGNABLE_ROLES),
        'lopQuyen': sorted(
            n for n in dir(pm)
            if n.startswith('Is') and isinstance(getattr(pm, n), type)),
    }


def _trang():
    goc = GOC / 'frontend' / 'src' / 'app'
    ra = []
    for p in sorted(goc.rglob('page.tsx')):
        d = str(p.parent.relative_to(goc)).replace(os.sep, '/')
        d = re.sub(r'\((base|standalone)\)/?', '', d)
        ra.append('/' + (d if d != '.' else ''))
    return sorted(set(ra))


def _dem_kiem_thu():
    """Số TỆP kiểm thử, không phải số phép kiểm — đếm phép kiểm đòi chạy cả bộ
    (29 phút). Con số phép kiểm thật ghi tay trong hồ sơ, kèm ngày đo."""
    be = len(list((GOC / 'backend').rglob('tests*.py')))
    fe = len(list((GOC / 'frontend' / 'e2e').rglob('*.test.mjs'))) \
        + len(list((GOC / 'frontend' / 'e2e').rglob('*.spec.ts')))
    return {'tepBackend': be, 'tepFrontend': fe}


def _so_lieu_hoc():
    """Vài con số nghiệp vụ, để hồ sơ nói đúng hiện trạng thay vì nói chung chung."""
    def d(sql, *a):
        try:
            return q1(sql, a)['n']
        except Exception:
            return None
    return {
        'khoaHoc': d('SELECT count(*) AS n FROM courses'),
        'baiHoc': d('SELECT count(*) AS n FROM lessons'),
        'taiKhoan': d('SELECT count(*) AS n FROM users'),
        'hocVien': d("SELECT count(*) AS n FROM users WHERE role=%s", 'Học viên'),
        'lop': d('SELECT count(*) AS n FROM classes'),
        'dotHoc': d('SELECT count(*) AS n FROM terms'),
        'buoiHoc': d('SELECT count(*) AS n FROM class_sessions'),
        'diemDanh': d('SELECT count(*) AS n FROM attendance'),
        'deThiThu': d('SELECT count(*) AS n FROM mock_exams'),
        'cauHoiThiThu': d('SELECT count(*) AS n FROM mock_questions'),
        'coEmailPhuHuynh': d("SELECT count(*) AS n FROM users WHERE parent_email <> ''"),
        'coSoPhuHuynh': d("SELECT count(*) AS n FROM users WHERE parent_phone <> ''"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ra', default='ho_so.json')
    o = ap.parse_args()

    api = _duong_dan_api()
    ho_so = {
        'ngayDo': date.today().isoformat(),
        'vaiTro': _vai_tro(),
        'api': {
            'tong': len(api),
            'congKhai': [r for r in api if r['congKhai']],
            # "Chỉ cần đăng nhập" = mọi vai trò đều vào được, kể cả học viên.
            # ĐÚNG với dữ liệu của chính người dùng, SAI nếu view đọc dữ liệu
            # của người khác — nên hồ sơ liệt kê ra để đối chiếu từng dòng.
            'chiDangNhap': [r for r in api
                            if not r['congKhai'] and r['quyen'] == ['IsAuthenticated']],
            'coCong': [r for r in api
                       if not r['congKhai'] and r['quyen'] != ['IsAuthenticated']],
        },
        'bang': _bang_csdl(),
        'trang': _trang(),
        'kiemThu': _dem_kiem_thu(),
        'soLieu': _so_lieu_hoc(),
    }

    # `--ra` giải theo thư mục NGƯỜI GỌI đứng, không theo `backend/` mà tệp này
    # vừa `chdir` vào — cùng cái bẫy `cap_the.py` đã mắc và đã ghi lại.
    p = Path(o.ra)
    if not p.is_absolute():
        p = CWD_GOI / p
    with io.open(p, 'w', encoding='utf-8') as fh:
        json.dump(ho_so, fh, ensure_ascii=False, indent=2)

    print('Đã kiểm kê → %s' % p)
    print('  vai trò          : %d' % len(ho_so['vaiTro']['danhSach']))
    print('  lớp phân quyền   : %d' % len(ho_so['vaiTro']['lopQuyen']))
    print('  đường API        : %d  (công khai %d · chỉ đăng nhập %d · có cổng %d)' % (
        ho_so['api']['tong'], len(ho_so['api']['congKhai']),
        len(ho_so['api']['chiDangNhap']), len(ho_so['api']['coCong'])))
    print('  bảng CSDL        : %d' % len(ho_so['bang']))
    print('  trang giao diện  : %d' % len(ho_so['trang']))
    print('  tệp kiểm thử     : %s' % ho_so['kiemThu'])


if __name__ == '__main__':
    main()
