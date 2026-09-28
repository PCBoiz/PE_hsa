"""§74 trên màn "Chương trình lớp" — mục khung nào đã có bài giao, mục nào chưa.

Khung nói "buổi 3 có bài về nhà". Cho tới §74 không gì trả lời được bài ấy đã giao hay
chưa: giảng viên phải mở tab Bài tập, đọc tên từng bài rồi tự đoán bài nào ứng với mục
nào. Cửa `/api/teach/classes/<id>/chuong-trinh` nay trả `baiDaGiao` cho mỗi mục CẦN bài.

Ba chỗ dễ sai, mỗi chỗ một phép kiểm:
  · **khoá vắng mặt khác danh sách rỗng** — rỗng là "mục này cần bài mà chưa giao", vắng
    mặt là "mục này không phải loại cần bài". Màn vẽ hai thứ ấy khác nhau;
  · **hai lớp dùng CÙNG một khung** là chuyện thường (hai lớp cùng môn) — bài của lớp kia
    nối vào cùng mục ấy, và nếu quên lọc `class_id` thì lớp A hiện bài của lớp B;
  · **bài đang soạn** (`status='draft'`) học viên chưa thấy. Gọi nó là "đã giao" thì
    giảng viên tin là xong; bỏ hẳn nó đi thì họ soạn lại bài thứ hai. Nên trả kèm cờ.
"""
import pytest

from common.db import q1


def _url(lop):
    return '/api/teach/classes/%d/chuong-trinh' % lop


@pytest.fixture
def lop_co_muc_bai_tap(dung):
    """Khung một buổi, hai mục: mục 1 là bài tập, mục 2 là chủ đề."""
    k = dung.khoa()
    b = dung.ban(k, [[1, 1]])
    m_bai, m_chu_de = b['muc'][0]
    dung.loai_muc(m_bai, 'bai_tap')
    gv = dung.api('Giảng viên')
    lop = dung.lop(k, gv=gv.uid, vid=b['id'])
    return {'k': k, 'ban': b, 'gv': gv, 'lop': lop, 'm_bai': m_bai, 'm_chu_de': m_chu_de}


def _muc(r, item_id):
    for k in r.data['buoiKhung']:
        for m in k['items']:
            if m['id'] == item_id:
                return m
    raise AssertionError('không thấy mục %s trong khung màn trả về' % item_id)


def test_muc_bai_tap_noi_ro_bai_da_giao(dung, lop_co_muc_bai_tap):
    L = lop_co_muc_bai_tap
    aid = dung.bai(L['lop'], muc=L['m_bai'], ten='Bài về nhà buổi 1')
    r = L['gv'].get(_url(L['lop']))
    assert r.status_code == 200
    assert _muc(r, L['m_bai'])['baiDaGiao'] == [
        {'id': aid, 'tieuDe': 'Bài về nhà buổi 1', 'nhap': False}]


def test_muc_can_bai_ma_chua_giao_la_danh_sach_rong(lop_co_muc_bai_tap):
    m = _muc(lop_co_muc_bai_tap['gv'].get(_url(lop_co_muc_bai_tap['lop'])),
             lop_co_muc_bai_tap['m_bai'])
    assert m['baiDaGiao'] == [], 'rỗng = cần bài mà chưa giao'


def test_muc_chu_de_khong_co_khoa_bai_da_giao(lop_co_muc_bai_tap):
    m = _muc(lop_co_muc_bai_tap['gv'].get(_url(lop_co_muc_bai_tap['lop'])),
             lop_co_muc_bai_tap['m_chu_de'])
    assert 'baiDaGiao' not in m, 'mục chủ đề không cần bài — khoá phải VẮNG, không phải rỗng'


def test_bai_cua_lop_khac_dung_cung_khung_khong_lot_vao(dung, lop_co_muc_bai_tap):
    L = lop_co_muc_bai_tap
    lop_b = dung.lop(L['k'], gv=L['gv'].uid, vid=L['ban']['id'])
    dung.bai(lop_b, muc=L['m_bai'], ten='Bài của lớp B')
    cua_a = dung.bai(L['lop'], muc=L['m_bai'], ten='Bài của lớp A')
    m = _muc(L['gv'].get(_url(L['lop'])), L['m_bai'])
    assert [b['id'] for b in m['baiDaGiao']] == [cua_a]


def test_bai_dang_soan_van_hien_nhung_mang_co_nhap(dung, lop_co_muc_bai_tap):
    L = lop_co_muc_bai_tap
    dung.bai(L['lop'], muc=L['m_bai'], status='draft', ten='Đang soạn')
    m = _muc(L['gv'].get(_url(L['lop'])), L['m_bai'])
    assert [(b['tieuDe'], b['nhap']) for b in m['baiDaGiao']] == [('Đang soạn', True)]


def test_muc_kiem_tra_cung_duoc_hoi_da_giao_chua(dung, lop_co_muc_bai_tap):
    """Mục kiểm tra phải CÓ bài trong phép kiểm này, không chỉ có khoá rỗng.

    Bản đầu chỉ khẳng định `baiDaGiao == []`, và một đột biến hỏi riêng mục `bai_tap` (bỏ
    hẳn `kiem_tra` ra khỏi câu SQL) vẫn LỌT: mục bị bỏ sót cũng ra `[]` — cùng một kết quả
    vì hai lý do trái ngược. Có một bài giao thật thì hai đường mới khác nhau.
    """
    L = lop_co_muc_bai_tap
    dung.loai_muc(L['m_chu_de'], 'kiem_tra')
    aid = dung.bai(L['lop'], muc=L['m_chu_de'], ten='Kiểm tra giữa khoá')
    r = L['gv'].get(_url(L['lop']))
    assert [b['id'] for b in _muc(r, L['m_chu_de'])['baiDaGiao']] == [aid]
    # Và mục bài tập chưa giao gì thì vẫn là danh sách rỗng, không lây bài của mục kia.
    assert _muc(r, L['m_bai'])['baiDaGiao'] == []


def test_so_dau_bai_va_man_chuong_trinh_noi_cung_mot_chuyen(dung, lop_co_muc_bai_tap):
    """Hai cửa, một câu trả lời — cùng gọi `bai_theo_muc_khung`."""
    L = lop_co_muc_bai_tap
    aid = dung.bai(L['lop'], muc=L['m_bai'])
    buoi = dung.buoi(L['lop'], ngay=-1, ss=L['ban']['buoi'][0])
    so = L['gv'].get('/api/teach/sessions/%d/so-dau-bai' % buoi)
    assert so.status_code == 200
    trong_so = [m for m in so.data['mucKeHoach'] if m['itemId'] == L['m_bai']][0]
    assert [b['id'] for b in trong_so['baiDaGiao']] == [aid]
    assert q1('SELECT syllabus_item_id FROM assignments WHERE id = %s',
              (aid,))['syllabus_item_id'] == L['m_bai']
