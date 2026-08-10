/* ============================================================================
 * LESSON_CONTENT_HSA — nội dung bài học HSA (luồng ĐẢO NGƯỢC theo cô Hương):
 *   Bước 1 KIỂM TRA đầu vào → Bước 2 ĐÁNH GIÁ năng lực → Bước 3 LÝ THUYẾT
 *   (thích ứng: vững → tóm tắt gọn; yếu → đầy đủ + ví dụ) → Bước 4 GHI CHÚ.
 *
 * Schema mỗi lesson:
 *   test:   { intro, questions: [{id, type('mcq'|'fill'), question, options?, answer, explain?}] }
 *   assess: { strong_min, ok_min }              // ngưỡng số câu đúng
 *   theory: { condensed: {title, cards:[{icon,title,body}]},
 *             full:      {title, cards:[...], examples:[{q, sol}]} }
 *   notes:  { key_points:[...], formula?, tip? }
 * Nội dung mỏng (1 bài mẫu/phần) — TopHSA cấp nội dung đầy đủ sau.
 * ============================================================================ */
window.LESSON_CONTENT_HSA = window.LESSON_CONTENT_HSA || {};

window.LESSON_CONTENT_HSA['hsa_quantitative'] = {
  course_id: 'hsa_quantitative',
  course_title: 'Tư duy Định lượng',
  accent_color: '#8B7CF6',
  lessons: [
    {
      id: 'ql_01',
      index: 1,
      title: 'Bài toán phần trăm',
      subtitle: 'Tăng – giảm phần trăm và bài toán thực tế',
      topic_tag: 'Định lượng · Số học',
      xp_reward: 50,

      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn ở chủ đề này. ' +
               'Kết quả sẽ quyết định phần lý thuyết bạn được xem là bản gọn hay bản đầy đủ.',
        questions: [
          {
            id: 't1', type: 'mcq',
            question: 'Một chiếc áo giá 400.000đ được giảm 25%. Giá sau khi giảm là bao nhiêu?',
            options: ['375.000đ', '350.000đ', '320.000đ', '300.000đ'],
            answer: '300.000đ',
            explain: '400.000 × (1 − 0,25) = 400.000 × 0,75 = 300.000đ.'
          },
          {
            id: 't2', type: 'fill',
            question: 'Một số tăng 20% rồi lại giảm 20%. Số mới bằng bao nhiêu phần trăm số ban đầu? (nhập số)',
            answer: '96',
            explain: '(1 + 0,2) × (1 − 0,2) = 1,2 × 0,8 = 0,96 = 96%. Tăng rồi giảm cùng % luôn < 100%.'
          },
          {
            id: 't3', type: 'mcq',
            question: 'Số học sinh giỏi của lớp tăng từ 20 lên 25 bạn. Tỉ lệ tăng là bao nhiêu?',
            options: ['5%', '20%', '25%', '125%'],
            answer: '25%',
            explain: '(25 − 20) / 20 = 5/20 = 0,25 = 25%. % thay đổi tính trên giá trị GỐC.'
          }
        ]
      },

      assess: { strong_min: 3, ok_min: 2 },

      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững, chỉ cần chốt lại',
          cards: [
            {
              icon: 'fa-percent',
              title: 'Ba công thức lõi',
              body: 'Giảm p%: <code>× (1 − p/100)</code> · Tăng p%: <code>× (1 + p/100)</code> · ' +
                    '% thay đổi: <code>(mới − gốc)/gốc × 100</code>. Luôn tính % trên <strong>giá trị gốc</strong>.'
            },
            {
              icon: 'fa-triangle-exclamation',
              title: 'Bẫy hay gặp',
              body: 'Tăng rồi giảm cùng % <strong>KHÔNG</strong> về lại số cũ (VD ±20% → còn 96%). ' +
                    'Đừng cộng/trừ % trực tiếp qua nhiều bước — phải nhân các hệ số.'
            }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ chủ đề này',
          cards: [
            {
              icon: 'fa-percent',
              title: 'Phần trăm là gì?',
              body: 'p% = p/100. Muốn lấy p% của một số, ta nhân số đó với p/100. ' +
                    'VD 25% của 400.000 = 400.000 × 25/100 = 100.000.'
            },
            {
              icon: 'fa-arrow-down',
              title: 'Giảm giá / giảm p%',
              body: 'Giá sau giảm = giá gốc × (1 − p/100). VD giảm 25%: × 0,75. ' +
                    'Tương tự tăng p%: × (1 + p/100).'
            },
            {
              icon: 'fa-arrows-up-down',
              title: '% thay đổi (tăng/giảm bao nhiêu %)',
              body: '% thay đổi = (giá trị mới − giá trị gốc) / <strong>giá trị gốc</strong> × 100. ' +
                    'Sai lầm phổ biến: chia cho giá trị mới.'
            },
            {
              icon: 'fa-triangle-exclamation',
              title: 'Bẫy "tăng rồi giảm"',
              body: 'Tăng p% rồi giảm p% ra kết quả nhỏ hơn ban đầu vì phần giảm tính trên số ĐÃ tăng. ' +
                    'Luôn nhân các hệ số: (1+p)(1−p) = 1 − p².'
            }
          ],
          examples: [
            {
              q: 'Áo 400k giảm 25% rồi giảm thêm 10%. Giá cuối?',
              sol: '400.000 × 0,75 × 0,90 = 270.000đ (không phải giảm thẳng 35%).'
            },
            {
              q: 'Lương tăng từ 8 triệu lên 10 triệu, tăng mấy %?',
              sol: '(10 − 8)/8 × 100 = 25%.'
            }
          ]
        }
      },

      notes: {
        key_points: [
          'Giảm p%: nhân (1 − p/100). Tăng p%: nhân (1 + p/100).',
          '% thay đổi = (mới − gốc)/GỐC × 100 — luôn chia cho giá trị gốc.',
          'Nhiều bước tăng/giảm: NHÂN các hệ số, đừng cộng/trừ % trực tiếp.',
          'Tăng rồi giảm cùng % → luôn nhỏ hơn số ban đầu (1 − p²).'
        ],
        formula: 'Kết quả = Gốc × (1 ± p₁/100) × (1 ± p₂/100) × …',
        tip: 'Trong phòng thi HSA: đổi % sang hệ số thập phân (25% → 0,75 / 1,25) rồi bấm máy 1 lần — nhanh và tránh sai dấu.'
      },

      drill: {
        time_seconds: 75,
        questions: [
          { id: 'd1', type: 'mcq', question: '20% của 150 là bao nhiêu?', options: ['25', '30', '35', '40'], answer: '30' },
          { id: 'd2', type: 'mcq', question: 'Giảm 10% của 200.000đ còn bao nhiêu?', options: ['160.000đ', '170.000đ', '180.000đ', '190.000đ'], answer: '180.000đ' },
          { id: 'd3', type: 'fill', question: 'Tăng 50% của 40 bằng bao nhiêu? (nhập số)', answer: '60' },
          { id: 'd4', type: 'mcq', question: '8 chiếm bao nhiêu % của 40?', options: ['15%', '20%', '25%', '32%'], answer: '20%' },
          { id: 'd5', type: 'mcq', question: 'Tăng 25% rồi giảm 20% thì còn bao nhiêu % số ban đầu?', options: ['90%', '95%', '100%', '105%'], answer: '100%' },
          { id: 'd6', type: 'fill', question: 'Giá 500 (nghìn) giảm 30% còn bao nhiêu nghìn? (nhập số)', answer: '350' },
          { id: 'd7', type: 'mcq', question: 'Số học sinh tăng từ 50 lên 60, tăng bao nhiêu %?', options: ['10%', '16%', '20%', '120%'], answer: '20%' },
          { id: 'd8', type: 'fill', question: '10% của 10% của 1000 bằng bao nhiêu? (nhập số)', answer: '10' }
        ]
      }
    }
  ]
};

