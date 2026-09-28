"""BÁO CÁO CHÉO MÔN × LỚP — bảng TopHSA dòng 6, ô "Kết quả theo môn, hoàn thành bài tập".

CHỈ ĐỌC. Không bảng riêng, không DDL: mọi con số ở đây đã có trong CSDL, cái còn thiếu là
một trục.

── CÂU HỎI CHƯA AI TRẢ LỜI ĐƯỢC ─────────────────────────────────────────────

Tới 27/09/2026 trung tâm hỏi được hai câu:
  · "lớp này em nào chưa nộp bài" — `teaching/assignments.py`, bảng chấm từng bài;
  · "khoá này điểm thế nào" — báo cáo lớp và tờ phụ huynh.
Câu chưa ai trả lời được là câu ở GIỮA hai cái đó: **"môn Tư duy Định lượng đang thế nào
so với môn khác, và trong môn ấy lớp nào tụt"**. Học vụ muốn biết thì phải mở ~400 lớp rồi
tự gộp theo môn trong đầu — nên thực tế là không ai biết.

Một dòng = một LỚP, xếp vào nhóm theo MÔN (`classes.course_id` → `courses`), mỗi nhóm có
dòng tổng của môn, và cuối cùng một dòng tổng toàn trung tâm.

── KHÔNG PHÁT MINH CHỈ SỐ MỚI ───────────────────────────────────────────────

Cùng luật đếm với chỗ đã có, để số ở đây và số giảng viên nhìn thấy truy được về một gốc:
  · Học viên ĐANG HỌC — `class_members.left_at IS NULL` + `vocab.chi_hoc_vien`, y như
    `overview.tong_quan` câu 1 (kể cả mẹo LATERAL để lớp chỉ có thành viên KHÔNG phải học
    viên vẫn còn dòng).
  · Phải nộp / đã nộp / đã chấm — cùng phạm vi với `assignments.ClassAssignmentsView.get`:
    chỉ em ĐANG học, chỉ em ĐƯỢC GIAO (`nhan_bai.giao_cho`, bài giao cho nhóm có mẫu số là
    nhóm ấy).
  · Chuyên cần — `attendance.ti_le`, nơi DUY NHẤT định nghĩa công thức ấy. KHÔNG tự chia
    ở đây: tỉ lệ chuyên cần là số đi ra khỏi hệ thống, in vào tờ gửi phụ huynh.
  · Tiến độ chương trình — `chuong_trinh.dich_vu.tien_do_lop`, cửa duy nhất của miền
    chương trình (luật S4). Không đọc thẳng bảng sổ đầu bài.
  · Kỳ xem `tu`/`den` và mã đợt `term_id` — cùng quy ước `overview.py` (cả ngày `den` được
    tính, mặc định đầu tháng → hôm nay). Không quy ước thứ hai.
  · Bảng tính `?dinh_dang=xlsx` — `exports.xuat_bang` / `common.bangtinh.ghi_xlsx`, ô chữ
    không bao giờ thành công thức.

── ĐIỂM PHẢI CHUẨN HOÁ THEO THANG, KHÔNG CỘNG THÔ ───────────────────────────

`assignments.max_score` là thang điểm của RIÊNG từng bài — trung tâm chấm thang 10 hay
thang 100 là việc của họ. Cộng điểm thô rồi chia là sai theo một cách đặc biệt khó thấy:
một bài thang 10 được 10 (tuyệt đối) và một bài thang 100 được 50 (nửa vời) cộng thô ra
trung bình 30 — đọc như một môn đang chết, trong khi sự thật là 75 %. Tệ hơn: con số sai
ấy CHẠY ĐÚNG HƯỚNG (môn nào hay dùng thang 100 trông càng tệ), nên nó không trông như lỗi
mà trông như một phát hiện. Ở đây mỗi lượt điểm quy về phần trăm TRƯỚC khi cộng
(`score * 100 / max_score`), và dòng tổng cộng từ SỐ THÔ chứ không lấy trung bình của các
phần trăm cấp lớp — trung bình của trung bình cho mỗi lớp một phiếu bất kể lớp 3 em hay 30.

── `—` KHÁC 0 % ─────────────────────────────────────────────────────────────

Lớp chưa giao bài nào thì tỉ lệ nộp là `None` (màn hình vẽ `—`), KHÔNG phải 0 %. Hai thứ
đó là hai câu trả lời khác nhau và khách sẽ hỏi: "0 %" là "đã giao mà không em nào nộp" —
một lời buộc tội; `—` là "chưa có gì để đo". Cùng luật với `overview.py`.

Và **lớp không có dòng nào vẫn phải có mặt** với số 0 / `—`: một lớp biến mất khỏi báo cáo
trông y như một lớp đã đóng, nên người đọc không đi tìm nó nữa.

── AI XEM ĐƯỢC ──────────────────────────────────────────────────────────────

`IsAdminOrAcademic` — quản trị viên + quản lý học vụ. Chọn theo trang "Chấm công"
(`cham_cong.py`) và "Toàn trung tâm" (`overview.py`), KHÔNG theo `exports.py`
(`IsAdminRole`): quyết định 01/09/2026 ghi học vụ "xem MỌI lớp, báo cáo trung tâm", và đây
đúng là một báo cáo trung tâm. Giảng viên / trợ giảng / học viên KHÔNG xem được — họ thấy
lớp mình phụ trách qua `can_see_class`, còn bảng này so sánh mọi lớp của mọi người, tức nó
là một bảng xếp hạng đồng nghiệp. Không có liên lạc của em nào ở đây (chỉ số gộp), nên
không có lý do riêng tư nào để hẹp hơn quyết định ấy.

── SỐ CÂU TRUY VẤN LÀ THIẾT KẾ ──────────────────────────────────────────────

7 câu, KHÔNG phụ thuộc số lớp (bốn câu gộp theo lớp + tiến độ + hai câu danh mục). Gọi
báo cáo lớp cho từng lớp sẽ là 6 câu × 400 lớp cho một màn hình.
"""
import logging
from datetime import timedelta

