"""ĐỘT BIẾN HÀNG LOẠT — chạy cả loạt trong MỘT lượt, in MỘT bảng.

RULES §3: mỗi luật then chốt phải có một đột biến giết được nó. Một bộ test
không bao giờ đỏ là một bộ test chưa ai chứng minh là còn canh gì.

── VÌ SAO CÓ TỆP NÀY (26/09/2026) ─────────────────────────────────────────

Cách làm cũ: mỗi đột biến một lệnh — sao lưu, sed, chạy pytest, đọc kết quả,
phục hồi. Tám đột biến cho §72 là tám vòng như thế. Anh Sơn hỏi cách đẩy nhanh
tiến độ mà đỡ tốn token; đây là chỗ cắt được nhiều nhất mà không mất gì: cùng
bấy nhiêu phép kiểm, một lượt gọi, một bảng đọc.

Và nó sửa một chỗ nguy hiểm của cách cũ: phục hồi bằng `cp` ở câu lệnh kế tiếp.
Lệnh ấy không chạy nếu phiên đứt giữa chừng — tệp mã nằm lại ở trạng thái ĐỘT
BIẾN, và lượt test sau đó đỏ vì một lý do không ai còn nhớ. Ở đây phục hồi nằm
trong `finally` và trong cả bẫy tín hiệu.

── CÁCH DÙNG ──────────────────────────────────────────────────────────────

    python scripts/dot_bien.py backend/teaching/ban_ghi.py \\
        --test teaching/tests_ban_ghi.py \\
        --loat scripts/dot_bien/ban_ghi.json

    python scripts/dot_bien.py <tệp> --test <đường pytest> --loat <json> --xem

`--xem` chỉ in ra loạt đột biến và kiểm mỗi mẫu có khớp ĐÚNG MỘT chỗ trong tệp,
không chạy test — dùng để soạn loạt cho nhanh.

Tệp loạt là JSON, một mảng:

    [
      {"ten": "bỏ kiểm người đã rời lớp",
       "cu": "AND m.left_at IS NULL",
       "moi": "AND TRUE",
       "cho": "test_em_da_roi_lop_khong_con_ghi_duoc_gi"}
    ]

`cho` không bắt buộc: có thì bảng nói rõ ĐÚNG test ấy phải đỏ — một đột biến
làm đỏ một test chẳng liên quan là dấu hiệu mẫu thay quá rộng.
"""
from __future__ import annotations

import argparse
import atexit
import io
import json
import re
import signal
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

#: Tệp đang bị thay và nội dung gốc của nó — để phục hồi từ bất kỳ đường thoát nào.
_DANG_THAY: dict[Path, str] = {}

#: SỔ CỨU HỘ trên đĩa. `atexit` và bẫy tín hiệu chỉ cứu được những đường thoát mà
#: tiến trình còn chạy được một dòng mã nữa; chúng KHÔNG cứu được khi tiến trình
#: bị kết liễu cứng (SIGKILL, phiên làm việc đứt, máy tắt). Đo thật 26/09: phiên
#: đứt giữa loạt đột biến và `ban_ghi.py` nằm lại trên đĩa với `daMo = len(xong)`
#: — nếu không ai nhìn `git status` thì lượt test sau đỏ vì một lý do không ai
#: còn nhớ, hoặc tệ hơn: đột biến ấy đi thẳng vào một commit.
#:
#: Sổ này ghi TRƯỚC khi thay và chỉ xoá SAU khi phục hồi xong. Lượt chạy kế tiếp
#: thấy nó là biết lượt trước chết giữa chừng, và phục hồi trước khi làm gì khác.
SO_CUU_HO = GOC / '.dot_bien_cuu_ho.json'


def _ghi_so(duong: Path, goc: str) -> None:
    SO_CUU_HO.write_text(json.dumps({'tep': str(duong), 'goc': goc}, ensure_ascii=False),
                         encoding='utf-8')


def _phuc_hoi() -> None:
    for duong, goc in list(_DANG_THAY.items()):
        try:
            io.open(duong, 'w', encoding='utf-8', newline='').write(goc)
        except OSError as e:                                  # noqa: PERF203
            print('!! KHÔNG phục hồi được %s: %s' % (duong, e), file=sys.stderr)
        _DANG_THAY.pop(duong, None)
    SO_CUU_HO.unlink(missing_ok=True)


def _cuu_ho_luot_truoc() -> None:
    """Lượt trước chết giữa chừng thì trả tệp về bản gốc TRƯỚC khi làm gì khác."""
    if not SO_CUU_HO.is_file():
        return
    try:
        s = json.loads(SO_CUU_HO.read_text(encoding='utf-8'))
        duong = Path(s['tep'])
        if duong.is_file() and _doc(duong) != s['goc']:
            io.open(duong, 'w', encoding='utf-8', newline='').write(s['goc'])
            print('⟲ Lượt trước chết giữa chừng — đã trả %s về bản gốc.' % duong.name)
    except (OSError, ValueError, KeyError) as e:
        print('!! Sổ cứu hộ hỏng (%s) — kiểm `git status` bằng tay.' % e, file=sys.stderr)
    SO_CUU_HO.unlink(missing_ok=True)


atexit.register(_phuc_hoi)
for _sig in (signal.SIGINT, signal.SIGTERM):
    try:
        signal.signal(_sig, lambda *_: sys.exit(130))
    except (ValueError, OSError):
        pass


