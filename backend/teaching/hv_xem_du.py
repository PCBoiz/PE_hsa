"""EM XEM LẠI ĐỦ CẢ KHOÁ — bản ghi buổi học và học liệu, có ô tìm và phân trang.

  GET /api/lop-cua-toi/<class_id>/xem-du?loai=ban-ghi|hoc-lieu&tim=&truoc=&limit=&chi=&chuaMo=

── VÌ SAO CÓ (27/09/2026, bảng phân rã dòng 29 và 30) ────────────────────────

Thẻ lớp của em chỉ lấy **bốn** bản ghi gần nhất (`lop_cua_toi.py:44 SO_BAN_GHI = 4`) và
**bốn** tài liệu (`:48 SO_HOC_LIEU = 4`). Bốn là con số đúng cho một THẺ — nó phải nói "có
cái mới" chứ không thành cái kho. Nhưng ngoài thẻ ấy thì em không có màn nào khác: lớp 24
buổi thì từ buổi thứ năm trở về trước, bản ghi và tài liệu coi như không tồn tại với em, và
không có ô tìm nào. Nhân sự có danh sách đủ từ lâu (`hoc_lieu.py::danh_sach`,
`ban_ghi.py::ThongKeBanGhiView`); người PHẢI XEM LẠI BÀI thì không.

Bảng của khách đòi đúng hai thứ đang thiếu: *"danh sách record theo buổi, tìm kiếm"* (dòng
29) và học liệu (dòng 30). Agent soát 27/09 hạ ô tóm tắt dòng 29 từ "CÓ" xuống "MỘT PHẦN" vì
chỗ này (`docs/agent/BAO_CAO_PHAN_RA.md` §3.3, §3.4).

── MỘT CỬA, HAI DANH SÁCH — VÌ SAO KHÔNG HAI TUYẾN ───────────────────────────

Hai danh sách dùng CÙNG ba hàng rào (còn trong lớp · buổi bù · lớp khác thì 404) và cùng một
lối phân trang. Hai tuyến riêng thì ba hàng rào ấy nằm ở hai chỗ, và một ngày nào đó chúng
lệch nhau — đúng chuyện đã xảy ra với §72 (bốn cửa, ba cửa quên buổi bù, `hoc_lieu.py` đã
ghi lại). `loai` chọn danh sách; phần quyền chạy MỘT lần ở đầu hàm cho cả hai.

── PHÂN TRANG THEO KHOÁ, KHÔNG THEO OFFSET ───────────────────────────────────

Khoá là CẶP `(thời điểm, id)`, không phải `id` một mình: lịch sinh hàng loạt rồi chèn buổi bù
là ra một lớp mà thứ tự `id` KHÔNG trùng thứ tự thời gian, nên phân trang bằng `id` sẽ nhảy
dòng — im lặng, và chỉ ở những lớp có buổi bù. Cặp ấy so bằng phép so HÀNG của Postgres
(`(a, b) < (SELECT x, y …)`) để mốc lấy từ chính dòng cuối trang trước; màn chỉ gửi lại một
số nguyên (`truoc`), không phải một mốc thời gian tự ghép ở trình duyệt.

Câu con lấy mốc có `k.class_id = %s`: thiếu nó thì `truoc` là id của một dòng lớp KHÁC vẫn
cho ra một mốc hợp lệ, tức một cách dò thứ tự thời gian của lớp khác. Không có mốc thì câu
con trả NULL, điều kiện thành NULL, và trang rỗng — hỏng về phía an toàn.

── HAI CHỖ DỄ HỎNG, ĐÃ CÓ NGƯỜI VẤP ─────────────────────────────────────────

① **Tài liệu đang ẩn** (`NOT h.an`). Giảng viên soạn trước cả khoá rồi mở dần theo tiến độ
  (§60). Bỏ sót điều kiện này là em thấy đề kiểm tra trước giờ thi — và ô TÌM là cửa sau dễ
  quên nhất, nên `tests_hv_xem_du.py` kiểm cả đường tìm.

② **`thuoc_buoi` phải nhận tên cột CÓ TIỀN TỐ BẢNG** (`h.session_id`, `s.id` — không bao giờ
  `session_id` trần). Câu con của nó có bảng `sp` riêng; một tên trần bị hiểu là cột CỦA `sp`,
  điều kiện thành `sp.session_id = sp.session_id` — luôn đúng — và hàm trả lời "em có thuộc
  buổi NÀO ĐÓ không". Không lỗi cú pháp, không cảnh báo. Đọc docstring của `thuoc_buoi`.

── CHỈ ĐỌC, VÀ CHỈ CỦA CHÍNH EM ─────────────────────────────────────────────

Không ghi bảng nào. Việc ghi nhận "em đã mở bản ghi" vẫn là cửa §72 sẵn có
(`POST /api/sessions/<id>/ban-ghi/da-mo`, `ban_ghi.py`) — màn mới gọi đúng cửa ấy, nên con số
"1/2 em đã mở" của trợ giảng không đổi cách đếm. `daMo` / `lanMo` ở đây chỉ là trạng thái của
CHÍNH em, không bao giờ của bạn cùng lớp (ai đã xem bài là việc của người dạy — xem §72).
"""
from rest_framework.response import Response

