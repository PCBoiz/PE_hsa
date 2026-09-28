"""HẠN XỬ LÝ VÀ CỜ QUÁ HẠN cho hộp Yêu cầu, cùng ô tìm theo chữ (bảng TopHSA dòng 11).

Dòng 11 của `docs/NGHIEM_THU_TOPHSA.md` tự ghi "Còn sót: hạn xử lý / cờ quá hạn, ô tìm theo
chữ" từ 26/09 và chưa ai quay lại. Hộp Yêu cầu của học vụ hôm nay xếp theo `updated_at`, nên
yêu cầu bị BỎ QUÊN — không ai trả lời, nên `updated_at` không nhúc nhích — trôi xuống đáy
danh sách. Thứ tự ấy đẩy đúng việc cần chú ý nhất ra khỏi tầm mắt.

── BỐN CHỖ DỄ LÀM SAI, MỖI CHỖ MỘT PHÉP KIỂM ───────────────────────────────

1. **Hạn tính từ LÚC GỬI, không từ `updated_at`.** Tính từ `updated_at` thì mỗi lượt trả lời
   là một lượt dời hạn, và một yêu cầu bị hỏi tới hỏi lui hai tuần sẽ KHÔNG BAO GIỜ quá hạn —
   đúng thứ cờ này sinh ra để bắt.

2. **Đóng rồi thì thôi quá hạn.** Cờ đỏ trên việc đã xong là cờ không ai gỡ được: hộp Yêu cầu
   sẽ đỏ vĩnh viễn theo bề dày lịch sử, và một màn lúc nào cũng đỏ thì không ai nhìn nữa.

3. **Giờ Việt Nam.** `created_at` ghi bằng `local_now()` (giờ VN, naive) còn `now()` của Neon
   trả giờ UTC — so hai thứ ấy lệch đúng bảy tiếng, và lệch về phía BỎ SÓT (`common/clock.py`
   viết lại nguyên cái lỗi này). `test_qua_han_do_bang_gio_viet_nam` chọn tuổi 25 giờ đúng vì
   nó nằm trong khung 24–31 giờ: quá hạn theo giờ VN, CHƯA quá hạn nếu ai đó so bằng `now()`.

4. **Ô tìm không được để ký tự đại diện lọt xuống ILIKE.** Gõ `%` vào ô tìm mà không thoát là
   khớp MỌI yêu cầu trong phạm vi — một ô tìm trả về đúng thứ nó vừa được bảo là đừng trả về.

Chạy trên CSDL thật, giao dịch CUỘN LẠI; chỉ đếm dữ liệu của chính mình.
"""
from datetime import timedelta

import pytest

from accounts.models import User
from common.clock import local_now
from common.db import q1
from yeu_cau import dich_vu as dv
from yeu_cau import loai as L

pytestmark = pytest.mark.django_db


def _nhan_su(canh, khoa='hv'):
    return dv.NguoiLam(user=User.objects.get(id=canh[khoa]))


def _gui(canh, *, loai='hoi_dap', gio_truoc=0, trang_thai='moi', tieu_de='Hỏi bài',
         noi_dung=None, lop=True):
    """Một yêu cầu đặt thẳng bằng SQL với tuổi cho trước — `tao()` luôn đóng dấu BÂY GIỜ."""
    luc = local_now() - timedelta(hours=gio_truoc)
    return q1('''INSERT INTO yeu_cau (loai, trang_thai, nguon, nguoi_tao, hoc_vien_id, class_id,
                                      tieu_de, noi_dung, created_at, updated_at)
                 VALUES (%s, %s, 'hoc_vien', %s, %s, %s, %s, %s, %s, %s) RETURNING id''',
              (loai, trang_thai, canh['em'], canh['em'], canh['a'] if lop else None,
               tieu_de, noi_dung, luc, local_now()))['id']


def _mot(canh, yc_id, khoa='hv'):
    return dv.chi_tiet(_nhan_su(canh, khoa), yc_id)


# ── Hạn và cờ ───────────────────────────────────────────────────────────────

def test_nhan_su_thay_han_xu_ly_va_co_qua_han(canh):
    yc = _gui(canh, gio_truoc=48)
    ra = _mot(canh, yc)
    assert ra['quaHan'] is True
    assert ra['hanXuLy'], 'yêu cầu phải mang hạn xử lý để màn hiện được "hạn ngày nào"'


def test_chua_toi_han_thi_khong_phai_qua_han(canh):
    assert _mot(canh, _gui(canh, gio_truoc=1))['quaHan'] is False


def test_han_dung_bang_luc_gui_cong_so_gio_cua_nhom(canh):
    yc = _gui(canh, gio_truoc=3)
    luc = q1('SELECT created_at FROM yeu_cau WHERE id = %s', (yc,))['created_at']
    cho = luc + timedelta(hours=L.HAN_GIO[L.HOI_DAP])
    assert _mot(canh, yc)['hanXuLy'] == cho.isoformat()


def test_han_tinh_tu_luc_gui_chu_khong_phai_luc_cap_nhat(canh):
    """Trả lời một yêu cầu đã quá hạn KHÔNG làm nó hết quá hạn."""
    yc = _gui(canh, gio_truoc=48)
    dv.tra_loi(_nhan_su(canh), yc, 'Em đợi cô xem lại nhé.')
    moi = q1('SELECT updated_at FROM yeu_cau WHERE id = %s', (yc,))['updated_at']
    assert local_now() - moi < timedelta(minutes=5), 'trả lời phải có dời updated_at'
    assert _mot(canh, yc)['quaHan'] is True


