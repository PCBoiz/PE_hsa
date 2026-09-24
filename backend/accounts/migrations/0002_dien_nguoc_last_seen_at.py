"""Điền ngược §56 `users.last_seen_at` từ lịch sử cấp phiên đăng nhập (25/09/2026).

Anh Sơn chốt 25/09: CÓ điền ngược. Không điền thì sau khi §56 lên, trang Tổng quan đếm
gần như mọi nhân sự là "chưa vào" cho tới lần đăng nhập kế tiếp của từng người (đo trên
bản sao dữ liệu 24/09: 69/75 tài khoản trống cột này).

Nguồn: `token_blacklist_outstandingtoken` — mỗi lượt đăng nhập / làm mới phiên để lại một
dòng (SimpleJWT). Lấy lượt MUỘN NHẤT của mỗi người.

VÌ SAO LÀ MIGRATION, KHÔNG PHẢI MỤC TRONG `legacy_schema.sql`: `bootstrap_schema` chạy
TRƯỚC `migrate` — trên CSDL mới toanh bảng token chưa có, câu UPDATE sẽ làm hỏng lượt dựng.
Migration chạy SAU migration tạo bảng token (phụ thuộc dưới), và chạy ĐÚNG MỘT LẦN (Django
ghi sổ `django_migrations`) — đúng thứ một lần điền ngược cần.

Hai bẫy đã xử lý:
- MÚI GIỜ: cột token là `timestamptz`, còn `last_seen_at` lưu giờ Việt Nam KHÔNG múi (quy
  ước `common/clock.py::local_now`) → đổi `AT TIME ZONE 'Asia/Ho_Chi_Minh'`.
- PHIÊN CẤP LÚC TẠO TÀI KHOẢN: lượt đăng ký (`RegisterView`) cấp token cho tài khoản VỪA tạo
  dù chủ tài khoản chưa vào → bỏ các dòng token trong 5 phút đầu kể từ lúc tạo tài khoản.
Chỉ điền ô CÒN TRỐNG — không bao giờ ghi đè dấu thật đã có.
"""
from django.db import migrations

SQL_DIEN_NGUOC = """
UPDATE users u
   SET last_seen_at = t.lan_cuoi
  FROM (SELECT o.user_id,
               MAX(o.created_at AT TIME ZONE 'Asia/Ho_Chi_Minh') AS lan_cuoi
          FROM token_blacklist_outstandingtoken o
          JOIN users uu ON uu.id = o.user_id
         WHERE o.user_id IS NOT NULL
           AND (uu.created_at IS NULL
                OR o.created_at AT TIME ZONE 'Asia/Ho_Chi_Minh' > uu.created_at + INTERVAL '5 minutes')
         GROUP BY o.user_id) t
 WHERE u.id = t.user_id
   AND u.last_seen_at IS NULL
"""


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('token_blacklist', '0013_alter_blacklistedtoken_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(SQL_DIEN_NGUOC, reverse_sql=migrations.RunSQL.noop),
    ]
