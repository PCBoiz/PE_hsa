"""CƠ SỞ TÍNH HỌC PHÍ — những con số ai tính học phí cũng cần, và không hơn.

── VÌ SAO CHỈ TỚI ĐÂY (07/09/2026) ──────────────────────────────────────────

`docs/ERP_TOPHSA_2026-08-24.md` §7 nói thẳng về nhóm kinh doanh: "không tận
dụng được gì đã dựng và **sai một chi tiết là sai sổ sách**", khuyến nghị chỉ
làm sau khi có quy trình thu chi thật của TopHSA, và cân nhắc NỐI với phần mềm
kế toán họ đang dùng thay vì viết lại.

Anh Sơn chốt 07/09/2026: dựng **cơ sở tính**, không dựng bảng giá / hoá đơn /
công nợ.

Ranh giới ấy không phải làm cho ít đi. Nó là ranh giới giữa hai loại sự thật:

    ĐỀ TÀI Ở ĐÂY                          KHÔNG Ở ĐÂY
    em vào lớp ngày nào, rời ngày nào     một buổi giá bao nhiêu
    đã mở bao nhiêu buổi trong kỳ         thu theo tháng hay theo khoá
    em có mặt mấy buổi, vắng mấy buổi     nghỉ có phép thì có trừ tiền không
    có mấy buổi điểm danh lệch ghi danh   ai đã đóng, còn nợ bao nhiêu

Cột trái là chuyện ĐÃ XẢY RA ở trung tâm — đúng như nhau dù TopHSA thu theo
tháng, theo khoá hay theo buổi. Cột phải là chính sách, và mọi con số ở đó tôi
chỉ đoán được.

Nên view này **không có một trường tiền nào**. Không `amount`, không `price`,
không `currency`. Nó là bảng mà người đang tính học phí bằng Excel cần cầm —
và cũng đúng là đầu vào mà một mô-đun học phí thật sau này sẽ đọc.

── HAI CÁCH ĐẾM, VÀ VÌ SAO PHẢI TRẢ CẢ HAI ─────────────────────────────────

"Em ấy học mấy buổi" có hai câu trả lời khác nhau, và chúng lệch nhau thật:

  · `buoi_trong_ky`  — số buổi lớp đã mở TRONG QUÃNG em còn là thành viên.
                       Đây là con số của cách thu theo THỜI GIAN.
  · `co_mat`         — số buổi em thật sự có mặt (`present` + `late`).
                       Đây là con số của cách thu theo BUỔI THAM DỰ.

Trả cả hai, không chọn hộ. Chọn hộ là ngầm quyết định chính sách thu tiền của
một trung tâm mà mình không điều hành.

── `lech_ghi_danh`: chỗ dễ ra tiền sai nhất ────────────────────────────────

Đếm số lượt điểm danh của em vào một buổi diễn ra NGOÀI quãng em là thành viên
— trước ngày vào lớp, hoặc sau ngày rời lớp.

`docs/VIEC_CUA_ANH.md` mục 11.5 đã ghi khoảng lệch này như một việc chờ anh Sơn
quyết. Ở đây nó thành một CỘT chứ không bị nuốt vào tổng, vì mỗi lượt như thế
là một trong hai chuyện, và hai chuyện ấy ra tiền ngược nhau:

  · buổi học thử trước khi ghi danh → thường KHÔNG thu
  · ghi danh nhập sau, sai ngày     → PHẢI thu, và ngày vào lớp đang sai

Máy không phân biệt được. Người nhìn cột này thì phân biệt được ngay.

── VÌ SAO `IsAdminRole` ────────────────────────────────────────────────────

View gộp dữ liệu CẢ TRUNG TÂM, cùng loại với `AdminOverviewView` vốn đã chốt là
chỉ quản trị viên. Giữ đúng tiền lệ ấy.

Có thể sau này nên mở cho `Quản lý học vụ` — họ mới là người thật sự ngồi làm
bảng học phí. Chưa mở vì vai ấy hiện chưa có ai (đo 07/09: 1 quản trị, 1 giảng
viên, 4 học viên), tức nới quyền bây giờ là nới cho một cột trống. Ghi ra đây
để lần sau là một quyết định chứ không phải một chỗ bỏ sót.
"""
from datetime import date

from rest_framework.response import Response
from rest_framework.views import APIView

from common.db import q, q1
from common.permissions import IsAdminRole
from teaching.vocab import chi_hoc_vien

