"""Bộ minh hoạ soạn sẵn (`lessons/minh_hoa/`) — kiểm KHÔNG cần CSDL.

Giữ cho dữ liệu soạn tay không trôi khỏi thứ engine vẽ được: mỗi khối phải qua
`validate_lesson` (cùng cửa với đường sửa bài của quản trị viên), mọi `curve.fn`
phải phân tích được bằng `do_thi`, và mọi chỉ số thẻ ghi tay phải hợp lệ.
"""
import pytest

from lessons.content import validate_lesson
from lessons.do_thi import phan_tich
from lessons.minh_hoa import BO_MINH_HOA, THE_TOM_TAT

LOAI_ENGINE_VE_DUOC = {'bars', 'numline', 'curve', 'flow', 'table', 'pie', 'tree', 'timeline'}
SO_THE_DAY_DU, SO_THE_TOM_TAT = 4, 2      # mọi bài HSA đều 4 thẻ đầy đủ + 2 thẻ tóm tắt (đo 16/09/2026)


def _bai_gia(visual, the):
    cards = [{'title': 'T%d' % i, 'body': 'b'} for i in range(SO_THE_DAY_DU)]
    cards[the]['visual'] = visual
    return {'id': 'x', 'index': 1, 'title': 'x',
            'test': {'intro': '', 'questions': [{'id': 'q1', 'type': 'mcq', 'question': '?', 'options': ['a', 'b'], 'answer': 'a'}]},
            'theory': {'full': {'cards': cards}, 'condensed': {'cards': cards[:SO_THE_TOM_TAT]}}}


def _tat_ca():
    for khoa, bo in BO_MINH_HOA.items():
        for so, (the, visual) in bo.items():
            yield khoa, so, the, visual


@pytest.mark.parametrize('khoa,so,the,visual', list(_tat_ca()),
                         ids=lambda v: v if isinstance(v, str) else '')
def test_moi_minh_hoa_qua_validate_lesson(khoa, so, the, visual):
    assert visual['type'] in LOAI_ENGINE_VE_DUOC, (khoa, so, visual['type'])
    assert 0 <= the < SO_THE_DAY_DU, (khoa, so, the)
    assert not validate_lesson(_bai_gia(visual, the), path='%s #%s' % (khoa, so))


def test_duong_cong_phan_tich_duoc_va_co_khoang():
    n = 0
    for khoa, so, _, v in _tat_ca():
        if v['type'] != 'curve':
            continue
        n += 1
        phan_tich(v['fn'])
        assert v['from'] < v['to'], (khoa, so)
        for m in v.get('marks', []):
            assert v['from'] <= m['at'] <= v['to'], 'mốc nằm ngoài khoảng vẽ: %s #%s' % (khoa, so)
    assert n >= 3, 'bộ soạn sẵn có ít nhất ba đồ thị hàm'


def test_the_tom_tat_ghi_tay_tro_dung_bai_va_dung_chi_so():
    for (khoa, so), i in THE_TOM_TAT.items():
        assert so in BO_MINH_HOA[khoa], 'ghi tay cho bài không có trong bộ: %s #%s' % (khoa, so)
        assert 0 <= i < SO_THE_TOM_TAT, (khoa, so, i)


def test_du_67_bai_va_khong_trung_bai_da_co_minh_hoa():
    """9 bài đã có minh hoạ từ trước (đo 16/09/2026) không nằm trong bộ này —
    nạp vào là ghi đè công soạn tay của người trước."""
    da_co = {('hsa_quantitative', 1), ('hsa_quantitative', 4), ('hsa_quantitative', 7),
             ('hsa_quantitative', 20), ('hsa_science', 1), ('hsa_science', 16),
             ('hsa_science', 23), ('hsa_verbal', 1), ('hsa_verbal', 3)}
    tat_ca = {(k, s) for k, s, _, _ in _tat_ca()}
    assert len(tat_ca) == 67
    assert not (tat_ca & da_co)


