"""Bảng điều khiển TRUNG TÂM — đặc tả ERP §6, nửa "Trung tâm".

Cho tới hôm nay mọi báo cáo đều dừng ở CẤP LỚP: `class_report` trả lời rất kỹ
"lớp này đang thế nào", nhưng không ai trả lời "TRUNG TÂM đang thế nào". Quản lý
học vụ muốn biết lớp nào đang rơi, đợt này so với đợt trước ra sao, thì phải mở
từng lớp một rồi tự cộng trong đầu.

── BA CON SỐ, VÀ VÌ SAO ĐÚNG BA ─────────────────────────────────────────────
Tra cứu 31/08/2026 về chỉ số vận hành của trung tâm dạy thêm (Tutorbase, và
tài liệu về hệ thống thông tin học sinh của ModernCampus):

1. **Tỉ lệ giữ chân** là chỉ số sống còn của mô hình dạy thêm — giữ được người
   quan trọng hơn tuyển thêm người. Mốc tham chiếu: ≥80% là khoẻ, <70% là dấu
   hiệu hỏng ở khâu đón học viên, chất lượng giảng viên, hoặc học phí lệch.
   Con số này CHỈ tính được từ 31/08/2026, khi `class_members.leave_reason`
   (§36) tách được "học xong" khỏi "bỏ giữa chừng". Trước đó cả hai là cùng một
   giá trị `left_at IS NOT NULL`, nên mọi lớp kết thúc đều trông như bỏ học 100%.

2. **So sánh theo ĐỢT** để bắt sớm đợt nào rơi. Một trung tâm mở lớp theo mùa
   thi, nên đợt là đơn vị so sánh tự nhiên — và đó là lý do bảng `terms` tồn tại.

3. **Chỉ báo sớm** ở tầng trung tâm là ba thứ mà `class_report` đã đo cho từng
   em: chuyên cần, xu hướng điểm thi thử, và tiến độ bài học. Ở đây chỉ cần cuộn
   chúng lên cấp lớp rồi cấp đợt — KHÔNG phát minh chỉ số mới, để con số trung
   tâm nhìn thấy và con số giảng viên nhìn thấy luôn truy được về cùng một gốc.

── V2 (1.4a, 24/09/2026): BỐN CÂU HỎI CỦA GHI CHÚ HỌP ────────────────────
TopHSA hỏi: "hiện nay bao nhiêu lớp học, bao nhiêu rời lớp, giáo viên điểm danh,
bao nhiêu tài khoản lâu không hoạt động". Mỗi câu một khối trong phản hồi:
  · `summary.classesByType` — lớp NHÓM / GIA SƯ (§54) theo trạng thái;
  · `roiLop` — rời lớp trong KỲ XEM (`tu`..`den`), theo lý do, theo loại lớp,
    6 tháng gần nhất và 50 dòng mới nhất;
  · `giangVien` — từng giảng viên: buổi đã dạy / đã điểm danh / chưa / muộn;
  · `taiKhoanNgu` — tài khoản đang mở không hoạt động 7/14/30 ngày (§56).
Bảng từng lớp nay xếp LỚP CẦN NGƯỜI NHÌN lên đầu và cắt còn 50 dòng ở cửa API
(TopHSA có ~400 lớp gia sư); mọi con số đếm vẫn tính trên TOÀN BỘ lớp.

── SỐ CÂU TRUY VẤN LÀ THIẾT KẾ ──────────────────────────────────────────────
Hàm này chạy TỐI ĐA 8 câu, không phụ thuộc số lớp (có phép kiểm đếm câu với 2 và
20 lớp: `tests_tong_quan.py`). Gọi `class_report` cho từng lớp sẽ là 6 câu × N
lớp — hai chục lớp là 120 lượt tới Neon cho một màn hình. Đó chính là cái ngân
sách vòng gọi ghi ở đầu `teaching/admin_users.py`. Hai khối v2 dùng một CTE rồi
đọc nó HAI lần trong CÙNG một câu (`json_agg`) — tách hai câu là tính lại CTE
(đắt nhất ở tài khoản ngủ: một MAX sự kiện cho từng người) và thêm một vòng gọi.

── LUÔN TƯƠI ────────────────────────────────────────────────────────────────
Không bộ đệm nào ở cả hai phía: trang `force-dynamic`, `serverFetch` gọi với
`cache: 'no-store'`, và phản hồi mang `generatedAt` để màn hình ghi "Cập nhật
lúc …" — "báo cáo realtime" của khách nghĩa là mở trang là số của lúc ấy.

── KHÔNG ĐỌC ĐƯỢC THÌ NÓI, KHÔNG VIẾT 0 ─────────────────────────────────────
Cùng luật với `reports.py`: mảng nào hỏng thì tên nó vào `incomplete`, và tỉ lệ
tính không được thì trả `None` chứ không phải 0. Một bảng điều khiển trung tâm
hiện "tỉ lệ bỏ học 0%" vì câu tra hỏng là thứ nguy hiểm hơn hẳn một màn hình lỗi.
Ba khối v2 cũng vậy: hỏng thì khối ấy là `None` và tên nó vào `incomplete`.
"""
import logging
from datetime import date, timedelta

from django.db import DatabaseError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.hoat_dong import sql_hoat_dong
from common.clock import local_now, local_today
from common.db import q, q1
from common.events import KIND_ATTENDANCE
from common.permissions import IsAdminOrAcademic
from stats.goals import as_date
from teaching.attendance import KHONG_TINH, ti_le
from teaching.sessions import DEFAULT_SESSION_MINUTES
from teaching.vocab import LEAVE_REASONS, LOAI_LOP, TRANG_THAI_LOP, chi_hoc_vien

logger = logging.getLogger(__name__)

