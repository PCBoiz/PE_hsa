"""Lịch sử sửa điểm danh — kế hoạch v2 V-d (bảng TopHSA dòng 9, 14, 28).

Chạy trên DB thật, giao dịch CUỘN LẠI (`conftest.py`); lời gọi đi qua URL thật.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Mỗi lần lưu điểm danh ghi MỘT dòng lịch sử cho mỗi em THẬT SỰ đổi (kể cả lần tick
     đầu, `tu` NULL); lưu lại y hệt ghi 0 dòng. Mốc `changed_at` = mốc dòng nhật ký cùng
     lượt (để phần điền ngược nhận ra dòng đã có).
  2. `GET …/attendance/history`: nhân sự của lớp (kể cả trợ giảng); lớp khác 404; học
     viên 403. Mới nhất trước.
  3. Điền ngược §62 từ `admin_audit`: chạy lần hai ghi 0 dòng.
  4. Học viên xem điểm danh TỪNG buổi của mình ở "Lớp của tôi", cùng bộ lọc với chuyên
     cần (buổi huỷ / chưa tới không vào; buổi chưa điểm danh nói rõ).
"""
import json
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
             (ten, '%s_lsdd@example.com' % ten.replace(' ', '_').lower(), vai))
    return User.objects.get(id=row['id'])


def _api(ai):
    a = APIClient()
    if ai is not None:
        a.force_authenticate(user=ai)
    return a


def _buoi(lop, lech_gio, status='planned', topic=None):
    return q1('INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status, topic) '
              'VALUES (%s, %s, 90, %s, %s) RETURNING id',
              (lop, local_now() + timedelta(hours=lech_gio), status, topic))['id']


def _diem_danh(ai, buoi, **tt):
    return _api(ai).post('/api/teach/sessions/%d/attendance' % buoi,
                         {'marks': [{'user_id': u.id, 'status': s} for u, s in tt.values()]},
                         format='json')


def _lich_su(buoi):
    return q('SELECT user_id, tu, den, changed_by, changed_at, nguon FROM attendance_history '
             'WHERE session_id = %s ORDER BY id', (buoi,))


@pytest.fixture
def canh(db):
    gv = _nguoi('GV LSDD', ROLE_TEACHER)
    gv_khac = _nguoi('GV Khac LSDD', ROLE_TEACHER)
    tg = _nguoi('TG LSDD', ROLE_ASSISTANT)
    an = _nguoi('An LSDD', ROLE_STUDENT)
    binh = _nguoi('Binh LSDD', ROLE_STUDENT)
    lop = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
             "VALUES ('Lop LSDD', 'hsa_quantitative', %s, 'active') RETURNING id", (gv.id,))['id']
    for u in (an, binh, tg):
        x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, %s)',
          (lop, u.id, local_now() - timedelta(days=20)))
    return {'gv': gv, 'gv_khac': gv_khac, 'tg': tg, 'an': an, 'binh': binh, 'lop': lop,
            'buoi': _buoi(lop, -30, topic='Tỉ lệ')}


# ── 1. Ghi lịch sử ──────────────────────────────────────────────────────────

def test_luu_ghi_dong_doi_luu_y_het_ghi_0_dong(canh):
    gv, b, an, binh = canh['gv'], canh['buoi'], canh['an'], canh['binh']
    r = _diem_danh(gv, b, a=(an, 'present'), b=(binh, 'absent'))
    assert r.status_code == 200, r.json()
    ls = _lich_su(b)
    assert [(h['user_id'], h['tu'], h['den'], h['nguon']) for h in ls] == [
        (an.id, None, 'present', 'diem_danh'), (binh.id, None, 'absent', 'diem_danh')], ls
    assert {h['changed_by'] for h in ls} == {gv.id}

    # Lưu lại y hệt: 0 dòng mới.
    assert _diem_danh(gv, b, a=(an, 'present'), b=(binh, 'absent')).status_code == 200
    assert len(_lich_su(b)) == 2

    # Sửa MỘT em: đúng một dòng, kèm giá trị cũ; trợ giảng sửa thì ghi trợ giảng.
    assert _diem_danh(canh['tg'], b, a=(an, 'late'), b=(binh, 'absent')).status_code == 200
    ls = _lich_su(b)
    assert len(ls) == 3 and (ls[2]['user_id'], ls[2]['tu'], ls[2]['den'], ls[2]['changed_by']) == (
        an.id, 'present', 'late', canh['tg'].id), ls
    # Mốc lịch sử = mốc dòng nhật ký cùng lượt — phần điền ngược dựa vào đó.
    nk = q1("SELECT occurred_at FROM admin_audit WHERE action = 'attendance.mark' "
            "AND actor_id = %s AND target_id = %s ORDER BY id DESC LIMIT 1", (canh['tg'].id, str(b)))
    assert nk and nk['occurred_at'] == ls[2]['changed_at'], (nk, ls[2])


