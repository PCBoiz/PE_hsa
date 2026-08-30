"""Xuất dữ liệu ra CSV mở được bằng Excel — đặc tả ERP §6

Đặc tả nói thẳng: *"Xuất Excel/PDF — bắt buộc với trung tâm, họ luôn cần bản
mang đi họp."* Người mở ba file dưới đây không phải lập trình viên: là trợ giảng
và quản lý học vụ của TopHSA, mở bằng Excel trên Windows, lọc, tô màu, in ra
mang đi họp phụ huynh. Mọi quyết định trong tệp này bám vào đúng cảnh đó.

VÌ SAO CSV CHỨ KHÔNG PHẢI .XLSX. Ghi .xlsx cần openpyxl; mỗi dependency thêm vào
là thêm một thứ có thể vỡ lúc dựng bản trên Render, mà CSV mở bằng Excel đã đủ
cho việc lọc – tô màu – in. Đổi lại phải làm ĐÚNG ba việc dưới đây; sai một việc
thì file mở ra thành rác và trung tâm bỏ dùng ngay từ lần đầu:

1. **BOM ``\\ufeff`` ở đầu file.** Không có BOM, Excel trên Windows đọc CSV theo
   bảng mã ANSI của hệ thống chứ không phải UTF-8: "Nguyễn" hiện thành
   "Nguyá»…n". Một danh sách học viên mà tên nào cũng hỏng thì không có thao tác
   nào trong Excel cứu được — họ đóng file lại và quay về gõ tay.
2. **Xuống dòng ``\\r\\n``.** Excel bản Windows đọc file chỉ có ``\\n`` là một ô
   khổng lồ nhiều dòng ở vài cấu hình cũ; ``\\r\\n`` thì mọi bản đều đúng.
3. **Tên file mã hoá RFC 5987** (``filename*=UTF-8''…`` kèm một ``filename=``
   ASCII dự phòng). Tên file tiếng Việt để nguyên trong header sẽ bị trình duyệt
   cắt hoặc đổi thành ký tự lạ, và ba file tải trong một buổi mà cùng tên
   "download.csv" thì không ai biết file nào là lớp nào.

CHỐNG CHÈN CÔNG THỨC. Ô bắt đầu bằng ``=``, ``+``, ``-``, ``@`` bị Excel hiểu là
công thức. Ở đây ``note`` của buổi học, ghi chú lớp và cả họ tên đều là ô TỰ DO
do người dùng gõ, nên đây không phải rủi ro lý thuyết: một dòng
``=HYPERLINK(...)`` gõ vào ô ghi chú sẽ chạy trên máy của trợ giảng khi họ mở
file. Mọi ô đi qua ``_cell`` và bị chèn dấu nháy đơn ở đầu để vô hiệu hoá.

KHÔNG TÍNH LẠI SỐ LIỆU Ở ĐÂY. ``teaching/reports.py`` đã dựng sẵn toàn bộ phép
tính của báo cáo lớp (tiến độ, năng lực, độ chậm, cảnh báo sớm). Tệp này chỉ ĐỌC
LẠI kết quả đó rồi đổ ra hàng và cột. Nếu tính song song một lần nữa ở đây thì
màn hình và file mang đi họp sẽ lệch nhau, và không ai biết bản nào đúng —
đúng cái tình huống làm mất niềm tin vào cả hệ thống báo cáo.

HIỆU NĂNG. Mỗi lượt tới Neon tốn ~245ms thuần đường truyền, nên SỐ CÂU truy vấn
mới là thứ quyết định chứ không phải độ phức tạp câu. Cả ba endpoint dùng số câu
CỐ ĐỊNH, không phụ thuộc sĩ số lớp hay số buổi học: lấy đủ dữ liệu rồi xoay bảng
trong Python.
"""
import csv
import io
import json
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import quote

from django.db import DatabaseError
from django.http import HttpResponse
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from common.clock import local_now
from common.db import q, q1
from teaching.admin_users import any_user_filter, build_user_filters
from common.permissions import IsAdminRole, IsTeacherOrAdmin, can_see_class
from teaching import reports