from django.db import DatabaseError
from rest_framework.response import Response
from rest_framework.views import APIView

from chuong_trinh.dich_vu import tien_do_lop
from common.clock import local_now, local_today
from common.db import q
from common.permissions import IsAdminOrAcademic
from teaching.attendance import KHONG_TINH, ti_le
from teaching.nhan_bai import giao_cho

# CÙNG hàm phần trăm với bảng điều khiển trung tâm, không một bản sao: "phần trăm, hoặc
# None khi KHÔNG có mẫu số" là đúng hợp đồng cần ở đây, và hai bản sao của một công thức
# là hai bản sẽ trôi — bản trôi về phía dễ dãi (viết 0 thay cho `—`) thì không ai thấy.
# Chuyên cần thì KHÔNG đi qua đây: nó có định nghĩa riêng, có tên, ở `attendance.ti_le`.
from teaching.overview import _doc_ngay, _mot_phan_tram
from teaching.vocab import chi_hoc_vien

logger = logging.getLogger(__name__)

#: Nhãn tiếng Việt của `classes.status`. Màn hình và bảng tính đọc từ đây, không gõ lại —
#: và không để mã kỹ thuật (`active`, `finished`) lọt lên màn (RULES §10).
NHAN_TRANG_THAI_LOP = {
    'active': 'Đang học', 'paused': 'Tạm dừng',
    'finished': 'Đã kết thúc', 'cancelled': 'Đã huỷ',
}

#: Nhóm cho lớp KHÔNG gắn môn — lớp ôn cả ba môn của HSA (cùng cảnh với `overview` câu 4:
#: `c.course_id IS NULL` = ôn trọn HSA). Không bỏ chúng đi: đó là những lớp ôn tổng, thường
#: là lớp đông nhất của một trung tâm luyện thi. Chữ "môn" chứ không "hợp phần": cổng
#: `e2e/unit/thuat-ngu.test.mjs` giữ MỘT tên cho khái niệm này trên mọi màn, và chuỗi này
#: đi thẳng ra màn.
MON_KHONG_GAN = 'Lớp ôn cả ba môn'

#: Bài tập tính vào MẪU SỐ "phải nộp" — bản nháp thì học viên chưa thấy, nên chưa thể
#: "phải nộp"; đưa nó vào mẫu số là một lớp bị trừ điểm vì giảng viên đang soạn bài.
TRANG_THAI_BAI_DA_GIAO = ('open', 'closed')

#: Loại bài NỘP ĐƯỢC. Bài kiểm tra làm TRÊN LỚP (§62f) không nộp được, nên nó không nằm
#: trong tỉ lệ nộp bài — nhưng ĐIỂM của nó vẫn vào điểm trung bình của môn, vì đó chính
#: là "kết quả theo môn" mà khách hỏi.
LOAI_BAI_NOP = 'bai_tap'

