"""SỔ ĐẦU BÀI của một buổi — bảng yêu cầu TopHSA dòng 15, 16.

GET/PUT /api/teach/sessions/<id>/so-dau-bai — giảng viên, trợ giảng, học vụ, quản trị
(`IsTeachingStaff` + `can_see_class`: trợ giảng lớp KHÁC nhận 404 như mọi cửa buổi học).

Một lượt lưu ghi:
  · từng MỤC: đã dạy / dạy một phần / chưa dạy + ghi chú. Mục của buổi khung được gắn là
    "kế hoạch"; ghi được cả mục của buổi khung KHÁC trong cùng phiên bản (dạy nốt phần
    buổi trước, dạy vượt) và mục tự thêm không có trong khung (không tính tiến độ);
  · mức tiếp thu 1–5; đề xuất (học bù / điều chỉnh — chữ tự do, luồng C sẽ biến nó thành
    Yêu cầu); các em cần hỗ trợ (chỉ em đang học lớp).

TÌNH HÌNH LỚP không ở đây: nó là cột sẵn có `class_sessions.note`, màn hình ghi qua đúng
cửa cũ `PATCH /api/teach/sessions/<id>` — miền này không ghi bảng của miền buổi học.

Chỉ ghi được buổi ĐÃ BẮT ĐẦU và chưa huỷ (409): sổ đầu bài ghi điều đã xảy ra, và một
dòng sổ là thứ làm buổi rời khỏi danh sách "đã dạy mà chưa ghi sổ".

Hai người cùng mở sổ (giảng viên + trợ giảng): thân PUT mang `phien_ban` = `loggedAt` lúc
mở; sổ đã được lưu lại sau mốc ấy → 409 thay vì đè lặng lẽ. Không gửi `phien_ban` thì
ghi đè (lời gọi API trần). Mọi lượt ghi vào nhật ký kiểm toán kèm bản CŨ.
"""
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from chuong_trinh.tu_vung import DAI, NHAN_TRANG_THAI_MUC, TRANG_THAI_MUC
from common.audit import SESSION_LOG, record
from common.clock import local_now
from common.db import q, q1, x
from common.permissions import IsTeachingStaff, can_see_class
from teaching.vocab import chi_hoc_vien

_KHONG_THAY_BUOI = {'error': 'Không tìm thấy buổi học này.'}
_TRAN_MUC = 60
_TRAN_HO_TRO = 60


def _chu(v, tran):
    if v is None:
        return None
    s = str(v).strip()
    return s[:tran] if s else None


def _buoi(session_id):
    """Buổi + lớp + buổi khung KẾ HOẠCH của nó. Buổi bù (§62e) chưa gắn riêng thì kế hoạch
    là buổi khung của buổi GỐC — buổi bù dạy lại nội dung ấy."""
    return q1('''SELECT cs.id, cs.class_id, cs.starts_at, cs.duration_minutes, cs.topic,
                        cs.status, cs.note, cs.makeup_for,
                        COALESCE(cs.syllabus_session_id, goc.syllabus_session_id) AS ke_hoach_ss,
                        c.name AS class_name, c.syllabus_version_id,
                        ss.name AS khung_name, ss.homework, ss.version_id AS ban_cua_buoi,
                        goc.starts_at AS goc_starts_at
                   FROM class_sessions cs
                   JOIN classes c ON c.id = cs.class_id
                   LEFT JOIN class_sessions goc ON goc.id = cs.makeup_for
                   LEFT JOIN syllabus_sessions ss
                          ON ss.id = COALESCE(cs.syllabus_session_id, goc.syllabus_session_id)
                  WHERE cs.id = %s''', (session_id,))


def _muc_cua_ban(version_id):
    """Mọi mục của phiên bản, kèm SỐ buổi (hạng theo `sort_order`) — MỘT câu."""
    if not version_id:
        return []
    return q('''SELECT i.id, i.title AS label, i.kind, i.weight, i.sort_order,
                       ss.id AS ss_id, ss.so AS so_buoi
                  FROM syllabus_items i
                  JOIN (SELECT id, ROW_NUMBER() OVER (ORDER BY sort_order, id) AS so
                          FROM syllabus_sessions WHERE version_id = %s) ss ON ss.id = i.session_id
                 ORDER BY ss.so, i.sort_order, i.id''', (version_id,))


