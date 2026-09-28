"""EM XEM LẠI ĐỦ CẢ KHOÁ — bản ghi buổi học và học liệu, không chỉ bốn dòng gần nhất.

Bảng phân rã TopHSA dòng 29 (*"danh sách record theo buổi, tìm kiếm, đã xem / chưa xem"*)
và dòng 30 (*"học liệu"*).

── ĐO TRƯỚC KHI LÀM (27/09/2026) ─────────────────────────────────────────────

Thẻ lớp của em chỉ lấy **bốn** bản ghi (`teaching/lop_cua_toi.py:44 SO_BAN_GHI = 4`) và
**bốn** tài liệu (`:48 SO_HOC_LIEU = 4`). Lớp 24 buổi thì từ buổi thứ năm trở về trước em
KHÔNG còn đường nào mở lại — không tuyến nào và không màn nào của học viên liệt kê đủ, và
không có ô tìm. Nhân sự thì có danh sách đủ (`teaching/hoc_lieu.py::danh_sach`); em thì
không. Agent soát bảng phân rã 27/09 hạ ô tóm tắt dòng 29 từ "CÓ" xuống "MỘT PHẦN" vì đúng
chỗ này (`docs/agent/BAO_CAO_PHAN_RA.md` §3.3, §3.4).

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Em xem được ĐỦ bản ghi / học liệu của cả khoá, phân trang THEO KHOÁ — không trùng
     dòng, không sót dòng, kể cả khi thứ tự `id` không trùng thứ tự thời gian (lịch sinh
     hàng loạt rồi chèn buổi bù là ra đúng cảnh ấy).
  2. Ô tìm THẬT SỰ lọc: theo chủ đề buổi và theo ngày (bản ghi), theo tên và mô tả (tài liệu).
  3. Tài liệu đang ẩn KHÔNG lọt. Giảng viên soạn trước cả khoá rồi mở dần theo tiến độ
     (§60) — lọt là em thấy đề kiểm tra trước giờ thi.
  4. Bản ghi / tài liệu của buổi BÙ chỉ tới em CÓ trong buổi ấy (§62e, `thuoc_buoi`), và
     của buổi THƯỜNG thì tới cả lớp. Hai phép kiểm chứ không một: bỏ tiền tố bảng khi gọi
     `thuoc_buoi` làm điều kiện luôn đúng với em ĐÃ có dòng `session_participants` và luôn
     sai với em CHƯA có dòng nào — chỉ phép kiểm "buổi thường tới cả lớp" bắt được nhánh sau.
  5. Em không học lớp ấy → **404**, không 403: không cửa lớp nào được lộ ra rằng lớp đó tồn tại.
  6. Em ĐÃ RỜI LỚP (`class_members.left_at`) không xem được nữa — cùng luật với §60 và §72.
  7. Lớp chưa có bản ghi / tài liệu nào thì trả danh sách RỖNG, không phải lỗi.

Đo QUA CỬA API, không đọc thẳng bảng sau một lời gọi API (tiền lệ 26/09: đọc thẳng bảng đi
bằng kết nối khác nên test xanh khi chạy riêng, đỏ khi chạy cả bộ). Chạy trên CSDL thật,
giao dịch CUỘN LẠI (`conftest.py`); email sinh ngẫu nhiên nên hai lượt song song không tranh
nhau, và mọi phép đếm chỉ đếm dữ liệu của chính mình.
"""
from datetime import timedelta
from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q1, x
from common.permissions import ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db

LINK = 'https://zoom.us/rec/share/xem-du-27-09'
TAI_LIEU = 'https://drive.google.com/file/d/xem-du-27-09/view'


def _nguoi(ten, vai=ROLE_STUDENT):
    row = q1("INSERT INTO users (name, email, password, role, streak) "
             "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             (ten, 'xemdu_%s@example.com' % uuid4().hex[:12], vai))
    return User.objects.get(id=row['id'])


def _lop(ten, gv):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status) "
              "VALUES (%s, 'hsa_quantitative', %s, 'active') RETURNING id", (ten, gv.id))['id']


def _vao(lop, u, roi=False):
    q1('INSERT INTO class_members (class_id, user_id, joined_at, left_at) '
       'VALUES (%s, %s, %s, %s) RETURNING id',
       (lop, u.id, local_now() - timedelta(days=200),
        local_now() - timedelta(days=1) if roi else None))