window.LESSON_CONTENT_HSA['hsa_verbal'] = {
  course_id: 'hsa_verbal',
  course_title: 'Tư duy Định tính',
  accent_color: '#F472B6',
  lessons: [
    {
      id: 'vb_01',
      index: 1,
      title: 'Từ đồng nghĩa & trái nghĩa',
      subtitle: 'Sắc thái nghĩa và cách chọn từ chính xác',
      topic_tag: 'Định tính · Từ vựng',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> từ vựng của bạn ở chủ đề này.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Từ nào ĐỒNG NGHĨA với “chăm chỉ”?',
            options: ['lười biếng', 'siêng năng', 'thông minh', 'hiền lành'], answer: 'siêng năng',
            explain: '“Siêng năng” cùng nghĩa với “chăm chỉ” (cần cù, chịu khó).' },
          { id: 't2', type: 'mcq', question: 'Từ nào TRÁI NGHĨA với “rộng lượng”?',
            options: ['hào phóng', 'độ lượng', 'ích kỷ', 'khoan dung'], answer: 'ích kỷ',
            explain: '“Ích kỷ” (chỉ nghĩ cho mình) trái nghĩa “rộng lượng”. Các từ kia đều gần nghĩa nhau.' },
          { id: 't3', type: 'fill', question: 'Điền từ TRÁI NGHĨA với “thành công” (1 từ):',
            answer: 'thất bại', explain: '“Thất bại” là phản nghĩa của “thành công”.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-equals', title: 'Đồng nghĩa – Trái nghĩa',
              body: 'Từ <b>đồng nghĩa</b> có nghĩa giống/gần nhau; từ <b>trái nghĩa</b> có nghĩa đối lập. Chú ý sắc thái: “chết” – “hi sinh” – “qua đời” cùng nghĩa nhưng khác sắc thái.' },
            { icon: 'fa-magnifying-glass', title: 'Mẹo loại trừ',
              body: 'Trong câu tìm từ “khác loại”, hãy tìm nhóm 3 từ gần nghĩa nhau — từ còn lại là đáp án.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ',
          cards: [
            { icon: 'fa-equals', title: 'Từ đồng nghĩa',
              body: 'Là các từ có nghĩa giống hoặc gần giống nhau (VD: to – lớn, chăm chỉ – siêng năng). Có thể thay cho nhau trong nhiều ngữ cảnh.' },
            { icon: 'fa-not-equal', title: 'Từ trái nghĩa',
              body: 'Là các từ có nghĩa đối lập (VD: cao – thấp, thành công – thất bại). Dùng để nhấn mạnh sự tương phản.' },
            { icon: 'fa-palette', title: 'Sắc thái nghĩa',
              body: 'Nhiều từ đồng nghĩa nhưng khác sắc thái biểu cảm: “chết” (trung tính) – “hi sinh” (trang trọng) – “toi” (suồng sã). Chọn từ hợp ngữ cảnh.' },
            { icon: 'fa-magnifying-glass', title: 'Chiến thuật làm bài',
              body: 'Câu “tìm từ khác loại”: gom nhóm từ gần nghĩa; từ lẻ loi là đáp án. Câu điền từ: đọc cả câu để đoán sắc thái phù hợp.' }
          ],
          examples: [
            { q: 'Từ khác loại: Bàn / Ghế / Tủ / Chạy?', sol: '“Chạy” (động từ) — ba từ kia là đồ vật.' },
            { q: 'Trái nghĩa “siêng năng”?', sol: '“Lười biếng”.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Đồng nghĩa = nghĩa giống/gần; trái nghĩa = nghĩa đối lập.',
          'Từ đồng nghĩa vẫn có thể khác SẮC THÁI — chọn theo ngữ cảnh.',
          'Câu “khác loại”: tìm nhóm 3 từ gần nghĩa, từ còn lại là đáp án.'
        ],
        tip: 'Khi phân vân, thử THAY từ vào câu — từ nào đọc lên tự nhiên và đúng sắc thái là đáp án.'
      },
      drill: {
        time_seconds: 70,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Đồng nghĩa với “to lớn”?', options: ['nhỏ bé', 'khổng lồ', 'xinh xắn', 'gầy gò'], answer: 'khổng lồ' },
          { id: 'd2', type: 'mcq', question: 'Trái nghĩa với “vui vẻ”?', options: ['hạnh phúc', 'buồn bã', 'phấn khởi', 'hân hoan'], answer: 'buồn bã' },
          { id: 'd3', type: 'fill', question: 'Trái nghĩa với “nhanh” (1 từ):', answer: 'chậm' },
          { id: 'd4', type: 'mcq', question: 'Từ nào KHÁC loại?', options: ['đỏ', 'xanh', 'vàng', 'ngọt'], answer: 'ngọt' },
          { id: 'd5', type: 'mcq', question: 'Đồng nghĩa với “dũng cảm”?', options: ['nhút nhát', 'can đảm', 'hèn nhát', 'yếu đuối'], answer: 'can đảm' },
          { id: 'd6', type: 'fill', question: 'Trái nghĩa với “sáng” (1 từ):', answer: 'tối' },
          { id: 'd7', type: 'mcq', question: 'Trái nghĩa với “giàu có”?', options: ['sung túc', 'nghèo khó', 'dư dả', 'khá giả'], answer: 'nghèo khó' },
          { id: 'd8', type: 'mcq', question: 'Từ nào KHÁC loại?', options: ['chạy', 'nhảy', 'bơi', 'bàn'], answer: 'bàn' }
        ]
      }
    }
  ]
};

