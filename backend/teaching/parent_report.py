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
import json
from datetime import timedelta

from rest_framework.response import Response
from rest_framework.views import APIView

from chuong_trinh.dich_vu import tien_do_em
from common.clock import local_now, local_today
from common.db import q, q1
from common.permissions import IsSeniorTeachingStaff, can_see_class
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

#: Số tuần nhiều nhất in ở khối "nhịp từng tuần". Kỳ mặc định là 4 tuần, nhưng
#: giảng viên chọn được kỳ dài cả đợt — một bảng 30 dòng thì tờ giấy thành sổ
#: cái. Quá mức này thì chỉ in các tuần GẦN NHẤT và nói ra số tuần bị bỏ.
TUAN_TOI_DA = 13

#: Khối lẻ ở đầu kỳ ngắn hơn chừng này ngày thì GỘP vào tuần kế tiếp. Kỳ mặc
#: định là `den - 4 tuần … den` (hai đầu tính cả) = 29 ngày, tức 4 tuần + 1 ngày;
#: in riêng một "tuần" 1 ngày thì hàng ấy gần như toàn số 0 và đọc như con bỏ học.
NGAY_LE_TOI_THIEU = 4


def dau_ky_mac_dinh(class_id, user_id, den):
    """Đầu kỳ báo cáo MẶC ĐỊNH (khi người dùng không tự chọn ngày).

    `DEFAULT_WEEKS` tuần trước `den` — nhưng KHÔNG sớm hơn ngày lớp khai giảng
    (`classes.starts_on`) hay ngày em vào lớp (đợt đầu tiên). `user_id` None thì
    chỉ kẹp theo ngày khai giảng (màn gửi cả lớp).

    Vá 22/09/2026 (agent GV→PH F7): lớp khai giảng 13/09, tờ ngày 21/09 in kỳ
    "24/08 – 21/09", nên bảng "Con có học đều không" mở đầu bằng hai tuần toàn
    số 0 — phụ huynh đọc thành "hai tuần đầu con không học gì". Mọi nơi dựng kỳ
    mặc định (xem báo cáo, cấp chìa, gửi cả lớp, lệnh thử thư) đi qua hàm này;
    kỳ người dùng CHỌN thì giữ nguyên — đó là quyết định của họ.
    """
    tu = den - timedelta(weeks=DEFAULT_WEEKS)
    r = q1('''SELECT c.starts_on,
                     (SELECT MIN(m.joined_at)::date FROM class_members m
                      WHERE m.class_id = c.id AND m.user_id = %s) AS vao
              FROM classes c WHERE c.id = %s''', (user_id, class_id)) or {}
    for moc in (r.get('starts_on'), r.get('vao')):
        if moc and tu < moc <= den:
            tu = moc
    return tu


def _khoang_ngay(request, class_id=None, user_id=None):
    """Đọc ?from & ?to; không có ?from thì dùng `dau_ky_mac_dinh`. Trả (từ, đến, có_hợp_lệ)."""
    hom_nay = local_today()
    mac_dinh_tu = hom_nay - timedelta(weeks=DEFAULT_WEEKS)
    if class_id is not None and not (request.query_params.get('from') or '').strip():
        mac_dinh_tu = dau_ky_mac_dinh(class_id, user_id, hom_nay)

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


