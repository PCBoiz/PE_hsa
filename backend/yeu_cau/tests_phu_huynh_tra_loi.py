"""PHỤ HUYNH TRẢ LỜI TIẾP trong MỘT yêu cầu — thay vì phải mở yêu cầu mới mỗi lượt.

── LỖ ĐANG CHẶN LẠI (28/09/2026) ───────────────────────────────────────────

Phụ huynh mở tờ báo cáo bằng chìa, gửi được yêu cầu, và ĐỌC được trả lời của trung tâm. Nhưng
không trả lời tiếp được: cửa `POST /api/yeu-cau/<id>/tra-loi` gác bằng `LaHocVien`, tức đòi
một tài khoản đã đăng nhập — mà phụ huynh theo thiết kế thì KHÔNG có tài khoản (dòng 23 của
bảng: xem qua link riêng).

Hậu quả trên thực tế: học vụ hỏi lại "cháu nghỉ từ hôm nào ạ?", phụ huynh không có chỗ trả
lời, nên mở một yêu cầu MỚI. Một cuộc trao đổi bốn lượt thành bốn phiếu rời nhau, mỗi phiếu
một trạng thái, và không phiếu nào mang đủ câu chuyện. Trần 5 yêu cầu đang mở
(`TRAN_MO_PHU_HUYNH`) thì đầy sau hai câu hỏi qua lại.

── ĐIỀU BẤT NGỜ: TẦNG DỊCH VỤ ĐÃ CHO PHÉP SẴN ──────────────────────────────

`dich_vu.tra_loi` gác bằng `nguoi.la_nhan_su or _la_nguoi_tao(nguoi, yc)`, và
`_la_nguoi_tao` ĐÃ nhận phụ huynh cầm chìa (`yc['nguon'] == 'phu_huynh' and yc['link_id'] ==
nguoi.link['id']`). `chi_tiet` cũng đang trả `coThe.traLoi = true` cho họ. Tức máy chủ vẫn nói
"bạn trả lời được" trong khi không có cửa nào để trả lời — thiếu đúng một tuyến HTTP.

Nên bộ kiểm này canh CỬA, và canh cả những thứ mà cửa mới KHÔNG được mở thêm.

Chạy trên CSDL thật, giao dịch CUỘN LẠI; chỉ đếm dữ liệu của chính mình.
"""
import pytest
from rest_framework.test import APIClient

from common.db import q, q1

pytestmark = pytest.mark.django_db

DUONG = '/api/public/phu-huynh/%s/yeu-cau/%d/tra-loi'


def _gui(tk, loai='ht_hoc_tap', tieu_de='Cháu nghỉ hôm qua'):
    """Phụ huynh gửi một yêu cầu qua chìa, trả id."""
    r = APIClient().post('/api/public/phu-huynh/%s/yeu-cau' % tk,
                         {'loai': loai, 'tieu_de': tieu_de}, format='json')
    assert r.status_code == 201, r.data
    return r.data['id']


def _su_kien(yc_id):
    return q('SELECT kieu, noi_dung, noi_bo, actor_ten FROM yeu_cau_su_kien '
             'WHERE yeu_cau_id = %s ORDER BY id', (yc_id,))


# ── 1. Trả lời được, và lời ấy vào đúng mạch ────────────────────────────────

def test_phu_huynh_tra_loi_tiep_duoc_trong_yeu_cau_cua_minh(d, canh):
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    yid = _gui(tk)
    r = APIClient().post(DUONG % (tk, yid), {'noi_dung': 'Cháu nghỉ từ thứ Hai ạ.'}, format='json')
    assert r.status_code == 200, r.data
    ds = [s for s in _su_kien(yid) if s['kieu'] == 'tra_loi']
    assert any('thứ Hai' in (s['noi_dung'] or '') for s in ds), _su_kien(yid)


def test_loi_cua_phu_huynh_KHONG_phai_ghi_chu_noi_bo(d, canh):
    """Ghi chú nội bộ là thứ chỉ nhân sự đọc. Phụ huynh viết vào đó là rò ngược.

    Phải canh CẢ HAI VẾ. Bản đầu chỉ đòi "không có sự kiện nội bộ nào", và đột biến "nhận
    `noi_bo` từ thân yêu cầu" LỌT thẳng (đo 28/09): với đột biến ấy máy chủ trả 403 và KHÔNG
    ghi gì cả, nên vế phủ định vẫn đúng — bộ kiểm nói "an toàn" trong khi cửa đã hỏng hẳn.
    Một phép kiểm chỉ đòi "không có X" thì mọi cách làm hỏng đều qua được, kể cả cách làm cho
    không có gì hết.
    """
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    yid = _gui(tk)
    r = APIClient().post(DUONG % (tk, yid), {'noi_dung': 'Cháu ốm ạ.', 'noi_bo': True},
                         format='json')
    assert r.status_code == 200, r.data
    ds = _su_kien(yid)
    assert not [s for s in ds if s['noi_bo']], ds
    assert [s for s in ds if s['kieu'] == 'tra_loi' and 'ốm' in (s['noi_dung'] or '')], ds


