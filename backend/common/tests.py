"""Phép kiểm cho `common/params.py` — tham số URL hỏng không được làm đổ 500.

Tham số trên URL là thứ người dùng gõ được. Đo 31/08/2026: bốn endpoint trả
**500** với `?limit=abc`, `?weeks=abc`, `?days=abc`, `?weeks=1e9`.

`common.params` nhập MUỘN trong từng phép kiểm đơn vị để chúng CHẠY ĐƯỢC trên
mã cũ (nơi tệp ấy chưa tồn tại) — phép kiểm endpoint thì không cần, vì chúng gọi
view chứ không gọi hàm.
"""
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1

f = APIRequestFactory()


def _goi(view, url, ai):
    req = f.get(url)
    force_authenticate(req, user=ai)
    return view.as_view()(req)


@pytest.fixture
def em(db):
    r = q1("INSERT INTO users (name, email, password, streak) "
           "VALUES ('HV Tham So','hv_thamso_tmp@example.com','x',0) RETURNING id")
    return User.objects.get(id=r['id'])


# ── hàm dùng chung ──────────────────────────────────────────────────────────

def test_so_nguyen_nhan_rac_ma_khong_nem():
    from common.params import so_nguyen
    for rac in ('abc', '', '  ', '1e9', '3.5', None, [], {}, 'NaN', '0x10'):
        assert so_nguyen(rac, 12, 4, 52) == 12, rac


def test_so_nguyen_kep_bien():
    from common.params import so_nguyen
    assert so_nguyen('999', 12, 4, 52) == 52
    assert so_nguyen('1', 12, 4, 52) == 4
    assert so_nguyen('-5', 12, 4, 52) == 4
    assert so_nguyen(' 20 ', 12, 4, 52) == 20


def test_so_nguyen_tu_choi_bool():
    """`int(True)` là 1 trong Python; một tham số URL không mang nghĩa ấy."""
    from common.params import so_nguyen
    assert so_nguyen(True, 12, 1, 52) == 12
    assert so_nguyen(False, 12, 1, 52) == 12


def test_so_nguyen_khong_kep_khi_khong_dat_bien():
    from common.params import so_nguyen
    assert so_nguyen('999999', 10) == 999999
    assert so_nguyen('abc', None) is None


# ── bốn endpoint đã đo được 500 ─────────────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize('url', [
    '/api/hsa/gradebook?limit=abc',
    '/api/hsa/gradebook?limit=1e9',
    '/api/hsa/gradebook?limit=-1',
])
def test_so_diem_khong_do_vi_limit_rac(em, url):
    from stats.views import GradebookView
    r = _goi(GradebookView, url, em)
    assert r.status_code == 200, r.status_code


@pytest.mark.django_db
@pytest.mark.parametrize('url', [
    '/api/hsa/progress-curve?weeks=abc',
    '/api/hsa/progress-curve?weeks=1e9',
    '/api/hsa/progress-curve?weeks=0',
])
def test_duong_cong_khong_do_vi_weeks_rac(em, url):
    from stats.views import ProgressCurveView
    r = _goi(ProgressCurveView, url, em)
    assert r.status_code == 200, r.status_code


@pytest.mark.django_db
@pytest.mark.parametrize('url', [
    '/api/hsa/journal?days=abc',
    '/api/hsa/journal?days=1e9',
])
def test_nhat_ky_khong_do_vi_days_rac(em, url):
    from stats.views import JournalView
    r = _goi(JournalView, url, em)
    assert r.status_code == 200, r.status_code


@pytest.mark.django_db
def test_dien_dan_khong_do_vi_phan_trang_rac(em):
    from forum.views import PostsView
    r = _goi(PostsView, '/api/forum/posts?page=abc&per_page=xyz', em)
    assert r.status_code == 200, r.status_code


# ── A13 · quota đường chấm đếm theo NGƯỜI DÙNG, không theo IP ────────────────

@pytest.mark.django_db
def test_quota_duong_cham_tach_theo_tung_hoc_vien_dung_chung_IP(em, db):
    """Cả phòng máy của trung tâm đi ra Internet bằng MỘT địa chỉ NAT. Đếm theo
    IP nghĩa là 30 em chia nhau một quota — mà từ 31/08/2026 phòng luyện gọi
    `/check` 10 lần mỗi bài, nên 30 em × 4 bài/giờ đã vượt trần 1000/giờ.

    Kiểm THẲNG danh tính mà bộ đếm dùng, chứ không bắn 1000 request.
    """
    from common.throttling import HourlyIPThrottle, HourlyUserThrottle
    from lessons.views import CheckAnswersView

    r2 = q1("INSERT INTO users (name, email, password, streak) "
            "VALUES ('HV Hai','hv_hai_tmp@example.com','x',0) RETURNING id")
    em2 = User.objects.get(id=r2['id'])
    view = CheckAnswersView()

    def khoa(lop, ai, ip):
        # Gán thẳng `req.user`: throttle đọc đúng thuộc tính đó. `force_authenticate`
        # chỉ có tác dụng khi request đi qua lớp Request của DRF.
        req = f.post('/x', {}, format='json')
        req.user = ai
        req.META['REMOTE_ADDR'] = ip
        return lop().get_cache_key(req, view)

    # Hai em CÙNG một IP phải có hai bộ đếm khác nhau…
    assert khoa(HourlyUserThrottle, em, '1.1.1.1') != khoa(HourlyUserThrottle, em2, '1.1.1.1')
    # …và một em đổi máy/đổi mạng vẫn là một bộ đếm.
    assert khoa(HourlyUserThrottle, em, '1.1.1.1') == khoa(HourlyUserThrottle, em, '9.9.9.9')
    # Bộ đếm theo IP thì ngược lại — đó chính là lý do không dùng nó ở đây.
    assert khoa(HourlyIPThrottle, em, '1.1.1.1') == khoa(HourlyIPThrottle, em2, '1.1.1.1')


def test_duong_cham_dung_quota_theo_nguoi_dung():
    """Đặt `throttle_classes` trên view là GHI ĐÈ mặc định, không phải bổ sung —
    nên phải kiểm rằng danh sách ấy đúng là bộ theo người dùng."""
    from common.throttling import DailyUserThrottle, HourlyUserThrottle
    from lessons.views import CheckAnswersView
    assert CheckAnswersView.throttle_classes == [DailyUserThrottle, HourlyUserThrottle]
