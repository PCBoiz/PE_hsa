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

── ĐIỀU CÒN CHƯA VÁ, ĐỪNG QUÊN ───────────────────────────────────────────────

Đường đi qua Vercel (tức MỌI người dùng thật) hiện gộp chung MỘT xô: lớp trung
gian ``src/lib/proxy.ts`` cố ý gỡ ``x-forwarded-for`` của khách, và ``fetch``
của Node không thêm lại — nên Django chỉ thấy IP egress của Vercel. Với trần
đăng nhập 5 lượt/phút, người thứ sáu đăng nhập trong cùng một phút bị chặn dù ở
đầu kia đất nước. ``NUM_PROXIES`` KHÔNG sửa được chuyện đó; nó là việc riêng,
xem ``TODO.md``.
"""
from django.conf import settings


def _so_chang():
    """Số chặng proxy TIN CẬY. Đọc từ settings để chỉ có một chỗ khai."""
    return getattr(settings, 'NUM_PROXIES', 0) or 0


def client_ip(request, gioi_han=60):
    """IP máy khách, hoặc ``None`` khi không xác định được.

    ``gioi_han`` cắt chuỗi cho vừa cột ``admin_audit.ip``. Cắt ở đây chứ không ở
    bên gọi: một IPv6 dài bị cắt khác nhau ở hai chỗ là hai chuỗi khác nhau, và
    khi đó việc gộp về một cửa lại thành công cốc.
    """
    if request is None:
        return None
    meta = getattr(request, 'META', None) or {}
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
