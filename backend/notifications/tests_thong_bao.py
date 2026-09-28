"""THÔNG BÁO TRUNG TÂM (E2, §61b): học vụ gửi mọi đối tượng, giảng viên gửi lớp mình."""
import json
import uuid

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common.db import q, q1, x
from common.permissions import ROLE_ACADEMIC, ROLE_ASSISTANT, ROLE_STUDENT, ROLE_TEACHER
from courses.truy_cap import BA_MON

pytestmark = pytest.mark.django_db


def _nguoi(vai=ROLE_STUDENT, email=True, **cai):
    uid = q1("INSERT INTO users (name, email, password, role, streak) VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             ('TB %s' % uuid.uuid4().hex[:4], ('tbc_%s@example.com' % uuid.uuid4().hex[:10]) if email else None,
              vai))['id']
    if 'email_notif' in cai:
        x('INSERT INTO notification_settings (user_id, email_notif) VALUES (%s, %s)', (uid, cai['email_notif']))
    if cai.get('demo'):
        x('UPDATE users SET is_demo = TRUE WHERE id = %s', (uid,))
    return uid


def _api(uid):
    c = APIClient()
    c.force_authenticate(user=User.objects.get(id=uid))
    return c


def _lop(gv, *ems, course=None):
    cid = q1("INSERT INTO classes (name, teacher_id, status, course_id) VALUES ('Lớp TB', %s, 'active', %s) "
             "RETURNING id", (gv, course))['id']
    for u in ems:
        x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, now())', (cid, u))
    return cid


@pytest.fixture
def canh():
    gv, gv_khac, hv = _nguoi(ROLE_TEACHER), _nguoi(ROLE_TEACHER), _nguoi(ROLE_ACADEMIC)
    tg = _nguoi(ROLE_ASSISTANT)
    bat, tat, khong_mail, mau = _nguoi(), _nguoi(email_notif=0), _nguoi(email=False), _nguoi(demo=True)
    lop = _lop(gv, bat, tat, khong_mail, mau, tg)
    lop_khac = _lop(gv_khac, _nguoi())
    return dict(gv=gv, gv_khac=gv_khac, hv=hv, tg=tg, bat=bat, tat=tat, khong_mail=khong_mail, mau=mau,
                lop=lop, lop_khac=lop_khac)


def _chuong(uid):
    return q("SELECT title, link, announcement_id FROM notifications WHERE user_id = %s AND type = 'thong_bao'",
             (uid,))


def _thu(uid):
    return q("SELECT channel, subject, status, dedup_key FROM outbox WHERE user_id = %s", (uid,))


def test_xem_truoc_dem_theo_kenh_va_neu_ai_thieu_email(canh):
    r = _api(canh['hv']).post('/api/admin/thong-bao/preview',
                              {'audience': {'classIds': [canh['lop']]}, 'sendEmail': True}, format='json')
    assert r.status_code == 200, r.content
    d = r.json()
    assert d['tong'] == 4, 'chỉ học viên đang học (trợ giảng trong lớp không tính)'
    assert d['email'] == 1
    assert d['tatEmail'] == 1 and d['mau'] == 1
    assert [e['id'] for e in d['thieuEmail']] == [canh['khong_mail']]
    assert d['zalo']['sanSang'] is False and d['zalo']['lyDo']
    assert {e['id'] for e in d['danhSach']} == {canh['bat'], canh['tat'], canh['khong_mail'], canh['mau']}
    assert _chuong(canh['bat']) == [], 'xem trước không gửi gì'


def test_hoc_vu_gui_lop_chuong_moi_em_thu_chi_em_bat_email(canh, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=False):
        r = _api(canh['hv']).post('/api/admin/thong-bao', {
            'title': 'Nghỉ lễ 2/9', 'body': 'Trung tâm nghỉ ngày 2/9.',
            'audience': {'classIds': [canh['lop']]}, 'sendEmail': True, 'gui': True}, format='json')
    assert r.status_code == 201, r.content
    aid = r.json()['id']
    a = q1('SELECT status, recipient_count, sent_at FROM announcements WHERE id = %s', (aid,))
    assert a['status'] == 'sent' and a['recipient_count'] == 4 and a['sent_at']
    for u in ('bat', 'tat', 'khong_mail', 'mau'):
        assert _chuong(canh[u]) == [{'title': 'Nghỉ lễ 2/9', 'link': '/thong-bao', 'announcement_id': aid}], u
    assert _chuong(canh['tg']) == [] and _chuong(canh['gv']) == []
    assert _thu(canh['bat']) == [{'channel': 'email', 'subject': 'Nghỉ lễ 2/9', 'status': 'queued',
                                  'dedup_key': 'thong_bao:%d:%d' % (aid, canh['bat'])}]
    assert _thu(canh['tat']) == [] and _thu(canh['mau']) == [], 'tắt email / tài khoản mẫu: chỉ chuông'


