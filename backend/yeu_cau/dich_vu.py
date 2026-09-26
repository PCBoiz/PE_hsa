"""Hàm dịch vụ CÔNG KHAI của hộp Yêu cầu (E3, §65) — miền khác chỉ gọi các hàm ở đây.

    tao()                — tạo yêu cầu (học viên, phụ huynh qua link, nhân sự)
    tra_loi()            — trả lời / ghi chú nội bộ
    chuyen_trang_thai()  — MỘT hàm cho mọi lần đổi trạng thái, theo `loai.CHUYEN`
    giao()               — giao / chuyển tiếp người xử lý
    phan_loai()          — học vụ đổi loại một yêu cầu hỗ trợ (bảng TopHSA dòng 11)
    duyet()              — duyệt loại thay đổi = THỰC THI trong cùng một giao dịch
    pham_vi_yeu_cau()    — ai thấy yêu cầu nào (MỘT nguồn cho danh sách, chi tiết, ghi)

Luật chung: mọi thay đổi ghi một dòng `yeu_cau_su_kien`; việc phụ (thông báo, xoá đệm
quyền môn) chạy SAU commit (`gui_sau_commit`, `transaction.on_commit`); yêu cầu ngoài phạm
vi → `KhongThay` (view trả 404 — không lộ yêu cầu có tồn tại).
"""
import json
from dataclasses import dataclass
from datetime import date

from django.db import transaction

from common import audit
from common.clock import local_now
from common.db import q, q1, x
from common.permissions import (
    ROLE_ACADEMIC,
    ROLE_ADMIN,
    ROLE_ASSISTANT,
    ROLE_STUDENT,
    ROLE_TEACHER,
    can_see_class,
    is_academic,
    is_admin,
    is_assistant,
    is_teacher,
    visible_class_ids,
)
from notifications.gui import gui_sau_commit
from teaching.nguoi_buoi import thuoc_buoi
from yeu_cau import loai as L

VAI_PHU_HUYNH = 'Phụ huynh'
LOAI_THONG_BAO = 'yeu_cau'
DONG = ('da_xong', 'tu_choi', 'da_huy')


class LoiYeuCau(Exception):
    """Từ chối kèm mã HTTP và câu cho người dùng. Ném trong giao dịch → cuộn lại."""

    def __init__(self, ma, cau):
        super().__init__(cau)
        self.ma = ma
        self.cau = cau


class KhongThay(LoiYeuCau):
    def __init__(self):
        super().__init__(404, 'Không tìm thấy yêu cầu này.')


@dataclass
class NguoiLam:
    """Ai đang làm: một tài khoản (`user`) hoặc phụ huynh cầm link (`link`)."""
    user: object = None
    link: dict = None

    @property
    def id(self):
        return getattr(self.user, 'id', None)

    @property
    def vai(self):
        return VAI_PHU_HUYNH if self.link else getattr(self.user, 'role', None)

    @property
    def ten(self):
        """Tên CHÉP vào `yeu_cau_su_kien.actor_ten` — mọi người thấy yêu cầu đều đọc được, kể cả
        trợ giảng. Không lấy email thay tên (soát 26/09/2026): em chưa có tên thì bản đầu chép
        email của em vào lịch sử, trợ giảng đọc được liên lạc của em."""
        if self.link:
            return VAI_PHU_HUYNH
        return getattr(self.user, 'name', None) or ('#%s' % self.id if self.id else '—')

    @property
    def la_duyet(self):
        return not self.link and (is_admin(self.user) or is_academic(self.user))

    @property
    def la_nhan_su(self):
        u = self.user
        return not self.link and (is_admin(u) or is_academic(u) or is_teacher(u) or is_assistant(u))

    @property
    def nguon(self):
        if self.link:
            return 'phu_huynh'
        return {ROLE_STUDENT: 'hoc_vien', ROLE_ASSISTANT: 'tro_giang', ROLE_TEACHER: 'giang_vien',
                ROLE_ACADEMIC: 'hoc_vu', ROLE_ADMIN: 'hoc_vu'}.get(self.vai)


# ── Phạm vi ──────────────────────────────────────────────────────────────────

def pham_vi_yeu_cau(user=None, link=None):
    """`(sql, params, xem_noi_bo)` — điều kiện trên bí danh `y` của bảng `yeu_cau`.

    - học vụ / quản trị: mọi yêu cầu;
    - GV / TG: loại gắn lớp trong `visible_class_ids` + việc giao cho mình + việc mình tạo,
      KHÔNG BAO GIỜ `ht_tai_khoan`;
    - học viên: CHỈ yêu cầu em tự gửi; không thấy ghi chú nội bộ;
    - phụ huynh (qua link): CHỈ yêu cầu gửi qua CHÍNH link ấy; không thấy nội bộ;
    - ai khác: không gì cả.

    Soát 26/09/2026 — hai chỗ bản đầu rộng hơn quyết định:
    · học viên từng thấy mọi yêu cầu có `hoc_vien_id` là mình, tức cả trợ giảng "báo lên" về
      em ("em không phản hồi"), cả điều phụ huynh nhờ trung tâm để ý, cả lượt giảng viên xin
      thay đổi cho em. "Của mình" = mình GỬI (`nguoi_tao`).
    · phụ huynh từng thấy mọi yêu cầu nguồn phụ huynh của em, qua MỌI link — link thứ hai (bố /
      mẹ, kỳ báo cáo khác) đọc được trả lời gửi cho link thứ nhất. Lời giao việc: danh sách
      trên tờ = yêu cầu "đã gửi qua link ấy".
    """
    if link is not None:
        return ("y.link_id = %s AND y.nguon = 'phu_huynh'", [link['id']], False)
    if is_admin(user) or is_academic(user):
        return ('TRUE', [], True)
    if is_teacher(user) or is_assistant(user):
        return ("y.loai <> 'ht_tai_khoan' AND (y.class_id = ANY(%s) OR y.nguoi_xu_ly = %s "
                'OR y.nguoi_tao = %s)', [visible_class_ids(user), user.id, user.id], True)
    if user is not None and getattr(user, 'is_authenticated', False):
        return ('y.nguoi_tao = %s', [user.id], False)
    return ('FALSE', [], False)