#: Ngưỡng tham chiếu cho tỉ lệ giữ chân, theo chuẩn ngành dạy thêm (tra cứu
#: 31/08/2026). Để lộ thành hằng số vì đây là một GIẢ ĐỊNH về mô hình kinh
#: doanh, và giả định thì phải nhìn thấy được mới bàn lại được.
GIU_CHAN_TOT = 80
GIU_CHAN_BAO_DONG = 70

#: Mốc "lâu không hoạt động" (ngày), tăng dần. Mốc ĐẦU cũng là ngưỡng vào danh
#: sách từng em. Màn hình vẽ cột theo mảng này, không gõ lại con số.
NGUONG_NGU = (7, 14, 30)
#: Điểm danh MUỘN = ghi sau khi buổi KẾT THÚC quá bấy nhiêu giờ. Đo từ kết thúc
#: chứ không từ bắt đầu: buổi 3 tiếng tick lúc tan lớp không phải là muộn.
TRE_DIEM_DANH_GIO = 24
#: Cửa API cắt bảng từng lớp còn bấy nhiêu dòng (xếp lớp cần nhìn lên đầu).
TRAN_BANG_LOP = 50
#: Độ dài hai danh sách từng dòng (rời lớp, tài khoản ngủ).
TRAN_DANH_SACH = 50
#: Số tháng của dải "rời lớp theo tháng", tháng cuối là tháng của `den`.
SO_THANG = 6


def _mot_phan_tram(tu, mau):
    """Phần trăm, hoặc None khi KHÔNG có mẫu số.

    None chứ không 0: "chưa em nào rời lớp" và "chưa có ai để mà tính" là hai
    chuyện khác nhau, và một bảng điều khiển gộp chúng lại sẽ nói dối đúng vào
    lúc trung tâm mới mở đợt.

    DÙNG CHO tỉ lệ giữ chân và tiến độ bài. KHÔNG dùng cho chuyên cần: chuyên
    cần có một định nghĩa riêng, có tên, ở `attendance.ti_le` — kèm cả một
    trang lý lẽ về việc chọn mẫu số nào. Hai hàm này hôm nay cho ra cùng một
    con số, nên đổi `_mot_phan_tram` (chẳng hạn làm tròn xuống cho tỉ lệ bỏ
    học) sẽ lặng lẽ đổi luôn chuyên cần của cả trung tâm — mà chuyên cần là
    thứ đi ra khỏi hệ thống, in vào tờ báo cáo gửi phụ huynh.
    """
    return round(tu * 100 / mau) if mau else None


def _xep_van_de(c):
    """Khoá xếp bảng từng lớp: lớp CẦN NGƯỜI NHÌN lên đầu.

    Bảng bị cắt còn `TRAN_BANG_LOP` dòng ở cửa API, nên thứ tự quyết định lớp nào
    còn nằm trên màn hình. Theo đúng thứ tự khối "Hôm nay cần làm gì" ở màn hình:
    việc làm SAI CON SỐ trước (buổi chưa điểm danh, lớp chưa có giảng viên, rời
    lớp chưa ghi lý do), rồi việc chỉ đáng lo (vượt sĩ số, tỉ lệ bỏ cao). Lớp đã
    kết thúc/huỷ xuống cuối — ở đó không còn gì để làm hôm nay.
    """
    dang_chay = c['status'] == 'active'
    return (
        not dang_chay,
        -c['sessionsUnmarked'],
        not (dang_chay and c['teacherId'] is None),
        -c['leftUnknown'],
        not (c['capacity'] is not None and c['active'] > c['capacity']),
        -(c['dropRate'] or 0),
        (c['name'] or '').lower(),
    )


def _dau_thang_lui(ngay, so_thang):
    """Ngày 1 của tháng cách tháng của `ngay` về trước `so_thang` tháng."""
    nam, thang = ngay.year, ngay.month - so_thang
    while thang < 1:
        thang += 12
        nam -= 1
    return date(nam, thang, 1)


