"""BẢN GHI BUỔI HỌC — em xem lại được, và trợ giảng biết ai chưa xem.

Bảng phân rã tính năng dòng 22 (trợ giảng · quản lý record Zoom): *"Học sinh đã
xem/chưa xem · Nhắc học sinh chưa xem"*; dòng 21: *"Theo dõi việc xem record"*.

── ĐO TRƯỚC KHI LÀM (26/09/2026) ─────────────────────────────────────────────

Chỗ dán link đã có sẵn từ lâu (`class_sessions.recording_url`, màn Buổi học), và
bảng phân rã ghi dòng 22 là FALSE nên tưởng chỉ còn thiếu phần thống kê. Đo lại
mới thấy tính năng đứt ở giữa: `recording_url` không xuất hiện trong BẤT KỲ màn
nào của học viên. Trợ giảng dán link vào, không em nào xem được, và cũng không ai
biết là không xem được — đó mới là lỗ to hơn cái thống kê.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Em thấy link bản ghi của buổi ĐÃ DIỄN RA trong lớp mình — và chỉ lớp mình.
  2. Bấm mở thì ghi nhận; bấm lại KHÔNG đẻ dòng mới, chỉ cộng `lan_mo`.
  3. Buổi chưa có link thì không ghi nhận gì (không đếm lượt mở của một thứ
     không tồn tại).
  4. Người ngoài lớp mở được đường dẫn ấy → 403, và KHÔNG có dòng nào được ghi.
  5. Trợ giảng của lớp xem được ai đã mở / chưa mở. Người ngoài lớp → 403.

Chạy trên CSDL thật, giao dịch CUỘN LẠI (`conftest.py`); chỉ đếm dữ liệu của
chính mình, mọi lời gọi đi qua URL thật.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q, q1
from common.permissions import ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db

LINK = 'https://zoom.us/rec/share/bg-thu-nghiem-26-09'


def _nguoi(ten, vai):
    row = q1("INSERT INTO users (name, email, password, role, streak) "
             "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             (ten, '%s_bg@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=row['id'])


def _lop(ten, gv):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status) "
              "VALUES (%s, 'hsa_quantitative', %s, 'active') RETURNING id", (ten, gv.id))['id']


def _vao(lop, u):
    q1('INSERT INTO class_members (class_id, user_id, joined_at) '
       'VALUES (%s, %s, %s) RETURNING id', (lop, u.id, local_now() - timedelta(days=20)))


def _buoi(lop, cach_ngay=3, link=LINK):
    """Buổi ĐÃ DIỄN RA `cach_ngay` ngày trước, có (hoặc không) link bản ghi."""
    return q1('INSERT INTO class_sessions (class_id, starts_at, duration_minutes, '
              'topic, recording_url, status) '
              "VALUES (%s, %s, 90, 'Hàm số bậc hai', %s, 'done') RETURNING id",
              (lop, local_now() - timedelta(days=cach_ngay), link))['id']


def _the(u):
    c = APIClient()
    c.force_authenticate(user=u)
    return c


def _dem_luot(buoi, nguoi):
    r = q1('SELECT lan_mo FROM recording_views WHERE session_id = %s AND user_id = %s',
           (buoi, nguoi.id))
    return r['lan_mo'] if r else 0


def _so_dong(buoi):
    return q1('SELECT COUNT(*) AS n FROM recording_views WHERE session_id = %s', (buoi,))['n']


# ── 1 · Em thấy link bản ghi ─────────────────────────────────────────────────

def test_em_thay_link_ban_ghi_cua_buoi_da_hoc():
    gv = _nguoi('GV Ban Ghi', ROLE_TEACHER)
    em = _nguoi('Em Ban Ghi', ROLE_STUDENT)
    lop = _lop('Lớp bản ghi', gv)
    _vao(lop, em)
    buoi = _buoi(lop)

    res = _the(em).get('/api/lop-cua-toi')
    assert res.status_code == 200
    lop_cua_em = [c for c in res.json()['lop'] if c['id'] == lop]
    assert lop_cua_em, 'em phải thấy lớp mình'
    ds = lop_cua_em[0].get('banGhiGanDay') or []
    assert any(b['sessionId'] == buoi and b['recordingUrl'] == LINK for b in ds), \
        'buổi đã học có link bản ghi thì em phải thấy để xem lại'


def test_em_lop_khac_khong_thay_link():
    gv = _nguoi('GV Khac', ROLE_TEACHER)
    em_ngoai = _nguoi('Em Ngoai Lop', ROLE_STUDENT)
    lop = _lop('Lớp kín', gv)
    buoi = _buoi(lop)

    res = _the(em_ngoai).get('/api/lop-cua-toi')
    assert res.status_code == 200
    for c in res.json()['lop']:
        for b in (c.get('banGhiGanDay') or []):
            assert b['sessionId'] != buoi


# ── 2 · Ghi nhận lượt mở ─────────────────────────────────────────────────────

def test_bam_mo_ghi_nhan_va_bam_lai_khong_de_dong_moi():
    gv = _nguoi('GV Mo', ROLE_TEACHER)
    em = _nguoi('Em Mo', ROLE_STUDENT)
    lop = _lop('Lớp mở', gv)
    _vao(lop, em)
    buoi = _buoi(lop)
    c = _the(em)

    assert c.post('/api/sessions/%d/ban-ghi/da-mo' % buoi).status_code == 200
    assert _dem_luot(buoi, em) == 1 and _so_dong(buoi) == 1

    assert c.post('/api/sessions/%d/ban-ghi/da-mo' % buoi).status_code == 200
    assert _dem_luot(buoi, em) == 2, 'mở lại thì cộng lần'
    assert _so_dong(buoi) == 1, 'mở lại KHÔNG đẻ dòng mới'


def test_buoi_chua_co_link_thi_khong_ghi_nhan():
    gv = _nguoi('GV Chua Link', ROLE_TEACHER)
    em = _nguoi('Em Chua Link', ROLE_STUDENT)
    lop = _lop('Lớp chưa có bản ghi', gv)
    _vao(lop, em)
    buoi = _buoi(lop, link=None)

    res = _the(em).post('/api/sessions/%d/ban-ghi/da-mo' % buoi)
    assert res.status_code == 400
    assert _so_dong(buoi) == 0, 'không đếm lượt mở của một thứ không tồn tại'


def test_nguoi_ngoai_lop_khong_ghi_duoc_luot_mo():
    gv = _nguoi('GV Ngoai', ROLE_TEACHER)
    ngoai = _nguoi('Em La Mat', ROLE_STUDENT)
    lop = _lop('Lớp riêng', gv)
    buoi = _buoi(lop)

    assert _the(ngoai).post('/api/sessions/%d/ban-ghi/da-mo' % buoi).status_code == 403
    assert _so_dong(buoi) == 0, 'bị từ chối thì không được ghi gì'


# ── 3 · Trợ giảng xem ai chưa mở ─────────────────────────────────────────────

def test_tro_giang_thay_ai_da_mo_ai_chua():
    gv = _nguoi('GV Theo Doi', ROLE_TEACHER)
    tg = _nguoi('TG Theo Doi', ROLE_ASSISTANT)
    da = _nguoi('Em Da Mo', ROLE_STUDENT)
    chua = _nguoi('Em Chua Mo', ROLE_STUDENT)
    lop = _lop('Lớp theo dõi', gv)
    for u in (tg, da, chua):
        _vao(lop, u)
    buoi = _buoi(lop)
    _the(da).post('/api/sessions/%d/ban-ghi/da-mo' % buoi)

    res = _the(tg).get('/api/teach/classes/%d/ban-ghi' % lop)
    assert res.status_code == 200
    buoi_ds = [b for b in res.json()['buoi'] if b['sessionId'] == buoi]
    assert buoi_ds, 'buổi có bản ghi phải nằm trong danh sách'
    b = buoi_ds[0]
    assert b['daMo'] == 1 and b['chuaMo'] == 1
    ten_chua = [e['name'] for e in b['dsChuaMo']]
    assert 'Em Chua Mo' in ten_chua and 'Em Da Mo' not in ten_chua
    assert 'TG Theo Doi' not in ten_chua, 'chỉ đếm HỌC VIÊN, không đếm trợ giảng'


def test_nguoi_ngoai_lop_khong_xem_duoc_thong_ke():
    gv = _nguoi('GV Kin', ROLE_TEACHER)
    tg_ngoai = _nguoi('TG Lop Khac', ROLE_ASSISTANT)
    lop = _lop('Lớp không phải của TG ấy', gv)
    _buoi(lop)

    assert _the(tg_ngoai).get('/api/teach/classes/%d/ban-ghi' % lop).status_code == 403


def test_em_khong_xem_duoc_thong_ke_cua_ca_lop():
    gv = _nguoi('GV Rieng Tu', ROLE_TEACHER)
    em = _nguoi('Em Khong Duoc Xem', ROLE_STUDENT)
    lop = _lop('Lớp riêng tư', gv)
    _vao(lop, em)
    _buoi(lop)

    res = _the(em).get('/api/teach/classes/%d/ban-ghi' % lop)
    assert res.status_code == 403, 'ai đã xem bài là việc của người dạy, không phải của bạn cùng lớp'


# ── 4 · Nhắc em chưa mở (bảng phân rã dòng 22: "Nhắc học sinh chưa xem") ─────

def _chuong(uid):
    return q('SELECT title, body, type FROM notifications WHERE user_id = %s', (uid,))


def test_nhac_chi_goi_toi_em_chua_mo():
    gv = _nguoi('GV Nhac', ROLE_TEACHER)
    tg = _nguoi('TG Nhac', ROLE_ASSISTANT)
    da = _nguoi('Em Da Xem Roi', ROLE_STUDENT)
    chua = _nguoi('Em Quen Xem', ROLE_STUDENT)
    lop = _lop('Lớp nhắc', gv)
    for u in (tg, da, chua):
        _vao(lop, u)
    buoi = _buoi(lop)
    _the(da).post('/api/sessions/%d/ban-ghi/da-mo' % buoi)

    res = _the(tg).post('/api/teach/classes/%d/ban-ghi/%d/nhac' % (lop, buoi))
    assert res.status_code == 200
    assert res.json()['daNhac'] == 1, 'chỉ nhắc em chưa mở'

    assert len(_chuong(chua.id)) == 1, 'em chưa mở phải nhận chuông'
    assert _chuong(da.id) == [], 'em đã mở rồi thì đừng làm phiền'
    assert _chuong(tg.id) == [], 'trợ giảng không phải người phải xem lại bài'
    assert 'xem lại' in _chuong(chua.id)[0]['body'].lower()


def test_em_khong_tu_nhac_duoc_ca_lop():
    gv = _nguoi('GV Cam', ROLE_TEACHER)
    em = _nguoi('Em Khong Duoc Nhac', ROLE_STUDENT)
    lop = _lop('Lớp cấm nhắc', gv)
    _vao(lop, em)
    buoi = _buoi(lop)

    assert _the(em).post('/api/teach/classes/%d/ban-ghi/%d/nhac' % (lop, buoi)).status_code == 403


def test_buoi_khong_thuoc_lop_thi_khong_nhac_duoc():
    gv = _nguoi('GV Lop A', ROLE_TEACHER)
    gv_b = _nguoi('GV Lop B', ROLE_TEACHER)
    lop_a = _lop('Lớp A nhắc', gv)
    lop_b = _lop('Lớp B nhắc', gv_b)
    buoi_b = _buoi(lop_b)

    # Giảng viên lớp A mượn id buổi của lớp B: phải trượt, không được nhắc chéo lớp.
    assert _the(gv).post('/api/teach/classes/%d/ban-ghi/%d/nhac'
                         % (lop_a, buoi_b)).status_code == 404


# ── 5 · Buổi đã học mà QUÊN dán bản ghi (dòng 22: "Record đã upload/chưa upload") ──

def test_thong_ke_neu_ro_buoi_nao_con_thieu_ban_ghi():
    gv = _nguoi('GV Thieu', ROLE_TEACHER)
    lop = _lop('Lớp thiếu bản ghi', gv)
    co = _buoi(lop, cach_ngay=3)
    khong = _buoi(lop, cach_ngay=5, link=None)
    # Buổi CHƯA HỌC cũng chưa có bản ghi — đương nhiên, và KHÔNG phải thiếu sót.
    # Không có dòng này thì đột biến bỏ điều kiện "đã diễn ra" lọt qua (đo 26/09).
    chua_hoc = _buoi(lop, cach_ngay=-7, link=None)

    res = _the(gv).get('/api/teach/classes/%d/ban-ghi' % lop)
    assert res.status_code == 200
    d = res.json()
    assert [b['sessionId'] for b in d['buoi']] == [co]
    thieu = [b['sessionId'] for b in d.get('thieuBanGhi', [])]
    assert khong in thieu, 'buổi đã học mà chưa dán link phải được nêu ra để trợ giảng biết'
    assert co not in thieu
    assert chua_hoc not in thieu, 'buổi chưa học thì chưa thể có bản ghi — đừng gọi là thiếu'


# ── 6 · Báo lỗi bản ghi (dòng 22: "Báo lỗi record") ─────────────────────────

def test_em_bao_loi_ban_ghi_thi_nguoi_day_nhan_chuong():
    gv = _nguoi('GV Nhan Bao', ROLE_TEACHER)
    tg = _nguoi('TG Nhan Bao', ROLE_ASSISTANT)
    em = _nguoi('Em Bao Loi', ROLE_STUDENT)
    ban = _nguoi('Ban Cung Lop', ROLE_STUDENT)
    lop = _lop('Lớp báo lỗi', gv)
    for u in (tg, em, ban):
        _vao(lop, u)
    buoi = _buoi(lop)

    res = _the(em).post('/api/sessions/%d/ban-ghi/bao-loi' % buoi)
    assert res.status_code == 200

    assert len(_chuong(gv.id)) == 1, 'giảng viên của lớp phải biết link hỏng'
    assert len(_chuong(tg.id)) == 1, 'trợ giảng là người dán link, phải biết'
    assert _chuong(em.id) == [], 'người báo không tự nhận chuông của mình'
    assert _chuong(ban.id) == [], 'bạn cùng lớp không liên quan — đây là việc của người dạy'
    assert 'Em Bao Loi' in _chuong(gv.id)[0]['body'], 'phải nói AI báo để còn hỏi lại'


def test_tro_giang_tu_bao_loi_thi_khong_tu_goi_minh():
    """Trợ giảng NẰM trong danh sách nhận, nên đây là lượt duy nhất chạm được
    luật "bỏ qua chính người báo". Thiếu nó, luật ấy là mã chết (đo 26/09)."""
    gv = _nguoi('GV Tu Bao', ROLE_TEACHER)
    tg = _nguoi('TG Tu Bao', ROLE_ASSISTANT)
    lop = _lop('Lớp trợ giảng tự báo', gv)
    _vao(lop, tg)
    buoi = _buoi(lop)

    assert _the(tg).post('/api/sessions/%d/ban-ghi/bao-loi' % buoi).status_code == 200
    assert _chuong(tg.id) == [], 'người báo không tự gọi chuông cho mình'
    assert len(_chuong(gv.id)) == 1, 'giảng viên vẫn phải nhận'


def test_nguoi_ngoai_lop_khong_bao_loi_duoc():
    gv = _nguoi('GV Kin Bao', ROLE_TEACHER)
    ngoai = _nguoi('Em Ngoai Bao', ROLE_STUDENT)
    lop = _lop('Lớp kín báo lỗi', gv)
    buoi = _buoi(lop)

    assert _the(ngoai).post('/api/sessions/%d/ban-ghi/bao-loi' % buoi).status_code == 403
    assert _chuong(gv.id) == []


# ── Lỗ agent soát tìm ra (26/09/2026) ────────────────────────────────────────
#
# Agent soát chạy đột biến của RIÊNG nó trên bộ test này và bốn cái KHÔNG bị
# giết. Ba lỗ trắng: người đã rời lớp, buổi đã huỷ, và cửa `recording_url` của
# đường báo lỗi. Cộng một lỗi thật: §72 không biết tới BUỔI BÙ.
#
# Buổi bù (V-g, §62e `session_participants`): buổi chỉ có vài em, không phải cả
# lớp. `lop_cua_toi.py` đã lọc đúng bằng `thuoc_buoi`, nhưng `ban_ghi.py` thì
# không — nên §72 tự cãi nhau: thống kê và chuông đếm CẢ LỚP, còn màn của em lại
# ẩn đúng buổi ấy. Hai em nhận chuông "xem lại buổi 23/09" mà `banGhiGanDay` của
# chính họ rỗng: làm đúng lời nhắc rồi không thấy gì.


def _buoi_bu(lop, ds_em, cach_ngay=3, link=LINK):
    """Buổi CHỈ dành cho `ds_em` — §62e: có `session_participants` thì chỉ họ thuộc buổi."""
    sid = _buoi(lop, cach_ngay=cach_ngay, link=link)
    for u in ds_em:
        q1('INSERT INTO session_participants (session_id, user_id) VALUES (%s, %s) '
           'RETURNING session_id', (sid, u.id))
    return sid


def test_buoi_bu_chi_dem_em_thuoc_buoi():
    gv = _nguoi('GV Bu Dem', ROLE_TEACHER)
    du = _nguoi('Em Du Buoi Bu', ROLE_STUDENT)
    khong = _nguoi('Em Khong Du Bu', ROLE_STUDENT)
    lop = _lop('Lớp có buổi bù', gv)
    for u in (du, khong):
        _vao(lop, u)
    buoi = _buoi_bu(lop, [du])

    res = _the(gv).get('/api/teach/classes/%d/ban-ghi' % lop)
    b = next(x for x in res.json()['buoi'] if x['sessionId'] == buoi)
    assert b['daMo'] + b['chuaMo'] == 1, \
        'buổi bù chỉ có một em — không được lấy sĩ số cả lớp làm mẫu số'
    assert [e['name'] for e in b['dsChuaMo']] == ['Em Du Buoi Bu']


def test_buoi_bu_chi_nhac_em_thuoc_buoi():
    gv = _nguoi('GV Bu Nhac', ROLE_TEACHER)
    du = _nguoi('Em Du Nhac', ROLE_STUDENT)
    khong = _nguoi('Em Ngoai Buoi Bu', ROLE_STUDENT)
    lop = _lop('Lớp bù nhắc', gv)
    for u in (du, khong):
        _vao(lop, u)
    buoi = _buoi_bu(lop, [du])

    res = _the(gv).post('/api/teach/classes/%d/ban-ghi/%d/nhac' % (lop, buoi))
    assert res.json()['daNhac'] == 1
    assert _chuong(khong.id) == [], \
        'em không dự buổi bù mà bị nhắc xem lại thì em ấy mở ra không thấy gì'


def test_buoi_bu_em_khong_du_thi_khong_ghi_duoc_luot_mo():
    gv = _nguoi('GV Bu Mo', ROLE_TEACHER)
    du = _nguoi('Em Du Mo Bu', ROLE_STUDENT)
    khong = _nguoi('Em Khong Du Mo', ROLE_STUDENT)
    lop = _lop('Lớp bù mở', gv)
    for u in (du, khong):
        _vao(lop, u)
    buoi = _buoi_bu(lop, [du])

    assert _the(du).post('/api/sessions/%d/ban-ghi/da-mo' % buoi).status_code == 200
    assert _the(khong).post('/api/sessions/%d/ban-ghi/da-mo' % buoi).status_code == 403
    assert _so_dong(buoi) == 1


def test_em_da_roi_lop_khong_con_ghi_duoc_gi():
    """Đột biến A của agent soát: bỏ `left_at IS NULL` mà 15/15 test vẫn xanh."""
    gv = _nguoi('GV Da Roi', ROLE_TEACHER)
    em = _nguoi('Em Da Roi Lop', ROLE_STUDENT)
    lop = _lop('Lớp em đã rời', gv)
    _vao(lop, em)
    q1("UPDATE class_members SET left_at = now(), leave_reason = 'dropped' "
       'WHERE class_id = %s AND user_id = %s RETURNING id', (lop, em.id))
    buoi = _buoi(lop)

    assert _the(em).post('/api/sessions/%d/ban-ghi/da-mo' % buoi).status_code == 403
    assert _the(em).post('/api/sessions/%d/ban-ghi/bao-loi' % buoi).status_code == 403
    assert _so_dong(buoi) == 0


def test_bao_loi_buoi_chua_co_ban_ghi_thi_tu_choi():
    """Đột biến B: cửa `recording_url` chỉ được canh cho `da-mo`, không cho `bao-loi`."""
    gv = _nguoi('GV Bao Trong', ROLE_TEACHER)
    em = _nguoi('Em Bao Trong', ROLE_STUDENT)
    lop = _lop('Lớp báo lỗi buổi trống', gv)
    _vao(lop, em)
    buoi = _buoi(lop, link=None)

    assert _the(em).post('/api/sessions/%d/ban-ghi/bao-loi' % buoi).status_code == 400
    assert _chuong(gv.id) == [], 'không có bản ghi thì không có gì để báo hỏng'


def test_buoi_da_huy_khong_bi_doi_dan_ban_ghi():
    """Đột biến C: `thieuBanGhi` bỏ `status <> 'cancelled'`."""
    gv = _nguoi('GV Huy', ROLE_TEACHER)
    lop = _lop('Lớp có buổi huỷ', gv)
    thuong = _buoi(lop, cach_ngay=4, link=None)
    huy = q1("INSERT INTO class_sessions (class_id, starts_at, duration_minutes, topic, status) "
             "VALUES (%s, %s, 90, 'Buổi huỷ', 'cancelled') RETURNING id",
             (lop, local_now() - timedelta(days=5)))['id']

    d = _the(gv).get('/api/teach/classes/%d/ban-ghi' % lop).json()
    thieu = [b['sessionId'] for b in d.get('thieuBanGhi', [])]
    assert thuong in thieu
    assert huy not in thieu, 'buổi đã huỷ thì không ai phải dán bản ghi cho nó'


def test_so_da_mo_cong_chua_mo_bang_si_so_that():
    """Đột biến D: `daMo` tính bằng `len(xong)` — phồng số khi có người ngoài diện."""
    gv = _nguoi('GV Dem', ROLE_TEACHER)
    tg = _nguoi('TG Khong Tinh', ROLE_ASSISTANT)
    a = _nguoi('Em Dem A', ROLE_STUDENT)
    b = _nguoi('Em Dem B', ROLE_STUDENT)
    lop = _lop('Lớp đếm', gv)
    for u in (tg, a, b):
        _vao(lop, u)
    buoi = _buoi(lop)
    _the(a).post('/api/sessions/%d/ban-ghi/da-mo' % buoi)
    # Trợ giảng CŨNG mở bản ghi. `recording_views` vì thế có 2 dòng, nhưng mẫu số
    # chỉ gồm HỌC VIÊN — nên `daMo` phải là 1, không phải 2. Thiếu lượt mở này thì
    # đột biến `daMo = len(xong)` lọt qua (agent soát 26/09 chỉ đúng chỗ).
    _the(tg).post('/api/sessions/%d/ban-ghi/da-mo' % buoi)

    x = next(k for k in _the(gv).get('/api/teach/classes/%d/ban-ghi' % lop).json()['buoi']
             if k['sessionId'] == buoi)
    assert x['daMo'] == 1 and x['chuaMo'] == 1, 'chỉ đếm HỌC VIÊN thuộc buổi'
    assert x['daMo'] + x['chuaMo'] == 2, 'tổng phải bằng sĩ số thật, không phồng'


def test_nhieu_em_bao_hong_thi_chuong_noi_ro_may_em():
    """Agent soát mục 3: gộp 120 phút xoá mất `coalesce_count`, còn lại "1 em báo"."""
    gv = _nguoi('GV Dem Bao', ROLE_TEACHER)
    ds = [_nguoi('Em Bao So %d' % i, ROLE_STUDENT) for i in range(3)]
    lop = _lop('Lớp nhiều em báo', gv)
    for u in ds:
        _vao(lop, u)
    buoi = _buoi(lop)
    for u in ds:
        _the(u).post('/api/sessions/%d/ban-ghi/bao-loi' % buoi)

    ch = _chuong(gv.id)
    assert len(ch) == 1, 'ba lượt báo cùng một buổi thì gộp làm một dòng chuông'
    # KHÔNG so bằng `'3' in title`: tiêu đề có sẵn ngày tháng, và "23/09" cũng chứa
    # chữ số 3 — thước ấy xanh cả khi mã không đếm gì (đo 26/09).
    assert '3 em' in ch[0]['title'], \
        ('một em báo có thể là mạng nhà em ấy, ba em báo là link hỏng thật — '
         'tiêu đề phải nói ra con số', ch[0]['title'])
    assert ch[0]['type'] == 'ban_ghi_loi'
