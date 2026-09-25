"""Quản lý tài khoản ở quy mô trung tâm — danh sách, nhập hàng loạt, vòng đời,
nhật ký kiểm toán.

VÌ SAO TÁCH RA KHỎI ``teaching/views.py``. Bốn endpoint dưới đây phục vụ một
việc duy nhất mà bản cũ làm hỏng: TopHSA có vài trăm học viên, còn màn hình quản
trị được viết cho một sản phẩm tự học vài chục người. ``AdminUsersView`` cũ cứng
``LIMIT 50`` không phân trang không lọc — đến em thứ 51 là trợ giảng không còn
đường nào nhìn thấy em đó nữa, kể cả biết chắc em có tài khoản.

NGÂN SÁCH VÒNG GỌI — đọc trước khi thêm bất kỳ câu SQL nào vào tệp này. Đo thực
tế 30/08/2026, từ máy phát triển ở Việt Nam tới Neon: **246ms cho MỘT vòng gọi**,
bất kể câu đó nặng hay nhẹ — ``SELECT 1`` và ``SELECT count(*) FROM users`` đều
246ms. Trên Render (region ohio, cùng vùng Neon us-east-2) con số này xuống <5ms
(xem ``render.yaml``), nên ĐỪNG lấy 246ms làm cơ sở tính giới hạn cho chạy thật.

Nhưng cái quy tắc rút ra thì đúng ở cả hai nơi: thứ quyết định độ trễ là SỐ CÂU
chứ không phải độ phức tạp từng câu, và số câu KHÔNG được tăng theo số dòng dữ
liệu. Lấy tên lớp cho 25 học viên bằng 25 câu là 6 giây trắng màn hình khi phát
triển, và vẫn là 25 lần đi-về mạng khi chạy thật — một thiết kế hỏng ở cả hai
môi trường, chỉ khác là ở môi trường thật nó im lặng cho tới khi trung tâm đông
lên. Mọi hàm ở đây cố định số câu theo THIẾT KẾ, trừ đúng một chỗ không tránh
được (ghi tài khoản trong ``AdminBulkCreateUsersView``) và chỗ đó có trần cứng.

Định danh (email, số điện thoại) mọi lúc GHI và mọi lúc TRA đều đi qua
``common/identity.py``. Chuẩn hoá một phía là tái tạo đúng cái lỗi đã vá
30/08/2026: trợ giảng lưu ``nguyen.an@gmail.com``, học viên gõ
``Nguyen.An@Gmail.com``, hệ thống trả "sai mật khẩu" trong khi tài khoản nằm
ngay đó — và từ khi bỏ tự đăng ký thì em không có đường nào tự thoát.
"""
import re
from datetime import timedelta

from django.db import IntegrityError, transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.hoat_dong import sql_hoat_dong
from accounts.validators import validate_email_field, validate_name_field, validate_phone_field
from common import audit
from common.bangtinh import KY_TU_CONG_THUC
from common.clock import local_now
from common.db import q, q1, x
from common.identity import looks_like_email, norm_email, norm_phone
from common.params import doc_trang, mau_like, trang_kem_tong
from common.permissions import (
    ASSIGNABLE_ROLES,
    ROLE_ADMIN,
    ROLE_STUDENT,
    IsAdminOrAcademic,
    IsAdminRole,
    is_admin,
    last_active_admin,
)
from courses.truy_cap import BA_MON, LOP_DANG_HOC, mon_mo
from stats.goals import as_date
from teaching import vocab
from teaching.overview import NGUONG_NGU
from teaching.reports import _progress_by_user, tong_bai_theo_khoa
from teaching.tinh_trang import (
    HOC_PHI,
    MA_HOC_PHI,
    NHAN_TINH_TRANG_HOC,
    TINH_TRANG_HOC,
    sql_tinh_trang_hoc,
)

# Dùng lại của teaching/views.py, không viết bản thứ hai: mật khẩu tạm sinh hai
# kiểu khác nhau thì trợ giảng đọc cho học viên hai dạng chuỗi khác nhau, còn
# nhãn nhật ký dựng hai kiểu thì cùng một người hiện ra hai tên trong cùng một
# trang nhật ký. Chiều nhập một hướng: views.py KHÔNG được import ngược lại đây.
from teaching.views import _doc_ngay_vao_lop, _temp_password, _user_label

#: Vòng đời tài khoản (schema §31). 'suspended' = khoá đăng nhập, GIỮ dữ liệu học.
USER_STATUSES = ('active', 'suspended')

#: Trần số tài khoản được tạo trong MỘT lần dán. Xem docstring
#: ``AdminBulkCreateUsersView``: con số này ra từ giá CPU của scrypt (126ms mỗi
#: mật khẩu) đặt cạnh timeout 30 giây của gunicorn, không phải chọn cho tròn.
MAX_CREATE_PER_BATCH = 50

#: Trần số dòng được PHÂN TÍCH một lần. Kiểm tra không tốn thêm câu SQL nào nên
#: rộng tay hơn nhiều trần ở trên: trợ giảng vẫn xem trước được cả danh sách 400
#: em trong một lần, rồi mới chia nhỏ ra mà tạo.
MAX_PARSE_LINES = 1000


# ── Trợ giúp chung ──────────────────────────────────────────────────────────

def _paging(params, default_per_page, max_per_page):
    """Bọc mỏng quanh `common.params.doc_trang` — giữ tên cũ cho 6 chỗ đang gọi."""
    return doc_trang(params, default_per_page, max_per_page)


# Dời sang `common/params.py` (24/09/2026) để danh sách lớp dùng chung mà không
# import vòng (`admin_users` → `teaching.views` → `reports`). Giữ tên cũ.
_like = mau_like
_page_with_total = trang_kem_tong


#: Các tham số lọc của màn hình tài khoản. Khai một chỗ để bộ lọc và câu hỏi
#: "người dùng có lọc gì không" không bao giờ lệch nhau.
USER_FILTER_PARAMS = ('q', 'role', 'status', 'class_id', 'chua_xep_lop', 'khong_hoat_dong',
                      # V-k (25/09/2026): đợt, môn, ngày cấp tài khoản.
                      'term_id', 'course_id', 'tu', 'den',
                      # V-m (25/09/2026): tình trạng học tập (tính), tình trạng học phí.
                      'tinh_trang_hoc', 'hoc_phi')
#: Giá trị ô lọc "Học phí" nghĩa là CHƯA ĐẶT (cột NULL) — không phải một mã của CHECK.
HOC_PHI_CHUA_DAT = 'chua_dat'
#: Ô lọc dạng CÔNG TẮC: chỉ đang lọc khi giá trị là "có" — `chua_xep_lop=0` (bỏ tích) thì không.
_CONG_TAC = ('chua_xep_lop',)
#: Trần của ô "không hoạt động ≥ N ngày". Không kẹp thì `N = 10**9` tràn `timedelta` → 500.
_TRAN_NGAY_NGU = 3650


def _bat(gia_tri):
    return (gia_tri or '').strip().lower() in ('1', 'true', 'on', 'yes')


def _so_ngay_ngu(raw):
    """``khong_hoat_dong`` → số ngày trong [1, `_TRAN_NGAY_NGU`], hoặc None khi không đọc được."""
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return None
    return n if 1 <= n <= _TRAN_NGAY_NGU else None


def any_user_filter(params) -> bool:
    """Người dùng có đặt bộ lọc nào không.

    Bản xuất CSV cần biết để đặt tên tệp: một tệp đủ và một tệp đã lọc nằm cạnh
    nhau trong thư mục Tải về mà không phân biệt được thì sớm muộn có người mang
    bản thiếu người đi họp.
    """
    return any(_bat(params.get(k)) if k in _CONG_TAC else (params.get(k) or '').strip()
               for k in USER_FILTER_PARAMS)


