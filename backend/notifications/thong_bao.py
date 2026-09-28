"""THÔNG BÁO TRUNG TÂM (§61b, E2) — bảng yêu cầu TopHSA dòng 27 + "Phân hệ thông báo chung".

Đối tượng (`announcements.audience`): lớp (`classIds`), môn (`courseIds`), người chọn tay
(`userIds`, kèm `groupName` chỉ để đặt tên nhóm). Người nhận:

  · lớp / môn: HỌC VIÊN đang học (`left_at IS NULL`), lớp chưa huỷ — trợ giảng cũng là
    thành viên lớp nhưng không phải người nhận "thông báo cho lớp"; lớp không gắn môn
    (`course_id` NULL = cả ba môn) tính cho mọi môn;
  · chọn tay: đúng những người ấy, vai nào cũng được;
  · tài khoản khoá không nhận gì.

GỬI = MỘT giao dịch: đổi trạng thái (chặn gửi hai lần), MỘT INSERT…SELECT vào
`notifications`, MỘT INSERT…SELECT vào `outbox` (email: có địa chỉ, bật `email_notif`,
không phải tài khoản mẫu; dedup `thong_bao:{id}:{em}`). Sau commit hộp thư đi gửi.

Zalo ZNS chỉ gửi được THEO MẪU đã duyệt — thông báo tự do chỉ đi Zalo khi OA đã cấu hình,
và tham số mẫu (`tieu_de`, `noi_dung`) phải khớp mẫu anh Sơn đăng ký (xem báo cáo E2).
"""
import json

from django.db import transaction

from common import zalo
from common.db import q, q1
from courses.truy_cap import BA_MON
from notifications import hop_thu
from teaching.vocab import chi_hoc_vien

LOAI = 'thong_bao'
LINK = '/thong-bao'
TRAN_TIEU_DE = 200
TRAN_NOI_DUNG = 5000

_NHAN = '''
    SELECT u.id FROM users u
     WHERE coalesce(u.status, 'active') <> 'suspended'
       AND (u.id = ANY(%(nguoi)s::int[])
            OR (''' + chi_hoc_vien('u') + ''' AND EXISTS (
                SELECT 1 FROM class_members m JOIN classes c ON c.id = m.class_id
                 WHERE m.user_id = u.id AND m.left_at IS NULL AND c.status <> 'cancelled'
                   AND (m.class_id = ANY(%(lop)s::int[])
                        OR c.course_id = ANY(%(mon)s::text[])
                        OR (c.course_id IS NULL AND cardinality(%(mon)s::text[]) > 0)))))'''


def doi_tuong(raw):
    """Chuẩn hoá `audience` người gửi đưa lên → dict chỉ gồm khoá biết, id là số."""
    raw = raw if isinstance(raw, dict) else {}

    def so(k):
        ra = []
        for v in raw.get(k) or ():
            try:
                ra.append(int(v))
            except (TypeError, ValueError):
                continue
        return sorted(set(ra))
    ra = {'classIds': so('classIds'), 'courseIds': sorted({str(v) for v in raw.get('courseIds') or () if v}),
          'userIds': so('userIds')}
    ten = str(raw.get('groupName') or '').strip()[:100]
    if ten:
        ra['groupName'] = ten
    return ra


def _ts(aud):
    return {'nguoi': aud.get('userIds') or [], 'lop': aud.get('classIds') or [],
            'mon': aud.get('courseIds') or []}


def rong(aud):
    return not (aud.get('userIds') or aud.get('classIds') or aud.get('courseIds'))


def zalo_san_sang():
    """(sẵn sàng, lý do nếu chưa)."""
    if zalo.da_cau_hinh():
        return True, None
    return False, 'Chưa có Zalo OA đã xác thực — thông báo chỉ đi qua chuông và email.'


