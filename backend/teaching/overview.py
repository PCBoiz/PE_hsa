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

── SỐ CÂU TRUY VẤN LÀ THIẾT KẾ ──────────────────────────────────────────────
Hàm này chạy ĐÚNG 5 câu, không phụ thuộc số lớp. Gọi `class_report` cho từng lớp
sẽ là 6 câu × N lớp — hai chục lớp là 120 lượt tới Neon cho một màn hình. Đó
chính là cái ngân sách vòng gọi ghi ở đầu `teaching/admin_users.py`.

── KHÔNG ĐỌC ĐƯỢC THÌ NÓI, KHÔNG VIẾT 0 ─────────────────────────────────────
Cùng luật với `reports.py`: mảng nào hỏng thì tên nó vào `incomplete`, và tỉ lệ
tính không được thì trả `None` chứ không phải 0. Một bảng điều khiển trung tâm
hiện "tỉ lệ bỏ học 0%" vì câu tra hỏng là thứ nguy hiểm hơn hẳn một màn hình lỗi.
"""
import logging

from django.db import DatabaseError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.clock import local_now
from common.db import q
from common.permissions import IsAdminRole
from teaching.attendance import KHONG_TINH
from teaching.vocab import chi_hoc_vien

logger = logging.getLogger(__name__)

#: Ngưỡng tham chiếu cho tỉ lệ giữ chân, theo chuẩn ngành dạy thêm (tra cứu
#: 31/08/2026). Để lộ thành hằng số vì đây là một GIẢ ĐỊNH về mô hình kinh
#: doanh, và giả định thì phải nhìn thấy được mới bàn lại được.
GIU_CHAN_TOT = 80
GIU_CHAN_BAO_DONG = 70


def _mot_phan_tram(tu, mau):
    """Phần trăm, hoặc None khi KHÔNG có mẫu số.

    None chứ không 0: "chưa em nào rời lớp" và "chưa có ai để mà tính" là hai
    chuyện khác nhau, và một bảng điều khiển gộp chúng lại sẽ nói dối đúng vào
    lúc trung tâm mới mở đợt.
    """
    return round(tu * 100 / mau) if mau else None


def tong_quan(term_id=None):
    """Số liệu toàn trung tâm, gộp theo lớp rồi theo đợt. Trả dict.

    ``term_id`` lọc theo một đợt; None = mọi lớp.
    """
    thieu = []
    dieu_kien, args = ['TRUE'], []
    if term_id is not None:
        dieu_kien.append('c.term_id = %s')
        args.append(term_id)
    where = ' AND '.join(dieu_kien)

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
                      u.name AS teacher_name,
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
                          GROUP BY class_id''', (ids, local_now())):
                buoi[r['class_id']] = r
        except DatabaseError:
            logger.error('[overview] KHÔNG đọc được buổi học')
            thieu.append('sessions')

    # ── Câu 4: học tập gộp theo lớp (bài xong + điểm thi thử) ───────────────
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
            # KHÔNG áp bộ lọc khoá cho ĐỀ THI THỬ: một lượt thi thử là bài thi cả
            # ba hợp phần HSA, không thuộc riêng khoá nào.
            for r in q('''SELECT m.class_id,
                                 COUNT(*) FILTER (WHERE e.kind = 'lesson'
                                              AND e.course_id = c.course_id) AS bai,
                                 COUNT(*) FILTER (WHERE e.kind = 'mock')    AS luot_de,
                                 AVG(e.score * 100.0 / NULLIF(e.max_score, 0))
                                     FILTER (WHERE e.kind = 'mock')         AS diem_tb
                          FROM class_members m
                          JOIN users u ON u.id = m.user_id
                          JOIN classes c ON c.id = m.class_id
                          JOIN learning_events e ON e.user_id = m.user_id
                          WHERE m.class_id = ANY(%s) AND m.left_at IS NULL
                            AND ''' + chi_hoc_vien('u') + '''
                            AND e.kind IN ('lesson','mock')
                          GROUP BY m.class_id''', (ids,)):
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
        mau_bai = (tong_bai.get(r['course_id']) or 0) * (r['dang_hoc'] or 0)
        # "Rời lớp có lý do" mới là mẫu số của tỉ lệ giữ chân. Người rời lớp mà
        # chưa ai ghi lý do KHÔNG được tính vào cả tử lẫn mẫu — đoán họ bỏ học
        # là thổi phồng con số xấu, đoán họ học xong là giấu con số xấu. Số đó
        # báo riêng ở `leftUnknown` để trung tâm biết còn bao nhiêu dòng cần ghi.
        roi_co_ly_do = (r['hoc_xong'] or 0) + (r['bo_giua'] or 0)
        ra_lop.append({
            'id': r['id'], 'code': r['code'], 'name': r['name'], 'status': r['status'],
            'termId': r['term_id'], 'termName': r['term_name'], 'termCode': r['term_code'],
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
            'attendedPct': _mot_phan_tram(cc.get('co_mat') or 0, cc.get('tick') or 0),
            # KHÔNG đọc được thì trả None, KHÔNG trả 0 — đúng luật ghi ở đầu
            # module. Bản đầu để `h` rỗng đi tiếp thành `_mot_phan_tram(0, mẫu)` = 0,
            # nên một câu SQL hỏng làm CẢ TRUNG TÂM hiện "Tiến độ 0%" — trông y
            # hệt một trung tâm chưa ai học bài nào. Màn hình vẽ `—` cho None và
            # `0%` cho 0: hai thứ đó phải khác nhau ở đây thì mới khác nhau trên
            # màn hình.
            'lessonsDone': None if hong_hoc_tap else (h.get('bai') or 0),
            'progressPct': (None if hong_hoc_tap
                            else _mot_phan_tram(h.get('bai') or 0, mau_bai)),
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
            'attendedPct': _mot_phan_tram(d['_comat'], d['_tick']),
            'dropRate': _mot_phan_tram(d['dropped'], roi_co_ly_do),
            # Giữ chân = phần KHÔNG bỏ giữa chừng. Ngưỡng tham chiếu ở hằng số
            # đầu module; màn hình tô màu theo đó.
            'retentionPct': (None if not roi_co_ly_do
                             else _mot_phan_tram(d['completed'], roi_co_ly_do)),
            'mockAvg': round(d['_diem'] / d['_de']) if d['_de'] else None,
        })
    dot.sort(key=lambda x: (x['termId'] is None, -(x['termId'] or 0)))

    tong_ghi_danh = sum(c['enrolledEver'] for c in ra_lop)
    tong_xong = sum(c['completed'] for c in ra_lop)
    tong_bo = sum(c['dropped'] for c in ra_lop)
    tong_comat = sum((cham_can.get(c['id']) or {}).get('co_mat') or 0 for c in ra_lop)
    tong_tick = sum((cham_can.get(c['id']) or {}).get('tick') or 0 for c in ra_lop)
    return {
        'classes': ra_lop,
        'terms': dot,
        'summary': {
            'classCount': len(ra_lop),
            'activeClasses': sum(1 for c in ra_lop if c['status'] == 'active'),
            'active': sum(c['active'] for c in ra_lop),
            'enrolledEver': tong_ghi_danh,
            'completed': tong_xong,
            'dropped': tong_bo,
            'leftUnknown': sum(c['leftUnknown'] for c in ra_lop),
            'dropRate': _mot_phan_tram(tong_bo, tong_xong + tong_bo),
            'retentionPct': _mot_phan_tram(tong_xong, tong_xong + tong_bo),
            'attendedPct': _mot_phan_tram(tong_comat, tong_tick),
            'sessionsUnmarked': sum(c['sessionsUnmarked'] for c in ra_lop),
            'incomplete': thieu,
        },
        'thresholds': {'good': GIU_CHAN_TOT, 'alarm': GIU_CHAN_BAO_DONG},
    }


class AdminOverviewView(APIView):
    """GET /api/admin/overview?term_id= — bảng điều khiển toàn trung tâm."""
    permission_classes = [IsAdminRole]

    def get(self, request):
        raw = (request.query_params.get('term_id') or '').strip()
        term_id = None
        if raw:
            try:
                term_id = int(raw)
            except ValueError:
                return Response({'error': 'Mã đợt học phải là số.'}, status=400)
        return Response(tong_quan(term_id))
