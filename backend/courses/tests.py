"""Port tests/test_course_ratings.py (Flask) + happy-path /api/courses."""
import pytest

from common.db import q, q1, x

pytestmark = pytest.mark.django_db

TEST_COURSE_ID = 'hsa_quantitative'   # CSDL HSA khong con khoa 'python' cua ProgrammingEdu


@pytest.fixture
def test_enrollment(temp_user):
    x('''INSERT INTO enrollments (user_id, course_id, progress, completed_lessons,
                                  time_spent, last_lesson, next_lesson)
         VALUES (%s, %s, 0, 0, '0h', '', '')
         ON CONFLICT (user_id, course_id) DO NOTHING''', (temp_user, TEST_COURSE_ID))
    return temp_user


@pytest.fixture
def other_api(db):
    """APIClient thứ HAI — cần một người chấm khác để trung bình có nghĩa."""
    from accounts.models import User
    from rest_framework.test import APIClient
    row = q1("INSERT INTO users (name, email, password) VALUES (%s,%s,%s) RETURNING id",
             ('Rate Other', 'rate_other_dj@example.com', 'x'))
    client = APIClient()
    client.force_authenticate(user=User.objects.get(id=row['id']))
    return client


def _rate(client, payload):
    return client.post('/api/course/rating', payload, format='json')


def test_rate_course_success(auth_api, test_enrollment):
    res = _rate(auth_api, {'course_id': TEST_COURSE_ID, 'rating': 4})
    assert res.status_code == 200
    assert res.json()['ok'] is True
    row = q1('SELECT rating FROM course_ratings WHERE user_id=%s AND course_id=%s',
             (test_enrollment, TEST_COURSE_ID))
    assert row['rating'] == 4


def test_rate_course_updates_not_duplicates(auth_api, test_enrollment):
    _rate(auth_api, {'course_id': TEST_COURSE_ID, 'rating': 3})
    res = _rate(auth_api, {'course_id': TEST_COURSE_ID, 'rating': 5})
    assert res.status_code == 200
    rows = q('SELECT rating FROM course_ratings WHERE user_id=%s AND course_id=%s',
             (test_enrollment, TEST_COURSE_ID))
    assert len(rows) == 1
    assert rows[0]['rating'] == 5


def test_rate_course_requires_enrollment(auth_api):
    res = _rate(auth_api, {'course_id': TEST_COURSE_ID, 'rating': 4})
    assert res.status_code == 403


def test_rate_course_unknown_course(auth_api):
    res = _rate(auth_api, {'course_id': 'does-not-exist', 'rating': 4})
    assert res.status_code == 404


@pytest.mark.parametrize('bad_rating', [0, 6, 'abc', True, None])
def test_rate_course_invalid_rating(auth_api, test_enrollment, bad_rating):
    payload = {'course_id': TEST_COURSE_ID}
    if bad_rating is not None:
        payload['rating'] = bad_rating
    assert _rate(auth_api, payload).status_code == 400


def test_rate_course_requires_login(api, db):
    res = _rate(api, {'course_id': TEST_COURSE_ID, 'rating': 4})
    assert res.status_code == 401


def test_get_rating_endpoint(auth_api, test_enrollment):
    _rate(auth_api, {'course_id': TEST_COURSE_ID, 'rating': 4})
    res = auth_api.get(f'/api/course/{TEST_COURSE_ID}/rating')
    assert res.status_code == 200
    data = res.json()
    assert data['count'] >= 1
    assert data['average'] is not None


def test_get_rating_unknown_course(auth_api):
    assert auth_api.get('/api/course/does-not-exist/rating').status_code == 404


# ── Coverage cơ bản mới (khóa /api/courses chưa từng có test) ────────────────

def test_courses_list_happy_path(auth_api):
    res = auth_api.get('/api/courses')
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list) and len(data) >= 1
    sample = data[0]
    assert 'accentColor' in sample and 'enrolled' in sample


def test_courses_enrolled_combined(auth_api, test_enrollment):
    res = auth_api.get('/api/courses-enrolled')
    assert res.status_code == 200
    data = res.json()
    assert any(e['id'] == TEST_COURSE_ID for e in data['enrolled'])


# ── L15 · điểm sao phải là điểm THẬT, không phải con số seed ────────────────

def test_chua_ai_danh_gia_thi_KHONG_hien_5_sao(auth_api):
    """`courses.rating` là con số SEED: cả ba khoá đang 5.0 trong khi
    `course_ratings` RỖNG — mọi trang khoá khoe "5.0 ★" mà chưa một ai chấm.

    Đỏ trên mã cũ: nó trả thẳng `c.rating` = 5.0.
    """
    from common.db import x as _x
    _x('DELETE FROM course_ratings WHERE course_id=%s', (TEST_COURSE_ID,))
    ds = auth_api.get('/api/courses').json()
    ds = ds.get('courses') if isinstance(ds, dict) else ds
    kh = next(c for c in ds if c['id'] == TEST_COURSE_ID)
    assert kh['rating'] is None, (
        'chưa ai đánh giá mà vẫn hiện %r sao' % kh['rating'])
    assert kh['rating_count'] == 0


def test_co_nguoi_danh_gia_thi_hien_dung_trung_binh(auth_api, other_api):
    """Hai người chấm 4 và 2 → trung bình 3.0, không phải 5.0 của seed."""
    from common.db import x as _x
    _x('DELETE FROM course_ratings WHERE course_id=%s', (TEST_COURSE_ID,))
    # Phải ghi danh mới được đánh giá — luật của `RateCourseView`, giữ nguyên.
    for cl in (auth_api, other_api):
        cl.post(f'/api/courses/{TEST_COURSE_ID}/enroll', {}, format='json')
    assert _rate(auth_api, {'course_id': TEST_COURSE_ID, 'rating': 4}).status_code in (200, 201)
    assert _rate(other_api, {'course_id': TEST_COURSE_ID, 'rating': 2}).status_code in (200, 201)

    ds = auth_api.get('/api/courses').json()
    ds = ds.get('courses') if isinstance(ds, dict) else ds
    kh = next(c for c in ds if c['id'] == TEST_COURSE_ID)
    assert float(kh['rating']) == 3.0, kh
    assert kh['rating_count'] == 2, kh


def test_MOI_duong_doc_khoa_deu_lay_diem_sao_that(auth_api):
    """Bộ kiểm backend xanh mà trang chi tiết vẫn hiện 5.0 — phép kiểm trình
    duyệt mới bắt được: `CourseDetailView` là đường đọc THỨ TƯ và tôi bỏ sót nó.

    Bốn đường: /api/courses · /api/courses-enrolled · /api/courses/<id> ·
    /api/public/courses. Một đường quên là một màn hình nói dối.
    """
    from common.db import x as _x
    _x('DELETE FROM course_ratings WHERE course_id=%s', (TEST_COURSE_ID,))

    def lay(d):
        ds = d.get('courses') if isinstance(d, dict) and 'courses' in d else d
        if isinstance(ds, list):
            return next(c for c in ds if c['id'] == TEST_COURSE_ID)
        return ds

    for url in ('/api/courses', '/api/courses-enrolled',
                f'/api/courses/{TEST_COURSE_ID}', '/api/public/courses'):
        kh = lay(auth_api.get(url).json())
        assert kh['rating'] is None, '%s vẫn trả %r' % (url, kh['rating'])
        assert kh['rating_count'] == 0, url
