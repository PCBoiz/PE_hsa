"""NHẬP HỌC VIÊN VÀO LỚP TỪ TỆP MẪU — V-j, bảng TopHSA dòng 4 ("import DS theo biểu mẫu").

Luồng: học vụ mở lớp → "Nhập từ tệp mẫu" → tải tệp mẫu .xlsx → điền → tải lên → XEM TRƯỚC
từng dòng → "Nhập vào lớp". Ô dán email ngay cạnh vẫn giữ cho việc lẻ.

MỘT dòng tệp = một em. Ba cách nhận ra em đã có tài khoản: mã học viên (HSA-xxxxx), email,
số điện thoại — chuẩn hoá bằng `common/identity.py` như mọi đường khác. Ba cách ấy trỏ HAI
người khác nhau thì BÁO chứ không đoán: xếp nhầm một em vào lớp là mở môn cho người khác.

  · Em CÓ SẴN tài khoản → vào lớp qua `AdminClassMembersView._ghi_thanh_vien` — cùng cửa với
    ô "Thêm vào lớp" (nhật ký, trần lớp gia sư dưới khoá, quên đệm quyền môn).
  · Em CHƯA có → cấp qua `admin_users.cap_tai_khoan` — CÙNG hàm với ô dán ở trang Tài khoản
    (kiểm từng dòng `_check_row`, mã HSA, mật khẩu tạm, nhật ký, xếp lớp một câu). Hai đường
    tạo tài khoản là hai chỗ sẽ trôi khỏi nhau.

TRẦN 50 DÒNG MỘT TỆP — cùng trần cấp tài khoản một mẻ (`MAX_CREATE_PER_BATCH`, tính từ giá
bằm mật khẩu so với hạn 30 giây của máy chủ). Vượt thì từ chối cả tệp, kể cả khi xem trước:
chia tệp là việc của người nhập, không phải của máy.

Ô CÔNG THỨC: `.xlsx` được đọc bằng GIÁ TRỊ đã tính (`bangtinh.doc`), và ô công thức chưa có
giá trị làm cả tệp bị từ chối kèm toạ độ ô. `.csv` thì ô "=…" là chữ trần — họ tên mở đầu
bằng = + - @ bị `_check_row` báo lỗi (một họ tên thật không bao giờ như thế, còn để lọt
thì nó thành công thức trong mọi bản xuất Excel sau này).
"""
from functools import partial

from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from common import audit
from common.bangtinh import KIEU_XLSX, LoiBangTinh, Trang, doc, ghi_xlsx, thanh_ban_ghi
from common.db import q, q1
from common.identity import norm_email, norm_phone
from common.permissions import ROLE_STUDENT, IsAdminOrAcademic
from teaching import vocab
from teaching.admin_users import (
    MAX_CREATE_PER_BATCH,
    _check_row,
    cap_tai_khoan,
    cho_trong_gia_su,
)
from teaching.views import AdminClassMembersView, _doc_ngay_vao_lop, _user_label

#: Tiêu đề tệp mẫu — tên cột người dùng NHÌN THẤY. Bộ đọc so chữ thường, bỏ khoảng trắng thừa.
COT_MAU = ('Họ và tên', 'Email', 'Số điện thoại', 'Mã học viên')
COT_BAT_BUOC = ('họ và tên',)
#: Tên khác của cùng một cột — khai TƯỜNG MINH (xem `bangtinh.thanh_ban_ghi`).
TEN_KHAC = {'họ tên': 'họ và tên', 'sđt': 'số điện thoại', 'điện thoại': 'số điện thoại',
            'số đt': 'số điện thoại', 'mã hsa': 'mã học viên', 'mã hv': 'mã học viên'}
#: Trần kích thước tệp. 50 dòng chữ là vài chục kB; 1 MB chặn được việc chọn nhầm ảnh.
MAX_BYTES = 1024 * 1024

