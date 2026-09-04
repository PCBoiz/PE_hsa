"""Cấp cặp thẻ JWT cho một tài khoản ĐÃ CÓ, để bộ đo giao diện mở được trang thật.

── VÌ SAO CÓ TỆP NÀY (05/09/2026) ──────────────────────────────────────────

`scripts/do_giao_dien.mjs` đọc thẻ từ một tệp JSON, và đường dẫn mặc định của nó
là **thư mục tạm của một phiên Claude đã kết thúc**:

    C:/Users/.../Temp/claude/d--PE-test/<id-phiên-cũ>/scratchpad/tokens_ad.json

Thư mục ấy bị dọn, nên bộ đo bị đẩy về màn đăng nhập và **không đo được 15 trong
16 trang**. Nó in ra hướng dẫn "cấp thẻ mới (mint_ad.py) rồi đo lại" — nhưng
`mint_ad.py` cũng là một script nháp, chưa bao giờ được commit. Tức công cụ chỉ
người đọc tới một tệp không tồn tại, để sửa một đường dẫn không tồn tại.

Một công cụ đo mà không chạy được thì tệ hơn không có: người ta vẫn nhắc tới nó
trong ghi chú, vẫn tưởng có ai đó đang đo.

── KHÔNG GHI GÌ VÀO CSDL ───────────────────────────────────────────────────

Cấp thẻ chỉ là KÝ một chuỗi bằng `SECRET_KEY` cho một `user_id` đã tồn tại —
không `INSERT`, không `UPDATE`. Tệp này chỉ `SELECT` một lần để xác nhận tài
khoản có thật và đúng vai, rồi ký.

Bộ đo cũng đã tự chặn mọi lời gọi không phải GET (`do_giao_dien.mjs`, khối
`p.route`), nên một lượt đo không đổi được gì dù thẻ có quyền quản trị.

    python scripts/cap_the.py                 # vai admin, ghi ra .the/tokens_ad.json
    python scripts/cap_the.py --vai "Giảng viên"
    python scripts/cap_the.py --id 7 --ra duong/dan.json

Tệp thẻ nằm trong `.the/` và thư mục ấy ĐÃ vào `.gitignore` — thẻ là bí mật.
"""
import argparse
import json
import os
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.chdir(GOC / 'backend')

import django  # noqa: E402

django.setup()

from rest_framework_simplejwt.tokens import RefreshToken  # noqa: E402

from accounts.models import User  # noqa: E402
from common.db import q1  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--vai', default='admin', help='vai cần cấp thẻ (mặc định admin)')
    ap.add_argument('--id', type=int, help='chỉ định thẳng user_id, bỏ qua --vai')
    ap.add_argument('--ra', default=str(GOC / '.the' / 'tokens_ad.json'),
                    help='tệp JSON để ghi thẻ')
    a = ap.parse_args()

    if a.id:
        row = q1('SELECT id, name, role FROM users WHERE id = %s', (a.id,))
    else:
        row = q1('SELECT id, name, role FROM users WHERE role = %s ORDER BY id LIMIT 1',
                 (a.vai,))
    if not row:
        # Nói rõ CÁI GÌ không có, chứ không "không tìm thấy tài khoản": người đọc
        # cần biết là nên đổi `--vai` hay là CSDL này thật sự chưa có ai vai ấy.
        print('Không có tài khoản nào %s trong CSDL đang nối.'
              % (f'với id={a.id}' if a.id else f'vai {a.vai!r}'))
        print('Các vai đang có:')
        from common.db import q
        for r in q('SELECT role, COUNT(*) AS n FROM users GROUP BY role ORDER BY n DESC'):
            print('   %-22s %d' % (r['role'], r['n']))
        raise SystemExit(1)

    ref = RefreshToken.for_user(User.objects.get(id=row['id']))
    ra = Path(a.ra)
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(json.dumps({'access': str(ref.access_token), 'refresh': str(ref)}),
                  encoding='utf-8')

    # KHÔNG in thẻ ra màn hình: nó vào bản ghi phiên làm việc, vào lịch sử shell.
    print('Đã cấp thẻ cho id=%s (%s, vai %s)' % (row['id'], row['name'], row['role']))
    print('Ghi vào: %s' % ra)
    print('Đo:  cd scripts && PE_TOKENS="%s" node do_giao_dien.mjs' % ra)


if __name__ == '__main__':
    main()
