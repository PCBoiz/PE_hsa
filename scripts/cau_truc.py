"""CẤU TRÚC — sổ miền → bản đồ mã + bản đồ dữ liệu (tự sinh) + cổng kiểm ghi chéo miền (25/09/2026).

Một nguồn: `scripts/so_mien.json` (miền → glob tệp → bảng sở hữu → ai được ghi). Tệp này đọc sổ ấy cùng
lược đồ SQL thật (`backend/sql/*.sql`, tách câu bằng CHÍNH bộ tách của `bootstrap_schema` —
`common.luoc_do_sql.doc_tat_ca`, không viết bộ tách thứ hai) và mọi tệp mã, rồi:

    python scripts/cau_truc.py            sinh docs/CAU_TRUC_DU_LIEU.md + docs/CAU_TRUC_MA.md
    python scripts/cau_truc.py --kiem     cổng (pre-push f7) — thoát 1 khi:
        · bảng trong lược đồ không miền nào sở hữu (hoặc sổ nêu bảng không có / hai miền cùng nhận);
        · tệp mã (backend .py không test, frontend .ts/.tsx trong src) không thuộc miền nào, hay hoà hai miền;
        · miền A GHI bảng của miền B mà không có trong `cho_ghi` của B và không có trong sổ NỢ;
        · mục NỢ không còn xảy ra (sổ nợ chỉ được CO — xoá mục ấy đi);
        · hai tệp docs sinh ra đã cũ (sinh lại vào bộ nhớ rồi so; số dòng tệp không tính);
        · TỰ KIỂM hỏng: thước phải đỏ được với một tệp `teaching/moi_khong_mien.py` giả và một câu
          `UPDATE classes` giả từ miền bai_tap — không đỏ = thước mù.
    python scripts/cau_truc.py --no-moi   in các vi phạm hiện có dạng mục `no_ghi_cheo` (để dán vào sổ)

"GHI" = câu SQL trong một chuỗi Python: `INSERT INTO t`, `UPDATE t`, `DELETE FROM t`, `TRUNCATE t`
(từ khoá VIẾT HOA, tên bảng viết thường, chỉ tính bảng có trong lược đồ; bỏ docstring / chuỗi đứng
riêng một dòng lệnh). Ghi qua ORM Django không thấy — mã nghiệp vụ ở đây viết SQL thuần (RULES).

Chỉ thư viện chuẩn Python, không Django, không CSDL — chạy được trên máy không có `backend/.venv`.
"""
import ast
import io
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict, defaultdict

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(GOC, 'backend'))
from common.luoc_do_sql import doc_tat_ca  # noqa: E402 — cần sys.path ở trên

SO_MIEN = os.path.join(GOC, 'scripts', 'so_mien.json')
DOC_DU_LIEU = 'docs/CAU_TRUC_DU_LIEU.md'
DOC_MA = 'docs/CAU_TRUC_MA.md'
LENH = '`python scripts/cau_truc.py`'

#: Tệp giả của tự kiểm — không miền nào được nhận nó.
GIA_TEP = 'backend/teaching/moi_khong_mien.py'
GIA_NGUON = "def f(x):\n    x('UPDATE classes SET name = %s WHERE id = %s', ('a', 1))\n"


# ── Tệp mã ────────────────────────────────────────────────────────────────────

BO_THU_MUC = {'.venv', 'venv', 'migrations', 'graphify-out', '__pycache__', 'node_modules', '.next'}


def la_test(duong):
    ten = duong.rsplit('/', 1)[-1]
    return (ten.startswith('test') or ten == 'conftest.py'
            or '/tests/' in duong or '/e2e/' in duong or re.search(r'\.test\.[jt]sx?$', ten) is not None)


def ds_tep():
    """Đường dẫn (tính từ gốc repo, dấu `/`) của mọi tệp git biết + tệp mới chưa bị .gitignore bỏ."""
    try:
        ra = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                            cwd=GOC, capture_output=True, check=True).stdout.decode('utf-8')
        tep = [t for t in ra.split('\0') if t]
    except (OSError, subprocess.CalledProcessError):
        tep = []
        for goc, ds, fs in os.walk(GOC):
            ds[:] = [d for d in ds if d not in BO_THU_MUC and not d.startswith('.')]
            tep += [os.path.relpath(os.path.join(goc, f), GOC).replace('\\', '/') for f in fs]
    return sorted({t for t in tep if os.path.isfile(os.path.join(GOC, t))})


def tep_ma(tat_ca):
    """(backend .py không test, frontend src .ts/.tsx không test, JS cũ public/static/js)."""
    def bo(t):
        return any(p in BO_THU_MUC for p in t.split('/'))
    be = [t for t in tat_ca if t.startswith('backend/') and t.endswith('.py') and not bo(t) and not la_test(t)]
    fe = [t for t in tat_ca if t.startswith('frontend/src/') and re.search(r'\.tsx?$', t)
          and not t.endswith('.d.ts') and not bo(t) and not la_test(t)]
    js = [t for t in tat_ca if t.startswith('frontend/public/static/js/') and t.endswith('.js')]
    return be, fe, js


def so_dong(t):
    with io.open(os.path.join(GOC, t), encoding='utf-8', errors='replace') as f:
        return sum(1 for _ in f)


# ── Sổ miền + glob ────────────────────────────────────────────────────────────

