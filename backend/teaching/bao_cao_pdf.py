"""Tờ báo cáo phụ huynh dưới dạng PDF — bản mang đi họp, và bản đính kèm thư.

── VÌ SAO CÓ (07/09/2026, anh Sơn chốt) ────────────────────────────────────

Đặc tả ERP §6 ghi thẳng: *"Xuất Excel/PDF — bắt buộc với trung tâm, họ luôn
cần bản mang đi họp."* Và khi chốt gửi báo cáo qua email, anh Sơn nói rõ hơn:
**tóm tắt trong thư + tệp PDF đính kèm**, giống tờ "Báo cáo kết quả thi thử
HSA" mà TopHSA đang phát cho học viên.

Ba thứ học được từ tờ ấy và mang sang đây:

  1. **Đánh số mục** (I, II, III…). Phụ huynh cầm tờ giấy đọc trên điện thoại
     hoặc in ra; đánh số thì gọi nhau qua điện thoại còn chỉ được "phần II".
  2. **Nhóm theo DẢI phần trăm** kèm một đoạn nhận xét cho cả dải, thay vì
     liệt kê từng chủ đề rời rạc. Người đọc không phải tự xếp hạng trong đầu.
  3. **Mỗi con số đi kèm mẫu số.** Tờ của họ ghi "27/50", không ghi "54%".

Một thứ CỐ Ý KHÔNG mang sang: tờ của họ kết bằng quảng cáo khoá học và hotline
tuyển sinh. Tờ này gửi cho phụ huynh của học viên ĐANG HỌC — bán thêm ở đây thì
mọi con số phía trên đều bị đọc như lời chào hàng.

── VÌ SAO reportlab, KHÔNG PHẢI HTML → PDF ────────────────────────────────

Đường đẹp nhất về mặt hình thức là in trang `/bc/<chìa>` bằng trình duyệt: giữ
nguyên bố cục React, không dựng lại gì. Nhưng nó đòi một Chromium chạy cạnh
máy chủ — trên gói Render hiện tại thì đó là vài trăm MB và một tiến trình nữa
cho mỗi lượt in. `reportlab` thuần Python, không phần mở rộng C, không phụ
thuộc hệ thống; cài trên Render không cần trình biên dịch — cùng lý lẽ đã chọn
`openpyxl` cho đường nhập bảng tính.

Cái giá phải trả: bố cục ở đây KHÔNG tự đi theo `ToBaoCao.tsx`. Ai sửa tờ giấy
trên web mà quên tệp này thì hai bản trôi khỏi nhau — nên `tests_bao_cao_pdf.py`
canh những trường BẮT BUỘC phải có mặt ở cả hai.

── VÌ SAO NHÚNG FONT VÀO REPO ─────────────────────────────────────────────

`reportlab` kèm sẵn Vera, mà Vera **thiếu 40/57** ký tự tiếng Việt đã đo (ệ, ỗ,
ữ, ằ, ụ, ợ…). Dùng font hệ thống thì máy của anh Sơn có Arial còn Render thì
không, và lỗi ấy chỉ lộ ra trên production dưới dạng những ô vuông đen giữa tên
học viên. DejaVuSans phủ đủ 57/57, giấy phép cho phép phát hành lại, nên nó nằm
trong repo tại `backend/assets/fonts/`.
"""
from datetime import date
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

FONT_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'fonts'
FONT = 'DejaVu'
FONT_DAM = 'DejaVu-Bold'

# Bảng màu: một màu nhấn duy nhất, phần còn lại là thang xám. Tờ giấy này in
# ra máy in đen trắng ở trung tâm là chuyện thường, nên không thông tin nào
# được truyền BẰNG MÀU — màu chỉ để phân tầng, chữ mới mang nghĩa.
NHAN = colors.HexColor('#4B3FBF')
MUC = colors.HexColor('#2B2B33')
NHAT = colors.HexColor('#6B6B78')
VIEN = colors.HexColor('#D8D8E0')
NEN_NHAT = colors.HexColor('#F4F3FA')

