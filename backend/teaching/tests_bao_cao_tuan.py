"""Tờ báo cáo phụ huynh — ba sửa của vòng 30 (17/09/2026).

Chạy trên DB thật, trong giao dịch CUỘN LẠI (`conftest.py`).

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. **Nhịp từng tuần cộng lại ĐÚNG tổng kỳ.** Khối từng tuần và các ô tổng kỳ
     nằm cạnh nhau trên cùng tờ giấy; lệch một buổi là phụ huynh không tin ô nào.
     Nên cả hai lấy từ `_buoi_cua_em`, và phép kiểm dựng đủ các ca khó của
     `_chuyen_can`: muộn, vắng có phép, tick sót em, buổi chưa tick, và một buổi
     rơi đúng ngày ĐẦU kỳ (ngày lẻ bị gộp vào tuần kế).
  2. **Bài tập đếm theo ngày EM NỘP, chỉ bài của lớp này.** Sự kiện `assignment`
     ghi lúc giảng viên chấm — dùng nó là đo nhịp của giảng viên.
  3. **Hợp phần chỉ gồm khoá em học.** Tờ báo cáo từng in "0/23 bài (0%)" cho
     hợp phần em không học ở trung tâm (đo trên lớp mẫu 17/09).
  4. **Email phụ huynh tới được màn giảng viên, KHÔNG tới đường công khai.**
"""
from datetime import date, timedelta

import pytest

from common.clock import local_now, local_today
from common.db import q1, x
from common.permissions import ROLE_STUDENT, ROLE_TEACHER
from teaching.parent_link import ParentReportLinkView, PublicParentReportView
from teaching.parent_report import DEFAULT_WEEKS, NGAY_LE_TOI_THIEU, _cac_tuan, dung_bao_cao
from teaching.tests_parent_link import _goi, _nguoi

# ── 1a. Chia tuần — hàm thuần, không CSDL ─────────────────────────────────

def test_ky_mac_dinh_ra_bon_tuan_ngay_le_gop_vao_tuan_dau():
    den = date(2026, 9, 17)
    tuan = _cac_tuan(den - timedelta(weeks=DEFAULT_WEEKS), den)
    assert tuan == [(date(2026, 8, 20), date(2026, 8, 27)),
                    (date(2026, 8, 28), date(2026, 9, 3)),
                    (date(2026, 9, 4), date(2026, 9, 10)),
                    (date(2026, 9, 11), date(2026, 9, 17))]


@pytest.mark.parametrize('so_ngay', range(1, 71))
def test_cac_tuan_phu_kin_ky_khong_ho_khong_chong(so_ngay):
    den = date(2026, 9, 17)
    tu = den - timedelta(days=so_ngay - 1)
    tuan = _cac_tuan(tu, den)
    assert tuan[0][0] == tu and tuan[-1][1] == den
    for (_, b1), (a2, _) in zip(tuan, tuan[1:], strict=False):
        assert a2 == b1 + timedelta(days=1), 'hở hoặc chồng giữa hai tuần'
    dai = [(b - a).days + 1 for a, b in tuan]
    assert all(d == 7 for d in dai[1:]), 'chỉ khối ĐẦU được lệch 7 ngày'
    assert min(so_ngay, NGAY_LE_TOI_THIEU) <= dai[0] <= 7 + NGAY_LE_TOI_THIEU - 1


# ── 1b–4. Trên CSDL ────────────────────────────────────────────────────────

@pytest.fixture
def lop(db):
    gv = _nguoi('GV Tuan', ROLE_TEACHER)
    em = _nguoi('HV Tuan', ROLE_STUDENT, parent_name='Me Tuan',
                parent_email='me.tuan@example.com')
    c = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
           "VALUES ('Lop tuan','hsa_quantitative',%s,'active') RETURNING id", (gv.id,))
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s)',
      (c['id'], em.id, local_now() - timedelta(days=60)))
    x("INSERT INTO enrollments (user_id, course_id) VALUES (%s, 'hsa_quantitative')", (em.id,))
    return {'lop': c['id'], 'gv': gv, 'em': em}


def _buoi(lop, ngay_truoc, tick=True, trang_thai=None):
    nay = local_now()
    s = q1("INSERT INTO class_sessions (class_id, starts_at, status, attendance_taken_at, created_by) "
           "VALUES (%s,%s,'planned',%s,%s) RETURNING id",
           (lop['lop'], nay - timedelta(days=ngay_truoc), nay if tick else None, lop['gv'].id))
    if trang_thai:
        x('INSERT INTO attendance (session_id, user_id, status, marked_at, marked_by) '
          'VALUES (%s,%s,%s,%s,%s)', (s['id'], lop['em'].id, trang_thai, nay, lop['gv'].id))


