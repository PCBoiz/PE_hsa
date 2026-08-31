"""Báo cáo gửi phụ huynh — đặc tả ERP §6.

KHÁC HẲN hồ sơ học viên ở `TeachStudentView`, dù cùng nói về một em. Hồ sơ kia
là bàn làm việc của giảng viên: đầy đủ, dày, để tư vấn. Cái này là một tờ giấy
gửi về nhà, và người đọc là phụ huynh — thường không biết "chỉ số thành thạo"
hay "đường cong tiến bộ" là gì, chỉ cần biết ba chuyện: **con có đi học không,
có tiến bộ không, và cần giúp chỗ nào**.

Vì thế ở đây cắt hết chỉ số kỹ thuật, giữ đúng những gì trả lời ba câu đó, và
mỗi con số đi kèm mẫu số để nó tự giải thích ("6/7 buổi" chứ không phải "86%").

BA RANH GIỚI CỐ Ý, đọc trước khi thêm trường:

1. **KHÔNG có nhật ký học viên tự ghi.** Đó là chỗ em viết cho chính mình. Đặc
   tả ERP mục "Quyền riêng tư" chốt: tiến độ và điểm là hợp lý để phụ huynh xem,
   nhật ký và ghi chú riêng thì phải hỏi ý học viên trước. Chưa hỏi thì chưa gửi.

2. **Chuyên cần chỉ tính trên những buổi ĐÃ ĐIỂM DANH** (`attendance_taken_at`
   khác NULL). Buổi giảng viên quên tick mà đem chia vào mẫu số sẽ biến thành
   "con vắng" trong mắt phụ huynh — một lời buộc tội sai, gửi về tận nhà, và
   không ai ở đó để đính chính. Số buổi chưa điểm danh vẫn được báo riêng
   (`sessionsUnmarked`) để trung tâm biết tờ giấy này đang thiếu bao nhiêu.

3. **Không có dữ liệu thì nói KHÔNG CÓ DỮ LIỆU, không viết 0.** "Điểm thi thử
   trung bình: 0" đọc như con làm bài sai hết, trong khi sự thật là con chưa thi
   lần nào. Cùng lý do `common/events.py:pct` trả None thay vì 0.
"""
from datetime import timedelta

from rest_framework.response import Response
from rest_framework.views import APIView

from common.clock import local_now, local_today
from common.db import q, q1
from common.permissions import IsTeacherOrAdmin, can_see_class
from stats import competency
from teaching.attendance import ti_le
from teaching.vocab import chi_hoc_vien, trang_thai

#: Kỳ báo cáo mặc định. Bốn tuần vì trung tâm gửi báo cáo theo tháng, và một
#: tuần thì quá ngắn để thấy xu hướng — một tuần ốm là cả báo cáo xấu.
DEFAULT_WEEKS = 4

#: Dưới ngưỡng này thì đưa vào mục "cần chú ý". Khớp `stats/plan.py:REVIEW_BELOW`
#: để lời khuyên gửi phụ huynh không mâu thuẫn với lịch học máy xếp cho em.
WEAK_BELOW = 60

#: Từ ngưỡng này trở lên thì gọi là điểm mạnh.
STRONG_FROM = 75

#: Số chủ đề nêu tên ở mỗi mục. Ba là đủ để hành động; liệt kê mười thì phụ
#: huynh không biết bắt đầu từ đâu, và tờ báo cáo thành bản kiểm điểm.
TOP_N = 3


