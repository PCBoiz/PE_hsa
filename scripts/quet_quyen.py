"""LIỆT KÊ MỌI VIEW API VÀ LỚP QUYỀN CỦA NÓ — hỏi bộ định tuyến đang chạy.

── VÌ SAO CÓ TỆP NÀY (07/09/2026) ───────────────────────────────────────────

`DEFAULT_PERMISSION_CLASSES` của dự án là `IsAuthenticated`. Nghĩa là một view
QUÊN khai `permission_classes` không đổ lỗi, không cảnh báo — nó chỉ lặng lẽ mở
cho **mọi tài khoản đăng nhập**, kể cả học viên. Đó là lớp lỗ hổng nguy nhất
trong dự án này, vì nó không có triệu chứng nào: màn hình chạy đúng, phép kiểm
xanh, và người duy nhất phát hiện ra sẽ là người khai thác nó.

Grep `permission_classes` không trả lời được câu ấy — nó chỉ thấy chỗ CÓ khai,
không thấy chỗ THIẾU. Và `permission_classes` còn kế thừa được từ lớp cha, nên
đọc mã bằng regex sẽ báo oan chỗ kế thừa đúng.

Nên tệp này đi qua `get_resolver()` — chính bộ định tuyến Django đang chạy — và
đọc thuộc tính đã phân giải trên lớp view. Hỏi thứ đang chạy thật, không hỏi mã
nguồn.

── BỘ NÀY THU HẸP VÙNG PHẢI NHÌN, KHÔNG KẾT LUẬN ───────────────────────────

`IsAuthenticated` là ĐÚNG cho phần lớn view: bài học, tiến độ của chính mình,
diễn đàn. Nó chỉ SAI khi view ấy đọc hay sửa dữ liệu của người khác. Máy không
biết view nào thuộc loại nào — nên đầu ra dưới đây là danh sách để đọc bằng
mắt, không phải danh sách lỗi.

(Bài học 07/09: một bộ dò tôi tự viết đã báo oan bốn lần trong một buổi, và
lần đắt nhất là khi con số của nó kịp vào tài liệu và vào một câu hỏi cho anh
Sơn quyết. Xem `docs/VIEC_CUA_ANH.md` mục 12.4.)

Chạy:
    backend/.venv/Scripts/python.exe scripts/quet_quyen.py
    backend/.venv/Scripts/python.exe scripts/quet_quyen.py --tat-ca
"""
import os
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.chdir(GOC / 'backend')

import django  # noqa: E402

django.setup()

from django.urls import get_resolver  # noqa: E402


def _di(res, tien_to=''):
    """Duyệt cây định tuyến, trả về (đường dẫn đầy đủ, hàm xử lý)."""
    for p in res.url_patterns:
        if hasattr(p, 'url_patterns'):
            yield from _di(p, tien_to + str(p.pattern))
        else:
            yield tien_to + str(p.pattern), p.callback


def quet():
    ra = []
    for duong, cb in _di(get_resolver()):
        cls = getattr(cb, 'cls', None) or getattr(cb, 'view_class', None)
        if cls is None:
            continue
        ra.append({
            'duong': duong,
            'view': cls.__name__,
            'module': cls.__module__,
            'quyen': [c.__name__ for c in getattr(cls, 'permission_classes', [])],
            # Khai TRỰC TIẾP trên lớp này, hay thừa hưởng từ lớp cha / mặc định?
            # Phân biệt được điều đó mới biết chỗ nào là "quên" và chỗ nào là
            # "cha đã lo" — hai thứ trông giống hệt nhau trong đầu ra.
            'khai_tay': 'permission_classes' in cls.__dict__,
            'ke_thua_tu': next(
                (b.__name__ for b in cls.__mro__[1:]
                 if 'permission_classes' in b.__dict__), None),
            'auth_rong': 'authentication_classes' in cls.__dict__
                         and not cls.__dict__['authentication_classes'],
        })
    return [r for r in ra if r['duong'].startswith('api/')]


def main():
    tat_ca = '--tat-ca' in sys.argv
    ds = quet()
    print('tổng view api/:', len(ds))

    mo = [r for r in ds if 'AllowAny' in r['quyen']]
    chi_dn = [r for r in ds if r['quyen'] == ['IsAuthenticated']]

    print()
    print('══ KHÔNG CẦN ĐĂNG NHẬP (AllowAny) ══', len(mo))
    print('   Mỗi dòng ở đây là một bề mặt công khai. Đọc từng dòng.')
    for r in sorted(mo, key=lambda x: x['duong']):
        print('  ', r['duong'].ljust(50), r['view'],
              '| authentication_classes rỗng' if r['auth_rong'] else '')

    print()
    print('══ CHỈ CẦN ĐĂNG NHẬP (mọi vai, kể cả học viên) ══', len(chi_dn))
    print('   ĐÚNG với dữ liệu của chính người dùng. SAI nếu view đọc/sửa dữ')
    print('   liệu của người khác. Cột đầu cho biết đây là khai tay hay bỏ trống.')
    for r in sorted(chi_dn, key=lambda x: x['duong']):
        nguon = ('khai tay' if r['khai_tay']
                 else ('cha:' + r['ke_thua_tu'] if r['ke_thua_tu'] else 'BỎ TRỐNG'))
        print('  ', nguon.ljust(16), r['duong'].ljust(50), r['view'])

    if tat_ca:
        print()
        print('══ TẤT CẢ, theo lớp quyền ══')
        theo = {}
        for r in ds:
            theo.setdefault(' + '.join(r['quyen']) or '(không có)', []).append(r)
        for k in sorted(theo, key=lambda x: -len(theo[x])):
            print()
            print(' ', k, '—', len(theo[k]), 'view')
            for r in sorted(theo[k], key=lambda x: x['duong']):
                print('    ', r['duong'].ljust(50), r['view'])


if __name__ == '__main__':
    main()
