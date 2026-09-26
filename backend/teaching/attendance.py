"""Chuyên cần — nơi DUY NHẤT định nghĩa "vắng mấy buổi".

VÌ SAO CÓ TỆP NÀY. Trước 31/08/2026 có HAI luật đếm buổi vắng chạy song song:
`sessions.py` loại buổi đã HUỶ, `exports.py` thì không. Hậu quả đo được: màn
hình nói "em nghỉ 2 buổi", file CSV mang đi họp phụ huynh nói "nghỉ 4". Hai con
số cùng tên, cùng một em, trong cùng một buổi họp — và không ai ở đó biết bên
nào đúng.

Luật đã chốt: **buổi `cancelled` KHÔNG tính vào chuyên cần của học viên.** Lớp
nghỉ vì giảng viên ốm mà tính vào số buổi vắng của em là đổ lỗi nhầm người, mà
con số đó lại đang dùng để quyết định gọi điện cho phụ huynh.

Buổi `planned` VẪN tính, và đó là chủ ý: một buổi đã điểm danh mà giảng viên
quên đổi trạng thái sang `done` vẫn là một buổi đã dạy thật.
"""
from django.db import DatabaseError

from common.db import q

#: Trạng thái buổi học KHÔNG được tính vào chuyên cần.
#: Khớp `SESSION_STATUS` ở `teaching/sessions.py` và CHECK ở lược đồ §33.
KHONG_TINH = ('cancelled',)


def _menh_de(alias='s'):
    """Mệnh đề SQL loại buổi không tính. Bí danh mặc định `s` = class_sessions.

    Nhúng giá trị hằng số vào chuỗi là an toàn ở đây — chúng là hằng trong mã
    nguồn, không phải dữ liệu người dùng gửi lên. Dựng từ hằng thay vì gõ tay
    để không thể lệch khi ai đó sửa `KHONG_TINH`.
    """
    return '%s.status NOT IN (%s)' % (
        alias, ', '.join("'%s'" % t for t in KHONG_TINH))


def ti_le(co_mat, co_dong):
    """Tỉ lệ chuyên cần = (có mặt + muộn) / số buổi EM ẤY CÓ DÒNG điểm danh.

    Nơi DUY NHẤT định nghĩa công thức này — kể cả bảng điều khiển toàn trung
    tâm: `overview.attendedPct` gọi thẳng vào đây chứ không tự tính (tới
    01/09/2026 nó vẫn tự tính bằng `_mot_phan_tram`, ra đúng cùng con số, nên
    không ai thấy — nhưng thứ giữ hai bản khớp nhau chỉ là việc chưa ai sửa một
    bên). Trước 31/08/2026 có HAI mẫu số chạy
    song song: sổ điểm danh CSV chia cho số buổi EM có dòng, tờ báo cáo gửi phụ
    huynh chia cho số buổi CẢ LỚP được tick. Đo được trên cùng một em: CSV nói
    100%, tờ giấy nói 67% — và tờ giấy là thứ đi ra khỏi hệ thống, về tận nhà.

    CHỌN MẪU SỐ "SỐ BUỔI EM ẤY CÓ DÒNG". Giảng viên tick cả lớp mà sót một em
    thì đó là lỗi hành chính của người lớn; chia em ấy cho mẫu số lớn hơn là
    biến lỗi đó thành hạnh kiểm của em, in ra giấy, gửi về nhà, không ai ở đó
    đính chính được.

    Khoảng trống ấy KHÔNG bị giấu đi — nó được báo RIÊNG (`noRecord` ở báo cáo
    phụ huynh, cột "Chưa điểm danh" ở sổ CSV), để người đọc biết tờ giấy này
    thiếu bao nhiêu buổi thay vì lặng lẽ chia cho một con số khác.

    "Có phép" NẰM TRONG mẫu số: nghỉ có phép vẫn là một buổi em không có mặt, và
    con số này đo mức độ CÓ MẮT chứ không đo mức độ ngoan. Lý do nghỉ đã có ô
    "Có phép" ngay bên cạnh nói hộ.

    Chưa có dòng nào → `None`, KHÔNG phải 0: "chưa có dữ liệu" và "không đi buổi
    nào" là hai chuyện khác nhau (cùng luật với `common.events.pct`).
    """
    if not co_dong:
        return None
    return round(co_mat * 100 / co_dong)