#: Dải phần trăm cho phần "chủ đề", kèm nhận xét cho CẢ DẢI.
#:
#: Học từ tờ của TopHSA, nhưng chữ viết lại: tờ ấy chấm một BÀI THI, còn đây
#: chấm mức nắm chủ đề tích luỹ qua quá trình học. Bê nguyên câu "chinh phục
#: được các bài khó, phong độ làm bài ổn định" sang đây là nói về một bài thi
#: không tồn tại.
DAI = [
    (85, 100, 'Nắm chắc',
     'Con làm đúng gần như mọi dạng đã gặp ở các chủ đề này. Việc cần làm chỉ '
     'là giữ nhịp — ôn lại thưa hơn để dành thời gian cho phần còn yếu.'),
    (75, 84, 'Khá vững',
     'Con hiểu bản chất và vận dụng được, chỉ còn sai ở câu khó hoặc khi vội. '
     'Luyện thêm đề có bấm giờ là đủ.'),
    (60, 74, 'Tạm được',
     'Con làm được câu quen thuộc nhưng còn lúng túng khi đề đổi cách hỏi. '
     'Nên làm lại các câu đã sai và tự giải thích vì sao sai.'),
    (40, 59, 'Cần chú ý',
     'Con nhớ lý thuyết nhưng chưa vận dụng ổn. Cách chữa hiệu quả nhất là làm '
     'từng cụm bài ngắn, so đáp án ngay, rồi làm lại đúng dạng ấy.'),
    (0, 39, 'Cần học lại từ gốc',
     'Phần này chưa chắc ở mức kiến thức nền. Nên ôn lại lý thuyết theo chuyên '
     'đề trước khi luyện đề, vì luyện đề lúc này chủ yếu tạo cảm giác bế tắc.'),
]


def nap_font():
    """Đăng ký DejaVu. Gọi nhiều lần vô hại — reportlab ghi đè cùng tên."""
    pdfmetrics.registerFont(TTFont(FONT, str(FONT_DIR / 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont(FONT_DAM, str(FONT_DIR / 'DejaVuSans-Bold.ttf')))
    # Ánh xạ họ font để thẻ <b> trong Paragraph tìm được bản đậm. Không có
    # dòng này thì <b> im lặng trả về bản thường, và mọi nhấn mạnh biến mất
    # mà không có lỗi nào — kiểu hỏng chỉ phát hiện được bằng mắt.
    pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=FONT_DAM,
                                  italic=FONT, boldItalic=FONT_DAM)


def kieu(ten, co, mau=MUC, dam=False, truoc=0, sau=2, dan=1.35):
    return ParagraphStyle(ten, fontName=FONT_DAM if dam else FONT, fontSize=co,
                          leading=co * dan, textColor=mau, alignment=TA_LEFT,
                          spaceBefore=truoc, spaceAfter=sau)


def an(v) -> str:
    """Chuỗi AN TOÀN cho `Paragraph`.

    `Paragraph` phân tích một tập con của HTML, nên tên học viên chứa `&` hoặc
    một ghi chú của giảng viên chứa `<` sẽ làm reportlab NÉM ngoại lệ giữa lúc
    dựng tờ giấy — cả lượt gửi cả lớp hỏng vì một dấu trong một cái tên.

    Cùng họ với lỗ stored-XSS đã vá ở `dashboard.js` hôm qua: một chuỗi do
    người dùng nhập đi thẳng vào một bộ phân tích đánh dấu. Ở đây hậu quả là
    hỏng chứ không phải chạy mã, nhưng lối vào giống hệt.
    """
    return escape('' if v is None else str(v))


def o_bang(v, kieu):
    """Một ô bảng CHỨA DỮ LIỆU NGƯỜI DÙNG.

    Ô bảng của reportlab nhận chuỗi thuần thì KHÔNG phân tích đánh dấu — nên
    `escape()` ở đó là thoát thừa, và tờ giấy in ra "Khoa học &amp;amp; Tiếng
    Anh". Đo được bằng cách đọc lại chính tệp PDF vừa dựng, không đoán.

    Bọc thành `Paragraph` sửa cả hai chuyện một lúc: đánh dấu được phân tích
    nên `an` trở lại đúng vai, và ô tự XUỐNG DÒNG khi tên lớp hoặc tên chủ đề
    dài hơn bề ngang cột — chuỗi thuần thì tràn ra ngoài mà không báo gì.
    """
    return Paragraph(an(v), kieu)


def ngay(s) -> str:
    """'2026-08-10' → '10/08/2026'. Phụ huynh Việt đọc ngày trước."""
    if not s:
        return '—'
    if isinstance(s, (date,)):
        return s.strftime('%d/%m/%Y')
    try:
        return date.fromisoformat(str(s)[:10]).strftime('%d/%m/%Y')
    except ValueError:
        return str(s)


def _bang(du_lieu, rong):
    """Bảng hai cột nhãn–giá trị, dùng lại ở mục I.

    CẢ HAI cột là `Paragraph`, không phải chuỗi thuần. Bản đầu để chuỗi thuần
    và tờ giấy in ra "Bài đã hoàn thành19 bài" — nhãn dài hơn bề ngang cột thì
    tràn đè lên ô bên cạnh, im lặng, không lỗi nào. Chỉ thấy được bằng cách MỞ
    tệp PDF ra nhìn; đọc lại chữ trích xuất thì hai chuỗi vẫn tách rời.

    Nhãn nhạt và thường, giá trị đậm và đen — cùng thứ bậc với thân thư HTML,
    để phụ huynh đọc thư rồi mở tệp không phải học lại cách đọc.
    """
    k_nhan = kieu('bang_nhan', 8.5, NHAT, sau=0)
    k_gt = kieu('bang_gt', 8.5, MUC, dam=True, sau=0)
    hang = [[Paragraph(an(a), k_nhan), Paragraph(an(b), k_gt)] for a, b in du_lieu]
    t = Table(hang, colWidths=rong, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 0), (-1, -2), 0.25, VIEN),
    ]))
    return t


