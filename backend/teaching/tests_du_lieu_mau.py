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
  8. Làm mới neo dữ liệu vào HÔM NAY, giữ giảng viên — và dựng hỏng thì bộ cũ còn nguyên.
"""
from collections import Counter
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common import mail, zalo
from common.clock import local_today
from common.db import q, q1, x
from common.permissions import (
    ROLE_ACADEMIC,
    ROLE_ASSISTANT,
    ROLE_EDITOR,
    ROLE_STUDENT,
    ROLE_TEACHER,
)
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
    # 6 học viên + 3 nhân sự (học vụ, trợ giảng, biên tập — thêm 20/09/2026 để
    # bộ mẫu có đủ sáu vai). Giảng viên KHÔNG phải tài khoản mẫu.
    assert so['tài khoản mẫu'] == 9 and so['lớp mẫu'] == 2
    for k in ('buổi học', 'điểm danh', 'bài tập', 'bài nộp', 'tiến độ bài học', 'ghi danh',
              'sự kiện học tập', 'kết quả thi tại trung tâm', 'nhật ký XP ngày'):
        assert so[k] > 0, 'thiếu khối: %s' % k
    em = q('SELECT email, role FROM users WHERE is_demo')
    assert all(r['email'].endswith('@example.com') for r in em)
    assert Counter(r['role'] for r in em) == {ROLE_STUDENT: 6, ROLE_ACADEMIC: 1,
                                              ROLE_ASSISTANT: 1, ROLE_EDITOR: 1}
    # Trợ giảng mẫu phải Ở TRONG một lớp mẫu — không thì vai ấy không thấy gì.
    tg = q1('''SELECT m.class_id FROM class_members m JOIN users u ON u.id = m.user_id
               JOIN classes c ON c.id = m.class_id
               WHERE u.is_demo AND u.role = %s AND c.is_demo AND m.left_at IS NULL''',
            (ROLE_ASSISTANT,))
    assert tg, 'trợ giảng mẫu chưa được xếp vào lớp mẫu nào'
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
    assert truoc['tài khoản mẫu'] == 7 and truoc['sự kiện học tập'] > 0
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


def test_lam_moi_neo_vao_HOM_NAY_va_giu_giang_vien(sach):
    """Bộ dựng 20 ngày trước trông như trung tâm đã ngừng hoạt động; làm mới phải kéo
    hoạt động về hôm nay mà không đổi người phụ trách lớp mẫu."""
    M.tao(giang_vien_id=sach.id, so_em_moi_lop=2, hom_nay=local_today() - timedelta(days=20))
    assert M.hoat_dong_gan_nhat() <= local_today() - timedelta(days=19)

    truoc, sau = M.lam_moi(so_em_moi_lop=2)
    assert truoc['tài khoản mẫu'] == sau['tài khoản mẫu'] == 7
    assert M.hoat_dong_gan_nhat() >= local_today() - timedelta(days=1), 'vẫn neo vào ngày dựng cũ'
    assert {r['teacher_id'] for r in q('SELECT teacher_id FROM classes WHERE is_demo')} == {sach.id}, \
        'làm mới lặng lẽ đổi giảng viên phụ trách lớp mẫu'


def test_lam_moi_dung_HONG_thi_bo_cu_con_nguyen(sach, monkeypatch):
    """Neon rớt giữa lúc dựng: không được để lại một trung tâm không có lớp mẫu nào."""
    M.tao(giang_vien_id=sach.id, so_em_moi_lop=2)
    truoc = M.dem()

    def hong(**_):
        raise M.LoiDuLieuMau('giả lập dựng hỏng giữa chừng')

    monkeypatch.setattr(M, 'tao', hong)
    with pytest.raises(M.LoiDuLieuMau):
        M.lam_moi(so_em_moi_lop=2)
    assert M.dem() == truoc, 'dựng hỏng mà bộ cũ đã bị gỡ'


def test_bo_mau_co_bai_NOI_VAO_khung_de_man_chuong_trinh_noi_duoc_ca_hai_ve(sach):
    """§74 cần bộ mẫu có CẢ HAI trạng thái, không chỉ một.

    Màn Chương trình lớp trả lời "buổi này đã giao bài chưa". Nếu bộ trình diễn không nối
    bài nào vào khung thì mọi mục đều hiện "Chưa giao bài" — khách xem sẽ kết luận là tính
    năng chỉ biết nói "chưa", vì họ không có cách nào thấy vế kia. Đo trên dev 27/09 trước
    khi vá: 6 mục cần bài, **0** mục có bài nối vào.

    Một bài là đủ: một mục "Đã giao", những mục còn lại "Chưa giao bài".
    """
    M.tao(giang_vien_id=sach.id, so_em_moi_lop=2)
    noi = q('''SELECT a.class_id, a.syllabus_item_id, i.kind
                 FROM assignments a
                 JOIN classes c ON c.id = a.class_id AND c.is_demo
                 JOIN syllabus_items i ON i.id = a.syllabus_item_id''')
    assert noi, 'bộ mẫu không nối bài nào vào mục khung — màn Chương trình chỉ nói được "chưa"'
    assert all(r['kind'] in ('bai_tap', 'kiem_tra') for r in noi), \
        'chỉ nối vào mục CẦN bài, không nối vào mục chủ đề'
    # Và vẫn còn mục chưa giao để hai vế cùng lên màn.
    con = q1('''SELECT COUNT(*) AS n FROM syllabus_items i
                  JOIN syllabus_sessions ss ON ss.id = i.session_id
                  JOIN classes c ON c.syllabus_version_id = ss.version_id AND c.is_demo
                 WHERE i.kind IN ('bai_tap', 'kiem_tra')
                   AND NOT EXISTS (SELECT 1 FROM assignments a
                                    WHERE a.class_id = c.id AND a.syllabus_item_id = i.id)''')['n']
    assert con > 0, 'nối hết thì không còn vế "Chưa giao bài" để cho khách thấy'


def test_bo_mau_co_BAI_KIEM_TRA_de_nut_nhap_diem_hien_ra(sach):
    """Không có bài `kiem_tra` thì nút "Nhập điểm" (V-h) không bao giờ hiện trong buổi demo.

    Đo trên dev 27/09 trước khi vá: bài mẫu toàn bộ là `bai_tap`, **0** bài `kiem_tra`. Màn
    bài tập chỉ hiện "Nhập điểm" cho bài kiểm tra trên lớp — tức một ô của bảng nghiệm thu
    trông như chưa làm, dù mã đã chạy từ 25/09.

    Bài kiểm tra mẫu còn phải có ĐIỂM (khách mở ra mà bảng trống thì cũng như không) và
    còn chừa ít nhất một em chưa chấm, để con số "còn N bài chưa chấm" có thật.
    """
    M.tao(giang_vien_id=sach.id, so_em_moi_lop=3)
    kt = q('''SELECT a.id, a.class_id, a.held_on, a.syllabus_item_id
                FROM assignments a JOIN classes c ON c.id = a.class_id AND c.is_demo
               WHERE a.kind = 'kiem_tra' ''')
    assert kt, 'bộ mẫu không có bài kiểm tra nào — nút "Nhập điểm" không hiện'
    assert all(r['held_on'] for r in kt), 'bài kiểm tra trên lớp phải có ngày kiểm tra'
    diem = q1('''SELECT COUNT(*) FILTER (WHERE s.score IS NOT NULL) AS da_cham,
                        COUNT(*) FILTER (WHERE s.score IS NULL) AS chua_cham
                   FROM submissions s WHERE s.assignment_id = ANY(%s)''',
              ([r['id'] for r in kt],))
    assert diem['da_cham'] > 0, 'bài kiểm tra mẫu chưa có điểm nào'


def test_bo_mau_co_BAN_GHI_va_HOC_LIEU_de_ba_dong_nghiem_thu_khong_trong_rong(sach):
    """Dòng 22, 29, 30 của bảng khách đều đọc từ dữ liệu — mã chạy mà bộ mẫu rỗng thì khách
    mở ra thấy trống, và kết luận là chưa làm.

    Đo trên dev 27/09 trước khi vá: lớp mẫu có **0** buổi mang link bản ghi, **0** lượt xem,
    **0** học liệu. Cùng loại lỗi với bài kiểm tra vắng mặt — không phải lỗi mã, nhưng nó
    hỏng buổi nghiệm thu y như một lỗi.

    Ba con số phải có, không chỉ "khác 0":
      · **bản ghi** gắn vào buổi ĐÃ DẠY (gắn vào buổi chưa diễn ra là nói dối);
      · **lượt xem chưa đủ cả lớp** — trợ giảng cần thấy "còn N em chưa mở", và một lớp
        100 % đã xem thì không cho thấy việc còn phải làm;
      · **học liệu** có cả loại gắn vào buổi lẫn loại ở kho chung của lớp, và có ít nhất
        một mục ĐANG ẨN để cho thấy việc mở dần theo tiến độ.
    """
    M.tao(giang_vien_id=sach.id, so_em_moi_lop=3)

    bg = q('''SELECT s.id, s.starts_at FROM class_sessions s
                JOIN classes c ON c.id = s.class_id AND c.is_demo
               WHERE s.recording_url IS NOT NULL''')
    assert bg, 'bộ mẫu không có bản ghi nào — dòng 22 và 29 mở ra là trống'
    chua_dien_ra = q1('''SELECT COUNT(*) AS n FROM class_sessions s
                           JOIN classes c ON c.id = s.class_id AND c.is_demo
                          WHERE s.recording_url IS NOT NULL AND s.starts_at > now()''')['n']
    assert chua_dien_ra == 0, 'có bản ghi gắn vào buổi CHƯA diễn ra'

    xem = q1('''SELECT COUNT(*) AS n FROM recording_views v
                  JOIN class_sessions s ON s.id = v.session_id
                  JOIN classes c ON c.id = s.class_id AND c.is_demo''')['n']
    assert xem > 0, 'không em nào đã mở bản ghi — khối "ai chưa mở" không có gì để đếm'
    thanh_vien = q1('''SELECT COUNT(*) AS n FROM class_members m
                         JOIN classes c ON c.id = m.class_id AND c.is_demo
                        WHERE m.left_at IS NULL''')['n']
    assert xem < thanh_vien * len(bg), 'mọi em đều đã xem mọi buổi — không còn ai để nhắc'

    hl = q('''SELECT h.id, h.session_id, h.an FROM hoc_lieu h
                JOIN classes c ON c.id = h.class_id AND c.is_demo''')
    assert hl, 'bộ mẫu không có học liệu nào — dòng 30 mở ra là trống'
    assert any(r['session_id'] for r in hl), 'không tài liệu nào gắn vào một buổi'
    assert any(not r['session_id'] for r in hl), 'không tài liệu nào ở kho chung của lớp'
    assert any(r['an'] for r in hl), 'không tài liệu nào đang ẩn — không thấy việc mở dần'
