"""Đồ thị hàm trong bài học — máy chủ tính ĐIỂM, trình duyệt chỉ vẽ.

── VÌ SAO CÓ TỆP NÀY (15/09/2026) ─────────────────────────────────────────

`lesson_hsa.js::compileFn` biến chuỗi `fn` của khối `curve` thành hàm JS bằng
`new Function`, chỉ canh bằng một regex trên CHUỖI. Hai cái giá:

1. CSP của Vercel phải mở `'unsafe-eval'` cho MỌI trang của sản phẩm — để vẽ
   đúng hai đồ thị (quét CSDL 15/09: cả CSDL có đúng 2 khối `curve`, cùng ở
   `hsa_quantitative` bài số 7 "Hàm bậc hai & parabol", `lessons.id` 9).
2. Regex ấy khớp `Math\\.[a-z0-9]+`, tức `Math.constructor` cũng lọt. Chưa dựng
   được mã độc từ đó, nhưng một bộ lọc chuỗi đứng giữa chữ do người BIÊN TẬP gõ
   và `new Function` là thứ không nên phải ngồi chứng minh là an toàn.

Nay: `ast` phân tích `fn` theo DANH SÁCH NÚT CHO PHÉP, hàm `_tinh` tự đi cây để
ra số (không `eval`, không `compile`), và phản hồi nội dung bài mang sẵn `pts`
cùng `y` của từng mốc. Trình duyệt không còn biên dịch chuỗi nào.

Cú pháp giữ đúng thứ engine cũ nhận: số, `x`, `+ - * / %`, `^` là luỹ thừa,
ngoặc, `abs sqrt sin cos tan log exp pow` (có hoặc không tiền tố `Math.`), `PI`.
So sánh và toán tử ba ngôi mà regex cũ lỡ cho qua thì CHẶN — không bài nào dùng.
"""
import ast
import math
import operator

MAX_DAI = 200        # ký tự của một biểu thức
MAX_DIEM = 400       # số khoảng lấy mẫu tối đa
DIEM_MAC_DINH = 60   # khớp `v.points || 60` của engine cũ

_HAM = {
    'abs': abs, 'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'log': math.log, 'exp': math.exp, 'pow': math.pow,
    'floor': math.floor, 'ceil': math.ceil, 'min': min, 'max': max,
    'log10': math.log10, 'log2': math.log2,
}
_HANG = {'PI': math.pi, 'E': math.e}
_HAI_NGOI = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_MOT_NGOI = {ast.USub: operator.neg, ast.UAdd: operator.pos}
_CHO_PHEP_CHU = ('chỉ dùng số, x, + - * / % ^, dấu ngoặc và các hàm '
                 + ', '.join(sorted(_HAM)) + ' (có thể viết Math.sqrt…), hằng PI, E')


class LoiBieuThuc(ValueError):
    """Biểu thức không hợp lệ — thông điệp viết cho người soạn bài đọc."""


def _ten_ham(nut):
    """`sqrt` hoặc `Math.sqrt` → 'sqrt'; thứ khác → None."""
    if isinstance(nut, ast.Name):
        return nut.id
    if (isinstance(nut, ast.Attribute) and isinstance(nut.value, ast.Name)
            and nut.value.id == 'Math'):
        return nut.attr
    return None


def _kiem(nut, src):
    if isinstance(nut, ast.Constant):
        # `bool` là lớp con của `int` — `True` phải chặn riêng.
        if isinstance(nut.value, bool) or not isinstance(nut.value, (int, float)):
            raise LoiBieuThuc('"fn" có giá trị không phải số: %r. %s' % (nut.value, _CHO_PHEP_CHU))
        return
    if isinstance(nut, ast.Name):
        if nut.id != 'x' and nut.id not in _HANG:
            raise LoiBieuThuc('"fn" có tên lạ "%s" — biến duy nhất là x. %s' % (nut.id, _CHO_PHEP_CHU))
        return
    if isinstance(nut, ast.Attribute):
        # Chỉ `Math.PI` / `Math.E` đứng một mình; `Math.sqrt` phải nằm trong lời gọi.
        if _ten_ham(nut) not in _HANG:
            raise LoiBieuThuc('"fn" có "%s" không cho phép. %s' % (ast.unparse(nut)[:40], _CHO_PHEP_CHU))
        return
    if isinstance(nut, ast.BinOp) and type(nut.op) in _HAI_NGOI:
        _kiem(nut.left, src)
        _kiem(nut.right, src)
        return
    if isinstance(nut, ast.UnaryOp) and type(nut.op) in _MOT_NGOI:
        _kiem(nut.operand, src)
        return
    if isinstance(nut, ast.Call):
        ten = _ten_ham(nut.func)
        if ten not in _HAM or nut.keywords or not nut.args or len(nut.args) > 8:
            raise LoiBieuThuc('"fn" gọi "%s" — không cho phép. %s' % (ast.unparse(nut.func)[:40], _CHO_PHEP_CHU))
        for a in nut.args:
            _kiem(a, src)
        return
    raise LoiBieuThuc('"fn" có phần "%s" không cho phép. %s' % (ast.unparse(nut)[:40], _CHO_PHEP_CHU))


