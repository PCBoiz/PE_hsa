"""Tiến độ chương trình theo khung buổi (4.3, 25/09/2026) — teaching/tien_do_chuong_trinh.py."""
import pytest

from common.db import q1
from teaching.reports import class_report
from teaching.tien_do_chuong_trinh import tien_do_lop

pytestmark = pytest.mark.django_db


@pytest.fixture
def lop(db):
    return q1("INSERT INTO classes (name, course_id, status) "
             "VALUES ('Lớp tiến độ CT', 'hsa_quantitative', 'active') RETURNING id")['id']


def _phien_ban(course_id='hsa_quantitative'):
    return q1("INSERT INTO syllabus_versions (course_id, name, status) "
             "VALUES (%s, 'Bản tiến độ CT', 'xuat_ban') RETURNING id", (course_id,))['id']


def _buoi(version_id, so):
    return q1("INSERT INTO syllabus_sessions (version_id, sort_order, name) "
             "VALUES (%s, %s, %s) RETURNING id", (version_id, so, 'Buổi %d' % so))['id']


def _buoi_that(class_id, syllabus_session_id=None, status='planned'):
    return q1("INSERT INTO class_sessions (class_id, starts_at, status, syllabus_session_id) "
             "VALUES (%s, now(), %s, %s) RETURNING id", (class_id, status, syllabus_session_id))['id']


def test_chua_gan_khung_thi_none(lop):
    assert tien_do_lop(lop) is None
    assert class_report(lop)['syllabusProgress'] is None


def test_da_gan_khung_chua_day_buoi_nao(lop):
    v = _phien_ban()
    for i in (1, 2, 3):
        _buoi(v, i)
    q1('UPDATE classes SET syllabus_version_id=%s WHERE id=%s RETURNING id', (v, lop))
    td = tien_do_lop(lop)
    assert td == {'versionId': v, 'sessionsPlanned': 3, 'sessionsDone': 0,
                 'pct': 0, 'currentSession': None}


def test_da_day_mot_phan(lop):
    v = _phien_ban()
    b1, b2, b3, b4 = (_buoi(v, i) for i in (1, 2, 3, 4))
    q1('UPDATE classes SET syllabus_version_id=%s WHERE id=%s RETURNING id', (v, lop))
    _buoi_that(lop, b1, status='done')
    _buoi_that(lop, b2, status='done')
    _buoi_that(lop, b3, status='planned')  # sắp tới, chưa dạy

    td = tien_do_lop(lop)
    assert td['sessionsPlanned'] == 4
    assert td['sessionsDone'] == 2
    assert td['pct'] == 50
    assert td['currentSession'] == 2
    # Gắn đúng vào class_report — chỗ giáo vụ/giảng viên thật sự nhìn thấy.
    assert class_report(lop)['syllabusProgress'] == td


def test_buoi_done_nhung_chua_khop_khung_khong_tinh(lop):
    """Buổi ĐÃ dạy thật nhưng chưa chạy "gán khung" cho buổi đó
    (`syllabus_session_id IS NULL`) — không biết nó ứng buổi mấy trong khung
    nên không được tính vào `sessionsDone`, kẻo phóng đại tiến độ."""
    v = _phien_ban()
    _buoi(v, 1)
    q1('UPDATE classes SET syllabus_version_id=%s WHERE id=%s RETURNING id', (v, lop))
    _buoi_that(lop, None, status='done')

    td = tien_do_lop(lop)
    assert td['sessionsDone'] == 0 and td['pct'] == 0
