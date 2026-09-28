"""Test cơ bản app notifications (0-test ở bản Flask)."""
import pytest

pytestmark = pytest.mark.django_db


def test_settings_default(auth_api):
    res = auth_api.get('/api/notifications')
    assert res.status_code == 200
    assert res.json() == {'emailNotif': True, 'pushNotif': False,
                          'studyRemind': True, 'contentUpdate': False}


def test_settings_roundtrip(auth_api):
    res = auth_api.put('/api/notifications',
                       {'emailNotif': False, 'pushNotif': True,
                        'studyRemind': False, 'contentUpdate': True}, format='json')
    assert res.status_code == 200
    data = auth_api.get('/api/notifications').json()
    assert data == {'emailNotif': False, 'pushNotif': True,
                    'studyRemind': False, 'contentUpdate': True}


def test_feed_empty_and_read_all(auth_api):
    feed = auth_api.get('/api/notifications/feed').json()
    assert feed['items'] == [] and feed['unread'] == 0
    assert auth_api.post('/api/notifications/feed/read-all').status_code == 200


def test_badge_empty(auth_api):
    res = auth_api.get('/api/notifications/badge')
    assert res.status_code == 200
    assert res.json() == {'unread': 0, 'latest': 0}


def test_badge_counts_unread(auth_api, temp_user):
    from notifications.service import notify
    notify(temp_user, 'system', 'Chào mừng', 'nội dung', 'post', 1)
    data = auth_api.get('/api/notifications/badge').json()
    assert data['unread'] == 1 and data['latest'] > 0


def test_requires_auth(api, db):
    assert api.get('/api/notifications').status_code == 401
    assert api.get('/api/notifications/badge').status_code == 401


# ── Gộp thông báo: tiêu đề và nội dung phải cùng nói MỘT chuyện (26/09/2026) ──
#
# Anh Sơn đọc thư thật rồi hỏi lại case này. Dựng lại đúng cảnh đã thấy: giảng
# viên dời buổi lúc 10:00, năm phút sau huỷ luôn buổi ấy. Hai lần báo cùng rơi
# vào cửa gộp 10 phút, nên chúng nhập làm một dòng chuông — đúng ý đồ, vì ba
# mươi chuông một lúc thì không ai đọc.
#
# Chỗ hỏng: `notify()` thay `body` bằng nội dung MỚI nhưng chỉ đổi `title` khi
# người gọi truyền `title_multi`. `bao_doi_lich`, `assignments` và
# `notifications/gui.py` đều không truyền, nên học viên nhận một dòng mà tiêu đề
# nói "dời buổi sang 10:40" còn nội dung nói "sẽ không diễn ra" — hai câu ngược
# nhau, và câu sai lại là câu to hơn.
#
# Hai lời gọi này KHÁC nhau về nghĩa, và hàm phải phân biệt được:
#   · tích luỹ (bình luận) — "3 bình luận mới", cần `title_multi`, đếm lên;
#   · thay thế (đổi lịch, bài tập) — lần sau ĐÈ lần trước, không phải cộng dồn.


def _doc(nid):
    from common.db import q1
    return q1('SELECT title, body, coalesce_count FROM notifications WHERE id = %s', (nid,))


def test_gop_khong_de_tieu_de_nguoc_voi_noi_dung(temp_user):
    """Không có `title_multi` = lần sau THAY lần trước: cả tiêu đề lẫn nội dung."""
    from notifications.service import notify
    a = notify(temp_user, 'lich_doi', 'Lớp A dời buổi 26/09 09:00 sang 26/09 10:40',
               'Buổi học lớp A đổi giờ: bắt đầu lúc 10:40.', 'class_session', 9001)
    b = notify(temp_user, 'lich_doi', 'Lớp A: buổi 26/09 09:00 đã huỷ',
               'Buổi học lớp A vào thứ Bảy 26/09, 09:00 sẽ không diễn ra.',
               'class_session', 9001)
    assert a == b, 'hai lần báo cùng một buổi trong 10 phút thì phải gộp làm một'
    r = _doc(b)
    assert 'huỷ' in r['title'], 'tiêu đề phải là lần MỚI NHẤT, không giữ lần đã cũ'
    assert 'không diễn ra' in r['body']
    assert 'dời' not in r['title'], 'tiêu đề cũ nói dời mà nội dung nói huỷ là hai câu ngược nhau'


def test_gop_tich_luy_van_dem_va_dung_mau_title_multi(temp_user):
    """Có `title_multi` = tích luỹ: tiêu đề đếm số, không phải đè."""
    from notifications.service import notify
    a = notify(temp_user, 'post_comment', 'An đã bình luận', 'câu của An', 'post', 9002,
               title_multi='{n} bình luận mới')
    b = notify(temp_user, 'post_comment', 'Bình đã bình luận', 'câu của Bình', 'post', 9002,
               title_multi='{n} bình luận mới')
    assert a == b
    r = _doc(b)
    assert r['title'] == '2 bình luận mới'
    assert r['body'] == 'câu của Bình'
    assert r['coalesce_count'] == 2
