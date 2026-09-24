"""Mặt tiền GỬI THÔNG BÁO dùng chung (kế hoạch v2, Ngày 0 — 25/09/2026).

Ba luồng làm song song (A vận hành lớp, B trung tâm thông báo, C hộp "Yêu cầu") đều cần
"báo cho những người này, kèm email nếu họ bật". Nếu mỗi luồng tự viết như
`teaching/bao_doi_lich.py` (vòng `notify()` + đọc `notification_settings` + luồng rời gửi
thư) thì luồng B phải sửa ba nơi khi chuyển sang hộp thư đi (outbox, §61). Nên A và C CHỈ
gọi hàm ở đây; B thay RUỘT hàm (ghi outbox trong cùng giao dịch) mà không đổi chữ ký.

Bản đầu (hôm nay) làm đúng như `bao_doi_lich`: chuông qua `notify()` (có gộp 10 phút),
thư trên luồng rời — thư lỗi chỉ ghi log, mất khi worker khởi động lại. Đó là lý do có §61.

Tôn trọng `notification_settings.email_notif` (không có dòng = bật, như `bao_doi_lich`).
KHÔNG BAO GIỜ ném lỗi: báo không được thì việc chính vẫn phải xong.
"""
import logging
import threading

from django.db import transaction

from common import mail
from common.db import q
from notifications.service import COALESCE_MINUTES, notify

log = logging.getLogger(__name__)

#: Phép kiểm đặt True để gửi thư ĐỒNG BỘ (đọc được kết quả ngay sau lời gọi).
GUI_NGAY = False

CHAN_THU = '\n\n— TopHSA\n'


def _gui_thu(ds, tieu_de, chu):
    for den in ds:
        ok, _, loi = mail.gui(den, tieu_de, chu)
        if not ok:
            log.warning('[thong_bao] không gửi được thư "%s": %s', tieu_de, loi)


def gui(user_ids, loai, tieu_de, noi_dung, ref=(None, None), email=False,
        gop_phut=COALESCE_MINUTES):
    """Báo cho từng người trong ``user_ids``. Trả số người được báo chuông.

    loai       — `notifications.type` (vd 'yeu_cau_moi'); bộ lọc chuông dựa vào nó.
    ref        — (ref_type, ref_id) để bấm chuông mở đúng chỗ; `ref_id` là INTEGER.
    email      — True: gửi thêm thư cho người có email và bật `email_notif`.
    gop_phut   — gộp với thông báo CHƯA ĐỌC cùng (loai, ref) trong ngần ấy phút (0 = không gộp).

    Gọi TRONG một giao dịch sắp ghi? Dùng `gui_sau_commit` — không thì giao dịch cuộn lại
    mà người nhận vẫn đã nhận thư về một việc không xảy ra.
    """
    try:
        ids = sorted({int(u) for u in user_ids or () if u})
        if not ids:
            return 0
        ref_type, ref_id = ref
        for uid in ids:
            notify(uid, loai, tieu_de, noi_dung, ref_type, ref_id, coalesce_minutes=gop_phut)
        if email:
            nguoi = q('''SELECT u.email FROM users u
                         LEFT JOIN notification_settings ns ON ns.user_id = u.id
                         WHERE u.id = ANY(%s) AND u.email IS NOT NULL AND u.email <> ''
                           AND coalesce(ns.email_notif, 1) = 1''', (ids,))
            thu = [r['email'] for r in nguoi]
            if thu:
                chu = (noi_dung or tieu_de) + CHAN_THU
                if GUI_NGAY:
                    _gui_thu(thu, tieu_de, chu)
                else:
                    threading.Thread(target=_gui_thu, args=(thu, tieu_de, chu), daemon=True).start()
        return len(ids)
    except Exception:            # noqa: BLE001 — báo không được không chặn việc chính
        log.exception('[thong_bao] không báo được "%s"', loai)
        return 0


def gui_sau_commit(*args, **kwargs):
    """Như `gui`, nhưng chỉ chạy khi giao dịch bao quanh COMMIT (ngoài giao dịch: chạy ngay)."""
    transaction.on_commit(lambda: gui(*args, **kwargs))