#: Nhãn tiếng Việt cho `attendance.status`. Ô trong bảng chéo phải NGẮN — một
#: lớp 30 buổi là 30 cột, chữ dài thì in ra tràn trang.
ATTENDANCE_LABELS = {
    'present': 'Có mặt', 'late': 'Muộn', 'absent': 'Vắng', 'excused': 'Có phép',
}
#: Thứ tự cột tổng ở cuối bảng điểm danh — cùng thứ tự với sổ giấy.
ATTENDANCE_ORDER = ('present', 'late', 'absent', 'excused')

#: `users.role` lưu 'admin' bằng tiếng Anh vì là giá trị máy đọc; file này để
#: mang đi họp nên phải dịch. Hai vai trò kia đã là tiếng Việt sẵn.
ROLE_LABELS = {'admin': 'Quản trị viên'}
USER_STATUS_LABELS = {'active': 'Đang hoạt động', 'suspended': 'Đã khoá'}

#: Ký tự mở đầu khiến Excel/LibreOffice coi ô là CÔNG THỨC.
#: KHÔNG có tab và CR trong danh sách này, và đó là chủ ý chứ không phải bỏ sót:
#: ``_cell`` cắt khoảng trắng hai đầu TRƯỚC khi kiểm, nên biến thể né bộ lọc
#: ``"\t=cmd"`` bị lột lớp tab và lộ ra dấu ``=`` để bị chặn ở đây. Liệt kê tab
#: vào đây thì nhánh đó vĩnh viễn không chạy, và một hằng số nói dối về việc nó
#: đang bảo vệ cái gì còn nguy hiểm hơn là không có nó.
_FORMULA_STARTERS = ('=', '+', '-', '@')

#: `đ`/`Đ` không tách được dấu bằng NFKD (chúng là chữ cái riêng, không phải
#: d + dấu), nên phải thay tay trước khi bỏ dấu cho tên file dự phòng.
_D_STROKE = str.maketrans({'đ': 'd', 'Đ': 'D'})


# ── Bộ dựng CSV dùng chung ──────────────────────────────────────────────────
# Ba endpoint dưới đây khác nhau ở dữ liệu, KHÔNG khác nhau ở cách đóng gói.
# Viết ba lần thì ba tháng nữa sửa BOM ở một chỗ và quên hai chỗ còn lại.

def _cell(value):
    """Một giá trị Python → một ô CSV an toàn, đọc được bằng tiếng Việt.

    Số được đổi thẳng sang chuỗi mà KHÔNG chèn nháy: nếu chèn thì ``-34``
    ("điểm thi thử giảm 34%") thành chuỗi ``'-34``, Excel không cộng trừ được
    nữa và cột đó mất tác dụng — mà cột đó chính là thứ trợ giảng lọc để tìm em
    đang tụt. Chỉ CHUỖI mới đi qua bộ chống công thức.
    """
    if value is None:
        return ''
    # bool phải xét TRƯỚC int (bool là lớp con của int trong Python).
    if isinstance(value, bool):
        return 'Có' if value else 'Không'
    if isinstance(value, datetime):
        return value.strftime('%d/%m/%Y %H:%M')
    if isinstance(value, date):
        return value.strftime('%d/%m/%Y')
    if isinstance(value, (int, float, Decimal)):
        return str(value)
    text = str(value)
    # Ghi chú của giảng viên là ô nhiều dòng. CSV có ngoặc kép thì xuống dòng
    # bên trong ô là hợp lệ, nhưng in ra thì một dòng học viên cao bằng nửa
    # trang giấy. Gộp về một dòng: sổ mang đi họp là MỖI HỌC VIÊN MỘT DÒNG.
    text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').strip()
    if text[:1] in _FORMULA_STARTERS:
        # Dấu nháy đơn ở đầu = cách vô hiệu hoá công thức mà OWASP khuyến nghị.
        return "'" + text
    return text


