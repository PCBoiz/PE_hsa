"""Cơ sở tính học phí — sai ở đây là ra tiền sai, và không ai kêu.

Chạy trên DB thật, mọi thứ nằm trong giao dịch được CUỘN LẠI (xem `conftest.py`).

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

Bảng này không thu tiền, nhưng người ta sẽ THU TIỀN THEO NÓ. Ba lỗi có thể mắc
mà không có gì kêu lên, vì tất cả đều trả HTTP 200 kèm một con số trông hợp lý:

  1. Đếm buổi của cả lớp rồi gán cho mọi em → em vào lớp giữa chừng bị tính
     đủ số buổi từ đầu khoá. Ở một trung tâm luyện thi, vào giữa chừng là
     chuyện thường ngày, nên lỗi này thu thừa của gần như mọi khoá.
  2. Buổi đã huỷ vẫn tính là buổi đã mở → thu tiền một buổi không ai dạy.
  3. Điểm danh nằm ngoài quãng ghi danh bị nuốt vào tổng → hoặc thu tiền một
     buổi học thử, hoặc bỏ sót một ngày ghi danh nhập sai.

Phép kiểm cuối cùng canh RANH GIỚI của cả tệp: phản hồi không được có trường
tiền nào. Đó là điều phân biệt "cơ sở tính" với "mô-đun học phí" — và là ranh
giới anh Sơn chốt ngày 07/09/2026.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.clock import local_now
from common.db import q1
from common.permissions import ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER
from teaching.co_so_hoc_phi import AdminBillingBasisView

f = APIRequestFactory()


def _goi(ai, **tham_so):
    req = f.get('/x', tham_so)
    force_authenticate(req, user=ai)
    return AdminBillingBasisView.as_view()(req)


def _nguoi(ten, vai):
    row = q1('INSERT INTO users (name, email, password, role, streak) '
             "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             (ten, '%s_hp@example.com' % ten.replace(' ', '_'), vai))
    return User.objects.get(id=row['id'])


@pytest.fixture
def canh(db):
    """Một lớp, bốn buổi (một đã huỷ), hai em vào lớp ở hai thời điểm khác nhau."""
    qt = _nguoi('QT HocPhi', ROLE_ADMIN)
    gv = _nguoi('GV HocPhi', ROLE_TEACHER)
    som = _nguoi('Em Vao Som', ROLE_STUDENT)
    muon = _nguoi('Em Vao Muon', ROLE_STUDENT)

    c = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
           "VALUES ('Lop hoc phi','hsa_quantitative',%s,'active') RETURNING id", (gv.id,))
    lop = c['id']
    nay = local_now()

    # Bốn buổi: cách nhau 7 ngày, lùi về quá khứ. Buổi thứ tư ĐÃ HUỶ.
    buoi = []
    for i, tt in enumerate(['done', 'done', 'done', 'cancelled']):
        d = q1('INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status, '
               'created_by) VALUES (%s,%s,90,%s,%s) RETURNING id',
               (lop, nay - timedelta(days=28 - i * 7), tt, gv.id))
        buoi.append(d['id'])

    # Em vào SỚM: trước cả buổi đầu → dự được cả ba buổi chưa huỷ.
    q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) '
       'RETURNING id', (lop, som.id, nay - timedelta(days=30)))
    # Em vào MUỘN: sau buổi 1 và 2 → chỉ còn buổi 3 nằm trong quãng của em.
    q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) '
       'RETURNING id', (lop, muon.id, nay - timedelta(days=16)))

    return {'lop': lop, 'qt': qt, 'som': som, 'muon': muon, 'buoi': buoi}


def _lop(kq, lop_id):
    return next(l for l in kq.data['lop'] if l['id'] == lop_id)


def _em(l, uid):
    return next(e for e in l['hocVien'] if e['userId'] == uid)


@pytest.mark.django_db
def test_em_vao_giua_chung_khong_bi_tinh_du_ca_khoa(canh):
    """Lỗi thu thừa dễ mắc nhất: gán số buổi của LỚP cho mọi em."""
    l = _lop(_goi(canh['qt']), canh['lop'])
    assert l['buoiDaMo'] == 3, l          # ba buổi chưa huỷ
    assert _em(l, canh['som'].id)['buoiTrongKy'] == 3
    # Em vào ngày thứ 16 trước hôm nay: chỉ buổi cuối (ngày 14) nằm sau đó.
    assert _em(l, canh['muon'].id)['buoiTrongKy'] == 1, _em(l, canh['muon'].id)


@pytest.mark.django_db
def test_buoi_da_huy_khong_tinh_la_buoi_da_mo(canh):
    l = _lop(_goi(canh['qt']), canh['lop'])
    assert l['buoiDaMo'] == 3
    assert l['buoiDaHuy'] == 1, l
    # Và nó cũng không lọt vào quãng của em nào.
    assert _em(l, canh['som'].id)['buoiTrongKy'] == 3


@pytest.mark.django_db
def test_diem_danh_truoc_ngay_ghi_danh_hien_thanh_cot_rieng(canh):
    """Buổi học thử, hay ngày ghi danh nhập sai — hai chuyện ra tiền ngược nhau.

    Máy không phân biệt được nên KHÔNG nuốt vào tổng; nó phải nổi lên thành một
    cột để người nhìn phân biệt.
    """
    # Em vào muộn được điểm danh ở buổi ĐẦU — trước cả ngày em vào lớp.
    q1("INSERT INTO attendance (session_id, user_id, status, marked_by) "
       'VALUES (%s,%s,%s,%s) RETURNING session_id',
       (canh['buoi'][0], canh['muon'].id, 'present', canh['qt'].id))

    l = _lop(_goi(canh['qt']), canh['lop'])
    e = _em(l, canh['muon'].id)
    assert e['lechGhiDanh'] == 1, e
    # Vẫn đếm là có mặt (chuyện đã xảy ra thật), nhưng quãng ghi danh không đổi.
    assert e['coMat'] == 1, e
    assert e['buoiTrongKy'] == 1, e
    # Em vào sớm không dính gì.
    assert _em(l, canh['som'].id)['lechGhiDanh'] == 0


@pytest.mark.django_db
def test_muon_van_la_co_mat_nhung_dem_rieng(canh):
    q1("INSERT INTO attendance (session_id, user_id, status, marked_by) "
       'VALUES (%s,%s,%s,%s) RETURNING session_id',
       (canh['buoi'][1], canh['som'].id, 'late', canh['qt'].id))
    q1("INSERT INTO attendance (session_id, user_id, status, marked_by) "
       'VALUES (%s,%s,%s,%s) RETURNING session_id',
       (canh['buoi'][2], canh['som'].id, 'absent', canh['qt'].id))

    e = _em(_lop(_goi(canh['qt']), canh['lop']), canh['som'].id)
    assert e['coMat'] == 1, e     # `late` tính là có mặt
    assert e['muon'] == 1, e
    assert e['vang'] == 1, e


@pytest.mark.django_db
def test_chi_quan_tri_vien_xem_duoc(canh):
    gv = _nguoi('GV Khac', ROLE_TEACHER)
    assert _goi(gv).status_code == 403
    assert _goi(canh['som']).status_code == 403
    assert _goi(canh['qt']).status_code == 200


@pytest.mark.django_db
def test_KHONG_co_truong_tien_nao_trong_phan_hoi(canh):
    """RANH GIỚI của cả tệp — anh Sơn chốt 07/09/2026: cơ sở tính, không kế toán.

    Phép kiểm này không canh một lỗi; nó canh một QUYẾT ĐỊNH. Ngày ai đó thấy
    tiện tay thêm `donGia` vào đây, cả ranh giới "chỉ dựng phần không phụ thuộc
    quy trình TopHSA" sẽ trôi đi trong một dòng mã, và không có gì khác trong
    dự án nhận ra.
    """
    # Soi TÊN KHOÁ, không soi cả chuỗi JSON.
    #
    # Bản đầu của phép kiểm này tìm chuỗi con trong toàn bộ JSON và ĐỎ ngay
    # lượt chạy đầu: `'gia'` nằm trong `giangVien`. Một phép kiểm báo oan tệ
    # ngang một phép kiểm bỏ sót — nó dạy người đọc sau bỏ qua chính nó.
    def khoa(x):
        if isinstance(x, dict):
            for k, v in x.items():
                yield k
                yield from khoa(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                yield from khoa(v)

    CAM = {'gia', 'dongia', 'thanhtien', 'tien', 'sotien', 'hocphi',
           'price', 'amount', 'money', 'currency', 'fee', 'total',
           'invoice', 'hoadon', 'congno', 'debt', 'paid', 'payment'}
    for k in khoa(_goi(canh['qt']).data):
        assert k.lower().replace('_', '') not in CAM, k


@pytest.mark.django_db
def test_KHONG_tinh_tien_nguoi_khong_phai_hoc_vien(canh):
    """Quản trị viên ngồi trong lớp để xem giao diện — không phải người phải đóng tiền.

    Trên CSDL thật, tài khoản quản trị (id 7) ĐANG là thành viên lớp 1, và anh
    Sơn chốt giữ nó ở đó. Bản đầu của view này quên lọc theo vai, nên lượt gọi
    thật đầu tiên trả về "Quản trị viên · admin@pe-hsa.vn" nằm giữa danh sách
    học viên. Ở bảng tiến độ đó là một dòng thừa; ở bảng học phí đó là một hoá
    đơn gửi nhầm.
    """
    q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) '
       'RETURNING id', (canh['lop'], canh['qt'].id, local_now() - timedelta(days=30)))

    l = _lop(_goi(canh['qt']), canh['lop'])
    ids = {e['userId'] for e in l['hocVien']}
    assert canh['qt'].id not in ids, l['hocVien']
    assert ids == {canh['som'].id, canh['muon'].id}, ids