#: Cửa API cắt danh sách lớp của MỖI MÔN còn bấy nhiêu dòng, lớp cần nhìn lên đầu (TopHSA
#: có ~400 lớp gia sư). Mọi phép ĐẾM và mọi dòng TỔNG vẫn tính trên toàn bộ lớp, và bản
#: tải .xlsx KHÔNG bị cắt — tệp mang đi họp thì phải đủ.
TRAN_LOP_MOI_MON = 50

#: Mốc thời gian của một bài: ngày kiểm tra (bài kiểm tra trên lớp), rồi hạn nộp, rồi ngày
#: tạo. Bài không đặt hạn vẫn phải rơi vào một kỳ nào đó, nếu không nó vô hình mãi mãi.
_MOC_BAI = 'COALESCE(a.held_on::timestamp, a.due_at, a.created_at)'

_KHONG_TINH = ', '.join("'%s'" % t for t in KHONG_TINH)   # hằng trong mã, không phải dữ liệu vào


def _khoa_xep_lop(c):
    """Khoá xếp lớp trong một môn: lớp CẦN NGƯỜI NHÌN lên đầu.

    Danh sách bị cắt còn `TRAN_LOP_MOI_MON` dòng, nên thứ tự quyết định lớp nào còn trên
    màn hình. Lớp ĐANG HỌC trước (lớp đã kết thúc thì không còn gì làm hôm nay), rồi tỉ lệ
    nộp bài THẤP NHẤT lên trước — đó đúng là câu "lớp nào trong môn ấy tụt". Lớp chưa đo
    được (`None`) xuống dưới lớp đo được: `—` không phải một con số tệ, nó là không có số.
    """
    return (c['status'] != 'active', c['tiLeNop'] is None,
            c['tiLeNop'] if c['tiLeNop'] is not None else 0, (c['name'] or '').lower())


def _khoa_xep_mon(m):
    """Khoá xếp nhóm môn: môn ĐANG TỤT lên đầu.

    Trang này tồn tại để trả lời "môn nào đang tụt", nên thứ tự các nhóm CHÍNH LÀ câu trả
    lời — bắt người đọc tự so 5 con số trong đầu là trả lời nửa vời. Môn chưa đo được
    xuống cuối, và `MON_KHONG_GAN` không được ưu tiên gì riêng: nó là một môn như các môn
    khác ở đây.
    """
    t = m['tong']
    return (t['tiLeNop'] is None, t['tiLeNop'] if t['tiLeNop'] is not None else 0,
            (m['courseTitle'] or '').lower())


def _o_rong():
    """Bộ đếm thô của một dòng. Dòng tổng cộng CHÍNH các số này, không cộng phần trăm."""
    return {'dangHoc': 0, 'phaiNop': 0, 'daNop': 0, 'daCham': 0,
            'soDiem': 0, '_tongDiemChuan': 0.0,
            'luotDiemDanh': 0, 'coMat': 0, '_tongTienDo': 0.0, 'lopCoKhung': 0,
            'lopCham': 0, 'soLop': 0}


def _cong(vao, o):
    """Cộng bộ đếm THÔ của một lớp vào bộ đếm của môn (rồi của trung tâm).

    Nhận `o` THÔ chứ không nhận dòng đã chốt: dòng đã chốt không còn hai ô cộng dồn
    (`_tongDiemChuan`, `_tongTienDo`) vì `_chot` lọc mọi khoá `_`, và cộng từ phần trăm đã
    làm tròn của từng lớp là đúng cái lỗi "trung bình của trung bình" mà cả tệp này tránh.
    """
    for k in ('dangHoc', 'phaiNop', 'daNop', 'daCham', 'soDiem', 'luotDiemDanh', 'coMat',
              'lopCoKhung', 'lopCham'):
        vao[k] += o[k]
    vao['_tongDiemChuan'] += o['_tongDiemChuan']
    vao['_tongTienDo'] += o['_tongTienDo']
    vao['soLop'] += 1


