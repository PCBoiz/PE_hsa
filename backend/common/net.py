"""IP của máy khách — nơi DUY NHẤT trả lời câu hỏi "request này đến từ đâu".

VÌ SAO CẦN MỘT CỬA. Trước 04/09/2026 câu hỏi này có HAI câu trả lời chạy song
song, và chúng chọn hai đầu ĐỐI NGHỊCH của cùng một chuỗi:

  · hàng rào tần suất dùng ``get_ident`` của DRF → phần tử **CUỐI**;
  · nhật ký kiểm toán dùng ``audit._client_ip`` → phần tử **ĐẦU**.

Nên cùng một request bị chặn vì IP này lại được ghi vào sổ dưới IP kia. Đó là
kiểu hỏng tệ nhất của một nhật ký kiểm toán: nó vẫn đầy đủ, vẫn khớp định dạng,
và chỉ sai ở chỗ không ai nghĩ tới việc đối chiếu.

── PHẦN TỬ NÀO LÀ ĐÚNG, VÀ VÌ SAO ────────────────────────────────────────────

``X-Forwarded-For`` là một chuỗi mà **mỗi proxy nối thêm vào cuối**. Khách gửi
gì cũng được; các chặng sau đó chỉ nối, không xoá. Nên:

    <phần khách tự bịa, tuỳ ý>, <ip do chặng 1 thấy>, <ip do chặng 2 thấy>, …

Phần tử ĐẦU là thứ khách tự viết. Phần tử thứ ``n`` tính TỪ CUỐI là thứ chặng
tin cậy thứ ``n`` nhìn thấy — nên với ``NUM_PROXIES`` chặng tin cậy, câu trả lời
đúng là ``addrs[-NUM_PROXIES]``. Đây cũng đúng công thức của DRF; giữ nguyên nó
có chủ đích, để hai bên không thể lệch.

Đo 04/09/2026 (``SimpleRateThrottle.get_ident`` với ``RequestFactory`` thật, IP
khách thật là 203.0.113.9):

    kịch bản                      None(cũ)   =0          =1          =2
    gọi thẳng, GIẢ 1 chặng        9.9.9.9    203.0.113.9 9.9.9.9     9.9.9.9
    qua 1 proxy, khách GIẢ thêm   9.9.9.9    <ip proxy>  203.0.113.9 9.9.9.9

Hai điều rút ra, và điều thứ hai **sửa lại bảng cũ trong `docs/VIEC_CUA_ANH.md`
§A2** (bảng ấy ghi ``=1`` cho ra IP thật ở dòng "gọi thẳng" — sai):

1. ``=1`` KHÔNG bảo vệ một lời gọi thẳng không qua proxy: phần tử cuối lúc ấy
   vẫn do khách đặt. Nó đúng trên production vì **không gì tới được Django mà
   không qua tầng biên của Render**, và chính tầng ấy nối IP thật vào cuối.
2. Trên máy dev thì KHÔNG có chặng nào, nên ``0`` mới là con số đúng ở đó —
   ``REMOTE_ADDR`` không giả được. Vì thế mặc định ở đây theo môi trường chứ
   không phải một hằng số duy nhất.

── ĐƯỜNG QUA VERCEL: MỘT HEADER RIÊNG, CÓ BÍ MẬT (vá 05/09/2026) ─────────────

Trước bản vá này, MỌI người dùng thật gộp chung MỘT xô. Lớp trung gian
``src/lib/proxy.ts`` cố ý gỡ ``x-forwarded-for`` của khách — đúng, vì để nguyên
thì trình duyệt tự đặt được khoá giới hạn (đo 30/08: 300 lần đăng nhập kèm XFF
ngẫu nhiên thì **300 lần đều lọt**). Nhưng ``fetch`` của Node không thêm lại,
nên Django chỉ thấy IP egress của Vercel. Với trần 5 lượt đăng nhập/phút, người
thứ sáu bị chặn dù ngồi ở đầu kia đất nước — hàng rào chống vét cạn trở thành
máy sinh sự cố cho một lớp 30 em vào học cùng giờ.

``NUM_PROXIES`` KHÔNG sửa được: nó chọn một phần tử trong chuỗi, mà chuỗi ấy
không còn IP khách nào để chọn.

Cách vá: ``proxy.ts`` gửi IP khách trong một header RIÊNG, kèm một bí mật dùng
chung. Django chỉ tin header ấy khi bí mật khớp.

    X-PE-Client-IP     — IP khách, do CHÍNH VERCEL tính, không phải khách gửi
    X-PE-Proxy-Secret  — bí mật, đặt ở cả Vercel lẫn Render

VÌ SAO PHẢI CÓ BÍ MẬT: Render vẫn nhận request gọi THẲNG, không qua Vercel.
Không có bí mật thì bất kỳ ai cũng đặt được ``X-PE-Client-IP`` — tức mở lại đúng
cái lỗ vừa bịt, chỉ đổi tên header.

AN TOÀN KHI CHƯA CẤU HÌNH: thiếu bí mật ở một trong hai đầu thì hàm này rơi về
đúng hành vi cũ. Một bản vá an ninh mà cấu hình sai thành mở toang là bản vá tệ
hơn không vá; ở đây cấu hình sai chỉ đưa về nguyên trạng.
"""
import hmac
from django.conf import settings


