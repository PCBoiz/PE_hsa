"""Dán liên hệ phụ huynh cho CẢ LỚP — giảng viên/học vụ nhập hộ, xem trước rồi mới ghi.

── VÌ SAO CÓ (13/09/2026) ─────────────────────────────────────────────────

Kênh gửi báo cáo CHÍNH là email (anh Sơn chốt 07/09), nhưng tới hôm nay không có
đường nào ghi `users.parent_email` — đo production: 0 em có. Ô ở Cài đặt (mở
cùng ngày) chỉ giải quyết một nửa. Nửa kia là thực tế ở trung tâm: số và email
của bố mẹ nằm trong TỆP ĐĂNG KÝ học vụ đang giữ, không nằm trong đầu các em lớp
12. Chờ 25 em tự vào Cài đặt điền là chờ mãi.

Các hệ quản lý trường học làm việc này cùng một kiểu: nhập theo tệp, khớp theo
mã học sinh, và cho người nhập DUYỆT danh sách đã khớp trước khi ghi.

── CHỈ KHỚP EM TRONG DANH SÁCH LỚP, KHÔNG TRA CẢ HỆ THỐNG ─────────────────

Người dán chỉ chạm được em ĐANG HỌC của CHÍNH lớp này — cùng danh sách với màn
hình gửi báo cáo (`parent_send._hoc_vien_dang_hoc`). Tra cả bảng `users` thì một
dòng mang email của em lớp khác sẽ ghi đè liên hệ phụ huynh của em ấy: một lối
đọc-ghi chéo (IDOR) đi bằng văn bản dán, không cần đoán id nào.

── HAI CÁCH ĐỌC MỘT DÒNG ──────────────────────────────────────────────────

Có dòng TIÊU ĐỀ → đọc theo TÊN CỘT. Đây là cách đúng cho bảng đăng ký thật: bảng
ấy có CẢ số của em lẫn số của bố mẹ, và hai số trông y hệt nhau. Không có tên
cột thì không phân biệt được bằng bất cứ cách nào.

Không có tiêu đề → đọc theo NỘI DUNG, như ô cấp tài khoản hàng loạt: ô đầu (bỏ
cột STT) là em học viên — họ tên, email hoặc số của em; phần còn lại, ô có @ là
email phụ huynh, ô trông như số là số Zalo, ô chữ là tên phụ huynh. Hai ô cùng
loại mà không phân định được thì TRƯỢT cả dòng chứ không đoán: đoán sai là ghi
tên học viên vào ô tên phụ huynh, hoặc gửi báo cáo về chính số của em.

── Ô TRỐNG THÌ GIỮ ────────────────────────────────────────────────────────

Dán thiếu cột email không được xoá email đang có. Muốn xoá thì sửa từng em —
xoá hàng loạt bằng một lần dán thiếu cột là tai nạn, không phải thao tác.
"""
import re
import unicodedata

from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.validators import validate_email_field, validate_name_field, validate_phone_field
from common import audit
from common.db import q1, x
from common.identity import looks_like_email, norm_email, norm_phone
from common.permissions import IsSeniorTeachingStaff, can_see_class
from teaching.admin_users import _PHONE_SHAPED, _SPLIT_COLUMNS, MAX_PARSE_LINES
from teaching.parent_send import _hoc_vien_dang_hoc

#: Trần độ dài văn bản dán. Một lớp 50 em kèm đủ cột chưa tới 10 kB; trần rộng
#: tay để dán cả bảng đăng ký nhiều lớp, nhưng chặn một khối vài MB đi thẳng vào
#: vòng lặp phân tích.
MAX_KY_TU = 200_000

#: Cột STT đứng đầu dòng khi chép từ bảng tính: "1", "12.", "3)".
_STT = re.compile(r'\d{1,4}[.)]?')

#: Sáu loại cột nhận ra được từ dòng tiêu đề, và tên đọc được của chúng — màn
#: hình hiện lại cách hệ thống đã hiểu từng cột, để người dán thấy ngay khi một
#: cột bị hiểu sai trước khi lưu.
_NHAN_COT = {
    'hv_name': 'họ tên em', 'hv_email': 'email của em', 'hv_phone': 'SĐT của em',
    'ph_name': 'tên phụ huynh', 'ph_phone': 'số Zalo phụ huynh', 'ph_email': 'email phụ huynh',
}