def glob_re(mau):
    """`*` không qua `/`, `**` qua mọi tầng; mọi ký tự khác (kể cả `[`, `(`) là chữ thường."""
    ra, i = '', 0
    while i < len(mau):
        if mau.startswith('**/', i):
            ra, i = ra + '(?:.*/)?', i + 3
        elif mau.startswith('**', i):
            ra, i = ra + '.*', i + 2
        elif mau[i] == '*':
            ra, i = ra + '[^/]*', i + 1
        else:
            ra, i = ra + re.escape(mau[i]), i + 1
    return re.compile(ra + r'\Z')


def do_cu_the(mau):
    return (0 if '*' in mau else 1, len(mau.replace('*', '')))


def doc_so():
    with io.open(SO_MIEN, encoding='utf-8') as f:
        return json.load(f, object_pairs_hook=OrderedDict)


class Mien:
    """Sổ miền đã dịch: glob → regex, bảng → chủ."""

    def __init__(self, so):
        self.so = so
        self.mien = so['mien']
        self.luat = []           # (độ cụ thể, miền, mẫu, regex)
        for m, d in self.mien.items():
            for mau in d.get('backend', []) + d.get('frontend', []):
                self.luat.append((do_cu_the(mau), m, mau, glob_re(mau)))
        self.chu = {}
        self.loi_so = []
        for m, d in self.mien.items():
            for b in d.get('bang', []):
                if b in self.chu:
                    self.loi_so.append('bảng `%s` có HAI miền nhận: %s, %s' % (b, self.chu[b], m))
                self.chu[b] = m

    def mien_cua(self, tep):
        """(miền, mẫu) hoặc (None, lý do). Mẫu cụ thể nhất thắng; hoà giữa hai miền = lỗi."""
        khop = sorted(((dct, m, mau) for dct, m, mau, r in self.luat if r.match(tep)), reverse=True)
        if not khop:
            return None, 'không khớp glob nào'
        dau = [k for k in khop if k[0] == khop[0][0]]
        if len({m for _, m, _ in dau}) > 1:
            return None, 'hoà giữa miền %s' % ', '.join('%s (%s)' % (m, mau) for _, m, mau in dau)
        return khop[0][1], khop[0][2]

    def duoc_ghi(self, mien_ghi, bang):
        """None = được ghi; chuỗi = lý do KHÔNG (để in)."""
        chu = self.chu.get(bang)
        if chu is None or chu == mien_ghi or self.mien[mien_ghi].get('ghi_moi_bang'):
            return None
        cho = [c['mien'] for c in self.mien[chu].get('cho_ghi', {}).get(bang, [])]
        return None if mien_ghi in cho else chu


# ── Lược đồ SQL ───────────────────────────────────────────────────────────────

_TU = re.compile(r"\"[^\"]*\"|[^\s(),'\"]+")
_DUNG = {'NOT', 'NULL', 'DEFAULT', 'PRIMARY', 'UNIQUE', 'REFERENCES', 'CHECK', 'CONSTRAINT',
         'GENERATED', 'COLLATE'}


def _het_chuoi(s, i):
    """Vị trí dấu `'` đóng chuỗi mở ở s[i] (`''` là nháy trong chuỗi)."""
    i += 1
    while i < len(s):
        if s[i] == "'" and s[i + 1:i + 2] == "'":
            i += 2
        elif s[i] == "'":
            return i
        else:
            i += 1
    return len(s) - 1


def khoi(s):
    """Token của một mảnh câu: từ, chuỗi '…', và mỗi cặp ngoặc (lồng nhau) giữ NGUYÊN VĂN thành một token."""
    ra, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch.isspace() or ch == ',':
            i += 1
        elif ch == "'":
            j = _het_chuoi(s, i)
            ra.append(s[i:j + 1])
            i = j + 1
        elif ch == '(':
            sau, j = 0, i
            while j < len(s):
                if s[j] == "'":
                    j = _het_chuoi(s, j)
                elif s[j] == '(':
                    sau += 1
                elif s[j] == ')':
                    sau -= 1
                    if not sau:
                        break
                j += 1
            ra.append(s[i:j + 1])
            i = j + 1
        elif ch == ')':
            i += 1
        else:
            m = _TU.match(s, i)
            ra.append(m.group())
            i = m.end()
    return ra


def tach_phay(s):
    """Tách theo dấu phẩy ở tầng ngoài (không trong ngoặc, không trong chuỗi)."""
    ra, sau, trong, cur = [], 0, False, ''
    for ch in s:
        if ch == "'":
            trong = not trong
        elif not trong and ch == '(':
            sau += 1
        elif not trong and ch == ')':
            sau -= 1
        elif not trong and ch == ',' and sau == 0:
            ra.append(cur.strip())
            cur = ''
            continue
        cur += ch
    if cur.strip():
        ra.append(cur.strip())
    return ra


def ten(t):
    return t.strip('"').split('.')[-1].lower()


def trong_ngoac(t):
    return t[1:-1].strip() if t.startswith('(') else t


def ds_cot(t):
    return [ten(c) for c in tach_phay(trong_ngoac(t))]


