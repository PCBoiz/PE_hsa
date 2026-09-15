"""Nhập kết quả thi thử từ tờ PDF của hệ thống khảo thí ngoài — ERP, 15–16/09/2026.

Hai tuyến, hai việc:

    POST …/ket-qua-thi/doc   multipart, tối đa MAX_TEP_MOT_LUOT tệp. CHỈ ĐỌC.
                             Trả mỗi tờ một PHIẾU đã ký (hoặc câu lỗi).
    POST …/ket-qua-thi/ghi   JSON {phieu: [...], chon: {...}, ghi: bool}. Khớp
                             học viên, soát trùng; `ghi: true` mới ghi.

── VÌ SAO TÁCH ĐỌC VÀ GHI (16/09/2026) ───────────────────────────────────

Bản đầu (15/09) làm cả hai trong MỘT tuyến nhận cả xấp PDF. Đo trên máy dev:
đọc một tờ mất 0,75 giây (7 trang, chế độ `layout`) → lớp 35 em là ~26 giây
trong một request, và lượt bấm "Ghi" đọc lại cả xấp từ đầu. Hai trần chặn đường
ấy trên production:

    · gunicorn `--timeout 60` (render.yaml), trên CPU Render yếu hơn máy dev;
    · mọi `/api/*` đi qua route handler Next trên Vercel, thân request tối đa
      4,5 MB — mà một tờ mẫu đã 481 kB, chục tờ là vượt.

Nên trình duyệt gửi TỪNG tờ đi đọc (có thanh tiến độ), còn lượt ghi chỉ gửi lại
các phiếu — không đọc PDF lần hai, và thấy được CẢ XẤP một lúc để soát trùng.

── PHIẾU ĐÃ KÝ, KHÔNG PHẢI SỐ TRÌNH DUYỆT TỰ GỬI ─────────────────────────

Lượt ghi không nhận điểm số từ trình duyệt. Nó nhận phiếu do chính tuyến `doc`
phát ra, ký bằng `django.core.signing` (HMAC theo SECRET_KEY), gắn với LỚP và
NGƯỜI đọc, hết hạn sau TUOI_PHIEU giây. Sửa một con số là chữ ký hỏng; mang
phiếu sang lớp khác hay tài khoản khác đều bị từ chối. Điểm trong hồ sơ vì thế
vẫn đúng là "điểm đọc từ tờ PDF", như nhật ký ghi.

Dev và production đang dùng chung SECRET_KEY (việc A6 trong VIEC_CUA_ANH): ai có
`backend/.env` thì ký được phiếu — y như ký được thẻ đăng nhập. Không mở thêm lỗ
mới, và được đóng cùng lúc với A6.

── VÌ SAO XEM TRƯỚC LÀ BẮT BUỘC, KHÔNG PHẢI TIỆN NGHI ────────────────────

Khớp theo TÊN là chỗ sai được. Hai em cùng tên trong một lớp là chuyện có thật;
tên trên tờ của bên kia có thể viết khác (thiếu dấu, thừa đệm). Ghi thẳng nghĩa
là điểm của em này rơi vào hồ sơ em khác, rồi đi tiếp vào tờ báo cáo gửi về nhà.
Không ai phát hiện ra, vì con số trông hoàn toàn hợp lý.

Nên khớp không chắc thì KHÔNG đoán: học vụ chọn tay em trong lớp, hoặc bỏ qua tờ
đó. `chon` = {"<thứ tự phiếu>": user_id, hoặc 0 để bỏ qua}; user_id ngoài lớp thì
từ chối CẢ lượt chứ không lặng lẽ bỏ qua.

── HAI TỜ RƠI VÀO MỘT EM ─────────────────────────────────────────────────

Hai tờ cùng khớp vào một em cho cùng một kỳ thi thì KHÔNG ghi tờ nào: ghi cả
hai là tờ sau đè tờ trước trong cùng một giao dịch, im lặng. Đánh dấu `trung`.

── GHI ĐÈ, KHÔNG ĐẺ THÊM ────────────────────────────────────────────────

Nhập lại đúng tờ ấy lần nữa (học vụ tải lại cả thư mục) không được tạo thêm một
lượt thi ma: khoá duy nhất theo (người, ngày thi, đợt) và `ON CONFLICT DO UPDATE`.
"""
import json
import unicodedata
from collections import Counter
from datetime import date

from django.core import signing
from django.db import transaction
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from common import audit
from common.db import q, x
from common.permissions import IsSeniorTeachingStaff, can_see_class
from teaching.nhap_ket_qua_thi import MAX_BYTES, LoiDocBaoCao, doc_tep
from teaching.vocab import chi_hoc_vien