_GOI_Y_TIEU_DE = 'Dán kèm dòng tiêu đề của bảng để hệ thống đọc theo tên cột.'


def _khoa_ten(s):
    """Khoá so tên: cùng dạng Unicode, không phân biệt hoa thường, gộp khoảng trắng.

    KHÔNG bỏ dấu: "Nguyễn Văn An" và "Nguyễn Văn Ân" là hai người khác nhau, và
    gộp chúng lại là ghi liên hệ của nhà này vào hồ sơ của nhà kia.
    """
    return ' '.join(unicodedata.normalize('NFC', s or '').casefold().split())


def _giong_so(o):
    return (bool(o) and not looks_like_email(o) and _PHONE_SHAPED.fullmatch(o) is not None
            and any(ch.isdigit() for ch in o))


def _loai_cot(tieu_de):
    """Tên cột → một khoá của `_NHAN_COT`, hoặc None (cột bỏ qua: STT, ngày sinh…)."""
    k = _khoa_ten(tieu_de)
    tu = set(re.findall(r'\w+', k))
    cua_ph = ('phụ huynh' in k or 'phu huynh' in k
              or bool(tu & {'ph', 'bố', 'mẹ', 'cha', 'parent', 'guardian'}))
    if 'mail' in k:
        loai = 'email'
    elif tu & {'sđt', 'sdt', 'đt', 'dt', 'zalo', 'phone'} or 'điện thoại' in k or 'dien thoai' in k:
        loai = 'phone'
    elif (tu & {'tên', 'ten', 'name'}
          or k in {'phụ huynh', 'phu huynh', 'bố mẹ', 'cha mẹ', 'parent', 'guardian'}
          or any(c in k for c in ('học viên', 'học sinh', 'hoc vien', 'hoc sinh'))):
        # "Địa chỉ phụ huynh", "Nghề nghiệp phụ huynh" KHÔNG rơi vào đây: chỉ
        # nhận là tên khi có chữ "tên" hoặc tiêu đề CHỈ gồm "Phụ huynh".
        loai = 'name'
    else:
        return None
    return ('ph_' if cua_ph else 'hv_') + loai


def _tach(dong, chi_tab):
    return [o.strip() for o in (dong.split('\t') if chi_tab else _SPLIT_COLUMNS.split(dong))]


def _doc(text):
    """Văn bản dán → ``(ô_tiêu_đề | None, [(số_dòng, [ô…])], bị_cắt)``.

    Số dòng đếm trên ĐÚNG văn bản người ta dán (từ 1, kể cả dòng trống) — cùng
    lý do với `admin_users._parse_text`: đánh số lại là chỉ vào dòng khác.

    Dòng đầu có dấu tab thì CẢ văn bản chỉ tách theo tab: bảng tính chép ra là
    tab, và một ô "Hà Nội, Việt Nam" tách theo dấu phẩy sẽ đẩy lệch mọi cột
    phía sau — lệch cột ở chế độ đọc theo tiêu đề là ghi nhầm ô.
    """
    dong = [(i, d) for i, d in enumerate((text or '').splitlines(), start=1) if d.strip()]
    if not dong:
        return None, [], False
    chi_tab = '\t' in dong[0][1]
    dau = _tach(dong[0][1], chi_tab)
    la_tieu_de = (any(_loai_cot(o) for o in dau if o)
                  and not any(looks_like_email(o) or _giong_so(o) for o in dau if o))
    du_lieu = dong[1:] if la_tieu_de else dong
    return ((dau if la_tieu_de else None),
            [(i, _tach(d, chi_tab)) for i, d in du_lieu[:MAX_PARSE_LINES]],
            len(du_lieu) > MAX_PARSE_LINES)