def gia_tri_check(bieu_thuc):
    """{cột: [giá trị]} của mọi `cột IN ('a', 'b')` (bỏ `NOT IN`)."""
    ra = {}
    for m in re.finditer(r"(\bNOT\s+)?\b(\w+)\s+IN\s*\(\s*('(?:[^']|'')*'(?:\s*,\s*'(?:[^']|'')*')*)\s*\)",
                         bieu_thuc, re.I):
        if not m.group(1):
            ra.setdefault(m.group(2).lower(), []).extend(
                v.replace("''", "'") for v in re.findall(r"'((?:[^']|'')*)'", m.group(3)))
    return ra


class Bang:
    def __init__(self, ten_bang, muc):
        self.ten, self.muc = ten_bang, muc
        self.cot = OrderedDict()     # tên → {kieu, not_null, default, muc}
        self.rb = OrderedDict()      # tên ràng buộc → {loai, cot, toi, toi_cot, on_delete, bt, muc}

    def them_rb(self, ten_rb, rb):
        self.rb[ten_rb] = rb

    def pk(self):
        return next((r['cot'] for r in self.rb.values() if r['loai'] == 'PK'), [])

    def fk(self):
        return [r for r in self.rb.values() if r['loai'] == 'FK']


def _doc_tham_chieu(tk, i):
    """`REFERENCES t (c) ON DELETE X …` bắt đầu ở tk[i] == REFERENCES → (toi, cột, on_delete, i sau)."""
    toi = ten(tk[i + 1])
    i += 2
    toi_cot = ['id']
    if i < len(tk) and tk[i].startswith('('):
        toi_cot = ds_cot(tk[i])
        i += 1
    on_delete = ''
    while i + 2 < len(tk) and tk[i].upper() == 'ON':
        su_kien, hanh = tk[i + 1].upper(), [tk[i + 2].upper()]
        i += 3
        if hanh[0] in ('SET', 'NO') and i < len(tk):
            hanh.append(tk[i].upper())
            i += 1
        if su_kien == 'DELETE':
            on_delete = ' '.join(hanh)
    return toi, toi_cot, on_delete, i


def doc_cot(b, tk, muc):
    """Định nghĩa cột (đã tách token) → thêm vào bảng b cùng ràng buộc cột."""
    c = ten(tk[0])
    i, kieu = 1, []
    while i < len(tk) and tk[i].upper() not in _DUNG:
        kieu.append(tk[i])
        i += 1
    cot = {'kieu': ''.join((' ' if k and not t.startswith('(') else '') + t for k, t in enumerate(kieu)).upper(),
           'not_null': False, 'default': None, 'muc': muc}
    ten_rb = None
    while i < len(tk):
        t = tk[i].upper()
        if t == 'CONSTRAINT':
            ten_rb, i = ten(tk[i + 1]), i + 2
            continue
        if t == 'NOT' and i + 1 < len(tk) and tk[i + 1].upper() == 'NULL':
            cot['not_null'], i = True, i + 2
        elif t == 'DEFAULT':
            j = i + 1
            while j < len(tk) and tk[j].upper() not in _DUNG:
                j += 1
            cot['default'] = ''.join((' ' if k and not x.startswith('(') else '') + x
                                     for k, x in enumerate(tk[i + 1:j]))
            i = j
        elif t == 'PRIMARY':
            b.them_rb(ten_rb or '%s_pkey' % b.ten, {'loai': 'PK', 'cot': [c], 'muc': muc})
            cot['not_null'], i = True, i + 2
        elif t == 'UNIQUE':
            b.them_rb(ten_rb or '%s_%s_key' % (b.ten, c), {'loai': 'UNIQUE', 'cot': [c], 'muc': muc})
            i += 1
        elif t == 'REFERENCES':
            toi, toi_cot, od, i = _doc_tham_chieu(tk, i)
            b.them_rb(ten_rb or '%s_%s_fkey' % (b.ten, c),
                      {'loai': 'FK', 'cot': [c], 'toi': toi, 'toi_cot': toi_cot, 'on_delete': od, 'muc': muc})
        elif t == 'CHECK':
            b.them_rb(ten_rb or '%s_%s_check' % (b.ten, c),
                      {'loai': 'CHECK', 'cot': [c], 'bt': trong_ngoac(tk[i + 1]), 'muc': muc})
            i += 2
        else:
            i += 1
            continue
        ten_rb = None
    b.cot[c] = cot


def doc_rb_bang(b, tk, ten_rb, muc):
    """Ràng buộc mức bảng: PRIMARY KEY / UNIQUE / FOREIGN KEY / CHECK (tk bắt đầu ở từ khoá)."""
    t = tk[0].upper()
    if t == 'PRIMARY':
        b.them_rb(ten_rb or '%s_pkey' % b.ten, {'loai': 'PK', 'cot': ds_cot(tk[2]), 'muc': muc})
        for c in ds_cot(tk[2]):
            if c in b.cot:
                b.cot[c]['not_null'] = True
    elif t == 'UNIQUE':
        cot = ds_cot(tk[1])
        b.them_rb(ten_rb or '%s_%s_key' % (b.ten, '_'.join(cot)), {'loai': 'UNIQUE', 'cot': cot, 'muc': muc})
    elif t == 'FOREIGN':
        cot = ds_cot(tk[2])
        toi, toi_cot, od, _ = _doc_tham_chieu(tk, 3)
        b.them_rb(ten_rb or '%s_%s_fkey' % (b.ten, '_'.join(cot)),
                  {'loai': 'FK', 'cot': cot, 'toi': toi, 'toi_cot': toi_cot, 'on_delete': od, 'muc': muc})
    elif t == 'CHECK':
        bt = trong_ngoac(tk[1])
        cot = sorted(gia_tri_check(bt)) or []
        b.them_rb(ten_rb or '%s_check' % b.ten, {'loai': 'CHECK', 'cot': cot, 'bt': bt, 'muc': muc})