def _pham_vi(nguoi):
    return pham_vi_yeu_cau(nguoi.user, nguoi.link)


_COT = '''y.*, hv.name AS hv_ten, hv.email AS hv_email, c.name AS lop_ten,
          s.starts_at AS buoi_luc, nt.name AS nt_ten, nx.name AS nx_ten, nx.role AS nx_vai,
          nd.name AS nd_ten'''
_TU = '''FROM yeu_cau y
         LEFT JOIN users hv ON hv.id = y.hoc_vien_id
         LEFT JOIN classes c ON c.id = y.class_id
         LEFT JOIN class_sessions s ON s.id = y.session_id
         LEFT JOIN users nt ON nt.id = y.nguoi_tao
         LEFT JOIN users nx ON nx.id = y.nguoi_xu_ly
         LEFT JOIN users nd ON nd.id = y.nguoi_duyet'''


def _json(v):
    return json.loads(v) if isinstance(v, str) else v


def _chuan(yc):
    """jsonb đi qua con trỏ thô của Django là CHUỖI — đổi về dict một chỗ."""
    yc['du_lieu'] = _json(yc['du_lieu']) or {}
    yc['thuc_thi'] = _json(yc['thuc_thi'])
    return yc


def _doc(nguoi, yc_id, khoa=False):
    """Đọc MỘT yêu cầu trong phạm vi của `nguoi` (khoá dòng nếu `khoa`). Ngoài phạm vi → KhongThay."""
    dk, ts, _ = _pham_vi(nguoi)
    if khoa:
        # Khoá riêng dòng `yeu_cau` — FOR UPDATE trên LEFT JOIN không khoá được phía rỗng.
        if not q1('SELECT id FROM yeu_cau WHERE id = %s FOR UPDATE', (yc_id,)):
            raise KhongThay()
    yc = q1('SELECT ' + _COT + ' ' + _TU + ' WHERE y.id = %s AND (' + dk + ')', [yc_id] + ts)
    if not yc:
        raise KhongThay()
    return _chuan(yc)


# ── Dựng phản hồi ───────────────────────────────────────────────────────────

def _iso(v):
    return v.isoformat() if v else None


def _nguoi_json(i, ten):
    return {'id': i, 'ten': ten} if i else None


def _du_lieu_cho(nguoi, du_lieu):
    d = dict(du_lieu or {})
    if nguoi.link is None and is_assistant(nguoi.user):
        for k in L.LIEN_LAC_PH:
            d.pop(k, None)
    return d


def co_the(nguoi, yc):
    """Cờ năng lực theo đối tượng — nút trên màn đọc cờ này, không tự đoán."""
    tt, loai = yc['trang_thai'], yc['loai']
    la_tao = _la_nguoi_tao(nguoi, yc)

    def duoc(den):
        ai = L.ai_duoc_chuyen(loai, tt, den)
        return ((ai == L.NHAN_SU and nguoi.la_nhan_su) or (ai == L.DUYET and nguoi.la_duyet)
                or (ai == L.NGUOI_TAO and la_tao))

    thay_doi = L.la_thay_doi(loai)
    return {
        'traLoi': tt not in DONG and (nguoi.la_nhan_su or la_tao),
        'ghiChu': nguoi.la_nhan_su,
        'nhan': duoc('dang_xu_ly') and tt == 'moi',
        'moLai': duoc('dang_xu_ly') and tt in DONG,
        'xong': duoc('da_xong'),
        'tuChoi': duoc('tu_choi'),
        'huy': duoc('da_huy'),
        'duyet': thay_doi and nguoi.la_duyet and duoc('da_duyet'),
        'giao': nguoi.la_duyet and tt not in DONG,
        'chuyenTiep': nguoi.la_nhan_su and tt not in DONG,
        'phanLoai': nguoi.la_duyet and tt not in DONG and loai in L.PHAN_LOAI_DUOC,
    }


def _ten_em(nguoi, yc):
    """Tên em của yêu cầu. Em chưa có tên: chỉ học vụ / quản trị đọc email thay tên — bản đầu
    lấy email cho mọi người, trợ giảng đọc được liên lạc của em (soát 26/09/2026)."""
    if not yc['hoc_vien_id']:
        return None
    return yc['hv_ten'] or (yc['hv_email'] if nguoi.la_duyet else 'Học viên #%d' % yc['hoc_vien_id'])


