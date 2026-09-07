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
import json
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


def che_do_thu() -> bool:
    """`ZALO_CHE_DO_THU` — đi trọn luồng nhưng KHÔNG gọi Zalo.

    ── VÌ SAO CÓ (07/09/2026, anh Sơn chốt) ─────────────────────────────────

    Mỗi tin ZNS mất phí và không thu về được, còn người nhận là phụ huynh học
    viên — gửi nhầm một lượt là gửi nhầm cho hàng chục gia đình. Nên phải xem
    được ĐÚNG nội dung sẽ đi trước khi bật gửi thật.

    Chế độ này KHÔNG giả vờ đã gửi: `gui_zns` trả về mã bắt đầu bằng `THU:`,
    và `parent_send` không ghi dòng nào vào `parent_report_sends`. Sổ gửi là sổ
    của những tin ĐÃ ĐI; một dòng "đã gửi" cho tin chưa từng rời máy là loại
    nói dối khó phát hiện nhất — lần sau đọc sổ sẽ tưởng phụ huynh đã nhận.
    """
    v = (os.environ.get('ZALO_CHE_DO_THU') or '').strip().lower()
    return v in ('1', 'true', 'yes', 'on', 'co', 'có')


def soan_zns(phone: str, tham_so: dict) -> dict:
    """Thân request ĐÚNG như sẽ gửi đi. Dùng chung cho cả gửi thật lẫn chế độ thử.

    Tách ra là có chủ ý: nếu chế độ thử tự dựng lấy một bản xem trước riêng thì
    nó sẽ trôi khỏi bản gửi thật, và người dùng duyệt một nội dung KHÁC với nội
    dung sẽ đi — tức chế độ thử biến thành thứ nguy hiểm hơn là không có nó.
    """
    return {
        'phone': phone,
        'template_id': _thong_so()['template'],
        'template_data': tham_so,
    }


