"""Sinh buổi học hàng loạt theo lịch tuần — xem trước, bỏ ngày nghỉ, không đẻ buổi trùng.

── VÌ SAO CÓ (13/09/2026) ─────────────────────────────────────────────────

Lớp TopHSA học cố định hai tối mỗi tuần trong một đợt ba tháng: ~26 buổi. Chỉ
có đường tạo TỪNG buổi thì đó là 26 lần chọn ngày-giờ — và khi tự làm bằng tay
để dựng dữ liệu mẫu 07/09, tôi đã tạo 4 buổi vào Thứ 6 trong khi lịch lớp ghi
Thứ 5. Cách các phần mềm điểm danh làm việc này (Moodle Attendance, SchoolTracs)
giống nhau: chọn thứ trong tuần + giờ + khoảng ngày, bỏ ngày nghỉ, xem trước.

── AI ĐƯỢC SINH (anh Sơn chốt 13/09/2026) ─────────────────────────────────

Giảng viên của lớp, học vụ, quản trị. KHÔNG trợ giảng — trợ giảng vẫn tạo từng
buổi được như trước. Kiểm trong `post` chứ không đổi `permission_classes`: trợ
giảng vẫn phải đọc được bản gợi ý (GET) để màn hình biết KHÔNG dựng nút — cùng
lối với `ClassSessionDetailView.delete`.

── NGÀY NGHỈ: LƯU THEO ĐỢT, KHÔNG TỰ QUYẾT ────────────────────────────────

Bỏ đúng những ngày học vụ đã khai cho đợt của lớp (`term_holidays`, §46). Lễ
dương lịch cố định mà đợt CHƯA khai thì vẫn tạo, nhưng dòng ấy mang cảnh báo:
lớp luyện thi có khi vẫn học ngày lễ, và đó là quyết định của trung tâm, không
phải của phần mềm. Xem `teaching/ngay_le.py` về Tết và Giỗ Tổ.

── CHẠY LẠI KHÔNG ĐẺ BUỔI TRÙNG ───────────────────────────────────────────

Người ta SẼ bấm hai lần, hoặc sinh lại sau khi sửa ngày kết thúc. Ngày nào lớp
đã có buổi (chưa huỷ) chồng giờ thì bỏ qua và nêu số buổi đang có. Buổi ĐÃ HUỶ
không chặn — cùng luật với `sessions._overlap_warning`.
"""
import re
import unicodedata
from datetime import datetime, time, timedelta

from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from common.audit import SESSION_GENERATE, record
from common.clock import local_now, local_today
from common.db import q, q1
from common.permissions import IsTeachingStaff, can_see_class, is_assistant
from stats.goals import as_date
from teaching.ngay_le import le_co_dinh_trong
from teaching.sessions import DEFAULT_SESSION_MINUTES, MAX_SESSION_MINUTES
from teaching.trung_lich import tim_trung_nhieu
from teaching.vocab import LOP_TAM_DUNG

#: Trần buổi tạo MỘT lần. Một đợt ba tháng hai buổi/tuần là ~26; năm buổi/tuần
#: cả năm học là ~200. Quá số đó gần như chắc chắn là chọn nhầm khoảng ngày, và
#: gỡ 300 buổi tạo nhầm bằng tay là việc không ai làm nổi.
MAX_BUOI_MOI_LAN = 200

#: Khoảng ngày tối đa — chặn trước khi vòng lặp chạy qua hàng nghìn ngày.
MAX_KHOANG_NGAY = 366

_TEN_THU = {1: 'T2', 2: 'T3', 3: 'T4', 4: 'T5', 5: 'T6', 6: 'T7', 7: 'CN'}

# ── Đoán lịch từ mô tả tự do của lớp ───────────────────────────────────────
#
# `classes.schedule` là chuỗi người gõ: "Thứ 3, 5 · 19:30–21:00", "T2-T4-T6
# 18h–19h30", "Thứ 7 và CN 8:00 - 10:00". Đoán để ĐIỀN SẴN form, không để quyết
# định: người bấm vẫn thấy và sửa được trước khi xem trước.

