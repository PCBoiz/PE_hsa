"""Đồ thị hàm tính ở MÁY CHỦ, không `eval` (15/09/2026) — xem `lessons/do_thi.py`.

Phần lớn là hàm thuần, không cần CSDL. Riêng phép kiểm cuối đọc bài thật
`hsa_quantitative` số 7 — "Hàm bậc hai & parabol", `lessons.id = 9`, chứa hai khối
`curve` duy nhất đang có — qua đúng đường đọc nội dung mà trình duyệt gọi.

Bẫy đã sập khi viết tệp này: `one_lesson` và `?lesson=` nhận `sort_order`, KHÔNG
nhận `lessons.id`. Bản đầu gọi `one_lesson(..., 9)` theo id từ câu truy vấn quét,
đọc nhầm bài "Đạo hàm & ứng dụng" và phép kiểm đỏ vì không thấy đồ thị nào.
"""
import math
import time

import pytest

from lessons.do_thi import LoiBieuThuc, gan_diem, gia_tri, loi_do_thi, phan_tich

# Hai biểu thức THẬT trong CSDL (quét 15/09/2026) — không được phép vỡ.
THAT = [
    ('x*x - 2*x - 3', lambda x: x * x - 2 * x - 3),
    ('-(x*x) + 4*x - 1', lambda x: -(x * x) + 4 * x - 1),
]


@pytest.mark.parametrize('src,dung', THAT)
def test_hai_bieu_thuc_dang_co_trong_csdl_tinh_dung(src, dung):
    cay = phan_tich(src)
    for x in (-3, -0.5, 0, 1, 2.25, 5):
        assert gia_tri(cay, x) == pytest.approx(dung(x))


@pytest.mark.parametrize('src,x,y', [
    ('x^2', 3, 9),                    # `^` là luỹ thừa, như engine cũ
    ('sqrt(x)', 16, 4),
    ('Math.sqrt(x)', 16, 4),          # engine cũ nhận cả tiền tố `Math.`
    ('PI*x', 1, math.pi),
    ('Math.PI', 0, math.pi),
    ('abs(-x)', 2, 2),
    ('pow(x, 3)', 2, 8),
    ('2e1*x', 2, 40),
    ('x % 3', 7, 1),
])
def test_cu_phap_engine_cu_van_nhan(src, x, y):
    assert gia_tri(phan_tich(src), x) == pytest.approx(y)


@pytest.mark.parametrize('src', [
    '__import__("os").system("x")',
    'x.__class__',
    'Math.constructor',               # regex cũ `Math\\.[a-z0-9]+` cho lọt
    'Math.constructor("return 1")()',
    '(lambda: 1)()',
    'open("f")',
    '[x]',
    '"x"',
    'x if x else 1',
    'x < 1',                          # regex cũ cho qua `<>=?:`; không bài nào dùng
    'True',
    'sqrt(x=1)',
    'a*x',                            # biến duy nhất là x
    'sqrt',
    '',
    'x' * 201,
])
def test_chan_moi_thu_ngoai_danh_sach(src):
    with pytest.raises(LoiBieuThuc):
        phan_tich(src)


def test_luy_thua_khong_lo_KHONG_treo_may_chu():
    """`9^9^9` với số nguyên Python là dựng một số hàng trăm triệu chữ số — treo
    tiến trình. Toán hạng là float nên nó tràn ngay thành NaN."""
    bat_dau = time.perf_counter()
    assert math.isnan(gia_tri(phan_tich('9^9^9'), 0))
    assert math.isnan(gia_tri(phan_tich('pow(x, 1e9)'), 10))
    assert time.perf_counter() - bat_dau < 0.5


@pytest.mark.parametrize('src,x', [('1/x', 0), ('sqrt(x)', -1), ('x^(1/3)', -8), ('log(x)', 0)])
def test_khong_xac_dinh_thanh_NaN_nhu_JS(src, x):
    assert math.isnan(gia_tri(phan_tich(src), x))


