"""Danh mục của hộp Yêu cầu (E3, §65) — MỘT nguồn cho loại, trạng thái, nguồn, kiểu sự kiện
và bảng chuyển trạng thái hợp lệ. `tests_yeu_cau.py::test_danh_muc_khop_check` đối chiếu từng
bộ với CHECK của §65 trong CSDL: thêm một loại ở đây mà quên §65 (hay ngược lại) là đỏ.
"""

#: Nhóm quyết định ai xử lý và máy trạng thái đi nhánh nào.
HO_TRO = 'ho_tro'        # học vụ xử lý, chuyển tiếp được cho GV/TG
HOI_DAP = 'hoi_dap'      # học viên hỏi → GV/TG của lớp
BAO_CAO = 'bao_cao'      # TG báo lên GV hoặc học vụ
BAO_LOI = 'bao_loi'      # báo lỗi bản ghi buổi học
THAY_DOI = 'thay_doi'    # xin–duyệt, chỉ học vụ / quản trị duyệt

#: code → nhãn, nhóm, cần lớp, cần buổi, việc khi duyệt ('tu_dong' | 'tay' | None).
LOAI = {
    'ht_hoc_tap':      {'nhan': 'Hỗ trợ học tập', 'nhom': HO_TRO},
    'ht_lich_hoc':     {'nhan': 'Hỗ trợ lịch học', 'nhom': HO_TRO},
    'ht_ky_thuat':     {'nhan': 'Hỗ trợ kỹ thuật', 'nhom': HO_TRO},
    'ht_tai_khoan':    {'nhan': 'Hỗ trợ tài khoản', 'nhom': HO_TRO},
    'hoi_dap':         {'nhan': 'Hỏi giảng viên', 'nhom': HOI_DAP, 'can_lop': True},
    'bao_cao_len':     {'nhan': 'Báo lên', 'nhom': BAO_CAO, 'can_lop': True},
    'bao_loi_ban_ghi': {'nhan': 'Báo lỗi bản ghi buổi học', 'nhom': BAO_LOI, 'can_lop': True,
                        'can_buoi': True},
    # `chon_lop_toi`: màn duyệt phải hiện ô chọn lớp. Cờ này ở ĐÂY chứ không phải trong
    # `ChiTietYeuCau.tsx` — bản đầu (26/09) so tay `yc.loai === 'tt_chuyen_lop' || …` ở
    # phía màn, tức danh mục loại có bản thứ hai (RULES §7) và loại thứ ba thêm vào sẽ
    # lặng lẽ mất ô chọn lớp. Nay máy chủ trả `chonLopToi` trong mỗi yêu cầu.
    'tt_chuyen_lop':   {'nhan': 'Xin chuyển lớp', 'nhom': THAY_DOI, 'can_lop': True,
                        'viec': 'tu_dong', 'chon_lop_toi': True},
    'tt_chuyen_mon':   {'nhan': 'Xin chuyển môn', 'nhom': THAY_DOI, 'can_lop': True,
                        'viec': 'tu_dong', 'chon_lop_toi': True},
    'tt_chuyen_lich':  {'nhan': 'Xin chuyển lịch', 'nhom': THAY_DOI, 'viec': 'tay'},
    'tt_bao_luu':      {'nhan': 'Xin bảo lưu', 'nhom': THAY_DOI, 'can_lop': True, 'viec': 'tu_dong'},
    # KHÔNG `can_buoi`: lúc em (hoặc giảng viên) xin học bù thì buổi bù thường CHƯA tồn
    # tại — học vụ tạo nó trên màn Buổi học rồi mới duyệt. Buổi là thứ học vụ CHỌN lúc
    # duyệt (`chon_buoi_bu`), như `tt_chuyen_lop` chọn lớp tới. Đòi buổi ngay lúc gửi là
    # chặn đúng người cần gửi nhất.
    'tt_hoc_bu':       {'nhan': 'Xin học bù', 'nhom': THAY_DOI, 'viec': 'tu_dong',
                        'chon_buoi_bu': True},
    'tt_hoc_lai':      {'nhan': 'Xin học lại', 'nhom': THAY_DOI, 'can_lop': True, 'viec': 'tu_dong'},
    'tt_nghi_hoc':     {'nhan': 'Xin nghỉ học', 'nhom': THAY_DOI, 'can_lop': True,
                    'viec': 'tu_dong'},
    'tt_huy_khoa':     {'nhan': 'Xin huỷ khoá', 'nhom': THAY_DOI, 'can_lop': True, 'viec': 'tu_dong'},
    # §73 (E5, 27/09/2026) — hàng chờ xếp lớp của học viên TỰ đăng ký. Nằm trong nhóm
    # THAY_DOI vì nó cần đúng bộ luật của nhóm ấy: chỉ học vụ / quản trị duyệt và từ
    # chối, duyệt = thực thi trong MỘT giao dịch, duyệt hai lần chỉ xếp lớp một lần.
    # KHÔNG `can_lop`: lúc gửi em chưa có lớp nào — lớp là thứ học vụ CHỌN khi duyệt
    # (`chon_lop_toi`), như `tt_chuyen_lop` chọn lớp tới.
    'tk_dang_ky':      {'nhan': 'Đăng ký mới — chờ xếp lớp', 'nhom': THAY_DOI,
                        'viec': 'tu_dong', 'chon_lop_toi': True},
}
#: Loại CHỈ hệ thống sinh ra, không ai gửi tay được (kể cả học vụ). `tk_dang_ky` chỉ ra
#: đời ở cửa xác thực email (`accounts/tu_dang_ky.py`): mở cho người gửi tay thì hàng chờ
#: xếp lớp thành một đường ai cũng nhét việc vào được, và một em có thể tự nhân bản mình
#: thành mười lượt "chờ xếp lớp".
CHI_HE_THONG = ('tk_dang_ky',)
#: Loại CHỈ học vụ / quản trị thấy — giảng viên và trợ giảng không bao giờ. Cùng ranh giới
#: với báo cáo phụ huynh: lượt đăng ký mang số điện thoại và email của em.
CHI_HOC_VU = ('ht_tai_khoan', 'tk_dang_ky')

