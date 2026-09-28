"""BÁO CÁO CHÉO MÔN × LỚP — bảng TopHSA dòng 6, ô "Kết quả theo môn, hoàn thành bài tập".

Khách hỏi được "lớp này em nào chưa nộp bài" và "khoá này điểm thế nào", nhưng chưa hỏi
được "môn Tư duy Định lượng đang thế nào SO VỚI môn khác, và trong môn ấy lớp nào tụt".
Bộ này ghim bảy chỗ dễ sai của câu trả lời đó:

  1. CHUẨN HOÁ THANG. Một bài thang 10 và một bài thang 100 KHÔNG được cộng thô.
     Cảnh: điểm 10/10 và 50/100 → trung bình 75 %, chứ không phải 30.
  2. CHIA CHO 0 ra `None` (màn hình vẽ `—`), không ra 0 %. "Lớp chưa giao bài nào" và
     "lớp giao bài mà không em nào nộp" là hai câu trả lời khác nhau.
  3. LỚP RỖNG VẪN CÓ DÒNG. Lớp biến mất khỏi báo cáo trông như đã đóng.
  4. HỌC VIÊN ĐÃ RỜI LỚP (`class_members.left_at`) không vào tử số lẫn mẫu số —
     cùng luật đếm với `teaching/assignments.py`.
  5. HÀNG RÀO QUYỀN: quản trị viên + học vụ xem được; giảng viên / trợ giảng / học viên
     KHÔNG (đây là số toàn trung tâm).
  6. BỘ LỌC môn / đợt / khoảng ngày thật sự lọc.
  7. DÒNG TỔNG của môn và của trung tâm cộng từ SỐ THÔ, không phải trung bình của
     các phần trăm.

Tháng 05/2032 — không dữ liệu thật nào nằm đó. Đi qua VIEW THẬT (không đọc thẳng bảng sau
một lời gọi API: đọc thẳng dùng kết nối khác nên test xanh khi chạy riêng, đỏ khi chạy cả
bộ — đã có tiền lệ 26/09/2026). CSDL cuộn lại sau mỗi test (`conftest.py`).
"""
import datetime
import io
import uuid

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1, x
from common.permissions import (
    ROLE_ACADEMIC,
    ROLE_ADMIN,
    ROLE_ASSISTANT,
    ROLE_STUDENT,
    ROLE_TEACHER,
)

f = APIRequestFactory()
pytestmark = pytest.mark.django_db
_luc = datetime.datetime.fromisoformat

#: Kỳ xem mặc định của mọi phép kiểm — trọn tháng 05/2032.
KY = '?tu=2032-05-01&den=2032-05-31'


def _nguoi(vai, ten):
    r = q1('INSERT INTO users (name, email, password, role, streak) '
           'VALUES (%s, %s, %s, %s, 0) RETURNING id',
           (ten, 'bcc_%s@example.com' % uuid.uuid4().hex[:10], 'x', vai))
    return User.objects.get(id=r['id'])


def _mon(ten):
    ma = 'bcc_%s' % uuid.uuid4().hex[:8]
    x('INSERT INTO courses (id, title) VALUES (%s, %s)', (ma, ten))
    return ma


def _dot(ten):
    return q1('INSERT INTO terms (name, code) VALUES (%s, %s) RETURNING id',
              (ten, 'BCC%s' % uuid.uuid4().hex[:6]))['id']


def _lop(ten, mon=None, dot=None, gv=None):
    return q1("INSERT INTO classes (name, course_id, term_id, teacher_id, status) "
              "VALUES (%s, %s, %s, %s, 'active') RETURNING id", (ten, mon, dot, gv.id if gv else None))['id']


def _vao(lop, u, tu='2032-04-01T00:00', den=None):
    x('INSERT INTO class_members (class_id, user_id, joined_at, left_at, leave_reason) '
      'VALUES (%s, %s, %s, %s, %s)',
      (lop, u.id, _luc(tu), _luc(den) if den else None, 'dropped' if den else None))


