"""SỔ NHÃN LOẠI CHUÔNG — mỗi mã `notifications.type` phải có một câu tiếng Việt.

Trang "Thông báo" (bảng TopHSA dòng 27) có bộ lọc theo loại. Bộ lọc ấy phải hiện
"Bài tập mới", không phải `assignment_new` (RULES §10), và nhãn do MÁY CHỦ trả chứ
không phải màn hình gõ lại danh mục (RULES §7).

Luật ở đây là cái thước: quét mọi lời gọi `gui(...)` / `gui_sau_commit(...)` trong
backend bằng AST, lấy đối số `loai` khi nó là chuỗi hằng, và đòi mỗi mã có nhãn. Viết
bằng AST chứ không phải danh sách chép tay, vì một danh sách chép tay chỉ đúng vào
ngày người ta chép — còn loại chuông thì thêm mỗi khi có tính năng mới, và người thêm
sẽ không nhớ tới tệp này.
"""
import ast
from pathlib import Path

import pytest

from notifications import loai as sol

GOC = Path(__file__).resolve().parent.parent
REPO = GOC.parent
BO_QUA = {'.venv', 'migrations', '__pycache__'}


#: Ba cửa sinh ra một dòng chuông. Cả ba nhận mã loại ở ĐỐI SỐ THỨ HAI, chỉ khác tên
#: tham số: `notify(user_id, ntype, …)` là cửa thấp nhất, `gui` / `gui_sau_commit` là mặt
#: tiền gọi nó cho nhiều người.
#:
#: Bản đầu của bộ quét chỉ nhìn `gui` / `gui_sau_commit` và tìm thấy ĐÚNG MỘT mã trong cả
#: backend — trong khi CSDL có tám. `test_bo_quet_thay_ma_that_cua_backend` bắt được ngay,
#: và đó là lý do một cái thước phải tự chứng minh trước khi được dùng để đo người khác.
CUA_GUI = ('notify', 'gui', 'gui_sau_commit')

#: Tên tham số mang mã loại ở mỗi cửa, khi người gọi dùng từ khoá.
TU_KHOA_LOAI = ('loai', 'ntype')


def _ma_loai_trong(nguon: str):
    """Mã loại của mọi `notify(uid, '<loai>', …)` / `gui(ids, '<loai>', …)` là chuỗi hằng."""
    try:
        cay = ast.parse(nguon)
    except SyntaxError:
        return []
    # Hằng chuỗi khai ở thân mô-đun: `thong_bao.py` viết `LOAI = 'thong_bao'` rồi truyền
    # `LOAI` vào `gui()`. Không giải hằng thì cả thông báo trung tâm — loại mà trang này
    # sinh ra để lọc — biến mất khỏi thước.
    hang = {m.targets[0].id: m.value.value
            for m in cay.body
            if isinstance(m, ast.Assign) and len(m.targets) == 1
            and isinstance(m.targets[0], ast.Name)
            and isinstance(m.value, ast.Constant) and isinstance(m.value.value, str)}
    ra = []
    for nut in ast.walk(cay):
        if not isinstance(nut, ast.Call):
            continue
        f = nut.func
        ten = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)
        if ten not in CUA_GUI:
            continue
        # Mã loại là đối số thứ HAI theo vị trí, hoặc một từ khoá trong `TU_KHOA_LOAI`.
        d = nut.args[1] if len(nut.args) >= 2 else next(
            (k.value for k in nut.keywords if k.arg in TU_KHOA_LOAI), None)
        if isinstance(d, ast.Constant) and isinstance(d.value, str):
            ra.append((d.value, nut.lineno))
        elif isinstance(d, ast.Name) and d.id in hang:
            ra.append((hang[d.id], nut.lineno))
    return ra


def _la_tep_kiem(p: Path) -> bool:
    """Tệp kiểm không tính: mã loại trong đó là mã GIẢ, không bao giờ tới người thật.

    Bắt cả `tests.py` chứ không chỉ `tests_*.py` — `notifications/tests.py` gửi
    `'system'` và bản đầu của bộ lọc coi nó là mã sản phẩm."""
    return p.name == 'conftest.py' or p.name == 'tests.py' or p.name.startswith('tests_')


def _ma_loai_backend():
    """{mã: [tệp:dòng, …]} trên mọi tệp .py của backend, TRỪ tệp kiểm."""
    ra = {}
    for p in sorted(GOC.rglob('*.py')):
        if BO_QUA & set(p.parts) or _la_tep_kiem(p):
            continue
        for ma, dong in _ma_loai_trong(p.read_text(encoding='utf-8')):
            ra.setdefault(ma, []).append('%s:%d' % (p.relative_to(REPO).as_posix(), dong))
    return ra


