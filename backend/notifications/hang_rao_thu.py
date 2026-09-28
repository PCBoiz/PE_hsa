"""HÀNG RÀO THƯ Ở MÁY DEV (§61, E2 — anh Sơn chốt 26/09/2026, quyết định số 3).

Hộp thư đi biến "gửi thư" thành một việc BỀN: xếp một dòng rồi một luồng nền tự lấy ra
gửi, thử lại khi lỗi. Đúng thứ ta muốn trên production — và đúng thứ NGUY HIỂM trên máy
dev, vì CSDL dev là bản chép của production: trong đó có email THẬT của học viên và phụ
huynh TopHSA. Một lượt `pytest`, một cú bấm "Gửi thông báo" trên localhost, một nhịp
`hop_thu.nhip` chạy nền — bất kỳ cái nào cũng đủ để một lá thư thật rời máy chủ.

`EMAIL_CHE_DO_THU=1` đã chặn được, nhưng nó là thứ chủ máy phải NHỚ đặt, và nó tắt luôn
đường gửi thật nên không dùng được cho e2e có ghi. Hàng rào này thì ngược: nó TỰ nhận ra
"đây không phải production" và CHẶN THEO ĐỊA CHỈ, nên đường gửi vẫn đi trọn (SMTP thật,
`sent`, dấu vết thật) tới những địa chỉ an toàn.

── CHẶN KHI NÀO ────────────────────────────────────────────────────────────

Dùng lại hàng rào CSDL sẵn có (`common/hang_rao_csdl.py`, nhận production qua TÊN điểm
cuối Neon): CSDL là production → hàng rào TẮT, thư đi như thường. CSDL không phải
production (dev, ci, CSDL rỗng) → hàng rào BẬT.

Nhận qua CSDL chứ không qua `DEBUG` hay một biến riêng, vì thứ quyết định "trong máy này
có email thật của ai" là CSDL đang nối, không phải cờ gỡ lỗi. Và đây là hàng rào đã có
người đo, có phép kiểm, và anh Sơn đã biết cách tắt (`CHO_PHEP_PRODUCTION=1`).

── ĐỊA CHỈ NÀO ĐI ĐƯỢC ─────────────────────────────────────────────────────

CHO PHÉP (khi hàng rào bật):
  · `@example.com` / `.org` / `.net` — tên miền RFC 2606 dành riêng cho ví dụ, không ai
    nhận được thư ở đó. Mọi phép kiểm trong repo dùng đuôi này.
  · email của tài khoản e2e — `E2E_EMAIL`, hoặc khoá `email` trong `.the/e2e.json`
    (tệp thẻ kiểm thử, không commit). CHỈ đọc khoá `email`; mật khẩu trong đó không bao
    giờ được đọc hay in.
  · danh sách trong `OUTBOX_DIA_CHI_CHO_PHEP` (ngăn bằng dấu phẩy; một mục bắt đầu bằng
    `@` là cả tên miền).

CÒN LẠI → `dropped` kèm lý do tiếng Việt, KHÔNG thử lại. Bỏ hẳn chứ không để `failed`:
`failed` là "thử lại sau", mà ở đây thử bao nhiêu lần cũng vẫn là địa chỉ ấy — để lại
thì hộp thư đi đầy việc sẽ không bao giờ xong, và nhịp nào cũng đi gõ lại SMTP.

Mặc định là TỪ CHỐI: quên đặt `E2E_EMAIL` thì tài khoản e2e không nhận được thư (phép
kiểm đỏ, thấy ngay), chứ không phải một lá thư lọt ra ngoài (không ai thấy). Hướng gãy
này là cố ý — cùng lý lẽ với `hang_rao_csdl`.

Zalo ZNS đi theo SỐ ĐIỆN THOẠI nên không có "tên miền ví dụ": khi hàng rào bật, ZNS chỉ
đi tới số trong `OUTBOX_SO_CHO_PHEP`. Trên máy dev hôm nay chưa có Zalo OA nên đường ấy
đã dừng sớm hơn ở `zalo.da_cau_hinh()`; hàng rào vẫn kiểm để lúc có OA không phải nhớ.
"""
import json
import os
from pathlib import Path

BIEN_DIA_CHI = 'OUTBOX_DIA_CHI_CHO_PHEP'
BIEN_SO = 'OUTBOX_SO_CHO_PHEP'
BIEN_E2E = 'E2E_EMAIL'