def test_ban_nhap_roi_gui_va_khong_gui_lai_duoc(canh):
    c = _api(canh['hv'])
    r = c.post('/api/admin/thong-bao', {'title': 'Nháp', 'body': 'x', 'audience': {'userIds': [canh['bat']]}},
               format='json')
    aid = r.json()['id']
    assert r.json()['status'] == 'draft' and _chuong(canh['bat']) == []
    assert c.post('/api/admin/thong-bao/%d/gui' % aid).status_code == 200
    assert len(_chuong(canh['bat'])) == 1
    assert c.post('/api/admin/thong-bao/%d/gui' % aid).status_code == 409
    assert len(_chuong(canh['bat'])) == 1
    ds = c.get('/api/admin/thong-bao').json()['items']
    assert ds[0]['id'] == aid and ds[0]['status'] == 'sent' and ds[0]['recipientCount'] == 1


def test_huy_ban_nhap(canh):
    c = _api(canh['hv'])
    aid = c.post('/api/admin/thong-bao', {'title': 'N', 'body': 'x', 'audience': {'userIds': [canh['bat']]}},
                 format='json').json()['id']
    assert c.post('/api/admin/thong-bao/%d/huy' % aid).status_code == 200
    assert c.post('/api/admin/thong-bao/%d/gui' % aid).status_code == 409


def test_doi_tuong_theo_mon_va_nhom_chon_tay(canh):
    em_mon = _nguoi()
    _lop(canh['gv'], em_mon, course='hsa_quantitative')
    x("UPDATE classes SET course_id = 'hsa_verbal' WHERE id = %s", (canh['lop'],))   # lớp môn khác
    le = _nguoi()
    r = _api(canh['hv']).post('/api/admin/thong-bao/preview', {'audience': {
        'courseIds': ['hsa_quantitative'], 'userIds': [le], 'groupName': 'Nhóm A'}}, format='json').json()
    ids = {u['id'] for u in r['danhSach']}
    assert {em_mon, le} <= ids and canh['bat'] not in ids
    x('UPDATE classes SET course_id = NULL WHERE id = %s', (canh['lop'],))       # lớp cả ba môn: có tính
    r = _api(canh['hv']).post('/api/admin/thong-bao/preview', {'audience': {'courseIds': ['hsa_quantitative']}},
                              format='json').json()
    assert canh['bat'] in {u['id'] for u in r['danhSach']}


def test_doi_tuong_rong_hoac_thieu_tieu_de_400(canh):
    c = _api(canh['hv'])
    assert c.post('/api/admin/thong-bao', {'title': '', 'body': 'x', 'audience': {'userIds': [canh['bat']]}},
                  format='json').status_code == 400
    assert c.post('/api/admin/thong-bao', {'title': 'T', 'body': 'x', 'audience': {}, 'gui': True},
                  format='json').status_code == 400


def test_zalo_chua_san_sang_thi_400(canh):
    r = _api(canh['hv']).post('/api/admin/thong-bao', {
        'title': 'T', 'body': 'x', 'audience': {'userIds': [canh['bat']]}, 'sendZalo': True, 'gui': True},
        format='json')
    assert r.status_code == 400 and 'Zalo' in json.dumps(r.json(), ensure_ascii=False)


# ── Giảng viên gửi lớp mình ─────────────────────────────────────────────────