_RB_BANG = {'PRIMARY', 'UNIQUE', 'FOREIGN', 'CHECK', 'EXCLUDE'}


def nhan_muc(m):
    return m.ma if m.tep == 'legacy_schema.sql' else '%s %s' % (m.tep.replace('_schema.sql', ''), m.ma)


def doc_luoc_do():
    """{tên bảng: Bang} dựng lại từ CREATE TABLE + ALTER TABLE theo đúng thứ tự tệp."""
    bang = OrderedDict()
    for m in doc_tat_ca(os.path.join(GOC, 'backend', 'sql')):
        muc = nhan_muc(m)
        for cau in m.cau:
            s = ' '.join(cau.split())
            x = re.match(r'CREATE\s+(?:UNLOGGED\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\S+?)\s*\((.*)\)\s*$', s, re.I)
            if x:
                tb = ten(x.group(1))
                if tb in bang:
                    continue
                b = bang[tb] = Bang(tb, muc)
                for phan in tach_phay(x.group(2)):
                    tk = khoi(phan)
                    if not tk:
                        continue
                    if tk[0].upper() == 'CONSTRAINT':
                        doc_rb_bang(b, tk[2:], ten(tk[1]), muc)
                    elif tk[0].upper() in _RB_BANG:
                        doc_rb_bang(b, tk, None, muc)
                    else:
                        doc_cot(b, tk, muc)
                continue
            x = re.match(r'ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?(\S+)\s+(.*)$', s, re.I)
            if not x or ten(x.group(1)) not in bang:
                continue
            b = bang[ten(x.group(1))]
            for hd in tach_phay(x.group(2)):
                _doc_hanh_dong(b, khoi(hd), muc)
    return bang


def _doc_hanh_dong(b, tk, muc):
    up = [t.upper() for t in tk]

    def bo_neu(i, *tu):
        while i < len(up) and up[i] in tu:
            i += 1
        return i

    if up[:1] == ['ADD']:
        i = 1
        if up[1:2] == ['CONSTRAINT']:
            doc_rb_bang(b, tk[3:], ten(tk[2]), muc)
        elif up[1:2] and up[1] in _RB_BANG:
            doc_rb_bang(b, tk[1:], None, muc)
        else:
            if up[1:2] == ['COLUMN']:
                i = 2
            if up[i:i + 3] == ['IF', 'NOT', 'EXISTS']:
                i += 3
            if ten(tk[i]) not in b.cot:
                doc_cot(b, tk[i:], muc)
    elif up[:1] == ['DROP']:
        if up[1:2] == ['CONSTRAINT']:
            i = bo_neu(2, 'IF', 'EXISTS')
            b.rb.pop(ten(tk[i]), None)
        else:
            i = bo_neu(1, 'COLUMN', 'IF', 'EXISTS')
            c = ten(tk[i])
            b.cot.pop(c, None)
            for k in [k for k, r in b.rb.items() if c in r['cot']]:
                del b.rb[k]
    elif up[:1] == ['ALTER']:
        i = 2 if up[1:2] == ['COLUMN'] else 1
        c = b.cot.get(ten(tk[i]))
        if c is None:
            return
        du = up[i + 1:]
        if du[:1] == ['TYPE'] or du[:3] == ['SET', 'DATA', 'TYPE']:
            j = 1 if du[:1] == ['TYPE'] else 3
            kieu = []
            for t in tk[i + 1 + j:]:
                if t.upper() in ('USING', 'COLLATE'):
                    break
                kieu.append(t)
            c['kieu'] = ''.join((' ' if k and not t.startswith('(') else '') + t for k, t in enumerate(kieu)).upper()
        elif du[:3] == ['SET', 'NOT', 'NULL']:
            c['not_null'] = True
        elif du[:3] == ['DROP', 'NOT', 'NULL']:
            c['not_null'] = False
        elif du[:2] == ['SET', 'DEFAULT']:
            c['default'] = ' '.join(tk[i + 3:])
        elif du[:2] == ['DROP', 'DEFAULT']:
            c['default'] = None


# ── Quét câu GHI trong mã Python ─────────────────────────────────────────────

_GHI = re.compile(r'(?<![\w])(INSERT\s+INTO|UPDATE|DELETE\s+FROM|TRUNCATE(?:\s+TABLE)?)\s+(?:ONLY\s+)?'
                  r'(?:"?[a-z_][a-z0-9_]*"?\.)?"?([a-z_][a-z0-9_]*)"?')


def quet_nguon(nguon, bang_biet):
    """[(dòng, loại, bảng)] mọi câu ghi trong chuỗi Python của `nguon`. Bỏ chuỗi đứng riêng làm một
    câu lệnh (docstring, chú thích bằng chuỗi) — không bao giờ được chạy như SQL."""
    cay = ast.parse(nguon)
    bo = {id(n.value) for n in ast.walk(cay) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)}
    ra = set()
    for n in ast.walk(cay):
        if not (isinstance(n, ast.Constant) and isinstance(n.value, str)) or id(n) in bo:
            continue
        for m in _GHI.finditer(n.value):
            truoc = n.value[:m.start()].rstrip().rsplit(None, 1)[-1:] or ['']
            if truoc[0].upper() in ('FOR', 'DO') or m.group(2) not in bang_biet:
                continue
            ra.add((n.lineno + n.value.count('\n', 0, m.start()), m.group(1).split()[0], m.group(2)))
    return sorted(ra)


