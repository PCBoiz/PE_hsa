"""Đọc tờ báo cáo kết quả thi của hệ thống khảo thí ngoài — `teaching/nhap_ket_qua_thi.py`.

KHÔNG có tệp PDF nào trong kho mã: tờ báo cáo thật mang tên một học sinh CÓ THẬT
và kho này công khai. Bản chữ dưới đây giữ NGUYÊN bố cục tờ thật (đã đo bằng
`extraction_mode='layout'` trên tệp mẫu ngày 15/09/2026) và chỉ thay tên, mã,
địa điểm bằng dữ liệu giả.

Phần lớn phép kiểm chạy trên CHỮ nên không cần CSDL. Riêng hai phép `test_doc_chu_*`
đi qua `pypdf` thật với tệp tự dựng trong bộ nhớ — không có chúng thì dòng nhập
`pypdf` không được chạy tới lần nào.
"""
import pytest

from teaching.nhap_ket_qua_thi import LoiDocBaoCao, doc_bao_cao

# Bố cục hai cột của mục I là chỗ dễ đọc sai nhất: dòng "Họ và tên" mang theo cả
# ô điểm bên phải. Giữ đúng như tờ thật.
CHU = """
                                    BÁO CÁO KẾT QUẢ THI
                                      Thi thử Online 2308

I. THÔNG TIN CHUNG

    Thông tin thí sinh                                    Điểm thi
    Họ và tên       Nguyễn Văn An                         Định lượng và Xử lí số liệu: 27/50
    Mã học sinh     ONL000000                             Định tính: 38/50
    Ngày thi        23/08/2026                            Tiếng Anh: 40/50
    Hình thức thi   Offline                               TỔNG ĐIỂM: 105/150
    Địa điểm thi    THPT Thử Nghiệm - Hà Nội

II. BÁO CÁO KẾT QUẢ

II.1. Phần 1: Định lượng và Xử lí số liệu
    Đơn vị kiến thức                        Biết    Hiểu    Vận dụng    Tổng
    Số học, đại số tổ hợp và xác suất       2 0     1 0         2 1     1/5 (20%)
    Thống kê                                 –      1 1         3 2     3/4 (75%)
    Tổng                                                                27/50 (54%)

III. PHÂN TÍCH KẾT QUẢ THI

Đạt 91–100%
Học sinh nắm vững kiến thức từ cơ bản đến nâng cao.
Phần 3: Tổ hợp: Antonyms (100%)
Phần 3: Tổ hợp: Cloze text (100%)

Đạt 61–80%
Học sinh đã nắm khá chắc kiến thức cơ bản.
Phần 1: Định lượng và Xử lí số liệu: Phương trình, bất phương trình của các hàm số cơ bản (80%)
Phần 2: Định tính: Văn bản nghị luận (80%)
Phần 3: Tổ hợp: Logical thinking and problem solving (80%)
Phần 1: Định lượng và Xử lí số liệu: Thống kê (75%)
Phần 2: Định tính: Ngôn ngữ - Tiếng việt (67%)

Đạt 41–60%
Phần 1: Định lượng và Xử lí số liệu: Dãy số, cấp số cộng, cấp số nhân, giới hạn, liên tục (60%)
Phần 1: Định lượng và Xử lí số liệu: Hình học Oxyz (50%)

Đạt 0–20%
Phần 1: Định lượng và Xử lí số liệu: Nguyên hàm, tích phân và ứng dụng (0%)
"""


@pytest.fixture
def d():
    return doc_bao_cao(CHU)


def test_doc_duoc_thong_tin_chung(d):
    assert d['hoTen'] == 'Nguyễn Văn An', 'bố cục hai cột: không được nuốt sang ô điểm bên phải'
    assert d['maHocSinh'] == 'ONL000000'
    assert d['ngayThi'].isoformat() == '2026-08-23', 'ngày trên tờ là ngày/tháng/năm'
    assert d['hinhThuc'] == 'Offline'
    assert d['diaDiem'] == 'THPT Thử Nghiệm - Hà Nội'
    assert d['dot'] == 'Online 2308'


def test_diem_tong_va_tung_phan(d):
    assert (d['tongDiem'], d['tongToiDa']) == (105, 150)
    assert [(p['phan'], p['diem']) for p in d['diemPhan']] == [(1, 27), (2, 38), (3, 40)]
    assert d['diemPhan'][2]['ten'] == 'Tiếng Anh', 'phần 3 đổi tên theo bài tự chọn'
    assert d['canhBao'] == [], '27+38+40 = 105, không có gì để cảnh báo'


