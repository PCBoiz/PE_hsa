"""Hỏi thẳng Zalo xem một access token OA làm được những gì.

── VÌ SAO CÓ LỆNH NÀY (07/09/2026) ─────────────────────────────────────────

Anh Sơn không xác thực được OA vì Zalo đòi giấy phép kinh doanh, mà đây mới là
thử nghiệm. Câu hỏi còn lại: **OA chưa xác thực có gửi được tin không?**

Tài liệu công khai không phân xử được — ba nguồn nói ba kiểu (xem chú thích
đầu phần OA trong `common/zalo.py`). Suy tiếp từ tài liệu mâu thuẫn thì ra một
kết luận nghe rất chắc mà sai, và lần này cái sai ấy tốn của anh 14 ngày: OA
tạo ra mà không nộp hồ sơ xác thực trong 14 ngày thì Zalo KHOÁ, và OA đã khoá
thì không mở lại.

Nên lệnh này không suy. Nó gọi thật, rồi in đúng chữ Zalo trả lời.

    python manage.py chan_doan_oa --token <access_token>

Ba bước, dừng ở bước hỏng đầu tiên vì bước sau vô nghĩa nếu bước trước hỏng:

    1. token còn sống không, và OA này ĐÃ XÁC THỰC chưa  (v2.0/oa/getoa)
    2. có ai đang quan tâm OA không                      (v2.0/oa/getfollowers)
    3. gửi thử MỘT tin tư vấn                            (v3.0/oa/message/cs)

── BƯỚC 3 KHÔNG TỰ CHẠY ───────────────────────────────────────────────────

Bước 1 và 2 chỉ ĐỌC. Bước 3 gửi một tin thật vào Zalo của một người thật, nên
nó đòi `--gui-toi <user_id>` viết rõ ràng — và in nguyên thân request trước
khi gửi. `ZALO_CHE_DO_THU=1` thì bước 3 in ra rồi dừng, không gọi Zalo.

── KHÔNG IN TOKEN ─────────────────────────────────────────────────────────

Token OA là chìa mở toàn quyền nhắn tin dưới tên trung tâm. Lệnh này in vài ký
tự đầu/cuối đủ để đối chiếu "đúng token tôi vừa dán không", chứ không in cả
chuỗi: đầu ra của lệnh sẽ bị chép vào chat, vào tài liệu, vào ảnh chụp màn hình.
"""
import json
import os

from django.core.management.base import BaseCommand

from common import zalo


def _che(token: str) -> str:
    """Vài ký tự đầu/cuối, đủ để đối chiếu mà không lộ chìa."""
    if not token:
        return '(trống)'
    if len(token) <= 14:
        return '%s… (%d ký tự — ngắn bất thường)' % (token[:4], len(token))
    return '%s…%s (%d ký tự)' % (token[:6], token[-4:], len(token))


