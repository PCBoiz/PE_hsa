"""AI mở được dữ liệu phụ huynh của một em — ghim đúng ranh giới, theo VAI.

VÌ SAO TỆP NÀY RA ĐỜI (17/09/2026). Đang vẽ sơ đồ vai trò cho hồ sơ kỹ thuật thì
mở `common/permissions.py` ra đối chiếu và thấy chú thích đầu tệp nói *"Quản lý
học vụ … KHÔNG mở báo cáo phụ huynh"*, trong khi mã thì cho qua:
`IsSeniorTeachingStaff` = admin | academic | teacher.

Chú thích sai sửa được bằng một dòng. Thứ KHÔNG sửa được bằng một dòng là lý do
nó sống sót: ba đường mang dữ liệu liên lạc của một đứa trẻ ra ngoài — tờ báo
cáo, chìa công khai và lệnh thu hồi — **không có phép kiểm nào đi theo VAI**.
`tests_lien_he_phu_huynh.py` có, nhưng chỉ cho đường danh bạ. Nên ranh giới thật
của ba đường kia chưa từng được ai ghim; nó chỉ tồn tại trong một câu chú thích,
và câu ấy thì vừa bị bắt là nói sai.

Ghim cả sáu vai, kể cả những vai ĐƯỢC phép: nếu chỉ ghim vai bị chặn thì lần nới
quyền sau vẫn im lặng, mà nới quyền trên đúng ba đường này là chuyện đáng kêu.

BA MÃ LỖI, BA Ý NGHĨA KHÁC NHAU:
    403  vào được khu giảng dạy nhưng không đủ vai (trợ giảng)
    404  không nhìn thấy lớp ấy — KHÔNG lộ ra rằng lớp có tồn tại (giảng viên
         lớp khác)
    403  không thuộc khu giảng dạy (học viên, biên tập nội dung)
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.clock import local_now
from common.db import q1
from common.permissions import (
    ROLE_ACADEMIC,
    ROLE_ADMIN,
    ROLE_ASSISTANT,
    ROLE_EDITOR,
    ROLE_STUDENT,
    ROLE_TEACHER,
)
from teaching.parent_link import ParentReportLinkRevokeView, ParentReportLinkView
from teaching.parent_report import ParentReportView

f = APIRequestFactory()


def _goi(view, method, ai, body=None, **kw):
    req = (getattr(f, method)('/x', body, format='json') if body is not None
           else getattr(f, method)('/x'))
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(ten, vai, **cot):
    khoa = ', '.join(cot)
    cho = ', '.join(['%s'] * len(cot))
    row = q1(
        f'INSERT INTO users (name, email, password, role, streak{", " + khoa if khoa else ""}) '
        f'VALUES (%s, %s, %s, %s, 0{", " + cho if cho else ""}) RETURNING id',
        (ten, '%s_q@example.com' % ten.replace(' ', '_'), 'x', vai, *cot.values()))
    return User.objects.get(id=row['id'])


@pytest.fixture
def canh(db):
    """Một lớp có đủ sáu vai đứng quanh nó."""
    gv = _nguoi('GV Quyen', ROLE_TEACHER)
    gv_khac = _nguoi('GV Khac Quyen', ROLE_TEACHER)
    tg = _nguoi('TG Quyen', ROLE_ASSISTANT)
    qt = _nguoi('QT Quyen', ROLE_ADMIN)
    hv = _nguoi('HocVu Quyen', ROLE_ACADEMIC)
    bt = _nguoi('BienTap Quyen', ROLE_EDITOR)
    em = _nguoi('HV Em Quyen', ROLE_STUDENT,
                parent_name='Nguyen Thi Me', parent_phone='0912345678',
                parent_email='me.quyen@example.com')
    c = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
           "VALUES ('Lop quyen','hsa_quantitative',%s,'active') RETURNING id", (gv.id,))
    # Trợ giảng Ở TRONG lớp: đây mới là ca đáng kiểm. Trợ giảng ngoài lớp bị
    # `can_see_class` chặn từ trước, nên nó không chứng minh được gì về ranh
    # giới của `IsSeniorTeachingStaff`.
    for ai in (em, tg):
        q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) '
           'RETURNING id', (c['id'], ai.id, local_now() - timedelta(days=10)))
    return {'lop': c['id'], 'em': em, 'gv': gv, 'gv_khac': gv_khac,
            'tg': tg, 'qt': qt, 'hv': hv, 'bt': bt, 'em_role': em}


def _vai_va_ma(canh):
    """(nhãn, người, mã mong đợi) — dùng chung cho cả ba đường."""
    return [
        ('quản trị viên', canh['qt'], 200),
        ('quản lý học vụ', canh['hv'], 200),
        ('giảng viên phụ trách', canh['gv'], 200),
        ('giảng viên lớp khác', canh['gv_khac'], 404),
        ('trợ giảng TRONG lớp', canh['tg'], 403),
        ('học viên', canh['em'], 403),
        ('biên tập nội dung', canh['bt'], 403),
    ]


@pytest.mark.django_db
def test_to_bao_cao_phu_huynh_mo_duoc_boi_dung_ba_vai(canh):
    for nhan, ai, mong in _vai_va_ma(canh):
        kq = _goi(ParentReportView, 'get', ai,
                  class_id=canh['lop'], user_id=canh['em'].id)
        assert kq.status_code == mong, '%s: %s (mong %s)' % (nhan, kq.status_code, mong)


@pytest.mark.django_db
def test_cap_chia_cong_khai_mo_duoc_boi_dung_ba_vai(canh):
    for nhan, ai, mong in _vai_va_ma(canh):
        kq = _goi(ParentReportLinkView, 'post', ai, body={},
                  class_id=canh['lop'], user_id=canh['em'].id)
        # Cấp chìa thành công trả 201, không phải 200.
        cho = 201 if mong == 200 else mong
        assert kq.status_code == cho, '%s: %s (mong %s)' % (nhan, kq.status_code, cho)


@pytest.mark.django_db
def test_thu_hoi_chia_khong_long_hon_cap_chia(canh):
    """Thu hồi là việc NẶNG hơn cấp — cổng của nó không được rộng hơn.

    Chú thích ở `parent_link.py` nói đúng câu ấy; đây là chỗ ghim nó lại.
    """
    cap = _goi(ParentReportLinkView, 'post', canh['gv'], body={},
               class_id=canh['lop'], user_id=canh['em'].id)
    assert cap.status_code == 201, cap.data
    link_id = q1('SELECT id FROM parent_report_links WHERE token=%s',
                 (cap.data['token'],))['id']
    for nhan, ai, mong in _vai_va_ma(canh):
        if mong == 200:
            continue          # thu hồi thật thì chìa chết, không lặp được
        kq = _goi(ParentReportLinkRevokeView, 'post', ai, body={}, link_id=link_id)
        assert kq.status_code == mong, '%s: %s (mong %s)' % (nhan, kq.status_code, mong)
