"""Đọc tờ "Báo cáo kết quả thi" của hệ thống khảo thí ngoài (uranustech) thành dữ liệu.

── VÌ SAO CÓ TỆP NÀY (15/09/2026) ─────────────────────────────────────────

TopHSA tổ chức thi thử trên một hệ thống khảo thí khác, và anh Sơn trả lời hệ
thống ấy "chỉ xem được trên web" — không có API. Nhưng tờ PDF nó xuất cho TỪNG
em thì đọc được sạch, và trong đó có đúng thứ báo cáo phụ huynh đang thiếu:

    · điểm ba phần và tổng /150 của một kỳ thi THẬT (không phải điểm luyện tập);
    · tỉ lệ đúng theo TỪNG đơn vị kiến thức — 24 dòng ở tệp mẫu.

Nên không cần bên kia mở gì cả: học vụ kéo tệp PDF vào, hệ thống bóc số ra.

── ĐỌC MỤC "III. PHÂN TÍCH KẾT QUẢ THI", KHÔNG ĐỌC BẢNG MA TRẬN ───────────

Tờ báo cáo có hai chỗ chứa cùng thông tin: bảng ma trận (mục II) và danh sách
phân tích (mục III). Bảng ma trận xếp số theo bốn cấp độ nhận thức, và khi bóc
ra chữ thì các con số dính vào nhau ("20\\n2\\n1 0\\n1" cho một hàng) — đọc được
nhưng mong manh, đổi bố cục một chút là sai số.

Mục III thì mỗi đơn vị kiến thức nằm gọn một dòng theo đúng một khuôn:

    Phần 1: Định lượng và Xử lí số liệu: Hình học Oxyz (50%)

Một dòng, một khuôn, có cả tên phần lẫn phần trăm. Đó là chỗ đáng đọc.

── BẮT BUỘC DÙNG extraction_mode='layout' ────────────────────────────────

Cách bóc chữ mặc định của `pypdf` chèn dấu cách quanh mọi chữ có dấu:
"Nguy ễ n Th ị  Minh Ng ọ c", "Đị nhlượ ng vàXử  lísố  liệ u". Đo 15/09: cách mặc
định khớp 1/4 chuỗi mong đợi, chế độ `layout` khớp 4/4. Tôi có thử tự ghép lại
bằng luật "mảnh một ký tự thì dính vào mảnh trước" — ra "Đị nhlượ ng", tức tệ
hơn. Đừng làm lại thí nghiệm ấy.

Hàm đọc nhận CHỮ chứ không nhận tệp, nên phép kiểm chạy được mà không cần một
tệp PDF nào trong kho mã — tờ báo cáo thật mang tên một học sinh có thật, và kho
này công khai.
"""
import re
from datetime import date

#: Tên ba phần thi trên tờ báo cáo → số phần. Phần 3 đổi tên theo bài thi tự
#: chọn của thí sinh ("Tiếng Anh" hoặc "Khoa học"), nên khớp theo tiền tố.
TEN_PHAN = (
    (1, ('định lượng',)),
    (2, ('định tính',)),
    (3, ('tiếng anh', 'khoa học', 'tổ hợp')),
)

MAX_BYTES = 8 * 1024 * 1024   # tệp mẫu 7 trang nặng ~300 kB; 8 MB là rất rộng

_DONG_DON_VI = re.compile(
    r'Phần\s*(\d)\s*:\s*([^:()\n]{3,60}?)\s*:\s*([^:()\n]{2,80}?)\s*\((\d{1,3})\s*%\)')
_DIEM_PHAN = re.compile(r'([^:\n]{3,60}?)\s*:\s*(\d{1,3})\s*/\s*(\d{1,3})\s*$', re.M)
_TONG = re.compile(r'TỔNG\s*ĐIỂM\s*:\s*(\d{1,3})\s*/\s*(\d{1,3})')


class LoiDocBaoCao(ValueError):
    """Không đọc được tờ báo cáo — thông điệp viết cho học vụ đọc."""


def _gon(s):
    return re.sub(r'\s+', ' ', (s or '')).strip()