def test_xem_lich_su_ai_duoc_xem(canh):
    b = canh['buoi']
    _diem_danh(canh['gv'], b, a=(canh['an'], 'absent'))
    _diem_danh(canh['tg'], b, a=(canh['an'], 'excused'))
    url = '/api/teach/sessions/%d/attendance/history' % b
    r = _api(canh['gv']).get(url)
    assert r.status_code == 200, r.json()
    ds = r.json()['lichSu']
    # Mới nhất trước, kèm tên em và người sửa.
    assert [(e['userId'], e['tu'], e['den'], e['boi']) for e in ds] == [
        (canh['an'].id, 'absent', 'excused', 'TG LSDD'), (canh['an'].id, None, 'absent', 'GV LSDD')], ds
    assert ds[0]['name'] == 'An LSDD' and ds[0]['luc']
    assert _api(canh['tg']).get(url).status_code == 200
    assert _api(canh['gv_khac']).get(url).status_code == 404
    assert _api(canh['an']).get(url).status_code == 403
    assert _api(None).get(url).status_code == 401


# ── 2. Điền ngược từ nhật ký ────────────────────────────────────────────────

def _cau_dien_nguoc():
    """Câu điền ngược lấy NGUYÊN VĂN từ §62 qua bộ chia mục của `bootstrap_schema` —
    ranh giới mục do tiêu đề mục kế tiếp quyết định, không do chuỗi tìm tay."""
    from common.luoc_do_sql import doc_tat_ca
    muc = next(m for m in doc_tat_ca() if m.tep == 'legacy_schema.sql' and m.ma == '§62')
    cau = [c for c in muc.cau if c.lstrip().startswith('INSERT INTO attendance_history')]
    assert len(cau) == 1, 'không tìm thấy đúng một câu điền ngược trong §62'
    return cau[0]


def test_dien_nguoc_tu_nhat_ky_chay_lai_ghi_0_dong(canh):
    b, an, binh = canh['buoi'], canh['an'], canh['binh']
    luc = local_now() - timedelta(days=2)
    # Dòng nhật ký như mã CŨ ghi (chưa có bảng lịch sử): hai em đổi, một em lạ đã xoá.
    x("INSERT INTO admin_audit (actor_id, actor_name, action, target_type, target_id, "
      "summary, detail, occurred_at) VALUES (%s, 'GV LSDD', 'attendance.mark', 'class_session', "
      "%s, 'x', %s::jsonb, %s)",
      (canh['gv'].id, str(b), json.dumps({'changed': [
          {'userId': an.id, 'from': None, 'to': 'present'},
          {'userId': binh.id, 'from': 'present', 'to': 'absent'},
          {'userId': 999999999, 'from': None, 'to': 'present'},
          {'userId': an.id, 'from': 'present', 'to': 'khong-hop-le'}]}), luc))
    cau = _cau_dien_nguoc()
    x(cau)
    ls = _lich_su(b)
    assert [(h['user_id'], h['tu'], h['den'], h['nguon'], h['changed_by']) for h in ls] == [
        (an.id, None, 'present', 'nhat_ky', canh['gv'].id),
        (binh.id, 'present', 'absent', 'nhat_ky', canh['gv'].id)], ls
    assert all(h['changed_at'] == luc for h in ls)
    x(cau)
    assert len(_lich_su(b)) == 2, 'điền ngược lần hai đẻ bản sao'
    # Lượt lưu THẬT sau đó (ghi cả lịch sử lẫn nhật ký cùng mốc) rồi chạy lại điền ngược:
    # vẫn không đẻ bản sao của dòng vừa ghi.
    _diem_danh(canh['gv'], b, a=(an, 'late'))
    x(cau)
    assert [h['nguon'] for h in _lich_su(b)] == ['nhat_ky', 'nhat_ky', 'diem_danh']


# ── 3. Học viên xem điểm danh từng buổi ─────────────────────────────────────

def test_hoc_vien_xem_diem_danh_tung_buoi(canh):
    lop, an = canh['lop'], canh['an']
    cu = _buoi(lop, -72, topic='Buổi cũ')
    chua = _buoi(lop, -24, topic='Chưa điểm danh')
    _buoi(lop, -48, status='cancelled', topic='Đã huỷ')
    _buoi(lop, 48, topic='Tương lai')
    _diem_danh(canh['gv'], cu, a=(an, 'late'))
    _diem_danh(canh['gv'], canh['buoi'], a=(an, 'absent'))
    d = _api(an).get('/api/lop-cua-toi').json()['lop'][0]
    ds = d['diemDanh']
    # Mới nhất trước; buổi huỷ và buổi chưa tới không có; buổi chưa ai điểm danh nói rõ.
    # `chua` bắt đầu −24 giờ, buổi của fixture −30 giờ, `cu` −72 giờ.
    assert [(e['sessionId'], e['trangThai']) for e in ds] == [
        (chua, None), (canh['buoi'], 'absent'), (cu, 'late')], ds
    assert ds[1]['topic'] == 'Tỉ lệ' and ds[0]['daDiemDanh'] is False and ds[1]['daDiemDanh'] is True
    # Khớp chuyên cần: cùng bộ lọc.
    assert d['chuyenCan']['sessionsCounted'] == sum(1 for e in ds if e['daDiemDanh'])
    # Không lộ trạng thái của em khác.
    _diem_danh(canh['gv'], chua, b=(canh['binh'], 'present'))
    ds2 = _api(an).get('/api/lop-cua-toi').json()['lop'][0]['diemDanh']
    assert next(e for e in ds2 if e['sessionId'] == chua)['trangThai'] is None