def _cot_theo_tieu_de(dau):
    """→ ``(cột, mô_tả, lỗi)``. `cột` = khoá loại → danh sách chỉ số cột.

    Nhiều cột cùng loại ("Email bố", "Email mẹ") thì lấy ô ĐẦU TIÊN có chữ.
    """
    cot, mo_ta = {}, []
    for i, h in enumerate(dau):
        if not h:
            continue
        k = _loai_cot(h)
        mo_ta.append({'tieuDe': h, 'la': _NHAN_COT.get(k)})
        if k:
            cot.setdefault(k, []).append(i)
    if not any(k.startswith('ph_') for k in cot):
        return None, mo_ta, ('Dòng tiêu đề không có cột nào của phụ huynh. Đặt tên cột kiểu '
                             '"Tên phụ huynh", "SĐT phụ huynh", "Email phụ huynh" — hoặc bỏ '
                             'dòng tiêu đề và dán mỗi dòng: em học viên trước, liên hệ phụ huynh sau.')
    if not any(k.startswith('hv_') for k in cot):
        return None, mo_ta, ('Dòng tiêu đề không có cột nào chỉ ra em học viên (họ tên, email '
                             'hoặc SĐT của em), nên không biết mỗi dòng là của em nào.')
    return cot, mo_ta, None


def _chi_muc(ds):
    theo_ten = {}
    for e in ds:
        theo_ten.setdefault(_khoa_ten(e['name']), []).append(e)
    return {'email': {norm_email(e['email']): e for e in ds if e['email']},
            'so': {norm_phone(e['phone']): e for e in ds if e['phone']},
            'ten': theo_ten}


def _tim_em(lop, email, so, ten):
    """Em nào trong lớp? → ``(em | None, lý_do_trượt | None)``."""
    if not (email or so or ten):
        return None, 'Dòng này không có ô nào chỉ ra em học viên.'
    thay, trung_ten = {}, 0
    if email and (e := lop['email'].get(norm_email(email))):
        thay[e['id']] = e
    if so and (e := lop['so'].get(norm_phone(so))):
        thay[e['id']] = e
    if ten:
        cung_ten = lop['ten'].get(_khoa_ten(ten), [])
        if len(cung_ten) == 1:
            thay[cung_ten[0]['id']] = cung_ten[0]
        elif len(cung_ten) > 1:
            trung_ten = len(cung_ten)
    if len(thay) == 1:
        return next(iter(thay.values())), None
    if len(thay) > 1:
        return None, ('Các ô của em trên dòng này trỏ tới %d em khác nhau (%s).'
                      % (len(thay), ', '.join(e['name'] or '#%d' % e['id'] for e in thay.values())))
    if trung_ten:
        return None, ('Lớp có %d em tên "%s" — dùng email hoặc SĐT của em thay cho tên.'
                      % (trung_ten, ten))
    return None, ('Không tìm thấy em "%s" trong danh sách đang học của lớp này.'
                  % (email or so or ten))


def _theo_cot(o, cot, lop):
    def lay(khoa):
        return next((o[i] for i in cot.get(khoa, ()) if i < len(o) and o[i]), '')
    em, ly_do = _tim_em(lop, lay('hv_email'), lay('hv_phone'), lay('hv_name'))
    return em, (lay('ph_name'), lay('ph_phone'), lay('ph_email')), ly_do


def _theo_noi_dung(o, lop):
    o = [c for c in o if c]
    if len(o) > 1 and _STT.fullmatch(o[0]):
        o = o[1:]
    trong = ('', '', '')
    if not o:
        return None, trong, 'Dòng này không có ô nào chỉ ra em học viên.'
    dau, con_lai = o[0], o[1:]
    if looks_like_email(dau):
        em, ly_do = _tim_em(lop, dau, '', '')
    elif _giong_so(dau):
        em, ly_do = _tim_em(lop, '', dau, '')
    else:
        em, ly_do = _tim_em(lop, '', '', dau)
    if em is None:
        return None, trong, ly_do

    emails = [c for c in con_lai if looks_like_email(c)]
    sos = [c for c in con_lai if _giong_so(c)]
    chus = [c for c in con_lai if not looks_like_email(c) and not _giong_so(c)
            and _khoa_ten(c) != _khoa_ten(em['name'])]
    # Hai ô cùng loại mà một ô trùng chính email/số của EM thì ô ấy là của em
    # (dòng đăng ký đủ cột). Chỉ bỏ khi CÒN ô khác: tài khoản mở bằng số của mẹ
    # thì số ấy đúng là số phụ huynh, và bỏ đi là dòng không còn gì để lưu.
    if len(emails) > 1:
        emails = [c for c in emails if norm_email(c) != norm_email(em['email'])]
    if len(sos) > 1:
        sos = [c for c in sos if norm_phone(c) != norm_phone(em['phone'])]
    for cac_o, loai in ((emails, 'email'), (sos, 'số điện thoại')):
        if len(cac_o) > 1:
            return em, trong, ('Có %d ô %s, không rõ ô nào của phụ huynh: %s. %s'
                               % (len(cac_o), loai, ', '.join(cac_o), _GOI_Y_TIEU_DE))
    if len(chus) > 1:
        return em, trong, ('Có %d ô chữ, không rõ ô nào là tên phụ huynh: %s. %s'
                           % (len(chus), ', '.join('"%s"' % c for c in chus), _GOI_Y_TIEU_DE))
    return em, (chus[0] if chus else '', sos[0] if sos else '', emails[0] if emails else ''), None