def _bai(lop, thang_diem, han, trang_thai='open', loai='bai_tap', mon=None):
    return q1("INSERT INTO assignments (class_id, title, course_id, due_at, max_score, status, kind) "
              "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
              (lop, 'BCC bài %s' % uuid.uuid4().hex[:6], mon, _luc(han), thang_diem,
               trang_thai, loai))['id']


def _nop(bai, u, nop_luc='2032-05-11T08:00', diem=None, cham_luc=None):
    x('INSERT INTO submissions (assignment_id, user_id, submitted_at, score, graded_at) '
      'VALUES (%s, %s, %s, %s, %s)',
      (bai, u.id, _luc(nop_luc) if nop_luc else None, diem,
       _luc(cham_luc) if cham_luc else None))


def _buoi(lop, bat_dau, trang_thai='done'):
    return q1('INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status, '
              'attendance_taken_at) VALUES (%s, %s, 90, %s, %s) RETURNING id',
              (lop, _luc(bat_dau), trang_thai, _luc(bat_dau)))['id']


def _tick(buoi, u, trang_thai):
    x('INSERT INTO attendance (session_id, user_id, status) VALUES (%s, %s, %s)',
      (buoi, u.id, trang_thai))


def _goi(ai, qs=KY):
    from teaching.bao_cao_cheo import BaoCaoCheoView
    req = f.get('/x' + qs)
    force_authenticate(req, user=ai)
    return BaoCaoCheoView.as_view()(req)


def _bang(r):
    """Phản hồi 200 → (dict môn theo mã, dict lớp theo id, dòng tổng trung tâm)."""
    assert r.status_code == 200, getattr(r, 'data', r)
    mon = {m['courseId']: m for m in r.data['mon']}
    lop = {c['classId']: c for m in r.data['mon'] for c in m['lop']}
    return mon, lop, r.data['tong']