def _phone_cell(value):
    """Số điện thoại — ép Excel giữ nguyên số 0 đầu.

    Số Việt Nam luôn bắt đầu bằng 0, mà Excel thấy một ô toàn chữ số thì đọc
    thành SỐ: "0964245623" hiện ra "964245623". Đây không phải lỗi thẩm mỹ —
    trung tâm dùng đúng cột này để gọi phụ huynh, và một số sai thì gọi không ai
    nghe. Chèn nháy đơn ở đầu để ô thành chuỗi. Đánh đổi: ở vài bản Excel dấu
    nháy hiện ra trong ô. Thà xấu một ký tự còn hơn sai cả số — số hỏng thì
    người đọc KHÔNG biết là nó đã hỏng.
    """
    text = '' if value is None else str(value).strip()
    if text.isascii() and text.isdigit() and text.startswith('0'):
        return "'" + text
    return text          # '+84…' bắt đầu bằng '+' → _cell tự chèn nháy


def _ascii_fallback(name):
    """Tên file dự phòng cho trình duyệt cũ: bỏ dấu, chỉ giữ ký tự an toàn.

    Cũng là hàng rào an ninh: tên lớp do trợ giảng gõ mà lọt được ``\\r\\n`` vào
    ``Content-Disposition`` là chèn header. Ở đây mọi ký tự lạ (kể cả xuống
    dòng, dấu ngoặc kép, dấu gạch chéo) đều thành ``-``.
    """
    plain = unicodedata.normalize('NFKD', name.translate(_D_STROKE))
    plain = ''.join(c for c in plain if not unicodedata.combining(c))
    plain = plain.encode('ascii', 'ignore').decode('ascii')
    plain = ''.join(c if (c.isalnum() or c in ' .-_()') else '-' for c in plain)
    return plain.strip() or 'export.csv'


def _disposition(filename):
    """Header tải file: tên tiếng Việt theo RFC 5987 + bản ASCII dự phòng.

    Hai tham số cùng lúc là cố ý: trình duyệt hiện đại đọc ``filename*`` (đúng
    dấu tiếng Việt), trình duyệt cũ bỏ qua nó và rơi về ``filename``. Chỉ có
    ``filename*`` thì máy cũ tải về thành tên rác không đuôi .csv.
    """
    return "attachment; filename=\"%s\"; filename*=UTF-8''%s" % (
        _ascii_fallback(filename), quote(filename, safe=''))


def _stamp():
    """Dấu thời gian trong tên file, theo GIỜ VIỆT NAM.

    Bắt buộc dùng ``local_now`` chứ không phải SQL ``now()``: Neon trả UTC,
    lệch 7 giờ, nên một file xuất lúc 1h sáng sẽ mang tên ngày HÔM TRƯỚC. Hai
    file cùng một lớp đề hai ngày khác nhau là đủ để cãi nhau trong buổi họp.
    """
    return local_now().strftime('%d-%m-%Y %Hh%M')


def _csv_response(filename, header, rows):
    """Dựng HttpResponse CSV đúng cả ba điểm bắt buộc (BOM, \\r\\n, RFC 5987).

    Dựng trọn trong bộ nhớ thay vì StreamingHttpResponse: quy mô ở đây là hàng
    nghìn dòng (một trung tâm luyện thi), tức vài trăm KB. Nếu có ngày danh sách
    tài khoản vượt vài chục nghìn dòng thì đổi sang streaming — nhưng đừng đổi
    trước, vì streaming làm mất khả năng đặt Content-Length và trình duyệt sẽ
    không hiện thanh tiến trình khi tải.
    """
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator='\r\n')
    writer.writerow([_cell(c) for c in header])
    for row in rows:
        writer.writerow([_cell(c) for c in row])
    body = ('﻿' + buf.getvalue()).encode('utf-8')

    resp = HttpResponse(body, content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = _disposition(filename)
    return resp


class _CsvRenderer(BaseRenderer):
    """Cho phép thương lượng nội dung với ``Accept: text/csv``.

    DRF chốt renderer TRƯỚC khi gọi ``get()``; chỉ có JSONRenderer thì một
    client tử tế gửi ``Accept: text/csv`` sẽ nhận 406 mà không bao giờ chạm tới
    mã bên dưới. Trình duyệt gửi ``*/*`` nên không gặp, nhưng script tải tự động
    của trung tâm thì có. Thân CSV thật vẫn do ``_csv_response`` trả thẳng, lớp
    này chỉ để bước thương lượng đi qua được; nó chỉ thật sự render khi endpoint
    trả JSON lỗi (404) cho một client đòi text/csv.
    """
    media_type = 'text/csv'
    format = 'csv'
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, (bytes, str)):
            return data
        return json.dumps(data, ensure_ascii=False)


