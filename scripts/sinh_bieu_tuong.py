"""Sinh `frontend/src/components/bieuTuong.tsx` từ `public/static/js/icons.js`.

── VÌ SAO CẦN SINH, THAY VÌ CHÉP TAY (06/09/2026) ──────────────────────────

`icons.js` là script THUẦN: nó quét `[data-icon]` đúng MỘT LẦN lúc
`DOMContentLoaded` rồi thôi. React dựng sau mốc ấy, và dựng lại mỗi lần điều
hướng trong ứng dụng — nên ô biểu tượng do React tạo ra sẽ rỗng.

Hệ quả nhìn thấy được trước khi vá: `Topbar.tsx` để ô trống chờ script điền,
còn `courses/[courseId]` bỏ cuộc và dùng emoji 🔍🌙🔔▾. Hai thanh điều hướng
của cùng một sản phẩm không thể trông giống nhau.

Bản TSX là bản sao, nhưng là bản sao ĐƯỢC ĐO: `e2e/unit/bieu-tuong-khop.test.mjs`
đọc cả hai tệp và so từng đường path, lệch một ký tự là đỏ. Chép tay thì không
có ai canh; sinh ra rồi khoá bằng phép kiểm thì có.

    python scripts/sinh_bieu_tuong.py          # sinh lại
    python scripts/sinh_bieu_tuong.py --xem    # chỉ in ra, không ghi
"""
import argparse
import json
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
NGUON = GOC / 'frontend' / 'public' / 'static' / 'js' / 'icons.js'
RA = GOC / 'frontend' / 'src' / 'components' / 'bieuTuong.tsx'

# Chỉ những biểu tượng KHUNG CHUNG dùng tới. Không sinh cả bộ: mỗi tên thừa là
# một đường path nằm trong gói gửi cho trình duyệt mà không ai vẽ.
CAN = [
    'home', 'library', 'calendar', 'map', 'medal', 'chat', 'target', 'pencil',
    'users', 'shield', 'wrench', 'search', 'sun', 'moon', 'bell',
    'chevron-down', 'user', 'settings', 'log-out',
    # Khu VẬN HÀNH (07/09/2026): khu ấy nay dùng chung `AppShell` thay vì tự
    # dựng một thanh Tailwind riêng, nên các tab của nó cần biểu tượng cùng bộ.
    'bar-chart', 'graduation-cap', 'file-text',
    # Trang "Hôm nay cần làm gì" — việc còn tồn, việc đã xong, chỗ trống.
    'clock', 'check-circle-2', 'inbox', 'arrow-right',
]

DAU = '''/* ══════════════════════════════════════════════════════════════════════════
 * SINH TỰ ĐỘNG TỪ `public/static/js/icons.js` — ĐỪNG SỬA TAY.
 *
 * Vì sao có bản sao này. `icons.js` là một script THUẦN: nó quét `[data-icon]`
 * MỘT LẦN lúc `DOMContentLoaded` rồi thôi. React dựng sau mốc ấy (và dựng lại
 * mỗi lần điều hướng trong ứng dụng), nên ô biểu tượng do React tạo ra sẽ rỗng.
 * Đó là lý do `Topbar.tsx` từng để ô trống chờ script điền, còn màn chi tiết
 * khoá học thì bỏ cuộc và dùng emoji — hai màn không thể giống nhau được.
 *
 * Vì sao không sợ trôi. `e2e/unit/bieu-tuong-khop.test.mjs` đọc CẢ HAI tệp và
 * so từng đường path; lệch một ký tự là đỏ. Nên đây là bản sao ĐƯỢC ĐO, không
 * phải bản sao chép tay.
 *
 * Muốn đổi một biểu tượng: sửa `icons.js`, rồi chạy lại
 *     python scripts/sinh_bieu_tuong.py
 * ══════════════════════════════════════════════════════════════════════════ */

/** Đường vẽ SVG, khớp từng ký tự với `icons.js`. */
export const DUONG_VE: Record<string, string> = {
'''

CUOI = '''
};

/**
 * Một biểu tượng SVG. `currentColor` chứ không màu cứng: nút đổi màu chữ khi rê
 * chuột thì biểu tượng phải đổi theo — đó là điều emoji không bao giờ làm được.
 */
export function BieuTuong({ ten, co = 17 }: { ten: string; co?: number }) {
  const d = DUONG_VE[ten];
  // Tên sai thì KHÔNG vẽ ô trống im lặng — ô trống trông y như "đang tải".
  if (!d) return null;
  return (
    <svg
      width={co}
      height={co}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: d }}
    />
  );
}
'''


def doc_nguon() -> dict:
    s = NGUON.read_text(encoding='utf-8')
    # `[a-z0-9-]` chứ KHÔNG phải `[a-z-]`. Bản cũ không nhận chữ số, nên
    # `check-circle-2` trong icons.js là VÔ HÌNH với cả bộ sinh lẫn phép kiểm
    # trôi — tên nào có số thì cả hai công cụ lặng lẽ bỏ qua (phát hiện
    # 07/09/2026 khi thêm biểu tượng cho khu Vận hành). Một thước bỏ sót một
    # phần vật cần đo thì tệ hơn không có thước: nó vẫn báo "khớp".
    return dict(re.findall(r"^\s*'?([a-z0-9-]+)'?:\s*'(.*?)',?\s*$", s, re.M))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--xem', action='store_true', help='in ra, không ghi tệp')
    a = ap.parse_args()

    duong = doc_nguon()
    thieu = [c for c in CAN if c not in duong]
    if thieu:
        # Nói rõ phải sửa Ở ĐÂU: nguồn là icons.js, không phải tệp sinh ra.
        print('Thiếu trong %s: %s' % (NGUON.name, ', '.join(thieu)), file=sys.stderr)
        print('Thêm vào icons.js trước, rồi chạy lại lệnh này.', file=sys.stderr)
        raise SystemExit(1)

    than = '\n'.join(
        "  %s: '%s'," % (json.dumps(c) if '-' in c else c, duong[c]) for c in CAN
    )
    noi_dung = DAU + than + CUOI

    if a.xem:
        print(noi_dung)
        return
    RA.write_text(noi_dung, encoding='utf-8')
    print('đã sinh %s (%d biểu tượng)' % (RA.relative_to(GOC), len(CAN)))


if __name__ == '__main__':
    main()