#: Số tệp tối đa MỘT lượt đọc. Màn hình gửi từng tệp; trần này chặn một request
#: tự dựng gửi cả xấp. 5 tờ ≈ 4 giây trên máy dev — xa trần 60 giây của gunicorn
#: kể cả khi CPU Render chậm hơn vài lần.
MAX_TEP_MOT_LUOT = 5

#: Số phiếu tối đa một lượt ghi. Một lớp TopHSA tối đa 35 em (bảng giá trung tâm).
MAX_PHIEU = 60

#: Phiếu sống bao lâu (giây). Đủ cho một buổi làm việc bị ngắt quãng, đủ ngắn để
#: phiếu nằm quên trong trình duyệt không thành một đường ghi về sau.
TUOI_PHIEU = 6 * 3600

#: "Muối" của chữ ký — tách phiếu này khỏi mọi thứ khác cũng ký bằng SECRET_KEY.
_MUOI_PHIEU = 'teaching.nhap_ket_qua_thi.phieu'


def _chuan(ten):
    """Tên để SO KHỚP: bỏ hoa/thường và khoảng trắng thừa."""
    return ' '.join((ten or '').split()).casefold()


def _bo_dau(ten):
    """Bỏ dấu tiếng Việt — lưới an toàn khi tờ bên kia gõ thiếu dấu.

    Chỉ dùng khi khớp CHÍNH XÁC đã thất bại, và vẫn phải duy nhất mới nhận:
    bỏ dấu làm "Hoà" và "Hoa" thành một, nên nó nới khớp chứ không thay thế.
    """
    s = unicodedata.normalize('NFD', _chuan(ten))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.replace('đ', 'd')


def _hoc_vien_cua_lop(class_id):
    """Học viên ĐANG học — `left_at IS NULL`, như điểm danh và chấm bài.

    Bản đầu lấy cả em đã rời lớp: một em cùng tên đã chuyển đi làm tờ của em
    đang học thành "trùng tên", và ô "Ghi cho" mời ghi điểm vào hồ sơ em ấy.
    """
    return q('''SELECT DISTINCT u.id, u.name, u.email
                  FROM class_members m
                  JOIN users u ON u.id = m.user_id
                 WHERE m.class_id = %s AND m.left_at IS NULL AND ''' + chi_hoc_vien('u') + '''
                 ORDER BY u.name''', (class_id,))


def _da_co(hoc_vien):
    """{(user_id, ngày thi, đợt)} đã nằm trong hồ sơ của học viên lớp này — MỘT truy vấn."""
    ids = [e['id'] for e in hoc_vien]
    if not ids:
        return set()
    return {(r['user_id'], r['ngay_thi'], r['dot'] or '') for r in q(
        'SELECT user_id, ngay_thi, dot FROM ket_qua_thi_ngoai WHERE user_id = ANY(%s)', (ids,))}


def khop_ten(ho_ten, danh_sach):
    """(user_id, lý do) — `user_id` None nghĩa là chưa khớp được, lý do nói vì sao."""
    dich = _chuan(ho_ten)
    hit = [e for e in danh_sach if _chuan(e['name']) == dich]
    if len(hit) == 1:
        return hit[0]['id'], None
    if len(hit) > 1:
        return None, 'Trong lớp có %d em cùng tên "%s" — chọn tay giúp tôi.' % (len(hit), ho_ten)

    khong_dau = _bo_dau(ho_ten)
    hit = [e for e in danh_sach if _bo_dau(e['name']) == khong_dau]
    if len(hit) == 1:
        return hit[0]['id'], 'Khớp khi bỏ dấu ("%s" ↔ "%s") — kiểm lại giúp tôi.' % (
            ho_ten, hit[0]['name'])
    if len(hit) > 1:
        return None, 'Bỏ dấu thì trùng %d em — chọn tay giúp tôi.' % len(hit)
    return None, 'Không có em nào tên "%s" trong lớp này.' % ho_ten


def _ky_phieu(request, class_id, ten_tep, d):
    return signing.dumps(
        {'c': class_id, 'u': request.user.id, 'tep': ten_tep,
         'd': {**d, 'ngayThi': d['ngayThi'].isoformat()}},
        salt=_MUOI_PHIEU, compress=True)