def _buoi(lop, cach_ngay=3, link=LINK, chu_de='Hàm số bậc hai', trang_thai='done'):
    return q1('INSERT INTO class_sessions (class_id, starts_at, duration_minutes, '
              'topic, recording_url, status) VALUES (%s, %s, 90, %s, %s, %s) RETURNING id',
              (lop, local_now() - timedelta(days=cach_ngay), chu_de, link, trang_thai))['id']


def _rieng(buoi, uids):
    """Buổi BÙ: chỉ những em này thuộc buổi (§62e `session_participants`)."""
    for u in uids:
        x('INSERT INTO session_participants (session_id, user_id) VALUES (%s, %s)', (buoi, u.id))


def _tl(lop, ten, buoi=None, an=False, mo_ta=None):
    return q1("INSERT INTO hoc_lieu (class_id, session_id, ten, mo_ta, nguon, url, an) "
              "VALUES (%s, %s, %s, %s, 'link', %s, %s) RETURNING id",
              (lop, buoi, ten, mo_ta, TAI_LIEU, an))['id']


def _the(u):
    c = APIClient()
    c.force_authenticate(user=u)
    return c


def _goi(u, lop, **tham):
    """Gọi CỬA API thật. `tham` đi vào query string đã mã hoá — không dựng SQL ở test."""
    return _the(u).get('/api/lop-cua-toi/%d/xem-du' % lop, tham)


def _ids(res, khoa='sessionId'):
    return [d[khoa] for d in res.json()['items']]


def _het_trang(u, lop, khoa='sessionId', **tham):
    """Đi hết mọi trang, trả danh sách id THEO THỨ TỰ nhận được (kể cả trùng)."""
    ra = []
    truoc = None
    for _ in range(40):                      # trần để một lỗi cursor không thành vòng vô tận
        res = _goi(u, lop, **({'truoc': truoc} if truoc else {}), **tham)
        assert res.status_code == 200, res.content
        ra += _ids(res, khoa)
        truoc = res.json()['tiep']
        if not truoc:
            return ra
    raise AssertionError('phân trang không kết thúc — cursor không tiến')


# ── 1 · Em xem được ĐỦ cả khoá, không chỉ bốn buổi gần nhất ───────────────────

def test_em_xem_du_ban_ghi_ca_khoa_chu_khong_chi_bon_buoi():
    gv = _nguoi('GV Xem Du', ROLE_TEACHER)
    em = _nguoi('Em Xem Du')
    lop = _lop('Lớp xem đủ', gv)
    _vao(lop, em)
    buoi = [_buoi(lop, cach_ngay=n) for n in range(2, 14)]      # 12 buổi có bản ghi

    res = _goi(em, lop, limit=50)
    assert res.status_code == 200
    assert set(_ids(res)) == set(buoi), 'em phải thấy ĐỦ bản ghi của cả khoá'

    the = _the(em).get('/api/lop-cua-toi')
    ds_the = [c for c in the.json()['lop'] if c['id'] == lop][0]['banGhiGanDay']
    assert len(ds_the) == 4, 'thẻ lớp vẫn giữ bốn dòng gần nhất — trang mới là chỗ xem đủ'


def test_em_xem_du_hoc_lieu_ca_khoa():
    gv = _nguoi('GV Xem Du HL', ROLE_TEACHER)
    em = _nguoi('Em Xem Du HL')
    lop = _lop('Lớp xem đủ học liệu', gv)
    _vao(lop, em)
    tl = [_tl(lop, 'Tài liệu số %d' % n) for n in range(9)]

    res = _goi(em, lop, loai='hoc-lieu', limit=50)
    assert res.status_code == 200
    assert set(_ids(res, 'id')) == set(tl), 'em phải thấy ĐỦ tài liệu của cả khoá'


# ── 2 · Phân trang theo khoá: không trùng, không sót ─────────────────────────

def test_phan_trang_ban_ghi_khong_trung_khong_sot():
    gv = _nguoi('GV Trang', ROLE_TEACHER)
    em = _nguoi('Em Trang')
    lop = _lop('Lớp phân trang', gv)
    _vao(lop, em)
    # Thứ tự `id` CỐ Ý khác thứ tự thời gian: lịch sinh hàng loạt rồi chèn buổi bù là ra
    # đúng cảnh này. Phân trang bằng `id` không thôi sẽ nhảy dòng ở đây mà không ở nơi khác.
    buoi = [_buoi(lop, cach_ngay=n) for n in (2, 11, 4, 9, 6, 13, 3, 8, 5)]

    ds = _het_trang(em, lop, limit=2)
    assert len(ds) == len(set(ds)), 'phân trang trả TRÙNG dòng: %r' % ds
    assert set(ds) == set(buoi), 'phân trang SÓT dòng: thiếu %r' % (set(buoi) - set(ds))
    assert len(ds) == 9