def _truong(chu, nhan, mau=r'(.+?)(?:\s{2,}|$)'):
    """Đọc một ô ở mục "I. THÔNG TIN CHUNG" — nhãn và giá trị cách nhau ≥2 dấu cách.

    Bố cục hai cột: cùng một dòng có thể chứa cả ô bên trái lẫn ô bên phải
    ("Họ và tên   Nguyễn…   Định lượng…: 27/50"), nên phải dừng ở khoảng trắng
    kép chứ không lấy tới hết dòng.
    """
    m = re.search(nhan + r'\s{2,}' + mau, chu)
    return _gon(m.group(1)) if m else None


def _so_phan(ten):
    t = _gon(ten).lower()
    for so, tien_to in TEN_PHAN:
        if any(t.startswith(x) for x in tien_to):
            return so
    return None


def _dot(chu):
    """Tên đợt thi — dòng tiêu đề ngay dưới "BÁO CÁO KẾT QUẢ THI", ví dụ "Thi thử Online 2308".

    KHÔNG dùng khuôn "nhãn + hai dấu cách + giá trị" như các ô ở mục I: dòng này
    là một tiêu đề, nhãn và giá trị chỉ cách nhau MỘT dấu cách. Bản đầu đọc theo
    khuôn kia nên trường này rỗng — cả trên bản chữ thử lẫn trên tệp thật.
    """
    for dong in chu.splitlines():
        d = _gon(dong)
        if d.lower().startswith('thi thử') and len(d) > 8:
            return _gon(d[len('thi thử'):])
    return None


