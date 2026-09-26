"""HỘP THƯ ĐI (outbox, §61a — E2, 25/09/2026).

Trước đây mỗi nơi gửi thư tự mở một luồng rời trong tiến trình web: SMTP lỗi thì chỉ
có một dòng nhật ký, worker khởi động lại (deploy, Render ngủ) là mất thư. Từ đây:

  · nơi gửi GHI một dòng `outbox` trong CÙNG giao dịch với việc chính (`xep`) — giao
    dịch cuộn lại thì không có thư nào về một việc không xảy ra;
  · sau commit, `day_di` đánh thức một lượt gửi ngay (thư quên mật khẩu không phải chờ
    nhịp kế), còn lỗi thì thư NẰM LẠI và được thử lại theo lịch lùi.

── NHẬN VIỆC ───────────────────────────────────────────────────────────────

MỘT câu `UPDATE … WHERE id IN (SELECT … FOR UPDATE SKIP LOCKED LIMIT n) RETURNING *`
(`CAU_NHAN`): hai máy chạy cùng lúc thì máy sau bỏ qua dòng máy trước đang giữ, và
dòng đã chuyển 'sending' không lọt vào lượt hỏi sau. Không dùng khoá phiên kiểu
"advisory": Neon đi qua pooler theo giao dịch, khoá phiên dính vào một kết nối thật mà
lượt sau không chắc quay lại đúng kết nối ấy.

Dòng 'sending' quá `TREO_PHUT` phút (máy gửi chết giữa chừng) được nhận lại. Thư có
thể đi HAI lần trong ca ấy — chấp nhận: mất thư tệ hơn trùng thư.

── THỬ LẠI ─────────────────────────────────────────────────────────────────

Lỗi lần n → 'failed', thử lại sau `BACKOFF_PHUT[n-1]` phút (1', 5', 30', 2h, 6h). Hết
lượt lùi → 'dropped'. Lỗi VĨNH VIỄN (địa chỉ hỏng, kênh chưa cấu hình, thư quá hạn, hàng
rào máy dev) → 'dropped' ngay, lý do ở `error`. Zalo ZNS chỉ đi khi đã có OA
(`zalo.da_cau_hinh`).

── ƯU TIÊN + TRẦN NGÀY (anh Sơn chốt 26/09/2026) ────────────────────────────

`outbox.priority`: 0 = thư GIAO DỊCH (một người đang chờ đúng lá thư ấy), 1 = thư HÀNG
LOẠT. Mỗi lượt nhận việc lấy hết phần giao dịch tới lượt TRƯỚC, chỗ còn lại mới tới hàng
loạt — và chỉ tới phần `con_lai_hang_loat()` của trần ngày (`OUTBOX_TRAN_HANG_LOAT_NGAY`,
mặc định 300, dưới hạn Gmail ~500). Vượt trần thì dòng NẰM LẠI 'queued', sang ngày sau đi
tiếp; không `dropped` — một thông báo cả khối bị bỏ im lặng tệ hơn là tới muộn một ngày.

── HÀNG RÀO THƯ Ở MÁY DEV ──────────────────────────────────────────────────

CSDL đang nối không phải production → thư CHỈ đi tới địa chỉ an toàn, còn lại 'dropped'
kèm lý do tiếng Việt. Luật và lý lẽ: `notifications/hang_rao_thu.py`. Hàng rào nằm ở
`_gui_email` / `_gui_zalo`, TRƯỚC khi dựng thư và trước khi mở SMTP.

── NGƯỜI CHẠY ──────────────────────────────────────────────────────────────

`nhip()` = một nhịp: quét nhắc hạn nộp (`nhac_han.quet`) rồi gửi hết việc tới lượt. Ba
nơi gọi: luồng nền trong tiến trình (`ENABLE_OUTBOX=1`, mẫu `common/keepalive.py`), lệnh
`manage.py gui_hop_thu`, và `POST /api/noi-bo/tick` cho máy gọi ngoài (cron-job.org) —
Render gói rẻ ngủ khi vắng khách, luồng nền ngủ theo, nên cần một nhịp từ bên ngoài.

── LOẠI THƯ DỰNG LẠI LÚC GỬI ───────────────────────────────────────────────

Thư có tệp đính kèm (báo cáo phụ huynh kèm PDF) không lưu tệp trong CSDL: `params.loai`
trỏ tới một mô-đun trong `LOAI` có `dung_thu_outbox(dong)` (dựng lại thư) và tuỳ chọn
`sau_gui_outbox(dong, trang_thai, dau_vet, loi)` (mô-đun ấy tự ghi sổ của nó — hộp thư
đi không ghi bảng miền khác).
"""
import importlib
import json
import logging
import os
import threading
import time
from datetime import datetime

