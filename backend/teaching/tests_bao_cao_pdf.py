"""Tờ báo cáo phụ huynh dạng PDF.

KHÔNG cần CSDL: `dung_pdf` nhận thẳng payload, nên phép kiểm dựng dữ liệu tay.
Đó là lý do nó được tách khỏi view ngay từ đầu.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. **Chữ Việt phải ra chữ Việt.** `reportlab` kèm font Vera, mà Vera thiếu
     40/57 ký tự tiếng Việt đã đo. Ai lỡ tay đổi font về mặc định thì tên học
     viên biến thành ô vuông — trên tờ giấy gửi về tận nhà.
  2. **Dấu `&` và `<` trong tên phải hiện NGUYÊN VĂN.** Ô bảng chuỗi thuần
     không phân tích đánh dấu, nên `escape()` ở đó là thoát thừa và tờ giấy in
     ra "Khoa học &amp;amp; Tiếng Anh". Lỗi này đã có thật, tìm ra bằng cách MỞ
     tệp PDF ra nhìn — trích xuất chữ suông không thấy.
  3. **Không có dữ liệu thì nói KHÔNG CÓ, không viết 0** — ranh giới 3 của
     `parent_report.py`. "Điểm thi thử trung bình: 0" đọc như con làm sai hết.
  4. **Buổi chưa điểm danh phải được NÓI RA**, không im lặng chia mẫu số nhỏ đi.
  5. **Chủ đề phải rơi đúng dải nhận xét.** Sai dải là gửi về nhà một lời khuyên
     dành cho trình độ khác hẳn.
"""
import io

import pytest
from pypdf import PdfReader

from teaching.bao_cao_pdf import dung_pdf

CO_SO = {
    'student': {'id': 1, 'name': 'Nguyễn Minh An'},
    'parent': {'name': 'Nguyễn Thị Hà'},
    'class': {'id': 1, 'name': 'Luyện HSA đợt 1/2027 — Ca tối', 'code': 'HSA-01',
              'teacher': 'Thầy Hà Thái Sơn'},
    'membership': {'joinedAt': '2026-08-10', 'leftAt': None, 'status': 'Đang học',
                   'teacherNote': 'Định lượng tiến bộ rõ.'},
    'period': {'from': '2026-08-10', 'to': '2026-09-07', 'weeks': 4},
    'attendance': {'sessionsTotal': 9, 'sessionsCounted': 8, 'sessionsUnmarked': 0,
                   'present': 6, 'late': 1, 'absent': 1, 'excused': 0, 'noRecord': 0,
                   'attendedPct': 88},
    'study': {'lessonsDone': 19, 'mockCount': 3, 'mockAvg': 82, 'mockBest': 91,
              'mockTrend': 'up'},
    'topics': {'weak': [], 'strong': [], 'measured': 0, 'total': 19, 'courses': []},
    'warnings': [],
}


def _chu(bc) -> str:
    """Dựng PDF rồi đọc lại chữ trong đó — kiểm thứ ĐÃ VẼ, không phải thứ định vẽ."""
    b = dung_pdf(bc)
    assert b[:5] == b'%PDF-', 'không phải tệp PDF'
    return ''.join((p.extract_text() or '') for p in PdfReader(io.BytesIO(b)).pages)


def _voi(**doi):
    """Bản sao CO_SO với vài khoá lồng bị thay."""
    import copy
    bc = copy.deepcopy(CO_SO)
    for khoa, gt in doi.items():
        if isinstance(gt, dict) and isinstance(bc.get(khoa), dict):
            bc[khoa].update(gt)
        else:
            bc[khoa] = gt
    return bc


# ── 1. Chữ Việt ────────────────────────────────────────────────────────────

