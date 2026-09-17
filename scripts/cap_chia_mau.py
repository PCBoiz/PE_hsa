"""Cấp MỘT chìa báo cáo phụ huynh cho một em của LỚP MẪU, để đo trang `/bc/<chìa>`.

── VÌ SAO CÓ TỆP NÀY (17/09/2026) ──────────────────────────────────────────

`/bc/<chìa>` là trang phụ huynh mở trên điện thoại từ tin nhắn — bề mặt DUY NHẤT
của sản phẩm mà người ngoài hệ thống nhìn thấy. Bộ đo hiệu năng
(`do_hieu_nang.mjs`) chưa từng đo nó, vì đo nó cần một chìa còn sống; chìa của
dữ liệu mẫu hết hạn hoặc bị thu hồi sau mỗi lần `du_lieu_mau --lam-moi`.

── ĐI ĐÚNG ĐƯỜNG THẬT, KHÔNG CHÈN DÒNG TAY ─────────────────────────────────

Chìa được cấp bằng CHÍNH `ParentReportLinkView`, dưới tên giảng viên phụ trách
lớp mẫu — nên nó mang đúng hạn dùng, đúng độ dài chìa và đúng dòng nhật ký như
khi giảng viên bấm nút. Chèn tay một dòng `parent_report_links` thì đo được một
trang, nhưng không chứng minh gì về trang mà người dùng thật nhận được.

── NÓ GHI GÌ — ĐÃ ĐẾM, KHÔNG SUY RA ────────────────────────────────────────

Đếm trước/sau ngày 17/09/2026 trên Neon:
    parent_report_links   +1   (lớp mẫu, is_demo)
    admin_audit           +1   (action = parent_link.create)
    parent_report_sends    0   (cấp chìa KHÔNG gửi gì cho ai)

VÀ MỖI LƯỢT MỞ TRANG ĐỀU TĂNG `opened_count`. Sau một buổi đo hôm ấy chìa ghi
"đã mở 23 lần" — đúng bằng 23 lượt tải của bộ đo, không một phụ huynh nào. Đó
là bằng chứng cụ thể cho câu hỏi C7 trong `docs/VIEC_CUA_ANH.md`: con số "đã mở"
hiện đếm lượt TẢI TRANG, không đếm NGƯỜI XEM.

Chỉ chạy trên lớp `is_demo` — tệp tự dừng nếu không có lớp mẫu, chứ không rơi
sang lớp thật. Chìa KHÔNG in ra màn hình (là quyền xem dữ liệu một đứa trẻ);
nó được cất vào `.the/chia_mau.json`, thư mục đã nằm trong `.gitignore`.

Chạy (ở máy có `backend/.env`):
    backend/.venv/Scripts/python.exe scripts/cap_chia_mau.py
"""
import json
import os
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(GOC, 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django  # noqa: E402

django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402

from accounts.models import User  # noqa: E402
from common.db import q1  # noqa: E402
from teaching.parent_link import ParentReportLinkView  # noqa: E402

lop = q1("""SELECT c.id, c.teacher_id FROM classes c
            WHERE c.is_demo AND c.teacher_id IS NOT NULL
            ORDER BY (SELECT count(*) FROM class_sessions s
                      WHERE s.class_id = c.id AND s.attendance_taken_at IS NOT NULL) DESC
            LIMIT 1""")
if not lop:
    sys.exit('Không có lớp mẫu nào có giảng viên — chạy `manage.py du_lieu_mau` trước. '
             'KHÔNG dùng lớp thật để đo.')

# Em có nhiều kỳ thi thử nhất → tờ báo cáo nhiều khối nhất → trang NẶNG nhất.
# Đo trang nặng nhất mới nói được trang của mọi em đều nhẹ hơn thế.
em = q1("""SELECT m.user_id,
                  (SELECT count(*) FROM ket_qua_thi_ngoai k WHERE k.user_id = m.user_id) AS ky
           FROM class_members m JOIN users u ON u.id = m.user_id
           WHERE m.class_id = %s AND m.left_at IS NULL
             AND u.role = 'Học viên' AND u.is_demo
           ORDER BY ky DESC, m.user_id LIMIT 1""", (lop['id'],))
if not em:
    sys.exit('Lớp mẫu không có học viên mẫu nào.')

req = APIRequestFactory().post('/x', {}, format='json')
force_authenticate(req, user=User.objects.get(id=lop['teacher_id']))
kq = ParentReportLinkView.as_view()(req, class_id=lop['id'], user_id=em['user_id'])
if kq.status_code != 201:
    sys.exit('View từ chối cấp chìa: %s %s' % (kq.status_code, kq.data))

token = kq.data['token']
link = q1('SELECT id, expires_at FROM parent_report_links WHERE token = %s', (token,))
os.makedirs(os.path.join(GOC, '.the'), exist_ok=True)
with open(os.path.join(GOC, '.the', 'chia_mau.json'), 'w', encoding='utf-8') as f:
    json.dump({'token': token, 'link_id': link['id']}, f)
print('Đã cấp chìa link id=%s (lớp mẫu %s, em %s, %s kỳ thi thử), hết hạn %s.'
      % (link['id'], lop['id'], em['user_id'], em['ky'], link['expires_at']))
print('Cất ở .the/chia_mau.json. Mỗi lượt đo sẽ tăng opened_count của chìa này.')
