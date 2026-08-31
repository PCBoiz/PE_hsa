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
