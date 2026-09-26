"""BÁO ĐỔI LỊCH — chuông + email cho HỌC VIÊN khi một buổi SẮP TỚI bị dời giờ,
huỷ, đổi phòng, đổi hình thức hay đổi link phòng học (bảng yêu cầu TopHSA, tab
"Nhi" #4). Anh Sơn chốt 23/09/2026: chuông + email cho HỌC VIÊN, KHÔNG gửi phụ
huynh.

── KHI NÀO BÁO, KHI NÀO IM ────────────────────────────────────────────────

  · Buổi ĐÃ DIỄN RA (theo giờ cũ) thì sửa là sửa sổ sách — không báo ai.
  · Sinh lịch cả kỳ hay tạo buổi mới thì KHÔNG báo: đó là lịch mới, em xem ở
    "Lớp của tôi"; báo từng buổi của cả kỳ là ba mươi chuông một lúc.
  · Chỉ báo khi đổi thứ em cần để đi học ĐÚNG: giờ, độ dài, hình thức, phòng,
    link phòng học, hoặc huỷ. Sửa chủ đề hay ghi chú thì không.

── VÌ SAO CHUÔNG VÀ THƯ KHÔNG ĐƯỢC LÀM HỎNG VIỆC CHÍNH ────────────────────

Buổi đã lưu vào CSDL rồi mới báo. Chuông lỗi, SMTP chậm hay sập — giảng viên
vẫn phải thấy "đã lưu". Từ E2 (§61) thư vào HỘP THƯ ĐI cùng giao dịch với chuông
(`notifications/gui.py::xep_thu`), gửi sau commit trên luồng riêng (Gmail mất 1–3
giây mỗi lá); SMTP sập thì thư nằm lại và được thử lại, không còn mất.

Em tắt "Nhận thông báo qua email" ở Cài đặt (`notification_settings.email_notif`)
thì chỉ có chuông, không có thư.
"""
import logging

from django.db import transaction

from common.clock import local_now
from common.db import q
from notifications import hop_thu
from notifications.gui import xep_thu
from notifications.service import notify
from teaching.nguoi_buoi import thuoc_buoi
from teaching.vocab import chi_hoc_vien

log = logging.getLogger(__name__)

#: Cùng số với `sessions.DEFAULT_SESSION_MINUTES`.
PHUT_MAC_DINH = 90

#: Phép kiểm đặt True để gửi thư ĐỒNG BỘ và đọc được `.eml` ngay sau lời gọi.
GUI_NGAY = False


#: Thứ trong tuần, viết như người Việt nói. `weekday()` 0 = thứ Hai.
THU = ('thứ Hai', 'thứ Ba', 'thứ Tư', 'thứ Năm', 'thứ Sáu', 'thứ Bảy', 'Chủ nhật')


def _gio(dt):
    return dt.strftime('%d/%m %H:%M')


def _gio_dep(dt):
    """'thứ Hai 29/09, 10:26' — cách một người nhắn cho người khác.

    `_gio` giữ nguyên cho tiêu đề (ngắn, để không tràn trên điện thoại); chữ
    trong thân thư dùng bản này. Thêm THỨ vì người ta nhớ buổi học theo thứ chứ
    không theo ngày: "thứ Năm tuần này" nghe ra ngay, "02/10" thì phải mở lịch.
    """
    return '%s %s, %s' % (THU[dt.weekday()], dt.strftime('%d/%m'), dt.strftime('%H:%M'))


def _ten(lop):
    """Tên lớp để ghép vào câu. Tên đã bắt đầu bằng 'Lớp' thì không thêm nữa —
    nếu không ra 'Lớp Lớp thử thư 26/09' (đo thật 26/09/2026)."""
    t = (lop.get('name') or '').strip()
    if not t:
        return 'lớp của em'
    return t if t.lower().startswith('lớp') else 'lớp %s' % t


def _noi(buoi, lop):
    """"trực tuyến" / "phòng 201" / "" — theo §53, buổi để trống thì theo lớp."""
    mode = buoi.get('mode') or lop.get('mode')
    room = (buoi.get('room') or lop.get('room') or '').strip()
    if mode == 'online':
        return 'học trực tuyến'
    if mode == 'offline':
        return ('phòng %s' % room) if room else 'học tại trung tâm'
    return ''