from django.db import connection, transaction
from django.utils import timezone

from common import mail, zalo
from common.db import q, q1
from notifications import hang_rao_thu

log = logging.getLogger(__name__)

#: Khoảng lùi (phút) sau lần lỗi thứ 1, 2, … Hết dãy → bỏ.
BACKOFF_PHUT = (1, 5, 30, 120, 360)
#: Dòng 'sending' lâu hơn chừng này phút = máy gửi đã chết → nhận lại.
TREO_PHUT = 10
#: Số việc một lần nhận.
MOT_LUOT = 20
#: Chu kỳ luồng nền (giây).
CHU_KY_GIAY = 60

#: `outbox.priority` — xem §61a. GIAO_DỊCH đi TRƯỚC trong mỗi lượt nhận việc.
GIAO_DICH = 0
HANG_LOAT = 1
#: Trần thư HÀNG LOẠT mỗi ngày (giờ VN). Đặt 0 = hôm nay không gửi thư hàng loạt nào.
BIEN_TRAN = 'OUTBOX_TRAN_HANG_LOAT_NGAY'
TRAN_HANG_LOAT_MAC_DINH = 300

#: Loại thư dựng lại lúc gửi → mô-đun có `dung_thu_outbox` (xem chú thích đầu tệp).
LOAI = {
    'bao_cao_phu_huynh': 'teaching.thu_bao_cao',
}

#: 0h00 hôm nay GIỜ VIỆT NAM, đổi về ĐÚNG đồng hồ mà `sent_at`/`claimed_at` đang ghi.
#:
#: Không viết mốc này ở Python: `sent_at = now()` đi qua `SET TIME ZONE` của phiên (Django
#: đặt UTC vì `USE_TZ=True`), nên cột giữ giờ UTC không múi — đo 26/09/2026: phiên `UTC`,
#: `now()` = 00:41 ngày 26 trong khi `local_now()` = 07:41. So một mốc naive dựng ở Python
#: theo giờ VN với cột ấy là lệch 7 tiếng, đúng cái lỗi `common/clock.py` mô tả. Câu dưới
#: đi VÒNG QUA cùng một phép đổi: giờ VN → mốc tuyệt đối → giờ của phiên. Đúng với mọi
#: `TimeZone` của phiên, không cắm cứng số 7.
DAU_NGAY_VN = ("(date_trunc('day', now() AT TIME ZONE 'Asia/Ho_Chi_Minh')"
               " AT TIME ZONE 'Asia/Ho_Chi_Minh')::timestamp")

CAU_NHAN = '''
    UPDATE outbox SET status = 'sending', claimed_at = now(), attempts = attempts + 1
     WHERE id IN (
           SELECT id FROM outbox
            WHERE ((status IN ('queued', 'failed') AND next_try_at <= now())
                   OR (status = 'sending' AND claimed_at < now() - make_interval(mins => %(treo)s)))
              AND (%(ids)s::bigint[] IS NULL OR id = ANY(%(ids)s::bigint[]))
              AND priority = %(uu_tien)s
            ORDER BY next_try_at, id
            LIMIT %(n)s
              FOR UPDATE SKIP LOCKED)
    RETURNING *'''