from common.clock import local_now
from common.db import q, q1
from common.params import mau_like, so_nguyen
from common.views import NguoiDungView
from teaching.nguoi_buoi import thuoc_buoi

#: Số dòng một trang, và trần khi màn tự xin nhiều hơn.
MOI_TRANG = 20
TRAN_TRANG = 50

#: Hai danh sách cửa này phục vụ — chữ trên URL, nên đặt bằng gạch ngang như mọi tuyến khác.
LOAI_BAN_GHI = 'ban-ghi'
LOAI_HOC_LIEU = 'hoc-lieu'

#: Ô lọc của danh sách học liệu: kho chung của lớp, hay tài liệu gắn vào một buổi.
CHI = ('chung', 'buoi')

#: Trần độ dài chuỗi tìm — ô tìm là chữ người dùng gõ; một chuỗi 10 kB không tìm ra gì hơn.
TRAN_TIM = 100

# Bản ghi buổi ĐÃ DIỄN RA, chưa huỷ, đã có link. `starts_at DESC, id DESC` — buổi vừa học
# trước, và `id` là bậc phá thế để hai buổi cùng giờ không đổi chỗ giữa hai trang.
_SQL_BAN_GHI = '''
    SELECT s.id, s.starts_at, s.topic, s.recording_url,
           COALESCE(v.lan_mo, 0) AS lan_mo
      FROM class_sessions s
      LEFT JOIN recording_views v ON v.session_id = s.id AND v.user_id = %s
     WHERE s.class_id = %s
       AND s.status <> 'cancelled'
       AND s.recording_url IS NOT NULL AND s.recording_url <> ''
       AND s.starts_at < %s
       AND ''' + thuoc_buoi('s.id', '%s') + '''
       AND (%s::int IS NULL
            OR (s.starts_at, s.id) < (SELECT k.starts_at, k.id FROM class_sessions k
                                       WHERE k.id = %s AND k.class_id = %s))
       AND (%s::text IS NULL OR s.topic ILIKE %s
            OR to_char(s.starts_at, 'DD/MM/YYYY') ILIKE %s)
       AND (NOT %s OR v.session_id IS NULL)
     ORDER BY s.starts_at DESC, s.id DESC
     LIMIT %s'''

# Học liệu §60. Sắp "THEO BUỔI": tài liệu của buổi nào thì theo giờ buổi ấy, kho chung của
# lớp (`session_id IS NULL`) theo lúc gắn — nên buổi vừa học nằm trên, buổi đầu khoá nằm dưới.
_SQL_HOC_LIEU = '''
    SELECT h.id, h.ten, h.mo_ta, h.nguon, h.url, h.session_id, h.created_at,
           s.starts_at AS buoi_luc, s.topic AS buoi_chu_de
      FROM hoc_lieu h
      LEFT JOIN class_sessions s ON s.id = h.session_id
     WHERE h.class_id = %s
       AND NOT h.an
       AND (h.session_id IS NULL OR ''' + thuoc_buoi('h.session_id', '%s') + ''')
       AND (%s::int IS NULL
            OR (COALESCE(s.starts_at, h.created_at), h.id)
               < (SELECT COALESCE(ks.starts_at, k.created_at), k.id
                    FROM hoc_lieu k LEFT JOIN class_sessions ks ON ks.id = k.session_id
                   WHERE k.id = %s AND k.class_id = %s))
       AND (%s::text IS NULL OR h.ten ILIKE %s OR COALESCE(h.mo_ta, '') ILIKE %s)
       AND (%s::text IS NULL OR (%s::text = 'chung') = (h.session_id IS NULL))
     ORDER BY COALESCE(s.starts_at, h.created_at) DESC, h.id DESC
     LIMIT %s'''


def _iso(v):
    return v.isoformat() if v else None