def _chuyen_can(class_id, user_id, tu, den, cac_dot=(), du_lieu=None):
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

    `du_lieu`: kết quả `_buoi_cua_em` đã lấy sẵn (tờ báo cáo dùng nó cho cả khối
    từng tuần — hai lượt hỏi cùng một thứ là hai cơ hội để hai khối lệch nhau).
    """
    d = du_lieu if du_lieu is not None else _buoi_cua_em(class_id, user_id, tu, den, cac_dot)
    buoi, da_dien_ra = d['buoi'], d['da_dien_ra']
    da_tick = [b['id'] for b in da_dien_ra if b['attendance_taken_at']]
    chua_tick = len(da_dien_ra) - len(da_tick)

    dem = {'present': 0, 'late': 0, 'absent': 0, 'excused': 0}
    for sid in da_tick:
        st = d['trang_thai'].get(sid)
        if st in dem:
            dem[st] += 1

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


def _buoi_cua_em(class_id, user_id, tu, den, cac_dot=()):
    """Buổi của lớp trong kỳ + dòng điểm danh của em — nguồn chung cho `_chuyen_can`
    (tổng kỳ) và `_nhip_tuan` (từng tuần). Ba bộ lọc: xem docstring `_chuyen_can`.

    Trả `{'buoi': mọi buổi trong kỳ và trong thời gian em ở lớp, 'da_dien_ra':
    buổi không huỷ và đã bắt đầu, 'trang_thai': {session_id: status}}`.
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
    #
    # NGOẠI LỆ (20/09/2026): buổi giảng viên ĐÃ TICK em thì là buổi của em, dù
    # nằm ngoài mọi đợt. `joined_at` là lúc học vụ BẤM NÚT, không phải lúc em
    # bước vào lớp — rà trên mock production: lớp khai giảng 13/09, học vụ nhập
    # em ngày 20/09, giảng viên đã điểm danh em hai buổi 14 và 16/09; màn giảng
    # viên nói "1 có mặt, 1 muộn", thẻ lớp của em và tờ gửi phụ huynh nói "chưa
    # có buổi nào được điểm danh". Luật chống đổ vắng nhầm vẫn nguyên: buổi
    # trước ngày ghi danh mà KHÔNG có dòng của em thì vẫn bị gạt.
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
        khoang.append('EXISTS (SELECT 1 FROM attendance a '
                      'WHERE a.session_id = s.id AND a.user_id = %s)')
        args.append(user_id)
        dieu_kien.append('(' + ' OR '.join(khoang) + ')')

    buoi = q('SELECT s.id, s.attendance_taken_at, s.status, s.starts_at '
             'FROM class_sessions s WHERE ' + ' AND '.join(dieu_kien), tuple(args))

    # Buổi đã huỷ: lớp nghỉ vì giảng viên ốm, không phải việc của em.
    # Buổi chưa tới: chưa xảy ra thì không thể thiếu điểm danh.
    da_dien_ra = [b for b in buoi
                  if b['status'] != 'cancelled' and b['starts_at'] and b['starts_at'] <= gio]
    da_tick = [b['id'] for b in da_dien_ra if b['attendance_taken_at']]
    trang_thai = {}
    if da_tick:
        for r in q("""SELECT session_id, status FROM attendance
                      WHERE user_id = %s AND session_id = ANY(%s)""", (user_id, da_tick)):
            trang_thai[r['session_id']] = r['status']
    return {'buoi': buoi, 'da_dien_ra': da_dien_ra, 'trang_thai': trang_thai}


def _cac_tuan(tu, den):
    """Chia `[tu, den]` (hai đầu tính cả) thành các khối 7 ngày KẾT THÚC ở `den`.

    Khối 7 ngày chứ không theo tuần lịch (thứ Hai–Chủ nhật): lớp học theo THỨ
    trong tuần, nên mỗi khối 7 ngày chứa đúng một lượt mỗi thứ — lớp T2/T4 thì
    khối nào cũng 2 buổi, và các hàng so được với nhau. Tuần lịch thì kỳ bắt đầu
    thứ Năm sẽ có hàng đầu 4 ngày, 1 buổi, đọc như con đi học ít đi một nửa.

    Phần lẻ đầu kỳ ngắn hơn `NGAY_LE_TOI_THIEU` ngày gộp vào khối kế tiếp (khối
    ấy dài hơn 7 ngày, và `days` nói ra điều đó). Trả list `(từ, đến)` cũ → mới.
    """
    khoi = []
    cuoi = den
    while cuoi >= tu:
        dau = max(tu, cuoi - timedelta(days=6))
        khoi.append([dau, cuoi])
        cuoi = dau - timedelta(days=1)
    if len(khoi) > 1 and (khoi[-1][1] - khoi[-1][0]).days + 1 < NGAY_LE_TOI_THIEU:
        le = khoi.pop()
        khoi[-1][0] = le[0]
    return [tuple(k) for k in reversed(khoi)]


