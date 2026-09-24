"""Tầng VAI (G2) — bản dò đầu: trang Next → cổng vai của trang → menu nào hiện nó cho vai nào →
API trang gọi (ban_do: goi_api) → view → lớp quyền → vai máy chủ cho qua. Đánh dấu chỗ LỆCH:
trang cho vai R vào (hoặc menu hiện cho R) mà API trang cần lại từ chối R.

Chạy sau `node scripts/ban_do.mjs` (đọc ban_do/graph.json). Ra markdown ở argv[1] + JSON ở argv[2].
"""
import collections
import io
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(GOC, r'frontend\src\app')

VAI = {'VAI_QUAN_TRI': 'admin', 'VAI_HOC_VU': 'Quản lý học vụ', 'VAI_BIEN_TAP': 'Biên tập nội dung',
       'VAI_GIANG_VIEN': 'Giảng viên', 'VAI_TRO_GIANG': 'Trợ giảng', 'VAI_HOC_VIEN': 'Học viên'}
TAT_CA = list(VAI.values())
NGAN = {'admin': 'QT', 'Quản lý học vụ': 'HV', 'Giảng viên': 'GV', 'Trợ giảng': 'TG',
        'Biên tập nội dung': 'BT', 'Học viên': 'HS'}
# lớp quyền → vai (khớp frontend/src/lib/quyenVai.ts::VAI_CUA_LOP_QUYEN + backend/common/permissions.py)
LOP = {
    'IsAdminRole': ['admin'], 'IsCourseOwner': ['admin'],
    'IsAdminOrAcademic': ['admin', 'Quản lý học vụ'],
    'IsSeniorTeachingStaff': ['admin', 'Quản lý học vụ', 'Giảng viên'],
    'IsTeachingStaff': ['admin', 'Quản lý học vụ', 'Giảng viên', 'Trợ giảng'],
    'IsContentEditor': ['admin', 'Biên tập nội dung'],
    '(mặc định: IsAuthenticated)': TAT_CA, 'AllowAny': TAT_CA + ['(khách)'],
}


def doc(p):
    return io.open(p, encoding='utf-8', errors='replace').read()


def ds_vai(chu):
    return [VAI[t] for t in re.findall(r'VAI_[A-Z_]+', chu) if t in VAI]


# ── Trang + cổng ──────────────────────────────────────────────────────────────
trang = []
for goc, _, tep in os.walk(APP):
    if 'page.tsx' in tep:
        rel = os.path.relpath(goc, APP).replace('\\', '/')
        tuyen = '/' + '/'.join(p for p in rel.split('/') if p != '.' and not p.startswith('('))
        trang.append((tuyen.rstrip('/') or '/', goc))

VAO_KHU = ds_vai(re.search(r'VAI_VAO_KHU[^=]*=\s*\[([^\]]*)\]', doc(os.path.join(APP, r'(standalone)\quan-tri\vai.ts'))).group(1))


def cong(goc):
    """Cổng vai gần nhất: page.tsx rồi layout.tsx từ thư mục trang đi lên."""
    d = goc
    while d.startswith(APP):
        for ten in ('page.tsx', 'layout.tsx'):
            p = os.path.join(d, ten)
            if not os.path.exists(p) or (ten == 'page.tsx' and d != goc):
                continue
            s = doc(p)
            m = re.search(r'duocVao\([^,]+,\s*\[([^\]]*)\]', s) or re.search(r'DUOC_VAO\s*=\s*new Set\(\[([^\]]*)\]', s)
            if m:
                return ds_vai(m.group(1)), os.path.relpath(p, GOC)
            if 'duocVao(kq.vai, VAI_VAO_KHU)' in s:
                return VAO_KHU, os.path.relpath(p, GOC)
            if 'requireAuth' in s or 'layVai' in s:
                pass
        d = os.path.dirname(d)
    return None, None


# ── Menu theo vai ────────────────────────────────────────────────────────────
menu = collections.defaultdict(list)   # tuyến → [(nguồn, nhãn, vai)]
s = doc(os.path.join(APP, r'(standalone)\quan-tri\vai.ts'))
for m in re.finditer(r"href:\s*'([^']+)',\s*label:\s*'([^']+)'[^}]*vai:\s*\[([^\]]*)\]", s):
    menu[m.group(1)].append(('quan-tri/vai.ts', m.group(2), ds_vai(m.group(3))))