def dung(nguoi, yc, su_kien=None):
    """Một yêu cầu → JSON cho `nguoi` (ẩn nội bộ / liên lạc phụ huynh theo vai)."""
    thong_tin = L.LOAI[yc['loai']]
    ra = {
        'id': yc['id'], 'loai': yc['loai'], 'loaiNhan': thong_tin['nhan'], 'nhom': thong_tin['nhom'],
        'canDuyet': L.la_thay_doi(yc['loai']),
        'trangThai': yc['trang_thai'], 'trangThaiNhan': L.NHAN_TRANG_THAI[yc['trang_thai']],
        'nguon': yc['nguon'], 'tieuDe': yc['tieu_de'], 'noiDung': yc['noi_dung'],
        'duLieu': _du_lieu_cho(nguoi, yc['du_lieu']), 'ketQua': yc['ket_qua'],
        'hocVien': _nguoi_json(yc['hoc_vien_id'], _ten_em(nguoi, yc)),
        'lop': _nguoi_json(yc['class_id'], yc['lop_ten']),
        'buoi': {'id': yc['session_id'], 'luc': _iso(yc['buoi_luc'])} if yc['session_id'] else None,
        'nguoiTao': (_nguoi_json(yc['nguoi_tao'], yc['nt_ten'])
                     or ({'id': None, 'ten': VAI_PHU_HUYNH} if yc['nguon'] == 'phu_huynh' else None)),
        'nguoiXuLy': _nguoi_json(yc['nguoi_xu_ly'], yc['nx_ten']),
        'nguoiDuyet': _nguoi_json(yc['nguoi_duyet'], yc['nd_ten']),
        'duyetLuc': _iso(yc['duyet_luc']),
        'createdAt': _iso(yc['created_at']), 'updatedAt': _iso(yc['updated_at']),
        'closedAt': _iso(yc['closed_at']),
    }
    if nguoi.la_nhan_su:
        ra['thucThi'] = yc['thuc_thi']
        ra['coThe'] = co_the(nguoi, yc)
    else:
        ra['coThe'] = {k: v for k, v in co_the(nguoi, yc).items() if k in ('traLoi', 'huy')}
    if su_kien is not None:
        ra['suKien'] = su_kien
    return ra


def _nhan_moc(kieu, ma):
    """Nhãn người đọc của `tu` / `den`: mã trạng thái / mã loại → chữ ở `loai.py` (MỘT nguồn nhãn
    cho mọi màn); giao / chuyển tiếp đã chép sẵn TÊN người nên giữ nguyên."""
    if ma is None:
        return None
    if kieu == 'phan_loai':
        return L.LOAI.get(ma, {}).get('nhan', ma)
    return L.NHAN_TRANG_THAI.get(ma, ma)


def su_kien_cua(nguoi, yc_id):
    _, _, xem_noi_bo = _pham_vi(nguoi)
    rows = q('SELECT * FROM yeu_cau_su_kien WHERE yeu_cau_id = %s'
             + ('' if xem_noi_bo else ' AND NOT noi_bo') + ' ORDER BY id', (yc_id,))
    return [{'id': r['id'], 'kieu': r['kieu'], 'noiBo': r['noi_bo'],
             'ai': {'id': r['actor_id'] if xem_noi_bo else None, 'ten': r['actor_ten'],
                    'vai': r['actor_vai']},
             'tu': r['tu'], 'den': r['den'],
             'tuNhan': _nhan_moc(r['kieu'], r['tu']), 'denNhan': _nhan_moc(r['kieu'], r['den']),
             'noiDung': r['noi_dung'], 'luc': _iso(r['created_at'])}
            for r in rows]


def chi_tiet(nguoi, yc_id):
    yc = _doc(nguoi, yc_id)
    return dung(nguoi, yc, su_kien_cua(nguoi, yc_id))


def danh_sach(nguoi, *, loai=None, trang_thai=None, class_id=None, cua_toi=False, mo=False, tran=200):
    dk, ts, _ = _pham_vi(nguoi)
    them, ts2 = [], []
    if loai:
        them.append('y.loai = %s')
        ts2.append(loai)
    if trang_thai:
        them.append('y.trang_thai = %s')
        ts2.append(trang_thai)
    if mo:
        them.append('y.trang_thai = ANY(%s)')
        ts2.append(list(L.MO))
    if class_id:
        them.append('y.class_id = %s')
        ts2.append(class_id)
    if cua_toi and nguoi.id:
        them.append('y.nguoi_xu_ly = %s')
        ts2.append(nguoi.id)
    rows = q('SELECT ' + _COT + ' ' + _TU + ' WHERE (' + dk + ')'
             + ''.join(' AND ' + t for t in them)
             + ' ORDER BY (y.trang_thai = ANY(%s)) DESC, y.updated_at DESC LIMIT %s',
             ts + ts2 + [list(L.MO), tran])
    return [dung(nguoi, _chuan(r)) for r in rows]


# ── Ghi ─────────────────────────────────────────────────────────────────────