def _chuan_hoa(ph):
    """``(tên, số, email)`` thô → ``(bản chuẩn hoá, lý_do_trượt | None)``. Rỗng = không đổi."""
    ten, so_tho, email_tho = (s.strip() for s in ph)
    if ten and validate_name_field(ten):
        return None, 'Tên phụ huynh dài quá 100 ký tự.'
    so = norm_phone(so_tho) or ''
    if so and (loi := validate_phone_field(so)):
        return None, 'Số Zalo phụ huynh "%s": %s' % (so_tho, loi)
    email = norm_email(email_tho) or ''
    if email and validate_email_field(email):
        return None, 'Email phụ huynh không hợp lệ: "%s".' % email_tho
    if not (ten or so or email):
        return None, 'Dòng này không có tên, số hay email phụ huynh nào để lưu.'
    return (ten, so, email), None


_COT_DB = (('parentName', 'parent_name'), ('parentPhone', 'parent_phone'),
           ('parentEmail', 'parent_email'))


def _cham(dong, cot, lop):
    """Chấm từng dòng, CHƯA GHI GÌ → ``(rows, ghi)``; `ghi` = ``[(em, thay_đổi)]``."""
    rows, ghi, da_gap = [], [], {}
    for so_dong, o in dong:
        em, ph, ly_do = _theo_cot(o, cot, lop) if cot is not None else _theo_noi_dung(o, lop)
        gia_tri = None
        if ly_do is None:
            gia_tri, ly_do = _chuan_hoa(ph)
        if ly_do is None and em['id'] in da_gap:
            ly_do = 'Em này đã có ở dòng %d — giữ dòng đầu, bỏ dòng này.' % da_gap[em['id']]
        hoc_vien = {'id': em['id'], 'name': em['name']} if em else None
        if ly_do:
            rows.append({'line': so_dong, 'hocVien': hoc_vien, 'trangThai': 'bo_qua',
                         'lyDo': ly_do, 'doi': {}})
            continue
        da_gap[em['id']] = so_dong
        doi = {}
        for (khoa, cot_db), moi in zip(_COT_DB, gia_tri, strict=True):
            cu = em[cot_db] or ''
            if moi and moi != cu:
                doi[khoa] = {'cu': cu, 'moi': moi}
        rows.append({'line': so_dong, 'hocVien': hoc_vien,
                     'trangThai': 'doi' if doi else 'giu',
                     'lyDo': None if doi else 'Trùng với thông tin đang lưu — không đổi gì.',
                     'doi': doi})
        if doi:
            ghi.append((em, doi))
    return rows, ghi


def _con_thieu(ds, ghi):
    """Em vẫn KHÔNG có số lẫn email phụ huynh sau lần này — nêu tên, không chỉ đếm."""
    moi = {em['id']: doi for em, doi in ghi}
    ra = []
    for e in ds:
        d = moi.get(e['id'], {})
        so = d['parentPhone']['moi'] if 'parentPhone' in d else (e['parent_phone'] or '')
        mail = d['parentEmail']['moi'] if 'parentEmail' in d else (e['parent_email'] or '')
        if not (so.strip() or mail.strip()):
            ra.append(e['name'] or '#%d' % e['id'])
    return ra


