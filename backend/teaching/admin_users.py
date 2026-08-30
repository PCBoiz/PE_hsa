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

from accounts.validators import (validate_email_field, validate_name_field,
                                 validate_phone_field)
from common import audit
from common.clock import local_now
from common.db import q, q1, x
from common.identity import looks_like_email, norm_email, norm_phone
from common.permissions import (ASSIGNABLE_ROLES, ROLE_ADMIN, ROLE_STUDENT,
                                IsAdminRole, last_active_admin)
from stats.goals import as_date
# Dùng lại của teaching/views.py, không viết bản thứ hai: mật khẩu tạm sinh hai
# kiểu khác nhau thì trợ giảng đọc cho học viên hai dạng chuỗi khác nhau, còn
# nhãn nhật ký dựng hai kiểu thì cùng một người hiện ra hai tên trong cùng một
# trang nhật ký. Chiều nhập một hướng: views.py KHÔNG được import ngược lại đây.
from teaching.views import _temp_password, _user_label

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
    """Đọc ``page``/``per_page`` từ query string → (page, per_page, offset).

    Tham số rác (``page=abc``, ``per_page=-3``, ``per_page=100000``) được kéo về
    khoảng hợp lệ chứ không trả 400: đây là tham số của thanh phân trang, người
    dùng không gõ tay: một liên kết cũ hay một lần sửa URL nhầm mà làm hỏng cả
    màn hình quản trị thì lỗi nằm ở phía ta.
    """
    def _num(name, fallback):
        try:
            return int(params.get(name) or fallback)
        except (TypeError, ValueError):
            return fallback

    page = max(1, _num('page', 1))
    per_page = max(1, min(max_per_page, _num('per_page', default_per_page)))
    return page, per_page, (page - 1) * per_page


def _like(term):
    """Bọc chuỗi tìm kiếm thành mẫu LIKE, VÔ HIỆU HOÁ ký tự đại diện.

    Không thoát ``%`` và ``_`` thì trợ giảng gõ một dấu ``%`` vào ô tìm kiếm sẽ
    nhận về TOÀN BỘ bảng users và tưởng là mình vừa tìm ra đúng người.
    """
    safe = term.replace('\\', '\\\\').replace('%', r'\%').replace('_', r'\_')
    return '%' + safe.lower() + '%'


def _page_with_total(body_sql, order_sql, args, per_page, offset):
    """MỘT câu SQL trả về CẢ tổng số dòng khớp LẪN đúng một trang.

    ``body_sql`` là câu SELECT đầy đủ (đã có WHERE) cho toàn bộ tập khớp; nó
    BẮT BUỘC phải chọn cột ``id`` — xem lý do ở cuối docstring. Trả (total, rows).

    Vì sao một câu chứ không hai: xem "NGÂN SÁCH VÒNG GỌI" ở đầu module. Đếm
    riêng rồi lấy trang riêng là nhân đôi một lần đi-về mạng ở MỌI lần bấm sang
    trang — 246ms khi phát triển, và vẫn là một chuyến đi thừa khi chạy thật.

    Vì sao không dùng ``COUNT(*) OVER ()`` gắn thẳng vào câu lấy trang — cách
    ngắn hơn và ai cũng nghĩ tới đầu tiên: nó không trả dòng NÀO khi trang rỗng,
    mà "trang rỗng" không đồng nghĩa với "không có kết quả". Bấm sang trang 9
    của danh sách 8 trang (hoặc lọc lại khi đang đứng ở trang cuối) là trang
    rỗng, tổng khi đó tụt về 0, thanh phân trang tự sập và người dùng kẹt lại
    không còn nút nào quay về trang 1. ``LEFT JOIN LATERAL`` luôn trả ít nhất
    một dòng — dòng tổng, mọi cột dữ liệu NULL — nên tổng không bao giờ mất.
    Dòng mồi đó nhận ra bằng ``id IS NULL``: id là khoá chính, dòng thật không
    bao giờ NULL.
    """
    sql = ('WITH khop AS (%s), tong AS (SELECT count(*) AS __total FROM khop) '
           'SELECT tong.__total, trang.* FROM tong '
           'LEFT JOIN LATERAL (SELECT * FROM khop %s LIMIT %%s OFFSET %%s) trang ON TRUE'
           % (body_sql, order_sql))
    rows = q(sql, tuple(args) + (per_page, offset))
    if not rows:
        return 0, []
    total = rows[0]['__total'] or 0
    out = []
    for row in rows:
        if row.get('id') is None:
            continue                      # dòng mồi của trang rỗng
        row = dict(row)
        row.pop('__total', None)
        out.append(row)
    return total, out


#: Các tham số lọc của màn hình tài khoản. Khai một chỗ để bộ lọc và câu hỏi
#: "người dùng có lọc gì không" không bao giờ lệch nhau.
USER_FILTER_PARAMS = ('q', 'role', 'status', 'class_id')


