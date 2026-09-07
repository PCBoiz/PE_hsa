"""Báo cáo CẢ LỚP dạng PDF — bản trung tâm mang đi họp.

── VÌ SAO CÓ, DÙ ĐÃ CÓ HAI TỆP CSV (07/09/2026) ────────────────────────────

`exports.py` đã xuất CSV tiến độ và CSV chuyên cần, và chúng đúng cho việc
LỌC – TÔ MÀU – TÍNH. Nhưng đặc tả ERP §6 nói "Excel/PDF", hai thứ chứ không
phải một, vì hai việc khác nhau:

  · **CSV** là bảng để LÀM VIỆC TRÊN ĐÓ. Người nhận mở Excel, lọc cột "cảnh báo
    sớm", sắp lại, gọi điện theo danh sách.
  · **PDF** là bản để ĐƯA CHO NGƯỜI KHÁC ĐỌC. Không lọc được, không sắp lại
    được — và đó chính là điểm mạnh: mọi người trong phòng họp nhìn cùng một
    trang, theo cùng một thứ tự, với cùng phần diễn giải.

Đưa một tệp CSV vào buổi họp phụ huynh thì người ta phải mở Excel trên điện
thoại; đưa PDF thì mở ra là đọc.

── KHÔNG TÍNH LẠI MỘT CON SỐ NÀO ──────────────────────────────────────────

Mọi số ở đây lấy từ `reports.class_report` (bảng điều khiển lớp) và
`exports._attendance_data` (sổ điểm danh) — CÙNG hai nguồn mà màn hình và CSV
dùng. Tính song song ở đây thì bản mang đi họp và bản trên màn hình lệch nhau,
và không ai biết bản nào đúng. Đó đúng là thứ làm mất niềm tin vào cả hệ thống
báo cáo, và `exports.py` đã ghi luật ấy từ đầu.

── DÙNG CHUNG BỘ DỰNG VỚI TỜ BÁO CÁO MỘT EM ──────────────────────────────

Font, bảng màu, cách đánh số mục, định dạng ngày đều nhập từ `bao_cao_pdf`.
Hai tờ giấy của cùng một trung tâm mà khác phông chữ là thứ người nhận nhận ra
ngay, kể cả khi không gọi được tên vấn đề.

── NÓI RA PHẦN KHÔNG ĐÁNG TIN ─────────────────────────────────────────────

`class_report` trả `summary.incomplete` — danh sách những mảng KHÔNG đọc được.
Tờ này in nó ra thay vì im lặng trình bày số 0. Một báo cáo dùng để quyết định
gọi điện cho phụ huynh thì phải tự khai chỗ nào đang thiếu.
"""
from io import BytesIO

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from teaching.bao_cao_pdf import (
    FONT,
    FONT_DAM,
    MUC,
    NEN_NHAT,
    NHAN,
    NHAT,
    VIEN,
    an,
    kieu,
    nap_font,
    ngay,
    o_bang,
)

#: Nhãn tiếng Việt cho trạng thái điểm danh. Một mình `present` trên tờ giấy
#: gửi ra ngoài là mã enum lọt vào mặt người đọc — lỗi đã mắc một lần ở dữ liệu
#: mẫu của trang giới thiệu.
NHAN_CC = [('present', 'Có mặt'), ('late', 'Muộn'),
           ('absent', 'Vắng'), ('excused', 'Có phép')]