def _doc(duong: Path) -> str:
    return io.open(duong, encoding='utf-8', newline='').read()


def _chay_test(duong_test: str, chi: str | None) -> tuple[bool, str]:
    """Trả (xanh, dòng tóm tắt cuối của pytest)."""
    lenh = [str(GOC / 'backend' / '.venv' / 'Scripts' / 'python.exe'),
            '-m', 'pytest', '-q', '-p', 'no:cacheprovider', duong_test]
    if chi:
        lenh += ['-k', chi]
    r = subprocess.run(lenh, cwd=GOC / 'backend', capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    dong = [d for d in (r.stdout or '').splitlines() if d.strip()]
    tom = dong[-1] if dong else '(không có đầu ra)'
    return r.returncode == 0, tom


def _ten_test_do(duong_test: str, chi: str | None) -> set[str]:
    """Tên các test ĐỎ ở lượt vừa chạy — để biết đột biến giết ĐÚNG chỗ chưa."""
    lenh = [str(GOC / 'backend' / '.venv' / 'Scripts' / 'python.exe'),
            '-m', 'pytest', '-q', '-p', 'no:cacheprovider', duong_test, '--tb=no']
    if chi:
        lenh += ['-k', chi]
    r = subprocess.run(lenh, cwd=GOC / 'backend', capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    return set(re.findall(r'FAILED [^:]+::(\w+)', r.stdout or ''))


def main() -> int:
    ap = argparse.ArgumentParser(description='Chạy một loạt đột biến, in một bảng.')
    ap.add_argument('tep', help='tệp mã sẽ bị đột biến (đường tương đối từ gốc repo)')
    ap.add_argument('--test', required=True, help='đường pytest, tính từ backend/')
    ap.add_argument('--loat', required=True, help='tệp JSON mô tả loạt đột biến')
    ap.add_argument('--chi', help='truyền tiếp cho pytest -k')
    ap.add_argument('--xem', action='store_true', help='chỉ kiểm mẫu, không chạy test')
    a = ap.parse_args()

    _cuu_ho_luot_truoc()

    duong = (GOC / a.tep).resolve()
    if not duong.is_file():
        print('Không thấy tệp %s' % duong, file=sys.stderr)
        return 2
    loat = json.loads(io.open(GOC / a.loat, encoding='utf-8').read())
    goc = _doc(duong)

    # ── Kiểm mẫu TRƯỚC khi chạy gì: mẫu khớp 0 hoặc nhiều chỗ là mẫu sai, và
    # phát hiện muộn thì đã tốn cả loạt test. ──────────────────────────────
    hong = []
    for m in loat:
        n = goc.count(m['cu'])
        if n != 1:
            hong.append((m['ten'], n))
    if hong:
        for ten, n in hong:
            print('✗ mẫu của "%s" khớp %d chỗ (phải đúng 1)' % (ten, n))
        return 2
    print('✓ %d mẫu, mỗi mẫu khớp đúng một chỗ trong %s' % (len(loat), a.tep))
    if a.xem:
        return 0

    # Lượt này SỬA tệp mã nhiều lần rồi trả lại. Bất cứ thứ gì khác đọc tệp ấy
    # trong lúc đó — cổng pre-push, một lượt pytest khác, một agent — sẽ thấy nó
    # ở trạng thái đột biến và báo hỏng vì một lý do không có thật. Đo 26/09:
    # cổng chạy song song và bước `ruff` đỏ, mất một lượt đi tìm lỗi không tồn tại.
    print('⚠ Đang sửa %s nhiều lượt. ĐỪNG chạy cổng pre-push hay pytest khác'
          ' trên tệp này tới khi bảng in ra.' % Path(a.tep).name)
    xanh, tom = _chay_test(a.test, a.chi)
    print('nền: %s' % tom)
    if not xanh:
        print('!! Nền đang ĐỎ — sửa cho xanh rồi hãy chạy đột biến.')
        return 1

    ra = []
    for m in loat:
        _DANG_THAY[duong] = goc
        _ghi_so(duong, goc)
        io.open(duong, 'w', encoding='utf-8', newline='').write(goc.replace(m['cu'], m['moi'], 1))
        try:
            do = _ten_test_do(a.test, a.chi)
        finally:
            _phuc_hoi()
        dung_cho = (m.get('cho') in do) if m.get('cho') else None
        ra.append({'ten': m['ten'], 'giet': bool(do), 'do': sorted(do), 'dung_cho': dung_cho})

    print('\n| Đột biến | Kết quả | Test đỏ |')
    print('|---|---|---|')
    for r in ra:
        if not r['giet']:
            kq = 'LỌT ✗'
        elif r['dung_cho'] is False:
            kq = 'giết NHẦM CHỖ ✗'
        else:
            kq = 'giết ✓'
        print('| %s | %s | %s |' % (r['ten'], kq, ', '.join(r['do']) or '—'))

    lot = [r for r in ra if not r['giet'] or r['dung_cho'] is False]
    print('\n%d/%d đột biến bị giết đúng chỗ.' % (len(ra) - len(lot), len(ra)))
    if lot:
        print('Đột biến LỌT nghĩa là test yếu — siết TEST, đừng bỏ qua:')
        for r in lot:
            print('  · %s' % r['ten'])
    return 1 if lot else 0


if __name__ == '__main__':
    raise SystemExit(main())
