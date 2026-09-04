"""Đọc một bảng tính thành các DÒNG — nơi duy nhất trong repo biết định dạng ấy.

── VÌ SAO CÓ TỆP NÀY (04/09/2026) ──────────────────────────────────────────

Anh chốt đề thi và giáo trình do TopHSA cung cấp. Đường nhập hiện có nhận
**JSON** (`docs/NHAP_GIAO_TRINH.md`) — định dạng của lập trình viên. Người soạn
đề ở một trung tâm luyện thi làm việc trong Excel, không trong dấu ngoặc nhọn;
bảo họ chuyển sang JSON là dựng một bức tường ngay ở chỗ nội dung phải chảy vào.

Cách làm lấy từ Kahoot (tra 04/09/2026): **tải mẫu → điền → tải lên → sai thì
báo TỪNG DÒNG kèm số dòng để sửa rồi nạp lại.** Ba chi tiết của họ đáng chép:

  · trần độ dài hiện ra dưới dạng LỖI chứ không cắt ngầm — cắt ngầm thì người
    soạn tưởng đã vào đủ, và phát hiện ra vào lúc học viên đang thi;
  · lỗi nêu đủ MỌI dòng sai trong một lượt, không dừng ở dòng đầu tiên — sửa
    một lỗi rồi tải lên lại để gặp lỗi thứ hai là một vòng lặp làm người ta bỏ
    cuộc;
  · không có trạng thái nửa vời: kiểm hết rồi mới ghi.

Hai điều sau repo này đã có sẵn ở đường JSON (`lessons/content.py`,
`courseadmin/views.py`), nên tệp này chỉ lo phần ĐỌC.

── VÌ SAO ĐỌC CẢ .xlsx LẪN .csv ────────────────────────────────────────────

`.xlsx` là thứ người ta thật sự có, và nó không có vấn đề mã hoá: ô chứa chuỗi
Unicode, không phải byte. `.csv` thì Excel bản tiếng Việt lưu mặc định theo bảng
mã hệ thống, nên "Định lượng" quay về thành ký tự hỏng — repo này đã trả giá cho
đúng chuyện đó ở đường XUẤT (phải thêm BOM). Nhận cả hai, nhưng mẫu tải về là
`.xlsx` để người dùng đi đường ít bẫy nhất.
"""
import csv
import datetime
import io

#: Trần số dòng một lần nhập. Không phải để tiết kiệm bộ nhớ — để một file dán
#: nhầm (cả cuốn ngân hàng câu hỏi) không âm thầm thành 5.000 câu hỏi.
MAX_DONG = 2000

#: Trần độ dài một ô. Vượt thì BÁO, không cắt. Xem lý do ở đầu tệp.
MAX_O = 4000


class LoiBangTinh(Exception):
    """Không đọc nổi tệp — khác hẳn với 'đọc được nhưng nội dung sai'."""


def _chuan_tieu_de(s):
    """Tên cột về dạng so khớp được: thường, bỏ khoảng trắng thừa.

    KHÔNG bỏ dấu tiếng Việt: tiêu đề mẫu là tiếng Việt và người dùng sẽ copy
    nguyên, nên so khớp thẳng là đúng và dễ đoán. Bỏ dấu ở đây sẽ làm "Đáp án"
    và "Dap an" cùng khớp — nghe tiện, nhưng rồi một cột gõ sai chính tả cũng
    khớp và người soạn không bao giờ biết cột nào đã được dùng.
    """
    return ' '.join(str(s or '').split()).lower()


def _o(v, dinh_dang=None):
    """Một ô về chuỗi — CÁI NGƯỜI SOẠN NHÌN THẤY, không phải cái Excel lưu.

    Hai chỗ hai thứ ấy khác nhau, và cả hai hỏng ÂM THẦM (đo 04/09/2026):

        ô hiện "30%"        → Excel lưu 0.3        → bản cũ trả "0.3"
        ô hiện "04/09/2026" → Excel lưu datetime   → "2026-09-04 00:00:00"

    Không chỗ nào báo lỗi: chuỗi ấy hợp lệ, nó chỉ SAI. Người soạn gõ "30%" vào
    ô đáp án, và học viên phải trả lời "0.3" mới được tính đúng — lộ ra vào đúng
    lúc đang thi. Đây là loại lỗi mà bộ kiểm nội dung không thể bắt được, vì tới
    lúc nó nhìn thì dữ liệu đã sai từ trước rồi.

    `number_format` phân biệt được hai thứ, và nó CÓ ở chế độ `read_only` — đã
    đo — nhưng chỉ khi đọc bằng `values_only=False`, tức phải bỏ đường tắt cũ.
    """
    if v is None:
        return ''
    if isinstance(v, datetime.datetime):
        # Excel không có kiểu "chỉ ngày": ngày về là datetime lúc 00:00.
        if v.hour or v.minute or v.second:
            return v.strftime('%d/%m/%Y %H:%M')
        return v.strftime('%d/%m/%Y')
    if isinstance(v, datetime.date):
        return v.strftime('%d/%m/%Y')
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if dinh_dang and '%' in dinh_dang:
            pt = v * 100
            if abs(pt - round(pt)) < 1e-9:
                return '%d%%' % round(pt)
            return '%s%%' % ('%.4f' % pt).rstrip('0').rstrip('.')
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
    return str(v).strip()