#: Tên miền RFC 2606 dành riêng cho tài liệu / ví dụ — không tồn tại hộp thư nào.
DUOI_VI_DU = ('@example.com', '@example.org', '@example.net')

#: Thẻ tài khoản kiểm thử (không commit). Chỉ đọc khoá `email`.
THE_E2E = '.the/e2e.json'


def bat() -> bool:
    """Hàng rào có hiệu lực? (CSDL đang nối KHÔNG phải production)."""
    from common.hang_rao_csdl import dang_tro_production
    return not dang_tro_production()


def _tach(chuoi):
    """Cắt một chuỗi ngăn bằng dấu phẩy thành danh sách đã hạ chữ.

    Nhận GIÁ TRỊ chứ không nhận TÊN biến, để mỗi lần đọc môi trường nằm ngay tại chỗ gọi
    với một hằng đọc ra được. Bản đầu nhận tên (`os.environ.get(bien)`) và cổng pre-push
    bắt được: bộ soát `common/tests_cau_hinh.py` đọc tên biến bằng AST để đối chiếu với
    `render.yaml`, nên một tên đi qua tham số là một biến KHÔNG ai soát — đúng lớp biến
    dễ bị quên khai nhất khi lên production.
    """
    return [m.strip().lower() for m in (chuoi or '').split(',') if m.strip()]


def _email_e2e():
    """Email tài khoản e2e: biến môi trường trước, rồi `.the/e2e.json`."""
    ra = []
    tu_bien = (os.environ.get(BIEN_E2E) or '').strip().lower()
    if tu_bien:
        ra.append(tu_bien)
    # backend/notifications/hang_rao_thu.py → gốc repo là ba bậc lên.
    p = Path(__file__).resolve().parent.parent.parent / THE_E2E
    try:
        if p.is_file():
            e = (json.loads(p.read_text(encoding='utf-8')).get('email') or '').strip().lower()
            if e:
                ra.append(e)
    except (OSError, ValueError):
        pass                       # thẻ hỏng / không đọc được: coi như không có
    return ra


def dia_chi_cho_phep():
    """Mọi địa chỉ / tên miền email đi được khi hàng rào bật (đã hạ chữ)."""
    return list(DUOI_VI_DU) + _email_e2e() + _tach(os.environ.get(BIEN_DIA_CHI))


def _khop(dia_chi, cho_phep):
    d = (dia_chi or '').strip().lower()
    return any(d.endswith(m) if m.startswith('@') else d == m for m in cho_phep)


def ly_do_chan(channel, dia_chi):
    """Lý do tiếng Việt nếu KHÔNG được gửi tới `dia_chi`; None nếu đi được.

    Gọi ở `hop_thu._gui_email` / `_gui_zalo`, TRƯỚC khi mở SMTP."""
    if not bat():
        return None
    if channel == 'zalo':
        if _khop(dia_chi, _tach(os.environ.get(BIEN_SO))):
            return None
        return ('Máy này không nối CSDL production nên hàng rào thư đang bật: tin Zalo chỉ '
                'đi tới số trong %s. Số %s không có trong danh sách nên không gửi.'
                % (BIEN_SO, _che(dia_chi)))
    if _khop(dia_chi, dia_chi_cho_phep()):
        return None
    return ('Máy này không nối CSDL production nên hàng rào thư đang bật: chỉ gửi tới '
            '@example.com, email tài khoản kiểm thử, hoặc địa chỉ trong %s. Địa chỉ %s '
            'không có trong danh sách nên không gửi (đây là địa chỉ thật của một người — '
            'muốn gửi thật thì thêm vào %s).' % (BIEN_DIA_CHI, _che(dia_chi), BIEN_DIA_CHI))


def _che(dia_chi):
    """Che phần giữa để lý do lỗi (vào cột `error`, hiện trên màn quản trị) không thành
    một chỗ chép email học viên thật ra. Giữ đủ để người trực nhận ra là ai."""
    d = (dia_chi or '').strip()
    if '@' in d:
        ten, mien = d.split('@', 1)
        return '%s***@%s' % (ten[:2], mien)
    return '%s***%s' % (d[:3], d[-2:]) if len(d) > 5 else '***'