def _nhip_tuan(class_id, user_id, tu, den, du_lieu):
    """Nhịp học TỪNG TUẦN trong kỳ — câu "con có học đều không".

    Định vị trung tâm chọn là "phụ huynh thấy con tiến bộ từng tuần", nhưng tới
    17/09/2026 tờ báo cáo chỉ có TỔNG của cả kỳ: 11 bài trong 4 tuần có thể là
    đều mỗi tuần 3 bài, hoặc 11 bài dồn vào tuần cuối — hai chuyện khác hẳn nhau
    với phụ huynh, và tổng không phân biệt được.

    Bốn cột, mỗi cột là việc CỦA EM trong tuần ấy:
      · đi học   — có mặt (kể cả muộn) / buổi có dòng điểm danh của em. CÙNG mẫu
                   số với `attendedPct`, lấy từ CÙNG `_buoi_cua_em`;
      · bài học  — sự kiện `lesson`, cùng nguồn với `study.lessonsDone` — nên cộng
                   các tuần lại ra đúng tổng kỳ (trừ khi kỳ dài quá `TUAN_TOI_DA`);
      · luyện tập — lượt phòng luyện bấm giờ (`drill`);
      · bài tập  — bài của LỚP NÀY em đã NỘP, theo ngày nộp. KHÔNG lấy sự kiện
                   `assignment`: sự kiện ấy ghi lúc giảng viên CHẤM, tức nó đo
                   nhịp của giảng viên, không phải của em.
    """
    tuan = _cac_tuan(tu, den)
    bo = max(0, len(tuan) - TUAN_TOI_DA)
    tuan = tuan[bo:]

    def o_cua(ngay_):
        for i, (a, b) in enumerate(tuan):
            if a <= ngay_ <= b:
                return i
        return None

    dong = [{'from': a.isoformat(), 'to': b.isoformat(), 'days': (b - a).days + 1,
             'attended': 0, 'attendanceCounted': 0, 'lessons': 0, 'drills': 0,
             'submissions': 0} for a, b in tuan]

    for b in du_lieu['da_dien_ra']:
        i = o_cua(b['starts_at'].date())
        st = du_lieu['trang_thai'].get(b['id'])
        # Chỉ bốn trạng thái mà `_chuyen_can` đếm — cùng mẫu số, không thì hàng
        # tuần và ô tổng kỳ chia cho hai thứ khác nhau.
        if i is None or not b['attendance_taken_at'] or st not in ('present', 'late', 'absent', 'excused'):
            continue
        dong[i]['attendanceCounted'] += 1
        if st in ('present', 'late'):
            dong[i]['attended'] += 1

    for r in q('''SELECT event_date, kind, COUNT(*) AS n FROM learning_events
                  WHERE user_id = %s AND kind IN ('lesson', 'drill')
                    AND event_date BETWEEN %s AND %s
                  GROUP BY event_date, kind''', (user_id, tu, den)):
        i = o_cua(r['event_date'])
        if i is not None:
            dong[i]['lessons' if r['kind'] == 'lesson' else 'drills'] += r['n']

    for r in q('''SELECT s.submitted_at::date AS ngay, COUNT(*) AS n
                  FROM submissions s JOIN assignments a ON a.id = s.assignment_id
                  WHERE s.user_id = %s AND a.class_id = %s
                    AND s.submitted_at::date BETWEEN %s AND %s
                  GROUP BY 1''', (user_id, class_id, tu, den)):
        i = o_cua(r['ngay'])
        if i is not None:
            dong[i]['submissions'] += r['n']

    return {'weeks': dong, 'omitted': bo}


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


