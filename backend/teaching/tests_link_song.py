"""§66 · LINK SỐNG — tờ báo cáo phụ huynh tính số liệu TỚI HÔM NAY, và nêu thay đổi lịch.

Ô cuối còn thiếu của CẢ HAI dòng 23 và 24 trong bảng phân rã:

  dòng 23 — *"Link 'sống' (số liệu tới hôm nay, không cố định theo kỳ)"* → CHƯA
  dòng 24 — *"Thông báo khi lịch đổi"* → anh Sơn chốt KHÔNG gửi cho phụ huynh;
            thay bằng *"link sống hiện 'thay đổi gần đây'"*

Chìa sống **45 ngày** (`HAN_NGAY`) nhưng `period_to` bị đóng băng lúc cấp. Nên phụ huynh mở
link vào ngày thứ 40 đọc được một tờ của 40 ngày trước: buổi con học tuần này không có trong
bảng chuyên cần, và nếu lớp đổi lịch thì tờ giấy vẫn in lịch cũ. Trung tâm thì tưởng đã gửi
thông tin — chìa vẫn mở được, `opened_count` vẫn tăng.

── BA RANH GIỚI KHÔNG ĐƯỢC NỚI THEO ─────────────────────────────────────────

① **Chỉ nới ĐẦU SAU.** `period_from` giữ nguyên. Nới cả đầu trước là cho một chìa cấp cho kỳ
  tháng 9 đọc ngược về tháng 6 — chìa là chìa, ai cầm link cũng mở được.

② **Hết hạn vẫn là hết hạn.** "Sống" nói về KHOẢNG SỐ LIỆU, không nói về tuổi thọ chìa. Lẫn
  hai thứ ấy là làm mất đường rút lại duy nhất đang có.

③ **Buổi bù của bạn khác không lộ.** Cùng hàng rào `thuoc_buoi` với mọi cửa buổi học khác —
  và cửa này không có vai nào đứng sau, nên nó là cửa phải chắc nhất.

── THỨ KHÔNG SUY RA ĐƯỢC, VÀ TÔI KHÔNG GIẢ VỜ LÀ CÓ ─────────────────────────

"Buổi X dời từ 19h sang 20h" KHÔNG suy ra được: `class_sessions` không có sổ ghi thay đổi,
`updated_at` thì nhúc nhích cả khi giảng viên chỉ dán link Zoom hay sửa sổ đầu bài. In
"lịch có thay đổi" dựa vào `updated_at` là nói với phụ huynh một điều mình không biết.

Nêu được ba thứ, cả ba đọc thẳng từ dữ liệu và không thể sai: **buổi bị huỷ**, **buổi học bù**,
**buổi mới thêm sau ngày cấp chìa**. Muốn có "đổi giờ" thì phải thêm một sổ ghi thay đổi — một
mục §NN riêng, không phải thứ nhét vào đây.

Chạy trên CSDL thật, giao dịch CUỘN LẠI.
"""
from datetime import timedelta

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from common.clock import local_now, local_today
from common.db import q, q1, x
from common.permissions import ROLE_STUDENT, ROLE_TEACHER
from teaching import thay_doi_lop as TD
from teaching.parent_link import ParentReportLinkView, PublicParentReportView

f = APIRequestFactory()
pytestmark = pytest.mark.django_db


def _goi(view, method, body=None, ai=None, **kw):
    req = (getattr(f, method)('/x', body, format='json') if body is not None
           else getattr(f, method)('/x'))
    if ai is not None:
        force_authenticate(req, user=ai)
    return view.as_view()(req, **kw)


def _nguoi(ten, vai, **cot):
    khoa = ', '.join(cot)
    cho = ', '.join(['%s'] * len(cot))
    r = q1(f'INSERT INTO users (name, email, password, role, streak'
           f'{", " + khoa if khoa else ""}) VALUES (%s, %s, %s, %s, 0'
           f'{", " + cho if cho else ""}) RETURNING id',
           (ten, '%s_ls@example.com' % ten.replace(' ', '_').lower(), 'x', vai, *cot.values()))
    return User.objects.get(id=r['id'])


@pytest.fixture
def canh(db):
    gv = _nguoi('GV Song', ROLE_TEACHER)
    em = _nguoi('HV Song', ROLE_STUDENT, parent_name='Me Song', parent_phone='0912000111')
    ban = _nguoi('HV Ban Song', ROLE_STUDENT)
    c = q1("INSERT INTO classes (name, course_id, teacher_id, status) "
           "VALUES ('Lop song','hsa_quantitative',%s,'active') RETURNING id", (gv.id,))
    for u in (em, ban):
        x('INSERT INTO class_members (class_id, user_id, joined_at) VALUES (%s,%s,%s)',
          (c['id'], u.id, local_now() - timedelta(days=60)))
    return {'lop': c['id'], 'gv': gv, 'em': em, 'ban': ban}