def test_doc_du_don_vi_kien_thuc_va_dung_phan(d):
    assert len(d['donVi']) == 10
    theo_phan = {}
    for v in d['donVi']:
        theo_phan.setdefault(v['phan'], []).append(v['ten'])
    assert len(theo_phan[1]) == 5 and len(theo_phan[2]) == 2 and len(theo_phan[3]) == 3
    assert 'Hình học Oxyz' in theo_phan[1]
    assert 'Logical thinking and problem solving' in theo_phan[3], 'tên tiếng Anh vẫn phải đọc được'


def test_giu_nguyen_ten_dai_co_dau_phay(d):
    ten = [v['ten'] for v in d['donVi']]
    assert 'Dãy số, cấp số cộng, cấp số nhân, giới hạn, liên tục' in ten
    assert 'Phương trình, bất phương trình của các hàm số cơ bản' in ten


def test_phan_tram_doc_dung_ke_ca_0(d):
    pct = {v['ten']: v['pct'] for v in d['donVi']}
    assert pct['Nguyên hàm, tích phân và ứng dụng'] == 0, '0% phải là 0, không phải None'
    assert pct['Antonyms'] == 100
    assert pct['Hình học Oxyz'] == 50


def test_KHONG_doc_nham_dong_tong_cua_bang_ma_tran(d):
    """Bảng ma trận cũng có dòng "27/50 (54%)" nhưng không mang tên đơn vị nào.

    Đọc nhầm nó thành một đơn vị kiến thức là thêm một chủ đề ma vào báo cáo
    gửi phụ huynh."""
    assert all(v['ten'] not in ('Tổng', '') for v in d['donVi'])
    assert all(v['pct'] != 54 for v in d['donVi'])


def test_thieu_tong_diem_thi_bao_loi_ro_rang():
    with pytest.raises(LoiDocBaoCao) as e:
        doc_bao_cao(CHU.replace('TỔNG ĐIỂM: 105/150', ''))
    assert 'TỔNG ĐIỂM' in str(e.value)


def test_khong_phai_to_bao_cao_thi_bao_loi():
    with pytest.raises(LoiDocBaoCao) as e:
        doc_bao_cao('Đây là một tệp PDF khác hẳn, không có gì liên quan.')
    assert 'Họ và tên' in str(e.value)


def test_thieu_muc_III_thi_bao_loi():
    chu = CHU.split('III. PHÂN TÍCH')[0]
    with pytest.raises(LoiDocBaoCao) as e:
        doc_bao_cao(chu)
    assert 'đơn vị kiến thức' in str(e.value)


def test_doc_chu_tu_tep_KHONG_PHAI_PDF_bao_loi_ro_rang_chu_khong_500():
    """Đi qua đường đọc PDF THẬT (`doc_chu`), không qua hàm giả.

    Phép kiểm cửa nhập thay `doc_tep` bằng hàm giả, và mọi phép kiểm khác ở tệp
    này nhận CHỮ — nên suốt một vòng không phép kiểm nào chạm tới dòng
    `from pypdf.errors import …`. Dòng ấy nhập một cái tên KHÔNG CÓ trong pypdf,
    và chỉ lượt bấm thật trên trình duyệt mới lộ ra: máy chủ trả 500 cho mọi tệp
    tải lên (15/09/2026).
    """
    from teaching.nhap_ket_qua_thi import doc_chu
    with pytest.raises(LoiDocBaoCao) as e:
        doc_chu(b'day khong phai tep PDF, chi la chu thuong' * 10)
    assert 'PDF' in str(e.value)


def test_doc_chu_tu_PDF_trang_bao_la_khong_co_chu():
    """PDF hợp lệ nhưng không có chữ (bản scan chụp ảnh) → nói đúng chuyện ấy."""
    import io

    from pypdf import PdfWriter

    from teaching.nhap_ket_qua_thi import doc_chu
    w = PdfWriter()
    w.add_blank_page(width=595, height=842)
    buf = io.BytesIO()
    w.write(buf)
    with pytest.raises(LoiDocBaoCao) as e:
        doc_chu(buf.getvalue())
    assert 'không có chữ' in str(e.value)


def test_lech_tong_thi_CANH_BAO_chu_khong_chan():
    d = doc_bao_cao(CHU.replace('TỔNG ĐIỂM: 105/150', 'TỔNG ĐIỂM: 120/150'))
    assert d['tongDiem'] == 120, 'vẫn đọc được, không ném lỗi'
    assert any('cộng ba phần' in c for c in d['canhBao'])