def test_phan_trang_hoc_lieu_khong_trung_khong_sot():
    gv = _nguoi('GV Trang HL', ROLE_TEACHER)
    em = _nguoi('Em Trang HL')
    lop = _lop('Lớp phân trang học liệu', gv)
    _vao(lop, em)
    b = [_buoi(lop, cach_ngay=n) for n in (2, 10, 5)]
    tl = ([_tl(lop, 'Kho chung %d' % n) for n in range(3)]
          + [_tl(lop, 'Của buổi %d' % i, buoi=s) for i, s in enumerate(b)])

    ds = _het_trang(em, lop, khoa='id', loai='hoc-lieu', limit=2)
    assert len(ds) == len(set(ds)), 'phân trang trả TRÙNG tài liệu: %r' % ds
    assert set(ds) == set(tl), 'phân trang SÓT tài liệu: thiếu %r' % (set(tl) - set(ds))


def test_trang_cuoi_khong_con_tiep():
    gv = _nguoi('GV Cuoi', ROLE_TEACHER)
    em = _nguoi('Em Cuoi')
    lop = _lop('Lớp trang cuối', gv)
    _vao(lop, em)
    for n in (2, 3):
        _buoi(lop, cach_ngay=n)

    res = _goi(em, lop, limit=10)
    assert res.json()['tiep'] is None, 'hết dòng thì `tiep` phải null — nút "Xem thêm" biến đi'


# ── 3 · Ô tìm thật sự lọc ───────────────────────────────────────────────────

def test_o_tim_ban_ghi_loc_theo_chu_de():
    gv = _nguoi('GV Tim', ROLE_TEACHER)
    em = _nguoi('Em Tim')
    lop = _lop('Lớp ô tìm', gv)
    _vao(lop, em)
    can = _buoi(lop, cach_ngay=4, chu_de='Xác suất thống kê')
    khong = _buoi(lop, cach_ngay=5, chu_de='Hình học không gian')

    res = _goi(em, lop, tim='xác suất')
    assert res.status_code == 200
    assert _ids(res) == [can], 'ô tìm phải lọc theo chủ đề buổi'
    assert khong not in _ids(res)


def test_o_tim_ban_ghi_loc_theo_ngay():
    gv = _nguoi('GV Tim Ngay', ROLE_TEACHER)
    em = _nguoi('Em Tim Ngay')
    lop = _lop('Lớp ô tìm ngày', gv)
    _vao(lop, em)
    can = _buoi(lop, cach_ngay=4)
    _buoi(lop, cach_ngay=40)

    res = _goi(em, lop, tim=(local_now() - timedelta(days=4)).strftime('%d/%m/%Y'))
    assert res.status_code == 200
    assert _ids(res) == [can], 'em gõ ngày buổi học vào ô tìm thì phải ra buổi ấy'


def test_o_tim_hoc_lieu_loc_theo_ten_va_mo_ta():
    gv = _nguoi('GV Tim TL', ROLE_TEACHER)
    em = _nguoi('Em Tim TL')
    lop = _lop('Lớp ô tìm tài liệu', gv)
    _vao(lop, em)
    theo_ten = _tl(lop, 'Đề ôn tập định lượng')
    theo_mo_ta = _tl(lop, 'Buổi 3', mo_ta='Bản chữa ĐỊNH LƯỢNG phần cuối')
    khong = _tl(lop, 'Hình học phẳng', mo_ta='Không liên quan')

    res = _goi(em, lop, loai='hoc-lieu', tim='định lượng')
    assert res.status_code == 200
    ra = set(_ids(res, 'id'))
    assert ra == {theo_ten, theo_mo_ta}, 'ô tìm soi cả tên lẫn mô tả, không phân biệt hoa thường'
    assert khong not in ra