@pytest.fixture
def canh(db):
    """Hai môn, bốn lớp, hai thang điểm, một em đã rời lớp, một buổi ngoài kỳ xem.

    · L1 (môn ĐL, đợt 1) — 2 em đang học + 1 em ĐÃ RỜI LỚP. Hai bài khác thang:
      bài A thang 10 (em1 10 điểm = 100 %, em2 chưa nộp, em3-đã-rời 0 điểm),
      bài B thang 100 (em1 50 điểm = 50 %, em2 nộp mà chưa chấm).
      → phải nộp 4 · đã nộp 3 (75 %) · đã chấm 2/3 (67 %) · điểm TB (100+50)/2 = 75.
      Cộng THÔ sẽ ra (10+50)/2 = 30 — đó là đột biến cần bị giết.
      Chuyên cần: một buổi trong kỳ (em1 có mặt, em2 vắng) = 50 %; một buổi THÁNG 4 cả
      hai có mặt (ngoài kỳ xem) và một buổi ĐÃ HUỶ — cả hai không được tính.
    · L2 (môn ĐL, đợt 1) — 1 em, KHÔNG bài nào: mọi tỉ lệ `None`, dòng vẫn phải có.
    · L3 (môn ĐT, đợt 1) — 1 em, một bài thang 10 hạn THÁNG 4 (ngoài kỳ xem).
    · L4 (môn ĐL, đợt 2) — 1 em, một bài đã nộp: chỉ hiện khi KHÔNG lọc đợt 1.
    """
    d = uuid.uuid4().hex[:6]
    qtv = _nguoi(ROLE_ADMIN, 'BCC QTV %s' % d)
    hv = _nguoi(ROLE_ACADEMIC, 'BCC HV %s' % d)
    gv = _nguoi(ROLE_TEACHER, 'BCC GV %s' % d)
    tg = _nguoi(ROLE_ASSISTANT, 'BCC TG %s' % d)
    em1 = _nguoi(ROLE_STUDENT, 'BCC Em1 %s' % d)
    em2 = _nguoi(ROLE_STUDENT, 'BCC Em2 %s' % d)
    em3 = _nguoi(ROLE_STUDENT, 'BCC Em3 %s' % d)      # ĐÃ RỜI LỚP
    em4 = _nguoi(ROLE_STUDENT, 'BCC Em4 %s' % d)
    em5 = _nguoi(ROLE_STUDENT, 'BCC Em5 %s' % d)
    em6 = _nguoi(ROLE_STUDENT, 'BCC Em6 %s' % d)

    mon_dl, mon_dt = _mon('BCC Định lượng %s' % d), _mon('BCC Định tính %s' % d)
    dot1, dot2 = _dot('BCC đợt 1 %s' % d), _dot('BCC đợt 2 %s' % d)

    l1 = _lop('BCC L1 %s' % d, mon_dl, dot1, gv)
    l2 = _lop('BCC L2 rỗng %s' % d, mon_dl, dot1, gv)
    l3 = _lop('BCC L3 %s' % d, mon_dt, dot1, gv)
    l4 = _lop('BCC L4 đợt sau %s' % d, mon_dl, dot2, gv)

    _vao(l1, em1)
    _vao(l1, em2)
    _vao(l1, em3, den='2032-05-05T00:00')             # rời lớp giữa kỳ
    _vao(l2, em4)
    _vao(l3, em5)
    _vao(l4, em6)

    bai_a = _bai(l1, 10, '2032-05-10T23:59')          # thang 10
    bai_b = _bai(l1, 100, '2032-05-20T23:59')         # thang 100
    _nop(bai_a, em1, diem=10, cham_luc='2032-05-12T08:00')
    _nop(bai_a, em3, diem=0, cham_luc='2032-05-12T08:00')   # đã rời lớp — không tính
    _nop(bai_b, em1, diem=50, cham_luc='2032-05-21T08:00')
    _nop(bai_b, em2)                                   # nộp, chưa chấm

    bai_t4 = _bai(l3, 10, '2032-04-10T23:59')          # ngoài kỳ xem
    _nop(bai_t4, em5, nop_luc='2032-04-11T08:00', diem=10, cham_luc='2032-04-12T08:00')

    bai_l4 = _bai(l4, 10, '2032-05-15T23:59')
    _nop(bai_l4, em6, diem=8, cham_luc='2032-05-16T08:00')

    b_trong = _buoi(l1, '2032-05-08T19:00')
    _tick(b_trong, em1, 'present')
    _tick(b_trong, em2, 'absent')
    b_ngoai = _buoi(l1, '2032-04-08T19:00')            # ngoài kỳ xem
    _tick(b_ngoai, em1, 'present')
    _tick(b_ngoai, em2, 'present')
    b_huy = _buoi(l1, '2032-05-15T19:00', 'cancelled')  # huỷ — không tính
    _tick(b_huy, em1, 'absent')
    _tick(b_huy, em2, 'absent')

    return {'qtv': qtv, 'hv': hv, 'gv': gv, 'tg': tg,
            'em1': em1, 'em2': em2, 'em3': em3,
            'monDL': mon_dl, 'monDT': mon_dt, 'dot1': dot1, 'dot2': dot2,
            'l1': l1, 'l2': l2, 'l3': l3, 'l4': l4}


# ── 1. Chuẩn hoá thang điểm ──────────────────────────────────────────────────

def test_diem_trung_binh_chuan_hoa_theo_thang(canh):
    """10/10 và 50/100 → 75 %, KHÔNG phải (10+50)/2 = 30."""
    _, lop, _ = _bang(_goi(canh['hv'], KY))
    l1 = lop[canh['l1']]
    assert l1['soDiem'] == 2, l1
    assert l1['diemTB'] == 75, l1


