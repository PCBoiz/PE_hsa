"""Gửi thư ra ngoài — SMTP, kèm chế độ thử ghi ra tệp `.eml`.

── VÌ SAO EMAIL, VÀ VÌ SAO BÂY GIỜ (07/09/2026) ────────────────────────────

Đặc tả ERP §9 xếp "Thông báo Zalo/email ra ngoài" là việc số 6 và ghi rõ nó
phụ thuộc TopHSA ở đúng một câu: *gửi qua kênh nào*. Anh Sơn đã trả lời — Zalo
ZNS đòi OA đã xác thực, mà xác thực đòi giấy phép kinh doanh; SMS brandname
vướng đúng cái cửa ấy. **Email là kênh duy nhất mở được hôm nay mà không cần
giấy tờ nào.**

── VÌ SAO SMTP GMAIL + APP PASSWORD, KHÔNG PHẢI OAUTH ─────────────────────

App Password là một chuỗi 16 ký tự lấy trong 2 phút, không cần đăng ký ứng
dụng, không cần màn hình đồng ý, không hết hạn theo phiên. OAuth thì phải dựng
luồng uỷ quyền, giữ refresh token, và xử lý lúc nó hết hạn — ba việc chỉ đáng
làm khi gửi dưới danh nghĩa NHIỀU tài khoản. Ở đây chỉ có một hộp thư gửi đi.

Giới hạn phải biết trước: Gmail cho ~500 người nhận/ngày. Với một trung tâm
vài chục học viên thì thoải mái; tới vài trăm thì phải đổi sang dịch vụ gửi
thư chuyên dụng — và lúc ấy chỉ đổi khối `smtplib` trong `gui()`, vì mọi nơi
gọi chỉ thấy giao ước `(ok, dấu_vết, lỗi)`.

── VÌ SAO KHÔNG DÙNG `django.core.mail` ───────────────────────────────────

`send_mail` của Django NÉM ngoại lệ, và cấu hình của nó nằm ở `settings`. Cả
hai đều sai với chỗ này:

  · Đường gửi báo cáo là một VÒNG LẶP cả lớp. Em thứ ba ném ngoại lệ thì 22 em
    còn lại không được gửi, và người bấm nút không biết đã tới đâu. Lỗi phải là
    một GIÁ TRỊ để vòng lặp đi tiếp và ghi vào sổ — đúng giao ước `zalo.py`
    đang dùng, và hai kênh cùng một giao ước thì nơi gọi không phải rẽ nhánh.
  · Đọc biến môi trường mỗi lần gọi, không cache: đổi biến trên Render mà phải
    khởi động lại tiến trình mới có tác dụng là cái bẫy người đổi không biết,
    rồi kết luận "điền rồi mà vẫn không gửi được".

── CHẾ ĐỘ THỬ GHI RA `.eml`, KHÔNG PHẢI IN RA MÀN HÌNH ────────────────────

`.eml` mở được bằng Outlook, Thunderbird, hoặc kéo thẳng vào Gmail. Tức người
duyệt nội dung nhìn thấy ĐÚNG thứ phụ huynh sẽ thấy — cả bố cục HTML, cả tệp
đính kèm — chứ không phải một bản tóm tắt trong terminal. Một bản xem trước
khác với bản gửi thật là thứ nguy hiểm hơn là không có bản xem trước nào.
"""
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path

log = logging.getLogger(__name__)

#: Chờ tối đa cho một lời gọi SMTP. Ngắn có chủ đích — xem `zalo.CHO_GIAY`:
#: đây là lời gọi nằm TRONG vòng lặp gửi cả lớp.
CHO_GIAY = 20


def _thong_so():
    """Đọc cấu hình từ môi trường. Đọc MỖI LẦN GỌI — xem chú thích đầu tệp."""
    return {
        'host': (os.environ.get('EMAIL_HOST') or 'smtp.gmail.com').strip(),
        'port': int((os.environ.get('EMAIL_PORT') or '587').strip() or 587),
        'user': (os.environ.get('EMAIL_USER') or '').strip(),
        'mat_khau': (os.environ.get('EMAIL_APP_PASSWORD') or '').strip(),
        # Tên hiện trong hộp thư người nhận. Gmail luôn ghi đè phần ĐỊA CHỈ về
        # tài khoản đã đăng nhập, nhưng phần TÊN thì giữ — nên đây là chỗ duy
        # nhất nói được "TopHSA" thay vì một địa chỉ gmail cá nhân.
        'ten': (os.environ.get('EMAIL_TU_TEN') or 'TopHSA').strip(),
    }


def che_do_thu() -> bool:
    """`EMAIL_CHE_DO_THU` — đi trọn luồng, ghi `.eml` ra đĩa, KHÔNG gửi thật."""
    v = (os.environ.get('EMAIL_CHE_DO_THU') or '').strip().lower()
    return v in ('1', 'true', 'yes', 'on', 'co', 'có')


