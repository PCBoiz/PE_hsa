"""Test cơ bản app leaderboard (0-test ở bản Flask)."""
import pytest

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('lb_type,unit', [('weekly', 'XP'), ('streak', 'ngày'), ('friends', 'XP')])
def test_leaderboard_types(auth_api, lb_type, unit):
    res = auth_api.get(f'/api/leaderboard?type={lb_type}')
    assert res.status_code == 200
    data = res.json()
    assert data['type'] == lb_type
    assert data['unit'] == unit
    assert isinstance(data['entries'], list)
    assert data['me'] is not None


def test_leaderboard_invalid_type_400(auth_api):
    assert auth_api.get('/api/leaderboard?type=bogus').status_code == 400


def test_requires_auth(api, db):
    assert api.get('/api/leaderboard').status_code == 401


# ── Chỉ HỌC VIÊN lên bảng (14/09/2026) ─────────────────────────────────────────
#
# Đo trên production cùng ngày: tab "Streak" mà một học viên nhìn thấy có
# "Quản trị viên" đứng HẠNG 1 và "Ha Thai Son" (giảng viên) hạng 5 — hai truy
# vấn xếp hạng lấy MỌI tài khoản. Học viên đua với XP do nhân viên bấm thử, và
# tên nhân viên hiện trong một bảng dành cho học viên. Cùng lớp lỗi mà
# `teaching.vocab.chi_hoc_vien` sinh ra để chặn ở sĩ số lớp (31/08).
#
# CSDL là bảng THẬT dùng chung, nên các giá trị dựng ở đây cố ý RẤT LỚN để hai
# tài khoản thử chắc chắn nằm trong top 10, và phép so chỉ hỏi về ĐÚNG hai id
# này — không đếm tổng.

from datetime import timedelta  # noqa: E402

from accounts.models import User  # noqa: E402
from common.clock import local_today  # noqa: E402
from common.db import q1, x  # noqa: E402
from common.permissions import ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER  # noqa: E402

RAT_LON = 10 ** 8


def _tao(ten, vai, streak=0):
    return q1("INSERT INTO users (name, email, password, role, streak) "
              "VALUES (%s, %s, 'x', %s, %s) RETURNING id",
              (ten, ten.replace(' ', '.').lower() + '_lb_tmp@example.com', vai, streak))['id']


def _ids(res):
    return {e['id'] for e in res.json()['entries']}


@pytest.fixture
def hai_nguoi():
    """Một quản trị viên và một học viên, cả hai điểm RẤT cao, tên thật."""
    qt = _tao('Nguyen Quan Tri Bang', ROLE_ADMIN, streak=RAT_LON + 5)
    hv = _tao('Tran Hoc Vien Bang', ROLE_STUDENT, streak=RAT_LON)
    dau_tuan = local_today() - timedelta(days=local_today().weekday())
    for uid, xp in ((qt, RAT_LON + 5), (hv, RAT_LON)):
        x("INSERT INTO user_daily_xp_logs (user_id, log_date, xp_earned) VALUES (%s, %s, %s)",
          (uid, dau_tuan, xp))
    return {'qt': qt, 'hv': hv}


def _xem_bang(api, uid, loai):
    api.force_authenticate(user=User.objects.get(id=uid))
    return api.get(f'/api/leaderboard?type={loai}')


@pytest.mark.parametrize('loai', ['weekly', 'streak'])
def test_nhan_vien_khong_len_bang(api, hai_nguoi, loai):
    res = _xem_bang(api, hai_nguoi['hv'], loai)
    assert res.status_code == 200, res.json()
    ids = _ids(res)
    assert hai_nguoi['hv'] in ids, 'học viên điểm rất cao phải có mặt trong top'
    assert hai_nguoi['qt'] not in ids, 'quản trị viên KHÔNG được lên bảng của học viên'


@pytest.mark.parametrize('loai', ['weekly', 'streak'])
def test_hang_cua_em_khong_tinh_nhan_vien(api, hai_nguoi, loai):
    """Quản trị viên điểm cao hơn em 5 — nếu còn đếm nhân viên thì em hạng 2."""
    me = _xem_bang(api, hai_nguoi['hv'], loai).json()['me']
    assert me['id'] == hai_nguoi['hv'] and me['rank'] == 1, me


@pytest.mark.parametrize('loai', ['weekly', 'streak', 'friends'])
def test_nhan_vien_xem_bang_thi_khong_co_hang_cua_minh(api, hai_nguoi, loai):
    """Nhân viên mở Trang của tôi vẫn thấy bảng, nhưng không có "Vị trí của bạn"."""
    res = _xem_bang(api, hai_nguoi['qt'], loai)
    assert res.status_code == 200, res.json()
    assert res.json()['me'] is None
    assert hai_nguoi['qt'] not in _ids(res)


def test_ban_be_khong_xep_nhan_vien(api, hai_nguoi):
    """Học viên theo dõi một giảng viên ở diễn đàn — giảng viên không vào bảng Bạn bè."""
    gv = _tao('Le Giang Vien Bang', ROLE_TEACHER)
    x("UPDATE users SET xp=%s WHERE id=%s", (RAT_LON, gv))
    x("INSERT INTO user_follows (follower_id, followee_id) VALUES (%s, %s)", (hai_nguoi['hv'], gv))
    res = _xem_bang(api, hai_nguoi['hv'], 'friends')
    assert gv not in _ids(res)
    assert hai_nguoi['hv'] in _ids(res)


def test_ba_tab_che_ten_cung_mot_cach(api, db):
    """Tab tuần hiện tên THÔ còn tab streak che tên kiểu tài khoản thử — hai tab
    của cùng một bảng không được nói hai cách về cùng một người."""
    uid = _tao('test user bang', ROLE_STUDENT, streak=RAT_LON)
    dau_tuan = local_today() - timedelta(days=local_today().weekday())
    x("INSERT INTO user_daily_xp_logs (user_id, log_date, xp_earned) VALUES (%s, %s, %s)",
      (uid, dau_tuan, RAT_LON))
    ten = {}
    for loai in ('weekly', 'streak', 'friends'):
        d = _xem_bang(api, uid, loai).json()
        e = next(e for e in d['entries'] if e['id'] == uid)
        ten[loai] = e['name']
        ten[loai + '.me'] = d['me']['name']
    # Cả ba tab, cả dòng trong bảng lẫn khối "Vị trí của bạn": một cách che.
    assert set(ten.values()) == {f'Học viên #{uid}'}, ten
