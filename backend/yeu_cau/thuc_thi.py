"""Việc hệ thống làm khi DUYỆT một yêu cầu thay đổi (E3) — chạy BÊN TRONG giao dịch của
`dich_vu.duyet()`, nên việc nào ném `LoiYeuCau` là cả lần duyệt cuộn lại.

Mọi việc đi qua hàm sẵn có của miền lớp học (luật S4 — `yeu_cau` không ghi thẳng bảng của
miền khác):
- chuyển lớp / chuyển môn → `teaching/chuyen_lop.py::ChuyenLopView._chuyen` (giữ trần lớp gia
  sư, kiểm ngày, ghi `transferred_to`, nhật ký `class.member.transfer`);
- bảo lưu → `teaching/roi_lop.py::roi_lop(..., 'reserved', reserve_until=…)`;
- huỷ khoá → `roi_lop(..., 'dropped')`;
- học lại → `AdminClassMembersView._ghi_thanh_vien` (giữ trần gia sư);
- chuyển lịch / học bù / nghỉ học → v1 CHỈ ghi quyết định (`{"cach": "tay"}`): học vụ tự làm
  trên màn Buổi học (tạo buổi bù, đổi lịch, điểm danh "có phép").

Xoá đệm quyền môn: `dich_vu.duyet()` hẹn `quen_truy_cap` SAU commit.
"""
from datetime import date

from common.clock import local_now, local_today
from common.db import q1
from common.permissions import ROLE_STUDENT
from yeu_cau import loai as L
from yeu_cau.dich_vu import LoiYeuCau

VIEC_TAY = {
    'tt_chuyen_lich': 'Học vụ đổi lịch cho em trên màn Buổi học.',
    'tt_hoc_bu': 'Học vụ tạo buổi bù (hoặc xếp em vào buổi bù sẵn có) trên màn Buổi học.',
    'tt_nghi_hoc': 'Học vụ ghi "có phép" cho các buổi em nghỉ trên sổ điểm danh.',
}


#: Lỗi của VIỆC khi duyệt không bao giờ là 404: đường duyệt trả 404 đọc thành "không có yêu cầu
#: này" (màn chặn `khong-thay`), trong khi yêu cầu có thật — chỉ việc không làm được. Bản đầu
#: chuyển nguyên 404 của `ChuyenLopView._chuyen` ("Em không đang học lớp …") ra ngoài (soát 26/09).
MA_VIEC_HONG = 409


def _em(yc):
    em = q1('SELECT id, name, email, role FROM users WHERE id = %s', (yc['hoc_vien_id'],))
    if not em:
        raise LoiYeuCau(MA_VIEC_HONG, 'Không tìm thấy học viên của yêu cầu.')
    if em['role'] != ROLE_STUDENT:
        raise LoiYeuCau(400, 'Tài khoản của yêu cầu không phải học viên.')
    return em


def _lop(class_id, ten='lớp'):
    lop = q1('SELECT c.id, c.name, c.status, c.class_type, c.course_id, co.title AS course_title '
             'FROM classes c LEFT JOIN courses co ON co.id = c.course_id WHERE c.id = %s', (class_id,))
    if not lop:
        raise LoiYeuCau(MA_VIEC_HONG, 'Không tìm thấy %s.' % ten)
    return lop


def _den_lop(yc, tham_so):
    raw = tham_so.get('den_lop_id')
    if raw in (None, ''):
        raw = (yc['du_lieu'] or {}).get('den_lop_id')
    if raw in (None, ''):
        raise LoiYeuCau(400, 'Chọn lớp chuyển tới.')
    try:
        return int(raw)
    except (TypeError, ValueError) as e:
        raise LoiYeuCau(400, 'Chọn lớp chuyển tới.') from e


def _den_ngay(yc, tham_so):
    raw = tham_so.get('den_ngay')
    if raw in (None, ''):
        raw = (yc['du_lieu'] or {}).get('den_ngay')
    if raw in (None, ''):
        return None
    try:
        d = date.fromisoformat(str(raw)[:10])
    except ValueError as e:
        raise LoiYeuCau(400, 'Ngày bảo lưu phải ở dạng YYYY-MM-DD.') from e
    if d < local_today():
        raise LoiYeuCau(400, 'Ngày hết bảo lưu không được ở quá khứ.')
    return d


def _ten(r):
    return r['name'] or r['email']


def _dang_hoc(em_id, class_id):
    return bool(q1('SELECT 1 AS c FROM class_members WHERE class_id = %s AND user_id = %s '
                   'AND left_at IS NULL', (class_id, em_id)))