def thu_muc_thu() -> Path:
    """Nơi chứa `.eml` của chế độ thử. Ngoài repo để không lỡ tay commit thư
    có dữ liệu học viên thật."""
    return Path(os.environ.get('EMAIL_THU_MUC_THU') or
                (Path(__file__).resolve().parent.parent.parent / '.thu_email'))


def da_cau_hinh() -> bool:
    """Đủ thông số để gửi THẬT chưa. Thiếu MỘT là chưa.

    KHÔNG tính chế độ thử vào đây — cùng lý lẽ với `zalo.da_cau_hinh`: màn
    hình dùng hàm này để nói "email sẵn sàng", và nói sẵn sàng khi chưa có mật
    khẩu là đẩy người dùng đi bấm một nút không gửi được gì.
    """
    t = _thong_so()
    return bool(t['user'] and t['mat_khau'])


def thieu_gi() -> list[str]:
    """Tên biến môi trường còn trống — để màn hình nói ĐÚNG thứ còn thiếu."""
    t = _thong_so()
    ra = []
    if not t['user']:
        ra.append('EMAIL_USER')
    if not t['mat_khau']:
        ra.append('EMAIL_APP_PASSWORD')
    return ra


#: Ký tự chấm dứt dòng trong header thư. `\r` và `\n` là hai ký tự mở ra lỗ
#: CHÈN HEADER: một tiêu đề chứa "\nBcc: ke-trom@..." sẽ thành một header Bcc
#: thật, và báo cáo của một đứa trẻ đi kèm tới một địa chỉ lạ.
#:
#: `\x0b`, `\x0c` và `\u2028`/`\u2029` cũng bị một số bộ phân tích header coi
#: là xuống dòng, nên dọn luôn thay vì chỉ dọn hai ký tự hiển nhiên.
_XUONG_DONG = '\r\n\x0b\x0c\x1c\x1d\x1e\u2028\u2029'


def don_header(v) -> str:
    """Bỏ mọi ký tự xuống dòng khỏi một giá trị sắp đặt vào header thư.

    ── VÌ SAO DỌN CHỨ KHÔNG TỪ CHỐI (07/09/2026) ────────────────────────────

    Tiêu đề thư chứa TÊN HỌC VIÊN, mà tên đến từ CSDL. Từ chối cả lá thư vì
    một cái tên có ký tự lạ nghĩa là một em không bao giờ nhận được báo cáo, và
    người trực không hiểu vì sao. Dọn thì em ấy vẫn nhận, chỉ là tên hiển thị
    mất một ký tự vô hình mà không ai nhìn thấy.

    Với ĐỊA CHỈ người nhận thì ngược lại — xem `gui()`: ở đó một ký tự lạ nghĩa
    là dữ liệu hỏng hoặc có người đang thử chèn, và gửi tới một địa chỉ đã bị
    sửa là gửi nhầm người.
    """
    return ''.join(c for c in ('' if v is None else str(v)) if c not in _XUONG_DONG)


def soan(den: str, tieu_de: str, chu: str, html: str | None = None,
         dinh_kem: tuple = ()) -> EmailMessage:
    """Dựng thư. Dùng CHUNG cho cả gửi thật lẫn chế độ thử.

    Tách ra là có chủ ý, đúng lý do `zalo.soan_zns` tách: bản xem trước tự dựng
    lấy sẽ trôi khỏi bản gửi thật, và khi ấy người duyệt duyệt một thứ KHÁC với
    thứ phụ huynh nhận.

    `dinh_kem` là các bộ `(tên_tệp, kiểu_mime, dữ_liệu_bytes)`.

    Thư luôn có PHẦN CHỮ THUẦN bên cạnh phần HTML. Không phải phép lịch sự với
    quá khứ: bộ lọc rác chấm điểm thấp hơn hẳn thư chỉ có HTML, và thư báo cáo
    học tập rơi vào hộp Spam thì cả đường gửi này vô nghĩa.
    """
    t = _thong_so()
    m = EmailMessage()
    # DỌN mọi giá trị đi vào header. Tiêu đề chứa tên học viên lấy từ CSDL, và
    # `EMAIL_TU_TEN` lấy từ biến môi trường — cả hai đều là chuỗi người khác
    # nhập. `EmailMessage` NÉM `ValueError` khi gặp xuống dòng trong header, mà
    # hàm này nằm giữa một vòng lặp gửi cả lớp: ném ở em thứ ba thì 22 em còn
    # lại không được gửi. Đo được: một tên chứa "\nBcc:" làm hỏng cả lượt.
    m['Subject'] = don_header(tieu_de)
    m['From'] = formataddr((don_header(t['ten']),
                            t['user'] or 'khong-cau-hinh@localhost'))
    m['To'] = den
    # Tự đặt Message-ID chứ không để máy chủ đặt: `smtplib.send_message` KHÔNG
    # thêm trường này, nên không tự đặt thì `gui()` trả về dấu vết rỗng và sổ
    # gửi ghi một ô trống cho mọi lá thư — tức sổ không lần lại được thư nào.
    m['Message-ID'] = make_msgid(domain='tophsa.vn')
    m.set_content(chu)
    if html:
        m.add_alternative(html, subtype='html')

    for ten_tep, kieu, du_lieu in dinh_kem:
        chinh, phu = (kieu.split('/', 1) + ['octet-stream'])[:2]
        m.add_attachment(du_lieu, maintype=chinh, subtype=phu, filename=ten_tep)
    return m