def test_chu_viet_co_dau_ra_dung_chu_viet():
    """Không ký tự nào rơi vào ô glyph khuyết.

    ── BẢN ĐẦU CỦA PHÉP KIỂM NÀY LÀ PHÉP KIỂM GIẢ ───────────────────────────

    Nó liệt kê bốn chuỗi ('Nguyễn Minh An', 'Luyện HSA'…) và đòi chúng có mặt.
    Lùi font thường về Vera (thiếu 40/57 ký tự Việt) thì nó VẪN XANH — vì cả
    bốn chuỗi ấy còn xuất hiện MỘT LẦN NỮA ở font đậm, mà `_chu()` thì gộp cả
    tài liệu lại. Nó chứng minh "có một bản lành ở đâu đó", không chứng minh
    "không có bản hỏng nào".

    Thứ canh đúng là DẤU VẾT CỦA HỎNG: reportlab vẽ ký tự font không có thành
    ô khuyết, và `pypdf` rút ra là `\x00`. Một ô như thế ở bất kỳ đâu cũng là
    hỏng, bất kể font thường hay đậm.
    """
    t = _chu(CO_SO)

    assert '\x00' not in t and '\ufffd' not in t, (
        'có ký tự rơi vào ô glyph khuyết — font đang dùng không phủ tiếng Việt')

    # Một chuỗi chỉ xuất hiện ở font THƯỜNG, và một chuỗi chỉ ở font ĐẬM: hai
    # họ font được đăng ký riêng, nên hỏng một họ là chuyện xảy ra được.
    assert 'không xuất hiện ở đây' in t
    assert 'CHUYÊN CẦN' in t


# ── 2. Thoát thừa ─────────────────────────────────────────────────────────

def test_dau_va_va_ngoac_nhon_trong_ten_hien_NGUYEN_VAN():
    """Lỗi có thật, đã sửa 07/09/2026 — không được quay lại.

    Ô bảng nhận chuỗi thuần thì reportlab vẽ y nguyên, không phân tích đánh
    dấu; `escape()` ở đó biến "Khoa học & Tiếng Anh" thành "Khoa học &amp;
    Tiếng Anh" TRÊN GIẤY. Cách sửa là bọc ô thành `Paragraph` — khi ấy đánh
    dấu ĐƯỢC phân tích và `escape()` trở lại đúng vai.
    """
    bc = _voi(
        student={'name': 'Lê <An> & Bùi'},
        topics={'weak': [{'courseTitle': 'Khoa học & Tiếng Anh',
                          'topic': 'Ngữ pháp & từ vựng', 'mastery': 41}],
                'strong': [], 'measured': 1, 'total': 19,
                'courses': [{'title': 'Khoa học & Tiếng Anh', 'lessonsDone': 3,
                             'lessonsTotal': 26, 'pct': 12}]})
    t = _chu(bc)

    assert '&amp;' not in t, 'tờ giấy in ra "&amp;" — thoát thừa trong ô bảng'
    assert '&lt;' not in t and '&gt;' not in t
    assert 'Khoa học & Tiếng Anh' in t
    assert 'Ngữ pháp & từ vựng' in t


# ── 3. Không bịa số 0 ─────────────────────────────────────────────────────

def test_chua_thi_lan_nao_thi_KHONG_viet_0_diem():
    bc = _voi(study={'lessonsDone': 4, 'mockCount': 0, 'mockAvg': None,
                     'mockBest': None, 'mockTrend': None})
    t = _chu(bc)

    assert 'chưa thi lần nào' in t
    # "Điểm thi thử TB 0%" đọc như con làm sai hết, trong khi sự thật là con
    # chưa thi lần nào. Hai câu ấy khác nhau hoàn toàn với người đọc là bố mẹ.
    assert 'Điểm thi thử TB\n0%' not in t and 'Điểm thi thử TB 0%' not in t


# ── 4. Khoảng trống phải được nói ra ──────────────────────────────────────

def test_buoi_chua_diem_danh_duoc_noi_ra():
    t = _chu(_voi(attendance={'sessionsUnmarked': 3}))
    assert 'chưa điểm danh' in t and '3 buổi' in t


def test_khong_con_buoi_nao_chua_tick_thi_khong_ghi_cau_thua():
    t = _chu(_voi(attendance={'sessionsUnmarked': 0}))
    assert 'chưa điểm danh' not in t, 'ghi cảnh báo cho một khoảng trống không tồn tại'


# ── 5. Chủ đề rơi đúng dải ────────────────────────────────────────────────

