"""Ô liên hệ phụ huynh ở Cài đặt — `PUT /api/user`.

── VÌ SAO CÓ (13/09/2026) ─────────────────────────────────────────────────

Cột `users.parent_email` có từ 07/09 và kênh email là kênh CHÍNH gửi báo cáo
(anh Sơn chốt), nhưng tới hôm nay KHÔNG có đường nào ghi vào cột ấy: ô Cài đặt
chỉ có tên và số Zalo, `PUT /api/user` không đọc khoá `parent_email`. Đo trên
production: 0 em có email phụ huynh. Tức cả kênh gửi chính không gửi được cho
ai, và màn hình gửi cả lớp khuyên "các em tự điền được ở Cài đặt" — một chỗ
không có ô để điền.

── VẮNG KHOÁ THÌ GIỮ, GỬI RỖNG THÌ XOÁ ───────────────────────────────────

Từ hôm nay liên hệ phụ huynh có HAI người ghi: chính em (Cài đặt) và học vụ
(dán cả lớp). `PUT` cũ ghi đè cả ba cột bằng bất cứ thứ gì gửi lên, kể cả khi
khoá không có mặt — nên một thẻ trình duyệt mở từ trước bản cập nhật (chưa có ô
email) bấm Lưu là xoá trắng email học vụ vừa nhập, im lặng.
"""
import pytest

from common.db import q1, x

pytestmark = pytest.mark.django_db

HO_SO = {'name': 'Django Tester', 'email': 'django_test_tmp@example.com', 'phone': ''}


def _ph(uid):
    return q1('SELECT parent_name, parent_phone, parent_email FROM users WHERE id=%s', (uid,))


def test_luu_va_tra_lai_email_phu_huynh(auth_api, temp_user):
    r = auth_api.put('/api/user', dict(HO_SO, parent_email='  Me.An@Example.com '),
                     format='json')
    assert r.status_code == 200, r.json()
    # Lưu bản CHUẨN HOÁ — cùng luật với email đăng nhập.
    assert _ph(temp_user)['parent_email'] == 'me.an@example.com'
    # Không trả về thì mở lại Cài đặt là ô trống, dù đã lưu đúng.
    assert auth_api.get('/api/user').json()['parent_email'] == 'me.an@example.com'


def test_email_phu_huynh_sai_dang_bi_chan_truoc_khi_ghi(auth_api, temp_user):
    r = auth_api.put('/api/user', dict(HO_SO, parent_email='me@@example'), format='json')
    assert r.status_code == 400
    assert 'parent_email' in r.json()['errors']
    assert _ph(temp_user)['parent_email'] == ''


def test_email_phu_huynh_bo_trong_thi_hop_le(auth_api, temp_user):
    """`validate_email_field` coi rỗng là lỗi (nó viết cho email ĐĂNG NHẬP). Ô
    phụ huynh thì tuỳ chọn — dùng thẳng validator ấy là chặn mọi em chưa có
    email của bố mẹ lưu bất cứ thứ gì ở Cài đặt."""
    r = auth_api.put('/api/user', dict(HO_SO, parent_email=''), format='json')
    assert r.status_code == 200, r.json()


# ── §47 · Trung tâm đã nhập thì em không sửa (anh Sơn chốt C5, 14/09/2026) ──

def _khoa(uid, boi):
    x("UPDATE users SET parent_name='Mẹ', parent_phone='0900555901', parent_email='', "
      "parent_contact_locked_at=now(), parent_contact_locked_by=%s WHERE id=%s", (boi, uid))


def test_da_khoa_thi_khong_doi_duoc_o_da_co(auth_api, temp_user, temp_admin):
    _khoa(temp_user, temp_admin)
    r = auth_api.put('/api/user', dict(HO_SO, parent_name='Mẹ', parent_phone='0900555999',
                                       parent_email=''), format='json')
    assert r.status_code == 400, r.json()
    assert 'parent_phone' in r.json()['errors']
    assert 'học vụ' in r.json()['errors']['parent_phone']
    assert _ph(temp_user)['parent_phone'] == '0900555901'


