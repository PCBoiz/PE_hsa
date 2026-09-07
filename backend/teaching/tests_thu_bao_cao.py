"""Lá thư báo cáo gửi phụ huynh: tóm tắt + PDF đính kèm + đường dẫn.

KHÔNG cần CSDL và KHÔNG gửi gì: `soan_thu` chỉ dựng nội dung.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. **Đường dẫn phải có trong phần CHỮ THUẦN**, không chỉ trong HTML. Nhiều
     ứng dụng thư và mọi bộ đọc màn hình đọc phần chữ thuần; đặt link chỉ ở
     nút HTML là để một phần người nhận không tới được tờ giấy.
  2. **Tên con trong tiêu đề và trong tên tệp.** Phụ huynh có hai đứa học ở
     đây thì hai lá thư phải phân biệt được ngay ở danh sách hộp thư, và tệp
     thứ hai không được đè lên tệp thứ nhất khi tải về.
  3. **HTML phải thoát dữ liệu người dùng.** Tên có `&` hoặc `<` mà nối thẳng
     vào chuỗi HTML là làm vỡ lá thư — và mở đúng lối vào của một lỗ chèn mã.
  4. **Không gọi kết quả MỘT lượt là "trung bình".** Đo trên CSDL thật: em id 9
     thi đúng một lần được 0/9, và "Điểm thi thử trung bình: 0%" gửi về nhà là
     một bản án cho một lượt bấm.
  5. **"0/0 buổi" không được xuất hiện.** Nó đọc như con không đi buổi nào,
     trong khi sự thật là lớp chưa có buổi nào được điểm danh.
"""
import copy

from teaching.thu_bao_cao import soan_thu

CO_SO = {
    'student': {'id': 1, 'name': 'Nguyễn Minh An'},
    'parent': {'name': 'Nguyễn Thị Hà'},
    'class': {'id': 1, 'name': 'Luyện HSA đợt 1/2027 — Ca tối', 'teacher': 'Thầy Sơn'},
    'membership': {'joinedAt': '2026-08-10', 'status': 'Đang học', 'teacherNote': None},
    'period': {'from': '2026-08-10', 'to': '2026-09-07', 'weeks': 4},
    'attendance': {'sessionsTotal': 9, 'sessionsCounted': 8, 'sessionsUnmarked': 1,
                   'present': 6, 'late': 1, 'absent': 1, 'excused': 0, 'noRecord': 0,
                   'attendedPct': 88},
    'study': {'lessonsDone': 19, 'mockCount': 3, 'mockAvg': 82, 'mockBest': 91,
              'mockTrend': 'up'},
    'topics': {'weak': [{'courseTitle': 'Tư duy Định tính', 'topic': 'Đọc hiểu',
                         'mastery': 34}],
               'strong': [], 'measured': 1, 'total': 19, 'courses': []},
    'warnings': [],
}
LINK = 'https://tophsa.vn/bc/' + 'M' * 43


def _voi(**doi):
    bc = copy.deepcopy(CO_SO)
    for k, v in doi.items():
        if isinstance(v, dict) and isinstance(bc.get(k), dict):
            bc[k].update(v)
        else:
            bc[k] = v
    return bc


# ── 1. Đường dẫn ở CẢ HAI phần ────────────────────────────────────────────

def test_duong_dan_co_trong_ca_chu_thuan_lan_html():
    _, chu, html, _ = soan_thu(CO_SO, LINK)
    assert LINK in chu, 'phần chữ thuần thiếu đường dẫn'
    assert LINK in html


def test_khong_co_duong_dan_thi_thu_van_dung_duoc():
    """Đường gửi tay chưa cấp chìa — thư vẫn phải soạn được, chỉ thiếu nút."""
    tieu_de, chu, html, dinh_kem = soan_thu(CO_SO, None)
    assert tieu_de and chu and html and dinh_kem
    assert 'Xem bản đầy đủ' not in html, 'dựng nút trỏ vào hư không'


# ── 2. Tên con ────────────────────────────────────────────────────────────