@pytest.mark.parametrize('muc,dai', [
    (95, 'Nắm chắc'),
    (80, 'Khá vững'),
    (65, 'Tạm được'),
    (45, 'Cần chú ý'),
    (12, 'Cần học lại từ gốc'),
])
def test_chu_de_roi_dung_dai_nhan_xet(muc, dai):
    bc = _voi(topics={'weak': [{'courseTitle': 'Tư duy Định tính',
                                'topic': 'Đọc hiểu', 'mastery': muc}],
                      'strong': [], 'measured': 1, 'total': 19, 'courses': []})
    t = _chu(bc)
    assert dai in t, 'chủ đề %d%% không rơi vào dải %r' % (muc, dai)


def test_moc_bien_cua_dai_khong_bo_sot():
    """Đúng ngưỡng thì thuộc dải TRÊN, không rơi xuống dải dưới.

    Dải viết là `(85, 100)`, `(75, 84)` — hai đầu đều ĐÓNG. Ai đổi thành nửa
    mở mà quên đầu kia thì một chủ đề đúng 85% không thuộc dải nào, và
    `_dai_cua` lặng lẽ trả về dải cuối: "cần học lại từ gốc" cho một em nắm
    chắc. Đây là kiểu sai không ai phát hiện được từ mã.
    """
    for muc, dai in ((85, 'Nắm chắc'), (84, 'Khá vững'), (75, 'Khá vững'),
                     (74, 'Tạm được'), (40, 'Cần chú ý'), (39, 'Cần học lại từ gốc')):
        bc = _voi(topics={'weak': [{'courseTitle': 'X', 'topic': 'Y', 'mastery': muc}],
                          'strong': [], 'measured': 1, 'total': 1, 'courses': []})
        assert dai in _chu(bc), '%d%% phải thuộc dải %r' % (muc, dai)


# ── 6. Không vỡ với dữ liệu nghèo ─────────────────────────────────────────

def test_hoc_vien_moi_toanh_van_dung_duoc_to_giay():
    """Trung tâm hiện có 0 buổi và 0 lượt điểm danh — đây là trạng thái THẬT
    hôm nay, nên nó phải là trường hợp chạy được, không phải trường hợp lỗi."""
    bc = _voi(
        attendance={'sessionsTotal': 0, 'sessionsCounted': 0, 'sessionsUnmarked': 0,
                    'present': 0, 'late': 0, 'absent': 0, 'excused': 0,
                    'noRecord': 0, 'attendedPct': None},
        study={'lessonsDone': 0, 'mockCount': 0, 'mockAvg': None, 'mockBest': None,
               'mockTrend': None},
        membership={'teacherNote': None})
    t = _chu(bc)

    assert 'BÁO CÁO HỌC TẬP' in t
    assert 'Chưa có dữ liệu tiến độ' in t
    assert 'Chưa chủ đề nào đo được' in t
    assert 'chưa ghi nhận xét' in t


def test_payload_rong_hoac_thieu_khoa_khong_lam_no():
    """Không ném ngoại lệ khi payload thiếu khoá.

    Đường gửi hàng loạt dựng tờ giấy cho CẢ LỚP trong một vòng lặp. Một em có
    dữ liệu lạ mà làm hàm này ném thì cả lượt gửi dừng ở đó, và người bấm nút
    không biết đã tới em nào.
    """
    assert dung_pdf({})[:5] == b'%PDF-'


# ── 6. Thi thử tại trung tâm (nhập từ tờ PDF của hệ thống khảo thí) ────────

KY_THI = {
    'date': '2026-08-23', 'round': 'Online 2308', 'score': 105, 'max': 150,
    'sections': [{'phan': 1, 'ten': 'Định lượng và Xử lí số liệu', 'diem': 27, 'toiDa': 50},
                 {'phan': 2, 'ten': 'Định tính', 'diem': 38, 'toiDa': 50},
                 {'phan': 3, 'ten': 'Tiếng Anh', 'diem': 40, 'toiDa': 50}],
    'weakUnits': [{'phan': 1, 'ten': 'Nguyên hàm, tích phân và ứng dụng', 'pct': 0},
                  {'phan': 3, 'ten': 'Reading comprehension 1', 'pct': 20}],
    'unitsMeasured': 24,
    'previous': None,
}