def xep(channel, to_addr, subject='', body='', *, user_id=None, params=None,
        source=(None, None), dedup=None, uu_tien=GIAO_DICH):
    """Ghi MỘT việc gửi. Trả id, hoặc None khi `dedup` đã có (việc ấy đã xếp rồi).

    `uu_tien`: `GIAO_DICH` (mặc định — một người đang chờ đúng lá thư này) hoặc
    `HANG_LOAT` (thư cả lớp / cả khối, chịu trần ngày). Xem §61a.

    Gọi TRONG giao dịch của việc chính; sau commit gọi `day_di([id])` để gửi sớm."""
    r = q1('''INSERT INTO outbox (channel, user_id, to_addr, subject, body, params,
                                  source_type, source_id, dedup_key, priority)
              VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
              ON CONFLICT (dedup_key) DO NOTHING RETURNING id''',
           (channel, user_id, to_addr or '', subject or '', body or '',
            json.dumps(params or {}, ensure_ascii=False), source[0], source[1], dedup,
            HANG_LOAT if uu_tien == HANG_LOAT else GIAO_DICH))
    return r['id'] if r else None


def tran_hang_loat():
    """Trần thư HÀNG LOẠT mỗi ngày. Biến hỏng / âm → mặc định (thà gửi đúng luật hơn là
    mở toang vì một biến gõ sai)."""
    v = (os.environ.get(BIEN_TRAN) or '').strip()
    if not v:
        return TRAN_HANG_LOAT_MAC_DINH
    try:
        n = int(v)
    except ValueError:
        log.warning('[hop_thu] %s = %r không phải số — dùng mặc định %d',
                    BIEN_TRAN, v, TRAN_HANG_LOAT_MAC_DINH)
        return TRAN_HANG_LOAT_MAC_DINH
    return n if n >= 0 else TRAN_HANG_LOAT_MAC_DINH


def con_lai_hang_loat():
    """Hôm nay (giờ VN) còn gửi thêm được bao nhiêu thư HÀNG LOẠT.

    Đếm cả dòng 'sending' đã nhận trong ngày: hai máy chạy cùng lúc thì mỗi máy thấy phần
    máy kia ĐANG gửi, nên không cùng nhau vượt trần. Vẫn còn khe hở đúng bằng một lượt
    (`MOT_LUOT`) khi hai máy hỏi trước khi cả hai kịp nhận — trần 300 nằm dưới hạn Gmail
    ~500 chính là để chỗ cho khe ấy."""
    tran = tran_hang_loat()
    if tran <= 0:
        return 0
    da = q1('''SELECT count(*) AS n FROM outbox
                WHERE priority = %%s
                  AND ((status = 'sent' AND sent_at >= %s)
                       OR (status = 'sending' AND claimed_at >= %s))''' % (DAU_NGAY_VN, DAU_NGAY_VN),
            (HANG_LOAT,))['n']
    return max(0, tran - da)


def _nhan_theo_uu_tien(uu_tien, n, ids):
    if n <= 0:
        return []
    return q(CAU_NHAN, {'n': n, 'ids': list(ids) if ids is not None else None,
                        'treo': TREO_PHUT, 'uu_tien': uu_tien})


def nhan_viec(n=MOT_LUOT, ids=None):
    """Nhận tối đa `n` việc tới lượt (chỉ trong `ids` nếu truyền). Câu tự commit khi
    đứng ngoài giao dịch — máy khác thấy ngay trạng thái 'sending'.

    HAI câu, GIAO_DICH trước: một lượt "thông báo cả khối" (100 thư) xếp trước thư quên
    mật khẩu thì em ấy chờ tới nhịp sau (quyết định 4 của anh Sơn 26/09/2026). Chỗ còn
    lại mới tới thư hàng loạt, và chỉ tới phần trần ngày còn cho phép — vượt trần thì
    dòng NẰM LẠI 'queued' (không `dropped`): sang ngày sau trần mở lại, thư vẫn đi."""
    ds = _nhan_theo_uu_tien(GIAO_DICH, n, ids)
    con = n - len(ds)
    if con > 0:
        ds += _nhan_theo_uu_tien(HANG_LOAT, min(con, con_lai_hang_loat()), ids)
    for d in ds:
        d['params'] = _params(d)      # Django trả jsonb dạng chuỗi — đọc một lần ở đây
    return ds


def _params(d):
    p = d.get('params') or {}
    return json.loads(p) if isinstance(p, str) else p


def _qua_han(p):
    han = p.get('het_han')
    if not han:
        return False
    try:
        return datetime.fromisoformat(han) <= timezone.now()
    except (TypeError, ValueError):
        return False


def _dung(d, p):
    """(tiêu đề, chữ, html, đính kèm) của thư email."""
    loai = p.get('loai')
    if loai in LOAI:
        return importlib.import_module(LOAI[loai]).dung_thu_outbox(d)
    return d['subject'], d['body'], p.get('html'), ()


