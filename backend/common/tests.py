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
from common.clock import local_today
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


def test_duong_cham_giu_ca_hai_truc_quota():
    """Đặt `throttle_classes` trên view là GHI ĐÈ mặc định, không phải bổ sung.
    Bản đầu chỉ để hai lớp theo người dùng, nên endpoint mất hẳn trần theo MÁY.

    Kiểm bằng cách KHỞI TẠO từng lớp và đọc `rate` — bản cũ chỉ so danh sách
    lớp, tức chép lại đúng dòng khai báo, nên nó xanh cả khi `user_day` vắng
    mặt trong `DEFAULT_THROTTLE_RATES` (thứ làm view ném `ImproperlyConfigured`
    ở MỌI request).
    """
    from lessons.views import CheckAnswersView
    scope = {}
    for lop in CheckAnswersView.throttle_classes:
        t = lop()                      # ném ImproperlyConfigured nếu thiếu rate
        scope[t.scope] = (t.num_requests, t.duration)
    assert set(scope) == {'user_hour', 'user_day', 'ip_hour', 'ip_day'}, scope
    assert all(n and n > 0 for n, _ in scope.values()), scope


# ── L7 · học lại bài cũ GIỮ NGÀY ĐẦU (anh Sơn chốt 31/08/2026) ──────────────

@pytest.mark.django_db
def test_hoc_lai_bai_cu_KHONG_viet_lai_qua_khu(em):
    """`event_date` là trục thời gian của đường cong tiến bộ và "chỉ tiêu tuần".
    Ghi đè thẳng thì ôn lại một bài cũ ĐỔI HÌNH DẠNG tuần trước: điểm biến khỏi
    chỗ nó từng ở, chỉ tiêu tuần nhích lên trong khi nhiệm vụ ngày vẫn 0/1.

    `occurred_at` thì NGƯỢC LẠI — nó phải cập nhật, vì nó trả lời "lần gần nhất
    em chạm vào việc này".
    """
    from datetime import timedelta

    from common.db import x as _x
    from common.events import KIND_LESSON, record_event

    cu = local_today() - timedelta(days=30)
    record_event(em.id, KIND_LESSON, 'l7:test', occurred_at=cu, event_date=cu,
                 ref_type='lesson', ref_id='777', score=50, max_score=100)
    dong = q1("SELECT event_date, occurred_at FROM learning_events "
              "WHERE user_id=%s AND dedup_key='l7:test'", (em.id,))
    assert dong['event_date'] == cu

    # Ôn lại hôm nay.
    from common.clock import local_now
    now = local_now()
    record_event(em.id, KIND_LESSON, 'l7:test', occurred_at=now,
                 ref_type='lesson', ref_id='777', score=90, max_score=100)
    sau = q1("SELECT event_date, occurred_at, score FROM learning_events "
             "WHERE user_id=%s AND dedup_key='l7:test'", (em.id,))
    assert sau['event_date'] == cu, (
        'ôn lại hôm nay mà ngày của lần đầu bị đẩy sang %s' % sau['event_date'])
    assert sau['occurred_at'].date() == now.date(), '"lần gần nhất" phải cập nhật'
    assert sau['score'] == 90, 'điểm mới vẫn phải ghi đè như cũ'
    _x("DELETE FROM learning_events WHERE user_id=%s AND dedup_key='l7:test'", (em.id,))


@pytest.mark.django_db
def test_bang_theo_doi_cua_giang_vien_doc_LAN_GAN_NHAT(em):
    """Giảng viên nhìn cột "hoạt động gần nhất" để biết em nào đang mất hút.
    Đọc `event_date` (nay giữ ngày đầu) là hỏi sai câu."""
    from datetime import timedelta

    from common.db import x as _x
    from common.events import KIND_LESSON, record_event
    from teaching.reports import _last_activity

    cu = local_today() - timedelta(days=40)
    record_event(em.id, KIND_LESSON, 'l7:hd', occurred_at=cu, event_date=cu,
                 ref_type='lesson', ref_id='778', score=50, max_score=100)
    from common.clock import local_now
    record_event(em.id, KIND_LESSON, 'l7:hd', occurred_at=local_now(),
                 ref_type='lesson', ref_id='778', score=60, max_score=100)

    ra = _last_activity([em.id])[em.id]
    assert ra['last_day'] == local_today(), (
        'em vừa ôn bài hôm nay mà bảng nói hoạt động gần nhất là %s' % ra['last_day'])
    _x("DELETE FROM learning_events WHERE user_id=%s AND dedup_key='l7:hd'", (em.id,))


# ── B14 · thứ tự DDL: `bootstrap_schema` chạy trong buildCommand của Render ─

