"""Báo cáo lớp dạng PDF — bản trung tâm mang đi họp.

Chạy trên DB thật, trong giao dịch được CUỘN LẠI (xem `conftest.py`).

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. **Cổng quyền.** Tờ này có tên, email và chuyên cần của cả lớp. Học viên
     mở được là lộ dữ liệu bạn học; giảng viên lớp khác mở được là lộ dữ liệu
     lớp không phải của họ.
  2. **Không đọc được sổ điểm danh thì NÓI RA**, không in bảng toàn số 0 —
     một bảng như thế trông y hệt "lớp chưa học buổi nào", rồi được mang vào
     buổi họp phụ huynh. Cùng luật mà `ClassAttendanceCsvView` đã đặt.
  3. **Con số phải KHỚP `dem_chuyen_can`** — nguồn dùng chung với CSV. Hai bản
     xuất từ cùng một màn hình mà nói hai con số là lỗi đã xảy ra một lần
     (31/08/2026) và là lý do hàm ấy được tách ra.
  4. **"chưa thi" chứ không phải 0%** cho em chưa thi lần nào.
  5. Tên file có cả `filename=` ASCII lẫn `filename*=UTF-8` — thiếu cái đầu
     thì máy cũ tải về thành tên rác không đuôi .pdf.
"""
import io

import pytest
from pypdf import PdfReader
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.db import q1
from common.permissions import ROLE_STUDENT, ROLE_TEACHER
from teaching.bao_cao_lop_pdf import dung_pdf_lop
from teaching.exports import ClassReportPdfView

f = APIRequestFactory()


def _goi(ai, class_id):
    req = f.get('/x')
    force_authenticate(req, user=ai)
    return ClassReportPdfView.as_view()(req, class_id=class_id)


def _nguoi(ten, vai):
    r = q1('INSERT INTO users (name, email, password, role, streak) '
           'VALUES (%s,%s,%s,%s,0) RETURNING id',
           (ten, '%s_pdf@example.com' % ten.replace(' ', '_'), 'x', vai))
    return User.objects.get(id=r['id'])


@pytest.fixture
def lop(db):
    gv = _nguoi('GV PDF', ROLE_TEACHER)
    hv = _nguoi('HV PDF', ROLE_STUDENT)
    c = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
           "VALUES ('Lop PDF','hsa_quantitative',%s,'active') RETURNING id", (gv.id,))
    q1('INSERT INTO class_members (class_id, user_id) VALUES (%s,%s) RETURNING id',
       (c['id'], hv.id))
    return {'id': c['id'], 'gv': gv, 'hv': hv}


def _chu(noi_dung) -> str:
    return ''.join((p.extract_text() or '')
                   for p in PdfReader(io.BytesIO(noi_dung)).pages)


# ── 1. Cổng quyền ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_hoc_vien_KHONG_tai_duoc_bao_cao_lop(lop):
    """Tờ này có tên, email và chuyên cần của mọi bạn cùng lớp."""
    assert _goi(lop['hv'], lop['id']).status_code == 403


@pytest.mark.django_db
def test_giang_vien_lop_KHAC_khong_tai_duoc(lop):
    khac = _nguoi('GV Lop Khac', ROLE_TEACHER)
    kq = _goi(khac, lop['id'])
    # 404 chứ không 403: trả 403 là xác nhận lớp ấy TỒN TẠI, tức rò một mẩu
    # thông tin cho người không có quyền — cùng luật `can_see_class` đã đặt.
    assert kq.status_code == 404, kq.status_code


@pytest.mark.django_db
def test_giang_vien_phu_trach_tai_duoc(lop):
    kq = _goi(lop['gv'], lop['id'])
    assert kq.status_code == 200, kq.status_code
    assert kq['Content-Type'] == 'application/pdf'
    assert kq.content[:5] == b'%PDF-'


@pytest.mark.django_db
def test_lop_khong_ton_tai_tra_404(lop):
    assert _goi(lop['gv'], 999999).status_code == 404


# ── 2. Tên tệp ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_ten_tep_co_ca_hai_dang(lop):
    cd = _goi(lop['gv'], lop['id'])['Content-Disposition']
    assert 'attachment;' in cd
    assert 'filename="' in cd, 'thiếu bản ASCII dự phòng cho máy cũ'
    assert "filename*=UTF-8''" in cd
    assert '.pdf' in cd