def _khoang_ngay(request):
    """Đọc ?from & ?to, mặc định là 4 tuần gần nhất. Trả (từ, đến, có_hợp_lệ)."""
    hom_nay = local_today()
    mac_dinh_tu = hom_nay - timedelta(weeks=DEFAULT_WEEKS)

    def doc(ten, mac_dinh):
        raw = (request.query_params.get(ten) or '').strip()
        if not raw:
            return mac_dinh, True
        try:
            from datetime import date
            return date.fromisoformat(raw), True
        except ValueError:
            return mac_dinh, False

    tu, ok1 = doc('from', mac_dinh_tu)
    den, ok2 = doc('to', hom_nay)
    dao = tu > den
    if dao:
        # Đổi chỗ để không ra kỳ rỗng, NHƯNG phải nói. Người gõ nhầm thứ tự hai
        # ngày sẽ nhận về một kỳ khác hẳn kỳ họ định lấy, và nếu im lặng thì họ
        # in tờ giấy đó ra mà không biết.
        tu, den = den, tu
    return tu, den, (ok1 and ok2), dao


def _chuyen_can(class_id, user_id, tu, den, cac_dot=()):
    """Chuyên cần trong kỳ. Mẫu số là số buổi CHÍNH EM ẤY có thể dự.

    ── Ba bộ lọc, mỗi cái vá một cách buộc tội sai ──────────────────────────

    1. **Chỉ buổi ĐÃ điểm danh** (`attendance_taken_at`). Buổi giảng viên quên
       tick mà đem chia vào mẫu số sẽ thành "con vắng" trong mắt phụ huynh.

    2. **Chỉ buổi TRONG THỜI GIAN EM Ở LỚP** (`cac_dot`). Đây là lỗi
       đo được ngày 31/08/2026 và là lỗi nặng nhất của tệp này: mẫu số lấy mọi
       buổi CỦA LỚP, nên em vào lớp giữa đợt bị tính vắng cho những buổi diễn ra
       trước khi em ghi danh. Kịch bản đã dựng lại: lớp 4 buổi, em dự 2 buổi
       cuối và CÓ MẶT cả hai — tờ giấy in "Có mặt 2/4 (50%)". Sự thật là 100%.
       Đối xứng y hệt với em rời lớp giữa kỳ.

    3. **Bỏ buổi ĐÃ HUỶ và buổi CHƯA DIỄN RA**. Chúng từng lọt vào
       `sessionsUnmarked`, và dòng chữ ấy IN RA GIẤY: "Còn 2 buổi trong kỳ chưa
       được điểm danh" — tờ giấy tự tố trung tâm bỏ sót, trong khi một buổi đã
       huỷ và một buổi tối nay chưa tới.

    ── Bốn ô phải CỘNG LẠI bằng mẫu số ─────────────────────────────────────
    Sau ba bộ lọc trên, vẫn có thể còn buổi mà em không có dòng điểm danh nào
    (giảng viên tick sót đúng em đó). Số ấy trả riêng ở `noRecord` và ĐƯỢC CỘNG
    vào, để `present + late + absent + excused + noRecord = sessionsCounted`.
    Một tờ giấy mà bốn ô không cộng lại bằng mẫu số là tờ giấy tự mâu thuẫn, và
    người đọc sẽ không tin ô nào nữa.
    """
    gio = local_now()
    dieu_kien = ["s.class_id = %s", "s.starts_at::date BETWEEN %s AND %s"]
    args = [class_id, tu, den]

    # Buổi diễn ra TRƯỚC khi em vào lớp không phải buổi của em — và một em có
    # thể ở lớp NHIỀU ĐỢT (rời rồi học lại). Bản cũ lấy đúng MỘT đợt
    # (`LIMIT 1`, ưu tiên đợt đang mở) để bó chuyên cần, trong khi phần học tập
    # và dòng "Kỳ báo cáo" in ra dùng TRỌN kỳ. Em học 01–20/08 rồi quay lại
    # 28/08 sẽ nhận tờ giấy ghi "học 5 bài, làm 2 đề, điểm đang lên" ngay cạnh
    # "chuyên cần 0%" — hai nửa của cùng một tờ giấy nói hai chuyện khác nhau,
    # và người đọc sẽ không tin nửa nào.
    #
    # Hợp của các đợt, không phải một đợt. `cac_dot` rỗng = không giới hạn.
    khoang = []
    for vao, roi in cac_dot:
        ve = []
        if vao:
            ve.append('s.starts_at >= %s')
            args.append(vao)
        if roi:
            ve.append('s.starts_at <= %s')
            args.append(roi)
        khoang.append('(' + ' AND '.join(ve) + ')' if ve else 'TRUE')
    if khoang:
        dieu_kien.append('(' + ' OR '.join(khoang) + ')')

    buoi = q('SELECT s.id, s.attendance_taken_at, s.status, s.starts_at '
             'FROM class_sessions s WHERE ' + ' AND '.join(dieu_kien), tuple(args))

    # Buổi đã huỷ: lớp nghỉ vì giảng viên ốm, không phải việc của em.
    # Buổi chưa tới: chưa xảy ra thì không thể thiếu điểm danh.
    da_dien_ra = [b for b in buoi
                  if b['status'] != 'cancelled' and b['starts_at'] and b['starts_at'] <= gio]
    da_tick = [b['id'] for b in da_dien_ra if b['attendance_taken_at']]
    chua_tick = len(da_dien_ra) - len(da_tick)

    dem = {'present': 0, 'late': 0, 'absent': 0, 'excused': 0}
    if da_tick:
        for r in q("""SELECT status, COUNT(*) AS n FROM attendance
                      WHERE user_id = %s AND session_id = ANY(%s)
                      GROUP BY status""", (user_id, da_tick)):
            if r['status'] in dem:
                dem[r['status']] = r['n']

    co_dong = sum(dem.values())
    khong_co_dong = max(0, len(da_tick) - co_dong)
    co_mat = dem['present'] + dem['late']
    return {
        # Tổng buổi của lớp trong kỳ, TRƯỚC khi lọc — để trung tâm đối chiếu.
        'sessionsTotal': len(buoi),
        'sessionsCounted': len(da_tick),
        # Buổi ĐÃ diễn ra mà chưa ai tick. Báo riêng để trung tâm biết tờ giấy
        # này thiếu bao nhiêu, thay vì im lặng chia cho một mẫu số nhỏ hơn.
        'sessionsUnmarked': chua_tick,
        'present': dem['present'],
        'late': dem['late'],
        'absent': dem['absent'],
        'excused': dem['excused'],
        # Buổi đã tick nhưng KHÔNG có dòng nào cho riêng em này.
        'noRecord': khong_co_dong,
        # MẪU SỐ là số buổi EM ẤY CÓ DÒNG, không phải số buổi cả lớp được
        # tick — công thức ở `attendance.ti_le`, dùng chung với sổ điểm danh CSV.
        #
        # Bản đầu chia cho `len(da_tick)`: giảng viên tick cả lớp mà sót một em
        # thì em đi đủ 2/2 buổi có dòng vẫn ra 50% trên tờ giấy gửi về nhà.
        #
        # BẤT BIẾN BỐN Ô VẪN GIỮ: present + late + absent + excused + noRecord
        # = sessionsCounted. Đổi mẫu số của RIÊNG tỉ lệ chứ không bỏ `noRecord` —
        # khoảng trống phải được nói ra, chỉ là không được tính vào mẫu số.
        'attendedPct': ti_le(co_mat, co_dong),
    }


