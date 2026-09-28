"""§75 · DIỄN ĐÀN RIÊNG CỦA LỚP — anh Sơn chốt 27/09/2026.

Nguyên văn: *"Những phần như này thì mình biến thành nhắn tin qua Zalo hoặc qua diễn đàn
riêng của lớp, không làm thành 1 messenger trong ứng dụng mình đâu"* — cho ô STT 20 của bảng
phân rã (trợ giảng nhắn / nhận tin / theo dõi lịch sử trao đổi).

Diễn đàn tới hôm nay là MỘT SÂN CHUNG: mọi người đăng nhập đều đọc được mọi bài. Khoanh nó
theo lớp không phải thêm một bộ lọc trên màn — bộ lọc trên màn chỉ giấu, còn cửa API vẫn trả.

Ba chỗ hỏng thì hỏng NẶNG, mỗi chỗ một phép kiểm:

  · **bài của lớp lọt ra sân chung** — em lớp khác mở `/api/posts` thấy nguyên văn trao đổi
    riêng của lớp. Đây là rò rỉ, không phải lỗi hiển thị;
  · **người ngoài lớp đọc được bài của lớp** qua đường `/api/posts/<id>` (đoán id là xong);
  · **em đã rời lớp vẫn đọc tiếp** — `class_members.left_at` là thứ duy nhất phân biệt.

Trả **404** chứ không 403 cho người ngoài: cùng luật với mọi cửa lớp — không lộ lớp nào tồn tại.
"""
import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.db import q1, x


class Dung:
    """Dựng nền bằng SQL; phần đang kiểm luôn đi qua API thật."""

    def __init__(self):
        import uuid
        self.ht = uuid.uuid4().hex[:10]
        self.dem = 0

    def nguoi(self, vai='Học viên'):
        self.dem += 1
        return q1("INSERT INTO users (name, email, password, role) "
                  "VALUES (%s, %s, 'x', %s) RETURNING id",
                  ('DD %s %d' % (self.ht, self.dem), 'dj_dd_%s_%d@example.com' % (self.ht, self.dem),
                   vai))['id']

    def api(self, vai='Học viên', uid=None):
        c = APIClient()
        uid = uid or self.nguoi(vai)
        c.force_authenticate(user=User.objects.get(id=uid))
        c.uid = uid
        return c

    def lop(self, gv=None):
        return q1("INSERT INTO classes (name, status, teacher_id) "
                  "VALUES (%s, 'active', %s) RETURNING id", ('Lớp DD ' + self.ht, gv))['id']

    def vao(self, lop, uid, roi=False):
        x('INSERT INTO class_members (class_id, user_id, joined_at, left_at) '
          'VALUES (%s, %s, now(), %s)', (lop, uid, 'now()' if False else None))
        if roi:
            x('UPDATE class_members SET left_at = now() WHERE class_id=%s AND user_id=%s',
              (lop, uid))


@pytest.fixture
def canh(db):
    d = Dung()
    gv = d.api('Giảng viên')
    lop = d.lop(gv=gv.uid)
    em = d.api('Học viên')
    d.vao(lop, em.uid)
    nguoi_la = d.api('Học viên')          # học viên lớp khác
    return {'d': d, 'gv': gv, 'lop': lop, 'em': em, 'la': nguoi_la}


def _dang(c, lop, noi_dung='Chiều nay các em nhớ làm bài 3 nhé'):
    return c.post('/api/posts', {'title': 'Nhắc lớp', 'content': noi_dung,
                                 'category': 'discuss', 'class_id': lop}, format='json')


def test_giang_vien_dang_duoc_bai_cho_rieng_lop(canh):
    r = _dang(canh['gv'], canh['lop'])
    assert r.status_code in (200, 201), r.data
    pid = r.data.get('id') or r.data.get('post', {}).get('id')
    assert pid
    assert q1('SELECT class_id FROM posts WHERE id=%s', (pid,))['class_id'] == canh['lop']


def test_bai_cua_lop_KHONG_lot_ra_san_chung(canh):
    """Sân chung `/api/posts` không kèm `lop` thì chỉ trả bài KHÔNG thuộc lớp nào."""
    _dang(canh['gv'], canh['lop'], 'Trao đổi riêng của lớp')
    r = canh['la'].get('/api/posts')
    assert r.status_code == 200
    chu = str(r.data)
    assert 'Trao đổi riêng của lớp' not in chu, 'bài riêng của lớp lọt ra sân chung'


def test_nguoi_ngoai_lop_khong_doc_duoc_bai_cua_lop(canh):
    pid = _dang(canh['gv'], canh['lop']).data['id']
    assert canh['la'].get('/api/posts/%d' % pid).status_code == 404
    assert canh['la'].get('/api/posts?lop=%d' % canh['lop']).status_code == 404


def test_em_trong_lop_doc_va_tra_loi_duoc(canh):
    pid = _dang(canh['gv'], canh['lop']).data['id']
    assert canh['em'].get('/api/posts/%d' % pid).status_code == 200
    r = canh['em'].get('/api/posts?lop=%d' % canh['lop'])
    assert r.status_code == 200 and str(r.data).count('Nhắc lớp') >= 1
    tl = canh['em'].post('/api/posts/%d/comments' % pid, {'content': 'Em rõ rồi ạ'}, format='json')
    assert tl.status_code in (200, 201), tl.data


def test_em_da_ROI_lop_khong_doc_duoc_nua(canh):
    pid = _dang(canh['gv'], canh['lop']).data['id']
    cu = canh['d'].api('Học viên')
    canh['d'].vao(canh['lop'], cu.uid, roi=True)
    assert cu.get('/api/posts/%d' % pid).status_code == 404


def test_nguoi_ngoai_khong_dang_duoc_vao_lop(canh):
    assert _dang(canh['la'], canh['lop']).status_code == 404


def test_binh_luan_cua_bai_lop_khong_doc_duoc_tu_ngoai(canh):
    pid = _dang(canh['gv'], canh['lop']).data['id']
    canh['em'].post('/api/posts/%d/comments' % pid, {'content': 'Em rõ rồi ạ'}, format='json')
    assert canh['la'].get('/api/posts/%d/comments' % pid).status_code == 404


def test_cua_dien_dan_lop_tra_ten_lop_de_man_khoi_phai_hoi_hai_lan(canh):
    """Màn cần tên lớp để đặt tiêu đề. Không trả kèm thì màn phải gọi thêm một cửa nữa —
    mà học viên KHÔNG có cửa nào đọc được thông tin lớp (những cửa ấy là `IsTeachingStaff`).
    """
    r = canh['em'].get('/api/posts?lop=%d' % canh['lop'])
    assert r.status_code == 200
    assert r.data['lop']['id'] == canh['lop']
    assert r.data['lop']['ten'], 'thiếu tên lớp'
    # Sân chung thì KHÔNG có khối ấy — không có lớp nào để đặt tên.
    assert 'lop' not in canh['la'].get('/api/posts').data