def any_user_filter(params) -> bool:
    """Người dùng có đặt bộ lọc nào không.

    Bản xuất CSV cần biết để đặt tên tệp: một tệp đủ và một tệp đã lọc nằm cạnh
    nhau trong thư mục Tải về mà không phân biệt được thì sớm muộn có người mang
    bản thiếu người đi họp.
    """
    return any((params.get(k) or '').strip() for k in USER_FILTER_PARAMS)


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
        where.append('(lower(u.name) LIKE %s OR lower(u.email) LIKE %s OR u.phone LIKE %s)')
        args += [_like(term), _like(term), _like(norm_phone(term) or term)]

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

    return ' AND '.join(where), args


def _classes_by_user(user_ids):
    """Tên các lớp ĐANG theo học, cho một loạt học viên, bằng ĐÚNG MỘT câu.

    Đây là chỗ dễ hỏng nhất của cả màn hình: viết vòng lặp gọi từng em là 25
    lần đi-về mạng cho một lần mở trang (6 giây khi phát triển), và tệ hơn — số
    lần đó tăng theo per_page, nên khi chạy thật lỗi ẩn mình cho tới lúc trung
    tâm đông lên rồi mới lộ. ``= ANY(%s)`` giữ đúng một câu bất kể trang có bao
    nhiêu em.

    ``left_at IS NULL`` = đang trong lớp. Em đã chuyển lớp vẫn còn dòng trong
    class_members (để báo cáo kỳ cũ đọc được) nhưng không được hiện ở đây nữa.
    """
    if not user_ids:
        return {}                          # trang rỗng: đừng tốn một vòng gọi
    out = {}
    for row in q('''SELECT cm.user_id, c.name
                      FROM class_members cm
                      JOIN classes c ON c.id = cm.class_id
                     WHERE cm.user_id = ANY(%s) AND cm.left_at IS NULL
                     ORDER BY c.name''', (list(user_ids),)):
        out.setdefault(row['user_id'], []).append(row['name'])
    return out


# ── 1. Danh sách tài khoản ──────────────────────────────────────────────────