#: JSON đứng trước để ``Accept: */*`` (trình duyệt) vẫn nhận thân lỗi dạng JSON.
CSV_RENDERERS = [JSONRenderer, _CsvRenderer]

#: Đúng một câu trả lời cho cả hai trường hợp "lớp không tồn tại" và "lớp của
#: người khác" — trả 403 cho vế sau là gián tiếp xác nhận lớp đó CÓ tồn tại.
_NOT_FOUND = {'error': 'Không tìm thấy lớp này.'}


def _label_from(code, name, class_id):
    """Nhãn lớp dùng đặt tên file: ưu tiên MÃ lớp vì đó là thứ trung tâm gọi
    nhau hằng ngày ("HSA-DEMO-01"), và nó ngắn nên tên file không bị trình duyệt
    cắt. Lớp chưa đặt mã thì lấy tên, cùng đường thì lấy id."""
    return ((code or '').strip() or (name or '').strip() or str(class_id))


def _class_label(class_id):
    """Nhãn lớp khi bên gọi CHƯA có sẵn dòng `classes` trong tay."""
    row = q1('SELECT code, name FROM classes WHERE id = %s', (class_id,))
    if not row:
        return str(class_id)
    return _label_from(row['code'], row['name'], class_id)


def _vn_date(iso):
    """'2026-08-27' hoặc '2026-08-27T11:30:38' → '27/08/2026'.

    ``reports.py`` trả ngày dạng ISO vì nó phục vụ API; file mang đi họp thì
    phải là ngày kiểu Việt Nam. Đọc lại chuỗi ISO rẻ hơn nhiều so với hỏi CSDL
    thêm một lượt chỉ để lấy đúng cái ngày đó dưới dạng khác.
    """
    if not iso:
        return ''
    try:
        return date.fromisoformat(str(iso)[:10]).strftime('%d/%m/%Y')
    except ValueError:
        return str(iso)


# ── 1. Tiến độ lớp ──────────────────────────────────────────────────────────

def _phones(uids):
    """Số điện thoại của cả lớp trong MỘT lượt hỏi.

    ``reports._members`` không lấy cột này (màn hình báo cáo không hiện số điện
    thoại), mà file mang đi họp thì cần — trợ giảng gọi phụ huynh ngay từ bản
    in. Hỏi thêm một câu ở đây đúng hơn là sửa ``reports.py`` để mọi màn hình
    khác cùng phải tải theo dữ liệu cá nhân mà chúng không dùng.
    """
    if not uids:
        return {}
    rows = q('SELECT id, phone FROM users WHERE id = ANY(%s)', (list(uids),))
    return {r['id']: r['phone'] for r in rows}


def _absence_counts(class_id, uids):
    """Số buổi vắng / có phép của từng học viên trong lớp — MỘT câu cho cả lớp.

    Bọc ``DatabaseError`` theo đúng nếp của ``reports._events_by_user``: hai
    bảng §33 mới dựng 30/08, một bản triển khai chưa chạy bootstrap_schema vẫn
    phải tải được file tiến độ (cột chuyên cần để trống) thay vì nhận 500 —
    phần tiến độ học tập không liên quan gì tới điểm danh.
    """
    if not uids:
        return {}
    try:
        rows = q('''SELECT a.user_id,
                           COUNT(*) FILTER (WHERE a.status = 'absent')  AS absent,
                           COUNT(*) FILTER (WHERE a.status = 'excused') AS excused
                    FROM attendance a
                    JOIN class_sessions s ON s.id = a.session_id
                    WHERE s.class_id = %s AND a.user_id = ANY(%s)
                    GROUP BY a.user_id''', (class_id, list(uids)))
    except DatabaseError:
        return {}
    return {r['user_id']: r for r in rows}