def build_user_filters(params):
    """Dựng mệnh đề WHERE lọc tài khoản → (sql, args). Bí danh bảng bắt buộc: ``u``.

    Để ngoài lớp view và không đặt dấu gạch dưới ở đầu tên vì bản xuất CSV
    (``teaching/exports.py``) phải lọc GIỐNG HỆT màn hình danh sách. Hai chỗ tự
    viết một bộ điều kiện thì kiểu gì cũng có ngày trợ giảng xuất ra tệp không
    khớp với bảng em vừa nhìn, và khi đó không ai biết bên nào đúng.
    """
    where, args = ['TRUE'], []

    term = (params.get('q') or '').strip()
    if term:
        # Số điện thoại đi qua norm_phone TRƯỚC khi so: phiếu đăng ký của TopHSA
        # ghi '+84 964 245 623' còn CSDL lưu '0964245623'. Chép nguyên văn từ
        # phiếu vào ô tìm kiếm mà không chuẩn hoá là tìm không ra chính em vừa
        # được nhập vào hệ thống năm phút trước.
        # Mã học viên và username (§51, 23/09/2026): bảng yêu cầu của TopHSA đòi
        # tìm theo "họ tên, Email, Username, số điện thoại" — và học vụ tra một
        # em theo mã HSA-xxxxx in trên phiếu thu nhanh hơn theo tên.
        where.append('(lower(u.name) LIKE %s OR lower(u.email) LIKE %s OR u.phone LIKE %s '
                     'OR lower(u.student_code) LIKE %s OR lower(u.username) LIKE %s)')
        args += [_like(term), _like(term), _like(norm_phone(term) or term), _like(term), _like(term)]

    role = (params.get('role') or '').strip()
    if role:
        where.append('u.role = %s')
        args.append(role)

    status = (params.get('status') or '').strip()
    if status:
        where.append('u.status = %s')
        args.append(status)

    class_id = (params.get('class_id') or '').strip()
    if class_id:
        try:
            cid = int(class_id)
        except (TypeError, ValueError):
            where.append('FALSE')          # mã lớp không phải số → không ai khớp
        else:
            # EXISTS chứ không JOIN: JOIN nhân bản dòng nếu một cặp
            # (lớp, học viên) có nhiều bản ghi, và khi đó câu ĐẾM tổng sai theo.
            # Khoá chính của class_members đang chặn chuyện đó, nhưng con số
            # tổng của màn hình này không nên phụ thuộc vào ràng buộc của một
            # bảng khác có thể đổi.
            where.append('EXISTS (SELECT 1 FROM class_members cm '
                         'WHERE cm.user_id = u.id AND cm.class_id = %s '
                         'AND cm.left_at IS NULL)')
            args.append(cid)

    if _bat(params.get('chua_xep_lop')):
        # "Chưa xếp lớp" (1.4b) = HỌC VIÊN không còn lượt học nào ĐANG MỞ MÔN — cùng mệnh
        # đề với cột "Lớp" và với cổng mở môn (`truy_cap.LOP_DANG_HOC`): em hiện ở đây
        # đúng là em không vào được bài nào. Em chỉ còn trong một lớp đã huỷ cũng thuộc
        # nhóm này. Nhân sự không "chờ xếp lớp" nên loại ở MÁY CHỦ, cùng lý do như lọc vai
        # của học vụ: bản CSV đi qua đúng hàm này.
        where.append(vocab.chi_hoc_vien('u'))
        where.append('NOT EXISTS (SELECT 1 FROM class_members m JOIN classes c ON c.id = m.class_id '
                     'WHERE m.user_id = u.id AND ' + LOP_DANG_HOC + ')')

    raw = (params.get('khong_hoat_dong') or '').strip()
    if raw:
        so_ngay = _so_ngay_ngu(raw)
        if so_ngay is None:
            where.append('FALSE')          # cùng luật mã lớp sai: không hiểu thì không ai khớp
        else:
            # ĐÚNG định nghĩa của thẻ "Tài khoản lâu không vào" ở Tổng quan
            # (`overview.tai_khoan_ngu`): tài khoản ĐANG MỞ, mốc hoạt động (rơi về ngày cấp
            # nếu chưa vào lần nào) cách bây giờ ≥ N ngày — cùng câu `sql_hoat_dong`, cùng
            # phép `<=`. Có phép kiểm so hai con số: `tests_danh_sach_hoc_vien.py`.
            nay = local_now()
            where.append("u.status = 'active'")
            where.append('(' + sql_hoat_dong('u', '%s', cot=('moc',)) + ') <= %s')
            args += [nay, nay - timedelta(days=so_ngay)]

    # ĐỢT HỌC / MÔN (V-k, 25/09/2026 — bảng TopHSA dòng 6 "lọc theo lớp / môn / khoá"):
    # em đang học (`LOP_DANG_HOC`) một lớp thuộc đợt ấy / mang môn ấy — cùng luật với cột
    # "Lớp đang theo học" của tệp xuất. Lớp để trống môn học cả ba môn HSA (`BA_MON`).
    term_id = (params.get('term_id') or '').strip()
    if term_id:
        try:
            args.append(int(term_id))
        except (TypeError, ValueError):
            where.append('FALSE')
        else:
            where.append('EXISTS (SELECT 1 FROM class_members m JOIN classes c ON c.id = m.class_id '
                         'WHERE m.user_id = u.id AND c.term_id = %s AND ' + LOP_DANG_HOC + ')')
    course_id = (params.get('course_id') or '').strip()
    if course_id:
        where.append('EXISTS (SELECT 1 FROM class_members m JOIN classes c ON c.id = m.class_id '
                     'WHERE m.user_id = u.id AND ' + LOP_DANG_HOC + ' '
                     'AND (c.course_id = %s OR (c.course_id IS NULL AND %s)))')
        args += [course_id, course_id in BA_MON]

    # NGÀY CẤP TÀI KHOẢN (`created_at`), `den` tính CẢ ngày ấy. Ngày không đọc được → không
    # ai khớp (cùng luật mã lớp sai); tệp xuất trả 400 trước khi tới đây.
    for khoa, phep in (('tu', '>='), ('den', '<')):
        raw = (params.get(khoa) or '').strip()
        if not raw:
            continue
        ngay = as_date(raw)
        if not ngay:
            where.append('FALSE')
            continue
        where.append('u.created_at %s %%s' % phep)
        args.append(ngay + timedelta(days=1) if khoa == 'den' else ngay)

    # TÌNH TRẠNG HỌC TẬP (V-m): CÙNG biểu thức với cột của màn hình và tệp xuất
    # (`teaching/tinh_trang.py`). Mã lạ → không ai khớp (cùng luật mã lớp sai).
    tth = (params.get('tinh_trang_hoc') or '').strip()
    if tth:
        if tth in NHAN_TINH_TRANG_HOC:
            where.append('(' + sql_tinh_trang_hoc('u') + ') = %s')
            args.append(tth)
        else:
            where.append('FALSE')
    # TÌNH TRẠNG HỌC PHÍ (V-m, §69a): một mã của CHECK, hoặc "chưa đặt" (NULL).
    hp = (params.get('hoc_phi') or '').strip()
    if hp:
        if hp == HOC_PHI_CHUA_DAT:
            where.append(vocab.chi_hoc_vien('u'))
            where.append('u.tuition_status IS NULL')
        elif hp in MA_HOC_PHI:
            where.append('u.tuition_status = %s')
            args.append(hp)
        else:
            where.append('FALSE')

    return ' AND '.join(where), args