def test_da_khoa_van_dien_duoc_o_con_trong_va_gui_lai_y_cu_thi_ok(auth_api, temp_user, temp_admin):
    _khoa(temp_user, temp_admin)
    # Gửi lại y giá trị đang có (Cài đặt gửi cả ba ô mỗi lần Lưu) → không phải "sửa".
    r = auth_api.put('/api/user', dict(HO_SO, parent_name='Mẹ', parent_phone='0900 555 901',
                                       parent_email=''), format='json')
    assert r.status_code == 200, r.json()
    # Ô email còn trống thì em điền được.
    r = auth_api.put('/api/user', dict(HO_SO, parent_name='Mẹ', parent_phone='0900555901',
                                       parent_email='me@example.com'), format='json')
    assert r.status_code == 200, r.json()
    assert _ph(temp_user)['parent_email'] == 'me@example.com'
    # Điền xong thì ô ấy cũng thành ô của trung tâm — sửa lại phải qua học vụ.
    r = auth_api.put('/api/user', dict(HO_SO, parent_email='khac@example.com'), format='json')
    assert r.status_code == 400, r.json()


def test_da_khoa_thi_khong_xoa_trang_duoc(auth_api, temp_user, temp_admin):
    _khoa(temp_user, temp_admin)
    r = auth_api.put('/api/user', dict(HO_SO, parent_phone=''), format='json')
    assert r.status_code == 400, r.json()
    assert _ph(temp_user)['parent_phone'] == '0900555901'


def test_chua_khoa_thi_em_sua_thoai_mai_va_get_bao_co_khoa_hay_khong(auth_api, temp_user, temp_admin):
    x("UPDATE users SET parent_phone='0900555901' WHERE id=%s", (temp_user,))
    assert auth_api.get('/api/user').json()['parent_contact_locked'] is False
    r = auth_api.put('/api/user', dict(HO_SO, parent_phone='0900555999'), format='json')
    assert r.status_code == 200, r.json()
    _khoa(temp_user, temp_admin)
    assert auth_api.get('/api/user').json()['parent_contact_locked'] is True


def test_so_co_khoang_trang_duoc_chuan_hoa_truoc_khi_kiem(auth_api, temp_user):
    """Cùng luật với ô cấp tài khoản hàng loạt. Bản trước kiểm số thô nên
    "0900 555 901" bị Cài đặt từ chối trong khi màn cấp tài khoản nhận."""
    r = auth_api.put('/api/user', dict(HO_SO, phone='+84 900 555 100',
                                       parent_phone='0900 555 901'), format='json')
    assert r.status_code == 200, r.json()
    row = q1('SELECT phone, parent_phone FROM users WHERE id=%s', (temp_user,))
    assert (row['phone'], row['parent_phone']) == ('0900555100', '0900555901')


def test_vang_khoa_thi_giu_gui_rong_thi_xoa(auth_api, temp_user):
    x("UPDATE users SET parent_name='Mẹ', parent_phone='0900555901', "
      "parent_email='me@example.com' WHERE id=%s", (temp_user,))

    r = auth_api.put('/api/user', HO_SO, format='json')
    assert r.status_code == 200, r.json()
    assert _ph(temp_user) == {'parent_name': 'Mẹ', 'parent_phone': '0900555901',
                              'parent_email': 'me@example.com'}, \
        'PUT không mang khoá liên hệ phụ huynh mà vẫn xoá trắng thứ học vụ đã nhập'

    r = auth_api.put('/api/user', dict(HO_SO, parent_name='', parent_phone='',
                                       parent_email=''), format='json')
    assert r.status_code == 200, r.json()
    assert _ph(temp_user) == {'parent_name': '', 'parent_phone': '', 'parent_email': ''}
