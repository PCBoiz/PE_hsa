"""LỚP CỦA TÔI — học viên nhìn thấy lớp mình: buổi tới, link phòng, chuyên cần của chính mình.

── VÌ SAO CÓ (14/09/2026) ─────────────────────────────────────────────────

Rà luồng học viên trên trình duyệt thật: lớp 1 học buổi đầu tối 15/09 với link
phòng, 16 buổi đã lên lịch — mà bảng điều khiển của em không có một chữ nào về
lớp. Giảng viên, trợ giảng, học vụ đều thấy; người phải VÀO PHÒNG lúc 19:30
thì không. Mọi API buổi học tới hôm nay đều nằm sau cổng giảng dạy.

── CHỈ CỦA CHÍNH MÌNH ─────────────────────────────────────────────────────

`NguoiDungView`: phải đăng nhập, và view lọc theo `request.user`. Trả về KHÔNG
có gì về em khác — không sĩ số, không tên bạn học. Chuyên cần là của em, đếm
bằng CÙNG hàm với tờ báo cáo phụ huynh (`parent_report._chuyen_can`) để em và
bố mẹ nhìn cùng một con số; hai hàm đếm hai kiểu là cãi nhau ở nhà.

Buổi tới: chưa huỷ, gần nhất từ bây giờ (buổi đang diễn ra vẫn là buổi tới —
kèm cờ). Link của buổi, thiếu thì của lớp — cùng luật với "Việc hôm nay".
Hình thức / phòng cũng vậy (§53, 24/09/2026): buổi để trống thì theo lớp — em
học tại trung tâm cần biết PHÒNG, không cần nút "Vào phòng học".

Ngày thi của lớp khác mục tiêu cá nhân thì NÓI (`ngayThiLech`), không tự đổi:
anh Sơn chốt "nhắc + một nút", em bấm mới đổi (qua `PATCH /api/hsa/goals`).
"""
from datetime import timedelta

from rest_framework.response import Response

from common.clock import local_now
from common.db import q
from common.views import NguoiDungView
from stats.goals import as_date, read_goals
from teaching.parent_report import _buoi_cua_em, _chuyen_can
from teaching.sessions import DEFAULT_SESSION_MINUTES

#: Số buổi sắp tới hiện ra — tuần này và đầu tuần sau là đủ.
SO_SAP_TOI = 3
#: Buổi ĐÃ HUỶ trong ngần này ngày tới thì nêu tên. Huỷ mà chỉ lặng lẽ biến
#: khỏi "buổi tới" thì em vẫn tưởng tối đó có học — hoặc tưởng lớp quên xếp lịch.
NGAY_NEU_BUOI_HUY = 7
#: Số buổi gần nhất trong danh sách điểm danh TỪNG buổi (V-d) — một đợt ba tháng hai
#: buổi/tuần là ~26; trần để thẻ lớp không thành sổ cái khi em học cả năm.
SO_BUOI_DIEM_DANH = 60


def _iso(v):
    return v.isoformat() if v else None


def _buoi_dict(r, lop, nay):
    """`lop`: dòng lớp (`meeting_url`, `mode`, `room`) — thứ buổi để trống thì kế thừa."""
    ket = r['starts_at'] + timedelta(minutes=r['duration_minutes'] or DEFAULT_SESSION_MINUTES)
    return {
        'sessionId': r['id'], 'startsAt': _iso(r['starts_at']),
        'durationMinutes': r['duration_minutes'], 'topic': r['topic'],
        'meetingUrl': r['meeting_url'] or lop['meeting_url'] or None,
        'hinhThuc': r['mode'] or lop['mode'],
        'phong': r['room'] or lop['room'],
        'dangDienRa': r['starts_at'] <= nay < ket,
    }