def _chot(o):
    """Bộ đếm thô → dòng có tỉ lệ. Mọi tỉ lệ `None` khi KHÔNG có mẫu số."""
    ra = {k: v for k, v in o.items() if not k.startswith('_')}
    ra['tiLeNop'] = _mot_phan_tram(o['daNop'], o['phaiNop'])
    # Mẫu số của "đã chấm" là số bài ĐÃ NỘP, không phải số bài phải nộp: chỉ chấm được thứ
    # đã nộp. Lấy `phaiNop` làm mẫu thì một lớp nộp ít mà giảng viên chấm hết vẫn hiện
    # "chấm 50 %", và người đọc sẽ đi nhắc đúng người đang làm tốt nhất.
    ra['tiLeCham'] = _mot_phan_tram(o['daCham'], o['daNop'])
    # Điểm TB: tổng các PHẦN TRĂM đã chuẩn hoá chia số lượt điểm. Làm tròn ở bước cuối,
    # không làm tròn từng lượt: `max_score` là NUMERIC(6,2) nên từng lượt có phần thập phân
    # thật, và làm tròn trước khi cộng là vứt nó đi 1 lần cho mỗi bài.
    ra['diemTB'] = round(o['_tongDiemChuan'] / o['soDiem']) if o['soDiem'] else None
    # Chuyên cần đi qua `attendance.ti_le` — nơi DUY NHẤT định nghĩa công thức này.
    ra['tiLeChuyenCan'] = ti_le(o['coMat'], o['luotDiemDanh'])
    # Tiến độ của một NHÓM: trung bình theo LỚP (mỗi lớp một phiếu), chỉ trên lớp ĐÃ nhận
    # khung. Cố ý không cân theo sĩ số: câu hỏi ở đây là "chương trình của môn này có bị
    # chậm không", và chậm là chuyện của lớp, không của đầu người.
    ra['tienDoPct'] = (round(o['_tongTienDo'] / o['lopCoKhung']) if o['lopCoKhung'] else None)
    return ra