@pytest.mark.parametrize('tt', ('da_xong', 'tu_choi', 'da_huy'))
def test_yeu_cau_da_dong_thi_khong_con_qua_han(canh, tt):
    assert _mot(canh, _gui(canh, gio_truoc=500, trang_thai=tt))['quaHan'] is False


def test_qua_han_do_bang_gio_viet_nam(canh):
    """25 giờ: quá hạn theo giờ VN, chưa quá hạn nếu ai đó so bằng `now()` của Neon (UTC)."""
    assert _mot(canh, _gui(canh, gio_truoc=25))['quaHan'] is True


def test_moi_nhom_mot_han_rieng(canh):
    """Xin–duyệt được nhiều thời gian hơn hỏi bài — nếu không thì bảng giờ chỉ là một con số."""
    assert L.HAN_GIO[L.THAY_DOI] > L.HAN_GIO[L.HOI_DAP], 'bảng giờ phải phân biệt được nhóm'
    gio = (L.HAN_GIO[L.HOI_DAP] + L.HAN_GIO[L.THAY_DOI]) // 2
    assert _mot(canh, _gui(canh, loai='hoi_dap', gio_truoc=gio))['quaHan'] is True
    assert _mot(canh, _gui(canh, loai='tt_bao_luu', gio_truoc=gio))['quaHan'] is False


def test_hoc_vien_khong_thay_han_cua_trung_tam(canh):
    """Hạn là cam kết NỘI BỘ. In nó lên màn của em là hứa với em một điều trung tâm chưa hứa."""
    yc = _gui(canh, gio_truoc=48)
    ra = dv.chi_tiet(dv.NguoiLam(user=User.objects.get(id=canh['em'])), yc)
    assert 'hanXuLy' not in ra and 'quaHan' not in ra


# ── Lọc và tìm ──────────────────────────────────────────────────────────────

def test_loc_qua_han_chi_tra_ve_yeu_cau_qua_han(canh):
    cu, moi = _gui(canh, gio_truoc=48), _gui(canh, gio_truoc=1)
    ids = [y['id'] for y in dv.danh_sach(_nhan_su(canh), qua_han=True)]
    assert cu in ids and moi not in ids


def test_loc_qua_han_bo_qua_yeu_cau_da_dong(canh):
    xong = _gui(canh, gio_truoc=48, trang_thai='da_xong')
    assert xong not in [y['id'] for y in dv.danh_sach(_nhan_su(canh), qua_han=True)]


def test_qua_han_xep_len_truoc_trong_danh_sach(canh):
    """Yêu cầu bị bỏ quên không được trôi xuống đáy vì `updated_at` của nó không nhúc nhích."""
    cu = _gui(canh, gio_truoc=48)
    moi = _gui(canh, gio_truoc=1)
    ids = [y['id'] for y in dv.danh_sach(_nhan_su(canh)) if y['id'] in (cu, moi)]
    assert ids == [cu, moi]


def test_tim_theo_chu_trong_tieu_de(canh):
    co = _gui(canh, tieu_de='Xin đổi lịch buổi thứ Sáu')
    khong = _gui(canh, tieu_de='Hỏi bài hình học')
    ids = [y['id'] for y in dv.danh_sach(_nhan_su(canh), tim='thứ sáu')]
    assert co in ids and khong not in ids


def test_tim_theo_chu_trong_noi_dung(canh):
    co = _gui(canh, tieu_de='Hỏi bài', noi_dung='Em chưa nhận được mã phòng Zoom ạ')
    khong = _gui(canh, tieu_de='Hỏi bài', noi_dung='Em xin nghỉ buổi tối')
    ids = [y['id'] for y in dv.danh_sach(_nhan_su(canh), tim='zoom')]
    assert co in ids and khong not in ids


def test_tim_khong_de_ky_tu_dai_dien_lot_xuong_ilike(canh):
    """Gõ `%` không được biến ô tìm thành "trả về tất cả"."""
    _gui(canh, tieu_de='Hỏi bài hình học')
    assert dv.danh_sach(_nhan_su(canh), tim='%') == []
    assert dv.danh_sach(_nhan_su(canh), tim='_') == []


def test_tim_khong_lam_lo_yeu_cau_ngoai_pham_vi(canh, d):
    """Ô tìm chạy TRONG phạm vi — giảng viên lớp B không tìm thấy yêu cầu của lớp A."""
    yc = _gui(canh, tieu_de='Bí mật của lớp A')
    nguoi_b = dv.NguoiLam(user=User.objects.get(id=canh['gv_b']))
    assert yc not in [y['id'] for y in dv.danh_sach(nguoi_b, tim='Bí mật')]


def test_cua_view_nhan_qua_han_va_tim(canh, d):
    """Hai ô lọc phải tới được từ MÀN, không chỉ từ hàm dịch vụ."""
    cu = _gui(canh, gio_truoc=48, tieu_de='Bỏ quên mất rồi')
    _gui(canh, gio_truoc=1, tieu_de='Bỏ quên mất rồi')
    api = d.api(canh['hv'])
    r = api.get('/api/teach/yeu-cau?qua_han=1&tim=' + 'quên')
    assert r.status_code == 200
    assert [y['id'] for y in r.json()['yeuCau']] == [cu]