def test_giang_vien_gui_lop_minh(canh):
    r = _api(canh['gv']).post('/api/teach/classes/%d/thong-bao' % canh['lop'],
                              {'title': 'Mai kiểm tra', 'body': 'Ôn chương 2.', 'sendEmail': True}, format='json')
    assert r.status_code == 201, r.content
    assert len(_chuong(canh['bat'])) == 1 and len(_thu(canh['bat'])) == 1
    a = q1('SELECT audience, created_by FROM announcements WHERE id = %s', (r.json()['id'],))
    assert json.loads(a['audience'])['classIds'] == [canh['lop']]
    assert a['created_by'] == canh['gv']


def test_giang_vien_gui_lop_nguoi_khac_404(canh):
    r = _api(canh['gv']).post('/api/teach/classes/%d/thong-bao' % canh['lop_khac'],
                              {'title': 'T', 'body': 'x'}, format='json')
    assert r.status_code == 404
    assert q1('SELECT count(*) AS n FROM notifications n JOIN class_members m ON m.user_id = n.user_id '
              "WHERE m.class_id = %s AND n.type = 'thong_bao'", (canh['lop_khac'],))['n'] == 0


def test_giang_vien_xem_truoc_lop_minh(canh):
    r = _api(canh['gv']).post('/api/teach/classes/%d/thong-bao/preview' % canh['lop'], {'sendEmail': True},
                              format='json')
    assert r.status_code == 200 and r.json()['tong'] == 4
    assert _api(canh['gv']).post('/api/teach/classes/%d/thong-bao/preview' % canh['lop_khac'], {},
                                 format='json').status_code == 404


@pytest.mark.parametrize('duong', ['/api/admin/thong-bao', '/api/admin/thong-bao/preview'])
def test_hoc_vien_tro_giang_giang_vien_khong_vao_khu_hoc_vu(canh, duong):
    for vai in ('bat', 'tg', 'gv'):
        assert _api(canh[vai]).post(duong, {'title': 'T', 'body': 'x',
                                            'audience': {'userIds': [canh['bat']]}}, format='json').status_code == 403
    assert _api(canh['bat']).get('/api/admin/thong-bao').status_code == 403


def test_hoc_vien_khong_gui_duoc_cho_lop(canh):
    assert _api(canh['bat']).post('/api/teach/classes/%d/thong-bao' % canh['lop'],
                                  {'title': 'T', 'body': 'x'}, format='json').status_code == 403


# ── Trợ giảng gửi lớp mình (anh Sơn chốt 26/09/2026, quyết định 1) ──────────

def test_tro_giang_gui_duoc_LOP_MINH_nhu_giang_vien(canh):
    """Trợ giảng là người nhắc học viên hằng ngày (bảng yêu cầu dòng 20) — không bắt họ
    nhờ giảng viên bấm hộ. Kèm email cũng được."""
    r = _api(canh['tg']).post('/api/teach/classes/%d/thong-bao' % canh['lop'],
                              {'title': 'Nhớ làm bài', 'body': 'Hạn 21h nay.', 'sendEmail': True},
                              format='json')
    assert r.status_code == 201, r.content
    assert len(_chuong(canh['bat'])) == 1 and len(_thu(canh['bat'])) == 1
    a = q1('SELECT audience, created_by FROM announcements WHERE id = %s', (r.json()['id'],))
    assert json.loads(a['audience'])['classIds'] == [canh['lop']] and a['created_by'] == canh['tg']


def test_tro_giang_gui_lop_khac_404_va_khong_ai_nhan_gi(canh):
    r = _api(canh['tg']).post('/api/teach/classes/%d/thong-bao' % canh['lop_khac'],
                              {'title': 'T', 'body': 'x'}, format='json')
    assert r.status_code == 404, 'không lộ ra lớp ấy có tồn tại'
    assert q1('SELECT count(*) AS n FROM notifications n JOIN class_members m ON m.user_id = n.user_id '
              "WHERE m.class_id = %s AND n.type = 'thong_bao'", (canh['lop_khac'],))['n'] == 0


def test_tro_giang_xem_truoc_lop_minh_va_khong_xem_lop_khac(canh):
    c = _api(canh['tg'])
    assert c.post('/api/teach/classes/%d/thong-bao/preview' % canh['lop'], {}, format='json').json()['tong'] == 4
    assert c.post('/api/teach/classes/%d/thong-bao/preview' % canh['lop_khac'], {},
                  format='json').status_code == 404