def xem_truoc(aud, gui_email=False):
    """Đếm người nhận theo kênh, ai thiếu email. Không ghi gì.

    `gui_email` mặc định FALSE (anh Sơn chốt 26/09/2026, quyết định số 2): ô "Gửi kèm
    email" trên màn soạn để TRỐNG, nên bản xem trước phải đếm đúng thứ sắp xảy ra nếu bấm
    Gửi ngay lúc ấy. Mặc định True là một bản xem trước hứa nhiều hơn thứ nó làm."""
    ts = _ts(aud)
    ds = q('''SELECT u.id, u.name, u.email, u.phone, u.is_demo, coalesce(ns.email_notif, 1) AS nhan_thu
                FROM users u LEFT JOIN notification_settings ns ON ns.user_id = u.id
               WHERE u.id IN (''' + _NHAN + ''') ORDER BY u.name, u.id''', ts) if not rong(aud) else []
    co_mail = [r for r in ds if (r['email'] or '').find('@') > 0]
    san_sang, ly_do = zalo_san_sang()
    return {
        'tong': len(ds),
        'chuong': len(ds),
        'email': sum(1 for r in co_mail if r['nhan_thu'] and not r['is_demo']) if gui_email else 0,
        'tatEmail': sum(1 for r in co_mail if not r['nhan_thu']),
        'mau': sum(1 for r in ds if r['is_demo']),
        'thieuEmail': [{'id': r['id'], 'name': r['name']} for r in ds if r not in co_mail][:100],
        'zalo': {'sanSang': san_sang, 'lyDo': ly_do,
                 'coSo': sum(1 for r in ds if (r['phone'] or '').strip() and not r['is_demo'])},
        'danhSach': [{'id': r['id'], 'name': r['name']} for r in ds[:200]],
    }


def tao(tieu_de, noi_dung, aud, gui_email, gui_zalo, nguoi_tao):
    return q1('''INSERT INTO announcements (title, body, audience, send_email, send_zalo, created_by)
                 VALUES (%s, %s, %s::jsonb, %s, %s, %s) RETURNING id''',
              (tieu_de, noi_dung, json.dumps(aud), bool(gui_email), bool(gui_zalo), nguoi_tao))['id']


def gui(aid):
    """Gửi một bản nháp. Trả số người nhận, hoặc None nếu bản ấy không còn là nháp."""
    with transaction.atomic():
        a = q1('''UPDATE announcements SET status = 'sent', sent_at = now()
                   WHERE id = %s AND status = 'draft'
               RETURNING id, title, body, audience, send_email, send_zalo''', (aid,))
        if not a:
            return None
        aud = a['audience'] if isinstance(a['audience'], dict) else json.loads(a['audience'])
        ts = dict(_ts(aud), aid=aid, loai=LOAI, link=LINK, tieu_de=a['title'], noi_dung=a['body'],
                  uu_tien=hop_thu.HANG_LOAT)
        nhan = q('''INSERT INTO notifications (user_id, type, title, body, ref_type, ref_id,
                                               announcement_id, link)
                    SELECT n.id, %(loai)s, %(tieu_de)s, %(noi_dung)s, 'announcement', %(aid)s, %(aid)s, %(link)s
                      FROM (''' + _NHAN + ''') n
                 RETURNING user_id''', ts)
        thu = []
        if a['send_email']:
            thu += [r['id'] for r in q('''
                INSERT INTO outbox (channel, user_id, to_addr, subject, body, source_type,
                                    source_id, dedup_key, priority)
                SELECT 'email', u.id, u.email, %(tieu_de)s,
                       %(noi_dung)s || E'\\n\\nXem ở mục "Thông báo" trên TopHSA.\\n\\n— TopHSA\\n',
                       'announcement', %(aid)s, 'thong_bao:' || %(aid)s || ':' || u.id, %(uu_tien)s
                  FROM users u LEFT JOIN notification_settings ns ON ns.user_id = u.id
                 WHERE u.id IN (''' + _NHAN + ''')
                   AND u.email LIKE '%%@%%' AND coalesce(ns.email_notif, 1) = 1 AND NOT u.is_demo
                 ORDER BY u.id
                ON CONFLICT (dedup_key) DO NOTHING RETURNING id''', ts)]
        if a['send_zalo']:
            thu += [r['id'] for r in q('''
                INSERT INTO outbox (channel, user_id, to_addr, params, source_type, source_id,
                                    dedup_key, priority)
                SELECT 'zalo', u.id, u.phone,
                       jsonb_build_object('zns', jsonb_build_object('tieu_de', %(tieu_de)s::text,
                                                                    'noi_dung', left(%(noi_dung)s::text, 400))),
                       'announcement', %(aid)s, 'thong_bao_zalo:' || %(aid)s || ':' || u.id, %(uu_tien)s
                  FROM users u
                 WHERE u.id IN (''' + _NHAN + ''') AND coalesce(u.phone, '') <> '' AND NOT u.is_demo
                ON CONFLICT (dedup_key) DO NOTHING RETURNING id''', ts)]
        q1('UPDATE announcements SET recipient_count = %s WHERE id = %s RETURNING id', (len(nhan), aid))
        hop_thu.day_di(thu)
    return len(nhan)