#: Trạng thái từng dòng — màn hình dựng nhãn từ đây.
TAO_MOI, THEM_VAO_LOP, DA_TRONG_LOP, LOI = 'tao_moi', 'them_vao_lop', 'da_trong_lop', 'loi'


def _tim_co_san(ds):
    """MỘT câu cho cả tệp: tài khoản khớp mã / email / SĐT → ba bảng tra."""
    ma = sorted({(b.get('mã học viên') or '').strip().upper() for _, b in ds} - {''})
    em = sorted({norm_email(b.get('email')) for _, b in ds if norm_email(b.get('email'))})
    sdt = sorted({norm_phone(b.get('số điện thoại')) for _, b in ds if norm_phone(b.get('số điện thoại'))})
    if not (ma or em or sdt):
        return {}, {}, {}
    rows = q('''SELECT id, name, email, phone, role, student_code FROM users
                 WHERE upper(student_code) = ANY(%s::text[])
                    OR (email IS NOT NULL AND lower(email) = ANY(%s::text[]))
                    OR (phone IS NOT NULL AND phone <> '' AND phone = ANY(%s::text[]))''',
             (ma, em, sdt))
    return ({(r['student_code'] or '').upper(): r for r in rows if r['student_code']},
            {norm_email(r['email']): r for r in rows if r['email']},
            {r['phone']: r for r in rows if r['phone']})


def _ghi_loi(rows, entry, ly_do):
    rows.append(dict(entry, status=LOI, reason=ly_do))


def _cham(ds, lop_id):
    """Chấm từng dòng, CHƯA GHI GÌ → (rows, to_create, co_san)."""
    theo_ma, theo_email, theo_sdt = _tim_co_san(ds)
    trong_lop = {r['user_id'] for r in q(
        'SELECT user_id FROM class_members WHERE class_id = %s AND left_at IS NULL', (lop_id,))}
    rows, to_create, co_san = [], [], []
    seen_email, seen_phone, seen_uid = {}, {}, {}
    for so_dong, b in ds:
        ten = (b.get('họ và tên') or '').strip()
        ma = (b.get('mã học viên') or '').strip().upper()
        email = norm_email(b.get('email'))
        sdt = norm_phone(b.get('số điện thoại'))
        entry = {'line': so_dong, 'name': ten or None, 'email': email or None, 'phone': sdt or None}
        loi = partial(_ghi_loi, rows, entry)

        if ma and ma not in theo_ma:
            loi('Không có học viên nào mang mã %s.' % ma)
            continue
        tim = [t for t in (theo_ma.get(ma) if ma else None,
                           theo_email.get(email) if email else None,
                           theo_sdt.get(sdt) if sdt else None) if t]
        if len({t['id'] for t in tim}) > 1:
            loi('Mã, email, số điện thoại trên dòng này trỏ tới hai tài khoản khác nhau (%s). '
                'Sửa lại dòng cho đúng một em.' % ', '.join(sorted({_user_label(t) for t in tim})))
            continue
        if tim:
            nguoi = tim[0]
            entry.update(name=nguoi['name'] or ten or None, userId=nguoi['id'],
                         studentCode=nguoi['student_code'])
            if (nguoi['role'] or ROLE_STUDENT) != ROLE_STUDENT:
                loi('"%s" là tài khoản nhân sự (%s) — tệp này chỉ nhập học viên.'
                    % (_user_label(nguoi), nguoi['role']))
                continue
            if nguoi['id'] in seen_uid:
                loi('Trùng em với dòng %d.' % seen_uid[nguoi['id']])
                continue
            seen_uid[nguoi['id']] = so_dong
            if nguoi['id'] in trong_lop:
                rows.append(dict(entry, status=DA_TRONG_LOP, reason='Em đã ở trong lớp — không làm gì.'))
                continue
            rows.append(dict(entry, status=THEM_VAO_LOP, reason='Tài khoản có sẵn — sẽ thêm vào lớp.'))
            co_san.append((rows[-1], nguoi))
            continue
        # Chưa có tài khoản: CÙNG bộ kiểm với ô dán ở trang Tài khoản.
        name, email, sdt, ly_do = _check_row({'name': ten, 'email': email, 'phone': sdt},
                                             theo_email, theo_sdt, seen_email, seen_phone)
        if ly_do:
            loi(ly_do)
            continue
        if email:
            seen_email[email] = so_dong
        if sdt:
            seen_phone[sdt] = so_dong
        rows.append(dict(entry, status=TAO_MOI, reason='Chưa có tài khoản — sẽ cấp tài khoản mới.'))
        to_create.append((rows[-1], name, email, sdt))
    return rows, to_create, co_san


