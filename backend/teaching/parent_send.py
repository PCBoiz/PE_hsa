"""Gửi báo cáo cho phụ huynh CẢ LỚP — hệ thống soạn sẵn, người bấm gửi.

── QUYẾT ĐỊNH CỦA ANH SƠN, 07/09/2026 ─────────────────────────────────────

Được hỏi giữa ba cách: tự động hoàn toàn theo lịch, tự động nhưng chờ 24h, và
"hệ thống soạn sẵn — người bấm gửi". Anh chọn cách thứ ba.

Nên ở đây có ĐÚNG HAI bước, và chúng là hai phương thức khác nhau có chủ ý:

    GET   → soạn sẵn: ai sẽ nhận, ai thiếu số, link của từng em
    POST  → gửi thật

Tách ra vì một tin đã tới Zalo phụ huynh thì không thu về được, và mỗi tin ZNS
đều mất phí. Gộp hai bước vào một lời gọi là biến một cú bấm nhầm thành một
hoá đơn thật và 25 tin nhắn không rút lại được.

── CHƯA CÓ ZALO OA THÌ VẪN LÀM ĐƯỢC VIỆC ─────────────────────────────────

Trung tâm chưa có OA đã xác thực (việc của anh Sơn — xem `docs/VIEC_CUA_ANH.md`).
Khi ấy `POST` **không tạo dòng chờ nào**: một hàng chờ mà không có gì xử lý là
một danh sách việc giả, và người nhìn nó sẽ tưởng tin đang trên đường đi.

Thay vào đó nó vẫn CẤP LINK cho cả lớp và trả về, để học vụ chép đi gửi tay.
Đó là bản dùng được ngay, không phải bản tạm — và ngày OA có thì đúng cùng một
nút ấy chuyển sang gửi thật, không ai phải học lại thao tác nào.

── VÌ SAO KHÔNG DÙNG LẠI LINK CŨ VÔ ĐIỀU KIỆN ────────────────────────────

Có link còn sống cùng kỳ thì dùng lại: cấp chìa mới mỗi lượt gửi là để lại một
đống chìa còn hiệu lực mà không ai theo dõi được. Nhưng KHÁC KỲ thì phải cấp
mới — kỳ ghim cứng vào chìa, nên gửi lại chìa tháng trước là gửi báo cáo tháng
trước.
"""
from datetime import timedelta

from rest_framework.response import Response
from rest_framework.views import APIView

from common import mail, zalo
from common.clock import local_today
from common.db import q, q1, x
from common.permissions import IsSeniorTeachingStaff, can_see_class
from teaching.parent_link import HAN_NGAY, SO_BYTE
from teaching.parent_report import DEFAULT_WEEKS, dung_bao_cao
from teaching.thu_bao_cao import soan_thu
from teaching.vocab import chi_hoc_vien

import secrets

#: Tên tham số của MẪU ZNS. Do mẫu Zalo duyệt quy định, KHÔNG phải mã này tự
#: đặt — khi anh Sơn tạo mẫu thì sửa đúng ở đây cho khớp, và chỉ ở đây.
#:
#: Mẫu dự kiến (nội dung phải thuộc nhóm CHĂM SÓC KHÁCH HÀNG thì Zalo mới duyệt):
#:   "TopHSA — báo cáo học tập của <ten_hoc_vien> lớp <ten_lop>, kỳ <ky>.
#:    Xem chi tiết: <duong_dan>"
THAM_SO_MAU = ('ten_hoc_vien', 'ten_lop', 'ky', 'duong_dan')


def _ky():
    """Kỳ báo cáo mặc định — CÙNG công thức với `ParentReportView`.

    Không viết lại con số 4 tuần ở đây: `DEFAULT_WEEKS` là bản gốc, và hai bản
    chép sẽ trôi khỏi nhau đúng vào ngày ai đó đổi kỳ báo cáo của trung tâm.
    """
    den = local_today()
    return den - timedelta(weeks=DEFAULT_WEEKS), den


