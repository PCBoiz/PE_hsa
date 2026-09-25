"""Đối tượng nhận bài — kế hoạch v2 V-e (bảng TopHSA dòng 17 "thiết lập đối tượng nhận bài").

`assignments.target_mode` 'lop' | 'nhom' + `assignment_targets` (§62d). MỘT hàm SQL lọc
(`teaching/nhan_bai.giao_cho`) cho mọi chỗ đọc bài. Chạy trên DB thật, giao dịch CUỘN
LẠI (`conftest.py`) — dòng 'nhom' không sống quá phép kiểm. Đi qua URL thật.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  Em NGOÀI nhóm: không thấy bài, không nộp được (404), không nhận chuông, không bị
  đếm "chưa nộp" (sĩ số của bài, thẻ lớp, tờ phụ huynh), không có dòng ở bảng chấm.
  Đổi người nhận: em MỚI được thêm nhận chuông, em cũ không nhận lần hai.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now
from common.db import q, q1, x
from common.permissions import ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db


def _nguoi(ten, vai):
    row = q1("INSERT INTO users (name, email, password, role, streak) "
             "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             (ten, '%s_nb@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=row['id'])


def _api(ai):
    a = APIClient()
    if ai is not None:
        a.force_authenticate(user=ai)
    return a


@pytest.fixture
def canh(db):
    gv = _nguoi('GV NB', ROLE_TEACHER)
    tg = _nguoi('TG NB', ROLE_ASSISTANT)
    an, binh, chau = (_nguoi(t, ROLE_STUDENT) for t in ('An NB', 'Binh NB', 'Chau NB'))
    ngoai = _nguoi('Ngoai NB', ROLE_STUDENT)
    lop = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
             "VALUES ('Lop NB', 'hsa_quantitative', %s, 'active') RETURNING id", (gv.id,))['id']
    for u in (an, binh, chau, tg):
        x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, %s)',
          (lop, u.id, local_now() - timedelta(days=10)))
    return {'gv': gv, 'tg': tg, 'an': an, 'binh': binh, 'chau': chau, 'ngoai': ngoai, 'lop': lop}


def _giao(canh, **than):
    body = {'title': 'Bài nhóm NB', 'max_score': 10, 'status': 'open',
            'due_at': (local_now() + timedelta(days=3)).isoformat(timespec='minutes')}
    body.update(than)
    return _api(canh['gv']).post('/api/teach/classes/%d/assignments' % canh['lop'], body, format='json')


def _chuong(u, bai):
    return q("SELECT id FROM notifications WHERE user_id = %s AND type = 'assignment_new' "
             "AND ref_type = 'assignment' AND ref_id = %s", (u.id, bai))


def _bai_cua(u):
    return {a['id'] for a in _api(u).get('/api/assignments').json()['assignments']}


# ── 1. Em ngoài nhóm không thấy, không nộp, không nhận chuông ────────────────

def test_giao_cho_nhom_chi_em_trong_nhom_thay_nop_va_nhan_chuong(canh):
    r = _giao(canh, target_mode='nhom', target_user_ids=[canh['an'].id])
    assert r.status_code == 201, r.json()
    bai = r.json()['id']
    assert r.json()['notified'] == 1
    assert _chuong(canh['an'], bai) and not _chuong(canh['binh'], bai)
    assert bai in _bai_cua(canh['an']) and bai not in _bai_cua(canh['binh'])
    nop = lambda u: _api(u).post('/api/assignments', {'assignment_id': bai, 'content': 'bài'}, format='json')  # noqa: E731
    assert nop(canh['binh']).status_code == 404
    assert nop(canh['an']).status_code == 200
    # Thẻ lớp: chỉ em trong nhóm có "bài chưa nộp".
    the = lambda u: _api(u).get('/api/lop-cua-toi').json()['lop'][0]['baiTap']['chuaNop']  # noqa: E731
    assert the(canh['binh']) == 0 and the(canh['chau']) == 0


def test_si_so_bang_cham_va_to_phu_huynh_theo_nhom(canh):
    ca_lop = _giao(canh, title='Bài cả lớp NB').json()['id']
    nhom = _giao(canh, target_mode='nhom', target_user_ids=[canh['an'].id, canh['binh'].id]).json()['id']
    d = _api(canh['gv']).get('/api/teach/classes/%d/assignments' % canh['lop']).json()
    theo_id = {a['id']: a for a in d['assignments']}
    assert theo_id[ca_lop]['members'] == 3 and theo_id[nhom]['members'] == 2, theo_id
    assert theo_id[nhom]['targetMode'] == 'nhom'
    assert sorted(theo_id[nhom]['targetUserIds']) == sorted([canh['an'].id, canh['binh'].id])
    assert theo_id[ca_lop]['targetMode'] == 'lop' and theo_id[ca_lop]['targetUserIds'] == []
    # Danh sách học viên cho ô "Chọn học viên" — chỉ học viên đang học (không trợ giảng).
    assert {h['id'] for h in d['hocVien']} == {canh['an'].id, canh['binh'].id, canh['chau'].id}

    bang = _api(canh['tg']).get('/api/teach/assignments/%d/submissions' % nhom).json()
    assert {s['userId'] for s in bang['students']} == {canh['an'].id, canh['binh'].id}
    r = _api(canh['tg']).post('/api/teach/assignments/%d/submissions' % nhom,
                              {'grades': [{'user_id': canh['chau'].id, 'score': 5}]}, format='json')
    assert r.status_code == 400 and r.json()['skipped'] == [canh['chau'].id], r.json()

    to = lambda u: _api(canh['gv']).get(  # noqa: E731
        '/api/teach/classes/%d/students/%d/parent-report' % (canh['lop'], u.id)).json()
    assert nhom not in {a['id'] for a in to(canh['chau'])['assignments']}
    assert nhom in {a['id'] for a in to(canh['an'])['assignments']}
    assert ca_lop in {a['id'] for a in to(canh['chau'])['assignments']}


def test_viec_hom_nay_chi_dem_bai_cua_em_trong_nhom(canh):
    nhom = _giao(canh, target_mode='nhom', target_user_ids=[canh['an'].id]).json()['id']
    nay = local_now()
    # Bài của Châu nằm sẵn (ví dụ nộp trước khi giảng viên thu hẹp nhóm) — không phải việc.
    x("INSERT INTO submissions (assignment_id, user_id, submitted_at, content) VALUES "
      "(%s, %s, %s, 'x'), (%s, %s, %s, 'y')", (nhom, canh['an'].id, nay, nhom, canh['chau'].id, nay))
    d = _api(canh['gv']).get('/api/teach/viec-hom-nay').json()['chuaCham']
    assert [(b['assignmentId'], b['soBai']) for b in d] == [(nhom, 1)], d


# ── 2. Kiểm đầu vào ─────────────────────────────────────────────────────────

@pytest.mark.parametrize('than', [
    {'target_mode': 'nhom', 'target_user_ids': []},
    {'target_mode': 'nhom'},
    {'target_mode': 'ca-lop'},
    {'target_mode': 'nhom', 'target_user_ids': ['x']},
])
def test_dau_vao_sai_thi_400_va_khong_ghi(canh, than):
    truoc = q1('SELECT COUNT(*) AS n FROM assignments WHERE class_id = %s', (canh['lop'],))['n']
    r = _giao(canh, **than)
    assert r.status_code == 400, r.json()
    assert q1('SELECT COUNT(*) AS n FROM assignments WHERE class_id = %s', (canh['lop'],))['n'] == truoc


def test_nguoi_nhan_phai_la_hoc_vien_dang_hoc_lop(canh):
    for ai in (canh['ngoai'], canh['tg']):
        r = _giao(canh, target_mode='nhom', target_user_ids=[canh['an'].id, ai.id])
        assert r.status_code == 400 and str(ai.id) in str(r.json()), r.json()


# ── 3. Đổi người nhận ───────────────────────────────────────────────────────

def test_doi_nguoi_nhan_bao_them_em_moi_mot_lan(canh):
    bai = _giao(canh, target_mode='nhom', target_user_ids=[canh['an'].id]).json()['id']
    sua = lambda **t: _api(canh['gv']).patch('/api/teach/assignments/%d' % bai, t, format='json')  # noqa: E731
    r = sua(target_user_ids=[canh['an'].id, canh['binh'].id])
    assert r.status_code == 200, r.json()
    assert len(_chuong(canh['an'], bai)) == 1 and len(_chuong(canh['binh'], bai)) == 1
    assert not _chuong(canh['chau'], bai)
    assert r.json()['assignment']['targetUserIds'] == sorted([canh['an'].id, canh['binh'].id])
    # Về cả lớp: Châu mới nhận; bảng người nhận được dọn.
    assert sua(target_mode='lop').status_code == 200
    assert len(_chuong(canh['chau'], bai)) == 1 and len(_chuong(canh['an'], bai)) == 1
    assert not q('SELECT 1 FROM assignment_targets WHERE assignment_id = %s', (bai,))
    assert bai in _bai_cua(canh['chau'])


def test_tro_giang_khong_doi_duoc_nguoi_nhan(canh):
    """Trợ giảng không giao bài (01/09) — đổi người nhận là giao lại bài cho người khác,
    nên cũng không. Mở / đóng bài thì trợ giảng vẫn làm được như trước."""
    bai = _giao(canh, target_mode='nhom', target_user_ids=[canh['an'].id]).json()['id']
    r = _api(canh['tg']).patch('/api/teach/assignments/%d' % bai,
                               {'target_mode': 'lop'}, format='json')
    assert r.status_code == 403, r.json()
    assert q1('SELECT target_mode FROM assignments WHERE id = %s', (bai,))['target_mode'] == 'nhom'
    assert _api(canh['tg']).patch('/api/teach/assignments/%d' % bai, {'status': 'closed'},
                                  format='json').status_code == 200