def test_ten_con_trong_tieu_de_va_ten_tep():
    tieu_de, _, _, dinh_kem = soan_thu(CO_SO, LINK)
    assert 'Nguyễn Minh An' in tieu_de

    ten_tep, kieu, du_lieu = dinh_kem[0]
    assert kieu == 'application/pdf' and du_lieu[:5] == b'%PDF-'
    # Bỏ dấu: một số ứng dụng thư trên điện thoại làm hỏng tên tệp có dấu.
    assert ten_tep == 'bao-cao-nguyen-minh-an-2026-09-07.pdf', ten_tep


def test_hai_ky_khac_nhau_ra_hai_ten_tep_khac_nhau():
    """Trùng tên thì tệp mới đè tệp cũ khi phụ huynh tải về."""
    a = soan_thu(CO_SO, LINK)[3][0][0]
    b = soan_thu(_voi(period={'to': '2026-10-05'}), LINK)[3][0][0]
    assert a != b


# ── 3. Thoát dữ liệu người dùng trong HTML ────────────────────────────────

def test_html_thoat_ky_tu_dac_biet_trong_ten():
    _, _, html, _ = soan_thu(_voi(student={'name': 'Lê <b>An</b> & Bùi'}), LINK)
    # Tên nối thẳng vào chuỗi HTML thì `<b>` thành thẻ thật — lá thư vỡ, và
    # đó đúng là lối vào của một lỗ chèn mã ở nơi khác.
    assert '<b>An</b>' not in html
    assert '&lt;b&gt;An&lt;/b&gt; &amp; Bùi' in html


# ── 4. Một lượt thi không phải "trung bình" ───────────────────────────────

def test_mot_luot_thi_thi_noi_ro_la_mot_luot():
    _, chu, html, _ = soan_thu(
        _voi(study={'mockCount': 1, 'mockAvg': 0, 'mockBest': 0, 'mockTrend': None}), LINK)
    assert 'mới thi 1 lượt' in chu, chu
    assert 'mới thi 1 lượt' in html
    # Và KHÔNG được gọi nó là trung bình.
    assert 'trung bình' not in chu.lower()


def test_chua_thi_lan_nao_thi_khong_viet_0():
    _, chu, _, _ = soan_thu(
        _voi(study={'mockCount': 0, 'mockAvg': None, 'mockBest': None}), LINK)
    assert 'chưa thi lần nào' in chu
    assert 'Điểm thi thử: 0%' not in chu


def test_nhieu_luot_thi_thi_neu_so_luot():
    _, chu, _, _ = soan_thu(CO_SO, LINK)
    assert '82% (3 lượt)' in chu, chu


# ── 5. Chưa điểm danh buổi nào ────────────────────────────────────────────

def test_lop_chua_diem_danh_buoi_nao_thi_KHONG_viet_0_tren_0():
    _, chu, html, _ = soan_thu(
        _voi(attendance={'sessionsTotal': 0, 'sessionsCounted': 0, 'sessionsUnmarked': 0,
                         'present': 0, 'late': 0, 'absent': 0, 'excused': 0,
                         'noRecord': 0, 'attendedPct': None}), LINK)
    # `'0/0'` KHÔNG dùng được làm mẫu tìm: nó khớp bên trong ngày "10/08/2026".
    # Bản đầu của phép kiểm này đỏ vì đúng lý do ấy — thước báo oan chứ mã
    # không sai. Bám vào cả cụm "0/0 buổi" thì chỉ khớp đúng câu đang cấm.
    assert '0/0 buổi' not in chu, '"0/0 buổi" đọc như con không đi buổi nào'
    assert '0/0 buổi' not in html
    assert 'chưa có buổi nào được điểm danh' in chu


def test_buoi_chua_tick_duoc_noi_ra_trong_thu():
    _, chu, html, _ = soan_thu(CO_SO, LINK)
    assert 'chưa điểm danh' in chu and 'chưa điểm danh' in html


# ── Thư luôn có hai phần ──────────────────────────────────────────────────

def test_chu_thuan_khong_chua_the_html():
    """Phần chữ thuần phải là CHỮ THUẦN. Lọt thẻ vào đó thì người đọc bằng
    ứng dụng chỉ hiện chữ thuần nhìn thấy mã nguồn."""
    _, chu, _, _ = soan_thu(CO_SO, LINK)
    for the in ('<p', '<div', '<table', '<a '):
        assert the not in chu, 'phần chữ thuần lọt thẻ %r' % the