def test_o_tim_dau_phan_tram_khong_tra_ve_tat_ca():
    gv = _nguoi('GV Tim Pct', ROLE_TEACHER)
    em = _nguoi('Em Tim Pct')
    lop = _lop('Lớp ô tìm phần trăm', gv)
    _vao(lop, em)
    _tl(lop, 'Đề ôn tập')

    res = _goi(em, lop, loai='hoc-lieu', tim='%')
    assert res.status_code == 200
    assert res.json()['items'] == [], 'gõ một dấu % không được trả về cả kho'


# ── 4 · Tài liệu đang ẩn không lọt ──────────────────────────────────────────

def test_tai_lieu_dang_an_khong_lot_toi_em():
    gv = _nguoi('GV An', ROLE_TEACHER)
    em = _nguoi('Em An')
    lop = _lop('Lớp tài liệu ẩn', gv)
    _vao(lop, em)
    hien = _tl(lop, 'Đề đã mở')
    an = _tl(lop, 'Đề kiểm tra tuần sau', an=True)

    res = _goi(em, lop, loai='hoc-lieu', limit=50)
    assert res.status_code == 200
    ra = _ids(res, 'id')
    assert hien in ra
    assert an not in ra, 'tài liệu giảng viên chưa mở thì em KHÔNG được thấy (§60)'


def test_tai_lieu_dang_an_khong_lot_qua_o_tim():
    gv = _nguoi('GV An Tim', ROLE_TEACHER)
    em = _nguoi('Em An Tim')
    lop = _lop('Lớp tài liệu ẩn ô tìm', gv)
    _vao(lop, em)
    an = _tl(lop, 'Đề kiểm tra tuần sau', an=True)

    res = _goi(em, lop, loai='hoc-lieu', tim='kiểm tra')
    assert res.status_code == 200
    assert an not in _ids(res, 'id'), 'ô tìm không được là cửa sau vào tài liệu đang ẩn'


# ── 5 · Buổi bù: chỉ em trong buổi ấy thấy — và buổi thường thì cả lớp ───────

def test_ban_ghi_buoi_bu_chi_em_trong_buoi_thay():
    gv = _nguoi('GV Bu', ROLE_TEACHER)
    a = _nguoi('Em Bu A')
    b = _nguoi('Em Bu B')
    lop = _lop('Lớp buổi bù', gv)
    _vao(lop, a)
    _vao(lop, b)
    bu = _buoi(lop, cach_ngay=3, chu_de='Buổi bù cho A')
    _rieng(bu, [a])

    assert bu in _ids(_goi(a, lop, limit=50)), 'em CÓ trong buổi bù phải thấy bản ghi'
    assert bu not in _ids(_goi(b, lop, limit=50)), \
        'em KHÔNG trong buổi bù không được thấy bản ghi buổi ấy (§62e)'


def test_ban_ghi_buoi_thuong_toi_ca_lop():
    gv = _nguoi('GV Thuong', ROLE_TEACHER)
    a = _nguoi('Em Thuong A')
    b = _nguoi('Em Thuong B')
    lop = _lop('Lớp buổi thường', gv)
    _vao(lop, a)
    _vao(lop, b)
    thuong = _buoi(lop, cach_ngay=4)
    bu = _buoi(lop, cach_ngay=3)
    _rieng(bu, [a])                          # A có dòng session_participants, B chưa có dòng nào

    assert thuong in _ids(_goi(a, lop, limit=50))
    assert thuong in _ids(_goi(b, lop, limit=50)), \
        ('buổi THƯỜNG phải tới cả lớp — B chưa có dòng session_participants nào, và đây là '
         'nhánh mà việc gọi `thuoc_buoi` thiếu tiền tố bảng làm mất lặng lẽ')


def test_tai_lieu_buoi_bu_chi_em_trong_buoi_thay():
    gv = _nguoi('GV Bu TL', ROLE_TEACHER)
    a = _nguoi('Em Bu TL A')
    b = _nguoi('Em Bu TL B')
    lop = _lop('Lớp buổi bù tài liệu', gv)
    _vao(lop, a)
    _vao(lop, b)
    bu = _buoi(lop, cach_ngay=3)
    _rieng(bu, [a])
    tl = _tl(lop, 'Bản chữa buổi bù', buoi=bu)

    assert tl in _ids(_goi(a, lop, loai='hoc-lieu', limit=50), 'id')
    assert tl not in _ids(_goi(b, lop, loai='hoc-lieu', limit=50), 'id'), \
        'tài liệu của buổi bù không phải việc của cả lớp (§60, §62e)'