def _bieu_do_hop_phan(khoa):
    """Cột: phần trăm bài đã hoàn thành của từng hợp phần.

    Vẽ NHÃN PHẦN TRĂM ngay trên mỗi cột. Không có nhãn thì người đọc phải đối
    chiếu chiều cao cột với trục — mà tờ này in đen trắng và đọc trên điện
    thoại, hai hoàn cảnh khiến việc đối chiếu ấy gần như bất khả.
    """
    # Bề ngang theo SỐ HỢP PHẦN, không cố định. Cố định 410pt thì một em mới
    # học hai hợp phần được vẽ hai cột mảnh nằm hai đầu một trục dài — trông
    # như biểu đồ mất dữ liệu chứ không như biểu đồ có hai giá trị.
    n_cot = max(1, len(khoa))
    rong_ve = min(410, 120 * n_cot)
    d = Drawing(rong_ve + 45, 150)
    bd = VerticalBarChart()
    bd.x, bd.y = 30, 38
    bd.width, bd.height = rong_ve, 95
    bd.data = [[int(k.get('pct') or 0) for k in khoa]]
    bd.categoryAxis.categoryNames = [str(k.get('title') or '') for k in khoa]
    bd.categoryAxis.labels.fontName = FONT
    bd.categoryAxis.labels.fontSize = 7
    bd.categoryAxis.labels.dy = -4
    bd.categoryAxis.labels.boxAnchor = 'n'
    # Nhãn dài thì xuống dòng thay vì đè lên nhau. 22 ký tự là bề ngang lọt
    # được của một cột khi có ba hợp phần.
    bd.categoryAxis.labels.width = 100
    bd.categoryAxis.labels.height = 22
    bd.valueAxis.valueMin, bd.valueAxis.valueMax, bd.valueAxis.valueStep = 0, 100, 25
    bd.valueAxis.labels.fontName = FONT
    bd.valueAxis.labels.fontSize = 7
    bd.bars[0].fillColor = NHAN
    bd.bars[0].strokeColor = None
    bd.barWidth = 9
    # Khoảng cách nhóm theo bề ngang thực tế: cột phải nằm giữa ô của nó, và
    # ô thì hẹp lại khi ít hợp phần.
    bd.groupSpacing = max(10, rong_ve / n_cot * 0.55)
    d.add(bd)

    # Nhãn số trên đỉnh cột, tính từ CÙNG công thức toạ độ mà biểu đồ dùng.
    n = max(1, len(khoa))
    rong_nhom = bd.width / n
    for i, k in enumerate(khoa):
        pct = int(k.get('pct') or 0)
        x = bd.x + rong_nhom * (i + 0.5)
        y = bd.y + bd.height * pct / 100.0 + 3
        d.add(String(x, y, '%d%%' % pct, fontName=FONT_DAM, fontSize=7.5,
                     fillColor=MUC, textAnchor='middle'))
    return d