s = doc(os.path.join(GOC, r'frontend\src\lib\khuTheoVai.ts'))
hang = {'DAY': ds_vai('VAI_GIANG_VIEN VAI_TRO_GIANG VAI_HOC_VU VAI_QUAN_TRI')}
hang['MOI_NHAN_SU'] = hang['DAY'] + ['Biên tập nội dung']
for m in re.finditer(r"nhan:\s*'([^']+)'[^}]*?(url|tab):\s*'([^']+)'[^}]*?vai:\s*(\[[^\]]*\]|[A-Z_]+)", s, re.S):
    v = ds_vai(m.group(4)) if m.group(4).startswith('[') else hang.get(m.group(4), [])
    dich = m.group(3) if m.group(2) == 'url' else '/dashboard#' + m.group(3)
    menu[dich].append(('khuTheoVai.ts', m.group(1), v))
s = doc(os.path.join(APP, r'(standalone)\giang-day\KhungGiangDay.tsx'))
for m in re.finditer(r"doan:\s*'([^']+)',\s*nhan:\s*'([^']+)'[^}]*troGiang:\s*(true|false)", s):
    v = hang['DAY'] if m.group(3) == 'true' else [x for x in hang['DAY'] if x != 'Trợ giảng']
    menu['/giang-day/%s/[classId]' % m.group(1)].append(('KhungGiangDay.tsx', m.group(2), v))

# ── API của từng trang (ban_do) ──────────────────────────────────────────────
g = json.load(io.open(os.path.join(GOC, r'ban_do\graph.json'), encoding='utf-8'))
ra_di = collections.defaultdict(list)
for e in g['edges']:
    ra_di[e['tu']].append(e)
nut = {n['id']: n for n in g['nodes']}


def api_cua_thu_muc(goc):
    rel = os.path.relpath(goc, GOC).replace('\\', '/')
    kq = set()
    for n in g['nodes']:
        if n['loai'] != 'tep_fe':
            continue
        f = n['tep']
        # tệp nằm ngay trong thư mục trang (không đi sâu vào thư mục con có page.tsx riêng)
        if f.startswith(rel + '/') and '/' not in f[len(rel) + 1:]:
            for e in ra_di[n['id']]:
                if e['quanHe'] in ('goi_api', 'goi_api_tien_to'):
                    kq.add(e['toi'])
    return kq


def quyen_cua_tuyen(tid):
    vs = [e['toi'] for e in ra_di[tid] if e['quanHe'] == 'goi_view']
    out = []
    for v in vs:
        qs = [nut[e['toi']]['nhan'] for e in ra_di[v] if e['quanHe'] == 'can_quyen']
        out.append((nut[v]['nhan'], qs or ['(mặc định: IsAuthenticated)']))
    return out


#: Lệch ở mức NÚT đã kiểm tay — kèm lý do. Thêm dòng ở đây = khẳng định đã soi mã; ghi tệp:dòng chứng minh.
DA_GIAI_THICH = {
    ('/quan-tri/tai-khoan', 'Quản lý học vụ'):
        'nút xuất CSV / đổi vai / khoá chỉ vẽ khi máy chủ KHÔNG trả `chiHocVien` (AccountsClient.tsx `!chiHocVien`)',
}

def tinh(nhan_cong_api=True):
    """Trả (dòng, lệch, đã giải thích). `nhan_cong_api=False` = giả vờ không biết cổng `chanTu`/chuyển hướng
    — dùng để tự kiểm thước còn đỏ được (phải ra lệch > 0)."""
    dong, lech, giai_thich = [], [], []
    for tuyen, goc in sorted(trang):
        vai_cong, tep_cong = cong(goc)
        apis = sorted(api_cua_thu_muc(goc))
        can = {}
        for a in apis:
            for view, qs in quyen_cua_tuyen(a):
                cho = set(TAT_CA + ['(khách)'])
                for q in qs:
                    cho &= set(LOP.get(q, TAT_CA))
                can[(nut[a]['nhan'], view)] = (qs, cho)
        hien = [(src, nh, v) for k, lst in menu.items() for (src, nh, v) in lst if k == tuyen]
        # Trang tự dịch mã API thành màn chặn (`chanTu(status)` → `data-chan="vai"` khi 403): vai bị API
        # từ chối gặp màn "không đủ quyền" đúng nghĩa — đó là CỔNG theo mã API, không phải chỗ lệch.
        # Trang chỉ chuyển hướng: lỗi (kể cả 403) đưa về trang khu — trang khu tự báo chặn theo vai.
        nd_trang = doc(os.path.join(goc, 'page.tsx'))
        chan_theo_api = nhan_cong_api and (
            'chanTu(' in nd_trang or re.search(r"redirect\([^)]*:\s*'/giang-day'\)", nd_trang) is not None)
        vao = set(vai_cong) if vai_cong is not None else set(TAT_CA)
        for v in sorted(vao | {x for _, _, vs in hien for x in vs}):
            bi_chan = [(a, view, qs) for (a, view), (qs, cho) in can.items() if v not in cho]
            if bi_chan and v in vao and not chan_theo_api:
                if (tuyen, v) in DA_GIAI_THICH:
                    giai_thich.append((tuyen, v, DA_GIAI_THICH[(tuyen, v)]))
                else:
                    lech.append((tuyen, v, bi_chan))
        dong.append({'tuyen': tuyen, 'cong': vai_cong, 'tepCong': tep_cong, 'chanTheoApi': chan_theo_api,
                     'menu': [(src, nh, v) for src, nh, v in hien],
                     'api': [{'tuyen': a, 'view': vw, 'quyen': qs, 'cho': sorted(cho)}
                             for (a, vw), (qs, cho) in can.items()]})
    return dong, lech, giai_thich