def tong_quan(term_id=None, tu=None, den=None, tran_lop=None):
    """Số liệu toàn trung tâm, gộp theo lớp rồi theo đợt. Trả dict.

    ``term_id`` lọc theo một đợt; None = mọi lớp (tài khoản ngủ thì luôn là toàn
    trung tâm — tài khoản không thuộc đợt nào).
    ``tu``/``den`` (date) — KỲ XEM của "rời lớp" và "điểm danh"; mặc định từ đầu
    tháng của ``den`` tới hôm nay, cả ngày ``den`` được tính.
    ``tran_lop`` — cắt bảng từng lớp còn N dòng; None = đủ (các phép kiểm dò lớp
    của chính mình theo id nên cần đủ). Số đếm luôn tính trên MỌI lớp.
    """
    nay = local_now()
    den = den or nay.date()
    tu = tu or den.replace(day=1)
    thieu = []
    dieu_kien, args = ['TRUE'], []
    if term_id is not None:
        dieu_kien.append('c.term_id = %s')
        args.append(term_id)
    where = ' AND '.join(dieu_kien)
    # Cùng bộ lọc, dạng THAM SỐ CÓ TÊN cho các câu v2 — ba câu ấy có nhiều tham
    # số, và thứ tự `%s` lệch một ô là lọc sai lặng lẽ chứ không báo lỗi.
    loc_lop = 'c.term_id = %(term_id)s' if term_id is not None else 'TRUE'

    # ── Câu 1: lớp + đợt + ghi danh, tách theo lý do rời lớp ────────────────
    #
    # Bộ lọc học viên nằm trong TỬNG PHÉP ĐẾM, không nằm ở mệnh đề WHERE.
    # Bản đầu (31/08/2026) đặt `AND (m.id IS NULL OR mu.id IS NOT NULL)` ở
    # WHERE: lớp rỗng thì giữ được, nhưng lớp có thành viên mà KHÔNG thành viên
    # nào là học viên thì mọi dòng bị loại — cả lớp rơi khỏi GROUP BY và biến
    # mất khỏi bảng điều khiển, `classCount` thiếu mà không câu lỗi nào.
    # Không phải giả định: tài khoản quản trị viên đang là thành viên lớp 1, nên
    # một lớp mới mở mà quản trị viên vào xem trước khi xếp học viên là đúng cảnh đó.
    lop = q('''SELECT c.id, c.code, c.name, c.status, c.course_id, c.capacity,
                      c.term_id, t.name AS term_name, t.code AS term_code,
                      c.class_type, c.teacher_id, u.name AS teacher_name,
                      COUNT(m.id) FILTER (WHERE hv AND m.left_at IS NULL)    AS dang_hoc,
                      COUNT(m.id) FILTER (WHERE hv)                           AS tung_ghi_danh,
                      COUNT(m.id) FILTER (WHERE hv
                                            AND m.leave_reason = 'completed') AS hoc_xong,
                      COUNT(m.id) FILTER (WHERE hv
                                            AND m.leave_reason = 'dropped')   AS bo_giua,
                      COUNT(m.id) FILTER (WHERE hv AND m.left_at IS NOT NULL
                                            AND m.leave_reason IS NULL)       AS roi_khong_ro
               FROM classes c
               LEFT JOIN terms t ON t.id = c.term_id
               LEFT JOIN users u ON u.id = c.teacher_id
               LEFT JOIN class_members m ON m.class_id = c.id
               LEFT JOIN LATERAL (
                   SELECT TRUE AS hv FROM users mu
                   WHERE mu.id = m.user_id AND ''' + chi_hoc_vien('mu') + '''
               ) hvq ON TRUE
               WHERE ''' + where + '''
               GROUP BY c.id, t.name, t.code, u.name
               ORDER BY c.status, c.name''', tuple(args))
    ids = [r['id'] for r in lop]

    # ── Câu 2: chuyên cần gộp theo lớp ──────────────────────────────────────
    cham_can = {}
    if ids:
        try:
            khong = ', '.join("'%s'" % t for t in KHONG_TINH)
            for r in q('''SELECT s.class_id,
                                 COUNT(*)                                     AS tick,
                                 COUNT(*) FILTER (WHERE a.status IN ('present','late')) AS co_mat
                          FROM attendance a
                          JOIN class_sessions s ON s.id = a.session_id
                          JOIN users u ON u.id = a.user_id
                          WHERE s.class_id = ANY(%s) AND s.status NOT IN (''' + khong + ''')
                            AND ''' + chi_hoc_vien('u') + '''
                          GROUP BY s.class_id''', (ids,)):
                cham_can[r['class_id']] = r
        except DatabaseError:
            logger.error('[overview] KHÔNG đọc được chuyên cần cho %d lớp', len(ids))
            thieu.append('attendance')

    # ── Câu 3: buổi học đã diễn ra & đã điểm danh ───────────────────────────
    buoi = {}
    if ids:
        try:
            khong = ', '.join("'%s'" % t for t in KHONG_TINH)
            # `starts_at <= now`: buổi CHƯA TỚI thì chưa thể thiếu điểm danh.
            # `parent_report.py` đã vá đúng chỗ này; đường này thì quên, và hậu
            # quả in thẳng ra màn hình quản lý: "N buổi đã dạy nhưng chưa ai
            # điểm danh" với N gồm cả buổi tuần sau. Lớp nào xếp lịch trước cho cả
            # kỳ trông như bỏ bê nhất — càng chuẩn bị kỹ càng bị quy trách nhiệm nặng.
            for r in q('''SELECT class_id, COUNT(*) AS tong,
                                 COUNT(*) FILTER (WHERE attendance_taken_at IS NOT NULL) AS da_tick
                          FROM class_sessions
                          WHERE class_id = ANY(%s) AND status NOT IN (''' + khong + ''')
                            AND starts_at <= %s
                          GROUP BY class_id''', (ids, nay)):
                buoi[r['class_id']] = r
        except DatabaseError:
            logger.error('[overview] KHÔNG đọc được buổi học')
            thieu.append('sessions')

    # ── Câu 4: học tập gộp theo lớp (bài xong + điểm thi thử + học 7 ngày) ──
    hoc = {}
    if ids:
        try:
            # HAI bộ lọc dưới đây phải khớp với MẪU SỐ ở phần ghép, nếu không tử
            # số và mẫu số đếm hai TẬP NGƯỜI khác nhau:
            #
            #  · `m.left_at IS NULL` — mẫu số nhân với `dang_hoc`, nên tử số cũng
            #    chỉ được tính người ĐANG học. Thiếu vế này thì lớp càng nhiều em
            #    bỏ học trông càng tiến độ tốt, và điểm thi thử của người đã bỏ học
            #    từ nhiều tháng trước vẫn kéo trung bình cả đợt xuống.
            #    Đo trên lớp thật duy nhất (31/08/2026): bản cũ 13% → bản mới 11%,
            #    chính là 1 bài của một em đã rời lớp. Độ lệch nhỏ vì lớp đó mới có
            #    một người rời; nó lớn dần theo đúng tỷ lệ bỏ học.
            #
            #  · `e.course_id = c.course_id` cho phép đếm BÀI — mẫu số là tổng số
            #    bài của KHOÁ mà lớp đang dạy, nên bài em ấy tự học ở khoá khác
            #    không được cộng vào.
            #    CHƯA ĐO ĐƯỢC trên dữ liệu thật: hiện 100% sự kiện `kind='lesson'`
            #    đều thuộc `hsa_quantitative`, nên chưa có bài xuyên khoá nào để lệch.
            #    Giữ bộ lọc vì mẫu số ĐÃ bó theo khoá — tử số không bó là sai ngay
            #    ngày TopHSA mở khoá thứ hai cho cùng một học viên.
            #
            #    `c.course_id IS NULL` = lớp ôn CẢ BA hợp phần — cùng luật với
            #    `reports.class_report` (tổng cả ba khoá). Bản trước chỉ có vế
            #    `e.course_id = c.course_id`, mà NULL không bằng gì, nên lớp ôn trọn
            #    HSA LUÔN hiện "Tiến độ —" ở đây trong khi báo cáo lớp có số — đúng
            #    kiểu "hai bên lệch nhau" mà màn hình này hứa là không có. Đo 17/09/2026
            #    trên lớp mẫu "Tăng tốc HSA cuối tuần".
            #
            # KHÔNG áp bộ lọc khoá cho ĐỀ THI THỬ: một lượt thi thử là bài thi cả
            # ba hợp phần HSA, không thuộc riêng khoá nào. (Cột thi thử còn trả để
            # màn hình CŨ không vỡ khi hai bên deploy lệch nhau; màn hình mới thôi
            # vẽ nó — gỡ hẳn cùng việc bỏ thi, mục 1.5 của kế hoạch 24/09.)
            #
            # `hoc_7` (1.4a): số em đang học có sự kiện học trong 7 ngày qua —
            # thay cột thi thử trên màn hình. Cùng định nghĩa "hoạt động" với
            # `tai_khoan_ngu` (bỏ điểm danh, bỏ sự kiện ở tương lai); xem đó.
            for r in q('''SELECT m.class_id,
                                 COUNT(*) FILTER (WHERE e.kind = 'lesson'
                                              AND (c.course_id IS NULL
                                                   OR e.course_id = c.course_id)) AS bai,
                                 COUNT(*) FILTER (WHERE e.kind = 'mock')    AS luot_de,
                                 AVG(e.score * 100.0 / NULLIF(e.max_score, 0))
                                     FILTER (WHERE e.kind = 'mock')         AS diem_tb,
                                 COUNT(DISTINCT m.user_id) FILTER (
                                     WHERE e.kind <> %(dd)s AND e.occurred_at > %(moc7)s
                                       AND e.occurred_at <= %(nay)s)       AS hoc_7
                          FROM class_members m
                          JOIN users u ON u.id = m.user_id
                          JOIN classes c ON c.id = m.class_id
                          JOIN learning_events e ON e.user_id = m.user_id
                          WHERE m.class_id = ANY(%(ids)s) AND m.left_at IS NULL
                            AND ''' + chi_hoc_vien('u') + '''
                            AND (e.kind IN ('lesson','mock')
                                 OR (e.kind <> %(dd)s AND e.occurred_at > %(moc7)s
                                     AND e.occurred_at <= %(nay)s))
                          GROUP BY m.class_id''',
                       {'ids': ids, 'dd': KIND_ATTENDANCE, 'nay': nay,
                        'moc7': nay - timedelta(days=7)}):
                hoc[r['class_id']] = r
        except DatabaseError:
            logger.error('[overview] KHÔNG đọc được dữ liệu học tập')
            thieu.append('study')

    # ── Câu 5: tổng số bài của từng khoá, làm mẫu số tiến độ ────────────────
    tong_bai = {}
    try:
        tong_bai = {r['course_id']: r['n'] for r in q(
            "SELECT course_id, COUNT(*) AS n FROM lessons "
            "WHERE module IS NOT NULL AND module <> '' GROUP BY course_id")}
    except DatabaseError:
        thieu.append('lessons')

    # ── Ghép ────────────────────────────────────────────────────────────────
    hong_hoc_tap = 'study' in thieu
    ra_lop = []
    for r in lop:
        cc = cham_can.get(r['id']) or {}
        b = buoi.get(r['id']) or {}
        h = hoc.get(r['id']) or {}
        # Mẫu số cùng phạm vi với tử số: khoá của lớp, hoặc cả ba khoá khi lớp không
        # gắn khoá — y như `reports.class_report`.
        so_bai_khoa = (tong_bai.get(r['course_id']) if r['course_id']
                       else sum(tong_bai.values())) or 0
        mau_bai = so_bai_khoa * (r['dang_hoc'] or 0)
        # "Rời lớp có lý do" mới là mẫu số của tỉ lệ giữ chân. Người rời lớp mà
        # chưa ai ghi lý do KHÔNG được tính vào cả tử lẫn mẫu — đoán họ bỏ học
        # là thổi phồng con số xấu, đoán họ học xong là giấu con số xấu. Số đó
        # báo riêng ở `leftUnknown` để trung tâm biết còn bao nhiêu dòng cần ghi.
        roi_co_ly_do = (r['hoc_xong'] or 0) + (r['bo_giua'] or 0)
        ra_lop.append({
            'id': r['id'], 'code': r['code'], 'name': r['name'], 'status': r['status'],
            'classType': r['class_type'],
            'termId': r['term_id'], 'termName': r['term_name'], 'termCode': r['term_code'],
            'teacherId': r['teacher_id'],
            'teacherName': r['teacher_name'], 'capacity': r['capacity'],
            'active': r['dang_hoc'] or 0,
            'enrolledEver': r['tung_ghi_danh'] or 0,
            'completed': r['hoc_xong'] or 0,
            'dropped': r['bo_giua'] or 0,
            'leftUnknown': r['roi_khong_ro'] or 0,
            # Tỉ lệ bỏ giữa chừng trên số người ĐÃ rời lớp có ghi lý do.
            'dropRate': _mot_phan_tram(r['bo_giua'] or 0, roi_co_ly_do),
            'sessionsHeld': b.get('tong') or 0,
            'sessionsMarked': b.get('da_tick') or 0,
            # Buổi đã diễn ra mà chưa ai điểm danh — việc còn tồn của giảng viên.
            'sessionsUnmarked': max(0, (b.get('tong') or 0) - (b.get('da_tick') or 0)),
            'attendedPct': ti_le(cc.get('co_mat') or 0, cc.get('tick') or 0),
            # KHÔNG đọc được thì trả None, KHÔNG trả 0 — đúng luật ghi ở đầu
            # module. Bản đầu để `h` rỗng đi tiếp thành `_mot_phan_tram(0, mẫu)` = 0,
            # nên một câu SQL hỏng làm CẢ TRUNG TÂM hiện "Tiến độ 0%" — trông y
            # hệt một trung tâm chưa ai học bài nào. Màn hình vẽ `—` cho None và
            # `0%` cho 0: hai thứ đó phải khác nhau ở đây thì mới khác nhau trên
            # màn hình.
            'lessonsDone': None if hong_hoc_tap else (h.get('bai') or 0),
            'progressPct': (None if hong_hoc_tap
                            else _mot_phan_tram(h.get('bai') or 0, mau_bai)),
            'activeLearners7d': None if hong_hoc_tap else (h.get('hoc_7') or 0),
            'mockCount': None if hong_hoc_tap else (h.get('luot_de') or 0),
            'mockAvg': round(float(h['diem_tb'])) if h.get('diem_tb') is not None else None,
        })

    # ── Cuộn lên cấp ĐỢT ────────────────────────────────────────────────────
    theo_dot = {}
    for c in ra_lop:
        k = c['termId']
        d = theo_dot.setdefault(k, {
            'termId': k, 'termName': c['termName'] or 'Chưa thuộc đợt nào',
            'termCode': c['termCode'], 'classes': 0, 'active': 0, 'enrolledEver': 0,
            'completed': 0, 'dropped': 0, 'leftUnknown': 0,
            '_comat': 0, '_tick': 0, '_de': 0, '_diem': 0.0,
        })
        d['classes'] += 1
        for k2 in ('active', 'enrolledEver', 'completed', 'dropped', 'leftUnknown'):
            d[k2] += c[k2]
        cc = cham_can.get(c['id']) or {}
        d['_comat'] += cc.get('co_mat') or 0
        d['_tick'] += cc.get('tick') or 0
        if c['mockAvg'] is not None:
            d['_de'] += c['mockCount']
            d['_diem'] += c['mockAvg'] * c['mockCount']

    dot = []
    for d in theo_dot.values():
        roi_co_ly_do = d['completed'] + d['dropped']
        dot.append({
            k: v for k, v in d.items() if not k.startswith('_')
        } | {
            'attendedPct': ti_le(d['_comat'], d['_tick']),
            'dropRate': _mot_phan_tram(d['dropped'], roi_co_ly_do),
            # Giữ chân = phần KHÔNG bỏ giữa chừng. Ngưỡng tham chiếu ở hằng số
            # đầu module; màn hình tô màu theo đó.
            'retentionPct': (None if not roi_co_ly_do
                             else _mot_phan_tram(d['completed'], roi_co_ly_do)),
            'mockAvg': round(d['_diem'] / d['_de']) if d['_de'] else None,
        })
    dot.sort(key=lambda x: (x['termId'] is None, -(x['termId'] or 0)))

    # ── Lớp theo loại × trạng thái (§54) ────────────────────────────────────
    # Khoá lấy từ từ vựng (`vocab`), không từ dữ liệu: loại chưa có lớp nào vẫn
    # hiện số 0 — "0 lớp gia sư" là một câu trả lời, thiếu dòng thì không phải.
    theo_loai = {k: dict({'total': 0}, **{s: 0 for s in TRANG_THAI_LOP}) for k in LOAI_LOP}
    for c in ra_lop:
        o = theo_loai.setdefault(c['classType'] or 'nhom',
                                 dict({'total': 0}, **{s: 0 for s in TRANG_THAI_LOP}))
        o['total'] += 1
        o[c['status']] = o.get(c['status'], 0) + 1

    # ── Ba khối v2 — mỗi khối hỏng riêng, nói riêng ─────────────────────────
    try:
        roi_lop = _roi_lop(loc_lop, term_id, tu, den)
    except DatabaseError:
        logger.error('[overview] KHÔNG đọc được rời lớp', exc_info=True)
        thieu.append('leavers')
        roi_lop = None
    try:
        giang_vien = _diem_danh_giang_vien(loc_lop, term_id, tu, den, nay, ra_lop)
    except DatabaseError:
        logger.error('[overview] KHÔNG đọc được điểm danh của giảng viên', exc_info=True)
        thieu.append('teachers')
        giang_vien = None
    try:
        ngu = tai_khoan_ngu()
    except DatabaseError:
        logger.error('[overview] KHÔNG đọc được tài khoản không hoạt động', exc_info=True)
        thieu.append('accounts')
        ngu = None

    tong_ghi_danh = sum(c['enrolledEver'] for c in ra_lop)
    tong_xong = sum(c['completed'] for c in ra_lop)
    tong_bo = sum(c['dropped'] for c in ra_lop)
    tong_comat = sum((cham_can.get(c['id']) or {}).get('co_mat') or 0 for c in ra_lop)
    tong_tick = sum((cham_can.get(c['id']) or {}).get('tick') or 0 for c in ra_lop)
    dang_chay = [c for c in ra_lop if c['status'] == 'active']
    summary = {
        'classCount': len(ra_lop),
        'activeClasses': len(dang_chay),
        'classesByType': theo_loai,
        'active': sum(c['active'] for c in ra_lop),
        'enrolledEver': tong_ghi_danh,
        'completed': tong_xong,
        'dropped': tong_bo,
        'leftUnknown': sum(c['leftUnknown'] for c in ra_lop),
        'dropRate': _mot_phan_tram(tong_bo, tong_xong + tong_bo),
        'retentionPct': _mot_phan_tram(tong_xong, tong_xong + tong_bo),
        'attendedPct': _mot_phan_tram(tong_comat, tong_tick),
        'sessionsUnmarked': sum(c['sessionsUnmarked'] for c in ra_lop),
        # Ba số dưới đây màn hình từng tự đếm trên mảng `classes`. Nay mảng ấy bị
        # cắt còn `TRAN_BANG_LOP` dòng, nên đếm phía màn hình sẽ HỤT lặng lẽ đúng
        # lúc trung tâm đông lớp nhất — đếm ở đây, trên mọi lớp.
        'activeNoTeacher': sum(1 for c in dang_chay if c['teacherId'] is None),
        'overCapacity': sum(1 for c in ra_lop
                            if c['capacity'] is not None and c['active'] > c['capacity']),
        # Giữ chân dưới ngưỡng báo động ⇔ bỏ giữa chừng từ (100 − ngưỡng)% trở lên.
        'dropAlarm': sum(1 for c in dang_chay
                         if c['dropRate'] is not None
                         and c['dropRate'] >= 100 - GIU_CHAN_BAO_DONG),
        'incomplete': thieu,
    }

    ra_lop.sort(key=_xep_van_de)
    return {
        'classes': ra_lop if tran_lop is None else ra_lop[:tran_lop],
        'classesTotal': len(ra_lop),
        'terms': dot,
        'summary': summary,
        # `lateHours`: màn hình in ngưỡng "muộn" từ đây, không gõ lại số 24.
        'thresholds': {'good': GIU_CHAN_TOT, 'alarm': GIU_CHAN_BAO_DONG,
                       'lateHours': TRE_DIEM_DANH_GIO},
        'roiLop': roi_lop,
        'giangVien': giang_vien,
        'taiKhoanNgu': ngu,
        # Giờ VN, naive — màn hình in nguyên giờ này, không quy đổi múi giờ.
        'generatedAt': nay.isoformat(timespec='seconds'),
    }