def _thi_tai_trung_tam(user_id):
    """Kết quả thi thử TẠI TRUNG TÂM — nhập từ tờ PDF của hệ thống khảo thí (§48).

    KHÁC HẲN `study.mockAvg`, và không được gộp: kia là điểm luyện tập trong hệ
    thống (thang phần trăm, máy tự chấm theo ngân hàng câu hỏi của mình), còn đây
    là một kỳ thi THẬT do bên khảo thí tổ chức và chấm, thang 150. Trộn hai thang
    lại thành một con số là đẻ ra một điểm thứ ba mà không ai — kể cả giảng viên —
    đối chiếu lại được.

    Lấy HAI lượt gần nhất, vì câu đầu tiên phụ huynh hỏi khi cầm tờ báo cáo thứ
    hai là "so với lần trước thì sao".
    """
    cac = q('''SELECT ngay_thi, dot, tong_diem, tong_toi_da, diem_phan, don_vi
                 FROM ket_qua_thi_ngoai
                WHERE user_id = %s
                ORDER BY ngay_thi DESC, id DESC
                LIMIT 2''', (user_id,))
    if not cac:
        return None

    def _js(v):
        # Con trỏ thô trả cột `jsonb` dạng CHUỖI — xem `lessons/content.py`.
        return json.loads(v) if isinstance(v, str) else (v or [])

    moi = cac[0]
    truoc = cac[1] if len(cac) > 1 else None
    don_vi = _js(moi['don_vi'])
    # So sánh CHỈ khi cùng thang điểm. Hai kỳ khác thang (150 và 100) mà trừ nhau
    # thì ra một con số "tiến bộ" hoàn toàn bịa.
    so_sanh = None
    if truoc and truoc['tong_toi_da'] == moi['tong_toi_da']:
        so_sanh = {'date': truoc['ngay_thi'].isoformat(), 'round': truoc['dot'],
                   'score': truoc['tong_diem'],
                   'delta': moi['tong_diem'] - truoc['tong_diem']}
    return {
        'date': moi['ngay_thi'].isoformat(),
        'round': moi['dot'],
        'score': moi['tong_diem'],
        'max': moi['tong_toi_da'],
        'sections': _js(moi['diem_phan']),
        # Đơn vị kiến thức yếu nhất của CHÍNH kỳ thi ấy — cụ thể hơn "chủ đề cần
        # chú ý" tính từ dữ liệu luyện tập, vì nó là bài thi vừa làm xong.
        'weakUnits': sorted(don_vi, key=lambda v: v.get('pct', 0))[:TOP_N],
        'unitsMeasured': len(don_vi),
        'previous': so_sanh,
    }


def _khoa_cua_em(user_id, khoa_lop, comp):
    """Hợp phần em THẬT SỰ học: đã ghi danh, là khoá của lớp, hoặc đã có bài làm.

    `competency.compute` trả MỌI hợp phần của giáo trình — đúng cho bản đồ năng
    lực em tự xem, sai cho tờ giấy gửi về nhà. Đo 17/09/2026 trên lớp mẫu Định
    lượng: em chỉ ghi danh MỘT khoá mà tờ báo cáo in "Tư duy Định tính: đã học
    0/23 bài (0%)" và "Khoa học & Tiếng Anh: 0/26 (0%)" — phụ huynh đọc là con bỏ
    trống hai phần, trong khi con không học hai phần ấy ở trung tâm.

    Giữ cả khoá CÓ BÀI LÀM dù chưa ghi danh: em tự học thêm thì đó là việc thật,
    giấu đi là bớt công của em trên tờ giấy.
    """
    giu = {r['course_id'] for r in q('SELECT course_id FROM enrollments WHERE user_id = %s',
                                    (user_id,))}
    if khoa_lop:
        giu.add(khoa_lop)
    for t in comp.get('topics') or []:
        if t.get('lessonsDone') or t.get('confidence'):
            giu.add(t['course'])
    return giu


def _chu_de(user_id, khoa_lop=None):
    """Chủ đề cần chú ý và chủ đề đang mạnh — chỉ lấy những ô ĐO ĐƯỢC.

    Bỏ qua ô `status != 'ok'` là bắt buộc: một chủ đề chưa làm bài nào có
    `mastery = None`, và xếp nó vào "cần chú ý" là nói với phụ huynh rằng con
    yếu phần đó, trong khi sự thật là con chưa học tới.

    `courses` và `total` chỉ tính hợp phần em học (`_khoa_cua_em`).
    """
    comp = competency.compute(user_id)
    giu = _khoa_cua_em(user_id, khoa_lop, comp)
    cac_chu_de = [t for t in (comp.get('topics') or []) if t['course'] in giu]
    do_duoc = [t for t in cac_chu_de
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
        'total': len(cac_chu_de),
        'courses': [k for k in (comp.get('courses') or []) if k['id'] in giu],
    }


