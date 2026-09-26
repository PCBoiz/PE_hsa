"""Đột biến E2 (hộp thư đi §61, thông báo trung tâm, hàng rào thư) — 26/09/2026.

Mỗi mục: (tệp, chuỗi cũ, chuỗi mới, luật, bộ kiểm). Nền của từng bộ kiểm phải xanh; mỗi
đột biến phải làm bộ kiểm CỦA NÓ đỏ. Thoát 1 nếu còn đột biến SỐNG — một đột biến sống là
một luật không có ai canh, và luật ấy đúng vào lúc này chỉ vì chưa ai gõ sai chỗ đó.

Chạy (cần DATABASE_URL, SECRET_KEY): python scripts/dot_bien_e2.py

── VÌ SAO MỖI ĐỘT BIẾN MANG BỘ KIỂM RIÊNG (khác `dot_bien_e1.py`) ───────────

Bản đầu dùng MỘT lệnh pytest sáu mô-đun cho cả 16 đột biến: nền ~9 phút, và mỗi đột biến
sống phải trả đủ 9 phút ấy. Trên Neon dev DÙNG CHUNG với các agent khác, lượt đo đầu bò
tới hơn 20 phút rồi vẫn chưa qua nền.

Nay mỗi đột biến chỉ chạy mô-đun THẬT SỰ canh luật ấy (thường một mô-đun, ~40–110 giây), và
nền của mỗi bộ kiểm tính MỘT lần rồi nhớ lại. Đổi lại phải khai bộ kiểm cho từng mục —
đó là việc nên làm: nó ghi thẳng ra "luật này ai canh", và một mục không khai nổi bộ kiểm
là dấu hiệu luật ấy chưa có nhà.
"""
import os
import subprocess
import sys

GOC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend') + os.sep

HANG_RAO = ('notifications/tests_hang_rao_thu.py',)
HOP_THU = ('notifications/tests_hop_thu.py',)
THONG_BAO = ('notifications/tests_thong_bao.py',)
GUI = ('notifications/tests_gui.py',)
MAT_KHAU = ('accounts/tests_quen_mat_khau.py',)

M = [
 # ── Hàng rào thư ở máy dev: thứ ngăn một lá thư THẬT rời máy chủ ────────────
 ('notifications/hang_rao_thu.py',
  '    return not dang_tro_production()',
  '    return False',
  'hàng rào TẮT hẳn — thư đi tới mọi địa chỉ trên máy dev', HANG_RAO),
 ('notifications/hang_rao_thu.py',
  "    return any(d.endswith(m) if m.startswith('@') else d == m for m in cho_phep)",
  '    return True',
  'mọi địa chỉ đều coi là "được phép"', HANG_RAO),
 ('notifications/hang_rao_thu.py',
  "DUOI_VI_DU = ('@example.com', '@example.org', '@example.net')",
  "DUOI_VI_DU = ('@example.com', '@example.org', '@example.net', '@gmail.com')",
  'thêm một tên miền THẬT vào danh sách an toàn', HANG_RAO),
 ('notifications/hang_rao_thu.py',
  "    if channel == 'zalo':",
  '    if False:',
  'Zalo không qua hàng rào — tin đi tới số thật', HANG_RAO),

 # ── Ưu tiên giao dịch / hàng loạt + trần ngày ───────────────────────────────
 ('notifications/hop_thu.py',
  '    ds = _nhan_theo_uu_tien(GIAO_DICH, n, ids)',
  '    ds = _nhan_theo_uu_tien(HANG_LOAT, n, ids)',
  'đảo ưu tiên: thư cả khối đi trước thư quên mật khẩu', HOP_THU),
 ('notifications/hop_thu.py',
  '        ds += _nhan_theo_uu_tien(HANG_LOAT, min(con, con_lai_hang_loat()), ids)',
  '        ds += _nhan_theo_uu_tien(HANG_LOAT, con, ids)',
  'trần ngày không được áp vào lúc nhận việc', HOP_THU),
 ('notifications/hop_thu.py',
  '    return max(0, tran - da)',
  '    return tran',
  'trần ngày bỏ qua số thư đã gửi hôm nay', HOP_THU),
 ('notifications/hop_thu.py',
  '    return n if n >= 0 else TRAN_HANG_LOAT_MAC_DINH',
  '    return n if n >= 0 else 0',
  'biến trần âm → 0 thay vì mặc định (im lặng không gửi gì)', HOP_THU),
 ('notifications/gui.py',
  '        uu_tien = hop_thu.GIAO_DICH if len(ids) <= 1 else hop_thu.HANG_LOAT',
  '        uu_tien = hop_thu.GIAO_DICH',
  'thư cả lớp khai là GIAO DỊCH → lách trần ngày', GUI + HOP_THU),

 # ── Thân thư có chìa: xoá sau khi gửi; thư quá hạn thì bỏ ───────────────────
 ('notifications/hop_thu.py',
  "    xoa = bool(p.get('xoa_than')) and trang_thai != 'failed'",
  '    xoa = False',
  'chìa đặt lại mật khẩu NẰM LẠI trong CSDL sau khi gửi', HOP_THU + MAT_KHAU),
 ('notifications/hop_thu.py',
  '        if _qua_han(p):',
  '        if False:',
  'thư quá hạn vẫn gửi — đường dẫn trong đó đã chết', HOP_THU + MAT_KHAU),

 # ── Nhận việc: không hai máy cùng gửi một lá ────────────────────────────────
 ('notifications/hop_thu.py',
  "           WHERE id = %s AND status = 'sending' AND claimed_at = %s RETURNING id''',",
  "           WHERE id = %s RETURNING id''',",
  'ghi kết quả không kiểm mình còn giữ việc (hai máy đè nhau)', HOP_THU),
 ('notifications/hop_thu.py',
  "    if ket == 'loi' and d['attempts'] > len(BACKOFF_PHUT):",
  '    if False:',
  'hết dãy lùi vẫn không bỏ — thư thử lại vô hạn', HOP_THU),
 ('notifications/hop_thu.py',
  '              FOR UPDATE SKIP LOCKED)',
  '              )',
  'bỏ SKIP LOCKED — hai máy chờ nhau ở cùng một dòng', HOP_THU),

 # ── Thông báo trung tâm: xem trước phải đếm đúng thứ sắp xảy ra ─────────────
 ('notifications/thong_bao.py',
  'def xem_truoc(aud, gui_email=False):',
  'def xem_truoc(aud, gui_email=True):',
  'bản xem trước hứa nhiều hơn thứ nó làm', THONG_BAO),

 # ── Trợ giảng gửi được LỚP MÌNH, không phải lớp khác ────────────────────────
 ('notifications/views_thong_bao.py',
  """        if not can_see_class(request.user, class_id):
            return Response({'error': 'Không tìm thấy lớp này.'}, status=404)
        return _soan(request, {'classIds': [class_id]}, True)""",
  "        return _soan(request, {'classIds': [class_id]}, True)",
  'gửi được thông báo cho lớp KHÔNG phải của mình', THONG_BAO),
]