def test_phu_huynh_doc_lai_thay_loi_minh_vua_gui(d, canh):
    """Đường về: mở lại chính chìa ấy thì lời vừa gửi có trong luồng."""
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    yid = _gui(tk)
    APIClient().post(DUONG % (tk, yid), {'noi_dung': 'Mai cháu đi học lại ạ.'}, format='json')
    r = APIClient().get('/api/public/phu-huynh/%s/yeu-cau' % tk)
    assert r.status_code == 200
    yc = [y for y in r.data['yeuCau'] if y['id'] == yid][0]
    assert any('đi học lại' in (s.get('noiDung') or '') for s in yc['suKien']), yc['suKien']


# ── 2. Những thứ cửa mới KHÔNG được mở thêm ─────────────────────────────────

def test_khong_tra_loi_duoc_yeu_cau_cua_CHIA_KHAC(d, canh):
    """Chìa của em này không được chạm vào yêu cầu gửi qua chìa của em khác."""
    tk1 = d.link(canh['a'], canh['em'], canh['gv'])
    tk2 = d.link(canh['a'], canh['em2'], canh['gv'])
    yid = _gui(tk1)
    r = APIClient().post(DUONG % (tk2, yid), {'noi_dung': 'Tôi xem trộm được không'}, format='json')
    assert r.status_code == 404, r.data
    assert not [s for s in _su_kien(yid) if s['kieu'] == 'tra_loi'], _su_kien(yid)


def test_khong_tra_loi_duoc_yeu_cau_CUA_EM_tu_gui(d, canh):
    """Em đăng nhập tự gửi một yêu cầu — phụ huynh cầm chìa KHÔNG đọc, không trả lời."""
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    cua_em = d.api(canh['em']).post('/api/yeu-cau',
                                    {'loai': 'ht_hoc_tap', 'tieu_de': 'Việc riêng của em'},
                                    format='json').data['id']
    r = APIClient().post(DUONG % (tk, cua_em), {'noi_dung': 'Chen vào'}, format='json')
    assert r.status_code == 404, r.data


def test_chia_da_thu_hoi_thi_khong_tra_loi_duoc(d, canh):
    """Thu hồi chìa là cắt đường, không chỉ cắt phần đọc."""
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    yid = _gui(tk)
    from common.db import x as _x
    _x('UPDATE parent_report_links SET revoked_at = now() WHERE token = %s', (tk,))
    r = APIClient().post(DUONG % (tk, yid), {'noi_dung': 'Còn vào được không'}, format='json')
    assert r.status_code == 404, r.data


def test_yeu_cau_da_dong_thi_khong_tra_loi_them(d, canh):
    """Cùng luật với học viên: đóng rồi thì mở yêu cầu mới, đừng nối vào phiếu đã kết."""
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    yid = _gui(tk)
    d.api(canh['hv']).post('/api/teach/yeu-cau/%d/trang-thai' % yid, {'den': 'da_xong'},
                           format='json')
    r = APIClient().post(DUONG % (tk, yid), {'noi_dung': 'Nói thêm'}, format='json')
    assert r.status_code == 409, r.data


def test_loi_rong_bi_tu_choi(d, canh):
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    yid = _gui(tk)
    r = APIClient().post(DUONG % (tk, yid), {'noi_dung': '   '}, format='json')
    assert r.status_code == 400, r.data


# ── 3. Trả lời của phụ huynh phải ĐÁNH THỨC người xử lý ─────────────────────

def test_nguoi_xu_ly_duoc_bao_khi_phu_huynh_tra_loi(d, canh, django_capture_on_commit_callbacks):
    """Phiếu đang chờ mà phụ huynh nói thêm — không báo thì lời ấy nằm im tới khi ai đó mở ra."""
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    yid = _gui(tk)
    # Học vụ nhận việc → trở thành người xử lý.
    d.api(canh['hv']).post('/api/teach/yeu-cau/%d/trang-thai' % yid, {'den': 'dang_xu_ly'},
                           format='json')
    with django_capture_on_commit_callbacks(execute=True):
        APIClient().post(DUONG % (tk, yid), {'noi_dung': 'Cháu vẫn sốt ạ.'}, format='json')
    assert q1("SELECT 1 AS c FROM notifications WHERE user_id = %s AND type = 'yeu_cau' "
              'AND ref_id = %s', (canh['hv'], yid)), 'người xử lý không được báo'


def test_tra_loi_KHONG_lam_doi_trang_thai_phieu(d, canh):
    """Phụ huynh nói thêm không phải là "đã nhận việc" — trạng thái là của nhân sự."""
    tk = d.link(canh['a'], canh['em'], canh['gv'])
    yid = _gui(tk)
    APIClient().post(DUONG % (tk, yid), {'noi_dung': 'Thêm một ý ạ.'}, format='json')
    assert q1('SELECT trang_thai FROM yeu_cau WHERE id = %s', (yid,))['trang_thai'] == 'moi'