class ParentContactsImportView(APIView):
    """POST /api/teach/classes/<id>/parent-contacts — ``{text, dry_run}``.

    Cổng: giảng viên của lớp, học vụ, quản trị — KHÔNG trợ giảng. Cùng cổng với
    màn hình gửi báo cáo, vì cùng một thứ: liên lạc của gia đình em (anh Sơn chốt
    01/09/2026 trợ giảng không chạm).

    ``dry_run`` là bước bắt buộc của màn hình: trả đúng bảng sẽ ghi, ô nào ghi
    đè giá trị nào. Lưu thật thì chấm lại từ đầu trên dữ liệu mới nhất, rồi ghi
    MỘT câu cho cả lớp và MỘT dòng nhật ký có giá trị cũ.
    """
    permission_classes = [IsSeniorTeachingStaff]

    def post(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        body = request.data if isinstance(request.data, dict) else {}
        text = body.get('text') if isinstance(body.get('text'), str) else ''
        dry_run = bool(body.get('dry_run'))
        if not text.strip():
            return Response({'error': 'Chưa dán dòng nào.'}, status=400)
        if len(text) > MAX_KY_TU:
            return Response({'error': 'Văn bản dài quá %d ký tự — dán từng lớp một.'
                                      % MAX_KY_TU}, status=400)

        dau, dong, bi_cat = _doc(text)
        cot, mo_ta = None, []
        if dau is not None:
            cot, mo_ta, loi = _cot_theo_tieu_de(dau)
            if loi:
                return Response({'error': loi, 'cot': mo_ta}, status=400)
        if not dong:
            return Response({'error': 'Mới có dòng tiêu đề, chưa có dòng học viên nào.'},
                            status=400)

        ds = _hoc_vien_dang_hoc(class_id)
        rows, ghi = _cham(dong, cot, _chi_muc(ds))

        if not dry_run and ghi:
            vals = []
            for em, doi in ghi:
                vals.append(em['id'])
                vals.extend(doi[khoa]['moi'] if khoa in doi else None for khoa, _c in _COT_DB)
            lop = q1('SELECT name FROM classes WHERE id=%s', (class_id,)) or {}
            with transaction.atomic():
                # COALESCE: chỉ ghi ô CÓ đổi. Ô không đổi để nguyên cột trong
                # CSDL chứ không ghi lại giá trị đọc lúc nãy — nếu em vừa tự sửa
                # ở Cài đặt giữa lúc xem trước và lúc lưu thì không bị đè mất.
                x('UPDATE users AS u SET parent_name = COALESCE(v.ten, u.parent_name), '
                  'parent_phone = COALESCE(v.so, u.parent_phone), '
                  'parent_email = COALESCE(v.email, u.parent_email) '
                  'FROM (VALUES ' + ', '.join(['(%s::int, %s::text, %s::text, %s::text)'] * len(ghi))
                  + ') AS v(id, ten, so, email) WHERE u.id = v.id', tuple(vals))
                audit.record(
                    request, audit.CLASS_PARENT_CONTACTS, target_type='class',
                    target_id=class_id, target_label=lop.get('name') or str(class_id),
                    summary='Nhập liên hệ phụ huynh cho %d em (dán %d dòng).' % (len(ghi), len(dong)),
                    detail={'doi': [dict({'id': em['id'], 'name': em['name']}, **doi)
                                    for em, doi in ghi]})

        dem = {'doi': 0, 'giu': 0, 'bo_qua': 0}
        for r in rows:
            dem[r['trangThai']] += 1
        canh_bao = []
        if bi_cat:
            canh_bao.append('Danh sách dài hơn %d dòng nên phần sau CHƯA được đọc. Dán nốt '
                            'phần còn lại ở lần tiếp theo.' % MAX_PARSE_LINES)
        return Response({'ok': True, 'dryRun': dry_run, 'theoTieuDe': cot is not None,
                         'cot': mo_ta, 'soDong': len(dong), 'dem': dem, 'canhBao': canh_bao,
                         'conThieu': _con_thieu(ds, ghi), 'rows': rows})
