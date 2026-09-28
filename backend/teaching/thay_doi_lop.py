"""§66 · THAY ĐỔI LỊCH GẦN ĐÂY của một em — để in lên tờ báo cáo phụ huynh.

Bảng phân rã dòng 24 đòi *"Nhận thông báo khi có thay đổi lịch"*. Anh Sơn chốt 27/09 là
KHÔNG gửi tin cho phụ huynh — tin nhắn ra khỏi hệ thống là không cuộn lại được, và trung tâm
chưa muốn mở kênh đẩy tới phụ huynh. Thay vào đó tờ báo cáo (vốn đã "sống", xem
`parent_link.py`) tự nêu ra phần đã đổi, và phụ huynh đọc khi họ mở.

── CHỈ NÊU THỨ ĐỌC THẲNG ĐƯỢC TỪ DỮ LIỆU ────────────────────────────────────

Ba thứ suy ra được và không thể sai:

  • **buổi bị huỷ** — `status = 'cancelled'`;
  • **buổi học bù** — `makeup_for IS NOT NULL`;
  • **buổi mới thêm** — `created_at` sau ngày cấp chìa.

Thứ KHÔNG suy ra được: *"buổi thứ Tư dời từ 19h sang 20h"*. `class_sessions` không có sổ ghi
thay đổi, và `updated_at` nhúc nhích cả khi giảng viên chỉ dán link Zoom hay ghi sổ đầu bài —
in "lịch có thay đổi" dựa vào nó là nói với phụ huynh một điều mình không biết, trên đúng tờ
giấy mà trung tâm dùng để chứng minh mình minh bạch. Muốn có "đổi giờ" thì phải thêm một sổ
ghi thay đổi thật; đó là một mục §NN riêng, không phải thứ nhét vào đây.

── HAI HÀNG RÀO ─────────────────────────────────────────────────────────────

① **`thuoc_buoi`** — buổi bù chỉ thuộc về mấy em có tên trong đó (§62e). Thiếu nó là tờ của
  em này nêu buổi bù riêng của bạn khác, qua một đường KHÔNG CÓ VAI NÀO đứng sau.

② **Mốc là NGÀY CẤP CHÌA.** Không có mốc thì mục này liệt kê mọi buổi của lớp, tức thành một
  bản sao của thời khoá biểu và thôi mang nghĩa "có gì đổi". Buổi đã có từ trước lúc cấp chìa
  nằm trong tờ gốc rồi.
"""
from common.db import q
from teaching.nguoi_buoi import thuoc_buoi

#: Trần số dòng. Tờ gửi phụ huynh, không phải sổ vận hành: một lớp vừa sinh lại lịch cả kỳ sẽ
#: có hàng chục buổi "mới thêm", và ba mươi dòng như thế thì che mất một buổi bị huỷ.
TRAN = 12

#: Mã trạng thái → chữ phụ huynh đọc. Nhãn dựng ở MÁY CHỦ (RULES §7, §10): tờ này còn có bản
#: PDF và bản thư, ba nơi tự dịch mã là ba bản dịch sẽ lệch nhau.
NHAN = {
    'huy': 'Buổi đã huỷ',
    'bu': 'Buổi học bù',
    'them': 'Buổi mới xếp thêm',
}

_SQL = '''
    SELECT s.id, s.starts_at, s.topic, s.status, s.makeup_for
      FROM class_sessions s
     WHERE s.class_id = %s
       AND ''' + thuoc_buoi('s.id', '%s') + '''
       AND ((s.status = 'cancelled' AND s.starts_at >= %s) OR s.created_at > %s)
     ORDER BY s.starts_at
     LIMIT %s'''


def _kieu(r):
    """Huỷ THẮNG trước: một buổi bù đã bị huỷ thì tin cần nói là nó không diễn ra nữa."""
    if r['status'] == 'cancelled':
        return 'huy'
    return 'bu' if r['makeup_for'] is not None else 'them'


def thay_doi_gan_day(class_id, user_id, tu_luc):
    """Buổi của em `user_id` trong lớp `class_id` đã đổi kể từ `tu_luc` (lúc cấp chìa).

    Trả `{'ds': [...], 'conNua': bool}`.

    Danh sách RỖNG là một câu trả lời thật ("không có gì đổi"), không phải chỗ để bỏ khoá đi:
    màn và bản PDF phải phân biệt được nó với "máy chủ chưa trả mục này".

    `conNua` vì `TRAN` CẮT BỚT, và cắt mà im lặng là cách êm ái nhất để một tờ báo cáo nói
    dối. Lớp sinh lại lịch cả kỳ là hàng chục buổi "mới xếp thêm" cùng lúc; tờ in 12 dòng rồi
    dừng, phụ huynh đếm được 12 và tưởng đó là tất cả, trong khi buổi ảnh hưởng tới con có thể
    nằm ở dòng 13. Lấy `TRAN + 1` dòng để BIẾT có bị cắt hay không mà không phải chạy thêm một
    câu `COUNT(*)` — một lượt đi Neon nữa cho một con số không ai đọc.
    """
    rows = q(_SQL, (class_id, user_id, tu_luc, tu_luc, TRAN + 1))
    ra = []
    for r in rows[:TRAN]:
        k = _kieu(r)
        ra.append({'sessionId': r['id'], 'kieu': k, 'nhan': NHAN[k],
                   'luc': r['starts_at'].isoformat() if r['starts_at'] else None,
                   'chuDe': r['topic']})
    return {'ds': ra, 'conNua': len(rows) > TRAN}
