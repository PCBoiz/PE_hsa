"""TRỢ GIẢNG TRÊN TỜ BÁO CÁO PHỤ HUYNH (§66 — bảng TopHSA dòng 24).

Bảng của khách, dòng 24: phụ huynh xem được *"lịch học, giảng viên, trợ giảng"*. Tờ đã có
giảng viên từ lâu; trợ giảng thì chưa bao giờ. Agent soát đo 27/09 và đó là **thứ duy nhất
còn thiếu của dòng 24** — nên nó đáng một phép kiểm riêng, đứng trước khi có mã.

── VÌ SAO PHỤ HUYNH CẦN TÊN TRỢ GIẢNG ────────────────────────────────────────

Ở TopHSA, trợ giảng mới là người nhắc bài hằng ngày và là người phụ huynh nhắn khi con
nghỉ. Một tờ báo cáo chỉ có tên giảng viên thì phụ huynh không biết ai đang thật sự theo
con mình — họ nhắn cho giảng viên, giảng viên chuyển lại, và lời nhắn tới muộn một ngày.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Lớp có trợ giảng → tờ mang tên trợ giảng.
  2. Trợ giảng ĐÃ RỜI lớp (`left_at`) không còn trên tờ. Gỡ một người khỏi lớp mà tên họ
     vẫn nằm trên giấy gửi phụ huynh là một lời giới thiệu sai, và không ai gỡ được nữa.
  3. Lớp chưa có trợ giảng → `null`, KHÔNG phải chuỗi rỗng hay "Chưa có": màn hình quyết
     định hiển thị gì, dữ liệu chỉ nói có hay không.
  4. Hai trợ giảng thì cả hai lên tờ — TopHSA có lớp đông hai người kèm.
  5. **Học viên trong lớp KHÔNG bị nhận nhầm là trợ giảng.** Cả hai đều là dòng
     `class_members`; phân biệt bằng VAI, không bằng việc có mặt trong bảng ấy.

Chạy trên CSDL thật, giao dịch CUỘN LẠI; chỉ đếm dữ liệu của chính mình.
"""
from datetime import timedelta

import pytest

from common.clock import local_now, local_today
from common.db import q1, x
from common.permissions import ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER
from teaching.parent_report import dung_bao_cao
from teaching.tests_parent_link import _nguoi

pytestmark = pytest.mark.django_db


def _lop(ten, gv):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status) "
              "VALUES (%s, 'hsa_quantitative', %s, 'active') RETURNING id", (ten, gv.id))['id']


def _vao(lop, u, roi=False):
    x('INSERT INTO class_members (class_id, user_id, joined_at, left_at) VALUES (%s,%s,%s,%s)',
      (lop, u.id, local_now() - timedelta(days=30),
       local_now() - timedelta(days=2) if roi else None))


def _to(lop, em):
    den = local_today()
    d, loi = dung_bao_cao(lop, em.id, den - timedelta(days=28), den)
    assert d, loi
    return d


@pytest.fixture
def canh():
    gv = _nguoi('GV To TG', ROLE_TEACHER)
    em = _nguoi('Em To TG', ROLE_STUDENT)
    lop = _lop('Lop to tro giang', gv)
    _vao(lop, em)
    return {'gv': gv, 'em': em, 'lop': lop}


def test_lop_co_tro_giang_thi_to_mang_ten(canh):
    tg = _nguoi('Co Tro Giang A', ROLE_ASSISTANT)
    _vao(canh['lop'], tg)
    assert _to(canh['lop'], canh['em'])['class']['assistants'] == ['Co Tro Giang A']


def test_tro_giang_da_roi_lop_khong_con_tren_to(canh):
    """Gỡ một người khỏi lớp mà tên họ vẫn nằm trên giấy gửi phụ huynh là lời giới thiệu
    sai, và phụ huynh không có cách nào biết."""
    tg = _nguoi('Co Da Roi Lop', ROLE_ASSISTANT)
    _vao(canh['lop'], tg, roi=True)
    assert _to(canh['lop'], canh['em'])['class']['assistants'] == []


def test_lop_chua_co_tro_giang_thi_danh_sach_rong(canh):
    assert _to(canh['lop'], canh['em'])['class']['assistants'] == []


def test_hai_tro_giang_thi_ca_hai_len_to(canh):
    for ten in ('Co Tro Giang B', 'Thay Tro Giang C'):
        _vao(canh['lop'], _nguoi(ten, ROLE_ASSISTANT))
    assert sorted(_to(canh['lop'], canh['em'])['class']['assistants']) == \
        ['Co Tro Giang B', 'Thay Tro Giang C']


def test_hoc_vien_khong_bi_nham_la_tro_giang(canh):
    """Học viên và trợ giảng cùng nằm trong `class_members` — phân biệt bằng VAI."""
    _vao(canh['lop'], _nguoi('Em Khac To TG', ROLE_STUDENT))
    assert _to(canh['lop'], canh['em'])['class']['assistants'] == []


def test_giang_vien_van_nguyen_cho_cu(canh):
    """Thêm trợ giảng không được làm xê dịch thứ tờ đã có."""
    _vao(canh['lop'], _nguoi('Co Tro Giang D', ROLE_ASSISTANT))
    assert _to(canh['lop'], canh['em'])['class']['teacher'] == 'GV To TG'


def test_ten_tro_giang_di_qua_duoc_duong_cong_khai(canh):
    """Tờ mở bằng chìa (phụ huynh không có tài khoản) VẪN phải có tên trợ giảng.

    `rut_gon_cho_link` bỏ email/số điện thoại vì chìa có thể bị chuyển tiếp. Tên nhân sự
    phụ trách lớp thì ngược lại: nó là thứ tờ sinh ra để nói. Ghim ở đây để một lượt siết
    đường công khai sau này không lỡ tay cắt mất đúng phần dòng 24 đang đòi.
    """
    from teaching.parent_report import rut_gon_cho_link
    _vao(canh['lop'], _nguoi('Co Tro Giang E', ROLE_ASSISTANT))
    mong = rut_gon_cho_link(_to(canh['lop'], canh['em']))
    assert mong['class']['assistants'] == ['Co Tro Giang E']
    # Và đường ấy vẫn không mang liên lạc của em — hai luật cùng đứng.
    assert 'email' not in mong['student'] and 'phone' not in mong['student']