def _mot_dong(bc) -> str:
    """Chữ trong PDF đã GỘP DÒNG.

    reportlab ngắt dòng theo bề ngang ô, nên một câu đúng vẫn nằm trên hai dòng
    ("tăng 13 điểm so với kỳ\\n19/07/2026"). Tìm nguyên câu trong chữ thô sẽ đỏ
    oan — và cách sửa sai là đi sửa tờ giấy cho vừa một dòng.
    """
    return ' '.join(_chu(bc).split())


def test_chua_nhap_ket_qua_thi_thi_KHONG_in_muc_ay():
    """Mục này chỉ có khi đã nhập được tờ kết quả.

    In "chưa có dữ liệu" cho một mục phụ huynh chưa từng nghe tới chỉ tạo thêm
    một câu hỏi không ai ở đó trả lời."""
    chu = _chu(CO_SO)
    assert 'THI THỬ TẠI TRUNG TÂM' not in chu
    assert 'III. TIẾN ĐỘ THEO HỢP PHẦN' in chu, 'không có mục ấy thì số mục KHÔNG được nhảy'
    assert 'IV. CHỦ ĐỀ ĐÃ ĐO ĐƯỢC' in chu and 'V. NHẬN XÉT CỦA GIẢNG VIÊN' in chu


def test_co_ket_qua_thi_thi_in_dung_diem_va_day_so_muc_xuong():
    chu = _chu(_voi(centerExam=KY_THI))
    assert 'III. THI THỬ TẠI TRUNG TÂM' in chu
    assert '105/150' in chu and 'Online 2308' in chu and '23/08/2026' in chu
    assert 'Định lượng và Xử lí số liệu 27/50' in chu, 'điểm từng phần in nguyên mẫu số'
    # Các mục sau bị đẩy xuống một bậc — không trùng số, không nhảy số.
    assert 'IV. TIẾN ĐỘ THEO HỢP PHẦN' in chu
    assert 'V. CHỦ ĐỀ ĐÃ ĐO ĐƯỢC' in chu and 'VI. NHẬN XÉT CỦA GIẢNG VIÊN' in chu


def test_lan_dau_thi_noi_ro_la_lan_dau_chu_khong_bia_tien_bo():
    chu = _chu(_voi(centerExam=KY_THI))
    assert 'chưa có kết quả kỳ trước để so' in chu
    assert 'tăng' not in chu.split('III. THI THỬ')[1].split('IV.')[0]


def test_co_lan_truoc_thi_noi_tang_hay_giam_bao_nhieu():
    tang = _mot_dong(_voi(centerExam={**KY_THI, 'previous': {
        'date': '2026-07-19', 'round': 'Online 1907', 'score': 92, 'delta': 13}}))
    assert 'tăng 13 điểm so với kỳ 19/07/2026' in tang and '92/150' in tang

    giam = _mot_dong(_voi(centerExam={**KY_THI, 'previous': {
        'date': '2026-07-19', 'round': 'Online 1907', 'score': 118, 'delta': -13}}))
    assert 'giảm 13 điểm' in giam, 'dấu trừ phải đọc thành chữ, không in "-13"'


def test_in_don_vi_kien_thuc_thap_nhat_ke_ca_0_phan_tram():
    chu = _chu(_voi(centerExam=KY_THI))
    assert 'Nguyên hàm, tích phân và ứng dụng (0%)' in chu, '0% là một con số, không phải chỗ trống'
    assert 'Reading comprehension 1 (20%)' in chu


def test_noi_ro_hai_thang_diem_khac_nhau():
    """Mục I có "Điểm thi thử TB 82%" (luyện tập), mục này có "105/150" (thi thật).

    Hai con số cạnh nhau trong một tờ giấy mà không chú thích thì đọc như mâu
    thuẫn, và phụ huynh sẽ hỏi giảng viên câu mà tờ giấy đáng lẽ phải tự trả lời.
    """
    chu = _mot_dong(_voi(centerExam=KY_THI))
    assert 'thang 150' in chu and 'điểm luyện tập trong ứng dụng' in chu
