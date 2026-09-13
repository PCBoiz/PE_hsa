"""Dán liên hệ phụ huynh cho cả lớp — `POST /api/teach/classes/<id>/parent-contacts`.

Chạy trên DB thật, trong giao dịch được CUỘN LẠI (xem `conftest.py`). Mọi lời
gọi đi qua URL thật chứ không gọi thẳng lớp view: phép kiểm đi tắt sẽ bỏ qua
đúng bộ định tuyến và cổng phân quyền mà nó cần canh.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Trợ giảng KHÔNG chạm được (anh Sơn chốt 01/09/2026: liên lạc của em là thứ
     trợ giảng không đụng), giảng viên lớp khác nhận 404 chứ không phải 403.
  2. Xem trước KHÔNG ghi gì — kể cả nhật ký kiểm toán.
  3. Chỉ ghi được cho em ĐANG HỌC của CHÍNH lớp ấy. Dán email của một em lớp
     khác vào là một cách ghi đè liên hệ phụ huynh của em đó — phải trượt.
  4. Ô để trống thì GIỮ giá trị cũ. Dán thiếu cột email không được xoá trắng
     email phụ huynh đang có.
  5. Tên trùng trong lớp thì không đoán.
  6. Nhật ký giữ giá trị CŨ — đó là đường hoàn tác duy nhất của một lần dán nhầm.
"""
import json
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q1, x
from common.permissions import (
    ROLE_ACADEMIC,
    ROLE_ASSISTANT,
    ROLE_STUDENT,
    ROLE_TEACHER,
)

pytestmark = pytest.mark.django_db


def _nguoi(ten, vai, email=None, phone=None, **cot):
    khoa = ''.join(', ' + k for k in cot)
    cho = ''.join(', %s' for _ in cot)
    row = q1(f'INSERT INTO users (name, email, phone, password, role, streak{khoa}) '
             f'VALUES (%s, %s, %s, %s, %s, 0{cho}) RETURNING id',
             (ten, email, phone, 'x', vai, *cot.values()))
    return User.objects.get(id=row['id'])


def _vao_lop(class_id, u, roi=False):
    nay = local_now()
    x('INSERT INTO class_members (class_id, user_id, joined_at, left_at) VALUES (%s,%s,%s,%s)',
      (class_id, u.id, nay - timedelta(days=20), nay - timedelta(days=2) if roi else None))


def _lop(ten, gv):
    return q1("INSERT INTO classes (name, course_id, teacher_id, status) "
              "VALUES (%s,'hsa_quantitative',%s,'active') RETURNING id", (ten, gv.id))['id']


def _ph(u):
    return q1('SELECT parent_name, parent_phone, parent_email FROM users WHERE id=%s', (u.id,))


@pytest.fixture
def lop(db):
    gv = _nguoi('GV LHPH', ROLE_TEACHER, email='gv_lhph@example.com')
    gv_khac = _nguoi('GV Khac LHPH', ROLE_TEACHER, email='gvkhac_lhph@example.com')
    c = _lop('Lop LHPH', gv)
    c_khac = _lop('Lop khac LHPH', gv_khac)

    an = _nguoi('Nguyễn Văn An', ROLE_STUDENT, email='an_lhph@example.com',
                phone='0900555101', parent_name='Mẹ An cũ', parent_phone='0900555901')
    binh = _nguoi('Trần Thị Bình', ROLE_STUDENT, phone='0900555102')
    chau1 = _nguoi('Lê Minh Châu', ROLE_STUDENT, email='chau1_lhph@example.com')
    chau2 = _nguoi('Lê Minh Châu', ROLE_STUDENT, email='chau2_lhph@example.com')
    da_roi = _nguoi('Đỗ Đã Rời', ROLE_STUDENT, email='roi_lhph@example.com')
    ngoai = _nguoi('Người Ngoài', ROLE_STUDENT, email='ngoai_lhph@example.com',
                   parent_email='bo.ngoai@example.com')
    tg = _nguoi('TG LHPH', ROLE_ASSISTANT, email='tg_lhph@example.com')

    for u in (an, binh, chau1, chau2, tg):
        _vao_lop(c, u)
    _vao_lop(c, da_roi, roi=True)
    _vao_lop(c_khac, ngoai)
    return {'id': c, 'gv': gv, 'gv_khac': gv_khac, 'an': an, 'binh': binh,
            'chau1': chau1, 'chau2': chau2, 'da_roi': da_roi, 'ngoai': ngoai, 'tg': tg}


def _dan(ai, class_id, text, dry_run=False):
    api = APIClient()
    if ai is not None:
        api.force_authenticate(user=ai)
    return api.post(f'/api/teach/classes/{class_id}/parent-contacts',
                    {'text': text, 'dry_run': dry_run}, format='json')


