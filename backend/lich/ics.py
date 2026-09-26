"""SINH TỆP LỊCH (.ics) cho địa chỉ lịch riêng — §71, 26/09/2026.

Anh Sơn chốt 26/09: đưa lịch học ra ngoài bằng MỘT địa chỉ lịch riêng cho mỗi
người, thay vì nối Google Calendar API. Người dùng dán địa chỉ ấy vào Google
Calendar / Lịch iPhone / Outlook một lần, sau đó ứng dụng lịch tự hỏi lại vài giờ
một lần và mọi thay đổi (dời buổi, học bù, huỷ) tự về máy họ.

── VÌ SAO KHÔNG DÙNG THƯ VIỆN ─────────────────────────────────────────────────

`icalendar` làm đúng chuẩn hơn hẳn bộ này, nhưng tệp mình cần chỉ có VEVENT, và
mỗi gói thêm vào là một thứ phải vá khi có lỗi bảo mật, trên một máy chủ gói rẻ
đã chậm sẵn. Bù lại, ba chỗ dưới đây phải tự làm cho đúng — đều là chỗ mà ứng
dụng lịch KHÔNG báo lỗi, nó chỉ lặng lẽ bỏ qua tệp và người dùng thấy lịch trống:

1. **Kết thúc dòng là CRLF**, không phải LF (RFC 5545 §3.1).
2. **Gấp dòng ở 75 OCTET**, không phải 75 ký tự — chữ Việt có dấu chiếm 2–3 byte
   UTF-8, nên cắt theo ký tự sẽ vượt ngưỡng; mà cắt giữa một ký tự nhiều byte thì
   ra chuỗi hỏng. Bộ này cắt theo byte nhưng không cắt giữa ký tự.
3. **Thoát bốn ký tự** `\\` `;` `,` và xuống dòng. Tên lớp "HSA-01, ca tối" có dấu
   phẩy — không thoát thì `SUMMARY` bị hiểu thành hai giá trị.

── GIỜ GIẤC ────────────────────────────────────────────────────────────────────

`class_sessions.starts_at` lưu giờ Việt Nam không kèm múi. Ở đây đổi sang UTC
(trừ 7 giờ) rồi ghi dạng `...Z`. Làm vậy khỏi phải nhúng khối VTIMEZONE, và vẫn
đúng cho người xem ở múi giờ khác. Việt Nam không có giờ mùa hè từ 1975 nên
khoảng lệch luôn là 7 giờ — không có ca biên nào.

── BUỔI ĐÃ HUỶ ─────────────────────────────────────────────────────────────────

Buổi huỷ vẫn đi theo tệp, mang `STATUS:CANCELLED`. Nếu bỏ hẳn ra, ứng dụng lịch
giữ nguyên bản đã tải lần trước và học viên vẫn thấy buổi ấy trên máy — tới lớp
đúng giờ một buổi không còn tồn tại. Đây là lý do tệp luôn trả CẢ buổi huỷ.
"""
from datetime import datetime, timedelta, timezone

#: Việt Nam = UTC+7, cố định từ 1975 (không có giờ mùa hè).
LECH_GIO = timedelta(hours=7)
#: Buổi không ghi thời lượng thì coi là 60 phút — sự kiện thiếu giờ kết thúc bị
#: một số ứng dụng lịch vẽ thành "cả ngày", che mất các buổi khác trong ngày.
PHUT_MAC_DINH = 60
#: RFC 5545 §3.1: dòng không quá 75 octet (chưa kể CRLF).
TRAN_OCTET = 75
#: Ứng dụng lịch hỏi lại tệp bao lâu một lần. Google thường chỉ tôn trọng ở mức
#: "gợi ý" và tự chọn vài giờ tới một ngày; Apple và Outlook theo sát hơn.
NHIP_HOI_LAI = 'PT2H'


def thoat_chu(s):
    """Thoát bốn ký tự RFC 5545 đòi. Thứ tự quan trọng: gạch chéo ngược TRƯỚC."""
    return (str(s).replace('\\', '\\\\').replace(';', '\\;')
            .replace(',', '\\,').replace('\r\n', '\\n').replace('\n', '\\n'))


