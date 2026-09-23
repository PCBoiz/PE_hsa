"""Cây tuyến CHỈ DÀNH CHO PHÉP KIỂM: tuyến thật + các tuyến thi đã tháo (1.5A).

── VÌ SAO CÓ TỆP NÀY (24/09/2026) ─────────────────────────────────────────

Bỏ thi pha A tháo tuyến của `mockexam` và của nhập kết quả thi (`ket-qua-thi`)
khỏi `config/urls.py`, nhưng GIỮ mã — pha A phải đảo ngược được bằng một dòng.
Mã còn đó mà phép kiểm của nó chết (404 hết) thì hai tuần sau bật lại là bật
một đống mã không ai canh. Nên phép kiểm cũ của hai chỗ ấy đổi sang cây tuyến
này bằng `pytestmark = pytest.mark.urls('config.urls_thi_da_thao')` — không sửa
một dòng khẳng định nào.

KHÔNG ai trong sản phẩm nạp tệp này: `ROOT_URLCONF` vẫn là `config.urls`, và
`scripts/ban_do.mjs` chỉ tính `urls.py` được gắn từ gốc. Pha C xoá mã thi thì
xoá luôn tệp này.
"""
from django.urls import include, path

from config.urls import urlpatterns as _tuyen_that
from teaching import nhap_ket_qua_view

urlpatterns = [
    *_tuyen_that,
    path('', include('mockexam.urls')),
    path('api/teach/classes/<int:class_id>/ket-qua-thi/doc',
         nhap_ket_qua_view.DocKetQuaThiView.as_view()),
    path('api/teach/classes/<int:class_id>/ket-qua-thi/ghi',
         nhap_ket_qua_view.GhiKetQuaThiView.as_view()),
]