def test_tai_lieu_buoi_thuong_toi_ca_lop():
    gv = _nguoi('GV Thuong TL', ROLE_TEACHER)
    a = _nguoi('Em Thuong TL A')
    b = _nguoi('Em Thuong TL B')
    lop = _lop('Lớp buổi thường tài liệu', gv)
    _vao(lop, a)
    _vao(lop, b)
    thuong = _buoi(lop, cach_ngay=4)
    bu = _buoi(lop, cach_ngay=3)
    _rieng(bu, [a])
    tl = _tl(lop, 'Slide buổi thường', buoi=thuong)

    assert tl in _ids(_goi(a, lop, loai='hoc-lieu', limit=50), 'id')
    assert tl in _ids(_goi(b, lop, loai='hoc-lieu', limit=50), 'id'), \
        'tài liệu của buổi THƯỜNG phải tới cả lớp (nhánh thiếu tiền tố bảng của `thuoc_buoi`)'


def test_kho_chung_cua_lop_toi_moi_em():
    gv = _nguoi('GV Kho', ROLE_TEACHER)
    b = _nguoi('Em Kho B')
    lop = _lop('Lớp kho chung', gv)
    _vao(lop, b)
    bu = _buoi(lop, cach_ngay=3)
    _rieng(bu, [_nguoi('Em Kho A')])
    tl = _tl(lop, 'Sổ tay công thức')     # session_id NULL — kho chung của lớp

    assert tl in _ids(_goi(b, lop, loai='hoc-lieu', limit=50), 'id'), \
        'kho chung không gắn buổi nào thì tới mọi em trong lớp'


# ── 6 · Hàng rào lớp: 404, và em đã rời lớp ─────────────────────────────────

def test_em_lop_khac_nhan_404_chu_khong_403():
    gv = _nguoi('GV Kin', ROLE_TEACHER)
    ngoai = _nguoi('Em Ngoai Lop')
    lop = _lop('Lớp kín', gv)
    _buoi(lop, cach_ngay=3)

    res = _goi(ngoai, lop)
    assert res.status_code == 404, 'không được lộ ra rằng lớp ấy có tồn tại'


def test_ban_ghi_lop_khac_khong_lot_vao_danh_sach():
    gv = _nguoi('GV Hai Lop', ROLE_TEACHER)
    em = _nguoi('Em Hai Lop')
    cua_em = _lop('Lớp của em', gv)
    lop_khac = _lop('Lớp khác', gv)
    _vao(cua_em, em)
    _vao(lop_khac, _nguoi('Em Lop Khac'))
    cua_em_buoi = _buoi(cua_em, cach_ngay=3)
    khac_buoi = _buoi(lop_khac, cach_ngay=3)
    khac_tl = _tl(lop_khac, 'Tài liệu lớp khác')
    _tl(cua_em, 'Tài liệu lớp của em')

    ds = _ids(_goi(em, cua_em, limit=50))
    assert cua_em_buoi in ds
    assert khac_buoi not in ds, 'bản ghi lớp khác không được lọt vào danh sách của em'
    assert khac_tl not in _ids(_goi(em, cua_em, loai='hoc-lieu', limit=50), 'id'), \
        'tài liệu lớp khác không được lọt vào danh sách của em'


def test_em_da_roi_lop_khong_xem_duoc_nua():
    gv = _nguoi('GV Roi', ROLE_TEACHER)
    roi = _nguoi('Em Da Roi')
    lop = _lop('Lớp đã rời', gv)
    _vao(lop, roi, roi=True)
    _buoi(lop, cach_ngay=3)
    _tl(lop, 'Đề ôn')

    assert _goi(roi, lop).status_code == 404, 'rời lớp là hết quyền xem (§60, §72)'
    assert _goi(roi, lop, loai='hoc-lieu').status_code == 404


def test_lop_khong_co_thi_404():
    em = _nguoi('Em Lop Khong Co')
    assert _goi(em, 2 ** 30).status_code == 404


# ── 7 · Lớp rỗng, và tham số rác ────────────────────────────────────────────

