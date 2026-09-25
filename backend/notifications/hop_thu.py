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
lượt lùi → 'dropped'. Lỗi VĨNH VIỄN (địa chỉ hỏng, kênh chưa cấu hình, thư quá hạn) →
'dropped' ngay, lý do ở `error`. Zalo ZNS chỉ đi khi đã có OA (`zalo.da_cau_hinh`).

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

log = logging.getLogger(__name__)

#: Khoảng lùi (phút) sau lần lỗi thứ 1, 2, … Hết dãy → bỏ.
BACKOFF_PHUT = (1, 5, 30, 120, 360)
#: Dòng 'sending' lâu hơn chừng này phút = máy gửi đã chết → nhận lại.
TREO_PHUT = 10
#: Số việc một lần nhận.
MOT_LUOT = 20
#: Chu kỳ luồng nền (giây).
CHU_KY_GIAY = 60

#: Loại thư dựng lại lúc gửi → mô-đun có `dung_thu_outbox` (xem chú thích đầu tệp).
LOAI = {
    'bao_cao_phu_huynh': 'teaching.thu_bao_cao',
}

CAU_NHAN = '''
    UPDATE outbox SET status = 'sending', claimed_at = now(), attempts = attempts + 1
     WHERE id IN (
           SELECT id FROM outbox
            WHERE ((status IN ('queued', 'failed') AND next_try_at <= now())
                   OR (status = 'sending' AND claimed_at < now() - make_interval(mins => %(treo)s)))
              AND (%(ids)s::bigint[] IS NULL OR id = ANY(%(ids)s::bigint[]))
            ORDER BY next_try_at, id
            LIMIT %(n)s
              FOR UPDATE SKIP LOCKED)
    RETURNING *'''


def xep(channel, to_addr, subject='', body='', *, user_id=None, params=None,
        source=(None, None), dedup=None):
    """Ghi MỘT việc gửi. Trả id, hoặc None khi `dedup` đã có (việc ấy đã xếp rồi).

    Gọi TRONG giao dịch của việc chính; sau commit gọi `day_di([id])` để gửi sớm."""
    r = q1('''INSERT INTO outbox (channel, user_id, to_addr, subject, body, params,
                                  source_type, source_id, dedup_key)
              VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
              ON CONFLICT (dedup_key) DO NOTHING RETURNING id''',
           (channel, user_id, to_addr or '', subject or '', body or '',
            json.dumps(params or {}, ensure_ascii=False), source[0], source[1], dedup))
    return r['id'] if r else None


def nhan_viec(n=MOT_LUOT, ids=None):
    """Nhận tối đa `n` việc tới lượt (chỉ trong `ids` nếu truyền). Câu tự commit khi
    đứng ngoài giao dịch — máy khác thấy ngay trạng thái 'sending'."""
    return q(CAU_NHAN, {'n': n, 'ids': list(ids) if ids is not None else None, 'treo': TREO_PHUT})


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
