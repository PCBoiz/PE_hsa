"""Bộ dữ liệu trình diễn (§49) — `teaching/du_lieu_mau.py`.

Chạy trên Neon thật trong giao dịch được CUỘN LẠI. Mỗi phép kiểm có CSDL gọi `go()`
TRƯỚC: CSDL dùng chung có thể đang giữ bộ dữ liệu mẫu thật (dựng cho buổi trình
diễn), và `tao()` từ chối khi đã có — gỡ trong giao dịch sẽ cuộn lại cùng phép
kiểm, không mất gì. Kích thước nhỏ (2–3 em mỗi lớp): mỗi câu tới Neon ~240 ms.

Canh:
  1. Kế hoạch TẤT ĐỊNH, tên không trùng, email đuôi dành riêng.
  2. Dựng đủ mọi khối và ĐÁNH DẤU mọi thứ đã dựng.
  3. Tờ báo cáo phụ huynh của một em mẫu có đủ các khối — tức dữ liệu đi đúng đường ghi.
  4. Dựng lần hai bị chặn.
  5. Gỡ sạch mà không chạm dữ liệu thật.
  6. "Gửi cả lớp" KHÔNG gửi gì cho học viên mẫu.
  7. Tài khoản mẫu KHÔNG đăng nhập được — qua đúng `LoginView`.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common import mail, zalo
from common.clock import local_today
from common.db import q, q1, x
from common.permissions import ROLE_STUDENT, ROLE_TEACHER
from teaching import du_lieu_mau as M
from teaching.parent_report import DEFAULT_WEEKS, dung_bao_cao


@pytest.fixture
def sach(db):
    """Không còn dữ liệu mẫu nào (trong giao dịch của phép kiểm) + một giảng viên thử."""
    M.go()
    r = q1("INSERT INTO users (name, email, password, role, streak) "
           "VALUES ('GV Mau Test', 'gv_mau_test@example.com', 'x', %s, 0) RETURNING id",
           (ROLE_TEACHER,))
    return User.objects.get(id=r['id'])


def _bao_cao(user_id):
    lop = q1('SELECT class_id FROM class_members WHERE user_id=%s LIMIT 1', (user_id,))
    den = local_today()
    bc, loi = dung_bao_cao(lop['class_id'], user_id, den - timedelta(weeks=DEFAULT_WEEKS), den)
    assert loi is None, loi
    return bc


def test_ke_hoach_TAT_DINH_va_khong_trung_ten():
    a, b = M.ke_hoach(6), M.ke_hoach(6)
    assert a == b, 'cùng hạt giống phải ra cùng tên, cùng năng lực'
    ds = [e for lop in a for e in lop['hoc_vien']]
    assert len(ds) == 12 and len({e['ho_ten'] for e in ds}) == 12, 'không trùng tên trong bộ'
    assert all(e['email'].endswith('@example.com')
               and e['email_ph'].endswith('@example.com') for e in ds), \
        'địa chỉ phải là tên miền dành riêng — không bao giờ tới hộp thư thật'
    assert M.ke_hoach(6, hat_giong=1) != a


def test_tao_du_moi_khoi_va_DANH_DAU_moi_thu(sach):
    so = M.tao(giang_vien_id=sach.id, so_em_moi_lop=3)
    assert so['tài khoản mẫu'] == 6 and so['lớp mẫu'] == 2
    for k in ('buổi học', 'điểm danh', 'bài tập', 'bài nộp', 'tiến độ bài học', 'ghi danh',
              'sự kiện học tập', 'kết quả thi tại trung tâm', 'nhật ký XP ngày'):
        assert so[k] > 0, 'thiếu khối: %s' % k
    em = q('SELECT email, role FROM users WHERE is_demo')
    assert all(r['email'].endswith('@example.com') and r['role'] == ROLE_STUDENT for r in em)
    lop = q('SELECT name, teacher_id FROM classes WHERE is_demo')
    assert all('lớp mẫu' in r['name'] and r['teacher_id'] == sach.id for r in lop)


def test_to_bao_cao_cua_em_MAU_co_du_cac_khoi(sach):
    """Nếu một khối trống ở đây thì trong buổi trình diễn nó cũng trống — và
    nghĩa là dữ liệu mẫu đã ĐI VÒNG một đường ghi nào đó."""
    M.tao(giang_vien_id=sach.id, so_em_moi_lop=3)
    nhieu_bai = q1('''SELECT u.id FROM users u WHERE u.is_demo
                      ORDER BY (SELECT COUNT(*) FROM lesson_progress p WHERE p.user_id = u.id) DESC
                      LIMIT 1''')['id']
    bc = _bao_cao(nhieu_bai)
    assert bc['attendance']['sessionsCounted'] > 0 and bc['attendance']['attendedPct'] is not None
    assert bc['study']['lessonsDone'] > 0
    assert bc['topics']['measured'] > 0, 'bản đồ năng lực phải đo được ít nhất một chủ đề'
    assert any(c['lessonsDone'] > 0 for c in bc['topics']['courses'])

    hai_ky = q1('''SELECT k.user_id FROM ket_qua_thi_ngoai k JOIN users u ON u.id = k.user_id
                   WHERE u.is_demo GROUP BY k.user_id HAVING COUNT(*) = 2 LIMIT 1''')
    assert hai_ky, 'phải có em thi đủ hai kỳ tại trung tâm'
    ce = _bao_cao(hai_ky['user_id'])['centerExam']
    assert ce and ce['previous'] and ce['max'] == 150 and len(ce['weakUnits']) == 3


def test_tao_LAN_HAI_bi_chan(sach):
    M.tao(giang_vien_id=sach.id, so_em_moi_lop=2)
    with pytest.raises(M.LoiDuLieuMau) as e:
        M.tao(giang_vien_id=sach.id, so_em_moi_lop=2)
    assert '--go' in str(e.value)


def test_go_GO_SACH_va_KHONG_cham_du_lieu_that(sach):
    that = q1("INSERT INTO users (name, email, password, role, streak) "
              "VALUES ('Em That', 'em_that_mau@example.com', 'x', %s, 0) RETURNING id",
              (ROLE_STUDENT,))['id']
    lop_that = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
                  "VALUES ('Lop that', 'hsa_quantitative', %s, 'active') RETURNING id",
                  (sach.id,))['id']
    x("INSERT INTO learning_events (user_id, dedup_key, occurred_at, event_date, kind) "
      "VALUES (%s, 'that:1', now(), current_date, 'lesson')", (that,))

    M.tao(giang_vien_id=sach.id, so_em_moi_lop=2)
    truoc, sau = M.go()
    assert truoc['tài khoản mẫu'] == 4 and truoc['sự kiện học tập'] > 0
    assert all(n == 0 for n in sau.values()), sau
    assert q1('SELECT id FROM users WHERE id=%s', (that,))
    assert q1('SELECT id FROM classes WHERE id=%s', (lop_that,))
    assert q1('SELECT COUNT(*) AS n FROM learning_events WHERE user_id=%s', (that,))['n'] == 1
    assert q1('SELECT id FROM users WHERE id=%s', (sach.id,)), \
        'giảng viên THẬT phụ trách lớp mẫu không được xoá theo'


def test_gui_ca_lop_KHONG_gui_gi_cho_hoc_vien_mau(sach, monkeypatch):
    da_gui = []
    monkeypatch.setattr(mail, 'da_cau_hinh', lambda: True)
    monkeypatch.setattr(mail, 'che_do_thu', lambda: False)
    monkeypatch.setattr(mail, 'thieu_gi', lambda: [])
    monkeypatch.setattr(mail, 'gui', lambda *a, **k: da_gui.append(a) or (True, 'gia', None))
    monkeypatch.setattr(zalo, 'da_cau_hinh', lambda: False)
    monkeypatch.setattr(zalo, 'thieu_gi', lambda: ['ZALO_OA_ACCESS_TOKEN'])

    M.tao(giang_vien_id=sach.id, so_em_moi_lop=2)
    lop = q1("SELECT id FROM classes WHERE is_demo AND code = 'HSA-MAU-01'")['id']
    c = APIClient()
    c.force_authenticate(sach)
    duong = '/api/teach/classes/%s/parent-report/send-all' % lop

    xem = c.get(duong)
    assert xem.status_code == 200
    assert all(e['laMau'] and e['kenh'] is None and not e['guiDuoc']
               for e in xem.data['students']), xem.data['students']

    r = c.post(duong, {}, format='json')
    assert r.status_code == 200
    assert {e['trangThai'] for e in r.data['ketQua']} == {'mau'}
    assert da_gui == [], 'không một lá thư nào được đi tới địa chỉ bịa'
    assert q1('''SELECT COUNT(*) AS n FROM parent_report_sends s
                 JOIN parent_report_links l ON l.id = s.link_id WHERE l.class_id = %s''',
              (lop,))['n'] == 0, 'sổ gửi là sổ của tin đã đi thật'


def test_tai_khoan_mau_KHONG_dang_nhap_duoc(sach):
    """Đi qua `LoginView` thật, và đòi ĐÚNG 401 — 400 nghĩa là bị chặn ở kiểm email,
    tức phép kiểm chưa hề tới chỗ so mật khẩu.

    Bản đầu đặt mật khẩu là một chuỗi thô "không phải bản băm nào". Nhưng `LoginView`
    còn nhánh mật khẩu THÔ cũ: không phải băm thì so NGUYÊN VĂN rồi nâng cấp lên băm —
    nên chuỗi ấy chính là mật khẩu của mọi em mẫu, nằm trong kho mã công khai.
    """
    M.tao(giang_vien_id=sach.id, so_em_moi_lop=2)
    em = q1('SELECT email, password FROM users WHERE is_demo ORDER BY id LIMIT 1')
    c = APIClient()
    for thu in ('!du-lieu-mau-khong-dang-nhap-duoc', em['password'], 'matkhau123'):
        r = c.post('/auth/login', {'email': em['email'], 'password': thu}, format='json')
        assert r.status_code == 401, (thu[:12], r.status_code, getattr(r, 'data', None))