def _lop_cua_em(uid, class_id):
    """Dòng lớp — CHỈ khi em còn đang học lớp ấy. `None` = không có gì để trả.

    Một câu cho hai việc: hàng rào quyền và tên lớp cho tiêu đề màn. `m.left_at IS NULL` là
    cùng một luật với `hoc_lieu.py::_la_hoc_vien_dang_hoc` và `ban_ghi.py::_thuoc_lop` — rời
    lớp là hết quyền xem; gộp vào đây vì màn cần CẢ tên lớp, và hai câu là hai lượt đi Neon.
    """
    return q1('''SELECT c.id, c.name, c.code
                   FROM classes c
                   JOIN class_members m ON m.class_id = c.id
                  WHERE c.id = %s AND m.user_id = %s AND m.left_at IS NULL''',
              (class_id, uid))


def _tim(raw):
    """Chuỗi tìm → mẫu LIKE đã vô hiệu hoá ký tự đại diện, hoặc `None` khi ô tìm để trống.

    `mau_like` (dùng chung với danh sách tài khoản) thoát `%` và `_`: không thoát thì em gõ
    một dấu `%` sẽ nhận về CẢ kho và tưởng mình vừa tìm ra đúng thứ cần.
    """
    s = (raw or '').strip()[:TRAN_TIM]
    return mau_like(s) if s else None


def _ban_ghi(uid, cid, truoc, mau, chua_mo, n):
    return q(_SQL_BAN_GHI, (uid, cid, local_now(), uid, truoc, truoc, cid,
                            mau, mau, mau, chua_mo, n))


def _hoc_lieu(uid, cid, truoc, mau, chi, n):
    return q(_SQL_HOC_LIEU, (cid, uid, truoc, truoc, cid, mau, mau, mau, chi, chi, n))


def _hinh_ban_ghi(r):
    return {'sessionId': r['id'], 'startsAt': _iso(r['starts_at']), 'topic': r['topic'],
            'recordingUrl': r['recording_url'],
            # "đã MỞ", không phải "đã xem xong": bản ghi nằm trên Zoom, ngoài tầm đo (§72).
            'daMo': r['lan_mo'] > 0, 'lanMo': r['lan_mo']}


def _hinh_hoc_lieu(r):
    return {'id': r['id'], 'ten': r['ten'], 'moTa': r['mo_ta'], 'nguon': r['nguon'],
            'url': r['url'], 'sessionId': r['session_id'],
            'buoiLuc': _iso(r['buoi_luc']), 'buoiChuDe': r['buoi_chu_de'],
            'luc': _iso(r['created_at'])}


class XemDuLopView(NguoiDungView):
    """GET /api/lop-cua-toi/<class_id>/xem-du — không ghi gì.

    404 (không 403) cho mọi trường hợp em không đang học lớp ấy: một cửa lớp trả 403 là đã
    nói ra rằng lớp đó có tồn tại, và đó là thứ đếm được từ ngoài.
    """

    def get(self, request, class_id):
        lop = _lop_cua_em(request.user.id, class_id)
        if not lop:
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)

        p = request.query_params
        loai = (p.get('loai') or LOAI_BAN_GHI).strip()
        if loai not in (LOAI_BAN_GHI, LOAI_HOC_LIEU):
            return Response({'error': 'Không có danh sách này.'}, status=400)

        n = so_nguyen(p.get('limit'), MOI_TRANG, 1, TRAN_TRANG)
        truoc = so_nguyen(p.get('truoc'), None, 1, 2 ** 31 - 1)
        mau = _tim(p.get('tim'))
        uid = request.user.id

        if loai == LOAI_BAN_GHI:
            # Lấy n+1 dòng để biết CÓ CÒN trang sau mà không phải đếm cả tập (`COUNT(*)` trên
            # mỗi lần bấm "Xem thêm" là một lượt đi Neon cho một con số không ai đọc).
            rows = _ban_ghi(uid, class_id, truoc, mau,
                            p.get('chuaMo') in ('1', 'true'), n + 1)
            hinh = _hinh_ban_ghi
        else:
            chi = p.get('chi') if p.get('chi') in CHI else None
            rows = _hoc_lieu(uid, class_id, truoc, mau, chi, n + 1)
            hinh = _hinh_hoc_lieu

        tiep = rows[n - 1]['id'] if len(rows) > n else None
        return Response({'lop': {'id': lop['id'], 'name': lop['name'], 'code': lop['code']},
                         'loai': loai,
                         'items': [hinh(r) for r in rows[:n]],
                         'tiep': tiep})
