"""SOI VĂN PHONG — đếm dấu vết "chữ do máy viết" trong chữ NGƯỜI DÙNG ĐỌC.

    python scripts/soi_van_phong.py              # bảng tổng, mỗi luật một số
    python scripts/soi_van_phong.py --xem <luật> # in từng câu của một luật
    python scripts/soi_van_phong.py --tran       # so với trần đã chốt, đỏ nếu tăng

── VÌ SAO CÓ TỆP NÀY (29/09/2026) ──────────────────────────────────────────

Anh Sơn 29/09: *"cách hành văn trong bản production nhìn là biết AI"*. Nhận xét ấy đúng và
đo được, nhưng không đo được bằng cách đọc lại từng màn — sản phẩm có hơn ba trăm câu, và
người viết ra chúng (tôi) là người kém nhất trong việc nhận ra giọng của chính mình.

Thứ lộ ra rõ nhất KHÔNG phải từ ngữ, mà là **NHỊP LẶP**: gần như mọi câu gợi ý đều cùng một
khuôn `<sự việc> — <hệ quả>`. Một câu như thế thì hay; hai trăm câu như thế, xếp cạnh nhau
trên mọi màn, là thứ người đọc cảm được ngay cả khi không chỉ tên được. Người viết thật thì
lúc xuống dòng, lúc dùng dấu hai chấm, lúc bỏ hẳn vế sau vì nó thừa.

── PHẠM VI: CHỈ CHỮ NGƯỜI DÙNG ĐỌC ─────────────────────────────────────────

KHÔNG soi chú thích trong mã, docstring, `PROGRESS.md`, `CLAUDE.md` hay tài liệu nội bộ.
Chúng viết cho người lập trình và cố ý dài — đó là quy ước của kho này, không phải lỗi.
Ranh giới ấy cắt bằng `ast` cho Python (docstring là nút riêng, phân biệt được chắc chắn)
và bằng phép bóc chú thích cho TSX.

── BA LUẬT, MỖI LUẬT MỘT LÝ DO ─────────────────────────────────────────────

`nhip_gach`   `— ` nối hai vế trong MỘT câu, vế sau viết thường. Đây là khuôn lặp nói trên.
              KHÔNG tính `Tên A — Tên B` (vế sau viết hoa): đó là dấu ngăn tên, bình thường.

`chu_ky_thuat` chữ của người làm phần mềm lọt lên màn của người dùng: "máy chủ", "hệ thống",
              "API", "token", "endpoint", "server", "backend". RULES §10 đã cấm mã kỹ thuật;
              mấy chữ này là cùng một lỗi ở dạng nhẹ hơn, nên không ai bắt.

`giang_giai`  câu dạy đời hoặc khuyên bảo: "càng … càng", "nên …" sau dấu gạch, "thì … sẽ".
              Phần mềm quản lý trung tâm không có việc gì phải khuyên người dùng sống thế nào.

Đếm, không tự sửa: câu nào sửa thế nào là việc của người, và sửa máy móc (thay `—` bằng `.`
ở cả ba trăm chỗ) chỉ đổi một nhịp máy này lấy một nhịp máy khác.
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
TRAN_TEP = GOC / 'scripts' / 'tran_van_phong.json'

#: Có dấu tiếng Việt thì gần như chắc là chữ cho người đọc, không phải mã.
CO_DAU = re.compile(r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữự'
                    r'ỳýỷỹỵđÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤ'
                    r'ƯỪỨỬỮỰỲÝỶỸỴĐ]')

LUAT = {
    # `— ` rồi một chữ thường: dấu gạch đang NỐI hai vế của một câu.
    'nhip_gach': re.compile(r'\S\s—\s[a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộ'
                            r'ơờớởỡợùúủũụưừứửữựỳýỷỹỵđ(]'),
    # Chữ của người làm phần mềm, KHÔNG có nghĩa gì với người dùng cuối. Luôn sai trên màn.
    'chu_ky_thuat': re.compile(r'\b(endpoint|backend|server|API|token|payload|query)\b',
                               re.IGNORECASE),
    # Phần mềm TỰ XƯNG ở ngôi thứ ba: "Hệ thống gặp lỗi", "hệ thống vừa gửi", "máy chủ bắt…".
    #
    # Siết lại 29/09 sau khi đọc kết quả lượt đầu: luật cũ bắt MỌI chữ "máy chủ", kể cả câu
    # có ích và người vẫn nói thế ("Máy chủ đang khởi động lại. Chờ khoảng một phút."). Thay
    # sạch chúng thì chính lượt siết giọng lại thành một lượt thay máy móc — đúng thứ §23 cấm.
    # Thứ thật sự hỏng hẹp hơn nhiều: phần mềm kể về bản thân nó như một nhân vật thứ ba.
    'tu_xung': re.compile(r'(^|[.!?]\s+|["“]\s*)(Hệ thống|Máy chủ)\b'
                          r'|\b(hệ thống|máy chủ)\s+(vừa|sẽ|đang|tự|bắt|không|có thể|gặp)\b'
                          r'|\btrên hệ thống\b'),
    'giang_giai': re.compile(r'càng\s+\S+\s+càng|—\s*nên\s|,\s*nên\s+\S+\s+(sớm|ngay|trước)'),
}

#: Không phải chữ người dùng đọc, dù có dấu tiếng Việt:
#:  · phép kiểm (`tests_*.py`, `tests.py`, `*.test.mjs`) — câu trong assert là cho người sửa mã;
#:  · `backend/chatbot/` — chỗ này dựng LỜI NHẮC gửi cho mô hình, người dùng không bao giờ thấy
#:    (bắt nó vào đây thì mọi lượt siết giọng lại đi sửa nhầm phần điều khiển mô hình);
#:  · `management/commands/` — chữ in ra cho người chạy lệnh, cùng loại với chú thích.
BO_QUA_TEP = ('tests_', 'test_', 'conftest', '.test.', 'scripts/',
              '/tests.py', 'backend/chatbot/', 'management/commands/',
              #  · `luoc_do_sql.py` — chữ in ra cho người chạy công cụ lược đồ, cùng loại với
              #    chú thích; người dùng sản phẩm không bao giờ đọc.
              'common/luoc_do_sql.py')


def _dung_soi(p: Path) -> bool:
    s = p.as_posix()
    if '/.venv/' in s or '/node_modules/' in s or '/.next/' in s:
        return False
    return not any(k in s for k in BO_QUA_TEP)


def chuoi_python(p: Path):
    """Mọi hằng chuỗi KHÔNG phải docstring. `ast` phân biệt được chắc chắn — đọc bằng regex
    thì một docstring nhiều dòng trông y hệt một câu hiện lên màn."""
    try:
        cay = ast.parse(p.read_text(encoding='utf-8'))
    except (SyntaxError, UnicodeDecodeError):
        return
    tai_lieu = set()
    for nut in ast.walk(cay):
        if isinstance(nut, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            d = ast.get_docstring(nut, clean=False)
            if d is not None and nut.body:
                tai_lieu.add(id(nut.body[0].value))
    for nut in ast.walk(cay):
        if isinstance(nut, ast.Constant) and isinstance(nut.value, str) and id(nut) not in tai_lieu:
            yield nut.lineno, nut.value


def _boc_chu_thich(ma: str) -> str:
    """Bỏ chú thích nhưng GIỮ NGUYÊN SỐ DÒNG.

    Bản đầu thay cả khối `/* … */` bằng một dấu cách, nên mọi số dòng sau một chú thích nhiều
    dòng đều lệch — và một thước chỉ sai chỗ thì vô dụng đúng ở việc nó sinh ra để làm (đo
    29/09: dòng báo 98 thật ra là dòng 55). Thay bằng đúng ngần ấy dấu xuống dòng.
    """
    ma = re.sub(r'/\*[\s\S]*?\*/', lambda m: '\n' * m.group(0).count('\n'), ma)
    return re.sub(r'^(\s*)//.*$', r'\1', ma, flags=re.M)


def chuoi_tsx(p: Path):
    """Chuỗi trong nháy + chữ nằm giữa hai thẻ JSX, sau khi bóc chú thích."""
    try:
        ma = _boc_chu_thich(p.read_text(encoding='utf-8'))
    except UnicodeDecodeError:
        return
    dem = 0
    for dong in ma.split('\n'):
        dem += 1
        for m in re.finditer(r"'([^'\\]{6,400})'|\"([^\"\\]{6,400})\"|`([^`\\]{6,400})`", dong):
            yield dem, next(g for g in m.groups() if g is not None)
        for m in re.finditer(r'>\s*([^<>{}\n]{8,400}?)\s*<', dong):
            yield dem, m.group(1)


def _tep_soi(loc=None):
    """Mọi tệp đáng soi, theo thứ tự ổn định. `loc` = lọc theo chuỗi trong đường dẫn."""
    ds = list(GOC.glob('backend/**/*.py'))
    for mau in ('frontend/src/**/*.tsx', 'frontend/src/**/*.ts'):
        ds += list(GOC.glob(mau))
    for p in sorted(ds):
        if _dung_soi(p) and (loc is None or loc in p.as_posix()):
            yield p


def _cau_cua(p):
    return chuoi_python(p) if p.suffix == '.py' else chuoi_tsx(p)


def _in_tat_ca(loc):
    """Đọc TOÀN BỘ chữ người dùng của một nhánh — để sửa giọng thì phải đọc liền mạch, chứ
    đọc từng câu phạm luật thì không thấy được nhịp lặp giữa các câu."""
    n = 0
    for p in _tep_soi(loc):
        cau = [(d, ' '.join(s.split())) for d, s in _cau_cua(p)
               if len(s) >= 12 and CO_DAU.search(s) and not s.lstrip().startswith('[')]
        if not cau:
            continue
        print('\n=== %s ===' % p.relative_to(GOC).as_posix())
        for d, s in cau:
            print('  %-5d %s' % (d, s[:170]))
            n += 1
    print('\n%d câu.' % n)
    return 0


def quet(loc=None):
    thay = {k: [] for k in LUAT}
    for p in _tep_soi(loc):
        if p.suffix != '.py':
            continue
        for dong, s in chuoi_python(p):
            _cham(thay, p, dong, s)
    for p in _tep_soi(loc):
        if p.suffix == '.py':
            continue
        for dong, s in chuoi_tsx(p):
            _cham(thay, p, dong, s)
    return thay


def _cham(thay, p, dong, s):
    # Dòng ghi log mở đầu bằng `[tên]` — đọc bởi người trực máy chủ, không phải người dùng.
    if len(s) < 12 or not CO_DAU.search(s) or s.lstrip().startswith('['):
        return
    # Địa chỉ URL không phải câu văn. Một `?q=Học viên` trong đường dẫn có dấu tiếng Việt
    # nên lọt qua phép lọc trên, rồi bị chấm là 'chữ kỹ thuật lọt lên màn' (29/09).
    if '://' in s or s.lstrip().startswith('/api/') or '?' in s and '=' in s and '/' in s:
        return
    for ten, re_ in LUAT.items():
        if re_.search(s):
            thay[ten].append((p.relative_to(GOC).as_posix(), dong, ' '.join(s.split())[:150]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xem', help='in từng câu của một luật')
    ap.add_argument('--tran', action='store_true', help='so với trần đã chốt')
    ap.add_argument('--tep', help='chỉ soi tệp có đường dẫn chứa chuỗi này')
    ap.add_argument('--tat-ca', action='store_true',
                    help='in MỌI câu người dùng đọc của `--tep`, không chỉ câu phạm luật')
    a = ap.parse_args()

    if a.tat_ca:
        if not a.tep:
            print('`--tat-ca` cần `--tep` — in cả sản phẩm thì không ai đọc hết.')
            return 1
        return _in_tat_ca(a.tep)

    thay = quet(a.tep)
    if a.xem:
        for tep, dong, s in thay.get(a.xem, []):
            print(f'{tep}:{dong}\n    {s}')
        print(f'\n{len(thay.get(a.xem, []))} chỗ.')
        return 0

    dem = {k: len(v) for k, v in thay.items()}
    print('VĂN PHONG — chữ người dùng đọc (không tính chú thích, docstring, tài liệu)\n')
    for k, n in sorted(dem.items(), key=lambda x: -x[1]):
        print(f'  {k:<14} {n:>4}')
    print(f'  {"TỔNG":<14} {sum(dem.values()):>4}')

    if not a.tran:
        print('\n`--xem <luật>` để đọc từng câu; `--tran` để so với trần đã chốt.')
        return 0

    if not TRAN_TEP.exists():
        TRAN_TEP.write_text(json.dumps(dem, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(f'\nChưa có trần — đã chốt trần hiện tại vào {TRAN_TEP.name}.')
        return 0
    tran = json.loads(TRAN_TEP.read_text(encoding='utf-8'))
    hong = [f'{k}: {dem[k]} > trần {tran.get(k, 0)}' for k in dem if dem[k] > tran.get(k, 0)]
    if hong:
        print('\nTĂNG so với trần — văn phong đang đi lùi:')
        for h in hong:
            print('  ✗', h)
        print('\nTrần chỉ được HẠ. Sửa câu mới, hoặc hạ trần khi đã dọn bớt.')
        return 1
    if any(dem[k] < tran.get(k, 0) for k in dem):
        print('\n✓ Dưới trần. Hạ trần bằng cách sửa `scripts/tran_van_phong.json` trong cùng commit.')
    else:
        print('\n✓ Đúng trần.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
