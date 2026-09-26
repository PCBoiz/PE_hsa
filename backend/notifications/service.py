"""
notifications/service.py — helper tạo thông báo có GỘP (coalesce).

Quy tắc gộp: nếu user còn một thông báo CHƯA ĐỌC cùng (type, ref_type, ref_id)
được tạo/cập nhật trong vòng COALESCE_MINUTES phút → không insert dòng mới mà
tăng coalesce_count + đổi title sang dạng số nhiều + bump created_at (đẩy lên
đầu feed). Tránh spam kiểu "10 comment = 10 thông báo" khi thảo luận sôi nổi.

Cột notifications.coalesce_count là additive (ALTER TABLE ... IF NOT EXISTS),
code cũ không đọc cột này nên không ảnh hưởng bản Flask đang chạy chung DB.
"""
from common.db import q1, x

COALESCE_MINUTES = 10


def notify(user_id, ntype, title, body, ref_type, ref_id,
           title_multi=None, coalesce_minutes=COALESCE_MINUTES):
    """Tạo thông báo cho user, gộp với thông báo chưa đọc gần đây cùng nguồn.

    title       — tiêu đề khi đứng một mình ("A đã bình luận về bài viết của bạn")
    title_multi — template khi gộp, chứa '{n}' ("{n} bình luận mới trong bài viết
                  của bạn"). None = lần sau THAY lần trước: cả tiêu đề lẫn nội
                  dung lấy của lần mới nhất.
    body        — snippet nội dung MỚI NHẤT (giữ của comment sau cùng).
    Trả về id của notification (mới hoặc được gộp).

    HAI KIỂU GỘP, và vì sao phải phân biệt (26/09/2026)
    ---------------------------------------------------
    · TÍCH LUỸ (`title_multi` có): nhiều việc cùng loại cộng dồn — "3 bình luận
      mới". Tiêu đề đếm số, thân giữ câu mới nhất.
    · THAY THẾ (`title_multi` là None): việc sau ĐÈ việc trước. Buổi học dời lúc
      10:00 rồi huỷ lúc 10:05 không phải "2 lần đổi lịch" — nó là một buổi, nay
      đã huỷ.

    Bản cũ thay `body` cho cả hai kiểu nhưng chỉ đổi `title` ở kiểu tích luỹ. Mà
    `bao_doi_lich`, `assignments` và `notifications/gui.py` đều không truyền
    `title_multi`, nên học viên nhận một dòng chuông mà tiêu đề nói "dời buổi
    sang 10:40" còn thân nói "sẽ không diễn ra" — hai câu ngược nhau, và câu sai
    lại là câu to hơn.
    """
    if coalesce_minutes and coalesce_minutes > 0:
        merged = q1(
            '''UPDATE notifications
               SET coalesce_count = COALESCE(coalesce_count, 1) + 1,
                   body = %s,
                   created_at = NOW()
               WHERE id = (
                   SELECT id FROM notifications
                   WHERE user_id = %s AND type = %s
                     AND ref_type = %s AND ref_id = %s
                     AND is_read = FALSE
                     AND created_at > NOW() - make_interval(mins => %s)
                   ORDER BY created_at DESC LIMIT 1
               )
               RETURNING id, coalesce_count''',
            (body, user_id, ntype, ref_type, ref_id, coalesce_minutes))
        if merged:
            # Tiêu đề phải đi cùng thân, luôn luôn: đếm số khi tích luỹ, lấy của
            # lần mới nhất khi thay thế. Không nhánh nào để tiêu đề ở lại phía sau.
            x('UPDATE notifications SET title = %s WHERE id = %s',
              (title_multi.format(n=merged['coalesce_count']) if title_multi else title,
               merged['id']))
            return merged['id']

    row = q1(
        '''INSERT INTO notifications (user_id, type, title, body, ref_type, ref_id)
           VALUES (%s, %s, %s, %s, %s, %s) RETURNING id''',
        (user_id, ntype, title, body, ref_type, ref_id))
    return row['id']


def unread_state(user_id):
    """(unread_count, latest_id) — nguồn cho /api/notifications/badge (client poll)."""
    row = q1(
        '''SELECT COUNT(*) FILTER (WHERE is_read = FALSE) AS unread,
                  COALESCE(MAX(id), 0) AS latest
           FROM notifications WHERE user_id = %s''',
        (user_id,))
    return row['unread'], row['latest']
