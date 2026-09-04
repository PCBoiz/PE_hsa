"""Cấp thẻ JWT cho một tài khoản ĐÃ CÓ, để bộ đo giao diện mở được trang thật.

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

── MẶC ĐỊNH KHÔNG GHI CSDL, VÀ ĐÂY LÀ CHỖ TÔI ĐÃ NÓI SAI ───────────────────

Bản đầu của tệp này cấp CẢ CẶP access + refresh và tuyên bố "không INSERT, không
UPDATE". **Sai.** `RefreshToken` của SimpleJWT mang `BlacklistMixin`, và
`for_user()` của mixin ấy tạo một dòng `token_blacklist_outstandingtoken`.

Đo trực tiếp (đếm trước/sau một lượt chạy): 490 → 491. Bốn lượt chạy ngày
05/09/2026 đã chèn bốn dòng id 821–824, đều `user_id=7`.

`AccessToken` KHÔNG mang mixin ấy (`AccessToken.__mro__` chỉ có `Token`), nên
cấp riêng access là thật sự chỉ ký một chuỗi. Đã đo: 491 → 491.

Nên MẶC ĐỊNH nay là access-only. Muốn có refresh thì phải nói ra bằng
`--co-refresh`, và cờ ấy in rõ rằng nó GHI một dòng.

Bài học ghi lại ở đây vì nó đắt: tôi viết "không ghi gì vào CSDL" dựa trên suy
luận "ký JWT thì cần gì CSDL", rồi chép câu ấy vào commit, vào PROGRESS, vào
`e2e/helpers.ts`. Một dòng chú thích khẳng định về AN TOÀN mà không đo thì đúng
bằng một dòng mã sai — nó tắt phản xạ kiểm tra của mọi người đọc sau.

Bộ đo cũng tự chặn mọi lời gọi không phải GET (`do_giao_dien.mjs`, khối
`p.route`), nên một lượt ĐO không đổi được gì dù thẻ có quyền quản trị.

    python scripts/cap_the.py                 # access-only, KHÔNG ghi CSDL
    python scripts/cap_the.py --co-refresh    # + refresh (GHI 1 dòng)
    python scripts/cap_the.py --vai "Giảng viên"
    python scripts/cap_the.py --id 7 --ra duong/dan.json

Thẻ access sống 30 phút. Hết hạn thì chạy lại lệnh trên — rẻ hơn nhiều so với
việc giữ một refresh token và phải ghi vào CSDL production.

Tệp thẻ nằm trong `.the/`, thư mục ấy ĐÃ vào `.gitignore` — thẻ là bí mật.
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

from rest_framework_simplejwt.tokens import AccessToken, RefreshToken  # noqa: E402

from accounts.models import User  # noqa: E402
from common.db import q1  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--vai', default='admin', help='vai cần cấp thẻ (mặc định admin)')
    ap.add_argument('--id', type=int, help='chỉ định thẳng user_id, bỏ qua --vai')
    ap.add_argument('--ra', default=str(GOC / '.the' / 'tokens_ad.json'),
                    help='tệp JSON để ghi thẻ')
    ap.add_argument('--co-refresh', action='store_true',
                    help='cấp kèm refresh token — GHI một dòng vào '
                         'token_blacklist_outstandingtoken của CSDL đang nối')
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

    nguoi = User.objects.get(id=row['id'])
    if a.co_refresh:
        # `RefreshToken.for_user` GHI một dòng `token_blacklist_outstandingtoken`
        # (BlacklistMixin). Nói ra trước khi làm, chứ không để người dùng phát
        # hiện sau — đây là CSDL production.
        print('CẢNH BÁO: --co-refresh sẽ GHI một dòng vào '
              'token_blacklist_outstandingtoken.')
        ref = RefreshToken.for_user(nguoi)
        the = {'access': str(ref.access_token), 'refresh': str(ref)}
    else:
        # `AccessToken` không mang BlacklistMixin → chỉ ký, không chạm CSDL.
        the = {'access': str(AccessToken.for_user(nguoi))}

    ra = Path(a.ra)
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(json.dumps(the), encoding='utf-8')

    # KHÔNG in thẻ ra màn hình: nó vào bản ghi phiên làm việc, vào lịch sử shell.
    print('Đã cấp thẻ cho id=%s (%s, vai %s)%s'
          % (row['id'], row['name'], row['role'],
             ' — kèm refresh' if a.co_refresh else ' — access-only, không ghi CSDL'))
    print('Thẻ access sống 30 phút; hết hạn thì chạy lại lệnh này.')
    print('Ghi vào: %s' % ra)
    print('Đo:  cd scripts && PE_TOKENS="%s" node do_giao_dien.mjs' % ra)


if __name__ == '__main__':
    main()