def _cap(canh):
    kq = _goi(ParentReportLinkView, 'post', {}, ai=canh['gv'],
              class_id=canh['lop'], user_id=canh['em'].id)
    assert kq.status_code == 201, kq.data
    return kq.data['token']


def _lui_chia(token, ngay):
    """Kéo chìa lùi `ngay` ngày: kỳ đóng băng và ngày cấp đều lùi, chìa vẫn còn hạn."""
    x('''UPDATE parent_report_links
            SET period_to = period_to - %s, period_from = period_from - %s,
                created_at = created_at - (%s * INTERVAL '1 day')
          WHERE token = %s''', (ngay, ngay, ngay, token))


def _buoi(lop, ngay_le, **cot):
    """Một buổi của lớp, lệch `ngay_le` ngày so với hôm nay (âm = quá khứ)."""
    khoa = ', '.join(cot)
    cho = ', '.join(['%s'] * len(cot))
    return q1(f'''INSERT INTO class_sessions (class_id, starts_at
                  {", " + khoa if khoa else ""})
                  VALUES (%s, %s {", " + cho if cho else ""}) RETURNING id''',
              (lop, local_now() + timedelta(days=ngay_le), *cot.values()))['id']


def _mo(token):
    return _goi(PublicParentReportView, 'get', token=token)


# ── ① Khoảng số liệu nới tới hôm nay ────────────────────────────────────────

def test_so_lieu_tinh_toi_hom_nay_du_ky_da_dong_bang(canh):
    tk = _cap(canh)
    _lui_chia(tk, 30)
    kq = _mo(tk)
    assert kq.status_code == 200, kq.data
    assert kq.data['period']['to'] == local_today().isoformat()


def test_dau_ky_KHONG_bi_noi_nguoc_ve_truoc(canh):
    """Chìa cấp cho kỳ tháng này không được đọc ngược về kỳ trước."""
    tk = _cap(canh)
    goc = q1('SELECT period_from FROM parent_report_links WHERE token = %s', (tk,))
    _lui_chia(tk, 30)
    sau = q1('SELECT period_from FROM parent_report_links WHERE token = %s', (tk,))
    assert _mo(tk).data['period']['from'] == sau['period_from'].isoformat()
    assert sau['period_from'] < goc['period_from']


def test_to_noi_ro_ky_da_cap_ban_dau(canh):
    """Không nói rõ thì phụ huynh không phân biệt được tờ này với tờ đã nhận tháng trước."""
    tk = _cap(canh)
    _lui_chia(tk, 30)
    d = q1('SELECT period_to FROM parent_report_links WHERE token = %s', (tk,))
    song = _mo(tk).data['song']
    assert song['kyCap']['to'] == d['period_to'].isoformat()
    assert song['toiNgay'] == local_today().isoformat()


def test_chia_het_han_van_404_du_da_song(canh):
    """"Sống" nói về khoảng SỐ LIỆU, không nói về tuổi thọ chìa."""
    tk = _cap(canh)
    x("UPDATE parent_report_links SET expires_at = now() - INTERVAL '1 day' WHERE token = %s", (tk,))
    assert _mo(tk).status_code == 404


def test_chia_da_thu_hoi_van_404(canh):
    tk = _cap(canh)
    x('UPDATE parent_report_links SET revoked_at = now() WHERE token = %s', (tk,))
    assert _mo(tk).status_code == 404


# ── ② Thay đổi gần đây ──────────────────────────────────────────────────────

def test_buoi_bi_huy_hien_trong_thay_doi_gan_day(canh):
    tk = _cap(canh)
    _lui_chia(tk, 20)
    sid = _buoi(canh['lop'], -3, status='cancelled', topic='Hình học phẳng')
    ds = _mo(tk).data['thayDoi']
    assert [t for t in ds if t['sessionId'] == sid and t['kieu'] == 'huy']


def test_buoi_them_sau_khi_cap_chia_hien_ra(canh):
    tk = _cap(canh)
    _lui_chia(tk, 20)
    sid = _buoi(canh['lop'], 2, topic='Buổi bổ sung')
    assert [t for t in _mo(tk).data['thayDoi'] if t['sessionId'] == sid and t['kieu'] == 'them']


def test_buoi_co_TRUOC_khi_cap_chia_khong_bi_ke_la_moi(canh):
    """Kể mọi buổi của lớp là biến mục "thay đổi" thành bản sao của thời khoá biểu."""
    sid = _buoi(canh['lop'], 3, topic='Buổi đã có sẵn')
    x("UPDATE class_sessions SET created_at = now() - INTERVAL '40 days' WHERE id = %s", (sid,))
    tk = _cap(canh)
    _lui_chia(tk, 20)
    assert not [t for t in _mo(tk).data['thayDoi'] if t['sessionId'] == sid]