def _dem(rows):
    return {k: sum(1 for r in rows if r['status'] == k) for k in (TAO_MOI, THEM_VAO_LOP, DA_TRONG_LOP, LOI)}


class NhapHocVienView(APIView):
    """POST /api/admin/classes/<id>/nhap-hoc-vien — tệp .xlsx/.csv (trường `tep`), `dry_run`,
    `joined_at` (ngày vào lớp cho cả tệp, tuỳ chọn). Xem trước KHÔNG ghi gì."""
    permission_classes = [IsAdminOrAcademic]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, class_id):
        lop = q1('SELECT id, name, class_type FROM classes WHERE id=%s', (class_id,))
        if not lop:
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        tep = request.FILES.get('tep')
        if not tep:
            return Response({'error': 'Chọn tệp danh sách (.xlsx hoặc .csv) trước khi tải lên.'}, status=400)
        if tep.size > MAX_BYTES:
            return Response({'error': 'Tệp nặng %d kB, tối đa %d kB — có thể bạn chọn nhầm tệp.'
                                      % (tep.size // 1024, MAX_BYTES // 1024)}, status=400)
        dry_run = (request.data.get('dry_run') or '').strip().lower() in ('1', 'true', 'on', 'yes')
        vao, loi_ngay = _doc_ngay_vao_lop(request.data.get('joined_at'))
        if loi_ngay:
            return Response({'error': loi_ngay}, status=400)
        try:
            ds = thanh_ban_ghi(doc(tep.name, tep.read()), COT_BAT_BUOC, TEN_KHAC)
        except LoiBangTinh as e:
            return Response({'error': str(e)}, status=400)
        if len(ds) > MAX_CREATE_PER_BATCH:
            return Response({'error': 'Tệp có %d dòng, tối đa %d em mỗi lần nhập — chia tệp ra rồi '
                                      'nhập nhiều lần.' % (len(ds), MAX_CREATE_PER_BATCH)}, status=400)

        rows, to_create, co_san = _cham(ds, lop['id'])
        warnings = []
        so_vao = len(to_create) + len(co_san)
        if lop.get('class_type') == 'gia_su' and so_vao:
            con = cho_trong_gia_su(lop['id'])
            if so_vao > con:
                cau = ('Lớp gia sư "%s" chỉ còn %d chỗ (tối đa %d em) — tệp có %d em sẽ vào lớp. '
                       'Bớt dòng hoặc chọn lớp khác.' % (lop['name'], max(con, 0), vocab.TRAN_GIA_SU, so_vao))
                if not dry_run:
                    return Response({'ok': False, 'error': cau, 'rows': rows, 'dem': _dem(rows)}, status=400)
                warnings.append(cau)
        if dry_run:
            return Response({'ok': True, 'dryRun': True, 'rows': rows, 'dem': _dem(rows),
                             'warnings': warnings, 'maxRows': MAX_CREATE_PER_BATCH})

        # Ghi: có sẵn trước (một em một lượt qua cửa chung), rồi cấp tài khoản mới.
        da_them = []
        for entry, nguoi in co_san:
            kq = AdminClassMembersView._ghi_thanh_vien(request, lop, nguoi, vao=vao)
            if kq == 'them':
                da_them.append(nguoi['id'])
            elif kq == 'day':
                entry.update(status=LOI, reason='Lớp gia sư vừa đủ %d em — em chưa vào lớp.' % vocab.TRAN_GIA_SU)
            else:
                entry.update(status=DA_TRONG_LOP, reason='Em đã ở trong lớp — không làm gì.')
        created, _, canh_bao = cap_tai_khoan(request, to_create, ROLE_STUDENT, lop, vao,
                                             nguon='nhập từ tệp "%s"' % tep.name)
        warnings += canh_bao
        for entry, *_ in to_create:
            if entry.get('userId') is None:
                entry['status'] = LOI                 # vấp chỉ mục duy nhất lúc tạo
        audit.record(request, audit.CLASS_MEMBER_IMPORT, target_type='class', target_id=lop['id'],
                     target_label=lop['name'],
                     summary='Nhập %d học viên vào lớp "%s" từ tệp "%s": %d tài khoản mới, %d tài khoản có sẵn.'
                             % (len(created) + len(da_them), lop['name'], tep.name, len(created), len(da_them)),
                     detail={'tep': tep.name, 'moi': created, 'coSan': da_them,
                             'loi': sum(1 for r in rows if r['status'] == LOI)})
        return Response({'ok': True, 'dryRun': False, 'rows': rows, 'dem': _dem(rows), 'warnings': warnings,
                         'note': 'Mật khẩu tạm chỉ hiện MỘT lần ở đây — chép ra trước khi đóng.'},
                        status=201)


class TepMauNhapHocVienView(APIView):
    """GET /api/admin/classes/<id>/nhap-hoc-vien/mau — tệp mẫu .xlsx.

    Sinh tại chỗ từ `COT_MAU` (cùng hằng bộ đọc dùng) — một tệp tĩnh trong repo là bản thứ
    hai sẽ trôi. `class_id` chỉ để đường dẫn nằm cạnh lượt nhập; mẫu giống nhau mọi lớp."""
    permission_classes = [IsAdminOrAcademic]

    def get(self, request, class_id):
        from django.http import HttpResponse

        from teaching.exports import _disposition
        mau = Trang('Danh sách', [
            list(COT_MAU),
            ['Nguyễn Văn An', 'an.nguyen@gmail.com', '0912345678', ''],
            ['Trần Thị Bình', '', '0987654321', ''],
            ['(em đã có tài khoản — chỉ cần mã)', '', '', 'HSA-00012'],
        ], rong=[30, 32, 18, 16])
        huong = Trang('Hướng dẫn', [
            ['Mỗi DÒNG là một học viên. Giữ nguyên dòng tiêu đề ở trang "Danh sách", xoá ba dòng ví dụ.'],
            [''],
            ['Họ và tên', 'Bắt buộc với em chưa có tài khoản.'],
            ['Email', 'Không bắt buộc — nhưng mỗi dòng cần ít nhất email, số điện thoại hoặc mã học viên.'],
            ['Số điện thoại', '10 số, ví dụ 0912345678. Định dạng cột là Văn bản để giữ số 0 đầu.'],
            ['Mã học viên', 'Chỉ điền cho em ĐÃ có tài khoản (HSA-xxxxx). Em có sẵn được thêm vào lớp, không cấp mới.'],
            [''],
            ['Tối đa %d dòng mỗi tệp.' % MAX_CREATE_PER_BATCH],
            ['Tải lên xong, hệ thống XEM TRƯỚC từng dòng; chỉ khi bấm "Nhập vào lớp" mới ghi.'],
            ['Em mới nhận mật khẩu tạm — hiện MỘT lần sau khi nhập, chép ra ngay.'],
        ], rong=[18, 90], tieu_de=False)
        res = HttpResponse(ghi_xlsx([mau, huong]), content_type=KIEU_XLSX)
        res['Content-Disposition'] = _disposition('Mẫu nhập học viên vào lớp.xlsx')
        return res