def xem_truoc(yc, tham_so):
    """`{cach, moTa, canhBao}` — việc sẽ làm, không ghi gì. Lỗi dữ liệu → `canhBao`, không ném."""
    loai = yc['loai']
    if L.LOAI[loai].get('viec') == 'tay':
        return {'cach': 'tay', 'moTa': 'Chỉ ghi quyết định. ' + VIEC_TAY[loai], 'canhBao': []}
    canh_bao = []
    try:
        em = _em(yc)
        lop = _lop(yc['class_id']) if yc['class_id'] else None
        if loai in ('tt_chuyen_lop', 'tt_chuyen_mon'):
            den = _lop(_den_lop(yc, tham_so), 'lớp chuyển tới')
            mo_ta = 'Chuyển %s từ lớp "%s" sang lớp "%s"%s.' % (
                _ten(em), lop['name'] if lop else '?', den['name'],
                ' (môn %s)' % (den['course_title'] or 'cả ba môn') if den['course_id'] != (lop or {}).get('course_id')
                else '')
            if den['class_type'] == 'gia_su':
                canh_bao.append('Lớp gia sư — tối đa 3 em; đủ thì duyệt sẽ bị từ chối.')
        elif loai == 'tt_bao_luu':
            d = _den_ngay(yc, tham_so)
            mo_ta = 'Cho %s rời lớp "%s" với lý do bảo lưu%s. Em mất quyền vào môn của lớp.' % (
                _ten(em), lop['name'], ' tới %s' % d.strftime('%d/%m/%Y') if d else '')
        elif loai == 'tt_huy_khoa':
            mo_ta = 'Cho %s rời lớp "%s" với lý do bỏ giữa chừng. Em mất quyền vào môn của lớp.' % (
                _ten(em), lop['name'])
        else:  # tt_hoc_lai
            mo_ta = 'Xếp %s vào lại lớp "%s".' % (_ten(em), lop['name'])
            if _dang_hoc(em['id'], lop['id']):
                canh_bao.append('Em đang học lớp này rồi.')
        if lop and loai in ('tt_chuyen_lop', 'tt_chuyen_mon', 'tt_bao_luu', 'tt_huy_khoa') \
                and not _dang_hoc(em['id'], lop['id']):
            canh_bao.append('Em không còn đang học lớp "%s".' % lop['name'])
    except LoiYeuCau as e:
        return {'cach': 'tu_dong', 'moTa': None, 'canhBao': [e.cau]}
    return {'cach': 'tu_dong', 'moTa': mo_ta, 'canhBao': canh_bao}


def thuc_hien(yc, tham_so, request):
    """Làm việc của yêu cầu. Trả dict ghi vào `yeu_cau.thuc_thi` (`cach`, `mo_ta`, …)."""
    from teaching.chuyen_lop import ChuyenLopView, _Huy
    from teaching.roi_lop import roi_lop
    from teaching.views import AdminClassMembersView

    loai = yc['loai']
    if L.LOAI[loai].get('viec') == 'tay':
        return {'cach': 'tay', 'mo_ta': 'Đã duyệt. ' + VIEC_TAY[loai]}
    em = _em(yc)
    if not yc['class_id']:
        raise LoiYeuCau(400, 'Yêu cầu chưa gắn lớp.')
    lop = _lop(yc['class_id'])
    ghi_chu = 'Theo yêu cầu #%d' % yc['id']

    if loai in ('tt_chuyen_lop', 'tt_chuyen_mon'):
        den_id = _den_lop(yc, tham_so)
        if den_id == lop['id']:
            raise LoiYeuCau(400, 'Lớp chuyển tới phải khác lớp em đang học.')
        try:
            kq = ChuyenLopView._chuyen(request, lop['id'], den_id, em, _ten(em), local_now(), ghi_chu)
        except _Huy as h:
            ma = h.phan_hoi.status_code
            raise LoiYeuCau(MA_VIEC_HONG if ma == 404 else ma,
                            h.phan_hoi.data.get('error') or 'Không chuyển được.') from h
        den = _lop(den_id)
        return {'cach': 'tu_dong', 'viec': 'chuyen_lop', 'tuLop': lop['id'], 'denLop': den_id,
                'tuLuot': kq['fromMemberId'], 'denLuot': kq['toMemberId'], 'canhBao': kq['warnings'],
                'mo_ta': 'Đã chuyển %s từ lớp "%s" sang lớp "%s".' % (_ten(em), lop['name'], den['name'])}

    if loai in ('tt_bao_luu', 'tt_huy_khoa'):
        bao_luu = loai == 'tt_bao_luu'
        d = _den_ngay(yc, tham_so) if bao_luu else None
        luot = roi_lop(request, lop['id'], em['id'], 'reserved' if bao_luu else 'dropped', reserve_until=d)
        if luot is None:
            raise LoiYeuCau(409, 'Em không đang học lớp "%s".' % lop['name'])
        ra = {'cach': 'tu_dong', 'viec': 'bao_luu' if bao_luu else 'huy_khoa', 'lop': lop['id'], 'luot': luot}
        if bao_luu:
            ra['denNgay'] = d.isoformat() if d else None
            ra['mo_ta'] = 'Đã bảo lưu cho %s ở lớp "%s"%s.' % (
                _ten(em), lop['name'], ' tới %s' % d.strftime('%d/%m/%Y') if d else '')
        else:
            ra['mo_ta'] = 'Đã huỷ khoá của %s ở lớp "%s".' % (_ten(em), lop['name'])
        return ra

    # tt_hoc_lai
    if lop['status'] == 'cancelled':
        raise LoiYeuCau(400, 'Lớp "%s" đã huỷ — không xếp vào được.' % lop['name'])
    kq = AdminClassMembersView._ghi_thanh_vien(request, lop, em)
    if kq == 'day':
        raise LoiYeuCau(409, 'Lớp gia sư "%s" đã đủ em.' % lop['name'])
    if kq == 'da_co':
        raise LoiYeuCau(409, 'Em đang học lớp "%s" rồi.' % lop['name'])
    return {'cach': 'tu_dong', 'viec': 'hoc_lai', 'lop': lop['id'],
            'mo_ta': 'Đã xếp %s vào lại lớp "%s".' % (_ten(em), lop['name'])}