TRANG_THAI = ('moi', 'dang_xu_ly', 'da_duyet', 'da_xong', 'tu_choi', 'da_huy')
NHAN_TRANG_THAI = {
    'moi': 'Mới', 'dang_xu_ly': 'Đang xử lý', 'da_duyet': 'Đã duyệt', 'da_xong': 'Đã xong',
    'tu_choi': 'Từ chối', 'da_huy': 'Đã rút',
}
#: Trạng thái còn MỞ (đếm trần 5 yêu cầu / link phụ huynh, "Việc hôm nay").
MO = ('moi', 'dang_xu_ly', 'da_duyet')

NGUON = ('hoc_vien', 'phu_huynh', 'tro_giang', 'giang_vien', 'hoc_vu')

KIEU_SU_KIEN = ('tao', 'tra_loi', 'ghi_chu', 'trang_thai', 'giao', 'chuyen_tiep', 'duyet',
                'tu_choi', 'thuc_thi', 'loi', 'phan_loai')

#: Loại người làm, suy từ vai trong `dich_vu.NguoiLam`.
NGUOI_TAO = 'nguoi_tao'   # chính người đã tạo (học viên / phụ huynh qua link / nhân sự)
NHAN_SU = 'nhan_su'       # nhân sự thấy yêu cầu (GV/TG trong phạm vi, học vụ, quản trị)
DUYET = 'duyet'           # học vụ / quản trị — `IsAdminOrAcademic`

