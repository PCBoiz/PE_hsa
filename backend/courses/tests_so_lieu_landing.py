"""Số trên trang giới thiệu phải KHỚP CSDL — nói sai ở đây là nói sai với khách.

Chạy trên DB thật, mọi thứ nằm trong giao dịch được CUỘN LẠI (xem `conftest.py`).

── VÌ SAO CÓ TỆP NÀY (07/09/2026) ───────────────────────────────────────────

Trang giới thiệu trước hôm nay để hai ô số là `—` rồi đợi `landing.inline.js`
gọi `/api/public/courses` điền vào. Hôm ấy backend trả 503, và anh Sơn chụp lại
đúng cảnh trang chủ hiện **"— Bài học"**.

Một trang bán hàng không được phụ thuộc API sống để nói mình có bao nhiêu bài:
con số ấy chỉ đổi khi có người SOẠN THÊM BÀI — vài tháng một lần, không phải dữ
liệu thời gian thực. Nay số dựng sẵn trong HTML, và JS chỉ làm mới khi API sống.

Nhưng số dựng sẵn thì TRÔI ĐƯỢC: ai soạn thêm một khoá mà quên sửa `page.tsx`
thì trang chủ nói sai với khách, và không có gì kêu lên. Phép kiểm này là thứ
kêu lên.

── VÌ SAO ĐỌC TỆP .tsx TỪ PYTHON ────────────────────────────────────────────

Con số cần đối chiếu nằm ở HAI TẦNG KHÁC NHAU: HTML của Next và bảng của
Postgres. Không phép kiểm nào ở một tầng thấy được cả hai. Bên có CSDL là bên
Python, nên nó đọc sang tệp .tsx — cùng lối `quyen-vai.test.mjs` đọc ngược sang
`permissions.py`.
"""
import io
import re
from pathlib import Path

import pytest

from common.db import q1

GOC = Path(__file__).resolve().parent.parent.parent
TRANG = GOC / 'frontend' / 'src' / 'app' / '(base)' / 'page.tsx'


def _so(id_o):
    """Con số dựng sẵn trong ô thống kê `id_o` của trang giới thiệu."""
    with io.open(TRANG, encoding='utf-8') as fh:
        s = fh.read()
    # `id="…">SỐ<` — bám vào id chứ không bám vào thứ tự thẻ: thêm một ô mới
    # vào giữa thì thứ tự đổi, còn id thì không.
    m = re.search(r'id="%s">\s*(\d+)\s*<' % re.escape(id_o), s)
    return int(m.group(1)) if m else None


@pytest.mark.django_db
def test_so_hop_phan_tren_trang_chu_khop_csdl():
    tren_trang = _so('stat-courses')
    assert tren_trang is not None, 'không đọc được số hợp phần dựng sẵn trong page.tsx'
    that = q1('SELECT count(*) AS n FROM courses')['n']
    assert tren_trang == that, (
        'trang chủ nói %d hợp phần, CSDL có %d. Sửa `id="stat-courses"` trong '
        '`frontend/src/app/(base)/page.tsx`.' % (tren_trang, that))


@pytest.mark.django_db
def test_so_bai_hoc_tren_trang_chu_khop_csdl():
    tren_trang = _so('stat-hours')
    assert tren_trang is not None, 'không đọc được số bài học dựng sẵn trong page.tsx'
    that = q1('SELECT count(*) AS n FROM lessons')['n']
    assert tren_trang == that, (
        'trang chủ nói %d bài học, CSDL có %d. Sửa `id="stat-hours"` trong '
        '`frontend/src/app/(base)/page.tsx`.' % (tren_trang, that))


def test_trang_chu_KHONG_con_loi_chung_thuc_bia():
    """Ba lời khẳng định SAI đã gỡ 07/09/2026 — không được quay lại.

    Bản cũ có "100% — Miễn phí luyện tập cơ bản" (không có gói miễn phí nào; tài
    khoản do trung tâm cấp khi đăng ký học) và HAI trích dẫn học viên chú là
    "trải nghiệm từ nhóm học viên thử nghiệm" / "phản hồi từ nhóm pilot".

    Không có nhóm pilot nào: đo trên CSDL thật ngày ấy là 0 đợt học, 0 buổi,
    0 lượt điểm danh. Đó là lời chứng thực bịa, đặt trên trang nhắm vào phụ
    huynh học sinh lớp 12.

    Phép kiểm này KHÔNG cần CSDL — nó canh một quyết định, không canh một con số.
    """
    with io.open(TRANG, encoding='utf-8') as fh:
        s = fh.read()

    # Bỏ chú thích JSX trước khi tìm: chú thích ở tệp ấy CÓ nhắc lại nguyên văn
    # ba câu sai để người đọc sau biết chuyện gì đã xảy ra — và đó là điều nên
    # giữ. Thứ bị cấm là chúng quay lại phần HIỂN THỊ.
    hien = re.sub(r'\{/\*.*?\*/\}', ' ', s, flags=re.S)

    for cam in ('nhóm pilot', 'học viên thử nghiệm', 'Miễn phí luyện tập',
                'trust-quote', 'testimonial-card'):
        assert cam not in hien, (
            'trang giới thiệu lại có "%s". Trung tâm chưa có khoá nào chạy xong, '
            'nên chưa ai nói được câu nào về việc học ở đây.' % cam)
