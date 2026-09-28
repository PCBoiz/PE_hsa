"""Mặt tiền GỬI THÔNG BÁO dùng chung (kế hoạch v2, Ngày 0 — 25/09/2026; ruột E2 cùng ngày).

Ba luồng làm song song (A vận hành lớp, B trung tâm thông báo, C hộp "Yêu cầu") đều cần
"báo cho những người này, kèm email nếu họ bật". A và C CHỈ gọi hàm ở đây; B (E2) thay
RUỘT mà không đổi chữ ký (chỉ THÊM đối số có mặc định ở cuối).

Ruột từ E2 (§61): chuông qua `notify()` (có gộp 10 phút) VÀ thư vào HỘP THƯ ĐI (`outbox`)
trong CÙNG một giao dịch — hỏng giữa chừng thì không còn chuông nào, không còn thư nào.
Sau commit, `hop_thu.day_di` gửi ngay trên luồng riêng; thư lỗi nằm lại và được thử lại
theo lịch lùi (`notifications/hop_thu.py`) thay vì mất như bản đầu.

Tôn trọng `notification_settings.email_notif` (không có dòng = bật). Tài khoản mẫu
(`users.is_demo`, §49) có chuông, không có thư — địa chỉ của nó là bịa.
KHÔNG BAO GIỜ ném lỗi: báo không được thì việc chính vẫn phải xong.
"""
import logging

from django.db import transaction

from common import (
    mail,  # noqa: F401 — phép kiểm thay `gui.mail.gui` (chính là `common.mail.gui`)
)
from common.db import q, x
from notifications import hop_thu
from notifications.service import COALESCE_MINUTES, notify

log = logging.getLogger(__name__)

#: Phép kiểm đặt True để gửi thư ĐỒNG BỘ (đọc được kết quả ngay sau lời gọi).
GUI_NGAY = False

CHAN_THU = '\n\n— TopHSA\n'


def xep_thu(ids, tieu_de, chu_thu, ref=(None, None), dedup=None, uu_tien=None):
    """Ghi thư vào hộp thư đi cho người trong `ids` có email, bật `email_notif`, không
    phải tài khoản mẫu — MỘT câu INSERT…SELECT. Trả id các thư vừa xếp (dedup trùng thì
    không có). `dedup` là TIỀN TỐ: khoá của từng người = `{dedup}:{user_id}`.

    `uu_tien` (§61a): None = SUY theo số người nhận — một người là thư GIAO DỊCH (người ấy
    đang chờ đúng lá thư này: đơn "Yêu cầu" vừa được duyệt), nhiều người là thư HÀNG LOẠT
    (báo đổi lịch cả lớp) nên chịu trần ngày và đi sau thư giao dịch. Suy chứ không bắt mọi
    nơi gọi khai: luồng A và C chỉ gọi mặt tiền này, và chữ ký của nó không được đổi."""
    ids = list(ids)
    if uu_tien is None:
        uu_tien = hop_thu.GIAO_DICH if len(ids) <= 1 else hop_thu.HANG_LOAT
    return [r['id'] for r in q(
        '''INSERT INTO outbox (channel, user_id, to_addr, subject, body, source_type, source_id,
                               dedup_key, priority)
           SELECT 'email', u.id, u.email, %s, %s, %s, %s,
                  CASE WHEN %s::text IS NULL THEN NULL ELSE %s::text || ':' || u.id END, %s
             FROM users u LEFT JOIN notification_settings ns ON ns.user_id = u.id
            WHERE u.id = ANY(%s) AND u.email IS NOT NULL AND u.email LIKE '%%@%%'
              AND coalesce(ns.email_notif, 1) = 1 AND NOT u.is_demo
            ORDER BY u.id
           ON CONFLICT (dedup_key) DO NOTHING RETURNING id''',
        (tieu_de, chu_thu, ref[0], ref[1], dedup, dedup, uu_tien, ids))]


def gui(user_ids, loai, tieu_de, noi_dung, ref=(None, None), email=False,
        gop_phut=COALESCE_MINUTES, link=None, dedup=None, chu_thu=None, gui_ngay=None):
    """Báo cho từng người trong ``user_ids``. Trả số người được báo chuông.

    loai       — `notifications.type` (vd 'yeu_cau_moi'); bộ lọc chuông dựa vào nó.
    ref        — (ref_type, ref_id) để bấm chuông mở đúng chỗ; `ref_id` là INTEGER.
    email      — True: thêm thư (hộp thư đi) cho người có email và bật `email_notif`.
    gop_phut   — gộp với thông báo CHƯA ĐỌC cùng (loai, ref) trong ngần ấy phút (0 = không gộp).
    link       — đường dẫn trong ứng dụng mở khi bấm chuông (vd '/bai-tap').
    dedup      — tiền tố khoá chống trùng THƯ (`{dedup}:{user_id}`): gọi lại cùng khoá thì
                 không xếp thêm thư (chuông vẫn theo luật gộp của `notify`).
    chu_thu    — thân thư nếu khác nội dung chuông (mặc định: nội dung + chữ ký).
    gui_ngay   — None: theo `GUI_NGAY` của mô-đun.

    Gọi TRONG một giao dịch sắp ghi? Dùng `gui_sau_commit` — không thì giao dịch cuộn lại
    mà người nhận vẫn đã nhận chuông về một việc không xảy ra.
    """
    try:
        ids = sorted({int(u) for u in user_ids or () if u})
        if not ids:
            return 0
        ref_type, ref_id = ref
        with transaction.atomic():
            for uid in ids:
                nid = notify(uid, loai, tieu_de, noi_dung, ref_type, ref_id, coalesce_minutes=gop_phut)
                if link:
                    x('UPDATE notifications SET link = %s WHERE id = %s', (link, nid))
            thu = xep_thu(ids, tieu_de, chu_thu or ((noi_dung or tieu_de) + CHAN_THU),
                          ref, dedup) if email else []
            hop_thu.day_di(thu, ngay=GUI_NGAY if gui_ngay is None else gui_ngay)
        return len(ids)
    except Exception:            # noqa: BLE001 — báo không được không chặn việc chính
        log.exception('[thong_bao] không báo được "%s"', loai)
        return 0


def gui_sau_commit(*args, **kwargs):
    """Như `gui`, nhưng chỉ chạy khi giao dịch bao quanh COMMIT (ngoài giao dịch: chạy ngay)."""
    transaction.on_commit(lambda: gui(*args, **kwargs))