# `present` và `late` đều là CÓ MẶT. Muộn vẫn ngồi trong lớp, và không trung
# tâm nào miễn tiền một buổi vì em tới muộn mười phút. Tách riêng ở cột `muon`
# để ai cần vẫn thấy, nhưng tổng có mặt thì gộp.
CO_MAT = ('present', 'late')

# `chi_hoc_vien` KHÔNG phải chi tiết phụ.
#
# `class_members` trả lời "ai đang ở trong lớp", không trả lời "ai là học viên
# của lớp". Trên CSDL thật, tài khoản quản trị viên (id 7) đang là thành viên
# lớp 1 — anh Sơn chốt GIỮ nó ở đó để xem giao diện.
#
# Bản đầu của tệp này quên lọc, và lượt gọi thật đầu tiên trả về "Quản trị
# viên · admin@pe-hsa.vn" nằm giữa danh sách học viên phải tính tiền. Ở một
# bảng tiến độ thì đó là một dòng thừa; ở đây nó là một hoá đơn gửi nhầm.
#
# `teaching/vocab.py` viết ra ĐÚNG vì lỗi này, và chú thích của nó nêu đúng
# trường hợp id 7 lớp 1. Tôi vẫn mắc lại. Ghi ra đây để lần sau ai thêm một
# phép đếm theo lớp thì thấy ngay là phải hỏi câu ấy.


def _ngay(s, mac_dinh=None):
    """Đọc `YYYY-MM-DD`; chuỗi rỗng hay sai định dạng đều trả về mặc định.

    KHÔNG ném lỗi: tham số kỳ là thứ người dùng gõ tay vào thanh địa chỉ, và
    một trang 500 vì gõ nhầm ngày thì khó hiểu hơn nhiều so với một trang hiện
    đúng kỳ mặc định.
    """
    if not s:
        return mac_dinh
    try:
        return date.fromisoformat(s)
    except ValueError:
        return mac_dinh