def _hoc_tap(user_id, tu, den):
    """Số bài học xong và số lượt thi thử TRONG KỲ, kèm điểm trung bình."""
    bai = q1('''SELECT COUNT(*) AS n FROM learning_events
                WHERE user_id = %s AND kind = 'lesson'
                  AND event_date BETWEEN %s AND %s''', (user_id, tu, den))['n']

    # SẮP THEO CẢ `occurred_at`, không chỉ `event_date`. Thi hai đề trong cùng
    # một ngày là chuyện thường (đo trên dữ liệu thật: em id 13 có hai lượt cùng
    # ngày 25/08), và khi đó sắp theo mỗi ngày thì thứ tự trong ngày là bất kỳ
    # thứ gì Postgres trả về. Xu hướng tính trên thứ tự ấy sẽ LẬT NGƯỢC ngẫu
    # nhiên — và câu "con đang đi xuống" gửi về tận nhà cho một em đang tiến bộ
    # là kiểu sai không có đường đính chính.
    de = q('''SELECT score, max_score, event_date FROM learning_events
              WHERE user_id = %s AND kind = 'mock'
                AND event_date BETWEEN %s AND %s
                AND score IS NOT NULL AND max_score > 0
              ORDER BY event_date, occurred_at''', (user_id, tu, den))
    diem = [float(r['score']) * 100 / float(r['max_score']) for r in de]

    # Xu hướng so nửa sau với nửa đầu kỳ. Cần ít nhất HAI lượt thi mới nói được
    # "tiến bộ" — một lượt thì không có gì để so, và đoán bừa ở tờ giấy gửi về
    # nhà là kiểu sai khó sửa nhất.
    xu_huong = None
    if len(diem) >= 2:
        giua = len(diem) // 2
        dau = sum(diem[:giua or 1]) / (giua or 1)
        sau = sum(diem[giua:]) / (len(diem) - giua)
        lech = sau - dau
        xu_huong = 'up' if lech >= 3 else ('down' if lech <= -3 else 'flat')

    return {
        'lessonsDone': bai,
        'mockCount': len(diem),
        'mockAvg': round(sum(diem) / len(diem)) if diem else None,
        'mockBest': round(max(diem)) if diem else None,
        'mockTrend': xu_huong,
    }


