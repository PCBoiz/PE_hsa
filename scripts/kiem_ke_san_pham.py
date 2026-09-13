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
import json
import os
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
CWD_GOI = Path.cwd()          # nhớ trước khi đổi thư mục — xem `cap_the.py`
sys.path.insert(0, str(GOC / 'backend'))
os.chdir(GOC / 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from django.urls import get_resolver

from common.clock import local_today
from common.db import q, q1
from common.views import da_khai_cong


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
            # `khaiTay`: view có TỰ khai cổng không — ở chính nó hoặc ở lớp cha
            # của dự án. Dùng CHUNG hàm với `tests_khai_cong.py`; bản đầu tự
            # đếm bằng `vars(cls)` và báo 71 thay vì 60 (đếm cả view khai qua
            # `AdminBase`). Hai bộ đếm một thứ ra hai số là thứ làm mất tin.
            khai_tay = da_khai_cong(cls)
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
            ra.append({'bang': t, 'dong': q1(f'SELECT count(*) AS n FROM "{t}"')['n']})
        except Exception:  # noqa: BLE001 — một bảng không đếm được (thiếu quyền,
            # bảng hệ thống) không được làm hỏng cả bản kiểm kê; ghi None và đi tiếp.
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
        except Exception:  # noqa: BLE001 — cùng lý do ở `_bang_csdl`: thiếu một
            # con số thì ghi None, không được ném để mất cả bản kiểm kê.
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


def _viet_md(h, ten_lenh):
    """Bản markdown đọc được của cùng số đo — `BAO-CAO-TRANG-THAI.md`.

    Học từ dự án cô Giang (chỉ đọc bên ấy để học cách làm): bản này CHỈ ĐO,
    không nhận định. Muốn biết vì sao một con số ra như vậy thì đọc PROGRESS.md.
    Và ĐỪNG chép số từ đây sang tài liệu khác — chép ra là bắt đầu cũ đi; chạy
    lại lệnh thì có số mới.
    """
    S = h['soLieu']
    api = h['api']
    khong_khai = [r for r in api['chiDangNhap'] if not r['khaiTay']]
    co_dong = [b for b in h['bang'] if (b['dong'] or 0) > 0]
    ngay = h['ngayDo'][8:10] + '/' + h['ngayDo'][5:7] + '/' + h['ngayDo'][:4]

    def hang(cac):
        return '\n'.join('| %s |' % ' | '.join(str(c) for c in r) for r in cac)

    return f'''# Báo cáo trạng thái — số đo thật

*Sinh tự động ngày {ngay} bằng `{ten_lenh}`. Mọi con số dưới đây được đếm lại từ mã
nguồn hoặc đo trực tiếp trên CSDL tại thời điểm chạy lệnh.*

*Bản này CHỈ ĐO, không nhận định. Muốn biết vì sao một con số ra như vậy thì đọc
`PROGRESS.md`. Đừng chép số từ đây sang tài liệu khác — chép ra là bắt đầu cũ đi.*

---

## Mã nguồn

| Hạng mục | Số đo | Nguồn |
|---|---|---|
{hang([
    ('Vai trò người dùng', len(h['vaiTro']['danhSach']), '`permissions.py` → `ASSIGNABLE_ROLES`'),
    ('Lớp cổng phân quyền', len(h['vaiTro']['lopQuyen']), '`permissions.py` → `Is*`'),
    ('Đường API', api['tong'], '`get_resolver()` — đường bắt đầu bằng `api/`'),
    ('· không cần đăng nhập', len(api['congKhai']), 'AllowAny hoặc `authentication_classes = []`'),
    ('· chỉ cần đăng nhập', len(api['chiDangNhap']), '`permission_classes == [IsAuthenticated]`'),
    ('· · trong đó KHÔNG tự khai cổng', len(khong_khai), 'dựa vào mặc định của khung'),
    ('· có cổng vai trò', len(api['coCong']), 'lớp `Is*` khác'),
    ('Trang giao diện', len(h['trang']), '`frontend/src/app/**/page.tsx`'),
    ('Bảng CSDL', len(h['bang']), '`information_schema.tables`'),
    ('· có dữ liệu', len(co_dong), 'count(*) > 0'),
    ('Tệp kiểm thử backend', h['kiemThu']['tepBackend'], '`backend/**/tests*.py`'),
    ('Tệp kiểm thử frontend', h['kiemThu']['tepFrontend'], '`frontend/e2e/**`'),
])}

## Dữ liệu nghiệp vụ trên CSDL

| Hạng mục | Số đo |
|---|---|
{hang([
    ('Hợp phần (khoá học)', S['khoaHoc']), ('Bài học', S['baiHoc']),
    ('Tài khoản', S['taiKhoan']), ('· học viên', S['hocVien']),
    ('Lớp', S['lop']), ('Đợt học', S['dotHoc']), ('Buổi học', S['buoiHoc']),
    ('Lượt điểm danh', S['diemDanh']), ('Đề thi thử', S['deThiThu']),
    ('Học viên có email phụ huynh', S['coEmailPhuHuynh']),
    ('Học viên có số phụ huynh', S['coSoPhuHuynh']),
])}

## Đường API chỉ cần đăng nhập mà KHÔNG tự khai cổng

*Mặc định của khung là "phải đăng nhập" — đúng, nhưng một đường mới quên khai sẽ
mở cho mọi người đã đăng nhập, im lặng. Liệt kê để đối chiếu từng dòng.*

{hang([(r['duong'], r['view']) for r in khong_khai]) or '(không có)'}

---

*Sinh bởi `scripts/kiem_ke_san_pham.py --md`. Chạy lại bất cứ lúc nào để có số mới.*
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ra', default='ho_so.json')
    ap.add_argument('--md', default='', help='đường dẫn BAO-CAO-TRANG-THAI.md (tuỳ chọn)')
    o = ap.parse_args()

    api = _duong_dan_api()
    ho_so = {
        'ngayDo': local_today().isoformat(),  # giờ VN, cùng đồng hồ với sản phẩm
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
    with open(p, 'w', encoding='utf-8') as fh:
        json.dump(ho_so, fh, ensure_ascii=False, indent=2)

    if o.md:
        pm = Path(o.md)
        if not pm.is_absolute():
            pm = CWD_GOI / pm
        with open(pm, 'w', encoding='utf-8') as fh:
            fh.write(_viet_md(ho_so, 'python scripts/kiem_ke_san_pham.py --md'))
        print('Đã viết → %s' % pm)

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