def _doc(t):
    with open(GOC + t, encoding='utf-8') as f:
        return f.read()


def _ghi(t, s):
    with open(GOC + t, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def _chay(bo_kiem):
    lenh = [sys.executable, '-m', 'pytest', '-x', '-q', '-p', 'no:cacheprovider', *bo_kiem]
    return subprocess.run(lenh, cwd=GOC, capture_output=True, text=True).returncode == 0


_nen = {}


def _nen_xanh(bo_kiem):
    """Nền của MỘT bộ kiểm, tính một lần rồi nhớ."""
    if bo_kiem not in _nen:
        print('   nền %s … ' % ' '.join(os.path.basename(b) for b in bo_kiem), end='', flush=True)
        _nen[bo_kiem] = _chay(bo_kiem)
        print('xanh' if _nen[bo_kiem] else 'ĐỎ', flush=True)
    return _nen[bo_kiem]


def main():
    song, giet = [], 0
    for i, (tep, cu, moi, luat, bo_kiem) in enumerate(M, 1):
        if not _nen_xanh(bo_kiem):
            print('%2d/%d  %-56s BỎ QUA (nền đỏ)' % (i, len(M), luat[:56]), flush=True)
            song.append((luat, 'nền đỏ — không kết luận được'))
            continue
        goc = _doc(tep)
        if goc.count(cu) != 1:
            print('%2d/%d  %-56s BỎ QUA (khớp %d chỗ, cần 1)'
                  % (i, len(M), luat[:56], goc.count(cu)), flush=True)
            song.append((luat, 'chuỗi không khớp'))
            continue
        try:
            _ghi(tep, goc.replace(cu, moi))
            do = not _chay(bo_kiem)
        finally:
            _ghi(tep, goc)          # PHỤC HỒI dù có chuyện gì
        print('%2d/%d  %-56s %s' % (i, len(M), luat[:56], 'bị giết' if do else 'CÒN SỐNG'),
              flush=True)
        if do:
            giet += 1
        else:
            song.append((luat, 'bộ kiểm vẫn xanh'))

    print('\n%d/%d đột biến bị giết.' % (giet, len(M)))
    if song:
        print('CÒN SỐNG:')
        for luat, vi in song:
            print('  · %s (%s)' % (luat, vi))
    return 1 if song else 0


if __name__ == '__main__':
    sys.exit(main())