#: "thứ 3, 5" / "t2, t4, t6" / "thứ 2-4-6". Chữ số KHÔNG được đứng liền trước
#: ":" hay "h" — nếu không "thứ 3 19:30" nuốt luôn chữ 1 của giờ.
_THU = re.compile(r'(?<!\w)(?:thứ|thu|t)\s*([2-7](?:\s*(?:,|&|/|-|và|va)\s*(?:thứ|thu|t)?\s*'
                  r'[2-7](?![\d:h]))*)(?![\d:h])')
_CN = re.compile(r'(?<!\w)(?:cn|chủ\s*nhật|chu\s*nhat)(?!\w)')
#: "19:30" / "18h" / "19h30". Chữ "h" phải KHÔNG đứng trước một chữ cái, nếu không
#: "thứ 2 học" đọc thành 02:00.
_GIO = re.compile(r'(?<![\d:])([01]?\d|2[0-3])\s*(?::|h(?![^\W\d_]))\s*([0-5]\d)?(?![\d:])')


def doan_lich(mo_ta):
    """Mô tả lịch → ``(thứ_ISO đã sắp, 'HH:MM' | None, số_phút | None)``."""
    s = unicodedata.normalize('NFC', mo_ta or '').lower()
    thu = set()
    for m in _THU.finditer(s):
        thu.update(int(c) - 1 for c in re.findall(r'[2-7]', m.group(1)))
    if _CN.search(s):
        thu.add(7)
    gio = [(int(h), int(p or 0)) for h, p in _GIO.findall(s)]
    bat_dau = '%02d:%02d' % gio[0] if gio else None
    phut = None
    if len(gio) >= 2:
        chenh = (gio[1][0] * 60 + gio[1][1]) - (gio[0][0] * 60 + gio[0][1])
        if 0 < chenh <= MAX_SESSION_MINUTES:
            phut = chenh
    return sorted(thu), bat_dau, phut


# ── Đọc dữ liệu ─────────────────────────────────────────────────────────────

def _lop(class_id):
    return q1('''SELECT c.id, c.name, c.schedule, c.meeting_url, c.starts_on, c.ends_on,
                        c.status, c.term_id, t.name AS term_name,
                        t.starts_on AS term_starts_on, t.ends_on AS term_ends_on
                 FROM classes c LEFT JOIN terms t ON t.id = c.term_id
                 WHERE c.id = %s''', (class_id,))


def _ngay_nghi(term_id):
    if not term_id:
        return []
    return q('SELECT id, on_date, name FROM term_holidays WHERE term_id = %s ORDER BY on_date',
             (term_id,))


def _doc_than(body):
    """Thân yêu cầu → ``(tham_số, lỗi)``. Kiểm ĐỦ trước khi chạm CSDL."""
    thu_tho = body.get('weekdays')
    if not isinstance(thu_tho, list) or not thu_tho:
        return None, 'Chọn ít nhất một thứ trong tuần.'
    try:
        thu = sorted({int(v) for v in thu_tho})
    except (TypeError, ValueError):
        thu = []
    if not thu or any(t < 1 or t > 7 for t in thu):
        return None, 'Thứ trong tuần phải là số từ 1 (Thứ 2) tới 7 (Chủ nhật).'

    m = re.fullmatch(r'([01]?\d|2[0-3]):([0-5]\d)', str(body.get('start_time') or '').strip())
    if not m:
        return None, 'Giờ bắt đầu phải có dạng HH:MM, ví dụ 19:30.'
    gio = time(int(m.group(1)), int(m.group(2)))

    raw = body.get('duration_minutes')
    if raw in (None, ''):
        phut = DEFAULT_SESSION_MINUTES
    else:
        try:
            phut = int(raw)
        except (TypeError, ValueError):
            return None, 'Độ dài buổi học phải là số phút nguyên.'
        if phut <= 0 or phut > MAX_SESSION_MINUTES:
            return None, 'Độ dài buổi học phải trong khoảng 1–%d phút.' % MAX_SESSION_MINUTES

    tu, den = as_date(body.get('from')), as_date(body.get('to'))
    if not tu or not den:
        return None, 'Ngày bắt đầu và ngày kết thúc phải có dạng YYYY-MM-DD.'
    if tu > den:
        return None, 'Ngày kết thúc phải sau ngày bắt đầu.'
    if (den - tu).days > MAX_KHOANG_NGAY:
        return None, ('Một lần chỉ sinh được trong %d ngày — chia khoảng ngày làm nhiều lần.'
                      % MAX_KHOANG_NGAY)
    return {'thu': thu, 'gio': gio, 'phut': phut, 'tu': tu, 'den': den}, None