class LopCuaToiView(NguoiDungView):
    """GET /api/lop-cua-toi — không ghi gì."""

    def get(self, request):
        uid = request.user.id
        nay = local_now()
        # Mọi lượt ghi danh còn mở của em, kèm lớp và giảng viên — một câu.
        # Một em có thể ở hai lớp (ôn hai hợp phần); trả cả hai.
        thanh_vien = q('''SELECT m.class_id, m.joined_at,
                                 c.name, c.code, c.schedule, c.meeting_url, c.exam_date,
                                 c.mode, c.room,
                                 c.starts_on, c.ends_on, u.name AS teacher_name,
                                 (SELECT MIN(s.starts_at) FROM attendance a
                                    JOIN class_sessions s ON s.id = a.session_id
                                   WHERE a.user_id = m.user_id
                                     AND s.class_id = m.class_id) AS tick_som
                          FROM class_members m
                          JOIN classes c ON c.id = m.class_id
                          LEFT JOIN users u ON u.id = c.teacher_id
                          WHERE m.user_id = %s AND m.left_at IS NULL
                          ORDER BY c.name''', (uid,))
        ids = [r['class_id'] for r in thanh_vien]
        sap_toi = {}
        da_huy = {}
        cac_dot = {}
        bai_tap = {}
        if ids:
            for r in q('''SELECT id, class_id, starts_at, duration_minutes, topic, meeting_url,
                                 mode, room
                          FROM class_sessions
                          WHERE class_id = ANY(%s) AND status = 'cancelled'
                            AND starts_at >= %s AND starts_at < %s
                          ORDER BY starts_at''',
                       (ids, nay, nay + timedelta(days=NGAY_NEU_BUOI_HUY))):
                da_huy.setdefault(r['class_id'], []).append(r)
            for r in q('''SELECT id, class_id, starts_at, duration_minutes, topic, meeting_url,
                                 mode, room
                          FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY class_id
                                                             ORDER BY starts_at) AS tt
                                FROM class_sessions
                                WHERE class_id = ANY(%s) AND status <> 'cancelled'
                                  AND starts_at + (COALESCE(duration_minutes, %s)
                                                   * INTERVAL '1 minute') > %s) s
                          WHERE tt <= %s ORDER BY class_id, starts_at''',
                       (ids, DEFAULT_SESSION_MINUTES, nay, SO_SAP_TOI)):
                sap_toi.setdefault(r['class_id'], []).append(r)
            # MỌI lượt em ở lớp (kể cả lượt đã đóng) — mẫu số chuyên cần chỉ
            # gồm buổi trong thời gian em ở lớp, xem `_chuyen_can`.
            for r in q('SELECT class_id, joined_at, left_at FROM class_members '
                       'WHERE user_id = %s AND class_id = ANY(%s)', (uid, ids)):
                cac_dot.setdefault(r['class_id'], []).append((r['joined_at'], r['left_at']))
            # Bài giảng viên giao mà em CHƯA NỘP, kèm hạn sớm nhất (20/09/2026).
            # Rà trên điện thoại 390px: Trang của tôi không có chữ "bài tập" nào
            # trong khi mục Bài tập nói "còn 1 bài chưa nộp" — thanh trên ở khổ
            # điện thoại không có mục ấy, nên em không có đường biết. Thẻ lớp là
            # chỗ đúng: bài tập là quan hệ giữa em và LỚP.
            for r in q('''SELECT a.class_id, COUNT(*) AS chua_nop, MIN(a.due_at) AS han_som
                            FROM assignments a
                            LEFT JOIN submissions s ON s.assignment_id = a.id AND s.user_id = %s
                           WHERE a.class_id = ANY(%s) AND a.status = 'open'
                             AND s.submitted_at IS NULL
                           GROUP BY a.class_id''', (uid, ids)):
                bai_tap[r['class_id']] = {'chuaNop': r['chua_nop'],
                                          'hanSom': _iso(r['han_som'])}

        muc_tieu = read_goals(uid)
        ngay_thi_em = as_date(muc_tieu.get('examDate'))

        lop = []
        for r in thanh_vien:
            cid = r['class_id']
            ds = [_buoi_dict(b, r, nay) for b in sap_toi.get(cid, [])]
            # Đầu kỳ = ngày vào lớp, HOẶC sớm hơn nếu giảng viên đã tick em ở
            # buổi trước đó (`joined_at` là lúc học vụ bấm nút — xem ngoại lệ
            # trong `parent_report._buoi_cua_em`, 20/09/2026).
            vao = min(d[0] for d in cac_dot[cid]).date()
            vao = min(vao, r['tick_som'].date()) if r.get('tick_som') else vao
            # MỘT lượt đọc buổi cho cả chuyên cần lẫn danh sách từng buổi (V-d, bảng
            # TopHSA dòng 28): cùng ba bộ lọc (buổi đã diễn ra, chưa huỷ, trong thời
            # gian em ở lớp), nên đếm và liệt kê không thể lệch nhau.
            du = _buoi_cua_em(cid, uid, vao, nay.date(), cac_dot=cac_dot[cid])
            lop.append({
                'id': cid, 'name': r['name'], 'code': r['code'], 'schedule': r['schedule'],
                'teacherName': r['teacher_name'], 'meetingUrl': r['meeting_url'],
                'mode': r['mode'], 'room': r['room'],
                'examDate': _iso(r['exam_date']),
                'startsOn': _iso(r['starts_on']), 'endsOn': _iso(r['ends_on']),
                'joinedAt': _iso(r['joined_at']),
                'buoiToi': ds[0] if ds else None,
                'sapToi': ds,
                'daHuy': [_buoi_dict(b, r, nay) for b in da_huy.get(cid, [])],
                'chuyenCan': _chuyen_can(cid, uid, vao, nay.date(), du_lieu=du),
                # Điểm danh TỪNG buổi, mới nhất trước. `daDiemDanh` False = giảng viên
                # chưa mở sổ buổi ấy (không phải em vắng); True mà `trangThai` null =
                # sổ đã lưu nhưng không có dòng của em. Chỉ trạng thái của CHÍNH em.
                'diemDanh': [{
                    'sessionId': b['id'], 'startsAt': _iso(b['starts_at']), 'topic': b['topic'],
                    'daDiemDanh': bool(b['attendance_taken_at']),
                    'trangThai': (du['trang_thai'].get(b['id'])
                                  if b['attendance_taken_at'] else None),
                } for b in sorted(du['da_dien_ra'], key=lambda b: b['starts_at'],
                                  reverse=True)[:SO_BUOI_DIEM_DANH]],
                'baiTap': bai_tap.get(cid, {'chuaNop': 0, 'hanSom': None}),
                'ngayThiLech': bool(r['exam_date'] and ngay_thi_em
                                    and r['exam_date'] != ngay_thi_em),
            })
        return Response({'lop': lop, 'mucTieu': {'examDate': muc_tieu.get('examDate')}})