# ── Bỏ qua bảng ma trận khi bóc chữ (16/09/2026) ─────────────────────────────
#
# Đo trên tờ thật 7 trang: trang 1 có mục I, trang 2–5 CHỈ là bảng ma trận (43%
# thời gian bóc chữ), mục III bắt đầu ở trang 6. Trên Render một tờ mất 6–7 s, hai
# tờ song song 22 s và làm một lời gọi nhẹ của người khác chờ 4,2 s. Tờ dựng bằng
# reportlab dưới đây giữ đúng bố cục ấy, không mang tên người thật nào.

DAU_MA_TRAN = 'MATRIX-FILLER-MARK'


def _pdf(*trang):
    """PDF nhiều trang: mỗi trang là danh sách dòng, mỗi dòng là các ô (x, chữ)."""
    import io
    from pathlib import Path

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    if 'DVT' not in pdfmetrics.getRegisteredFontNames():
        font = Path(__file__).resolve().parent.parent / 'assets' / 'fonts' / 'DejaVuSans.ttf'
        pdfmetrics.registerFont(TTFont('DVT', str(font)))
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    for dong_cua_trang in trang:
        y = A4[1] - 60
        for dong in dong_cua_trang:
            for x, chu in dong:
                c.setFont('DVT', 10)
                c.drawString(x, y, chu)
            y -= 18
        c.showPage()
    c.save()
    return buf.getvalue()


TRANG_I = [
    [(200, 'BÁO CÁO KẾT QUẢ THI')],
    [(205, 'Thi thử Online 1309')],
    [(40, 'I. THÔNG TIN CHUNG')],
    [(50, 'Họ và tên'), (140, 'Nguyễn Văn An'), (330, 'Định lượng và Xử lí số liệu: 30/50')],
    [(50, 'Mã học sinh'), (140, 'ONL000000'), (330, 'Định tính: 33/50')],
    [(50, 'Ngày thi'), (140, '13/09/2026'), (330, 'Tiếng Anh: 38/50')],
    [(50, 'Hình thức thi'), (140, 'Offline'), (330, 'TỔNG ĐIỂM: 101/150')],
    [(50, 'Địa điểm thi'), (140, 'Trung tâm thử nghiệm')],
]
TRANG_MA_TRAN = [[(40, 'II. BÁO CÁO KẾT QUẢ')]] + [
    [(40, '%s hàng %d   2 0   1 0   2 1   1/5 (20%%)' % (DAU_MA_TRAN, i))] for i in range(20)]
TRANG_III = [
    [(40, 'III. PHÂN TÍCH KẾT QUẢ THI')],
    [(40, 'Phần 1: Định lượng và Xử lí số liệu: Hình học Oxyz (40%)')],
    [(40, 'Phần 2: Định tính: Văn bản nghị luận (60%)')],
]
TRANG_III_TIEP = [
    [(40, 'Phần 3: Tổ hợp: Reading comprehension 1 (30%)')],
    [(40, 'Phần 3: Tổ hợp: Antonyms (100%)')],
]


def test_doc_chu_BO_QUA_bang_ma_tran_giua_muc_I_va_muc_III():
    from teaching.nhap_ket_qua_thi import doc_chu
    chu = doc_chu(_pdf(TRANG_I, TRANG_MA_TRAN, TRANG_MA_TRAN, TRANG_MA_TRAN, TRANG_III, TRANG_III_TIEP))
    assert DAU_MA_TRAN not in chu, 'ba trang ma trận vẫn bị bóc chữ — thứ tốn CPU Render nhất'
    assert chu.index('THÔNG TIN CHUNG') < chu.index('PHÂN TÍCH KẾT QUẢ'), 'giữ đúng thứ tự trang'

    d = doc_bao_cao(chu)
    assert (d['tongDiem'], d['tongToiDa']) == (101, 150)
    assert len(d['donVi']) == 4, 'mục III trải HAI trang: không được mất trang cuối'


def test_doc_chu_KHONG_thay_muc_III_thi_doc_HET_de_bao_loi_dung():
    """Tờ bản khác, không có tiêu đề mục III: đọc cả tệp như trước (chậm hơn chứ
    không sai), để câu lỗi vẫn là "không thấy mục III" chứ không phải một tờ cụt."""
    from teaching.nhap_ket_qua_thi import doc_chu
    chu = doc_chu(_pdf(TRANG_I, TRANG_MA_TRAN, TRANG_MA_TRAN))
    assert DAU_MA_TRAN in chu
    with pytest.raises(LoiDocBaoCao) as e:
        doc_bao_cao(chu)
    assert 'đơn vị kiến thức' in str(e.value)