def _theo_dong(r):
    return {d['line']: d for d in r.json()['rows']}


# ── 1. Ai được dán ──────────────────────────────────────────────────────────

def test_chi_giang_vien_hoc_vu_quan_tri_cua_lop_duoc_dan(lop):
    dong = 'an_lhph@example.com, Mẹ An, 0900555801'
    assert _dan(None, lop['id'], dong, True).status_code == 401
    assert _dan(lop['an'], lop['id'], dong, True).status_code == 403, 'học viên'
    # Trợ giảng ĐANG Ở trong lớp vẫn bị chặn — vào được lớp không có nghĩa là
    # chạm được số điện thoại của bố mẹ các em.
    assert _dan(lop['tg'], lop['id'], dong, True).status_code == 403, 'trợ giảng'
    # 404, không phải 403: không để lộ rằng lớp ấy có tồn tại.
    assert _dan(lop['gv_khac'], lop['id'], dong, True).status_code == 404
    assert _dan(lop['gv'], lop['id'], dong, True).status_code == 200
    hoc_vu = _nguoi('Hoc Vu LHPH', ROLE_ACADEMIC, email='hv_lhph@example.com')
    assert _dan(hoc_vu, lop['id'], dong, True).status_code == 200


# ── 2. Xem trước không ghi gì ───────────────────────────────────────────────

def test_xem_truoc_khong_ghi_gi_ca_nhat_ky(lop):
    truoc_nk = q1('SELECT COUNT(*) AS n FROM admin_audit')['n']
    r = _dan(lop['gv'], lop['id'],
             'an_lhph@example.com, Mẹ An Mới, 0900555801, me.an@example.com', dry_run=True)
    assert r.status_code == 200, r.json()
    d = r.json()
    assert d['dryRun'] is True
    assert d['dem']['doi'] == 1, d
    assert _ph(lop['an']) == {'parent_name': 'Mẹ An cũ', 'parent_phone': '0900555901',
                              'parent_email': ''}
    assert q1('SELECT COUNT(*) AS n FROM admin_audit')['n'] == truoc_nk


# ── 3 + 4 + 6. Lưu thật: đúng em, giữ ô trống, nhật ký giữ giá trị cũ ───────

def test_luu_ghi_dung_giu_o_trong_va_nhat_ky_giu_gia_tri_cu(lop):
    # Không có cột số điện thoại → số cũ phải còn nguyên. Email viết hoa → lưu
    # bản chuẩn hoá, cùng luật với ô tự điền ở Cài đặt.
    r = _dan(lop['gv'], lop['id'], 'an_lhph@example.com\tMẹ An Mới\t\tMe.An@Example.com')
    assert r.status_code == 200, r.json()
    assert r.json()['dryRun'] is False
    assert _ph(lop['an']) == {'parent_name': 'Mẹ An Mới', 'parent_phone': '0900555901',
                              'parent_email': 'me.an@example.com'}

    nk = q1("SELECT target_type, target_id, detail FROM admin_audit "
            "WHERE action='class.parent_contacts' ORDER BY id DESC LIMIT 1")
    assert nk is not None, 'lưu liên hệ phụ huynh mà nhật ký kiểm toán không có dòng nào'
    assert (nk['target_type'], nk['target_id']) == ('class', str(lop['id']))
    # Con trỏ thô của Django trả cột jsonb dưới dạng CHUỖI, không phải dict.
    chi_tiet = json.loads(nk['detail']) if isinstance(nk['detail'], str) else nk['detail']
    doi = {e['id']: e for e in chi_tiet['doi']}[lop['an'].id]
    assert doi['parentName'] == {'cu': 'Mẹ An cũ', 'moi': 'Mẹ An Mới'}
    assert 'parentPhone' not in doi, 'ô không đổi không được ghi vào nhật ký như một thay đổi'


def test_khong_ghi_duoc_cho_em_lop_khac_hay_em_da_roi(lop):
    r = _dan(lop['gv'], lop['id'],
             'ngoai_lhph@example.com, Kẻ Lạ, 0900555999, ke.la@example.com\n'
             'roi_lhph@example.com, Kẻ Lạ, 0900555998')
    assert r.status_code == 200, r.json()
    dong = _theo_dong(r)
    assert dong[1]['trangThai'] == 'bo_qua' and 'Không tìm thấy' in dong[1]['lyDo'], dong[1]
    assert dong[2]['trangThai'] == 'bo_qua', dong[2]
    assert _ph(lop['ngoai'])['parent_email'] == 'bo.ngoai@example.com'
    assert _ph(lop['da_roi'])['parent_phone'] in (None, '')