def _roi_lop(loc_lop, term_id, tu, den):
    """Học viên rời lớp trong kỳ ``tu``..``den`` (cả ngày ``den``) — MỘT câu.

    `left_at` là mốc; chỉ HỌC VIÊN (`chi_hoc_vien`) — cùng luật đếm với câu 1, nên
    số ở đây và số `completed`/`dropped` của bảng lớp đếm cùng một tập người.
    Lý do NULL = "chưa ghi" — báo riêng, không đoán (xem `vocab.trang_thai`).

    CTE `roi` lấy khoảng RỘNG hơn kỳ xem (tới đầu dải 6 tháng) và đọc hai lần: một
    lần gộp theo (tháng, loại lớp, lý do, trong-kỳ?) — ≤ vài chục dòng dù trung tâm
    lớn cỡ nào — và một lần lấy 50 dòng mới nhất TRONG kỳ.
    """
    dau_dai = _dau_thang_lui(den, SO_THANG - 1)
    r = q1('''WITH roi AS (
                  SELECT m.id, m.user_id, m.class_id, m.left_at, m.leave_reason,
                         c.name AS class_name, c.class_type, u.name AS user_name
                  FROM class_members m
                  JOIN classes c ON c.id = m.class_id
                  JOIN users u ON u.id = m.user_id
                  WHERE m.left_at >= %(tu_rong)s AND m.left_at < %(den_sau)s
                    AND ''' + chi_hoc_vien('u') + ''' AND ''' + loc_lop + '''
              )
              SELECT
                (SELECT COALESCE(json_agg(n), '[]'::json) FROM (
                    SELECT to_char(left_at, 'YYYY-MM') AS thang, class_type AS loai,
                           leave_reason AS ly_do, left_at >= %(tu)s AS trong_ky,
                           COUNT(*) AS so
                    FROM roi GROUP BY 1, 2, 3, 4) n) AS nhom,
                (SELECT COALESCE(json_agg(d ORDER BY d.left_at DESC, d.id DESC), '[]'::json)
                 FROM (SELECT id, user_id, user_name, class_id, class_name, class_type,
                              left_at, to_char(left_at, 'YYYY-MM-DD') AS left_on, leave_reason
                       FROM roi WHERE left_at >= %(tu)s
                       ORDER BY left_at DESC, id DESC LIMIT %(tran)s) d) AS ds''',
           {'tu_rong': min(tu, dau_dai), 'den_sau': den + timedelta(days=1), 'tu': tu,
            'term_id': term_id, 'tran': TRAN_DANH_SACH})

    rong = {**{k: 0 for k in LEAVE_REASONS}, 'chuaGhi': 0}
    theo_ly_do, theo_loai = dict(rong), {k: 0 for k in LOAI_LOP}
    thang = {}
    for i in range(SO_THANG):
        k = _dau_thang_lui(den, SO_THANG - 1 - i).strftime('%Y-%m')
        thang[k] = {'thang': k, 'tong': 0, **rong}
    for n in r['nhom']:
        ly = n['ly_do'] if n['ly_do'] in LEAVE_REASONS else 'chuaGhi'
        if n['trong_ky']:
            theo_ly_do[ly] += n['so']
            theo_loai[n['loai']] = theo_loai.get(n['loai'], 0) + n['so']
        t = thang.get(n['thang'])
        if t is not None:        # dòng trước dải 6 tháng (kỳ xem dài hơn) không vào dải
            t[ly] += n['so']
            t['tong'] += n['so']
    return {
        'tu': tu.isoformat(), 'den': den.isoformat(),
        'tong': sum(theo_ly_do.values()),
        'theoLyDo': theo_ly_do,
        'theoLoai': theo_loai,
        'theoThang': list(thang.values()),
        'ds': [{'id': d['id'], 'userId': d['user_id'], 'name': d['user_name'],
                'classId': d['class_id'], 'className': d['class_name'],
                'classType': d['class_type'], 'leftOn': d['left_on'],
                'reason': d['leave_reason']} for d in r['ds']],
    }