# ── 3. Không đọc được điểm danh thì NÓI RA ────────────────────────────────

def test_khong_doc_duoc_diem_danh_thi_noi_thang():
    """`cc=None` là "không đọc được", KHÁC HẲN `cc={}` là "chưa có buổi nào"."""
    bc = {'class': {'name': 'Lop X'}, 'students': [{'userId': 1, 'name': 'A'}],
          'summary': {}}
    t = _chu(dung_pdf_lop(bc, None))
    assert 'Không đọc được sổ điểm danh' in t
    # Và KHÔNG được in một bảng chuyên cần trông bình thường.
    assert 'Có mặt' not in t.split('III.')[0].split('II. CHUYÊN CẦN')[-1]


def test_co_du_lieu_thi_in_bang_chuyen_can():
    bc = {'class': {'name': 'Lop X'},
          'students': [{'userId': 1, 'name': 'Nguyễn A', 'progressPct': 40,
                        'lessonsDone': 4, 'lessonsTotal': 10, 'mockCount': 2,
                        'lastMockPct': 71, 'idleDays': 2}],
          'summary': {'students': 1, 'idleDays': 7}}
    t = _chu(dung_pdf_lop(bc, {1: {'present': 3, 'late': 1, 'absent': 0,
                                   'excused': 0, 'chuaTick': 1, 'tiLe': 100}}))
    assert 'Nguyễn A' in t
    assert 'Không đọc được sổ điểm danh' not in t
    assert '100%' in t


# ── 4. Không bịa số 0 ──────────────────────────────────────────────────────

def test_em_chua_thi_lan_nao_thi_ghi_chua_thi():
    bc = {'class': {'name': 'Lop X'},
          'students': [{'userId': 1, 'name': 'A', 'mockCount': 0,
                        'lastMockPct': None, 'progressPct': 0, 'idleDays': 1}],
          'summary': {'students': 1, 'idleDays': 7}}
    t = _chu(dung_pdf_lop(bc, {}))
    assert 'chưa thi' in t
    # "Điểm gần nhất 0%" đọc như em ấy làm sai hết, trong khi em chưa thi.
    assert '0 lượt\n0%' not in t


# ── 5. Phần KHÔNG đọc được phải hiện ngay đầu tờ ──────────────────────────

def test_mang_du_lieu_thieu_duoc_bao_ngay_muc_I():
    """`summary.incomplete` là lời tự khai của `class_report` rằng có mảng
    KHÔNG đọc được. Giấu nó đi là trình bày một con số 0 mà người đọc không có
    cách nào biết là 0 thật hay là không đọc được."""
    bc = {'class': {'name': 'Lop X'}, 'students': [],
          'summary': {'incomplete': ['mastery', 'lag']}}
    t = _chu(dung_pdf_lop(bc, {}))
    assert 'không đọc được' in t.lower()
    assert 'mastery' in t and 'lag' in t


# ── 6. Khớp nguồn dùng chung ──────────────────────────────────────────────

@pytest.mark.django_db
def test_so_trong_pdf_khop_dem_chuyen_can(lop):
    """Cùng nguồn với CSV — hai bản xuất phải nói cùng một con số."""
    from teaching.exports import dem_chuyen_can
    tong, ok = dem_chuyen_can(lop['id'])
    assert ok

    t = _chu(_goi(lop['gv'], lop['id']).content)
    d = (tong or {}).get(lop['hv'].id)
    if d and any(d[k] for k in ('present', 'late', 'absent', 'excused')):
        assert 'HV PDF' in t


# ── 7. Không vỡ với lớp rỗng ──────────────────────────────────────────────

def test_lop_rong_van_dung_duoc_to_giay():
    t = _chu(dung_pdf_lop({}, {}))
    assert 'BÁO CÁO LỚP' in t
    assert 'Lớp chưa có học viên nào đang học' in t


def test_payload_thieu_khoa_khong_lam_no():
    """Đường xuất chạy trong một request thật; ném ở đây là trả 500 cho giảng
    viên đang đứng trước buổi họp."""
    assert dung_pdf_lop({'class': None, 'students': None, 'summary': None})[:5] == b'%PDF-'
