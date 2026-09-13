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
