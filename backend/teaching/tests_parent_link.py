"""Đường CÔNG KHAI tới báo cáo phụ huynh — mở bằng chìa.

Chạy trên DB thật, mọi thứ nằm trong giao dịch được CUỘN LẠI (xem `conftest.py`).

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

Đây là bề mặt duy nhất trong sản phẩm mở cho người KHÔNG có tài khoản. Ba lỗi
có thể mắc mà không kêu:

  1. Tờ đi qua chìa quên rút gọn → email + số điện thoại của một đứa trẻ nằm
     sau một đường link có thể chuyển tiếp trong nhóm chat.
  2. Kỳ báo cáo đọc từ query → ai cầm link cũng xem được ngoài kỳ được gửi.
  3. Chìa hết hạn / bị thu hồi vẫn mở được → không có cách nào rút lại.

Cả ba đều trả về HTTP 200 khi hỏng, nên không có lỗi nào nổi lên. Chỉ có phép
kiểm mới thấy.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.clock import local_now
from common.db import q1
from common.permissions import ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER
from teaching.parent_link import (
    ParentReportLinkRevokeView,
    ParentReportLinkView,
    PublicParentReportView,
)

f = APIRequestFactory()


def _goi(view, method, body=None, ai=None, url='/x', **kw):
    req = (getattr(f, method)(url, body, format='json') if body is not None
           else getattr(f, method)(url))
    if ai is not None:
        force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(ten, vai, **cot):
    khoa = ', '.join(cot)
    cho = ', '.join(['%s'] * len(cot))
    row = q1(
        f'INSERT INTO users (name, email, password, role, streak{", " + khoa if khoa else ""}) '
        f'VALUES (%s, %s, %s, %s, 0{", " + cho if cho else ""}) RETURNING id',
        (ten, '%s_tmp@example.com' % ten.replace(' ', '_'), 'x', vai, *cot.values()))
    return User.objects.get(id=row['id'])


@pytest.fixture
def canh(db):
    """Một lớp, một giảng viên phụ trách, một học viên đã khai số phụ huynh."""
    gv = _nguoi('GV Link', ROLE_TEACHER)
    em = _nguoi('HV Link', ROLE_STUDENT,
                parent_name='Nguyen Thi Me', parent_phone='0912345678')
    c = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
           "VALUES ('Lop link','hsa_quantitative',%s,'active') RETURNING id", (gv.id,))
    q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) '
       'RETURNING id', (c['id'], em.id, local_now() - timedelta(days=10)))
    return {'lop': c['id'], 'gv': gv, 'em': em}


def _cap(canh):
    kq = _goi(ParentReportLinkView, 'post', {}, ai=canh['gv'],
              class_id=canh['lop'], user_id=canh['em'].id)
    assert kq.status_code == 201, kq.data
    return kq.data['token']


# ── Cấp chìa ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_cap_chia_tra_ve_token_du_dai(canh):
    kq = _goi(ParentReportLinkView, 'post', {}, ai=canh['gv'],
              class_id=canh['lop'], user_id=canh['em'].id)
    assert kq.status_code == 201, kq.data
    # 32 byte urlsafe → 43 ký tự. Ngắn hơn nhiều là ai đó đã hạ `SO_BYTE`, và
    # một chìa ngắn thì dò được — thứ không kêu lên khi hỏng.
    assert len(kq.data['token']) >= 40, kq.data['token']
    assert kq.data['parentPhone'] == '0912345678'


@pytest.mark.django_db
def test_hoc_vien_khong_cap_duoc_chia_cho_chinh_minh(canh):
    """Cấp một đường vào KHÔNG CẦN TÀI KHOẢN là hành vi nặng hơn XEM."""
    kq = _goi(ParentReportLinkView, 'post', {}, ai=canh['em'],
              class_id=canh['lop'], user_id=canh['em'].id)
    assert kq.status_code in (403, 404), kq.status_code


@pytest.mark.django_db
def test_giang_vien_lop_khac_khong_cap_duoc(canh):
    la = _nguoi('GV La', ROLE_TEACHER)
    kq = _goi(ParentReportLinkView, 'post', {}, ai=la,
              class_id=canh['lop'], user_id=canh['em'].id)
    assert kq.status_code == 404, kq.status_code


@pytest.mark.django_db
def test_khong_cap_chia_cho_em_khong_o_lop(canh):
    """Cấp link rồi mới phát hiện nó dẫn tới 404 là gửi cho phụ huynh một link
    hỏng — và người phát hiện ra sẽ là họ, không phải trung tâm."""
    ngoai = _nguoi('HV Ngoai Lop', ROLE_STUDENT)
    kq = _goi(ParentReportLinkView, 'post', {}, ai=canh['gv'],
              class_id=canh['lop'], user_id=ngoai.id)
    assert kq.status_code == 404, kq.status_code
    assert q1('SELECT COUNT(*) AS n FROM parent_report_links WHERE user_id=%s',
              (ngoai.id,))['n'] == 0


# ── Đường công khai ─────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_phu_huynh_mo_duoc_khong_can_dang_nhap(canh):
    token = _cap(canh)
    kq = _goi(PublicParentReportView, 'get', ai=None, token=token)
    assert kq.status_code == 200, kq.data
    assert kq.data['student']['name'] == 'HV Link'
    assert kq.data['class']['name'] == 'Lop link'


@pytest.mark.django_db
def test_to_cong_khai_KHONG_mang_email_va_so_dien_thoai_cua_em(canh):
    """Cổng của `ParentReportView` là `IsSeniorTeachingStaff` CHÍNH VÌ tờ ấy in
    email và số điện thoại của học viên — trợ giảng còn không được xem. Một
    đường KHÔNG CÓ VAI NÀO thì càng phải bỏ."""
    token = _cap(canh)
    kq = _goi(PublicParentReportView, 'get', ai=None, token=token)
    assert kq.status_code == 200
    assert 'email' not in kq.data['student'], kq.data['student']
    assert 'phone' not in kq.data['student'], kq.data['student']
    # Số của chính phụ huynh cũng không echo lại: nó là một số thật nằm sau một
    # chìa có thể bị chuyển tiếp.
    assert 'phone' not in kq.data['parent'], kq.data['parent']
    assert kq.data['parent']['name'] == 'Nguyen Thi Me'


@pytest.mark.django_db
def test_ky_bao_cao_lay_TU_CHIA_chu_khong_tu_query(canh):
    """Đọc `?from=` ở đường công khai là cho người cầm link xem cả lịch sử học
    ngoài kỳ mà trung tâm định gửi."""
    token = _cap(canh)
    goc = _goi(PublicParentReportView, 'get', ai=None, token=token).data['period']
    req = f.get('/x?from=2000-01-01&to=2099-12-31')
    lech = PublicParentReportView.as_view()(req, token=token).data['period']
    assert lech == goc, (goc, lech)


@pytest.mark.django_db
def test_chia_sai_tra_404(canh):
    kq = _goi(PublicParentReportView, 'get', ai=None, token='khong-he-ton-tai')
    assert kq.status_code == 404


@pytest.mark.django_db
def test_chia_het_han_khong_mo_duoc(canh):
    token = _cap(canh)
    q1("UPDATE parent_report_links SET expires_at = now() - INTERVAL '1 day' "
       "WHERE token=%s RETURNING id", (token,))
    kq = _goi(PublicParentReportView, 'get', ai=None, token=token)
    assert kq.status_code == 404


@pytest.mark.django_db
def test_thu_hoi_thi_chia_chet_ngay_ma_lich_su_con(canh):
    token = _cap(canh)
    d = q1('SELECT id FROM parent_report_links WHERE token=%s', (token,))
    kq = _goi(ParentReportLinkRevokeView, 'post', {}, ai=canh['gv'], link_id=d['id'])
    assert kq.status_code == 200, kq.data
    assert _goi(PublicParentReportView, 'get', ai=None, token=token).status_code == 404
    # KHÔNG xoá dòng: xoá là mất luôn bằng chứng đã từng gửi cho ai, lúc nào.
    con = q1('SELECT revoked_at FROM parent_report_links WHERE id=%s', (d['id'],))
    assert con is not None and con['revoked_at'] is not None


@pytest.mark.django_db
def test_ba_ly_do_tu_choi_noi_CUNG_MOT_CAU(canh):
    """Nói rõ "chìa này đã bị thu hồi" là xác nhận với người cầm link rằng nó
    TỪNG đúng — một mẩu tin chỉ có ích cho người không nên cầm nó."""
    token = _cap(canh)
    sai = _goi(PublicParentReportView, 'get', ai=None, token='xxx').data['error']

    q1("UPDATE parent_report_links SET expires_at = now() - INTERVAL '1 day' "
       "WHERE token=%s RETURNING id", (token,))
    het_han = _goi(PublicParentReportView, 'get', ai=None, token=token).data['error']

    q1("UPDATE parent_report_links SET expires_at = now() + INTERVAL '9 day', "
       "revoked_at = now() WHERE token=%s RETURNING id", (token,))
    thu_hoi = _goi(PublicParentReportView, 'get', ai=None, token=token).data['error']

    assert sai == het_han == thu_hoi, (sai, het_han, thu_hoi)


@pytest.mark.django_db
def test_dem_luot_mo(canh):
    token = _cap(canh)
    d = q1('SELECT id, opened_count FROM parent_report_links WHERE token=%s', (token,))
    assert d['opened_count'] == 0
    _goi(PublicParentReportView, 'get', ai=None, token=token)
    _goi(PublicParentReportView, 'get', ai=None, token=token)
    sau = q1('SELECT opened_count, last_opened_at FROM parent_report_links WHERE id=%s',
             (d['id'],))
    assert sau['opened_count'] == 2, sau
    assert sau['last_opened_at'] is not None


@pytest.mark.django_db
def test_khong_ghi_dau_vet_cua_nguoi_mo(canh):
    """Người mở link không phải người dùng của hệ thống. Thu thập IP hay user
    agent của họ là một quyết định khác hẳn, và chưa ai quyết."""
    from common.db import q
    ten = {r['column_name'] for r in q(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='parent_report_links'")}
    assert not ten & {'ip', 'ip_address', 'user_agent', 'remote_addr'}, ten


# ── Chìa của em NÀY không mở được tờ của em KHÁC ────────────────────────────

@pytest.mark.django_db
def test_chia_bam_dung_mot_em(canh):
    """`class_id`/`user_id` lấy TỪ CHÌA. Nếu chúng đọc từ đường dẫn thì một
    chìa hợp lệ sẽ mở được tờ của mọi em trong lớp."""
    em2 = _nguoi('HV Link Hai', ROLE_STUDENT)
    q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) '
       'RETURNING id', (canh['lop'], em2.id, local_now() - timedelta(days=10)))
    token = _cap(canh)
    kq = _goi(PublicParentReportView, 'get', ai=None, token=token)
    assert kq.data['student']['id'] == canh['em'].id
    assert kq.data['student']['id'] != em2.id


@pytest.mark.django_db
def test_quan_tri_vien_cung_cap_duoc(canh):
    """Học vụ và quản trị phải làm được việc này — họ là người ngồi gửi hàng
    loạt, không phải giảng viên đứng lớp."""
    qt = _nguoi('QT Link', ROLE_ADMIN)
    kq = _goi(ParentReportLinkView, 'post', {}, ai=qt,
              class_id=canh['lop'], user_id=canh['em'].id)
    assert kq.status_code == 201, kq.data