def doc_xlsx(du_lieu):
    import openpyxl  # nhập trễ: chỉ đường nhập mới cần, không nặng lúc khởi động

    try:
        wb = openpyxl.load_workbook(io.BytesIO(du_lieu), read_only=True, data_only=True)
    except Exception as e:  # noqa: BLE001 — mọi lỗi đọc tệp đều là "tệp hỏng"
        raise LoiBangTinh('Không mở được tệp .xlsx: %s' % e) from e

    def doc_trang(ws):
        return [[_o(c.value, getattr(c, 'number_format', None)) for c in hang]
                for hang in ws.iter_rows()]

    # Lấy trang ĐẦU TIÊN CÓ DỮ LIỆU, không cứng `worksheets[0]`. Người ta hay để
    # trang 1 là "Hướng dẫn" rồi mới tới dữ liệu ở trang 2; bản cũ đọc trang 1
    # rồi báo "thiếu cột bắt buộc" trong khi dữ liệu nằm ngay trang bên cạnh —
    # một thông báo lỗi chỉ đúng chữ, còn chỗ nó chỉ tới thì không có gì sai.
    #
    # Cần ÍT NHẤT 2 dòng (tiêu đề + một dòng dữ liệu): một trang chỉ có một dòng
    # chữ giới thiệu không phải là bảng dữ liệu.
    for ws in wb.worksheets:
        rows = doc_trang(ws)
        if sum(1 for h in rows if any(o for o in h)) >= 2:
            return rows
    return doc_trang(wb.worksheets[0]) if wb.worksheets else []


def doc_csv(du_lieu):
    for ma in ('utf-8-sig', 'utf-8', 'cp1258', 'latin-1'):
        try:
            van = du_lieu.decode(ma)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise LoiBangTinh('Không đọc được mã ký tự của tệp .csv. '
                          'Lưu lại bằng "CSV UTF-8" rồi thử lại, hoặc dùng .xlsx.')
    # `Sniffer` đoán dấu phân cách: Excel bản Việt hay dùng dấu chấm phẩy.
    try:
        dau = csv.Sniffer().sniff(van[:4000], delimiters=',;\t').delimiter
    except csv.Error:
        dau = ','
    return [[_o(c) for c in hang] for hang in csv.reader(io.StringIO(van), delimiter=dau)]


def doc(ten_tep, du_lieu):
    """Đọc tệp → danh sách các DÒNG (mỗi dòng là danh sách ô, đã về chuỗi)."""
    ten = (ten_tep or '').lower()
    if ten.endswith('.xlsx'):
        return doc_xlsx(du_lieu)
    if ten.endswith(('.csv', '.txt')):
        return doc_csv(du_lieu)
    raise LoiBangTinh('Chỉ nhận tệp .xlsx hoặc .csv (đang nhận: %s).'
                      % (ten_tep or 'không rõ tên'))


def thanh_ban_ghi(hang, cot_bat_buoc=(), ten_khac=None):
    """Dòng thô → danh sách ``(so_dong, {tên cột: giá trị})``.

    ``so_dong`` là số dòng NHƯ NGƯỜI DÙNG THẤY TRONG EXCEL (tính từ 1, kể cả
    dòng tiêu đề). Đây là chi tiết quyết định việc sửa lỗi có nhanh không: báo
    "dòng thứ 3 của mảng" thì người soạn phải tự đếm; báo "dòng 4" thì họ nhấn
    Ctrl+G trong Excel là tới nơi.

    ``ten_khac`` cho phép một cột có nhiều tên gọi (ví dụ "đáp án" và "dap an"),
    khai TƯỜNG MINH chứ không đoán bằng cách bỏ dấu.
    """
    # ĐÁNH SỐ TRƯỚC, LỌC SAU. Bản đầu làm ngược lại — lọc dòng trống rồi mới
    # `enumerate` — nên mỗi dòng trống trong tệp đẩy toàn bộ số dòng phía dưới
    # lệch đi một. Docstring ngay trên đây HỨA "số dòng như người dùng thấy
    # trong Excel"; mã thì đếm theo vị trí trong mảng đã lọc. Chú thích sai
    # nguy hiểm hơn không có chú thích: nó tắt phản xạ kiểm tra của người sau,
    # và ở đây nó còn gửi người soạn tới sửa NHẦM DÒNG.
    danh = [(i, h) for i, h in enumerate(hang, start=1) if any(o for o in h)]
    if not danh:
        raise LoiBangTinh('Tệp không có dòng nào.')

    tieu_de = [_chuan_tieu_de(o) for o in danh[0][1]]
    if ten_khac:
        tieu_de = [ten_khac.get(t, t) for t in tieu_de]

    thieu = [c for c in cot_bat_buoc if c not in tieu_de]
    if thieu:
        raise LoiBangTinh(
            'Thiếu cột bắt buộc: %s. Dòng đầu của tệp phải là dòng TIÊU ĐỀ, '
            'chép nguyên từ mẫu tải về. Đang thấy: %s.'
            % (', '.join('"%s"' % c for c in thieu),
               ', '.join('"%s"' % t for t in tieu_de if t) or '(không có tiêu đề nào)'))

    than = danh[1:]
    if len(than) > MAX_DONG:
        raise LoiBangTinh('Tối đa %d dòng một lần nhập (tệp đang có %d). '
                          'Chia nhỏ ra rồi nhập nhiều lượt.' % (MAX_DONG, len(than)))

    ra = []
    for so_dong, h in than:
        ban = {}
        for j, ten in enumerate(tieu_de):
            if ten:
                o = h[j] if j < len(h) else ''
                if len(o) > MAX_O:
                    raise LoiBangTinh(
                        'Dòng %d, cột "%s": ô dài %d ký tự, tối đa %d. '
                        'Cắt bớt trong Excel rồi nhập lại — hệ thống KHÔNG tự cắt, '
                        'vì cắt ngầm thì nội dung mất mà không ai biết.'
                        % (so_dong, ten, len(o), MAX_O))
                ban[ten] = o
        ra.append((so_dong, ban))
    return ra