def _ngay_vn(d):
    return d.strftime('%d/%m/%Y')


def _cau_trung_lop(ds):
    """Ca trùng của MỘT ngày → "Trùng: giảng viên dạy lớp X; 2 em học lớp Y; phòng P201 (lớp Z)."."""
    phan = []
    for t in ds:
        if t['loai'] == 'giang-vien':
            phan.append('giảng viên dạy lớp %s' % t['lop'])
        elif t['loai'] == 'hoc-vien':
            phan.append('%d em học lớp %s' % (t['soEm'], t['lop']))
        else:
            phan.append('phòng %s (lớp %s)' % (t['phong'], t['lop']))
    return 'Trùng: %s.' % '; '.join(phan)


def _cham(class_id, lop, ts):
    """Chấm từng ngày, CHƯA GHI GÌ → ``(buoi, can_tao)``."""
    nghi = {r['on_date']: r['name'] for r in _ngay_nghi(lop['term_id'])}
    le = le_co_dinh_trong(ts['tu'], ts['den'])
    # MỘT câu cho mọi buổi có thể chồng giờ trong cả khoảng — lùi thêm đúng độ
    # dài buổi tối đa, để buổi bắt đầu tối hôm trước mà kéo sang ngày đầu vẫn
    # được thấy.
    co_san = q('''SELECT id, starts_at, COALESCE(duration_minutes, %s) AS phut
                  FROM class_sessions
                  WHERE class_id = %s AND status <> 'cancelled'
                    AND starts_at >= %s AND starts_at < %s
                  ORDER BY starts_at''',
               (DEFAULT_SESSION_MINUTES, class_id,
                datetime.combine(ts['tu'], time.min) - timedelta(minutes=MAX_SESSION_MINUTES),
                datetime.combine(ts['den'] + timedelta(days=1), time.min)))

    buoi, can_tao = [], []
    d = ts['tu']
    while d <= ts['den']:
        if d.isoweekday() in ts['thu']:
            bd = datetime.combine(d, ts['gio'])
            kt = bd + timedelta(minutes=ts['phut'])
            dong = {'ngay': d.isoformat(), 'thu': d.isoweekday(), 'startsAt': bd.isoformat(),
                    'trangThai': 'tao', 'lyDo': None, 'canhBao': None}
            trung = next((e for e in co_san
                          if e['starts_at'] < kt
                          and e['starts_at'] + timedelta(minutes=e['phut']) > bd), None)
            if d in nghi:
                dong.update(trangThai='nghi_le', lyDo='Ngày nghỉ của đợt: %s.' % nghi[d])
            elif trung:
                dong.update(trangThai='trung',
                            lyDo='Đã có buổi #%d lúc %s — giữ nguyên, không tạo thêm.'
                                 % (trung['id'], trung['starts_at'].strftime('%H:%M')))
            else:
                if d in le:
                    dong['canhBao'] = ('%s là %s nhưng đợt chưa khai nghỉ — nếu lớp nghỉ, học '
                                       'vụ khai ở Đợt học rồi xem trước lại.' % (_ngay_vn(d), le[d]))
                can_tao.append(bd)
            buoi.append(dong)
        d += timedelta(days=1)
    return buoi, can_tao