def bao_cao_cheo(course_id=None, term_id=None, tu=None, den=None, tran_lop=None):
    """Bảng chéo môn × lớp. Trả dict — xem đầu tệp.

    ``course_id`` lọc một môn (`classes.course_id`); ``term_id`` lọc một đợt.
    ``tu``/``den`` (date) = KỲ XEM, cả ngày ``den`` được tính; mặc định đầu tháng của
    ``den`` tới hôm nay, cùng quy ước `overview.tong_quan`. Kỳ xem lọc BÀI (theo mốc
    `_MOC_BAI`) và BUỔI HỌC (theo `starts_at`) — không lọc sĩ số: "lớp này hiện có bao
    nhiêu em" là hiện trạng, không phải một khoảng thời gian.
    ``tran_lop`` cắt danh sách lớp của mỗi môn còn N dòng; None = đủ (bản .xlsx và các
    phép kiểm dò lớp của chính mình theo id nên cần đủ).
    """
    nay = local_now()
    den = den or nay.date()
    tu = tu or den.replace(day=1)
    thieu = []
    ky = {'tu': tu, 'den_sau': den + timedelta(days=1)}

    loc = ['TRUE']
    tham = dict(ky)
    if term_id is not None:
        loc.append('c.term_id = %(term_id)s')
        tham['term_id'] = term_id
    if course_id is not None:
        # Chuỗi rỗng KHÔNG tới được đây (view đổi về None): `course_id = ''` sẽ lọc ra
        # không lớp nào và màn hình hiện "chưa có lớp" cho một bộ lọc người dùng không đặt.
        loc.append('c.course_id = %(course_id)s')
        tham['course_id'] = course_id
    where = ' AND '.join(loc)

    # ── Câu 1: lớp + môn + đợt + sĩ số đang học ─────────────────────────────
    # LATERAL thay cho `JOIN users` để lọc học viên: bộ lọc nằm trong PHÉP ĐẾM chứ không ở
    # WHERE. Đặt ở WHERE thì lớp có thành viên mà KHÔNG thành viên nào là học viên (quản
    # trị viên vào xem trước khi xếp em) rơi khỏi GROUP BY và biến mất khỏi báo cáo —
    # chính cái bẫy `overview.py` đã trả giá 31/08/2026.
    lop = q('''SELECT c.id, c.code, c.name, c.status, c.course_id, co.title AS course_title,
                      c.term_id, t.name AS term_name, u.name AS teacher_name,
                      COUNT(m.id) FILTER (WHERE hv AND m.left_at IS NULL) AS dang_hoc
               FROM classes c
               LEFT JOIN courses co ON co.id = c.course_id
               LEFT JOIN terms t ON t.id = c.term_id
               LEFT JOIN users u ON u.id = c.teacher_id
               LEFT JOIN class_members m ON m.class_id = c.id
               LEFT JOIN LATERAL (
                   SELECT TRUE AS hv FROM users mu
                   WHERE mu.id = m.user_id AND ''' + chi_hoc_vien('mu') + '''
               ) hvq ON TRUE
               WHERE ''' + where + '''
               GROUP BY c.id, co.title, t.name, u.name''', tham)
    ids = [r['id'] for r in lop]

    # ── Câu 2: bài tập — phải nộp / đã nộp / đã chấm ────────────────────────
    #
    # MỘT dòng cho mỗi (bài × em được giao), rồi LEFT JOIN lượt nộp: mẫu số là số LƯỢT
    # PHẢI NỘP, không phải số bài. Đây là chỗ dễ sai nhất của cả tệp:
    #  · `m.left_at IS NULL` — em đã rời lớp không vào cả tử lẫn mẫu. Thiếu vế này thì lớp
    #    càng nhiều em bỏ học trông càng tệ ở tỉ lệ nộp, và điểm 0 của một em đã đi từ
    #    nhiều tháng trước vẫn kéo trung bình cả môn xuống (cùng bẫy `overview` câu 4).
    #  · `giao_cho` — bài giao cho NHÓM có mẫu số là nhóm ấy, không phải cả lớp. Cùng vế
    #    với `assignments.ClassAssignmentsView.get`; thiếu nó thì mọi lớp có một bài giao
    #    riêng cho ba em hiện "3/30 đã nộp".
    bai = {}
    if ids:
        try:
            for r in q('''SELECT a.class_id,
                                 COUNT(*)                                        AS phai_nop,
                                 COUNT(*) FILTER (WHERE s.submitted_at IS NOT NULL) AS da_nop,
                                 COUNT(*) FILTER (WHERE s.submitted_at IS NOT NULL
                                              AND s.graded_at IS NOT NULL)       AS da_cham
                          FROM assignments a
                          JOIN class_members m ON m.class_id = a.class_id AND m.left_at IS NULL
                          JOIN users u ON u.id = m.user_id
                          LEFT JOIN submissions s ON s.assignment_id = a.id
                                                 AND s.user_id = m.user_id
                          WHERE a.class_id = ANY(%(ids)s)
                            AND a.kind = %(loai)s AND a.status = ANY(%(trang_thai)s)
                            AND ''' + _MOC_BAI + ''' >= %(tu)s
                            AND ''' + _MOC_BAI + ''' < %(den_sau)s
                            AND ''' + chi_hoc_vien('u') + '''
                            AND ''' + giao_cho('a', 'm.user_id') + '''
                          GROUP BY a.class_id''',
                       dict(ky, ids=ids, loai=LOAI_BAI_NOP,
                            trang_thai=list(TRANG_THAI_BAI_DA_GIAO))):
                bai[r['class_id']] = r
        except DatabaseError:
            logger.error('[bao_cao_cheo] KHÔNG đọc được bài tập', exc_info=True)
            thieu.append('baiTap')

    # ── Câu 3: điểm đã chấm, CHUẨN HOÁ theo thang của từng bài ──────────────
    #
    # `score * 100 / max_score` cho MỖI lượt rồi mới cộng — xem khối "ĐIỂM PHẢI CHUẨN HOÁ"
    # ở đầu tệp. `NULLIF(max_score, 0)` dù lược đồ đã CHECK `max_score > 0`: hàng rào ở
    # CSDL bảo vệ dữ liệu mới, không bảo vệ dòng đã nằm đó trước ngày có CHECK, và chia
    # cho 0 ở đây là 500 cho cả trang.
    #
    # Tính CẢ bài kiểm tra trên lớp (không lọc `kind`): đó là "kết quả theo môn". Bỏ
    # `absent` — em vắng buổi kiểm tra có dòng đã chấm nhưng KHÔNG có điểm (§62f), và
    # `score IS NULL` đã loại nó; giữ vế `NOT absent` để ý định nhìn thấy được.
    diem = {}
    if ids:
        try:
            for r in q('''SELECT a.class_id, COUNT(*) AS so_diem,
                                 SUM(s.score * 100.0 / NULLIF(a.max_score, 0)) AS tong_chuan
                          FROM submissions s
                          JOIN assignments a ON a.id = s.assignment_id
                          JOIN class_members m ON m.class_id = a.class_id
                                              AND m.user_id = s.user_id
                                              AND m.left_at IS NULL
                          JOIN users u ON u.id = s.user_id
                          WHERE a.class_id = ANY(%(ids)s)
                            AND s.score IS NOT NULL AND NOT s.absent
                            AND a.status = ANY(%(trang_thai)s)
                            AND ''' + _MOC_BAI + ''' >= %(tu)s
                            AND ''' + _MOC_BAI + ''' < %(den_sau)s
                            AND ''' + chi_hoc_vien('u') + '''
                            AND ''' + giao_cho('a', 's.user_id') + '''
                          GROUP BY a.class_id''',
                       dict(ky, ids=ids, trang_thai=list(TRANG_THAI_BAI_DA_GIAO))):
                diem[r['class_id']] = r
        except DatabaseError:
            logger.error('[bao_cao_cheo] KHÔNG đọc được điểm', exc_info=True)
            thieu.append('diem')

    # ── Câu 4: chuyên cần trong kỳ xem ──────────────────────────────────────
    # Cùng luật với `overview` câu 2 (buổi huỷ không tính, chỉ lượt của HỌC VIÊN), thêm
    # đúng một vế: buổi phải bắt đầu TRONG kỳ xem — cùng vế mà `_diem_danh_giang_vien`
    # dùng. Bảng này có bộ lọc ngày, nên một cột chuyên cần tính trên MỌI buổi sẽ không
    # đổi khi người đọc đổi kỳ xem, và họ sẽ tin là nó đã đổi.
    cham_can = {}
    if ids:
        try:
            for r in q('''SELECT s.class_id,
                                 COUNT(*)                                     AS tick,
                                 COUNT(*) FILTER (WHERE a.status IN ('present','late')) AS co_mat
                          FROM attendance a
                          JOIN class_sessions s ON s.id = a.session_id
                          JOIN users u ON u.id = a.user_id
                          WHERE s.class_id = ANY(%(ids)s)
                            AND s.status NOT IN (''' + _KHONG_TINH + ''')
                            AND s.starts_at >= %(tu)s AND s.starts_at < %(den_sau)s
                            AND ''' + chi_hoc_vien('u') + '''
                          GROUP BY s.class_id''', dict(ky, ids=ids)):
                cham_can[r['class_id']] = r
        except DatabaseError:
            logger.error('[bao_cao_cheo] KHÔNG đọc được chuyên cần', exc_info=True)
            thieu.append('chuyenCan')

    # ── Câu 5: tiến độ chương trình — qua CỬA DỊCH VỤ của miền (luật S4) ────
    tien_do = {}
    try:
        tien_do = tien_do_lop(ids, nay)
    except DatabaseError:
        logger.error('[bao_cao_cheo] KHÔNG đọc được tiến độ chương trình', exc_info=True)
        thieu.append('chuongTrinh')

    # ── Ghép từng lớp ───────────────────────────────────────────────────────
    dong = []
    for r in lop:
        b = bai.get(r['id']) or {}
        d = diem.get(r['id']) or {}
        cc = cham_can.get(r['id']) or {}
        td = tien_do.get(r['id'])
        o = _o_rong()
        o.update({
            'dangHoc': r['dang_hoc'] or 0,
            'phaiNop': int(b.get('phai_nop') or 0),
            'daNop': int(b.get('da_nop') or 0),
            'daCham': int(b.get('da_cham') or 0),
            'soDiem': int(d.get('so_diem') or 0),
            '_tongDiemChuan': float(d.get('tong_chuan') or 0),
            'luotDiemDanh': int(cc.get('tick') or 0),
            'coMat': int(cc.get('co_mat') or 0),
        })
        # Tiến độ chương trình vào CÙNG bộ đếm, ở dạng "tổng / số lớp có khung" — nhờ vậy
        # `_chot` cho ra tiến độ của một LỚP và của một MÔN bằng đúng một phép tính.
        # `tien_do_lop` không có khoá cho lớp chưa nhận khung, và `pct` của nó còn có thể
        # là None khi bản khung chưa có mục nào có trọng số: hai trường hợp ấy đều là
        # "chưa đo được", không phải 0 %, nên không lớp nào trong số đó vào mẫu số.
        if td and td['pct'] is not None:
            o['_tongTienDo'] = float(td['pct'])
            o['lopCoKhung'] = 1
            o['lopCham'] = 1 if td['cham'] else 0
        dong.append(_chot(o) | {
            # `_o` đi kèm dòng để bước gộp cộng từ SỐ THÔ; `_chot` không giữ khoá `_` nên
            # nó không rơi vào phản hồi JSON (lọc lại ở bước dựng `mon` bên dưới).
            '_o': o,
            'classId': r['id'], 'code': r['code'], 'name': r['name'],
            'status': r['status'],
            'trangThai': NHAN_TRANG_THAI_LOP.get(r['status'], r['status']),
            'courseId': r['course_id'], 'courseTitle': r['course_title'],
            'termId': r['term_id'], 'termName': r['term_name'],
            'teacherName': r['teacher_name'],
            'chuongTrinhCham': bool(td and td['cham']),
        })

    # ── Nhóm theo MÔN, rồi dòng tổng ────────────────────────────────────────
    nhom = {}
    tong = _o_rong()
    for c in dong:
        k = c['courseId']
        g = nhom.setdefault(k, {
            'courseId': k,
            'courseTitle': c['courseTitle'] or (MON_KHONG_GAN if k is None else k),
            '_lop': [], '_o': _o_rong(),
        })
        g['_lop'].append(c)
        _cong(g['_o'], c['_o'])
        _cong(tong, c['_o'])

    mon = []
    for g in nhom.values():
        g['_lop'].sort(key=_khoa_xep_lop)
        mon.append({
            'courseId': g['courseId'], 'courseTitle': g['courseTitle'],
            'tong': _chot(g['_o']),
            'lopTong': len(g['_lop']),
            'lop': [{k: v for k, v in c.items() if not k.startswith('_')}
                    for c in (g['_lop'] if tran_lop is None else g['_lop'][:tran_lop])],
        })
    mon.sort(key=_khoa_xep_mon)

    # ── Danh mục cho ô lọc — LẤY TỪ MÁY CHỦ, màn hình không gõ lại (RULES §7) ──
    # KHÔNG áp bộ lọc hiện hành vào danh mục: chọn môn A rồi thấy ô chọn chỉ còn môn A là
    # không quay lại được. Chỉ môn ĐÃ CÓ LỚP — một danh mục khoá trong đó nửa lựa chọn cho
    # ra bảng rỗng thì người dùng học cách không tin nó.
    mon_chon, dot_chon = [], []
    try:
        mon_chon = [{'id': r['id'], 'title': r['title'] or r['id']} for r in q(
            'SELECT co.id, co.title FROM courses co '
            'WHERE EXISTS (SELECT 1 FROM classes c WHERE c.course_id = co.id) '
            'ORDER BY lower(COALESCE(co.title, co.id))')]
        dot_chon = [{'id': r['id'], 'name': r['name']} for r in q(
            'SELECT id, name FROM terms ORDER BY id DESC')]
    except DatabaseError:
        logger.error('[bao_cao_cheo] KHÔNG đọc được danh mục môn / đợt', exc_info=True)
        thieu.append('danhMuc')

    return {
        'tu': tu.isoformat(), 'den': den.isoformat(),
        'courseId': course_id, 'termId': term_id,
        'mon': mon,
        'tong': _chot(tong),
        'monOptions': mon_chon,
        'dotOptions': dot_chon,
        'monKhongGan': MON_KHONG_GAN,
        'incomplete': thieu,
        # Giờ VN, naive — màn hình in nguyên giờ này, không quy đổi múi giờ.
        'generatedAt': nay.isoformat(timespec='seconds'),
    }


