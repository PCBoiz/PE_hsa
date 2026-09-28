"""CẢNH BÁO LỚP CHẬM TIẾN ĐỘ — thứ cuối cùng còn CHƯA của phân hệ thông báo.

── LỖ ĐANG CHẶN LẠI (28/09/2026) ───────────────────────────────────────────

Hệ thống TÍNH được lớp nào chậm tiến độ từ E1 (`chuong_trinh/tien_do.py::danh_gia` — trễ
≥ 2 buổi khung, hoặc xong < 80 % phần phải xong tới hôm nay). Con số ấy hiện trên màn "Toàn
trung tâm" và trên chip của từng lớp.

**Nhưng không ai được BÁO.** Muốn biết lớp mình đang tụt thì phải tự mở màn ra xem — và
người cần biết nhất là người bận nhất. Sổ nghiệm thu ghi thẳng: *"không loại chuông nào đẩy
nó tới người; không mã nào gửi"*.

── LUẬT ────────────────────────────────────────────────────────────────────

  · Chỉ lớp ĐANG HỌC và ĐÃ NHẬN KHUNG: lớp chưa có khung thì không có kế hoạch để chậm so
    với nó, và lớp tạm dừng thì chậm là đúng.
  · Người nhận: NGƯỜI ĐỨNG LỚP (`teaching/nhan_su_lop.py`) — giảng viên, trợ giảng, học vụ
    phụ trách. Không gửi học viên: "lớp chậm tiến độ" là việc của người dạy, nói với cả lớp
    chỉ gây lo mà không ai làm được gì.
  · MỖI TUẦN MỘT LẦN cho mỗi người mỗi lớp. Anh Sơn 27/09 được hỏi nhịp gửi, đề xuất của
    tôi là mỗi tuần; chưa có trả lời tính tới 28/09. Gửi mỗi ngày là 30 chuông cho cùng một
    việc, và sau tuần đầu không ai đọc chuông nữa.
  · Chống trùng bằng CHỈ MỤC (§76), không bằng đọc-rồi-ghi: hai nhịp chạy chồng nhau sẽ
    cùng thấy "tuần này chưa gửi" (cùng bài học của `nhac_han`, §61d).

Chạy trên CSDL thật, giao dịch CUỘN LẠI; chỉ đếm dữ liệu của chính mình.
"""
from datetime import timedelta

import pytest

from common.clock import local_now
from common.db import q, q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER
from notifications import canh_bao_tien_do

pytestmark = pytest.mark.django_db


def _nguoi(ten, vai):
    return q1("INSERT INTO users (name, email, password, role, streak) "
              "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
              (ten, '%s_cbtd@example.com' % ten.replace(' ', '_').lower(), vai))['id']


def _khung(so_buoi=4):
    """Một khung đã xuất bản, `so_buoi` buổi, mỗi buổi một mục trọng số 10."""
    v = q1("""INSERT INTO syllabus_versions (course_id, name, status)
              VALUES ('hsa_quantitative', 'Khung cbtd', 'xuat_ban') RETURNING id""")['id']
    for i in range(so_buoi):
        s = q1("""INSERT INTO syllabus_sessions (version_id, name, sort_order, duration_minutes)
                  VALUES (%s, %s, %s, 90) RETURNING id""", (v, 'Buoi %d' % (i + 1), i))['id']
        x("""INSERT INTO syllabus_items (session_id, title, kind, weight, sort_order)
             VALUES (%s, %s, 'bai_hoc', 10, 0)""", (s, 'Muc buoi %d' % (i + 1)))
    return v


@pytest.fixture
def canh():
    gv = _nguoi('GV Cham Tien Do', ROLE_TEACHER)
    tg = _nguoi('TG Cham Tien Do', ROLE_ASSISTANT)
    hvu = _nguoi('Hoc Vu Cham Tien Do', ROLE_ACADEMIC)
    em = _nguoi('Em Cham Tien Do', ROLE_STUDENT)
    v = _khung()
    lop = q1("""INSERT INTO classes (name, course_id, teacher_id, status, syllabus_version_id)
                VALUES ('Lop cham tien do', 'hsa_quantitative', %s, 'active', %s)
                RETURNING id""", (gv, v))['id']
    for u in (em, tg, hvu):
        x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s)',
          (lop, u, local_now() - timedelta(days=40)))
    # Bốn buổi ĐÃ QUA, gắn vào bốn buổi khung, KHÔNG buổi nào ghi sổ đầu bài → đã xong 0,
    # phải xong 40. Chậm hết mức.
    ks = [r['id'] for r in q('SELECT id FROM syllabus_sessions WHERE version_id = %s '
                             'ORDER BY sort_order', (v,))]
    for i, ksid in enumerate(ks):
        x("""INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status,
                                         syllabus_session_id)
             VALUES (%s, %s, 90, 'planned', %s)""",
          (lop, local_now() - timedelta(days=30 - i * 5), ksid))
    return {'gv': gv, 'tg': tg, 'hvu': hvu, 'em': em, 'lop': lop, 'khung': v}


def _chuong(uid, lop=None):
    if lop is None:
        return q("SELECT type, title, body FROM notifications WHERE user_id = %s "
                 "AND type = 'cham_tien_do' ORDER BY id", (uid,))
    return q("SELECT type, title, body FROM notifications WHERE user_id = %s "
             "AND type = 'cham_tien_do' AND ref_id = %s ORDER BY id", (uid, lop))