#: Header do `src/lib/proxy.ts` đặt. Tiền tố `X-PE-` để không đụng header chuẩn
#: nào, và để đọc log là biết ngay nó của mình.
_H_IP = 'HTTP_X_PE_CLIENT_IP'
_H_BI_MAT = 'HTTP_X_PE_PROXY_SECRET'


def _so_chang():
    """Số chặng proxy TIN CẬY. Đọc từ settings để chỉ có một chỗ khai."""
    return getattr(settings, 'NUM_PROXIES', 0) or 0


def _bi_mat_khop(meta):
    """Header IP riêng có đáng tin không?

    Chưa cấu hình bí mật → luôn False, tức rơi về hành vi cũ. Đó là mặc định
    ĐÓNG: một chỗ triển khai quên đặt biến môi trường thì mất tính năng tách xô,
    chứ không mở đường cho ai giả IP.

    Bí mật ngắn hơn 16 ký tự coi như CHƯA CÓ: một chuỗi bốn ký tự đặt vội "cho
    chạy được" là thứ đoán ra trong vài giây, mà nó bật một đường tin cậy.

    So bằng ``hmac.compare_digest``: so bằng ``==`` rò rỉ độ dài tiền tố khớp
    qua thời gian chạy, và đây là thứ chạy trên MỌI request.
    """
    mong = getattr(settings, 'PROXY_SHARED_SECRET', '') or ''
    if len(mong) < 16:
        return False
    return hmac.compare_digest(str(meta.get(_H_BI_MAT) or ''), str(mong))


def client_ip(request, gioi_han=60):
    """IP máy khách, hoặc ``None`` khi không xác định được.

    ``gioi_han`` cắt chuỗi cho vừa cột ``admin_audit.ip``. Cắt ở đây chứ không ở
    bên gọi: một IPv6 dài bị cắt khác nhau ở hai chỗ là hai chuỗi khác nhau, và
    khi đó việc gộp về một cửa lại thành công cốc.
    """
    if request is None:
        return None
    meta = getattr(request, 'META', None) or {}

    # ƯU TIÊN header riêng đã ký — đây là đường của MỌI người dùng thật (qua
    # Vercel). Chỉ tin khi bí mật khớp; xem phần đầu tệp.
    if _bi_mat_khop(meta):
        ip = (meta.get(_H_IP) or '').strip()
        # Lấy phần tử ĐẦU nếu proxy lỡ gửi cả chuỗi: giá trị này do Vercel tính,
        # không phải chuỗi khách nối thêm, nên phần tử đầu mới là IP khách.
        ip = ip.split(',')[0].strip()
        if ip:
            return ip[:gioi_han]

    # `request.headers` chỉ có ở Django >= 2.2 và ở `HttpRequest`; DRF bọc lại
    # nhưng vẫn chuyển tiếp. Đọc META để chạy được với mọi thứ giống-request.
    xff = meta.get('HTTP_X_FORWARDED_FOR')
    n = _so_chang()
    if n > 0 and xff:
        dia = [p.strip() for p in xff.split(',') if p.strip()]
        if dia:
            return dia[-min(n, len(dia))][:gioi_han]
    addr = meta.get('REMOTE_ADDR')
    return addr[:gioi_han] if addr else None