def _dai_cua(m):
    for tu, den, ten, loi in DAI:
        if tu <= m <= den:
            return ten, loi
    return DAI[-1][2], DAI[-1][3]


def dung_pdf(bc: dict) -> bytes:
    """Dựng tờ báo cáo. Vào là payload của `dung_bao_cao`, ra là bytes PDF.

    KHÔNG chạm CSDL và KHÔNG kiểm quyền: nơi gọi đã làm cả hai. Nhờ vậy hàm
    này kiểm được bằng dữ liệu dựng tay, không cần một lớp và một học viên thật.
    """
    nap_font()

    em = bc.get('student') or {}
    lop = bc.get('class') or {}
    tv = bc.get('membership') or {}
    ky = bc.get('period') or {}
    cc = bc.get('attendance') or {}
    ht = bc.get('study') or {}
    cd = bc.get('topics') or {}

    dem = BytesIO()
    doc = SimpleDocTemplate(
        dem, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
        title='Báo cáo học tập — %s' % (em.get('name') or ''),
        author='TopHSA',
    )

    h1 = kieu('h1', 15, NHAN, dam=True, sau=1)
    h2 = kieu('h2', 10.5, MUC, dam=True, truoc=11, sau=5)
    p = kieu('p', 9)
    nho = kieu('nho', 7.8, NHAT, dan=1.45)
    kq = []

    # ── ĐẦU TỜ ──────────────────────────────────────────────────────────
    kq.append(Paragraph('BÁO CÁO HỌC TẬP', h1))
    kq.append(Paragraph(
        '%s &nbsp;·&nbsp; kỳ %s – %s' % (
            an(lop.get('name')), ngay(ky.get('from')), ngay(ky.get('to'))),
        kieu('duoi_h1', 9, NHAT, sau=8)))

    # ── I. THÔNG TIN CHUNG ─────────────────────────────────────────────
    kq.append(Paragraph('I. THÔNG TIN CHUNG', h2))

    o = kieu('o', 8.5, MUC, sau=0)
    trai = [
        ['Học viên', em.get('name')],
        ['Phụ huynh', (bc.get('parent') or {}).get('name') or '—'],
        ['Lớp', lop.get('name')],
        ['Giảng viên', lop.get('teacher') or '—'],
        ['Trạng thái', tv.get('status')],
        ['Vào lớp', ngay(tv.get('joinedAt'))],
    ]
    # "Chưa thi lần nào" chứ KHÔNG phải "0 điểm" — ranh giới 3 của
    # `parent_report.py`: viết 0 ở đây đọc như con làm sai hết.
    so_luot = ht.get('mockCount') or 0
    if ht.get('mockAvg') is None:
        diem_tb = 'chưa thi lần nào'
    elif so_luot == 1:
        # Gọi kết quả của MỘT lượt là "trung bình" thì phụ huynh đọc ra một xu
        # hướng, trong khi mới có một điểm. Đo trên CSDL thật: em id 9 thi đúng
        # một lần và được 0/9 — và "Điểm thi thử TB: 0%" gửi về nhà là một bản
        # án cho một lượt bấm.
        diem_tb = '%d%% — mới thi 1 lượt' % ht['mockAvg']
    else:
        diem_tb = '%d%%' % ht['mockAvg']
    diem_cao = ('%d%%' % ht['mockBest']) if ht.get('mockBest') is not None else '—'
    ti_le_cc = ('%d%%' % cc['attendedPct']) if cc.get('attendedPct') is not None else '—'
    da_tick = cc.get('sessionsCounted', 0)
    phai = [
        ['Kỳ báo cáo', '%s – %s' % (ngay(ky.get('from')), ngay(ky.get('to')))],
        # "0 có mặt / 0 buổi" đọc như con không đi buổi nào; sự thật là lớp
        # chưa có buổi nào được điểm danh. Ranh giới 3 của `parent_report.py`.
        ['Chuyên cần', '%s có mặt / %s buổi đã điểm danh (%s)' % (
            (cc.get('present', 0) + cc.get('late', 0)), da_tick, ti_le_cc)
         if da_tick else 'lớp chưa có buổi nào được điểm danh'],
        ['Bài đã hoàn thành', '%s bài' % ht.get('lessonsDone', 0)],
        ['Lượt thi thử', '%s lượt' % so_luot],
        ['Điểm thi thử TB', diem_tb],
        ['Điểm cao nhất', diem_cao],
    ]
    ngoai = Table(
        [[_bang(trai, [24 * mm, 54 * mm]), _bang(phai, [34 * mm, 58 * mm])]],
        colWidths=[80 * mm, 94 * mm], hAlign='LEFT')
    ngoai.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('LEFTPADDING', (0, 0), (-1, -1), 0),
                               ('RIGHTPADDING', (0, 0), (0, 0), 8)]))
    kq.append(ngoai)

    # ── II. CHUYÊN CẦN ─────────────────────────────────────────────────
    kq.append(Paragraph('II. CHUYÊN CẦN', h2))
    hang = [['', 'Số buổi']]
    for nhan, khoa in (('Có mặt', 'present'), ('Đi muộn', 'late'),
                       ('Vắng', 'absent'), ('Vắng có phép', 'excused'),
                       ('Không có dòng điểm danh', 'noRecord')):
        hang.append([nhan, str(cc.get(khoa, 0))])
    hang.append(['Tổng buổi đã điểm danh', str(cc.get('sessionsCounted', 0))])

    t = Table(hang, colWidths=[64 * mm, 22 * mm], hAlign='LEFT')
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT),
        ('FONTNAME', (0, 0), (-1, 0), FONT_DAM),
        ('FONTNAME', (0, -1), (-1, -1), FONT_DAM),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BACKGROUND', (0, 0), (-1, 0), NEN_NHAT),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.25, VIEN),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    kq.append(t)

    chua_tick = cc.get('sessionsUnmarked') or 0
    if chua_tick:
        # Nói ra khoảng trống thay vì im lặng chia cho một mẫu số nhỏ hơn —
        # cùng nguyên tắc `_chuyen_can` đã đặt ở tầng dữ liệu.
        kq.append(Spacer(1, 4))
        kq.append(Paragraph(
            'Lớp còn <b>%d buổi đã diễn ra mà giảng viên chưa điểm danh</b>, nên '
            'chưa tính vào bảng trên. Con số chuyên cần ở đây chỉ nói về những '
            'buổi đã được ghi nhận.' % chua_tick, nho))

    # ── III. TIẾN ĐỘ THEO HỢP PHẦN ─────────────────────────────────────
    khoa = cd.get('courses') or []
    kq.append(Paragraph('III. TIẾN ĐỘ THEO HỢP PHẦN', h2))
    if khoa:
        hang = [['Hợp phần', 'Bài đã xong', 'Tỉ lệ']]
        for k in khoa:
            hang.append([o_bang(k.get('title'), o),
                         '%s/%s' % (k.get('lessonsDone', 0), k.get('lessonsTotal', 0)),
                         '%s%%' % int(k.get('pct') or 0)])
        t = Table(hang, colWidths=[86 * mm, 32 * mm, 20 * mm], hAlign='LEFT')
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), FONT),
            ('FONTNAME', (0, 0), (-1, 0), FONT_DAM),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('BACKGROUND', (0, 0), (-1, 0), NEN_NHAT),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.25, VIEN),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ]))
        kq.append(t)
        kq.append(Spacer(1, 6))
        kq.append(_bieu_do_hop_phan(khoa))
        kq.append(Paragraph(
            'Điểm HSA cộng cả ba hợp phần, nên hợp phần thấp nhất là chỗ kéo '
            'điểm xuống nhiều nhất — không phải hợp phần con thích học nhất.', nho))
    else:
        kq.append(Paragraph('Chưa có dữ liệu tiến độ trong kỳ này.', p))

    # ── IV. CHỦ ĐỀ ─────────────────────────────────────────────────────
    # KHÔNG ngắt trang cứng ở đây. Bản đầu có `PageBreak()`, và với một em mới
    # học — hai hợp phần, hai chủ đề đo được — nó bỏ trống nửa dưới trang 1 rồi
    # in một trang 2 lèo tèo. Tờ hai trang mà mỗi trang nửa vời trông như báo
    # cáo bị lỗi, chứ không trông như báo cáo ngắn.
    #
    # `KeepTogether` thay vào đó: tiêu đề mục IV không bị mồ côi ở cuối trang,
    # nhưng khi còn chỗ thì mục IV nối tiếp ngay trong trang 1.
    kq.append(KeepTogether([
        Paragraph('IV. CHỦ ĐỀ ĐÃ ĐO ĐƯỢC', h2),
        Paragraph(
            'Đo trên %s chủ đề đã có bài làm, trên tổng %s chủ đề của chương trình. '
            'Chủ đề con chưa học tới thì không xuất hiện ở đây — chưa học không phải '
            'là yếu.' % (cd.get('measured', 0), cd.get('total', 0)), nho),
    ]))
    kq.append(Spacer(1, 6))

    # Gộp mạnh + yếu rồi xếp theo DẢI, học từ mục III của tờ TopHSA. Xếp theo
    # dải chứ không theo hai rổ "mạnh/yếu": hai rổ thì một chủ đề 59% và một
    # chủ đề 12% nằm chung một chỗ, mà cách chữa của chúng khác hẳn nhau.
    tat_ca = sorted(
        [*(cd.get('strong') or []), *(cd.get('weak') or [])],
        key=lambda t: -(t.get('mastery') or 0))
    if tat_ca:
        theo_dai = {}
        for t in tat_ca:
            ten_dai, loi = _dai_cua(int(t.get('mastery') or 0))
            theo_dai.setdefault((ten_dai, loi), []).append(t)

        for (ten_dai, loi), ds in theo_dai.items():
            khoi = [Paragraph(an(ten_dai), kieu('dai', 9.5, NHAN, dam=True,
                                                  truoc=7, sau=2))]
            hang = [[o_bang('%s — %s' % (t.get('courseTitle') or '', t.get('topic') or ''), o),
                     '%d%%' % int(t.get('mastery') or 0)] for t in ds]
            tb = Table(hang, colWidths=[130 * mm, 18 * mm], hAlign='LEFT')
            tb.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), FONT),
                ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('LINEBELOW', (0, 0), (-1, -2), 0.25, VIEN),
            ]))
            khoi.append(tb)
            khoi.append(Spacer(1, 3))
            khoi.append(Paragraph(an(loi), nho))
            # `KeepTogether`: một dải bị cắt ngang giữa bảng và lời khuyên thì
            # người đọc thấy danh sách chủ đề ở cuối trang này và lời khuyên ở
            # đầu trang sau, không nối được với nhau.
            kq.append(KeepTogether(khoi))
    else:
        kq.append(Paragraph(
            'Chưa chủ đề nào đo được. Con cần làm thêm bài để hệ thống có cơ sở '
            'nói con mạnh yếu ở đâu.', p))

    # ── V. NHẬN XÉT CỦA GIẢNG VIÊN ─────────────────────────────────────
    kq.append(Paragraph('V. NHẬN XÉT CỦA GIẢNG VIÊN', h2))
    kq.append(Paragraph(an(tv.get('teacherNote')) or
                        '<i>Giảng viên chưa ghi nhận xét cho kỳ này.</i>', p))

    # ── CUỐI TỜ: những điều tờ này KHÔNG nói ───────────────────────────
    kq.append(Spacer(1, 10))
    kq.append(Paragraph(
        '<b>Tờ này không nói gì về:</b> nhật ký học tập con tự ghi (đó là chỗ '
        'riêng của con), và dự đoán điểm thi thật. Các con số ở đây đo việc học '
        'trong kỳ, không phải một lời hứa về kết quả kỳ thi.', nho))
    kq.append(Spacer(1, 3))
    kq.append(Paragraph(
        'Có chỗ nào chưa đúng, xin nhắn lại cho giảng viên phụ trách lớp — số '
        'liệu sai sửa được, và sửa sớm thì kỳ sau đúng.', nho))

    doc.build(kq)
    return dem.getvalue()