def danh_sach(gioi_han=50, lop=None):
    """Thông báo mới nhất trước; `lop` = chỉ thông báo gửi riêng cho lớp ấy (màn trong lớp)."""
    dk, ts = ('WHERE a.audience -> \'classIds\' = %s::jsonb', [json.dumps([lop])]) if lop else ('', [])
    return q('''SELECT a.id, a.title, a.body, a.audience, a.send_email, a.send_zalo, a.status,
                       a.recipient_count, a.created_at, a.sent_at, u.name AS created_by_name,
                       (SELECT count(*) FROM outbox o WHERE o.source_type = 'announcement'
                           AND o.source_id = a.id AND o.status = 'sent') AS da_gui_thu,
                       (SELECT count(*) FROM notifications n WHERE n.announcement_id = a.id
                           AND n.is_read) AS da_doc
                  FROM announcements a LEFT JOIN users u ON u.id = a.created_by ''' + dk + '''
                 ORDER BY a.id DESC LIMIT %s''', ts + [gioi_han])


def danh_muc():
    """Lớp và môn để MÀN SOẠN dựng ô chọn đối tượng — không màn nào gõ lại danh mục.

    RULES §7 (không hai nguồn sự thật): bảng ba môn HSA sống ở `courses.truy_cap.BA_MON`,
    nhãn tiếng Việt của chúng sống ở `courses.title`. Chép sang React là hai bảng sẽ trôi
    khỏi nhau ngay lần TopHSA mở môn thứ tư, và không ai biết bản nào đúng.

    Lớp ĐÃ HUỶ không có mặt: `_NHAN` loại chúng khỏi người nhận (`c.status <> 'cancelled'`),
    nên một ô chọn bày lớp đã huỷ là một ô chọn hứa gửi cho 0 người mà không nói ra. Sĩ số
    đếm CÙNG luật với người nhận (học viên chưa rời lớp) để con số trên ô chọn và con số
    trong bản xem trước không lệch nhau.
    """
    lop = q('''SELECT c.id, c.name, c.code, c.status,
                      (SELECT count(*) FROM class_members m JOIN users u ON u.id = m.user_id
                        WHERE m.class_id = c.id AND m.left_at IS NULL
                          AND coalesce(u.status, 'active') <> 'suspended'
                          AND ''' + chi_hoc_vien('u') + ''') AS so_em
                 FROM classes c WHERE c.status <> 'cancelled' ORDER BY c.name, c.id''')
    mon = q('SELECT id, title FROM courses WHERE id = ANY(%s::text[])', (list(BA_MON),))
    nhan = {r['id']: r['title'] for r in mon}
    return {
        'lop': [{'id': r['id'], 'name': r['name'], 'code': r['code'], 'status': r['status'],
                 'soEm': r['so_em']} for r in lop],
        # Thứ tự của `BA_MON`, không thứ tự SQL trả về: cùng thứ tự với mọi màn khác.
        # Môn chưa có dòng trong `courses` thì nhãn là mã — thà thấy mã lạ còn hơn thấy một
        # ô chọn RỖNG không ai giải thích được (RULES §8).
        'mon': [{'id': m, 'nhan': nhan.get(m) or m} for m in BA_MON],
    }