class AdminUsersView(APIView):
    """GET /api/admin/users — danh sách tài khoản có tìm, lọc và phân trang.

    Thay bản cũ trong ``teaching/views.py`` (cứng ``LIMIT 50``, chỉ tìm theo tên
    và email, không phân trang): với vài trăm học viên thì em thứ 51 trở đi
    KHÔNG có đường nào hiện ra, kể cả khi trợ giảng biết chắc em có tài khoản.

    Tham số: ``q`` (tên/email/sđt), ``role``, ``status``, ``class_id``, ``page``,
    ``per_page`` (mặc định 25, trần 100).

    ĐÚNG HAI CÂU SQL bất kể trang có bao nhiêu em — xem "NGÂN SÁCH VÒNG GỌI" ở
    đầu module: một câu đếm-và-lấy-trang, một câu lấy lớp cho toàn bộ id của
    trang đó.
    """
    permission_classes = [IsAdminRole]

    def get(self, request):
        where, args = build_user_filters(request.query_params)
        page, per_page, offset = _paging(request.query_params, 25, 100)

        total, rows = _page_with_total(
            '''SELECT u.id, u.name, u.email, u.phone, u.role, u.status,
                      u.must_change_password, u.password_changed_at, u.created_at
                 FROM users u
                WHERE ''' + where,
            # Xếp theo tên chứ không theo id giảm dần: đây là danh sách để TRA
            # CỨU một em cụ thể, và người ta tra theo tên. Thứ tự phụ theo id để
            # hai em trùng tên không đảo chỗ giữa các lần tải — trang 2 mà đảo
            # thứ tự thì có em không bao giờ xuất hiện ở trang nào.
            "ORDER BY lower(coalesce(name, '')), id",
            args, per_page, offset)

        by_user = _classes_by_user([r['id'] for r in rows])
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
                'classes': by_user.get(r['id'], []),
            } for r in rows],
            'total': total,
            'page': page,
            'per_page': per_page,
            # Màn hình quản trị dựng ô chọn vai trò từ đây chứ không chép cứng
            # chuỗi 'Học viên' ở frontend — sai một dấu là tài khoản mất quyền
            # mà không báo lỗi gì.
            'roles': list(ASSIGNABLE_ROLES),
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

    Trả (danh_sách, bị_cắt_bớt). ``line`` là số dòng trong ĐÚNG văn bản trợ
    giảng vừa dán (đếm từ 1, kể cả dòng trống và dòng tiêu đề). Đánh số lại theo
    thứ tự sau khi lọc thì báo "dòng 7 hỏng" chỉ vào một dòng khác trên màn hình
    của trợ giảng, và em ấy sẽ sửa nhầm dòng.
    """
    out, header_checked, truncated = [], False, False
    for idx, raw in enumerate((text or '').splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if not header_checked:
            header_checked = True
            low = line.lower()
            if any(word in low for word in _HEADER_WORDS):
                continue
        if len(out) >= MAX_PARSE_LINES:
            # Cắt bớt thì phải NÓI ra. Lặng lẽ bỏ 200 dòng cuối là kịch bản tệ
            # nhất: trợ giảng thấy "đã cấp xong", đóng cửa sổ, và 200 em cuối
            # danh sách không có tài khoản mà không ai biết.
            truncated = True
            break
        name, email, phone = _split_line(line)
        out.append({'line': idx, 'name': name, 'email': email, 'phone': phone})
    return out, truncated


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
    còn chậm hơn, mà gunicorn cắt request ở 30 giây (``gunicorn.conf.py``). Phần
    ghi CSDL ngược lại rẻ (2 câu mỗi em × <5ms khi chạy thật), nên đừng đi tối ưu
    số câu SQL ở đây mà tưởng giải quyết được vấn đề.

    50 em ≈ 6 giây CPU khi phát triển, ước chừng 12–15 giây trên Render — còn dư
    địa thật dưới mốc 30 giây. Vượt trần thì TỪ CHỐI THẲNG chứ không thử rồi để
    worker bị giết giữa chừng: bị giết là kịch bản tệ nhất trong tất cả — một
    phần tài khoản đã tạo, phản hồi không bao giờ về, nên danh sách mật khẩu tạm
    mất trắng và KHÔNG em nào trong số đó đăng nhập được, trong khi email của
    các em thì đã bị chiếm chỗ nên dán lại cũng không tạo lại được.
    """
    permission_classes = [IsAdminRole]

    def post(self, request):
        from accounts.hashers import make_werkzeug_password

        body = request.data if isinstance(request.data, dict) else {}
        text = body.get('text') or ''
        role = (body.get('role') or ROLE_STUDENT).strip()
        dry_run = bool(body.get('dry_run'))
        class_id = body.get('class_id')

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
            klass = q1('SELECT id, name FROM classes WHERE id=%s', (class_id,))
            if not klass:
                return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        else:
            class_id = None

        cands, truncated = _parse_text(text)
        if not cands:
            return Response({'error': 'Không đọc được dòng dữ liệu nào. Mỗi dòng cần '
                                      'có họ tên kèm email hoặc số điện thoại.'}, status=400)

        by_email, by_phone = _existing_identities(
            {norm_email(c['email']) for c in cands if norm_email(c['email'])},
            {norm_phone(c['phone']) for c in cands if norm_phone(c['phone'])})

        # ── Vòng 1: chấm điểm từng dòng, chưa ghi gì ──
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

        # Tính trần TRƯỚC nhánh xem trước, không phải sau.
        #
        # Bản đầu đặt câu kiểm này sau `if dry_run` (phát hiện khi kiểm chứng
        # 30/08/2026): trợ giảng dán 60 dòng, bấm "Kiểm tra trước", màn hình báo
        # "sẽ tạo 60 tài khoản", bấm "Tạo" — rồi mới nhận lời từ chối. Bất ngờ
        # rơi đúng vào bước mà bản xem trước sinh ra để bảo vệ.
        # Xem trước vẫn trả 200 kèm đủ từng dòng: người dùng cần thấy dòng nào
        # hỏng VÀ cần cắt ở đâu, chứ không phải một câu lỗi trống rỗng.
        too_many = len(to_create) > MAX_CREATE_PER_BATCH
        if too_many:
            warnings.append(
                'Danh sách có %d dòng hợp lệ, vượt trần %d mỗi lần. Giữ lại %d dòng '
                'đầu rồi dán phần còn lại ở mẻ sau.'
                % (len(to_create), MAX_CREATE_PER_BATCH, MAX_CREATE_PER_BATCH))

        if dry_run:
            # Không một lệnh ghi nào chạy tới đây. Tổng cộng đúng 1–2 câu SQL cho
            # cả mẻ, nên trợ giảng bấm xem trước bao nhiêu lần cũng được.
            return Response({'ok': True, 'dryRun': True,
                             'created': len(to_create), 'skipped': skipped,
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
                'warnings': warnings, 'rows': rows,
            }, status=400)

        # ── Vòng 2: ghi. Mỗi tài khoản một giao dịch RIÊNG ──
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
            entry['tempPassword'] = temp

            audit.record(
                request, audit.USER_CREATE, target_type='user', target_id=uid,
                target_label=name,
                summary=('Cấp tài khoản "%s" (%s) bằng nhập hàng loạt%s.'
                         % (name, role, ' — xếp vào lớp "%s"' % klass['name'] if klass else '')),
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
            # `WHERE left_at IS NULL` trỏ đúng chỉ mục duy nhất một phần của
            # §36 (thiếu nó Postgres từ chối cả câu). Kèm theo là đổi hành vi có
            # chủ đích: người ĐÃ RỜI lớp mà được nhập lại sẽ sinh một dòng MỚI —
            # một lượt học mới — thay vì hồi sinh dòng cũ và xoá trắng mốc rời
            # lớp lần trước.
            x('''INSERT INTO class_members (class_id, user_id, joined_at)
                 SELECT %s, uid, %s FROM unnest(%s::int[]) AS uid
                 ON CONFLICT (class_id, user_id) WHERE left_at IS NULL DO NOTHING''',
              (class_id, now, created_ids))
            added_to_class = True

        return Response({
            'ok': True,
            'dryRun': False,
            'created': len(created_ids),
            'skipped': sum(1 for r in rows if r['status'] == 'skipped'),
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
