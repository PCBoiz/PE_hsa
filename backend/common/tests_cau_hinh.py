"""H2 (24/09/2026) — cấu hình chạy máy chủ: MỘT nguồn là `render.yaml`. KHÔNG chạm CSDL.

Tới 24/09 cấu hình nằm ba chỗ lệch nhau: `render.yaml` (Render đọc), `backend/Procfile`
(Render KHÔNG đọc; `release:` của nó chỉ `migrate`, quên `bootstrap_schema`) và
`backend/gunicorn.conf.py` (gunicorn TỰ nạp từ thư mục chạy, ghi threads 8 / timeout 30
mà dòng lệnh đè mất). Và `render.yaml` khai 17 tên, thiếu 15 tên production đọc — trong đó
`PROXY_SHARED_SECRET`, `EMAIL_APP_PASSWORD`, `REDIS_URL` (đo 24/09 bằng chính bộ quét dưới:
backend đọc 43 tên, 13 là chỉ-dev / nền tảng tự đặt). Dựng lại dịch vụ từ Blueprint là mất
chúng trong im lặng (mã có mặc định nên không gì báo lỗi, chỉ tính năng tắt).

Luật: mọi tên biến môi trường mà mã backend ĐỌC phải có trong `render.yaml`, hoặc trong
một danh sách dưới đây kèm LÝ DO. Thêm một `os.environ.get('X')` mới là phải chọn một bên.
"""
import ast
import re
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent          # backend/
REPO = GOC.parent
RENDER = REPO / 'render.yaml'

#: Biến CHỈ máy dev / bộ kiểm dùng — production không được đặt.
CHI_DEV = {
    'PE_DB_HOST_PRODUCTION': 'hàng rào CSDL production của máy dev (common/hang_rao_csdl.py)',
    'CHO_PHEP_PRODUCTION': 'lối thoát cố ý của hàng rào ấy; production không qua hàng rào',
    'EMAIL_CHE_DO_THU': 'ghi .eml ra đĩa thay vì gửi — đĩa Render mất sau mỗi deploy',
    'EMAIL_THU_MUC_THU': 'thư mục .eml của chế độ thử ở trên',
    'ZALO_CHE_DO_THU': 'đi trọn luồng ZNS mà không gọi Zalo — để soát nội dung ở máy dev',
    'ZALO_ZNS_API': 'trỏ bộ kiểm sang máy chủ Zalo giả; production dùng địa chỉ thật mặc định',
    'ZALO_OA_API': 'như trên, cho Open API của OA',
    'FLASK_ENV': 'tên cũ thời Flask, chỉ đọc khi thiếu DJANGO_ENV (render.yaml đặt DJANGO_ENV)',
    'FLASK_DEBUG': 'tên cũ thời Flask, chỉ đọc khi thiếu DJANGO_DEBUG (render.yaml đặt DJANGO_DEBUG)',
}

#: Biến NỀN TẢNG tự đặt — khai trong render.yaml là sai (Render đặt, hoặc Django đặt).
NEN_TANG = {
    'RENDER_EXTERNAL_HOSTNAME': 'Render tự đặt tên miền .onrender.com',
    'RUN_MAIN': 'bộ tự nạp lại của runserver đặt ở tiến trình con',
    'SERVER_SOFTWARE': 'máy chủ WSGI (nếu có) đặt; chỉ để nhận ra đang chạy dưới gunicorn',
    'DJANGO_SETTINGS_MODULE': 'manage.py / wsgi.py / asgi.py tự setdefault',
}

#: Khai trong render.yaml mà mã backend KHÔNG đọc — chỉ được vì một bên khác đọc.
KHAI_CHO_BEN_KHAC = {
    'PYTHON_VERSION': 'Render đọc để chọn bản Python lúc build',
}


def _la_tep_kiem(p):
    return p.name in ('tests.py', 'conftest.py') or p.name.startswith(('test_', 'tests_'))


def _la_environ(nut):
    """`os.environ` hoặc `environ` (from os import environ)."""
    return ((isinstance(nut, ast.Attribute) and nut.attr == 'environ'
             and isinstance(nut.value, ast.Name) and nut.value.id == 'os')
            or (isinstance(nut, ast.Name) and nut.id == 'environ'))


