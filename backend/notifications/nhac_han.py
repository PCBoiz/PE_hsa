"""NHẮC HẠN NỘP BÀI — loại thông báo tự động đầu tiên của E2 (bảng TopHSA dòng 20, 27).

Mỗi nhịp (`hop_thu.nhip`) quét bài còn 20–28 giờ tới hạn mà em CHƯA nộp → một chuông
(+ một thư nếu em bật email). Cửa sổ 8 giờ rộng hơn chu kỳ nhịp nhiều lần: nhịp ngoài
(cron-job.org) trễ hay máy chủ ngủ vài giờ thì bài vẫn lọt vào ít nhất một lượt quét.

── MỘT LẦN, KỂ CẢ HAI NHỊP CHỒNG NHAU ───────────────────────────────────────

Chuông: chỉ mục duy nhất phần `idx_notifications_nhac_han_mot_lan` (§61d) + ON CONFLICT DO
NOTHING. Thư: `dedup_key = nhac_han:{bài}:{em}`. Không đọc-rồi-ghi (hai câu) — hai nhịp chạy
cùng lúc sẽ cùng thấy "chưa nhắc".

── LUẬT ────────────────────────────────────────────────────────────────────

  · chỉ bài đang mở (`status = 'open'`), không phải bài kiểm tra trên lớp (`kind`), của lớp
    đang học (`classes.status = 'active'` — lớp tạm dừng thì thôi nhắc);
  · chỉ em ĐANG học lớp, là học viên, được giao bài (`nhan_bai.giao_cho`), chưa nộp;
  · tôn trọng `notification_settings.study_remind` (tắt = không nhắc gì) và `email_notif`
    (tắt = chỉ chuông); tài khoản mẫu (`is_demo`) và tài khoản khoá không có thư.

Mô-đun này CHỈ ĐỌC bảng bài tập (miền `bai_tap`); nó ghi bảng của chính miền thông báo.
"""
from datetime import timedelta

from django.db import transaction

from common.clock import local_now
from common.db import q
from notifications import hop_thu
from teaching.nhan_bai import giao_cho
from teaching.vocab import chi_hoc_vien

#: Cửa sổ nhắc: hạn nộp còn từ TU_GIO tới DEN_GIO giờ nữa.
TU_GIO, DEN_GIO = 20, 28
LOAI = 'nhac_han'
LINK = '/bai-tap'

_NGUON = '''
      FROM assignments a
      JOIN classes c ON c.id = a.class_id
      JOIN class_members m ON m.class_id = a.class_id AND m.left_at IS NULL
      JOIN users u ON u.id = m.user_id
      LEFT JOIN notification_settings ns ON ns.user_id = u.id
     WHERE a.status = 'open' AND a.kind <> 'kiem_tra' AND c.status = 'active'
       AND a.due_at > %(tu)s AND a.due_at <= %(den)s
       AND ''' + chi_hoc_vien('u') + ' AND ' + giao_cho('a', 'u.id') + '''
       AND coalesce(ns.study_remind, 1) = 1
       AND coalesce(u.status, 'active') <> 'suspended'
       AND NOT EXISTS (SELECT 1 FROM submissions s
                        WHERE s.assignment_id = a.id AND s.user_id = u.id
                          AND s.submitted_at IS NOT NULL)'''

_TIEU_DE = "'Sắp hết hạn nộp: ' || a.title"
_NOI_DUNG = ("'Bài \"' || a.title || '\" của lớp ' || c.name || ' hết hạn lúc ' "
             "|| to_char(a.due_at, 'HH24:MI DD/MM') || '. Bạn chưa nộp bài này.'")


def quet(bay_gio=None):
    """Một lượt quét. Trả số chuông MỚI (lời nhắc đã có thì không tính)."""
    bay_gio = bay_gio or local_now()
    ts = {'tu': bay_gio + timedelta(hours=TU_GIO), 'den': bay_gio + timedelta(hours=DEN_GIO),
          'loai': LOAI, 'link': LINK, 'uu_tien': hop_thu.HANG_LOAT}
    with transaction.atomic():
        moi = q('''INSERT INTO notifications (user_id, type, title, body, ref_type, ref_id, link)
                   SELECT DISTINCT u.id, %(loai)s, ''' + _TIEU_DE + ', ' + _NOI_DUNG + ''',
                          'assignment', a.id, %(link)s ''' + _NGUON + '''
                   ON CONFLICT (user_id, ref_type, ref_id) WHERE type = 'nhac_han' DO NOTHING
                   RETURNING id''', ts)
        q('''INSERT INTO outbox (channel, user_id, to_addr, subject, body, source_type,
                                      source_id, dedup_key, priority)
                   SELECT DISTINCT 'email', u.id, u.email, ''' + _TIEU_DE + ', ' + _NOI_DUNG + '''
                          || E'\\n\\nXem và nộp bài ở mục "Bài tập" trên TopHSA.\\n\\n— TopHSA\\n',
                          'assignment', a.id, 'nhac_han:' || a.id || ':' || u.id,
                          %(uu_tien)s ''' + _NGUON + '''
                     AND coalesce(ns.email_notif, 1) = 1 AND NOT u.is_demo
                     AND u.email IS NOT NULL AND u.email LIKE '%%@%%'
                   ON CONFLICT (dedup_key) DO NOTHING
                   RETURNING id''', ts)
    # Thư nằm trong hộp thư đi; `hop_thu.nhip` gửi ngay sau lượt quét này.
    return len(moi)