def quet_ghi(tep_be, bang_biet):
    """{(tệp, bảng): [dòng]} + {tệp: {bảng}} từ mọi tệp backend."""
    ghi = defaultdict(list)
    for t in tep_be:
        with io.open(os.path.join(GOC, t), encoding='utf-8') as f:
            nguon = f.read()
        for dong, _loai, b in quet_nguon(nguon, bang_biet):
            ghi[(t, b)].append(dong)
    return ghi


# ── Phân tích ─────────────────────────────────────────────────────────────────

def vi_pham(mien, ghi, tep_mien):
    """{(tệp, bảng): (miền ghi, miền chủ, [dòng])} — ghi chéo không có trong cho_ghi."""
    ra = OrderedDict()
    for (t, b), dong in sorted(ghi.items()):
        mg = tep_mien.get(t)
        if mg is None:
            continue
        chu = mien.duoc_ghi(mg, b)
        if chu:
            ra[(t, b)] = (mg, chu, sorted(set(dong)))
    return ra


def phan_tich(tu_kiem=False):
    so = doc_so()
    mien = Mien(so)
    bang = doc_luoc_do()
    tat_ca = ds_tep()
    be, fe, js = tep_ma(tat_ca)
    if tu_kiem:
        be = be + [GIA_TEP]
    tep_mien, khong_mien = {}, []
    for t in be + fe + js:
        m, mau = mien.mien_cua(t)
        if m:
            tep_mien[t] = m
        elif not t.startswith('frontend/public/'):
            khong_mien.append((t, mau))
    ghi = quet_ghi([t for t in be if t != GIA_TEP], set(bang))
    if tu_kiem:
        tep_bt = next((t for t in be if tep_mien.get(t) == 'bai_tap'), None)
        for dong, _l, b in quet_nguon(GIA_NGUON, set(bang)):
            ghi[(tep_bt or '(không có tệp bai_tap)', b)].append(dong)
    return dict(so=so, mien=mien, bang=bang, be=be, fe=fe, js=js, tep_mien=tep_mien,
                khong_mien=khong_mien, ghi=ghi, vp=vi_pham(mien, ghi, tep_mien))


def loi_cau_truc(p):
    """Danh sách lỗi (chuỗi) của một lượt phân tích — trừ phần docs cũ."""
    mien, bang, so = p['mien'], p['bang'], p['so']
    loi = list(mien.loi_so)
    for b in bang:
        if b not in mien.chu:
            loi.append('bảng `%s` (%s) không miền nào sở hữu — thêm vào `bang` của một miền ở so_mien.json'
                       % (b, bang[b].muc))
    for b, m in mien.chu.items():
        if b not in bang:
            loi.append('miền %s nhận bảng `%s` mà lược đồ không có' % (m, b))
    for m, d in mien.mien.items():
        for b, ds in d.get('cho_ghi', {}).items():
            if mien.chu.get(b) != m:
                loi.append('cho_ghi của %s nêu bảng `%s` mà %s không sở hữu' % (m, b, m))
            for c in ds:
                if c.get('mien') not in mien.mien or not c.get('ly_do'):
                    loi.append('cho_ghi `%s` → %r: miền lạ hoặc thiếu lý do' % (b, c))
    for t, vi_sao in p['khong_mien']:
        loi.append('tệp `%s` không thuộc miền nào (%s) — thêm glob vào so_mien.json' % (t, vi_sao))
    no = {(n['tep'], n['bang']): n for n in so.get('no_ghi_cheo', [])}
    for (t, b), (mg, chu, dong) in p['vp'].items():
        if (t, b) not in no:
            loi.append('GHI CHÉO MỚI: `%s` (miền %s) ghi bảng `%s` của miền %s (dòng %s) — gọi hàm dịch vụ '
                       'của %s, hoặc thêm `cho_ghi` có lý do ở miền %s'
                       % (t, mg, b, chu, ', '.join(map(str, dong)), chu, chu))
    for (t, b), n in no.items():
        if not n.get('ly_do'):
            loi.append('mục nợ `%s` → `%s` thiếu lý do' % (t, b))
        if (t, b) not in p['vp']:
            loi.append('NỢ ĐÃ HẾT: `%s` không còn ghi chéo bảng `%s` — xoá mục ấy khỏi `no_ghi_cheo` '
                       '(sổ nợ chỉ được co)' % (t, b))
    return loi


# ── Sinh tài liệu ─────────────────────────────────────────────────────────────

def dau_tep(tieu_de, mo_ta):
    return ['# %s' % tieu_de, '',
            '> **Sinh tự động — đừng sửa tay.** Sinh lại: %s (sau khi sửa `scripts/so_mien.json`, lược đồ '
            '`backend/sql/*.sql` hay thêm / dời tệp). Cổng pre-push `python scripts/cau_truc.py --kiem` đỏ khi '
            'tệp này cũ.' % LENH, '', mo_ta, '']


def kieu_mermaid(k):
    return re.sub(r'\W+', '_', k.lower().replace('[]', '_arr')).strip('_') or 'x'


