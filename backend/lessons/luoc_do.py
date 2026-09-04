"""LƯỢC ĐỒ NỘI DUNG BÀI HỌC — một bảng, hai bên dùng.

── VÌ SAO CÓ TỆP NÀY (anh Sơn chốt "A · một lược đồ, hai bên dùng") ─────────

Cùng một ràng buộc đang được viết ở HAI NƠI, bằng HAI NGÔN NGỮ:

    backend/lessons/content.py          `not 0 <= xp <= 500`
    admin/NoiDungBai.tsx                `min={0} max={500}`

    content.py                          `idx < 1`
    NoiDungBai.tsx                      `min={1}`

    content.py                          `not 5 <= ts <= 3600`
    NoiDungBai.tsx                      `min={5} max={3600}`

Hôm nay ba cặp ấy khớp nhau. Không có gì giữ cho chúng khớp: đổi trần XP ở
Python là biểu mẫu vẫn cho gõ 500, người soạn gõ xong bấm Lưu và nhận một lỗi
máy chủ cho một con số màn hình vừa bảo là hợp lệ.

VÀ CHÚNG ĐÃ LỆCH SẴN Ở HAI CHỖ — hai ràng buộc chỉ có ở máy chủ, biểu mẫu không
nói gì:

    · `answer` của câu trắc nghiệm phải nằm trong `options`
    · câu phòng luyện bắt buộc có `id`, và `id` không được trùng

Người soạn dựng xong cả bài, bấm Lưu, rồi mới biết. Với một bài 8 câu drill thì
đó là một vòng đi–về dài, và thông báo lỗi nói "câu thứ mấy" chứ không trỏ vào ô.

── VÌ SAO LƯỢC ĐỒ ĐẶT Ở PYTHON, KHÔNG Ở TYPESCRIPT ─────────────────────────

Máy chủ là bên CƯỠNG CHẾ. Một ràng buộc chỉ có ở trình duyệt là một lời gợi ý;
một ràng buộc chỉ có ở máy chủ vẫn là một hàng rào. Nên bản gốc phải nằm ở bên
cưỡng chế được, và bên kia ĐỌC nó.

Bảng này đi kèm phản hồi của `GET /api/admin/lessons/<id>/content` — endpoint mà
biểu mẫu soạn bài VỐN ĐÃ gọi. Không thêm cửa mới, không thêm lượt tải, không
thêm một chỗ hỏng được. Biểu mẫu vẫn có giá trị dự phòng viết cứng: lược đồ
không tới nơi thì ô nhập vẫn dùng được, chỉ mất phần gợi ý.

Đây KHÔNG phải một bộ sinh biểu mẫu như `semantics.json` của H5P. Sinh cả biểu
mẫu từ lược đồ nghe gọn hơn, nhưng nó đổi 699 dòng giao diện đang chạy lấy một
bộ dịch tổng quát mà mọi ô đặc thù (JSON đồ thị, thẻ lý thuyết, đáp án nhiều
dạng) đều phải trổ một cửa ngoại lệ. Thứ ĐANG hỏng là các CON SỐ trôi khỏi nhau
và hai luật thiếu bên client — đúng phần ấy được gộp, không hơn.
"""

#: Ràng buộc SỐ. Khoá là đường dẫn trong nội dung bài, dùng chung cho cả hai bên.
#:
#: `None` ở `max` nghĩa là không có trần — viết ra thay vì bỏ trống để người đọc
#: biết là đã cân nhắc, không phải quên.
SO = {
    'index': {'min': 1, 'max': None,
              'nhan': 'Số thứ tự (index)',
              'vi_sao': 'thứ tự bài trong khoá, đếm từ 1'},
    'xp_reward': {'min': 0, 'max': 500,
                  'nhan': 'XP thưởng',
                  'vi_sao': 'mỗi bài thường 50; trần 500 để một bài không bằng '
                            'cả một khoá'},
    'drill.time_seconds': {'min': 5, 'max': 3600,
                           'nhan': 'Thời gian phòng luyện (giây)',
                           'vi_sao': 'đồng hồ đếm ngược; dưới 5 giây thì không '
                                     'ai kịp đọc đề'},
}

#: Luật KHÔNG phải khoảng số — bên nào cũng phải kiểm, và mỗi luật một mã để
#: hai bên gọi nó bằng cùng một tên.
LUAT = {
    'dap_an_trong_lua_chon': {
        'nhan': 'Đáp án phải nằm trong danh sách lựa chọn',
        'ap_dung': 'câu trắc nghiệm (có "options")',
    },
    'ma_cau_drill_bat_buoc': {
        'nhan': 'Câu phòng luyện phải có mã, và mã không được trùng',
        'ap_dung': 'mọi câu trong "drill.questions"',
        'vi_sao': 'thiếu mã thì câu ấy KHÔNG CHẤM ĐƯỢC — máy chủ ghi nhận câu '
                  'trả lời theo mã',
    },
}


def cho_client():
    """Bản rút gọn gửi cho biểu mẫu soạn bài.

    Gửi cả `vi_sao`: người soạn đọc được LÝ DO của một con số thì họ không đi
    tìm cách lách nó. Đây là chỗ rẻ nhất để nói điều đó — ngay cạnh ô nhập.
    """
    return {'so': SO, 'luat': LUAT}
