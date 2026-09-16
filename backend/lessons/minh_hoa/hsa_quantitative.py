"""Minh hoạ cho các bài Tư duy Định lượng chưa có (16/09/2026) — xem `__init__.py`.

Mỗi mục: số bài (sort_order) → (chỉ số thẻ trong `theory.full.cards`, khối visual).
Mọi con số đã tính tay; ví dụ đặt ở chú thích bên cạnh để người sửa sau soát lại được.
"""

MINH_HOA = {
    # Dãy số: cùng u₁ = 3 — cộng đi đều (d = 4), nhân bứt lên (q = 2). u₅: 3+16 = 19; 3·2⁴ = 48.
    2: (3, {
        'type': 'table', 'badge': 'CÙNG SỐ ĐẦU u₁ = 3',
        'head': ['', 'Cấp số cộng', 'Cấp số nhân'],
        'rows': [
            ['Dãy', '3, 7, 11, 15, …', '3, 6, 12, 24, …'],
            ['Dấu hiệu', 'hiệu không đổi d = 4', 'tỉ số không đổi q = 2'],
            ['Số hạng tổng quát', 'uₙ = 3 + (n − 1)·4', 'uₙ = 3·2ⁿ⁻¹'],
            ['u₅', '19', '48'],
            ['u₁₀', '39', '1.536'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Lấy hai số liên tiếp <b>trừ</b> nhau: đều nhau → cấp số cộng. Lấy <b>chia</b> nhau: đều nhau → '
                   'cấp số nhân. Cùng xuất phát từ 3, tới u₁₀ dãy nhân đã gấp gần 40 lần dãy cộng.',
    }),
    # Hằng đẳng thức: thử a = 3, b = 2. (a+b)² = 25 ≠ a² + b² = 13.
    3: (0, {
        'type': 'table', 'badge': 'THỬ VỚI a = 3, b = 2',
        'head': ['Hằng đẳng thức', 'Khai triển', 'Giá trị'],
        'rows': [
            ['(a + b)²', 'a² + 2ab + b²', '25'],
            ['(a − b)²', 'a² − 2ab + b²', '1'],
            ['a² − b²', '(a − b)(a + b)', '5'],
            ['(a + b)³', 'a³ + 3a²b + 3ab² + b³', '125'],
            ['a³ + b³', '(a + b)(a² − ab + b²)', '35'],
        ],
        'align': ['left', 'left', 'right'],
        'caption': 'Nghi ngờ một khai triển thì <b>thay số nhỏ</b> vào cả hai vế. Bẫy kinh điển: (a + b)² = 25 '
                   'nhưng a² + b² chỉ bằng 13 — thiếu mất 2ab = 12.',
    }),
    # Phương pháp thế: {x + y = 5 ; 2x − y = 1} → y = 5 − x → 2x − 5 + x = 1 → x = 2, y = 3.
    5: (1, {
        'type': 'flow', 'badge': 'VÍ DỤ: x + y = 5 và 2x − y = 1',
        'steps': [
            {'label': 'Rút một ẩn', 'note': 'y = 5 − x', 'color': 'slate'},
            {'label': 'Thế vào PT kia', 'note': '2x − (5 − x) = 1', 'color': 'violet'},
            {'label': 'Giải PT một ẩn', 'note': '3x = 6 → x = 2', 'color': 'violet'},
            {'label': 'Thế ngược', 'note': 'y = 5 − 2 = 3', 'color': 'teal'},
            {'label': 'Thử lại cả hai PT', 'note': '2 + 3 = 5 ✓ · 4 − 3 = 1 ✓', 'color': 'amber'},
        ],
        'caption': 'Rút ẩn nào có hệ số 1 (ở đây là y trong PT đầu) để khỏi phải chia. Bước thử lại '
                   'chỉ mất vài giây nhưng bắt được hầu hết lỗi dấu.',
    }),
    # y = 2x − 3: cắt Oy tại (0; −3), cắt Ox tại (1,5; 0).
    6: (1, {
        'type': 'curve', 'fn': '2*x - 3', 'from': -1, 'to': 4,
        'marks': [{'at': 0, 'label': 'cắt Oy (0; −3)'}, {'at': 1.5, 'label': 'cắt Ox (1,5; 0)'}],
        'caption': 'y = 2x − 3: b = −3 là chỗ cắt trục tung, −b/a = 3/2 là chỗ cắt trục hoành. '
                   'a = 2 &gt; 0 nên đường <b>đi lên</b>; đổi a thành −2 thì lật xuống.',
    }),
    # y = 2ˣ: đồng biến, luôn dương, qua (0; 1) và (2; 4).
    8: (1, {
        'type': 'curve', 'fn': '2^x', 'from': -3, 'to': 3,
        'marks': [{'at': 0, 'label': '(0; 1)'}, {'at': 2, 'label': '(2; 4)'}],
        'caption': 'y = 2ˣ với a = 2 &gt; 1: <b>đồng biến</b>, không bao giờ chạm trục hoành (luôn dương), '
                   'và mọi hàm mũ đều đi qua (0; 1) vì a⁰ = 1. Với 0 &lt; a &lt; 1 đồ thị là ảnh lật qua trục tung.',
    }),
    # y = x³ − 3x: y′ = 3x² − 3 = 0 ⇔ x = ±1; y(−1) = 2 (cực đại), y(1) = −2 (cực tiểu).
    9: (3, {
        'type': 'curve', 'fn': 'x^3 - 3*x', 'from': -2.5, 'to': 2.5,
        'marks': [{'at': -1, 'label': 'cực đại (−1; 2)'}, {'at': 1, 'label': 'cực tiểu (1; −2)'}],
        'caption': 'y = x³ − 3x có y′ = 3x² − 3, bằng 0 tại x = ±1. Qua x = −1 dấu y′ đổi từ + sang − → '
                   '<b>cực đại</b>; qua x = 1 đổi từ − sang + → <b>cực tiểu</b>. Đỉnh đồi và đáy thung lũng '
                   'chính là hai chỗ tiếp tuyến nằm ngang.',
    }),
    # y = x³ − 3x + 1 trên [−2; 2]: y(−2) = −1, y(−1) = 3, y(1) = −1, y(2) = 3.
    10: (2, {
        'type': 'table', 'badge': 'y = x³ − 3x + 1 TRÊN ĐOẠN [−2; 2]',
        'head': ['Điểm xét', 'Vì sao xét', 'Giá trị y'],
        'rows': [
            ['x = −2', 'đầu mút trái', '−1'],
            ['x = −1', 'y′ = 3x² − 3 = 0', '3'],
            ['x = 1', 'y′ = 0', '−1'],
            ['x = 2', 'đầu mút phải', '3'],
        ],
        'highlight': [2], 'align': ['left', 'left', 'right'],
        'caption': 'So bốn giá trị: <b>max = 3</b> (tại x = −1 và x = 2), <b>min = −1</b> (tại x = −2 và x = 1). '
                   'Hai đầu mút cho đúng max/min như hai điểm tới hạn — bỏ quên đầu mút là lỗi phổ biến nhất.',
    }),
    # Giá trị lượng giác đặc biệt.
    11: (2, {
        'type': 'table', 'badge': 'BA GÓC PHẢI THUỘC',
        'head': ['α', '30°', '45°', '60°'],
        'rows': [
            ['sin α', '1/2', '√2/2', '√3/2'],
            ['cos α', '√3/2', '√2/2', '1/2'],
            ['tan α', '√3/3', '1', '√3'],
        ],
        'align': ['left', 'right', 'right', 'right'],
        'caption': 'Hàng sin tăng theo dãy 1/2 → √2/2 → √3/2; hàng cos là <b>chính dãy ấy đọc ngược</b>. '
                   'Thuộc một hàng là suy ra hàng kia; tan = sin/cos.',
    }),
    # S = πR²: R = 1, 2, 3, 4 → π, 4π, 9π, 16π.
    12: (2, {
        'type': 'bars', 'badge': 'S = πR²', 'max': 50.3,
        'bars': [
            {'label': 'R = 1', 'value': 3.14, 'display': 'π ≈ 3,14', 'color': 'slate'},
            {'label': 'R = 2', 'value': 12.57, 'display': '4π ≈ 12,57', 'color': 'teal'},
            {'label': 'R = 3', 'value': 28.27, 'display': '9π ≈ 28,27', 'color': 'violet'},
            {'label': 'R = 4', 'value': 50.27, 'display': '16π ≈ 50,27', 'color': 'amber'},
        ],
        'caption': 'Bán kính gấp đôi thì diện tích gấp <b>bốn</b>, gấp ba thì gấp <b>chín</b> — vì R bị bình phương. '
                   'Chu vi 2πR chỉ tăng cùng tỉ lệ với R: 2π, 4π, 6π, 8π.',
    }),
    # Cùng đáy S = 12, cao h = 5: lăng trụ 60, chóp 20.
    13: (2, {
        'type': 'bars', 'badge': 'CÙNG ĐÁY S = 12, CÙNG CHIỀU CAO h = 5', 'max': 60,
        'bars': [
            {'label': 'Lăng trụ / hình trụ', 'value': 60, 'display': 'S·h = 60', 'color': 'violet'},
            {'label': 'Hình chóp / hình nón', 'value': 20, 'display': 'S·h/3 = 20', 'color': 'teal'},
        ],
        'caption': 'Chóp và nón chỉ chứa được <b>một phần ba</b> lăng trụ hay hình trụ cùng đáy, cùng chiều cao. '
                   'Hệ số 1/3 là chỗ đề hay gài: quên nó là kết quả gấp ba lần đáp án.',
    }),
    # A(1; 2), B(4; 6): Δx = 3, Δy = 4 → AB = 5.
    14: (1, {
        'type': 'table', 'badge': 'A(1; 2), B(4; 6)',
        'head': ['Bước', 'Tính', 'Kết quả'],
        'rows': [
            ['Hiệu hoành độ', '4 − 1', '3'],
            ['Hiệu tung độ', '6 − 2', '4'],
            ['Bình phương rồi cộng', '3² + 4²', '25'],
            ['Căn bậc hai', '√25', '5'],
        ],
        'align': ['left', 'left', 'right'],
        'caption': 'AB = 5 — chính là tam giác vuông 3-4-5: cạnh ngang 3, cạnh dọc 4, cạnh huyền là AB. '
                   'Trung điểm M của AB là ((1 + 4)/2 ; (2 + 6)/2) = (2,5 ; 4).',
    }),
    # A(0;0;0), B(1;2;2): 1 + 4 + 4 = 9 → AB = 3.
    15: (2, {
        'type': 'flow', 'badge': 'VÍ DỤ: A(0; 0; 0), B(1; 2; 2)',
        'steps': [
            {'label': 'Hiệu ba tọa độ', 'note': '(1; 2; 2)', 'color': 'slate'},
            {'label': 'Bình phương từng hiệu', 'note': '1, 4, 4', 'color': 'violet'},
            {'label': 'Cộng lại', 'note': '9', 'color': 'violet'},
            {'label': 'Lấy căn', 'note': 'AB = 3', 'color': 'teal'},
        ],
        'caption': 'So với mặt phẳng Oxy chỉ thêm đúng một thành phần z vào tổng bình phương. '
                   'Vectơ AB = (1; 2; 2) và |AB| = 3 là cùng một phép tính.',
    }),
    # Chọn 2 trong 4: A(4,2) = 12, C(4,2) = 6, 12 = 6·2!.
    16: (3, {
        'type': 'table', 'badge': 'CHỌN 2 TRONG 4 PHẦN TỬ a, b, c, d',
        'head': ['', 'Có thứ tự — chỉnh hợp', 'Không thứ tự — tổ hợp'],
        'rows': [
            ['Công thức', 'A(4,2) = 4!/2! = 12', 'C(4,2) = 4!/(2!·2!) = 6'],
            ['Liệt kê', 'ab, ba, ac, ca, ad, da, bc, cb, bd, db, cd, dc', 'ab, ac, ad, bc, bd, cd'],
            ['Quan hệ', 'A(n,k) = C(n,k) · k!', '12 = 6 · 2'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Cùng một câu "chọn 2 trong 4": đề có quan tâm <b>ai đứng trước ai đứng sau</b> không là đã '
                   'chọn xong công thức. Mỗi tổ hợp {a, b} sinh ra k! = 2 chỉnh hợp ab và ba.',
    }),
    # Tung một xúc xắc: 6 kết quả đồng khả năng.
    17: (1, {
        'type': 'bars', 'badge': 'TUNG MỘT XÚC XẮC — 6 KẾT QUẢ ĐỒNG KHẢ NĂNG', 'max': 6,
        'bars': [
            {'label': 'Ra số chẵn (2, 4, 6)', 'value': 3, 'display': '3/6 = 1/2', 'color': 'violet'},
            {'label': 'Ra số lớn hơn 4 (5, 6)', 'value': 2, 'display': '2/6 = 1/3', 'color': 'teal'},
            {'label': 'Ra đúng số 6', 'value': 1, 'display': '1/6', 'color': 'amber'},
            {'label': 'Ra số không quá 6', 'value': 6, 'display': '6/6 = 1', 'color': 'slate'},
        ],
        'caption': 'P = số kết quả thuận lợi / 6. Biến cố chắc chắn có P = 1. Biến cố đối của "số chẵn" là '
                   '"số lẻ": P = 1 − 1/2 = 1/2 — khi đề hỏi "ít nhất" hay "không có", tính biến cố đối nhanh hơn.',
    }),
    # Số liệu 2, 3, 3, 4, 18: trung bình 30/5 = 6; trung vị 3; mốt 3.
    18: (0, {
        'type': 'table', 'badge': 'SỐ LIỆU: 2, 3, 3, 4, 18',
        'head': ['Đại lượng', 'Giá trị', 'Vì sao'],
        'rows': [
            ['Trung bình cộng', '30/5 = 6', 'bị số 18 kéo lên'],
            ['Trung vị', '3', 'giá trị đứng giữa; đổi 18 thành 180 vẫn là 3'],
            ['Mốt', '3', 'xuất hiện 2 lần, nhiều nhất'],
        ],
        'align': ['left', 'right', 'left'],
        'caption': 'Bốn trong năm số liệu không quá 4, nhưng trung bình lại là 6 — một giá trị cực đoan là đủ '
                   'kéo lệch. Khi ấy <b>trung vị</b> đại diện tốt hơn; đề HSA hay hỏi đúng chỗ khác nhau này.',
    }),
    # Quy tắc cộng vs nhân.
    19: (3, {
        'type': 'tree', 'badge': 'HỎI MỘT CÂU TRƯỚC KHI ĐẾM',
        'root': {'label': 'Bài toán đếm', 'note': 'các phương án quan hệ với nhau thế nào?'},
        'branches': [
            {'label': 'Chỉ chọn MỘT phương án', 'note': 'từ khoá "hoặc"', 'color': 'violet',
             'children': [{'label': 'Quy tắc CỘNG', 'note': 'm + n'},
                          {'label': 'Ví dụ', 'note': 'mặc 1 trong 3 áo HOẶC 1 trong 2 quần → 5 cách'}]},
            {'label': 'Làm HẾT các công đoạn', 'note': 'từ khoá "và", "rồi"', 'color': 'teal',
             'children': [{'label': 'Quy tắc NHÂN', 'note': 'm × n'},
                          {'label': 'Ví dụ', 'note': 'chọn 1 áo RỒI 1 quần → 3 × 2 = 6 bộ'}]},
        ],
        'caption': 'Cùng ba áo và hai quần, câu hỏi đổi một chữ là đáp án đổi từ 5 thành 6. '
                   'Mọi bài đếm phức tạp đều là hai quy tắc này lồng vào nhau.',
    }),
    # Sản lượng minh hoạ: 2015 so 2010 tăng 5,1 → 12,75 %.
    21: (1, {
        'type': 'bars', 'badge': 'SẢN LƯỢNG LÚA (triệu tấn, số liệu minh hoạ)', 'max': 50,
        'bars': [
            {'label': '2010', 'value': 40.0, 'display': '40,0', 'color': 'slate'},
            {'label': '2015', 'value': 45.1, 'display': '45,1', 'color': 'violet'},
            {'label': '2020', 'value': 42.8, 'display': '42,8', 'color': 'slate'},
            {'label': '2023', 'value': 43.5, 'display': '43,5', 'color': 'slate'},
        ],
        'caption': 'Cột cao nhất là 2015. So với 2010: chênh 45,1 − 40,0 = 5,1 triệu tấn, tức tăng '
                   '5,1/40 = <b>12,75 %</b>. Đọc đơn vị trên trục trước khi so cột — "triệu tấn" và "nghìn tấn" '
                   'nhìn giống hệt nhau trên hình.',
    }),
    # Mô hình toán cho bài thực tế. Lãi kép: 10 × 1,06² = 11,236.
    22: (1, {
        'type': 'table', 'badge': 'TỪ TÌNH HUỐNG SANG CÔNG THỨC',
        'head': ['Tình huống', 'Mô hình', 'Ví dụ'],
        'rows': [
            ['Chuyển động', 's = v · t', '60 km/h × 1,5 h = 90 km'],
            ['Giảm giá', 'giá sau = giá × (1 − %)', '200.000 × (1 − 20 %) = 160.000'],
            ['Lãi kép', 'A = P · (1 + r)ⁿ', '10 triệu, 6 %/năm, 2 năm → 11,236 triệu'],
            ['Năng suất', 'việc = năng suất × thời gian', '3 người × 4 giờ = 12 công'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Nhận ra dạng là chọn được công thức trong vài giây. Lãi kép cộng dồn: sau năm 1 có 10,6 triệu, '
                   'năm 2 tính 6 % trên 10,6 chứ không trên 10 — đó là chỗ khác lãi đơn.',
    }),
    # Nhẩm phần trăm của 840.
    23: (0, {
        'type': 'bars', 'badge': 'CÁC MỐC CỦA 840', 'max': 420,
        'bars': [
            {'label': '50 % (chia 2)', 'value': 420, 'display': '420', 'color': 'violet'},
            {'label': '25 % (chia 4)', 'value': 210, 'display': '210', 'color': 'violet'},
            {'label': '10 % (chia 10)', 'value': 84, 'display': '84', 'color': 'teal'},
            {'label': '5 % (nửa của 10 %)', 'value': 42, 'display': '42', 'color': 'teal'},
            {'label': '1 % (chia 100)', 'value': 8.4, 'display': '8,4', 'color': 'slate'},
        ],
        'caption': 'Ghép mốc để nhẩm phần trăm bất kì: 15 % của 840 = 10 % + 5 % = 84 + 42 = <b>126</b>; '
                   '35 % = 25 % + 10 % = 294. Không cần nhân 840 × 0,15 trong đầu.',
    }),
    # 75 phút = 47 + 23 + 5.
    24: (0, {
        'type': 'pie', 'unit': 'phút', 'badge': '75 PHÚT CHO 50 CÂU',
        'slices': [
            {'label': 'Lượt 1 — câu dễ và vừa', 'value': 47, 'color': 'violet'},
            {'label': 'Lượt 2 — câu khó và câu điền', 'value': 23, 'color': 'teal'},
            {'label': 'Rà soát cuối giờ', 'value': 5, 'color': 'amber'},
        ],
        'caption': 'Trung bình 1,5 phút một câu, nhưng không chia đều: gần <b>hai phần ba</b> thời gian dành cho '
                   'câu chắc điểm. Câu khó chỉ được nhận phần thời gian còn lại, không được vay của câu dễ.',
    }),
    # Câu điền đáp án: không có phương án để loại trừ.
    25: (1, {
        'type': 'flow', 'badge': 'KHÔNG CÓ BỐN PHƯƠNG ÁN ĐỂ SO',
        'steps': [
            {'label': 'Đọc yêu cầu', 'note': 'làm tròn tới đâu? đơn vị gì?', 'color': 'slate'},
            {'label': 'Tính', 'note': 'viết ra giấy, không nhẩm tắt', 'color': 'violet'},
            {'label': 'Thử thay ngược', 'note': 'kết quả có thoả đề không?', 'color': 'teal'},
            {'label': 'Ghi đúng định dạng', 'note': '2,5 hay 2.5 — theo quy ước đề', 'color': 'amber'},
        ],
        'caption': 'Bước thử ngược thay cho việc so đáp án của câu trắc nghiệm. Sai định dạng hay sai đơn vị '
                   'mất trọn điểm dù tính đúng.',
    }),
    # Thế ngược đáp án vào 2x + 3 = 11.
    26: (1, {
        'type': 'table', 'badge': 'GIẢI 2x + 3 = 11 BẰNG CÁCH THẾ NGƯỢC',
        'head': ['Đáp án', 'Thế vào 2x + 3', 'Kết luận'],
        'rows': [
            ['A. x = 2', '2·2 + 3 = 7', 'loại'],
            ['B. x = 3', '2·3 + 3 = 9', 'loại'],
            ['C. x = 4', '2·4 + 3 = 11', 'ĐÚNG'],
            ['D. x = 5', '2·5 + 3 = 13', 'loại'],
        ],
        'highlight': [1], 'align': ['left', 'left', 'left'],
        'caption': 'Thử đáp án <b>ở giữa</b> trước (B hoặc C): thế B ra 9 &lt; 11 thì A còn nhỏ hơn, loại luôn '
                   'cả hai — thường chỉ cần thử hai lần là xong.',
    }),
    # Bốn đề: điểm lên nhờ bớt bỏ dở.
    27: (1, {
        'type': 'bars', 'badge': 'SỔ THEO DÕI (ví dụ)', 'max': 50,
        'bars': [
            {'label': 'Đề 1', 'value': 28, 'display': '28/50', 'note': 'bỏ dở 9 câu', 'color': 'slate'},
            {'label': 'Đề 2', 'value': 31, 'display': '31/50', 'note': 'bỏ dở 6 câu', 'color': 'slate'},
            {'label': 'Đề 3', 'value': 35, 'display': '35/50', 'note': 'bỏ dở 3 câu', 'color': 'teal'},
            {'label': 'Đề 4', 'value': 38, 'display': '38/50', 'note': 'làm hết', 'color': 'violet'},
        ],
        'caption': 'Ghi cả điểm lẫn số câu bỏ dở. Ở đây điểm lên 10 câu sau bốn đề chủ yếu nhờ <b>bớt bỏ dở</b> — '
                   'tức nhờ tốc độ và tâm lý, chưa phải nhờ học thêm kiến thức. Hai thứ ấy cần hai cách chữa khác nhau.',
    }),
}
