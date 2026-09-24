"""Gộp đồ thị graphify (mức hàm/lớp) lên mức TỆP và mức APP cho pe_hsa — bỏ tệp test, migration.

Ra: bảng tệp nối nhiều nhất (fan-in từ tệp khác, fan-out, betweenness mức tệp), ma trận phụ thuộc
giữa các app backend, số dòng mã mỗi tệp.
"""
import collections
import io
import json
import os
import sys

import networkx as nx

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DO_THI = {
    'backend': os.path.join(GOC, r'backend\graphify-out\graph.json'),
    'react': os.path.join(GOC, r'frontend\src\graphify-out\graph.json'),
    'js_cu': os.path.join(GOC, r'frontend\public\static\js\graphify-out\graph.json'),
}
QUAN_HE = {'calls', 'imports', 'imports_from', 'uses', 'references', 'inherits', 'indirect_call'}


def la_test(f):
    t = f.replace('\\', '/').lower()
    ten = t.rsplit('/', 1)[-1]
    return ('/tests' in t or ten.startswith('test') or '/migrations/' in t or '/e2e/' in t
            or ten.endswith('.test.ts') or ten.endswith('.test.tsx') or '/management/commands/' in t and 'bootstrap' not in t and 'kiem_luoc_do' not in t)


def so_dong(f):
    p = os.path.join(GOC, f.replace('/', os.sep)) if not os.path.isabs(f) else f
    for goc in (p, os.path.join(GOC, 'frontend', f.replace('/', os.sep))):
        if os.path.exists(goc):
            try:
                return sum(1 for _ in io.open(goc, encoding='utf-8', errors='replace'))
            except OSError:
                return 0
    return 0


def app_cua(f):
    t = f.replace('\\', '/')
    phan = t.split('/')
    if phan[0] == 'backend' and len(phan) > 2:
        return phan[1]
    return phan[0]


ra = ['# Bản đồ mã (graphify, mức tệp) — sinh tự động, đừng sửa tay', '',
      'Sinh lại: `graphify update backend`, `graphify update frontend/src`, `graphify update frontend/public/static/js` (PowerShell; '
      'Git Bash làm graphify sập) rồi `python scripts/tong_hop_graphify.py docs/BAN_DO_MA.md`. Tệp test/migration bị bỏ.', '']
for ten, duong in DO_THI.items():
    g = json.load(io.open(duong, encoding='utf-8'))
    tep_cua = {n['id']: n.get('source_file') or '' for n in g['nodes']}
    G = nx.DiGraph()
    dem = collections.Counter()
    for n in g['nodes']:
        f = n.get('source_file') or ''
        if f and not la_test(f) and n.get('file_type') == 'code':
            dem[f] += 1
    for e in g['links']:
        if e.get('relation') not in QUAN_HE:
            continue
        a, b = tep_cua.get(e['source'], ''), tep_cua.get(e['target'], '')
        if not a or not b or a == b or la_test(a) or la_test(b):
            continue
        if G.has_edge(a, b):
            G[a][b]['w'] += 1
        else:
            G.add_edge(a, b, w=1)
    btw = nx.betweenness_centrality(G) if G.number_of_nodes() < 3000 else {}
    ra.append('## %s — %d tệp mã (bỏ test/migration), %d cạnh tệp→tệp' % (ten, G.number_of_nodes(), G.number_of_edges()))
    ra.append('')
    ra.append('| Tệp | fan-in (tệp dùng nó) | fan-out (tệp nó dùng) | betweenness | nút | dòng |')
    ra.append('|---|---|---|---|---|---|')
    xep = sorted(G.nodes, key=lambda f: (-G.in_degree(f), -btw.get(f, 0)))[:18]
    for f in xep:
        ra.append('| `%s` | %d | %d | %.3f | %d | %d |' % (f, G.in_degree(f), G.out_degree(f), btw.get(f, 0), dem.get(f, 0), so_dong(f)))
    ra.append('')
    ra.append('Betweenness cao nhất (tệp "cầu nối" giữa các cụm):')
    for f, v in sorted(btw.items(), key=lambda kv: -kv[1])[:10]:
        ra.append('- `%s` %.3f (fan-in %d, fan-out %d, %d dòng)' % (f, v, G.in_degree(f), G.out_degree(f), so_dong(f)))
    ra.append('')
    if ten == 'backend':
        M = collections.Counter()
        for a, b, d in G.edges(data=True):
            x, y = app_cua(a), app_cua(b)
            if x != y:
                M[(x, y)] += d['w']
        apps = sorted({app_cua(f) for f in G.nodes})
        ra.append('Ma trận phụ thuộc giữa app backend (dòng = app gọi, cột = app bị gọi; số cạnh hàm):')
        ra.append('')
        ra.append('| gọi \\ bị gọi | ' + ' | '.join(apps) + ' |')
        ra.append('|---' * (len(apps) + 1) + '|')
        for x in apps:
            ra.append('| **%s** | ' % x + ' | '.join(str(M.get((x, y), '')) for y in apps) + ' |')
        ra.append('')
        # Chu trình giữa app
        GA = nx.DiGraph()
        for (x, y), w in M.items():
            GA.add_edge(x, y, w=w)
        vong = [c for c in nx.simple_cycles(GA) if len(c) <= 3]
        ra.append('Vòng phụ thuộc giữa app (độ dài ≤ 3): %d' % len(vong))
        for c in vong[:15]:
            ra.append('- ' + ' → '.join(c + [c[0]]))
        ra.append('')

io.open(sys.argv[1], 'w', encoding='utf-8').write('\n'.join(ra))
print('ok')
