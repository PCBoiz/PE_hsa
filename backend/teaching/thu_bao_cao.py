"""Soạn lá thư báo cáo gửi phụ huynh: tóm tắt + PDF đính kèm + đường dẫn.

── VÌ SAO BA THỨ CHỨ KHÔNG PHẢI MỘT (07/09/2026, anh Sơn chốt) ─────────────

Được hỏi giữa "chỉ đường dẫn", "tóm tắt + đường dẫn" và "toàn bộ tờ trong
thư", anh chọn **tóm tắt + tệp PDF**. Mỗi phần làm một việc khác nhau:

  · **Tóm tắt trong thân thư** — phụ huynh mở thư trên điện thoại giữa lúc bận
    và thường không bấm gì thêm. Vài con số ngay trong thư đảm bảo dù họ không
    bấm gì thì vẫn biết con đi học đều không và đang yếu chỗ nào.
  · **PDF đính kèm** — bản đầy đủ, in ra được, mang đi họp phụ huynh được, và
    còn nguyên khi đường dẫn đã hết hạn. Đặc tả ERP §6 ghi thẳng là bắt buộc.
  · **Đường dẫn** — bản luôn mới. Điểm danh sửa sau khi gửi thì đường dẫn hiện
    số đúng, còn PDF thì giữ số của lúc gửi. Nói rõ điều đó trong thư.

── VÌ SAO KHÔNG NHÉT CẢ TỜ VÀO THÂN THƯ ───────────────────────────────────

Đó là lựa chọn thứ ba anh không chọn, và lý do đáng ghi lại: điểm số và danh
sách chủ đề yếu của một đứa trẻ nằm VĨNH VIỄN trong hộp thư, chuyển tiếp một
cái là lộ, và không thu hồi được. PDF đính kèm cũng nằm trong hộp thư — nhưng
nó là một tệp người ta phải cố ý mở và cố ý chuyển đi, chứ không phải thứ hiện
ra trong khung xem trước của mọi ứng dụng thư.

── HTML CỦA THƯ VIẾT KIỂU 2005, CÓ CHỦ ĐÍCH ───────────────────────────────

Bảng lồng bảng, `style` nội tuyến, không `flex`, không `grid`, không tệp CSS
ngoài. Outlook trên Windows dựng HTML bằng bộ dựng của Word, Gmail cắt bỏ thẻ
`<style>` trong nhiều hoàn cảnh, và ứng dụng thư trên điện thoại thì mỗi hãng
một kiểu. Viết đẹp theo chuẩn hiện đại ở đây nghĩa là tờ thư vỡ ở đúng nơi
người nhận đang đọc.
"""
from datetime import date

from teaching.bao_cao_pdf import DAI, dung_pdf


def _ngay(s) -> str:
    if not s:
        return '—'
    try:
        return date.fromisoformat(str(s)[:10]).strftime('%d/%m/%Y')
    except ValueError:
        return str(s)


def _ten_tep(bc) -> str:
    """Tên tệp PDF phụ huynh nhìn thấy trong hộp thư.

    Có TÊN CON và KỲ trong tên tệp: phụ huynh có hai đứa học ở đây, hoặc lưu
    báo cáo của nhiều kỳ, thì "bao-cao.pdf" lần thứ hai đè lên lần thứ nhất
    khi tải về. Bỏ dấu vì một số ứng dụng thư trên điện thoại vẫn làm hỏng tên
    tệp có dấu.
    """
    import unicodedata
    ten = (bc.get('student') or {}).get('name') or 'hoc-vien'
    khong_dau = ''.join(c for c in unicodedata.normalize('NFD', ten)
                        if unicodedata.category(c) != 'Mn').replace('đ', 'd').replace('Đ', 'D')
    gon = '-'.join(khong_dau.lower().split())
    gon = ''.join(c for c in gon if c.isalnum() or c == '-')[:40]
    ky = (bc.get('period') or {}).get('to') or ''
    return 'bao-cao-%s-%s.pdf' % (gon or 'hoc-vien', str(ky)[:10])


def _diem_yeu(bc):
    """Tối đa hai chủ đề yếu nhất, cho phần tóm tắt.

    Hai chứ không phải ba như trong PDF: thân thư đọc trên điện thoại, và một
    danh sách dài trong đoạn tóm tắt biến thành thứ người ta lướt qua — đúng
    cái mà tóm tắt sinh ra để tránh.
    """
    return sorted((bc.get('topics') or {}).get('weak') or [],
                  key=lambda t: t.get('mastery') or 0)[:2]