def _diem_danh_giang_vien(loc_lop, term_id, tu, den, nay, ra_lop):
    """Từng giảng viên: buổi đã dạy trong kỳ, đã/chưa điểm danh, điểm danh MUỘN.

    "Đã dạy" = cùng luật câu 3: không huỷ, đã bắt đầu (`starts_at <= now`), và ở
    đây thêm: bắt đầu trong kỳ xem. Buổi thuộc về `classes.teacher_id` — giảng
    viên PHỤ TRÁCH lớp, kể cả khi trợ giảng là người tick (trách nhiệm điểm danh
    là của lớp). Đổi giảng viên từng buổi (§58, Đợt 2) thì đổi thành
    COALESCE(buổi, lớp) ở đây.

    MUỘN = `attendance_taken_at` quá `TRE_DIEM_DANH_GIO` giờ sau KẾT THÚC buổi;
    buổi không ghi độ dài tính `sessions.DEFAULT_SESSION_MINUTES`.

    Giảng viên có lớp đang chạy mà chưa có buổi nào trong kỳ vẫn có dòng (số 0, tỉ
    lệ None) — "chưa dạy buổi nào" cũng là điều học vụ cần thấy. Buổi của lớp
    chưa phân công gom vào dòng `teacherId = None`.
    """
    khong = ', '.join("'%s'" % t for t in KHONG_TINH)
    rows = q('''SELECT c.teacher_id, COUNT(*) AS da_day,
                       COUNT(*) FILTER (WHERE s.attendance_taken_at IS NOT NULL) AS da_tick,
                       COUNT(*) FILTER (
                           WHERE s.attendance_taken_at > s.starts_at
                               + COALESCE(s.duration_minutes, %(phut)s::int) * INTERVAL '1 minute'
                               + %(tre)s::int * INTERVAL '1 hour') AS muon
                FROM class_sessions s
                JOIN classes c ON c.id = s.class_id
                WHERE s.status NOT IN (''' + khong + ''')
                  AND s.starts_at >= %(tu)s AND s.starts_at < %(den_sau)s
                  AND s.starts_at <= %(nay)s
                  AND ''' + loc_lop + '''
                GROUP BY c.teacher_id''',
             {'phut': DEFAULT_SESSION_MINUTES, 'tre': TRE_DIEM_DANH_GIO, 'tu': tu,
              'den_sau': den + timedelta(days=1), 'nay': nay, 'term_id': term_id})

    # Tên và số lớp lấy từ câu 1 (đã có sẵn, cùng bộ lọc đợt) — không thêm câu.
    ten, so_lop = {}, {}
    for c in ra_lop:
        if c['teacherId'] is not None:
            ten[c['teacherId']] = c['teacherName']
        if c['status'] == 'active':
            so_lop[c['teacherId']] = so_lop.get(c['teacherId'], 0) + 1
    theo = {r['teacher_id']: r for r in rows}
    ra = []
    for k in set(theo) | {k for k in so_lop if k is not None}:
        r = theo.get(k) or {}
        da_day, da_tick = r.get('da_day') or 0, r.get('da_tick') or 0
        ra.append({
            'teacherId': k, 'name': ten.get(k),
            'soLop': so_lop.get(k, 0),
            'buoiDaDay': da_day, 'daDiemDanh': da_tick,
            'chuaDiemDanh': da_day - da_tick,
            'diemDanhMuon': r.get('muon') or 0,
            'tiLe': _mot_phan_tram(da_tick, da_day),
        })
    ra.sort(key=lambda g: (-g['chuaDiemDanh'], -g['diemDanhMuon'], g['teacherId'] is None,
                           (g['name'] or '').lower()))
    return ra


