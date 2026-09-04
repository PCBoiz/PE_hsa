"""Tạo (hoặc xoá) tài khoản HỌC VIÊN dành riêng cho bộ kiểm tự động.

── VÌ SAO (T58, 05/09/2026) ────────────────────────────────────────────────

`frontend/e2e/helpers.ts` mặc định đăng nhập bằng `audit@example.com` — một tài
khoản KHÔNG tồn tại trong CSDL này. Ba phép kiểm Playwright vì thế luôn bỏ qua,
và nó chặn luôn mọi việc phải xem `/dashboard` thật.

Đường vòng bằng thẻ JWT (`cap_the.py`) chạy được, nhưng thẻ access sống 30 PHÚT:
một lượt chạy dài hơn thế là hai phép kiểm cuối lại bỏ qua. Tài khoản thật thì
không có hạn ấy.

── TỆP NÀY GHI VÀO CSDL, VÀ NÓI RÕ GHI GÌ ──────────────────────────────────

Đây là Neon **production**. Nên:

  · Xem trước mặc định; `--that` mới ghi.
  · Đếm `users` và `enrollments` trước/sau, in ra cả hai.
  · Ghi trong MỘT giao dịch, và nếu số dòng đổi khác dự kiến thì cuộn lại.
  · `--xoa` gỡ sạch (tài khoản + ghi danh), cũng đếm trước/sau.

Bài học vừa trả giá hôm nay: tôi từng viết "cấp thẻ không ghi CSDL" dựa trên suy
luận, rồi chèn 6 dòng vào production. Mọi câu về tác dụng phụ ở đây đều kèm số đo.

── TÀI KHOẢN NÀY CỐ TÌNH DỄ NHẬN RA ────────────────────────────────────────

Tên hiện ra là "KIỂM THỬ TỰ ĐỘNG" chứ không phải một cái tên người: nó SẼ xuất
hiện trong danh sách tài khoản của khu quản trị, và người nhìn phải biết ngay đó
không phải học viên thật.

Email dùng `example.com` — RFC 2606 dành riêng, không bao giờ gửi tới đâu được.
KHÔNG dùng `.invalid`/`.test`/`.local` dù chúng cũng là tên miền dành riêng: thư
viện `email_validator` mà `accounts/validators.py` gọi TỪ CHỐI chúng ("special-use
or reserved name"), nên tài khoản tạo ra sẽ không đăng nhập nổi. Tôi đã tạo nhầm
một tài khoản `.invalid` rồi mới phát hiện lúc thử đăng nhập thật — bài học: tạo
xong chưa phải xong, phải đi trọn đường đăng nhập.

XP để 0, nên nó không lọt bảng xếp hạng (bảng ấy `ORDER BY xp DESC`, đã đọc
`leaderboard/views.py:164`).

── MẬT KHẨU KHÔNG NẰM TRONG REPO ───────────────────────────────────────────

Sinh ngẫu nhiên, ghi vào `.the/e2e.json` (thư mục đã trong `.gitignore`).
`frontend/e2e/helpers.ts` đọc tệp ấy. Một tài khoản production với mật khẩu
commit sẵn trong mã nguồn là một cánh cửa, dù nó chỉ là học viên.

    python scripts/tai_khoan_e2e.py            # xem trước
    python scripts/tai_khoan_e2e.py --that     # tạo / đặt lại mật khẩu
    python scripts/tai_khoan_e2e.py --xoa --that
"""
import argparse
import json
import os
import secrets
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.chdir(GOC / 'backend')

import django  # noqa: E402

django.setup()

from django.db import connection, transaction  # noqa: E402

from accounts.hashers import make_werkzeug_password  # noqa: E402
from common.db import q1  # noqa: E402

EMAIL = 'e2e-kiem-thu@example.com'
TEN = 'KIỂM THỬ TỰ ĐỘNG (không phải học viên)'
KHOA = 'hsa_quantitative'
RA = GOC / '.the' / 'e2e.json'


def dem():
    return (q1('SELECT COUNT(*) AS n FROM users')['n'],
            q1('SELECT COUNT(*) AS n FROM enrollments')['n'])


def hien_co():
    return q1('SELECT id, name, role, status, xp FROM users WHERE email = %s', (EMAIL,))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--that', action='store_true', help='ghi thật (mặc định chỉ xem)')
    ap.add_argument('--xoa', action='store_true', help='xoá tài khoản và ghi danh của nó')
    a = ap.parse_args()

    cu = hien_co()
    u0, e0 = dem()
    print('users=%d  enrollments=%d' % (u0, e0))
    print('tài khoản %s: %s' % (EMAIL, ('id=%s, xp=%s' % (cu['id'], cu['xp'])) if cu else 'CHƯA CÓ'))

    if a.xoa:
        if not cu:
            print('\nKhông có gì để xoá.')
            return
        print('\nSẼ XOÁ: users id=%s và mọi dòng enrollments của nó.' % cu['id'])
    else:
        print('\nSẼ %s tài khoản học viên, ghi danh khoá %s, đặt lại mật khẩu ngẫu nhiên.'
              % ('CẬP NHẬT' if cu else 'TẠO', KHOA))

    if not a.that:
        print('\n(XEM TRƯỚC — thêm --that để ghi thật)')
        return

    if a.xoa:
        with transaction.atomic():
            with connection.cursor() as c:
                c.execute('DELETE FROM enrollments WHERE user_id = %s', (cu['id'],))
                n_e = c.rowcount
                c.execute('DELETE FROM users WHERE id = %s AND email = %s', (cu['id'], EMAIL))
                n_u = c.rowcount
            # Bảo hiểm: đúng MỘT tài khoản, không hơn.
            if n_u != 1:
                raise RuntimeError('xoá %d dòng users — cuộn lại' % n_u)
            print('đã xoá %d users + %d enrollments' % (n_u, n_e))
        if RA.exists():
            RA.unlink()
            print('đã xoá %s' % RA)
    else:
        mk = secrets.token_urlsafe(18)
        with transaction.atomic():
            with connection.cursor() as c:
                if cu:
                    c.execute('UPDATE users SET password=%s, name=%s, role=%s, status=%s, '
                              'must_change_password=false WHERE email=%s',
                              (make_werkzeug_password(mk), TEN, 'Học viên', 'active', EMAIL))
                else:
                    c.execute('INSERT INTO users (name, email, password, role, xp, streak, '
                              'questionnaire_completed, is_verified, status) '
                              'VALUES (%s,%s,%s,%s,0,0,1,true,%s)',
                              (TEN, EMAIL, make_werkzeug_password(mk), 'Học viên', 'active'))
                if c.rowcount != 1:
                    raise RuntimeError('ghi %d dòng users — cuộn lại' % c.rowcount)
                uid = q1('SELECT id FROM users WHERE email = %s', (EMAIL,))['id']
                # Ghi danh: `ON CONFLICT DO NOTHING` để chạy lại không nhân đôi.
                c.execute('INSERT INTO enrollments (user_id, course_id) VALUES (%s,%s) '
                          'ON CONFLICT DO NOTHING', (uid, KHOA))
        RA.parent.mkdir(parents=True, exist_ok=True)
        RA.write_text(json.dumps({'email': EMAIL, 'password': mk}), encoding='utf-8')
        # KHÔNG in mật khẩu: nó vào bản ghi phiên và lịch sử shell.
        print('xong. Thông tin đăng nhập ghi vào %s (đã trong .gitignore)' % RA)

    u1, e1 = dem()
    print('users=%d (%+d)  enrollments=%d (%+d)' % (u1, u1 - u0, e1, e1 - e0))


if __name__ == '__main__':
    main()