def rang_buoc_cot(b, c, cot):
    pk = b.pk()
    ra = []
    if c in pk:
        ra.append('PK' if len(pk) == 1 else 'PK(%s)' % ', '.join(pk))
    elif cot['not_null']:
        ra.append('NOT NULL')
    for r in b.rb.values():
        if r['loai'] == 'UNIQUE' and r['cot'] == [c]:
            ra.append('UNIQUE')
        if r['loai'] == 'FK' and c in r['cot']:
            ra.append('→ `%s.%s`%s' % (r['toi'], ', '.join(r['toi_cot']),
                                        ' (%s)' % r['on_delete'].lower() if r['on_delete'] else ''))
    if cot['default'] is not None:
        ra.append('mặc định `%s`' % cot['default'].replace('|', '\\|'))
    return ' · '.join(ra)


def sinh_du_lieu(p):
    mien, bang = p['mien'], p['bang']
    so_fk = sum(len(b.fk()) for b in bang.values())
    L = dau_tep('Cấu trúc dữ liệu theo miền',
                'Dựng từ `backend/sql/*.sql` (CREATE TABLE + ALTER TABLE, theo đúng thứ tự mục) — không cần CSDL. '
                '%d bảng, %d khoá ngoài, %d miền có bảng. Sổ miền: `scripts/so_mien.json`; luật: '
                '`docs/THIET_KE_HE_THONG.md` §4 (khoá ngoài giữa miền: GIỮ; chỉ cấm GHI chéo). § = mục lược đồ '
                'tạo ra bảng / cột.'
                % (len(bang), so_fk, len({m for m in mien.chu.values()})))
    L += ['| Miền | Bảng |', '|---|---|']
    for m, d in mien.mien.items():
        L.append('| [%s](#%s) | %s |' % (m, m.replace('_', '_'), ', '.join('`%s`' % b for b in d.get('bang', [])) or '—'))
    L.append('')
    for m, d in mien.mien.items():
        L += ['## %s' % m, '', '**%s** — %s' % (d['ten'], d['mo_ta']), '']
        ds = [b for b in d.get('bang', []) if b in bang]
        if not ds:
            L += ['Không sở hữu bảng.', '']
            continue
        khach = OrderedDict()
        quan_he = []
        for b in ds:
            for r in bang[b].fk():
                if r['toi'] not in ds:
                    khach.setdefault(r['toi'], set()).update(r['toi_cot'])
                bb = bang[b]
                mot = sorted(r['cot']) == sorted(bb.pk()) or any(
                    x['loai'] == 'UNIQUE' and x['cot'] == r['cot'] for x in bb.rb.values())
                bat_buoc = all(bb.cot.get(c, {}).get('not_null') for c in r['cot'])
                quan_he.append('    %s %s--%s %s : "%s"' % (b, '|o' if mot else '}o', '||' if bat_buoc else 'o|',
                                                          r['toi'], ', '.join(r['cot'])))
        L += ['```mermaid', 'erDiagram']
        for b in ds:
            bb = bang[b]
            fk_cot = {c for r in bb.fk() for c in r['cot']}
            L.append('    %s {' % b)
            for c, cot in bb.cot.items():
                khoa = [k for k, co in (('PK', c in bb.pk()), ('FK', c in fk_cot)) if co]
                L.append('        %s %s%s' % (kieu_mermaid(cot['kieu']), c, ' ' + ','.join(khoa) if khoa else ''))
            L.append('    }')
        for k, cot in khach.items():
            L.append('    %s {' % k)
            for c in sorted(cot):
                kieu = bang[k].cot[c]['kieu'] if k in bang and c in bang[k].cot else 'int'
                L.append('        %s %s PK' % (kieu_mermaid(kieu), c))
            L.append('    }')
        L += quan_he + ['```', '']
        if khach:
            L += ['Bảng khách (miền khác, vẽ rút gọn): %s.' % ', '.join(
                '`%s` (%s)' % (k, mien.chu.get(k, '?')) for k in khach), '']
        for b in ds:
            bb = bang[b]
            vao = sorted({'`%s.%s`' % (x.ten, ', '.join(r['cot'])) for x in bang.values() if x.ten not in ds
                          for r in x.fk() if r['toi'] == b})
            L += ['### `%s` · %s' % (b, bb.muc), '', '| Cột | Kiểu | Ràng buộc | § |', '|---|---|---|---|']
            for c, cot in bb.cot.items():
                L.append('| `%s` | %s | %s | %s |' % (c, cot['kieu'].lower(), rang_buoc_cot(bb, c, cot), cot['muc']))
            chk = [(k, r) for k, r in bb.rb.items() if r['loai'] == 'CHECK']
            if chk:
                L += ['', 'CHECK:', '']
                for k, r in chk:
                    gt = gia_tri_check(r['bt'])
                    if gt:
                        L.append('- `%s` (%s): %s' % (k, r['muc'], '; '.join(
                            '`%s` ∈ {%s}' % (c, ', '.join("'%s'" % v for v in vs)) for c, vs in gt.items())))
                    else:
                        L.append('- `%s` (%s): `%s`' % (k, r['muc'], r['bt'].replace('|', '\\|')))
            uq = [(k, r) for k, r in bb.rb.items() if r['loai'] == 'UNIQUE' and len(r['cot']) > 1]
            if uq:
                L += ['', 'UNIQUE nhiều cột: ' + '; '.join('`%s` (%s)' % (k, ', '.join(r['cot'])) for k, r in uq)]
            if vao:
                L += ['', 'Miền khác trỏ vào: ' + ', '.join(vao)]
            L.append('')
    return '\n'.join(L).rstrip('\n') + '\n'