def _them_cua_trang(rows):
    """Lớp đang học, hoạt động cuối và tiến độ cho MỘT TRANG → ``{uid: {...}}``.

    Đây là chỗ dễ hỏng nhất của cả màn hình: viết vòng lặp gọi từng em là 25
    lần đi-về mạng cho một lần mở trang (6 giây khi phát triển), và tệ hơn — số
    lần đó tăng theo per_page, nên khi chạy thật lỗi ẩn mình cho tới lúc trung
    tâm đông lên rồi mới lộ. Ở đây TỐI ĐA BA câu bất kể trang có bao nhiêu em
    (``= ANY(%s)``): (1) lớp + hoạt động cho cả trang; (2) bài đã xong và (3) tổng
    bài theo môn — hai câu sau chỉ chạy khi trang có học viên đang mở môn.

    Lớp ĐANG HỌC = `truy_cap.LOP_DANG_HOC` (chưa rời, lớp chưa huỷ). Em đã chuyển lớp
    vẫn còn dòng trong class_members (để báo cáo kỳ cũ đọc được) nhưng không hiện ở đây.
    Tiến độ = bài đã xong / tổng bài của các môn em đang được mở QUA LỚP (`truy_cap.mon_mo`),
    tử và mẫu số là hai hàm của báo cáo lớp — cùng một cách đếm với màn Giảng dạy.
    """
    if not rows:
        return {}                          # trang rỗng: đừng tốn một vòng gọi
    nay = local_now()
    them = {r['id']: r for r in q(
        '''SELECT u.id, to_char(h.thay, 'YYYY-MM-DD') AS lan_cuoi,
                  %(hom_nay)s::date - h.thay::date AS so_ngay,
                  (SELECT COALESCE(json_agg(json_build_object(
                              'id', c.id, 'name', c.name, 'classType', c.class_type,
                              'courseId', c.course_id) ORDER BY c.name, c.id), '[]'::json)
                     FROM class_members m JOIN classes c ON c.id = m.class_id
                    WHERE m.user_id = u.id AND ''' + LOP_DANG_HOC + ''') AS lop
             FROM users u
             LEFT JOIN LATERAL (''' + sql_hoat_dong('u', '%(nay)s', cot=('thay',)) + ''') h ON TRUE
            WHERE u.id = ANY(%(ids)s)''',
        {'ids': [r['id'] for r in rows], 'nay': nay, 'hom_nay': nay.date()})}

    mon = {r['id']: mon_mo(l['courseId'] for l in them[r['id']]['lop'])
           for r in rows if r['role'] == ROLE_STUDENT}
    co_mon = [uid for uid, m in mon.items() if m]
    xong = _progress_by_user(co_mon) if co_mon else {}
    tong = tong_bai_theo_khoa() if co_mon else {}

    out = {}
    for r in rows:
        t = them[r['id']]
        m = mon.get(r['id'])
        out[r['id']] = {
            'lop': [{'id': l['id'], 'name': l['name'], 'classType': l['classType']} for l in t['lop']],
            'lan_cuoi': t['lan_cuoi'],
            # Kẹp 0: dấu `last_seen_at` do tiến trình khác ghi có thể nhanh hơn đồng hồ này
            # vài giây — "−0 ngày trước" không phải thứ để in.
            'so_ngay': None if t['so_ngay'] is None else max(0, t['so_ngay']),
            # Chưa mở môn nào (chưa xếp lớp, hay nhân sự) thì KHÔNG có tiến độ: "0/0"
            # hay "3/0" đều nói sai. None → màn hình vẽ "—".
            'tien_do': ({'xong': sum(xong.get(r['id'], {}).get(k, 0) for k in m),
                         'tong': sum(tong.get(k, 0) for k in m)} if m else None),
        }
    return out


# ── 1. Danh sách tài khoản ──────────────────────────────────────────────────

class AdminUsersView(APIView):
    """GET /api/admin/users — danh sách tài khoản có tìm, lọc và phân trang.

    Thay bản cũ trong ``teaching/views.py`` (cứng ``LIMIT 50``, chỉ tìm theo tên
    và email, không phân trang): với vài trăm học viên thì em thứ 51 trở đi
    KHÔNG có đường nào hiện ra, kể cả khi trợ giảng biết chắc em có tài khoản.

    Tham số: ``q`` (tên/email/sđt), ``role``, ``status``, ``class_id``,
    ``chua_xep_lop=1``, ``khong_hoat_dong=<N ngày>`` (1.4b), ``page``, ``per_page``
    (mặc định 25, trần 100).

    TỐI ĐA BỐN CÂU SQL bất kể trang có bao nhiêu em — xem "NGÂN SÁCH VÒNG GỌI" ở
    đầu module: một câu đếm-và-lấy-trang, rồi `_them_cua_trang` (tối đa ba câu cho
    toàn bộ id của trang đó). Có phép kiểm đếm câu với 2 và 12 em.

    Mỗi dòng (1.4b, ghi chú họp TopHSA "quản lý học sinh"): ``lopDangHoc``
    [{id, name, classType}], ``hoatDongCuoi`` ('YYYY-MM-DD' | None = chưa thấy vào),
    ``ngayKhongHoatDong`` (số ngày tới hôm nay | None), ``tienDo`` ({xong, tong} | None
    khi chưa mở môn nào — nhân sự luôn None). ``classes`` (tên lớp) giữ cho màn hình bản
    trước, nay cùng tập lớp với ``lopDangHoc``.
    """
    # Học vụ vào được từ 23/09/2026 — nhưng CHỈ thấy tài khoản HỌC VIÊN, lọc ở
    # MÁY CHỦ chứ không ở giao diện. Họ tạo và sửa hồ sơ học viên; danh sách nhân
    # sự không thuộc việc của họ, và một ô lọc vai ở trình duyệt thì ai cũng gỡ được.
    permission_classes = [IsAdminOrAcademic]

    def get(self, request):
        where, args = build_user_filters(request.query_params)
        chi_hoc_vien = not is_admin(request.user)
        if chi_hoc_vien:
            where += ' AND u.role = %s'
            args = list(args) + [ROLE_STUDENT]
        page, per_page, offset = _paging(request.query_params, 25, 100)

        total, rows = _page_with_total(
            '''SELECT u.id, u.name, u.email, u.phone, u.role, u.status,
                      u.must_change_password, u.password_changed_at, u.created_at,
                      u.student_code, u.username, u.tuition_status,
                      ''' + sql_tinh_trang_hoc('u') + ''' AS tinh_trang_hoc
                 FROM users u
                WHERE ''' + where,
            # Xếp theo tên chứ không theo id giảm dần: đây là danh sách để TRA
            # CỨU một em cụ thể, và người ta tra theo tên. Thứ tự phụ theo id để
            # hai em trùng tên không đảo chỗ giữa các lần tải — trang 2 mà đảo
            # thứ tự thì có em không bao giờ xuất hiện ở trang nào.
            "ORDER BY lower(coalesce(name, '')), id",
            args, per_page, offset)

        them = _them_cua_trang(rows)
        return Response({
            'users': [{
                'id': r['id'],
                'name': r['name'],
                'email': r['email'],
                'phone': r['phone'],
                'role': r['role'],
                'status': r['status'],
                'must_change_password': r['must_change_password'],
                'password_changed_at': r['password_changed_at'],
                'created_at': r['created_at'],
                'studentCode': r['student_code'],
                'username': r['username'],
                'classes': [l['name'] for l in them[r['id']]['lop']],
                'lopDangHoc': them[r['id']]['lop'],
                'hoatDongCuoi': them[r['id']]['lan_cuoi'],
                'ngayKhongHoatDong': them[r['id']]['so_ngay'],
                'tienDo': them[r['id']]['tien_do'],
                # V-m: tình trạng học tập TÍNH (None = nhân sự), học phí chọn tay (None = chưa đặt).
                'tinhTrangHoc': r['tinh_trang_hoc'],
                'hocPhi': r['tuition_status'],
            } for r in rows],
            'total': total,
            'page': page,
            'per_page': per_page,
            # Màn hình quản trị dựng ô chọn vai trò từ đây chứ không chép cứng
            # chuỗi 'Học viên' ở frontend — sai một dấu là tài khoản mất quyền
            # mà không báo lỗi gì. Học vụ chỉ nhận đúng một vai để chọn.
            'roles': [ROLE_STUDENT] if chi_hoc_vien else list(ASSIGNABLE_ROLES),
            'chiHocVien': chi_hoc_vien,
            # Mốc của ô "Không hoạt động ≥ N ngày" — CÙNG mốc với thẻ Tổng quan; màn
            # hình dựng ô chọn từ đây, không gõ lại 7/14/30.
            'nguongNgu': list(NGUONG_NGU),
            # V-m: nhãn hai ô lọc / cột mới — màn hình dựng từ đây, không gõ lại chữ.
            'tinhTrangHocOptions': [{'ma': m, 'nhan': n} for m, n in TINH_TRANG_HOC],
            'hocPhiOptions': [{'ma': m, 'nhan': n} for m, n in HOC_PHI],
        })


