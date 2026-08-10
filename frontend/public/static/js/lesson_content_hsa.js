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
