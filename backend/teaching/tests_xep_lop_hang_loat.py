"""Xếp NHIỀU em vào lớp một lượt, và gán/gỡ TRỢ GIẢNG qua đúng cửa học vụ dùng.

Sinh ra từ rà luồng học vụ trên mock production (20/09/2026): xếp 3 em bằng cách
gõ từng email rồi bấm "Thêm vào lớp" — chỉ 1/3 em vào lớp vì lượt bấm thứ hai
rơi vào lúc báo cáo lớp đang tải lại và bị nuốt lặng lẽ. Cùng buổi đó, màn Lớp
học không có chữ "trợ giảng" nào: gán được (qua ô email học viên) nhưng gán xong
thì trợ giảng biến mất — không hiện trong danh sách, không gỡ được.

Cả hai đều chạy trên DB production trong giao dịch cuộn lại (`conftest.py`).
"""
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1
from common.permissions import ROLE_ACADEMIC, ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER
from teaching.reports import class_report
from teaching.views import AdminClassesView, AdminClassMembersView

f = APIRequestFactory()


def _goi(view, method, body=None, ai=None, url='/x', **kw):
    req = (getattr(f, method)(url, body, format='json') if body is not None
           else getattr(f, method)(url))
    force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(ten, vai):
    r = q1('INSERT INTO users (name, email, password, role, streak) '
           'VALUES (%s, %s, %s, %s, 0) RETURNING id',
           (ten, '%s_xl@example.com' % ten.replace(' ', '_').lower(), 'x', vai))
    return User.objects.get(id=r['id'])


@pytest.fixture
def canh(db):
    hv = _nguoi('HV Xep Lop', ROLE_ACADEMIC)
    gv = _nguoi('GV Xep Lop', ROLE_TEACHER)
    lop = q1('INSERT INTO classes (name, teacher_id, status, created_at) '
             "VALUES ('Lớp xếp hàng loạt', %s, 'active', now()) RETURNING id", (gv.id,))
    return {
        'hocvu': hv, 'gv': gv, 'lop': lop['id'],
        'em': [_nguoi('Em Mot', ROLE_STUDENT), _nguoi('Em Hai', ROLE_STUDENT),
               _nguoi('Em Ba', ROLE_STUDENT)],
        'tg': _nguoi('TG Xep Lop', ROLE_ASSISTANT),
    }


@pytest.mark.django_db
def test_dan_nhieu_email_mot_luot(canh):
    """`emails` = danh sách dán từ bảng tính. Từng email trả lời riêng."""
    a, b, c = canh['em']
    # Em Hai đã ở trong lớp từ trước; một email sai chính tả; một email lặp.
    q1('INSERT INTO class_members (class_id, user_id, joined_at) '
       'VALUES (%s, %s, now()) RETURNING id', (canh['lop'], b.id))
    kq = _goi(AdminClassMembersView, 'post',
              {'emails': [a.email, ' ' + b.email.upper() + ' ', 'khong.co@example.com',
                          c.email, a.email]},
              ai=canh['hocvu'], class_id=canh['lop'])
    assert kq.status_code == 200, kq.data
    assert [r['email'] for r in kq.data['added']] == [a.email, c.email], kq.data
    assert [r['email'] for r in kq.data['already']] == [b.email], kq.data
    assert kq.data['missing'] == ['khong.co@example.com'], kq.data
    # Ba em, ba dòng đang học — không dòng thứ tư cho email lặp.
    n = q1('SELECT count(*) AS n FROM class_members WHERE class_id=%s AND left_at IS NULL',
           (canh['lop'],))['n']
    assert n == 3, n


@pytest.mark.django_db
def test_danh_sach_rong_bi_tu_choi(canh):
    kq = _goi(AdminClassMembersView, 'post', {'emails': ['', '   ']},
              ai=canh['hocvu'], class_id=canh['lop'])
    assert kq.status_code == 400, kq.data


@pytest.mark.django_db
def test_tro_giang_hien_trong_bao_cao_va_o_chon(canh):
    """Gán trợ giảng xong phải NHÌN THẤY được: trong `assistants` của báo cáo lớp
    (chứ không phải trong sĩ số), và ô chọn của bảng lớp phải liệt kê mọi tài
    khoản Trợ giảng để học vụ có chỗ mà gán."""
    tg = canh['tg']
    kq = _goi(AdminClassMembersView, 'post', {'email': tg.email},
              ai=canh['hocvu'], class_id=canh['lop'])
    assert kq.status_code == 200 and kq.data.get('role') == ROLE_ASSISTANT, kq.data

    bc = class_report(canh['lop'])
    assert [t['userId'] for t in bc['assistants']] == [tg.id], bc['assistants']
    assert bc['summary']['students'] == 0, 'trợ giảng không được đếm vào sĩ số'

    ds = _goi(AdminClassesView, 'get', ai=canh['hocvu'])
    assert tg.id in {r['id'] for r in ds.data['assistants']}, ds.data.keys()

    # Nhật ký nói đúng việc đã làm — "gán trợ giảng", không phải "thêm học viên".
    nk = q1("SELECT summary FROM admin_audit WHERE action='class.member.add' "
            'AND target_id=%s ORDER BY id DESC LIMIT 1', (str(canh['lop']),))
    assert nk and nk['summary'].startswith('Gán trợ giảng'), nk

    # Gỡ: cùng cửa DELETE, không cần lý do rời lớp; biến khỏi `assistants`.
    kq = _goi(AdminClassMembersView, 'delete', ai=canh['hocvu'],
              url='/x?user_id=%s' % tg.id, class_id=canh['lop'])
    assert kq.status_code == 200, kq.data
    assert class_report(canh['lop'])['assistants'] == []
    nk = q1("SELECT summary FROM admin_audit WHERE action='class.member.remove' "
            'AND target_id=%s ORDER BY id DESC LIMIT 1', (str(canh['lop']),))
    assert nk and nk['summary'].startswith('Gỡ trợ giảng'), nk