#: BẢNG CHUYỂN HỢP LỆ — (từ, tới) → (ai được làm, nhóm loại được đi đường này).
#: `None` ở nhóm = mọi nhóm; 'khac' = mọi nhóm TRỪ thay đổi.
#: `→ da_duyet` chỉ đi qua `dich_vu.duyet()` (thực thi trong cùng giao dịch), không qua
#: `chuyen_trang_thai()` trần — xem `CHI_QUA_DUYET`.
CHUYEN = {
    ('moi', 'dang_xu_ly'): (NHAN_SU, None),
    ('moi', 'da_xong'): (NHAN_SU, 'khac'),
    ('dang_xu_ly', 'da_xong'): (NHAN_SU, 'khac'),
    ('moi', 'tu_choi'): (NHAN_SU, 'khac'),
    ('dang_xu_ly', 'tu_choi'): (NHAN_SU, 'khac'),
    # Loại thay đổi: chỉ người duyệt mới từ chối / duyệt.
    ('moi', 'da_duyet'): (DUYET, THAY_DOI),
    ('dang_xu_ly', 'da_duyet'): (DUYET, THAY_DOI),
    ('da_duyet', 'da_xong'): (NHAN_SU, THAY_DOI),
    # Người tạo rút khi chưa ai nhận.
    ('moi', 'da_huy'): (NGUOI_TAO, None),
    # Nhân sự mở lại. Loại thay đổi ĐÃ duyệt thì không mở lại (việc đã làm, duyệt lại là làm hai lần).
    ('da_xong', 'dang_xu_ly'): (NHAN_SU, 'khac'),
    ('tu_choi', 'dang_xu_ly'): (NHAN_SU, None),
    ('da_huy', 'dang_xu_ly'): (NHAN_SU, None),
}
#: Từ chối loại thay đổi = việc của người duyệt (thêm vào bảng, không đè dòng 'khac' ở trên).
#: Mở lại một lượt xin đã bị từ chối / đã rút cũng thế (soát 26/09/2026): bản đầu để mọi nhân
#: sự mở lại — trợ giảng mở lại được một lượt xin chuyển lớp học vụ vừa từ chối.
CHUYEN_THAY_DOI = {
    ('moi', 'tu_choi'): DUYET,
    ('dang_xu_ly', 'tu_choi'): DUYET,
    ('tu_choi', 'dang_xu_ly'): DUYET,
    ('da_huy', 'dang_xu_ly'): DUYET,
}
CHI_QUA_DUYET = 'da_duyet'

#: PHÂN LOẠI (bảng TopHSA dòng 11): học vụ đổi loại một yêu cầu CHƯA ĐÓNG trong nhóm này — em
#: chọn "học tập" mà thật ra là lỗi kỹ thuật. Không gồm loại xin–duyệt (đổi sang đó là biến một
#: câu hỏi thành một lượt thực thi) và không gồm "báo lên" (việc nội bộ của nhân sự).
PHAN_LOAI_DUOC = ('ht_hoc_tap', 'ht_lich_hoc', 'ht_ky_thuat', 'ht_tai_khoan', 'hoi_dap',
                  'bao_loi_ban_ghi')


def nhom(loai):
    return LOAI[loai]['nhom']


def la_thay_doi(loai):
    return nhom(loai) == THAY_DOI


def ai_duoc_chuyen(loai, tu, den):
    """Ai được chuyển yêu cầu loại `loai` từ `tu` sang `den`? `None` = không ai (không hợp lệ)."""
    if la_thay_doi(loai) and (tu, den) in CHUYEN_THAY_DOI:
        return CHUYEN_THAY_DOI[(tu, den)]
    luat = CHUYEN.get((tu, den))
    if not luat:
        return None
    ai, cho_nhom = luat
    if cho_nhom == 'khac' and la_thay_doi(loai):
        return None
    if cho_nhom not in (None, 'khac') and cho_nhom != nhom(loai):
        return None
    return ai


