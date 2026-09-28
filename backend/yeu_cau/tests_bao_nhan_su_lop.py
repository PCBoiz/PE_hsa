"""DUYỆT XONG THÌ BÁO NGƯỜI ĐỨNG LỚP — không chỉ báo người gửi đơn.

── LỖ ĐANG CHẶN LẠI (28/09/2026) ───────────────────────────────────────────

Duyệt "xin nghỉ học" GHI ĐÈ sổ điểm danh: các buổi trong khoảng ngày thành `excused`, kể cả
buổi em đã bị đánh `present` hay `absent` trước đó (`yeu_cau/thuc_thi.py`, nhánh
`tt_nghi_hoc`). Việc ấy đúng — học vụ duyệt đơn nghỉ phép là quyết định cuối.

Cái sai là **không ai báo cho người đứng lớp**. `_bao_nguoi_gui` chỉ gửi cho người tạo đơn và
cho em. Giảng viên mở sổ điểm danh tuần sau, thấy một em "có phép" ở buổi mình nhớ rõ là em
vắng không lý do, và không có gì trên màn nói ai đổi, đổi lúc nào, vì đơn nào. Đó là chỗ dễ
sinh tranh luận nhất về sau, và tranh luận ấy không có bằng chứng để kết.

Anh Sơn 27/09 được hỏi *"Duyệt 'xin nghỉ học' có báo giảng viên của lớp không?"*, đề xuất của
tôi là **CÓ**. Chưa có trả lời tính tới 28/09; làm theo mặc định đã nêu, và mặc định ấy ghi
ngay trong `dich_vu.BAO_NHAN_SU_LOP` để đổi là một dòng.

── AI ĐƯỢC BÁO ─────────────────────────────────────────────────────────────

Giảng viên phụ trách lớp, trợ giảng của lớp, và học vụ được gán vào lớp — cùng tập người mà
`can_see_class` cho vào lớp ấy, TRỪ nhóm nhìn thấy mọi lớp (quản trị viên, và học vụ chưa
được gán): báo cho người nhìn thấy mọi lớp là báo cho họ mọi đơn nghỉ của cả trung tâm.

Người BẤM duyệt không tự nhận chuông về việc mình vừa làm.

Chạy trên CSDL thật, giao dịch CUỘN LẠI; chỉ đếm dữ liệu của chính mình.
"""
from datetime import timedelta

import pytest

from accounts.models import User
from common.clock import local_now, local_today
from common.db import q, q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER
from yeu_cau import dich_vu

pytestmark = pytest.mark.django_db


def _nguoi(ten, vai):
    r = q1("INSERT INTO users (name, email, password, role, streak) "
           "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
           (ten, '%s_bns@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=r['id'])


def _buoi(lop, cach_ngay):
    return q1('''INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status)
                 VALUES (%s, %s, 90, 'planned') RETURNING id''',
              (lop, local_now() + timedelta(days=cach_ngay)))['id']


@pytest.fixture
def canh():
    gv = _nguoi('GV Bao Nhan Su', ROLE_TEACHER)
    tg = _nguoi('TG Bao Nhan Su', ROLE_ASSISTANT)
    hv = _nguoi('Hoc Vu Bao Nhan Su', ROLE_ACADEMIC)      # KHÔNG được gán vào lớp
    hv2 = _nguoi('Hoc Vu Ngoai Lop', ROLE_ACADEMIC)      # cũng không
    hvl = _nguoi('Hoc Vu Phu Trach Lop', ROLE_ACADEMIC)  # ĐƯỢC gán — người này bấm duyệt
    em = _nguoi('Em Bao Nhan Su', ROLE_STUDENT)
    lop = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
             "VALUES ('Lop bao nhan su', 'hsa_quantitative', %s, 'active') RETURNING id",
             (gv.id,))['id']
    for u in (em, tg, hvl):
        x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s)',
          (lop, u.id, local_now() - timedelta(days=30)))
    return {'gv': gv, 'tg': tg, 'hv': hv, 'hv2': hv2, 'hvl': hvl, 'em': em, 'lop': lop}


def _tao_nghi_hoc(canh):
    import json
    tu = local_today() + timedelta(days=1)
    den = local_today() + timedelta(days=5)
    return q1('''INSERT INTO yeu_cau (loai, trang_thai, nguon, nguoi_tao, hoc_vien_id,
                                      class_id, tieu_de, du_lieu)
                 VALUES ('tt_nghi_hoc', 'moi', 'hoc_vien', %s, %s, %s, %s, %s::jsonb)
                 RETURNING id''',
              (canh['em'].id, canh['em'].id, canh['lop'], 'Xin nghi hoc',
               json.dumps({'tu_ngay': tu.isoformat(), 'den_ngay': den.isoformat()})))['id']