def _bai_tap_lop(class_id, user_id, tu, den):
    """Bài giảng viên giao cho LỚP NÀY trong kỳ, kèm điểm và nhận xét của em.

    Thêm 20/09/2026 sau khi rà luồng: giảng viên chấm 8/10 kèm nhận xét, nhưng
    tờ gửi phụ huynh chỉ có cột "Bài tập: 1" trong bảng tuần và mục chủ đề nói
    "chưa đủ bài làm" — thứ duy nhất một con người đã đọc và chấm lại không lên
    tờ giấy. Nhận xét của giảng viên là viết cho em và gia đình, nên in nguyên.

    Thuộc kỳ nếu bài được GIAO trong kỳ, hoặc HẠN NỘP rơi vào kỳ, hoặc em NỘP
    trong kỳ — bài giao tháng trước mà em nộp muộn tháng này vẫn thuộc kỳ này,
    và bài vừa giao hôm nay (hạn tuần sau) vẫn lên tờ như "chưa nộp, hạn …".
    Bài nháp (`draft`) em chưa từng thấy nên không in.
    """
    rows = q('''SELECT a.id, a.title, a.topic, a.due_at, a.max_score, a.status,
                       s.submitted_at, s.score, s.feedback, s.graded_at
                  FROM assignments a
                  LEFT JOIN submissions s ON s.assignment_id = a.id AND s.user_id = %s
                 WHERE a.class_id = %s AND a.status <> 'draft'
                   AND (a.created_at::date BETWEEN %s AND %s
                        OR a.due_at::date BETWEEN %s AND %s
                        OR s.submitted_at::date BETWEEN %s AND %s)
                 ORDER BY COALESCE(a.due_at, a.created_at), a.id''',
             (user_id, class_id, tu, den, tu, den, tu, den))
    return [{
        'id': r['id'], 'title': r['title'], 'topic': r['topic'],
        'dueAt': r['due_at'].isoformat() if r['due_at'] else None,
        'maxScore': float(r['max_score']) if r['max_score'] is not None else None,
        'submittedAt': r['submitted_at'].isoformat() if r['submitted_at'] else None,
        'score': float(r['score']) if r['score'] is not None else None,
        'feedback': r['feedback'],
        'gradedAt': r['graded_at'].isoformat() if r['graded_at'] else None,
    } for r in rows]