def soan_thu(bc: dict, duong_dan: str | None = None):
    """Trả `(tiêu_đề, chữ_thuần, html, đính_kèm)` — vừa đủ cho `common.mail.gui`.

    KHÔNG chạm CSDL, KHÔNG kiểm quyền, KHÔNG gửi: nơi gọi lo cả ba. Nhờ thế
    hàm này kiểm được bằng dữ liệu dựng tay.
    """
    em = bc.get('student') or {}
    lop = bc.get('class') or {}
    ky = bc.get('period') or {}
    cc = bc.get('attendance') or {}
    ht = bc.get('study') or {}

    ten = em.get('name') or 'học viên'
    ky_chu = '%s – %s' % (_ngay(ky.get('from')), _ngay(ky.get('to')))
    tieu_de = 'Báo cáo học tập của %s — kỳ %s' % (ten, ky_chu)

    co_mat = (cc.get('present') or 0) + (cc.get('late') or 0)
    da_tick = cc.get('sessionsCounted') or 0
    # "chưa thi lần nào" chứ KHÔNG phải "0 điểm" — ranh giới 3 của
    # `parent_report.py`. Viết 0 ở đây đọc như con làm sai hết.
    diem = ('%d%%' % ht['mockAvg']) if ht.get('mockAvg') is not None else 'chưa thi lần nào'
    yeu = _diem_yeu(bc)

    dong = [
        ('Chuyên cần', '%d/%d buổi đã điểm danh' % (co_mat, da_tick)),
        ('Bài đã hoàn thành', '%d bài' % (ht.get('lessonsDone') or 0)),
        ('Điểm thi thử trung bình', diem),
    ]
    if yeu:
        dong.append(('Cần chú ý',
                     ', '.join('%s (%d%%)' % (t.get('topic') or '', t.get('mastery') or 0)
                               for t in yeu)))

    chua_tick = cc.get('sessionsUnmarked') or 0

    # ── phần CHỮ THUẦN ──────────────────────────────────────────────────
    d = ['Kính gửi phụ huynh em %s,' % ten, '',
         'Đây là báo cáo học tập kỳ %s tại lớp %s.' % (ky_chu, lop.get('name') or ''), '']
    d += ['- %s: %s' % (a, b) for a, b in dong]
    if chua_tick:
        d += ['', '(Lớp còn %d buổi đã diễn ra mà chưa điểm danh, nên chưa tính '
              'vào con số chuyên cần trên.)' % chua_tick]
    d += ['', 'Bản đầy đủ nằm trong tệp PDF đính kèm.']
    if duong_dan:
        d += ['Bản luôn cập nhật: %s' % duong_dan]
    d += ['', 'Có chỗ nào chưa đúng, xin nhắn lại cho giảng viên phụ trách lớp.',
          '', 'TopHSA']
    chu = '\n'.join(d)

    # ── phần HTML ───────────────────────────────────────────────────────
    from xml.sax.saxutils import escape as e

    hang = ''.join(
        '<tr>'
        '<td style="padding:7px 10px 7px 0;color:#6B6B78;font-size:14px;'
        'border-bottom:1px solid #E6E6EE;vertical-align:top">%s</td>'
        '<td style="padding:7px 0;color:#2B2B33;font-size:14px;font-weight:bold;'
        'border-bottom:1px solid #E6E6EE;vertical-align:top">%s</td></tr>'
        % (e(a), e(b)) for a, b in dong)

    luu_y = ''
    if chua_tick:
        luu_y = ('<p style="margin:14px 0 0;color:#6B6B78;font-size:13px;line-height:1.5">'
                 'Lớp còn <b>%d buổi đã diễn ra mà giảng viên chưa điểm danh</b>, nên chưa '
                 'tính vào con số chuyên cần ở trên.</p>' % chua_tick)

    nut = ''
    if duong_dan:
        nut = ('<p style="margin:22px 0 0"><a href="%s" '
               'style="background:#4B3FBF;color:#ffffff;text-decoration:none;'
               'display:inline-block;padding:12px 20px;border-radius:6px;'
               'font-size:15px;font-weight:bold">Xem bản đầy đủ</a></p>'
               '<p style="margin:8px 0 0;color:#8A8A96;font-size:12px">'
               'Đường dẫn này có hạn dùng và chỉ dành cho phụ huynh em %s.</p>'
               % (e(duong_dan), e(ten)))

    html = (
        '<div style="margin:0;padding:24px 12px;background:#F4F3FA;'
        'font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif">'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'width="100%%" style="max-width:600px;margin:0 auto;background:#ffffff;'
        'border-radius:10px;border:1px solid #E6E6EE"><tr><td style="padding:26px">'
        '<p style="margin:0 0 2px;color:#4B3FBF;font-size:12px;font-weight:bold;'
        'letter-spacing:.08em">TOPHSA</p>'
        '<h1 style="margin:0 0 4px;color:#2B2B33;font-size:20px;line-height:1.3">'
        'Báo cáo học tập của %(ten)s</h1>'
        '<p style="margin:0 0 18px;color:#6B6B78;font-size:14px">'
        '%(lop)s &middot; kỳ %(ky)s</p>'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'width="100%%">%(hang)s</table>'
        '%(luu_y)s'
        '<p style="margin:18px 0 0;color:#2B2B33;font-size:14px;line-height:1.55">'
        'Bản đầy đủ — chuyên cần từng buổi, tiến độ từng hợp phần và toàn bộ chủ đề '
        'đã đo — nằm trong <b>tệp PDF đính kèm</b> thư này.</p>'
        '%(nut)s'
        '<p style="margin:22px 0 0;padding-top:16px;border-top:1px solid #E6E6EE;'
        'color:#8A8A96;font-size:12px;line-height:1.55">'
        'Số trong PDF là số tại thời điểm gửi; đường dẫn ở trên luôn hiện bản mới nhất. '
        'Có chỗ nào chưa đúng, xin nhắn lại cho giảng viên phụ trách lớp — số liệu sai '
        'sửa được, và sửa sớm thì kỳ sau đúng.</p>'
        '</td></tr></table></div>'
    ) % {'ten': e(ten), 'lop': e(lop.get('name') or ''), 'ky': e(ky_chu),
         'hang': hang, 'luu_y': luu_y, 'nut': nut}

    dinh_kem = ((_ten_tep(bc), 'application/pdf', dung_pdf(bc)),)
    return tieu_de, chu, html, dinh_kem


#: Tái xuất để nơi gọi khỏi phải nhập từ hai chỗ khi chỉ cần các dải nhận xét.
__all__ = ['soan_thu', 'DAI']
