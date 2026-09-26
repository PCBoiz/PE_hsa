"""SỔ NHÃN LOẠI CHUÔNG (§61, bảng TopHSA dòng 27 — 26/09/2026).

`notifications.type` là mã kỹ thuật: `assignment_new`, `lich_doi`, `ban_ghi_nhac`. Trang
"Thông báo" lọc theo loại, và ô lọc phải nói "Bài tập mới" chứ không phải `assignment_new`.

Sổ nằm ở MÁY CHỦ chứ không ở màn hình, theo RULES §7: màn hình không gõ lại danh mục. Ba
chỗ đang cần cùng một câu chữ — ô lọc của trang Thông báo, panel chuông, và sau này là
cài đặt "loại nào gửi email" — nên chép tay ba lần là ba lần lệch nhau.

`notifications/tests_loai.py` quét mọi lời gọi `gui(...)` trong backend bằng AST và đòi
mỗi mã tìm thấy có một dòng ở đây. Thêm loại chuông mới mà quên nhãn thì phép kiểm đỏ
ngay, chứ không phải chờ tới lúc một em nhìn thấy `submission_new` trên màn.
"""

#: mã `notifications.type` → câu tiếng Việt người dùng đọc.
NHAN = {
    'assignment_new': 'Bài tập mới',
    'assignment_graded': 'Bài đã chấm',
    'submission_new': 'Bài em nộp',
    'lich_doi': 'Đổi lịch học',
    'thong_bao': 'Thông báo chung',
    'yeu_cau': 'Yêu cầu hỗ trợ',
    'ban_ghi_nhac': 'Nhắc xem bản ghi',
    'ban_ghi_loi': 'Báo hỏng bản ghi',
    'hoc_bu': 'Buổi học bù',
    'post_comment': 'Bình luận trong diễn đàn',
}

#: Mã có nhãn nhưng KHÔNG do `gui()` trong backend sinh ra, nên bộ quét không thấy.
#: Mỗi dòng phải nói ai sinh ra nó — một ngoại lệ không có lý do là một nhãn rác.
GUI_NOI_KHAC = {
    'thu_nghiem': 'phép kiểm và lệnh thử tay gửi; không bao giờ tới người thật',
    'thong_bao': 'thông báo trung tâm ghi THẲNG vào `notifications` bằng một câu INSERT '
                 '(`notifications/thong_bao.py::gui`) để một lượt gửi cả khối là một câu '
                 'lệnh, không phải mười nghìn lời gọi `notify`. Bộ quét đọc lời gọi hàm '
                 'nên không thấy cửa này — `tests_loai.py` ghim riêng `thong_bao.LOAI`.',
}
NHAN.setdefault('thu_nghiem', 'Thử nghiệm')

#: Câu cho mã không có trong sổ: dữ liệu cũ, hoặc một nhánh chưa gộp. KHÔNG để trống —
#: một ô lọc không có chữ trông như màn hình hỏng.
KHAC = 'Khác'


def nhan(ma) -> str:
    """Câu tiếng Việt của một mã loại. Mã lạ → "Khác", không bao giờ ném."""
    return NHAN.get(ma) or KHAC