def _bai_co_do_thi(**visual):
    v = {'type': 'curve', 'fn': 'x*x', 'from': -1, 'to': 1}
    v.update(visual)
    return {'theory': {'full': {'cards': [{'title': 'A', 'body': 'b', 'visual': v}]}}}


def test_gan_diem_lay_mau_mac_dinh_60_khoang():
    bai = gan_diem(_bai_co_do_thi(marks=[{'at': 0.5, 'label': 'M'}, {'at': 0, 'y': 7}]))
    v = bai['theory']['full']['cards'][0]['visual']
    assert len(v['pts']) == 61
    assert v['pts'][0] == [-1.0, 1.0] and v['pts'][-1] == [1.0, 1.0]
    assert v['marks'][0]['y'] == pytest.approx(0.25)
    assert v['marks'][1]['y'] == 7, 'mốc đã ghi y thì giữ nguyên'


def test_gan_diem_bo_diem_khong_xac_dinh():
    v = gan_diem(_bai_co_do_thi(fn='1/x', points=2))['theory']['full']['cards'][0]['visual']
    assert [p[0] for p in v['pts']] == [-1.0, 1.0], 'x = 0 phải bị bỏ, như isFinite của engine cũ'


def test_gan_diem_khoi_hong_thi_ve_rong_KHONG_vo_ca_bai():
    v = gan_diem(_bai_co_do_thi(fn='__import__("os")'))['theory']['full']['cards'][0]['visual']
    assert v['pts'] == []


def test_loi_do_thi_neu_dung_duong_dan():
    assert loi_do_thi(_bai_co_do_thi()) == []
    loi = loi_do_thi(_bai_co_do_thi(fn='open("f")'))
    assert len(loi) == 1 and loi[0].startswith('bài.theory.full.cards[0].visual.fn:'), loi
    assert loi_do_thi(_bai_co_do_thi(**{'from': 2, 'to': 1}))
    assert loi_do_thi(_bai_co_do_thi(points=1000))
    assert loi_do_thi(_bai_co_do_thi(points=True))


def test_validate_lesson_chan_fn_hong_luc_GHI():
    from lessons.content import validate_lesson
    bai = {
        'id': 'x1', 'index': 1, 'title': 'Bài thử',
        'test': {'intro': 'Làm nhanh.', 'questions': [{'id': 't1', 'type': 'fill', 'question': '2+2?', 'answer': '4'}]},
        'theory': {'full': {'title': 'Lý thuyết', 'cards': [
            {'title': 'A', 'body': 'b', 'visual': {'type': 'curve', 'fn': 'x.__class__', 'from': 0, 'to': 1}}]}},
    }
    assert any('.visual.fn:' in e for e in validate_lesson(bai))
    bai['theory']['full']['cards'][0]['visual']['fn'] = 'x*x'
    assert not any('.visual' in e for e in validate_lesson(bai))


@pytest.mark.django_db
def test_duong_doc_that_gan_san_diem_cho_hai_do_thi_bai_7():
    """Đi đúng đường trình duyệt gọi: `one_lesson` → phản hồi có `pts`, không cần `fn` ở client."""
    from lessons.content import one_lesson
    data, _ = one_lesson('hsa_quantitative', 7)
    if data is None:
        pytest.skip('CSDL không có bài hsa_quantitative số 7')
    cards = data['theory']['full']['cards']
    do_thi = [c['visual'] for c in cards if isinstance(c.get('visual'), dict) and c['visual'].get('type') == 'curve']
    assert len(do_thi) == 2, do_thi
    for v in do_thi:
        assert len(v['pts']) == 61
        cay = phan_tich(v['fn'])
        # x của điểm thứ 10 tính LẠI từ from/to, không đọc từ `pts`: `pts` đã làm tròn
        # 6 chữ số, và tính y từ x đã tròn thì lệch ~2e-6 — bản đầu phép kiểm này đỏ
        # vì đúng chuyện ấy chứ không vì máy chủ tính sai.
        x = v['from'] + (v['to'] - v['from']) * 10 / 60
        assert v['pts'][10] == [round(x, 6), round(gia_tri(cay, x), 6)]