def _hoc_vien_dang_hoc(class_id):
    """Học viên ĐANG học của lớp, kèm số phụ huynh.

    `left_at IS NULL` — em đã rời lớp thì không gửi báo cáo tiến độ nữa; gửi là
    nhắc phụ huynh về một việc đã kết thúc, và số liệu trong kỳ cũng trống.

    `chi_hoc_vien` BẮT BUỘC: tài khoản quản trị đang là thành viên lớp 1 (anh
    chủ sản phẩm chốt giữ), nên thiếu bộ lọc này là gửi "báo cáo phụ huynh" cho
    chính tài khoản quản trị.
    """
    return q('''SELECT DISTINCT ON (u.id)
                       u.id, u.name, u.parent_name, u.parent_phone,
                       u.parent_email
                FROM class_members m
                JOIN users u ON u.id = m.user_id
                WHERE m.class_id = %s AND m.left_at IS NULL
                  AND ''' + chi_hoc_vien('u') + '''
                ORDER BY u.id''', (class_id,))


def _link_cho(class_id, user_id, tu, den, nguoi_tao):
    """Chìa còn sống ĐÚNG KỲ này, cấp mới nếu chưa có. Trả token."""
    d = q1('''SELECT token FROM parent_report_links
              WHERE class_id=%s AND user_id=%s AND period_from=%s AND period_to=%s
                AND revoked_at IS NULL AND expires_at > now()
              ORDER BY created_at DESC LIMIT 1''', (class_id, user_id, tu, den))
    if d:
        return d['token']
    token = secrets.token_urlsafe(SO_BYTE)
    x('''INSERT INTO parent_report_links
             (token, class_id, user_id, period_from, period_to, created_by, expires_at)
         VALUES (%s,%s,%s,%s,%s,%s, now() + %s * INTERVAL '1 day')''',
      (token, class_id, user_id, tu, den, nguoi_tao, HAN_NGAY))
    return token


def _goc(request):
    """Gốc địa chỉ để dựng link tuyệt đối gửi đi.

    Lấy từ `FRONTEND_URL` chứ không từ `request`: request tới đây là của
    GIẢNG VIÊN (có thể qua localhost, qua IP nội bộ, qua một bản xem trước),
    còn link này đi tới điện thoại của PHỤ HUYNH — nó phải là địa chỉ công
    khai thật của sản phẩm.
    """
    from django.conf import settings
    return (getattr(settings, 'FRONTEND_URL', '') or '').rstrip('/')


def _kenh_cho(e):
    """Kênh sẽ dùng cho em này: `'email'`, `'zns'`, hay `None` nếu chưa gửi được.

    ── VÌ SAO EMAIL ĐI TRƯỚC (07/09/2026) ───────────────────────────────────

    Không phải vì email tốt hơn. Vì ZNS **chưa dùng được và chưa biết bao giờ
    dùng được**: nó đòi Zalo OA đã xác thực, mà xác thực đòi giấy phép kinh
    doanh. Anh Sơn chốt đi đường email trước, nên email là kênh CHÍNH còn ZNS
    là kênh cho ngày có OA — không phải ngược lại.

    Hàm hỏi HAI câu và cả hai phải đúng: hệ thống đã cấu hình kênh ấy chưa, và
    em này có địa chỉ/số của kênh ấy chưa. Thiếu một trong hai thì kênh ấy
    không dùng được CHO EM NÀY — trả `None` để nơi gọi nói thẳng ra, thay vì
    thử gửi rồi báo lỗi.
    """
    if (mail.da_cau_hinh() or mail.che_do_thu()) and (e.get('parent_email') or '').strip():
        return 'email'
    if (zalo.da_cau_hinh() or zalo.che_do_thu()) and (e.get('parent_phone') or '').strip():
        return 'zns'
    return None