def _ten_tep_thu(den: str, tieu_de: str) -> str:
    """Tên tệp `.eml` an toàn trên mọi hệ tệp.

    Tiêu đề thư có dấu tiếng Việt, dấu hai chấm, dấu gạch chéo — Windows từ
    chối ba thứ sau. Giữ lại chữ và số, còn lại thay bằng gạch dưới.
    """
    tho = '%s-%s' % (den.split('@')[0], tieu_de)
    return ''.join(c if c.isalnum() or c in ' -_' else '_' for c in tho)[:80].strip() + '.eml'


def gui(den: str, tieu_de: str, chu: str, html: str | None = None,
        dinh_kem: tuple = ()) -> tuple[bool, str | None, str | None]:
    """Gửi MỘT thư. Trả `(thành_công, dấu_vết, câu_lỗi)` — KHÔNG ném ngoại lệ.

    `dấu_vết` là `Message-ID` khi gửi thật, hoặc đường dẫn tệp `.eml` khi thử.
    """
    # ĐỊA CHỈ thì TỪ CHỐI chứ không dọn — xem `don_header`. Một ký tự xuống
    # dòng ở đây nghĩa là dữ liệu hỏng hoặc có người đang thử chèn header, và
    # gửi tới một địa chỉ đã bị sửa là gửi báo cáo của một đứa trẻ cho người lạ.
    if not den or '@' not in den or any(c in str(den) for c in _XUONG_DONG):
        return False, None, 'Địa chỉ email người nhận không hợp lệ: %r' % den

    try:
        m = soan(den, tieu_de, chu, html, dinh_kem)
    except (ValueError, TypeError, UnicodeError) as e:
        # LƯỚI CHẶN CUỐI. `don_header` đã dọn những lối đã biết, nhưng hàm này
        # hứa với mọi nơi gọi là "KHÔNG ném ngoại lệ", và một lời hứa như thế
        # chỉ đáng tin khi có chỗ bắt tất cả. Chú thích nói một đằng mà mã làm
        # một nẻo thì chú thích ấy nguy hiểm hơn là không có.
        return False, None, 'Không dựng được lá thư: %s' % e

    if che_do_thu():
        # Tới đây là ĐÃ dựng xong đúng lá thư sẽ gửi. Ghi ra đĩa rồi dừng —
        # không một byte nào rời khỏi máy chủ.
        d = thu_muc_thu()
        d.mkdir(parents=True, exist_ok=True)
        p = d / _ten_tep_thu(den, tieu_de)
        p.write_bytes(bytes(m))
        log.info('Email [CHẾ ĐỘ THỬ] không gửi thật, đã ghi: %s', p)
        return True, 'THU:%s' % p, None

    t = _thong_so()
    if not (t['user'] and t['mat_khau']):
        return False, None, 'Chưa cấu hình email (%s).' % ', '.join(thieu_gi())

    try:
        with smtplib.SMTP(t['host'], t['port'], timeout=CHO_GIAY) as s:
            s.starttls(context=ssl.create_default_context())
            s.login(t['user'], t['mat_khau'])
            s.send_message(m)
    except smtplib.SMTPAuthenticationError:
        # Tách riêng vì đây là lỗi PHỔ BIẾN NHẤT và nó có một nguyên nhân cụ
        # thể mà câu lỗi gốc của Gmail không nói ra: người ta dán mật khẩu
        # Google thường thay vì App Password 16 ký tự.
        return False, None, ('Gmail từ chối đăng nhập. Kiểm tra EMAIL_USER và '
                             'EMAIL_APP_PASSWORD — phải là App Password 16 ký '
                             'tự tạo riêng, KHÔNG phải mật khẩu Google thường.')
    except (smtplib.SMTPException, OSError) as e:
        # Không với tới được KHÁC HẲN bị từ chối: cái đầu đáng thử lại, cái sau
        # thì không. Câu lỗi phải nói rõ để người đọc sổ biết nên làm gì.
        return False, None, 'Không gửi được thư: %s' % e

    return True, m.get('Message-ID') or '', None
