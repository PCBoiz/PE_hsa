"""Minh hoạ cho các bài Tư duy Định tính chưa có (16/09/2026) — xem `__init__.py`."""

MINH_HOA = {
    # Từ nhiều nghĩa: "mắt".
    2: (0, {
        'type': 'tree', 'badge': 'MỘT TỪ, NHIỀU NGHĨA',
        'root': {'label': '“mắt”', 'note': 'nghĩa gốc sinh ra nghĩa chuyển'},
        'branches': [
            {'label': 'Nghĩa gốc', 'note': 'cụ thể, có trước', 'color': 'violet',
             'children': [{'label': 'mắt người', 'note': 'cơ quan để nhìn'}]},
            {'label': 'Nghĩa chuyển', 'note': 'giống về hình dáng hoặc vị trí', 'color': 'teal',
             'children': [{'label': 'mắt lưới', 'note': 'lỗ nhỏ, tròn như mắt'},
                          {'label': 'mắt na', 'note': 'chấm lồi trên vỏ quả'},
                          {'label': 'mắt bão', 'note': 'tâm bão, vùng lặng ở giữa'}]},
        ],
        'caption': 'Nghĩa chuyển ở đây đều dựa trên nét <b>giống nhau</b> với con mắt (ẩn dụ). Gặp từ quen ở chỗ lạ, '
                   'hỏi: nó đang chỉ đối tượng nào trong câu này?',
    }),
    # Thành ngữ ↔ tục ngữ.
    4: (2, {
        'type': 'table', 'badge': 'PHÂN BIỆT BẰNG CÁCH GHÉP VÀO CÂU',
        'head': ['', 'Thành ngữ', 'Tục ngữ'],
        'rows': [
            ['Hình thức', 'cụm từ cố định, chưa thành câu', 'câu trọn vẹn, thường có vần'],
            ['Vai trò', 'làm một thành phần của câu', 'đứng riêng như một lời khuyên'],
            ['Ví dụ', 'nước đổ lá khoai · mèo mù vớ cá rán', 'Tốt gỗ hơn tốt nước sơn.'],
            ['Thử', '“Nói với nó như nước đổ lá khoai.” — phải ghép vào câu', '“Tốt gỗ hơn tốt nước sơn.” — tự đứng được'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Mẹo nhanh: đặt dấu chấm ngay sau cụm từ. Đọc lên thấy <b>trọn ý</b> là tục ngữ; thấy hụt, '
                   'còn chờ phần tiếp là thành ngữ.',
    }),
    # Phân tích một câu.
    5: (0, {
        'type': 'flow', 'badge': 'TÁCH MỘT CÂU: “Sáng nay, học sinh lớp 12 chăm chỉ ôn bài ở thư viện.”',
        'steps': [
            {'label': 'Sáng nay', 'note': 'trạng ngữ — khi nào?', 'color': 'slate'},
            {'label': 'học sinh lớp 12', 'note': 'chủ ngữ — ai?', 'color': 'violet'},
            {'label': 'chăm chỉ ôn bài', 'note': 'vị ngữ — làm gì?', 'color': 'teal'},
            {'label': 'ở thư viện', 'note': 'trạng ngữ — ở đâu?', 'color': 'slate'},
        ],
        'caption': 'Hỏi “ai?” để tìm chủ ngữ, “làm gì / thế nào?” để tìm vị ngữ; phần trả lời “khi nào, ở đâu, '
                   'vì sao” là trạng ngữ — bỏ đi câu vẫn đứng được. “chăm chỉ” bổ nghĩa cho “ôn”, “bài” là bổ ngữ.',
    }),
    # Ba phép liên kết.
    6: (3, {
        'type': 'table', 'badge': 'BA PHÉP LIÊN KẾT CÂU',
        'head': ['Phép', 'Cách làm', 'Ví dụ'],
        'rows': [
            ['Lặp', 'lặp lại từ ngữ', 'Mưa rơi. MƯA xoá mờ con đường.'],
            ['Thế', 'thay bằng đại từ', 'Lan đến muộn. CÔ ẤY xin lỗi cả lớp.'],
            ['Nối', 'dùng quan hệ từ', 'Trời mưa to. TUY NHIÊN, trận đấu vẫn diễn ra.'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Đề hay hỏi “câu (2) liên kết với câu (1) bằng phép gì?”: tìm từ được lặp, đại từ thay thế, '
                   'hay quan hệ từ đứng đầu câu — đúng ba chỗ để nhìn.',
    }),
    # Bốn lỗi diễn đạt, có sửa.
    7: (0, {
        'type': 'table', 'badge': 'SAI — VÀ SỬA',
        'head': ['Lỗi', 'Câu sai', 'Câu đã sửa'],
        'rows': [
            ['Dùng từ sai nghĩa', 'Yếu điểm của em là môn toán.', 'Điểm yếu của em là môn toán.'],
            ['Thừa từ', 'Bạn ấy rất chăm chỉ và siêng năng.', 'Bạn ấy rất chăm chỉ.'],
            ['Thiếu chủ ngữ', 'Qua tác phẩm cho thấy số phận người nông dân.', 'Tác phẩm cho thấy số phận người nông dân.'],
            ['Sai quan hệ từ', 'Vì trời mưa nên em vẫn đi học.', 'Tuy trời mưa nhưng em vẫn đi học.'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': '“Yếu điểm” là <b>điểm quan trọng</b> (Hán Việt: yếu = trọng yếu) — đối lập hẳn với “điểm yếu”. '
                   'Câu mở đầu bằng “Qua…, Với…” mà không có ai làm chủ là câu thiếu chủ ngữ.',
    }),
    # Chủ động ↔ bị động.
    8: (0, {
        'type': 'table', 'badge': 'CÙNG MỘT VIỆC, HAI CÁCH NÓI',
        'head': ['Kiểu câu', 'Ví dụ', 'Nhấn mạnh'],
        'rows': [
            ['Chủ động', 'Thầy giáo khen Lan.', 'chủ thể — thầy giáo'],
            ['Bị động', 'Lan được thầy giáo khen.', 'đối tượng — Lan'],
            ['Bị động', 'Cây bị gió quật đổ.', '“bị” cho việc không mong muốn, “được” cho việc mong muốn'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Chuyển câu không đổi sự việc, chỉ đổi thứ đứng đầu câu — tức đổi thứ người đọc chú ý trước. '
                   'Chọn “bị” hay “được” theo sắc thái, không theo ngữ pháp.',
    }),
    # Diễn dịch ↔ quy nạp.
    9: (1, {
        'type': 'tree', 'badge': 'CÂU CHỦ ĐỀ NẰM Ở ĐÂU',
        'root': {'label': 'Đoạn văn', 'note': 'ý chính nằm trong câu chủ đề'},
        'branches': [
            {'label': 'Diễn dịch', 'note': 'chủ đề đứng ĐẦU', 'color': 'violet',
             'children': [{'label': 'Câu 1: nêu ý chính'}, {'label': 'Câu 2, 3, …: lí lẽ, dẫn chứng'}]},
            {'label': 'Quy nạp', 'note': 'chủ đề đứng CUỐI', 'color': 'teal',
             'children': [{'label': 'Câu 1, 2, …: dẫn dắt, dẫn chứng'}, {'label': 'Câu cuối: khái quát thành ý chính'}]},
        ],
        'caption': 'Tìm ý chính thì đọc câu <b>đầu</b> và câu <b>cuối</b> đoạn trước; không thấy câu nào khái quát '
                   'thì tự gom nội dung chung của các câu — và bỏ qua chi tiết, số liệu.',
    }),
    # Tường minh ↔ hàm ý.
    10: (0, {
        'type': 'table', 'badge': 'CÙNG CÂU NÓI, HAI TẦNG NGHĨA',
        'head': ['Câu nói', 'Nghĩa tường minh', 'Hàm ý (trong ngữ cảnh)'],
        'rows': [
            ['Trời nóng quá!', 'nhiệt độ cao', 'bật quạt giúp mình'],
            ['Mấy giờ rồi nhỉ?', 'hỏi giờ', 'muộn rồi, ta về thôi'],
            ['Cửa mở kìa.', 'cửa đang mở', 'đóng cửa lại giúp'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Hàm ý chỉ có <b>căn cứ</b> khi có ngữ cảnh: “Trời nóng quá!” nói với bạn cùng phòng là lời nhờ, '
                   'nói một mình chỉ là than. Đề chấm theo hàm ý hợp lí NHẤT với ngữ cảnh đã cho, không theo suy diễn.',
    }),
    # Dấu hiệu thái độ – giọng điệu.
    11: (2, {
        'type': 'table', 'badge': 'NHÌN VÀO ĐÂU ĐỂ THẤY THÁI ĐỘ',
        'head': ['Dấu hiệu', 'Ví dụ', 'Cho biết'],
        'rows': [
            ['Từ ngữ đánh giá', '“kiệt tác” / “tầm thường”', 'ngợi ca / chê bai'],
            ['Hình ảnh', '“ánh mắt lấp lánh” / “khuôn mặt cau có”', 'yêu mến / khó chịu'],
            ['Kiểu câu', 'câu cảm thán, câu hỏi tu từ', 'xúc động, trăn trở'],
            ['Biện pháp tu từ', 'nói quá, nói ngược', 'mỉa mai, châm biếm'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Gạch chân những từ <b>bộc lộ cảm xúc</b> khi đọc, rồi hỏi: tác giả yêu hay ghét, đồng tình hay '
                   'phê phán điều gì? Giọng điệu là tổng của các dấu hiệu ấy, không phải một từ đơn lẻ.',
    }),
    # Nghị luận ↔ thông tin.
    12: (2, {
        'type': 'table', 'badge': 'HỎI: VĂN BẢN NÀY MUỐN GÌ Ở NGƯỜI ĐỌC?',
        'head': ['', 'Văn bản nghị luận', 'Văn bản thông tin'],
        'rows': [
            ['Mục đích', 'thuyết phục', 'thông báo'],
            ['Quan điểm cá nhân', 'có — luận điểm rõ', 'không — khách quan'],
            ['Cấu trúc', 'luận điểm → luận cứ → lập luận', 'sự việc → số liệu → giải thích'],
            ['Ví dụ', 'bài bàn về việc học trực tuyến', 'bản tin thời tiết, hướng dẫn sử dụng'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Cùng một chủ đề có thể viết theo cả hai kiểu: bản tin “số học sinh học trực tuyến tăng 30 %” là '
                   'thông tin; “học trực tuyến nên là lựa chọn bắt buộc” là nghị luận.',
    }),
    # Trục thời gian văn học.
    13: (0, {
        'type': 'timeline', 'badge': 'TÁC GIẢ – TÁC PHẨM THEO THỜI GIAN',
        'events': [
            {'when': '1428', 'label': 'Bình Ngô đại cáo — Nguyễn Trãi', 'color': 'slate',
             'note': 'văn học trung đại; cùng thời kì: Truyện Kiều (Nguyễn Du, đầu thế kỉ XIX)'},
            {'when': '1932–1945', 'label': 'Phong trào Thơ mới', 'color': 'violet',
             'note': 'Xuân Diệu, Huy Cận, Hàn Mặc Tử, Chế Lan Viên'},
            {'when': '1936–1941', 'label': 'Văn học hiện thực', 'color': 'amber',
             'note': 'Số đỏ (1936), Tắt đèn (1937), Chí Phèo (1941)'},
            {'when': '1942–1943', 'label': 'Nhật ký trong tù — Hồ Chí Minh', 'color': 'teal',
             'note': 'thơ ca cách mạng'},
            {'when': '1954', 'label': 'Việt Bắc — Tố Hữu', 'color': 'teal',
             'note': 'thơ ca cách mạng thời kháng chiến chống Pháp'},
        ],
        'caption': 'Thơ mới và văn học hiện thực là <b>hai dòng chảy song song</b> trong cùng thập niên 1930: một bên '
                   'cái tôi lãng mạn, một bên số phận người nghèo. Đề hay hỏi “tác giả nào cùng thời với…”.',
    }),
    # Các thể thơ.
    14: (3, {
        'type': 'table', 'badge': 'NHẬN THỂ THƠ QUA SỐ CHỮ',
        'head': ['Thể thơ', 'Số chữ mỗi câu', 'Dấu hiệu'],
        'rows': [
            ['Lục bát', '6 – 8 luân phiên', 'chữ 6 câu lục vần với chữ 6 câu bát'],
            ['Song thất lục bát', '7 – 7 – 6 – 8', 'hai câu bảy rồi một cặp lục bát'],
            ['Thất ngôn bát cú', '8 câu × 7 chữ', 'Đường luật, niêm luật chặt'],
            ['Ngũ ngôn', '5 chữ', 'thường bốn câu hoặc tám câu'],
            ['Thơ tự do', 'không cố định', 'không bắt buộc vần, nhịp'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Đếm chữ của hai câu đầu là đủ nhận ra bốn thể đầu. Truyện Kiều là lục bát — tự sự bằng thơ, '
                   'nên vừa là truyện thơ, vừa là ví dụ điển hình của thể lục bát.',
    }),
    # Biện pháp tu từ.
    15: (0, {
        'type': 'table', 'badge': 'NĂM BIỆN PHÁP HAY GẶP',
        'head': ['Biện pháp', 'Ví dụ', 'Nhận ra bằng'],
        'rows': [
            ['So sánh', 'Trẻ em NHƯ búp trên cành', 'có từ so sánh: như, là, tựa'],
            ['Ẩn dụ', 'Thuyền về có nhớ bến chăng', 'so sánh ngầm, không có từ so sánh'],
            ['Nhân hoá', 'Ông trăng tròn; cây đa đứng gác', 'vật mang hành động, tình cảm người'],
            ['Hoán dụ', 'Áo nâu liền với áo xanh', 'gọi bằng cái gần gũi, liên quan'],
            ['Điệp ngữ', 'Ta đi ta nhớ…', 'lặp từ ngữ để nhấn mạnh'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Ẩn dụ và hoán dụ đều là “gọi A bằng B”: B <b>giống</b> A là ẩn dụ (thuyền – người đi), '
                   'B <b>đi kèm</b> A là hoán dụ (áo nâu – người nông dân mặc nó).',
    }),
    # Giá trị nội dung – nghệ thuật.
    16: (0, {
        'type': 'tree', 'badge': 'HAI TRỤC GIÁ TRỊ',
        'root': {'label': 'Giá trị của tác phẩm', 'note': 'nói gì — và nói hay ở chỗ nào'},
        'branches': [
            {'label': 'Nội dung', 'note': 'tác phẩm nói gì', 'color': 'violet',
             'children': [{'label': 'Hiện thực', 'note': 'phản ánh đời sống đương thời'},
                          {'label': 'Nhân đạo', 'note': 'thương người, lên án bất công'},
                          {'label': 'Tư tưởng', 'note': 'thông điệp gửi gắm'}]},
            {'label': 'Nghệ thuật', 'note': 'nói hay ở chỗ nào', 'color': 'teal',
             'children': [{'label': 'Ngôn ngữ', 'note': 'giàu hình ảnh'},
                          {'label': 'Kết cấu, nhân vật', 'note': 'chặt chẽ, sinh động'},
                          {'label': 'Tu từ, giọng điệu', 'note': 'đặc sắc'}]},
        ],
        'caption': '“Tắt đèn”: giá trị hiện thực là nỗi khổ sưu thuế của nông dân; giá trị nhân đạo là niềm thương '
                   'chị Dậu và sự phẫn nộ với bất công; nghệ thuật là nhân vật điển hình và ngôn ngữ nông thôn sống động.',
    }),
    # Từ theo nguồn gốc.
    17: (0, {
        'type': 'tree', 'badge': 'TỪ TIẾNG VIỆT THEO NGUỒN GỐC',
        'root': {'label': 'Từ tiếng Việt', 'note': 'có sẵn hay vay mượn?'},
        'branches': [
            {'label': 'Thuần Việt', 'note': 'có sẵn từ xưa', 'color': 'violet',
             'children': [{'label': 'nhà, nước, ăn, mẹ'}]},
            {'label': 'Từ mượn', 'note': 'vay từ ngôn ngữ khác', 'color': 'teal',
             'children': [{'label': 'Hán Việt', 'note': 'quốc gia, độc lập — chiếm phần lớn'},
                          {'label': 'Pháp', 'note': 'ga, pê-đan, xà phòng'},
                          {'label': 'Anh', 'note': 'ti vi, internet'}]},
        ],
        'caption': 'Từ Hán Việt thường trang trọng hơn từ thuần Việt cùng nghĩa (phụ nữ – đàn bà, tổ quốc – đất nước). '
                   'Dùng từ mượn đúng chỗ là giữ sự trong sáng, không phải tránh hẳn.',
    }),
    # Sáu phong cách.
    18: (0, {
        'type': 'table', 'badge': 'SÁU PHONG CÁCH — NHẬN QUA NƠI GẶP',
        'head': ['Phong cách', 'Gặp ở', 'Nhận diện'],
        'rows': [
            ['Sinh hoạt', 'trò chuyện, nhật ký, thư', 'tự nhiên, có tiếng lóng, từ địa phương'],
            ['Nghệ thuật', 'thơ, truyện', 'hình tượng, biểu cảm, tu từ'],
            ['Báo chí', 'bản tin, phóng sự', 'thời sự, ngắn gọn, khách quan'],
            ['Chính luận', 'xã luận, tuyên ngôn', 'lập luận chặt, thuyết phục'],
            ['Khoa học', 'sách giáo khoa, luận văn', 'thuật ngữ, chính xác, logic'],
            ['Hành chính', 'đơn từ, nghị định, hợp đồng', 'khuôn mẫu, trang trọng'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Đề cho một đoạn và hỏi phong cách: nhìn <b>nơi nó thường xuất hiện</b> và <b>mục đích</b> trước, '
                   'từ ngữ chỉ là dấu hiệu phụ.',
    }),
    # Đọc văn bản có bối cảnh.
    19: (3, {
        'type': 'flow', 'badge': 'VÍ DỤ: “Mùng ba tết thầy”',
        'steps': [
            {'label': 'Gặp chi tiết văn hoá', 'note': 'ngày tết, chữ “thầy”', 'color': 'slate'},
            {'label': 'Hỏi: bối cảnh gì?', 'note': 'phong tục ngày Tết', 'color': 'violet'},
            {'label': 'Kết nối kiến thức nền', 'note': 'mùng một tết cha, mùng hai tết mẹ, mùng ba tết thầy', 'color': 'teal'},
            {'label': 'Suy ra thông điệp', 'note': 'tôn sư trọng đạo', 'color': 'amber'},
        ],
        'caption': 'Thiếu kiến thức nền thì câu ấy chỉ là một lịch trình. Địa danh, mốc lịch sử, phong tục trong '
                   'văn bản đều là <b>chìa khoá</b> mở thông điệp — đọc rộng là để có sẵn chìa.',
    }),
    # Lướt → quét → đọc kỹ.
    20: (2, {
        'type': 'flow', 'badge': 'MỘT CÂU ĐỌC HIỂU, NĂM BƯỚC',
        'steps': [
            {'label': 'Lướt cả bài', 'note': 'tiêu đề, câu đầu và cuối mỗi đoạn', 'color': 'slate'},
            {'label': 'Đọc câu hỏi', 'note': 'gạch từ khoá', 'color': 'violet'},
            {'label': 'Quét tìm từ khoá', 'note': 'chỉ dừng ở đoạn có nó', 'color': 'violet'},
            {'label': 'Đọc kỹ đoạn ấy', 'note': 'không đọc kỹ cả bài', 'color': 'teal'},
            {'label': 'Chọn đáp án có căn cứ', 'note': 'bám từ ngữ của văn bản', 'color': 'amber'},
        ],
        'caption': 'Đọc kỹ toàn bài cho mọi câu hỏi là cách chắc chắn nhất để hết giờ. Lướt để biết bài nói gì, '
                   'quét để biết câu này nằm ở đâu, và chỉ đọc kỹ đúng chỗ ấy.',
    }),
    # Phân bổ 60 phút (ví dụ).
    21: (0, {
        'type': 'pie', 'unit': 'phút', 'badge': '60 PHÚT — MỘT CÁCH CHIA (ví dụ)',
        'slices': [
            {'label': 'Câu từ vựng, ngữ pháp — làm nhanh', 'value': 15, 'color': 'violet'},
            {'label': 'Đọc hiểu đoạn dài', 'value': 35, 'color': 'teal'},
            {'label': 'Quay lại câu đã đánh dấu', 'value': 6, 'color': 'amber'},
            {'label': 'Rà soát cuối giờ', 'value': 4, 'color': 'slate'},
        ],
        'caption': 'Câu từ vựng, ngữ pháp dưới một phút mỗi câu để dành thời gian cho đoạn dài; nhưng đoạn dài cũng '
                   'có trần — quá trần thì đánh dấu, đi tiếp, quay lại sau.',
    }),
    # Bốn kiểu đáp án sai.
    22: (0, {
        'type': 'table', 'badge': 'BỐN KIỂU ĐÁP ÁN SAI',
        'head': ['Kiểu sai', 'Dấu hiệu', 'Cách bắt'],
        'rows': [
            ['Không có trong bài', 'chi tiết lạ, nghe hợp lí', 'tìm căn cứ — không thấy thì loại'],
            ['Suy diễn quá mức', 'luôn luôn, tất cả, duy nhất', 'văn bản có nói tới mức ấy không?'],
            ['Trái nội dung', 'đảo ngược ý gốc', 'đối chiếu từng vế với bài'],
            ['Đúng một nửa', 'vế đầu đúng, vế sau sai', 'đọc HẾT đáp án, đừng dừng ở nửa đúng'],
        ],
        'align': ['left', 'left', 'left'],
        'caption': 'Kiểu thứ tư là bẫy tinh vi nhất: nửa đầu đúng làm người đọc gật ngay. Câu đọc hiểu chấm theo '
                   '<b>văn bản</b>, không theo hiểu biết ngoài — đáp án “đúng ngoài đời” vẫn sai nếu bài không nói.',
    }),
    # Chữa đề: phân loại câu sai.
    23: (1, {
        'type': 'tree', 'badge': 'MỖI CÂU SAI MỘT NGUYÊN NHÂN, MỘT CÁCH CHỮA',
        'root': {'label': 'Một câu làm sai', 'note': 'hỏi: sai vì gì?'},
        'branches': [
            {'label': 'Không hiểu từ', 'note': 'từ mới, thành ngữ lạ', 'color': 'violet',
             'children': [{'label': 'Ghi sổ từ mới', 'note': 'kèm câu ví dụ'}]},
            {'label': 'Hiểu sai ý', 'note': 'đọc lệch đoạn', 'color': 'teal',
             'children': [{'label': 'Đọc lại đoạn', 'note': 'tìm câu chủ đề, đối chiếu đáp án'}]},
            {'label': 'Vội', 'note': 'chưa đọc hết đáp án', 'color': 'amber',
             'children': [{'label': 'Luyện bấm giờ', 'note': 'đọc câu hỏi trước, đọc hết bốn đáp án'}]},
        ],
        'caption': 'Chữa đề không phải là xem đáp án đúng, mà là <b>gọi tên</b> lí do sai. Ba lí do trên cần ba bài '
                   'tập khác nhau — gộp chung lại là luyện mãi không lên.',
    }),
}