def _gap(dong):
    """Gấp một dòng cho vừa 75 octet, không cắt giữa một ký tự nhiều byte.

    Dòng nối bắt đầu bằng đúng một dấu cách (RFC 5545 §3.1) — dấu cách ấy tính
    vào 75 octet của dòng nối, nên phần chữ của dòng sau chỉ còn 74.
    """
    b = dong.encode('utf-8')
    if len(b) <= TRAN_OCTET:
        return [dong]
    ra, dau, tran = [], 0, TRAN_OCTET
    while dau < len(b):
        cuoi = min(dau + tran, len(b))
        # Lùi lại nếu điểm cắt rơi vào giữa một ký tự UTF-8 (byte nối là 10xxxxxx).
        while cuoi < len(b) and (b[cuoi] & 0xC0) == 0x80:
            cuoi -= 1
        ra.append(('' if dau == 0 else ' ') + b[dau:cuoi].decode('utf-8'))
        dau, tran = cuoi, TRAN_OCTET - 1
    return ra


def _utc(t):
    return (t - LECH_GIO).strftime('%Y%m%dT%H%M%SZ')


def _noi_hoc(b):
    """Địa điểm hiện trên lịch: 'Trực tuyến' hay tên phòng. Cùng luật với
    `frontend/src/lib/noiHoc.ts` — chữ hiện cho người dùng phải khớp hai bên."""
    if b.get('mode_hl') == 'online':
        return 'Trực tuyến'
    return b.get('room_hl') or ('Tại trung tâm' if b.get('mode_hl') == 'offline' else None)


def _mo_ta(b):
    phan = []
    if b.get('giang_vien'):
        phan.append('Giảng viên: %s' % b['giang_vien'])
    if b.get('topic'):
        phan.append('Nội dung: %s' % b['topic'])
    if b.get('meeting_url'):
        phan.append('Vào lớp: %s' % b['meeting_url'])
    if b.get('status') == 'cancelled':
        phan.insert(0, 'BUỔI NÀY ĐÃ HUỶ.')
    return '\n'.join(phan)


def _su_kien(b, luc):
    t = b['starts_at']
    het = t + timedelta(minutes=b.get('duration_minutes') or PHUT_MAC_DINH)
    ten = b.get('lop') or 'Buổi học'
    if b.get('topic'):
        ten = '%s — %s' % (ten, b['topic'])
    dong = [
        'BEGIN:VEVENT',
        'UID:buoi-%s@pe-hsa' % b['id'],
        'DTSTAMP:%s' % luc,
        'DTSTART:%s' % _utc(t),
        'DTEND:%s' % _utc(het),
        'SUMMARY:%s' % thoat_chu(ten),
        'STATUS:%s' % ('CANCELLED' if b.get('status') == 'cancelled' else 'CONFIRMED'),
        # Ứng dụng lịch chỉ nhận bản mới khi SEQUENCE lớn hơn bản đang giữ. Lấy số
        # phút kể từ khi buổi được sửa lần cuối làm số thứ tự: mỗi lần sửa là một
        # con số lớn hơn, mà không cần thêm cột đếm vào bảng.
        'SEQUENCE:%d' % int((b.get('updated_at') or t).timestamp() // 60),
    ]
    noi = _noi_hoc(b)
    if noi:
        dong.append('LOCATION:%s' % thoat_chu(noi))
    mo_ta = _mo_ta(b)
    if mo_ta:
        dong.append('DESCRIPTION:%s' % thoat_chu(mo_ta))
    if b.get('meeting_url'):
        dong.append('URL:%s' % thoat_chu(b['meeting_url']))
    dong.append('END:VEVENT')
    return dong


def dung_ics(buoi, ten_lich, luc=None):
    """Dựng nội dung tệp .ics từ danh sách buổi (mỗi buổi là một dict như câu SQL
    của `lich/doc.py` trả về). `luc` chỉ để phép kiểm ghim được giờ."""
    dau = (luc or datetime.now(timezone.utc)).strftime('%Y%m%dT%H%M%SZ')
    dong = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//TopHSA//Lich hoc//VI',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'X-WR-CALNAME:%s' % thoat_chu(ten_lich),
        'X-WR-TIMEZONE:Asia/Ho_Chi_Minh',
        'X-PUBLISHED-TTL:%s' % NHIP_HOI_LAI,
        'REFRESH-INTERVAL;VALUE=DURATION:%s' % NHIP_HOI_LAI,
    ]
    for b in buoi:
        dong += _su_kien(b, dau)
    dong.append('END:VCALENDAR')
    ra = []
    for d in dong:
        ra += _gap(d)
    return '\r\n'.join(ra) + '\r\n'