#: Cột của bản .xlsx. ĐÚNG những cột màn hình có, cùng thứ tự — người ta tải về để tính
#: tiếp, và hai bản lệch nhau thì bản nào cũng không tin được (cùng luật `cham_cong.py`).
COT_XLSX = ('Môn', 'Lớp', 'Đợt học', 'Giảng viên', 'Trạng thái', 'Đang học',
            'Phải nộp', 'Đã nộp', 'Tỉ lệ nộp (%)', 'Đã chấm', 'Tỉ lệ chấm (%)',
            'Số lượt điểm', 'Điểm trung bình (%)', 'Lượt điểm danh', 'Có mặt',
            'Chuyên cần (%)', 'Tiến độ chương trình (%)')

#: Ô cho một tỉ lệ KHÔNG tính được. Cùng ký tự với màn hình chứ không để ô trống hay 0:
#: ô trống đọc thành "quên điền" và 0 đọc thành "tệ hết mức". Cột tử số và mẫu số bên
#: cạnh vẫn là SỐ, nên ai cần tính lại trong Excel thì vẫn tính được.
GACH = '—'


def _pt(v):
    """Một tỉ lệ vào ô bảng tính: SỐ NGUYÊN phần trăm, hoặc `—`.

    Không ghi phân số (0,75) kèm định dạng phần trăm: `common.bangtinh.ghi_xlsx` cố ý KHÔNG
    nhận định dạng cho từng ô, nên 0,75 sẽ hiện ra đúng là "0.75" và người mở tệp đọc thành
    điểm 0,75. Tên cột mang sẵn "(%)" nên số 75 không thể đọc nhầm, và nó vẫn cộng / lọc /
    vẽ đồ thị được trong Excel — đúng việc người ta tải tệp này về để làm.
    """
    return GACH if v is None else v