def test_tro_giang_roi_lop_thi_khong_gui_duoc_nua(canh):
    x('UPDATE class_members SET left_at = now() WHERE class_id = %s AND user_id = %s',
      (canh['lop'], canh['tg']))
    assert _api(canh['tg']).post('/api/teach/classes/%d/thong-bao' % canh['lop'],
                                 {'title': 'T', 'body': 'x'}, format='json').status_code == 404


def test_tro_giang_van_khong_vao_duoc_khu_hoc_vu(canh):
    """Gửi cả khối / chọn tay người nhận vẫn chỉ học vụ + quản trị."""
    assert _api(canh['tg']).post('/api/admin/thong-bao', {'title': 'T', 'body': 'x',
                                 'audience': {'userIds': [canh['bat']]}}, format='json').status_code == 403


# ── Ô "Gửi kèm email" MẶC ĐỊNH TẮT (quyết định 2) ──────────────────────────

def test_khong_khai_sendEmail_thi_KHONG_co_thu(canh):
    r = _api(canh['hv']).post('/api/admin/thong-bao', {
        'title': 'Chỉ chuông', 'body': 'x', 'audience': {'classIds': [canh['lop']]}, 'gui': True},
        format='json')
    assert r.status_code == 201, r.content
    assert len(_chuong(canh['bat'])) == 1, 'chuông vẫn có'
    assert _thu(canh['bat']) == [], 'không khai sendEmail thì không xếp thư nào'
    assert q1('SELECT send_email FROM announcements WHERE id = %s', (r.json()['id'],))['send_email'] is False


def test_xem_truoc_khong_khai_sendEmail_thi_dem_email_bang_0(canh):
    for duong, than in (('/api/admin/thong-bao/preview', {'audience': {'classIds': [canh['lop']]}}),
                        ('/api/teach/classes/%d/thong-bao/preview' % canh['lop'], {})):
        d = _api(canh['hv']).post(duong, than, format='json').json()
        assert d['tong'] == 4 and d['email'] == 0, duong


# ── DANH MỤC ĐỐI TƯỢNG cho MÀN SOẠN (E2-GD, 26/09/2026) ───────────────────
#
# Màn soạn của học vụ phải hỏi máy chủ "có những lớp nào, những môn nào" chứ
# KHÔNG gõ lại danh mục vào mã giao diện (RULES §7). Một bảng môn chép sang
# React là bảng sẽ trôi khỏi `courses.truy_cap.BA_MON` ngay lần TopHSA mở môn
# thứ tư, và không ai biết bản nào đúng.

def test_get_tra_ve_danh_muc_lop_va_mon_cho_man_soan(canh):
    d = _api(canh['hv']).get('/api/admin/thong-bao').json()
    assert 'chon' in d, 'GET phải kèm danh mục đối tượng cho màn soạn'
    lop = {l['id']: l for l in d['chon']['lop']}
    assert canh['lop'] in lop and canh['lop_khac'] in lop
    assert lop[canh['lop']]['name'], 'ô chọn lớp cần TÊN lớp, không phải id'
    assert lop[canh['lop']]['soEm'] == 4, 'kèm sĩ số để người gửi biết mình sắp báo cho bao nhiêu em'
    mon = d['chon']['mon']
    assert [m['id'] for m in mon] == list(BA_MON), 'môn lấy từ cổng mở môn, không gõ lại ở màn'
    assert all(m['nhan'] for m in mon), 'mỗi môn phải có nhãn tiếng Việt'


def test_danh_muc_lop_khong_gom_lop_da_huy(canh):
    x("UPDATE classes SET status = 'cancelled' WHERE id = %s", (canh['lop_khac'],))
    d = _api(canh['hv']).get('/api/admin/thong-bao').json()
    ids = [l['id'] for l in d['chon']['lop']]
    assert canh['lop'] in ids and canh['lop_khac'] not in ids


def test_giang_vien_khong_doc_duoc_danh_muc_ca_trung_tam(canh):
    """Danh mục nằm sau `IsAdminOrAcademic` — nó liệt kê MỌI lớp của trung tâm."""
    assert _api(canh['gv']).get('/api/admin/thong-bao').status_code == 403