def dung_bao_cao(class_id, user_id, tu, den, canh_bao=None):
    """Dựng payload báo cáo. KHÔNG kiểm quyền — nơi gọi phải tự lo.

    Tách ra khỏi view (07/09/2026) vì nay có HAI đường tới cùng tờ giấy này:
    đường của giảng viên (`ParentReportView`, sau cổng `IsSeniorTeachingStaff`)
    và đường CÔNG KHAI bằng chìa (`teaching/parent_link.py`, cho phụ huynh mở
    từ tin Zalo). Hai đường mà hai bản dựng thì chúng sẽ trôi khỏi nhau, và
    kiểu trôi tệ nhất ở đây là bản công khai còn giữ một trường mà bản kia đã
    bỏ đi vì lý do riêng tư.

    Trả `(payload, loi)`. `loi` khác None thì payload là None.
    """
    canh_bao = list(canh_bao or [])

    # Lấy CẢ lượt học đã đóng: báo cáo cuối kỳ cho một em vừa học xong vẫn
    # phải in ra được. Ưu tiên lượt đang mở nếu có.
    # `chi_hoc_vien` là BẮT BUỘC ở đây, không phải để làm đẹp con số.
    # Tài khoản quản trị viên đang là thành viên lớp 1 (anh chủ sản phẩm
    # chốt giữ), nên thiếu bộ lọc này thì giảng viên in được "báo cáo gửi
    # phụ huynh" cho chính tài khoản quản trị — kèm email và số điện thoại
    # của nó. Đo 31/08/2026: HTTP 200, trả về admin@pe-hsa.vn.
    # TẤT CẢ các đợt, không phải một. Xem chú thích trong `_chuyen_can`.
    cac_dot = q('''SELECT m.joined_at, m.left_at, m.leave_reason,
                          m.teacher_comment, m.teacher_comment_at
                   FROM class_members m
                   JOIN users u ON u.id = m.user_id
                   WHERE m.class_id = %s AND m.user_id = %s
                     AND ''' + chi_hoc_vien('u') + '''
                   ORDER BY m.joined_at''', (class_id, user_id))
    if not cac_dot:
        return None, 'Không có học viên này trong lớp.'

    # Đợt MỚI NHẤT quyết định trạng thái và ghi chú hiện tại; ngày vào lấy
    # đợt đầu, ngày rời để trống nếu còn đợt nào đang mở.
    moi_nhat = max(cac_dot, key=lambda d: (d['left_at'] is None, d['joined_at']))
    thanh_vien = {
        'joined_at': cac_dot[0]['joined_at'],
        'left_at': None if any(d['left_at'] is None for d in cac_dot)
                   else max(d['left_at'] for d in cac_dot),
        'leave_reason': moi_nhat['leave_reason'],
        # Nhận xét giảng viên viết CHO phụ huynh (§62a) — lấy bản ghi muộn nhất qua
        # mọi đợt. KHÔNG đọc `note`: đó là ghi chú nội bộ (lý do rời, chuyển lớp).
        'teacher_comment': max(
            (d for d in cac_dot if d['teacher_comment']),
            key=lambda d: d['teacher_comment_at'] or d['joined_at'],
            default={'teacher_comment': None})['teacher_comment'],
    }

    lop = q1('SELECT id, name, code, course_id, teacher_id FROM classes WHERE id=%s',
             (class_id,))
    if not lop:
        return None, 'Không tìm thấy lớp này.'
    gv = q1('SELECT name FROM users WHERE id=%s', (lop['teacher_id'],))         if lop['teacher_id'] else None
    em = q1('''SELECT id, name, email, phone, parent_name, parent_phone, parent_email
                FROM users WHERE id=%s''', (user_id,))
    if not em:
        return None, 'Không tìm thấy học viên.'

    buoi_em = _buoi_cua_em(class_id, user_id, tu, den,
                           cac_dot=[(d['joined_at'], d['left_at']) for d in cac_dot])

    return {
        'student': {'id': em['id'], 'name': em['name'],
                    'email': em['email'], 'phone': em['phone']},
        # Người NHẬN tờ báo cáo này. Trả về chuỗi rỗng chứ không None khi
        # chưa ai điền: màn hình cần phân biệt "chưa điền" với "đã điền
        # rồi xoá", và cả hai đều là '' — nên đừng bịa ra hai trạng thái.
        # `email` từ 17/09/2026: email là kênh gửi CHÍNH từ 07/09, nhưng màn giảng
        # viên chỉ nhận được số Zalo nên in "Chưa có số Zalo của phụ huynh" cho cả
        # em đã có email. Đường công khai không mang khoá này (`rut_gon_cho_link`).
        'parent': {'name': em['parent_name'] or '',
                   'phone': em['parent_phone'] or '',
                   'email': em['parent_email'] or ''},
        'class': {'id': lop['id'], 'name': lop['name'], 'code': lop['code'],
                  'teacher': gv['name'] if gv else None},
        'membership': {
            'joinedAt': thanh_vien['joined_at'].isoformat()
                        if thanh_vien['joined_at'] else None,
            'leftAt': thanh_vien['left_at'].isoformat()
                      if thanh_vien['left_at'] else None,
            'status': trang_thai(thanh_vien['left_at'], thanh_vien['leave_reason']),
            # Nhận xét của giảng viên VỀ lớp/em này, viết để phụ huynh đọc —
            # khác nhật ký em tự ghi (ranh giới 1) và khác ghi chú NỘI BỘ
            # `class_members.note` (lý do rời/chuyển lớp — không bao giờ in ra).
            'teacherNote': thanh_vien['teacher_comment'],
            # Số ĐỢT em ở lớp. In ra khi > 1 để người đọc hiểu vì sao ngày
            # vào và ngày rời không liền một mạch.
            'stints': len(cac_dot),
        },
        'period': {'from': tu.isoformat(), 'to': den.isoformat(),
                   'weeks': DEFAULT_WEEKS},
        'attendance': _chuyen_can(class_id, user_id, tu, den, du_lieu=buoi_em),
        'weekly': _nhip_tuan(class_id, user_id, tu, den, buoi_em),
        'study': _hoc_tap(user_id, tu, den),
        # Kỳ thi THẬT tại trung tâm. `None` khi chưa nhập tờ nào — màn hình và tệp
        # PDF phải giấu hẳn mục này, đừng in "chưa có dữ liệu" cho một thứ phụ
        # huynh còn không biết là có tồn tại.
        'centerExam': _thi_tai_trung_tam(user_id),
        'topics': _chu_de(user_id, lop['course_id']),
        'assignments': _bai_tap_lop(class_id, user_id, tu, den),
        # Tiến độ chương trình của em tới hôm nay (E1); None khi lớp chưa nhận khung.
        'chuongTrinh': tien_do_em(user_id, [class_id]).get(class_id),
        'warnings': canh_bao,
    }, None


