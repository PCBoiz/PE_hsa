"""TIẾN ĐỘ CHƯƠNG TRÌNH THEO BUỔI (4.3, 25/09/2026) — lớp đã dạy tới buổi nào
trong khung đã gán, so với tổng số buổi của khung.

KHÁC "tiến độ học" của ``teaching/reports.py::class_report`` (đó là % BÀI HỌC
từng em đã hoàn thành trong hệ thống — CÁ NHÂN, không cần khung). Đây là tiến
độ CỦA LỚP theo LỊCH DẠY đã lên kế hoạch — chỉ có nghĩa khi lớp đã nhận một
phiên bản chương trình (``classes.syllabus_version_id``, §64). Hai con số đo
hai việc khác nhau: một em có thể học vượt trước qua tự học (tiến độ BÀI cao)
trong khi lớp mới dạy tới buổi 3/20 (tiến độ CHƯƠNG TRÌNH thấp).

Đây KHÔNG phải bộ đo tiến độ đầy đủ mà kế hoạch v2 mô tả cho E1 (còn "đã dạy
chưa ghi sổ", trọng số từng buổi qua ``syllabus_items.weight``...) — chỉ là
CON SỐ THÔ đầu tiên: buổi đã dạy / tổng buổi, đủ trả lời "lớp đang ở đâu trong
chương trình" cho yêu cầu 4.3. Mở rộng thêm thì SỬA Ở ĐÂY, đừng viết bản thứ
hai — xem cảnh báo tương tự ở đầu ``teaching/reports.py``.
"""
from common.db import q1


def tien_do_lop(class_id):
    """``None`` nếu lớp CHƯA nhận khung nào — khác hẳn "tiến độ 0%": không có
    khung thì không có mẫu số, và 0% ngầm bịa ra một mẫu số không tồn tại.
    """
    lop = q1('SELECT syllabus_version_id FROM classes WHERE id=%s', (class_id,))
    if not lop or not lop['syllabus_version_id']:
        return None
    version_id = lop['syllabus_version_id']

    tong = q1('SELECT count(*) AS n FROM syllabus_sessions WHERE version_id=%s',
              (version_id,))['n']
    if not tong:
        # Đã gán khung nhưng khung đó chưa có buổi nào (hiếm — xuất bản đòi ít
        # nhất 1 buổi, nhưng phòng khi buổi bị xoá sau đó). 0% có nghĩa ở đây vì
        # mẫu số CÓ TỒN TẠI, chỉ đang bằng 0.
        return {'versionId': version_id, 'sessionsPlanned': 0, 'sessionsDone': 0,
                'pct': 0, 'currentSession': None}

    # Buổi THẬT đã dạy (`status='done'`) VÀ đã khớp với một buổi trong khung —
    # buổi chưa khớp (`syllabus_session_id IS NULL`, lớp chưa chạy "gán khung"
    # cho buổi đó) không tính, vì không biết nó ứng với buổi số mấy trong khung.
    da_day = q1('''SELECT count(*) AS n, max(ss.sort_order) AS toi_buoi
                     FROM class_sessions cs
                     JOIN syllabus_sessions ss ON ss.id = cs.syllabus_session_id
                    WHERE cs.class_id = %s AND cs.status = 'done' ''', (class_id,))

    return {
        'versionId': version_id,
        'sessionsPlanned': tong,
        'sessionsDone': da_day['n'] or 0,
        'pct': round((da_day['n'] or 0) * 100 / tong),
        # Buổi (theo số thứ tự khung) XA NHẤT đã dạy — "lớp đang ở buổi mấy",
        # khác `sessionsDone` khi có buổi giữa chừng bị bỏ dạy hoặc dạy lệch thứ tự.
        'currentSession': da_day['toi_buoi'],
    }