def dem_theo_hoc_vien(class_id, uids):
    """Chuyên cần luỹ kế của từng học viên trong MỘT lớp. Trả ``(dict, ok)``.

    ``ok=False`` nghĩa là KHÔNG ĐỌC ĐƯỢC, khác hẳn với "không có buổi nào" —
    xem `reports.py` phần "Đọc được hay không đọc được" để biết vì sao phân biệt
    hai chuyện đó lại quan trọng đến thế.

    Khoá của dict là ``user_id``; giá trị có ``marked``, ``absent``, ``late``,
    ``excused``. Học viên chưa có dòng điểm danh nào thì KHÔNG có mặt trong
    dict — bên gọi tự quyết định coi đó là 0 hay là "chưa có dữ liệu", vì hai
    màn hình khác nhau muốn hai cách hiển thị khác nhau.
    """
    if not uids:
        return {}, True
    try:
        rows = q('''SELECT a.user_id,
                           COUNT(*)                                     AS marked,
                           COUNT(*) FILTER (WHERE a.status = 'absent')  AS absent,
                           COUNT(*) FILTER (WHERE a.status = 'late')    AS late,
                           COUNT(*) FILTER (WHERE a.status = 'excused') AS excused
                    FROM attendance a
                    JOIN class_sessions s ON s.id = a.session_id
                    WHERE s.class_id = %s AND ''' + _menh_de('s') + '''
                      AND a.user_id = ANY(%s)
                    GROUP BY a.user_id''', (class_id, list(uids)))
    except DatabaseError:
        return {}, False
    return {r['user_id']: r for r in rows}, True


def ghi_co_phep(class_id, user_id, tu_ngay, den_ngay, *, boi=None):
    """Ghi "có phép" cho MỌI buổi của em trong khoảng ngày. Trả (số buổi, số lượt ghi đè).

    Hàm DỊCH VỤ của miền điểm danh: miền Yêu cầu gọi vào đây khi học vụ duyệt đơn "xin nghỉ
    học", thay vì tự `INSERT INTO attendance` (luật S4 — không ghi thẳng bảng miền khác).

    ── HAI QUYẾT ĐỊNH ĐÁNG NÓI ────────────────────────────────────────────────

    ① GHI ĐÈ lượt điểm danh đã có, và ĐẾM số lần ghi đè. Học vụ duyệt đơn nghỉ phép là
      quyết định cuối cùng — nhưng một buổi đã tick "có mặt" mà bị đổi lặng lẽ thành "có
      phép" là thứ không ai lần lại được. Số đếm đi vào `yeu_cau.thuc_thi` để dòng ấy trả
      lời được "hệ thống đã làm gì".

    ② Buổi HUỶ không tính. Lớp nghỉ vì giảng viên ốm thì em không cần xin phép, và một
      lượt "có phép" ở đó sẽ chảy vào mẫu số chuyên cần của tờ gửi phụ huynh.
    """
    from common.db import q, q1, x
    buoi = [r['id'] for r in q(
        '''SELECT id FROM class_sessions
            WHERE class_id = %s AND status <> 'cancelled'
              AND starts_at::date >= %s AND starts_at::date <= %s
         ORDER BY starts_at''', (class_id, tu_ngay, den_ngay))]
    if not buoi:
        return 0, 0
    ghi_de = q1("SELECT COUNT(*) AS n FROM attendance WHERE user_id = %s "
                "AND session_id = ANY(%s) AND status <> 'excused'",
                (user_id, buoi))['n']
    for sid in buoi:
        x('''INSERT INTO attendance (session_id, user_id, status, marked_by)
             VALUES (%s, %s, 'excused', %s)
             ON CONFLICT (session_id, user_id)
             DO UPDATE SET status = 'excused', marked_by = EXCLUDED.marked_by''',
          (sid, user_id, boi))
    return len(buoi), ghi_de