def _gui_email(d, p, san):
    den = (d['to_addr'] or '').strip()
    if not den or '@' not in den or any(c in den for c in mail._XUONG_DONG):
        return 'bo', None, 'Địa chỉ email không hợp lệ: %r' % den
    # HÀNG RÀO MÁY DEV — trước khi dựng thư và trước khi mở SMTP (§61, quyết định 3).
    chan = hang_rao_thu.ly_do_chan('email', den)
    if chan:
        return 'bo', None, chan
    tieu_de, chu, html, dinh_kem = san if san else _dung(d, p)
    # Chỉ truyền html/tệp khi có: giữ đúng lời gọi ba đối số của các nơi gửi chữ thuần.
    thua = (html, tuple(dinh_kem or ())) if (html or dinh_kem) else ()
    ok, dau_vet, loi = mail.gui(den, tieu_de, chu, *thua)
    if ok:
        return 'xong', dau_vet, None
    # Chưa cấu hình (và không ở chế độ thử) là lỗi VĨNH VIỄN cho lá thư này: thử lại sáu
    # lần trong tám tiếng cũng không gửi được, chỉ làm hộp thư đi đầy việc giả.
    if not (mail.da_cau_hinh() or mail.che_do_thu()):
        return 'bo', None, loi or 'Chưa cấu hình email (%s).' % ', '.join(mail.thieu_gi())
    return 'loi', dau_vet, loi


def _gui_zalo(d, p):
    if not (zalo.da_cau_hinh() or zalo.che_do_thu()):
        return 'bo', None, 'Kênh Zalo chưa sẵn sàng: chưa có Zalo OA (%s).' % ', '.join(zalo.thieu_gi())
    if not (d['to_addr'] or '').strip():
        return 'bo', None, 'Chưa có số điện thoại người nhận.'
    chan = hang_rao_thu.ly_do_chan('zalo', d['to_addr'])
    if chan:
        return 'bo', None, chan
    ok, dau_vet, loi = zalo.gui_zns(d['to_addr'], p.get('zns') or {})
    return ('xong' if ok else 'loi'), dau_vet, loi


def gui_mot(d, san=None):
    """Gửi một việc ĐÃ NHẬN (status 'sending'). Trả (trạng thái mới, dấu vết, lỗi)."""
    p = _params(d)
    try:
        if _qua_han(p):
            kq = ('bo', None, 'Quá hạn, không gửi nữa.')
        elif d['channel'] == 'email':
            kq = _gui_email(d, p, san)
        elif d['channel'] == 'zalo':
            kq = _gui_zalo(d, p)
        else:
            kq = ('bo', None, 'Kênh không biết: %s' % d['channel'])
    except Exception as e:           # noqa: BLE001 — dựng thư hỏng: thử lại như lỗi mạng
        log.exception('[hop_thu] lỗi khi gửi việc %s', d['id'])
        kq = ('loi', None, 'Lỗi khi dựng/gửi: %s' % e)

    ket, dau_vet, loi = kq
    if ket == 'loi' and d['attempts'] > len(BACKOFF_PHUT):
        ket = 'bo'
    trang_thai = {'xong': 'sent', 'loi': 'failed', 'bo': 'dropped'}[ket]
    lui = BACKOFF_PHUT[d['attempts'] - 1] if ket == 'loi' else 0
    # Thân có chìa (thư quên mật khẩu): xong việc là xoá — chìa thô không nằm lại CSDL.
    xoa = bool(p.get('xoa_than')) and trang_thai != 'failed'
    q1('''UPDATE outbox SET status = %s, provider_id = coalesce(%s, provider_id), error = %s,
                 sent_at = CASE WHEN %s = 'sent' THEN now() ELSE sent_at END,
                 next_try_at = CASE WHEN %s = 'failed' THEN now() + make_interval(mins => %s)
                                    ELSE next_try_at END,
                 body = CASE WHEN %s THEN '' ELSE body END,
                 params = CASE WHEN %s THEN params - 'html' ELSE params END
           WHERE id = %s AND status = 'sending' AND claimed_at = %s RETURNING id''',
       (trang_thai, dau_vet or None, None if trang_thai == 'sent' else (loi or '')[:1000],
        trang_thai, trang_thai, lui, xoa, xoa, d['id'], d['claimed_at']))

    loai = p.get('loai')
    if loai in LOAI:
        sau = getattr(importlib.import_module(LOAI[loai]), 'sau_gui_outbox', None)
        if sau:
            try:
                sau(d, trang_thai, dau_vet, loi)
            except Exception:        # noqa: BLE001 — sổ phụ hỏng không làm hỏng lượt gửi
                log.exception('[hop_thu] sau_gui_outbox lỗi ở việc %s', d['id'])
    return trang_thai, dau_vet, loi