def _chuong(uid):
    return q("SELECT type, title, body FROM notifications WHERE user_id = %s ORDER BY id", (uid,))


# ── 1. Người đứng lớp được báo ──────────────────────────────────────────────

def test_duyet_nghi_hoc_bao_giang_vien_cua_lop(canh, django_capture_on_commit_callbacks):
    _buoi(canh['lop'], 2)
    yc = _tao_nghi_hoc(canh)
    with django_capture_on_commit_callbacks(execute=True):
        dich_vu.duyet(dich_vu.NguoiLam(user=canh['hv']), yc, {})
    ds = _chuong(canh['gv'].id)
    assert ds, 'giảng viên của lớp KHÔNG được báo gì'


def test_tro_giang_cua_lop_cung_duoc_bao(canh, django_capture_on_commit_callbacks):
    _buoi(canh['lop'], 2)
    yc = _tao_nghi_hoc(canh)
    with django_capture_on_commit_callbacks(execute=True):
        dich_vu.duyet(dich_vu.NguoiLam(user=canh['hv']), yc, {})
    assert _chuong(canh['tg'].id), 'trợ giảng của lớp KHÔNG được báo gì'


def test_chuong_noi_ro_em_nao_lop_nao_may_buoi(canh, django_capture_on_commit_callbacks):
    _buoi(canh['lop'], 2)
    _buoi(canh['lop'], 4)
    yc = _tao_nghi_hoc(canh)
    with django_capture_on_commit_callbacks(execute=True):
        dich_vu.duyet(dich_vu.NguoiLam(user=canh['hv']), yc, {})
    chu = ' '.join('%s %s' % (c['title'], c['body']) for c in _chuong(canh['gv'].id))
    assert 'Em Bao Nhan Su' in chu, 'chuông không nói em nào: %r' % chu
    assert '2 buổi' in chu, 'chuông không nói mấy buổi bị ghi đè: %r' % chu
    # RULES §10: chữ người dùng đọc, không phải mã kỹ thuật.
    assert 'tt_nghi_hoc' not in chu and 'excused' not in chu, 'mã kỹ thuật lọt lên chuông: %r' % chu


# ── 2. Ai KHÔNG được báo ────────────────────────────────────────────────────

def test_nguoi_bam_duyet_khong_tu_nhan_chuong(canh, django_capture_on_commit_callbacks):
    """Người bấm duyệt phải là người ĐANG ĐỨNG LỚP, nếu không phép kiểm này rỗng.

    Bản đầu cho một học vụ NGOÀI lớp bấm duyệt: họ vốn không có trong danh sách người đứng
    lớp, nên bỏ hẳn `tru=nguoi.id` cũng không đổi gì và đột biến ấy LỌT (đo 28/09). Ở đây
    dùng học vụ ĐƯỢC GÁN vào lớp — người duy nhất mà phép trừ có việc để làm.
    """
    _buoi(canh['lop'], 2)
    yc = _tao_nghi_hoc(canh)
    with django_capture_on_commit_callbacks(execute=True):
        dich_vu.duyet(dich_vu.NguoiLam(user=canh['hvl']), yc, {})
    assert _chuong(canh['gv'].id), 'cảnh dựng sai — giảng viên phải nhận được thì phép kiểm mới có nghĩa'
    assert not _chuong(canh['hvl'].id), 'người bấm duyệt tự nhận chuông về việc mình vừa làm'


def test_hoc_vu_khong_duoc_gan_vao_lop_thi_khong_bao(canh, django_capture_on_commit_callbacks):
    """Học vụ nhìn thấy MỌI lớp. Báo cho họ là báo mọi đơn nghỉ của cả trung tâm."""
    _buoi(canh['lop'], 2)
    yc = _tao_nghi_hoc(canh)
    with django_capture_on_commit_callbacks(execute=True):
        dich_vu.duyet(dich_vu.NguoiLam(user=canh['hv']), yc, {})
    assert not _chuong(canh['hv2'].id), 'học vụ ngoài lớp cũng nhận chuông'