if sys.argv[1:2] == ['--kiem']:
    # Cổng pre-push (việc S3): đỏ khi có chỗ lệch CHƯA giải thích, hoặc khi thước đã mù (tắt nhận cổng
    # theo mã API mà vẫn ra 0 lệch — tức nó không còn nhìn thấy API của trang nữa).
    _, lech, giai_thich = tinh()
    _, lech_mu, _ = tinh(nhan_cong_api=False)
    for tuyen, v, bc in lech:
        print('  ✗ %s · vai %s · %d API từ chối (vd %s)' % (tuyen, v, len(bc), bc[0][0]))
    print('tầng vai: %d trang, %d lệch chưa giải thích, %d đã giải thích; tự kiểm (tắt cổng API): %d lệch'
          % (len(trang), len(lech), len(giai_thich), len(lech_mu)))
    if not lech_mu:
        print('  ✗ thước mù: tắt nhận cổng theo mã API mà không ra lệch nào')
    sys.exit(1 if lech or not lech_mu else 0)

dong, lech, giai_thich = tinh()

L = ['# Tầng vai (G2, bản dò đầu) — trang × vai × API — sinh tự động, đừng sửa tay', '',
     'Sinh lại: `node scripts/ban_do.mjs` rồi `python scripts/tang_vai.py docs/BAN_DO_VAI.md <tệp json ra>`. Cổng pre-push: `python scripts/tang_vai.py --kiem`. Lệch ở mức NÚT phải ghi vào `DA_GIAI_THICH` kèm lý do.', '',
     'QT quản trị viên · HV học vụ · GV giảng viên · TG trợ giảng · BT biên tập · HS học viên.', '',
     '| Trang | Cổng trang (vai vào được) | Menu hiện cho | Số API | Lớp quyền API cần |', '|---|---|---|---|---|']
for d in dong:
    c = ('theo mã API (chanTu)' if d['chanTheoApi'] else 'mọi người đăng nhập / công khai') if d['cong'] is None         else ' '.join(NGAN.get(v, v) for v in d['cong'])
    mn = '; '.join('%s: %s' % (nh, ' '.join(NGAN.get(v, v) for v in vs)) for _, nh, vs in d['menu']) or '—'
    qs = sorted({q for a in d['api'] for q in a['quyen']})
    L.append('| `%s` | %s | %s | %d | %s |' % (d['tuyen'], c, mn, len(d['api']), ', '.join(qs) or '—'))
L += ['', '## Đã giải thích (lệch ở mức nút, đã soi mã)', '']
L += ['- `%s` · %s — %s' % g for g in giai_thich] or ['Không có.']
L += ['', '## Chỗ lệch: trang cho vai vào nhưng API trang gọi từ chối vai ấy', '']
if not lech:
    L.append('Không có.')
for tuyen, v, bc in lech:
    L.append('- `%s` · vai **%s** · %d API bị chặn: %s' % (tuyen, v, len(bc), '; '.join('%s → %s (%s)' % (a, vw, '+'.join(q)) for a, vw, q in bc[:4])))
io.open(sys.argv[1], 'w', encoding='utf-8').write('\n'.join(L))
io.open(sys.argv[2], 'w', encoding='utf-8').write(json.dumps({'trang': dong, 'lech': lech}, ensure_ascii=False, indent=1))
print('trang', len(dong), 'lech', len(lech))