def test_buoi_bu_CUA_BAN_KHAC_khong_lo_ra(canh):
    """Buổi bù chỉ thuộc về mấy em có tên trong đó (§62e) — cửa này không có vai nào đứng sau."""
    tk = _cap(canh)
    _lui_chia(tk, 20)
    sid = _buoi(canh['lop'], 1, topic='Bù riêng cho bạn khác')
    x('INSERT INTO session_participants (session_id, user_id) VALUES (%s, %s)',
      (sid, canh['ban'].id))
    assert not [t for t in _mo(tk).data['thayDoi'] if t['sessionId'] == sid]


def test_buoi_cua_lop_KHAC_khong_lot_vao(canh):
    """Đòi MỌI dòng thuộc lớp của em, không chỉ "buổi tôi vừa tạo thì vắng mặt".

    Bản đầu chỉ hỏi vế sau và ĐỘT BIẾN LỌT (28/09): bỏ lọc lớp làm câu SQL kéo về buổi của cả
    CSDL, `LIMIT` cắt lấy 12 buổi sớm nhất, và buổi tôi vừa tạo rơi ra ngoài trần — nên phép
    kiểm "không thấy" nó và tưởng hàng rào còn nguyên. Một phép kiểm mà TRẦN của câu truy vấn
    có thể làm cho xanh thì nó đang canh cái trần, không canh hàng rào.
    """
    tk = _cap(canh)
    _lui_chia(tk, 20)
    lop_la = q1("INSERT INTO classes (name, course_id, status) "
                "VALUES ('Lop la','hsa_verbal','active') RETURNING id")['id']
    sid = _buoi(lop_la, 1, topic='Của lớp khác')
    ds = _mo(tk).data['thayDoi']
    assert sid not in [t['sessionId'] for t in ds]
    cua_lop = {r['id'] for r in q('SELECT id FROM class_sessions WHERE class_id = %s',
                                  (canh['lop'],))}
    la = [t for t in ds if t['sessionId'] not in cua_lop]
    assert not la, 'có %d dòng KHÔNG thuộc lớp của em: %s' % (len(la), la[:3])


def test_nhan_thay_doi_la_chu_tieng_viet_khong_phai_ma(canh):
    """RULES §10 — tờ này gửi cho phụ huynh, `cancelled` trên đó là một lỗi nhìn thấy được."""
    tk = _cap(canh)
    _lui_chia(tk, 20)
    _buoi(canh['lop'], -2, status='cancelled', topic='Đại số')
    ds = _mo(tk).data['thayDoi']
    assert ds, 'phải có ít nhất một dòng để kiểm nhãn'
    for t in ds:
        assert t['nhan'] and t['nhan'] == t['nhan'].strip()
        assert 'cancelled' not in t['nhan'] and 'planned' not in t['nhan']


def test_qua_tran_thi_to_phai_NOI_RA_la_con_nua(canh):
    """Cắt bớt mà im lặng là cách êm ái nhất để một tờ báo cáo nói dối.

    Lớp sinh lại lịch cả kỳ là hàng chục buổi "mới xếp thêm" cùng lúc. Tờ in `TRAN` dòng rồi
    dừng; phụ huynh đếm được 12 và tưởng đó là tất cả — trong khi buổi ảnh hưởng tới con có
    thể nằm ở dòng 13.
    """
    tk = _cap(canh)
    _lui_chia(tk, 20)
    for i in range(TD.TRAN + 1):
        _buoi(canh['lop'], i + 1, topic='Buổi thêm %d' % i)
    d = _mo(tk).data
    assert len(d['thayDoi']) == TD.TRAN
    assert d['thayDoiConNua'] is True


def test_du_cho_thi_khong_bao_con_nua(canh):
    """Báo "còn nữa" khi đã in hết là dạy người đọc thôi tin dòng ấy."""
    tk = _cap(canh)
    _lui_chia(tk, 20)
    _buoi(canh['lop'], 1, topic='Một buổi thêm')
    d = _mo(tk).data
    assert len(d['thayDoi']) == 1
    assert d['thayDoiConNua'] is False


def test_khong_co_thay_doi_thi_la_danh_sach_rong_khong_phai_thieu_khoa(canh):
    """Màn phải phân biệt "không có thay đổi nào" với "máy chủ chưa trả khoá ấy"."""
    tk = _cap(canh)
    assert _mo(tk).data['thayDoi'] == []


def test_to_qua_chia_van_KHONG_mang_lien_lac_cua_em(canh):
    """Nới khoảng số liệu không được vô tình nới cả những gì đi qua chìa."""
    tk = _cap(canh)
    _lui_chia(tk, 30)
    d = _mo(tk).data
    assert 'email' not in d['student'] and 'phone' not in d['student']
    assert set(d['parent']) == {'name'}