def test_giang_vien_lop_KHAC_khong_nhan(canh, django_capture_on_commit_callbacks):
    gv2 = _nguoi('GV Lop Khac', ROLE_TEACHER)
    q1("INSERT INTO classes (name, course_id, teacher_id, status) "
       "VALUES ('Lop khac bns', 'hsa_quantitative', %s, 'active') RETURNING id", (gv2.id,))
    _buoi(canh['lop'], 2)
    yc = _tao_nghi_hoc(canh)
    with django_capture_on_commit_callbacks(execute=True):
        dich_vu.duyet(dich_vu.NguoiLam(user=canh['hv']), yc, {})
    assert not _chuong(gv2.id), 'giảng viên lớp khác cũng nhận chuông'


def test_tro_giang_DA_ROI_lop_khong_nhan_nua(canh, django_capture_on_commit_callbacks):
    """Gỡ một người khỏi lớp là ghi `left_at` — thiếu vế ấy thì họ nhận tin của lớp cũ mãi.

    Đây là phép kiểm mà bản đầu của bộ này KHÔNG có, và đột biến "bỏ `left_at IS NULL`" LỌT
    thẳng (đo 28/09). Cảnh không có ai đã rời lớp thì mệnh đề ấy không canh gì cả.
    """
    cu = _nguoi('TG Da Roi Lop', ROLE_ASSISTANT)
    x('''INSERT INTO class_members (class_id, user_id, joined_at, left_at)
         VALUES (%s, %s, %s, %s)''',
      (canh['lop'], cu.id, local_now() - timedelta(days=60), local_now() - timedelta(days=3)))
    _buoi(canh['lop'], 2)
    yc = _tao_nghi_hoc(canh)
    with django_capture_on_commit_callbacks(execute=True):
        dich_vu.duyet(dich_vu.NguoiLam(user=canh['hv']), yc, {})
    assert _chuong(canh['tg'].id), 'cảnh dựng sai — trợ giảng ĐANG ở lớp phải nhận được'
    assert not _chuong(cu.id), 'trợ giảng đã rời lớp vẫn nhận tin của lớp cũ'


# ── 3. Không báo khi việc KHÔNG xảy ra ──────────────────────────────────────

def test_duyet_hong_thi_khong_ai_duoc_bao(canh, django_capture_on_commit_callbacks):
    """Lớp không có buổi nào trong khoảng ngày → duyệt ném lỗi, giao dịch cuộn lại.

    Chuông đi trước khi biết việc có thành hay không là chuông nói dối: giảng viên đọc
    "đã ghi có phép 0 buổi" rồi đi tìm thứ không tồn tại.
    """
    yc = _tao_nghi_hoc(canh)          # KHÔNG tạo buổi nào
    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(dich_vu.LoiYeuCau):
            dich_vu.duyet(dich_vu.NguoiLam(user=canh['hv']), yc, {})
    assert not _chuong(canh['gv'].id), 'duyệt hỏng mà giảng viên vẫn nhận chuông'


def test_loai_KHAC_duyet_xong_van_khong_bao_nguoi_dung_lop(canh,
                                                            django_capture_on_commit_callbacks):
    """Một loại ĐI QUA ĐÚNG ĐƯỜNG DUYỆT nhưng không nằm trong `BAO_NHAN_SU_LOP`.

    Bản đầu lấy "hỗ trợ kỹ thuật" và gọi `tra_loi` — đường ấy không chạm dòng bị đột biến,
    nên "mọi loại đều gọi chuông" LỌT (đo 28/09). "Xin bảo lưu" thì duyệt thật, tự làm thật,
    và vẫn phải im: nó cho em rời lớp chứ không ghi đè sổ điểm danh đã chấm.
    """
    import json
    yc = q1('''INSERT INTO yeu_cau (loai, trang_thai, nguon, nguoi_tao, hoc_vien_id,
                                    class_id, tieu_de, du_lieu)
               VALUES ('tt_bao_luu', 'moi', 'hoc_vien', %s, %s, %s, 'Xin bao luu', %s::jsonb)
               RETURNING id''',
            (canh['em'].id, canh['em'].id, canh['lop'], json.dumps({})))['id']
    with django_capture_on_commit_callbacks(execute=True):
        dich_vu.duyet(dich_vu.NguoiLam(user=canh['hv']), yc, {})
    assert not _chuong(canh['gv'].id), 'loại ngoài danh sách cũng gọi chuông cho người đứng lớp'
    assert not _chuong(canh['tg'].id), 'loại ngoài danh sách cũng gọi chuông cho trợ giảng'