def tao_buoi(request, class_id, lop, ts, dry_run):
    """Chấm từng ngày rồi (khi không `dry_run`) GHI buổi cho một lớp → ``(kết_quả, lỗi)``.

    Tách khỏi `GenerateSessionsView.post` ngày 24/09/2026 (mục 1.2b) để lượt tạo
    NHANH lớp gia sư sinh lịch trong CÙNG giao dịch với lớp và em — một nguồn luật
    (trần buổi, ngày nghỉ, trùng lớp khác, buổi quá khứ) cho cả hai cửa. `lop` là
    dòng của `_lop()`; `ts` là kết quả `_doc_than()` đã kiểm.
    """
    buoi, can_tao = _cham(class_id, lop, ts)
    # Trần tính TRƯỚC nhánh xem trước — bài học của ô cấp tài khoản hàng loạt:
    # xem trước nói "sẽ tạo 365" rồi bấm Tạo mới bị từ chối là bất ngờ rơi
    # đúng vào bước sinh ra để tránh bất ngờ.
    if len(can_tao) > MAX_BUOI_MOI_LAN:
        return None, ('Khoảng này sinh ra %d buổi, vượt trần %d buổi mỗi lần. '
                      'Kiểm tra lại khoảng ngày, hoặc chia làm nhiều lần.'
                      % (len(can_tao), MAX_BUOI_MOI_LAN))

    dem = {'tao': 0, 'nghi_le': 0, 'trung': 0}
    for b in buoi:
        dem[b['trangThai']] += 1

    nay = local_now()
    canh_bao = []
    # Trùng với LỚP KHÁC (giảng viên / học viên / phòng — `trung_lich`): cảnh
    # báo trên từng dòng, VẪN tạo. Khác `trung` ở trên (lớp này đã có buổi) —
    # đó là chạy lại, còn đây có thể là ca cố ý (dạy ghép, học bù).
    trung_lop = tim_trung_nhieu(class_id, can_tao, ts['phut'])
    so_trung_lop = 0
    for b in buoi:
        ds = trung_lop.get(datetime.fromisoformat(b['startsAt'])) if b['trangThai'] == 'tao' else None
        if ds:
            so_trung_lop += 1
            b['trungLop'] = ds
            b['canhBao'] = ' '.join(filter(None, (b['canhBao'], _cau_trung_lop(ds))))
    if so_trung_lop:
        canh_bao.append('%d buổi trùng giờ với lớp khác (xem cột ghi chú). Vẫn tạo được — kiểm '
                        'lại nếu không cố ý.' % so_trung_lop)
    if not lop['term_id']:
        canh_bao.append('Lớp chưa thuộc đợt học nào nên không có ngày nghỉ nào được bỏ.')
    qua_khu = sum(1 for bd in can_tao if bd < nay)
    if qua_khu:
        canh_bao.append('%d buổi nằm trong quá khứ — chúng sẽ hiện ở mục "Đã diễn ra" và cần '
                        'điểm danh bù.' % qua_khu)

    ids = []
    if not dry_run and can_tao:
        vals = []
        for bd in can_tao:
            vals.extend((class_id, bd, ts['phut'], lop['meeting_url'], 'planned',
                         request.user.id, nay))
        with transaction.atomic():
            # MỘT câu cho cả lượt. Kế thừa link phòng của lớp — cùng luật với
            # tạo từng buổi (`ClassSessionsView.post`).
            ids = [r['id'] for r in q(
                'INSERT INTO class_sessions (class_id, starts_at, duration_minutes, meeting_url, '
                'status, created_by, created_at) VALUES '
                + ', '.join(['(%s, %s, %s, %s, %s, %s, %s)'] * len(can_tao))
                + ' RETURNING id', tuple(vals))]
            thu_chu = ', '.join(_TEN_THU[t] for t in ts['thu'])
            record(request, SESSION_GENERATE, target_type='class', target_id=class_id,
                   target_label=lop['name'],
                   summary=('Sinh %d buổi lớp %s (%s · %s · %d phút) từ %s tới %s; bỏ %d ngày '
                            'nghỉ, %d ngày đã có buổi.'
                            % (len(ids), lop['name'], thu_chu, ts['gio'].strftime('%H:%M'),
                               ts['phut'], _ngay_vn(ts['tu']), _ngay_vn(ts['den']),
                               dem['nghi_le'], dem['trung'])),
                   detail={'weekdays': ts['thu'], 'start_time': ts['gio'].strftime('%H:%M'),
                           'duration_minutes': ts['phut'], 'from': ts['tu'].isoformat(),
                           'to': ts['den'].isoformat(), 'ids': ids,
                           'nghi_le': [b['ngay'] for b in buoi if b['trangThai'] == 'nghi_le'],
                           'trung': [b['ngay'] for b in buoi if b['trangThai'] == 'trung']})

    return {'ok': True, 'dryRun': dry_run, 'dem': dem, 'buoi': buoi,
            'canhBao': canh_bao, 'ids': ids}, None