def _su_kien(uid, kind, ngay_truoc, khoa=None, **cot):
    ngay = local_today() - timedelta(days=ngay_truoc)
    x('INSERT INTO learning_events (user_id, dedup_key, occurred_at, event_date, kind, course_id, '
      'topic, ref_type, ref_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
      (uid, khoa or 'tuan:%s:%s' % (kind, ngay_truoc), local_now() - timedelta(days=ngay_truoc),
       ngay, kind, cot.get('course_id'), cot.get('topic'), cot.get('ref_type'), cot.get('ref_id')))


def _to(lop):
    den = local_today()
    bc, loi = dung_bao_cao(lop['lop'], lop['em'].id, den - timedelta(weeks=DEFAULT_WEEKS), den)
    assert loi is None, loi
    return bc


def test_tung_tuan_cong_lai_dung_tong_ky(lop):
    for truoc, st in ((1, 'present'), (3, 'late'), (8, 'absent'), (10, 'excused'),
                      (15, 'present'), (22, 'present'),
                      (28, 'present')):          # ngày ĐẦU kỳ — ngày lẻ gộp vào tuần đầu
        _buoi(lop, truoc, trang_thai=st)
    _buoi(lop, 17)                               # tick cả lớp nhưng sót em này
    _buoi(lop, 24, tick=False)                   # chưa tick
    for truoc in (0, 5, 9, 20, 28):
        _su_kien(lop['em'].id, 'lesson', truoc)
    _su_kien(lop['em'].id, 'lesson', 29)         # NGOÀI kỳ
    _su_kien(lop['em'].id, 'drill', 2)

    bc = _to(lop)
    cc, tuan = bc['attendance'], bc['weekly']['weeks']
    assert len(tuan) == 4 and bc['weekly']['omitted'] == 0
    assert sum(w['attended'] for w in tuan) == cc['present'] + cc['late'] == 5
    assert sum(w['attendanceCounted'] for w in tuan) == \
        cc['present'] + cc['late'] + cc['absent'] + cc['excused'] == 7
    assert sum(w['lessons'] for w in tuan) == bc['study']['lessonsDone'] == 5
    assert [w['drills'] for w in tuan] == [0, 0, 0, 1]
    # Buổi ngày đầu kỳ và bài ngày đầu kỳ rơi vào khối đầu (8 ngày), không mất.
    assert tuan[0]['days'] == 8 and tuan[0]['attended'] == 2 and tuan[0]['lessons'] == 1


def test_bai_tap_tinh_theo_ngay_NOP_va_chi_bai_cua_lop_nay(lop):
    nay = local_now()
    a = q1("INSERT INTO assignments (class_id, title, status) VALUES (%s,'Bai tuan','open') "
           "RETURNING id", (lop['lop'],))
    x('INSERT INTO submissions (assignment_id, user_id, submitted_at, content, graded_at, score) '
      'VALUES (%s,%s,%s,%s,%s,%s)', (a['id'], lop['em'].id, nay - timedelta(days=9), 'bai', nay, 8))
    # Giảng viên chấm HÔM NAY → sự kiện `assignment` mang ngày hôm nay.
    _su_kien(lop['em'].id, 'assignment', 0, ref_type='assignment', ref_id=str(a['id']))

    khac = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
              "VALUES ('Lop khac','hsa_quantitative',%s,'active') RETURNING id", (lop['gv'].id,))
    b = q1("INSERT INTO assignments (class_id, title, status) VALUES (%s,'Bai lop khac','open') "
           "RETURNING id", (khac['id'],))
    x('INSERT INTO submissions (assignment_id, user_id, submitted_at, content) VALUES (%s,%s,%s,%s)',
      (b['id'], lop['em'].id, nay - timedelta(days=2), 'bai'))

    tuan = _to(lop)['weekly']['weeks']
    assert [w['submissions'] for w in tuan] == [0, 0, 1, 0], \
        'bài nộp 9 ngày trước rơi vào tuần thứ ba; bài lớp khác và ngày chấm không được tính'