def _hang_xlsx(mon_ten, lop_ten, r, dot=None, gv=None, trang_thai=None):
    return [mon_ten, lop_ten, dot, gv, trang_thai, r['dangHoc'],
            r['phaiNop'], r['daNop'], _pt(r['tiLeNop']),
            r['daCham'], _pt(r['tiLeCham']),
            r['soDiem'], _pt(r['diemTB']),
            r['luotDiemDanh'], r['coMat'], _pt(r['tiLeChuyenCan']),
            _pt(r['tienDoPct'])]


def bang_xlsx(data):
    """Phản hồi `bao_cao_cheo` → (header, rows) cho `exports.xuat_bang`.

    Thứ tự y hệt màn hình: từng môn (lớp trước, dòng tổng môn sau), rồi dòng tổng trung
    tâm ở cuối. Dòng tổng KHÔNG nằm ở đầu nhóm: người mở tệp sẽ kéo chọn một vùng để tính
    lại, và một dòng tổng lẫn giữa các dòng lớp là cộng hai lần.
    """
    rows = []
    for m in data['mon']:
        for c in m['lop']:
            rows.append(_hang_xlsx(m['courseTitle'], c['name'], c,
                                   c['termName'], c['teacherName'], c['trangThai']))
        rows.append(_hang_xlsx(m['courseTitle'], 'TỔNG MÔN (%d lớp)' % m['lopTong'],
                               m['tong']))
    rows.append(_hang_xlsx('TOÀN TRUNG TÂM', 'TỔNG (%d lớp)' % data['tong']['soLop'],
                           data['tong']))
    return list(COT_XLSX), rows