def _doc(b):
    """Toàn bộ sổ của buổi `b` (dòng `_buoi`) — số câu cố định."""
    sid, vid = b['id'], b['syllabus_version_id']
    muc_ban = _muc_cua_ban(vid)
    ke_hoach_ss = b['ke_hoach_ss'] if b['ban_cua_buoi'] == vid else None
    so = q1('''SELECT sl.comprehension, sl.de_xuat, sl.logged_at,
                      COALESCE(NULLIF(u.name, ''), u.email) AS logged_by_name
                 FROM session_logs sl LEFT JOIN users u ON u.id = sl.logged_by
                WHERE sl.session_id = %s''', (sid,))
    da_ghi = q('SELECT item_id, label, status, note FROM session_log_items WHERE session_id = %s '
               'ORDER BY id', (sid,))
    ghi_theo_muc = {r['item_id']: r for r in da_ghi if r['item_id'] is not None}
    tu_them = [r for r in da_ghi if r['item_id'] is None]
    hoc_vien = q('''SELECT u.id, COALESCE(NULLIF(u.name, ''), u.email) AS ten, a.status AS diem_danh,
                           ho.note AS ho_tro_note, (ho.user_id IS NOT NULL) AS can_ho_tro
                      FROM class_members m
                      JOIN users u ON u.id = m.user_id
                      LEFT JOIN attendance a ON a.session_id = %s AND a.user_id = u.id
                      LEFT JOIN session_support ho ON ho.session_id = %s AND ho.user_id = u.id
                     WHERE m.class_id = %s AND m.left_at IS NULL AND ''' + chi_hoc_vien('u') + '''
                     ORDER BY 2''', (sid, sid, b['class_id']))

    def dong(m):
        g = ghi_theo_muc.get(m['id'])
        return {'itemId': m['id'], 'label': m['label'], 'kind': m['kind'],
                'weight': float(m['weight']), 'soBuoi': m['so_buoi'],
                'status': g['status'] if g else None, 'note': g['note'] if g else None}

    ke_hoach = [dong(m) for m in muc_ban if m['ss_id'] == ke_hoach_ss]
    ngoai_ke_hoach = [dong(m) for m in muc_ban if m['ss_id'] != ke_hoach_ss and m['id'] in ghi_theo_muc]
    # Mục đã ghi mà không còn thuộc phiên bản lớp đang theo (lớp đổi bản) — vẫn đọc được.
    id_ban = {m['id'] for m in muc_ban}
    mo_coi = [{'itemId': k, 'label': v['label'], 'status': v['status'], 'note': v['note'],
               'ngoaiBan': True} for k, v in ghi_theo_muc.items() if k not in id_ban]
    nay = local_now()
    return {
        'session': {
            'id': sid, 'classId': b['class_id'], 'className': b['class_name'],
            'startsAt': b['starts_at'].isoformat(), 'durationMinutes': b['duration_minutes'],
            'topic': b['topic'], 'status': b['status'], 'note': b['note'],
            'started': b['starts_at'] <= nay,
        },
        'lopCoKhung': bool(vid),
        'buoiKhung': None if not ke_hoach_ss else {
            'id': ke_hoach_ss, 'soBuoi': next((m['so_buoi'] for m in muc_ban
                                               if m['ss_id'] == ke_hoach_ss), None),
            'name': b['khung_name'], 'homework': b['homework']},
        # Buổi bù: sổ này ghi cho nội dung của buổi gốc (ngày gốc để giảng viên nhận ra).
        'buBuoiGoc': (b['goc_starts_at'].isoformat() if b['goc_starts_at'] else None),
        'mucKeHoach': ke_hoach,
        'mucNgoaiKeHoach': ngoai_ke_hoach + mo_coi,
        'mucTuThem': [{'label': r['label'], 'status': r['status'], 'note': r['note']}
                      for r in tu_them],
        # Để chọn thêm một mục của buổi khung KHÁC (dạy nốt / dạy vượt).
        'mucKhac': [{'itemId': m['id'], 'soBuoi': m['so_buoi'], 'label': m['label'],
                     'kind': m['kind']} for m in muc_ban if m['ss_id'] != ke_hoach_ss],
        'soDauBai': None if not so else {
            'comprehension': so['comprehension'], 'deXuat': so['de_xuat'],
            'loggedAt': so['logged_at'].isoformat(), 'loggedBy': so['logged_by_name']},
        'hocVien': [{'userId': h['id'], 'name': h['ten'], 'diemDanh': h['diem_danh'],
                     'canHoTro': bool(h['can_ho_tro']), 'ghiChu': h['ho_tro_note']}
                    for h in hoc_vien],
        'trangThaiMuc': [{'ma': k, 'nhan': NHAN_TRANG_THAI_MUC[k]} for k in TRANG_THAI_MUC],
        'ghiDuoc': b['starts_at'] <= nay and b['status'] != 'cancelled',
    }