def sinh_ma(p):
    mien, so = p['mien'], p['so']
    theo_mien = defaultdict(list)
    for t, m in p['tep_mien'].items():
        theo_mien[m].append(t)
    dong = {t: so_dong(t) for t in p['tep_mien'] if t != GIA_TEP}
    ghi_cua = defaultdict(set)
    for (t, b) in p['ghi']:
        ghi_cua[t].add(b)
    no = so.get('no_ghi_cheo', [])
    L = dau_tep('Cấu trúc mã theo miền',
                '%d miền · %d tệp backend · %d tệp frontend (src) · %d tệp JS cũ · %d mục nợ ghi chéo. Mỗi tệp thuộc '
                'đúng MỘT miền (glob cụ thể nhất trong `scripts/so_mien.json` thắng). Cột "ghi bảng" = câu '
                '`INSERT/UPDATE/DELETE/TRUNCATE` trong chuỗi SQL của tệp; *nghiêng* = ghi bảng miền khác. '
                'Số dòng đo lúc sinh, không làm cổng đỏ khi lệch.'
                % (len(mien.mien), len(p['be']), len(p['fe']), len(p['js']), len(no)))
    L += ['## Đặt mã mới ở đâu', '',
          '1. Tìm miền theo VIỆC (bảng dưới). Miền đã có thư mục riêng (`backend/chuong_trinh/`) → đặt vào đó. '
          'Miền còn nằm trong `teaching/` → tệp MỚI đặt ở `backend/<miền>/` (glob đã chờ sẵn); chỉ sửa tệp cũ '
          'tại chỗ.',
          '2. Không `INSERT/UPDATE/DELETE` bảng của miền khác — gọi hàm dịch vụ của miền ấy (vd '
          '`chuong_trinh.dich_vu`). Cần thật thì thêm `cho_ghi` ở miền CHỦ bảng, kèm lý do, trong cùng commit.',
          '3. Bảng mới: thêm vào `bang` của miền sở hữu trong `so_mien.json` cùng lúc thêm mục lược đồ.',
          '4. Tệp mới không khớp glob nào → cổng đỏ: thêm glob (hoặc đường dẫn đủ) vào miền của nó.',
          '5. Tệp cũ TRỘN (`tach_khi_cham`): tách phần của miền khác khi đang sửa chính chỗ ấy; mỗi lần tách, '
          'mục nợ tương ứng biến mất → xoá nó khỏi `no_ghi_cheo` (cổng đòi).',
          '6. Việc phụ (thông báo, nhật ký) đi SAU commit qua `notifications.gui` / `gui_sau_commit`.',
          '7. Sửa xong: %s rồi commit hai tệp docs sinh ra.' % LENH, '',
          '| Miền | Việc | Bảng | Backend | Frontend (src + JS cũ) |', '|---|---|---|---|---|']
    for m, d in mien.mien.items():
        ds = theo_mien.get(m, [])
        nb = [t for t in ds if t.startswith('backend/')]
        nf = [t for t in ds if t.startswith('frontend/')]
        L.append('| [%s](#%s) | %s | %d | %d tệp · %d dòng | %d tệp · %d dòng |' % (
            m, m, d['ten'], len(d.get('bang', [])), len(nb), sum(dong[t] for t in nb),
            len(nf), sum(dong[t] for t in nf)))
    L.append('')
    # Sổ nợ theo cặp miền
    cap = defaultdict(list)
    for n in no:
        mg = p['tep_mien'].get(n['tep'], '?')
        cap[(mg, mien.chu.get(n['bang'], '?'))].append(n)
    L += ['## Sổ nợ ghi chéo (chỉ được co)', '',
          'Vi phạm có sẵn ngày dựng sổ. Mục nào hết xảy ra thì cổng đỏ cho tới khi xoá nó; vi phạm MỚI không được '
          'thêm vào đây — dùng hàm dịch vụ, hoặc `cho_ghi` có lý do.', '']
    if not no:
        L += ['Không có.', '']
    else:
        L += ['| Miền ghi → miền chủ | Tệp | Bảng | Lý do |', '|---|---|---|---|']
        for (mg, chu), ds in sorted(cap.items()):
            for n in sorted(ds, key=lambda n: (n['tep'], n['bang'])):
                L.append('| %s → %s | `%s` | `%s` | %s |' % (mg, chu, n['tep'], n['bang'], n['ly_do']))
        L.append('')
    for m, d in mien.mien.items():
        ds = sorted(theo_mien.get(m, []))
        L += ['## %s' % m, '', '**%s** — %s' % (d['ten'], d['mo_ta']), '']
        L.append('- Bảng sở hữu: %s' % (', '.join('`%s`' % b for b in d.get('bang', [])) or 'không có'))
        duoc = []
        for b, cs in d.get('cho_ghi', {}).items():
            duoc += ['%s ghi `%s` — %s' % (c['mien'], b, c['ly_do']) for c in cs]
        duoc += ['%s (mọi bảng) — %s' % (k, v['ghi_moi_bang']) for k, v in mien.mien.items()
                 if v.get('ghi_moi_bang') and k != m and d.get('bang')]
        duoc += ['*nợ*: `%s` ghi `%s`' % (n['tep'], n['bang']) for n in no
                 if mien.chu.get(n['bang']) == m]
        if d.get('ghi_moi_bang'):
            L.append('- Được ghi MỌI bảng: %s' % d['ghi_moi_bang'])
        L.append('- Miền khác được ghi bảng của miền này: %s' % ('; '.join(duoc) if duoc else 'không'))
        L.append('- Glob: %s' % ', '.join('`%s`' % g for g in d.get('backend', []) + d.get('frontend', [])))
        for t, ly in d.get('tach_khi_cham', {}).items():
            L.append('- Tách khi chạm — `%s`: %s' % (t, ly))
        L.append('')
        nb = [t for t in ds if t.startswith('backend/')]
        if nb:
            L += ['| Tệp backend | Dòng | Ghi bảng |', '|---|---|---|']
            for t in nb:
                gb = ', '.join(('*`%s`*' if mien.chu.get(b) != m else '`%s`') % b for b in sorted(ghi_cua.get(t, ())))
                L.append('| `%s` | %d dòng | %s |' % (t, dong[t], gb or '—'))
            L.append('')
        nf = [t for t in ds if t.startswith('frontend/src/')]
        if nf:
            L += ['| Tệp frontend | Dòng |', '|---|---|']
            L += ['| `%s` | %d dòng |' % (t, dong[t]) for t in nf]
            L.append('')
        nj = [t for t in ds if t.startswith('frontend/public/')]
        if nj:
            L += ['JS cũ (chỉ co): %d tệp · %d dòng — %s' % (len(nj), sum(dong[t] for t in nj),
                                                             ', '.join('`%s`' % t.rsplit('/', 1)[-1] for t in nj)), '']
        if not ds:
            L += ['Chưa có tệp (glob chờ sẵn cho mã mới).', '']
    return '\n'.join(L).rstrip('\n') + '\n'