# ── 5. Tên trùng thì không đoán ─────────────────────────────────────────────

def test_ten_trung_trong_lop_phai_dung_email_hoac_so(lop):
    r = _dan(lop['gv'], lop['id'], 'Lê Minh Châu, Bố Châu, 0900555803', dry_run=True)
    d = _theo_dong(r)[1]
    assert d['trangThai'] == 'bo_qua' and '2 em' in d['lyDo'], d

    r = _dan(lop['gv'], lop['id'], 'chau2_lhph@example.com, Bố Châu, 0900555803')
    assert _theo_dong(r)[1]['trangThai'] == 'doi'
    assert _ph(lop['chau2'])['parent_phone'] == '0900555803'
    assert _ph(lop['chau1'])['parent_phone'] in (None, '')


# ── Dòng tiêu đề: nhận cột theo tên ─────────────────────────────────────────

def test_dong_tieu_de_tach_so_cua_em_khoi_so_cua_phu_huynh(lop):
    """Bảng đăng ký thật có CẢ số của em lẫn số của bố mẹ. Không có tiêu đề thì
    hai số ấy trông y hệt nhau; có tiêu đề thì phải đọc theo tên cột."""
    text = ('STT\tHọ và tên\tSĐT học viên\tNgày sinh\tTên phụ huynh\tSĐT phụ huynh\tEmail phụ huynh\n'
            '1\tTrần Thị Bình\t0900555102\t12/05/2008\tMẹ Bình\t0900555802\tme.binh@example.com')
    r = _dan(lop['gv'], lop['id'], text)
    assert r.status_code == 200, r.json()
    assert r.json()['theoTieuDe'] is True
    d = _theo_dong(r)[2]
    assert d['trangThai'] == 'doi', d
    assert _ph(lop['binh']) == {'parent_name': 'Mẹ Bình', 'parent_phone': '0900555802',
                                'parent_email': 'me.binh@example.com'}


def test_tieu_de_khong_co_cot_phu_huynh_thi_bao_ro(lop):
    r = _dan(lop['gv'], lop['id'], 'Họ tên\tEmail\nTrần Thị Bình\tb@example.com', dry_run=True)
    assert r.status_code == 400
    assert 'phụ huynh' in r.json()['error']


# ── Dòng hỏng: trượt CẢ dòng, nói lý do ─────────────────────────────────────

def test_sai_dang_thi_bo_qua_ca_dong(lop):
    r = _dan(lop['gv'], lop['id'],
             'Trần Thị Bình, Mẹ Bình, 090055580\n'
             'an_lhph@example.com, Mẹ An, me@@example', dry_run=True)
    dong = _theo_dong(r)
    assert dong[1]['trangThai'] == 'bo_qua' and '10 số' in dong[1]['lyDo'], dong[1]
    assert dong[2]['trangThai'] == 'bo_qua' and 'Email' in dong[2]['lyDo'], dong[2]


def test_mot_em_hai_dong_thi_giu_dong_dau(lop):
    r = _dan(lop['gv'], lop['id'],
             'an_lhph@example.com, Mẹ An, 0900555801\n'
             'Nguyễn Văn An, Bố An, 0900555811', dry_run=True)
    dong = _theo_dong(r)
    assert dong[1]['trangThai'] == 'doi'
    assert dong[2]['trangThai'] == 'bo_qua' and 'dòng 1' in dong[2]['lyDo'], dong[2]


def test_hai_o_chu_khong_ro_o_nao_la_ten_phu_huynh(lop):
    # "Nguyen Van An" không dấu KHÔNG khớp tên em, nên còn lại hai ô chữ — đoán
    # một trong hai là ghi tên học viên vào ô tên phụ huynh.
    r = _dan(lop['gv'], lop['id'], 'an_lhph@example.com, Nguyen Van An, Mẹ An', dry_run=True)
    d = _theo_dong(r)[1]
    assert d['trangThai'] == 'bo_qua' and 'tên phụ huynh' in d['lyDo'], d


def test_trung_voi_gia_tri_dang_luu_thi_khong_ghi_khong_nhat_ky(lop):
    truoc_nk = q1('SELECT COUNT(*) AS n FROM admin_audit')['n']
    r = _dan(lop['gv'], lop['id'], 'an_lhph@example.com, Mẹ An cũ, 0900555901')
    assert r.status_code == 200, r.json()
    assert _theo_dong(r)[1]['trangThai'] == 'giu'
    assert r.json()['dem']['doi'] == 0
    assert q1('SELECT COUNT(*) AS n FROM admin_audit')['n'] == truoc_nk