class ClassProgressCsvView(APIView):
    """GET /api/teach/classes/<class_id>/export/progress.csv

    Ai mở file này: giảng viên phụ trách lớp và quản lý học vụ, trước buổi họp
    phụ huynh hoặc buổi review lớp — mỗi học viên một dòng, lọc theo cột "Cảnh
    báo sớm" để biết gọi ai trước.

    Toàn bộ con số lấy từ ``reports.class_report`` — CÙNG hàm dựng bảng điều
    khiển lớp trên màn hình. Đó là điều kiện để file in ra và màn hình nói cùng
    một chuyện.

    KHÔNG có cột "Điểm trung bình" dù đặc tả gợi ý, và đây là chủ ý:
    ``reports.py`` cố tình không tính một điểm trung bình duy nhất cho mỗi học
    viên. Năng lực ở đó đo THEO CHỦ ĐỀ, có ngưỡng dữ liệu tối thiểu
    (``MIN_ACTIVITIES``) và có suy giảm theo thời gian; bình quân hoá 20 chủ đề
    thành một số sẽ che mất đúng thông tin dùng được ("yếu ở Số học") và tạo ra
    một con số thứ hai không khớp bản đồ năng lực học viên tự nhìn thấy. Thay
    vào đó là "Tiến độ (%)", "Điểm thi thử gần nhất" và "Chủ đề yếu nhất" —
    đều là số ĐÃ có sẵn, không phải phép tính mới đẻ ra ở tệp này.
    """
    permission_classes = [IsTeacherOrAdmin]
    renderer_classes = CSV_RENDERERS

    def get(self, request, class_id):
        # Vào được khu vực giảng dạy KHÔNG có nghĩa là xem được mọi lớp.
        if not can_see_class(request.user, class_id):
            return Response(_NOT_FOUND, status=404)
        data = reports.class_report(class_id)
        if data is None:
            return Response(_NOT_FOUND, status=404)

        students = data['students']
        uids = [s['userId'] for s in students]
        phones = _phones(uids)
        absences = _absence_counts(class_id, uids)

        header = [
            'Họ tên', 'Email', 'Số điện thoại', 'Ngày vào lớp', 'Trạng thái',
            'Số bài đã hoàn thành', 'Tổng số bài', 'Tiến độ (%)',
            'Số lượt thi thử', 'Điểm thi thử gần nhất (%)',
            'Thay đổi so với lượt trước (%)',
            'Số buổi vắng', 'Số buổi có phép',
            'Hoạt động gần nhất', 'Số ngày không hoạt động',
            'Chậm so với kế hoạch (bài)', 'Chủ đề yếu nhất', 'Cảnh báo sớm',
        ]

        rows = []
        for s in students:
            att = absences.get(s['userId']) or {}
            weak = ' · '.join('%s %d%%' % (w['topic'], w['mastery'])
                              for w in s['weakest'])
            # Cảnh báo mức 'high' được đánh dấu để mắt người quét cột thấy ngay
            # em nào phải gọi TRƯỚC — một cột toàn câu chữ dài mà không phân
            # hạng thì đọc như nhau và rốt cuộc không ai được gọi.
            alerts = ' · '.join(
                ('(gấp) ' if a['level'] == 'high' else '') + a['text']
                for a in s['alerts'])
            rows.append([
                s['name'],
                s['email'],
                _phone_cell(phones.get(s['userId'])),
                _vn_date(s['joinedAt']),
                # Học viên đã rời lớp VẪN nằm trong file (báo cáo của kỳ đó phải
                # đủ người), chỉ đánh dấu rõ ở cột này để người đọc tự lọc.
                'Đã rời lớp' if s['left'] else 'Đang học',
                s['lessonsDone'],
                s['lessonsTotal'],
                s['progressPct'],
                s['mockCount'],
                s['lastMockPct'],
                s['mockTrend'],
                att.get('absent', 0),
                att.get('excused', 0),
                _vn_date(s['lastActive']),
                s['idleDays'],
                s['lag'],
                weak,
                alerts,
            ])

        # Lấy mã lớp từ báo cáo đã nạp thay vì hỏi CSDL thêm một lượt: dòng
        # `classes` đã nằm sẵn trong kết quả, hỏi lại là 245ms cho không.
        info = data['class']
        name = 'Tiến độ lớp %s %s.csv' % (
            _label_from(info['code'], info['name'], class_id), _stamp())
        return _csv_response(name, header, rows)