# ── Bộ quét tự kiểm (một cái thước báo 0 lần đầu chưa chứng minh gì) ─────────

def test_bo_quet_bat_du_moi_dang_goi():
    ma = (
        "notify(1, 'G_NOTIFY', 'a', 'b', None, None)\n"
        "gui([1], 'G_VI_TRI', 'a', 'b')\n"
        "notifications.gui(ids, 'G_QUA_MODUN', 'a', 'b')\n"
        "gui_sau_commit([1], 'G_SAU_COMMIT', 'a', 'b')\n"
        "gui(ids, loai='G_TU_KHOA', tieu_de='a', noi_dung='b')\n"
        "gui(ids, bien_dong, 'a', 'b')\n"
        "gui_khac([1], 'G_HAM_KHAC', 'a', 'b')\n"
    )
    thay = sorted(m for m, _ in _ma_loai_trong(ma))
    assert thay == ['G_NOTIFY', 'G_QUA_MODUN', 'G_SAU_COMMIT', 'G_TU_KHOA', 'G_VI_TRI'], thay


def test_bo_quet_thay_ma_that_cua_backend():
    """Ghim vài mã chắc chắn có — bộ quét hỏng mà trả rỗng thì luật dưới xanh oan."""
    doc = _ma_loai_backend()
    # Ba mã đi qua lời gọi hàm. KHÔNG ghim `thong_bao` ở đây: nó vào CSDL bằng một câu
    # INSERT, và ghim nó cho bộ quét AST là đòi cái thước đo thứ nó không đo (xem
    # `test_loai_cua_thong_bao_trung_tam_co_nhan`).
    for ma in ('assignment_new', 'lich_doi', 'yeu_cau'):
        assert ma in doc, (ma, sorted(doc))


# ── Luật ─────────────────────────────────────────────────────────────────────

def test_moi_ma_loai_backend_gui_deu_co_nhan():
    thieu = {ma: noi for ma, noi in _ma_loai_backend().items() if ma not in sol.NHAN}
    assert thieu == {}, (
        'Loại chuông không có nhãn tiếng Việt — thêm một dòng vào '
        '`notifications/loai.py::NHAN`: %s' % thieu)


def test_so_nhan_khong_giu_ma_khong_ai_gui():
    """Nhãn của một mã đã bỏ là rác: nó hiện trong bộ lọc mà không bao giờ có dòng nào."""
    doc = _ma_loai_backend()
    thua = [ma for ma in sol.NHAN if ma not in doc and ma not in sol.GUI_NOI_KHAC]
    assert thua == [], 'Nhãn cho loại không ai gửi (loại cũ?): %s' % thua


def test_moi_nhan_la_tieng_viet_cua_nguoi_dung():
    """Nhãn không được là mã kỹ thuật đội lốt (RULES §10)."""
    xau = [(ma, n) for ma, n in sol.NHAN.items()
           if not n or n == ma or '_' in n or n.islower()]
    assert xau == [], 'Nhãn phải là câu tiếng Việt người dùng đọc được: %s' % xau


@pytest.mark.parametrize('ma, cho', [
    ('assignment_new', 'Bài tập mới'),
    ('khong_he_co_ma_nay', 'Khác'),
    ('', 'Khác'),
    (None, 'Khác'),
])
def test_nhan_tra_cau_doc_duoc_ke_ca_ma_la(ma, cho):
    """Mã lạ (dữ liệu cũ, hoặc một nhánh chưa gộp) KHÔNG được làm trang trắng."""
    assert sol.nhan(ma) == cho


def test_loai_cua_thong_bao_trung_tam_co_nhan():
    """Cửa thứ tư mà bộ quét AST KHÔNG thấy, nên ghim thẳng.

    `thong_bao.gui()` ghi chuông bằng một câu `INSERT INTO notifications … %(loai)s` —
    một lượt gửi cả khối là một câu lệnh thay vì mười nghìn lời gọi `notify`. Đổi lại,
    mã loại ở đó không nằm trong lời gọi hàm nào. Không có dòng này thì `thong_bao` —
    đúng loại mà trang "Thông báo" sinh ra để hiện — là loại duy nhất không ai canh.
    """
    from notifications import thong_bao
    assert thong_bao.LOAI in sol.NHAN, thong_bao.LOAI
    assert sol.nhan(thong_bao.LOAI) != sol.KHAC