def _hang_so_mo_dun(cay):
    ra = {}
    for n in cay.body:
        if (isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)):
            ra[n.targets[0].id] = n.value.value
    return ra


def doc_bien_moi_truong(ma, ten_tep='<ma>'):
    """[(tên biến | None, dòng)] mọi chỗ ĐỌC biến môi trường trong một đoạn mã Python.
    `None` = tên không đọc ra được (không phải chuỗi hằng) — phép kiểm coi là lỗi."""
    cay = ast.parse(ma, filename=ten_tep)
    hang = _hang_so_mo_dun(cay)

    def ten(nut):
        if isinstance(nut, ast.Constant) and isinstance(nut.value, str):
            return nut.value
        if isinstance(nut, ast.Name) and nut.id in hang:
            return hang[nut.id]
        return None

    ra = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Call) and n.args:
            f = n.func
            if ((isinstance(f, ast.Attribute) and f.attr in ('get', 'setdefault') and _la_environ(f.value))
                    or (isinstance(f, ast.Attribute) and f.attr == 'getenv'
                        and isinstance(f.value, ast.Name) and f.value.id == 'os')
                    or (isinstance(f, ast.Name) and f.id in ('getenv', 'env'))):
                ra.append((ten(n.args[0]), n.lineno))
        elif (isinstance(n, ast.Subscript) and _la_environ(n.value)
              and isinstance(n.ctx, ast.Load)):
            ra.append((ten(n.slice), n.lineno))
        elif (isinstance(n, ast.Compare) and len(n.ops) == 1 and isinstance(n.ops[0], (ast.In, ast.NotIn))
              and _la_environ(n.comparators[0])):
            ra.append((ten(n.left), n.lineno))
    return ra


def bien_backend_doc():
    """{tên: [tệp:dòng, …]} trên mọi tệp .py của backend (trừ .venv, tệp kiểm, migrations)."""
    ra, khong_ro = {}, []
    for p in sorted(GOC.rglob('*.py')):
        if {'.venv', 'migrations', '__pycache__'} & set(p.parts) or _la_tep_kiem(p):
            continue
        for ten, dong in doc_bien_moi_truong(p.read_text(encoding='utf-8'), str(p)):
            noi = '%s:%d' % (p.relative_to(REPO).as_posix(), dong)
            if ten is None:
                khong_ro.append(noi)
            else:
                ra.setdefault(ten, []).append(noi)
    return ra, khong_ro


def khoa_render():
    return re.findall(r'^\s*-\s*key:\s*([A-Z][A-Z0-9_]*)\s*$', RENDER.read_text(encoding='utf-8'), re.M)


def _lenh(khoa):
    """Giá trị gấp dòng (`>-`) của buildCommand / startCommand, nối thành một dòng."""
    m = re.search(r'^\s*%s:\s*>-\s*\n((?:[ \t]{6,}.*\n?)+)' % khoa, RENDER.read_text(encoding='utf-8'),
                  re.M)
    assert m, 'render.yaml không còn %s dạng `>-`' % khoa
    return ' '.join(d.strip() for d in m.group(1).splitlines())


# ── Bộ quét tự kiểm (một cái thước báo 0 lần đầu chưa chứng minh gì) ─────────

def test_bo_quet_bat_du_moi_dang_doc():
    ma = (
        'import os\nfrom os import environ, getenv\n'
        "BIEN = 'G_HANG'\n"
        "a = os.environ.get('G_GET')\n"
        "b = os.getenv('G_OSGETENV', 'x')\n"
        "c = os.environ['G_SUB']\n"
        "d = 'G_IN' in os.environ\n"
        "e = environ.get('G_ENV_TRAN')\n"
        "f = getenv('G_GETENV_TRAN')\n"
        "g = os.environ.get(BIEN)\n"
        "h = env('G_DJANGO_ENVIRON')\n"
        "os.environ.setdefault('G_SETDEFAULT', 'v')\n"
        "k = os.environ.get(ten_dong)\n"
        "os.environ['KHONG_DEM'] = 'ghi, không đọc'\n"
    )
    ra = doc_bien_moi_truong(ma)
    assert sorted(t for t, _ in ra if t) == sorted([
        'G_GET', 'G_OSGETENV', 'G_SUB', 'G_IN', 'G_ENV_TRAN', 'G_GETENV_TRAN', 'G_HANG',
        'G_DJANGO_ENVIRON', 'G_SETDEFAULT'])
    assert [d for t, d in ra if t is None] == [13], 'tên động phải báo là không đọc ra được'