def _ghi_su_kien(yc_id, nguoi, kieu, *, noi_dung=None, tu=None, den=None, noi_bo=False):
    x('''INSERT INTO yeu_cau_su_kien (yeu_cau_id, kieu, noi_bo, actor_id, actor_ten, actor_vai,
                                      tu, den, noi_dung, created_at)
         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
      (yc_id, kieu, noi_bo, nguoi.id, nguoi.ten, nguoi.vai, tu, den, noi_dung, local_now()))


def _audit(request, nguoi, hanh_dong, yc, tom_tat, chi_tiet=None):
    audit.record(request, hanh_dong, target_type='yeu_cau', target_id=yc['id'],
                 target_label=yc['tieu_de'][:120], summary=tom_tat,
                 detail=dict({'loai': yc['loai'], 'hocVienId': yc['hoc_vien_id'],
                              'classId': yc['class_id']}, **(chi_tiet or {})),
                 actor=nguoi.user if nguoi.user is not None else None)


def _la_nguoi_tao(nguoi, yc):
    if nguoi.link is not None:
        return yc['nguon'] == 'phu_huynh' and yc['link_id'] == nguoi.link['id']
    return nguoi.id is not None and yc['nguoi_tao'] == nguoi.id


def _chu(v, tran, ten, bat_buoc=False):
    s = str(v or '').strip()
    if bat_buoc and not s:
        raise LoiYeuCau(400, 'Cần %s.' % ten)
    if len(s) > tran:
        raise LoiYeuCau(400, '%s tối đa %d ký tự.' % (ten[:1].upper() + ten[1:], tran))
    return s or None


def _so(v):
    if v in (None, ''):
        return None
    try:
        return int(v)
    except (TypeError, ValueError) as e:
        raise LoiYeuCau(400, 'Mã không hợp lệ.') from e


def _lam_sach_du_lieu(du_lieu):
    """Chỉ giữ khoá đã biết — `du_lieu` hiện ra trên màn nhân sự, không nhận rác tuỳ ý."""
    d = du_lieu if isinstance(du_lieu, dict) else {}
    ra = {}
    if d.get('den_lop_id') not in (None, ''):
        ra['den_lop_id'] = _so(d['den_lop_id'])
    if d.get('den_ngay') not in (None, ''):
        try:
            ra['den_ngay'] = date.fromisoformat(str(d['den_ngay'])[:10]).isoformat()
        except ValueError as e:
            raise LoiYeuCau(400, 'Ngày phải ở dạng YYYY-MM-DD.') from e
    for k, (tran, nhan) in L.CHU_DU_LIEU.items():
        if d.get(k) not in (None, ''):
            ra[k] = _chu(d[k], tran, nhan)
    for k in L.CO_DU_LIEU:
        if d.get(k) is True:
            ra[k] = True
    return ra


def _lop_dang_hoc(uid):
    return [r['class_id'] for r in q('SELECT class_id FROM class_members WHERE user_id = %s '
                                     'AND left_at IS NULL ORDER BY class_id', (uid,))]


def _tung_hoc(uid, class_id):
    return bool(q1('SELECT 1 AS c FROM class_members WHERE user_id = %s AND class_id = %s LIMIT 1',
                   (uid, class_id)))


def _du_buoi(uid, session_id):
    """Em ``uid`` có thuộc buổi ``session_id`` không (BUỔI BÙ, V-g / §62e).

    "Có trong lớp" KHÔNG đủ: buổi bù chỉ vài em, mà một buổi bù cho hai em thì
    26 em còn lại chưa từng dự. Hỏi đúng bằng `teaching.nguoi_buoi.thuoc_buoi`,
    cùng mệnh đề với lịch, học phí, tờ phụ huynh và §72 — một chỗ định nghĩa
    "ai thuộc buổi", không có bản thứ hai để lệch.

    Thứ tự tham số là cái bẫy: chuỗi `thuoc_buoi` sinh ra có ``uid`` đứng TRƯỚC
    ``sid``, nên truyền ``(uid, session_id)`` chứ không phải ngược lại.
    """
    return bool(q1('SELECT 1 AS c WHERE ' + thuoc_buoi('%s', '%s'), (uid, session_id)))


def _nguoi_nhan_khi_tao(yc, nguoi):
    """Ai được báo khi có yêu cầu mới."""
    nhom = L.nhom(yc['loai'])
    ids = []
    if nhom in (L.HOI_DAP, L.BAO_LOI, L.BAO_CAO) and yc['class_id']:
        lop = q1('SELECT teacher_id FROM classes WHERE id = %s', (yc['class_id'],))
        if lop and lop['teacher_id']:
            ids.append(lop['teacher_id'])
        if nhom != L.BAO_CAO:
            ids += [r['user_id'] for r in q(
                'SELECT m.user_id FROM class_members m JOIN users u ON u.id = m.user_id '
                'WHERE m.class_id = %s AND m.left_at IS NULL AND u.role = %s',
                (yc['class_id'], ROLE_ASSISTANT))]
    if nhom in (L.HO_TRO, L.THAY_DOI) or not ids or (nhom == L.BAO_CAO and nguoi.vai == ROLE_TEACHER):
        ids += [r['id'] for r in q("SELECT id FROM users WHERE role = %s "
                                   "AND COALESCE(status, 'active') = 'active'", (ROLE_ACADEMIC,))]
    return [i for i in ids if i != nguoi.id]


def tao(nguoi, *, loai, tieu_de, noi_dung=None, class_id=None, session_id=None, hoc_vien_id=None,
        du_lieu=None, request=None):
    """Tạo một yêu cầu. Trả JSON của yêu cầu vừa tạo. Ném `LoiYeuCau` khi không hợp lệ."""
    nguon = nguoi.nguon
    if nguon is None:
        raise LoiYeuCau(403, 'Tài khoản này không gửi được yêu cầu.')
    if loai not in L.LOAI:
        raise LoiYeuCau(400, 'Loại yêu cầu không hợp lệ.')
    if loai not in L.TAO_DUOC[nguon]:
        raise LoiYeuCau(400, 'Bạn không gửi được loại yêu cầu "%s".' % L.LOAI[loai]['nhan'])
    tieu_de = _chu(tieu_de, L.TRAN_TIEU_DE, 'tiêu đề', bat_buoc=True)
    noi_dung = _chu(noi_dung, L.TRAN_NOI_DUNG, 'nội dung')
    du_lieu = _lam_sach_du_lieu(du_lieu)
    class_id, session_id, hoc_vien_id = _so(class_id), _so(session_id), _so(hoc_vien_id)
    thong_tin = L.LOAI[loai]

    if nguon == 'phu_huynh':
        hoc_vien_id, class_id = nguoi.link['user_id'], nguoi.link['class_id']
    elif nguon == 'hoc_vien':
        hoc_vien_id = nguoi.id
        if class_id is None and thong_tin.get('can_lop') and not session_id:
            dang = _lop_dang_hoc(nguoi.id)
            if len(dang) == 1:
                class_id = dang[0]
        if class_id is not None and not _tung_hoc(nguoi.id, class_id):
            raise LoiYeuCau(404, 'Em không học lớp này.')
        if class_id is not None and loai != 'tt_hoc_lai' and class_id not in _lop_dang_hoc(nguoi.id):
            raise LoiYeuCau(400, 'Em không còn học lớp này.')
    else:
        if class_id is not None and not can_see_class(nguoi.user, class_id):
            raise LoiYeuCau(404, 'Không tìm thấy lớp này.')

    if session_id is not None:
        buoi = q1('SELECT id, class_id FROM class_sessions WHERE id = %s', (session_id,))
        if not buoi or (class_id is not None and buoi['class_id'] != class_id):
            raise LoiYeuCau(404, 'Không tìm thấy buổi học này.')
        class_id = buoi['class_id']
        if nguon == 'hoc_vien' and not _tung_hoc(nguoi.id, class_id):
            raise LoiYeuCau(404, 'Không tìm thấy buổi học này.')
        # Buổi BÙ: ở trong lớp chưa đủ, phải có tên trong buổi ấy. 404 chứ không 403 —
        # cùng câu với "buổi của lớp khác", để không lộ buổi bù của bạn khác có tồn tại.
        if nguon == 'hoc_vien' and not _du_buoi(nguoi.id, session_id):
            raise LoiYeuCau(404, 'Không tìm thấy buổi học này.')
        if nguon not in ('hoc_vien', 'phu_huynh') and not can_see_class(nguoi.user, class_id):
            raise LoiYeuCau(404, 'Không tìm thấy buổi học này.')
    if thong_tin.get('can_buoi') and session_id is None:
        raise LoiYeuCau(400, 'Chọn buổi học có bản ghi bị lỗi.')
    if thong_tin.get('can_lop') and class_id is None:
        raise LoiYeuCau(400, 'Chọn lớp.')
    if L.la_thay_doi(loai) and hoc_vien_id is None:
        raise LoiYeuCau(400, 'Chọn học viên.')
    if hoc_vien_id is not None and nguon not in ('hoc_vien', 'phu_huynh'):
        em = q1('SELECT id, role FROM users WHERE id = %s', (hoc_vien_id,))
        if not em or em['role'] != ROLE_STUDENT:
            raise LoiYeuCau(404, 'Không tìm thấy học viên này.')
        if class_id is not None and not _tung_hoc(hoc_vien_id, class_id):
            raise LoiYeuCau(400, 'Em này không học lớp đã chọn.')
        # Nhân sự gõ hộ em cũng phải qua cùng hàng rào buổi bù: không thì hàng rào ở
        # màn học viên chỉ là một cửa, còn cửa kia vẫn để ngỏ cho đúng dòng dữ liệu ấy.
        if session_id is not None and not _du_buoi(hoc_vien_id, session_id):
            raise LoiYeuCau(400, 'Em này không dự buổi học đã chọn.')
        if class_id is None and not nguoi.la_duyet:
            raise LoiYeuCau(400, 'Chọn lớp.')

    with transaction.atomic():
        if nguon == 'phu_huynh':
            # Khoá dòng link: hai lượt gửi cùng lúc không cùng đếm được "còn 1 chỗ".
            q1('SELECT id FROM parent_report_links WHERE id = %s FOR UPDATE', (nguoi.link['id'],))
            n = q1('SELECT count(*) AS n FROM yeu_cau WHERE link_id = %s AND trang_thai = ANY(%s)',
                   (nguoi.link['id'], list(L.MO)))['n']
            if n >= L.TRAN_MO_PHU_HUYNH:
                raise LoiYeuCau(429, 'Đã có %d yêu cầu đang chờ trung tâm xử lý. Vui lòng đợi trung '
                                     'tâm trả lời trước khi gửi thêm.' % L.TRAN_MO_PHU_HUYNH)
        nay = local_now()
        yc = q1('''INSERT INTO yeu_cau (loai, trang_thai, nguon, nguoi_tao, link_id, hoc_vien_id, class_id,
                                        session_id, tieu_de, noi_dung, du_lieu, created_at, updated_at)
                   VALUES (%s, 'moi', %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s) RETURNING *''',
                (loai, nguon, nguoi.id, nguoi.link['id'] if nguoi.link else None, hoc_vien_id, class_id,
                 session_id, tieu_de, noi_dung, json.dumps(du_lieu, ensure_ascii=False), nay, nay))
        _ghi_su_kien(yc['id'], nguoi, 'tao', noi_dung=noi_dung, den='moi')
        _audit(request, nguoi, audit.REQUEST_CREATE, yc,
               'Tạo yêu cầu "%s" (%s).' % (tieu_de, thong_tin['nhan']))
        gui_sau_commit(_nguoi_nhan_khi_tao(yc, nguoi), LOAI_THONG_BAO,
                       'Yêu cầu mới: %s' % thong_tin['nhan'], tieu_de, ref=('yeu_cau', yc['id']))
    return chi_tiet(nguoi, yc['id'])


def _bao_nguoi_gui(yc, nguoi, tieu_de, noi_dung):
    """Báo người gửi (và em, nếu người gửi khác em) — phụ huynh không có tài khoản thì thôi."""
    ids = {i for i in (yc['nguoi_tao'], yc['hoc_vien_id'] if yc['nguon'] == 'hoc_vien' else None) if i}
    ids.discard(nguoi.id)
    gui_sau_commit(ids, LOAI_THONG_BAO, tieu_de, noi_dung, ref=('yeu_cau', yc['id']))


def tra_loi(nguoi, yc_id, noi_dung, *, noi_bo=False, request=None):
    """Trả lời (mọi người trong phạm vi) hoặc ghi chú nội bộ (chỉ nhân sự)."""
    noi_dung = _chu(noi_dung, L.TRAN_NOI_DUNG, 'nội dung', bat_buoc=True)
    with transaction.atomic():
        yc = _doc(nguoi, yc_id, khoa=True)
        la_tao = _la_nguoi_tao(nguoi, yc)
        if noi_bo and not nguoi.la_nhan_su:
            raise LoiYeuCau(403, 'Chỉ nhân sự ghi được ghi chú nội bộ.')
        if not noi_bo:
            if not (nguoi.la_nhan_su or la_tao):
                raise LoiYeuCau(403, 'Bạn không trả lời được yêu cầu này.')
            if yc['trang_thai'] in DONG:
                raise LoiYeuCau(409, 'Yêu cầu đã đóng — không trả lời thêm được.')
        _ghi_su_kien(yc_id, nguoi, 'ghi_chu' if noi_bo else 'tra_loi', noi_dung=noi_dung, noi_bo=noi_bo)
        if not noi_bo and nguoi.la_nhan_su and yc['trang_thai'] == 'moi':
            # Nhân sự trả lời = đã nhận việc.
            x("UPDATE yeu_cau SET trang_thai = 'dang_xu_ly' WHERE id = %s", (yc_id,))
            _ghi_su_kien(yc_id, nguoi, 'trang_thai', tu='moi', den='dang_xu_ly')
        x('UPDATE yeu_cau SET updated_at = %s WHERE id = %s', (local_now(), yc_id))
        if not noi_bo:
            if nguoi.la_nhan_su:
                _bao_nguoi_gui(yc, nguoi, 'Trung tâm đã trả lời: %s' % yc['tieu_de'], noi_dung[:200])
            else:
                nhan = [yc['nguoi_xu_ly']] if yc['nguoi_xu_ly'] else _nguoi_nhan_khi_tao(yc, nguoi)
                gui_sau_commit(nhan, LOAI_THONG_BAO, 'Trả lời mới: %s' % yc['tieu_de'],
                               noi_dung[:200], ref=('yeu_cau', yc_id))
    return chi_tiet(nguoi, yc_id)


def _dat_trang_thai(yc, den, nguoi, *, ket_qua=None, kieu='trang_thai', noi_dung=None):
    dong = den in DONG
    x('''UPDATE yeu_cau SET trang_thai = %s, updated_at = %s,
                            closed_at = CASE WHEN %s THEN %s ELSE NULL END,
                            ket_qua = COALESCE(%s, ket_qua)
         WHERE id = %s''', (den, local_now(), dong, local_now(), ket_qua, yc['id']))
    _ghi_su_kien(yc['id'], nguoi, kieu, tu=yc['trang_thai'], den=den, noi_dung=noi_dung or ket_qua)


def chuyen_trang_thai(nguoi, yc_id, den, *, ket_qua=None, request=None):
    """MỘT hàm cho mọi lần đổi trạng thái (trừ → da_duyet: `duyet()`), theo `loai.CHUYEN`."""
    if den not in L.TRANG_THAI:
        raise LoiYeuCau(400, 'Trạng thái không hợp lệ.')
    if den == L.CHI_QUA_DUYET:
        raise LoiYeuCau(400, 'Duyệt yêu cầu bằng nút Duyệt.')
    ket_qua = _chu(ket_qua, L.TRAN_NOI_DUNG, 'kết quả')
    with transaction.atomic():
        yc = _doc(nguoi, yc_id, khoa=True)
        ai = L.ai_duoc_chuyen(yc['loai'], yc['trang_thai'], den)
        if ai is None:
            raise LoiYeuCau(409, 'Yêu cầu đang "%s" — không chuyển sang "%s" được.'
                                 % (L.NHAN_TRANG_THAI[yc['trang_thai']], L.NHAN_TRANG_THAI[den]))
        duoc = ((ai == L.NGUOI_TAO and _la_nguoi_tao(nguoi, yc)) or (ai == L.NHAN_SU and nguoi.la_nhan_su)
                or (ai == L.DUYET and nguoi.la_duyet))
        if not duoc:
            raise LoiYeuCau(403, 'Bạn không làm được việc này.')
        _dat_trang_thai(yc, den, nguoi, ket_qua=ket_qua, kieu='tu_choi' if den == 'tu_choi' else 'trang_thai')
        hanh_dong = audit.REQUEST_REJECT if den == 'tu_choi' else audit.REQUEST_STATUS
        _audit(request, nguoi, hanh_dong, yc, 'Yêu cầu "%s": %s → %s.'
               % (yc['tieu_de'], L.NHAN_TRANG_THAI[yc['trang_thai']], L.NHAN_TRANG_THAI[den]),
               {'tu': yc['trang_thai'], 'den': den, 'ketQua': ket_qua})
        if not _la_nguoi_tao(nguoi, yc):
            _bao_nguoi_gui(yc, nguoi, 'Yêu cầu "%s": %s' % (yc['tieu_de'], L.NHAN_TRANG_THAI[den]),
                           ket_qua or '')
    return chi_tiet(nguoi, yc_id)


def giao(nguoi, yc_id, nguoi_xu_ly_id, *, ghi_chu=None, request=None):
    """Giao (học vụ) hoặc chuyển tiếp (GV/TG) người xử lý. `None` = trả về học vụ."""
    if not nguoi.la_nhan_su:
        raise LoiYeuCau(403, 'Bạn không làm được việc này.')
    ghi_chu = _chu(ghi_chu, L.TRAN_NOI_DUNG, 'ghi chú')
    dich = _so(nguoi_xu_ly_id)
    with transaction.atomic():
        yc = _doc(nguoi, yc_id, khoa=True)
        if yc['trang_thai'] in DONG:
            raise LoiYeuCau(409, 'Yêu cầu đã đóng.')
        ten_dich = 'học vụ'
        if dich is not None:
            u = q1("SELECT id, name, email, role FROM users WHERE id = %s "
                   "AND COALESCE(status, 'active') = 'active'", (dich,))
            if not u or u['role'] not in (ROLE_ADMIN, ROLE_ACADEMIC, ROLE_TEACHER, ROLE_ASSISTANT):
                raise LoiYeuCau(400, 'Chỉ giao được cho nhân sự.')
            if u['role'] in (ROLE_TEACHER, ROLE_ASSISTANT):
                if yc['loai'] == 'ht_tai_khoan':
                    raise LoiYeuCau(400, 'Hỗ trợ tài khoản do học vụ xử lý.')
                if not yc['class_id'] or not can_see_class(_Tam(u), yc['class_id']):
                    raise LoiYeuCau(400, 'Người này không phụ trách lớp của yêu cầu.')
            ten_dich = u['name'] or u['email']
        tu = yc['nx_ten'] or 'học vụ'
        x('UPDATE yeu_cau SET nguoi_xu_ly = %s, updated_at = %s WHERE id = %s', (dich, local_now(), yc_id))
        kieu = 'giao' if nguoi.la_duyet else 'chuyen_tiep'
        _ghi_su_kien(yc_id, nguoi, kieu, tu=tu, den=ten_dich, noi_dung=ghi_chu, noi_bo=True)
        _audit(request, nguoi, audit.REQUEST_ASSIGN, yc,
               'Giao yêu cầu "%s" cho %s.' % (yc['tieu_de'], ten_dich), {'nguoiXuLy': dich})
        if dich is not None and dich != nguoi.id:
            gui_sau_commit([dich], LOAI_THONG_BAO, 'Yêu cầu được giao cho bạn: %s' % yc['tieu_de'],
                           ghi_chu or '', ref=('yeu_cau', yc_id))
    return chi_tiet(nguoi, yc_id)


def phan_loai(nguoi, yc_id, loai_moi, *, request=None):
    """Học vụ ĐỔI LOẠI một yêu cầu hỗ trợ chưa đóng (bảng TopHSA dòng 11 "phân loại").

    Chỉ trong `loai.PHAN_LOAI_DUOC`; loại mới đòi lớp / buổi thì yêu cầu phải có sẵn. Sang
    "hỗ trợ tài khoản" mà người xử lý là GV / TG → trả về học vụ: phạm vi GV / TG không bao
    giờ gồm loại ấy, để nguyên là giao việc cho người không còn mở được nó."""
    if not nguoi.la_duyet:
        raise LoiYeuCau(403, 'Chỉ học vụ hoặc quản trị viên phân loại được.')
    if loai_moi not in L.PHAN_LOAI_DUOC:
        raise LoiYeuCau(400, 'Chỉ đổi được giữa các loại hỗ trợ và câu hỏi.')
    moi = L.LOAI[loai_moi]
    with transaction.atomic():
        yc = _doc(nguoi, yc_id, khoa=True)
        if yc['trang_thai'] in DONG:
            raise LoiYeuCau(409, 'Yêu cầu đã đóng.')
        if yc['loai'] not in L.PHAN_LOAI_DUOC:
            raise LoiYeuCau(400, 'Loại "%s" không đổi được.' % L.LOAI[yc['loai']]['nhan'])
        if yc['loai'] == loai_moi:
            return chi_tiet(nguoi, yc_id)
        if moi.get('can_lop') and not yc['class_id']:
            raise LoiYeuCau(400, 'Yêu cầu chưa gắn lớp — không đổi sang "%s" được.' % moi['nhan'])
        if moi.get('can_buoi') and not yc['session_id']:
            raise LoiYeuCau(400, 'Yêu cầu chưa gắn buổi học — không đổi sang "%s" được.' % moi['nhan'])
        tra_ve_hoc_vu = loai_moi == 'ht_tai_khoan' and yc['nx_vai'] in (ROLE_TEACHER, ROLE_ASSISTANT)
        x('UPDATE yeu_cau SET loai = %s, updated_at = %s, '
          'nguoi_xu_ly = CASE WHEN %s THEN NULL ELSE nguoi_xu_ly END WHERE id = %s',
          (loai_moi, local_now(), tra_ve_hoc_vu, yc_id))
        _ghi_su_kien(yc_id, nguoi, 'phan_loai', tu=yc['loai'], den=loai_moi)
        _audit(request, nguoi, audit.REQUEST_CLASSIFY, yc,
               'Đổi loại yêu cầu "%s": %s → %s.' % (yc['tieu_de'], L.LOAI[yc['loai']]['nhan'], moi['nhan']),
               {'tu': yc['loai'], 'den': loai_moi})
    return chi_tiet(nguoi, yc_id)


class _Tam:
    """Tài khoản dựng từ một dòng `users` — đủ cho `can_see_class`."""
    is_authenticated = True

    def __init__(self, row):
        self.id, self.role = row['id'], row['role']


def duyet(nguoi, yc_id, tham_so=None, *, ket_qua=None, request=None):
    """DUYỆT = THỰC THI trong MỘT giao dịch (khoá dòng, kiểm trạng thái, chạy việc, ghi người
    duyệt + giờ + sự kiện). Việc hỏng → cuộn lại hết, rồi ghi riêng một sự kiện `loi` nội bộ.
    Duyệt lần hai → 409, không thực thi lại."""
    from yeu_cau import thuc_thi
    if not nguoi.la_duyet:
        raise LoiYeuCau(403, 'Chỉ học vụ hoặc quản trị viên duyệt được.')
    ket_qua = _chu(ket_qua, L.TRAN_NOI_DUNG, 'kết quả')
    try:
        with transaction.atomic():
            yc = _doc(nguoi, yc_id, khoa=True)
            if not L.la_thay_doi(yc['loai']):
                raise LoiYeuCau(400, 'Loại yêu cầu này không cần duyệt.')
            if yc['trang_thai'] in ('da_duyet', 'da_xong') or yc['thuc_thi'] is not None:
                raise LoiYeuCau(409, 'Yêu cầu này đã được duyệt.')
            if L.ai_duoc_chuyen(yc['loai'], yc['trang_thai'], 'da_duyet') != L.DUYET:
                raise LoiYeuCau(409, 'Yêu cầu đang "%s" — không duyệt được.'
                                     % L.NHAN_TRANG_THAI[yc['trang_thai']])
            viec = thuc_thi.thuc_hien(yc, tham_so or {}, request)
            tu_dong = viec.get('cach') == 'tu_dong'
            nay = local_now()
            den = 'da_xong' if tu_dong else 'da_duyet'
            x('''UPDATE yeu_cau SET trang_thai = %s, nguoi_duyet = %s, duyet_luc = %s,
                                    thuc_thi = %s::jsonb, ket_qua = COALESCE(%s, ket_qua),
                                    updated_at = %s, closed_at = %s
                 WHERE id = %s''',
              (den, nguoi.id, nay, json.dumps(viec, ensure_ascii=False, default=str), ket_qua, nay,
               nay if tu_dong else None, yc_id))
            _ghi_su_kien(yc_id, nguoi, 'duyet', tu=yc['trang_thai'], den='da_duyet', noi_dung=ket_qua)
            _ghi_su_kien(yc_id, nguoi, 'thuc_thi', noi_dung=viec.get('mo_ta'))
            if tu_dong:
                _ghi_su_kien(yc_id, nguoi, 'trang_thai', tu='da_duyet', den='da_xong')
            _audit(request, nguoi, audit.REQUEST_APPROVE, yc,
                   'Duyệt yêu cầu "%s" (%s). %s' % (yc['tieu_de'], L.LOAI[yc['loai']]['nhan'],
                                                    viec.get('mo_ta') or ''),
                   {'thucThi': viec})
            if yc['hoc_vien_id'] and tu_dong:
                em = yc['hoc_vien_id']
                transaction.on_commit(lambda: _quen_truy_cap(em))
            _bao_nguoi_gui(yc, nguoi, 'Yêu cầu "%s" đã được duyệt' % yc['tieu_de'],
                           viec.get('mo_ta') or ket_qua or '')
    except LoiYeuCau as e:
        if not isinstance(e, KhongThay) and e.ma != 403:
            # Ghi dấu lần duyệt hỏng — giao dịch trên đã cuộn lại, dòng này đứng riêng.
            try:
                _ghi_su_kien(yc_id, nguoi, 'loi', noi_dung='Duyệt không thành: %s' % e.cau, noi_bo=True)
            except Exception:  # noqa: BLE001 — ghi dấu hỏng không che lỗi chính
                pass
        raise
    return chi_tiet(nguoi, yc_id)


def _quen_truy_cap(uid):
    from courses.truy_cap import quen_truy_cap
    quen_truy_cap(uid)


def xem_truoc(nguoi, yc_id, tham_so=None):
    """Việc SẼ làm khi duyệt — không ghi gì."""
    from yeu_cau import thuc_thi
    if not nguoi.la_duyet:
        raise LoiYeuCau(403, 'Chỉ học vụ hoặc quản trị viên duyệt được.')
    yc = _doc(nguoi, yc_id)
    if not L.la_thay_doi(yc['loai']):
        raise LoiYeuCau(400, 'Loại yêu cầu này không cần duyệt.')
    return thuc_thi.xem_truoc(yc, tham_so or {})


def dem_viec(user):
    """Cho "Việc hôm nay": `{choDuyet, mo}` trong phạm vi của `user` — MỘT câu."""
    nguoi = NguoiLam(user=user)
    dk, ts, _ = _pham_vi(nguoi)
    thay_doi = [k for k in L.LOAI if L.la_thay_doi(k)]
    r = q1("SELECT count(*) FILTER (WHERE y.trang_thai IN ('moi', 'dang_xu_ly') "
           'AND y.loai = ANY(%s)) AS cho_duyet, '
           'count(*) FILTER (WHERE y.trang_thai = ANY(%s)) AS mo '
           'FROM yeu_cau y WHERE ' + dk, [thay_doi, list(L.MO)] + ts)
    return {'choDuyet': r['cho_duyet'] if nguoi.la_duyet else 0, 'mo': r['mo']}