def _chu_de(user_id):
    """Chủ đề cần chú ý và chủ đề đang mạnh — chỉ lấy những ô ĐO ĐƯỢC.

    Bỏ qua ô `status != 'ok'` là bắt buộc: một chủ đề chưa làm bài nào có
    `mastery = None`, và xếp nó vào "cần chú ý" là nói với phụ huynh rằng con
    yếu phần đó, trong khi sự thật là con chưa học tới.
    """
    comp = competency.compute(user_id)
    do_duoc = [t for t in (comp.get('topics') or [])
               if t.get('status') == 'ok' and t.get('mastery') is not None]

    yeu = sorted((t for t in do_duoc if t['mastery'] < WEAK_BELOW),
                 key=lambda t: t['mastery'])[:TOP_N]
    manh = sorted((t for t in do_duoc if t['mastery'] >= STRONG_FROM),
                  key=lambda t: -t['mastery'])[:TOP_N]

    def gon(t):
        return {'course': t['course'], 'courseTitle': t.get('courseTitle'),
                'topic': t['topic'], 'mastery': t['mastery']}

    return {
        'weak': [gon(t) for t in yeu],
        'strong': [gon(t) for t in manh],
        'measured': len(do_duoc),
        'total': len(comp.get('topics') or []),
        'courses': comp.get('courses') or [],
    }


