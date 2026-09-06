"""RÀ SOÁT SÂU: đi trọn luồng ERP như một trung tâm thật, qua chính API thật.

Chạy trên DB production trong giao dịch được CUỘN LẠI (`conftest.py`). Anh Sơn
đã cho phép tôi ghi thẳng vào Neon để rà luồng này; tôi KHÔNG dùng quyền ấy —
đi qua đúng những endpoint đó trong một giao dịch cuộn lại cho cùng khả năng
phát hiện lỗi mà không để lại dòng nào.

── THỨ ĐANG ĐƯỢC CANH, VÀ VÌ SAO NÓ KHÁC MỌI BỘ KIỂM KHÁC ──────────────────

Các bộ kiểm hiện có soi TỪNG endpoint. Bộ này soi chỗ CHÚNG NỐI VÀO NHAU — nơi
lỗi đắt nhất sống, và nơi không phép kiểm đơn lẻ nào nhìn thấy:

  · điểm danh ở màn giảng viên có chảy vào bảng điều khiển toàn trung tâm không;
  · CÙNG MỘT SỰ THẬT có đọc ra CÙNG MỘT SỐ ở ba màn khác nhau không.

Đặc tả ERP §6 nói thẳng: *"Cùng cách tính với báo cáo từng lớp — nếu hai bên
lệch nhau thì đó là LỖI, không phải hai cách đo."* Câu ấy chưa có phép kiểm nào
canh cho tới hôm nay.

── ĐI THEO ĐÚNG THỨ TỰ MỘT TRUNG TÂM LÀM ───────────────────────────────────

    mở đợt → tạo lớp → xếp học viên → mở buổi → điểm danh
    → xem báo cáo lớp → xem toàn trung tâm → xem tờ gửi phụ huynh

Mỗi bước dùng ĐÚNG endpoint mà giao diện gọi, với ĐÚNG vai được phép làm việc
ấy. Gọi thẳng hàm bên trong sẽ bỏ qua cổng quyền — mà cổng quyền chính là thứ
hay lệch nhất giữa các màn.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.clock import local_now, local_today
from common.db import q1
from common.permissions import ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER
from teaching.overview import AdminOverviewView
from teaching.parent_report import ParentReportView
from teaching.sessions import ClassSessionsView, SessionAttendanceView
from teaching.terms import AdminTermsView
from teaching.views import AdminClassesView, AdminClassMembersView, TeachClassDetailView

f = APIRequestFactory()


def _goi(view, method, body=None, ai=None, url='/x', **kw):
    req = (getattr(f, method)(url, body, format='json') if body is not None
           else getattr(f, method)(url))
    if ai is not None:
        force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(ten, vai):
    r = q1('INSERT INTO users (name, email, password, role, streak) '
           'VALUES (%s, %s, %s, %s, 0) RETURNING id',
           (ten, '%s_erp@example.com' % ten.replace(' ', '_'), 'x', vai))
    return User.objects.get(id=r['id'])


@pytest.fixture
def vai(db):
    return {
        'qt': _nguoi('QT Luong', ROLE_ADMIN),
        'gv': _nguoi('GV Luong', ROLE_TEACHER),
        'hv': [_nguoi('HV Luong Mot', ROLE_STUDENT), _nguoi('HV Luong Hai', ROLE_STUDENT)],
    }


# ── Bước 1-3: mở đợt, tạo lớp, xếp học viên ─────────────────────────────────

@pytest.mark.django_db
def test_mo_dot_hoc(vai):
    kq = _goi(AdminTermsView, 'post',
              {'name': 'Đợt rà soát', 'code': 'RS1',
               'starts_on': str(local_today()),
               'ends_on': str(local_today() + timedelta(days=90))},
              ai=vai['qt'])
    assert kq.status_code in (200, 201), kq.data


@pytest.mark.django_db
def test_luong_tron_ven_va_BA_MAN_DOC_RA_CUNG_MOT_SO(vai):
    """Phép kiểm quan trọng nhất của tệp này.

    Điểm danh MỘT lần, rồi đọc lại tỉ lệ chuyên cần ở BA nơi: báo cáo lớp, bảng
    điều khiển toàn trung tâm, và tờ gửi phụ huynh. Ba con số phải bằng nhau.

    Nếu lệch: một trong ba màn đang nói dối, và không ai biết màn nào — đó đúng
    là kịch bản đặc tả §6 dựng ra để chặn.
    """
    qt, gv, (hv1, hv2) = vai['qt'], vai['gv'], vai['hv']

    # ── Đợt học ──
    kq = _goi(AdminTermsView, 'post',
              {'name': 'Đợt rà soát 2', 'code': 'RS2',
               'starts_on': str(local_today() - timedelta(days=7)),
               'ends_on': str(local_today() + timedelta(days=60))}, ai=qt)
    assert kq.status_code in (200, 201), kq.data
    dot_id = kq.data.get('id') or (kq.data.get('term') or {}).get('id')

    # ── Lớp ──
    than = {'name': 'Lớp rà soát', 'course_id': 'hsa_quantitative',
            'teacher_id': gv.id, 'capacity': 20, 'status': 'active'}
    if dot_id:
        than['term_id'] = dot_id
    kq = _goi(AdminClassesView, 'post', than, ai=qt)
    assert kq.status_code in (200, 201), kq.data
    lop_id = kq.data.get('id') or (kq.data.get('class') or {}).get('id')
    assert lop_id, kq.data

    # ── Xếp học viên ──
    for em in (hv1, hv2):
        kq = _goi(AdminClassMembersView, 'post', {'user_id': em.id},
                  ai=qt, class_id=lop_id)
        assert kq.status_code in (200, 201), (em.id, kq.status_code, kq.data)

    # ── LÙI NGÀY VÀO LỚP, và đây là chỗ tôi sai HAI LẦN trước khi hiểu ──
    #
    # `AdminClassMembersView` ghi `joined_at = bây giờ` (không nhận tham số), và
    # `parent_report._chuyen_can` chỉ tính buổi ĐÃ BẮT ĐẦU (`starts_at <= now`).
    # Hai luật ấy cộng lại: trong một kịch bản dựng trong vài mili giây, KHÔNG
    # buổi nào vừa-sau-khi-vào-lớp vừa-đã-diễn-ra.
    #
    # Lần 1 tôi đặt buổi ở "hôm qua" → nằm trước lượt học → tờ phụ huynh trả
    # None còn toàn trung tâm trả 50%, và tôi suýt ghi đó là "hai màn lệch nhau".
    # Lần 2 tôi đẩy buổi lên tương lai 1 phút → chưa diễn ra → vẫn None.
    #
    # Cả hai lần đều là thước sai, không phải mã sai. Trung tâm thật xếp lớp
    # trước rồi vài hôm sau mới dạy; phép kiểm phải dựng đúng dòng thời gian ấy.
    q1('UPDATE class_members SET joined_at = %s '
       'WHERE class_id = %s AND left_at IS NULL RETURNING id',
       (local_now() - timedelta(days=14), lop_id))

    # ── Buổi học: ĐÃ DIỄN RA, và sau ngày vào lớp ──
    kq = _goi(ClassSessionsView, 'post',
              {'starts_at': (local_now() - timedelta(days=1)).isoformat(),
               'duration_minutes': 90}, ai=gv, class_id=lop_id)
    assert kq.status_code in (200, 201), kq.data
    buoi_id = kq.data.get('id') or (kq.data.get('session') or {}).get('id')
    assert buoi_id, kq.data

    # ── Điểm danh: một em CÓ MẶT, một em VẮNG ──
    kq = _goi(SessionAttendanceView, 'post',
              {'marks': [{'user_id': hv1.id, 'status': 'present'},
                         {'user_id': hv2.id, 'status': 'absent'}]},
              ai=gv, session_id=buoi_id)
    assert kq.status_code in (200, 201), kq.data

    # ── ĐỌC LẠI Ở BA NƠI ──
    bao_cao_lop = _goi(TeachClassDetailView, 'get', ai=gv, class_id=lop_id)
    assert bao_cao_lop.status_code == 200, bao_cao_lop.data

    toan_tt = _goi(AdminOverviewView, 'get', ai=qt)
    assert toan_tt.status_code == 200, toan_tt.data
    lop_tt = next((c for c in toan_tt.data['classes'] if c['id'] == lop_id), None)
    assert lop_tt is not None, 'lớp vừa tạo KHÔNG xuất hiện ở bảng toàn trung tâm'

    to_ph = _goi(ParentReportView, 'get', ai=gv, class_id=lop_id, user_id=hv1.id)
    assert to_ph.status_code == 200, to_ph.data

    # Một trong hai em có mặt trên tổng số hai em đã tick → 50%.
    assert lop_tt['attendedPct'] == 50, (
        'toàn trung tâm tính chuyên cần ra %r, mong 50' % lop_tt['attendedPct'])
    # Tờ phụ huynh của em CÓ MẶT: 1/1 buổi → 100%.
    assert to_ph.data['attendance']['attendedPct'] == 100, (
        'tờ phụ huynh tính ra %r cho em có mặt đủ, mong 100'
        % to_ph.data['attendance']['attendedPct'])
    # Và số BUỔI ĐÃ ĐIỂM DANH phải khớp giữa hai màn.
    assert lop_tt['sessionsMarked'] == 1, lop_tt['sessionsMarked']
    assert to_ph.data['attendance']['sessionsCounted'] == 1, to_ph.data['attendance']

    # Buổi ĐÃ điểm danh thì KHÔNG được nằm trong "chưa điểm danh" — con số ấy
    # nuôi khối "Hôm nay cần làm gì", và một việc đã xong mà vẫn nhắc là cách
    # nhanh nhất để người dùng bỏ qua cả danh sách.
    assert lop_tt['sessionsUnmarked'] == 0, lop_tt['sessionsUnmarked']


@pytest.mark.django_db
def test_diem_danh_de_ra_su_kien_hoc_tap(vai):
    """Đặc tả ERP §4: mỗi dòng điểm danh đẻ một `learning_events`. Không có nó
    thì buổi ngồi lớp không bao giờ vào được bản đồ năng lực của em."""
    qt, gv, (hv1, _) = vai['qt'], vai['gv'], vai['hv']
    kq = _goi(AdminClassesView, 'post',
              {'name': 'Lớp sự kiện', 'course_id': 'hsa_quantitative',
               'teacher_id': gv.id, 'status': 'active'}, ai=qt)
    lop_id = kq.data.get('id') or (kq.data.get('class') or {}).get('id')
    _goi(AdminClassMembersView, 'post', {'user_id': hv1.id}, ai=qt, class_id=lop_id)
    kq = _goi(ClassSessionsView, 'post',
              {'starts_at': (local_now() - timedelta(hours=3)).isoformat(),
               'duration_minutes': 60}, ai=gv, class_id=lop_id)
    buoi_id = kq.data.get('id') or (kq.data.get('session') or {}).get('id')

    truoc = q1('SELECT COUNT(*) AS n FROM learning_events WHERE user_id=%s', (hv1.id,))['n']
    _goi(SessionAttendanceView, 'post',
         {'marks': [{'user_id': hv1.id, 'status': 'present'}]},
         ai=gv, session_id=buoi_id)
    sau = q1('SELECT COUNT(*) AS n FROM learning_events WHERE user_id=%s', (hv1.id,))['n']
    assert sau > truoc, 'điểm danh KHÔNG đẻ sự kiện học tập nào (%d → %d)' % (truoc, sau)


# ── Cổng quyền dọc theo luồng ───────────────────────────────────────────────

@pytest.mark.django_db
def test_giang_vien_KHONG_tao_duoc_lop(vai):
    """Xếp lớp là việc của học vụ/quản trị. Giảng viên tự tạo lớp được thì sĩ số
    và đợt học không còn ai kiểm soát."""
    kq = _goi(AdminClassesView, 'post',
              {'name': 'Lớp lậu', 'course_id': 'hsa_quantitative'}, ai=vai['gv'])
    assert kq.status_code in (403, 404), kq.status_code


@pytest.mark.django_db
def test_hoc_vien_KHONG_diem_danh_duoc(vai):
    qt, gv, (hv1, _) = vai['qt'], vai['gv'], vai['hv']
    kq = _goi(AdminClassesView, 'post',
              {'name': 'Lớp cổng', 'course_id': 'hsa_quantitative',
               'teacher_id': gv.id, 'status': 'active'}, ai=qt)
    lop_id = kq.data.get('id') or (kq.data.get('class') or {}).get('id')
    kq = _goi(ClassSessionsView, 'post',
              {'starts_at': local_now().isoformat(), 'duration_minutes': 60},
              ai=gv, class_id=lop_id)
    buoi_id = kq.data.get('id') or (kq.data.get('session') or {}).get('id')
    kq = _goi(SessionAttendanceView, 'post',
              {'marks': [{'user_id': hv1.id, 'status': 'present'}]},
              ai=hv1, session_id=buoi_id)
    assert kq.status_code in (403, 404), kq.status_code