def _kieu(truoc, sau, lop):
    """'huy' | 'doi-gio' | 'doi-noi' | None — thay đổi nào ĐÁNG BÁO."""
    if sau is None or (sau['status'] == 'cancelled' and truoc['status'] != 'cancelled'):
        return 'huy'
    if sau['status'] == 'cancelled':
        return None                       # huỷ rồi, sửa tiếp cũng không báo lại
    if (sau['starts_at'] != truoc['starts_at']
            or (sau['duration_minutes'] or PHUT_MAC_DINH) != (truoc['duration_minutes'] or PHUT_MAC_DINH)):
        return 'doi-gio'
    if _noi(sau, lop) != _noi(truoc, lop) or (sau.get('meeting_url') or '') != (truoc.get('meeting_url') or ''):
        return 'doi-noi'
    return None


def bao_doi_lich(truoc, sau, lop):
    """Báo cho mọi em ĐANG HỌC lớp. `truoc`/`sau`: dòng `class_sessions` trước và
    sau khi sửa (`sau=None` là xoá buổi). `lop`: dict có `id`, `name`, `mode`,
    `room`. Trả số em được báo (0 nếu không đáng báo). Không bao giờ ném lỗi."""
    try:
        if truoc['starts_at'] <= local_now():
            return 0
        kieu = _kieu(truoc, sau, lop)
        if not kieu:
            return 0
        ten_lop = lop.get('name') or 'của bạn'
        ten_cau = _ten(lop)          # ghép vào giữa câu, không lặp chữ "Lớp"
        if kieu == 'huy':
            tieu_de = 'Lớp %s: buổi %s đã huỷ' % (ten_lop, _gio(truoc['starts_at']))
            chu = ('Buổi học %s vào %s sẽ không diễn ra. Khi có lịch học bù, '
                   'trung tâm báo em ngay.' % (ten_cau, _gio_dep(truoc['starts_at'])))
        elif kieu == 'doi-gio':
            noi = _noi(sau, lop)
            tieu_de = 'Lớp %s dời buổi %s sang %s' % (ten_lop, _gio(truoc['starts_at']), _gio(sau['starts_at']))
            chu = ('Buổi học %s đổi giờ: thay vì %s như cũ, buổi này bắt đầu lúc %s và '
                   'học trong %d phút%s. Em nhớ vào đúng giờ mới nhé.' % (
                       ten_cau, _gio_dep(truoc['starts_at']), _gio_dep(sau['starts_at']),
                       sau['duration_minutes'] or PHUT_MAC_DINH,
                       (', %s' % noi) if noi else ''))
        else:
            noi = _noi(sau, lop) or 'nơi học mới'
            tieu_de = 'Lớp %s, buổi %s: %s' % (ten_lop, _gio(sau['starts_at']), noi)
            chu = ('Buổi học %s vào %s đổi chỗ: buổi này %s.%s' % (
                ten_cau, _gio_dep(sau['starts_at']), noi,
                (' Link vào lớp: %s' % sau['meeting_url']) if sau.get('meeting_url') else ''))

        ds = q('''SELECT u.id FROM class_members m JOIN users u ON u.id = m.user_id
                   WHERE m.class_id = %s AND m.left_at IS NULL AND ''' + chi_hoc_vien('u')
               # Buổi bù (V-g): chỉ báo các em của buổi ấy, không báo cả lớp.
               + ' AND ' + thuoc_buoi('%s', 'm.user_id'),
               (lop['id'], truoc['id']))
        # Thư mở bằng lời chào, kết bằng lời chúc; CHUÔNG thì để trần vì nó chỉ
        # có một dòng. Anh Sơn 26/09, sau khi đọc thư thật: "văn phong cứng quá"
        # — chữ cũ là "chuyển từ X sang Y (90 phút) · học trực tuyến", đúng
        # nhưng đọc như máy đọc cho máy nghe.
        chu_thu = ('Chào em,\n\n%s\n\n'
                   'Lịch đầy đủ của lớp nằm ở mục "Lớp của tôi" trên TopHSA. '
                   'Có gì chưa rõ, em nhắn lại cho trợ giảng của lớp nhé.\n\n'
                   'Chúc em học tốt,\nTopHSA\n' % chu)
        with transaction.atomic():
            for r in ds:
                notify(r['id'], 'lich_doi', tieu_de, chu, 'class_session', truoc['id'], coalesce_minutes=10)
            # `xep_thu` tự lọc: có email, bật `email_notif`, không phải tài khoản mẫu.
            thu = xep_thu([r['id'] for r in ds], tieu_de, chu_thu, ('class_session', truoc['id']))
            hop_thu.day_di(thu, ngay=GUI_NGAY)
        return len(ds)
    except Exception:            # noqa: BLE001 — báo không được chặn việc chính
        log.exception('[bao_doi_lich] không báo được đổi lịch buổi %s', truoc.get('id'))
        return 0