# ── 1. Người đứng lớp được báo ──────────────────────────────────────────────

def test_quet_bao_giang_vien_cua_lop_cham(canh):
    canh_bao_tien_do.quet()
    assert _chuong(canh['gv'], canh['lop']), 'giảng viên của lớp chậm KHÔNG được báo'


def test_tro_giang_va_hoc_vu_phu_trach_cung_duoc_bao(canh):
    canh_bao_tien_do.quet()
    assert _chuong(canh['tg'], canh['lop']), 'trợ giảng của lớp KHÔNG được báo'
    assert _chuong(canh['hvu'], canh['lop']), 'học vụ phụ trách lớp KHÔNG được báo'


def test_hoc_vien_KHONG_duoc_bao(canh):
    canh_bao_tien_do.quet()
    assert not _chuong(canh['em']), 'học viên cũng nhận cảnh báo lớp chậm tiến độ'


def test_chuong_noi_ro_lop_nao_cham_bao_nhieu(canh):
    canh_bao_tien_do.quet()
    ds = _chuong(canh['gv'], canh['lop'])
    # TIÊU ĐỀ riêng, không gộp với nội dung: panel chuông và danh sách thông báo hiện tiêu
    # đề trước, và người có năm lớp cần biết NGAY là lớp nào. Bản đầu của phép kiểm này gộp
    # hai trường, nên đột biến "tiêu đề rỗng chữ" LỌT (đo 28/09) — tên lớp vẫn còn ở nội dung.
    assert any('Lop cham tien do' in c['title'] for c in ds),         'TIÊU ĐỀ chuông không nói lớp nào: %r' % [c['title'] for c in ds]
    chu = ' '.join('%s %s' % (c['title'], c['body']) for c in ds)
    # RULES §10: chữ người dùng đọc, không phải mã kỹ thuật.
    for ma in ('cham_tien_do', 'syllabus', 'tiLe', 'treBuoi'):
        assert ma not in chu, 'mã kỹ thuật lọt lên chuông (%s): %r' % (ma, chu)


# ── 2. Lớp KHÔNG chậm, lớp không đủ điều kiện ───────────────────────────────

def test_lop_chua_nhan_khung_thi_khong_bao(canh):
    """Không có kế hoạch thì không có cái để chậm so với nó."""
    gv2 = _nguoi('GV Khong Khung', ROLE_TEACHER)
    q1("""INSERT INTO classes (name, course_id, teacher_id, status)
          VALUES ('Lop khong khung', 'hsa_quantitative', %s, 'active') RETURNING id""", (gv2,))
    canh_bao_tien_do.quet()
    assert not _chuong(gv2), 'lớp chưa nhận khung cũng bị báo chậm'


def test_lop_tam_dung_thi_khong_bao(canh):
    """Lớp tạm dừng thì chậm là đúng — báo hằng tuần chỉ là tiếng ồn."""
    x("UPDATE classes SET status = 'paused' WHERE id = %s", (canh['lop'],))
    canh_bao_tien_do.quet()
    assert not _chuong(canh['gv'], canh['lop']), 'lớp tạm dừng vẫn bị báo chậm'


def test_lop_da_ghi_du_so_dau_bai_thi_khong_cham(canh):
    """Ghi "đã dạy" cho mọi mục của mọi buổi đã qua → không còn chậm, không còn chuông."""
    for r in q("""SELECT cs.id AS buoi, si.id AS muc, si.title AS ten
                    FROM class_sessions cs
                    JOIN syllabus_items si ON si.session_id = cs.syllabus_session_id
                   WHERE cs.class_id = %s""", (canh['lop'],)):
        x("""INSERT INTO session_log_items (session_id, item_id, label, status)
             VALUES (%s, %s, %s, 'done')""", (r['buoi'], r['muc'], r['ten']))
    canh_bao_tien_do.quet()
    assert not _chuong(canh['gv'], canh['lop']), 'lớp đã dạy đủ vẫn bị báo chậm'


# ── 3. Mỗi tuần một lần ─────────────────────────────────────────────────────

def test_quet_hai_lan_trong_tuan_chi_mot_chuong(canh):
    """Nhịp chạy mỗi phút; không có hàng rào thì một tuần là hàng nghìn chuông."""
    canh_bao_tien_do.quet()
    canh_bao_tien_do.quet()
    canh_bao_tien_do.quet()
    assert len(_chuong(canh['gv'], canh['lop'])) == 1, 'quét ba lần ra nhiều hơn một chuông'


def test_tuan_sau_bao_lai(canh):
    """Lớp vẫn chậm sang tuần sau thì phải nhắc lại — im luôn là quên mất lớp ấy."""
    canh_bao_tien_do.quet()
    # Dời chuông tuần này lùi 8 ngày: đúng như thể nó được gửi tuần trước.
    x("""UPDATE notifications SET created_at = created_at - INTERVAL '8 days'
          WHERE user_id = %s AND type = 'cham_tien_do' AND ref_id = %s""",
      (canh['gv'], canh['lop']))
    canh_bao_tien_do.quet()
    assert len(_chuong(canh['gv'], canh['lop'])) == 2, 'sang tuần mới vẫn không nhắc lại'


def test_quet_tra_ve_so_chuong_MOI(canh):
    assert canh_bao_tien_do.quet() >= 3, 'lượt đầu phải sinh chuông cho gv + tg + học vụ'
    assert canh_bao_tien_do.quet() == 0, 'lượt hai không có chuông mới mà vẫn đếm'