#: Loại mỗi nguồn được TẠO. Học vụ tạo mọi loại (thay mặt em / phụ huynh gọi điện tới).
_TAY = tuple(k for k in LOAI if k not in CHI_HE_THONG)
TAO_DUOC = {
    'hoc_vien': tuple(k for k in _TAY if k != 'bao_cao_len'),
    'phu_huynh': tuple(k for k in _TAY if k not in ('ht_tai_khoan', 'bao_cao_len', 'bao_loi_ban_ghi')),
    'tro_giang': ('bao_cao_len', 'bao_loi_ban_ghi') + tuple(k for k in _TAY if la_thay_doi(k)),
    'giang_vien': ('bao_cao_len', 'bao_loi_ban_ghi') + tuple(k for k in _TAY if la_thay_doi(k)),
    'hoc_vu': _TAY,
}

#: Khoá trong `du_lieu` là liên lạc của phụ huynh — ẩn với trợ giảng (cùng ranh giới với báo
#: cáo phụ huynh, `common/permissions.py`).
LIEN_LAC_PH = ('sdt', 'sdt_phu_huynh', 'email_phu_huynh')

#: Khoá chữ nhận trong `du_lieu` → (trần ký tự, nhãn người dùng đọc). Nhãn đi vào câu lỗi —
#: bản đầu in thẳng mã khoá ("Sdt tối đa 20 ký tự."), trái RULES §10.
CHU_DU_LIEU = {
    'sdt': (20, 'số điện thoại'),
    # §73 · những gì em khai trên phiếu đăng ký. Hiện nguyên trên thẻ chi tiết để học vụ
    # gọi lại và xếp lớp mà không phải mở thêm màn hồ sơ.
    'nguon': (40, 'nguồn biết tới trung tâm'),
    'truong': (200, 'trường đang học'),
    'lop_o_truong': (40, 'lớp ở trường'),
    'ngay_mong_muon': (100, 'ngày mong muốn'),
    'lop_mong_muon': (200, 'lớp mong muốn'),
}
#: Khoá cờ (đúng / sai) trong `du_lieu`. `khong_phan_hoi`: trợ giảng báo em không phản hồi
#: (bảng TopHSA dòng 20 "ghi nhận HS không phản hồi").
CO_DU_LIEU = ('khong_phan_hoi',)

#: HẠN XỬ LÝ (số giờ kể từ lúc gửi) theo NHÓM — quá ngần ấy mà yêu cầu chưa đóng thì hộp
#: Yêu cầu gắn cờ "Quá hạn" và đẩy nó lên đầu danh sách.
#:
#: Mấy con số này là GIẢ ĐỊNH CỦA TÔI, không phải cam kết TopHSA đưa ra — cùng loại với bốn
#: ngưỡng ở `chuong_trinh/tu_vung.py` và `teaching/viec_hom_nay.py` (dòng 5 của
#: `docs/NGHIEM_THU_TOPHSA.md` kê cả bốn). Để lộ ở ĐÚNG MỘT chỗ để đổi là sửa một dòng, thay
#: vì rải số giờ vào câu SQL rồi quên mất chúng nằm đâu.
#:
#: Vì sao lệch nhau: hỏi bài và hỗ trợ là thứ trả lời được ngay trong ngày làm việc; báo lên
#: phải qua tay người thứ hai; còn xin–duyệt (chuyển lớp, bảo lưu, huỷ khoá) là một QUYẾT
#: ĐỊNH có hậu quả lên sổ điểm danh và học phí, hối nó bằng cờ đỏ sau một ngày là ép người
#: duyệt bấm cho xong cờ.
HAN_GIO = {
    HOI_DAP: 24,
    HO_TRO: 24,
    BAO_LOI: 24,
    BAO_CAO: 48,
    THAY_DOI: 72,
}


def han_gio(ma_loai):
    """Số giờ được phép xử lý một yêu cầu loại `ma_loai`."""
    return HAN_GIO[nhom(ma_loai)]


#: Trần độ dài.
TRAN_TIEU_DE = 200
TRAN_NOI_DUNG = 4000
#: Phụ huynh: tối đa ngần ấy yêu cầu còn mở trên MỘT link.
TRAN_MO_PHU_HUYNH = 5