class Command(BaseCommand):
    help = 'Đo xem một access token Zalo OA làm được gì (đọc; chỉ gửi khi có --gui-toi).'

    def add_arguments(self, ap):
        ap.add_argument('--token', default='',
                        help='access token của OA. Bỏ trống thì đọc ZALO_OA_ACCESS_TOKEN.')
        ap.add_argument('--gui-toi', default='',
                        help='user_id người nhận — CÓ cờ này mới gửi thật một tin tư vấn.')
        ap.add_argument('--chu', default='TopHSA thử kết nối — tin do người quản trị gửi tay.',
                        help='nội dung tin thử ở bước 3')

    def _in_json(self, nhan, d):
        self.stdout.write('  %s' % nhan)
        for dong in json.dumps(d, ensure_ascii=False, indent=2).split('\n'):
            self.stdout.write('    ' + dong)

    def handle(self, *a, **o):
        token = (o['token'] or os.environ.get('ZALO_OA_ACCESS_TOKEN') or '').strip()

        self.stdout.write('')
        self.stdout.write('  token       : %s' % _che(token))
        self.stdout.write('  gốc API     : %s' % zalo.API_OA)
        self.stdout.write('  chế độ thử  : %s' % zalo.che_do_thu())
        self.stdout.write('')

        if not token:
            self.stderr.write(
                'DỪNG: chưa có token. Truyền --token <chuỗi>, hoặc đặt biến môi trường '
                'ZALO_OA_ACCESS_TOKEN. Lấy token ở developers.zalo.me sau khi đã tạo OA '
                'và một Ứng dụng, rồi uỷ quyền Ứng dụng cho OA.')
            return

        # ── BƯỚC 1 ──────────────────────────────────────────────────────
        self.stdout.write('  ── 1. TOKEN & HỒ SƠ OA (v2.0/oa/getoa) ──')
        ok, d, loi = zalo.thong_tin_oa(token)
        if not ok:
            self.stdout.write('  ✗ %s' % loi)
            if d:
                self._in_json('Zalo trả về:', d)
            self.stdout.write('')
            self.stderr.write(
                'DỪNG ở bước 1. Token không gọi được API nào, nên hai bước sau vô nghĩa. '
                'Mã -216 nghĩa là token sai hoặc đã hết hạn (token OA sống 25 giờ, phải '
                'làm mới bằng refresh token).')
            return

        d = d or {}
        da_xac_thuc = d.get('is_verified')
        self.stdout.write('  ✓ token sống')
        self.stdout.write('    tên OA      : %s' % (d.get('name') or '—'))
        self.stdout.write('    oa_id       : %s' % (d.get('oa_id') or '—'))
        self.stdout.write('    đã xác thực : %s' % (
            '—  (Zalo không trả trường is_verified)' if da_xac_thuc is None else da_xac_thuc))
        self.stdout.write('    gói dịch vụ : %s' % (d.get('package_name') or '—'))
        self.stdout.write('')

        # ── BƯỚC 2 ──────────────────────────────────────────────────────
        self.stdout.write('  ── 2. NGƯỜI QUAN TÂM (v2.0/oa/getfollowers) ──')
        ok2, d2, loi2 = zalo.nguoi_quan_tam(token, so=5)
        if not ok2:
            self.stdout.write('  ✗ %s' % loi2)
            if d2:
                self._in_json('Zalo trả về:', d2)
        else:
            d2 = d2 or {}
            ds = d2.get('followers') or []
            self.stdout.write('  ✓ tổng số người quan tâm: %s' % d2.get('total', '—'))
            for f in ds[:5]:
                self.stdout.write('    user_id %s' % (f.get('user_id') if isinstance(f, dict) else f))
            if not ds:
                self.stdout.write('    (chưa ai quan tâm OA — chưa có user_id nào để gửi thử)')
        self.stdout.write('')

        # ── BƯỚC 3 ──────────────────────────────────────────────────────
        nhan = (o['gui_toi'] or '').strip()
        if not nhan:
            self.stdout.write('  ── 3. GỬI THỬ ──')
            self.stdout.write('  (bỏ qua — thêm --gui-toi <user_id> mới gửi. '
                              'Lấy user_id ở bước 2, hoặc bảo người ta nhắn cho OA trước.)')
            self.stdout.write('')
            self._ket_luan(da_xac_thuc, None)
            return

        self.stdout.write('  ── 3. GỬI THỬ MỘT TIN TƯ VẤN (v3.0/oa/message/cs) ──')
        self._in_json('thân request sẽ gửi:', zalo.soan_tin_tu_van(nhan, o['chu']))
        ok3, ma, loi3 = zalo.gui_tin_tu_van(nhan, o['chu'], token=token)
        self.stdout.write('  thành công : %s' % ok3)
        self.stdout.write('  mã tin     : %s' % (ma or '—'))
        self.stdout.write('  lỗi        : %s' % (loi3 or '—'))
        if ok3 and str(ma or '').startswith('THU:'):
            self.stdout.write('  ("THU:" nghĩa là CHẾ ĐỘ THỬ — không có tin nào rời máy chủ.)')
            # Chế độ thử KHÔNG chứng minh được gì về quyền gửi: nó dừng trước
            # khi Zalo kịp có ý kiến. Hạ về `None` để phần kết luận nói đúng
            # là "chưa biết", thay vì khoe một chiến thắng của chính mình.
            ok3 = None
        self.stdout.write('')
        self._ket_luan(da_xac_thuc, ok3)

    def _ket_luan(self, da_xac_thuc, gui_duoc):
        """Nói thẳng cái vừa ĐO được, và nói rõ cái CHƯA đo được.

        Bước quan trọng nhất của lệnh này. Không có nó thì người đọc tự suy từ
        ba khối đầu ra rời rạc — mà đúng kiểu suy ấy là thứ lệnh này sinh ra
        để thay thế.
        """
        self.stdout.write('  ── KẾT LUẬN ĐO ĐƯỢC ──')
        if da_xac_thuc is False:
            self.stdout.write('  · OA này CHƯA xác thực, và token vẫn gọi được API đọc.')
        elif da_xac_thuc is True:
            self.stdout.write('  · OA này ĐÃ xác thực — nên kết quả dưới đây KHÔNG nói được '
                              'gì về OA chưa xác thực.')
        if gui_duoc is True:
            self.stdout.write('  · GỬI ĐƯỢC tin tư vấn. Đường "phụ huynh nhắn OA trước rồi '
                              'hệ thống gửi link báo cáo" là đường đi được.')
        elif gui_duoc is False:
            self.stdout.write('  · KHÔNG gửi được. Đọc câu lỗi ở bước 3 — đó là lý do thật '
                              'của Zalo, không phải phỏng đoán.')
        else:
            self.stdout.write('  · Chưa thử gửi, nên CHƯA biết OA này có gửi được tin không. '
                              'Hai bước đầu chỉ chứng minh token đọc được.')
        self.stdout.write('')
