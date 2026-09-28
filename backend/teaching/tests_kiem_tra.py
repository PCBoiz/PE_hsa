"""Bài kiểm tra ngoại tuyến — "điểm thi thử" do giảng viên nhập (kế hoạch v2 V-h).

Anh Sơn chốt 25/09: thi thử online vẫn bỏ; "điểm thi thử / điểm kiểm tra" = bài kiểm tra
làm trên lớp, giảng viên nhập điểm tay — một LOẠI bài giao (`assignments.kind =
'kiem_tra'` + `held_on`, `submissions.absent`, §62f). Bảng TopHSA dòng 4 ("điểm kiểm tra,
điểm thi thử" trên dòng thời gian của em), dòng 17 (nhập điểm). KHÔNG đụng §48.

Chạy trên DB thật, giao dịch CUỘN LẠI (`conftest.py`) — dòng 'kiem_tra' không sống quá
phép kiểm. Đi qua URL thật.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.clock import local_now, local_today
from common.db import q, q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db
NGAY = local_today() - timedelta(days=2)


def _nguoi(ten, vai):
    row = q1("INSERT INTO users (name, email, password, role, streak) "
             "VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             (ten, '%s_kt@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=row['id'])


def _api(ai):
    a = APIClient()
    if ai is not None:
        a.force_authenticate(user=ai)
    return a


@pytest.fixture
def canh(db):
    gv = _nguoi('GV KT', ROLE_TEACHER)
    tg = _nguoi('TG KT', ROLE_ASSISTANT)
    hoc_vu = _nguoi('HocVu KT', ROLE_ACADEMIC)
    an, binh, chau = (_nguoi(t, ROLE_STUDENT) for t in ('An KT', 'Binh KT', 'Chau KT'))
    lop = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
             "VALUES ('Lop KT', 'hsa_quantitative', %s, 'active') RETURNING id", (gv.id,))['id']
    for u in (an, binh, chau, tg):
        x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, %s)',
          (lop, u.id, local_now() - timedelta(days=20)))
    return {'gv': gv, 'tg': tg, 'hoc_vu': hoc_vu, 'an': an, 'binh': binh, 'chau': chau, 'lop': lop}


def _tao(canh, **than):
    body = {'title': 'Kiểm tra giữa kỳ', 'kind': 'kiem_tra', 'held_on': NGAY.isoformat(),
            'max_score': 10}
    body.update(than)
    return _api(canh['gv']).post('/api/teach/classes/%d/assignments' % canh['lop'], body, format='json')


def _cham(ai, bai, grades):
    return _api(ai).post('/api/teach/assignments/%d/submissions' % bai, {'grades': grades}, format='json')


# ── 1. Tạo + học viên không nộp được ────────────────────────────────────────

def test_tao_bai_kiem_tra_hoc_vien_thay_nhung_khong_nop_duoc(canh):
    r = _tao(canh)
    assert r.status_code == 201, r.json()
    bai = r.json()['id']
    a = q1('SELECT kind, held_on FROM assignments WHERE id = %s', (bai,))
    assert (a['kind'], a['held_on']) == ('kiem_tra', NGAY)
    ds = {b['id']: b for b in _api(canh['an']).get('/api/assignments').json()['assignments']}
    assert ds[bai]['kind'] == 'kiem_tra' and ds[bai]['heldOn'] == NGAY.isoformat()
    r = _api(canh['an']).post('/api/assignments', {'assignment_id': bai, 'content': 'bài'}, format='json')
    assert r.status_code == 409 and 'kiểm tra' in r.json()['error'], r.json()
    assert not q('SELECT 1 FROM submissions WHERE assignment_id = %s', (bai,))
    # Bài kiểm tra KHÔNG phải "bài chưa nộp" trên thẻ lớp.
    assert _api(canh['an']).get('/api/lop-cua-toi').json()['lop'][0]['baiTap']['chuaNop'] == 0


@pytest.mark.parametrize('than', [{'kind': 'thi_thu'}, {'held_on': '20/09/2026'}])
def test_dau_vao_sai_400(canh, than):
    r = _tao(canh, **than)
    assert r.status_code == 400, r.json()


# ── 2. Nhập điểm cả lớp, kể cả em vắng ──────────────────────────────────────

def test_nhap_diem_ca_lop_ke_ca_vang(canh):
    bai = _tao(canh).json()['id']
    r = _cham(canh['tg'], bai, [{'user_id': canh['an'].id, 'score': 8, 'feedback': 'Tốt'},
                                {'user_id': canh['binh'].id, 'absent': True}])
    assert r.status_code == 200, r.json()
    s = {d['user_id']: d for d in q('SELECT user_id, score, absent, graded_at FROM submissions '
                                    'WHERE assignment_id = %s', (bai,))}
    assert float(s[canh['an'].id]['score']) == 8 and s[canh['an'].id]['absent'] is False
    assert s[canh['binh'].id]['score'] is None and s[canh['binh'].id]['absent'] is True
    assert s[canh['binh'].id]['graded_at'] is not None
    bang = {x['userId']: x for x in _api(canh['gv']).get(
        '/api/teach/assignments/%d/submissions' % bai).json()['students']}
    assert bang[canh['binh'].id]['absent'] is True and bang[canh['an'].id]['absent'] is False
    assert bang[canh['chau'].id]['gradedAt'] is None
    # Chuông "đã chấm": em có điểm nhận, em vắng không.
    chuong = lambda u: q("SELECT title FROM notifications WHERE user_id = %s "  # noqa: E731
                         "AND type = 'assignment_graded' AND ref_id = %s", (u.id, bai))
    assert chuong(canh['an']) and 'kiểm tra' in chuong(canh['an'])[0]['title']
    assert not chuong(canh['binh'])
    # Vắng mà vẫn gửi điểm, hoặc vắng ở bài tập thường → 400.
    assert _cham(canh['gv'], bai, [{'user_id': canh['chau'].id, 'absent': True, 'score': 5}]).status_code == 400
    thuong = _api(canh['gv']).post('/api/teach/classes/%d/assignments' % canh['lop'],
                                   {'title': 'Bài thường'}, format='json').json()['id']
    assert _cham(canh['gv'], thuong, [{'user_id': canh['an'].id, 'absent': True}]).status_code == 400


# ── 3. Điểm đi tới đâu ──────────────────────────────────────────────────────

def test_diem_len_to_phu_huynh_dong_thoi_gian_va_so_diem(canh):
    bai = _tao(canh).json()['id']
    _cham(canh['gv'], bai, [{'user_id': canh['an'].id, 'score': 7.5},
                            {'user_id': canh['binh'].id, 'absent': True}])
    to = lambda u: _api(canh['gv']).get(  # noqa: E731
        '/api/teach/classes/%d/students/%d/parent-report' % (canh['lop'], u.id)).json()
    t_an = to(canh['an'])
    assert [(k['id'], k['score'], k['absent'], k['heldOn']) for k in t_an['kiemTra']] == [
        (bai, 7.5, False, NGAY.isoformat())], t_an['kiemTra']
    assert bai not in {a['id'] for a in t_an['assignments']}, 'bài kiểm tra lẫn vào khối bài tập'
    assert to(canh['binh'])['kiemTra'][0]['absent'] is True

    tl = lambda u: _api(canh['hoc_vu']).get('/api/admin/users/%d/timeline' % u.id).json()['events']  # noqa: E731
    e_an = next(e for e in tl(canh['an']) if e['loai'] == 'kiem-tra')
    assert e_an['tieuDe'] == 'Bài kiểm tra: Kiểm tra giữa kỳ' and e_an['luc'] == NGAY.isoformat()
    assert e_an['chiTiet'] == '7.5/10 điểm · Lớp Lop KT' and e_an['caNgay'] is True, e_an
    e_binh = next(e for e in tl(canh['binh']) if e['loai'] == 'kiem-tra')
    assert e_binh['chiTiet'] == 'Vắng · Lớp Lop KT', e_binh

    so = _api(canh['an']).get('/api/hsa/gradebook').json()
    dong = [d for d in so['rows'] if d['kind'] == 'kiem_tra']
    assert [(d['label'], d['kindLabel'], d['score'], d['max']) for d in dong] == [
        ('Kiểm tra giữa kỳ', 'Bài kiểm tra', 7.5, 10.0)], so['rows']
    assert any(k['kind'] == 'kiem_tra' for k in so['byKind'])


def test_doi_diem_thanh_vang_thi_so_diem_bo_dong_ay(canh):
    bai = _tao(canh).json()['id']
    _cham(canh['gv'], bai, [{'user_id': canh['an'].id, 'score': 9}])
    assert [d for d in _api(canh['an']).get('/api/hsa/gradebook').json()['rows'] if d['kind'] == 'kiem_tra']
    assert _cham(canh['gv'], bai, [{'user_id': canh['an'].id, 'absent': True}]).status_code == 200
    assert not [d for d in _api(canh['an']).get('/api/hsa/gradebook').json()['rows']
                if d['kind'] == 'kiem_tra'], 'em vắng mà sổ điểm vẫn giữ điểm cũ'