def test_lop_chua_co_ban_ghi_nao_tra_danh_sach_rong():
    gv = _nguoi('GV Rong', ROLE_TEACHER)
    em = _nguoi('Em Rong')
    lop = _lop('Lớp chưa có bản ghi', gv)
    _vao(lop, em)
    _buoi(lop, cach_ngay=3, link=None)        # buổi đã học nhưng chưa ai dán link

    res = _goi(em, lop)
    assert res.status_code == 200, 'lớp rỗng là danh sách rỗng, không phải lỗi'
    assert res.json()['items'] == []
    assert res.json()['tiep'] is None

    res_tl = _goi(em, lop, loai='hoc-lieu')
    assert res_tl.status_code == 200
    assert res_tl.json()['items'] == []


def test_buoi_da_huy_va_buoi_chua_dien_ra_khong_hien():
    gv = _nguoi('GV Huy', ROLE_TEACHER)
    em = _nguoi('Em Huy')
    lop = _lop('Lớp buổi huỷ', gv)
    _vao(lop, em)
    huy = _buoi(lop, cach_ngay=3, trang_thai='cancelled')
    sau = _buoi(lop, cach_ngay=-3)            # buổi của tuần tới
    that = _buoi(lop, cach_ngay=2)

    ds = _ids(_goi(em, lop, limit=50))
    assert ds == [that], 'chỉ buổi ĐÃ DIỄN RA và chưa huỷ mới có bản ghi để xem lại'
    assert huy not in ds and sau not in ds


def test_tham_so_rac_khong_lam_do_man():
    gv = _nguoi('GV Rac', ROLE_TEACHER)
    em = _nguoi('Em Rac')
    lop = _lop('Lớp tham số rác', gv)
    _vao(lop, em)
    _buoi(lop, cach_ngay=3)

    res = _goi(em, lop, limit='abc', truoc='xyz')
    assert res.status_code == 200, 'tham số hỏng phải cho ra màn mặc định, không phải 500'
    assert len(res.json()['items']) == 1


def test_loai_khong_biet_thi_400_bang_loi_tieng_viet():
    gv = _nguoi('GV Loai', ROLE_TEACHER)
    em = _nguoi('Em Loai')
    lop = _lop('Lớp loại lạ', gv)
    _vao(lop, em)

    res = _goi(em, lop, loai='bai-hat')
    assert res.status_code == 400
    assert 'error' in res.json()


# ── 8 · "Đã mở / chưa mở" của dòng 29, và ô lọc ─────────────────────────────

def test_da_mo_va_loc_chi_buoi_chua_mo():
    gv = _nguoi('GV Da Mo', ROLE_TEACHER)
    em = _nguoi('Em Da Mo')
    lop = _lop('Lớp đã mở', gv)
    _vao(lop, em)
    da = _buoi(lop, cach_ngay=3)
    chua = _buoi(lop, cach_ngay=4)

    ghi = _the(em).post('/api/sessions/%d/ban-ghi/da-mo' % da)
    assert ghi.status_code == 200, ghi.content

    res = _goi(em, lop, limit=50)
    theo_id = {d['sessionId']: d for d in res.json()['items']}
    assert theo_id[da]['daMo'] is True and theo_id[da]['lanMo'] == 1
    assert theo_id[chua]['daMo'] is False and theo_id[chua]['lanMo'] == 0

    loc = _goi(em, lop, limit=50, chuaMo=1)
    assert _ids(loc) == [chua], 'ô lọc "chưa xem lại" phải bỏ buổi em đã mở'


def test_loc_kho_chung_va_theo_buoi():
    gv = _nguoi('GV Loc TL', ROLE_TEACHER)
    em = _nguoi('Em Loc TL')
    lop = _lop('Lớp lọc tài liệu', gv)
    _vao(lop, em)
    b = _buoi(lop, cach_ngay=3)
    chung = _tl(lop, 'Sổ tay cả khoá')
    cua_buoi = _tl(lop, 'Slide buổi 3', buoi=b)

    assert _ids(_goi(em, lop, loai='hoc-lieu', chi='chung', limit=50), 'id') == [chung]
    assert _ids(_goi(em, lop, loai='hoc-lieu', chi='buoi', limit=50), 'id') == [cua_buoi]


def test_tra_ve_ten_lop_de_man_co_tieu_de():
    gv = _nguoi('GV Ten', ROLE_TEACHER)
    em = _nguoi('Em Ten')
    lop = _lop('Lớp HSA định lượng 27/09', gv)
    _vao(lop, em)

    d = _goi(em, lop).json()
    assert d['lop']['id'] == lop
    assert d['lop']['name'] == 'Lớp HSA định lượng 27/09'