class ParentReportView(APIView):
    """GET /api/teach/classes/<id>/students/<uid>/parent-report?from=&to=

    Trả dữ liệu cho tờ báo cáo gửi phụ huynh. Bản in nằm ở frontend — cố ý
    KHÔNG sinh PDF ở máy chủ: trình duyệt in ra PDF đã đủ tốt, và thêm một bộ
    sinh PDF là thêm một phông chữ tiếng Việt phải cài trên Render, một khác
    biệt nữa giữa máy dev và production, và một chỗ nữa để hỏng.
    """
    permission_classes = [IsTeacherOrAdmin]

    def get(self, request, class_id, user_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)

        # Lấy CẢ lượt học đã đóng: báo cáo cuối kỳ cho một em vừa học xong vẫn
        # phải in ra được. Ưu tiên lượt đang mở nếu có.
        # `chi_hoc_vien` là BẮT BUỘC ở đây, không phải để làm đẹp con số.
        # Tài khoản quản trị viên đang là thành viên lớp 1 (anh chủ sản phẩm
        # chốt giữ), nên thiếu bộ lọc này thì giảng viên in được "báo cáo gửi
        # phụ huynh" cho chính tài khoản quản trị — kèm email và số điện thoại
        # của nó. Đo 31/08/2026: HTTP 200, trả về admin@pe-hsa.vn.
        # TẤT CẢ các đợt, không phải một. Xem chú thích trong `_chuyen_can`.
        cac_dot = q('''SELECT m.joined_at, m.left_at, m.leave_reason, m.note
                       FROM class_members m
                       JOIN users u ON u.id = m.user_id
                       WHERE m.class_id = %s AND m.user_id = %s
                         AND ''' + chi_hoc_vien('u') + '''
                       ORDER BY m.joined_at''', (class_id, user_id))
        if not cac_dot:
            return Response({'error': 'Không có học viên này trong lớp.'}, status=404)
        # Đợt MỚI NHẤT quyết định trạng thái và ghi chú hiện tại; ngày vào lấy
        # đợt đầu, ngày rời để trống nếu còn đợt nào đang mở.
        moi_nhat = max(cac_dot, key=lambda d: (d['left_at'] is None, d['joined_at']))
        thanh_vien = {
            'joined_at': cac_dot[0]['joined_at'],
            'left_at': None if any(d['left_at'] is None for d in cac_dot)
                       else max(d['left_at'] for d in cac_dot),
            'leave_reason': moi_nhat['leave_reason'],
            'note': moi_nhat['note'],
        }

        lop = q1('SELECT id, name, code, course_id, teacher_id FROM classes WHERE id=%s',
                 (class_id,))
        gv = q1('SELECT name FROM users WHERE id=%s', (lop['teacher_id'],)) \
            if lop['teacher_id'] else None
        em = q1('SELECT id, name, email, phone FROM users WHERE id=%s', (user_id,))
        if not em:
            return Response({'error': 'Không tìm thấy học viên.'}, status=404)

        tu, den, ngay_hop_le, dao_ngay = _khoang_ngay(request)
        canh_bao = []
        if not ngay_hop_le:
            canh_bao.append('Ngày lọc không đọc được (cần dạng YYYY-MM-DD) — '
                            'đang dùng kỳ mặc định %d tuần gần nhất.' % DEFAULT_WEEKS)
        if dao_ngay:
            canh_bao.append('Ngày bắt đầu đang muộn hơn ngày kết thúc nên đã đổi chỗ '
                            'hai ngày. Kiểm lại kỳ báo cáo trước khi in.')

        return Response({
            'student': {'id': em['id'], 'name': em['name'],
                        'email': em['email'], 'phone': em['phone']},
            'class': {'id': lop['id'], 'name': lop['name'], 'code': lop['code'],
                      'teacher': gv['name'] if gv else None},
            'membership': {
                'joinedAt': thanh_vien['joined_at'].isoformat()
                            if thanh_vien['joined_at'] else None,
                'leftAt': thanh_vien['left_at'].isoformat()
                          if thanh_vien['left_at'] else None,
                'status': trang_thai(thanh_vien['left_at'], thanh_vien['leave_reason']),
                # Ghi chú của giảng viên VỀ lớp/em này — khác hẳn nhật ký em tự
                # ghi (xem ranh giới 1). Cái này viết ra để người khác đọc.
                'teacherNote': thanh_vien['note'],
                # Số ĐỢT em ở lớp. In ra khi > 1 để người đọc hiểu vì sao ngày
                # vào và ngày rời không liền một mạch.
                'stints': len(cac_dot),
            },
            'period': {'from': tu.isoformat(), 'to': den.isoformat(),
                       'weeks': DEFAULT_WEEKS},
            'attendance': _chuyen_can(class_id, user_id, tu, den,
                                      cac_dot=[(d['joined_at'], d['left_at'])
                                               for d in cac_dot]),
            'study': _hoc_tap(user_id, tu, den),
            'topics': _chu_de(user_id),
            'warnings': canh_bao,
        })
