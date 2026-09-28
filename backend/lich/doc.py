"""ĐỌC BUỔI HỌC cho địa chỉ lịch riêng — §71, 26/09/2026.

Một câu SQL cho mỗi phạm vi, không vòng lặp gọi từng lớp: tệp lịch bị ứng dụng
lịch hỏi lại đều đặn (Google vài giờ một lần, Apple có thể nhanh hơn), nhân với
số người đã thêm lịch — đây là đường đọc bị gọi nhiều nhất trong sản phẩm mà
không ai ngồi nhìn. Nó phải rẻ ngay từ đầu.

PHẠM VI THỜI GIAN: từ 30 ngày trước tới 180 ngày sau. Quá khứ giữ một tháng để
người dùng còn tra lại buổi vừa học; xa hơn thì ứng dụng lịch đã có bản cũ rồi,
và tệp càng dài thì mỗi lượt hỏi lại càng tốn.

QUYỀN nằm ngay trong câu SQL, không lọc ở Python sau khi đã lấy về: học viên chỉ
thấy buổi của lớp em ĐANG học (`left_at IS NULL`), giảng viên/trợ giảng thấy buổi
mình phụ trách, `trung_tam` thấy tất cả. Lọc sau khi lấy là chỗ dễ quên nhất khi
ai đó thêm một nhánh mới vào hàm.
"""
from datetime import timedelta

from common.clock import local_now
from common.db import q

#: Khoảng thời gian tệp lịch phủ.
NGAY_TRUOC, NGAY_SAU = 30, 180

_CHUNG = '''SELECT s.id, s.starts_at, s.duration_minutes, s.topic, s.status,
                   s.meeting_url, s.updated_at,
                   coalesce(s.mode, c.mode) AS mode_hl,
                   coalesce(s.room, c.room) AS room_hl,
                   c.name AS lop, t.name AS giang_vien
              FROM class_sessions s
              JOIN classes c ON c.id = s.class_id
              LEFT JOIN users t ON t.id = c.teacher_id
             WHERE s.starts_at BETWEEN %(tu)s AND %(den)s
               AND c.status <> 'cancelled'
               AND '''

#: Học viên VÀ trợ giảng đều đứng trong `class_members` — không có bảng riêng cho
#: trợ giảng (đã kiểm `common/permissions.py::_la_tro_giang_cua_lop`, 26/09/2026).
#: Giảng viên đi bằng `classes.teacher_id`. Cùng luật với `can_see_class`, nên
#: người nào mở được lớp trên màn thì lịch của họ có đúng những buổi ấy.
_CUA_TOI = '''(EXISTS (SELECT 1 FROM class_members m
                        WHERE m.class_id = c.id AND m.user_id = %(nguoi)s
                          AND m.left_at IS NULL)
               OR c.teacher_id = %(nguoi)s)'''


def buoi_cua(user_id, scope='toi'):
    """Buổi học đưa vào tệp lịch của một người. `scope='trung_tam'` = mọi buổi."""
    nay = local_now()
    tham = {'tu': nay - timedelta(days=NGAY_TRUOC), 'den': nay + timedelta(days=NGAY_SAU),
            'nguoi': user_id}
    dieu_kien = 'TRUE' if scope == 'trung_tam' else _CUA_TOI
    return q(_CHUNG + dieu_kien + ' ORDER BY s.starts_at', tham)