def _bang(hang, rong, canh_phai_tu=1):
    """Bảng có đầu bảng tô nền, cột số căn phải."""
    t = Table(hang, colWidths=rong, hAlign='LEFT', repeatRows=1)
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT),
        ('FONTNAME', (0, 0), (-1, 0), FONT_DAM),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), NEN_NHAT),
        ('ALIGN', (canh_phai_tu, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.25, VIEN),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return t


def _bieu_do_tien_do(sv):
    """Cột tiến độ từng học viên, kèm nhãn phần trăm trên đỉnh.

    Giới hạn 12 em một biểu đồ: quá số ấy thì nhãn tên chồng lên nhau và biểu
    đồ thành thứ trang trí. Lớp đông hơn thì BẢNG ở trên đã nói đủ, và một biểu
    đồ không đọc được còn tệ hơn không có biểu đồ.
    """
    if not sv or len(sv) > 12:
        return None
    n = len(sv)
    rong = min(430, max(120, 60 * n))
    d = Drawing(rong + 45, 145)
    bd = VerticalBarChart()
    bd.x, bd.y = 30, 36
    bd.width, bd.height = rong, 92
    bd.data = [[int(e.get('progressPct') or 0) for e in sv]]
    bd.categoryAxis.categoryNames = [str(e.get('name') or '') for e in sv]
    bd.categoryAxis.labels.fontName = FONT
    bd.categoryAxis.labels.fontSize = 6.5
    bd.categoryAxis.labels.dy = -4
    bd.categoryAxis.labels.boxAnchor = 'n'
    bd.categoryAxis.labels.width = 60
    bd.categoryAxis.labels.height = 20
    bd.valueAxis.valueMin, bd.valueAxis.valueMax, bd.valueAxis.valueStep = 0, 100, 25
    bd.valueAxis.labels.fontName = FONT
    bd.valueAxis.labels.fontSize = 6.5
    bd.bars[0].fillColor = NHAN
    bd.bars[0].strokeColor = None
    bd.barWidth = 9
    bd.groupSpacing = max(10, rong / n * 0.5)
    d.add(bd)
    for i, e in enumerate(sv):
        pct = int(e.get('progressPct') or 0)
        d.add(String(bd.x + rong / n * (i + 0.5), bd.y + bd.height * pct / 100.0 + 3,
                     '%d%%' % pct, fontName=FONT_DAM, fontSize=7,
                     fillColor=MUC, textAnchor='middle'))
    return d


def dung_pdf_lop(bc: dict, cc: dict | None = None) -> bytes:
    """Dựng tờ báo cáo lớp.

    `bc` là kết quả `reports.class_report(class_id)`.
    `cc` là chuyên cần đã xoay bảng: `{userId: {present, late, absent, excused,
    chuaTick, tiLe}}`, hoặc None nếu không đọc được sổ điểm danh.

    KHÔNG chạm CSDL và KHÔNG kiểm quyền — nơi gọi lo cả hai, nên hàm này kiểm
    được bằng dữ liệu dựng tay.
    """
    nap_font()
    lop = bc.get('class') or {}
    sv = [e for e in (bc.get('students') or []) if not e.get('left')]
    tt = bc.get('summary') or {}

    dem = BytesIO()
    doc = SimpleDocTemplate(
        dem, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
        title='Báo cáo lớp — %s' % (lop.get('name') or ''), author='TopHSA')

    h1 = kieu('h1', 15, NHAN, dam=True, sau=1)
    h2 = kieu('h2', 10.5, MUC, dam=True, truoc=11, sau=5)
    p = kieu('p', 9)
    nho = kieu('nho', 7.8, NHAT, dan=1.45)
    kq = []

    kq.append(Paragraph('BÁO CÁO LỚP', h1))
    kq.append(Paragraph('%s &nbsp;·&nbsp; %s' % (an(lop.get('name')),
                                                 an(lop.get('code') or '')),
                        kieu('duoi', 9, NHAT, sau=8)))

    # ── I. THÔNG TIN LỚP ───────────────────────────────────────────────
    kq.append(Paragraph('I. THÔNG TIN LỚP', h2))
    o = kieu('o', 8.5, MUC, sau=0)
    k_nhan = kieu('nhan', 8.5, NHAT, sau=0)

    def hai_cot(trai, phai):
        def cot(ds, rong):
            t = Table([[Paragraph(an(a), k_nhan), Paragraph(an(b), o)] for a, b in ds],
                      colWidths=rong, hAlign='LEFT')
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LINEBELOW', (0, 0), (-1, -2), 0.25, VIEN),
            ]))
            return t
        ngoai = Table([[cot(trai, [24 * mm, 56 * mm]), cot(phai, [34 * mm, 56 * mm])]],
                      colWidths=[82 * mm, 94 * mm], hAlign='LEFT')
        ngoai.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                   ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                   ('RIGHTPADDING', (0, 0), (0, 0), 8)]))
        return ngoai

    kq.append(hai_cot(
        [('Lớp', lop.get('name')),
         ('Mã lớp', lop.get('code') or '—'),
         ('Giảng viên', lop.get('teacherName') or '—'),
         ('Lịch học', lop.get('schedule') or '—'),
         ('Khai giảng', ngay(lop.get('startsOn')))],
        [('Đang học', '%s học viên' % tt.get('students', 0)),
         ('Đã rời lớp', '%s' % tt.get('left', 0)),
         ('Tiến độ trung bình', '%s%%' % tt.get('avgProgress', 0)),
         ('Chưa thi thử lần nào', '%s em' % tt.get('noMock', 0)),
         ('Ngày thi', ngay(lop.get('examDate')))]))

    # Phần KHÔNG đọc được — in ngay dưới mục I, không giấu xuống cuối.
    if tt.get('incomplete'):
        kq.append(Spacer(1, 5))
        kq.append(Paragraph(
            '<b>Cảnh báo:</b> không đọc được các mảng: %s. Những con số liên quan '
            'trong tờ này có thể thiếu — đừng dùng chúng để kết luận trước khi '
            'kiểm lại.' % an(', '.join(tt['incomplete'])), nho))

    # ── II. CHUYÊN CẦN ─────────────────────────────────────────────────
    kq.append(Paragraph('II. CHUYÊN CẦN', h2))
    if cc is None:
        # Cùng nguyên tắc `ClassAttendanceCsvView`: thà nói không đọc được còn
        # hơn in một bảng toàn số 0 trông hệt "lớp chưa học buổi nào".
        kq.append(Paragraph(
            'Không đọc được sổ điểm danh của lớp này. Phần chuyên cần bỏ trống '
            'có chủ ý — một bảng toàn số 0 ở đây trông giống hệt một lớp chưa học '
            'buổi nào.', p))
    elif not sv:
        kq.append(Paragraph('Lớp chưa có học viên nào đang học.', p))
    else:
        hang = [['Học viên'] + [t for _k, t in NHAN_CC] + ['Chưa tick', 'Tỉ lệ']]
        for e in sv:
            d = cc.get(e['userId']) or {}
            hang.append([o_bang(e.get('name'), o)]
                        + ['%s' % (d.get(k) or 0) for k, _t in NHAN_CC]
                        + ['%s' % (d.get('chuaTick') or 0),
                           '—' if d.get('tiLe') is None else '%s%%' % d['tiLe']])
        kq.append(_bang(hang, [58 * mm] + [17 * mm] * 4 + [19 * mm, 17 * mm]))
        kq.append(Spacer(1, 4))
        kq.append(Paragraph(
            'Tỉ lệ tính trên số buổi em ấy CÓ DÒNG điểm danh, không phải số buổi '
            'cả lớp được tick — buổi giảng viên quên tick không được biến thành '
            '"em vắng". Cột "Chưa tick" là việc còn tồn của giảng viên, không '
            'phải lỗi của học viên.', nho))

    # ── III. TIẾN ĐỘ ───────────────────────────────────────────────────
    kq.append(Paragraph('III. TIẾN ĐỘ HỌC TẬP', h2))
    if not sv:
        kq.append(Paragraph('Chưa có học viên nào đang học.', p))
    else:
        hang = [['Học viên', 'Bài đã xong', 'Tiến độ', 'Thi thử', 'Điểm gần nhất',
                 'Vắng mặt (ngày)']]
        for e in sv:
            lan = e.get('mockCount') or 0
            hang.append([
                o_bang(e.get('name'), o),
                '%s/%s' % (e.get('lessonsDone', 0), e.get('lessonsTotal', 0)),
                '%s%%' % (e.get('progressPct') or 0),
                '%s lượt' % lan,
                # "chưa thi" KHÔNG được viết thành 0 — nó đọc như làm sai hết.
                'chưa thi' if not lan or e.get('lastMockPct') is None
                else '%s%%' % e['lastMockPct'],
                '—' if e.get('idleDays') is None else '%s' % e['idleDays'],
            ])
        kq.append(_bang(hang, [50 * mm] + [23 * mm, 17 * mm, 18 * mm, 27 * mm, 26 * mm]))
        bd = _bieu_do_tien_do(sv)
        if bd is not None:
            kq.append(Spacer(1, 6))
            kq.append(bd)

    # ── IV. CHỦ ĐỀ YẾU NHẤT CỦA LỚP ────────────────────────────────────
    yeu = tt.get('weakestTopics') or []
    kq.append(Paragraph('IV. CHỦ ĐỀ CẢ LỚP ĐANG YẾU', h2))
    if not yeu:
        kq.append(Paragraph(
            'Chưa đủ dữ liệu để xếp hạng chủ đề. Lớp cần làm thêm bài để hệ thống '
            'có cơ sở nói lớp yếu ở đâu.', p))
    else:
        hang = [['Chủ đề', 'Mức trung bình', 'Số em đo được']]
        for t in yeu:
            hang.append([o_bang(t.get('topic'), o),
                         '%s%%' % (t.get('avg') or 0),
                         '%s/%s' % (t.get('measuredStudents', 0), t.get('ofStudents', 0))])
        kq.append(_bang(hang, [96 * mm, 34 * mm, 34 * mm]))
        kq.append(Spacer(1, 4))
        kq.append(Paragraph(
            'Cột "số em đo được" là mẫu số thật của con số bên trái. Một chủ đề '
            '"trung bình 22%" đo trên 1/3 em thì chưa nói được gì về cả lớp.', nho))

    # ── V. EM CẦN CHÚ Ý ────────────────────────────────────────────────
    can = [e for e in sv if (e.get('idleDays') or 0) >= (tt.get('idleDays') or 7)
           or (e.get('mockCount') or 0) == 0]
    khoi = [Paragraph('V. EM CẦN GỌI TRƯỚC', h2)]
    if not can:
        khoi.append(Paragraph('Không em nào rơi vào nhóm cần chú ý trong kỳ này.', p))
    else:
        hang = [['Học viên', 'Vì sao']]
        for e in can:
            ly = []
            if (e.get('idleDays') or 0) >= (tt.get('idleDays') or 7):
                ly.append('không hoạt động %s ngày' % e['idleDays'])
            if (e.get('mockCount') or 0) == 0:
                ly.append('chưa thi thử lần nào')
            hang.append([o_bang(e.get('name'), o), o_bang(' · '.join(ly), o)])
        khoi.append(_bang(hang, [58 * mm, 106 * mm], canh_phai_tu=99))
    kq.append(KeepTogether(khoi))

    kq.append(Spacer(1, 10))
    kq.append(Paragraph(
        '<b>Tờ này không nói gì về:</b> nhật ký học tập học viên tự ghi, và dự '
        'đoán điểm thi thật. Các con số đo việc học trong kỳ, không phải một lời '
        'hứa về kết quả kỳ thi.', nho))
    doc.build(kq)
    return dem.getvalue()
