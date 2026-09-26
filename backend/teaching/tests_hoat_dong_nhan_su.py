"""HOẠT ĐỘNG CỦA GIẢNG VIÊN / TRỢ GIẢNG (bảng TopHSA dòng 6, ô *"Hoạt động GV/TG"*).

Bảng ghi MỘT PHẦN với lý do: *"buổi dạy / điểm danh theo tháng CÓ (V-o); các hoạt động
khác (chấm bài, nhắn tin) chưa gộp"*.

── VÌ SAO GỘP VÀO ĐÚNG BẢNG CHẤM CÔNG ────────────────────────────────────────

Trung tâm nhìn bảng này để trả lời một câu: tháng vừa rồi người này làm được gì. Dạy bao
nhiêu buổi là một nửa; chấm bao nhiêu bài và nhắn cho lớp bao nhiêu lần là nửa còn lại —
và với trợ giảng thì nửa sau mới là phần lớn công việc. Tách ra một trang riêng nghĩa là
không ai đọc cả hai cùng lúc, tức không ai trả lời được câu ấy.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Chấm một bài trong tháng → cột "bài đã chấm" của người chấm tăng đúng 1.
  2. Bài chấm THÁNG KHÁC không lọt vào (mốc theo `graded_at`, không phải hạn nộp).
  3. Gửi một thông báo lớp → cột "thông báo đã gửi" tăng; bản nháp chưa gửi thì KHÔNG.
  4. Người không chấm bài nào vẫn có dòng, số 0 — "không làm gì" cũng là điều học vụ
     cần thấy, và một dòng biến mất trông như người ấy đã nghỉ việc.
  5. Vẫn MỘT câu SQL (phép kiểm đếm câu đã có sẵn trong `tests_cham_cong.py`).

Chạy trên CSDL thật, giao dịch CUỘN LẠI; chỉ đếm dữ liệu của chính mình.
"""
from datetime import timedelta

import pytest

from accounts.models import User
from common.clock import local_now
from common.db import q1, x
from common.permissions import ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER
from teaching.cham_cong import cham_cong

pytestmark = pytest.mark.django_db


def _nguoi(ten, vai):
    r = q1("INSERT INTO users (name, email, password, role, streak) "
           "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
           (ten, '%s_hd@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=r['id'])


@pytest.fixture
def canh():
    gv = _nguoi('GV Hoat Dong', ROLE_TEACHER)
    tg = _nguoi('TG Hoat Dong', ROLE_ASSISTANT)
    em = _nguoi('Em Hoat Dong', ROLE_STUDENT)
    lop = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
             "VALUES ('Lop hoat dong', 'hsa_quantitative', %s, 'active') RETURNING id",
             (gv.id,))['id']
    nay = local_now()
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s)',
      (lop, em.id, nay - timedelta(days=40)))
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s)',
      (lop, tg.id, nay - timedelta(days=40)))
    bai = q1("INSERT INTO assignments (class_id, title, created_by) "
             "VALUES (%s, 'Bai hoat dong', %s) RETURNING id", (lop, gv.id))['id']
    return {'gv': gv, 'tg': tg, 'em': em, 'lop': lop, 'bai': bai, 'nay': nay}


def _thang(luc):
    dau = luc.date().replace(day=1)
    return dau, (dau + timedelta(days=45)).replace(day=1)


def _dong(canh, uid, luc=None):
    tu, den = _thang(luc or canh['nay'])
    for r in cham_cong(tu, den):
        if r['id'] == uid:
            return r
    return None


def _cham(canh, ai, luc):
    x('''INSERT INTO submissions (assignment_id, user_id, submitted_at, score, graded_by, graded_at)
         VALUES (%s, %s, %s, 8, %s, %s)''',
      (canh['bai'], canh['em'].id, luc - timedelta(days=1), ai.id, luc))


# ── 1. Bài đã chấm ───────────────────────────────────────────────────────────

def test_cham_mot_bai_thi_cot_tang_dung_mot(canh):
    truoc = (_dong(canh, canh['gv'].id) or {}).get('daCham', 0)
    _cham(canh, canh['gv'], canh['nay'])
    assert (_dong(canh, canh['gv'].id) or {}).get('daCham', 0) == truoc + 1


def test_bai_cham_thang_khac_khong_lot_vao(canh):
    """Mốc là NGÀY CHẤM, không phải hạn nộp — bảng này nói về công của tháng này."""
    truoc = (_dong(canh, canh['gv'].id) or {}).get('daCham', 0)
    _cham(canh, canh['gv'], canh['nay'] - timedelta(days=60))
    assert (_dong(canh, canh['gv'].id) or {}).get('daCham', 0) == truoc


def test_tro_giang_cham_bai_cung_duoc_tinh(canh):
    """Ở TopHSA trợ giảng chấm phần lớn bài — bỏ họ ra là bỏ mất phần lớn công việc."""
    truoc = (_dong(canh, canh['tg'].id) or {}).get('daCham', 0)
    _cham(canh, canh['tg'], canh['nay'])
    assert (_dong(canh, canh['tg'].id) or {}).get('daCham', 0) == truoc + 1


# ── 2. Thông báo đã gửi ─────────────────────────────────────────────────────

def _thong_bao(canh, ai, da_gui=True, luc=None):
    luc = luc or canh['nay']
    x('''INSERT INTO announcements (title, body, audience, status, created_by, created_at, sent_at)
         VALUES ('Thong bao hoat dong', 'x', %s::jsonb, %s, %s, %s, %s)''',
      ('{"classIds": [%d]}' % canh['lop'], 'sent' if da_gui else 'draft',
       ai.id, luc, luc if da_gui else None))


def test_gui_thong_bao_thi_cot_tang(canh):
    truoc = (_dong(canh, canh['gv'].id) or {}).get('daGuiThongBao', 0)
    _thong_bao(canh, canh['gv'])
    assert (_dong(canh, canh['gv'].id) or {}).get('daGuiThongBao', 0) == truoc + 1


def test_ban_nhap_chua_gui_thi_khong_tinh(canh):
    """Soạn nháp chưa phải là đã nhắn cho ai."""
    truoc = (_dong(canh, canh['gv'].id) or {}).get('daGuiThongBao', 0)
    _thong_bao(canh, canh['gv'], da_gui=False)
    assert (_dong(canh, canh['gv'].id) or {}).get('daGuiThongBao', 0) == truoc


# ── 3. Không làm gì cũng phải có dòng ───────────────────────────────────────

def test_nguoi_khong_cham_bai_nao_van_co_dong_so_0(canh):
    d = _dong(canh, canh['tg'].id)
    assert d is not None, 'trợ giảng biến mất khỏi bảng — trông như đã nghỉ việc'
    assert d.get('daCham') == 0 and d.get('daGuiThongBao') == 0