def doc_chu(du_lieu):
    """Bóc chữ từ tệp PDF (dạng bytes). Ném `LoiDocBaoCao` nếu không đọc được."""
    if not du_lieu:
        raise LoiDocBaoCao('Tệp rỗng.')
    if len(du_lieu) > MAX_BYTES:
        raise LoiDocBaoCao('Tệp nặng hơn %d MB — kiểm lại xem có đúng tờ báo cáo không.'
                           % (MAX_BYTES // (1024 * 1024)))
    import io

    from pypdf import PdfReader
    from pypdf.errors import PyPdfError
    # Bắt ĐÚNG họ lỗi của pypdf cộng ba lỗi nền khi thân tệp không phải PDF
    # (`KeyError`/`IndexError`/`ValueError` khi nó dò bảng tham chiếu). Bắt
    # `Exception` trần thì nuốt luôn lỗi lập trình của chính mình — luật `BLE`.
    # `PyPdfError` là gốc của mọi lỗi pypdf (PdfReadError, EmptyFileError…).
    # Bản đầu nhập `PdfError` — một cái tên KHÔNG có — và máy chủ trả 500 cho
    # mọi tệp tải lên; `tests_nhap_ket_qua_thi.py::test_doc_chu_*` canh chỗ này.
    try:
        doc = PdfReader(io.BytesIO(du_lieu))
        # Trang không có `/Contents` là trang TRẮNG hợp lệ, nhưng chế độ `layout`
        # của pypdf 6.17 ném `KeyError('/Contents')` với nó (đo 16/09). Không bỏ
        # qua thì MỘT trang trắng cuối tệp làm cả tờ báo cáo thành "không mở được".
        trang = [(p.extract_text(extraction_mode='layout') or '')
                 for p in doc.pages if '/Contents' in p]
    except (PyPdfError, OSError, KeyError, IndexError, ValueError, TypeError):
        # Không kèm tên lớp lỗi ("PdfStreamError") vào câu: người đọc là học vụ,
        # và bản đầu hiện đúng chữ ấy lên màn hình (soi ảnh 16/09).
        raise LoiDocBaoCao('Không mở được tệp PDF — tệp có thể hỏng hoặc không '
                           'phải PDF.') from None
    chu = '\n'.join(trang)
    if len(chu.strip()) < 200:
        raise LoiDocBaoCao('Tệp PDF này gần như không có chữ — có thể là bản scan '
                           'chụp ảnh. Cần bản PDF do hệ thống khảo thí xuất ra.')
    return chu


def doc_bao_cao(chu):
    """Chữ của tờ báo cáo → dict dữ liệu. Ném `LoiDocBaoCao` nếu thiếu phần bắt buộc."""
    ho_ten = _truong(chu, 'Họ và tên')
    if not ho_ten:
        raise LoiDocBaoCao('Không thấy dòng "Họ và tên" — tệp này có phải tờ báo cáo '
                           'kết quả thi không?')

    # Dựng ngày từ ba số thay vì `strptime`: tờ báo cáo chỉ có NGÀY, không giờ và
    # không múi giờ, nên mọi đường đi qua `datetime` đều tạo ra một mốc thời gian
    # không có thật rồi lại cắt bỏ (luật `DTZ` của dự án canh đúng chuyện này).
    ngay_chu = _truong(chu, 'Ngày thi', r'(\d{1,2}/\d{1,2}/\d{4})')
    ngay_thi = None
    if ngay_chu:
        ng, th, na = (int(v) for v in ngay_chu.split('/'))
        try:
            ngay_thi = date(na, th, ng)
        except ValueError:      # 31/02 chẳng hạn — tờ hỏng, không phải lỗi của mình
            ngay_thi = None
    if not ngay_thi:
        raise LoiDocBaoCao('Không đọc được "Ngày thi" (cần dạng ngày/tháng/năm).')

    m = _TONG.search(chu)
    if not m:
        raise LoiDocBaoCao('Không thấy dòng "TỔNG ĐIỂM".')
    tong, tong_toi_da = int(m.group(1)), int(m.group(2))

    # Điểm từng phần: lấy những dòng "…: x/50" và chỉ giữ dòng có TÊN PHẦN nhận ra được.
    # Dòng của mục I nằm ở cột phải nên phần đầu dòng có thể còn dính ô bên trái —
    # cắt từ khoảng trắng kép cuối cùng trở đi.
    diem_phan = []
    for ten, diem, toi_da in _DIEM_PHAN.findall(chu):
        ten = _gon(re.split(r'\s{2,}', ten)[-1])
        so = _so_phan(ten)
        if so and not any(d['phan'] == so for d in diem_phan):
            diem_phan.append({'phan': so, 'ten': ten, 'diem': int(diem), 'toiDa': int(toi_da)})
    diem_phan.sort(key=lambda d: d['phan'])

    don_vi = []
    for so, ten_phan, ten, pct in _DONG_DON_VI.findall(chu):
        don_vi.append({'phan': int(so), 'phanTen': _gon(ten_phan),
                       'ten': _gon(ten), 'pct': int(pct)})
    if not don_vi:
        raise LoiDocBaoCao('Không thấy mục "III. PHÂN TÍCH KẾT QUẢ THI" liệt kê các '
                           'đơn vị kiến thức — tờ báo cáo có thể thuộc bản khác.')

    # CẢNH BÁO, KHÔNG PHẢI LỖI. Tờ báo cáo là dữ liệu của bên khác; một chỗ lệch
    # không có nghĩa là cả tệp hỏng, và chặn cả lượt nhập vì nó thì học vụ mất
    # đường làm việc. Hiện ra để người nhập tự quyết.
    canh_bao = []
    if diem_phan:
        cong = sum(d['diem'] for d in diem_phan)
        if len(diem_phan) == 3 and cong != tong:
            canh_bao.append('Tổng điểm ghi %d nhưng cộng ba phần lại là %d.' % (tong, cong))
    else:
        canh_bao.append('Không đọc được điểm từng phần, chỉ có tổng điểm.')
    if tong > tong_toi_da:
        canh_bao.append('Tổng điểm %d lớn hơn thang %d.' % (tong, tong_toi_da))

    return {
        'hoTen': ho_ten,
        'maHocSinh': _truong(chu, 'Mã học sinh', r'(\S+)'),
        'ngayThi': ngay_thi,
        'hinhThuc': _truong(chu, 'Hình thức thi', r'(\S+)'),
        'diaDiem': _truong(chu, 'Địa điểm thi'),
        'dot': _dot(chu),
        'tongDiem': tong,
        'tongToiDa': tong_toi_da,
        'diemPhan': diem_phan,
        'donVi': don_vi,
        'canhBao': canh_bao,
    }


def doc_tep(du_lieu):
    """Tệp PDF (bytes) → dict dữ liệu. Gộp hai bước cho đường gọi thật."""
    return doc_bao_cao(doc_chu(du_lieu))