def test_bo_quet_thay_bien_that_cua_backend():
    """Ghim vài tên chắc chắn có — bộ quét hỏng mà trả rỗng thì luật dưới xanh oan."""
    doc, _ = bien_backend_doc()
    for ten in ('DATABASE_URL', 'SECRET_KEY', 'PE_DB_HOST_PRODUCTION', 'EMAIL_APP_PASSWORD'):
        assert ten in doc, ten


# ── Luật ─────────────────────────────────────────────────────────────────────

def test_moi_bien_backend_doc_deu_khai_o_render_yaml_hoac_co_ly_do():
    doc, khong_ro = bien_backend_doc()
    assert khong_ro == [], 'tên biến môi trường không phải chuỗi hằng: %s' % khong_ro
    khai = set(khoa_render()) | set(CHI_DEV) | set(NEN_TANG)
    thieu = {ten: noi for ten, noi in doc.items() if ten not in khai}
    assert thieu == {}, (
        'Mã đọc mà render.yaml không khai — thêm `- key: X` + `sync: false` (bí mật / có mặc '
        'định), hoặc đưa vào CHI_DEV / NEN_TANG kèm lý do: %s' % thieu)


def test_render_yaml_khong_khai_bien_khong_ai_doc():
    doc, _ = bien_backend_doc()
    thua = [k for k in khoa_render() if k not in doc and k not in KHAI_CHO_BEN_KHAC]
    assert thua == [], 'render.yaml khai mà không ai đọc (biến cũ?): %s' % thua


def test_danh_sach_ngoai_le_khong_mang_ten_chet_hay_trung():
    doc, _ = bien_backend_doc()
    chet = [k for k in (*CHI_DEV, *NEN_TANG) if k not in doc]
    assert chet == [], 'ngoại lệ cho biến không còn ai đọc: %s' % chet
    trung = (set(CHI_DEV) | set(NEN_TANG)) & set(khoa_render())
    assert trung == set(), 'vừa khai ở render.yaml vừa nằm trong ngoại lệ: %s' % trung
    lap = [k for k in set(khoa_render()) if khoa_render().count(k) > 1]
    assert lap == [], 'render.yaml khai trùng: %s' % lap


def test_khong_con_nguon_cau_hinh_thu_hai():
    """`gunicorn.conf.py` trong rootDir được gunicorn nạp NGẦM (không cần `-c`); `Procfile`
    Render không đọc nhưng nền tảng khác đọc (và nó quên `bootstrap_schema`)."""
    for ten in ('gunicorn.conf.py', 'Procfile'):
        assert not (GOC / ten).exists(), (
            'backend/%s là nguồn cấu hình thứ hai — mọi thông số ở render.yaml' % ten)
    assert not re.search(r'(^|\s)(-c|--config)\s', _lenh('startCommand'))


def test_build_chay_bootstrap_schema_TRUOC_migrate():
    """Bảng SQL thô phải có trước khi `migrate` dựng bảng Django trỏ vào chúng; lệnh dựng
    hỏng thì dừng (`&&`), không deploy bản mã đi trước lược đồ."""
    build = _lenh('buildCommand')
    buoc = [b.strip() for b in build.split('&&')]
    assert 'python manage.py bootstrap_schema' in buoc, build
    assert any(b.startswith('python manage.py migrate') for b in buoc), build
    assert (buoc.index('python manage.py bootstrap_schema')
            < next(i for i, b in enumerate(buoc) if b.startswith('python manage.py migrate')))
    assert ';' not in build and '||' not in build, 'mọi bước nối bằng && — hỏng là dừng'