def test_khong_cau_DDL_nao_dung_toi_bang_chua_duoc_tao():
    """`bootstrap_schema` `raise` ở câu lệnh ĐẦU TIÊN hỏng, và nó nằm trong
    `buildCommand` của Render — nên một câu đứng sai chỗ làm CHẾT cả lần triển
    khai trên CSDL rỗng. Trên CSDL đang chạy thì lỗi ấy NGỦ (bảng có sẵn); nó
    thức dậy đúng lúc dựng staging hoặc khôi phục sau sự cố.

    Đã bắt được thật 01/09/2026: `CREATE INDEX … ON mock_attempts` nằm ở
    `legacy_schema.sql`, mà `sorted()` cho "legacy" chạy trước "mockexam".
    `IF NOT EXISTS` chỉ bỏ qua khi CHỈ MỤC đã có, không cứu được khi BẢNG chưa có.
    """
    import io as _io
    import pathlib
    import re

    from common.management.commands.bootstrap_schema import _split_statements

    TAO = re.compile(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_]\w*)', re.I)
    SUA = re.compile(r'ALTER\s+TABLE\s+(?:ONLY\s+)?([A-Za-z_]\w*)', re.I)
    # Bám vào cụm "INDEX … ON" để không bắt nhầm `ON DELETE CASCADE`.
    IDX = re.compile(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:CONCURRENTLY\s+)?'
                     r'(?:IF\s+NOT\s+EXISTS\s+)?\w+\s+ON\s+([A-Za-z_]\w*)', re.I)

    thu_muc = pathlib.Path(__file__).resolve().parent.parent / 'sql'
    da_tao, loi = set(), []
    for f in sorted(thu_muc.glob('*.sql')):
        for st in _split_statements(_io.open(f, encoding='utf-8').read()):
            m = TAO.search(st)
            if m:
                da_tao.add(m.group(1).lower())
                continue
            for rx in (SUA, IDX):
                m = rx.search(st)
                if m:
                    if m.group(1).lower() not in da_tao:
                        loi.append('%s: %s' % (f.name, ' '.join(st.split())[:70]))
                    break
    assert loi == [], loi


# ── IP máy khách: MỘT cửa cho cả hàng rào tần suất lẫn nhật ký kiểm toán ────
#
# LỖI GỐC (đo 04/09/2026). `audit._client_ip` lấy phần tử ĐẦU của
# `X-Forwarded-For`, còn `get_ident` của DRF lấy phần tử CUỐI. Phần đầu là thứ
# khách TỰ VIẾT, nên: cùng một request bị chặn vì IP này lại vào sổ kiểm toán
# dưới IP kia — và cột `ip` của nhật ký, thứ sinh ra để làm bằng chứng, giả mạo
# được chỉ bằng một header.
#
# Ba phép kiểm dưới đây canh ba việc KHÁC nhau, cố ý:
#   1. hai bên có CÙNG một câu trả lời (bất biến bị vỡ);
#   2. `NUM_PROXIES=1` bỏ qua được chặng khách bịa (giá trị đúng);
#   3. `=0` thì không tin header nào (đường máy dev).

from django.test import RequestFactory, override_settings  # noqa: E402

from common import audit as _audit  # noqa: E402
from common.throttling import LoginThrottle  # noqa: E402

_rf = RequestFactory()


def _req(remote='203.0.113.9', xff=None):
    kw = {'REMOTE_ADDR': remote}
    if xff is not None:
        kw['HTTP_X_FORWARDED_FOR'] = xff
    return _rf.get('/', **kw)


@override_settings(NUM_PROXIES=1)
def test_hang_rao_tan_suat_va_nhat_ky_luon_thay_CUNG_mot_ip():
    """Bất biến: hai hệ thống phải nói cùng một con số cho cùng một request.

    Không khẳng định con số ấy BẰNG BAO NHIÊU — đó là việc của phép kiểm dưới.
    Ở đây chỉ khẳng định chúng KHÔNG LỆCH, vì lệch là kiểu hỏng mà cả hai bên
    đều trông vẫn đúng khi nhìn riêng.
    """
    t = LoginThrottle.__new__(LoginThrottle)   # bỏ qua __init__ (nó đọc rate)
    for xff in (None, '9.9.9.9', '9.9.9.9, 203.0.113.9', '1.1.1.1, 2.2.2.2, 3.3.3.3'):
        r = _req(xff=xff)
        assert t.get_ident(r) == _audit._client_ip(r), (
            'lệch với X-Forwarded-For=%r: tần suất thấy %r, nhật ký ghi %r'
            % (xff, t.get_ident(r), _audit._client_ip(r)))


@override_settings(NUM_PROXIES=1)
def test_mot_chang_tin_cay_thi_bo_qua_phan_khach_tu_bia():
    from common.net import client_ip
    # Khách bịa thêm một chặng vào ĐẦU; chặng tin cậy nối IP thật vào CUỐI.
    assert client_ip(_req(remote='10.0.0.5', xff='9.9.9.9, 203.0.113.9')) == '203.0.113.9'
    # Bịa nhiều chặng cũng vậy — chỉ phần tử cuối là do proxy thật nối vào.
    assert client_ip(_req(remote='10.0.0.5',
                          xff='1.1.1.1, 2.2.2.2, 203.0.113.9')) == '203.0.113.9'


@override_settings(NUM_PROXIES=0)
def test_khong_co_chang_tin_cay_thi_khong_tin_header_nao():
    """Đường máy dev: không có proxy nào, nên `REMOTE_ADDR` là câu trả lời duy
    nhất không giả được. Đây là lý do mặc định theo MÔI TRƯỜNG chứ không phải
    một hằng số dùng chung cho cả dev lẫn production."""
    from common.net import client_ip
    assert client_ip(_req(xff='9.9.9.9')) == '203.0.113.9'
    assert client_ip(_req(xff='1.1.1.1, 2.2.2.2')) == '203.0.113.9'