def phan_tich(src):
    """Kiểm rồi trả cây biểu thức. Ném `LoiBieuThuc` nếu không hợp lệ."""
    if not isinstance(src, str) or not src.strip():
        raise LoiBieuThuc('"fn" phải là một biểu thức theo x, ví dụ "x*x - 2*x - 3"')
    if len(src) > MAX_DAI:
        raise LoiBieuThuc('"fn" dài %d ký tự — tối đa %d' % (len(src), MAX_DAI))
    try:
        # `^` là luỹ thừa, như engine cũ (nó thay `^` bằng `**` trước khi biên dịch).
        cay = ast.parse(src.replace('^', '**'), mode='eval')
    except SyntaxError:
        raise LoiBieuThuc('"fn" không đọc được thành biểu thức: %r' % src[:60]) from None
    _kiem(cay.body, src)
    return cay.body


def _tinh(nut, x):
    if isinstance(nut, ast.Constant):
        return float(nut.value)
    if isinstance(nut, ast.Name):
        return x if nut.id == 'x' else _HANG[nut.id]
    if isinstance(nut, ast.Attribute):
        return _HANG[nut.attr]
    if isinstance(nut, ast.BinOp):
        return _HAI_NGOI[type(nut.op)](_tinh(nut.left, x), _tinh(nut.right, x))
    if isinstance(nut, ast.UnaryOp):
        return _MOT_NGOI[type(nut.op)](_tinh(nut.operand, x))
    return _HAM[_ten_ham(nut.func)](*[_tinh(a, x) for a in nut.args])


def gia_tri(cay, x):
    """y tại x; NaN khi không xác định — giống JS: chia 0, căn số âm, tràn số.

    Mọi toán hạng là `float`, nên `9^9^9` tràn thành `OverflowError` ngay chứ không
    ngồi dựng một số nguyên khổng lồ (với `int` của Python thì treo luôn máy chủ).
    """
    try:
        y = _tinh(cay, float(x))
        y = float(y)          # số phức (vd `(-8)^(1/3)`) → TypeError → NaN, như JS
    except (ArithmeticError, ValueError, TypeError):
        return math.nan
    return y if math.isfinite(y) else math.nan


def _so(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def loi_khoi(v, path):
    """Lỗi của MỘT khối `curve` (danh sách rỗng = hợp lệ)."""
    errors = []
    try:
        phan_tich(v.get('fn'))
    except LoiBieuThuc as exc:
        errors.append('%s.fn: %s' % (path, exc))
    a, b = v.get('from'), v.get('to')
    if not (_so(a) and _so(b) and a < b):
        errors.append('%s: "from" và "to" phải là số, và from < to (đang là %r, %r)' % (path, a, b))
    n = v.get('points')
    if n is not None and not (isinstance(n, int) and not isinstance(n, bool) and 2 <= n <= MAX_DIEM):
        errors.append('%s.points: phải là số nguyên từ 2 tới %d (đang là %r)' % (path, MAX_DIEM, n))
    return errors


def _duyet(o, path, gap):
    if isinstance(o, dict):
        if o.get('type') == 'curve':
            gap(o, path)
        for k, v in o.items():
            _duyet(v, '%s.%s' % (path, k), gap)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            _duyet(v, '%s[%d]' % (path, i), gap)


def loi_do_thi(obj, path='bài'):
    """Lỗi của MỌI khối `curve` trong một bài — gọi từ `validate_lesson`."""
    errors = []
    _duyet(obj, path, lambda v, p: errors.extend(loi_khoi(v, p)))
    return errors


def gan_diem(obj):
    """Gắn `pts` và `marks[].y` vào mọi khối `curve`, TẠI CHỖ. Trả lại chính nó.

    Chạy trên đường ĐỌC nội dung (cùng chỗ cắt đáp án). Khối nào không hợp lệ
    thì `pts = []` — engine vẽ rỗng, đúng như khi `compileFn` cũ trả `null`.
    Bài soạn trước khi có `loi_do_thi` có thể còn khối hỏng; đường đọc không
    được vì thế mà vỡ cả bài.
    """
    def gap(v, _path):
        v['pts'] = []
        if loi_khoi(v, 'curve'):
            return
        cay = phan_tich(v['fn'])
        a, b = float(v['from']), float(v['to'])
        n = v.get('points') or DIEM_MAC_DINH
        for i in range(n + 1):
            x = a + (b - a) * i / n
            y = gia_tri(cay, x)
            if math.isfinite(y):
                v['pts'].append([round(x, 6), round(y, 6)])
        for m in v.get('marks') or []:
            if isinstance(m, dict) and m.get('y') is None and _so(m.get('at')):
                y = gia_tri(cay, m['at'])
                m['y'] = round(y, 6) if math.isfinite(y) else None

    _duyet(obj, 'bài', gap)
    return obj