class AdminBillingBasisView(APIView):
    """GET /api/admin/co-so-hoc-phi?term_id=&tu=&den= — không có trường tiền nào."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        term_id = request.query_params.get('term_id') or None
        try:
            term_id = int(term_id) if term_id else None
        except ValueError:
            term_id = None

        dot = q1('SELECT id, code, name, starts_on, ends_on FROM terms WHERE id = %s',
                 (term_id,)) if term_id else None

        # Kỳ mặc định lấy theo đợt nếu có đợt; không có thì để trống và tính
        # trên TOÀN BỘ lịch sử. Không bịa ra một kỳ "3 tháng gần đây" — một kỳ
        # mặc định vô căn cứ sẽ lặng lẽ cắt mất buổi học ở rìa.
        tu = _ngay(request.query_params.get('tu'), dot['starts_on'] if dot else None)
        den = _ngay(request.query_params.get('den'), dot['ends_on'] if dot else None)

        lop = q('''SELECT c.id, c.code, c.name, c.status, c.term_id,
                          t.name AS term_name,
                          u.name AS teacher_name
                   FROM classes c
                   LEFT JOIN terms t ON t.id = c.term_id
                   LEFT JOIN users u ON u.id = c.teacher_id
                   WHERE (%s::int IS NULL OR c.term_id = %s)
                   ORDER BY t.starts_on DESC NULLS LAST, c.name''',
                (term_id, term_id))
        if not lop:
            return Response({'ky': {'tu': tu, 'den': den}, 'dot': dot, 'lop': []})

        ids = [d['id'] for d in lop]

        # ── Buổi đã mở, theo lớp ────────────────────────────────────────────
        # `status <> 'cancelled'`: buổi đã huỷ thì không ai dạy và không ai học,
        # nên nó không phải cơ sở tính gì cả. Đếm riêng để người đọc thấy nó có
        # tồn tại chứ không biến mất không dấu vết.
        buoi = {d['class_id']: d for d in q('''
            SELECT class_id,
                   COUNT(*) FILTER (WHERE status IS DISTINCT FROM 'cancelled') AS da_mo,
                   COUNT(*) FILTER (WHERE status = 'cancelled')                AS da_huy
            FROM class_sessions
            WHERE class_id = ANY(%s)
              AND (%s::date IS NULL OR starts_at::date >= %s)
              AND (%s::date IS NULL OR starts_at::date <= %s)
            GROUP BY class_id''', (ids, tu, tu, den, den))}

        # ── Từng em: quãng là thành viên, buổi trong quãng, có mặt ──────────
        #
        # `buoi_trong_ky` phải đếm buổi nằm trong GIAO của ba quãng: kỳ đang
        # xem, quãng em là thành viên, và lịch lớp. Đếm buổi của cả lớp rồi gán
        # cho mọi em là sai ngay với em vào lớp giữa chừng — mà giữa chừng là
        # chuyện thường ngày ở một trung tâm luyện thi.
        em = q('''
            SELECT m.class_id, m.user_id, u.name, u.email,
                   m.joined_at, m.left_at, m.leave_reason,

                   (SELECT COUNT(*) FROM class_sessions s
                     WHERE s.class_id = m.class_id
                       AND s.status IS DISTINCT FROM 'cancelled'
                       AND s.starts_at >= m.joined_at
                       AND (m.left_at IS NULL OR s.starts_at <= m.left_at)
                       AND (%s::date IS NULL OR s.starts_at::date >= %s)
                       AND (%s::date IS NULL OR s.starts_at::date <= %s)
                   ) AS buoi_trong_ky,

                   (SELECT COUNT(*) FROM attendance a
                     JOIN class_sessions s ON s.id = a.session_id
                     WHERE a.user_id = m.user_id AND s.class_id = m.class_id
                       AND a.status = ANY(%s)
                       AND (%s::date IS NULL OR s.starts_at::date >= %s)
                       AND (%s::date IS NULL OR s.starts_at::date <= %s)
                   ) AS co_mat,

                   (SELECT COUNT(*) FROM attendance a
                     JOIN class_sessions s ON s.id = a.session_id
                     WHERE a.user_id = m.user_id AND s.class_id = m.class_id
                       AND a.status = 'late'
                       AND (%s::date IS NULL OR s.starts_at::date >= %s)
                       AND (%s::date IS NULL OR s.starts_at::date <= %s)
                   ) AS muon,

                   (SELECT COUNT(*) FROM attendance a
                     JOIN class_sessions s ON s.id = a.session_id
                     WHERE a.user_id = m.user_id AND s.class_id = m.class_id
                       AND a.status = 'absent'
                       AND (%s::date IS NULL OR s.starts_at::date >= %s)
                       AND (%s::date IS NULL OR s.starts_at::date <= %s)
                   ) AS vang,

                   -- Điểm danh NGOÀI quãng ghi danh. Xem chú thích đầu tệp.
                   (SELECT COUNT(*) FROM attendance a
                     JOIN class_sessions s ON s.id = a.session_id
                     WHERE a.user_id = m.user_id AND s.class_id = m.class_id
                       AND (s.starts_at < m.joined_at
                            OR (m.left_at IS NOT NULL AND s.starts_at > m.left_at))
                   ) AS lech_ghi_danh

            FROM class_members m
            JOIN users u ON u.id = m.user_id
            WHERE m.class_id = ANY(%s)
              AND ''' + chi_hoc_vien('u') + '''
            ORDER BY m.class_id, u.name''',
               (tu, tu, den, den,
                list(CO_MAT), tu, tu, den, den,
                tu, tu, den, den,
                tu, tu, den, den,
                ids))

        theo_lop = {}
        for d in em:
            theo_lop.setdefault(d['class_id'], []).append({
                'userId': d['user_id'],
                'ten': d['name'],
                'email': d['email'],
                'vaoLop': d['joined_at'].date().isoformat() if d['joined_at'] else None,
                'roiLop': d['left_at'].date().isoformat() if d['left_at'] else None,
                'lyDoRoi': d['leave_reason'],
                'buoiTrongKy': d['buoi_trong_ky'],
                'coMat': d['co_mat'],
                'muon': d['muon'],
                'vang': d['vang'],
                'lechGhiDanh': d['lech_ghi_danh'],
            })

        return Response({
            'ky': {'tu': tu, 'den': den},
            'dot': ({'id': dot['id'], 'code': dot['code'], 'name': dot['name'],
                     'startsOn': dot['starts_on'], 'endsOn': dot['ends_on']}
                    if dot else None),
            'lop': [{
                'id': d['id'],
                'ma': d['code'],
                'ten': d['name'],
                'trangThai': d['status'],
                'dot': d['term_name'],
                'giangVien': d['teacher_name'],
                'buoiDaMo': (buoi.get(d['id']) or {}).get('da_mo', 0),
                'buoiDaHuy': (buoi.get(d['id']) or {}).get('da_huy', 0),
                'hocVien': theo_lop.get(d['id'], []),
            } for d in lop],
        })