def rut_gon_cho_link(payload):
    """Bỏ những trường KHÔNG được đi qua một đường mở bằng chìa.

    Chìa là chìa: ai cầm link cũng xem được — chuyển tiếp trong nhóm chat, máy
    mượn, điện thoại chung. Nên tờ đi qua đường ấy phải mỏng hơn tờ giảng viên
    xem.

    Bỏ `student.email` và `student.phone`: chính vì hai trường này mà cổng của
    `ParentReportView` là `IsSeniorTeachingStaff` chứ không phải cửa chung —
    "càng nhiều vai trò thì càng nhiều người nhìn thấy dữ liệu của một đứa
    trẻ" (§8 đặc tả). Một đường KHÔNG CÓ VAI NÀO thì càng phải bỏ.

    Bỏ `parent.phone` và `parent.email`: phụ huynh không cần đọc lại liên lạc
    của chính mình, và chúng là số/địa chỉ thật nằm sau một chìa có thể bị
    chuyển tiếp.

    GIỮ `membership.teacherNote`: nó được viết ra ĐỂ phụ huynh đọc (khác nhật
    ký riêng của em — xem ranh giới 1 ở đầu tệp). Từ 25/09 nó lấy từ cột
    `teacher_comment` (§62a), không còn từ ghi chú nội bộ `note`.
    """
    ra = dict(payload)
    ra['student'] = {k: v for k, v in payload['student'].items()
                     if k not in ('email', 'phone')}
    ra['parent'] = {'name': payload['parent']['name']}
    return ra


class ParentReportView(APIView):
    """GET /api/teach/classes/<id>/students/<uid>/parent-report?from=&to=

    Trả dữ liệu cho tờ báo cáo gửi phụ huynh. Bản in nằm ở frontend — cố ý
    KHÔNG sinh PDF ở máy chủ: trình duyệt in ra PDF đã đủ tốt, và thêm một bộ
    sinh PDF là thêm một phông chữ tiếng Việt phải cài trên Render, một khác
    biệt nữa giữa máy dev và production, và một chỗ nữa để hỏng.
    """
    # `IsSeniorTeachingStaff`, KHÔNG phải cửa chung: tờ này in ra email và số điện
    # thoại của học viên, và trợ giảng không được xem (anh Sơn chốt 01/09/2026 —
    # §8 của đặc tả: càng nhiều vai trò thì càng nhiều người nhìn thấy dữ liệu
    # của một đứa trẻ).
    permission_classes = [IsSeniorTeachingStaff]

    def get(self, request, class_id, user_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)

        tu, den, ngay_hop_le, dao_ngay = _khoang_ngay(request, class_id, user_id)
        canh_bao = []
        if not ngay_hop_le:
            canh_bao.append('Ngày lọc không đọc được (cần dạng YYYY-MM-DD) — '
                            'đang dùng kỳ mặc định %d tuần gần nhất.' % DEFAULT_WEEKS)
        if dao_ngay:
            canh_bao.append('Ngày bắt đầu đang muộn hơn ngày kết thúc nên đã đổi chỗ '
                            'hai ngày. Kiểm lại kỳ báo cáo trước khi in.')

        data, loi = dung_bao_cao(class_id, user_id, tu, den, canh_bao)
        if loi:
            return Response({'error': loi}, status=404)
        return Response(data)