class ParentReportSendAllView(APIView):
    """GET/POST /api/teach/classes/<id>/parent-report/send-all

    GET — bản SOẠN SẴN: ai nhận được, ai thiếu số. Không ghi gì.
    POST — gửi thật (hoặc cấp link để gửi tay, nếu chưa có OA).
    """
    permission_classes = [IsSeniorTeachingStaff]

    def get(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        tu, den = _ky()
        ds = _hoc_vien_dang_hoc(class_id)
        return Response({
            'period': {'from': tu.isoformat(), 'to': den.isoformat()},
            'znsSanSang': zalo.da_cau_hinh() or zalo.che_do_thu(),
            'znsCheDoThu': zalo.che_do_thu(),
            'znsThieu': zalo.thieu_gi(),
            'emailSanSang': mail.da_cau_hinh() or mail.che_do_thu(),
            'emailCheDoThu': mail.che_do_thu(),
            'emailThieu': mail.thieu_gi(),
            'students': [{
                'id': e['id'],
                'name': e['name'],
                'parentName': e['parent_name'] or '',
                'parentPhone': e['parent_phone'] or '',
                'parentEmail': e['parent_email'] or '',
                # HAI câu hỏi KHÁC NHAU, và người sửa chúng cũng khác nhau:
                #
                #   coLienLac — em này có số hoặc email phụ huynh chưa? Thiếu
                #               thì GIẢNG VIÊN đi hỏi phụ huynh.
                #   kenh      — gửi được ngay bây giờ bằng đường nào? `None`
                #               dù CÓ liên lạc nghĩa là hệ thống chưa cấu hình
                #               kênh ấy, và đó là việc của NGƯỜI QUẢN TRỊ.
                #
                # Gộp hai câu vào một cờ thì màn hình nói "không gửi được" mà
                # người đọc không biết phải đi sửa ở đâu.
                'coLienLac': bool((e['parent_phone'] or '').strip()
                                  or (e['parent_email'] or '').strip()),
                'kenh': _kenh_cho(e),
                'guiDuoc': _kenh_cho(e) is not None,
            } for e in ds],
        })

    def post(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)

        tu, den = _ky()
        ds = _hoc_vien_dang_hoc(class_id)
        if not ds:
            return Response({'error': 'Lớp này chưa có học viên nào đang học.'}, status=400)

        # Kênh nào dùng được là chuyện của TỪNG EM (xem `_kenh_cho`), nên
        # không còn một biến "sẵn sàng" chung cho cả lượt nữa.
        goc = _goc(request)
        ky_chu = '%s – %s' % (tu.strftime('%d/%m/%Y'), den.strftime('%d/%m/%Y'))
        lop = q1('SELECT name FROM classes WHERE id=%s', (class_id,))
        ten_lop = (lop or {}).get('name') or ''

        ket = []
        for e in ds:
            token = _link_cho(class_id, e['id'], tu, den, request.user.id)
            duong_dan = '%s/bc/%s' % (goc, token)
            so = (e['parent_phone'] or '').strip()
            dia_chi = (e['parent_email'] or '').strip()
            kenh = _kenh_cho(e)

            if kenh is None:
                # Tách HAI lý do khác nhau, vì cách chữa khác nhau: thiếu liên
                # lạc thì đi hỏi phụ huynh, còn chưa cấu hình kênh thì là việc
                # của người quản trị. Gộp cả hai vào "gửi tay" là giấu mất câu
                # hỏi "vì sao không gửi được".
                #
                # KHÔNG tạo dòng `parent_report_sends` ở cả hai nhánh: một hàng
                # chờ mà không có gì xử lý là một danh sách việc giả.
                ket.append({'id': e['id'], 'name': e['name'],
                            'trangThai': 'thieu_lienlac' if not (so or dia_chi) else 'gui_tay',
                            'kenh': None, 'duongDan': duong_dan, 'loi': None})
                continue

            if kenh == 'email':
                # Payload báo cáo THẬT của em này, dựng bằng CÙNG hàm mà API và
                # đường chìa công khai dùng — nên tệp PDF đính kèm không trôi
                # khỏi tờ giấy phụ huynh mở trên web.
                bc, loi_bc = dung_bao_cao(class_id, e['id'], tu, den)
                if loi_bc:
                    ket.append({'id': e['id'], 'name': e['name'], 'trangThai': 'loi',
                                'kenh': 'email', 'duongDan': duong_dan, 'loi': loi_bc})
                    continue
                tieu_de, chu, html, dinh_kem = soan_thu(bc, duong_dan)
                ok, dau_vet, loi = mail.gui(dia_chi, tieu_de, chu, html, dinh_kem)
                thu_kenh, nguoi_nhan = mail.che_do_thu(), dia_chi
                # Thứ người bấm cần DUYỆT ở kênh email. Không đưa phần HTML
                # vào: nó vài nghìn ký tự và không ai đọc được nó trong một ô
                # JSON — bản xem đúng của HTML là tệp `.eml` mà chế độ thử ghi
                # ra đĩa, và `dauVet` chỉ thẳng tới tệp ấy.
                noi_dung = {'tieuDe': tieu_de, 'chu': chu,
                            'dinhKem': [{'ten': t, 'kb': round(len(d) / 1024, 1)}
                                        for t, _k, d in dinh_kem]}
            else:
                noi_dung = {'ten_hoc_vien': e['name'] or '', 'ten_lop': ten_lop,
                            'ky': ky_chu, 'duong_dan': duong_dan}
                ok, dau_vet, loi = zalo.gui_zns(so, noi_dung)
                thu_kenh, nguoi_nhan = zalo.che_do_thu(), so

            if thu_kenh:
                # CHẾ ĐỘ THỬ: KHÔNG ghi `parent_report_sends`.
                #
                # Sổ ấy là sổ của những tin ĐÃ ĐI. Một dòng 'da_gui' cho tin
                # chưa từng rời máy chủ là loại nói dối khó thấy nhất: lần sau
                # mở sổ ra sẽ tưởng phụ huynh đã nhận, và không ai gửi lại.
                # `noiDung` là TOÀN BỘ lý do chế độ thử tồn tại: người bấm
                # phải duyệt được ĐÚNG thứ sẽ đi. Bản viết lại hôm nay lỡ bỏ
                # nó đi và `tests_parent_send` bắt được ngay — gỡ một năng lực
                # trong lúc đổi hình dạng dữ liệu là kiểu hỏng dễ lọt nhất.
                ket.append({'id': e['id'], 'name': e['name'], 'trangThai': 'thu',
                            'kenh': kenh, 'duongDan': duong_dan, 'loi': None,
                            'soNhan': nguoi_nhan, 'noiDung': noi_dung,
                            'dauVet': dau_vet})
                continue

            link = q1('SELECT id FROM parent_report_links WHERE token=%s', (token,))
            # Vào sổ CẢ lượt hỏng. Một lượt gửi lỗi mà không ghi lại thì lần
            # sau không ai biết em nào đã thử và trượt — còn phụ huynh thì chỉ
            # biết là họ chưa nhận được gì.
            x('''INSERT INTO parent_report_sends
                     (link_id, phone, email, channel, status, provider_id, error,
                      requested_by, sent_at)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s, CASE WHEN %s THEN now() ELSE NULL END)''',
              (link['id'], so if kenh == 'zns' else '',
               dia_chi if kenh == 'email' else '', kenh,
               'da_gui' if ok else 'loi', dau_vet, loi, request.user.id, ok))
            ket.append({'id': e['id'], 'name': e['name'],
                        'trangThai': 'da_gui' if ok else 'loi',
                        'kenh': kenh, 'duongDan': duong_dan, 'loi': loi})

        dem = {}
        for r in ket:
            dem[r['trangThai']] = dem.get(r['trangThai'], 0) + 1
        return Response({
            'period': {'from': tu.isoformat(), 'to': den.isoformat()},
            'znsSanSang': zalo.da_cau_hinh() or zalo.che_do_thu(),
            'znsCheDoThu': zalo.che_do_thu(),
            'znsThieu': zalo.thieu_gi(),
            'emailSanSang': mail.da_cau_hinh() or mail.che_do_thu(),
            'emailCheDoThu': mail.che_do_thu(),
            'emailThieu': mail.thieu_gi(),
            'tong': len(ket),
            'dem': dem,
            'ketQua': ket,
        })