def test_sao_hinh_co_san_sang_tom_tat_moi_hinh_mot_the_va_chay_lai_khong_sao_them():
    """Lượt hai của `nap_minh_hoa` (bài ngoài bộ, có hình soạn tay): mỗi hình đầy đủ
    sang một thẻ tóm tắt KHÁC nhau, và chạy lần hai không sao thêm.

    Đỏ trên bản đầu (17/09/2026): lần hai thấy thẻ đã nhận hình là "hết trống" nên
    sao cùng hình ấy sang thẻ trống còn lại — `--thu` ngay sau `--nap` báo 4 bài."""
    from lessons.management.commands.nap_minh_hoa import ghep
    v1 = {'type': 'bars', 'bars': [{'label': 'a', 'value': 1}]}
    v2 = {'type': 'flow', 'steps': [{'label': 'b'}]}
    bai = _bai_gia(v1, 0)
    bai['theory']['full']['cards'][2]['visual'] = v2
    bai['theory']['condensed']['cards'] = [{'title': 'X', 'body': ''}, {'title': 'Y', 'body': ''}]
    rows = [{'id': 1, 'course_id': 'hsa_science', 'sort_order': 99, 'content_json': bai}]

    doi, _, loi = ghep(rows, ghi=False, bo={})
    cond = bai['theory']['condensed']['cards']
    assert doi == 1 and not loi
    assert [c.get('visual', {}).get('type') for c in cond] == ['bars', 'flow'], 'hai hình → hai thẻ khác nhau'

    doi2, bao_cao, loi2 = ghep(rows, ghi=False, bo={})
    assert doi2 == 0 and not loi2, bao_cao
    assert [c.get('visual', {}).get('type') for c in cond] == ['bars', 'flow'], 'lần hai không được đổi gì'

    # Cảnh gây lỗi THẬT: MỘT hình, HAI thẻ tóm tắt. Lần hai, thẻ đã nhận hình là
    # "hết trống", thẻ kia còn trống — bản đầu sao cùng hình sang đó. Kịch bản hai
    # hình ở trên KHÔNG bắt được (hết thẻ trống thì không có gì để sao nhầm): đột
    # biến gỡ dòng canh mà nó vẫn xanh — thước giả cho tới khi thêm đoạn này.
    bai2 = _bai_gia(v1, 0)
    bai2['theory']['condensed']['cards'] = [{'title': 'X', 'body': ''}, {'title': 'Y', 'body': ''}]
    rows2 = [{'id': 2, 'course_id': 'hsa_science', 'sort_order': 98, 'content_json': bai2}]
    ghep(rows2, ghi=False, bo={})
    doi3, _, _ = ghep(rows2, ghi=False, bo={})
    cond2 = bai2['theory']['condensed']['cards']
    assert doi3 == 0
    assert sum(1 for c in cond2 if c.get('visual')) == 1, 'hình chỉ được sao MỘT lần, không lan sang thẻ trống còn lại'


def test_chu_thich_chi_dung_the_cho_phep():
    """`caption` đổ thẳng vào innerHTML (như `body` của thẻ) — cùng luật thẻ."""
    from lessons.content import loi_html
    for khoa, so, _, v in _tat_ca():
        assert not loi_html(v.get('caption', ''), 'caption'), (khoa, so)
        # Ô bảng, nhãn thanh, nhãn bước… đi qua `esc()` của engine: thẻ HTML trong đó
        # hiện THÔ. Bản đầu có <i>/<b> ở ba ô bảng (hsa_verbal #4, #6, #15) — phép kiểm
        # này bắt được trước khi ai mở bài ra xem.
        o = list(v.get('head', [])) + [c for r in v.get('rows', []) for c in r]
        o += [b.get('label', '') for b in v.get('bars', [])] + [s.get('label', '') for s in v.get('steps', [])]
        for h in o:
            assert '<' not in str(h), 'ô đi qua esc() mà có thẻ HTML, sẽ hiện thô: %s #%s: %r' % (khoa, so, h)