def test_hop_phan_chi_gom_khoa_em_hoc_hoac_da_co_bai_lam(lop):
    cd = _to(lop)['topics']
    assert [k['id'] for k in cd['courses']] == ['hsa_quantitative'], \
        'em chỉ học Định lượng mà tờ báo cáo in cả hợp phần em không học'
    so_chu_de = q1("SELECT COUNT(DISTINCT module) AS n FROM lessons "
                   "WHERE course_id='hsa_quantitative' AND module IS NOT NULL AND module <> ''")['n']
    assert cd['total'] == so_chu_de

    # Tự học thêm một bài Định tính → hợp phần ấy được in (công thật của em).
    bai = q1("SELECT id FROM lessons WHERE course_id='hsa_verbal' ORDER BY sort_order LIMIT 1")
    x("INSERT INTO lesson_progress (user_id, course_id, lesson_id, status, completed_at) "
      "VALUES (%s,'hsa_verbal',%s,'completed',now())", (lop['em'].id, bai['id']))
    assert [k['id'] for k in _to(lop)['topics']['courses']] == ['hsa_quantitative', 'hsa_verbal']


def test_email_phu_huynh_toi_man_giang_vien_nhung_KHONG_toi_duong_cong_khai(lop):
    bc = _to(lop)
    assert bc['parent']['email'] == 'me.tuan@example.com'

    kq = _goi(ParentReportLinkView, 'post', {}, ai=lop['gv'], class_id=lop['lop'], user_id=lop['em'].id)
    assert kq.status_code == 201, kq.data
    assert kq.data['parentEmail'] == 'me.tuan@example.com'

    cong_khai = _goi(PublicParentReportView, 'get', ai=None, token=kq.data['token'])
    assert cong_khai.status_code == 200
    assert cong_khai.data['parent'] == {'name': 'Me Tuan'}, cong_khai.data['parent']
    assert 'weekly' in cong_khai.data, 'phụ huynh mở link phải thấy khối từng tuần'


# ── 5. Đầu kỳ MẶC ĐỊNH không sớm hơn ngày khai giảng / ngày em vào lớp ──────
# Vá 22/09/2026 (agent GV→PH F7): lớp khai giảng 13/09, tờ ngày 21/09 in kỳ
# "24/08 – 21/09" → bảng từng tuần mở đầu bằng hai tuần toàn số 0, phụ huynh đọc
# thành "hai tuần đầu con không học gì".

def _to_goc(lop, url='/x'):
    from teaching.parent_report import ParentReportView
    kq = _goi(ParentReportView, 'get', ai=lop['gv'], url=url, class_id=lop['lop'], user_id=lop['em'].id)
    assert kq.status_code == 200, kq.data
    return kq.data


def test_ky_mac_dinh_bat_dau_tu_ngay_khai_giang(lop):
    khai_giang = local_today() - timedelta(days=8)
    x('UPDATE classes SET starts_on=%s WHERE id=%s', (khai_giang, lop['lop']))
    assert _to_goc(lop)['period']['from'] == khai_giang.isoformat(), \
        'kỳ mặc định vẫn bắt đầu TRƯỚC ngày khai giảng'
    # Link cấp cho phụ huynh dùng cùng kỳ.
    kq = _goi(ParentReportLinkView, 'post', {}, ai=lop['gv'], class_id=lop['lop'], user_id=lop['em'].id)
    assert kq.status_code == 201, kq.data
    ky = q1('SELECT period_from FROM parent_report_links WHERE id=%s', (kq.data['id'],))
    assert ky['period_from'] == khai_giang


def test_ky_mac_dinh_bat_dau_tu_ngay_em_vao_lop(lop):
    vao = local_today() - timedelta(days=5)
    x('UPDATE class_members SET joined_at=%s WHERE class_id=%s AND user_id=%s',
      (vao, lop['lop'], lop['em'].id))
    assert _to_goc(lop)['period']['from'] == vao.isoformat()


def test_ky_nguoi_dung_CHON_thi_giu_nguyen(lop):
    x('UPDATE classes SET starts_on=%s WHERE id=%s', (local_today() - timedelta(days=8), lop['lop']))
    tu = local_today() - timedelta(days=40)
    assert _to_goc(lop, url='/x?from=%s' % tu.isoformat())['period']['from'] == tu.isoformat()


def test_ky_mac_dinh_khong_doi_khi_lop_khai_giang_tu_lau(lop):
    x('UPDATE classes SET starts_on=%s WHERE id=%s', (local_today() - timedelta(days=90), lop['lop']))
    mac_dinh = local_today() - timedelta(weeks=DEFAULT_WEEKS)
    assert _to_goc(lop)['period']['from'] == mac_dinh.isoformat()