def da_cau_hinh() -> bool:
    """Đủ thông số để gửi THẬT chưa. Thiếu MỘT trong hai là chưa.

    KHÔNG tính chế độ thử vào đây: màn hình dùng hàm này để nói "ZNS sẵn sàng",
    và nói sẵn sàng trong khi chưa có OA là đẩy người dùng đi bấm một nút không
    gửi được gì.
    """
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
    if not phone:
        return False, None, 'Chưa có số điện thoại người nhận.'

    if che_do_thu():
        # Đi tới đây là ĐÃ dựng xong đúng thân request. Ghi nó vào log rồi
        # dừng — không một byte nào rời khỏi máy chủ.
        log.info('ZNS [CHẾ ĐỘ THỬ] không gửi thật: %s', soan_zns(phone, tham_so))
        return True, 'THU:%s' % phone[-4:], None

    if not (t['token'] and t['template']):
        return False, None, 'Chưa cấu hình Zalo OA (%s).' % ', '.join(thieu_gi())

    try:
        r = requests.post(
            API,
            headers={'access_token': t['token'], 'Content-Type': 'application/json'},
            json=soan_zns(phone, tham_so),
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


# ─────────────────────────────────────────────────────────────────────────────
# OA Open API — khác hẳn ZNS, và đây là lý do phần này tồn tại (07/09/2026)
# ─────────────────────────────────────────────────────────────────────────────
#
# ZNS đi qua `business.openapi.zalo.me` và BẮT BUỘC OA đã xác thực. Anh Sơn
# không xác thực được vì Zalo đòi giấy phép kinh doanh, còn đây mới là thử
# nghiệm — nên câu hỏi thành: OA CHƯA xác thực thì làm được gì?
#
# Tra tài liệu công khai thì các nguồn ĐÁ NHAU:
#   · trang chính sách gửi tin của Zalo liệt kê tin Tư vấn/Giao dịch kèm điều
#     kiện "người dùng có phát sinh tương tác", không nói phải xác thực;
#   · trang khởi tạo OA lại nói người chưa có GPKD chỉ lập được "Hồ sơ quảng
#     cáo", và hồ sơ ấy KHÔNG dùng được Nhắn tin/Broadcast/Chatbot;
#   · nhiều nguồn khác nói từ 01/12/2020 muốn gửi tin chủ động thì phải xác thực.
#
# Ba câu đó không thể cùng đúng, và không tài liệu nào phân xử được. Thứ phân
# xử được là MỘT LỜI GỌI THẬT với token thật. Nên phần này không đoán: nó chỉ
# mở đúng ba cửa cần thiết để `manage.py chan_doan_oa` hỏi thẳng Zalo.
#
# Vì sao KHÔNG dùng lại `gui_zns`: khác tên miền, khác phiên bản API, khác thân
# request, và khác cả điều kiện người nhận (ZNS đi theo SỐ ĐIỆN THOẠI; tin tư
# vấn đi theo `user_id` mà chỉ có được sau khi người ta nhắn cho OA). Nhét hai
# thứ ấy vào một hàm là dựng một hàm nói dối về chính nó.

#: Gốc Open API của OA. Tách biến để bộ kiểm trỏ sang máy chủ giả được.
API_OA = os.environ.get('ZALO_OA_API', 'https://openapi.zalo.me')


def _goi_oa(duong, token, *, params=None, body=None):
    """Gọi một API của OA. Trả `(ok, dữ_liệu, lỗi)` — KHÔNG ném ngoại lệ.

    Cùng giao ước với `gui_zns`, và vì cùng một lý do: nơi gọi là một vòng lặp
    hoặc một màn chẩn đoán muốn ĐI TIẾP rồi in ra tất cả, chứ không muốn dừng
    ở lỗi đầu tiên.

    Zalo trả HTTP 200 kèm `error != 0` cho lỗi nghiệp vụ, nên chỉ nhìn mã HTTP
    là kết luận sai. Khi lỗi, `dữ_liệu` trả về NGUYÊN thân phản hồi — màn chẩn
    đoán cần in đúng chữ Zalo nói, không phải bản diễn giải của tôi.
    """
    if not token:
        return False, None, 'Chưa có access token của OA.'
    url = '%s/%s' % (API_OA.rstrip('/'), duong.lstrip('/'))
    try:
        if body is None:
            r = requests.get(url, headers={'access_token': token},
                             params=params, timeout=CHO_GIAY)
        else:
            r = requests.post(url, headers={'access_token': token,
                                            'Content-Type': 'application/json'},
                              json=body, timeout=CHO_GIAY)
    except requests.RequestException as e:
        return False, None, 'Không gọi được Zalo: %s' % e

    try:
        d = r.json()
    except ValueError:
        return False, None, 'Zalo trả về phản hồi không đọc được (HTTP %s).' % r.status_code

    ma = d.get('error')
    if ma == 0:
        return True, d.get('data'), None
    return False, d, '%s (mã %s)' % (d.get('message') or 'Zalo từ chối', ma)


def thong_tin_oa(token=None):
    """Hồ sơ OA đứng sau token này. Trả `(ok, dữ_liệu, lỗi)`.

    Đây là lời gọi RẺ NHẤT chứng minh token còn sống, và phản hồi của nó chứa
    `is_verified` — tức chính câu trả lời cho "OA của tôi đã xác thực chưa"
    theo lời Zalo, chứ không theo phán đoán của người đọc giao diện.
    """
    return _goi_oa('v2.0/oa/getoa', token or _thong_so()['token'])


def nguoi_quan_tam(token=None, so=5):
    """Vài người đang quan tâm OA. Trả `(ok, dữ_liệu, lỗi)`.

    Cần cho việc chẩn đoán vì tin tư vấn đi theo `user_id`, mà `user_id` chỉ
    có sau khi người ta bấm quan tâm hoặc nhắn cho OA. Không có ai ở đây thì
    chưa thử gửi được — và biết điều đó TRƯỚC thì đỡ kết luận nhầm là "API
    hỏng" trong khi thật ra là "chưa có ai để gửi".

    `data` của Zalo là một chuỗi JSON nằm trong query, không phải tham số rời.
    """
    return _goi_oa('v2.0/oa/getfollowers', token or _thong_so()['token'],
                   params={'data': json.dumps({'offset': 0, 'count': int(so)})})


def soan_tin_tu_van(user_id, chu: str) -> dict:
    """Thân request của MỘT tin tư vấn. Tách ra vì đúng lý do `soan_zns` tách:
    chế độ thử phải xem được chính xác thứ sẽ đi, không phải một bản dựng lại."""
    return {'recipient': {'user_id': str(user_id)},
            'message': {'text': chu}}


def gui_tin_tu_van(user_id, chu: str, token=None):
    """Gửi MỘT tin tư vấn. Trả `(thành_công, mã_tin, câu_lỗi)`.

    KHÁC ZNS ở ba điểm phải nhớ, vì cả ba đều đổi cách nơi gọi phải hành xử:

      · đi theo `user_id` chứ không theo số điện thoại;
      · chỉ gửi được khi người dùng đã tương tác với OA, và chỉ trong 48 giờ
        kể từ lần tương tác gần nhất (8 tin đầu miễn phí, sau đó tính tiền);
      · nội dung TỰ DO, không cần mẫu duyệt trước.

    Điều kiện 48 giờ nghĩa là đường này KHÔNG thay thế được ZNS cho việc gửi
    báo cáo định kỳ: phụ huynh phải nhắn trước thì mới gửi được. Mã ở đây
    không giả vờ ngược lại — nó chỉ gửi và trả về đúng thứ Zalo nói.
    """
    t = token or _thong_so()['token']
    if che_do_thu():
        log.info('Tin tư vấn [CHẾ ĐỘ THỬ] không gửi thật: %s',
                 soan_tin_tu_van(user_id, chu))
        return True, 'THU:%s' % str(user_id)[-4:], None

    ok, d, loi = _goi_oa('v3.0/oa/message/cs', t, body=soan_tin_tu_van(user_id, chu))
    if not ok:
        return False, None, loi
    return True, str((d or {}).get('message_id') or ''), None