def _mo_phieu(request, class_id, phieu):
    """Phiếu → (tên tệp, dữ liệu tờ). Ném `ValueError` mang câu cho học vụ đọc."""
    lai = ' Chọn lại tệp PDF để đọc lại.'
    if not isinstance(phieu, str):
        raise ValueError('Phiếu đọc không hợp lệ.' + lai)
    try:
        p = signing.loads(phieu, salt=_MUOI_PHIEU, max_age=TUOI_PHIEU)
    except signing.SignatureExpired:
        raise ValueError('Bản đọc đã quá %d giờ.' % (TUOI_PHIEU // 3600) + lai) from None
    except signing.BadSignature:
        raise ValueError('Phiếu đọc không hợp lệ.' + lai) from None
    if p.get('c') != class_id or p.get('u') != request.user.id:
        raise ValueError('Phiếu đọc không thuộc lớp này hoặc không do bạn đọc.' + lai)
    d = dict(p['d'])
    d['ngayThi'] = date.fromisoformat(d['ngayThi'])
    return p['tep'], d


def _doc_chon(tho, id_trong_lop, so_phieu):
    """`chon` = {"<thứ tự phiếu>": user_id | 0}. Ném `ValueError` nếu sai."""
    if tho in (None, ''):
        return {}
    if not isinstance(tho, dict):
        raise ValueError('"chon" phải có dạng {thứ tự tờ: mã học viên}.')
    kq = {}
    for k, v in tho.items():
        try:
            i = int(k)
        except (TypeError, ValueError):
            raise ValueError('Thứ tự tờ "%.20s" không hợp lệ.' % k) from None
        # `True` cũng là `int` trong Python: không chặn thì `true` trong JSON
        # thành "học viên #1".
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError('Mã học viên chọn cho tờ thứ %d không hợp lệ.' % (i + 1))
        if not 0 <= i < so_phieu:
            raise ValueError('Không có tờ thứ %d trong lượt này.' % (i + 1))
        if v and v not in id_trong_lop:
            raise ValueError('Học viên #%d không thuộc lớp này.' % v)
        kq[i] = v
    return kq


def danh_gia(to, chon, hoc_vien, da_co):
    """Các tờ đã đọc + lựa chọn tay → trạng thái từng tờ. Không chạm CSDL.

    `to` = [(tên tệp, dữ liệu tờ)]; `da_co` = kết quả của `_da_co`.
    Trạng thái: `san-sang` | `chua-khop` | `bo-qua` | `trung`.
    """
    ten_theo_id = {e['id']: e['name'] for e in hoc_vien}
    dong = []
    for i, (ten_tep, d) in enumerate(to):
        tu_dong, ly_do = khop_ten(d['hoTen'], hoc_vien)
        uid, chon_tay = tu_dong, i in chon
        if chon_tay:
            uid = chon[i] or None
            if not uid:
                ly_do = 'Bỏ qua theo lựa chọn của bạn.'
            elif uid != tu_dong:
                ly_do = ('Chọn tay.' if _chuan(d['hoTen']) == _chuan(ten_theo_id[uid]) else
                         'Chọn tay — tên trên tờ khác tên trong hồ sơ, kiểm lại giúp tôi.')
        dong.append({
            'thuTu': i, 'tep': ten_tep,
            'trangThai': 'bo-qua' if chon_tay and not uid else 'san-sang' if uid else 'chua-khop',
            'hoTen': d['hoTen'], 'maHocSinh': d['maHocSinh'],
            'khopTuDong': tu_dong, 'userId': uid, 'chonTay': chon_tay,
            'tenTrongLop': ten_theo_id.get(uid),
            'ghiChu': ly_do,
            'ngayThi': d['ngayThi'].isoformat(), 'dot': d['dot'],
            'tongDiem': d['tongDiem'], 'tongToiDa': d['tongToiDa'],
            'diemPhan': d['diemPhan'], 'soDonVi': len(d['donVi']),
            'yeuNhat': sorted(d['donVi'], key=lambda v: v['pct'])[:3],
            'canhBao': d['canhBao'],
            'seGhiDe': bool(uid) and (uid, d['ngayThi'], d['dot'] or '') in da_co,
        })

    def khoa(r):
        return r['userId'], r['ngayThi'], r['dot'] or ''

    dem = Counter(khoa(r) for r in dong if r['trangThai'] == 'san-sang')
    for r in dong:
        if r['trangThai'] == 'san-sang' and dem[khoa(r)] > 1:
            r['trangThai'] = 'trung'
            r['ghiChu'] = ('%d tờ cùng rơi vào %s cho cùng kỳ thi — chọn lại cho đúng em.'
                           % (dem[khoa(r)], r['tenTrongLop']))
    return dong


class DocKetQuaThiView(APIView):
    """POST /api/teach/classes/<id>/ket-qua-thi/doc — đọc PDF, phát phiếu. Không ghi gì."""

    permission_classes = [IsSeniorTeachingStaff]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        tep = request.FILES.getlist('files')
        if not tep:
            return Response({'error': 'Chưa chọn tệp PDF nào.'}, status=400)
        if len(tep) > MAX_TEP_MOT_LUOT:
            return Response({'error': 'Gửi %d tệp, tối đa %d tệp một lượt đọc.'
                                      % (len(tep), MAX_TEP_MOT_LUOT)}, status=400)
        kq = []
        for f in tep:
            ten = (f.name or 'tep.pdf')[:200]
            try:
                # Đọc TỐI ĐA MAX_BYTES + 1 byte: đủ để `doc_chu` nhận ra tệp quá
                # nặng và nói đúng câu ấy, mà không kéo cả một tệp khổng lồ vào RAM
                # của máy chủ 512 MB (tuyến Render vẫn gọi thẳng được, không qua trần
                # 4,5 MB của Vercel).
                d = doc_tep(f.read(MAX_BYTES + 1))
            except LoiDocBaoCao as e:
                kq.append({'tep': ten, 'loi': str(e)})
                continue
            kq.append({'tep': ten, 'phieu': _ky_phieu(request, class_id, ten, d)})
        return Response({'tep': kq})


class GhiKetQuaThiView(APIView):
    """POST /api/teach/classes/<id>/ket-qua-thi/ghi — JSON {phieu, chon, ghi}.

    `ghi` vắng hoặc khác `true` → chỉ trả bảng khớp; màn hình gọi lại mỗi lần đổi
    lựa chọn tay, nên luật khớp chỉ có MỘT bản — ở đây.
    """

    permission_classes = [IsSeniorTeachingStaff]
    parser_classes = [JSONParser]

    def post(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        body = request.data if isinstance(request.data, dict) else {}
        ds = body.get('phieu')
        if not isinstance(ds, list) or not ds:
            return Response({'error': 'Chưa có tờ nào đã đọc.'}, status=400)
        if len(ds) > MAX_PHIEU:
            return Response({'error': '%d tờ, tối đa %d tờ một lượt ghi.'
                                      % (len(ds), MAX_PHIEU)}, status=400)
        try:
            to = [_mo_phieu(request, class_id, p) for p in ds]
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        hoc_vien = _hoc_vien_cua_lop(class_id)
        try:
            chon = _doc_chon(body.get('chon'), {e['id'] for e in hoc_vien}, len(to))
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        dong = danh_gia(to, chon, hoc_vien, _da_co(hoc_vien))
        san_sang = [r for r in dong if r['trangThai'] == 'san-sang']
        da_ghi = 0
        if body.get('ghi') is True and san_sang:
            with transaction.atomic():
                for r in san_sang:
                    d = to[r['thuTu']][1]
                    x('''INSERT INTO ket_qua_thi_ngoai
                             (user_id, ngay_thi, dot, ma_hoc_sinh, hinh_thuc, dia_diem,
                              tong_diem, tong_toi_da, diem_phan, don_vi, ten_tren_to, nhap_boi)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s)
                         ON CONFLICT (user_id, ngay_thi, COALESCE(dot, ''))
                         DO UPDATE SET ma_hoc_sinh=EXCLUDED.ma_hoc_sinh,
                                       hinh_thuc=EXCLUDED.hinh_thuc,
                                       dia_diem=EXCLUDED.dia_diem,
                                       tong_diem=EXCLUDED.tong_diem,
                                       tong_toi_da=EXCLUDED.tong_toi_da,
                                       diem_phan=EXCLUDED.diem_phan,
                                       don_vi=EXCLUDED.don_vi,
                                       ten_tren_to=EXCLUDED.ten_tren_to,
                                       nhap_boi=EXCLUDED.nhap_boi''',
                      (r['userId'], d['ngayThi'], d['dot'], d['maHocSinh'], d['hinhThuc'],
                       d['diaDiem'], d['tongDiem'], d['tongToiDa'],
                       json.dumps(d['diemPhan'], ensure_ascii=False),
                       json.dumps(d['donVi'], ensure_ascii=False),
                       d['hoTen'], request.user.id))
                audit.record(request, audit.EXTERNAL_EXAM_IMPORT, target_type='class',
                             target_id=class_id,
                             target_label='Lớp #%s' % class_id,
                             summary='Nhập kết quả thi thử từ %d tờ PDF cho lớp #%s (%d tờ không ghi).'
                                     % (len(san_sang), class_id, len(dong) - len(san_sang)),
                             detail={'files': [r['tep'] for r in san_sang],
                                     'students': [r['userId'] for r in san_sang],
                                     'manual': [r['tep'] for r in san_sang if r['chonTay']],
                                     'overwritten': [r['tep'] for r in san_sang if r['seGhiDe']],
                                     'skipped': [r['tep'] for r in dong
                                                 if r['trangThai'] != 'san-sang']})
            da_ghi = len(san_sang)

        def dem(tt):
            return sum(1 for r in dong if r['trangThai'] == tt)

        return Response({
            'daGhi': da_ghi,
            'tomTat': {
                'tong': len(dong),
                'sanSang': len(san_sang),
                'chuaKhop': dem('chua-khop'),
                'boQua': dem('bo-qua'),
                'trung': dem('trung'),
                'seGhiDe': sum(1 for r in san_sang if r['seGhiDe']),
            },
            'dong': dong,
            'hocVienTrongLop': [{'id': e['id'], 'name': e['name']} for e in hoc_vien],
        })