def tai_khoan_ngu(chi_id=None):
    """Tài khoản ĐANG MỞ lâu không hoạt động — MỘT câu. ``chi_id`` giới hạn tập
    người (phép kiểm, và màn danh sách học viên 1.4b khi cần cùng định nghĩa).

    HOẠT ĐỘNG = GREATEST(`last_seen_at` §56, sự kiện học gần nhất) — định nghĩa nằm
    ở MỘT chỗ, `accounts.hoat_dong.sql_hoat_dong` (1.4b: màn Tài khoản lọc "không hoạt
    động ≥ N ngày" bằng đúng câu ấy, nên số trên thẻ này = số dòng danh sách lọc):
      · BỎ `kind = 'attendance'`: điểm danh là giảng viên ghi cho em, kể cả ghi
        "vắng" — tính nó thì em đã bỏ học mà giảng viên vẫn đều đặn tick vắng sẽ
        không bao giờ lọt vào danh sách, đúng em trung tâm cần gọi nhất. (Khác
        `reports._last_activity` — cột "hoạt động" của giảng viên, trả lời "em còn
        dính tới lớp không" — nên nó giữ điểm danh; hai câu hỏi khác nhau.)
      · `occurred_at <= now` — cùng lý do như `reports._last_activity`: sổ điểm
        danh/tick nhầm buổi tương lai không phải hoạt động.
    Chưa có cả hai → rơi về `created_at`: tài khoản cấp 60 ngày chưa ai vào là
    ngủ 60 ngày; cấp hôm qua thì chưa. `created_at` do DEFAULT now() của CSDL ghi
    (giờ UTC, lệch giờ VN 7 tiếng) — không đáng kể ở mốc tính bằng ngày.

    `last_seen_at` chỉ có từ ngày §56 lên (`doTu` = lần đóng dấu sớm nhất): trước
    đó, người vào xem mà không làm bài không để lại dấu, nên trong vài tuần đầu
    số "ngủ" của NHÂN SỰ cao hơn thật. Màn hình ghi "đo từ ngày …" vì vậy.

    `chuaTungVao` = chưa đóng dấu lần nào VÀ chưa có sự kiện học — nghĩa là "chưa
    thấy vào kể từ `doTu`", không hẳn là chưa từng.
    """
    nay = local_now()
    tham = {'nay': nay, 'hom_nay': nay.date(),
            'tran': TRAN_DANH_SACH, 'chi_id': list(chi_id or [])}
    for n in NGUONG_NGU:
        tham['m%d' % n] = nay - timedelta(days=n)
    dem = ', '.join('COUNT(*) FILTER (WHERE moc <= %%(m%d)s) AS d%d' % (n, n) for n in NGUONG_NGU)
    loc = 'u.id = ANY(%(chi_id)s)' if chi_id is not None else 'TRUE'
    r = q1('''WITH hd AS (
                  SELECT u.id, u.name, u.student_code, u.last_seen_at,
                         COALESCE(''' + chi_hoc_vien('u') + ''', FALSE) AS hv,
                         ev.thay, ev.moc
                  FROM users u
                  LEFT JOIN LATERAL (''' + sql_hoat_dong('u', '%(nay)s') + ''') ev ON TRUE
                  WHERE u.status = 'active' AND ''' + loc + '''
              )
              SELECT
                (SELECT COALESCE(json_agg(t), '[]'::json) FROM (
                    SELECT hv, COUNT(*) AS tong, ''' + dem + ''',
                           COUNT(*) FILTER (WHERE thay IS NULL) AS chua_tung
                    FROM hd GROUP BY hv) t) AS dem,
                (SELECT to_char(MIN(last_seen_at), 'YYYY-MM-DD') FROM hd) AS do_tu,
                (SELECT COALESCE(json_agg(d ORDER BY d.moc, d.id), '[]'::json) FROM (
                    SELECT h.id, h.name, h.student_code, h.moc,
                           to_char(h.thay, 'YYYY-MM-DD') AS lan_cuoi,
                           %(hom_nay)s::date - h.moc::date AS ngay,
                           (SELECT string_agg(c.name, ', ' ORDER BY c.name)
                              FROM class_members m JOIN classes c ON c.id = m.class_id
                             WHERE m.user_id = h.id AND m.left_at IS NULL) AS lop
                    FROM hd h
                    WHERE h.hv AND h.moc <= %(m''' + str(NGUONG_NGU[0]) + ''')s
                    ORDER BY h.moc, h.id LIMIT %(tran)s) d) AS ds''', tham)

    nhom = {True: None, False: None}
    for t in r['dem']:
        nhom[bool(t['hv'])] = t

    def _gon(t):
        t = t or {}
        return {'tong': t.get('tong') or 0,
                **{'d%d' % n: t.get('d%d' % n) or 0 for n in NGUONG_NGU},
                'chuaTungVao': t.get('chua_tung') or 0}

    return {
        'nguong': list(NGUONG_NGU),
        'hocVien': _gon(nhom[True]),
        'nhanSu': _gon(nhom[False]),
        'doTu': r['do_tu'],
        'ds': [{'id': d['id'], 'name': d['name'], 'studentCode': d['student_code'],
                'lop': d['lop'], 'ngay': d['ngay'], 'lanCuoi': d['lan_cuoi']}
               for d in r['ds']],
    }


