"""Minh hoạ trực quan cho lý thuyết bài học — bộ soạn sẵn cho 67 bài chưa có (16/09/2026).

── VÌ SAO CÓ (việc (4) của hướng bán đứt) ─────────────────────────────────

Engine bài học (`lesson_hsa.js::renderVisual`) vẽ được TÁM loại minh hoạ từ JSON
— bars, numline, curve, flow, table, pie, tree, timeline — không cần ảnh. Nhưng
tới 16/09 chỉ 9/76 bài có minh hoạ (14 khối), phần lớn bài học là bốn thẻ chữ.
Người mua mở một bài bất kì sẽ thấy khác hẳn nếu bài nào cũng có một hình.

── LUẬT SOẠN ─────────────────────────────────────────────────────────────

· Mỗi bài MỘT khối, gắn vào đúng thẻ (`theory.full.cards[i]`) mà nó minh hoạ —
  chọn loại theo NỘI DUNG thẻ (hàm → curve, so sánh → table/bars, quy trình →
  flow, phân loại → tree, mốc → timeline, cơ cấu → pie), không theo ý thích.
· Mọi con số tính tay và ghi cách tính ở chú thích cạnh mục. Số liệu không có
  trong thẻ thì ghi rõ "ví dụ" / "minh hoạ" ngay trên khối, không bịa số thật.
· Chú thích (`caption`) nói thứ hình KHÔNG tự nói được: cái bẫy, cách nhớ, chỗ
  đề hay hỏi. Chỉ dùng thẻ trong `lessons.content.THE_CHO_PHEP`.
· Không ghi đè minh hoạ đã có: thẻ nào đã có `visual` thì bỏ qua, in ra để biết.

── CẢ BẢN TÓM TẮT, KHÔNG CHỈ BẢN ĐẦY ĐỦ (đo 16/09/2026) ─────────────────

Engine chọn bản lý thuyết theo điểm bước 1: `weak` → `full`, còn `ok` và `strong`
→ `condensed`. Ngưỡng `ok_min` mặc định là 1 — tức em trả lời đúng MỘT câu đã
thấy bản tóm tắt. Đi thử đúng đường học viên với ba cách chọn đáp án khác nhau
ở bốn bài: cả 12 lượt đều rơi vào bản tóm tắt. Minh hoạ chỉ gắn ở `full` thì
phần lớn học viên — và người mua đang xem trình diễn — không bao giờ thấy.

Nên mỗi minh hoạ gắn CẢ vào một thẻ của bản tóm tắt. Thẻ nào: chọn theo số từ
trùng giữa tiêu đề thẻ đầy đủ và thẻ tóm tắt; bảy chỗ heuristic ấy chọn sai
(bảng lượng giác rơi vào "Định lý Pytago"…) thì ghi tay ở `THE_TOM_TAT`.

Nạp vào CSDL: `python manage.py nap_minh_hoa --thu` (chỉ kiểm) · `--nap` (ghi).
Đường ghi đi qua `validate_lesson` y như đường sửa bài của quản trị viên.
"""
from lessons.minh_hoa import hsa_quantitative, hsa_science, hsa_verbal

BO_MINH_HOA = {
    'hsa_quantitative': hsa_quantitative.MINH_HOA,
    'hsa_science': hsa_science.MINH_HOA,
    'hsa_verbal': hsa_verbal.MINH_HOA,
}

#: (khoá, số bài) → chỉ số thẻ TÓM TẮT nhận bản sao minh hoạ, khi heuristic chọn sai.
#: Soát tay từng dòng ngày 16/09/2026 trên bảng in ra bởi `--thu`.
THE_TOM_TAT = {
    ('hsa_quantitative', 11): 1,   # bảng sin/cos/tan → "Tỉ số lượng giác", không phải "Định lý Pytago"
    ('hsa_quantitative', 21): 1,   # cột sản lượng → "Đọc biểu đồ"
    ('hsa_quantitative', 22): 1,   # bảng mô hình → "Công thức hay dùng"
    ('hsa_quantitative', 26): 1,   # thế ngược → "Thử đáp án"
    ('hsa_science', 6): 1,         # chu kì 3 → "Bảng tuần hoàn"
    ('hsa_science', 22): 1,        # khai thác Atlat → "Đọc bản đồ"
    ('hsa_verbal', 18): 0,         # sáu phong cách → "Một số phong cách"
}

#: 9 bài đã có minh hoạ soạn tay TỪ TRƯỚC (không nằm trong bộ này) cũng chỉ gắn ở bản đầy
#: đủ — cùng lỗ "không ai thấy". `nap_minh_hoa` sao hình có sẵn sang thẻ tóm tắt còn trống:
#: (khoá, số bài) → thẻ tóm tắt nhận HÌNH ĐẦU TIÊN; hình sau rơi vào thẻ trống hợp nhất.
#: Soát tay 17/09/2026 trên bảng in ra bởi `--thu`.
THE_TOM_TAT_CO_SAN = {
    ('hsa_quantitative', 4): 1,    # trục số bất phương trình → "Vi-ét & BPT", không phải "PT bậc nhất"
    ('hsa_verbal', 1): 1,          # bốn bước làm bài → "Mẹo loại trừ"
    ('hsa_verbal', 3): 0,          # cây thực từ / hư từ → "Ba từ loại chính"
}