def _lam_sach(body, b):
    """Thân PUT → (dữ liệu sạch, lỗi). Kiểm mục thuộc phiên bản lớp, em thuộc lớp."""
    muc_vao = body.get('items') or []
    if not isinstance(muc_vao, list) or len(muc_vao) > _TRAN_MUC:
        return None, 'Danh sách mục không đọc được (tối đa %d mục).' % _TRAN_MUC
    theo_id = {m['id']: m for m in _muc_cua_ban(b['syllabus_version_id'])}
    muc, da_co = [], set()
    for m in muc_vao:
        if not isinstance(m, dict):
            return None, 'Một mục trong sổ không đọc được.'
        tt = m.get('status')
        if tt not in TRANG_THAI_MUC:
            return None, 'Trạng thái mục phải là một trong: %s.' % ', '.join(
                NHAN_TRANG_THAI_MUC[k] for k in TRANG_THAI_MUC)
        ghi_chu = _chu(m.get('note'), DAI['ghi_chu_muc'])
        iid = m.get('item_id')
        if iid in (None, ''):
            nhan = _chu(m.get('label'), DAI['nhan_muc'])
            if not nhan:
                return None, 'Mục tự thêm cần có tên.'
            muc.append((None, nhan, tt, ghi_chu))
            continue
        try:
            iid = int(iid)
        except (TypeError, ValueError):
            return None, 'Mục không hợp lệ.'
        if iid not in theo_id:
            return None, 'Mục #%d không thuộc khung lớp đang theo.' % iid
        if iid in da_co:
            return None, 'Mục "%s" bị ghi hai lần.' % theo_id[iid]['label']
        da_co.add(iid)
        # Tên CHÉP từ khung lúc ghi, không lấy chữ trình duyệt gửi.
        muc.append((iid, theo_id[iid]['label'], tt, ghi_chu))

    muc_do = body.get('comprehension')
    if muc_do in (None, ''):
        muc_do = None
    else:
        try:
            muc_do = int(muc_do)
        except (TypeError, ValueError):
            return None, 'Mức tiếp thu phải là số từ 1 tới 5.'
        if not 1 <= muc_do <= 5:
            return None, 'Mức tiếp thu phải từ 1 tới 5.'

    ho_tro_vao = body.get('support') or []
    if not isinstance(ho_tro_vao, list) or len(ho_tro_vao) > _TRAN_HO_TRO:
        return None, 'Danh sách em cần hỗ trợ không đọc được.'
    ho_tro = {}
    for h in ho_tro_vao:
        if not isinstance(h, dict):
            return None, 'Danh sách em cần hỗ trợ không đọc được.'
        try:
            uid = int(h.get('user_id'))
        except (TypeError, ValueError):
            return None, 'Em cần hỗ trợ không hợp lệ.'
        ho_tro[uid] = _chu(h.get('note'), DAI['ghi_chu_ho_tro'])
    if ho_tro:
        trong_lop = {r['id'] for r in q(
            '''SELECT u.id FROM class_members m JOIN users u ON u.id = m.user_id
                WHERE m.class_id = %s AND m.left_at IS NULL AND u.id = ANY(%s) AND '''
            + chi_hoc_vien('u'), (b['class_id'], sorted(ho_tro)))}
        la = sorted(set(ho_tro) - trong_lop)
        if la:
            return None, 'Chỉ đánh dấu được em đang học lớp này (#%s không phải).' % ', #'.join(
                map(str, la))
    return {'muc': muc, 'muc_do': muc_do, 'de_xuat': _chu(body.get('de_xuat'), DAI['de_xuat']),
            'ho_tro': ho_tro}, None


