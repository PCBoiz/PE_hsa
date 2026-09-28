"""CÒN MÃ ĐỘT BIẾN NẰM LẠI KHÔNG? — bước cổng, chạy dưới một giây.

── VÌ SAO (27/09/2026) ──────────────────────────────────────────────────────

`scripts/dot_bien.py` ghi bản gốc ra `.dot_bien_cuu_ho.json` trước khi thay mã, và phục
hồi khi KHỞI ĐỘNG lượt sau. Cách ấy cứu được lượt bị Ctrl-C — nhưng chỉ khi có một lượt
sau. Đêm 26/09 phiên chết giữa loạt đột biến vì máy hết RAM, và sáng ra `teaching/hoc_lieu.py`
vẫn mang đột biến đầu tiên: chỗ kiểm buổi bù bị thay bằng `%s IS NOT NULL` — nghĩa là tài
liệu của một buổi bù hiện cho cả lớp. Mã ấy chạy được, `ruff` sạch, `manage.py check` sạch,
và nếu đem chạy cả bộ kiểm thì ĐỎ — nhưng cổng pre-push không chạy pytest theo mặc định.
Một dòng như thế đi thẳng vào commit mà không bước nào kêu.

Sổ cứu hộ đã ghi đủ mọi thứ cần để bắt: đường dẫn tệp và bản gốc từng ký tự. Thiếu đúng
một người ĐỌC nó vào lúc đáng đọc — tức ngay trước khi đẩy.

Trả 0 khi sạch, 1 khi còn sót. Không tự sửa: phục hồi một tệp ngay trước lúc đẩy là thay
đổi thứ người ta sắp gửi đi mà họ không kịp nhìn.
"""
import io
import json
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
SO = GOC / '.dot_bien_cuu_ho.json'


def main() -> int:
    if not SO.is_file():
        print('không có loạt đột biến nào đang dở')
        return 0
    try:
        s = json.loads(SO.read_text(encoding='utf-8'))
        duong = Path(s['tep'])
        goc = s['goc']
    except (OSError, ValueError, KeyError) as e:
        # Sổ hỏng thì KHÔNG chặn: nó là cái phao, không phải cái khoá. Nhưng phải nói ra —
        # một cái phao thủng mà im lặng còn tệ hơn không có phao.
        print('sổ cứu hộ đọc không được (%s) — bỏ qua bước này' % e)
        return 0

    if not duong.is_file():
        print('sổ cứu hộ trỏ tới tệp không còn: %s' % duong)
        return 0

    nay = io.open(duong, encoding='utf-8', newline='').read()
    if nay == goc:
        print('sạch — %s đúng bằng bản gốc' % duong.name)
        return 0

    ten = duong.name
    print('CÒN MÃ ĐỘT BIẾN NẰM LẠI trong %s' % ten)
    print('  Một loạt đột biến đã đứt giữa chừng và tệp chưa trở về bản gốc.')
    print('  Bản gốc nằm trong .dot_bien_cuu_ho.json (%d ký tự).' % len(goc))
    print('  Phục hồi: python scripts/dot_bien.py <tệp> --test <đường> --loat <json>')
    print('            (nó phục hồi ngay lúc khởi động), hoặc chép tay từ sổ.')
    print('  ĐỪNG commit trước khi tệp trở về bản gốc — mã đột biến chạy được và')
    print('  qua được ruff, nên không bước nào khác của cổng bắt nó.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
