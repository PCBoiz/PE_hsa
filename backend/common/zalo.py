"""Gửi tin ZNS qua Zalo Official Account.

── VÌ SAO TỆP NÀY TỒN TẠI DÙ CHƯA GỬI ĐƯỢC TIN NÀO (07/09/2026) ────────────

Trung tâm CHƯA có Zalo OA đã xác thực, và ZNS thì bắt buộc phải có. Nên hôm nay
`da_cau_hinh()` trả False ở mọi máy, và đường gửi hàng loạt tự chuyển sang chế
độ "cấp link, người tự gửi".

Viết sẵn phần này thay vì đợi, vì hai lý do:

  · Ranh giới ở đây quyết định hình dạng của mọi thứ phía trên nó — hàng chờ,
    màn hình gửi, cách báo lỗi. Dựng phần trên rồi mới nhét phần này vào là
    phải sửa lại cả ba.
  · Khi OA có, việc cần làm chỉ còn là điền bốn biến môi trường. Không ai phải
    đọc lại đặc tả ZNS lúc đang gấp.

── BỐN ĐIỀU VỀ ZNS ĐÃ TRA, GHI LẠI ĐỂ KHÔNG PHẢI TRA LẠI ──────────────────

1. **ZNS KHÔNG đính kèm được tệp.** Nó là tin theo MẪU đã được Zalo duyệt
   trước, chỉ điền được các tham số khai trong mẫu. Nên "gửi file PDF qua ZNS"
   là điều không tồn tại — phải gửi một đường dẫn.
2. **Mẫu phải được duyệt trước**, và nội dung phải thuộc loại CHĂM SÓC KHÁCH
   HÀNG (thông báo giao dịch, cập nhật dịch vụ). Báo cáo tiến độ học của con
   gửi cho phụ huynh đã đăng ký học nằm trong nhóm này.
3. **Mất phí theo tin** (~100–200đ tuỳ loại mẫu), bên GỬI trả. Đây là lý do
   `parent_send.py` bắt phải có một cái gật của con người trước mỗi lượt gửi
   hàng loạt: một vòng lặp sai là một hoá đơn thật.
4. **Chỉ gửi được tới số đã có quan hệ với OA** (đã giao dịch hoặc đồng ý nhận
   tin). Số phụ huynh của học viên đang học ở trung tâm thoả điều đó, nhưng
   Zalo mới là bên quyết — nên mã ở đây KHÔNG đoán trước, cứ gửi và đọc mã lỗi
   trả về.

── KHÔNG NÉM NGOẠI LỆ ─────────────────────────────────────────────────────

Mọi hàm ở đây trả `(ok, mã_nhà_cung_cấp, lỗi)`. Một lượt gửi hàng loạt 25 học
viên mà tin thứ ba ném ngoại lệ thì 22 em còn lại không được gửi, và người bấm
nút không biết đã gửi tới đâu. Lỗi phải là một GIÁ TRỊ để vòng lặp đi tiếp và
ghi vào sổ.
"""
import logging
import os

import requests

log = logging.getLogger(__name__)

#: Địa chỉ API gửi ZNS. Tách thành biến để bộ kiểm trỏ sang máy chủ giả được.
API = os.environ.get('ZALO_ZNS_API', 'https://business.openapi.zalo.me/message/template')

#: Chờ tối đa. Ngắn có chủ đích: đây là lời gọi nằm TRONG một vòng lặp gửi cả
#: lớp, nên một nhà cung cấp treo sẽ nhân lên theo số học viên. 10 giây × 25 em
#: là hơn bốn phút một request — quá lâu, người bấm sẽ tưởng hệ thống chết.
CHO_GIAY = 10


def _thong_so():
    """Đọc cấu hình từ môi trường. Đọc mỗi lần gọi chứ không cache ở module.

    Cache ở tầng module nghĩa là đổi biến môi trường trên Render phải khởi động
    lại tiến trình mới có tác dụng — và người đổi sẽ không biết điều đó, rồi
    kết luận là "điền rồi mà vẫn không gửi được".
    """
    return {
        'token': (os.environ.get('ZALO_OA_ACCESS_TOKEN') or '').strip(),
        'template': (os.environ.get('ZALO_ZNS_TEMPLATE_ID') or '').strip(),
    }


def da_cau_hinh() -> bool:
    """Đủ thông số để gửi chưa. Thiếu MỘT trong hai là chưa."""
    t = _thong_so()
    return bool(t['token'] and t['template'])


def thieu_gi() -> list[str]:
    """Tên các biến môi trường còn trống — để màn hình nói ĐÚNG thứ còn thiếu
    thay vì một câu chung chung mà người đọc không biết phải làm gì."""
    t = _thong_so()
    ra = []
    if not t['token']:
        ra.append('ZALO_OA_ACCESS_TOKEN')
    if not t['template']:
        ra.append('ZALO_ZNS_TEMPLATE_ID')
    return ra


def gui_zns(phone: str, tham_so: dict) -> tuple[bool, str | None, str | None]:
    """Gửi MỘT tin. Trả `(thành_công, mã_tin_của_Zalo, câu_lỗi)`.

    `tham_so` là các tham số của MẪU đã duyệt — tên khoá do mẫu quy định, mã ở
    đây không tự đặt. Nơi gọi biết mẫu của mình, chỗ này chỉ chuyển tiếp.
    """
    t = _thong_so()
    if not (t['token'] and t['template']):
        return False, None, 'Chưa cấu hình Zalo OA (%s).' % ', '.join(thieu_gi())
    if not phone:
        return False, None, 'Chưa có số điện thoại người nhận.'

    try:
        r = requests.post(
            API,
            headers={'access_token': t['token'], 'Content-Type': 'application/json'},
            json={'phone': phone, 'template_id': t['template'], 'template_data': tham_so},
            timeout=CHO_GIAY,
        )
    except requests.RequestException as e:
        # Không với tới được KHÁC HẲN bị từ chối: cái đầu đáng thử lại, cái sau
        # thì không. Câu lỗi phải nói rõ để người đọc sổ biết nên làm gì.
        return False, None, 'Không gọi được Zalo: %s' % e

    try:
        body = r.json()
    except ValueError:
        return False, None, 'Zalo trả về phản hồi không đọc được (HTTP %s).' % r.status_code

    # Zalo trả HTTP 200 kèm `error != 0` cho lỗi nghiệp vụ. Chỉ nhìn mã HTTP là
    # ghi "đã gửi" cho một tin chưa bao giờ tới nơi.
    ma = body.get('error')
    if ma == 0:
        d = body.get('data') or {}
        return True, str(d.get('msg_id') or ''), None

    loi = '%s (mã %s)' % (body.get('message') or 'Zalo từ chối gửi', ma)
    log.warning('ZNS lỗi: %s', loi)
    return False, None, loi