class BaoCaoCheoView(APIView):
    """GET /api/admin/bao-cao-cheo?course_id=&term_id=&tu=&den=[&dinh_dang=xlsx]

    Bảng chéo MÔN × LỚP — xem đầu tệp. CHỈ ĐỌC, không ghi bảng nào.

    `IsAdminOrAcademic`: quản trị viên + quản lý học vụ. Giảng viên, trợ giảng, học viên
    KHÔNG — bảng này so sánh mọi lớp của mọi người. Lý lẽ đầy đủ ở khối "AI XEM ĐƯỢC".
    """
    permission_classes = [IsAdminOrAcademic]

    def get(self, request):
        from teaching.exports import doc_dinh_dang, xuat_bang

        p = request.query_params
        dd, loi_dd = doc_dinh_dang(p)
        if loi_dd:
            return Response({'error': loi_dd}, status=400)
        # Chuỗi rỗng = KHÔNG lọc, không phải "lọc theo môn có mã rỗng": ô chọn của màn gửi
        # `course_id=` khi người dùng chọn "Mọi môn".
        course_id = (p.get('course_id') or '').strip() or None
        raw_dot = (p.get('term_id') or '').strip()
        term_id = None
        if raw_dot:
            try:
                term_id = int(raw_dot)
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

        # Bản .xlsx KHÔNG cắt danh sách lớp: tệp mang đi họp thì phải đủ, và ở đó không có
        # màn hình nào bị dài quá.
        data = bao_cao_cheo(course_id, term_id, tu=tu, den=den,
                            tran_lop=None if dd == 'xlsx' else TRAN_LOP_MOI_MON)
        if dd == 'xlsx':
            header, rows = bang_xlsx(data)
            return xuat_bang('xlsx', 'Bao cao mon %s den %s' % (data['tu'], data['den']),
                             header, rows, 'Môn × Lớp')
        return Response(data)