def an_so_dong(s):
    """So docs không tính số dòng tệp — đổi một tệp mã không được làm cổng đỏ chỉ vì số dòng."""
    return re.sub(r'\d+ dòng', 'N dòng', s)


def doc_tep(duong):
    try:
        with io.open(os.path.join(GOC, duong), encoding='utf-8') as f:
            return f.read().replace('\r\n', '\n')
    except OSError:
        return None


def ghi_tep(duong, noi_dung):
    with io.open(os.path.join(GOC, duong), 'w', encoding='utf-8', newline='\n') as f:
        f.write(noi_dung)


# ── Lệnh ──────────────────────────────────────────────────────────────────────

def tu_kiem():
    """Thước phải ĐỎ được: tệp giả không miền + câu UPDATE classes giả từ miền bai_tap. Trả [lỗi]."""
    p = phan_tich(tu_kiem=True)
    loi = loi_cau_truc(p)
    ra = []
    bat_tep = any(GIA_TEP in x for x in loi)
    bat_ghi = any(x.startswith('GHI CHÉO MỚI') and '`classes`' in x and 'miền bai_tap' in x for x in loi)
    print('tự kiểm: tệp `%s` không miền        → %s' % (GIA_TEP, 'BẮT ĐƯỢC' if bat_tep else 'BỎ SÓT'))
    print('tự kiểm: `UPDATE classes` từ miền bai_tap → %s' % ('BẮT ĐƯỢC' if bat_ghi else 'BỎ SÓT'))
    if not bat_tep:
        ra.append('thước mù: tệp giả không thuộc miền nào mà không bị báo')
    if not bat_ghi:
        ra.append('thước mù: câu ghi chéo giả (bai_tap → classes) không bị báo')
    return ra


def main(argv):
    if '--no-moi' in argv:
        p = phan_tich()
        no = {(n['tep'], n['bang']) for n in p['so'].get('no_ghi_cheo', [])}
        moi = [OrderedDict([('tep', t), ('bang', b), ('ly_do', 'có sẵn 25/09 — tách khi chạm (%s → %s)' % (mg, chu))])
               for (t, b), (mg, chu, _d) in p['vp'].items() if (t, b) not in no]
        print(json.dumps(moi, ensure_ascii=False, indent=2))
        return 0
    p = phan_tich()
    du_lieu, ma = sinh_du_lieu(p), sinh_ma(p)
    if '--kiem' not in argv:
        ghi_tep(DOC_DU_LIEU, du_lieu)
        ghi_tep(DOC_MA, ma)
        print('đã sinh %s, %s' % (DOC_DU_LIEU, DOC_MA))
    loi = loi_cau_truc(p)
    if '--kiem' in argv:
        for duong, moi in ((DOC_DU_LIEU, du_lieu), (DOC_MA, ma)):
            cu = doc_tep(duong)
            if cu is None or an_so_dong(cu) != an_so_dong(moi):
                loi.append('`%s` đã cũ so với sổ miền / lược đồ / tệp mã — chạy %s rồi commit' % (duong, LENH))
        loi += tu_kiem()
    for x in loi:
        print('  ✗ ' + x)
    print('cấu trúc: %d miền, %d bảng, %d tệp backend, %d tệp frontend, %d ghi chéo (nợ %d), %d lỗi'
          % (len(p['mien'].mien), len(p['bang']), len(p['be']), len(p['fe']), len(p['vp']),
             len(p['so'].get('no_ghi_cheo', [])), len(loi)))
    return 1 if loi else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