def _doc_ngay(raw, ten):
    """Chuỗi 'YYYY-MM-DD' → (date | None, câu lỗi | None). Rỗng = không lọc."""
    raw = (raw or '').strip()
    if not raw:
        return None, None
    ngay = as_date(raw)
    if ngay is None:
        return None, '%s phải có dạng năm-tháng-ngày, ví dụ 2026-09-01.' % ten
    return ngay, None


class AdminOverviewView(APIView):
    """GET /api/admin/overview?term_id=&tu=&den= — bảng điều khiển toàn trung tâm.

    `IsAdminOrAcademic` từ 14/09/2026. Quyết định 01/09 (TODO, bảng vai trò)
    ghi học vụ "xem MỌI lớp, báo cáo trung tâm"; hồ sơ gửi TopHSA và bài hướng
    dẫn "Mở đầu ngày làm việc" (viết cho học vụ) đều trỏ vào trang này — mà mã
    thì khoá `IsAdminRole`, và một phép kiểm đơn vị còn ghim cả điều ngược lại.
    Rà luồng học vụ trên trình duyệt thật mới lộ: tài liệu nói ba lần một đằng,
    cửa mở một nẻo. Dữ liệu ở đây là số gộp theo lớp/đợt, không có liên lạc
    của em nào — không có lý do riêng tư nào để giữ cửa hẹp hơn quyết định.
    (1.4a thêm danh sách tên em rời lớp / lâu không vào — vẫn không có liên lạc,
    và học vụ vốn xem được hồ sơ học viên ở màn Tài khoản.)

    `tu`/`den` = kỳ xem của "rời lớp" và "điểm danh"; mặc định đầu tháng → hôm nay.
    """
    permission_classes = [IsAdminOrAcademic]

    def get(self, request):
        p = request.query_params
        raw = (p.get('term_id') or '').strip()
        term_id = None
        if raw:
            try:
                term_id = int(raw)
            except ValueError:
                return Response({'error': 'Mã đợt học phải là số.'}, status=400)
        tu, loi_tu = _doc_ngay(p.get('tu'), 'Ngày bắt đầu')
        den, loi_den = _doc_ngay(p.get('den'), 'Ngày kết thúc')
        if loi_tu or loi_den:
            return Response({'error': loi_tu or loi_den}, status=400)
        den = den or local_today()
        tu = tu or den.replace(day=1)
        if tu > den:
            return Response({'error': 'Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.'},
                            status=400)
        return Response(tong_quan(term_id, tu=tu, den=den, tran_lop=TRAN_BANG_LOP))
