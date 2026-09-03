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


def _o(v):
    """Một ô về chuỗi. `None` → rỗng; số nguyên → không có đuôi `.0`."""
    if v is None:
        return ''
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def doc_xlsx(du_lieu):
    import openpyxl  # nhập trễ: chỉ đường nhập mới cần, không nặng lúc khởi động

    try:
        wb = openpyxl.load_workbook(io.BytesIO(du_lieu), read_only=True, data_only=True)
    except Exception as e:  # noqa: BLE001 — mọi lỗi đọc tệp đều là "tệp hỏng"
        raise LoiBangTinh('Không mở được tệp .xlsx: %s' % e) from e
    ws = wb.worksheets[0]
    return [[_o(c) for c in hang] for hang in ws.iter_rows(values_only=True)]


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
    hang = [h for h in hang if any(o for o in h)]
    if not hang:
        raise LoiBangTinh('Tệp không có dòng nào.')

    tieu_de = [_chuan_tieu_de(o) for o in hang[0]]
    if ten_khac:
        tieu_de = [ten_khac.get(t, t) for t in tieu_de]

    thieu = [c for c in cot_bat_buoc if c not in tieu_de]
    if thieu:
        raise LoiBangTinh(
            'Thiếu cột bắt buộc: %s. Dòng đầu của tệp phải là dòng TIÊU ĐỀ, '
            'chép nguyên từ mẫu tải về. Đang thấy: %s.'
            % (', '.join('"%s"' % c for c in thieu),
               ', '.join('"%s"' % t for t in tieu_de if t) or '(không có tiêu đề nào)'))

    than = hang[1:]
    if len(than) > MAX_DONG:
        raise LoiBangTinh('Tối đa %d dòng một lần nhập (tệp đang có %d). '
                          'Chia nhỏ ra rồi nhập nhiều lượt.' % (MAX_DONG, len(than)))

    ra = []
    for i, h in enumerate(than, start=2):   # +2: dòng 1 là tiêu đề, Excel đếm từ 1
        ban = {}
        for j, ten in enumerate(tieu_de):
            if ten:
                ban[ten] = h[j] if j < len(h) else ''
        ra.append((i, ban))
    return ra