def test_dong_tong_mon_cong_tu_so_tho_khong_phai_trung_binh_cua_phan_tram(canh):
    """Môn ĐL: L1 có 2 điểm (100, 50), L2 không có điểm nào → tổng môn = 75.

    Trung bình của các phần trăm ở cấp LỚP sẽ cho (75 + None)/1 = 75 ở đây — bằng nhau
    một cách tình cờ, nên phép kiểm phải ghim thêm tử/mẫu thô mới bắt được lỗi.
    """
    mon, _, _ = _bang(_goi(canh['hv'], KY + '&term_id=%d' % canh['dot1']))
    dl = mon[canh['monDL']]['tong']
    assert (dl['phaiNop'], dl['daNop'], dl['daCham']) == (4, 3, 2), dl
    assert (dl['tiLeNop'], dl['tiLeCham']) == (75, 67), dl
    assert (dl['soDiem'], dl['diemTB']) == (2, 75), dl
    assert dl['dangHoc'] == 3, dl          # 2 em ở L1 + 1 em ở L2


# ── 2. Chia cho 0 ra `—`, không ra 0 % ───────────────────────────────────────

def test_lop_chua_giao_bai_thi_ti_le_la_gach_khong_phai_0(canh):
    _, lop, _ = _bang(_goi(canh['hv'], KY))
    l2 = lop[canh['l2']]
    assert (l2['phaiNop'], l2['daNop'], l2['daCham'], l2['soDiem']) == (0, 0, 0, 0), l2
    assert l2['tiLeNop'] is None, l2
    assert l2['tiLeCham'] is None, l2
    assert l2['diemTB'] is None, l2
    assert l2['tiLeChuyenCan'] is None, l2


def test_khong_em_nao_nop_thi_ti_le_la_0_khong_phai_gach(canh):
    """Mặt kia của cùng một đồng xu: có mẫu số thì 0 % phải là 0 %, không thành `—`."""
    l = _lop('BCC L5 %s' % uuid.uuid4().hex[:6], canh['monDT'], canh['dot1'])
    em = _nguoi(ROLE_STUDENT, 'BCC Em7 %s' % uuid.uuid4().hex[:6])
    _vao(l, em)
    _bai(l, 10, '2032-05-10T23:59')
    _, lop, _ = _bang(_goi(canh['hv'], KY))
    r = lop[l]
    assert (r['phaiNop'], r['daNop']) == (1, 0), r
    assert r['tiLeNop'] == 0, r
    assert r['tiLeCham'] is None, r        # chưa bài nào nộp → chưa có gì để chấm


# ── 3. Lớp rỗng vẫn có dòng ──────────────────────────────────────────────────

def test_lop_khong_co_bai_va_khong_co_buoi_van_co_mat(canh):
    mon, lop, _ = _bang(_goi(canh['hv'], KY))
    assert canh['l2'] in lop, 'lớp rỗng đã rơi khỏi báo cáo'
    assert {c['classId'] for c in mon[canh['monDL']]['lop']} >= {canh['l1'], canh['l2']}


def test_lop_khong_co_hoc_vien_nao_van_co_mat(canh):
    l = _lop('BCC L6 không em %s' % uuid.uuid4().hex[:6], canh['monDT'], canh['dot1'])
    _, lop, _ = _bang(_goi(canh['hv'], KY))
    assert l in lop, 'lớp chưa xếp em nào đã rơi khỏi báo cáo'
    assert lop[l]['dangHoc'] == 0, lop[l]


# ── 4. Học viên đã rời lớp không tính ────────────────────────────────────────

def test_hoc_vien_da_roi_lop_khong_vao_tu_so_lan_mau_so(canh):
    """em3 đã rời lớp: bài của em ấy không vào `phaiNop`/`daNop`/`diemTB`.

    Thiếu vế `left_at IS NULL` thì `phaiNop` thành 6 (3 em × 2 bài), `daNop` thành 4 và
    điểm 0 của em ấy kéo `diemTB` từ 75 xuống 50.
    """
    _, lop, _ = _bang(_goi(canh['hv'], KY))
    l1 = lop[canh['l1']]
    assert l1['dangHoc'] == 2, l1
    assert (l1['phaiNop'], l1['daNop'], l1['daCham']) == (4, 3, 2), l1
    assert (l1['tiLeNop'], l1['tiLeCham']) == (75, 67), l1
    assert (l1['soDiem'], l1['diemTB']) == (2, 75), l1


