"""ĐO số chặng proxy thật — thứ duy nhất còn thiếu để đóng T38 và T66.

Hai mục ấy mắc ở CÙNG một con số: ``NUM_PROXIES``. Đặt sai theo chiều này thì
hàng rào tần suất vô hiệu (người gọi tự đặt ``X-Forwarded-For`` là mỗi request
một khoá throttle mới — đo 31/08/2026: 300 lần đăng nhập, 300 lần lọt) và cột
``ip`` của nhật ký kiểm toán giả mạo được. Đặt sai theo chiều KIA còn tệ hơn:
mọi người dùng dồn vào chung một khoá, và một em gõ sai mật khẩu khoá cả lớp.

Con số ấy phải ĐO, không đoán — mà chỉ đo được TRÊN PRODUCTION, vì nó là số
chặng Vercel + Render thật sự thêm vào. Trên máy dev mọi dòng đều là ``::1``.

Đường này để anh Sơn đo bằng một lần bấm, thay vì phải tự dựng cách đo:

  1. Deploy xong, mở ``/api/admin/do-proxy`` bằng TRÌNH DUYỆT (đi đường Vercel).
  2. Mở lại chính nó bằng ``curl`` THẲNG vào ``pe-hsa-backend.onrender.com``.
  3. So hai kết quả: ``soChang`` ở lượt (1) chính là ``NUM_PROXIES``.
     Ở lượt (2), ``xff`` sẽ ngắn hơn — đó là đường mà kẻ gọi thẳng đi qua.

CHỈ QUẢN TRỊ VIÊN, và chỉ trả về HEADER LIÊN QUAN TỚI PROXY. Không trả toàn bộ
``request.META``: trong đó có biến môi trường của tiến trình.
"""
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminRole


class DoProxyView(APIView):
    """GET /api/admin/do-proxy — xem máy chủ NHÌN THẤY gì về chuỗi proxy."""
    permission_classes = [IsAdminRole]

    def get(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR') or ''
        chang = [p.strip() for p in xff.split(',') if p.strip()]
        return Response({
            'xff': xff,
            'chang': chang,
            # Số chặng proxy = số phần tử TRỪ chính máy khách.
            'soChang': max(0, len(chang) - 1),
            'remoteAddr': request.META.get('REMOTE_ADDR'),
            'proto': request.META.get('HTTP_X_FORWARDED_PROTO'),
            'host': request.META.get('HTTP_X_FORWARDED_HOST'),
            'huongDan':
                'Mở đường này BẰNG TRÌNH DUYỆT (qua Vercel) và bằng curl THẲNG '
                'vào Render, rồi so `chang`. `soChang` của lượt qua trình duyệt '
                'chính là NUM_PROXIES. Đặt xong thì vá nốt `_client_ip` trong '
                'common/audit.py (T66) cho khớp — hai chỗ phải chỉ vào CÙNG một '
                'phần tử, lệch nhau là hàng rào tần suất và nhật ký kiểm toán '
                'ghi hai IP khác nhau cho cùng một request.',
        })
