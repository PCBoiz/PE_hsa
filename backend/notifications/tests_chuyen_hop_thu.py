"""Bốn nơi gửi thư cũ chuyển sang HỘP THƯ ĐI (§61, E2): đổi lịch, quên mật khẩu, báo cáo
phụ huynh (kèm PDF). Chạy trên CSDL thật rồi cuộn lại; thư không gửi thật.

Mỗi phép kiểm ở đây đỏ trên mã trước E2: khi ấy thư đi trên một luồng rời, không để lại
dòng nào — lỗi SMTP là mất thư.
"""
import json
import uuid
from datetime import timedelta

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from common import mail
from common.clock import local_now
from common.db import q, q1, x
from common.permissions import ROLE_STUDENT, ROLE_TEACHER

pytestmark = pytest.mark.django_db


def _nguoi(vai=ROLE_STUDENT, **cot):
    uid = q1("INSERT INTO users (name, email, password, role, streak) VALUES (%s, %s, 'x', %s, 0) RETURNING id",
             (cot.get('name', 'HT'), 'ht_%s@example.com' % uuid.uuid4().hex[:10], vai))['id']
    for k, v in cot.items():
        if k != 'name':
            x('UPDATE users SET %s = %%s WHERE id = %%s' % k, (v, uid))
    return uid


@pytest.fixture
def smtp(monkeypatch):
    """Email đã cấu hình, `mail.gui` giả. `smtp['hong'] = True` → mọi lần gửi lỗi."""
    tt = {'da_gui': [], 'hong': False}
    monkeypatch.setattr(mail, 'da_cau_hinh', lambda: True)
    monkeypatch.setattr(mail, 'che_do_thu', lambda: False)
    monkeypatch.setattr(mail, 'thieu_gi', lambda: [])

    def gia(den, tieu_de, chu, html=None, dinh_kem=()):
        if tt['hong']:
            return False, None, 'SMTP sập'
        tt['da_gui'].append({'den': den, 'tieuDe': tieu_de, 'chu': chu, 'html': html,
                             'dinhKem': list(dinh_kem)})
        return True, '<gia-%d>' % len(tt['da_gui']), None
    monkeypatch.setattr(mail, 'gui', gia)
    return tt


# ── Đổi lịch ────────────────────────────────────────────────────────────────

@pytest.fixture
def buoi():
    gv = _nguoi(ROLE_TEACHER)
    lop = q1("INSERT INTO classes (name, teacher_id, status) VALUES ('Lớp HT', %s, 'active') "
             "RETURNING id, name, NULL::text AS mode, NULL::text AS room", (gv,))
    em = _nguoi()
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, now())', (lop['id'], em))
    s = q1('''INSERT INTO class_sessions (class_id, starts_at, duration_minutes, status)
              VALUES (%s, %s, 90, 'planned')
              RETURNING id, starts_at, duration_minutes, status, NULL::text AS mode, NULL::text AS room,
                        meeting_url''', (lop['id'], local_now() + timedelta(days=2)))
    return {'lop': lop, 'em': em, 'truoc': s}


def test_doi_lich_ghi_thu_vao_hop_thu_di(buoi, django_capture_on_commit_callbacks):
    from teaching.bao_doi_lich import bao_doi_lich
    sau = dict(buoi['truoc'], starts_at=buoi['truoc']['starts_at'] + timedelta(hours=3))
    with django_capture_on_commit_callbacks(execute=False):
        assert bao_doi_lich(buoi['truoc'], sau, buoi['lop']) == 1
    d = q('SELECT channel, status, subject, body, source_type, source_id FROM outbox WHERE user_id = %s',
          (buoi['em'],))
    assert len(d) == 1 and d[0]['status'] == 'queued' and d[0]['channel'] == 'email'
    assert d[0]['subject'].startswith('Lớp Lớp HT dời buổi')
    assert 'Lớp của tôi' in d[0]['body']
    assert (d[0]['source_type'], d[0]['source_id']) == ('class_session', buoi['truoc']['id'])


def test_doi_lich_smtp_sap_thi_thu_nam_lai_de_thu_lai(buoi, smtp, monkeypatch):
    from teaching import bao_doi_lich as bdl
    monkeypatch.setattr(bdl, 'GUI_NGAY', True)
    smtp['hong'] = True
    bdl.bao_doi_lich(buoi['truoc'], None, buoi['lop'])
    d = q1('SELECT status, attempts, error FROM outbox WHERE user_id = %s', (buoi['em'],))
    assert (d['status'], d['attempts'], d['error']) == ('failed', 1, 'SMTP sập')


# ── Quên mật khẩu ───────────────────────────────────────────────────────────

def _xin(email_):
    return APIClient().post('/auth/quen-mat-khau', {'email': email_}, format='json')