# ── 5. Chuyên cần trong kỳ xem ───────────────────────────────────────────────

def test_chuyen_can_chi_dem_buoi_trong_ky_va_bo_buoi_huy(canh):
    """Một buổi trong kỳ (1 có mặt / 2 lượt) = 50 %. Buổi tháng 4 và buổi huỷ không tính."""
    _, lop, _ = _bang(_goi(canh['hv'], KY))
    l1 = lop[canh['l1']]
    assert (l1['coMat'], l1['luotDiemDanh']) == (1, 2), l1
    assert l1['tiLeChuyenCan'] == 50, l1


# ── 6. Hàng rào quyền ────────────────────────────────────────────────────────

def test_quan_tri_vien_va_hoc_vu_xem_duoc(canh):
    for ai in ('qtv', 'hv'):
        assert _goi(canh[ai], KY).status_code == 200, ai


def test_giang_vien_tro_giang_hoc_vien_bi_403(canh):
    """Đây là số TOÀN TRUNG TÂM — giảng viên chỉ được thấy lớp mình phụ trách."""
    for ai in ('gv', 'tg', 'em1'):
        assert _goi(canh[ai], KY).status_code == 403, ai


# ── 7. Bộ lọc ────────────────────────────────────────────────────────────────

def test_bo_loc_mon_that_su_loc(canh):
    mon, lop, _ = _bang(_goi(canh['hv'], KY + '&course_id=' + canh['monDT']))
    assert set(mon) == {canh['monDT']}, list(mon)
    assert canh['l1'] not in lop and canh['l2'] not in lop
    assert canh['l3'] in lop


def test_bo_loc_dot_that_su_loc(canh):
    _, lop, _ = _bang(_goi(canh['hv'], KY + '&term_id=%d' % canh['dot1']))
    assert canh['l4'] not in lop, 'lớp của đợt khác vẫn lọt vào'
    assert canh['l1'] in lop
    _, lop2, _ = _bang(_goi(canh['hv'], KY + '&term_id=%d' % canh['dot2']))
    assert canh['l4'] in lop2 and canh['l1'] not in lop2


def test_bo_loc_ngay_that_su_loc(canh):
    """Bài hạn tháng 4 chỉ được tính khi kỳ xem là tháng 4."""
    _, thang5, _ = _bang(_goi(canh['hv'], KY))
    assert thang5[canh['l3']]['phaiNop'] == 0, thang5[canh['l3']]
    assert thang5[canh['l3']]['tiLeNop'] is None

    _, thang4, _ = _bang(_goi(canh['hv'], '?tu=2032-04-01&den=2032-04-30'))
    assert thang4[canh['l3']]['phaiNop'] == 1, thang4[canh['l3']]
    assert thang4[canh['l3']]['tiLeNop'] == 100
    assert thang4[canh['l3']]['diemTB'] == 100
    # Hai bài của L1 hạn tháng 5 → tháng 4 không có bài nào
    assert thang4[canh['l1']]['phaiNop'] == 0, thang4[canh['l1']]


def test_ngay_sai_dang_thi_bao_loi_tieng_viet(canh):
    r = _goi(canh['hv'], '?tu=hom-qua&den=2032-05-31')
    assert r.status_code == 400, r.data
    assert 'năm-tháng-ngày' in r.data['error'], r.data
    r2 = _goi(canh['hv'], '?tu=2032-05-31&den=2032-05-01')
    assert r2.status_code == 400 and 'trước' in r2.data['error'], r2.data


