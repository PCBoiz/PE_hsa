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

Ngày thi của lớp khác mục tiêu cá nhân thì NÓI (`ngayThiLech`), không tự đổi:
anh Sơn chốt "nhắc + một nút", em bấm mới đổi (qua `PATCH /api/hsa/goals`).
"""
from datetime import timedelta

from rest_framework.response import Response

from common.clock import local_now
from common.db import q
from common.views import NguoiDungView
from stats.goals import as_date, read_goals
from teaching.parent_report import _chuyen_can
from teaching.sessions import DEFAULT_SESSION_MINUTES

#: Số buổi sắp tới hiện ra — tuần này và đầu tuần sau là đủ.
SO_SAP_TOI = 3
#: Buổi ĐÃ HUỶ trong ngần này ngày tới thì nêu tên. Huỷ mà chỉ lặng lẽ biến
#: khỏi "buổi tới" thì em vẫn tưởng tối đó có học — hoặc tưởng lớp quên xếp lịch.
NGAY_NEU_BUOI_HUY = 7


def _iso(v):
    return v.isoformat() if v else None


def _buoi_dict(r, link_lop, nay):
    ket = r['starts_at'] + timedelta(minutes=r['duration_minutes'] or DEFAULT_SESSION_MINUTES)
    return {
        'sessionId': r['id'], 'startsAt': _iso(r['starts_at']),
        'durationMinutes': r['duration_minutes'], 'topic': r['topic'],
        'meetingUrl': r['meeting_url'] or link_lop or None,
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
                                 c.starts_on, c.ends_on, u.name AS teacher_name
                          FROM class_members m
                          JOIN classes c ON c.id = m.class_id
                          LEFT JOIN users u ON u.id = c.teacher_id
                          WHERE m.user_id = %s AND m.left_at IS NULL
                          ORDER BY c.name''', (uid,))
        ids = [r['class_id'] for r in thanh_vien]
        sap_toi = {}
        da_huy = {}
        cac_dot = {}
        if ids:
            for r in q('''SELECT id, class_id, starts_at, duration_minutes, topic, meeting_url
                          FROM class_sessions
                          WHERE class_id = ANY(%s) AND status = 'cancelled'
                            AND starts_at >= %s AND starts_at < %s
                          ORDER BY starts_at''',
                       (ids, nay, nay + timedelta(days=NGAY_NEU_BUOI_HUY))):
                da_huy.setdefault(r['class_id'], []).append(r)
            for r in q('''SELECT id, class_id, starts_at, duration_minutes, topic, meeting_url
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

        muc_tieu = read_goals(uid)
        ngay_thi_em = as_date(muc_tieu.get('examDate'))

        lop = []
        for r in thanh_vien:
            cid = r['class_id']
            ds = [_buoi_dict(b, r['meeting_url'], nay) for b in sap_toi.get(cid, [])]
            vao = min(d[0] for d in cac_dot[cid]).date()
            lop.append({
                'id': cid, 'name': r['name'], 'code': r['code'], 'schedule': r['schedule'],
                'teacherName': r['teacher_name'], 'meetingUrl': r['meeting_url'],
                'examDate': _iso(r['exam_date']),
                'startsOn': _iso(r['starts_on']), 'endsOn': _iso(r['ends_on']),
                'joinedAt': _iso(r['joined_at']),
                'buoiToi': ds[0] if ds else None,
                'sapToi': ds,
                'daHuy': [_buoi_dict(b, r['meeting_url'], nay) for b in da_huy.get(cid, [])],
                'chuyenCan': _chuyen_can(cid, uid, vao, nay.date(), cac_dot=cac_dot[cid]),
                'ngayThiLech': bool(r['exam_date'] and ngay_thi_em
                                    and r['exam_date'] != ngay_thi_em),
            })
        return Response({'lop': lop, 'mucTieu': {'examDate': muc_tieu.get('examDate')}})