# ── 2. Nhập hàng loạt ───────────────────────────────────────────────────────

#: Ba dấu ngăn cột cùng được chấp nhận. TAB là cái quan trọng nhất: trợ giảng
#: bôi đen mấy cột trong Excel/Google Sheets rồi dán thẳng thì cột ngăn nhau
#: bằng TAB, không phải dấu phẩy. Chỉ nhận dấu phẩy là đẩy trợ giảng vào việc
#: định dạng lại tay 200 dòng — và đó chính là việc mà endpoint này sinh ra để
#: khỏi phải làm.
_SPLIT_COLUMNS = re.compile(r'[\t;,]')

#: Hình dạng của một ô "trông như số điện thoại": chỉ chữ số và dấu ngăn người
#: ta hay chèn khi chép tay, có thể có ``+`` đứng đầu.
_PHONE_SHAPED = re.compile(r'\+?[\d\s.\-()]+')

#: Dấu hiệu dòng đầu là dòng TIÊU ĐỀ chứ không phải một học viên. Dán từ bảng
#: tính thì gần như luôn dính theo dòng này; không bỏ nó ra thì mẻ nào cũng có
#: một dòng hỏng và trợ giảng tưởng công cụ bị lỗi.
_HEADER_WORDS = ('email', 'e-mail', 'họ tên', 'họ và tên', 'ho ten', 'hovaten')


def _looks_like_phone(value):
    """Ô này là số điện thoại chứ không phải tên?

    Đếm chữ số thay vì bắt đúng khuôn số Việt Nam: ở đây mới chỉ cần PHÂN LOẠI
    xem ô nào là số, còn số đúng hay sai đã có ``validate_phone_field`` phán ở
    bước sau. Nhận diện chặt tay ngay từ đây thì một số viết sai sẽ bị coi là
    TÊN, và dòng đó báo lỗi "thiếu họ tên" — một lời nhắn dẫn trợ giảng đi sai
    hướng hoàn toàn.
    """
    if not value:
        return False
    digits = sum(1 for ch in value if ch.isdigit())
    return digits >= 8 and _PHONE_SHAPED.fullmatch(value) is not None


def _split_line(line):
    """Tách một dòng thành (họ tên, email, sđt) THEO NỘI DUNG, không theo vị trí.

    Đọc theo nội dung vì thứ tự cột ngoài đời không cố định: có tệp đăng ký để
    số điện thoại trước email, có tệp chỉ có tên với số. Đọc theo vị trí thì
    dòng ``Nguyễn Văn A, 0912345678`` bị hiểu thành "email = 0912345678" và
    trượt — trong khi đó lại đúng là dạng phổ biến nhất ở TopHSA, vì nhiều em
    lớp 12 chưa có email.
    """
    name, email, phone, rest = None, None, None, []
    for part in (p.strip() for p in _SPLIT_COLUMNS.split(line)):
        if not part:
            continue
        if email is None and looks_like_email(part):
            email = part
        elif phone is None and _looks_like_phone(part):
            phone = part
        else:
            rest.append(part)

    if rest:
        name = rest[0]
        for extra in rest[1:]:
            # Ô chỉ gồm chữ số và dấu ngăn nhưng KHÔNG đủ dài để là số điện
            # thoại ('090', '091234') vẫn phải nhận là số điện thoại — nhận rồi
            # để bước kiểm tra bên dưới báo "số điện thoại phải có 10 số".
            #
            # Nếu bỏ qua ô đó thì dòng vẫn tạo được (nhờ email) nhưng học viên
            # mất số điện thoại MÀ KHÔNG AI ĐƯỢC BÁO — trung tâm gọi cho phụ
            # huynh mới phát hiện, và lúc đó không còn biết số gốc là gì. Báo
            # sai còn sửa được ngay ở bước xem trước; mất im lặng thì không.
            if phone is None and _PHONE_SHAPED.fullmatch(extra):
                phone = extra
                break
    return name, email, phone