# ── 8. Bài NHÁP và bài KIỂM TRA ──────────────────────────────────────────────

def test_bai_nhap_khong_vao_mau_so_phai_nop(canh):
    """`status='draft'` = đang soạn, học viên chưa thấy — chưa thể "phải nộp"."""
    _bai(canh['l2'], 10, '2032-05-10T23:59', trang_thai='draft')
    _, lop, _ = _bang(_goi(canh['hv'], KY))
    assert lop[canh['l2']]['phaiNop'] == 0, lop[canh['l2']]
    assert lop[canh['l2']]['tiLeNop'] is None


def test_bai_kiem_tra_tren_lop_khong_vao_ti_le_nop_nhung_diem_van_tinh(canh):
    """Bài kiểm tra làm TRÊN LỚP không nộp được (§62f) → không vào mẫu số nộp bài.

    Điểm của nó thì vào điểm trung bình của môn: đó là "kết quả theo môn" khách hỏi.
    """
    kt = _bai(canh['l2'], 20, '2032-05-12T23:59', loai='kiem_tra')
    # Em của L2 (bài kiểm tra chấm cho em đang học ở chính lớp ấy).
    em = q1('SELECT user_id FROM class_members WHERE class_id = %s AND left_at IS NULL',
            (canh['l2'],))['user_id']
    _nop(kt, User.objects.get(id=em), nop_luc=None, diem=10, cham_luc='2032-05-13T08:00')
    _, lop, _ = _bang(_goi(canh['hv'], KY))
    l2 = lop[canh['l2']]
    assert l2['phaiNop'] == 0, l2                  # bài kiểm tra KHÔNG vào mẫu số nộp
    assert l2['tiLeNop'] is None, l2
    assert (l2['soDiem'], l2['diemTB']) == (1, 50), l2   # 10/20 = 50 %


# ── 9. Danh mục cho ô lọc lấy TỪ MÁY CHỦ ─────────────────────────────────────

def test_tra_ve_danh_muc_mon_va_dot_cho_o_loc(canh):
    r = _goi(canh['hv'], KY)
    assert r.status_code == 200, r.data
    ma_mon = {m['id'] for m in r.data['monOptions']}
    assert {canh['monDL'], canh['monDT']} <= ma_mon
    ma_dot = {d['id'] for d in r.data['dotOptions']}
    assert {canh['dot1'], canh['dot2']} <= ma_dot


# ── 10. Tải bảng tính ────────────────────────────────────────────────────────

def test_tai_xlsx_cung_bo_loc_va_o_chu_khong_thanh_cong_thuc(canh):
    import openpyxl

    r = _goi(canh['hv'], KY + '&term_id=%d&dinh_dang=xlsx' % canh['dot1'])
    assert r.status_code == 200, getattr(r, 'data', r)
    assert 'spreadsheetml' in r['Content-Type'], r['Content-Type']
    wb = openpyxl.load_workbook(io.BytesIO(r.content))
    o = [[c.value for c in h] for h in wb.worksheets[0].iter_rows()]
    ten_lop = [str(v) for h in o for v in h if v is not None]
    assert any('BCC L1' in t for t in ten_lop), o[:4]
    assert any('BCC L2' in t for t in ten_lop), 'lớp rỗng phải có dòng trong bảng tính'
    # Lớp của đợt 2 bị bộ lọc loại — bảng tính phải cùng bộ lọc với màn.
    assert not any('BCC L4' in t for t in ten_lop), 'bảng tính không theo bộ lọc đợt'
    # Không ô nào là công thức (openpyxl đọc công thức ra chuỗi mở đầu '=').
    assert not [v for h in o for v in h if isinstance(v, str) and v.startswith('=')]


def test_dinh_dang_la_khong_bi_400(canh):
    r = _goi(canh['hv'], KY + '&dinh_dang=pdf')
    assert r.status_code == 400, getattr(r, 'data', r)
