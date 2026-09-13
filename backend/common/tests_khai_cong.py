"""Mọi view `api/` phải KHAI cổng phân quyền — không được dựa vào mặc định của khung.

── VÌ SAO (13/09/2026) ─────────────────────────────────────────────────────

`REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = [IsAuthenticated]`, nên một view
không khai gì vẫn đòi đăng nhập. Mặc định ấy ĐÚNG — nhưng nó là chỗ nguy hiểm
nhất của cả tầng phân quyền, vì hai lý do:

  1. Một view mới quên khai sẽ mở cho MỌI người đã đăng nhập, IM LẶNG. Không
     lỗi, không cảnh báo, trông y hệt một quyết định có chủ ý — cho tới ngày
     một học viên đọc được bảng điểm của lớp khác.
  2. Ai đó "dọn" cấu hình rồi bỏ dòng mặc định ấy đi (một dòng, trong một tệp
     không ai mở) thì 60 view cùng lúc thành công khai.

Đo 13/09/2026: **60/107** view đang dựa vào mặc định. Phép kiểm này bắt mọi view
phải nói rõ mình muốn gì — kể cả khi câu trả lời chỉ là "phải đăng nhập".

── "KHAI" NGHĨA LÀ GÌ ─────────────────────────────────────────────────────

`permission_classes` nằm trong `__dict__` của chính lớp view, HOẶC của một lớp
cha DO DỰ ÁN VIẾT (`AdminBase`, `NguoiDungView`…) — tức bất kỳ lớp nào trong
MRO đứng TRƯỚC `APIView`. Kế thừa từ `APIView` rồi thôi thì KHÔNG tính: đó chính
là "dựa vào mặc định".

Bộ kiểm kê `scripts/kiem_ke_san_pham.py` bản đầu đếm bằng `vars(cls)` nên báo
71 thay vì 60 — nó đếm cả 11 view khai qua `AdminBase`. Cùng một sai lầm, ở hai
chỗ, là lý do logic này nằm ở MỘT hàm dùng chung dưới đây.
"""
from django.urls import get_resolver
from rest_framework.views import APIView

from common.views import da_khai_cong


def cac_view_api():
    ra = []
    for m in get_resolver().url_patterns:
        for p in getattr(m, 'url_patterns', [m]):
            duong = str(getattr(p, 'pattern', ''))
            cls = getattr(getattr(p, 'callback', None), 'cls', None)
            if cls is not None and duong.startswith('api/'):
                ra.append((duong, cls))
    return ra


def test_moi_view_api_deu_tu_khai_cong():
    chua = sorted({'%s (%s.%s)' % (duong, cls.__module__, cls.__name__)
                   for duong, cls in cac_view_api() if not da_khai_cong(cls)})
    assert not chua, (
        '%d view đang dựa vào mặc định của khung thay vì tự khai cổng. Kế thừa '
        '`common.views.NguoiDungView` (phải đăng nhập, dữ liệu của chính mình) '
        'hoặc khai `permission_classes` rõ ràng:\n  ' % len(chua) + '\n  '.join(chua))


def test_da_khai_cong_khong_bi_lua_boi_APIView():
    """`APIView` của DRF cũng có `permission_classes` trong `__dict__` — chính là
    dòng đọc từ settings. Hàm kiểm phải DỪNG trước nó, nếu không mọi view đều
    'đã khai' và phép kiểm trên thành hằng đúng."""
    class Tran(APIView):
        pass
    assert da_khai_cong(Tran) is False

    class Khai(APIView):
        permission_classes = []
    assert da_khai_cong(Khai) is True

    class ChaDuAn(APIView):
        permission_classes = []

    class Con(ChaDuAn):
        pass
    assert da_khai_cong(Con) is True
