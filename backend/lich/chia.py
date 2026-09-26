"""CHÌA cho địa chỉ lịch riêng — §71, 26/09/2026.

Địa chỉ lịch mở được KHÔNG cần đăng nhập: ứng dụng lịch của điện thoại không biết
đăng nhập vào đâu, nó chỉ tải một địa chỉ. Nghĩa là chìa nằm ngay trong địa chỉ,
và ai cầm được địa chỉ thì đọc được lịch. Ba việc phải làm cho đúng:

1. **Chìa đủ dài để không dò ra**: 32 byte ngẫu nhiên từ `secrets` (256 bit), viết
   dạng an-toàn-cho-URL. Không dùng `random` — bộ ấy đoán được trạng thái.
2. **Chỉ lưu BĂM**, không lưu chìa. Ai đọc được cơ sở dữ liệu cũng không dựng lại
   được địa chỉ lịch của người khác. Dùng SHA-256: chìa là chuỗi ngẫu nhiên 256
   bit chứ không phải mật khẩu người tự nghĩ, nên không cần hàm băm chậm.
3. **So băm bằng phép so hằng thời gian** (`compare_digest`): so chuỗi thường trả
   lời sớm ở ký tự đầu khác nhau, và chênh lệch thời gian ấy đủ để dò dần từng ký
   tự. Ở đây tra bằng chỉ mục trên cột băm nên đã không so tuần tự, nhưng giữ
   `compare_digest` cho lượt so cuối để cách làm không phụ thuộc vào chi tiết ấy.

Cấp lại chìa là THU HỒI chìa cũ (`revoked_at`), không xoá dòng: giữ lại để còn
biết chìa cũ từng tồn tại và bị thu hồi lúc nào.
"""
import hashlib
import secrets

from common.clock import local_now
from common.db import q, q1, x

#: 32 byte = 256 bit. Dạng URL-safe nên dán vào địa chỉ không phải mã hoá thêm.
SO_BYTE = 32
PHAM_VI = ('toi', 'trung_tam')


def _bam(chia):
    return hashlib.sha256(chia.encode('utf-8')).hexdigest()


def cap(user_id, scope='toi'):
    """Cấp chìa mới (thu hồi chìa cũ cùng phạm vi). Trả về chìa THÔ — chỉ lần này.

    Hai bước nằm trong một giao dịch của tầng gọi (`ATOMIC_REQUESTS`): thu hồi
    trước rồi mới thêm, vì chỉ mục duy nhất phần `idx_calendar_links_mot_chia_song`
    không cho hai chìa còn sống cùng (người, phạm vi).
    """
    if scope not in PHAM_VI:
        raise ValueError('phạm vi lạ: %r' % (scope,))
    x('UPDATE calendar_links SET revoked_at = %s '
      'WHERE user_id = %s AND scope = %s AND revoked_at IS NULL',
      (local_now(), user_id, scope))
    chia = secrets.token_urlsafe(SO_BYTE)
    x('INSERT INTO calendar_links (user_id, scope, token_hash, created_at) '
      'VALUES (%s, %s, %s, %s)', (user_id, scope, _bam(chia), local_now()))
    return chia


def thu_hoi(user_id, scope='toi'):
    """Thu hồi chìa đang sống. Trả về True nếu có chìa để thu hồi."""
    r = q1('UPDATE calendar_links SET revoked_at = %s '
           'WHERE user_id = %s AND scope = %s AND revoked_at IS NULL RETURNING id',
           (local_now(), user_id, scope))
    return bool(r)


def dang_co(user_id):
    """Các phạm vi người này đang có chìa sống — để màn hình biết hiện nút gì."""
    return [r['scope'] for r in
            q('SELECT scope FROM calendar_links WHERE user_id = %s AND revoked_at IS NULL',
              (user_id,))]


def tra(chia):
    """Tra chìa thô → dòng `calendar_links` còn sống, hoặc None.

    Không phân biệt "chìa sai" với "chìa đã thu hồi": cả hai cùng trả None để
    tầng trên trả cùng một mã 404. Nói rõ chìa nào từng tồn tại là cho người dò
    biết họ đã đoán gần đúng.
    """
    if not chia or len(chia) > 200:
        return None
    r = q1('SELECT id, user_id, scope, token_hash FROM calendar_links '
           'WHERE token_hash = %s AND revoked_at IS NULL', (_bam(chia),))
    if not r or not secrets.compare_digest(r['token_hash'], _bam(chia)):
        return None
    return r


def ghi_luot_doc(link_id):
    """Đếm lượt ứng dụng lịch hỏi lại — để biết người dùng có thật sự dùng không."""
    x('UPDATE calendar_links SET fetch_count = fetch_count + 1, last_fetch_at = %s '
      'WHERE id = %s', (local_now(), link_id))