class SoDauBaiView(APIView):
    """GET/PUT /api/teach/sessions/<id>/so-dau-bai."""
    permission_classes = [IsTeachingStaff]

    def _load(self, request, session_id):
        b = _buoi(session_id)
        if not b or not can_see_class(request.user, b['class_id']):
            return None
        return b

    def get(self, request, session_id):
        b = self._load(request, session_id)
        if not b:
            return Response(_KHONG_THAY_BUOI, status=404)
        return Response(_doc(b))

    def put(self, request, session_id):
        b = self._load(request, session_id)
        if not b:
            return Response(_KHONG_THAY_BUOI, status=404)
        nay = local_now()
        if b['status'] == 'cancelled':
            return Response({'error': 'Buổi này đã huỷ — không có gì để ghi sổ.'}, status=409)
        if b['starts_at'] > nay:
            return Response({'error': 'Buổi này chưa diễn ra. Sổ đầu bài ghi sau khi dạy.'},
                            status=409)
        body = request.data if isinstance(request.data, dict) else {}
        du, loi = _lam_sach(body, b)
        if loi:
            return Response({'error': loi}, status=400)

        with transaction.atomic():
            cu = q1('SELECT comprehension, de_xuat, logged_at FROM session_logs '
                    'WHERE session_id = %s FOR UPDATE', (session_id,))
            if 'phien_ban' in body:
                thay = (cu['logged_at'].isoformat() if cu else None)
                if (body.get('phien_ban') or None) != thay:
                    return Response({'error': 'Sổ đầu bài buổi này vừa được lưu bởi người khác '
                                              '— tải lại trang để xem bản mới rồi sửa tiếp.',
                                     'xungDot': True}, status=409)
            muc_cu = q('SELECT item_id, label, status FROM session_log_items WHERE session_id = %s '
                       'ORDER BY id', (session_id,))
            ho_tro_cu = [r['user_id'] for r in q(
                'SELECT user_id FROM session_support WHERE session_id = %s', (session_id,))]
            x('''INSERT INTO session_logs (session_id, comprehension, de_xuat, logged_by, logged_at)
                 VALUES (%s, %s, %s, %s, %s)
                 ON CONFLICT (session_id) DO UPDATE
                    SET comprehension = EXCLUDED.comprehension, de_xuat = EXCLUDED.de_xuat,
                        logged_by = EXCLUDED.logged_by, logged_at = EXCLUDED.logged_at''',
              (session_id, du['muc_do'], du['de_xuat'], request.user.id, nay))
            x('DELETE FROM session_log_items WHERE session_id = %s', (session_id,))
            if du['muc']:
                x('''INSERT INTO session_log_items (session_id, item_id, label, status, note)
                     SELECT %s, t.iid, t.nhan, t.tt, t.gc
                       FROM unnest(%s::int[], %s::text[], %s::text[], %s::text[])
                            AS t(iid, nhan, tt, gc)''',
                  (session_id, [m[0] for m in du['muc']], [m[1] for m in du['muc']],
                   [m[2] for m in du['muc']], [m[3] for m in du['muc']]))
            x('DELETE FROM session_support WHERE session_id = %s', (session_id,))
            if du['ho_tro']:
                x('''INSERT INTO session_support (session_id, user_id, note, created_by, created_at)
                     SELECT %s, t.uid, t.gc, %s, %s
                       FROM unnest(%s::int[], %s::text[]) AS t(uid, gc)''',
                  (session_id, request.user.id, nay, list(du['ho_tro']),
                   list(du['ho_tro'].values())))
            dem = {k: sum(1 for m in du['muc'] if m[2] == k) for k in TRANG_THAI_MUC}
            record(request, SESSION_LOG, target_type='class_session', target_id=session_id,
                   target_label=b['topic'] or b['starts_at'].strftime('%d/%m/%Y %H:%M'),
                   summary='%s sổ đầu bài buổi %s lớp %s: %d đã dạy, %d một phần, %d chưa dạy'
                           % ('Sửa' if cu else 'Ghi', b['starts_at'].strftime('%d/%m/%Y'),
                              b['class_name'], dem['done'], dem['partial'], dem['not_done']),
                   detail={'truoc': None if not cu else {
                               'comprehension': cu['comprehension'], 'de_xuat': cu['de_xuat'],
                               'items': [[r['item_id'], r['label'], r['status']] for r in muc_cu],
                               'support': ho_tro_cu},
                           'sau': {'comprehension': du['muc_do'], 'de_xuat': du['de_xuat'],
                                   'items': [[m[0], m[1], m[2]] for m in du['muc']],
                                   'support': sorted(du['ho_tro'])}})
        return Response(dict(_doc(_buoi(session_id)), ok=True))