window.LESSON_CONTENT_HSA['hsa_science'] = {
  course_id: 'hsa_science',
  course_title: 'Khoa học & Tiếng Anh',
  accent_color: '#34D399',
  lessons: [
    {
      id: 'kh_01',
      index: 1,
      title: 'Kiến thức khoa học nền tảng',
      subtitle: 'Lý – Hoá – Sinh: những khái niệm cốt lõi',
      topic_tag: 'Khoa học · Tổng hợp',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> khoa học nền của bạn.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Đơn vị đo cường độ dòng điện là gì?',
            options: ['Vôn (V)', 'Ampe (A)', 'Ôm (Ω)', 'Oát (W)'], answer: 'Ampe (A)',
            explain: 'Cường độ dòng điện đo bằng Ampe (A). Vôn đo hiệu điện thế, Ôm đo điện trở, Oát đo công suất.' },
          { id: 't2', type: 'mcq', question: 'Khí nào chiếm tỉ lệ lớn nhất trong không khí?',
            options: ['Oxi', 'Cacbonic', 'Nitơ', 'Hidro'], answer: 'Nitơ',
            explain: 'Nitơ chiếm ~78% thể tích không khí; Oxi ~21%.' },
          { id: 't3', type: 'fill', question: 'Quá trình cây xanh dùng ánh sáng tạo chất hữu cơ gọi là quang ___ (1 từ):',
            answer: 'hợp', explain: 'Quang hợp — cây tạo glucose + O₂ từ CO₂ và nước nhờ ánh sáng.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-bolt', title: 'Điện học cơ bản',
              body: 'Định luật Ôm: <code>U = I × R</code>. Đơn vị: hiệu điện thế U (Vôn), cường độ I (Ampe), điện trở R (Ôm), công suất P = U×I (Oát).' },
            { icon: 'fa-leaf', title: 'Sinh – Hoá nhớ nhanh',
              body: 'Không khí: ~78% Nitơ, ~21% Oxi. Quang hợp: CO₂ + H₂O + ánh sáng → glucose + O₂. Nước: H₂O.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ',
          cards: [
            { icon: 'fa-bolt', title: 'Điện học – Định luật Ôm',
              body: '<code>U = I × R</code>. U (Vôn) là hiệu điện thế, I (Ampe) là cường độ dòng điện, R (Ôm) là điện trở. Công suất <code>P = U × I</code> (Oát).' },
            { icon: 'fa-wind', title: 'Thành phần không khí',
              body: 'Nitơ (N₂) ~78%, Oxi (O₂) ~21%, còn lại ~1% (Argon, CO₂, hơi nước…). Oxi duy trì sự cháy và hô hấp.' },
            { icon: 'fa-leaf', title: 'Quang hợp',
              body: 'Cây xanh dùng ánh sáng + diệp lục biến CO₂ và nước thành glucose (chất hữu cơ) và nhả khí O₂. Ngược lại là hô hấp.' },
            { icon: 'fa-flask', title: 'Một số công thức nhớ',
              body: 'Nước: H₂O · Muối ăn: NaCl · Khí cacbonic: CO₂ · Khí ta thở ra nhiều: CO₂.' }
          ],
          examples: [
            { q: 'Mạch có U = 6V, R = 3Ω. Cường độ dòng điện I = ?', sol: 'I = U/R = 6/3 = 2A.' },
            { q: 'Khí nào cây nhả ra khi quang hợp?', sol: 'Khí Oxi (O₂).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Điện: U = I×R; U(Vôn), I(Ampe), R(Ôm), P=U×I (Oát).',
          'Không khí: ~78% Nitơ, ~21% Oxi.',
          'Quang hợp: CO₂ + nước + ánh sáng → chất hữu cơ + O₂.',
          'Nhớ công thức: nước H₂O, muối ăn NaCl, cacbonic CO₂.'
        ],
        formula: 'U = I × R    |    P = U × I',
        tip: 'Câu khoa học HSA thường hỏi đơn vị + công thức cơ bản — thuộc lòng bảng đơn vị (V/A/Ω/W) là ăn điểm nhanh.'
      },
      drill: {
        time_seconds: 75,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Đơn vị đo hiệu điện thế là?', options: ['Ampe', 'Vôn', 'Ôm', 'Jun'], answer: 'Vôn' },
          { id: 'd2', type: 'fill', question: 'Công thức hoá học của muối ăn là gì?', answer: 'NaCl' },
          { id: 'd3', type: 'mcq', question: 'Mạch U=10V, R=5Ω thì I = ? (A)', options: ['0.5', '2', '5', '50'], answer: '2' },
          { id: 'd4', type: 'mcq', question: 'Khí cây xanh nhả ra khi quang hợp?', options: ['CO₂', 'Nitơ', 'Oxi', 'Hidro'], answer: 'Oxi' },
          { id: 'd5', type: 'fill', question: 'Nước sôi ở bao nhiêu °C (áp suất thường)? (nhập số)', answer: '100' },
          { id: 'd6', type: 'mcq', question: 'Đơn vị đo công suất điện?', options: ['Vôn', 'Ampe', 'Oát', 'Ôm'], answer: 'Oát' },
          { id: 'd7', type: 'mcq', question: 'Khí chiếm ~21% không khí?', options: ['Nitơ', 'Oxi', 'CO₂', 'Argon'], answer: 'Oxi' },
          { id: 'd8', type: 'fill', question: 'Công thức hoá học của nước? (viết liền)', answer: 'H2O' }
        ]
      }
    }
  ]
};