# ── 2. Điểm danh (bảng chéo) ────────────────────────────────────────────────

class ClassAttendanceCsvView(APIView):
    """GET /api/teach/classes/<class_id>/export/attendance.csv

    Ai mở file này: giảng viên và trợ giảng, để đối chiếu chuyên cần cuối tháng
    và in kèm khi báo cáo phụ huynh.

    DẠNG BẢNG CHÉO, không phải dạng dọc. Mỗi dòng một học viên, mỗi cột một
    buổi. Đây đúng là hình dạng cuốn sổ điểm danh giấy mà trung tâm đang dùng,
    nên họ mở ra là đọc được ngay. Xuất dạng dọc (mỗi lượt điểm danh một dòng)
    thì đúng về dữ liệu nhưng người nhận phải tự dựng PivotTable để nhìn ra một
    lớp — và họ sẽ không làm, họ sẽ quay về cuốn sổ giấy.

    BA CÂU TRUY VẤN, KHÔNG PHỤ THUỘC SĨ SỐ: một câu lấy buổi, một câu lấy học
    viên, một câu lấy TOÀN BỘ điểm danh của lớp; xoay bảng bằng Python. Hỏi theo
    từng học viên thì lớp 30 em × 30 buổi thành 900 lượt × 245ms ≈ 4 phút.
    """
    permission_classes = [IsTeacherOrAdmin]
    renderer_classes = CSV_RENDERERS

    def get(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response(_NOT_FOUND, status=404)

        sessions, marks = self._attendance_data(class_id)
        # Dùng lại đúng danh sách thành viên (và đúng thứ tự sắp xếp) của báo
        # cáo lớp thay vì viết câu SELECT thứ hai: hai định nghĩa "ai đang ở
        # trong lớp" sẽ trôi khỏi nhau ngay lần đầu một trong hai được sửa, và
        # khi đó sổ điểm danh thiếu người mà không ai nhận ra.
        members = reports._members(class_id)

        header = ['Họ tên', 'Email', 'Trạng thái']
        for s in sessions:
            header.append(self._session_label(s))
        header += ['Có mặt', 'Muộn', 'Vắng', 'Có phép',
                   'Chưa điểm danh', 'Tỉ lệ chuyên cần (%)']

        # Buổi đã huỷ không tính vào "chưa điểm danh": cột đó để trống là đúng,
        # không phải là việc còn tồn của giảng viên.
        held = [s for s in sessions if s['status'] != 'cancelled']

        rows = []
        for m in members:
            uid = m['user_id']
            row = [m['name'] or m['email'], m['email'],
                   'Đã rời lớp' if m['left_at'] else 'Đang học']
            counts = dict.fromkeys(ATTENDANCE_ORDER, 0)
            marked_held = 0
            for s in sessions:
                status = marks.get((s['id'], uid))
                # Ô TRỐNG khi chưa có dòng điểm danh — và đó là thông tin khác
                # hẳn "Vắng". Lấp trống bằng "Vắng" là vu cho học viên một buổi
                # nghỉ mà giảng viên chỉ đơn giản là chưa tick.
                row.append(ATTENDANCE_LABELS.get(status, status or ''))
                if status in counts:
                    counts[status] += 1
                    if s['status'] != 'cancelled':
                        marked_held += 1
            row += [counts[k] for k in ATTENDANCE_ORDER]
            row.append(max(0, len(held) - marked_held))
            row.append(self._rate(counts))
            rows.append(row)

        name = 'Điểm danh lớp %s %s.csv' % (_class_label(class_id), _stamp())
        return _csv_response(name, header, rows)

    @staticmethod
    def _attendance_data(class_id):
        """Buổi học + toàn bộ điểm danh của lớp. Hai câu, cố định.

        Bọc ``DatabaseError`` cùng lý do với ``_absence_counts``: hai bảng này
        mới dựng 30/08/2026 và HIỆN CHƯA CÓ DÒNG NÀO. Lớp chưa có buổi nào phải
        ra file chỉ có dòng tiêu đề + danh sách học viên, không được ném lỗi —
        đó là trạng thái của MỌI lớp trong tuần đầu dùng mô-đun điểm danh.
        """
        try:
            sessions = q('''SELECT id, starts_at, topic, status
                            FROM class_sessions
                            WHERE class_id = %s
                            ORDER BY starts_at, id''', (class_id,))
            rows = q('''SELECT a.session_id, a.user_id, a.status
                        FROM attendance a
                        JOIN class_sessions s ON s.id = a.session_id
                        WHERE s.class_id = %s''', (class_id,))
        except DatabaseError:
            return [], {}
        return sessions, {(r['session_id'], r['user_id']): r['status'] for r in rows}

    @staticmethod
    def _session_label(s):
        """Tiêu đề cột: ngày + giờ + chủ đề.

        Có cả giờ vì lớp online chạy nhiều ca trong ngày — hai buổi cùng ngày mà
        tiêu đề giống hệt nhau thì không đối chiếu được với lịch. Buổi huỷ được
        ghi rõ: một cột trống mà không nói vì sao sẽ bị đọc thành "cả lớp vắng".
        """
        when = s['starts_at']
        label = when.strftime('%d/%m %H:%M') if when else 'Chưa đặt lịch'
        topic = (s['topic'] or '').strip()
        if topic:
            label += ' · ' + topic
        if s['status'] == 'cancelled':
            label += ' (đã huỷ)'
        return label

    @staticmethod
    def _rate(counts):
        """Tỉ lệ chuyên cần = (có mặt + muộn) / số buổi ĐÃ ĐIỂM DANH.

        Mẫu số chỉ đếm buổi đã tick, không đếm buổi giảng viên chưa điểm danh:
        tính buổi chưa tick thành vắng sẽ kéo tỉ lệ của cả lớp xuống vì lý do
        hành chính, và con số đó lại đi vào báo cáo phụ huynh.

        "Có phép" NẰM TRONG mẫu số: nghỉ có phép vẫn là một buổi học em không có
        mặt, và cột này đo mức độ có mặt chứ không phải mức độ ngoan. Lý do nghỉ
        đã có cột "Có phép" ngay bên cạnh nói hộ.

        Chưa điểm danh buổi nào → ô TRỐNG chứ không phải 0%: "chưa có dữ liệu"
        và "không đi buổi nào" là hai chuyện khác nhau (cùng luật với
        ``common.events.pct``).
        """
        marked = sum(counts.values())
        if not marked:
            return ''
        return round((counts['present'] + counts['late']) * 100 / marked)


# ── 3. Danh sách tài khoản ──────────────────────────────────────────────────

class AdminUsersCsvView(APIView):
    """GET /api/admin/export/users.csv

    Ai mở file này: quản lý học vụ, để rà soát toàn bộ tài khoản trung tâm đã
    cấp — và đặc biệt để dựng DANH SÁCH GỌI NHẮC ĐỔI MẬT KHẨU (xem cột cuối).

    Nhận CÙNG bộ tham số lọc với ``GET /api/admin/users`` (``q``, ``role``,
    ``status``, ``class_id``) để nút "Xuất CSV" trên màn hình quản lý tài khoản
    xuất đúng cái đang nhìn thấy. Nếu file luôn là toàn bộ tài khoản trong khi
    màn hình đang lọc, người dùng sẽ tin file rồi gửi nhầm danh sách đi.

    KHÔNG BAO GIỜ xuất cột ``password``, kể cả dạng băm. File này đi qua Zalo,
    được in ra, để trên bàn — một cột băm mật khẩu trong đó là rò rỉ vĩnh viễn
    mà không thu hồi được. Cột duy nhất liên quan tới mật khẩu ở đây là "đã đổi
    hay chưa", tức một trạng thái, không phải một bí mật.

    Chưa ghi nhật ký kiểm toán cho lần xuất này: ``common/audit.py`` chốt phạm
    vi 30/08/2026 là chỉ ghi hành động SỬA, hành động XEM để lại chờ TopHSA chốt
    chính sách quyền riêng tư (đặc tả ERP §8.3). Đáng lưu ý vì đây là một lần
    ĐỌC nhạy cảm — kéo cả họ tên và số điện thoại ra khỏi hệ thống — nên khi
    §8.3 được chốt thì đây là chỗ đầu tiên phải thêm dòng nhật ký.
    """
    permission_classes = [IsAdminRole]
    renderer_classes = CSV_RENDERERS

    def get(self, request):
        # ĐÚNG bộ lọc của màn hình danh sách, không phải một bản chép lại.
        #
        # Trước 30/08/2026 tệp này tự dựng lấy một bộ điều kiện riêng, và hai bộ
        # đã lệch nhau thật: màn hình đưa ô tìm kiếm qua `norm_phone` trước khi
        # so, bản này thì `ILIKE` chuỗi thô. Đo được: tìm '+84 987 654 321' →
        # màn hình 1 kết quả, tệp CSV 0 kết quả. Trợ giảng lọc ra 30 em rồi tải
        # về 28 mà không có gì báo. Đúng cái khe `common/identity.py` sinh ra để
        # bịt, mọc lại ở tầng tìm kiếm.
        where, params = build_user_filters(request.query_params)
        filtered = any_user_filter(request.query_params)
        # Thứ tự sắp xếp cũng phải giống màn hình (`lower(coalesce(name,''))`),
        # không phải `name NULLS LAST`. Cùng một tập người mà xếp hai kiểu thì
        # trợ giảng dò từng dòng để đối chiếu tệp với bảng sẽ nhảy loạn.

        rows = q('''SELECT u.id, u.name, u.email, u.phone, u.role, u.status,
                           u.created_at, u.password_changed_at, u.must_change_password,
                           (SELECT string_agg(COALESCE(NULLIF(c.code, ''), c.name),
                                              ' · ' ORDER BY c.name)
                              FROM class_members m
                              JOIN classes c ON c.id = m.class_id
                             WHERE m.user_id = u.id AND m.left_at IS NULL) AS classes
                    FROM users u
                    WHERE %s
                    ORDER BY lower(coalesce(u.name, '')), u.id''' % where, params)

        header = ['Họ tên', 'Email', 'Số điện thoại', 'Vai trò', 'Trạng thái',
                  'Lớp đang theo học', 'Ngày tạo', 'Đã đổi mật khẩu chưa']
        data = [[
            r['name'],
            r['email'],
            _phone_cell(r['phone']),
            ROLE_LABELS.get(r['role'], r['role']),
            USER_STATUS_LABELS.get(r['status'], r['status']),
            r['classes'] or '',
            r['created_at'],
            self._password_state(r),
        ] for r in rows]

        # Ghi rõ "(đã lọc)" trong tên file: hai file cùng tên nằm cạnh nhau
        # trong thư mục Tải về, một file đủ và một file đã lọc, mà không phân
        # biệt được thì sớm muộn có người mang bản thiếu người đi họp.
        name = 'Danh sách tài khoản%s %s.csv' % (' (đã lọc)' if filtered else '',
                                                 _stamp())
        return _csv_response(name, header, data)

    @staticmethod
    def _password_state(row):
        """Trả lời một câu hỏi vận hành có thật, không phải một cột kỹ thuật.

        ``password_changed_at IS NULL`` = tài khoản VẪN dùng mật khẩu tạm do trợ
        giảng đặt và đọc qua điện thoại; trung tâm lọc đúng cột này để đi nhắc.

        Còn ``must_change_password`` bật trong khi đã từng đổi nghĩa là trợ
        giảng vừa ĐẶT LẠI mật khẩu — tài khoản quay về đúng tình trạng "người
        khác đang biết mật khẩu của em này", nên phải nằm trong cùng danh sách
        gọi nhắc. Gộp vào một cột chứ không tách hai vì người đọc chỉ cần một
        câu trả lời: có phải gọi em này không.
        """
        changed = row['password_changed_at']
        if not changed:
            return 'CHƯA — còn dùng mật khẩu tạm'
        if row['must_change_password']:
            return 'Đã đặt lại %s — chờ đổi' % changed.strftime('%d/%m/%Y')
        return 'Rồi · %s' % changed.strftime('%d/%m/%Y')