def _parse_text(text):
    """Văn bản dán vào → danh sách ứng viên ``{line, name, email, phone}``.

    Trả (danh_sách, bị_cắt_bớt, có_bỏ_dòng_tiêu_đề). ``line`` là số dòng trong ĐÚNG văn bản trợ
    giảng vừa dán (đếm từ 1, kể cả dòng trống và dòng tiêu đề). Đánh số lại theo
    thứ tự sau khi lọc thì báo "dòng 7 hỏng" chỉ vào một dòng khác trên màn hình
    của trợ giảng, và em ấy sẽ sửa nhầm dòng.
    """
    out, header_checked, truncated, header_skipped = [], False, False, False
    for idx, raw in enumerate((text or '').splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if not header_checked:
            header_checked = True
            low = line.lower()
            if any(word in low for word in _HEADER_WORDS):
                header_skipped = True
                continue
        if len(out) >= MAX_PARSE_LINES:
            # Cắt bớt thì phải NÓI ra. Lặng lẽ bỏ 200 dòng cuối là kịch bản tệ
            # nhất: trợ giảng thấy "đã cấp xong", đóng cửa sổ, và 200 em cuối
            # danh sách không có tài khoản mà không ai biết.
            truncated = True
            break
        name, email, phone = _split_line(line)
        out.append({'line': idx, 'name': name, 'email': email, 'phone': phone})
    return out, truncated, header_skipped


def _existing_identities(emails, phones):
    """Tra MỘT câu xem email/sđt nào đã có chủ → (theo_email, theo_sđt).

    Một câu cho cả mẻ chứ không hai câu mỗi dòng. 200 dòng × 2 câu là 400 lần
    đi-về mạng: 98 giây khi phát triển (worker đã bị gunicorn giết từ lâu), và
    dù chạy thật chỉ mất ~2 giây thì đó vẫn là 2 giây trả cho một việc mà một
    câu duy nhất làm xong — cái giá đó tăng thẳng theo số học viên mỗi khoá.
    """
    if not emails and not phones:
        return {}, {}
    rows = q('''SELECT id, name, email, phone FROM users
                 WHERE (email IS NOT NULL AND lower(email) = ANY(%s::text[]))
                    OR (phone IS NOT NULL AND phone <> '' AND phone = ANY(%s::text[]))''',
             (list(emails), list(phones)))
    by_email = {norm_email(r['email']): r for r in rows if r['email']}
    by_phone = {r['phone']: r for r in rows if r['phone']}
    return by_email, by_phone


def _check_row(cand, by_email, by_phone, seen_email, seen_phone):
    """Một dòng có tạo được không? Trả (name, email, phone, lý_do_trượt|None).

    Kiểm ĐỦ mọi lý do trượt TRƯỚC khi ghi bất cứ gì, vì hai lẽ. Một: dòng hỏng
    không được làm hỏng cả mẻ — trợ giảng đang có 200 em đứng đợi. Hai: trùng
    ngay trong chính danh sách vừa dán là lỗi hay gặp nhất (ghép hai tệp đăng
    ký của hai ca học), và nếu không bắt ở đây thì chỉ mục duy nhất
    ``idx_users_email_lower`` sẽ ném lỗi ở giữa mẻ — mà lúc đó một nửa số tài
    khoản đã tạo rồi, không có nút hoàn tác.
    """
    name = (cand['name'] or '').strip()
    email = norm_email(cand['email'])
    phone = norm_phone(cand['phone'])

    if not name:
        return name, email, phone, 'Thiếu họ tên.'
    err = validate_name_field(name)
    if err:
        return name, email, phone, err
    if name[:1] in KY_TU_CONG_THUC:
        # Họ tên thật không mở đầu bằng = + - @; một ô như thế là CÔNG THỨC dán từ bảng
        # tính (`=HYPERLINK(...)`) — để lọt thì nó thành công thức trong mọi bản xuất Excel
        # sau này của người khác (V-j, 25/09/2026: dùng chung cho ô dán và tệp mẫu).
        return name, email, phone, ('Họ tên không được bắt đầu bằng dấu %s — ô này trông như '
                                    'công thức bảng tính. Gõ lại họ tên.' % name[:1])
    if not email and not phone:
        return name, email, phone, 'Cần ít nhất email hoặc số điện thoại.'
    if email:
        err = validate_email_field(email)
        if err:
            return name, email, phone, err
    if phone:
        # Chuẩn hoá TRƯỚC khi kiểm: '+84 912 345 678' không lọt khuôn nào của
        # validate_phone_field, nhưng sau norm_phone thành '0912345678' thì hợp
        # lệ — và đó mới là con số sẽ nằm trong CSDL.
        err = validate_phone_field(phone)
        if err:
            return name, email, phone, err

    if email and email in seen_email:
        return name, email, phone, ('Trùng email với dòng %d trong danh sách vừa dán.'
                                    % seen_email[email])
    if phone and phone in seen_phone:
        return name, email, phone, ('Trùng số điện thoại với dòng %d trong danh sách vừa dán.'
                                    % seen_phone[phone])
    if email and email in by_email:
        return name, email, phone, ('Email này đã là tài khoản của "%s".'
                                    % _user_label(by_email[email]))
    if phone and phone in by_phone:
        return name, email, phone, ('Số điện thoại này đã là tài khoản của "%s".'
                                    % _user_label(by_phone[phone]))
    return name, email, phone, None


def _cham_tung_dong(cands, by_email, by_phone, dry_run, truncated):
    """Chấm điểm từng dòng, CHƯA GHI GÌ → ``(rows, to_create, skipped, warnings,
    too_many)``.

    Tách khỏi `AdminBulkCreateUsersView.post` (T24, 01/09/2026) vì đây là phần
    THUẦN của một hàm 180 dòng, và cũng là chỗ đã đẻ ra lỗi đắt nhất của cả khối:
    câu kiểm TRẦN từng nằm SAU nhánh `if dry_run`, nên trợ giảng dán 60 dòng,
    bấm "Kiểm tra trước", màn hình báo "sẽ tạo 60 tài khoản", bấm "Tạo" — rồi
    mới nhận lời từ chối. Bất ngờ rơi đúng vào bước mà bản xem trước sinh ra để
    bảo vệ.

    Thứ tự ấy giờ nằm trong một hàm thuần, gọi được thẳng từ phép kiểm mà không
    phải dựng cả một request.
    """
    seen_email, seen_phone = {}, {}
    rows, to_create = [], []
    for cand in cands:
        name, email, phone, reason = _check_row(cand, by_email, by_phone,
                                                seen_email, seen_phone)
        entry = {'line': cand['line'], 'name': name or None,
                 'email': email, 'phone': phone}
        if reason:
            rows.append(dict(entry, status='skipped', reason=reason))
            continue
        if email:
            seen_email[email] = cand['line']
        if phone:
            seen_phone[phone] = cand['line']
        rows.append(dict(entry, status='created',
                         reason='Hợp lệ — sẽ cấp tài khoản.' if dry_run else None))
        to_create.append((rows[-1], name, email, phone))

    skipped = sum(1 for r in rows if r['status'] == 'skipped')
    warnings = []
    if truncated:
        warnings.append('Danh sách dài hơn %d dòng nên phần còn lại CHƯA được đọc. '
                        'Dán nốt phần sau ở lần tiếp theo.' % MAX_PARSE_LINES)

    # Trần tính Ở ĐÂY, tức TRƯỚC mọi nhánh trả lời — xem docstring.
    too_many = len(to_create) > MAX_CREATE_PER_BATCH
    if too_many:
        warnings.append(
            'Danh sách có %d dòng hợp lệ, vượt trần %d mỗi lần. Giữ lại %d dòng '
            'đầu rồi dán phần còn lại ở mẻ sau.'
            % (len(to_create), MAX_CREATE_PER_BATCH, MAX_CREATE_PER_BATCH))
    return rows, to_create, skipped, warnings, too_many


def cho_trong_gia_su(class_id):
    """Số chỗ HỌC VIÊN còn trống của một lớp gia sư (`TRAN_GIA_SU` trừ em đang học). Có thể âm."""
    return vocab.TRAN_GIA_SU - q1(
        'SELECT count(*) AS n FROM class_members m JOIN users mu ON mu.id = m.user_id '
        'WHERE m.class_id = %s AND m.left_at IS NULL AND ' + vocab.chi_hoc_vien('mu'), (class_id,))['n']


def cap_tai_khoan(request, to_create, role, klass, vao, nguon='nhập hàng loạt'):
    """CẤP tài khoản cho các dòng đã chấm hợp lệ, rồi (nếu có lớp) xếp cả mẻ vào lớp.

    MỘT hàm cho HAI cửa (V-j, 25/09/2026): ô dán ở trang Tài khoản
    (`AdminBulkCreateUsersView`) và nhập học viên từ tệp mẫu (`teaching/nhap_hoc_vien.py`).
    Hai bản vòng ghi là hai chỗ sẽ trôi — mật khẩu tạm, mã HSA, nhật ký, trần gia sư dưới
    khoá đều nằm ở đây.

    ``to_create`` = ``[(entry, name, email, phone), …]`` từ bước chấm (CHƯA ghi gì); mỗi
    ``entry`` được ghi thêm ``userId``, ``studentCode``, ``tempPassword`` — hoặc đổi thành
    ``skipped`` khi vấp chỉ mục duy nhất. ``klass`` = dòng lớp (id, name, class_type) hoặc
    None. Trần mỗi mẻ (`MAX_CREATE_PER_BATCH`) do NƠI GỌI kiểm trước.

    Trả ``(created_ids, added_to_class, warnings)``.
    """
    from accounts.hashers import make_werkzeug_password
    from teaching.ho_so import cap_ma_hoc_vien

    class_id = klass['id'] if klass else None
    warnings = []
    created_ids = []
    now = local_now()
    for entry, name, email, phone in to_create:
        temp = _temp_password()
        try:
            # Giao dịch riêng từng dòng: dòng thứ 30 vấp chỉ mục duy nhất
            # (ai đó vừa tạo cùng email ở tab khác) chỉ cuộn lại đúng dòng
            # đó — 29 tài khoản trước vẫn còn, và mật khẩu tạm của chúng vẫn
            # nằm trong phản hồi. Bọc chung một giao dịch thì một va chạm
            # xoá sạch công của cả mẻ.
            with transaction.atomic():
                row = q1('INSERT INTO users (name, email, phone, role, password, '
                         'must_change_password, created_at) '
                         'VALUES (%s, %s, %s, %s, %s, TRUE, %s) RETURNING id',
                         (name, email, phone, role,
                          make_werkzeug_password(temp), now))
        except IntegrityError:
            entry['status'] = 'skipped'
            entry['reason'] = ('Email hoặc số điện thoại vừa bị tài khoản khác '
                               'chiếm mất trong lúc đang tạo. Kiểm tra lại rồi '
                               'dán riêng dòng này.')
            continue

        uid = row['id']
        created_ids.append(uid)
        entry['userId'] = uid
        entry['studentCode'] = cap_ma_hoc_vien(uid)
        entry['tempPassword'] = temp

        audit.record(
            request, audit.USER_CREATE, target_type='user', target_id=uid,
            target_label=name,
            summary=('Cấp tài khoản "%s" (%s) bằng %s%s.'
                     % (name, role, nguon, ' — xếp vào lớp "%s"' % klass['name'] if klass else '')),
            # KHÔNG có mật khẩu tạm ở đây và không bao giờ được có: nhật ký
            # kiểm toán đọc được bởi mọi quản trị viên và giữ vĩnh viễn.
            detail={'bulk': True, 'line': entry['line'], 'email': email,
                    'phone': phone, 'role': role, 'classId': class_id})

    # Xếp lớp bằng MỘT câu cho cả mẻ thay vì một câu mỗi em: 50 em là 50 vòng
    # gọi = 12 giây, đủ để đẩy request qua mốc timeout. Đặt sau vòng ghi và
    # ngoài các giao dịch riêng là có chủ ý — xếp lớp hỏng thì tài khoản vẫn
    # còn (thêm vào lớp lại được bất cứ lúc nào), còn tài khoản hỏng thì
    # không có gì để xếp.
    added_to_class = False
    if class_id and created_ids:
        xep = created_ids
        with transaction.atomic():
            if klass.get('class_type') == 'gia_su' and role == ROLE_STUDENT:
                # Đếm lại DƯỚI KHOÁ (§54): phép kiểm chỗ ở trên chạy TRƯỚC vòng cấp
                # tài khoản — một em được thêm vào lớp trong lúc ấy (tab khác) thì
                # giờ còn ít chỗ hơn. Tài khoản đã cấp vẫn giữ; em thừa được nêu tên.
                q1('SELECT id FROM classes WHERE id=%s FOR UPDATE', (class_id,))
                con_cho = max(cho_trong_gia_su(class_id), 0)
                if len(xep) > con_cho:
                    thua = [e['email'] for e, *_ in to_create if e.get('userId') in set(xep[con_cho:])]
                    warnings.append('Lớp gia sư "%s" vừa hết chỗ trong lúc cấp tài khoản — %d em đã có '
                                    'tài khoản nhưng chưa vào lớp: %s. Xếp các em vào lớp khác.'
                                    % (klass['name'], len(thua), ', '.join(thua)))
                    xep = xep[:con_cho]
            # `WHERE left_at IS NULL` trỏ đúng chỉ mục duy nhất một phần của
            # §36 (thiếu nó Postgres từ chối cả câu). Kèm theo là đổi hành vi có
            # chủ đích: người ĐÃ RỜI lớp mà được nhập lại sẽ sinh một dòng MỚI —
            # một lượt học mới — thay vì hồi sinh dòng cũ và xoá trắng mốc rời
            # lớp lần trước.
            if xep:
                x('''INSERT INTO class_members (class_id, user_id, joined_at)
                     SELECT %s, uid, %s FROM unnest(%s::int[]) AS uid
                     ON CONFLICT (class_id, user_id) WHERE left_at IS NULL DO NOTHING''',
                  (class_id, vao or now, xep))
                added_to_class = True
    return created_ids, added_to_class, warnings


class AdminBulkCreateUsersView(APIView):
    """POST /api/admin/users/bulk — cấp tài khoản cho cả một danh sách.

    Đây là lý do chính của cả khối quản lý tài khoản. Luồng thật ở TopHSA: học
    viên đăng ký học và để lại email/số điện thoại, trợ giảng có sẵn một tệp
    danh sách và cần cấp tài khoản cho cả lớp trước buổi đầu. Cấp từng em một
    cho 200 em thì không ai làm nổi, và bản thân việc phải làm 200 lần là nguồn
    sinh lỗi lớn hơn mọi lỗi nhập liệu.

    Thân yêu cầu: ``{text, role, class_id, dry_run}``. Mỗi dòng của ``text`` là
    ``Họ tên, email, số điện thoại`` ngăn nhau bằng dấu phẩy, chấm phẩy HOẶC
    tab; email và sđt đều tuỳ chọn nhưng phải có ít nhất một.

    ``dry_run`` KHÔNG phải tuỳ chọn cho đẹp mà là phần bắt buộc của quy trình:
    tạo nhầm rồi thì KHÔNG có nút hoàn tác (tài khoản đã sinh mật khẩu tạm, đã
    chiếm email trong chỉ mục duy nhất), nên trợ giảng phải xem được 200 dòng
    hỏng chỗ nào TRƯỚC khi ghi. Xem trước chỉ tốn đúng một câu SQL nên rẻ gần
    như bằng không.

    TRẦN 50 TÀI KHOẢN MỖI LẦN (``MAX_CREATE_PER_BATCH``) — con số tính ra, không
    chọn cho tròn, và thứ quyết định KHÔNG phải cơ sở dữ liệu. Đo 30/08/2026:
    ``make_werkzeug_password`` (scrypt, n=32768) tốn **126ms CPU cho MỖI mật
    khẩu**, và đó là thiết kế của scrypt chứ không phải chỗ tối ưu được — bằm
    chậm chính là cái làm mật khẩu khó dò. Cộng lại: 200 em là ~25 giây CPU
    thuần chỉ để bằm mật khẩu, trên máy phát triển; Render dùng CPU chia sẻ nên
    còn chậm hơn, mà gunicorn chạy với ``--timeout 60`` (startCommand của
    ``render.yaml``; chú thích này từng ghi 30 giây theo ``gunicorn.conf.py`` — số
    ấy bị dòng lệnh đè từ trước, tệp đã xoá 24/09/2026). Giữ mốc 30 giây dưới đây
    làm ngân sách thiết kế, dư một nửa. Phần
    ghi CSDL ngược lại rẻ (2 câu mỗi em × <5ms khi chạy thật), nên đừng đi tối ưu
    số câu SQL ở đây mà tưởng giải quyết được vấn đề.

    50 em ≈ 6 giây CPU khi phát triển, ước chừng 12–15 giây trên Render — còn dư
    địa thật dưới mốc 30 giây. Vượt trần thì TỪ CHỐI THẲNG chứ không thử rồi để
    worker bị giết giữa chừng: bị giết là kịch bản tệ nhất trong tất cả — một
    phần tài khoản đã tạo, phản hồi không bao giờ về, nên danh sách mật khẩu tạm
    mất trắng và KHÔNG em nào trong số đó đăng nhập được, trong khi email của
    các em thì đã bị chiếm chỗ nên dán lại cũng không tạo lại được.
    """
    # Học vụ nhập được — CHỈ vai Học viên (anh Sơn chốt 23/09/2026). Chính
    # docstring trên mô tả luồng "trợ giảng có sẵn tệp danh sách, cần cấp tài
    # khoản cho cả lớp trước buổi đầu" — mà cho tới hôm ấy cả trợ giảng lẫn học vụ
    # đều không chạm được vào tuyến này.
    permission_classes = [IsAdminOrAcademic]

    def post(self, request):
        body = request.data if isinstance(request.data, dict) else {}
        text = body.get('text') or ''
        role = (body.get('role') or ROLE_STUDENT).strip()
        dry_run = bool(body.get('dry_run'))
        class_id = body.get('class_id')

        if not is_admin(request.user) and role != ROLE_STUDENT:
            return Response({'error': 'Quản lý học vụ chỉ cấp được tài khoản HỌC VIÊN. '
                                      'Tài khoản nhân sự cần quản trị viên.'}, status=403)
        if role not in ASSIGNABLE_ROLES:
            return Response({'error': 'Vai trò phải là một trong: %s.'
                                      % ', '.join(ASSIGNABLE_ROLES)}, status=400)

        # Kiểm lớp MỘT lần ở đây, không kiểm theo từng dòng. Xếp lớp được gộp
        # thành một câu ghi ở cuối (xem dưới), nên một class_id sai sẽ làm hỏng
        # câu đó SAU khi cả mẻ tài khoản đã tạo xong — chặn trước là rẻ nhất.
        klass = None
        if class_id not in (None, '', 0):
            try:
                class_id = int(class_id)
            except (TypeError, ValueError):
                return Response({'error': 'Mã lớp không hợp lệ.'}, status=400)
            klass = q1('SELECT id, name, class_type FROM classes WHERE id=%s', (class_id,))
            if not klass:
                return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        else:
            class_id = None
        # Ngày vào lớp THẬT cho cả mẻ (20/09/2026): lớp đã khai giảng mà các em
        # đang học dở thì `joined_at = hôm nay` là ngày sai — xem
        # `AdminClassMembersView` cùng lý do. Một ngày cho cả mẻ: người dán một
        # bảng là dán một đợt cùng vào lớp; em vào lẻ thì đi đường Lớp học.
        vao, loi_ngay = _doc_ngay_vao_lop(body.get('joined_at'))
        if loi_ngay:
            return Response({'error': loi_ngay}, status=400)

        cands, truncated, header_skipped = _parse_text(text)
        if not cands:
            return Response({'error': 'Không đọc được dòng dữ liệu nào. Mỗi dòng cần '
                                      'có họ tên kèm email hoặc số điện thoại.'}, status=400)

        by_email, by_phone = _existing_identities(
            {norm_email(c['email']) for c in cands if norm_email(c['email'])},
            {norm_phone(c['phone']) for c in cands if norm_phone(c['phone'])})

        rows, to_create, skipped, warnings, too_many = _cham_tung_dong(
            cands, by_email, by_phone, dry_run, truncated)

        # Lớp GIA SƯ tối đa 3 học viên (§54, 24/09/2026) — lượt cấp hàng loạt xếp
        # cả mẻ bằng MỘT câu ở dưới, nên phải kiểm chỗ trống TRƯỚC: xem trước thì
        # cảnh báo, tạo thật thì từ chối trước khi cấp tài khoản nào.
        if klass and klass.get('class_type') == 'gia_su' and role == ROLE_STUDENT and to_create:
            con_cho = cho_trong_gia_su(class_id)
            if len(to_create) > con_cho:
                cau = ('Lớp gia sư "%s" chỉ còn %d chỗ (tối đa %d em) — danh sách có %d em mới. '
                       'Chọn lớp khác hoặc bỏ ô lớp.' % (klass['name'], max(con_cho, 0), vocab.TRAN_GIA_SU,
                                                         len(to_create)))
                if not dry_run:
                    return Response({'ok': False, 'error': cau}, status=400)
                warnings.append(cau)

        if dry_run:
            # Không một lệnh ghi nào chạy tới đây. Tổng cộng đúng 1–2 câu SQL cho
            # cả mẻ, nên trợ giảng bấm xem trước bao nhiêu lần cũng được.
            return Response({'ok': True, 'dryRun': True,
                             'created': len(to_create), 'skipped': skipped,
                             # Số dòng MÁY CHỦ đọc được, và có bỏ dòng tiêu đề
                             # hay không. Thiếu hai con số này thì màn hình phải
                             # tự đếm lấy, và nó đếm khác — nó tính cả dòng tiêu
                             # đề. Đo được: "8 dòng đã dán" rồi "sẽ tạo 2, bỏ
                             # qua 5", mà 2+5≠8, không ai giải thích nổi vì sao.
                             'parsedLines': len(rows),
                             'headerSkipped': header_skipped,
                             'tooMany': too_many, 'maxPerBatch': MAX_CREATE_PER_BATCH,
                             'warnings': warnings, 'rows': rows})

        if too_many:
            return Response({
                'ok': False,
                'error': ('Một lần chỉ cấp được %d tài khoản, danh sách này có %d dòng '
                          'hợp lệ. Sinh mật khẩu cho mỗi em tốn hơn một phần mười giây, '
                          'quá số đó là máy chủ cắt ngang giữa chừng và danh sách mật '
                          'khẩu tạm sẽ mất trong khi tài khoản thì đã tạo dở. Chia ra '
                          'dán làm nhiều lần — phần kiểm tra trước (dry_run) vẫn xem '
                          'được cả danh sách trong một lượt.'
                          % (MAX_CREATE_PER_BATCH, len(to_create))),
                'created': 0, 'skipped': skipped, 'wouldCreate': len(to_create),
                'parsedLines': len(rows), 'headerSkipped': header_skipped,
                'warnings': warnings, 'rows': rows,
            }, status=400)

        # ── Vòng 2: ghi — `cap_tai_khoan` (dùng CHUNG với nhập từ tệp mẫu, V-j) ──
        created_ids, added_to_class, canh_bao = cap_tai_khoan(request, to_create, role, klass, vao)
        warnings += canh_bao

        return Response({
            'ok': True,
            'dryRun': False,
            'created': len(created_ids),
            'skipped': sum(1 for r in rows if r['status'] == 'skipped'),
            'parsedLines': len(rows), 'headerSkipped': header_skipped,
            'addedToClass': added_to_class,
            'className': klass['name'] if klass else None,
            'warnings': warnings,
            'rows': rows,
            'note': 'Mật khẩu tạm chỉ hiện MỘT lần ở đây — máy chủ không lưu lại dạng '
                    'đọc được. Chép ra trước khi đóng cửa sổ; quên thì phải đặt lại.',
        }, status=201)


# ── 3. Vòng đời tài khoản ───────────────────────────────────────────────────

class AdminUserStatusView(APIView):
    """POST /api/admin/users/<id>/status {status, note} — khoá / mở tài khoản.

    Anh chủ sản phẩm chốt 30/08/2026: học viên nghỉ hoặc học xong thì KHOÁ ĐĂNG
    NHẬP nhưng GIỮ NGUYÊN dữ liệu học. Xoá tài khoản là mất luôn tiến độ, điểm
    thi thử và mọi báo cáo của kỳ đó — mà trung tâm cần đọc lại chính những báo
    cáo ấy để biết khoá vừa rồi dạy có hiệu quả không.

    Khoá có hiệu lực NGAY, kể cả với token đã cấp trước đó: chốt chặn nằm ở
    ``accounts.models.User.is_active`` mà SimpleJWT gọi ở mọi lời gọi API. Ở đây
    chỉ cần đổi cột ``status``, không phải đi thu hồi token.

    ``note`` là lý do khoá, và nên coi là bắt buộc trên giao diện: vài tháng sau
    trung tâm mở lại tài khoản mà không có dòng này thì không ai nhớ nổi vì sao
    nó bị khoá.
    """
    permission_classes = [IsAdminRole]

    def post(self, request, user_id):
        body = request.data if isinstance(request.data, dict) else {}
        status = (body.get('status') or '').strip()
        if status not in USER_STATUSES:
            return Response({'error': 'Trạng thái phải là một trong: %s.'
                                      % ', '.join(USER_STATUSES)}, status=400)

        target = q1('SELECT id, name, email, role, status FROM users WHERE id=%s',
                    (user_id,))
        if not target:
            return Response({'error': 'Không có tài khoản này.'}, status=404)

        if int(user_id) == request.user.id and status != 'active':
            # Cùng lý do với chốt chặn tự-hạ-quyền ở AdminUserRoleView, nhưng
            # hậu quả nặng hơn: hạ quyền mình còn nhờ quản trị viên khác nâng
            # lại, KHOÁ mình là mất cả đường đăng nhập. Nếu đây lại là quản trị
            # viên duy nhất thì không còn ai mở được cho ai, và cách duy nhất
            # vào lại là sửa tay trong CSDL.
            return Response({'error': 'Không tự khoá tài khoản của chính mình được. '
                                      'Nhờ một quản trị viên khác làm việc này.'},
                            status=400)

        # Câu trên chỉ chặn tự khoá MÌNH. Hai quản trị viên khoá LẪN NHAU thì cả
        # hai lần gọi đều lọt và hệ thống về không quản trị viên — xem chú thích
        # dài ở `common.permissions.last_active_admin`.
        if status != 'active' and target['role'] == ROLE_ADMIN and last_active_admin(user_id):
            return Response({'error': 'Đây là quản trị viên đang hoạt động cuối cùng. '
                                      'Phong quyền cho một người khác trước đã.'},
                            status=400)

        note = (body.get('note') or '').strip()[:500] or None
        ten = _user_label(target, user_id)

        # Giảng viên bị khoá thì lớp em ấy phụ trách mất người đứng lớp, mà
        # classes.teacher_id vẫn trỏ tới một tài khoản không đăng nhập được —
        # nhìn vào danh sách lớp không thấy gì bất thường. Phải nói ra ngay tại
        # thao tác này, chứ đợi tới buổi học mới phát hiện là quá muộn.
        orphaned = []
        if status != 'active':
            orphaned = q('SELECT id, code, name FROM classes WHERE teacher_id=%s '
                         'ORDER BY name', (user_id,))

        x('UPDATE users SET status=%s, status_changed_at=%s, status_note=%s WHERE id=%s',
          (status, local_now(), note, user_id))

        verb = 'Mở lại' if status == 'active' else 'Khoá'
        summary = '%s tài khoản "%s"%s' % (verb, ten, ' — %s' % note if note else '.')
        audit.record(request, audit.USER_STATUS, target_type='user', target_id=user_id,
                     target_label=ten, summary=summary,
                     detail={'from': target['status'], 'to': status, 'note': note,
                             'role': target['role'],
                             'orphanedClasses': [c['id'] for c in orphaned]})

        warnings = ['Lớp "%s" đang do tài khoản này phụ trách — khoá xong lớp sẽ không '
                    'còn giảng viên. Gán người khác trước khi tới buổi kế tiếp.' % c['name']
                    for c in orphaned]
        return Response({
            'ok': True,
            'userId': target['id'],
            'name': target['name'],
            'status': status,
            'warnings': warnings,
            'orphanedClasses': [dict(c) for c in orphaned],
            'note': ('Tài khoản bị chặn ngay ở lời gọi API kế tiếp, kể cả khi em đang '
                     'mở sẵn ứng dụng. Dữ liệu học giữ nguyên, mở lại là dùng tiếp.'
                     if status != 'active' else
                     'Tài khoản đăng nhập lại được ngay, không cần đặt lại mật khẩu.'),
        })


# ── 5. Nhật ký kiểm toán ────────────────────────────────────────────────────

class AdminAuditView(APIView):
    """GET /api/admin/audit — đọc nhật ký hành động quản trị.

    Bảng ``admin_audit`` chỉ ghi chứ chưa có đường đọc; nhật ký không đọc được
    thì bằng không. Câu hỏi thật mà màn hình này phải trả lời: "ai khoá tài
    khoản em này", "hôm 28/8 ai đặt lại mật khẩu cho ai", "trợ giảng mới vào
    tuần trước đã làm những gì".

    Tham số: ``action``, ``actor_id``, ``target_type``, ``target_id``, ``from``,
    ``to`` (YYYY-MM-DD, ``to`` tính CẢ ngày đó), ``page``, ``per_page`` (mặc
    định 50, trần 200). Đúng hai câu SQL.
    """
    permission_classes = [IsAdminRole]

    def get(self, request):
        params = request.query_params
        where, args = ['TRUE'], []

        # Ba cột chữ, so khớp NGUYÊN VĂN: cả ba đều là giá trị chọn từ ô lọc
        # (danh sách `actions` trả về ở cuối hàm), không phải chuỗi người ta gõ
        # tay, nên tìm gần đúng ở đây chỉ làm kết quả nhiễu.
        for column in ('action', 'target_type', 'target_id'):
            val = (params.get(column) or '').strip()
            if val:
                where.append('%s = %%s' % column)
                args.append(val)

        actor_id = (params.get('actor_id') or '').strip()
        if actor_id:
            try:
                args.append(int(actor_id))
            except (TypeError, ValueError):
                return Response({'error': 'actor_id phải là một số.'}, status=400)
            where.append('actor_id = %s')

        for field, op in (('from', '>='), ('to', '<')):
            raw = (params.get(field) or '').strip()
            if not raw:
                continue
            day = as_date(raw)
            if not day:
                # Trả 400 chứ không lặng lẽ bỏ qua: gõ sai ngày mà vẫn nhận về
                # cả bảng thì người đọc kết luận "hôm đó không ai làm gì" —
                # đúng cái kết luận ngược với sự thật mà nhật ký sinh ra để chặn.
                return Response({'error': 'Ngày "%s" không hợp lệ (định dạng '
                                          'YYYY-MM-DD).' % field}, status=400)
            if field == 'to':
                # 'to' tính CẢ ngày đó: người ta gõ 30/08 là muốn xem hết ngày
                # 30, không phải tới 0h00 ngày 30 (khi đó cả ngày cuối biến mất).
                day = day + timedelta(days=1)
            where.append('occurred_at %s %%s' % op)
            args.append(day)

        page, per_page, offset = _paging(params, 50, 200)
        total, rows = _page_with_total(
            '''SELECT id, actor_id, actor_name, actor_role, action, target_type,
                      target_id, target_label, summary, detail, ip, occurred_at
                 FROM admin_audit
                WHERE ''' + ' AND '.join(where),
            # Mới nhất lên đầu, id phụ để hai dòng cùng mốc giây không đảo chỗ
            # giữa các trang. Khớp với idx_audit_time.
            'ORDER BY occurred_at DESC, id DESC',
            args, per_page, offset)

        return Response({
            'entries': rows,
            'total': total,
            'page': page,
            'per_page': per_page,
            # Danh sách để dựng ô lọc — lấy từ dữ liệu THẬT chứ không từ hằng số
            # trong common/audit.py: hằng số nói cái gì CÓ THỂ được ghi, còn ô
            # lọc chỉ nên hiện cái đã thực sự xảy ra ở trung tâm này.
            'actions': [r['action'] for r in
                        q('SELECT DISTINCT action FROM admin_audit ORDER BY action')],
        })