class GenerateSessionsView(APIView):
    """GET/POST /api/teach/classes/<id>/sessions/generate.

    GET  — bản gợi ý: lịch đoán từ mô tả lớp, khoảng ngày theo lớp/đợt, ngày nghỉ
           của đợt, và `coTheSinh` cho người đang xem. Không ghi gì.
    POST — ``{weekdays, start_time, duration_minutes, from, to, dry_run}``.
           `weekdays` theo ISO: 1 = Thứ 2 … 7 = Chủ nhật.
    """
    permission_classes = [IsTeachingStaff]

    def get(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        lop = _lop(class_id)
        if not lop:
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)

        thu, gio, phut = doan_lich(lop['schedule'])
        # Từ hôm nay trở đi, nhưng không trước ngày lớp / đợt bắt đầu: lịch sinh
        # về quá khứ là hàng loạt buổi "chưa điểm danh" ngay khi vừa tạo.
        tu = max(d for d in (local_today(), lop['starts_on'], lop['term_starts_on']) if d)
        den = lop['ends_on'] or lop['term_ends_on']
        return Response({
            'lop': {'id': lop['id'], 'name': lop['name'], 'schedule': lop['schedule']},
            'dot': ({'id': lop['term_id'], 'name': lop['term_name'],
                     'ngayNghi': [{'id': r['id'], 'ngay': r['on_date'].isoformat(),
                                   'ten': r['name']} for r in _ngay_nghi(lop['term_id'])]}
                    if lop['term_id'] else None),
            'goiY': {'weekdays': thu, 'startTime': gio, 'durationMinutes': phut,
                     'from': tu.isoformat(),
                     'to': den.isoformat() if den and den >= tu else None},
            'coTheSinh': not is_assistant(request.user) and lop['status'] != LOP_TAM_DUNG,
            # Màn hình nói VÌ SAO không có khối sinh lịch, thay vì lặng lẽ giấu nó.
            'tamDung': lop['status'] == LOP_TAM_DUNG,
            'tranBuoi': MAX_BUOI_MOI_LAN,
        })

    def post(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        if is_assistant(request.user):
            return Response({'error': 'Trợ giảng không sinh lịch hàng loạt được. Tạo từng buổi '
                                      'ở ô "Tạo buổi học", hoặc nhờ giảng viên phụ trách lớp.'},
                            status=403)
        lop = _lop(class_id)
        if not lop:
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        # Lớp TẠM DỪNG (V-c, 25/09/2026) không sinh lịch — kể cả xem trước: buổi
        # sinh ra cho một lớp đang nghỉ là hàng loạt buổi "chưa điểm danh" giả,
        # và em nhận lịch học mà không buổi nào diễn ra. 409: yêu cầu hợp lệ, chỉ
        # xung đột với trạng thái lớp.
        if lop['status'] == LOP_TAM_DUNG:
            return Response({'error': 'Lớp đang tạm dừng nên chưa sinh lịch được. Học vụ đổi '
                                      'trạng thái lớp sang "Đang học" rồi sinh lịch.'}, status=409)

        body = request.data if isinstance(request.data, dict) else {}
        ts, loi = _doc_than(body)
        if loi:
            return Response({'error': loi}, status=400)
        dry_run = bool(body.get('dry_run'))

        kq, loi = tao_buoi(request, class_id, lop, ts, dry_run)
        if loi:
            return Response({'error': loi}, status=400)
        return Response(kq, status=201 if kq['ids'] else 200)