@pytest.mark.django_db
def test_ngay_vao_lop_that_cho_em_ghi_danh_muon(canh):
    """Em đang học dở từ trước ngày nhập liệu: học vụ ghi `joined_at` = ngày
    vào lớp thật (quy ước H.6 trong tờ đề xuất gửi TopHSA). Tương lai → 400."""
    a, b, _ = canh['em']
    kq = _goi(AdminClassMembersView, 'post', {'emails': [a.email], 'joined_at': '2026-09-01'},
              ai=canh['hocvu'], class_id=canh['lop'])
    assert kq.status_code == 200 and len(kq.data['added']) == 1, kq.data
    r = q1('SELECT joined_at FROM class_members WHERE class_id=%s AND user_id=%s',
           (canh['lop'], a.id))
    assert r['joined_at'].date().isoformat() == '2026-09-01', r
    kq = _goi(AdminClassMembersView, 'post', {'email': b.email, 'joined_at': '2999-01-01'},
              ai=canh['hocvu'], class_id=canh['lop'])
    assert kq.status_code == 400 and 'tương lai' in kq.data['error'], kq.data
    kq = _goi(AdminClassMembersView, 'post', {'email': b.email, 'joined_at': 'hôm qua'},
              ai=canh['hocvu'], class_id=canh['lop'])
    assert kq.status_code == 400, kq.data


@pytest.mark.django_db
def test_sua_duoc_ngay_vao_lop_cua_em_da_trong_lop(canh):
    """Gửi `joined_at` cho em ĐÃ ở trong lớp phải SỬA ngày ấy, không im lặng.

    Rà vai học vụ 21/09/2026: gửi 13/09 cho một em đang học → máy chủ trả
    "already" và ngày vẫn nguyên, trong khi đây là màn DUY NHẤT đặt được ngày
    vào lớp và chuyên cần thì tính theo nó. Không gửi ngày thì không đụng tới.
    """
    a = canh['em'][0]
    _goi(AdminClassMembersView, 'post', {'emails': [a.email], 'joined_at': '2026-09-01'},
         ai=canh['hocvu'], class_id=canh['lop'])
    # Lần hai: em đã ở trong lớp, ngày khác → phải đổi.
    kq = _goi(AdminClassMembersView, 'post', {'emails': [a.email], 'joined_at': '2026-08-15'},
              ai=canh['hocvu'], class_id=canh['lop'])
    assert kq.status_code == 200 and len(kq.data['already']) == 1, kq.data
    r = q1('SELECT joined_at FROM class_members WHERE class_id=%s AND user_id=%s '
           'AND left_at IS NULL', (canh['lop'], a.id))
    assert r['joined_at'].date().isoformat() == '2026-08-15', r
    nk = q1("SELECT summary FROM admin_audit WHERE action='class.member.add' "
            'AND target_id=%s ORDER BY id DESC LIMIT 1', (str(canh['lop']),))
    assert nk and 'Sửa ngày vào lớp' in nk['summary'], nk
    # KHÔNG gửi ngày → giữ nguyên, không ghi thêm nhật ký sửa.
    _goi(AdminClassMembersView, 'post', {'emails': [a.email]},
         ai=canh['hocvu'], class_id=canh['lop'])
    r2 = q1('SELECT joined_at FROM class_members WHERE class_id=%s AND user_id=%s '
            'AND left_at IS NULL', (canh['lop'], a.id))
    assert r2['joined_at'].date().isoformat() == '2026-08-15', r2


@pytest.mark.django_db
def test_cap_hang_loat_kem_xep_lop_nhan_ngay_vao_lop(canh):
    """Cấp hàng loạt + xếp lớp: `joined_at` một ngày cho cả mẻ (các em đang học
    dở được nhập sau khai giảng). Không có test nào cho đường này tới 20/09."""
    from common.permissions import ROLE_ADMIN
    from teaching.admin_users import AdminBulkCreateUsersView
    qt = _nguoi('QT Xep Lop', ROLE_ADMIN)
    text = 'Em Bon Xl, embon_xl@example.com, 0911000004\nEm Nam Xl, emnam_xl@example.com, 0911000005'
    kq = _goi(AdminBulkCreateUsersView, 'post',
              {'text': text, 'role': ROLE_STUDENT, 'class_id': canh['lop'], 'joined_at': '2999-01-01'},
              ai=qt)
    assert kq.status_code == 400 and 'tương lai' in kq.data['error'], kq.data
    kq = _goi(AdminBulkCreateUsersView, 'post',
              {'text': text, 'role': ROLE_STUDENT, 'class_id': canh['lop'], 'joined_at': '2026-09-13'},
              ai=qt)
    assert kq.status_code in (200, 201) and kq.data['created'] == 2 and kq.data['addedToClass'], kq.data
    ds = q1('SELECT COUNT(*) AS n FROM class_members m JOIN users u ON u.id = m.user_id '
            "WHERE m.class_id=%s AND u.email LIKE 'em%%_xl@example.com' "
            "AND m.joined_at::date = DATE '2026-09-13'", (canh['lop'],))
    assert ds['n'] == 2, ds
