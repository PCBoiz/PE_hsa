"""Minh hoạ cho các bài Khoa học chưa có (16/09/2026) — xem `__init__.py`."""

MINH_HOA = {
    # Hai điện trở 6 Ω và 3 Ω: nối tiếp 9 Ω; song song 1/R = 1/6 + 1/3 = 1/2 → 2 Ω.
    2: (1, {
        'type': 'table', 'badge': 'HAI CÁCH MẮC — CÙNG HAI ĐIỆN TRỞ 6 Ω VÀ 3 Ω',
        'head': ['', 'Nối tiếp', 'Song song'],
        'rows': [
            ['Dòng điện', 'bằng nhau: I = I₁ = I₂', 'cộng lại: I = I₁ + I₂'],
            ['Hiệu điện thế', 'cộng lại: U = U₁ + U₂', 'bằng nhau: U = U₁ = U₂'],
            ['Điện trở tương đương', 'R = R₁ + R₂', '1/R = 1/R₁ + 1/R₂'],
            ['Với 6 Ω và 3 Ω', 'R = 9 Ω', 'R = 2 Ω'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Nối tiếp thì <b>cộng điện trở</b>, song song thì <b>cộng nghịch đảo</b>. Mắc song song luôn cho '
                   'điện trở tương đương NHỎ hơn điện trở nhỏ nhất (2 Ω &lt; 3 Ω) — dấu hiệu để tự kiểm kết quả.',
    }),
    # Q = m·c·Δt với m = 1 kg, Δt = 10 °C. c (J/kg·K): nước 4200, nhôm 880, sắt 460, đồng 380.
    3: (3, {
        'type': 'bars', 'badge': 'Q = m·c·Δt VỚI m = 1 kg, Δt = 10 °C', 'max': 42000,
        'bars': [
            {'label': 'Nước (c = 4.200)', 'value': 42000, 'display': '42.000 J', 'color': 'violet'},
            {'label': 'Nhôm (c = 880)', 'value': 8800, 'display': '8.800 J', 'color': 'teal'},
            {'label': 'Sắt (c = 460)', 'value': 4600, 'display': '4.600 J', 'color': 'slate'},
            {'label': 'Đồng (c = 380)', 'value': 3800, 'display': '3.800 J', 'color': 'slate'},
        ],
        'caption': 'Cùng khối lượng, cùng độ tăng nhiệt: nước cần gấp <b>hơn 10 lần</b> nhiệt lượng so với đồng. '
                   'Nhiệt dung riêng lớn cũng nghĩa là nguội chậm — vì thế biển điều hoà khí hậu vùng ven bờ.',
    }),
    # T = 1/f; số dao động trong 1 phút = 60·f.
    4: (1, {
        'type': 'table', 'badge': 'T = 1/f',
        'head': ['Tần số f (Hz)', 'Chu kì T (s)', 'Số dao động trong 1 phút'],
        'rows': [
            ['0,5', '2', '30'],
            ['2', '0,5', '120'],
            ['5', '0,2', '300'],
            ['50', '0,02', '3.000'],
        ],
        'align': ['left', 'right', 'right'],
        'caption': 'f và T nghịch đảo nhau: f tăng 10 lần thì T giảm 10 lần. Đề cho "trong 1 phút có 120 dao động" '
                   'thì f = 120/60 = 2 Hz — nhớ đổi phút ra giây trước.',
    }),
    # Ba loại tia phóng xạ.
    5: (2, {
        'type': 'table', 'badge': 'SO SÁNH BA TIA',
        'head': ['Tia', 'Bản chất', 'Điện tích', 'Đâm xuyên', 'Chặn bằng'],
        'rows': [
            ['α', 'hạt nhân heli', '+', 'yếu', 'tờ giấy'],
            ['β', 'electron', '−', 'trung bình', 'tấm nhôm mỏng'],
            ['γ', 'sóng điện từ', 'không', 'mạnh', 'bê tông dày, chì'],
        ],
        'align': ['left', 'left', 'left', 'left', 'left'],
        'caption': 'Đâm xuyên tăng dần α → β → γ, và điện tích cũng là dấu hiệu: tia α và β bị điện trường '
                   'làm lệch về hai phía ngược nhau, tia γ đi thẳng.',
    }),
    # Chu kì 3: Na → Cl, kim loại giảm, phi kim tăng.
    6: (3, {
        'type': 'flow', 'badge': 'CHU KÌ 3, ĐI TỪ TRÁI SANG PHẢI',
        'steps': [
            {'label': 'Na', 'note': 'kim loại mạnh', 'color': 'violet'},
            {'label': 'Mg', 'note': 'kim loại', 'color': 'violet'},
            {'label': 'Al', 'note': 'kim loại', 'color': 'violet'},
            {'label': 'Si', 'note': 'á kim', 'color': 'slate'},
            {'label': 'P', 'note': 'phi kim', 'color': 'teal'},
            {'label': 'S', 'note': 'phi kim', 'color': 'teal'},
            {'label': 'Cl', 'note': 'phi kim mạnh', 'color': 'teal'},
        ],
        'caption': 'Trong một chu kì, tính kim loại <b>giảm</b> và tính phi kim <b>tăng</b> từ trái sang phải. '
                   'Đi xuống trong một nhóm thì ngược lại: nhóm IA từ Li → Na → K kim loại mạnh dần.',
    }),
    # Liên kết ion vs cộng hoá trị.
    7: (0, {
        'type': 'table', 'badge': 'HAI KIỂU LIÊN KẾT',
        'head': ['', 'Liên kết ion', 'Liên kết cộng hoá trị'],
        'rows': [
            ['Cách hình thành', 'cho – nhận electron, ion trái dấu hút nhau', 'dùng chung cặp electron'],
            ['Thường gặp giữa', 'kim loại điển hình + phi kim điển hình', 'phi kim + phi kim'],
            ['Ví dụ', 'NaCl, MgO', 'H₂, O₂, H₂O, CO₂'],
            ['Dấu hiệu nhận nhanh', 'có kim loại nhóm IA, IIA', 'công thức toàn phi kim'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Nhìn công thức: có kim loại mạnh (Na, K, Mg, Ca) đứng cạnh phi kim mạnh (Cl, O) → ion; '
                   'toàn phi kim (H, C, N, O) → cộng hoá trị.',
    }),
    # Bốn loại hợp chất vô cơ.
    8: (0, {
        'type': 'tree', 'badge': 'BỐN LOẠI HỢP CHẤT VÔ CƠ',
        'root': {'label': 'Hợp chất vô cơ', 'note': 'nhận ra loại là đoán được tính chất'},
        'branches': [
            {'label': 'Oxit', 'note': 'nguyên tố + oxi', 'color': 'slate',
             'children': [{'label': 'Oxit bazơ', 'note': 'CaO, Na₂O — của kim loại'},
                          {'label': 'Oxit axit', 'note': 'CO₂, SO₂ — của phi kim'}]},
            {'label': 'Axit', 'note': 'H + gốc axit', 'color': 'amber',
             'children': [{'label': 'HCl, H₂SO₄, HNO₃', 'note': 'quỳ tím hoá đỏ'}]},
            {'label': 'Bazơ', 'note': 'kim loại + OH', 'color': 'teal',
             'children': [{'label': 'NaOH, Ca(OH)₂', 'note': 'quỳ tím hoá xanh'}]},
            {'label': 'Muối', 'note': 'kim loại + gốc axit', 'color': 'violet',
             'children': [{'label': 'NaCl, CaCO₃', 'note': 'sản phẩm của trung hoà'}]},
        ],
        'caption': 'Axit + bazơ → muối + nước (HCl + NaOH → NaCl + H₂O). Màu quỳ tím là phép thử nhanh nhất '
                   'để phân biệt axit và bazơ trong đề nhận biết.',
    }),
    # Nhóm chức.
    9: (2, {
        'type': 'table', 'badge': 'NHÓM CHỨC QUYẾT ĐỊNH TÍNH CHẤT',
        'head': ['Nhóm chức', 'Loại chất', 'Ví dụ', 'Gặp ở đâu'],
        'rows': [
            ['−OH', 'ancol', 'C₂H₅OH', 'rượu etylic'],
            ['−COOH', 'axit cacboxylic', 'CH₃COOH', 'giấm ăn'],
            ['−CHO', 'anđehit', 'HCHO', 'fomon'],
            ['C=C', 'anken', 'C₂H₄', 'etilen — làm chín trái cây'],
        ],
        'align': ['left', 'left', 'left', 'left'],
        'caption': 'Cùng khung cacbon hai nguyên tử: gắn −OH là rượu, gắn −COOH là giấm. Đề nhận biết chất hữu cơ '
                   'gần như luôn xoay quanh nhóm chức.',
    }),
    # Tính theo PTHH: 2,4 g Mg (M = 24) → 0,1 mol; 2Mg + O₂ → 2MgO; MgO M = 40 → 4 g.
    10: (3, {
        'type': 'flow', 'badge': 'VÍ DỤ: ĐỐT 2,4 g Mg, THU ĐƯỢC BAO NHIÊU GAM MgO?',
        'steps': [
            {'label': 'Viết & cân bằng PT', 'note': '2Mg + O₂ → 2MgO', 'color': 'slate'},
            {'label': 'Đổi ra mol', 'note': 'n(Mg) = 2,4/24 = 0,1 mol', 'color': 'violet'},
            {'label': 'Dùng tỉ lệ hệ số', 'note': '2 : 2 → n(MgO) = 0,1 mol', 'color': 'violet'},
            {'label': 'Đổi ra gam', 'note': 'm = 0,1 × 40 = 4 g', 'color': 'teal'},
        ],
        'caption': 'Mọi bài tính theo phương trình đều đi bốn bước này. Sai hay rơi ở bước 1 (chưa cân bằng nên '
                   'tỉ lệ sai) và bước 4 (quên M của chất cần tìm).',
    }),
    # Quang hợp ↔ hô hấp.
    11: (2, {
        'type': 'table', 'badge': 'HAI QUÁ TRÌNH NGƯỢC CHIỀU',
        'head': ['', 'Quang hợp', 'Hô hấp tế bào'],
        'rows': [
            ['Diễn ra ở', 'lục lạp (thực vật)', 'ti thể (mọi tế bào)'],
            ['Nguyên liệu', 'CO₂ + H₂O + ánh sáng', 'glucozơ + O₂'],
            ['Sản phẩm', 'glucozơ + O₂', 'CO₂ + H₂O + năng lượng'],
            ['Năng lượng', 'tích luỹ vào chất hữu cơ', 'giải phóng cho hoạt động sống'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Sản phẩm của quá trình này là nguyên liệu của quá trình kia. Cây xanh làm cả hai; '
                   'động vật chỉ hô hấp, nên phụ thuộc vào thực vật cả về thức ăn lẫn oxi.',
    }),
    # Bảng Punnett Aa × Aa: 1 AA : 2 Aa : 1 aa.
    12: (2, {
        'type': 'table', 'badge': 'PHÉP LAI Aa × Aa',
        'head': ['♀ \\ ♂', 'A', 'a'],
        'rows': [
            ['A', 'AA', 'Aa'],
            ['a', 'Aa', 'aa'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Mỗi giao tử chỉ nhận <b>một</b> gen của cặp, nên bố và mẹ Aa đều cho hai loại giao tử A và a. '
                   'Kiểu gen 1 AA : 2 Aa : 1 aa → kiểu hình <b>3 trội : 1 lặn</b> — tỉ lệ 3 : 1 kinh điển của Menđen.',
    }),
    # Chọn lọc tự nhiên.
    13: (2, {
        'type': 'flow', 'badge': 'CƠ CHẾ CHỌN LỌC TỰ NHIÊN',
        'steps': [
            {'label': 'Quần thể có biến dị', 'note': 'cá thể khác nhau chút ít', 'color': 'slate'},
            {'label': 'Đấu tranh sinh tồn', 'note': 'thức ăn, kẻ thù, khí hậu', 'color': 'amber'},
            {'label': 'Cá thể thích nghi sống sót', 'note': 'sinh sản nhiều hơn', 'color': 'violet'},
            {'label': 'Đặc điểm có lợi di truyền', 'note': 'ngày một phổ biến', 'color': 'teal'},
            {'label': 'Quần thể biến đổi', 'note': 'qua nhiều thế hệ → loài mới', 'color': 'teal'},
        ],
        'caption': 'Ví dụ kinh điển: bướm đêm ở Anh thời công nghiệp — thân cây ám bồ hóng đen, bướm màu tối '
                   'khó bị chim thấy nên chiếm ưu thế chỉ sau vài chục thế hệ.',
    }),
    # Chuỗi thức ăn và vòng tuần hoàn vật chất.
    14: (2, {
        'type': 'flow', 'badge': 'MỘT CHUỖI THỨC ĂN',
        'steps': [
            {'label': 'Cỏ', 'note': 'sinh vật sản xuất', 'color': 'teal'},
            {'label': 'Thỏ', 'note': 'tiêu thụ bậc 1', 'color': 'violet'},
            {'label': 'Cáo', 'note': 'tiêu thụ bậc 2', 'color': 'violet'},
            {'label': 'Vi khuẩn, nấm', 'note': 'phân giải xác', 'color': 'amber'},
            {'label': 'Chất vô cơ về đất', 'note': 'cỏ dùng lại', 'color': 'slate'},
        ],
        'caption': 'Mũi tên chỉ chiều "bị ăn"; sinh vật sản xuất luôn đứng đầu. Nhóm phân giải khép kín vòng '
                   'tuần hoàn vật chất — thiếu chúng, xác sinh vật chất đống và đất cạn dinh dưỡng.',
    }),
    # Thành phần máu: huyết tương ~55 %, hồng cầu ~44 %, bạch cầu + tiểu cầu < 1 %.
    15: (3, {
        'type': 'pie', 'unit': '% thể tích', 'badge': 'MÁU GỒM NHỮNG GÌ',
        'slices': [
            {'label': 'Huyết tương', 'value': 55, 'color': 'amber'},
            {'label': 'Hồng cầu', 'value': 44, 'color': 'rose'},
            {'label': 'Bạch cầu và tiểu cầu', 'value': 1, 'color': 'slate'},
        ],
        'caption': 'Huyết tương chiếm hơn nửa thể tích máu. Trong phần tế bào, hồng cầu áp đảo (chở O₂); '
                   'bạch cầu và tiểu cầu chưa tới 1 % nhưng đảm nhiệm bảo vệ cơ thể và làm đông máu.',
    }),
    # Lịch sử thế giới thế kỉ XX.
    17: (1, {
        'type': 'timeline', 'badge': 'BỐN MỐC XUYÊN THẾ KỈ XX',
        'events': [
            {'when': '1917', 'label': 'Cách mạng tháng Mười Nga', 'color': 'violet',
             'note': 'Lê-nin lãnh đạo; nhà nước xã hội chủ nghĩa đầu tiên ra đời'},
            {'when': '1939', 'label': 'Chiến tranh thế giới thứ hai bùng nổ', 'color': 'amber',
             'note': 'phe Phát xít đối đầu phe Đồng minh'},
            {'when': '1945', 'label': 'Chiến tranh kết thúc', 'color': 'teal',
             'note': 'Đồng minh thắng; thế giới bắt đầu chia hai cực Mỹ – Liên Xô'},
            {'when': '1991', 'label': 'Liên Xô tan rã', 'color': 'slate',
             'note': 'Chiến tranh Lạnh chấm dứt; xu thế hoà bình, hợp tác, toàn cầu hoá'},
        ],
        'caption': 'Khoảng giữa 1945 và 1991 là Chiến tranh Lạnh: căng thẳng kéo dài gần nửa thế kỉ nhưng '
                   'hai siêu cường không trực tiếp đánh nhau.',
    }),
    # Năm chiến thắng chống ngoại xâm thời phong kiến.
    18: (2, {
        'type': 'timeline', 'badge': 'CHIẾN THẮNG CHỐNG NGOẠI XÂM THỜI PHONG KIẾN',
        'events': [
            {'when': '938', 'label': 'Bạch Đằng — Ngô Quyền', 'color': 'violet',
             'note': 'thắng quân Nam Hán, chấm dứt hơn nghìn năm Bắc thuộc'},
            {'when': '1077', 'label': 'Sông Như Nguyệt — Lý Thường Kiệt', 'color': 'teal',
             'note': 'chống Tống'},
            {'when': '1288', 'label': 'Bạch Đằng — Trần Hưng Đạo', 'color': 'amber',
             'note': 'lần thứ ba đánh bại Nguyên – Mông'},
            {'when': '1427', 'label': 'Chi Lăng – Xương Giang — Lê Lợi, Nguyễn Trãi', 'color': 'violet',
             'note': 'chống Minh'},
            {'when': '1789', 'label': 'Ngọc Hồi – Đống Đa — Quang Trung', 'color': 'teal',
             'note': 'đại phá quân Thanh'},
        ],
        'caption': 'Sông Bạch Đằng xuất hiện <b>hai lần</b> (938 và 1288) — đề hay hỏi "trận nào, thời nào". '
                   'Ghép nhân vật với triều đại và với kẻ xâm lược là cách nhớ chắc nhất.',
    }),
    # Tính thế kỉ.
    19: (2, {
        'type': 'table', 'badge': 'TÍNH THẾ KỈ TỪ NĂM',
        'head': ['Năm', 'Thế kỉ', 'Cách tính'],
        'rows': [
            ['1945', 'XX', '19 + 1'],
            ['2025', 'XXI', '20 + 1'],
            ['1000', 'X', 'năm tròn trăm: giữ nguyên 10'],
            ['179 TCN', 'II TCN', '1 + 1, đếm lùi về quá khứ'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Năm không tròn trăm: lấy hai chữ số đầu cộng 1. Năm 1000 còn thuộc thế kỉ X, năm 1001 mới sang '
                   'thế kỉ XI. Khoảng cách 1945 → 1975 là 30 năm; với mốc TCN thì trục thời gian đếm lùi.',
    }),
    # Địa hình: đồi núi 3/4, đồng bằng 1/4.
    20: (2, {
        'type': 'pie', 'unit': '% diện tích', 'badge': 'ĐỊA HÌNH VIỆT NAM',
        'slices': [
            {'label': 'Đồi núi (phần lớn là đồi núi thấp)', 'value': 75, 'color': 'teal'},
            {'label': 'Đồng bằng', 'value': 25, 'color': 'amber'},
        ],
        'caption': 'Ba phần tư lãnh thổ là đồi núi, nhưng đồng bằng — chỉ một phần tư — lại là nơi tập trung '
                   'dân cư và lúa gạo: đồng bằng sông Hồng và đồng bằng sông Cửu Long.',
    }),
    # Nông sản chủ lực và vùng chuyên canh.
    21: (1, {
        'type': 'table', 'badge': 'SẢN PHẨM — VÙNG — VỊ THẾ',
        'head': ['Sản phẩm', 'Vùng tiêu biểu', 'Vị thế'],
        'rows': [
            ['Lúa gạo', 'ĐB sông Cửu Long, ĐB sông Hồng', 'xuất khẩu hàng đầu thế giới'],
            ['Cà phê', 'Tây Nguyên', 'xuất khẩu hàng đầu thế giới'],
            ['Cao su', 'Đông Nam Bộ', 'cây công nghiệp lâu năm chủ lực'],
            ['Thủy sản', 'duyên hải, ĐB sông Cửu Long', 'xuất khẩu hàng đầu'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Đề hay hỏi ngược: "cà phê trồng nhiều nhất ở vùng nào?" — ghép sản phẩm với vùng là dạng '
                   'câu chắc điểm nếu đã có bảng này trong đầu.',
    }),
    # Khai thác Atlat: ví dụ giải thích cà phê ở Tây Nguyên.
    22: (3, {
        'type': 'flow', 'badge': 'VÍ DỤ: VÌ SAO TÂY NGUYÊN TRỒNG NHIỀU CÀ PHÊ?',
        'steps': [
            {'label': 'Đọc câu hỏi', 'note': 'hỏi gì, ở đâu', 'color': 'slate'},
            {'label': 'Tra mục lục', 'note': 'trang địa hình – đất, khí hậu, nông nghiệp', 'color': 'violet'},
            {'label': 'Đọc chú giải trước', 'note': 'ký hiệu cây công nghiệp, loại đất', 'color': 'violet'},
            {'label': 'Đối chiếu các trang', 'note': 'cao nguyên đất badan + khí hậu cận xích đạo', 'color': 'teal'},
            {'label': 'Trả lời', 'note': 'đủ hai vế: điều kiện tự nhiên → sản phẩm', 'color': 'amber'},
        ],
        'caption': 'Một câu Atlat gần như luôn cần <b>hai trang trở lên</b>. Đọc chú giải trước khi nhìn bản đồ — '
                   'đoán ký hiệu là cách nhanh nhất để sai.',
    }),
    # Phần Khoa học: chọn 3 trong 5.
    24: (0, {
        'type': 'tree', 'badge': 'CHỌN 3 TRONG 5 CHỦ ĐỀ',
        'root': {'label': 'Phần Khoa học', 'note': '50 câu · 60 phút · tự chọn 3 chủ đề'},
        'branches': [
            {'label': 'Khoa học tự nhiên', 'note': 'nặng tính toán', 'color': 'violet',
             'children': [{'label': 'Vật lý'}, {'label': 'Hoá học'}, {'label': 'Sinh học'}]},
            {'label': 'Khoa học xã hội', 'note': 'nặng ghi nhớ và đọc bản đồ', 'color': 'teal',
             'children': [{'label': 'Lịch sử'}, {'label': 'Địa lý'}]},
        ],
        'caption': 'Chọn theo môn mình <b>vững và làm nhanh</b> nhất; định hướng ngành là tiêu chí phụ. '
                   'Chốt tổ hợp sớm để dồn sức ôn ba môn thay vì dàn trải cả năm.',
    }),
    # Trọng tâm từng môn.
    25: (0, {
        'type': 'table', 'badge': 'MỖI MÔN MỘT CÁCH HỌC',
        'head': ['Môn', 'Trọng tâm', 'Cách luyện'],
        'rows': [
            ['Vật lý', 'công thức lõi, bản chất hiện tượng', 'bài tính; soát đơn vị'],
            ['Hoá học', 'tính chất chất, phương trình, mol', 'nhận biết; tính theo phương trình'],
            ['Sinh học', 'khái niệm và quá trình', 'sơ đồ tư duy, liên hệ thực tế'],
            ['Lịch sử', 'mốc – sự kiện – nhân vật', 'trục thời gian'],
            ['Địa lý', 'đặc điểm vùng, số liệu chính', 'đọc bản đồ, biểu đồ, Atlat'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Lý và Hoá ăn điểm nhờ <b>tính đúng</b>, Sinh và Sử nhờ <b>nhớ có hệ thống</b>, Địa nhờ '
                   '<b>đọc hình</b>. Học môn nào theo cách của môn ấy.',
    }),
    # Phân tích sau một đề tổ hợp (ví dụ).
    26: (2, {
        'type': 'bars', 'badge': 'SAU MỘT ĐỀ TỔ HỢP (ví dụ)', 'max': 17,
        'bars': [
            {'label': 'Vật lý', 'value': 13, 'display': '13/17', 'color': 'violet'},
            {'label': 'Hoá học', 'value': 11, 'display': '11/17', 'color': 'teal'},
            {'label': 'Sinh học', 'value': 8, 'display': '8/16', 'note': 'củng cố trước', 'color': 'amber'},
        ],
        'caption': 'Chấm theo <b>từng chủ đề</b>, không chỉ tổng điểm: ở đây Sinh học kéo cả phần xuống → tuần tới '
                   'dồn ôn Sinh, và ghi lại dạng câu hay sai (ví dụ: di truyền).',
    }),
}