def test_quen_mat_khau_thu_qua_hop_thu_di_va_xoa_chia_sau_khi_gui(smtp, monkeypatch, settings):
    from accounts import quen_mat_khau
    monkeypatch.setattr(quen_mat_khau, 'GUI_NGAY', True)
    settings.FRONTEND_URL = 'https://vi-du.tophsa.test'
    em = _nguoi()
    dia_chi = q1('SELECT email FROM users WHERE id = %s', (em,))['email']
    assert _xin(dia_chi).status_code == 200
    assert len(smtp['da_gui']) == 1 and '#chia=' in smtp['da_gui'][0]['chu']
    chia = smtp['da_gui'][0]['chu'].split('#chia=')[1].split()[0]
    d = q1('SELECT status, body, params, subject FROM outbox WHERE user_id = %s', (em,))
    assert d['status'] == 'sent' and d['subject'] == 'Đặt lại mật khẩu TopHSA'
    assert d['body'] == '' and 'html' not in json.loads(d['params']), 'chìa thô còn nằm trong CSDL sau khi gửi'
    assert not q1("SELECT 1 AS c FROM outbox WHERE body LIKE %s OR params::text LIKE %s",
                  ('%' + chia + '%', '%' + chia + '%'))


def test_quen_mat_khau_han_30_phut_di_theo_thu(smtp, monkeypatch):
    """Thư chưa đi được trong 30 phút thì bỏ — đường dẫn trong đó đã chết."""
    from django.utils import timezone

    from accounts import quen_mat_khau
    monkeypatch.setattr(quen_mat_khau, 'GUI_NGAY', True)
    smtp['hong'] = True
    em = _nguoi()
    _xin(q1('SELECT email FROM users WHERE id = %s', (em,))['email'])
    d = q1('SELECT id, status, params FROM outbox WHERE user_id = %s', (em,))
    assert d['status'] == 'failed'
    han = json.loads(d['params'])['het_han']
    tre = (timezone.datetime.fromisoformat(han) - timezone.now()).total_seconds() / 60
    assert 29 <= tre <= 30.5, tre
    x("UPDATE outbox SET params = jsonb_set(params, '{het_han}', to_jsonb((now() AT TIME ZONE 'UTC' - interval '1 minute')::text || '+00:00')), "
      "next_try_at = now() WHERE id = %s", (d['id'],))
    from notifications.hop_thu import gui_ngay
    gui_ngay([d['id']])
    d = q1('SELECT status, body FROM outbox WHERE id = %s', (d['id'],))
    assert d['status'] == 'dropped' and d['body'] == ''


# ── Báo cáo phụ huynh ───────────────────────────────────────────────────────

@pytest.fixture
def lop_ph(monkeypatch):
    from common import zalo
    monkeypatch.setattr(zalo, 'da_cau_hinh', lambda: False)
    monkeypatch.setattr(zalo, 'che_do_thu', lambda: False)
    gv = _nguoi(ROLE_TEACHER)
    cid = q1("INSERT INTO classes (name, teacher_id, status, starts_on) VALUES ('Lớp PH', %s, 'active', %s) "
             "RETURNING id", (gv, local_now().date() - timedelta(days=20)))['id']
    em = _nguoi(name='Em PH', parent_email='me.ph@example.com')
    x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s, %s, now())', (cid, em))
    c = APIClient()
    c.force_authenticate(user=User.objects.get(id=gv))
    return {'id': cid, 'em': em, 'api': c}


def test_bao_cao_phu_huynh_qua_hop_thu_di_co_PDF(lop_ph, smtp):
    r = lop_ph['api'].post('/api/teach/classes/%d/parent-report/send-all' % lop_ph['id'], {}, format='json')
    assert r.status_code == 200, r.content
    assert r.json()['ketQua'][0]['trangThai'] == 'da_gui'
    d = q1('SELECT status, channel, to_addr, source_type, params FROM outbox WHERE user_id = %s', (lop_ph['em'],))
    assert (d['status'], d['channel'], d['to_addr']) == ('sent', 'email', 'me.ph@example.com')
    assert d['source_type'] == 'parent_report_sends' and json.loads(d['params'])['loai'] == 'bao_cao_phu_huynh'
    assert smtp['da_gui'][0]['dinhKem'][0][2][:5] == b'%PDF-'


def test_bao_cao_phu_huynh_loi_thi_thu_lai_va_so_gui_cap_nhat(lop_ph, smtp):
    """Lượt đầu SMTP sập: sổ gửi 'loi', thư nằm lại. Lượt thử lại (PDF DỰNG LẠI từ tham số)
    gửi được → sổ gửi thành 'da_gui' — không ai phải bấm lại."""
    smtp['hong'] = True
    r = lop_ph['api'].post('/api/teach/classes/%d/parent-report/send-all' % lop_ph['id'], {}, format='json')
    assert r.json()['ketQua'][0]['trangThai'] == 'loi'
    so = q1('SELECT s.status FROM parent_report_sends s JOIN parent_report_links l ON l.id = s.link_id '
            'WHERE l.user_id = %s', (lop_ph['em'],))
    assert so['status'] == 'loi'
    d = q1('SELECT id, status FROM outbox WHERE user_id = %s', (lop_ph['em'],))
    assert d['status'] == 'failed'
    smtp['hong'] = False
    x('UPDATE outbox SET next_try_at = now() WHERE id = %s', (d['id'],))
    from notifications.hop_thu import gui_ngay
    gui_ngay([d['id']])
    assert smtp['da_gui'][0]['dinhKem'][0][2][:5] == b'%PDF-'
    so = q1('SELECT s.status, s.sent_at, s.error FROM parent_report_sends s JOIN parent_report_links l '
            'ON l.id = s.link_id WHERE l.user_id = %s', (lop_ph['em'],))
    assert so['status'] == 'da_gui' and so['sent_at'] is not None and so['error'] is None
