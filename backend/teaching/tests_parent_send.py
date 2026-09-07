"""Gửi báo cáo cho phụ huynh CẢ LỚP.

Chạy trên DB thật, trong giao dịch được CUỘN LẠI (xem `conftest.py`).
KHÔNG lời gọi mạng thật nào: `zalo.gui_zns` bị thay bằng bản giả — gọi Zalo
thật trong bộ kiểm là gửi tin thật, mất phí thật, tới số thật.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. GET (soạn sẵn) KHÔNG được ghi gì. Một "bản xem trước" mà cấp chìa là đã
     hành động trước khi người dùng gật.
  2. Chưa cấu hình OA thì KHÔNG tạo dòng chờ. Hàng chờ không có gì xử lý là
     một danh sách việc giả, và người nhìn nó tưởng tin đang trên đường đi.
  3. Em thiếu số phụ huynh phải được NÊU TÊN, không im lặng bỏ qua.
  4. Em ĐÃ RỜI LỚP không nhận báo cáo tiến độ.
  5. Lượt gửi HỎNG vẫn phải vào sổ — nếu không thì lần sau không ai biết em nào
     đã thử và trượt, còn phụ huynh chỉ biết là chưa nhận được gì.
  6. Gửi hai lần KHÔNG đẻ ra hai chìa cho cùng một kỳ.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common import mail, zalo
from common.clock import local_now
from common.db import q1
from common.permissions import ROLE_STUDENT, ROLE_TEACHER
from teaching.parent_send import ParentReportSendAllView

f = APIRequestFactory()


def _goi(method, body=None, ai=None, **kw):
    req = (getattr(f, method)('/x', body, format='json') if body is not None
           else getattr(f, method)('/x'))
    if ai is not None:
        force_authenticate(req, user=ai)
    return ParentReportSendAllView.as_view()(req, **kw)


def _nguoi(ten, vai, **cot):
    khoa = ', '.join(cot)
    cho = ', '.join(['%s'] * len(cot))
    row = q1(
        f'INSERT INTO users (name, email, password, role, streak{", " + khoa if khoa else ""}) '
        f'VALUES (%s, %s, %s, %s, 0{", " + cho if cho else ""}) RETURNING id',
        (ten, '%s_tmp@example.com' % ten.replace(' ', '_'), 'x', vai, *cot.values()))
    return User.objects.get(id=row['id'])


@pytest.fixture
def lop(db):
    """Một lớp: em CÓ số phụ huynh, em KHÔNG có, và em đã rời lớp."""
    gv = _nguoi('GV Gui', ROLE_TEACHER)
    co = _nguoi('HV Co So', ROLE_STUDENT, parent_name='Me A', parent_phone='0912345678')
    khong = _nguoi('HV Khong So', ROLE_STUDENT)
    da_roi = _nguoi('HV Da Roi', ROLE_STUDENT, parent_phone='0987654321')
    c = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
           "VALUES ('Lop gui','hsa_quantitative',%s,'active') RETURNING id", (gv.id,))
    nay = local_now()
    for u in (co, khong):
        q1('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s) '
           'RETURNING id', (c['id'], u.id, nay - timedelta(days=20)))
    q1('INSERT INTO class_members (class_id, user_id, joined_at, left_at, leave_reason) '
       'VALUES (%s,%s,%s,%s,%s) RETURNING id',
       (c['id'], da_roi.id, nay - timedelta(days=30), nay - timedelta(days=5), 'transferred'))
    return {'id': c['id'], 'gv': gv, 'co': co, 'khong': khong, 'da_roi': da_roi}


@pytest.fixture
def chua_oa(monkeypatch):
    """Trạng thái THẬT hôm nay: trung tâm chưa có Zalo OA đã xác thực."""
    monkeypatch.setattr(zalo, 'da_cau_hinh', lambda: False)
    monkeypatch.setattr(zalo, 'thieu_gi', lambda: ['ZALO_OA_ACCESS_TOKEN'])


@pytest.fixture
def oa_gia(monkeypatch):
    """OA đã cấu hình, và `gui_zns` là bản GIẢ — không gọi mạng."""
    da_goi = []
    monkeypatch.setattr(zalo, 'da_cau_hinh', lambda: True)
    monkeypatch.setattr(zalo, 'thieu_gi', lambda: [])

    def gia(phone, tham_so):
        da_goi.append((phone, tham_so))
        return True, 'msg-gia-%d' % len(da_goi), None
    monkeypatch.setattr(zalo, 'gui_zns', gia)
    return da_goi


@pytest.fixture
def mail_gia(monkeypatch):
    """Email ĐÃ cấu hình, và `mail.gui` là bản GIẢ — không mở kết nối SMTP nào."""
    da_goi = []
    monkeypatch.setattr(mail, 'da_cau_hinh', lambda: True)
    monkeypatch.setattr(mail, 'che_do_thu', lambda: False)
    monkeypatch.setattr(mail, 'thieu_gi', lambda: [])

    def gia(den, tieu_de, chu, html=None, dinh_kem=()):
        da_goi.append({'den': den, 'tieuDe': tieu_de, 'chu': chu, 'html': html,
                       'dinhKem': list(dinh_kem)})
        return True, '<gia-%d@tophsa.vn>' % len(da_goi), None
    monkeypatch.setattr(mail, 'gui', gia)
    return da_goi


@pytest.fixture
def em_co_email(lop):
    """Cho em `HV Khong So` một email phụ huynh — em ấy KHÔNG có số điện thoại,
    nên nó chứng minh email đi được ở nơi ZNS bó tay."""
    from common.db import x as _x
    _x('UPDATE users SET parent_email=%s WHERE id=%s',
       ('me.a@example.com', lop['khong'].id))
    return lop


# ── GET: bản soạn sẵn ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_get_noi_truoc_ai_gui_duoc_ai_khong(lop, chua_oa):
    kq = _goi('get', ai=lop['gv'], class_id=lop['id'])
    assert kq.status_code == 200, kq.data
    theo_ten = {e['name']: e for e in kq.data['students']}
    # `coLienLac`, KHÔNG phải `guiDuoc`. Từ 07/09/2026 hai cờ này trả lời hai
    # câu khác nhau: `coLienLac` hỏi em có số/email phụ huynh chưa (giảng viên
    # sửa), `guiDuoc` hỏi gửi được ngay bây giờ không (người quản trị sửa, vì
    # nó còn phụ thuộc đã cấu hình kênh nào). Phép kiểm này canh câu thứ nhất
    # — đúng thứ nó canh từ đầu, chỉ là ngày ấy chỉ có một cờ.
    assert theo_ten['HV Co So']['coLienLac'] is True
    assert theo_ten['HV Khong So']['coLienLac'] is False
    # Chưa cấu hình kênh nào thì KHÔNG ai gửi được, kể cả em có số.
    assert theo_ten['HV Co So']['guiDuoc'] is False
    assert theo_ten['HV Co So']['kenh'] is None
    # Em đã rời lớp KHÔNG có trong danh sách: gửi báo cáo tiến độ cho một việc
    # đã kết thúc là nhắc phụ huynh về chuyện không còn xảy ra.
    assert 'HV Da Roi' not in theo_ten, list(theo_ten)


@pytest.mark.django_db
def test_get_KHONG_ghi_gi(lop, chua_oa):
    """Một 'bản xem trước' mà cấp chìa là đã hành động trước khi người dùng gật."""
    truoc = q1('SELECT COUNT(*) AS n FROM parent_report_links')['n']
    _goi('get', ai=lop['gv'], class_id=lop['id'])
    assert q1('SELECT COUNT(*) AS n FROM parent_report_links')['n'] == truoc


@pytest.mark.django_db
def test_get_noi_ro_con_thieu_bien_moi_truong_nao(lop, chua_oa):
    kq = _goi('get', ai=lop['gv'], class_id=lop['id'])
    assert kq.data['znsSanSang'] is False
    assert 'ZALO_OA_ACCESS_TOKEN' in kq.data['znsThieu']


# ── POST khi CHƯA có OA ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_chua_co_oa_thi_cap_link_chu_KHONG_tao_dong_cho(lop, chua_oa):
    kq = _goi('post', {}, ai=lop['gv'], class_id=lop['id'])
    assert kq.status_code == 200, kq.data
    theo_ten = {r['name']: r for r in kq.data['ketQua']}
    assert theo_ten['HV Co So']['trangThai'] == 'gui_tay'
    assert '/bc/' in theo_ten['HV Co So']['duongDan']
    # Hàng chờ mà không có gì xử lý là một danh sách việc GIẢ.
    assert q1('SELECT COUNT(*) AS n FROM parent_report_sends')['n'] == 0


@pytest.mark.django_db
def test_thieu_so_phu_huynh_duoc_NEU_TEN(lop, chua_oa):
    kq = _goi('post', {}, ai=lop['gv'], class_id=lop['id'])
    theo_ten = {r['name']: r for r in kq.data['ketQua']}
    # `thieu_lienlac` chứ không còn `thieu_so`: từ 07/09/2026 có thêm kênh
    # email, nên "thiếu số" không còn mô tả đúng — em có email mà không có số
    # thì vẫn gửi được.
    assert theo_ten['HV Khong So']['trangThai'] == 'thieu_lienlac'
    # Vẫn có link: giảng viên có thể gửi qua kênh khác, hoặc đi hỏi số.
    assert '/bc/' in theo_ten['HV Khong So']['duongDan']


# ── POST khi ĐÃ có OA ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_gui_that_ghi_vao_so(lop, oa_gia):
    kq = _goi('post', {}, ai=lop['gv'], class_id=lop['id'])
    assert kq.status_code == 200, kq.data
    theo_ten = {r['name']: r for r in kq.data['ketQua']}
    assert theo_ten['HV Co So']['trangThai'] == 'da_gui'
    assert q1('SELECT COUNT(*) AS n FROM parent_report_sends')['n'] == 1
    d = q1('SELECT status, phone, provider_id, sent_at FROM parent_report_sends')
    assert d['status'] == 'da_gui' and d['phone'] == '0912345678'
    assert d['provider_id'] and d['sent_at'] is not None


@pytest.mark.django_db
def test_khong_gui_cho_em_thieu_so(lop, oa_gia):
    _goi('post', {}, ai=lop['gv'], class_id=lop['id'])
    # Đúng MỘT tin: em thiếu số không được gọi tới Zalo.
    assert len(oa_gia) == 1, oa_gia
    assert oa_gia[0][0] == '0912345678'


@pytest.mark.django_db
def test_tin_mang_du_bon_tham_so_cua_mau(lop, oa_gia):
    from teaching.parent_send import THAM_SO_MAU
    _goi('post', {}, ai=lop['gv'], class_id=lop['id'])
    _, tham_so = oa_gia[0]
    assert set(tham_so) == set(THAM_SO_MAU), (set(tham_so), set(THAM_SO_MAU))
    assert '/bc/' in tham_so['duong_dan']


@pytest.mark.django_db
def test_luot_gui_HONG_van_vao_so(lop, monkeypatch):
    """Không ghi lượt hỏng thì lần sau không ai biết em nào đã thử và trượt."""
    monkeypatch.setattr(zalo, 'da_cau_hinh', lambda: True)
    monkeypatch.setattr(zalo, 'thieu_gi', lambda: [])
    monkeypatch.setattr(zalo, 'gui_zns',
                        lambda p, t: (False, None, 'Zalo từ chối gửi (mã -124)'))
    kq = _goi('post', {}, ai=lop['gv'], class_id=lop['id'])
    theo_ten = {r['name']: r for r in kq.data['ketQua']}
    assert theo_ten['HV Co So']['trangThai'] == 'loi'
    d = q1('SELECT status, error, sent_at FROM parent_report_sends')
    assert d['status'] == 'loi' and 'mã -124' in d['error']
    # `sent_at` phải TRỐNG: đánh dấu thời điểm gửi cho một tin chưa bao giờ tới
    # nơi là làm hỏng chính con số mà sổ này sinh ra để trả lời.
    assert d['sent_at'] is None


@pytest.mark.django_db
def test_gui_hai_lan_khong_de_ra_hai_chia_cung_ky(lop, oa_gia):
    _goi('post', {}, ai=lop['gv'], class_id=lop['id'])
    _goi('post', {}, ai=lop['gv'], class_id=lop['id'])
    n = q1('SELECT COUNT(*) AS n FROM parent_report_links WHERE user_id=%s',
           (lop['co'].id,))['n']
    assert n == 1, n
    # Nhưng HAI lượt gửi thì vào sổ đủ hai: phụ huynh báo chưa nhận được và
    # được gửi lại là một sự kiện có thật, phải đếm được.
    assert q1('SELECT COUNT(*) AS n FROM parent_report_sends')['n'] == 2


# ── Cổng ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_hoc_vien_khong_bam_duoc_nut_nay(lop, chua_oa):
    kq = _goi('post', {}, ai=lop['co'], class_id=lop['id'])
    assert kq.status_code in (403, 404), kq.status_code


@pytest.mark.django_db
def test_giang_vien_lop_khac_khong_gui_duoc(lop, chua_oa):
    la = _nguoi('GV La Gui', ROLE_TEACHER)
    assert _goi('post', {}, ai=la, class_id=lop['id']).status_code == 404
    assert _goi('get', ai=la, class_id=lop['id']).status_code == 404


# ══ CHẾ ĐỘ THỬ — xem trước nội dung, KHÔNG gửi, KHÔNG ghi sổ ════════════════
#
# Anh Sơn chốt 07/09/2026: dựng chế độ thử trước khi bật ZNS thật. Mỗi tin ZNS
# mất phí và không thu về được, còn người nhận là phụ huynh học viên — nên phải
# xem được ĐÚNG nội dung sẽ đi trước khi bấm gửi.
#
# Ba phép kiểm dưới đây canh ba lời hứa của chế độ ấy, và lời hứa nặng nhất là
# lời hứa THỨ HAI: không ghi sổ. Sổ `parent_report_sends` là sổ của những tin ĐÃ
# ĐI; một dòng 'da_gui' cho tin chưa từng rời máy chủ là loại nói dối khó thấy
# nhất — lần sau mở sổ ra sẽ tưởng phụ huynh đã nhận, và không ai gửi lại.


@pytest.fixture
def che_do_thu(monkeypatch):
    """Bật chế độ thử qua ĐÚNG biến môi trường thật, không vá hàm.

    Vá `zalo.che_do_thu` thì phép kiểm chỉ chứng minh nhánh `if` chạy đúng.
    Đặt biến thì nó đi qua cả `_thong_so`, `soan_zns` và `gui_zns` thật — tức
    kiểm đúng thứ sẽ chạy trên máy chủ.
    """
    monkeypatch.setenv('ZALO_CHE_DO_THU', '1')
    # Không có OA: đây đúng trạng thái hôm nay, và chế độ thử phải chạy được
    # trong trạng thái ấy — nếu nó đòi token thì nó vô dụng đúng lúc cần nhất.
    monkeypatch.delenv('ZALO_OA_ACCESS_TOKEN', raising=False)
    monkeypatch.delenv('ZALO_ZNS_TEMPLATE_ID', raising=False)


@pytest.mark.django_db
def test_che_do_thu_KHONG_ghi_dong_nao_vao_so_gui(lop, che_do_thu):
    truoc = q1('SELECT count(*) AS n FROM parent_report_sends')['n']
    kq = _goi('post', {}, ai=lop['gv'], class_id=lop['id'])
    assert kq.status_code == 200, kq.data
    sau = q1('SELECT count(*) AS n FROM parent_report_sends')['n']
    assert sau == truoc, 'chế độ thử đã ghi %d dòng vào sổ gửi' % (sau - truoc)


@pytest.mark.django_db
def test_che_do_thu_tra_ve_dung_noi_dung_se_gui(lop, che_do_thu):
    """Toàn bộ mục đích của chế độ này: người bấm DUYỆT được nội dung."""
    kq = _goi('post', {}, ai=lop['gv'], class_id=lop['id'])
    assert kq.data['znsCheDoThu'] is True, kq.data

    em = next(r for r in kq.data['ketQua'] if r['id'] == lop['co'].id)
    assert em['trangThai'] == 'thu', em
    assert em['soNhan'] == '0912345678', em
    # Đúng bốn tham số của mẫu ZNS, không thiếu không thừa.
    from teaching.parent_send import THAM_SO_MAU
    assert set(em['noiDung']) == set(THAM_SO_MAU), em['noiDung']
    assert em['noiDung']['ten_hoc_vien'] == 'HV Co So', em['noiDung']
    assert em['noiDung']['duong_dan'].startswith('http'), em['noiDung']

    # Em chưa khai số phụ huynh vẫn phải được báo là thiếu số, không lẫn vào
    # nhóm "đã thử" — người bấm cần biết ai sẽ KHÔNG nhận được gì.
    khong = next(r for r in kq.data['ketQua'] if r['id'] == lop['khong'].id)
    assert khong['trangThai'] == 'thieu_lienlac', khong


@pytest.mark.django_db
def test_che_do_thu_KHONG_goi_mang(lop, che_do_thu, monkeypatch):
    """Không một byte nào được rời khỏi máy chủ.

    Vá `requests.post` thành một hàm NỔ: nếu chế độ thử lỡ gọi mạng thật thì
    phép kiểm đỏ ngay, thay vì im lặng gửi tin mất phí trong lúc chạy CI.
    """
    import requests

    def no(*a, **k):
        raise AssertionError('chế độ thử ĐÃ gọi mạng — đúng thứ nó sinh ra để tránh')
    monkeypatch.setattr(requests, 'post', no)

    kq = _goi('post', {}, ai=lop['gv'], class_id=lop['id'])
    assert kq.status_code == 200, kq.data
    assert any(r['trangThai'] == 'thu' for r in kq.data['ketQua']), kq.data


# ── KÊNH EMAIL (07/09/2026) ─────────────────────────────────────────────────
#
# ZNS đòi Zalo OA đã xác thực, mà xác thực đòi giấy phép kinh doanh — anh Sơn
# không có, và đây mới là thử nghiệm. Nên email là kênh CHÍNH, ZNS là kênh cho
# ngày có OA.


@pytest.mark.django_db
def test_email_gui_duoc_cho_em_KHONG_co_so_dien_thoai(em_co_email, chua_oa, mail_gia):
    """Đây là toàn bộ lý do mở kênh email: gửi được ở nơi ZNS bó tay."""
    lop = em_co_email
    kq = _goi('post', {}, ai=lop['gv'], class_id=lop['id'])

    theo_ten = {r['name']: r for r in kq.data['ketQua']}
    em = theo_ten['HV Khong So']
    assert em['trangThai'] == 'da_gui', em
    assert em['kenh'] == 'email', em

    assert len(mail_gia) == 1, mail_gia
    assert mail_gia[0]['den'] == 'me.a@example.com'
    # Em CÓ số nhưng chưa cấu hình ZNS thì không gửi được — và đó phải là
    # "gửi tay", không phải "thiếu liên lạc": em ấy có số, chỉ là hệ thống
    # chưa nối được kênh.
    assert theo_ten['HV Co So']['trangThai'] == 'gui_tay', theo_ten['HV Co So']


@pytest.mark.django_db
def test_thu_email_co_PDF_dinh_kem_va_duong_dan_trong_than(em_co_email, chua_oa, mail_gia):
    lop = em_co_email
    _goi('post', {}, ai=lop['gv'], class_id=lop['id'])

    thu = mail_gia[0]
    ten_tep, kieu, du_lieu = thu['dinhKem'][0]
    assert kieu == 'application/pdf'
    assert du_lieu[:5] == b'%PDF-', 'tệp đính kèm không phải PDF'
    assert ten_tep.endswith('.pdf')
    # Tên học viên trong tiêu đề: phụ huynh có hai con học ở đây thì hai lá
    # thư phải phân biệt được ngay ở danh sách hộp thư.
    assert 'HV Khong So' in thu['tieuDe']
    # Đường dẫn báo cáo phải có trong CẢ phần chữ thuần — người đọc bằng ứng
    # dụng thư chỉ hiện chữ thuần vẫn phải tới được tờ giấy.
    assert '/bc/' in thu['chu']


@pytest.mark.django_db
def test_email_duoc_uu_tien_hon_zns_khi_ca_hai_san_sang(lop, oa_gia, mail_gia):
    """Em `HV Co So` có SỐ; cho thêm email thì phải đi đường email.

    Không phải vì email tốt hơn — vì anh Sơn chốt email là kênh chính khi ZNS
    còn vướng xác thực. Nếu ai đổi thứ tự trong `_kenh_cho` thì phép kiểm này
    đỏ, và người đổi phải nói rõ vì sao.
    """
    from common.db import x as _x
    _x('UPDATE users SET parent_email=%s WHERE id=%s',
       ('me.b@example.com', lop['co'].id))

    kq = _goi('post', {}, ai=lop['gv'], class_id=lop['id'])
    em = {r['name']: r for r in kq.data['ketQua']}['HV Co So']

    assert em['kenh'] == 'email', em
    assert len(mail_gia) == 1 and mail_gia[0]['den'] == 'me.b@example.com'
    assert oa_gia == [], 'đã gửi ZNS trong khi email sẵn sàng'


@pytest.mark.django_db
def test_lan_gui_email_vao_so_dung_kenh_va_dung_dia_chi(em_co_email, chua_oa, mail_gia):
    lop = em_co_email
    _goi('post', {}, ai=lop['gv'], class_id=lop['id'])

    d = q1('''SELECT channel, email, phone, status FROM parent_report_sends
                ORDER BY id DESC LIMIT 1''')
    assert d['channel'] == 'email'
    assert d['email'] == 'me.a@example.com'
    # `phone` là cột của kênh ZNS. Nhét địa chỉ email vào đó thì mọi truy vấn
    # thống kê theo số điện thoại đọc phải một thứ không phải số điện thoại.
    assert d['phone'] == ''
    assert d['status'] == 'da_gui'


@pytest.mark.django_db
def test_che_do_thu_EMAIL_khong_ghi_so_va_van_duyet_duoc_noi_dung(
        em_co_email, chua_oa, monkeypatch):
    """Chế độ thử của email phải giữ ĐÚNG hai tính chất của chế độ thử ZNS."""
    lop = em_co_email
    monkeypatch.setattr(mail, 'da_cau_hinh', lambda: False)
    monkeypatch.setattr(mail, 'che_do_thu', lambda: True)
    goi = []
    monkeypatch.setattr(mail, 'gui',
                        lambda *a, **k: (goi.append(a) or (True, 'THU:x', None)))

    kq = _goi('post', {}, ai=lop['gv'], class_id=lop['id'])
    em = {r['name']: r for r in kq.data['ketQua']}['HV Khong So']

    assert em['trangThai'] == 'thu' and em['kenh'] == 'email'
    # Sổ gửi là sổ của những thư ĐÃ ĐI.
    assert q1('SELECT COUNT(*) AS n FROM parent_report_sends')['n'] == 0
    # Và người bấm vẫn phải DUYỆT được nội dung — đó là toàn bộ mục đích.
    assert 'tieuDe' in em['noiDung'] and 'dinhKem' in em['noiDung']
    assert em['noiDung']['dinhKem'][0]['ten'].endswith('.pdf')
    assert em['noiDung']['dinhKem'][0]['kb'] > 0


@pytest.mark.django_db
def test_GET_noi_ro_kenh_nao_dung_duoc_cho_tung_em(em_co_email, chua_oa, mail_gia):
    lop = em_co_email
    kq = _goi('get', ai=lop['gv'], class_id=lop['id'])

    assert kq.data['emailSanSang'] is True
    theo_ten = {e['name']: e for e in kq.data['students']}
    assert theo_ten['HV Khong So']['kenh'] == 'email'
    assert theo_ten['HV Khong So']['parentEmail'] == 'me.a@example.com'
    # Em có SỐ mà chưa cấu hình ZNS: CÓ liên lạc nhưng CHƯA gửi được. Hai cờ
    # phải nói ra hai chuyện ấy riêng rẽ.
    assert theo_ten['HV Co So']['coLienLac'] is True
    assert theo_ten['HV Co So']['kenh'] is None