def chay_luot(n=MOT_LUOT, ids=None, san=None):
    """Nhận rồi gửi một lượt. Trả {id: (trạng thái, dấu vết, lỗi)}."""
    san = san or {}
    return {d['id']: gui_mot(d, san.get(d['id'])) for d in nhan_viec(n, ids)}


def gui_ngay(ids, san=None):
    """Gửi NGAY các việc `ids` (nếu tới lượt). `san`: {id: thư đã dựng sẵn} để khỏi dựng lại."""
    ids = [i for i in ids or () if i]
    return chay_luot(len(ids), ids, san) if ids else {}


def gui_het(toi_da=500):
    """Gửi mọi việc tới lượt (tối đa `toi_da` việc). Trả số theo trạng thái."""
    dem = {'sent': 0, 'failed': 0, 'dropped': 0}
    while sum(dem.values()) < toi_da:
        kq = chay_luot()
        if not kq:
            break
        for trang_thai, _, _ in kq.values():
            dem[trang_thai] += 1
    return dem


def _gui_trong_luong(ids):
    try:
        gui_ngay(ids)
    except Exception:                # noqa: BLE001
        log.exception('[hop_thu] lượt gửi ngay lỗi — việc nằm lại chờ nhịp sau')
    finally:
        connection.close()


def danh_thuc(ids):
    """Gửi `ids` trên một luồng riêng (không bắt người bấm chờ SMTP)."""
    ids = [i for i in ids or () if i]
    if ids:
        threading.Thread(target=_gui_trong_luong, args=(ids,), daemon=True,
                         name='hop-thu-gui-ngay').start()


def day_di(ids, ngay=False):
    """Sau khi giao dịch bao quanh commit thì gửi `ids`. `ngay=True`: gửi đồng bộ, NGAY
    trong giao dịch hiện tại (phép kiểm cần đọc kết quả liền sau lời gọi)."""
    ids = [i for i in ids or () if i]
    if not ids:
        return
    if ngay:
        gui_ngay(ids)
    else:
        transaction.on_commit(lambda: danh_thuc(ids))


def nhip():
    """MỘT nhịp: quét nhắc hạn nộp rồi gửi hết việc tới lượt."""
    from notifications import nhac_han
    dem = {'nhacHan': 0}
    try:
        dem['nhacHan'] = nhac_han.quet()
    except Exception:                # noqa: BLE001 — nhắc hỏng không chặn gửi thư
        log.exception('[hop_thu] quét nhắc hạn lỗi')
    dem.update(gui_het())
    return dem


# ── Luồng nền trong tiến trình (mẫu `common/keepalive.py`) ──────────────────

_da_bat = False
_khoa = threading.Lock()


def _vong():
    while True:
        time.sleep(CHU_KY_GIAY)
        try:
            nhip()
        except Exception as e:       # noqa: BLE001 — lỗi một nhịp không giết luồng
            log.warning('[hop_thu] nhịp lỗi (thử lại nhịp sau): %s', e)
        finally:
            connection.close()


def _bat_luong():
    threading.Thread(target=_vong, name='hop-thu', daemon=True).start()
    log.info('[hop_thu] bật luồng gửi mỗi %ss', CHU_KY_GIAY)


def bat_luong_nen_neu_duoc():
    """Bật luồng nền (một lần mỗi tiến trình) khi `ENABLE_OUTBOX=1`."""
    global _da_bat
    if os.environ.get('ENABLE_OUTBOX') != '1':
        return
    with _khoa:
        if _da_bat:
            return
        _da_bat = True
    _bat_luong()
