"""CẢNH BÁO LỚP CHẬM TIẾN ĐỘ — đẩy con số đã tính tới người có thể làm gì với nó.

── VÌ SAO CÓ TỆP NÀY (28/09/2026) ──────────────────────────────────────────

Từ E1, hệ thống tính được lớp nào đang chậm so với khung chương trình
(`chuong_trinh/tien_do.py::danh_gia` — trễ ≥ 2 buổi khung, hoặc xong < 80 % phần phải xong
tới hôm nay). Con số ấy hiện trên màn "Toàn trung tâm" và trên chip từng lớp.

Nhưng **không ai được báo**. Muốn biết lớp mình đang tụt thì phải tự mở màn ra xem — và
người cần biết nhất là người bận nhất. Sổ nghiệm thu ghi thẳng đây là thứ CUỐI CÙNG còn
CHƯA của phân hệ thông báo: *"không loại chuông nào đẩy nó tới người; không mã nào gửi"*.

── BA QUYẾT ĐỊNH, VÀ LÝ DO ─────────────────────────────────────────────────

**Gửi cho ai.** Người ĐỨNG LỚP (`teaching/nhan_su_lop.py`): giảng viên, trợ giảng, học vụ
phụ trách. KHÔNG gửi học viên — "lớp chậm tiến độ" là việc của người dạy, nói với cả lớp chỉ
gây lo mà không em nào làm được gì. Cũng không gửi mọi học vụ: báo cho người nhìn thấy mọi
lớp nghĩa là mỗi tuần họ nhận một chuông cho mỗi lớp chậm của cả trung tâm.

**Bao lâu một lần.** MỖI TUẦN. Nhịp `hop_thu` chạy mỗi 60 giây; gửi mỗi lượt quét là hàng
nghìn chuông cho cùng một việc, và sau ngày đầu không ai đọc chuông nữa. Anh Sơn 27/09 được
hỏi nhịp gửi và tôi đề xuất mỗi tuần; chưa có trả lời tính tới 28/09, làm theo mặc định ấy —
đổi thì sửa `idx_notifications_cham_tien_do_moi_tuan` (§76) và dòng `ON CONFLICT` dưới đây.

**Chuông, không thư.** Người nhận là nhân sự, vào hệ thống hằng ngày; một lá thư mỗi tuần
cho mỗi lớp chậm là thứ người ta lọc bỏ sau tháng đầu. Thư ra khỏi hệ thống là không cuộn
lại được, nên chỗ nào chuông đủ thì đừng gửi thư.

── CHỐNG TRÙNG BẰNG CHỈ MỤC ────────────────────────────────────────────────

`ON CONFLICT DO NOTHING` trên chỉ mục duy nhất phần §76, KHÔNG đọc-rồi-ghi: hai nhịp chạy
chồng nhau sẽ CÙNG thấy "tuần này chưa gửi" và cùng ghi. Đúng bài học của §61d (nhắc hạn
nộp), và lý do ấy không đổi chỉ vì việc này chạy thưa hơn.

Mô-đun này CHỈ ĐỌC của miền chương trình và miền lớp học (qua hàm dịch vụ của chúng); nó ghi
bảng của chính miền thông báo.
"""
import logging

from django.db import transaction

from chuong_trinh.tien_do import tien_do_lop
from common.clock import local_now
from common.db import q
from teaching.nhan_su_lop import nhan_su_cua_lop

log = logging.getLogger(__name__)

LOAI = 'cham_tien_do'


def _chu(lop_ten, td):
    """(tiêu đề, nội dung) — câu người đọc, không con số kỹ thuật nào (RULES §10)."""
    tieu_de = 'Lớp "%s" đang chậm tiến độ' % lop_ten
    phan = []
    if td.get('treBuoi') is not None and td['treBuoi'] > 0:
        # Làm tròn về số buổi cho dễ nghe: "chậm 2,4 buổi" không ai nói thế.
        phan.append('chậm khoảng %s buổi so với khung chương trình' % round(td['treBuoi']))
    if td.get('tiLe') is not None:
        phan.append('mới dạy xong %s%% phần đáng lẽ xong tới hôm nay' % round(td['tiLe']))
    if td.get('chuaGhiSo'):
        phan.append('còn %d buổi chưa ghi sổ đầu bài' % td['chuaGhiSo'])
    cau = 'Lớp "%s" %s.' % (lop_ten, ', '.join(phan)) if phan else \
          'Lớp "%s" đang chậm so với khung chương trình.' % lop_ten
    return tieu_de, cau + ' Mở màn Chương trình lớp để xem buổi nào còn thiếu.'


def quet(bay_gio=None):
    """Một lượt quét. Trả số chuông MỚI (tuần này đã báo rồi thì không tính).

    Gọi từ `hop_thu.nhip`. Lỗi ở đây không được chặn nhịp gửi thư — bên gọi bọc try.
    """
    bay_gio = bay_gio or local_now()
    # Lớp ĐANG HỌC và ĐÃ NHẬN KHUNG. Lớp tạm dừng thì chậm là đúng, và lớp chưa có khung thì
    # không có kế hoạch nào để chậm so với nó — `tien_do_lop` cũng bỏ qua lớp không khung,
    # nhưng lọc ở đây để không hỏi nó về hàng trăm lớp mỗi phút.
    lop = q("""SELECT id, name FROM classes
                WHERE status = 'active' AND syllabus_version_id IS NOT NULL""")
    if not lop:
        return 0
    ten = {r['id']: r['name'] for r in lop}
    # KHÔNG `kem_buoi=True`: cờ ấy thêm một câu truy vấn nữa để lấy DANH SÁCH buổi chưa
    # ghi sổ, mà câu chuông chỉ cần con SỐ (`chuaGhiSo`, đã có sẵn). Nhịp này chạy mỗi 60
    # giây trên mọi lớp của trung tâm — một câu thừa ở đây là một câu thừa mãi mãi.
    td = tien_do_lop(list(ten), nay=bay_gio)

    dong = []
    for cid, t in td.items():
        if not t.get('cham'):
            continue
        for uid in nhan_su_cua_lop(cid):
            tieu_de, noi_dung = _chu(ten[cid], t)
            dong.append((uid, tieu_de, noi_dung, cid, '/giang-day/chuong-trinh/%d' % cid))
    if not dong:
        return 0

    with transaction.atomic():
        moi = q('''INSERT INTO notifications (user_id, type, title, body, ref_type, ref_id,
                                              link, created_at)
                   SELECT v.uid, %s, v.tieu_de, v.noi_dung, 'class', v.lop, v.link, %s
                     FROM (VALUES %s) AS v(uid, tieu_de, noi_dung, lop, link)
                   ON CONFLICT (user_id, ref_id, (date_trunc('week', created_at)))
                        WHERE type = 'cham_tien_do' DO NOTHING
                   RETURNING id''' % ('%s', '%s', ', '.join(['(%s, %s, %s, %s, %s)'] * len(dong))),
                tuple([LOAI, bay_gio] + [x for d in dong for x in d]))
    return len(moi)
