/* ============================================================================
 * LESSON_CONTENT_HSA — nội dung bài học HSA (luồng ĐẢO NGƯỢC theo cô Hương):
 *   Bước 1 KIỂM TRA đầu vào → Bước 2 ĐÁNH GIÁ năng lực → Bước 3 LÝ THUYẾT
 *   (thích ứng: vững → tóm tắt gọn; yếu → đầy đủ + ví dụ) → Bước 4 GHI CHÚ
 *   → Bước 5 LUYỆN TỐC ĐỘ (bấm giờ).
 *
 * Schema mỗi lesson:
 *   test:   { intro, questions: [{id, type('mcq'|'fill'), question, options?, answer, explain?}] }
 *   assess: { strong_min, ok_min }              // ngưỡng số câu đúng
 *   theory: { condensed: {title, cards:[{icon,title,body}]},
 *             full:      {title, cards:[...], examples:[{q, sol}]} }
 *   notes:  { key_points:[...], formula?, tip? }
 *   drill:  { time_seconds, questions: [{id, type, question, options?, answer}] }
 *
 * PILOT 2026-08-10: mỗi khoá 1 bài chuẩn (C1 bài 1). TopHSA mở rộng theo khung
 * curricula.json (3 khoá × 6 chương) sau.
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
      title: 'Tỉ lệ & phần trăm',
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
    },

    {
      id: 'ql_02',
      index: 2,
      title: 'Dãy số & quy luật',
      subtitle: 'Cấp số cộng, cấp số nhân và nhận diện quy luật',
      topic_tag: 'Định lượng · Số học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về dãy số.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Số hạng tiếp theo của dãy 2, 5, 8, 11, … là bao nhiêu?',
            options: ['12', '13', '14', '15'], answer: '14',
            explain: 'Đây là cấp số cộng công sai d = 3, nên số tiếp theo = 11 + 3 = 14.' },
          { id: 't2', type: 'fill', question: 'Cấp số cộng có u₁ = 3, công sai d = 4. Số hạng u₅ bằng bao nhiêu? (nhập số)',
            answer: '19', explain: 'uₙ = u₁ + (n−1)d → u₅ = 3 + 4×4 = 19.' },
          { id: 't3', type: 'mcq', question: 'Dãy 3, 6, 12, 24, … là cấp số nhân với công bội q bằng bao nhiêu?',
            options: ['2', '3', '4', '6'], answer: '2',
            explain: 'Mỗi số gấp 2 lần số trước (6/3 = 2, 12/6 = 2…) → q = 2.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-plus', title: 'Cấp số cộng (CSC)',
              body: 'Hiệu hai số liên tiếp KHÔNG đổi = d. Số hạng: <code>uₙ = u₁ + (n−1)d</code>. Tổng: <code>Sₙ = n(u₁ + uₙ)/2</code>.' },
            { icon: 'fa-xmark', title: 'Cấp số nhân (CSN)',
              body: 'Tỉ số hai số liên tiếp KHÔNG đổi = q. Số hạng: <code>uₙ = u₁·qⁿ⁻¹</code>. Tổng: <code>Sₙ = u₁(qⁿ − 1)/(q − 1)</code> (q ≠ 1).' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ Dãy số',
          cards: [
            { icon: 'fa-list-ol', title: 'Dãy số là gì?',
              body: 'Là một danh sách số có thứ tự u₁, u₂, u₃, … Nhận diện quy luật: xét HIỆU (uₙ₊₁ − uₙ) hay TỈ SỐ (uₙ₊₁/uₙ) giữa các số liên tiếp.' },
            { icon: 'fa-plus', title: 'Cấp số cộng',
              body: 'Hiệu không đổi d. <code>uₙ = u₁ + (n−1)d</code>. Tổng n số đầu: <code>Sₙ = n(u₁ + uₙ)/2 = n[2u₁ + (n−1)d]/2</code>.' },
            { icon: 'fa-xmark', title: 'Cấp số nhân',
              body: 'Tỉ số không đổi q. <code>uₙ = u₁·qⁿ⁻¹</code>. Tổng: <code>Sₙ = u₁(qⁿ − 1)/(q − 1)</code> với q ≠ 1.' },
            { icon: 'fa-magnifying-glass', title: 'Mẹo nhận diện',
              body: 'Hiệu đều nhau → CSC. Tỉ số đều nhau → CSN. Nếu không → thử quy luật khác (bình phương, +1 +2 +3…, xen kẽ).' }
          ],
          examples: [
            { q: 'CSC: u₁ = 5, d = 3. Tính u₁₀.', sol: 'u₁₀ = 5 + 9×3 = 32.' },
            { q: 'Tổng 1 + 2 + 3 + … + 100 = ?', sol: 'S = 100×(1 + 100)/2 = 5050.' }
          ]
        }
      },
      notes: {
        key_points: [
          'CSC: hiệu không đổi d; uₙ = u₁ + (n−1)d; Sₙ = n(u₁+uₙ)/2.',
          'CSN: tỉ số không đổi q; uₙ = u₁·qⁿ⁻¹.',
          'Nhận diện: xét HIỆU (→CSC) hay TỈ SỐ (→CSN) giữa các số liên tiếp.'
        ],
        formula: 'CSC: uₙ = u₁ + (n−1)d   |   CSN: uₙ = u₁·qⁿ⁻¹',
        tip: 'Câu HSA hay cho vài số đầu rồi hỏi số hạng xa — dùng công thức uₙ, ĐỪNG liệt kê tay dễ sai.'
      },
      drill: {
        time_seconds: 75,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Số hạng tiếp theo của 1, 4, 7, 10, …?', options: ['11', '12', '13', '14'], answer: '13' },
          { id: 'd2', type: 'fill', question: 'CSC u₁ = 5, d = 3. Số hạng u₄ = ? (nhập số)', answer: '14' },
          { id: 'd3', type: 'mcq', question: 'Dãy 2, 4, 8, 16 là CSN công bội bằng?', options: ['2', '3', '4', '8'], answer: '2' },
          { id: 'd4', type: 'fill', question: 'Tổng 1 + 2 + 3 + … + 10 = ? (nhập số)', answer: '55' },
          { id: 'd5', type: 'mcq', question: 'CSC 3, 7, 11, 15 có công sai d bằng?', options: ['3', '4', '5', '7'], answer: '4' },
          { id: 'd6', type: 'fill', question: 'CSN u₁ = 2, q = 3. Số hạng u₃ = ? (nhập số)', answer: '18' },
          { id: 'd7', type: 'mcq', question: 'Số hạng thứ 6 của CSC 1, 3, 5, …?', options: ['9', '10', '11', '13'], answer: '11' },
          { id: 'd8', type: 'fill', question: 'Dãy 100, 90, 80, … số hạng thứ 5 là? (nhập số)', answer: '60' }
        ]
      }
    },

    {
      id: 'ql_03',
      index: 3,
      title: 'Biểu thức & rút gọn',
      subtitle: 'Hằng đẳng thức, phân tích nhân tử và rút gọn',
      topic_tag: 'Định lượng · Đại số',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về biến đổi biểu thức.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Khai triển (a + b)² bằng biểu thức nào?',
            options: ['a² + b²', 'a² + 2ab + b²', 'a² − 2ab + b²', '2a² + 2b²'], answer: 'a² + 2ab + b²',
            explain: '(a + b)² = a² + 2ab + b² — hằng đẳng thức đáng nhớ số 1.' },
          { id: 't2', type: 'fill', question: 'Tính giá trị của (x + 3)² − (x − 3)² tại x = 5. (nhập số)',
            answer: '60', explain: '(x+3)² − (x−3)² = 12x → tại x = 5 được 60.' },
          { id: 't3', type: 'mcq', question: 'Phân tích x² − 9 thành nhân tử được kết quả nào?',
            options: ['(x − 3)²', '(x − 3)(x + 3)', '(x − 9)(x + 1)', '(x + 3)²'], answer: '(x − 3)(x + 3)',
            explain: 'Hiệu hai bình phương: a² − b² = (a − b)(a + b) → x² − 9 = (x − 3)(x + 3).' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-square-root-variable', title: '3 hằng đẳng thức lõi',
              body: '<code>(a±b)² = a² ± 2ab + b²</code> · <code>a² − b² = (a−b)(a+b)</code>. Nhớ để KHAI TRIỂN nhanh và PHÂN TÍCH nhân tử.' },
            { icon: 'fa-divide', title: 'Rút gọn phân thức',
              body: 'Phân tích tử & mẫu thành nhân tử rồi rút gọn nhân tử chung. Nhớ điều kiện xác định (mẫu ≠ 0).' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ biến đổi biểu thức',
          cards: [
            { icon: 'fa-square-root-variable', title: 'Hằng đẳng thức đáng nhớ',
              body: '(a+b)² = a²+2ab+b² · (a−b)² = a²−2ab+b² · a²−b² = (a−b)(a+b) · (a+b)³, (a−b)³, a³±b³.' },
            { icon: 'fa-scissors', title: 'Phân tích thành nhân tử',
              body: 'Các cách: đặt nhân tử chung, dùng hằng đẳng thức, nhóm hạng tử, tách hạng tử. VD: x² − 5x + 6 = (x−2)(x−3).' },
            { icon: 'fa-divide', title: 'Rút gọn phân thức',
              body: 'Đưa tử & mẫu về dạng tích rồi rút gọn nhân tử chung. VD: (x²−9)/(x−3) = (x−3)(x+3)/(x−3) = x+3 (với x ≠ 3).' },
            { icon: 'fa-triangle-exclamation', title: 'Bẫy hay gặp',
              body: '(a+b)² ≠ a²+b². Rút gọn phân thức phải nhớ ĐIỀU KIỆN xác định. Khi thay số, tính trong ngoặc trước.' }
          ],
          examples: [
            { q: 'Rút gọn (x²−4)/(x+2).', sol: '(x−2)(x+2)/(x+2) = x − 2 (với x ≠ −2).' },
            { q: 'Tính nhanh 99² = ?', sol: '(100−1)² = 10000 − 200 + 1 = 9801.' }
          ]
        }
      },
      notes: {
        key_points: [
          '(a±b)² = a² ± 2ab + b²; a² − b² = (a−b)(a+b).',
          'Phân tích nhân tử: nhân tử chung → hằng đẳng thức → nhóm/tách.',
          'Rút gọn phân thức: đưa về tích rồi rút gọn; nhớ điều kiện mẫu ≠ 0.',
          '(a+b)² KHÔNG bằng a² + b².'
        ],
        formula: '(a±b)² = a² ± 2ab + b²   |   a² − b² = (a−b)(a+b)',
        tip: 'Gặp hiệu/tổng bình phương hay số gần tròn (99², 101²), dùng hằng đẳng thức để nhẩm nhanh không cần máy.'
      },
      drill: {
        time_seconds: 75,
        questions: [
          { id: 'd1', type: 'mcq', question: '(a − b)² bằng?', options: ['a² − b²', 'a² − 2ab + b²', 'a² + 2ab + b²', 'a² + b²'], answer: 'a² − 2ab + b²' },
          { id: 'd2', type: 'fill', question: 'Tính (x − 1)(x + 1) tại x = 4. (nhập số)', answer: '15' },
          { id: 'd3', type: 'mcq', question: 'x² − 4 phân tích thành?', options: ['(x−2)²', '(x−2)(x+2)', '(x−4)(x+1)', '(x+2)²'], answer: '(x−2)(x+2)' },
          { id: 'd4', type: 'fill', question: 'Giá trị (a + b)² tại a = 2, b = 3. (nhập số)', answer: '25' },
          { id: 'd5', type: 'mcq', question: 'a² + 2ab + b² bằng?', options: ['(a−b)²', '(a+b)²', 'a² + b²', '2ab'], answer: '(a+b)²' },
          { id: 'd6', type: 'fill', question: 'Tính 5² − 3². (nhập số)', answer: '16' },
          { id: 'd7', type: 'mcq', question: '(x + 2)² khai triển bằng?', options: ['x² + 4', 'x² + 2x + 4', 'x² + 4x + 4', 'x² + 4x + 2'], answer: 'x² + 4x + 4' },
          { id: 'd8', type: 'fill', question: 'Tính 6² − 2². (nhập số)', answer: '32' }
        ]
      }
    },

    {
      id: 'ql_04',
      index: 4,
      title: 'Phương trình & bất phương trình',
      subtitle: 'Bậc nhất, bậc hai, định lý Vi-ét và dấu bất phương trình',
      topic_tag: 'Định lượng · Đại số',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về phương trình – bất phương trình.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Nghiệm của phương trình 2x − 6 = 0 là?',
            options: ['x = 2', 'x = 3', 'x = 4', 'x = −3'], answer: 'x = 3',
            explain: '2x = 6 → x = 3.' },
          { id: 't2', type: 'fill', question: 'Phương trình x² − 5x + 6 = 0 có hai nghiệm. Tổng hai nghiệm bằng bao nhiêu? (Vi-ét, nhập số)',
            answer: '5', explain: 'Vi-ét: tổng nghiệm = −b/a = 5 (hai nghiệm là 2 và 3).' },
          { id: 't3', type: 'mcq', question: 'Tập nghiệm của bất phương trình x − 2 > 0 là?',
            options: ['x < 2', 'x > 2', 'x ≥ 2', 'x ≤ 2'], answer: 'x > 2',
            explain: 'x − 2 > 0 → x > 2.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-equals', title: 'PT bậc nhất & bậc hai',
              body: 'Bậc nhất ax + b = 0 → <code>x = −b/a</code>. Bậc hai ax² + bx + c = 0: <code>Δ = b² − 4ac</code>; Δ&gt;0 hai nghiệm, Δ=0 nghiệm kép, Δ&lt;0 vô nghiệm.' },
            { icon: 'fa-scale-balanced', title: 'Vi-ét & BPT',
              body: 'Vi-ét: <code>x₁+x₂ = −b/a</code>, <code>x₁·x₂ = c/a</code>. BPT bậc nhất giải như PT, nhưng NHÂN/CHIA số ÂM phải ĐỔI CHIỀU dấu.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ PT & BPT',
          cards: [
            { icon: 'fa-equals', title: 'Phương trình bậc nhất',
              body: 'ax + b = 0 (a ≠ 0) → x = −b/a. Chuyển vế đổi dấu, gom ẩn một bên, số một bên.' },
            { icon: 'fa-square-root-variable', title: 'Phương trình bậc hai',
              body: 'ax² + bx + c = 0. Tính Δ = b² − 4ac. Δ > 0: x = (−b ± √Δ)/(2a). Δ = 0: nghiệm kép x = −b/(2a). Δ < 0: vô nghiệm.' },
            { icon: 'fa-scale-balanced', title: 'Định lý Vi-ét',
              body: 'Nếu PT bậc hai có 2 nghiệm: tổng x₁ + x₂ = −b/a, tích x₁·x₂ = c/a. Dùng để nhẩm nghiệm và tính biểu thức đối xứng.' },
            { icon: 'fa-arrow-right-arrow-left', title: 'Bất phương trình',
              body: 'Giải tương tự PT. Quy tắc VÀNG: khi NHÂN hoặc CHIA cả hai vế cho một số ÂM thì phải ĐỔI CHIỀU dấu bất phương trình.' }
          ],
          examples: [
            { q: 'Giải x² − 7x + 12 = 0.', sol: 'Δ = 49 − 48 = 1 → x = (7 ± 1)/2 → x = 4 hoặc x = 3.' },
            { q: 'Giải −2x > 6.', sol: 'Chia cho −2 (đổi chiều): x < −3.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Bậc nhất ax + b = 0 → x = −b/a.',
          'Bậc hai: Δ = b² − 4ac quyết định số nghiệm; x = (−b ± √Δ)/(2a).',
          'Vi-ét: x₁+x₂ = −b/a, x₁·x₂ = c/a.',
          'BPT: nhân/chia số ÂM → ĐỔI CHIỀU dấu.'
        ],
        formula: 'Δ = b² − 4ac   |   x = (−b ± √Δ)/(2a)   |   x₁+x₂ = −b/a, x₁x₂ = c/a',
        tip: 'Câu bậc hai HSA thường hỏi tổng/tích nghiệm — dùng Vi-ét trả lời NGAY, không cần giải ra nghiệm.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Nghiệm của 3x − 9 = 0?', options: ['x = 2', 'x = 3', 'x = −3', 'x = 9'], answer: 'x = 3' },
          { id: 'd2', type: 'fill', question: 'x² − 7x + 12 = 0, tổng hai nghiệm? (Vi-ét, nhập số)', answer: '7' },
          { id: 'd3', type: 'mcq', question: 'Tập nghiệm của 2x > 6?', options: ['x > 3', 'x < 3', 'x > 6', 'x < 6'], answer: 'x > 3' },
          { id: 'd4', type: 'fill', question: 'Nghiệm của 5x + 10 = 0? (nhập số)', answer: '-2' },
          { id: 'd5', type: 'mcq', question: 'Δ của x² − 4x + 4 = 0 bằng?', options: ['0', '4', '8', '16'], answer: '0' },
          { id: 'd6', type: 'fill', question: 'Nghiệm dương của x² − 9 = 0? (nhập số)', answer: '3' },
          { id: 'd7', type: 'mcq', question: 'BPT −x > −2 tương đương?', options: ['x < 2', 'x > 2', 'x < −2', 'x > −2'], answer: 'x < 2' },
          { id: 'd8', type: 'fill', question: 'x² − 5x + 6 = 0, tích hai nghiệm? (Vi-ét, nhập số)', answer: '6' }
        ]
      }
    },

    {
      id: 'ql_05',
      index: 5,
      title: 'Hệ phương trình',
      subtitle: 'Hệ bậc nhất hai ẩn: phương pháp thế và cộng đại số',
      topic_tag: 'Định lượng · Đại số',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về hệ phương trình.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Hệ {x + y = 5 ; x − y = 1} có nghiệm (x ; y) là?',
            options: ['(2 ; 3)', '(3 ; 2)', '(4 ; 1)', '(1 ; 4)'], answer: '(3 ; 2)',
            explain: 'Cộng hai PT: 2x = 6 → x = 3 → y = 2. Thử lại: 3+2 = 5, 3−2 = 1 (đúng).' },
          { id: 't2', type: 'fill', question: 'Hệ {x + y = 10 ; 2x + y = 14}. Giá trị của x bằng bao nhiêu? (nhập số)',
            answer: '4', explain: 'Trừ hai PT: (2x+y) − (x+y) = 14 − 10 → x = 4 (khi đó y = 6).' },
          { id: 't3', type: 'mcq', question: 'Phương pháp cộng/trừ hai phương trình để KHỬ một ẩn gọi là?',
            options: ['phương pháp thế', 'phương pháp cộng đại số', 'phương pháp đồ thị', 'định lý Vi-ét'], answer: 'phương pháp cộng đại số',
            explain: 'Cộng đại số: nhân cho hệ số phù hợp rồi cộng/trừ để khử một ẩn.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-right-left', title: 'Phương pháp thế',
              body: 'Rút một ẩn từ một PT (VD y = … theo x) rồi THẾ vào PT còn lại → PT một ẩn → giải xong thế ngược lại tìm ẩn kia.' },
            { icon: 'fa-plus-minus', title: 'Phương pháp cộng đại số',
              body: 'Nhân hai PT cho hệ số thích hợp để một ẩn có hệ số đối nhau, rồi CỘNG/TRỪ để KHỬ ẩn đó.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ Hệ phương trình',
          cards: [
            { icon: 'fa-list', title: 'Hệ bậc nhất hai ẩn',
              body: 'Dạng {a₁x + b₁y = c₁ ; a₂x + b₂y = c₂}. Nghiệm là cặp (x ; y) thỏa CẢ HAI phương trình.' },
            { icon: 'fa-right-left', title: 'Phương pháp thế',
              body: 'Bước 1: rút một ẩn theo ẩn kia. Bước 2: thế vào PT còn lại được PT một ẩn. Bước 3: giải rồi thế ngược lại.' },
            { icon: 'fa-plus-minus', title: 'Phương pháp cộng đại số',
              body: 'Làm cho một ẩn có hệ số bằng nhau (hoặc đối nhau) ở hai PT, rồi trừ (hoặc cộng) để khử ẩn đó, còn lại PT một ẩn.' },
            { icon: 'fa-circle-info', title: 'Số nghiệm của hệ',
              body: 'Có thể: một nghiệm duy nhất; VÔ SỐ nghiệm (hai PT trùng nhau); hoặc VÔ NGHIỆM (hai PT mâu thuẫn).' }
          ],
          examples: [
            { q: 'Giải {2x + y = 7 ; x − y = 2}.', sol: 'Cộng: 3x = 9 → x = 3 → y = 1.' },
            { q: 'Bài toán: 2 bút + 1 vở = 20k; 1 bút + 1 vở = 14k. Giá 1 bút?', sol: 'Trừ: 1 bút = 6k (vở = 8k).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Nghiệm hệ = cặp (x ; y) thỏa CẢ HAI phương trình.',
          'PP thế: rút một ẩn → thế vào PT còn lại.',
          'PP cộng đại số: khử một ẩn bằng cách cộng/trừ hai PT.',
          'Hệ có thể: 1 nghiệm / vô số nghiệm / vô nghiệm.'
        ],
        formula: 'Khử 1 ẩn → PT một ẩn → thế ngược lại tìm ẩn còn lại',
        tip: 'Nếu hai hệ số của một ẩn đã bằng/đối nhau → dùng NGAY cộng đại số, nhanh hơn phương pháp thế.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Hệ {x + y = 7 ; x − y = 3} có nghiệm (x ; y)?', options: ['(5 ; 2)', '(2 ; 5)', '(4 ; 3)', '(3 ; 4)'], answer: '(5 ; 2)' },
          { id: 'd2', type: 'fill', question: 'Hệ {x + y = 8 ; x = 3y}. Giá trị y = ? (nhập số)', answer: '2' },
          { id: 'd3', type: 'mcq', question: 'Hệ có VÔ SỐ nghiệm khi hai phương trình?', options: ['trùng nhau', 'mâu thuẫn', 'khác hệ số', 'vuông góc'], answer: 'trùng nhau' },
          { id: 'd4', type: 'fill', question: 'Hệ {2x + y = 7 ; x = 2}. Giá trị y = ? (nhập số)', answer: '3' },
          { id: 'd5', type: 'mcq', question: 'Rút một ẩn rồi thay vào PT kia là phương pháp?', options: ['thế', 'cộng đại số', 'đồ thị', 'Vi-ét'], answer: 'thế' },
          { id: 'd6', type: 'fill', question: 'Hệ {x − y = 1 ; x + y = 9}. Giá trị x = ? (nhập số)', answer: '5' },
          { id: 'd7', type: 'mcq', question: 'Hệ {x + y = 5 ; 2x + 2y = 10} có bao nhiêu nghiệm?', options: ['1 nghiệm', 'vô số nghiệm', 'vô nghiệm', '2 nghiệm'], answer: 'vô số nghiệm' },
          { id: 'd8', type: 'fill', question: 'Hệ {3x = 12 ; x + y = 10}. Giá trị y = ? (nhập số)', answer: '6' }
        ]
      }
    },

    {
      id: 'ql_06',
      index: 6,
      title: 'Hàm bậc nhất & đồ thị',
      subtitle: 'Đường thẳng y = ax + b, hệ số góc và tính đơn điệu',
      topic_tag: 'Định lượng · Hàm số',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về hàm bậc nhất.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Đồ thị của hàm số y = ax + b (a ≠ 0) là hình gì?',
            options: ['đường thẳng', 'parabol', 'đường tròn', 'hyperbol'], answer: 'đường thẳng',
            explain: 'Hàm bậc nhất y = ax + b luôn có đồ thị là một đường thẳng.' },
          { id: 't2', type: 'fill', question: 'Cho hàm số y = 2x + 1. Giá trị của y khi x = 3 bằng bao nhiêu? (nhập số)',
            answer: '7', explain: 'y = 2×3 + 1 = 7.' },
          { id: 't3', type: 'mcq', question: 'Hàm số y = ax + b ĐỒNG BIẾN (tăng) khi nào?',
            options: ['a > 0', 'a < 0', 'a = 0', 'b > 0'], answer: 'a > 0',
            explain: 'Hệ số góc a > 0 → hàm đồng biến; a < 0 → nghịch biến.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-chart-line', title: 'Hàm bậc nhất',
              body: 'y = ax + b (a ≠ 0). Đồ thị là ĐƯỜNG THẲNG. a là <b>hệ số góc</b> (độ dốc), b là tung độ gốc (giao Oy).' },
            { icon: 'fa-arrow-trend-up', title: 'Tính đơn điệu',
              body: 'a &gt; 0 → đồng biến (đi lên). a &lt; 0 → nghịch biến (đi xuống). Hai đường thẳng song song khi a = a′, b ≠ b′.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ hàm bậc nhất',
          cards: [
            { icon: 'fa-function', title: 'Định nghĩa',
              body: 'Hàm số bậc nhất có dạng y = ax + b với a ≠ 0. VD y = 2x − 3, y = −x + 5.' },
            { icon: 'fa-chart-line', title: 'Đồ thị đường thẳng',
              body: 'Là đường thẳng cắt Oy tại điểm (0 ; b) và cắt Ox tại điểm (−b/a ; 0). Chỉ cần 2 điểm là vẽ được.' },
            { icon: 'fa-arrow-trend-up', title: 'Hệ số góc & đơn điệu',
              body: 'a = hệ số góc = độ dốc. a > 0: đường đi lên (đồng biến); a < 0: đi xuống (nghịch biến); |a| càng lớn đường càng dốc.' },
            { icon: 'fa-grip-lines', title: 'Vị trí hai đường thẳng',
              body: 'y = ax + b và y = a′x + b′: song song khi a = a′, b ≠ b′; trùng nhau khi a = a′, b = b′; cắt nhau khi a ≠ a′.' }
          ],
          examples: [
            { q: 'Đường thẳng y = 3x − 6 cắt Ox tại điểm nào?', sol: 'Cho y = 0: 3x − 6 = 0 → x = 2 → điểm (2 ; 0).' },
            { q: 'y = −2x + 1 đồng biến hay nghịch biến?', sol: 'a = −2 < 0 → nghịch biến.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Hàm bậc nhất y = ax + b (a ≠ 0), đồ thị là đường thẳng.',
          'a = hệ số góc: a > 0 đồng biến, a < 0 nghịch biến.',
          'Cắt Oy tại (0 ; b), cắt Ox tại (−b/a ; 0).',
          'Song song khi a = a′ và b ≠ b′.'
        ],
        formula: 'y = ax + b   |   giao Ox: x = −b/a   |   giao Oy: y = b',
        tip: 'Nhìn dấu của a là biết ngay hàm tăng hay giảm — không cần vẽ đồ thị.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Đồ thị hàm y = ax + b (a≠0) là?', options: ['đường thẳng', 'parabol', 'đường tròn', 'hyperbol'], answer: 'đường thẳng' },
          { id: 'd2', type: 'fill', question: 'y = 3x − 2, giá trị y khi x = 2? (nhập số)', answer: '4' },
          { id: 'd3', type: 'mcq', question: 'Hàm y = −5x + 1 là?', options: ['đồng biến', 'nghịch biến', 'hằng số', 'không xác định'], answer: 'nghịch biến' },
          { id: 'd4', type: 'fill', question: 'Đường y = 2x − 8 cắt Ox tại x = ? (nhập số)', answer: '4' },
          { id: 'd5', type: 'mcq', question: 'Hệ số góc của đường y = 4x + 3 là?', options: ['3', '4', '−3', '7'], answer: '4' },
          { id: 'd6', type: 'fill', question: 'y = −x + 5, giá trị y khi x = 0? (nhập số)', answer: '5' },
          { id: 'd7', type: 'mcq', question: 'Hai đường y = 2x + 1 và y = 2x − 3?', options: ['song song', 'cắt nhau', 'trùng nhau', 'vuông góc'], answer: 'song song' },
          { id: 'd8', type: 'fill', question: 'y = 5x, giá trị y khi x = 3? (nhập số)', answer: '15' }
        ]
      }
    },

    {
      id: 'ql_07',
      index: 7,
      title: 'Hàm bậc hai & parabol',
      subtitle: 'y = ax² + bx + c, đỉnh và trục đối xứng',
      topic_tag: 'Định lượng · Hàm số',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về hàm bậc hai.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Đồ thị của hàm số bậc hai y = ax² + bx + c (a ≠ 0) là hình gì?',
            options: ['đường thẳng', 'parabol', 'đường tròn', 'hình sin'], answer: 'parabol',
            explain: 'Hàm bậc hai có đồ thị là một parabol.' },
          { id: 't2', type: 'fill', question: 'Cho y = x² − 4x + 3. Giá trị của y khi x = 0 bằng bao nhiêu? (nhập số)',
            answer: '3', explain: 'y = 0 − 0 + 3 = 3.' },
          { id: 't3', type: 'mcq', question: 'Parabol y = ax² + bx + c có bề lõm quay LÊN TRÊN khi nào?',
            options: ['a > 0', 'a < 0', 'a = 0', 'b > 0'], answer: 'a > 0',
            explain: 'a > 0 → bề lõm quay lên (có điểm thấp nhất); a < 0 → bề lõm quay xuống.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-chart-area', title: 'Parabol',
              body: 'y = ax² + bx + c (a ≠ 0), đồ thị là parabol. a > 0 lõm lên; a < 0 lõm xuống. Trục đối xứng: <code>x = −b/(2a)</code>.' },
            { icon: 'fa-location-dot', title: 'Đỉnh parabol',
              body: 'Hoành độ đỉnh <code>x = −b/(2a)</code>. Tại đỉnh, parabol đạt GTNN (nếu a>0) hoặc GTLN (nếu a<0).' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ hàm bậc hai',
          cards: [
            { icon: 'fa-function', title: 'Định nghĩa',
              body: 'y = ax² + bx + c với a ≠ 0. VD y = x² − 2x + 1, y = −2x² + 3.' },
            { icon: 'fa-chart-area', title: 'Đồ thị parabol',
              body: 'Là đường cong parabol. a > 0: bề lõm quay lên (hình chữ U); a < 0: bề lõm quay xuống (hình chữ U ngược).' },
            { icon: 'fa-location-dot', title: 'Đỉnh & trục đối xứng',
              body: 'Trục đối xứng là đường thẳng x = −b/(2a). Đỉnh là điểm thấp nhất (a>0) hoặc cao nhất (a<0) của parabol, có hoành độ x = −b/(2a).' },
            { icon: 'fa-arrows-up-down', title: 'Giá trị lớn nhất / nhỏ nhất',
              body: 'Vì parabol có đỉnh nên hàm bậc hai luôn đạt GTLN hoặc GTNN tại đỉnh — rất hay dùng trong bài toán tối ưu.' }
          ],
          examples: [
            { q: 'Tìm trục đối xứng của y = x² − 6x + 5.', sol: 'x = −b/(2a) = 6/2 = 3.' },
            { q: 'y = x² đạt GTNN bằng bao nhiêu?', sol: 'Tại đỉnh x = 0 → y = 0 là GTNN.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Hàm bậc hai y = ax² + bx + c (a ≠ 0), đồ thị là parabol.',
          'a > 0 lõm lên (có GTNN); a < 0 lõm xuống (có GTLN).',
          'Trục đối xứng & hoành độ đỉnh: x = −b/(2a).',
          'Hàm đạt GTLN/GTNN tại đỉnh.'
        ],
        formula: 'x_đỉnh = −b/(2a)   |   a>0 → GTNN tại đỉnh; a<0 → GTLN tại đỉnh',
        tip: 'Nhớ x = −b/(2a) là “chìa khóa” của mọi bài parabol: tìm đỉnh, trục đối xứng, GTLN/GTNN.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Đồ thị hàm bậc hai là?', options: ['đường thẳng', 'parabol', 'đường tròn', 'hình sin'], answer: 'parabol' },
          { id: 'd2', type: 'fill', question: 'y = x² − 4x + 3, giá trị y khi x = 3? (nhập số)', answer: '0' },
          { id: 'd3', type: 'mcq', question: 'Parabol y = −2x² + 1 có bề lõm?', options: ['quay lên', 'quay xuống', 'sang trái', 'sang phải'], answer: 'quay xuống' },
          { id: 'd4', type: 'fill', question: 'Hoành độ đỉnh của y = x² − 6x + 5 là? (nhập số)', answer: '3' },
          { id: 'd5', type: 'mcq', question: 'y = x² đạt GTNN tại x = ?', options: ['−1', '0', '1', '2'], answer: '0' },
          { id: 'd6', type: 'fill', question: 'y = x² − 2x, giá trị y khi x = 2? (nhập số)', answer: '0' },
          { id: 'd7', type: 'mcq', question: 'Trục đối xứng của parabol có phương trình?', options: ['x = −b/(2a)', 'x = b/a', 'x = −c/a', 'x = a/b'], answer: 'x = −b/(2a)' },
          { id: 'd8', type: 'fill', question: 'y = 2x² + 1, giá trị y khi x = 0? (nhập số)', answer: '1' }
        ]
      }
    },

    {
      id: 'ql_08',
      index: 8,
      title: 'Hàm mũ – logarit',
      subtitle: 'Lũy thừa, hàm mũ và logarit cơ bản',
      topic_tag: 'Định lượng · Giải tích',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về mũ – logarit.',
        questions: [
          { id: 't1', type: 'mcq', question: 'log₂ 8 bằng bao nhiêu?',
            options: ['2', '3', '4', '8'], answer: '3',
            explain: 'log₂ 8 = 3 vì 2³ = 8.' },
          { id: 't2', type: 'fill', question: 'Rút gọn 2³ × 2² = 2^n. Giá trị của n là bao nhiêu? (nhập số)',
            answer: '5', explain: 'aᵐ × aⁿ = aᵐ⁺ⁿ → 2³ × 2² = 2⁵, nên n = 5.' },
          { id: 't3', type: 'mcq', question: 'Công thức nào ĐÚNG với logarit của một tích?',
            options: ['log(a·b) = log a + log b', 'log(a·b) = log a − log b', 'log(a·b) = log a × log b', 'log(a·b) = log a / log b'], answer: 'log(a·b) = log a + log b',
            explain: 'Logarit của tích = tổng các logarit: log(ab) = log a + log b.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-superscript', title: 'Lũy thừa',
              body: '<code>aᵐ · aⁿ = aᵐ⁺ⁿ</code> · <code>aᵐ / aⁿ = aᵐ⁻ⁿ</code> · <code>(aᵐ)ⁿ = aᵐⁿ</code> · a⁰ = 1.' },
            { icon: 'fa-calculator', title: 'Logarit',
              body: '<code>log_a b = c ⟺ aᶜ = b</code>. Tính chất: log(xy) = log x + log y; log(x/y) = log x − log y; log(xⁿ) = n·log x.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ mũ – logarit',
          cards: [
            { icon: 'fa-superscript', title: 'Lũy thừa & tính chất',
              body: 'aⁿ = a·a·…·a (n thừa số). Quy tắc: aᵐ·aⁿ = aᵐ⁺ⁿ; aᵐ/aⁿ = aᵐ⁻ⁿ; (aᵐ)ⁿ = aᵐⁿ; a⁰ = 1; a⁻ⁿ = 1/aⁿ.' },
            { icon: 'fa-chart-line', title: 'Hàm số mũ',
              body: 'y = aˣ (a > 0, a ≠ 1). Nếu a > 1: đồng biến; 0 < a < 1: nghịch biến. Luôn dương, đi qua điểm (0 ; 1).' },
            { icon: 'fa-calculator', title: 'Logarit',
              body: 'log_a b = c nghĩa là aᶜ = b (a > 0, a ≠ 1, b > 0). VD log₂ 8 = 3; log₁₀ 100 = 2. log tự nhiên cơ số e viết là ln.' },
            { icon: 'fa-list-check', title: 'Tính chất logarit',
              body: 'log(xy) = log x + log y; log(x/y) = log x − log y; log(xⁿ) = n·log x; log_a a = 1; log_a 1 = 0.' }
          ],
          examples: [
            { q: 'Tính log₃ 27.', sol: 'log₃ 27 = 3 vì 3³ = 27.' },
            { q: 'Rút gọn 5⁴ / 5² = ?', sol: '5⁴⁻² = 5² = 25.' }
          ]
        }
      },
      notes: {
        key_points: [
          'aᵐ·aⁿ = aᵐ⁺ⁿ; aᵐ/aⁿ = aᵐ⁻ⁿ; (aᵐ)ⁿ = aᵐⁿ.',
          'log_a b = c ⟺ aᶜ = b.',
          'log(xy) = log x + log y; log(xⁿ) = n·log x.',
          'a⁰ = 1; log_a 1 = 0; log_a a = 1.'
        ],
        formula: 'aᵐ·aⁿ = aᵐ⁺ⁿ   |   log_a b = c ⟺ aᶜ = b   |   log(xy) = log x + log y',
        tip: 'Gặp logₐ b, tự hỏi “a mũ mấy bằng b?” — trả lời được là ra đáp án ngay.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'log₂ 16 bằng?', options: ['2', '3', '4', '8'], answer: '4' },
          { id: 'd2', type: 'fill', question: '3² × 3³ = 3^n. Giá trị n? (nhập số)', answer: '5' },
          { id: 'd3', type: 'mcq', question: 'log₁₀ 100 bằng?', options: ['1', '2', '10', '100'], answer: '2' },
          { id: 'd4', type: 'fill', question: 'Tính giá trị của 2⁵. (nhập số)', answer: '32' },
          { id: 'd5', type: 'mcq', question: 'a⁰ bằng?', options: ['0', '1', 'a', 'không xác định'], answer: '1' },
          { id: 'd6', type: 'fill', question: 'log₃ 9 bằng? (nhập số)', answer: '2' },
          { id: 'd7', type: 'mcq', question: 'log(xⁿ) bằng?', options: ['n · log x', 'log x / n', 'xⁿ', 'n + log x'], answer: 'n · log x' },
          { id: 'd8', type: 'fill', question: '2⁶ / 2² = 2^n. Giá trị n? (nhập số)', answer: '4' }
        ]
      }
    },

    {
      id: 'ql_09',
      index: 9,
      title: 'Đạo hàm & ứng dụng',
      subtitle: 'Đạo hàm cơ bản và tính đơn điệu của hàm số',
      topic_tag: 'Định lượng · Giải tích',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về đạo hàm.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Đạo hàm của hàm số y = x² là?',
            options: ['x', '2x', 'x²', '2'], answer: '2x',
            explain: '(xⁿ)′ = n·xⁿ⁻¹ → (x²)′ = 2x.' },
          { id: 't2', type: 'fill', question: 'Đạo hàm của y = x³ là 3x^n. Giá trị của n là? (nhập số)',
            answer: '2', explain: '(x³)′ = 3x² → n = 2.' },
          { id: 't3', type: 'mcq', question: 'Hàm số ĐỒNG BIẾN trên một khoảng khi đạo hàm y′ trên khoảng đó?',
            options: ['dương (y′ > 0)', 'âm (y′ < 0)', 'bằng 0', 'không xác định'], answer: 'dương (y′ > 0)',
            explain: 'y′ > 0 → hàm đồng biến (tăng); y′ < 0 → nghịch biến (giảm).' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-superscript', title: 'Đạo hàm cơ bản',
              body: '<code>(xⁿ)′ = n·xⁿ⁻¹</code>. Hằng số: (C)′ = 0. Tổng: (u ± v)′ = u′ ± v′. VD (x²)′ = 2x, (x³)′ = 3x².' },
            { icon: 'fa-arrow-trend-up', title: 'Đạo hàm & đơn điệu',
              body: 'y′ > 0 → hàm đồng biến; y′ < 0 → nghịch biến; y′ = 0 tại điểm nghi ngờ CỰC TRỊ.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ đạo hàm',
          cards: [
            { icon: 'fa-arrow-down-up-across-line', title: 'Đạo hàm là gì?',
              body: 'Đạo hàm y′ đo TỐC ĐỘ BIẾN THIÊN của hàm số; về hình học là hệ số góc tiếp tuyến tại một điểm.' },
            { icon: 'fa-superscript', title: 'Công thức cơ bản',
              body: '(xⁿ)′ = n·xⁿ⁻¹; (C)′ = 0; (kx)′ = k; (u + v)′ = u′ + v′. VD: (3x² − 5x + 2)′ = 6x − 5.' },
            { icon: 'fa-arrow-trend-up', title: 'Xét tính đơn điệu',
              body: 'Tính y′, xét dấu: khoảng nào y′ > 0 thì hàm đồng biến; y′ < 0 thì nghịch biến. Đây là ứng dụng quan trọng nhất.' },
            { icon: 'fa-location-dot', title: 'Cực trị',
              body: 'Điểm mà y′ = 0 và y′ đổi dấu là điểm cực trị. Đổi + sang − → cực đại; − sang + → cực tiểu.' }
          ],
          examples: [
            { q: 'Tính đạo hàm y = 3x² − 4x + 1.', sol: 'y′ = 6x − 4.' },
            { q: 'y = x² đồng biến trên khoảng nào?', sol: 'y′ = 2x > 0 ⟺ x > 0 → đồng biến trên (0 ; +∞).' }
          ]
        }
      },
      notes: {
        key_points: [
          '(xⁿ)′ = n·xⁿ⁻¹; (C)′ = 0; (u ± v)′ = u′ ± v′.',
          'y′ > 0 → đồng biến; y′ < 0 → nghịch biến.',
          'y′ = 0 và đổi dấu → điểm cực trị.',
          'Đạo hàm = hệ số góc tiếp tuyến tại một điểm.'
        ],
        formula: '(xⁿ)′ = n·xⁿ⁻¹   |   y′ > 0 đồng biến, y′ < 0 nghịch biến',
        tip: 'Đa số câu HSA chỉ cần đạo hàm đa thức: hạ số mũ xuống nhân, mũ giảm 1 — làm nhanh gọn.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Đạo hàm của y = x² là?', options: ['x', '2x', 'x²', '2'], answer: '2x' },
          { id: 'd2', type: 'fill', question: 'Đạo hàm của y = x⁴ là 4x^n. Giá trị n? (nhập số)', answer: '3' },
          { id: 'd3', type: 'mcq', question: 'Đạo hàm của hằng số y = 5 là?', options: ['5', '0', 'x', '1'], answer: '0' },
          { id: 'd4', type: 'fill', question: 'Đạo hàm của y = 3x tại mọi điểm bằng? (nhập số)', answer: '3' },
          { id: 'd5', type: 'mcq', question: 'Hàm nghịch biến khi đạo hàm y′?', options: ['dương', 'âm', 'bằng 0', 'bằng 1'], answer: 'âm' },
          { id: 'd6', type: 'fill', question: 'Đạo hàm của y = x² + 2x tại x có dạng 2x + n. Giá trị n? (nhập số)', answer: '2' },
          { id: 'd7', type: 'mcq', question: 'Điểm cực trị là nơi y′?', options: ['bằng 0 và đổi dấu', 'luôn dương', 'luôn âm', 'không tồn tại'], answer: 'bằng 0 và đổi dấu' },
          { id: 'd8', type: 'fill', question: 'Đạo hàm của y = 6x² là 12x^n. Giá trị n? (nhập số)', answer: '1' }
        ]
      }
    },

    {
      id: 'ql_10',
      index: 10,
      title: 'GTLN – GTNN',
      subtitle: 'Tìm giá trị lớn nhất, nhỏ nhất của hàm số',
      topic_tag: 'Định lượng · Giải tích',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về GTLN – GTNN.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Giá trị NHỎ NHẤT của hàm số y = x² là bao nhiêu?',
            options: ['−1', '0', '1', 'không có'], answer: '0',
            explain: 'y = x² ≥ 0, đạt nhỏ nhất bằng 0 tại x = 0.' },
          { id: 't2', type: 'fill', question: 'Giá trị LỚN NHẤT của hàm số y = −x² + 4 là bao nhiêu? (nhập số)',
            answer: '4', explain: 'y = −x² + 4 ≤ 4, đạt lớn nhất bằng 4 tại x = 0.' },
          { id: 't3', type: 'mcq', question: 'Để tìm GTLN – GTNN của hàm số trên một ĐOẠN, ta so sánh giá trị tại?',
            options: ['chỉ hai đầu mút', 'chỉ điểm y′ = 0', 'điểm y′ = 0 và hai đầu mút', 'một điểm bất kỳ'], answer: 'điểm y′ = 0 và hai đầu mút',
            explain: 'Trên đoạn [a ; b]: tính giá trị tại các điểm y′ = 0 trong đoạn và tại hai đầu a, b rồi so sánh.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-chart-area', title: 'Với hàm bậc hai',
              body: 'GTLN/GTNN đạt tại ĐỈNH parabol (x = −b/(2a)). a > 0 có GTNN; a < 0 có GTLN.' },
            { icon: 'fa-ruler', title: 'Trên một đoạn [a ; b]',
              body: 'Tính y tại các điểm y′ = 0 (trong đoạn) và tại hai đầu a, b. So sánh: lớn nhất là GTLN, nhỏ nhất là GTNN.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ GTLN – GTNN',
          cards: [
            { icon: 'fa-arrows-up-down', title: 'Khái niệm',
              body: 'GTLN (max) là giá trị lớn nhất hàm đạt được; GTNN (min) là giá trị nhỏ nhất — trên tập xác định hoặc trên một đoạn cho trước.' },
            { icon: 'fa-chart-area', title: 'Hàm bậc hai',
              body: 'y = ax² + bx + c đạt GTLN/GTNN tại đỉnh x = −b/(2a). Bài toán thực tế (diện tích, lợi nhuận) thường quy về dạng này.' },
            { icon: 'fa-square-root-variable', title: 'Dùng đạo hàm trên đoạn',
              body: 'Bước 1: tính y′, giải y′ = 0 tìm điểm tới hạn trong đoạn. Bước 2: tính y tại các điểm đó và hai đầu mút. Bước 3: so sánh chọn max/min.' },
            { icon: 'fa-lightbulb', title: 'Bài toán tối ưu',
              body: 'Lập hàm mục tiêu theo một biến, xác định miền, rồi tìm GTLN/GTNN. VD: hàng rào có chu vi cố định, tìm kích thước cho diện tích lớn nhất.' }
          ],
          examples: [
            { q: 'GTNN của y = x² − 2x + 3.', sol: 'Đỉnh x = 1 → y = 1 − 2 + 3 = 2. GTNN = 2.' },
            { q: 'GTLN của y = −x² + 6x trên ℝ.', sol: 'Đỉnh x = 3 → y = −9 + 18 = 9. GTLN = 9.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Hàm bậc hai: GTLN/GTNN tại đỉnh x = −b/(2a).',
          'a > 0 → có GTNN; a < 0 → có GTLN.',
          'Trên đoạn: so giá trị tại điểm y′ = 0 và hai đầu mút.',
          'Bài toán tối ưu → lập hàm mục tiêu rồi tìm max/min.'
        ],
        formula: 'Hàm bậc hai: cực trị tại x = −b/(2a)   |   Trên đoạn: so y tại y′=0 và 2 đầu mút',
        tip: 'Với parabol, thay thẳng x = −b/(2a) vào để tính GTLN/GTNN — nhanh hơn lập bảng biến thiên.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'GTNN của y = x² là?', options: ['−1', '0', '1', 'không có'], answer: '0' },
          { id: 'd2', type: 'fill', question: 'GTLN của y = −x² + 9 là? (nhập số)', answer: '9' },
          { id: 'd3', type: 'mcq', question: 'Hàm y = x² + 1 đạt GTNN tại x = ?', options: ['−1', '0', '1', '2'], answer: '0' },
          { id: 'd4', type: 'fill', question: 'GTNN của y = x² − 2x + 3 (tại đỉnh) là? (nhập số)', answer: '2' },
          { id: 'd5', type: 'mcq', question: 'Hàm bậc hai đạt GTLN khi hệ số a?', options: ['a > 0', 'a < 0', 'a = 0', 'a = 1'], answer: 'a < 0' },
          { id: 'd6', type: 'fill', question: 'GTLN của y = −x² + 6x tại đỉnh là? (nhập số)', answer: '9' },
          { id: 'd7', type: 'mcq', question: 'GTLN/GTNN của hàm bậc hai đạt tại?', options: ['đỉnh parabol', 'giao Oy', 'giao Ox', 'gốc tọa độ'], answer: 'đỉnh parabol' },
          { id: 'd8', type: 'fill', question: 'GTNN của y = x² + 4 là? (nhập số)', answer: '4' }
        ]
      }
    },

    {
      id: 'ql_11',
      index: 11,
      title: 'Hệ thức lượng trong tam giác',
      subtitle: 'Định lý Pytago và tỉ số lượng giác',
      topic_tag: 'Định lượng · Hình học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về hệ thức lượng.',
        questions: [
          { id: 't1', type: 'fill', question: 'Tam giác vuông có hai cạnh góc vuông là 3 và 4. Độ dài cạnh huyền bằng bao nhiêu? (nhập số)',
            answer: '5', explain: 'Pytago: c = √(3² + 4²) = √25 = 5.' },
          { id: 't2', type: 'mcq', question: 'Trong tam giác vuông, sin của một góc nhọn bằng?',
            options: ['đối / huyền', 'kề / huyền', 'đối / kề', 'huyền / đối'], answer: 'đối / huyền',
            explain: 'sin = cạnh đối / cạnh huyền; cos = kề/huyền; tan = đối/kề.' },
          { id: 't3', type: 'mcq', question: 'Định lý Pytago: trong tam giác vuông, bình phương cạnh huyền bằng?',
            options: ['tổng bình phương hai cạnh góc vuông', 'hiệu hai cạnh góc vuông', 'tích hai cạnh', 'nửa tổng hai cạnh'], answer: 'tổng bình phương hai cạnh góc vuông',
            explain: 'c² = a² + b² (c là cạnh huyền).' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-ruler-combined', title: 'Định lý Pytago',
              body: 'Tam giác vuông: <code>c² = a² + b²</code> (c cạnh huyền). Dùng tìm cạnh còn lại khi biết hai cạnh.' },
            { icon: 'fa-wave-square', title: 'Tỉ số lượng giác',
              body: '<code>sin = đối/huyền</code>, <code>cos = kề/huyền</code>, <code>tan = đối/kề</code>. Nhớ “sin đi học, cos không hư, tan đoàn kết”.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ hệ thức lượng',
          cards: [
            { icon: 'fa-ruler-combined', title: 'Định lý Pytago',
              body: 'Trong tam giác vuông: c² = a² + b². Đảo lại, nếu c² = a² + b² thì tam giác vuông. VD 3-4-5, 6-8-10 là bộ ba Pytago.' },
            { icon: 'fa-wave-square', title: 'Tỉ số lượng giác góc nhọn',
              body: 'sin α = đối/huyền; cos α = kề/huyền; tan α = đối/kề; cot α = kề/đối. Áp dụng cho góc nhọn trong tam giác vuông.' },
            { icon: 'fa-star', title: 'Giá trị đặc biệt',
              body: 'sin30°=1/2, sin45°=√2/2, sin60°=√3/2. cos ngược lại. tan45°=1. Nhớ để tính nhanh không cần máy.' },
            { icon: 'fa-triangle-exclamation', title: 'Định lý sin & cos',
              body: 'Định lý cos: a² = b² + c² − 2bc·cosA (tam giác bất kì). Định lý sin: a/sinA = b/sinB = c/sinC. Dùng cho tam giác thường.' }
          ],
          examples: [
            { q: 'Tam giác vuông cạnh góc vuông 6 và 8. Cạnh huyền?', sol: '√(36 + 64) = √100 = 10.' },
            { q: 'sin30° bằng bao nhiêu?', sol: 'sin30° = 1/2 = 0,5.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Pytago: c² = a² + b² (c cạnh huyền).',
          'sin = đối/huyền, cos = kề/huyền, tan = đối/kề.',
          'Giá trị đặc biệt: sin30°=1/2, sin45°=√2/2, sin60°=√3/2, tan45°=1.',
          'Tam giác thường: định lý cos a² = b² + c² − 2bc·cosA.'
        ],
        formula: 'c² = a² + b²   |   sin = đối/huyền, cos = kề/huyền, tan = đối/kề',
        tip: 'Gặp bộ số 3-4-5, 6-8-10, 5-12-13 là nhận ra tam giác vuông ngay, khỏi tính căn.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'fill', question: 'Tam giác vuông cạnh góc vuông 6 và 8. Cạnh huyền? (nhập số)', answer: '10' },
          { id: 'd2', type: 'mcq', question: 'cos của góc nhọn bằng?', options: ['đối/huyền', 'kề/huyền', 'đối/kề', 'kề/đối'], answer: 'kề/huyền' },
          { id: 'd3', type: 'fill', question: 'Tam giác vuông có cạnh huyền 13, một cạnh góc vuông 5. Cạnh kia? (nhập số)', answer: '12' },
          { id: 'd4', type: 'mcq', question: 'tan của góc nhọn bằng?', options: ['đối/huyền', 'kề/huyền', 'đối/kề', 'huyền/kề'], answer: 'đối/kề' },
          { id: 'd5', type: 'mcq', question: 'sin 30° bằng?', options: ['1/2', '√2/2', '√3/2', '1'], answer: '1/2' },
          { id: 'd6', type: 'fill', question: 'Tam giác vuông hai cạnh góc vuông đều 6. Bình phương cạnh huyền = ? (nhập số)', answer: '72' },
          { id: 'd7', type: 'mcq', question: 'tan 45° bằng?', options: ['0', '1', '√2', '√3'], answer: '1' },
          { id: 'd8', type: 'mcq', question: 'Bộ ba nào là bộ ba Pytago?', options: ['2-3-4', '3-4-5', '4-5-6', '5-6-7'], answer: '3-4-5' }
        ]
      }
    },

    {
      id: 'ql_12',
      index: 12,
      title: 'Đường tròn',
      subtitle: 'Bán kính, chu vi, diện tích và các yếu tố',
      topic_tag: 'Định lượng · Hình học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về đường tròn.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Chu vi của đường tròn bán kính R được tính bằng công thức nào?',
            options: ['πR', '2πR', 'πR²', '2πR²'], answer: '2πR',
            explain: 'Chu vi C = 2πR = πd (d là đường kính).' },
          { id: 't2', type: 'fill', question: 'Diện tích hình tròn bán kính R = 5 là S = πR². Hệ số đứng trước π là bao nhiêu? (nhập số)',
            answer: '25', explain: 'S = πR² = π×5² = 25π → hệ số là 25.' },
          { id: 't3', type: 'mcq', question: 'Đường kính của đường tròn bằng?',
            options: ['bán kính', '2 lần bán kính', 'nửa bán kính', 'π lần bán kính'], answer: '2 lần bán kính',
            explain: 'Đường kính d = 2R.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-circle', title: 'Chu vi & diện tích',
              body: 'Chu vi <code>C = 2πR</code> (= πd). Diện tích <code>S = πR²</code>. Đường kính d = 2R. Lấy π ≈ 3,14.' },
            { icon: 'fa-circle-notch', title: 'Các yếu tố',
              body: 'Tâm, bán kính R, đường kính d = 2R. Dây cung nối 2 điểm trên đường tròn; cung là phần đường tròn giữa 2 điểm.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ đường tròn',
          cards: [
            { icon: 'fa-circle-dot', title: 'Đường tròn & các yếu tố',
              body: 'Đường tròn tâm O bán kính R: tập hợp điểm cách O một khoảng R. Đường kính d = 2R là dây cung lớn nhất, đi qua tâm.' },
            { icon: 'fa-ruler', title: 'Chu vi',
              body: 'C = 2πR = πd. VD R = 7 → C = 2π×7 = 14π ≈ 43,96.' },
            { icon: 'fa-square', title: 'Diện tích',
              body: 'S = πR². VD R = 3 → S = 9π ≈ 28,26. Tăng bán kính k lần → diện tích tăng k² lần.' },
            { icon: 'fa-slice', title: 'Cung, dây và góc',
              body: 'Dây cung nối 2 điểm trên đường tròn. Góc ở tâm chắn cung; độ dài cung tỉ lệ với số đo góc ở tâm.' }
          ],
          examples: [
            { q: 'Đường tròn R = 10. Tính chu vi (theo π).', sol: 'C = 2π×10 = 20π.' },
            { q: 'Hình tròn R = 6. Diện tích (theo π)?', sol: 'S = π×6² = 36π.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Chu vi C = 2πR = πd; đường kính d = 2R.',
          'Diện tích S = πR².',
          'Bán kính tăng k lần → chu vi tăng k lần, diện tích tăng k² lần.',
          'Lấy π ≈ 3,14 khi tính số cụ thể.'
        ],
        formula: 'C = 2πR   |   S = πR²   |   d = 2R',
        tip: 'Đề HSA thường để đáp án theo π (20π, 36π…) — đừng nhân π ra vội, giữ theo π cho gọn.'
      },
      drill: {
        time_seconds: 75,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Công thức chu vi đường tròn?', options: ['πR', '2πR', 'πR²', 'R²'], answer: '2πR' },
          { id: 'd2', type: 'mcq', question: 'Công thức diện tích hình tròn?', options: ['2πR', 'πR²', 'πd', 'R²'], answer: 'πR²' },
          { id: 'd3', type: 'fill', question: 'Đường tròn có đường kính 10 thì bán kính R = ? (nhập số)', answer: '5' },
          { id: 'd4', type: 'fill', question: 'Hình tròn R = 4, diện tích S = kπ. Giá trị k = ? (nhập số)', answer: '16' },
          { id: 'd5', type: 'fill', question: 'Đường tròn R = 3, chu vi C = kπ. Giá trị k = ? (nhập số)', answer: '6' },
          { id: 'd6', type: 'mcq', question: 'Đường kính bằng?', options: ['R', '2R', 'R/2', 'πR'], answer: '2R' },
          { id: 'd7', type: 'mcq', question: 'Dây cung lớn nhất của đường tròn là?', options: ['bán kính', 'đường kính', 'cung', 'tiếp tuyến'], answer: 'đường kính' },
          { id: 'd8', type: 'fill', question: 'Bán kính tăng 2 lần thì diện tích tăng mấy lần? (nhập số)', answer: '4' }
        ]
      }
    },

    {
      id: 'ql_13',
      index: 13,
      title: 'Khối & thể tích',
      subtitle: 'Thể tích hình hộp, lăng trụ, chóp, cầu',
      topic_tag: 'Định lượng · Hình học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về thể tích khối.',
        questions: [
          { id: 't1', type: 'fill', question: 'Hình lập phương có cạnh bằng 3. Thể tích V = a³ bằng bao nhiêu? (nhập số)',
            answer: '27', explain: 'V = a³ = 3³ = 27.' },
          { id: 't2', type: 'mcq', question: 'Thể tích hình hộp chữ nhật được tính bằng?',
            options: ['dài × rộng × cao', 'dài + rộng + cao', '2(dài + rộng)', 'dài × rộng'], answer: 'dài × rộng × cao',
            explain: 'V = a × b × c (ba kích thước).' },
          { id: 't3', type: 'mcq', question: 'Thể tích hình cầu bán kính R được tính bằng công thức nào?',
            options: ['(4/3)πR³', 'πR²', '2πR', '(1/3)πR³'], answer: '(4/3)πR³',
            explain: 'Thể tích hình cầu V = (4/3)πR³.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-cube', title: 'Khối hộp & lăng trụ',
              body: 'Hộp chữ nhật: <code>V = dài × rộng × cao</code>. Lập phương: <code>V = a³</code>. Lăng trụ/hình trụ: <code>V = Sđáy × chiều cao</code>.' },
            { icon: 'fa-cone', title: 'Chóp & cầu',
              body: 'Hình chóp/nón: <code>V = (1/3)·Sđáy·h</code>. Hình cầu: <code>V = (4/3)πR³</code>.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ thể tích khối',
          cards: [
            { icon: 'fa-cube', title: 'Hình hộp chữ nhật & lập phương',
              body: 'Hộp chữ nhật: V = a·b·c. Lập phương (a = b = c): V = a³. Diện tích toàn phần hộp = 2(ab + bc + ca).' },
            { icon: 'fa-square', title: 'Lăng trụ & hình trụ',
              body: 'Thể tích = diện tích đáy × chiều cao: V = Sđáy·h. Hình trụ: V = πR²·h (đáy là hình tròn).' },
            { icon: 'fa-cone', title: 'Hình chóp & hình nón',
              body: 'V = (1/3)·Sđáy·h — bằng 1/3 lăng trụ/trụ cùng đáy và chiều cao. Hình nón: V = (1/3)πR²·h.' },
            { icon: 'fa-globe', title: 'Hình cầu',
              body: 'Thể tích V = (4/3)πR³; diện tích mặt cầu S = 4πR². Bán kính tăng k lần → thể tích tăng k³ lần.' }
          ],
          examples: [
            { q: 'Hộp chữ nhật 2×3×5. Thể tích?', sol: 'V = 2×3×5 = 30.' },
            { q: 'Hình trụ R = 2, h = 5. Thể tích (theo π)?', sol: 'V = π·2²·5 = 20π.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Hộp chữ nhật: V = dài × rộng × cao; lập phương V = a³.',
          'Lăng trụ/trụ: V = Sđáy × h; hình trụ V = πR²h.',
          'Chóp/nón: V = (1/3)·Sđáy·h.',
          'Cầu: V = (4/3)πR³; mặt cầu S = 4πR².'
        ],
        formula: 'V_hộp = a·b·c   |   V_trụ = πR²h   |   V_chóp = (1/3)Sđáy·h   |   V_cầu = (4/3)πR³',
        tip: 'Chóp/nón luôn có hệ số 1/3 — dấu hiệu nhận biết nhanh so với lăng trụ/trụ cùng đáy.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'fill', question: 'Lập phương cạnh 2, thể tích V = ? (nhập số)', answer: '8' },
          { id: 'd2', type: 'fill', question: 'Hộp chữ nhật 2×3×4, thể tích V = ? (nhập số)', answer: '24' },
          { id: 'd3', type: 'mcq', question: 'Thể tích hình cầu bán kính R?', options: ['(4/3)πR³', 'πR²', '4πR²', '(1/3)πR³'], answer: '(4/3)πR³' },
          { id: 'd4', type: 'mcq', question: 'Thể tích hình chóp?', options: ['Sđáy·h', '(1/3)Sđáy·h', '2Sđáy·h', 'Sđáy + h'], answer: '(1/3)Sđáy·h' },
          { id: 'd5', type: 'fill', question: 'Hình trụ R = 3, h = 2, thể tích V = kπ. Giá trị k = ? (nhập số)', answer: '18' },
          { id: 'd6', type: 'fill', question: 'Lập phương cạnh 4, thể tích V = ? (nhập số)', answer: '64' },
          { id: 'd7', type: 'mcq', question: 'Diện tích mặt cầu bán kính R?', options: ['4πR²', 'πR²', '(4/3)πR³', '2πR'], answer: '4πR²' },
          { id: 'd8', type: 'fill', question: 'Bán kính hình cầu tăng 2 lần thì thể tích tăng mấy lần? (nhập số)', answer: '8' }
        ]
      }
    },

    {
      id: 'ql_14',
      index: 14,
      title: 'Tọa độ phẳng Oxy',
      subtitle: 'Điểm, khoảng cách, trung điểm và đường thẳng',
      topic_tag: 'Định lượng · Hình học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về tọa độ phẳng.',
        questions: [
          { id: 't1', type: 'fill', question: 'Khoảng cách từ gốc tọa độ O đến điểm A(3 ; 4) bằng bao nhiêu? (nhập số)',
            answer: '5', explain: 'OA = √(3² + 4²) = √25 = 5.' },
          { id: 't2', type: 'mcq', question: 'Trung điểm của đoạn AB với A(0 ; 0), B(4 ; 6) có tọa độ là?',
            options: ['(2 ; 3)', '(4 ; 6)', '(1 ; 2)', '(3 ; 2)'], answer: '(2 ; 3)',
            explain: 'Trung điểm = ((0+4)/2 ; (0+6)/2) = (2 ; 3).' },
          { id: 't3', type: 'mcq', question: 'Trong mặt phẳng Oxy, phương trình một đường thẳng có dạng nào?',
            options: ['y = ax + b', 'x² + y² = R²', 'y = ax²', 'xy = k'], answer: 'y = ax + b',
            explain: 'Đường thẳng có dạng y = ax + b (hoặc ax + by + c = 0). x²+y²=R² là đường tròn.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-ruler-horizontal', title: 'Khoảng cách & trung điểm',
              body: 'Khoảng cách: <code>AB = √((x₂−x₁)² + (y₂−y₁)²)</code>. Trung điểm: <code>M = ((x₁+x₂)/2 ; (y₁+y₂)/2)</code>.' },
            { icon: 'fa-chart-line', title: 'Đường thẳng',
              body: 'Dạng y = ax + b (a: hệ số góc). Đường tròn tâm O bán kính R: x² + y² = R².' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ tọa độ phẳng',
          cards: [
            { icon: 'fa-location-crosshairs', title: 'Hệ trục Oxy',
              body: 'Mỗi điểm xác định bởi cặp (x ; y): x là hoành độ, y là tung độ. Gốc O(0 ; 0). Điểm trên Ox có y = 0; trên Oy có x = 0.' },
            { icon: 'fa-ruler-horizontal', title: 'Khoảng cách hai điểm',
              body: 'AB = √((x₂−x₁)² + (y₂−y₁)²). Đây là hệ quả của định lý Pytago áp dụng trong hệ tọa độ.' },
            { icon: 'fa-dot-circle', title: 'Trung điểm đoạn thẳng',
              body: 'Trung điểm M của AB: M = ((x₁+x₂)/2 ; (y₁+y₂)/2). Là điểm chính giữa đoạn AB.' },
            { icon: 'fa-chart-line', title: 'Đường thẳng & đường tròn',
              body: 'Đường thẳng: y = ax + b (a hệ số góc). Đường tròn tâm I(a ; b) bán kính R: (x−a)² + (y−b)² = R².' }
          ],
          examples: [
            { q: 'Tính khoảng cách A(1 ; 2) và B(4 ; 6).', sol: '√((4−1)² + (6−2)²) = √(9+16) = 5.' },
            { q: 'Trung điểm của A(2 ; 4) và B(6 ; 8)?', sol: '((2+6)/2 ; (4+8)/2) = (4 ; 6).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Điểm trong Oxy: (x ; y) — x hoành độ, y tung độ.',
          'Khoảng cách AB = √((x₂−x₁)² + (y₂−y₁)²).',
          'Trung điểm M = ((x₁+x₂)/2 ; (y₁+y₂)/2).',
          'Đường thẳng y = ax + b; đường tròn (x−a)²+(y−b)² = R².'
        ],
        formula: 'AB = √((x₂−x₁)²+(y₂−y₁)²)   |   M = ((x₁+x₂)/2 ; (y₁+y₂)/2)',
        tip: 'Nhớ công thức khoảng cách chính là Pytago — hiệu tọa độ x và y là hai cạnh góc vuông.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'fill', question: 'Khoảng cách từ O đến A(6 ; 8)? (nhập số)', answer: '10' },
          { id: 'd2', type: 'mcq', question: 'Trung điểm của A(0;0) và B(6;8)?', options: ['(3 ; 4)', '(6 ; 8)', '(2 ; 3)', '(4 ; 3)'], answer: '(3 ; 4)' },
          { id: 'd3', type: 'fill', question: 'Khoảng cách A(1;1) và B(4;5)? (nhập số)', answer: '5' },
          { id: 'd4', type: 'mcq', question: 'Hoành độ của điểm A(3 ; 7) là?', options: ['3', '7', '10', '4'], answer: '3' },
          { id: 'd5', type: 'mcq', question: 'Điểm nằm trên trục Oy có?', options: ['x = 0', 'y = 0', 'x = y', 'x = 1'], answer: 'x = 0' },
          { id: 'd6', type: 'fill', question: 'Trung điểm của A(2;2) và B(8;2) có hoành độ là? (nhập số)', answer: '5' },
          { id: 'd7', type: 'mcq', question: 'Phương trình x² + y² = 25 là?', options: ['đường thẳng', 'đường tròn', 'parabol', 'điểm'], answer: 'đường tròn' },
          { id: 'd8', type: 'fill', question: 'Khoảng cách từ O đến A(0 ; 9)? (nhập số)', answer: '9' }
        ]
      }
    },

    {
      id: 'ql_15',
      index: 15,
      title: 'Tọa độ không gian Oxyz',
      subtitle: 'Điểm, vectơ và khoảng cách trong không gian',
      topic_tag: 'Định lượng · Hình học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về tọa độ không gian.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Trong không gian Oxyz, mỗi điểm được xác định bởi bao nhiêu tọa độ?',
            options: ['2', '3', '4', '1'], answer: '3',
            explain: 'Mỗi điểm trong không gian có ba tọa độ (x ; y ; z).' },
          { id: 't2', type: 'fill', question: 'Khoảng cách từ gốc O đến điểm A(2 ; 3 ; 6) bằng bao nhiêu? (nhập số)',
            answer: '7', explain: 'OA = √(2² + 3² + 6²) = √(4+9+36) = √49 = 7.' },
          { id: 't3', type: 'mcq', question: 'Một vectơ trong không gian Oxyz có bao nhiêu thành phần?',
            options: ['1', '2', '3', '4'], answer: '3',
            explain: 'Vectơ trong không gian có ba thành phần (a ; b ; c).' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-cube', title: 'Điểm trong không gian',
              body: 'Mỗi điểm A(x ; y ; z) xác định bởi 3 tọa độ. Ba trục Ox, Oy, Oz vuông góc từng đôi một, gốc O(0;0;0).' },
            { icon: 'fa-ruler', title: 'Khoảng cách',
              body: 'OA = √(x² + y² + z²). Hai điểm: <code>AB = √((x₂−x₁)²+(y₂−y₁)²+(z₂−z₁)²)</code>.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ tọa độ không gian',
          cards: [
            { icon: 'fa-cube', title: 'Hệ trục Oxyz',
              body: 'Ba trục Ox, Oy, Oz đôi một vuông góc. Mỗi điểm A(x ; y ; z). Đây là mở rộng của mặt phẳng Oxy thêm chiều thứ ba z (chiều cao).' },
            { icon: 'fa-arrow-right', title: 'Vectơ & tọa độ',
              body: 'Vectơ AB = (x_B−x_A ; y_B−y_A ; z_B−z_A). Độ dài vectơ |AB| = √(tổng bình phương ba thành phần).' },
            { icon: 'fa-ruler', title: 'Khoảng cách hai điểm',
              body: 'AB = √((x₂−x₁)² + (y₂−y₁)² + (z₂−z₁)²). Mở rộng công thức trong mặt phẳng thêm thành phần z.' },
            { icon: 'fa-dot-circle', title: 'Ứng dụng',
              body: 'Trung điểm M = ((x₁+x₂)/2 ; (y₁+y₂)/2 ; (z₁+z₂)/2). Tính độ dài đoạn thẳng, xác định vị trí điểm trong không gian.' }
          ],
          examples: [
            { q: 'Khoảng cách O đến A(1 ; 2 ; 2).', sol: '√(1+4+4) = √9 = 3.' },
            { q: 'Trung điểm của A(0;0;0) và B(2;4;6)?', sol: '(1 ; 2 ; 3).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Điểm trong không gian: A(x ; y ; z) — 3 tọa độ.',
          'Khoảng cách OA = √(x² + y² + z²).',
          'AB = √((x₂−x₁)² + (y₂−y₁)² + (z₂−z₁)²).',
          'Trung điểm = trung bình cộng từng tọa độ.'
        ],
        formula: 'OA = √(x²+y²+z²)   |   AB = √(Δx²+Δy²+Δz²)',
        tip: 'Công thức không gian y hệt mặt phẳng, chỉ thêm thành phần z — nhớ một là suy ra cái kia.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Điểm trong không gian có mấy tọa độ?', options: ['2', '3', '4', '1'], answer: '3' },
          { id: 'd2', type: 'fill', question: 'Khoảng cách từ O đến A(1 ; 2 ; 2)? (nhập số)', answer: '3' },
          { id: 'd3', type: 'fill', question: 'Khoảng cách từ O đến A(2 ; 3 ; 6)? (nhập số)', answer: '7' },
          { id: 'd4', type: 'mcq', question: 'Ba trục trong Oxyz đôi một?', options: ['song song', 'vuông góc', 'trùng nhau', 'cắt xiên'], answer: 'vuông góc' },
          { id: 'd5', type: 'fill', question: 'Khoảng cách từ O đến A(0 ; 0 ; 5)? (nhập số)', answer: '5' },
          { id: 'd6', type: 'mcq', question: 'Trung điểm của A(0;0;0) và B(2;4;6)?', options: ['(1 ; 2 ; 3)', '(2 ; 4 ; 6)', '(1 ; 1 ; 1)', '(3 ; 2 ; 1)'], answer: '(1 ; 2 ; 3)' },
          { id: 'd7', type: 'fill', question: 'Khoảng cách từ O đến A(6 ; 6 ; 7)? (nhập số)', answer: '11' },
          { id: 'd8', type: 'mcq', question: 'Vectơ trong không gian có mấy thành phần?', options: ['2', '3', '4', '1'], answer: '3' }
        ]
      }
    },

    {
      id: 'ql_16',
      index: 16,
      title: 'Tổ hợp – chỉnh hợp',
      subtitle: 'Quy tắc đếm, hoán vị, chỉnh hợp và tổ hợp',
      topic_tag: 'Định lượng · Thống kê & Xác suất',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về tổ hợp – chỉnh hợp.',
        questions: [
          { id: 't1', type: 'fill', question: 'Số cách xếp 3 người vào 3 ghế (tính 3!) bằng bao nhiêu? (nhập số)',
            answer: '6', explain: '3! = 3×2×1 = 6.' },
          { id: 't2', type: 'mcq', question: 'Số cách chọn 2 người trong 4 người (KHÔNG phân biệt thứ tự) là tổ hợp C(4,2). Giá trị bằng?',
            options: ['4', '6', '8', '12'], answer: '6',
            explain: 'C(4,2) = 4!/(2!·2!) = 6.' },
          { id: 't3', type: 'mcq', question: 'Khi THỨ TỰ sắp xếp là quan trọng, ta dùng khái niệm nào?',
            options: ['tổ hợp', 'chỉnh hợp', 'giai thừa', 'trung bình'], answer: 'chỉnh hợp',
            explain: 'Có thứ tự → chỉnh hợp (A); không thứ tự → tổ hợp (C).' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-arrow-down-1-9', title: 'Quy tắc đếm & hoán vị',
              body: 'Quy tắc CỘNG (hoặc … hoặc), quy tắc NHÂN (và … và). Hoán vị n phần tử: <code>Pₙ = n!</code> (n! = n×(n−1)×…×1).' },
            { icon: 'fa-shuffle', title: 'Chỉnh hợp & tổ hợp',
              body: 'Chỉnh hợp (CÓ thứ tự): A(n,k) = n!/(n−k)!. Tổ hợp (KHÔNG thứ tự): <code>C(n,k) = n!/[k!·(n−k)!]</code>.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ tổ hợp – chỉnh hợp',
          cards: [
            { icon: 'fa-plus', title: 'Quy tắc cộng & nhân',
              body: 'Quy tắc cộng: công việc có m cách này HOẶC n cách kia (rời nhau) → m + n cách. Quy tắc nhân: gồm hai công đoạn liên tiếp, m cách và n cách → m × n cách.' },
            { icon: 'fa-arrow-down-1-9', title: 'Hoán vị & giai thừa',
              body: 'Hoán vị của n phần tử (sắp xếp tất cả) = n! = n×(n−1)×…×1. VD 3! = 6, 4! = 24, 5! = 120.' },
            { icon: 'fa-list-ol', title: 'Chỉnh hợp (có thứ tự)',
              body: 'Chọn k trong n phần tử CÓ để ý thứ tự: A(n,k) = n!/(n−k)!. VD A(4,2) = 12 (chọn 2 trong 4 có thứ tự).' },
            { icon: 'fa-object-group', title: 'Tổ hợp (không thứ tự)',
              body: 'Chọn k trong n phần tử KHÔNG để ý thứ tự: C(n,k) = n!/[k!(n−k)!]. VD C(4,2) = 6. Luôn có C(n,k) = C(n, n−k).' }
          ],
          examples: [
            { q: 'Có bao nhiêu cách xếp 4 bạn thành hàng?', sol: '4! = 24 cách.' },
            { q: 'Chọn 3 trong 5 học sinh đi trực (không thứ tự)?', sol: 'C(5,3) = 10.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Quy tắc cộng (hoặc): m + n; quy tắc nhân (và): m × n.',
          'Hoán vị n phần tử: Pₙ = n!.',
          'Chỉnh hợp (có thứ tự): A(n,k) = n!/(n−k)!.',
          'Tổ hợp (không thứ tự): C(n,k) = n!/[k!(n−k)!].'
        ],
        formula: 'Pₙ = n!   |   A(n,k) = n!/(n−k)!   |   C(n,k) = n!/[k!(n−k)!]',
        tip: 'Hỏi “thứ tự có quan trọng không?” — CÓ dùng chỉnh hợp A, KHÔNG dùng tổ hợp C.'
      },
      drill: {
        time_seconds: 85,
        questions: [
          { id: 'd1', type: 'fill', question: 'Tính 4! (nhập số)', answer: '24' },
          { id: 'd2', type: 'fill', question: 'Tính 5! (nhập số)', answer: '120' },
          { id: 'd3', type: 'mcq', question: 'C(4,2) bằng?', options: ['4', '6', '8', '12'], answer: '6' },
          { id: 'd4', type: 'fill', question: 'Số cách xếp 3 người thành hàng = 3! = ? (nhập số)', answer: '6' },
          { id: 'd5', type: 'mcq', question: 'Chọn CÓ thứ tự dùng?', options: ['tổ hợp', 'chỉnh hợp', 'hoán vị', 'giai thừa'], answer: 'chỉnh hợp' },
          { id: 'd6', type: 'mcq', question: 'Chọn KHÔNG thứ tự dùng?', options: ['tổ hợp', 'chỉnh hợp', 'hoán vị', 'xác suất'], answer: 'tổ hợp' },
          { id: 'd7', type: 'fill', question: 'C(5,2) bằng bao nhiêu? (nhập số)', answer: '10' },
          { id: 'd8', type: 'mcq', question: 'Có 3 áo, 2 quần. Số bộ đồ (quy tắc nhân)?', options: ['5', '6', '8', '9'], answer: '6' }
        ]
      }
    },

    {
      id: 'ql_17',
      index: 17,
      title: 'Xác suất cơ bản',
      subtitle: 'Xác suất của biến cố và cách tính',
      topic_tag: 'Định lượng · Thống kê & Xác suất',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về xác suất.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Xác suất của một biến cố được tính bằng?',
            options: ['số kết quả thuận lợi / tổng số kết quả', 'tổng số kết quả / số thuận lợi', 'số thuận lợi × tổng', 'tổng − thuận lợi'], answer: 'số kết quả thuận lợi / tổng số kết quả',
            explain: 'P(A) = số kết quả thuận lợi cho A / tổng số kết quả có thể.' },
          { id: 't2', type: 'fill', question: 'Tung một con xúc xắc cân đối. Xác suất ra mặt 6 là 1/n. Giá trị của n là bao nhiêu? (nhập số)',
            answer: '6', explain: 'Có 6 mặt, 1 mặt là số 6 → P = 1/6.' },
          { id: 't3', type: 'mcq', question: 'Xác suất của một biến cố luôn nhận giá trị trong khoảng nào?',
            options: ['từ 0 đến 1', 'từ 1 đến 10', 'từ −1 đến 1', 'bất kỳ số nào'], answer: 'từ 0 đến 1',
            explain: '0 ≤ P(A) ≤ 1. P = 0: không thể xảy ra; P = 1: chắc chắn xảy ra.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-percent', title: 'Công thức xác suất',
              body: '<code>P(A) = (số kết quả thuận lợi) / (tổng số kết quả)</code>. Luôn có 0 ≤ P(A) ≤ 1.' },
            { icon: 'fa-dice', title: 'Ý nghĩa',
              body: 'P = 0: biến cố không thể xảy ra. P = 1: biến cố chắc chắn. P càng gần 1 càng dễ xảy ra.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ xác suất',
          cards: [
            { icon: 'fa-dice', title: 'Phép thử & biến cố',
              body: 'Phép thử ngẫu nhiên: hành động có nhiều kết quả không đoán trước (tung xúc xắc, gieo đồng xu). Biến cố là tập kết quả ta quan tâm.' },
            { icon: 'fa-percent', title: 'Công thức cổ điển',
              body: 'Khi các kết quả đồng khả năng: P(A) = số kết quả thuận lợi cho A / tổng số kết quả. VD tung xúc xắc, P(ra số chẵn) = 3/6 = 1/2.' },
            { icon: 'fa-arrows-left-right', title: 'Tính chất',
              body: '0 ≤ P(A) ≤ 1. P(biến cố chắc chắn) = 1; P(biến cố không thể) = 0. P(A) + P(không A) = 1.' },
            { icon: 'fa-plus', title: 'Biến cố đối & kết hợp',
              body: 'Biến cố đối “không A” có P = 1 − P(A) — dùng khi tính “ít nhất”, “không có” thuận tiện hơn.' }
          ],
          examples: [
            { q: 'Gieo đồng xu, xác suất ra mặt ngửa?', sol: '1/2 (1 trong 2 kết quả đồng khả năng).' },
            { q: 'Xúc xắc, xác suất ra số lớn hơn 4?', sol: 'Các số 5, 6 → 2/6 = 1/3.' }
          ]
        }
      },
      notes: {
        key_points: [
          'P(A) = số kết quả thuận lợi / tổng số kết quả.',
          '0 ≤ P(A) ≤ 1; P = 0 không thể, P = 1 chắc chắn.',
          'P(A) + P(không A) = 1 (biến cố đối).',
          'Áp dụng khi các kết quả đồng khả năng.'
        ],
        formula: 'P(A) = (thuận lợi)/(tổng)   |   P(không A) = 1 − P(A)',
        tip: 'Tính “ít nhất một” thường dễ hơn qua biến cố đối: 1 − P(không có cái nào).'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Công thức xác suất P(A) =?', options: ['thuận lợi/tổng', 'tổng/thuận lợi', 'thuận lợi×tổng', 'tổng−thuận lợi'], answer: 'thuận lợi/tổng' },
          { id: 'd2', type: 'fill', question: 'Gieo đồng xu, xác suất mặt ngửa là 1/n. n = ? (nhập số)', answer: '2' },
          { id: 'd3', type: 'mcq', question: 'Xác suất ra số chẵn khi tung xúc xắc?', options: ['1/6', '1/3', '1/2', '2/3'], answer: '1/2' },
          { id: 'd4', type: 'mcq', question: 'P của biến cố chắc chắn bằng?', options: ['0', '0,5', '1', '2'], answer: '1' },
          { id: 'd5', type: 'mcq', question: 'P của biến cố không thể xảy ra bằng?', options: ['0', '0,5', '1', '−1'], answer: '0' },
          { id: 'd6', type: 'fill', question: 'Xúc xắc: xác suất ra số 6 là 1/n. n = ? (nhập số)', answer: '6' },
          { id: 'd7', type: 'mcq', question: 'Nếu P(A) = 0,3 thì P(không A) = ?', options: ['0,3', '0,7', '1', '0'], answer: '0,7' },
          { id: 'd8', type: 'mcq', question: 'Xác suất luôn nằm trong?', options: ['[0 ; 1]', '[1 ; 10]', '[−1 ; 1]', 'bất kỳ'], answer: '[0 ; 1]' }
        ]
      }
    },

    {
      id: 'ql_18',
      index: 18,
      title: 'Thống kê mô tả',
      subtitle: 'Trung bình, trung vị, mốt và phương sai',
      topic_tag: 'Định lượng · Thống kê & Xác suất',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về thống kê mô tả.',
        questions: [
          { id: 't1', type: 'fill', question: 'Trung bình cộng của ba số 2, 4, 6 bằng bao nhiêu? (nhập số)',
            answer: '4', explain: '(2 + 4 + 6)/3 = 12/3 = 4.' },
          { id: 't2', type: 'mcq', question: 'Giá trị xuất hiện NHIỀU NHẤT trong một dãy số liệu được gọi là?',
            options: ['số trung bình', 'trung vị', 'mốt', 'phương sai'], answer: 'mốt',
            explain: 'Mốt (mode) là giá trị có tần số lớn nhất.' },
          { id: 't3', type: 'mcq', question: 'Trung vị của một dãy số liệu là?',
            options: ['giá trị đứng giữa khi đã sắp xếp', 'giá trị lớn nhất', 'tổng chia số phần tử', 'giá trị nhỏ nhất'], answer: 'giá trị đứng giữa khi đã sắp xếp',
            explain: 'Trung vị là giá trị ở chính giữa khi sắp xếp số liệu theo thứ tự.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-calculator', title: 'Ba số đo trung tâm',
              body: 'TRUNG BÌNH = tổng/số phần tử. TRUNG VỊ = giá trị đứng giữa (sau khi sắp xếp). MỐT = giá trị xuất hiện nhiều nhất.' },
            { icon: 'fa-chart-simple', title: 'Độ phân tán',
              body: 'Phương sai và độ lệch chuẩn đo mức độ phân tán của số liệu quanh giá trị trung bình. Càng lớn, số liệu càng phân tán.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ thống kê mô tả',
          cards: [
            { icon: 'fa-calculator', title: 'Số trung bình cộng',
              body: 'Bằng tổng tất cả giá trị chia cho số giá trị: x̄ = (x₁ + x₂ + … + xₙ)/n. Đại diện “trung tâm” của số liệu, nhưng nhạy với giá trị cực đoan.' },
            { icon: 'fa-ruler-horizontal', title: 'Trung vị',
              body: 'Sắp xếp số liệu tăng dần; trung vị là giá trị ở giữa (n lẻ) hoặc trung bình hai giá trị giữa (n chẵn). Ít bị ảnh hưởng bởi giá trị cực đoan.' },
            { icon: 'fa-crown', title: 'Mốt',
              body: 'Là giá trị (hoặc các giá trị) xuất hiện nhiều nhất. Một dãy có thể có một hoặc nhiều mốt, hoặc không có mốt.' },
            { icon: 'fa-chart-simple', title: 'Phương sai & độ lệch chuẩn',
              body: 'Phương sai đo trung bình bình phương độ lệch so với x̄; độ lệch chuẩn là căn bậc hai của phương sai. Cho biết số liệu tập trung hay phân tán.' }
          ],
          examples: [
            { q: 'Dãy 3, 5, 7, 9. Trung bình?', sol: '(3+5+7+9)/4 = 24/4 = 6.' },
            { q: 'Dãy 2, 2, 3, 5. Mốt là?', sol: '2 (xuất hiện nhiều nhất).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Trung bình = tổng / số phần tử.',
          'Trung vị = giá trị đứng giữa sau khi sắp xếp.',
          'Mốt = giá trị xuất hiện nhiều nhất.',
          'Phương sai/độ lệch chuẩn đo độ phân tán.'
        ],
        formula: 'x̄ = (x₁ + x₂ + … + xₙ)/n',
        tip: 'Muốn tính trung vị, luôn SẮP XẾP số liệu trước rồi mới tìm giá trị ở giữa.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'fill', question: 'Trung bình của 4, 6, 8? (nhập số)', answer: '6' },
          { id: 'd2', type: 'mcq', question: 'Giá trị xuất hiện nhiều nhất gọi là?', options: ['trung bình', 'trung vị', 'mốt', 'phương sai'], answer: 'mốt' },
          { id: 'd3', type: 'fill', question: 'Trung bình của 10 và 20? (nhập số)', answer: '15' },
          { id: 'd4', type: 'mcq', question: 'Trung vị của 1, 3, 5, 7, 9 là?', options: ['3', '5', '7', '25'], answer: '5' },
          { id: 'd5', type: 'mcq', question: 'Mốt của dãy 2, 2, 3, 4 là?', options: ['2', '3', '4', '2,75'], answer: '2' },
          { id: 'd6', type: 'fill', question: 'Trung bình của 2, 4, 6, 8? (nhập số)', answer: '5' },
          { id: 'd7', type: 'mcq', question: 'Đại lượng đo độ phân tán số liệu?', options: ['phương sai', 'trung bình', 'mốt', 'trung vị'], answer: 'phương sai' },
          { id: 'd8', type: 'mcq', question: 'Muốn tìm trung vị, đầu tiên phải?', options: ['sắp xếp số liệu', 'cộng lại', 'chia đôi', 'tìm mốt'], answer: 'sắp xếp số liệu' }
        ]
      }
    },

    {
      id: 'ql_19',
      index: 19,
      title: 'Biến cố & quy tắc đếm',
      subtitle: 'Quy tắc cộng, quy tắc nhân và ứng dụng',
      topic_tag: 'Định lượng · Thống kê & Xác suất',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về quy tắc đếm.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Quy tắc CỘNG được dùng khi nào?',
            options: ['các trường hợp rời nhau (hoặc cái này hoặc cái kia)', 'các công đoạn liên tiếp', 'chỉ có một cách', 'luôn luôn'], answer: 'các trường hợp rời nhau (hoặc cái này hoặc cái kia)',
            explain: 'Quy tắc cộng: công việc thực hiện theo phương án A HOẶC B (không đồng thời) → cộng số cách.' },
          { id: 't2', type: 'mcq', question: 'Quy tắc NHÂN được dùng khi nào?',
            options: ['gồm các công đoạn liên tiếp (và … và)', 'các trường hợp rời nhau', 'chỉ đếm một lần', 'khi có xác suất'], answer: 'gồm các công đoạn liên tiếp (và … và)',
            explain: 'Quy tắc nhân: công việc gồm nhiều công đoạn nối tiếp → nhân số cách của từng công đoạn.' },
          { id: 't3', type: 'fill', question: 'Có 2 chiếc áo và 3 chiếc quần. Số cách chọn một bộ (gồm một áo VÀ một quần) là bao nhiêu? (nhập số)',
            answer: '6', explain: 'Quy tắc nhân: 2 × 3 = 6 cách.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-plus', title: 'Quy tắc cộng',
              body: 'Công việc thực hiện theo phương án A HOẶC B (rời nhau): m cách và n cách → tổng <code>m + n</code> cách.' },
            { icon: 'fa-xmark', title: 'Quy tắc nhân',
              body: 'Công việc gồm hai công đoạn liên tiếp (A VÀ B): m cách rồi n cách → tổng <code>m × n</code> cách.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ biến cố & quy tắc đếm',
          cards: [
            { icon: 'fa-plus', title: 'Quy tắc cộng',
              body: 'Nếu một công việc có thể làm theo một trong hai phương án rời nhau (A có m cách, B có n cách) thì có m + n cách. Dấu hiệu: “HOẶC”.' },
            { icon: 'fa-xmark', title: 'Quy tắc nhân',
              body: 'Nếu một công việc gồm hai công đoạn liên tiếp (công đoạn 1 có m cách, công đoạn 2 có n cách) thì có m × n cách. Dấu hiệu: “VÀ”, “rồi”.' },
            { icon: 'fa-diagram-project', title: 'Biến cố',
              body: 'Trong bài toán xác suất, dùng quy tắc đếm để tính tổng số kết quả và số kết quả thuận lợi cho biến cố, rồi lập tỉ số.' },
            { icon: 'fa-lightbulb', title: 'Cách phân biệt',
              body: 'Hỏi: các phương án có RỜI NHAU (chỉ chọn một) → cộng; hay LIÊN TIẾP (làm hết các bước) → nhân. Đây là gốc của mọi bài đếm.' }
          ],
          examples: [
            { q: 'Đi từ A đến B có 3 đường, từ B đến C có 2 đường. Số cách đi A→C?', sol: 'Quy tắc nhân: 3 × 2 = 6.' },
            { q: 'Chọn một món: 4 món cơm HOẶC 3 món phở. Số cách?', sol: 'Quy tắc cộng: 4 + 3 = 7.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Quy tắc cộng (HOẶC — rời nhau): m + n cách.',
          'Quy tắc nhân (VÀ — liên tiếp): m × n cách.',
          'Dùng quy tắc đếm để tính tổng và số thuận lợi trong xác suất.',
          'Phân biệt: rời nhau → cộng; liên tiếp → nhân.'
        ],
        formula: 'Cộng (hoặc): m + n   |   Nhân (và): m × n',
        tip: 'Gặp “và/rồi” nghĩ tới NHÂN; gặp “hoặc” nghĩ tới CỘNG — là quyết định đúng ngay.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'fill', question: 'Có 3 áo và 4 quần. Số bộ đồ (áo và quần)? (nhập số)', answer: '12' },
          { id: 'd2', type: 'mcq', question: 'Quy tắc “hoặc … hoặc” là?', options: ['quy tắc cộng', 'quy tắc nhân', 'hoán vị', 'tổ hợp'], answer: 'quy tắc cộng' },
          { id: 'd3', type: 'mcq', question: 'Quy tắc “và … và” (liên tiếp) là?', options: ['quy tắc cộng', 'quy tắc nhân', 'chỉnh hợp', 'trung bình'], answer: 'quy tắc nhân' },
          { id: 'd4', type: 'fill', question: 'A→B có 2 đường, B→C có 5 đường. Số cách A→C? (nhập số)', answer: '10' },
          { id: 'd5', type: 'fill', question: 'Chọn 1 món: 3 món chè HOẶC 2 loại nước. Số cách? (nhập số)', answer: '5' },
          { id: 'd6', type: 'mcq', question: 'Gieo 2 con xúc xắc, tổng số kết quả?', options: ['12', '36', '6', '11'], answer: '36' },
          { id: 'd7', type: 'fill', question: 'Có 4 màu áo và 2 kiểu cổ. Số loại áo? (nhập số)', answer: '8' },
          { id: 'd8', type: 'mcq', question: 'Dấu hiệu dùng quy tắc nhân là từ?', options: ['và, rồi', 'hoặc', 'nhưng', 'vì'], answer: 'và, rồi' }
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
    },

    {
      id: 'vb_02',
      index: 2,
      title: 'Nghĩa của từ trong ngữ cảnh',
      subtitle: 'Nghĩa gốc – nghĩa chuyển và từ nhiều nghĩa',
      topic_tag: 'Định tính · Từ vựng',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về nghĩa của từ.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Từ “chân” trong “chân bàn” được dùng theo nghĩa nào?',
            options: ['nghĩa gốc', 'nghĩa chuyển', 'từ đồng âm', 'từ trái nghĩa'], answer: 'nghĩa chuyển',
            explain: '“Chân” gốc là bộ phận cơ thể; “chân bàn” là nghĩa chuyển (bộ phận đỡ phía dưới).' },
          { id: 't2', type: 'mcq', question: 'Từ “ăn” trong câu nào dưới đây dùng theo NGHĨA CHUYỂN?',
            options: ['ăn cơm', 'ăn ảnh', 'ăn sáng', 'ăn bánh'], answer: 'ăn ảnh',
            explain: '“Ăn ảnh” = lên hình đẹp (nghĩa chuyển); các câu còn lại đều là ăn thức ăn (nghĩa gốc).' },
          { id: 't3', type: 'fill', question: 'Từ nhiều nghĩa có một nghĩa gốc và các nghĩa ___ (điền 1 từ):',
            answer: 'chuyển', explain: 'Từ nhiều nghĩa = 1 nghĩa gốc + nhiều nghĩa chuyển (suy ra từ nghĩa gốc).' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-diagram-project', title: 'Nghĩa gốc & nghĩa chuyển',
              body: 'Từ nhiều nghĩa có 1 <b>nghĩa gốc</b> (nghĩa đầu tiên, cơ bản) và các <b>nghĩa chuyển</b> suy ra từ nghĩa gốc theo ẩn dụ / hoán dụ.' },
            { icon: 'fa-magnifying-glass', title: 'Dựa vào ngữ cảnh',
              body: 'Cùng một từ có thể mang nghĩa khác nhau — phải đọc CẢ CÂU (ngữ cảnh) để xác định nghĩa đúng.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ nghĩa của từ',
          cards: [
            { icon: 'fa-layer-group', title: 'Từ nhiều nghĩa',
              body: 'Là từ có một nghĩa gốc và một hoặc nhiều nghĩa chuyển. VD “mắt”: mắt người (gốc) → mắt lưới, mắt na, mắt bão (chuyển).' },
            { icon: 'fa-seedling', title: 'Nghĩa gốc',
              body: 'Là nghĩa xuất hiện đầu tiên, làm cơ sở hình thành các nghĩa khác. Thường là nghĩa cụ thể, dễ hình dung nhất.' },
            { icon: 'fa-shuffle', title: 'Nghĩa chuyển (ẩn dụ / hoán dụ)',
              body: 'Ẩn dụ: chuyển nghĩa dựa trên nét GIỐNG NHAU (chân bàn ~ chân người). Hoán dụ: dựa trên quan hệ GẦN NHAU (cả nhà = mọi người trong nhà).' },
            { icon: 'fa-magnifying-glass', title: 'Chọn nghĩa theo ngữ cảnh',
              body: 'Đọc cả câu, xác định từ đang nói về đối tượng nào rồi chọn nghĩa phù hợp. Cùng “ngọt”: đường ngọt (vị) ≠ lời nói ngọt (dễ nghe).' }
          ],
          examples: [
            { q: 'Xác định nghĩa của “mũi” trong “mũi thuyền”.', sol: 'Nghĩa chuyển — phần nhô ra phía trước (giống mũi người).' },
            { q: '“Cứng” trong “học lực cứng” nghĩa là gì?', sol: 'Nghĩa chuyển — giỏi, vững vàng (không phải cứng vật lý).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Từ nhiều nghĩa = 1 nghĩa gốc + nhiều nghĩa chuyển.',
          'Nghĩa chuyển hình thành theo ẩn dụ (giống nhau) hoặc hoán dụ (gần nhau).',
          'Xác định nghĩa phải dựa vào NGỮ CẢNH (đọc cả câu).'
        ],
        tip: 'Gặp câu hỏi “từ … mang nghĩa gì”, đọc cả câu rồi thử thay nghĩa gốc — nếu vô lý thì đó là nghĩa chuyển.'
      },
      drill: {
        time_seconds: 70,
        questions: [
          { id: 'd1', type: 'mcq', question: '“mũi” trong “mũi thuyền” dùng nghĩa?', options: ['nghĩa gốc', 'nghĩa chuyển', 'đồng âm', 'trái nghĩa'], answer: 'nghĩa chuyển' },
          { id: 'd2', type: 'mcq', question: '“ngọt” trong “lời nói ngọt” dùng nghĩa?', options: ['nghĩa gốc', 'nghĩa chuyển', 'đồng âm', 'trái nghĩa'], answer: 'nghĩa chuyển' },
          { id: 'd3', type: 'mcq', question: 'Từ nào dùng NGHĨA GỐC?', options: ['chân trời', 'chân bàn', 'chân người', 'chân núi'], answer: 'chân người' },
          { id: 'd4', type: 'fill', question: 'Từ có 1 nghĩa gốc và nhiều nghĩa chuyển gọi là từ nhiều ___ (1 từ):', answer: 'nghĩa' },
          { id: 'd5', type: 'mcq', question: '“cứng” trong “học lực cứng” là nghĩa?', options: ['nghĩa gốc', 'nghĩa chuyển', 'đồng âm', 'trái nghĩa'], answer: 'nghĩa chuyển' },
          { id: 'd6', type: 'mcq', question: 'Nghĩa của một từ phụ thuộc chủ yếu vào?', options: ['ngữ cảnh', 'số chữ cái', 'dấu câu', 'âm thanh'], answer: 'ngữ cảnh' },
          { id: 'd7', type: 'mcq', question: '“tay” trong “tay nghề” là nghĩa?', options: ['nghĩa gốc', 'nghĩa chuyển', 'đồng âm', 'trái nghĩa'], answer: 'nghĩa chuyển' },
          { id: 'd8', type: 'mcq', question: 'Từ nào dùng NGHĨA CHUYỂN?', options: ['mắt em', 'mắt lưới', 'mắt to', 'đau mắt'], answer: 'mắt lưới' }
        ]
      }
    },

    {
      id: 'vb_03',
      index: 3,
      title: 'Từ loại',
      subtitle: 'Danh từ, động từ, tính từ, đại từ và quan hệ từ',
      topic_tag: 'Định tính · Ngữ pháp',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về từ loại.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Từ “chạy” thuộc từ loại nào?',
            options: ['danh từ', 'động từ', 'tính từ', 'đại từ'], answer: 'động từ',
            explain: '“Chạy” chỉ hành động → động từ.' },
          { id: 't2', type: 'mcq', question: 'Từ “đẹp” thuộc từ loại nào?',
            options: ['danh từ', 'động từ', 'tính từ', 'quan hệ từ'], answer: 'tính từ',
            explain: '“Đẹp” chỉ đặc điểm, tính chất → tính từ.' },
          { id: 't3', type: 'mcq', question: 'Trong câu “Tôi và bạn cùng học”, từ “và” thuộc từ loại nào?',
            options: ['danh từ', 'quan hệ từ', 'đại từ', 'động từ'], answer: 'quan hệ từ',
            explain: '“Và” nối hai từ/vế câu → quan hệ từ (liên từ).' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-shapes', title: 'Ba từ loại chính',
              body: '<b>Danh từ</b> chỉ sự vật (nhà, người). <b>Động từ</b> chỉ hành động/trạng thái (chạy, yêu). <b>Tính từ</b> chỉ đặc điểm/tính chất (đẹp, cao).' },
            { icon: 'fa-link', title: 'Từ loại phụ trợ',
              body: '<b>Đại từ</b> thay thế (tôi, nó, ai). <b>Quan hệ từ</b> nối (và, nhưng, của, vì). <b>Số từ</b> chỉ số lượng (ba, năm).' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ Từ loại',
          cards: [
            { icon: 'fa-cube', title: 'Danh từ',
              body: 'Chỉ người, vật, hiện tượng, khái niệm (học sinh, bàn, mưa, tình yêu). Thường làm chủ ngữ; kết hợp được với số từ (ba học sinh).' },
            { icon: 'fa-person-running', title: 'Động từ',
              body: 'Chỉ hành động (đi, viết) hoặc trạng thái (yêu, ngủ). Thường làm vị ngữ; kết hợp với “đã, đang, sẽ, hãy, đừng”.' },
            { icon: 'fa-palette', title: 'Tính từ',
              body: 'Chỉ đặc điểm, tính chất, màu sắc (tốt, xanh, cao). Kết hợp với “rất, quá, lắm” (rất đẹp, cao quá).' },
            { icon: 'fa-link', title: 'Đại từ – Quan hệ từ – Số từ',
              body: 'Đại từ thay thế (tôi, chúng ta, ai, gì). Quan hệ từ nối (và, nhưng, của, để, vì). Số từ chỉ số lượng/thứ tự (một, hai, thứ nhất).' }
          ],
          examples: [
            { q: 'Xác định từ loại của “vui”.', sol: 'Tính từ (chỉ trạng thái/đặc điểm; kết hợp “rất vui”).' },
            { q: '“Nhưng” trong câu là từ loại gì?', sol: 'Quan hệ từ (nối hai vế đối lập).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Danh từ: người/vật/khái niệm. Động từ: hành động/trạng thái. Tính từ: đặc điểm/tính chất.',
          'Đại từ thay thế; quan hệ từ nối; số từ chỉ số lượng.',
          'Mẹo: kết hợp “rất/quá” → tính từ; “đã/đang/sẽ” → động từ; “ba/những” → danh từ.'
        ],
        tip: 'Không chắc từ loại thì thử ghép: “rất …” hợp → tính từ; “đang …” hợp → động từ; “ba …” hợp → danh từ.'
      },
      drill: {
        time_seconds: 70,
        questions: [
          { id: 'd1', type: 'mcq', question: '“bàn, ghế, nhà” là từ loại?', options: ['danh từ', 'động từ', 'tính từ', 'đại từ'], answer: 'danh từ' },
          { id: 'd2', type: 'mcq', question: '“xanh, cao, tốt” là từ loại?', options: ['danh từ', 'động từ', 'tính từ', 'số từ'], answer: 'tính từ' },
          { id: 'd3', type: 'mcq', question: '“đọc, viết, nghĩ” là từ loại?', options: ['danh từ', 'động từ', 'tính từ', 'đại từ'], answer: 'động từ' },
          { id: 'd4', type: 'mcq', question: '“tôi, nó, chúng ta” là từ loại?', options: ['danh từ', 'đại từ', 'động từ', 'quan hệ từ'], answer: 'đại từ' },
          { id: 'd5', type: 'mcq', question: 'Từ “nhưng” là từ loại?', options: ['danh từ', 'quan hệ từ', 'động từ', 'tính từ'], answer: 'quan hệ từ' },
          { id: 'd6', type: 'mcq', question: '“ba, năm, nhiều” chỉ số lượng là?', options: ['danh từ', 'số từ', 'động từ', 'tính từ'], answer: 'số từ' },
          { id: 'd7', type: 'mcq', question: 'Từ nào là ĐỘNG TỪ?', options: ['chạy', 'nhanh', 'con', 'và'], answer: 'chạy' },
          { id: 'd8', type: 'mcq', question: 'Từ nào là TÍNH TỪ?', options: ['học', 'vui', 'bàn', 'tôi'], answer: 'vui' }
        ]
      }
    },

    {
      id: 'vb_04',
      index: 4,
      title: 'Thành ngữ – tục ngữ',
      subtitle: 'Phân biệt, hiểu nghĩa bóng và dùng đúng ngữ cảnh',
      topic_tag: 'Định tính · Từ vựng',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về thành ngữ – tục ngữ.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Câu “Có công mài sắt, có ngày nên kim” khuyên điều gì?',
            options: ['tiết kiệm tiền của', 'kiên trì sẽ thành công', 'đoàn kết là sức mạnh', 'sống trung thực'], answer: 'kiên trì sẽ thành công',
            explain: 'Kiên trì, bền bỉ thì việc khó đến mấy cũng thành công.' },
          { id: 't2', type: 'mcq', question: '“Ăn quả nhớ kẻ trồng cây” nói về đức tính gì?',
            options: ['lòng biết ơn', 'sự chăm chỉ', 'tính tiết kiệm', 'lòng dũng cảm'], answer: 'lòng biết ơn',
            explain: 'Được hưởng thành quả phải nhớ ơn người tạo ra nó → lòng biết ơn.' },
          { id: 't3', type: 'mcq', question: 'Đâu là THÀNH NGỮ (không phải tục ngữ)?',
            options: ['Chậm như rùa', 'Gần mực thì đen', 'Đói cho sạch, rách cho thơm', 'Có chí thì nên'], answer: 'Chậm như rùa',
            explain: 'Thành ngữ = cụm từ cố định (chưa thành câu/lời khuyên); các câu kia là tục ngữ đúc kết kinh nghiệm.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-quote-right', title: 'Phân biệt nhanh',
              body: '<b>Thành ngữ</b> là CỤM từ cố định, thường mang nghĩa bóng (chậm như rùa). <b>Tục ngữ</b> là CÂU hoàn chỉnh đúc kết kinh nghiệm, lời khuyên (Có chí thì nên).' },
            { icon: 'fa-lightbulb', title: 'Hiểu nghĩa bóng',
              body: 'Đa số mang nghĩa bóng — đừng hiểu theo chữ. “Lá lành đùm lá rách” = người khá giúp người khó, không phải nói về lá.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ Thành ngữ – Tục ngữ',
          cards: [
            { icon: 'fa-puzzle-piece', title: 'Thành ngữ',
              body: 'Cụm từ cố định, ngắn gọn, giàu hình ảnh, thường mang nghĩa bóng. Chưa là câu trọn vẹn. VD: nước đổ lá khoai, mèo mù vớ cá rán.' },
            { icon: 'fa-scroll', title: 'Tục ngữ',
              body: 'Câu ngắn gọn, có vần điệu, đúc kết kinh nghiệm sống / lời khuyên / nhận xét. Là câu trọn vẹn. VD: Tốt gỗ hơn tốt nước sơn.' },
            { icon: 'fa-code-compare', title: 'Cách phân biệt',
              body: 'Thành ngữ = tương đương một TỪ/CỤM (làm thành phần câu). Tục ngữ = một CÂU độc lập, có thể đứng riêng như một lời khuyên.' },
            { icon: 'fa-lightbulb', title: 'Nghĩa bóng & cách dùng',
              body: 'Hiểu ý nghĩa ẩn sau hình ảnh, dùng đúng hoàn cảnh. VD “gần mực thì đen, gần đèn thì sáng” = môi trường ảnh hưởng đến con người.' }
          ],
          examples: [
            { q: '“Nước chảy đá mòn” khuyên điều gì?', sol: 'Kiên trì, bền bỉ thì việc khó cũng thành.' },
            { q: '“Đứng núi này trông núi nọ” chỉ người thế nào?', sol: 'Không bằng lòng với cái mình đang có, hay so bì.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Thành ngữ = cụm từ cố định (làm thành phần câu); tục ngữ = câu hoàn chỉnh đúc kết kinh nghiệm.',
          'Đa số mang NGHĨA BÓNG — không hiểu theo nghĩa đen.',
          'Dùng đúng hoàn cảnh mới đạt hiệu quả diễn đạt.'
        ],
        tip: 'Phân biệt nhanh: đọc riêng ra thành một LỜI KHUYÊN/CÂU hoàn chỉnh được → tục ngữ; chỉ là một cụm gợi hình → thành ngữ.'
      },
      drill: {
        time_seconds: 75,
        questions: [
          { id: 'd1', type: 'mcq', question: '“Nước chảy đá mòn” khuyên điều gì?', options: ['kiên trì', 'tiết kiệm', 'đoàn kết', 'khiêm tốn'], answer: 'kiên trì' },
          { id: 'd2', type: 'mcq', question: '“Uống nước nhớ nguồn” nói về?', options: ['lòng biết ơn', 'sự chăm chỉ', 'tính trung thực', 'lòng dũng cảm'], answer: 'lòng biết ơn' },
          { id: 'd3', type: 'mcq', question: 'Câu nào là TỤC NGỮ?', options: ['Chậm như rùa', 'Nhanh như chớp', 'Tốt gỗ hơn tốt nước sơn', 'Mèo mù vớ cá rán'], answer: 'Tốt gỗ hơn tốt nước sơn' },
          { id: 'd4', type: 'mcq', question: '“Lá lành đùm lá rách” nói về?', options: ['đùm bọc, giúp đỡ nhau', 'tiết kiệm', 'chăm chỉ', 'trung thực'], answer: 'đùm bọc, giúp đỡ nhau' },
          { id: 'd5', type: 'mcq', question: 'Thành ngữ là?', options: ['cụm từ cố định', 'câu hoàn chỉnh', 'đoạn văn', 'bài thơ'], answer: 'cụm từ cố định' },
          { id: 'd6', type: 'mcq', question: '“Đứng núi này trông núi nọ” chỉ người?', options: ['không bằng lòng cái đang có', 'chăm chỉ', 'dũng cảm', 'tiết kiệm'], answer: 'không bằng lòng cái đang có' },
          { id: 'd7', type: 'mcq', question: '“Học một biết mười” khen người?', options: ['thông minh', 'lười biếng', 'chậm chạp', 'khiêm tốn'], answer: 'thông minh' },
          { id: 'd8', type: 'mcq', question: '“Gần mực thì đen, gần đèn thì sáng” nói về?', options: ['ảnh hưởng của môi trường', 'sự tiết kiệm', 'lòng dũng cảm', 'sự biết ơn'], answer: 'ảnh hưởng của môi trường' }
        ]
      }
    },

    {
      id: 'vb_05',
      index: 5,
      title: 'Thành phần câu',
      subtitle: 'Chủ ngữ, vị ngữ, trạng ngữ và các thành phần phụ',
      topic_tag: 'Định tính · Ngữ pháp',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về thành phần câu.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Trong câu “Em bé đang ngủ”, bộ phận “Em bé” là thành phần gì?',
            options: ['chủ ngữ', 'vị ngữ', 'trạng ngữ', 'bổ ngữ'], answer: 'chủ ngữ',
            explain: '“Em bé” là đối tượng được nói đến → chủ ngữ.' },
          { id: 't2', type: 'mcq', question: 'Bộ phận nêu HOẠT ĐỘNG, trạng thái, đặc điểm của chủ ngữ được gọi là?',
            options: ['chủ ngữ', 'vị ngữ', 'trạng ngữ', 'định ngữ'], answer: 'vị ngữ',
            explain: 'Vị ngữ nêu hoạt động/trạng thái/đặc điểm của chủ ngữ.' },
          { id: 't3', type: 'mcq', question: 'Trong câu “Sáng nay, tôi đi học”, bộ phận “Sáng nay” là?',
            options: ['chủ ngữ', 'vị ngữ', 'trạng ngữ', 'bổ ngữ'], answer: 'trạng ngữ',
            explain: '“Sáng nay” bổ sung ý nghĩa về thời gian → trạng ngữ (thành phần phụ).' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-diagram-successor', title: 'Nòng cốt câu',
              body: '<b>Chủ ngữ</b> (nêu đối tượng) + <b>Vị ngữ</b> (nêu hoạt động/đặc điểm) tạo thành nòng cốt câu. VD: “Chim / hót”.' },
            { icon: 'fa-clock', title: 'Trạng ngữ',
              body: 'Thành phần PHỤ, bổ sung ý về thời gian, nơi chốn, nguyên nhân, cách thức… Thường đứng đầu câu, ngăn bằng dấu phẩy.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ thành phần câu',
          cards: [
            { icon: 'fa-user', title: 'Chủ ngữ',
              body: 'Nêu người, vật, sự việc được nói đến trong câu; trả lời câu hỏi “Ai? Cái gì? Con gì?”. Thường do danh từ / cụm danh từ / đại từ đảm nhiệm.' },
            { icon: 'fa-person-running', title: 'Vị ngữ',
              body: 'Nêu hoạt động, trạng thái, đặc điểm của chủ ngữ; trả lời “làm gì? thế nào? là gì?”. Thường do động từ / tính từ đảm nhiệm.' },
            { icon: 'fa-clock', title: 'Trạng ngữ',
              body: 'Bổ sung hoàn cảnh: thời gian (hôm qua), nơi chốn (ở trường), nguyên nhân (vì mưa), mục đích, cách thức. Có thể đứng đầu / giữa / cuối câu.' },
            { icon: 'fa-puzzle-piece', title: 'Thành phần phụ khác',
              body: 'Định ngữ bổ nghĩa cho danh từ (áo ĐẸP); bổ ngữ bổ nghĩa cho động từ/tính từ (học GIỎI). Chúng làm câu rõ nghĩa và sinh động hơn.' }
          ],
          examples: [
            { q: 'Xác định chủ – vị trong “Hoa nở rất đẹp”.', sol: 'Chủ ngữ: “Hoa”; vị ngữ: “nở rất đẹp”.' },
            { q: 'Tìm trạng ngữ trong “Ngoài sân, các bạn đang chơi”.', sol: 'Trạng ngữ chỉ nơi chốn: “Ngoài sân”.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Nòng cốt câu = Chủ ngữ + Vị ngữ.',
          'Chủ ngữ trả lời “Ai/Cái gì?”; vị ngữ trả lời “làm gì/thế nào/là gì?”.',
          'Trạng ngữ = thành phần phụ (thời gian, nơi chốn, nguyên nhân…).',
          'Định ngữ bổ nghĩa danh từ; bổ ngữ bổ nghĩa động/tính từ.'
        ],
        tip: 'Tách câu: hỏi “Ai/Cái gì?” ra chủ ngữ, phần còn lại của nòng cốt là vị ngữ; phần thêm hoàn cảnh là trạng ngữ.'
      },
      drill: {
        time_seconds: 70,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Trong “Con mèo ngủ”, “Con mèo” là?', options: ['chủ ngữ', 'vị ngữ', 'trạng ngữ', 'bổ ngữ'], answer: 'chủ ngữ' },
          { id: 'd2', type: 'mcq', question: 'Trong “Trời mưa to”, “mưa to” là?', options: ['chủ ngữ', 'vị ngữ', 'trạng ngữ', 'định ngữ'], answer: 'vị ngữ' },
          { id: 'd3', type: 'mcq', question: 'Trong “Hôm qua, em nghỉ học”, “Hôm qua” là?', options: ['chủ ngữ', 'vị ngữ', 'trạng ngữ', 'bổ ngữ'], answer: 'trạng ngữ' },
          { id: 'd4', type: 'mcq', question: 'Thành phần trả lời câu hỏi “Ai? Cái gì?” là?', options: ['chủ ngữ', 'vị ngữ', 'trạng ngữ', 'định ngữ'], answer: 'chủ ngữ' },
          { id: 'd5', type: 'mcq', question: 'Trạng ngữ chỉ nơi chốn trong “Ở lớp, chúng em học bài”?', options: ['Ở lớp', 'chúng em', 'học bài', 'bài'], answer: 'Ở lớp' },
          { id: 'd6', type: 'mcq', question: 'Vị ngữ thường do từ loại nào đảm nhiệm?', options: ['động từ, tính từ', 'quan hệ từ', 'số từ', 'chỉ danh từ'], answer: 'động từ, tính từ' },
          { id: 'd7', type: 'mcq', question: 'Bộ phận bổ nghĩa cho danh từ gọi là?', options: ['định ngữ', 'bổ ngữ', 'trạng ngữ', 'chủ ngữ'], answer: 'định ngữ' },
          { id: 'd8', type: 'mcq', question: 'Nòng cốt câu gồm?', options: ['chủ ngữ và vị ngữ', 'chủ ngữ và trạng ngữ', 'vị ngữ và bổ ngữ', 'trạng ngữ và định ngữ'], answer: 'chủ ngữ và vị ngữ' }
        ]
      }
    },

    {
      id: 'vb_06',
      index: 6,
      title: 'Dấu câu & liên kết',
      subtitle: 'Công dụng các dấu câu và phép liên kết',
      topic_tag: 'Định tính · Ngữ pháp',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về dấu câu và liên kết.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Dấu câu nào dùng để KẾT THÚC một câu kể (câu trần thuật)?',
            options: ['dấu chấm', 'dấu phẩy', 'dấu hai chấm', 'dấu gạch ngang'], answer: 'dấu chấm',
            explain: 'Câu kể kết thúc bằng dấu chấm (.).' },
          { id: 't2', type: 'mcq', question: 'Dấu hai chấm (:) thường được dùng để làm gì?',
            options: ['kết thúc câu hỏi', 'báo hiệu phần liệt kê hoặc lời giải thích', 'ngăn cách chủ ngữ và vị ngữ', 'thể hiện cảm xúc'], answer: 'báo hiệu phần liệt kê hoặc lời giải thích',
            explain: 'Dấu hai chấm báo hiệu phần đứng sau là liệt kê, lời dẫn hoặc lời giải thích.' },
          { id: 't3', type: 'mcq', question: 'Các từ “vì vậy, do đó, tuy nhiên” là phương tiện dùng để?',
            options: ['liên kết câu (phép nối)', 'làm chủ ngữ', 'làm vị ngữ', 'chỉ số lượng'], answer: 'liên kết câu (phép nối)',
            explain: 'Đó là các quan hệ từ / từ nối, thực hiện phép NỐI để liên kết câu, đoạn.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-period', title: 'Dấu câu chính',
              body: 'Dấu chấm (.) kết thúc câu kể; chấm hỏi (?) câu hỏi; chấm than (!) câu cảm/cầu khiến; phẩy (,) ngăn cách; hai chấm (:) báo hiệu liệt kê/giải thích.' },
            { icon: 'fa-link', title: 'Phép liên kết',
              body: 'Liên kết câu/đoạn bằng: phép LẶP (lặp từ), phép THẾ (dùng đại từ thay thế), phép NỐI (vì vậy, tuy nhiên, và…).' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ dấu câu & liên kết',
          cards: [
            { icon: 'fa-period', title: 'Dấu kết thúc câu',
              body: 'Dấu chấm (.) — câu kể; dấu chấm hỏi (?) — câu hỏi; dấu chấm than (!) — câu cảm thán / cầu khiến, bộc lộ cảm xúc mạnh.' },
            { icon: 'fa-comma', title: 'Dấu ngăn cách',
              body: 'Dấu phẩy (,) ngăn các bộ phận cùng chức năng, ngăn trạng ngữ với nòng cốt, ngăn các vế câu ghép. Dấu chấm phẩy (;) ngăn các vế lớn.' },
            { icon: 'fa-quote-left', title: 'Dấu hai chấm & ngoặc kép',
              body: 'Dấu hai chấm (:) báo hiệu liệt kê, lời dẫn, giải thích. Dấu ngoặc kép (“ ”) đánh dấu lời dẫn trực tiếp hoặc từ ngữ đặc biệt.' },
            { icon: 'fa-link', title: 'Liên kết câu và đoạn',
              body: 'Phép lặp: lặp lại từ ngữ. Phép thế: thay bằng đại từ (nó, đó, ấy). Phép nối: dùng quan hệ từ (và, nhưng, vì vậy, tuy nhiên). Giúp văn bản mạch lạc.' }
          ],
          examples: [
            { q: 'Chọn dấu cho: “Em thích nhiều môn ( ) Toán, Văn, Anh.”', sol: 'Dùng dấu hai chấm (:) để báo hiệu liệt kê.' },
            { q: 'Câu “Trời mưa. Vì vậy, trận đấu hoãn.” dùng phép liên kết nào?', sol: 'Phép nối (từ nối “vì vậy”).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Dấu chấm kết thúc câu kể; chấm hỏi câu hỏi; chấm than câu cảm/cầu khiến.',
          'Dấu phẩy ngăn cách; dấu hai chấm báo hiệu liệt kê/giải thích.',
          'Liên kết câu: phép lặp, phép thế, phép nối.'
        ],
        tip: 'Nhìn chức năng câu để chọn dấu kết thúc; gặp liệt kê/giải thích thì nghĩ ngay tới dấu hai chấm.'
      },
      drill: {
        time_seconds: 70,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Dấu kết thúc câu HỎI là?', options: ['dấu chấm', 'dấu chấm hỏi', 'dấu chấm than', 'dấu phẩy'], answer: 'dấu chấm hỏi' },
          { id: 'd2', type: 'mcq', question: 'Dấu kết thúc câu CẢM THÁN là?', options: ['dấu chấm', 'dấu chấm hỏi', 'dấu chấm than', 'dấu phẩy'], answer: 'dấu chấm than' },
          { id: 'd3', type: 'mcq', question: 'Dấu báo hiệu phần liệt kê/giải thích?', options: ['dấu phẩy', 'dấu hai chấm', 'dấu chấm', 'dấu ngoặc'], answer: 'dấu hai chấm' },
          { id: 'd4', type: 'mcq', question: '“Nó, đó, ấy” dùng trong phép liên kết nào?', options: ['phép lặp', 'phép thế', 'phép nối', 'phép so sánh'], answer: 'phép thế' },
          { id: 'd5', type: 'mcq', question: '“Tuy nhiên, vì vậy” là phương tiện của phép?', options: ['lặp', 'thế', 'nối', 'ẩn dụ'], answer: 'nối' },
          { id: 'd6', type: 'mcq', question: 'Dấu dùng ngăn các bộ phận cùng chức năng?', options: ['dấu phẩy', 'dấu chấm', 'dấu chấm than', 'dấu hai chấm'], answer: 'dấu phẩy' },
          { id: 'd7', type: 'mcq', question: 'Dấu ngoặc kép dùng để?', options: ['đánh dấu lời dẫn trực tiếp', 'kết thúc câu', 'ngăn chủ-vị', 'chỉ số lượng'], answer: 'đánh dấu lời dẫn trực tiếp' },
          { id: 'd8', type: 'mcq', question: 'Lặp lại từ ngữ để nối câu là phép?', options: ['lặp', 'thế', 'nối', 'đối'], answer: 'lặp' }
        ]
      }
    },

    {
      id: 'vb_07',
      index: 7,
      title: 'Lỗi diễn đạt',
      subtitle: 'Nhận diện lỗi dùng từ và lỗi câu thường gặp',
      topic_tag: 'Định tính · Ngữ pháp',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về lỗi diễn đạt.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Câu “Vì trời mưa to nên chúng tôi vẫn đi học” mắc lỗi gì?',
            options: ['lỗi lặp từ', 'lỗi logic (dùng sai quan hệ từ)', 'lỗi chính tả', 'không mắc lỗi'], answer: 'lỗi logic (dùng sai quan hệ từ)',
            explain: '“Vì… nên… vẫn” mâu thuẫn; đúng phải là “Tuy trời mưa to nhưng chúng tôi vẫn đi học”.' },
          { id: 't2', type: 'mcq', question: 'Câu “Bạn ấy rất chăm chỉ và siêng năng học tập” mắc lỗi gì?',
            options: ['lặp nghĩa (dùng từ thừa)', 'thiếu chủ ngữ', 'sai chính tả', 'không mắc lỗi'], answer: 'lặp nghĩa (dùng từ thừa)',
            explain: '“Chăm chỉ” và “siêng năng” đồng nghĩa → dùng cả hai là thừa, lặp nghĩa.' },
          { id: 't3', type: 'mcq', question: 'Câu “Qua tác phẩm cho thấy tấm lòng nhân đạo của tác giả” thiếu thành phần nào?',
            options: ['thiếu chủ ngữ', 'thiếu vị ngữ', 'thiếu trạng ngữ', 'đủ thành phần'], answer: 'thiếu chủ ngữ',
            explain: 'Cụm “Qua tác phẩm” là trạng ngữ, câu chưa có chủ ngữ. Sửa: “Tác phẩm cho thấy…” hoặc “Qua tác phẩm, ta thấy…”.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-spell-check', title: 'Lỗi dùng từ',
              body: 'Dùng từ SAI NGHĨA, LẶP nghĩa (chăm chỉ + siêng năng), THỪA từ. Cách sửa: chọn đúng từ, bỏ từ thừa.' },
            { icon: 'fa-scissors', title: 'Lỗi câu',
              body: 'Thiếu chủ ngữ / vị ngữ; sai LOGIC (dùng sai quan hệ từ vì–nên, tuy–nhưng). Cách sửa: bổ sung thành phần, chỉnh quan hệ từ cho hợp.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ lỗi diễn đạt',
          cards: [
            { icon: 'fa-spell-check', title: 'Lỗi dùng từ sai nghĩa',
              body: 'Chọn từ không đúng nghĩa cần diễn đạt (VD “yếu điểm” = điểm quan trọng, không phải “điểm yếu”). Sửa: dùng đúng từ theo nghĩa.' },
            { icon: 'fa-copy', title: 'Lỗi lặp / thừa từ',
              body: 'Dùng hai từ đồng nghĩa liền nhau (chăm chỉ + siêng năng) hoặc lặp ý không cần thiết. Sửa: bỏ bớt cho gọn.' },
            { icon: 'fa-scissors', title: 'Lỗi thiếu thành phần câu',
              body: 'Câu thiếu chủ ngữ hoặc vị ngữ (thường gặp khi mở đầu bằng “Qua…, Với…, Bằng…”). Sửa: thêm chủ ngữ hoặc bỏ quan hệ từ đầu câu.' },
            { icon: 'fa-arrows-split-up-and-left', title: 'Lỗi logic – quan hệ từ',
              body: 'Dùng sai cặp quan hệ từ khiến ý mâu thuẫn (vì–nên–vẫn). Sửa: chọn cặp đúng quan hệ nguyên nhân (vì–nên) hay nhượng bộ (tuy–nhưng).' }
          ],
          examples: [
            { q: 'Sửa “Nó rất thông minh và giỏi giang.”', sol: 'Bỏ bớt từ thừa: “Nó rất thông minh.” (thông minh ≈ giỏi giang).' },
            { q: 'Sửa “Bằng sự cố gắng đã giúp em tiến bộ.”', sol: 'Thêm chủ ngữ: “Sự cố gắng đã giúp em tiến bộ.”' }
          ]
        }
      },
      notes: {
        key_points: [
          'Lỗi dùng từ: sai nghĩa, lặp nghĩa, thừa từ.',
          'Lỗi câu: thiếu chủ ngữ/vị ngữ; sai logic quan hệ từ.',
          'Cách sửa: chọn đúng từ, bỏ từ thừa, bổ sung thành phần, chỉnh quan hệ từ.'
        ],
        tip: 'Đọc lại câu và tự hỏi “Ai/Cái gì làm chủ ngữ?” — nếu không trả lời được thì câu thiếu chủ ngữ.'
      },
      drill: {
        time_seconds: 75,
        questions: [
          { id: 'd1', type: 'mcq', question: '“Nó vừa thông minh vừa sáng dạ” mắc lỗi?', options: ['lặp nghĩa/thừa từ', 'thiếu chủ ngữ', 'sai logic', 'không lỗi'], answer: 'lặp nghĩa/thừa từ' },
          { id: 'd2', type: 'mcq', question: '“Qua bài thơ đã thể hiện tình yêu quê hương” thiếu?', options: ['chủ ngữ', 'vị ngữ', 'trạng ngữ', 'không thiếu'], answer: 'chủ ngữ' },
          { id: 'd3', type: 'mcq', question: '“Tuy nhà nghèo nhưng bạn ấy vẫn học giỏi” — câu này?', options: ['đúng, không lỗi', 'sai logic', 'thiếu chủ ngữ', 'lặp từ'], answer: 'đúng, không lỗi' },
          { id: 'd4', type: 'mcq', question: 'Cách sửa lỗi LẶP/THỪA từ là?', options: ['bỏ bớt từ thừa', 'thêm trạng ngữ', 'thêm dấu phẩy', 'đổi chủ ngữ'], answer: 'bỏ bớt từ thừa' },
          { id: 'd5', type: 'mcq', question: '“Vì chăm học nên bạn ấy vẫn bị điểm kém” mắc lỗi?', options: ['sai logic (quan hệ từ)', 'lặp từ', 'thiếu vị ngữ', 'không lỗi'], answer: 'sai logic (quan hệ từ)' },
          { id: 'd6', type: 'mcq', question: 'Cặp quan hệ từ chỉ nhượng bộ là?', options: ['tuy… nhưng…', 'vì… nên…', 'nếu… thì…', 'không… mà…'], answer: 'tuy… nhưng…' },
          { id: 'd7', type: 'mcq', question: '“Với lòng quyết tâm đã đưa em đến thành công” cần?', options: ['bỏ “Với” để có chủ ngữ', 'thêm dấu chấm', 'thêm tính từ', 'giữ nguyên'], answer: 'bỏ “Với” để có chủ ngữ' },
          { id: 'd8', type: 'mcq', question: 'Câu đủ nghĩa cần tối thiểu?', options: ['chủ ngữ và vị ngữ', 'trạng ngữ', 'định ngữ', 'quan hệ từ'], answer: 'chủ ngữ và vị ngữ' }
        ]
      }
    },

    {
      id: 'vb_08',
      index: 8,
      title: 'Biến đổi câu',
      subtitle: 'Câu chủ động – bị động, rút gọn và phân loại câu',
      topic_tag: 'Định tính · Ngữ pháp',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về biến đổi câu.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Câu “Con mèo bắt con chuột” đổi sang câu BỊ ĐỘNG là?',
            options: ['Con chuột bị con mèo bắt', 'Con mèo bị con chuột bắt', 'Con chuột bắt con mèo', 'Con mèo và con chuột'], answer: 'Con chuột bị con mèo bắt',
            explain: 'Chủ động → bị động: đối tượng chịu tác động (con chuột) làm chủ ngữ, thêm “bị/được”.' },
          { id: 't2', type: 'mcq', question: 'Câu rút gọn là câu như thế nào?',
            options: ['lược bỏ một số thành phần', 'thêm nhiều trạng ngữ', 'có hai chủ ngữ', 'luôn là câu hỏi'], answer: 'lược bỏ một số thành phần',
            explain: 'Câu rút gọn lược bỏ một số thành phần (chủ ngữ hoặc vị ngữ) mà vẫn hiểu được nhờ ngữ cảnh.' },
          { id: 't3', type: 'mcq', question: 'Câu “Đi học đi!” thuộc loại câu nào (theo mục đích nói)?',
            options: ['câu kể', 'câu hỏi', 'câu cầu khiến', 'câu cảm thán'], answer: 'câu cầu khiến',
            explain: 'Câu dùng để yêu cầu, ra lệnh, đề nghị → câu cầu khiến.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-right-left', title: 'Chủ động – Bị động',
              body: 'Câu chủ động: chủ ngữ thực hiện hành động. Câu bị động: đối tượng chịu tác động làm chủ ngữ, thêm “bị / được”.' },
            { icon: 'fa-list', title: 'Phân loại theo mục đích',
              body: 'Câu KỂ (trần thuật), câu HỎI (nghi vấn), câu CẦU KHIẾN (yêu cầu/ra lệnh), câu CẢM THÁN (bộc lộ cảm xúc).' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ biến đổi câu',
          cards: [
            { icon: 'fa-right-left', title: 'Câu chủ động & bị động',
              body: 'Chủ động: “A làm B” (A là chủ thể). Bị động: “B bị/được A làm” (B là đối tượng). Chuyển đổi giúp thay đổi trọng tâm nhấn mạnh.' },
            { icon: 'fa-compress', title: 'Rút gọn câu',
              body: 'Lược bỏ chủ ngữ hoặc vị ngữ khi ngữ cảnh đã rõ, làm câu gọn hơn. VD: “Bao giờ đi?” — “Ngày mai.” (lược chủ – vị).' },
            { icon: 'fa-expand', title: 'Mở rộng câu',
              body: 'Thêm thành phần phụ (trạng ngữ, định ngữ, bổ ngữ) để câu chi tiết, sinh động hơn. VD: “Em học” → “Sáng nay, em chăm chỉ học bài ở thư viện.”' },
            { icon: 'fa-list', title: 'Phân loại theo mục đích nói',
              body: 'Câu kể (thông báo, kết thúc bằng dấu chấm); câu hỏi (dấu ?); câu cầu khiến (yêu cầu/ra lệnh); câu cảm thán (bộc lộ cảm xúc, dấu !).' }
          ],
          examples: [
            { q: 'Đổi “Người ta xây ngôi nhà này” sang bị động.', sol: '“Ngôi nhà này được người ta xây.”' },
            { q: '“Ôi, đẹp quá!” là loại câu gì?', sol: 'Câu cảm thán (bộc lộ cảm xúc).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Chủ động → bị động: đối tượng làm chủ ngữ, thêm “bị/được”.',
          'Câu rút gọn: lược bỏ thành phần khi ngữ cảnh đã rõ.',
          'Mở rộng câu: thêm trạng ngữ/định ngữ/bổ ngữ.',
          'Phân loại: câu kể, câu hỏi, câu cầu khiến, câu cảm thán.'
        ],
        tip: 'Nhận diện loại câu qua mục đích và dấu cuối: ? → hỏi, ! → cảm/cầu khiến, . → kể.'
      },
      drill: {
        time_seconds: 70,
        questions: [
          { id: 'd1', type: 'mcq', question: '“Bé làm vỡ cốc” đổi bị động là?', options: ['Cốc bị bé làm vỡ', 'Bé bị cốc làm vỡ', 'Cốc làm vỡ bé', 'Bé và cốc vỡ'], answer: 'Cốc bị bé làm vỡ' },
          { id: 'd2', type: 'mcq', question: '“Bạn có khỏe không?” là câu?', options: ['câu kể', 'câu hỏi', 'câu cầu khiến', 'câu cảm thán'], answer: 'câu hỏi' },
          { id: 'd3', type: 'mcq', question: '“Hãy giữ trật tự!” là câu?', options: ['câu kể', 'câu hỏi', 'câu cầu khiến', 'câu cảm thán'], answer: 'câu cầu khiến' },
          { id: 'd4', type: 'mcq', question: '“Trời hôm nay đẹp quá!” là câu?', options: ['câu kể', 'câu hỏi', 'câu cầu khiến', 'câu cảm thán'], answer: 'câu cảm thán' },
          { id: 'd5', type: 'mcq', question: 'Câu bị động thường thêm từ nào?', options: ['bị / được', 'và / nhưng', 'rất / quá', 'đã / sẽ'], answer: 'bị / được' },
          { id: 'd6', type: 'mcq', question: 'Câu lược bỏ thành phần khi ngữ cảnh rõ gọi là?', options: ['câu rút gọn', 'câu ghép', 'câu cảm', 'câu hỏi'], answer: 'câu rút gọn' },
          { id: 'd7', type: 'mcq', question: '“Em đọc sách” mở rộng thành?', options: ['Buổi tối, em chăm chú đọc sách ở nhà', 'Đọc sách', 'Sách', 'Em'], answer: 'Buổi tối, em chăm chú đọc sách ở nhà' },
          { id: 'd8', type: 'mcq', question: '“Ngôi trường được xây năm 2000” là câu?', options: ['bị động', 'chủ động', 'câu hỏi', 'câu cầu khiến'], answer: 'bị động' }
        ]
      }
    },

    {
      id: 'vb_09',
      index: 9,
      title: 'Ý chính & ý phụ',
      subtitle: 'Xác định ý chính, câu chủ đề và ý triển khai',
      topic_tag: 'Định tính · Đọc hiểu',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> đọc hiểu của bạn.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Câu nêu lên ý khái quát, bao trùm nội dung cả đoạn văn được gọi là?',
            options: ['câu chủ đề', 'câu mở rộng', 'câu hỏi', 'câu cảm thán'], answer: 'câu chủ đề',
            explain: 'Câu chủ đề mang ý chính, các câu khác triển khai làm rõ nó.' },
          { id: 't2', type: 'mcq', question: 'Câu chủ đề của một đoạn văn thường đứng ở vị trí nào?',
            options: ['đầu hoặc cuối đoạn', 'chỉ ở giữa đoạn', 'luôn ở giữa', 'không có vị trí cố định trong câu'], answer: 'đầu hoặc cuối đoạn',
            explain: 'Đoạn diễn dịch: câu chủ đề đầu đoạn; đoạn quy nạp: cuối đoạn.' },
          { id: 't3', type: 'mcq', question: 'Các ý phụ (câu triển khai) trong đoạn văn có vai trò gì?',
            options: ['làm rõ, bổ sung, chứng minh cho ý chính', 'thay thế ý chính', 'không liên quan ý chính', 'kết thúc văn bản'], answer: 'làm rõ, bổ sung, chứng minh cho ý chính',
            explain: 'Ý phụ giải thích, dẫn chứng, làm sáng tỏ cho ý chính.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-star', title: 'Ý chính & câu chủ đề',
              body: 'Ý chính = nội dung khái quát nhất của đoạn, thường nằm ở CÂU CHỦ ĐỀ (đầu đoạn — diễn dịch, hoặc cuối đoạn — quy nạp).' },
            { icon: 'fa-list-ul', title: 'Ý phụ',
              body: 'Các câu triển khai làm rõ, chứng minh, bổ sung cho ý chính bằng lí lẽ, dẫn chứng, ví dụ.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ ý chính & ý phụ',
          cards: [
            { icon: 'fa-star', title: 'Ý chính là gì?',
              body: 'Là nội dung quan trọng, bao trùm nhất mà đoạn văn muốn truyền đạt. Trả lời câu hỏi: “Đoạn này nói về điều gì?”.' },
            { icon: 'fa-anchor', title: 'Câu chủ đề & vị trí',
              body: 'Câu chủ đề chứa ý chính. Đoạn diễn dịch: chủ đề ở đầu, các câu sau triển khai. Đoạn quy nạp: chủ đề ở cuối, các câu trước dẫn dắt.' },
            { icon: 'fa-list-ul', title: 'Ý phụ & dẫn chứng',
              body: 'Các câu triển khai (ý phụ) đưa lí lẽ, ví dụ, số liệu để làm sáng tỏ ý chính. Không mang nội dung khái quát toàn đoạn.' },
            { icon: 'fa-magnifying-glass', title: 'Cách xác định ý chính',
              body: 'Đọc lướt tìm câu chủ đề; nếu không có câu chủ đề rõ, tự khái quát nội dung chung của các câu. Loại bỏ chi tiết vụn vặt.' }
          ],
          examples: [
            { q: 'Đoạn mở đầu bằng “Đọc sách mang lại nhiều lợi ích.” rồi liệt kê lợi ích — câu chủ đề ở đâu?', sol: 'Ở đầu đoạn (đoạn diễn dịch); ý chính: lợi ích của đọc sách.' },
            { q: 'Làm sao phân biệt ý chính và ý phụ?', sol: 'Ý chính khái quát toàn đoạn; ý phụ chỉ làm rõ một khía cạnh.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Ý chính = nội dung khái quát nhất, nằm ở câu chủ đề.',
          'Câu chủ đề thường ở đầu (diễn dịch) hoặc cuối đoạn (quy nạp).',
          'Ý phụ = câu triển khai, làm rõ/chứng minh ý chính.',
          'Xác định ý chính: tìm câu chủ đề hoặc khái quát nội dung chung.'
        ],
        tip: 'Hỏi “Đoạn này nói về cái gì?” — câu trả lời ngắn gọn nhất chính là ý chính.'
      },
      drill: {
        time_seconds: 70,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Câu mang ý khái quát cả đoạn là?', options: ['câu chủ đề', 'câu hỏi', 'câu cảm', 'câu ghép'], answer: 'câu chủ đề' },
          { id: 'd2', type: 'mcq', question: 'Đoạn diễn dịch có câu chủ đề ở?', options: ['đầu đoạn', 'cuối đoạn', 'giữa đoạn', 'không có'], answer: 'đầu đoạn' },
          { id: 'd3', type: 'mcq', question: 'Đoạn quy nạp có câu chủ đề ở?', options: ['đầu đoạn', 'cuối đoạn', 'giữa đoạn', 'không có'], answer: 'cuối đoạn' },
          { id: 'd4', type: 'mcq', question: 'Ý phụ có vai trò?', options: ['làm rõ ý chính', 'thay ý chính', 'kết thúc bài', 'gây nhiễu'], answer: 'làm rõ ý chính' },
          { id: 'd5', type: 'mcq', question: 'Để tìm ý chính, ta nên?', options: ['tìm câu chủ đề / khái quát nội dung', 'đọc câu cuối cùng', 'đếm số câu', 'xem dấu câu'], answer: 'tìm câu chủ đề / khái quát nội dung' },
          { id: 'd6', type: 'mcq', question: 'Câu hỏi “Đoạn này nói về gì?” giúp tìm?', options: ['ý chính', 'ý phụ', 'số từ', 'dấu câu'], answer: 'ý chính' },
          { id: 'd7', type: 'mcq', question: 'Dẫn chứng, ví dụ trong đoạn thuộc?', options: ['ý phụ', 'ý chính', 'câu chủ đề', 'nhan đề'], answer: 'ý phụ' },
          { id: 'd8', type: 'mcq', question: 'Ý chính khác ý phụ ở chỗ?', options: ['khái quát toàn đoạn', 'dài hơn', 'nhiều số liệu', 'đứng cuối'], answer: 'khái quát toàn đoạn' }
        ]
      }
    },

    {
      id: 'vb_10',
      index: 10,
      title: 'Suy luận & hàm ý',
      subtitle: 'Đọc giữa dòng và hiểu ý ngầm của văn bản',
      topic_tag: 'Định tính · Đọc hiểu',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> suy luận của bạn.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Hàm ý là gì?',
            options: ['ý người nói không nói trực tiếp, phải suy ra', 'ý nói to, rõ ràng', 'ý trong nhan đề', 'lỗi diễn đạt'], answer: 'ý người nói không nói trực tiếp, phải suy ra',
            explain: 'Hàm ý là phần ý nghĩa ẩn, người nghe phải suy luận từ câu chữ và ngữ cảnh.' },
          { id: 't2', type: 'mcq', question: 'Để hiểu đúng hàm ý của một câu, người đọc cần dựa vào?',
            options: ['ngữ cảnh và từ ngữ', 'số chữ trong câu', 'chỉ dấu câu', 'độ dài văn bản'], answer: 'ngữ cảnh và từ ngữ',
            explain: 'Hàm ý phụ thuộc hoàn cảnh nói và cách dùng từ.' },
          { id: 't3', type: 'mcq', question: 'Lúc 11 giờ đêm, mẹ nói với con đang xem tivi: “Muộn rồi đấy!”. Câu này hàm ý gì?',
            options: ['nhắc con đi ngủ', 'hỏi mấy giờ', 'khen con', 'chào con'], answer: 'nhắc con đi ngủ',
            explain: 'Ngữ cảnh (đêm khuya, con còn thức) cho thấy hàm ý là nhắc đi ngủ.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-comment-dots', title: 'Hàm ý (ý ngầm)',
              body: 'Là phần nghĩa KHÔNG nói trực tiếp, người đọc phải SUY RA. Khác với nghĩa tường minh (nói thẳng).' },
            { icon: 'fa-magnifying-glass', title: 'Suy luận',
              body: 'Dựa vào NGỮ CẢNH (hoàn cảnh nói) + từ ngữ + kiến thức nền để rút ra ý ngầm và thái độ người nói.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ suy luận & hàm ý',
          cards: [
            { icon: 'fa-comment', title: 'Nghĩa tường minh & hàm ý',
              body: 'Nghĩa tường minh: nói thẳng, hiểu ngay. Hàm ý: nghĩa ẩn phải suy ra. VD “Trời nóng quá!” có thể hàm ý “bật quạt/máy lạnh giúp”.' },
            { icon: 'fa-brain', title: 'Cơ sở suy luận',
              body: 'Muốn hiểu hàm ý, dựa vào: ngữ cảnh giao tiếp, quan hệ người nói – người nghe, từ ngữ và giọng điệu.' },
            { icon: 'fa-lightbulb', title: 'Đọc giữa dòng',
              body: 'Trong văn bản, tác giả có thể ngụ ý qua hình ảnh, chi tiết. Người đọc suy luận để hiểu thông điệp sâu hơn câu chữ bề mặt.' },
            { icon: 'fa-triangle-exclamation', title: 'Lưu ý',
              body: 'Suy luận phải CÓ CĂN CỨ từ văn bản, không suy diễn tùy tiện. Chọn hàm ý hợp lí nhất với ngữ cảnh.' }
          ],
          examples: [
            { q: 'Bạn nói “Bài này khó thật” sau khi làm sai — hàm ý?', sol: 'Thừa nhận mình chưa làm được / cần giúp đỡ.' },
            { q: 'Câu “Cũng được đấy” với giọng hờ hững hàm ý?', sol: 'Không thực sự hài lòng, chỉ chấp nhận miễn cưỡng.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Hàm ý = nghĩa ẩn, phải suy ra (khác nghĩa tường minh).',
          'Suy luận dựa vào ngữ cảnh + từ ngữ + giọng điệu.',
          'Đọc giữa dòng: hiểu thông điệp sâu hơn câu chữ.',
          'Suy luận phải có căn cứ trong văn bản, chọn ý hợp lí nhất.'
        ],
        tip: 'Gặp câu hỏi hàm ý, luôn đặt câu vào HOÀN CẢNH nói rồi tự hỏi “người nói thật ra muốn gì?”.'
      },
      drill: {
        time_seconds: 70,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Hàm ý là nghĩa?', options: ['ẩn, phải suy ra', 'nói thẳng', 'trong nhan đề', 'sai ngữ pháp'], answer: 'ẩn, phải suy ra' },
          { id: 'd2', type: 'mcq', question: 'Hiểu hàm ý cần dựa vào?', options: ['ngữ cảnh', 'số chữ', 'dấu phẩy', 'độ dài'], answer: 'ngữ cảnh' },
          { id: 'd3', type: 'mcq', question: '“Con làm bài xong chưa?” (mẹ hỏi lúc con chơi game) hàm ý?', options: ['nhắc con làm bài', 'khen con', 'hỏi giờ', 'rủ chơi'], answer: 'nhắc con làm bài' },
          { id: 'd4', type: 'mcq', question: 'Nghĩa nói thẳng, hiểu ngay là nghĩa?', options: ['tường minh', 'hàm ý', 'bóng', 'ẩn dụ'], answer: 'tường minh' },
          { id: 'd5', type: 'mcq', question: 'Suy luận đúng phải?', options: ['có căn cứ trong văn bản', 'tùy ý người đọc', 'dựa vào số câu', 'bỏ qua ngữ cảnh'], answer: 'có căn cứ trong văn bản' },
          { id: 'd6', type: 'mcq', question: '“Trời nóng quá!” trong phòng có quạt hàm ý?', options: ['muốn bật quạt', 'khen thời tiết', 'hỏi nhiệt độ', 'chào'], answer: 'muốn bật quạt' },
          { id: 'd7', type: 'mcq', question: '“Cũng được” với giọng hờ hững hàm ý?', options: ['chưa thật hài lòng', 'rất thích', 'từ chối hẳn', 'khen ngợi'], answer: 'chưa thật hài lòng' },
          { id: 'd8', type: 'mcq', question: 'Đọc “giữa dòng” nghĩa là?', options: ['hiểu thông điệp ẩn', 'đọc dòng giữa trang', 'đọc to', 'đọc nhanh'], answer: 'hiểu thông điệp ẩn' }
        ]
      }
    },

    {
      id: 'vb_11',
      index: 11,
      title: 'Thái độ – giọng điệu tác giả',
      subtitle: 'Nhận diện tình cảm, quan điểm và giọng điệu',
      topic_tag: 'Định tính · Đọc hiểu',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về thái độ tác giả.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Thái độ của tác giả trong văn bản là gì?',
            options: ['tình cảm, quan điểm của tác giả với đối tượng', 'số câu trong bài', 'độ dài văn bản', 'thể loại văn bản'], answer: 'tình cảm, quan điểm của tác giả với đối tượng',
            explain: 'Thái độ = tình cảm, cách nhìn nhận, đánh giá của tác giả về vấn đề/đối tượng.' },
          { id: 't2', type: 'mcq', question: 'Giọng điệu (trang trọng, mỉa mai, tha thiết…) của văn bản được thể hiện chủ yếu qua?',
            options: ['cách dùng từ ngữ, hình ảnh, câu', 'số trang', 'tên tác giả', 'năm xuất bản'], answer: 'cách dùng từ ngữ, hình ảnh, câu',
            explain: 'Giọng điệu bộc lộ qua lựa chọn từ ngữ, hình ảnh, kiểu câu.' },
          { id: 't3', type: 'mcq', question: 'Việc tác giả dùng nhiều từ ngữ ca ngợi, trân trọng thể hiện thái độ gì?',
            options: ['yêu mến, đề cao', 'chê bai', 'trung lập', 'mỉa mai'], answer: 'yêu mến, đề cao',
            explain: 'Từ ngữ ca ngợi → thái độ yêu mến, trân trọng, đề cao.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-heart', title: 'Thái độ tác giả',
              body: 'Là tình cảm, quan điểm, cách đánh giá của tác giả về đối tượng: yêu/ghét, ca ngợi/phê phán, trân trọng/mỉa mai…' },
            { icon: 'fa-music', title: 'Giọng điệu',
              body: 'Là “âm hưởng” của văn bản: trang trọng, tha thiết, hài hước, mỉa mai, xót xa… bộc lộ qua TỪ NGỮ, hình ảnh, kiểu câu.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ thái độ & giọng điệu',
          cards: [
            { icon: 'fa-heart', title: 'Thái độ của tác giả',
              body: 'Cách tác giả nhìn nhận, đánh giá đối tượng: đồng tình/phản đối, ngợi ca/phê phán, yêu thương/căm ghét. Thái độ chi phối cách viết.' },
            { icon: 'fa-music', title: 'Giọng điệu',
              body: 'Sắc thái biểu cảm chủ đạo: trang trọng, thân mật, tha thiết, mỉa mai, châm biếm, xót xa… Là “giọng nói” của người viết trong văn bản.' },
            { icon: 'fa-palette', title: 'Dấu hiệu nhận biết',
              body: 'Qua từ ngữ (ca ngợi, chê bai), hình ảnh (đẹp đẽ/xấu xí), kiểu câu (cảm thán, câu hỏi tu từ), biện pháp tu từ.' },
            { icon: 'fa-magnifying-glass', title: 'Cách xác định',
              body: 'Đọc kỹ, chú ý các từ bộc lộ cảm xúc và cách miêu tả; đặt câu hỏi “Tác giả yêu/ghét, đồng tình/phê phán điều gì?”.' }
          ],
          examples: [
            { q: '“Ôi Tổ quốc ta yêu như máu thịt” thể hiện thái độ gì?', sol: 'Yêu thương, gắn bó tha thiết với Tổ quốc; giọng điệu tha thiết.' },
            { q: 'Văn bản dùng nhiều từ chê trách, mỉa mai thể hiện thái độ?', sol: 'Phê phán, không đồng tình.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Thái độ = tình cảm, quan điểm của tác giả với đối tượng.',
          'Giọng điệu = sắc thái biểu cảm (trang trọng, mỉa mai, tha thiết…).',
          'Nhận biết qua từ ngữ, hình ảnh, kiểu câu, biện pháp tu từ.',
          'Từ ca ngợi → yêu mến; từ chê trách → phê phán.'
        ],
        tip: 'Chú ý các từ bộc lộ cảm xúc (yêu, thương, ghét, mỉa…) — chúng “tố cáo” thái độ của tác giả.'
      },
      drill: {
        time_seconds: 70,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Thái độ tác giả là?', options: ['tình cảm, quan điểm với đối tượng', 'số câu', 'thể loại', 'tên bài'], answer: 'tình cảm, quan điểm với đối tượng' },
          { id: 'd2', type: 'mcq', question: 'Giọng điệu thể hiện qua?', options: ['từ ngữ, hình ảnh, câu', 'số trang', 'năm viết', 'nhà xuất bản'], answer: 'từ ngữ, hình ảnh, câu' },
          { id: 'd3', type: 'mcq', question: 'Từ ngữ ca ngợi thể hiện thái độ?', options: ['yêu mến, đề cao', 'chê bai', 'trung lập', 'thờ ơ'], answer: 'yêu mến, đề cao' },
          { id: 'd4', type: 'mcq', question: 'Từ ngữ mỉa mai thể hiện thái độ?', options: ['phê phán', 'ca ngợi', 'yêu thương', 'trân trọng'], answer: 'phê phán' },
          { id: 'd5', type: 'mcq', question: 'Giọng điệu “tha thiết” thường gặp khi?', options: ['bày tỏ tình cảm sâu nặng', 'liệt kê số liệu', 'hướng dẫn kỹ thuật', 'thông báo'], answer: 'bày tỏ tình cảm sâu nặng' },
          { id: 'd6', type: 'mcq', question: 'Để xác định thái độ tác giả, chú ý?', options: ['từ bộc lộ cảm xúc', 'số đoạn', 'độ dài câu', 'phông chữ'], answer: 'từ bộc lộ cảm xúc' },
          { id: 'd7', type: 'mcq', question: 'Câu cảm thán, câu hỏi tu từ giúp bộc lộ?', options: ['cảm xúc, thái độ', 'số lượng', 'thời gian', 'địa điểm'], answer: 'cảm xúc, thái độ' },
          { id: 'd8', type: 'mcq', question: 'Giọng điệu là?', options: ['sắc thái biểu cảm của văn bản', 'số chữ', 'tên tác giả', 'thể loại'], answer: 'sắc thái biểu cảm của văn bản' }
        ]
      }
    },

    {
      id: 'vb_12',
      index: 12,
      title: 'Văn bản thông tin & nghị luận',
      subtitle: 'Phân biệt mục đích và đặc điểm hai loại văn bản',
      topic_tag: 'Định tính · Đọc hiểu',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về loại văn bản.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Văn bản NGHỊ LUẬN nhằm mục đích chính là gì?',
            options: ['thuyết phục người đọc bằng lí lẽ và dẫn chứng', 'kể một câu chuyện', 'miêu tả phong cảnh', 'bộc lộ cảm xúc'], answer: 'thuyết phục người đọc bằng lí lẽ và dẫn chứng',
            explain: 'Nghị luận dùng luận điểm, lí lẽ, dẫn chứng để thuyết phục người đọc về một quan điểm.' },
          { id: 't2', type: 'mcq', question: 'Văn bản THÔNG TIN nhằm mục đích gì?',
            options: ['cung cấp thông tin, kiến thức khách quan', 'thuyết phục theo quan điểm riêng', 'thể hiện cảm xúc mãnh liệt', 'kể chuyện tưởng tượng'], answer: 'cung cấp thông tin, kiến thức khách quan',
            explain: 'Văn bản thông tin trình bày thông tin, kiến thức, hướng dẫn một cách khách quan, chính xác.' },
          { id: 't3', type: 'mcq', question: 'Ý kiến, quan điểm chính được nêu ra trong văn nghị luận gọi là gì?',
            options: ['luận điểm', 'nhan đề', 'lời dẫn', 'kết bài'], answer: 'luận điểm',
            explain: 'Luận điểm là quan điểm chính; luận cứ (lí lẽ, dẫn chứng) làm sáng tỏ luận điểm.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-scale-balanced', title: 'Văn bản nghị luận',
              body: 'Mục đích: THUYẾT PHỤC bằng lí lẽ + dẫn chứng. Gồm luận điểm (quan điểm chính) và luận cứ (lí lẽ, dẫn chứng).' },
            { icon: 'fa-circle-info', title: 'Văn bản thông tin',
              body: 'Mục đích: CUNG CẤP thông tin, kiến thức khách quan (bản tin, hướng dẫn, thuyết minh). Chính xác, rõ ràng, không thiên về cảm xúc.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ loại văn bản',
          cards: [
            { icon: 'fa-scale-balanced', title: 'Văn bản nghị luận',
              body: 'Bàn luận, thuyết phục người đọc về một vấn đề. Cấu trúc: luận điểm (ý kiến chính) — luận cứ (lí lẽ + dẫn chứng) — lập luận (cách sắp xếp, liên kết).' },
            { icon: 'fa-circle-info', title: 'Văn bản thông tin',
              body: 'Truyền đạt thông tin, tri thức khách quan: bản tin, văn bản thuyết minh, hướng dẫn. Đề cao tính chính xác, khách quan, dễ hiểu.' },
            { icon: 'fa-code-compare', title: 'Phân biệt',
              body: 'Nghị luận thiên về THUYẾT PHỤC (có quan điểm, tranh luận). Thông tin thiên về THÔNG BÁO (khách quan, không áp đặt quan điểm cá nhân).' },
            { icon: 'fa-list-check', title: 'Các loại văn bản khác',
              body: 'Ngoài ra còn: tự sự (kể chuyện), miêu tả (tả người/vật/cảnh), biểu cảm (bộc lộ cảm xúc). Nhận diện qua MỤC ĐÍCH chính của văn bản.' }
          ],
          examples: [
            { q: 'Bài “Bàn về đọc sách” thuộc loại văn bản nào?', sol: 'Nghị luận (thuyết phục về ích lợi và cách đọc sách).' },
            { q: 'Một bản tin thời tiết thuộc loại?', sol: 'Văn bản thông tin (cung cấp thông tin khách quan).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Nghị luận: thuyết phục bằng luận điểm + lí lẽ + dẫn chứng.',
          'Thông tin: cung cấp thông tin/kiến thức khách quan.',
          'Luận điểm = quan điểm chính; luận cứ = lí lẽ, dẫn chứng.',
          'Nhận diện loại văn bản qua MỤC ĐÍCH chính.'
        ],
        tip: 'Hỏi “Văn bản này để THUYẾT PHỤC hay để THÔNG BÁO?” — trả lời được là phân loại đúng.'
      },
      drill: {
        time_seconds: 70,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Văn nghị luận nhằm?', options: ['thuyết phục', 'kể chuyện', 'tả cảnh', 'bộc lộ cảm xúc'], answer: 'thuyết phục' },
          { id: 'd2', type: 'mcq', question: 'Văn bản thông tin nhằm?', options: ['cung cấp thông tin khách quan', 'thuyết phục', 'kể chuyện', 'làm thơ'], answer: 'cung cấp thông tin khách quan' },
          { id: 'd3', type: 'mcq', question: 'Quan điểm chính trong nghị luận gọi là?', options: ['luận điểm', 'nhan đề', 'kết bài', 'lời dẫn'], answer: 'luận điểm' },
          { id: 'd4', type: 'mcq', question: 'Lí lẽ, dẫn chứng làm rõ luận điểm gọi là?', options: ['luận cứ', 'luận điểm', 'chủ ngữ', 'trạng ngữ'], answer: 'luận cứ' },
          { id: 'd5', type: 'mcq', question: 'Bản tin thời tiết là văn bản?', options: ['thông tin', 'nghị luận', 'tự sự', 'biểu cảm'], answer: 'thông tin' },
          { id: 'd6', type: 'mcq', question: 'Bài bàn luận về một vấn đề xã hội là văn bản?', options: ['nghị luận', 'thông tin', 'miêu tả', 'tự sự'], answer: 'nghị luận' },
          { id: 'd7', type: 'mcq', question: 'Văn bản kể lại một câu chuyện là?', options: ['tự sự', 'nghị luận', 'thông tin', 'thuyết minh'], answer: 'tự sự' },
          { id: 'd8', type: 'mcq', question: 'Để phân loại văn bản, ta xét?', options: ['mục đích chính', 'số câu', 'tên tác giả', 'độ dài'], answer: 'mục đích chính' }
        ]
      }
    },

    {
      id: 'vb_13',
      index: 13,
      title: 'Tác giả – tác phẩm trọng tâm',
      subtitle: 'Ghép đúng tác giả với tác phẩm tiêu biểu',
      topic_tag: 'Định tính · Văn học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về tác giả – tác phẩm.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Tác giả của "Truyện Kiều" là ai?',
            options: ['Nguyễn Du', 'Nguyễn Trãi', 'Hồ Xuân Hương', 'Nam Cao'], answer: 'Nguyễn Du',
            explain: '"Truyện Kiều" (Đoạn trường tân thanh) là kiệt tác của đại thi hào Nguyễn Du.' },
          { id: 't2', type: 'mcq', question: 'Các truyện ngắn "Lão Hạc", "Chí Phèo" là của tác giả nào?',
            options: ['Nam Cao', 'Ngô Tất Tố', 'Vũ Trọng Phụng', 'Thạch Lam'], answer: 'Nam Cao',
            explain: 'Nam Cao là cây bút hiện thực xuất sắc với "Lão Hạc", "Chí Phèo".' },
          { id: 't3', type: 'mcq', question: 'Bài thơ "Việt Bắc" là của tác giả nào?',
            options: ['Tố Hữu', 'Xuân Diệu', 'Huy Cận', 'Chế Lan Viên'], answer: 'Tố Hữu',
            explain: '"Việt Bắc" là bài thơ nổi tiếng của Tố Hữu – lá cờ đầu của thơ ca cách mạng.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-feather', title: 'Trung đại tiêu biểu',
              body: 'Nguyễn Trãi (Bình Ngô đại cáo), Nguyễn Du (Truyện Kiều), Hồ Xuân Hương (thơ Nôm). Nắm tác giả – tác phẩm gắn liền.' },
            { icon: 'fa-book', title: 'Hiện đại tiêu biểu',
              body: 'Nam Cao (Lão Hạc, Chí Phèo), Ngô Tất Tố (Tắt đèn), Tố Hữu (Việt Bắc), Xuân Diệu (thơ tình), Hồ Chí Minh (Nhật ký trong tù).' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ tác giả – tác phẩm',
          cards: [
            { icon: 'fa-scroll', title: 'Văn học trung đại',
              body: 'Nguyễn Trãi – "Bình Ngô đại cáo"; Nguyễn Du – "Truyện Kiều"; Hồ Xuân Hương – thơ Nôm ("Bánh trôi nước"); Nguyễn Đình Chiểu – "Lục Vân Tiên".' },
            { icon: 'fa-pen-nib', title: 'Văn học hiện thực (1930-1945)',
              body: 'Nam Cao – "Lão Hạc", "Chí Phèo"; Ngô Tất Tố – "Tắt đèn"; Vũ Trọng Phụng – "Số đỏ"; Thạch Lam – "Hai đứa trẻ".' },
            { icon: 'fa-flag', title: 'Thơ ca cách mạng',
              body: 'Hồ Chí Minh – "Nhật ký trong tù"; Tố Hữu – "Việt Bắc", "Từ ấy"; các nhà thơ kháng chiến khác.' },
            { icon: 'fa-star', title: 'Phong trào Thơ mới',
              body: 'Xuân Diệu (ông hoàng thơ tình), Huy Cận, Hàn Mặc Tử, Chế Lan Viên — đổi mới thơ ca Việt Nam đầu thế kỷ XX.' }
          ],
          examples: [
            { q: '"Bình Ngô đại cáo" là của ai?', sol: 'Nguyễn Trãi.' },
            { q: '"Nhật ký trong tù" là của ai?', sol: 'Hồ Chí Minh.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Nguyễn Du – Truyện Kiều; Nguyễn Trãi – Bình Ngô đại cáo.',
          'Nam Cao – Lão Hạc, Chí Phèo; Ngô Tất Tố – Tắt đèn.',
          'Tố Hữu – Việt Bắc; Hồ Chí Minh – Nhật ký trong tù.',
          'Xuân Diệu – ông hoàng thơ tình (phong trào Thơ mới).'
        ],
        tip: 'Học theo cặp “tác giả – tác phẩm – thời kỳ” — câu HSA hay hỏi ghép đúng ba yếu tố này.'
      },
      drill: {
        time_seconds: 75,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Tác giả "Truyện Kiều"?', options: ['Nguyễn Du', 'Nguyễn Trãi', 'Tố Hữu', 'Nam Cao'], answer: 'Nguyễn Du' },
          { id: 'd2', type: 'mcq', question: 'Tác giả "Chí Phèo"?', options: ['Nam Cao', 'Ngô Tất Tố', 'Vũ Trọng Phụng', 'Thạch Lam'], answer: 'Nam Cao' },
          { id: 'd3', type: 'mcq', question: 'Tác giả "Bình Ngô đại cáo"?', options: ['Nguyễn Trãi', 'Nguyễn Du', 'Hồ Xuân Hương', 'Tố Hữu'], answer: 'Nguyễn Trãi' },
          { id: 'd4', type: 'mcq', question: 'Tác giả "Tắt đèn"?', options: ['Ngô Tất Tố', 'Nam Cao', 'Vũ Trọng Phụng', 'Xuân Diệu'], answer: 'Ngô Tất Tố' },
          { id: 'd5', type: 'mcq', question: 'Tác giả "Nhật ký trong tù"?', options: ['Hồ Chí Minh', 'Tố Hữu', 'Xuân Diệu', 'Huy Cận'], answer: 'Hồ Chí Minh' },
          { id: 'd6', type: 'mcq', question: 'Tác giả bài thơ "Việt Bắc"?', options: ['Tố Hữu', 'Xuân Diệu', 'Chế Lan Viên', 'Nguyễn Du'], answer: 'Tố Hữu' },
          { id: 'd7', type: 'mcq', question: 'Nhà thơ được gọi "ông hoàng thơ tình"?', options: ['Xuân Diệu', 'Huy Cận', 'Tố Hữu', 'Hàn Mặc Tử'], answer: 'Xuân Diệu' },
          { id: 'd8', type: 'mcq', question: '"Bánh trôi nước" là của?', options: ['Hồ Xuân Hương', 'Nguyễn Du', 'Đoàn Thị Điểm', 'Bà Huyện Thanh Quan'], answer: 'Hồ Xuân Hương' }
        ]
      }
    },

    {
      id: 'vb_14',
      index: 14,
      title: 'Thể loại văn học',
      subtitle: 'Tự sự, trữ tình, kịch và các thể thơ',
      topic_tag: 'Định tính · Văn học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về thể loại văn học.',
        questions: [
          { id: 't1', type: 'mcq', question: '"Truyện Kiều" của Nguyễn Du thuộc thể loại nào?',
            options: ['truyện thơ', 'tiểu thuyết', 'kịch', 'tùy bút'], answer: 'truyện thơ',
            explain: '"Truyện Kiều" là truyện thơ Nôm viết theo thể lục bát.' },
          { id: 't2', type: 'mcq', question: 'Thơ lục bát có đặc điểm nổi bật là gì?',
            options: ['câu 6 chữ và câu 8 chữ xen kẽ', 'mỗi câu 7 chữ', 'mỗi câu 5 chữ', 'không có luật'], answer: 'câu 6 chữ và câu 8 chữ xen kẽ',
            explain: 'Lục bát: một câu 6 chữ (lục) nối một câu 8 chữ (bát), có vần điệu đặc trưng.' },
          { id: 't3', type: 'mcq', question: 'Thể loại TỰ SỰ có đặc điểm gì?',
            options: ['kể chuyện, có cốt truyện và nhân vật', 'bộc lộ cảm xúc trực tiếp', 'chỉ có đối thoại trên sân khấu', 'chỉ tả cảnh'], answer: 'kể chuyện, có cốt truyện và nhân vật',
            explain: 'Tự sự dùng để kể lại sự việc, có cốt truyện, nhân vật, diễn biến.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-masks-theater', title: 'Ba loại lớn',
              body: 'TỰ SỰ (kể chuyện: truyện, tiểu thuyết). TRỮ TÌNH (bộc lộ cảm xúc: thơ). KỊCH (diễn trên sân khấu bằng hành động, đối thoại).' },
            { icon: 'fa-feather', title: 'Một số thể thơ',
              body: 'Lục bát (6-8), song thất lục bát, thất ngôn (7 chữ), ngũ ngôn (5 chữ), thơ tự do. Nhận diện qua số chữ mỗi câu và vần.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ thể loại văn học',
          cards: [
            { icon: 'fa-book-open', title: 'Tự sự',
              body: 'Kể lại sự việc, có cốt truyện, nhân vật, tình huống. Gồm truyện ngắn, truyện dài, tiểu thuyết, truyện thơ (Truyện Kiều).' },
            { icon: 'fa-heart', title: 'Trữ tình',
              body: 'Bộc lộ tình cảm, cảm xúc, tâm trạng của tác giả. Tiêu biểu là thơ. Không nặng về cốt truyện mà nặng về cảm xúc.' },
            { icon: 'fa-masks-theater', title: 'Kịch',
              body: 'Tác phẩm để diễn trên sân khấu, xây dựng bằng hành động và đối thoại của nhân vật, có xung đột kịch. VD chèo, tuồng, kịch nói.' },
            { icon: 'fa-feather', title: 'Các thể thơ Việt',
              body: 'Lục bát (câu 6 – câu 8), song thất lục bát, thất ngôn bát cú (Đường luật), ngũ ngôn, thơ tự do. Phân biệt qua số chữ và cách gieo vần.' }
          ],
          examples: [
            { q: '"Lão Hạc" thuộc thể loại nào?', sol: 'Truyện ngắn (tự sự).' },
            { q: 'Ca dao "Trong đầm gì đẹp bằng sen" theo thể thơ nào?', sol: 'Lục bát.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Ba loại lớn: tự sự (kể chuyện), trữ tình (thơ), kịch (sân khấu).',
          'Truyện Kiều = truyện thơ (lục bát).',
          'Lục bát: câu 6 chữ xen câu 8 chữ.',
          'Nhận diện thể thơ qua số chữ mỗi câu và vần.'
        ],
        tip: 'Câu hỏi thể loại: xem tác phẩm KỂ CHUYỆN (tự sự), BỘC LỘ CẢM XÚC (trữ tình) hay DIỄN (kịch).'
      },
      drill: {
        time_seconds: 75,
        questions: [
          { id: 'd1', type: 'mcq', question: '"Truyện Kiều" thuộc thể loại?', options: ['truyện thơ', 'kịch', 'tùy bút', 'tiểu thuyết'], answer: 'truyện thơ' },
          { id: 'd2', type: 'mcq', question: 'Lục bát gồm câu?', options: ['6 và 8 chữ', '7 và 7 chữ', '5 và 5 chữ', '8 và 8 chữ'], answer: '6 và 8 chữ' },
          { id: 'd3', type: 'mcq', question: 'Thể loại kể chuyện, có cốt truyện là?', options: ['tự sự', 'trữ tình', 'kịch', 'nghị luận'], answer: 'tự sự' },
          { id: 'd4', type: 'mcq', question: 'Thơ bộc lộ cảm xúc thuộc loại?', options: ['trữ tình', 'tự sự', 'kịch', 'thông tin'], answer: 'trữ tình' },
          { id: 'd5', type: 'mcq', question: 'Tác phẩm diễn trên sân khấu là?', options: ['kịch', 'thơ', 'truyện', 'tùy bút'], answer: 'kịch' },
          { id: 'd6', type: 'mcq', question: '"Lão Hạc" là?', options: ['truyện ngắn', 'thơ', 'kịch', 'ca dao'], answer: 'truyện ngắn' },
          { id: 'd7', type: 'mcq', question: 'Thơ mỗi câu 7 chữ gọi là?', options: ['thất ngôn', 'ngũ ngôn', 'lục bát', 'tự do'], answer: 'thất ngôn' },
          { id: 'd8', type: 'mcq', question: 'Ca dao thường viết theo thể?', options: ['lục bát', 'thất ngôn', 'ngũ ngôn', 'tự do'], answer: 'lục bát' }
        ]
      }
    },

    {
      id: 'vb_15',
      index: 15,
      title: 'Biện pháp tu từ',
      subtitle: 'So sánh, ẩn dụ, nhân hóa, hoán dụ và điệp ngữ',
      topic_tag: 'Định tính · Văn học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về biện pháp tu từ.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Câu "Thuyền về có nhớ bến chăng?" dùng biện pháp tu từ nào (thuyền – bến chỉ người)?',
            options: ['so sánh', 'ẩn dụ', 'nhân hóa', 'điệp ngữ'], answer: 'ẩn dụ',
            explain: '"Thuyền" và "bến" là ẩn dụ chỉ người đi – kẻ ở, dựa trên nét tương đồng.' },
          { id: 't2', type: 'mcq', question: 'Câu "Trâu ơi ta bảo trâu này" gọi con vật như gọi người là biện pháp?',
            options: ['so sánh', 'ẩn dụ', 'nhân hóa', 'hoán dụ'], answer: 'nhân hóa',
            explain: 'Nhân hóa: gán cho vật đặc điểm, hành động của con người.' },
          { id: 't3', type: 'mcq', question: 'Cụm "đẹp như hoa" sử dụng biện pháp tu từ nào?',
            options: ['so sánh', 'ẩn dụ', 'hoán dụ', 'nói quá'], answer: 'so sánh',
            explain: 'So sánh: đối chiếu hai sự vật qua từ "như", "là", "tựa"…' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-equals', title: 'So sánh & ẩn dụ',
              body: 'SO SÁNH: đối chiếu hai vật qua "như, là, tựa". ẨN DỤ: gọi tên vật này bằng vật khác dựa trên nét GIỐNG NHAU (so sánh ngầm).' },
            { icon: 'fa-face-smile', title: 'Nhân hóa & hoán dụ',
              body: 'NHÂN HÓA: gán đặc điểm con người cho vật. HOÁN DỤ: gọi tên bằng cái GẦN GŨI liên quan (áo nâu = nông dân).' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ biện pháp tu từ',
          cards: [
            { icon: 'fa-equals', title: 'So sánh',
              body: 'Đối chiếu hai sự vật, hiện tượng có nét tương đồng qua từ so sánh: như, là, tựa, bằng. VD "Trẻ em như búp trên cành".' },
            { icon: 'fa-shuffle', title: 'Ẩn dụ',
              body: 'So sánh NGẦM: gọi tên sự vật A bằng sự vật B có nét giống, không dùng từ so sánh. VD "Thuyền – bến" chỉ người đi – kẻ ở.' },
            { icon: 'fa-face-smile', title: 'Nhân hóa',
              body: 'Gán cho vật, con vật, cây cối… những đặc điểm, hành động, tình cảm của con người. VD "Ông trăng tròn", "cây đa đứng gác".' },
            { icon: 'fa-link', title: 'Hoán dụ & điệp ngữ',
              body: 'Hoán dụ: gọi bằng cái gần gũi liên quan (áo nâu, áo xanh = nông dân, công nhân). Điệp ngữ: lặp từ ngữ để nhấn mạnh. Nói quá: phóng đại để gây ấn tượng.' }
          ],
          examples: [
            { q: '"Mặt trời của bắp thì nằm trên đồi / Mặt trời của mẹ, em nằm trên lưng" — biện pháp?', sol: 'Ẩn dụ ("mặt trời của mẹ" chỉ đứa con).' },
            { q: '"Áo chàm đưa buổi phân li" — biện pháp?', sol: 'Hoán dụ (áo chàm chỉ người dân Việt Bắc).' }
          ]
        }
      },
      notes: {
        key_points: [
          'So sánh: có từ "như, là, tựa"; Ẩn dụ: so sánh ngầm (nét giống).',
          'Nhân hóa: gán đặc điểm con người cho vật.',
          'Hoán dụ: gọi bằng cái gần gũi liên quan.',
          'Điệp ngữ (lặp từ nhấn mạnh); Nói quá (phóng đại).'
        ],
        tip: 'Phân biệt ẩn dụ (nét GIỐNG nhau) và hoán dụ (quan hệ GẦN nhau) — đây là điểm HSA hay “bẫy”.'
      },
      drill: {
        time_seconds: 75,
        questions: [
          { id: 'd1', type: 'mcq', question: '"Đẹp như tiên" là biện pháp?', options: ['so sánh', 'ẩn dụ', 'nhân hóa', 'hoán dụ'], answer: 'so sánh' },
          { id: 'd2', type: 'mcq', question: '"Ông mặt trời thức dậy" là biện pháp?', options: ['nhân hóa', 'so sánh', 'ẩn dụ', 'nói quá'], answer: 'nhân hóa' },
          { id: 'd3', type: 'mcq', question: '"Áo nâu" chỉ người nông dân là biện pháp?', options: ['hoán dụ', 'so sánh', 'nhân hóa', 'điệp ngữ'], answer: 'hoán dụ' },
          { id: 'd4', type: 'mcq', question: 'So sánh NGẦM (không từ so sánh) là?', options: ['ẩn dụ', 'so sánh', 'nhân hóa', 'nói quá'], answer: 'ẩn dụ' },
          { id: 'd5', type: 'mcq', question: 'Lặp lại từ ngữ để nhấn mạnh là?', options: ['điệp ngữ', 'ẩn dụ', 'so sánh', 'hoán dụ'], answer: 'điệp ngữ' },
          { id: 'd6', type: 'mcq', question: '"Mồ hôi thánh thót như mưa" là biện pháp?', options: ['so sánh + nói quá', 'chỉ nhân hóa', 'chỉ hoán dụ', 'điệp ngữ'], answer: 'so sánh + nói quá' },
          { id: 'd7', type: 'mcq', question: 'Phóng đại mức độ để gây ấn tượng là?', options: ['nói quá', 'nói giảm', 'so sánh', 'hoán dụ'], answer: 'nói quá' },
          { id: 'd8', type: 'mcq', question: 'Ẩn dụ dựa trên quan hệ?', options: ['giống nhau', 'gần nhau', 'đối lập', 'ngẫu nhiên'], answer: 'giống nhau' }
        ]
      }
    },

    {
      id: 'vb_16',
      index: 16,
      title: 'Giá trị nội dung – nghệ thuật',
      subtitle: 'Đánh giá tư tưởng và hình thức của tác phẩm',
      topic_tag: 'Định tính · Văn học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về giá trị tác phẩm.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Giá trị NỘI DUNG của một tác phẩm văn học là gì?',
            options: ['ý nghĩa, tư tưởng, tình cảm mà tác phẩm gửi gắm', 'số trang của tác phẩm', 'tên nhà xuất bản', 'giá bán'], answer: 'ý nghĩa, tư tưởng, tình cảm mà tác phẩm gửi gắm',
            explain: 'Giá trị nội dung = điều tác phẩm nói lên: tư tưởng, tình cảm, thông điệp.' },
          { id: 't2', type: 'mcq', question: 'Giá trị NGHỆ THUẬT của tác phẩm là gì?',
            options: ['cái hay về hình thức: ngôn từ, hình ảnh, kết cấu, biện pháp tu từ', 'số nhân vật', 'năm sáng tác', 'độ dài'], answer: 'cái hay về hình thức: ngôn từ, hình ảnh, kết cấu, biện pháp tu từ',
            explain: 'Giá trị nghệ thuật = cách thể hiện: ngôn ngữ, hình ảnh, xây dựng nhân vật, biện pháp tu từ.' },
          { id: 't3', type: 'mcq', question: 'Giá trị NHÂN ĐẠO của một tác phẩm thường thể hiện ở?',
            options: ['tình thương con người, bênh vực người khổ', 'số câu văn', 'nhịp điệu', 'màu bìa sách'], answer: 'tình thương con người, bênh vực người khổ',
            explain: 'Giá trị nhân đạo: đồng cảm, yêu thương, bênh vực con người, tố cáo bất công.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-lightbulb', title: 'Giá trị nội dung',
              body: 'Là tư tưởng, tình cảm, thông điệp tác phẩm gửi gắm. Gồm giá trị HIỆN THỰC (phản ánh đời sống) và giá trị NHÂN ĐẠO (yêu thương con người).' },
            { icon: 'fa-palette', title: 'Giá trị nghệ thuật',
              body: 'Là cái hay về HÌNH THỨC: ngôn từ, hình ảnh, kết cấu, xây dựng nhân vật, biện pháp tu từ, giọng điệu.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ giá trị tác phẩm',
          cards: [
            { icon: 'fa-lightbulb', title: 'Giá trị nội dung',
              body: 'Điều tác phẩm nói lên: chủ đề, tư tưởng, tình cảm, thông điệp. Trả lời câu hỏi "Tác phẩm phản ánh gì, gửi gắm điều gì?".' },
            { icon: 'fa-eye', title: 'Giá trị hiện thực',
              body: 'Phản ánh chân thực đời sống, xã hội đương thời (VD "Tắt đèn" phản ánh nỗi khổ của nông dân trước Cách mạng).' },
            { icon: 'fa-heart', title: 'Giá trị nhân đạo',
              body: 'Thể hiện tình thương, sự đồng cảm với con người, đặc biệt người bất hạnh; lên án cái ác, bất công; trân trọng phẩm giá con người.' },
            { icon: 'fa-palette', title: 'Giá trị nghệ thuật',
              body: 'Cái hay về hình thức: ngôn ngữ giàu hình ảnh, kết cấu chặt chẽ, xây dựng nhân vật sinh động, sử dụng biện pháp tu từ, giọng điệu đặc sắc.' }
          ],
          examples: [
            { q: '"Chí Phèo" có giá trị nhân đạo ở đâu?', sol: 'Cảm thông với bi kịch bị tha hóa của người nông dân, khát khao được làm người lương thiện.' },
            { q: 'Giá trị nghệ thuật của "Truyện Kiều"?', sol: 'Thể lục bát điêu luyện, ngôn ngữ giàu hình ảnh, tả cảnh ngụ tình bậc thầy.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Giá trị nội dung = tư tưởng, tình cảm, thông điệp (gồm hiện thực + nhân đạo).',
          'Giá trị hiện thực: phản ánh chân thực đời sống, xã hội.',
          'Giá trị nhân đạo: yêu thương, bênh vực con người, lên án bất công.',
          'Giá trị nghệ thuật: cái hay về hình thức (ngôn từ, kết cấu, tu từ…).'
        ],
        tip: 'Phân tích tác phẩm luôn tách hai mặt: NÓI GÌ (nội dung) và NÓI HAY THẾ NÀO (nghệ thuật).'
      },
      drill: {
        time_seconds: 75,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Giá trị nội dung là?', options: ['tư tưởng, tình cảm tác phẩm', 'số trang', 'tên NXB', 'giá sách'], answer: 'tư tưởng, tình cảm tác phẩm' },
          { id: 'd2', type: 'mcq', question: 'Giá trị nghệ thuật là?', options: ['cái hay về hình thức', 'số nhân vật', 'năm viết', 'độ dài'], answer: 'cái hay về hình thức' },
          { id: 'd3', type: 'mcq', question: 'Giá trị phản ánh chân thực đời sống gọi là?', options: ['giá trị hiện thực', 'giá trị nghệ thuật', 'giá trị thương mại', 'giá trị sử dụng'], answer: 'giá trị hiện thực' },
          { id: 'd4', type: 'mcq', question: 'Tình thương, bênh vực con người là giá trị?', options: ['nhân đạo', 'nghệ thuật', 'hiện thực đơn thuần', 'giải trí'], answer: 'nhân đạo' },
          { id: 'd5', type: 'mcq', question: 'Ngôn từ, hình ảnh, kết cấu thuộc giá trị?', options: ['nghệ thuật', 'nội dung', 'hiện thực', 'nhân đạo'], answer: 'nghệ thuật' },
          { id: 'd6', type: 'mcq', question: 'Phân tích tác phẩm cần tách?', options: ['nội dung và nghệ thuật', 'câu và chữ', 'trang và dòng', 'tên và giá'], answer: 'nội dung và nghệ thuật' },
          { id: 'd7', type: 'mcq', question: '"Tắt đèn" nổi bật giá trị?', options: ['hiện thực & nhân đạo', 'chỉ giải trí', 'chỉ hình thức', 'thương mại'], answer: 'hiện thực & nhân đạo' },
          { id: 'd8', type: 'mcq', question: 'Biện pháp tu từ, giọng điệu thuộc?', options: ['giá trị nghệ thuật', 'giá trị nội dung', 'giá trị hiện thực', 'giá trị nhân đạo'], answer: 'giá trị nghệ thuật' }
        ]
      }
    }
  ]
};

window.LESSON_CONTENT_HSA['hsa_science'] = {
  course_id: 'hsa_science',
  course_title: 'Khoa học',
  accent_color: '#34D399',
  lessons: [
    {
      id: 'kh_01',
      index: 1,
      title: 'Cơ học',
      subtitle: 'Chuyển động, lực và công – năng lượng',
      topic_tag: 'Khoa học · Vật lý',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> Vật lý cơ học của bạn.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Một vật khối lượng 5 kg chịu lực kéo 20 N (bỏ qua ma sát). Gia tốc của vật là bao nhiêu?',
            options: ['2 m/s²', '4 m/s²', '5 m/s²', '100 m/s²'], answer: '4 m/s²',
            explain: 'Định luật II Newton: a = F/m = 20/5 = 4 m/s².' },
          { id: 't2', type: 'fill', question: 'Một xe chạy với vận tốc 36 km/h. Đổi ra đơn vị m/s bằng bao nhiêu? (nhập số)',
            answer: '10', explain: '36 km/h = 36 / 3,6 = 10 m/s (chia 3,6 để đổi km/h → m/s).' },
          { id: 't3', type: 'mcq', question: 'Lực F = 50 N kéo một thùng hàng dịch chuyển 4 m theo hướng của lực. Công của lực là bao nhiêu?',
            options: ['12,5 J', '46 J', '200 J', '54 J'], answer: '200 J',
            explain: 'Công A = F·s·cosα, với α = 0° (cùng hướng): A = 50 × 4 = 200 J.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-arrows-left-right', title: 'Động học & Định luật Newton',
              body: 'Chuyển động thẳng đều: <code>s = v·t</code>. Biến đổi đều: <code>v = v₀ + a·t</code>. ' +
                    'Định luật II Newton: <code>F = m·a</code> → gia tốc tỉ lệ THUẬN lực, NGHỊCH khối lượng.' },
            { icon: 'fa-bolt', title: 'Công – Năng lượng',
              body: 'Công: <code>A = F·s·cosα</code> (J). Động năng: <code>W_đ = ½mv²</code>. Thế năng: <code>W_t = mgh</code>. ' +
                    'Đơn vị: lực N, công/năng lượng J, công suất W.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ Cơ học',
          cards: [
            { icon: 'fa-gauge-high', title: 'Động học: mô tả chuyển động',
              body: 'Vận tốc v (m/s), gia tốc a (m/s²). Thẳng đều: <code>s = v·t</code>. Thẳng biến đổi đều: ' +
                    '<code>v = v₀ + a·t</code> và <code>s = v₀t + ½at²</code>. Đổi đơn vị: km/h → m/s chia 3,6.' },
            { icon: 'fa-hand-fist', title: 'Động lực học: 3 định luật Newton',
              body: 'I — vật giữ nguyên trạng thái nếu không có lực (quán tính). II — <code>F = m·a</code> (lực gây gia tốc). ' +
                    'III — lực và phản lực: hai vật tác dụng lẫn nhau bằng nhau, ngược chiều.' },
            { icon: 'fa-bolt', title: 'Công & Công suất',
              body: 'Công: <code>A = F·s·cosα</code> (J) — α là góc giữa lực và hướng đi. Lực vuông góc đường đi (α = 90°) sinh công = 0. ' +
                    'Công suất: <code>P = A/t</code> (W) — công thực hiện trong một đơn vị thời gian.' },
            { icon: 'fa-battery-full', title: 'Năng lượng & Bảo toàn cơ năng',
              body: 'Động năng <code>W_đ = ½mv²</code>, thế năng trọng trường <code>W_t = mgh</code> (g ≈ 9,8 m/s²). ' +
                    'Bỏ qua ma sát: cơ năng W = W_đ + W_t được BẢO TOÀN (khi rơi: thế năng → động năng).' }
          ],
          examples: [
            { q: 'Vật 2 kg rơi từ độ cao 5 m (g = 10). Thế năng ban đầu?', sol: 'W_t = mgh = 2 × 10 × 5 = 100 J.' },
            { q: 'Ô tô đi 108 km/h là bao nhiêu m/s?', sol: '108 / 3,6 = 30 m/s.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Định luật II Newton: F = m·a (đơn vị lực: Niutơn N).',
          'Đổi km/h → m/s: chia 3,6 (và ngược lại nhân 3,6).',
          'Công A = F·s·cosα (J); lực vuông góc đường đi → công = 0.',
          'Động năng W_đ = ½mv²; thế năng W_t = mgh; bỏ ma sát → cơ năng bảo toàn.'
        ],
        formula: 'F = m·a   |   A = F·s·cosα   |   W_đ = ½mv²   |   W_t = mgh',
        tip: 'Câu Cơ học HSA hay lồng ĐỔI ĐƠN VỊ (km/h ↔ m/s) trước khi tính — đổi ngay từ đầu để tránh sai số ×3,6.'
      },
      drill: {
        time_seconds: 75,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Đơn vị của lực trong hệ SI là gì?', options: ['Jun (J)', 'Niutơn (N)', 'Oát (W)', 'Paxcan (Pa)'], answer: 'Niutơn (N)' },
          { id: 'd2', type: 'fill', question: 'Vật m = 4 kg chịu lực 12 N. Gia tốc a = ? (m/s², nhập số)', answer: '3' },
          { id: 'd3', type: 'mcq', question: '72 km/h bằng bao nhiêu m/s?', options: ['20', '25', '36', '200'], answer: '20' },
          { id: 'd4', type: 'mcq', question: 'Lực 30 N kéo vật đi 5 m cùng hướng. Công của lực?', options: ['6 J', '35 J', '150 J', '25 J'], answer: '150 J' },
          { id: 'd5', type: 'fill', question: 'Động năng của vật m = 2 kg, v = 3 m/s là bao nhiêu J? (Wđ = ½mv², nhập số)', answer: '9' },
          { id: 'd6', type: 'mcq', question: 'Đơn vị của công suất là?', options: ['Niutơn', 'Jun', 'Oát', 'Ampe'], answer: 'Oát' },
          { id: 'd7', type: 'fill', question: 'Vật 3 kg ở độ cao 4 m, g = 10. Thế năng Wt = mgh = ? (J, nhập số)', answer: '120' },
          { id: 'd8', type: 'mcq', question: 'Theo định luật II Newton, cùng một lực, khối lượng càng lớn thì gia tốc:', options: ['càng lớn', 'càng nhỏ', 'không đổi', 'bằng 0'], answer: 'càng nhỏ' }
        ]
      }
    },

    {
      id: 'kh_02',
      index: 2,
      title: 'Điện học',
      subtitle: 'Định luật Ôm, mạch điện và công suất',
      topic_tag: 'Khoa học · Vật lý',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> Vật lý điện học của bạn.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Mạch có hiệu điện thế U = 12 V, điện trở R = 4 Ω. Cường độ dòng điện I bằng bao nhiêu?',
            options: ['2 A', '3 A', '4 A', '48 A'], answer: '3 A',
            explain: 'Định luật Ôm: I = U/R = 12/4 = 3 A.' },
          { id: 't2', type: 'fill', question: 'Hai điện trở R₁ = 3 Ω và R₂ = 5 Ω mắc NỐI TIẾP. Điện trở tương đương bằng bao nhiêu Ω? (nhập số)',
            answer: '8', explain: 'Nối tiếp: R = R₁ + R₂ = 3 + 5 = 8 Ω.' },
          { id: 't3', type: 'mcq', question: 'Công suất tiêu thụ của một đoạn mạch được tính bằng công thức nào?',
            options: ['P = U/I', 'P = U·I', 'P = I/U', 'P = U + I'], answer: 'P = U·I',
            explain: 'Công suất điện: P = U·I (đơn vị W).' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-bolt', title: 'Định luật Ôm',
              body: '<code>I = U/R</code>. U (Vôn) hiệu điện thế, I (Ampe) cường độ, R (Ôm) điện trở. Từ đó U = I·R, R = U/I.' },
            { icon: 'fa-diagram-project', title: 'Mạch & công suất',
              body: 'Nối tiếp: <code>R = R₁ + R₂</code>. Song song: <code>1/R = 1/R₁ + 1/R₂</code>. Công suất: <code>P = U·I</code> (W). Điện năng: <code>A = P·t</code>.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ Điện học',
          cards: [
            { icon: 'fa-bolt', title: 'Định luật Ôm',
              body: 'Cường độ dòng điện tỉ lệ THUẬN với hiệu điện thế, tỉ lệ NGHỊCH với điện trở: I = U/R. Đơn vị: V, A, Ω.' },
            { icon: 'fa-grip-lines', title: 'Mạch nối tiếp',
              body: 'Dòng điện qua các điện trở BẰNG NHAU (I chung). Điện trở tương đương R = R₁ + R₂ + … Hiệu điện thế cộng lại: U = U₁ + U₂.' },
            { icon: 'fa-grip', title: 'Mạch song song',
              body: 'Hiệu điện thế trên các nhánh BẰNG NHAU. Nghịch đảo điện trở tương đương: 1/R = 1/R₁ + 1/R₂. Dòng chính = tổng dòng nhánh.' },
            { icon: 'fa-plug', title: 'Công suất & điện năng',
              body: 'Công suất P = U·I = I²R = U²/R (W). Điện năng tiêu thụ A = P·t (J hoặc kWh). Đây là cơ sở tính tiền điện.' }
          ],
          examples: [
            { q: 'R₁ = 4 Ω, R₂ = 6 Ω mắc song song. Tính R.', sol: '1/R = 1/4 + 1/6 = 5/12 → R = 2,4 Ω.' },
            { q: 'Bóng đèn 220 V – 2 A. Công suất?', sol: 'P = U·I = 220 × 2 = 440 W.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Định luật Ôm: I = U/R (V, A, Ω).',
          'Nối tiếp: R = R₁ + R₂; dòng điện bằng nhau.',
          'Song song: 1/R = 1/R₁ + 1/R₂; hiệu điện thế bằng nhau.',
          'Công suất P = U·I (W); điện năng A = P·t.'
        ],
        formula: 'I = U/R   |   nối tiếp R = R₁+R₂   |   song song 1/R = 1/R₁+1/R₂   |   P = U·I',
        tip: 'Nhận diện mạch trước: NỐI TIẾP thì cộng R, SONG SONG thì cộng nghịch đảo — chọn đúng công thức là xong.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Đơn vị đo điện trở là gì?', options: ['Vôn', 'Ampe', 'Ôm (Ω)', 'Oát'], answer: 'Ôm (Ω)' },
          { id: 'd2', type: 'fill', question: 'U = 6 V, R = 2 Ω. Cường độ I = ? (A, nhập số)', answer: '3' },
          { id: 'd3', type: 'mcq', question: 'R₁ = 4 Ω, R₂ = 6 Ω mắc nối tiếp. Rₜđ = ?', options: ['2,4 Ω', '5 Ω', '10 Ω', '24 Ω'], answer: '10 Ω' },
          { id: 'd4', type: 'fill', question: 'Thiết bị 220 V – 1 A tiêu thụ công suất bao nhiêu W? (nhập số)', answer: '220' },
          { id: 'd5', type: 'mcq', question: 'Theo định luật Ôm, I bằng?', options: ['U·R', 'U/R', 'R/U', 'U − R'], answer: 'U/R' },
          { id: 'd6', type: 'fill', question: 'Hai điện trở 3 Ω và 6 Ω mắc SONG SONG. Rₜđ = ? (Ω, nhập số)', answer: '2' },
          { id: 'd7', type: 'mcq', question: 'Đơn vị đo công suất điện?', options: ['Vôn', 'Ampe', 'Oát (W)', 'Ôm'], answer: 'Oát (W)' },
          { id: 'd8', type: 'mcq', question: 'Trong mạch nối tiếp, cường độ dòng điện qua các điện trở?', options: ['bằng nhau', 'khác nhau', 'bằng 0', 'tỉ lệ với R'], answer: 'bằng nhau' }
        ]
      }
    },

    {
      id: 'kh_03',
      index: 3,
      title: 'Quang – Nhiệt',
      subtitle: 'Phản xạ, khúc xạ, thấu kính và nhiệt lượng',
      topic_tag: 'Khoa học · Vật lý',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> Vật lý quang – nhiệt của bạn.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Hiện tượng tia sáng bị gãy khúc khi truyền xiên góc qua mặt phân cách hai môi trường gọi là?',
            options: ['phản xạ', 'khúc xạ', 'tán sắc', 'giao thoa'], answer: 'khúc xạ',
            explain: 'Tia sáng đổi hướng (gãy khúc) khi qua mặt phân cách → khúc xạ ánh sáng.' },
          { id: 't2', type: 'fill', question: 'Đun 2 kg nước (c = 4200 J/kg.K) tăng thêm 10 °C cần nhiệt lượng bao nhiêu J? (nhập số)',
            answer: '84000', explain: 'Q = m·c·Δt = 2 × 4200 × 10 = 84000 J.' },
          { id: 't3', type: 'mcq', question: 'Thấu kính hội tụ cho ảnh THẬT khi vật đặt ở đâu?',
            options: ['trong khoảng tiêu cự', 'ngoài khoảng tiêu cự', 'tại quang tâm', 'ở vô cực'], answer: 'ngoài khoảng tiêu cự',
            explain: 'Vật ngoài tiêu cự (d > f) → ảnh thật, ngược chiều. Vật trong tiêu cự → ảnh ảo, cùng chiều.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-lightbulb', title: 'Phản xạ & khúc xạ',
              body: 'Phản xạ: góc tới = góc phản xạ. Khúc xạ: tia sáng gãy khúc khi qua mặt phân cách hai môi trường trong suốt khác nhau.' },
            { icon: 'fa-temperature-half', title: 'Nhiệt lượng',
              body: 'Nhiệt lượng thu/tỏa: <code>Q = m·c·Δt</code> (J). m khối lượng (kg), c nhiệt dung riêng (J/kg.K), Δt độ tăng/giảm nhiệt độ.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ Quang – Nhiệt',
          cards: [
            { icon: 'fa-arrows-turn-to-dots', title: 'Phản xạ ánh sáng',
              body: 'Tia sáng gặp mặt nhẵn bị hắt lại. Định luật: góc tới = góc phản xạ; tia tới, tia phản xạ và pháp tuyến cùng một mặt phẳng. Gương phẳng cho ảnh ảo, bằng vật.' },
            { icon: 'fa-water', title: 'Khúc xạ ánh sáng',
              body: 'Tia sáng đổi hướng khi truyền xiên qua mặt phân cách hai môi trường (ví dụ chiếc đũa gãy khúc trong cốc nước). Từ môi trường ít chiết quang sang nhiều → tia lệch gần pháp tuyến.' },
            { icon: 'fa-magnifying-glass', title: 'Thấu kính',
              body: 'Hội tụ (rìa mỏng) làm chụm tia; phân kì (rìa dày) làm loe tia. Thấu kính hội tụ: vật ngoài tiêu cự → ảnh thật; trong tiêu cự → ảnh ảo (dùng làm kính lúp).' },
            { icon: 'fa-temperature-half', title: 'Nhiệt lượng & truyền nhiệt',
              body: 'Q = m·c·Δt. Ba cách truyền nhiệt: dẫn nhiệt (rắn), đối lưu (lỏng/khí), bức xạ nhiệt (qua chân không). Vật màu tối hấp thụ nhiệt tốt hơn màu sáng.' }
          ],
          examples: [
            { q: 'Đun 3 kg nước tăng 20 °C (c = 4200). Nhiệt lượng?', sol: 'Q = 3 × 4200 × 20 = 252000 J.' },
            { q: 'Vì sao mùa hè nên mặc áo sáng màu?', sol: 'Màu sáng hấp thụ ít nhiệt bức xạ hơn màu tối → mát hơn.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Phản xạ: góc tới = góc phản xạ; gương phẳng cho ảnh ảo bằng vật.',
          'Khúc xạ: tia sáng gãy khúc khi qua mặt phân cách hai môi trường.',
          'Thấu kính hội tụ: vật ngoài tiêu cự → ảnh thật; trong tiêu cự → ảnh ảo.',
          'Nhiệt lượng Q = m·c·Δt (J).'
        ],
        formula: 'Q = m·c·Δt   |   góc tới = góc phản xạ',
        tip: 'Câu nhiệt lượng HSA chỉ cần thay số vào Q = m·c·Δt — nhớ đổi khối lượng ra kg và Δt là ĐỘ TĂNG nhiệt độ.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Góc tới bằng góc phản xạ là nội dung định luật?', options: ['phản xạ ánh sáng', 'khúc xạ', 'tán sắc', 'giao thoa'], answer: 'phản xạ ánh sáng' },
          { id: 'd2', type: 'fill', question: 'Q = m·c·Δt với m = 1 kg, c = 4200, Δt = 5. Q = ? (J, nhập số)', answer: '21000' },
          { id: 'd3', type: 'mcq', question: 'Ánh sáng đổi hướng khi truyền xiên qua mặt phân cách 2 môi trường là?', options: ['phản xạ', 'khúc xạ', 'nhiễu xạ', 'tán sắc'], answer: 'khúc xạ' },
          { id: 'd4', type: 'mcq', question: 'Thấu kính hội tụ có phần rìa?', options: ['dày hơn giữa', 'mỏng hơn giữa', 'bằng giữa', 'phẳng'], answer: 'mỏng hơn giữa' },
          { id: 'd5', type: 'fill', question: 'Đun 3 kg nước tăng 10 °C (c = 4200). Nhiệt lượng? (J, nhập số)', answer: '126000' },
          { id: 'd6', type: 'mcq', question: 'Đơn vị của nhiệt lượng là?', options: ['Jun (J)', 'Oát', 'Vôn', 'Niutơn'], answer: 'Jun (J)' },
          { id: 'd7', type: 'mcq', question: 'Vật màu đen so với màu trắng thì hấp thụ nhiệt?', options: ['nhiều hơn', 'ít hơn', 'bằng nhau', 'không hấp thụ'], answer: 'nhiều hơn' },
          { id: 'd8', type: 'mcq', question: 'Ảnh của vật qua gương phẳng là ảnh?', options: ['thật, lớn hơn', 'ảo, bằng vật', 'thật, nhỏ hơn', 'ảo, lớn hơn'], answer: 'ảo, bằng vật' }
        ]
      }
    },

    {
      id: 'kh_04',
      index: 4,
      title: 'Dao động & Sóng',
      subtitle: 'Chu kì, tần số, sóng cơ và âm thanh',
      topic_tag: 'Khoa học · Vật lý',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về dao động và sóng.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Chu kì T và tần số f của một dao động liên hệ với nhau như thế nào?',
            options: ['T = f', 'T = 1/f', 'T = 2f', 'T = f²'], answer: 'T = 1/f',
            explain: 'Chu kì và tần số nghịch đảo nhau: T = 1/f (và f = 1/T).' },
          { id: 't2', type: 'fill', question: 'Một dao động có chu kì T = 0,5 s. Tần số f bằng bao nhiêu Hz? (nhập số)',
            answer: '2', explain: 'f = 1/T = 1/0,5 = 2 Hz.' },
          { id: 't3', type: 'mcq', question: 'Âm thanh KHÔNG truyền được trong môi trường nào?',
            options: ['chất rắn', 'chất lỏng', 'chất khí', 'chân không'], answer: 'chân không',
            explain: 'Âm cần môi trường vật chất để truyền → không truyền trong chân không.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-wave-square', title: 'Chu kì & tần số',
              body: 'Chu kì T (giây): thời gian thực hiện MỘT dao động. Tần số f (Hz): số dao động trong MỘT giây. Liên hệ: <code>T = 1/f</code>.' },
            { icon: 'fa-volume-high', title: 'Sóng cơ & âm',
              body: 'Sóng cơ lan truyền dao động trong môi trường vật chất. Âm truyền trong rắn/lỏng/khí, KHÔNG truyền trong chân không; truyền nhanh nhất trong CHẤT RẮN.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ Dao động & Sóng',
          cards: [
            { icon: 'fa-arrows-left-right-to-line', title: 'Dao động điều hòa',
              body: 'Vật lặp lại chuyển động quanh vị trí cân bằng. Biên độ A: độ lệch lớn nhất. Chu kì T: thời gian một dao động. Tần số f = 1/T (Hz).' },
            { icon: 'fa-stopwatch', title: 'Chu kì – Tần số',
              body: 'T (giây) và f (Hz) nghịch đảo: T = 1/f. VD f = 5 Hz → T = 0,2 s. Đếm số dao động trong t giây: f = số dao động / t.' },
            { icon: 'fa-wave-square', title: 'Sóng cơ',
              body: 'Là dao động lan truyền trong môi trường. Bước sóng λ = quãng đường sóng đi trong một chu kì: λ = v·T = v/f (v là tốc độ truyền sóng).' },
            { icon: 'fa-volume-high', title: 'Âm thanh',
              body: 'Âm là sóng cơ. Truyền trong rắn > lỏng > khí; KHÔNG truyền trong chân không. Tần số cao → âm bổng (thanh); tần số thấp → âm trầm.' }
          ],
          examples: [
            { q: 'Vật dao động 20 lần trong 10 giây. Tần số?', sol: 'f = 20/10 = 2 Hz (→ T = 0,5 s).' },
            { q: 'Vì sao áp tai xuống đường ray nghe tàu từ xa rõ hơn?', sol: 'Âm truyền trong chất rắn (đường ray) nhanh và rõ hơn trong không khí.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Chu kì T (s): thời gian 1 dao động. Tần số f (Hz): số dao động trong 1 giây.',
          'Liên hệ: T = 1/f (và f = 1/T).',
          'Biên độ = độ lệch lớn nhất khỏi vị trí cân bằng.',
          'Âm truyền trong rắn/lỏng/khí, KHÔNG truyền trong chân không (nhanh nhất trong rắn).'
        ],
        formula: 'T = 1/f   |   f = số dao động / thời gian   |   λ = v·T',
        tip: 'Bài đếm dao động: f = số lần / số giây rồi lấy T = 1/f — không cần nhớ công thức phức tạp.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Chu kì và tần số liên hệ?', options: ['T = f', 'T = 1/f', 'T = 2f', 'T = f²'], answer: 'T = 1/f' },
          { id: 'd2', type: 'fill', question: 'T = 0,25 s thì tần số f = ? (Hz, nhập số)', answer: '4' },
          { id: 'd3', type: 'mcq', question: 'Số dao động thực hiện trong 1 giây gọi là?', options: ['chu kì', 'tần số', 'biên độ', 'bước sóng'], answer: 'tần số' },
          { id: 'd4', type: 'mcq', question: 'Âm KHÔNG truyền được trong?', options: ['chất rắn', 'chất lỏng', 'chất khí', 'chân không'], answer: 'chân không' },
          { id: 'd5', type: 'fill', question: 'Vật dao động 20 lần trong 10 giây. Tần số f = ? (Hz, nhập số)', answer: '2' },
          { id: 'd6', type: 'mcq', question: 'Đại lượng chỉ độ lệch lớn nhất khỏi vị trí cân bằng?', options: ['biên độ', 'chu kì', 'tần số', 'bước sóng'], answer: 'biên độ' },
          { id: 'd7', type: 'mcq', question: 'Âm thanh truyền NHANH nhất trong môi trường nào?', options: ['chất rắn', 'chất lỏng', 'chất khí', 'chân không'], answer: 'chất rắn' },
          { id: 'd8', type: 'mcq', question: 'Đơn vị của tần số là?', options: ['Héc (Hz)', 'giây (s)', 'mét (m)', 'Vôn (V)'], answer: 'Héc (Hz)' }
        ]
      }
    },

    {
      id: 'kh_05',
      index: 5,
      title: 'Vật lý hạt nhân',
      subtitle: 'Cấu tạo hạt nhân, phóng xạ và phản ứng hạt nhân',
      topic_tag: 'Khoa học · Vật lý',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về vật lý hạt nhân.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Hạt nhân nguyên tử được cấu tạo từ những hạt nào?',
            options: ['proton và electron', 'proton và nơtron', 'nơtron và electron', 'chỉ có proton'], answer: 'proton và nơtron',
            explain: 'Hạt nhân gồm proton (mang điện +) và nơtron (không mang điện). Electron ở lớp vỏ, ngoài hạt nhân.' },
          { id: 't2', type: 'mcq', question: 'Tia phóng xạ nào KHÔNG mang điện?',
            options: ['tia alpha (α)', 'tia beta (β)', 'tia gamma (γ)', 'tia beta cộng (β⁺)'], answer: 'tia gamma (γ)',
            explain: 'Tia α mang điện dương, tia β mang điện âm, tia γ là sóng điện từ KHÔNG mang điện.' },
          { id: 't3', type: 'fill', question: 'Số khối A của hạt nhân bằng tổng số proton và số ___ (điền 1 từ):',
            answer: 'nơtron', explain: 'A = Z (số proton) + N (số nơtron).' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-atom', title: 'Cấu tạo hạt nhân',
              body: 'Hạt nhân gồm proton (điện +) và nơtron (trung hòa). Số proton Z quyết định NGUYÊN TỐ. Số khối <code>A = Z + N</code>.' },
            { icon: 'fa-radiation', title: 'Phóng xạ',
              body: 'Ba loại tia: α (điện dương, đâm xuyên yếu), β (điện âm), γ (sóng điện từ, không mang điện, đâm xuyên mạnh).' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ Vật lý hạt nhân',
          cards: [
            { icon: 'fa-atom', title: 'Cấu tạo hạt nhân',
              body: 'Nguyên tử = hạt nhân (proton + nơtron) + lớp vỏ electron. Proton mang điện +, nơtron trung hòa, electron mang điện −. Bình thường số proton = số electron.' },
            { icon: 'fa-hashtag', title: 'Số hiệu & số khối',
              body: 'Số proton Z (số hiệu nguyên tử) quyết định đó là nguyên tố gì. Số khối A = Z + N (N là số nơtron). Đồng vị: cùng Z nhưng khác N.' },
            { icon: 'fa-radiation', title: 'Ba loại tia phóng xạ',
              body: 'Tia α (hạt nhân heli, điện +, đâm xuyên yếu — chặn bằng tờ giấy). Tia β (electron, điện −, đâm xuyên trung bình). Tia γ (sóng điện từ, không điện, đâm xuyên MẠNH — cần bê tông/chì).' },
            { icon: 'fa-explosion', title: 'Phản ứng hạt nhân',
              body: 'Phân hạch: hạt nhân nặng vỡ thành hạt nhân nhẹ hơn (nhà máy điện nguyên tử). Nhiệt hạch: các hạt nhân nhẹ hợp lại (nguồn năng lượng Mặt Trời) — tỏa năng lượng khổng lồ.' }
          ],
          examples: [
            { q: 'Hạt nhân có Z = 6, N = 6 thì số khối A = ?', sol: 'A = Z + N = 6 + 6 = 12 (đó là Cacbon-12).' },
            { q: 'Nguồn năng lượng của Mặt Trời là phản ứng gì?', sol: 'Phản ứng nhiệt hạch (tổng hợp hạt nhân nhẹ).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Hạt nhân = proton (điện +) + nơtron (trung hòa); electron ở lớp vỏ.',
          'Số proton Z quyết định nguyên tố; số khối A = Z + N.',
          'Ba tia phóng xạ: α (+), β (−), γ (không mang điện, đâm xuyên mạnh nhất).',
          'Phân hạch (vỡ) và nhiệt hạch (hợp) đều tỏa năng lượng lớn.'
        ],
        formula: 'A = Z + N   (Z: số proton, N: số nơtron)',
        tip: 'Nhớ dấu điện 3 tia: alpha +, beta −, gamma trung hòa — câu HSA hay hỏi tia nào (không) mang điện.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Hạt nhân nguyên tử gồm?', options: ['proton và electron', 'proton và nơtron', 'nơtron và electron', 'chỉ nơtron'], answer: 'proton và nơtron' },
          { id: 'd2', type: 'mcq', question: 'Hạt mang điện dương trong hạt nhân là?', options: ['proton', 'nơtron', 'electron', 'photon'], answer: 'proton' },
          { id: 'd3', type: 'mcq', question: 'Tia phóng xạ mang điện âm là?', options: ['tia alpha (α)', 'tia beta (β)', 'tia gamma (γ)', 'tia X'], answer: 'tia beta (β)' },
          { id: 'd4', type: 'fill', question: 'Số khối A = số proton + số ___ (điền 1 từ):', answer: 'nơtron' },
          { id: 'd5', type: 'mcq', question: 'Tia phóng xạ KHÔNG mang điện là?', options: ['tia alpha (α)', 'tia beta (β)', 'tia gamma (γ)', 'tia beta cộng (β⁺)'], answer: 'tia gamma (γ)' },
          { id: 'd6', type: 'mcq', question: 'Nguồn năng lượng của Mặt Trời là phản ứng?', options: ['phân hạch', 'nhiệt hạch', 'ion hóa', 'oxi hóa'], answer: 'nhiệt hạch' },
          { id: 'd7', type: 'mcq', question: 'Số proton (Z) quyết định điều gì?', options: ['loại nguyên tố', 'khối lượng riêng', 'màu sắc', 'nhiệt độ'], answer: 'loại nguyên tố' },
          { id: 'd8', type: 'mcq', question: 'Hạt KHÔNG mang điện trong hạt nhân là?', options: ['proton', 'nơtron', 'electron', 'ion'], answer: 'nơtron' }
        ]
      }
    },

    {
      id: 'kh_06',
      index: 6,
      title: 'Nguyên tử & Bảng tuần hoàn',
      subtitle: 'Cấu tạo nguyên tử, chu kì và nhóm',
      topic_tag: 'Khoa học · Hóa học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> Hóa học của bạn về nguyên tử.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Nguyên tử được cấu tạo từ những phần nào?',
            options: ['hạt nhân và lớp vỏ electron', 'chỉ hạt nhân', 'chỉ electron', 'proton và ion'], answer: 'hạt nhân và lớp vỏ electron',
            explain: 'Nguyên tử gồm hạt nhân (ở giữa) và lớp vỏ electron chuyển động xung quanh.' },
          { id: 't2', type: 'mcq', question: 'Hạt mang điện ÂM trong nguyên tử là?',
            options: ['proton', 'nơtron', 'electron', 'ion'], answer: 'electron',
            explain: 'Electron mang điện âm, ở lớp vỏ. Proton mang điện dương, nơtron trung hòa.' },
          { id: 't3', type: 'mcq', question: 'Trong bảng tuần hoàn, các nguyên tố được sắp xếp theo chiều TĂNG DẦN của?',
            options: ['khối lượng riêng', 'số proton (số hiệu nguyên tử)', 'màu sắc', 'độ cứng'], answer: 'số proton (số hiệu nguyên tử)',
            explain: 'Các nguyên tố xếp theo chiều tăng dần điện tích hạt nhân (số proton = số hiệu nguyên tử).' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-atom', title: 'Cấu tạo nguyên tử',
              body: 'Hạt nhân (proton + nơtron) ở giữa; electron mang điện âm chuyển động ở lớp vỏ. Bình thường số proton = số electron nên nguyên tử trung hòa điện.' },
            { icon: 'fa-table-cells', title: 'Bảng tuần hoàn (BTH)',
              body: 'Nguyên tố xếp theo số proton tăng dần. HÀNG = chu kì; CỘT = nhóm (các nguyên tố cùng nhóm có tính chất hóa học giống nhau).' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ nguyên tử & BTH',
          cards: [
            { icon: 'fa-atom', title: 'Cấu tạo nguyên tử',
              body: 'Nguyên tử = hạt nhân + lớp vỏ. Hạt nhân chứa proton (điện +) và nơtron (trung hòa). Vỏ chứa electron (điện −). Kích thước rất nhỏ, khối lượng tập trung ở hạt nhân.' },
            { icon: 'fa-hashtag', title: 'Số hiệu & điện tích',
              body: 'Số hiệu nguyên tử Z = số proton = số electron (nguyên tử trung hòa). Z đặc trưng cho MỖI nguyên tố hóa học.' },
            { icon: 'fa-table-cells', title: 'Cấu trúc bảng tuần hoàn',
              body: 'Xếp theo Z tăng dần. Chu kì (hàng ngang): số lớp electron. Nhóm (cột dọc): số electron lớp ngoài cùng, quyết định tính chất hóa học.' },
            { icon: 'fa-arrow-right-long', title: 'Quy luật biến đổi',
              body: 'Trong một chu kì (trái → phải): tính kim loại giảm, tính phi kim tăng. Trong một nhóm (trên → xuống): tính kim loại tăng.' }
          ],
          examples: [
            { q: 'Nguyên tố có Z = 11 có bao nhiêu electron?', sol: 'Z = số electron = 11 (đó là Natri).' },
            { q: 'Các nguyên tố cùng một nhóm có gì giống nhau?', sol: 'Cùng số electron lớp ngoài cùng → tính chất hóa học tương tự.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Nguyên tử = hạt nhân (proton + nơtron) + lớp vỏ electron.',
          'Proton (+), nơtron (trung hòa), electron (−); Z = số proton = số electron.',
          'BTH xếp theo Z tăng dần: chu kì = hàng, nhóm = cột.',
          'Cùng nhóm → cùng số e ngoài cùng → tính chất hóa học giống nhau.'
        ],
        formula: 'Z (số hiệu) = số proton = số electron',
        tip: 'Nhớ nhóm quyết định tính chất hóa học (số e ngoài cùng) — đây là ý HSA hay hỏi về BTH.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Hạt mang điện dương trong nguyên tử?', options: ['proton', 'nơtron', 'electron', 'ion'], answer: 'proton' },
          { id: 'd2', type: 'mcq', question: 'Electron mang điện?', options: ['dương', 'âm', 'trung hòa', 'thay đổi'], answer: 'âm' },
          { id: 'd3', type: 'mcq', question: 'Số hiệu nguyên tử Z bằng?', options: ['số proton', 'số nơtron', 'số khối', 'khối lượng'], answer: 'số proton' },
          { id: 'd4', type: 'fill', question: 'Nguyên tử có Z = 8 thì có bao nhiêu electron? (nhập số)', answer: '8' },
          { id: 'd5', type: 'mcq', question: 'Hàng ngang trong bảng tuần hoàn gọi là?', options: ['chu kì', 'nhóm', 'phân lớp', 'ô'], answer: 'chu kì' },
          { id: 'd6', type: 'mcq', question: 'Cột dọc trong bảng tuần hoàn gọi là?', options: ['chu kì', 'nhóm', 'lớp', 'chu trình'], answer: 'nhóm' },
          { id: 'd7', type: 'mcq', question: 'Nguyên tố xếp trong BTH theo?', options: ['số proton tăng dần', 'màu sắc', 'khối lượng riêng', 'độ cứng'], answer: 'số proton tăng dần' },
          { id: 'd8', type: 'mcq', question: 'Nguyên tử trung hòa điện vì?', options: ['số proton = số electron', 'không có electron', 'không có proton', 'chỉ có nơtron'], answer: 'số proton = số electron' }
        ]
      }
    },

    {
      id: 'kh_07',
      index: 7,
      title: 'Liên kết & Phản ứng',
      subtitle: 'Liên kết hóa học và phương trình phản ứng',
      topic_tag: 'Khoa học · Hóa học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về liên kết và phản ứng.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Liên kết hình thành do lực hút giữa các ion trái dấu gọi là?',
            options: ['liên kết ion', 'liên kết cộng hóa trị', 'liên kết kim loại', 'liên kết hidro'], answer: 'liên kết ion',
            explain: 'Ion dương và ion âm hút nhau tạo liên kết ion (VD NaCl).' },
          { id: 't2', type: 'fill', question: 'Trong phương trình đã cân bằng 2H₂ + O₂ → 2H₂O, hệ số của H₂ là bao nhiêu? (nhập số)',
            answer: '2', explain: 'Cân bằng để số nguyên tử mỗi bên bằng nhau → hệ số H₂ là 2.' },
          { id: 't3', type: 'mcq', question: 'Phản ứng hóa học kèm theo sự TỎA nhiệt được gọi là phản ứng?',
            options: ['tỏa nhiệt', 'thu nhiệt', 'phân hủy', 'trao đổi'], answer: 'tỏa nhiệt',
            explain: 'Phản ứng tỏa nhiệt giải phóng năng lượng ra môi trường (VD đốt cháy).' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-link', title: 'Liên kết hóa học',
              body: 'Liên kết ION: cho – nhận electron, giữa kim loại & phi kim (NaCl). Liên kết CỘNG HÓA TRỊ: dùng chung electron, giữa các phi kim (H₂O, CO₂).' },
            { icon: 'fa-flask', title: 'Phản ứng & bảo toàn',
              body: 'Phương trình hóa học phải CÂN BẰNG số nguyên tử mỗi nguyên tố hai vế. Định luật bảo toàn khối lượng: tổng m chất phản ứng = tổng m sản phẩm.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ liên kết & phản ứng',
          cards: [
            { icon: 'fa-plus-minus', title: 'Liên kết ion',
              body: 'Hình thành khi nguyên tử CHO và NHẬN electron, tạo ion trái dấu hút nhau. Thường giữa kim loại điển hình và phi kim điển hình. VD: NaCl, MgO.' },
            { icon: 'fa-share-nodes', title: 'Liên kết cộng hóa trị',
              body: 'Các nguyên tử DÙNG CHUNG cặp electron. Thường giữa các phi kim. VD: H₂, O₂, H₂O, CO₂.' },
            { icon: 'fa-flask', title: 'Phản ứng hóa học',
              body: 'Chất phản ứng biến đổi thành chất mới. Dấu hiệu: đổi màu, tạo kết tủa, sinh khí, tỏa/thu nhiệt. Viết bằng phương trình hóa học.' },
            { icon: 'fa-scale-balanced', title: 'Cân bằng & bảo toàn khối lượng',
              body: 'Phương trình cân bằng khi số nguyên tử mỗi nguyên tố hai vế bằng nhau. Định luật bảo toàn khối lượng: m(phản ứng) = m(sản phẩm).' }
          ],
          examples: [
            { q: 'NaCl có liên kết gì?', sol: 'Liên kết ion (Na cho e, Cl nhận e → Na⁺ và Cl⁻).' },
            { q: 'Cân bằng: Fe + O₂ → Fe₂O₃.', sol: '4Fe + 3O₂ → 2Fe₂O₃.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Liên kết ion: cho–nhận electron (kim loại + phi kim), VD NaCl.',
          'Liên kết cộng hóa trị: dùng chung electron (phi kim), VD H₂O.',
          'Phương trình phải cân bằng số nguyên tử mỗi nguyên tố hai vế.',
          'Bảo toàn khối lượng: m chất phản ứng = m sản phẩm.'
        ],
        formula: 'm(chất phản ứng) = m(sản phẩm)   (định luật bảo toàn khối lượng)',
        tip: 'Cân bằng phương trình: chỉnh hệ số (số đứng trước công thức), tuyệt đối KHÔNG đổi chỉ số trong công thức.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'NaCl có loại liên kết gì?', options: ['liên kết ion', 'cộng hóa trị', 'kim loại', 'hidro'], answer: 'liên kết ion' },
          { id: 'd2', type: 'mcq', question: 'H₂O có loại liên kết gì?', options: ['ion', 'cộng hóa trị', 'kim loại', 'ion và kim loại'], answer: 'cộng hóa trị' },
          { id: 'd3', type: 'fill', question: 'Cân bằng 2H₂ + O₂ → 2H₂O, hệ số của O₂ là? (nhập số)', answer: '1' },
          { id: 'd4', type: 'mcq', question: 'Phản ứng đốt cháy thường là phản ứng?', options: ['tỏa nhiệt', 'thu nhiệt', 'không đổi nhiệt', 'phân hủy nước'], answer: 'tỏa nhiệt' },
          { id: 'd5', type: 'mcq', question: 'Định luật bảo toàn khối lượng phát biểu?', options: ['m phản ứng = m sản phẩm', 'm giảm dần', 'm tăng dần', 'm bằng 0'], answer: 'm phản ứng = m sản phẩm' },
          { id: 'd6', type: 'mcq', question: 'Liên kết dùng chung cặp electron là?', options: ['ion', 'cộng hóa trị', 'kim loại', 'hidro'], answer: 'cộng hóa trị' },
          { id: 'd7', type: 'mcq', question: 'Dấu hiệu nhận biết có phản ứng hóa học?', options: ['đổi màu, tạo kết tủa, sinh khí', 'nóng chảy', 'bay hơi', 'đông đặc'], answer: 'đổi màu, tạo kết tủa, sinh khí' },
          { id: 'd8', type: 'mcq', question: 'Khi cân bằng phương trình, ta chỉnh?', options: ['hệ số trước công thức', 'chỉ số trong công thức', 'tên chất', 'trạng thái chất'], answer: 'hệ số trước công thức' }
        ]
      }
    },

    {
      id: 'kh_08',
      index: 8,
      title: 'Hóa vô cơ trọng tâm',
      subtitle: 'Oxit, axit, bazơ, muối và phản ứng',
      topic_tag: 'Khoa học · Hóa học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về hóa vô cơ.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Chất nào sau đây là AXIT?',
            options: ['NaOH', 'HCl', 'NaCl', 'CaO'], answer: 'HCl',
            explain: 'HCl (axit clohidric) là axit. NaOH là bazơ, NaCl là muối, CaO là oxit.' },
          { id: 't2', type: 'mcq', question: 'Dung dịch BAZƠ làm quỳ tím chuyển sang màu gì?',
            options: ['đỏ', 'xanh', 'tím', 'không đổi'], answer: 'xanh',
            explain: 'Bazơ làm quỳ tím hóa xanh; axit làm quỳ tím hóa đỏ.' },
          { id: 't3', type: 'mcq', question: 'Phản ứng giữa axit và bazơ tạo thành muối và nước gọi là phản ứng?',
            options: ['oxi hóa', 'trung hòa', 'phân hủy', 'thế'], answer: 'trung hòa',
            explain: 'Axit + bazơ → muối + nước là phản ứng trung hòa. VD: HCl + NaOH → NaCl + H₂O.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-vial', title: 'Bốn loại hợp chất vô cơ',
              body: 'OXIT (nguyên tố + O, vd CaO), AXIT (H + gốc axit, vd HCl), BAZƠ (kim loại + OH, vd NaOH), MUỐI (kim loại + gốc axit, vd NaCl).' },
            { icon: 'fa-flask-vial', title: 'Nhận biết bằng quỳ tím',
              body: 'Axit → quỳ tím hóa ĐỎ. Bazơ → quỳ tím hóa XANH. Muối trung tính → không đổi màu.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ hóa vô cơ',
          cards: [
            { icon: 'fa-o', title: 'Oxit',
              body: 'Hợp chất của oxi với một nguyên tố khác. Oxit bazơ (CaO, Na₂O — của kim loại), oxit axit (CO₂, SO₂ — của phi kim).' },
            { icon: 'fa-droplet', title: 'Axit',
              body: 'Phân tử có một hay nhiều nguyên tử H liên kết với gốc axit (HCl, H₂SO₄, HNO₃). Làm quỳ tím hóa đỏ; tác dụng với kim loại giải phóng H₂.' },
            { icon: 'fa-soap', title: 'Bazơ',
              body: 'Gồm kim loại liên kết với nhóm OH (NaOH, Ca(OH)₂). Dung dịch bazơ (kiềm) làm quỳ tím hóa xanh, làm phenolphtalein hóa hồng.' },
            { icon: 'fa-cubes', title: 'Muối & phản ứng trung hòa',
              body: 'Muối gồm kim loại + gốc axit (NaCl, CaCO₃). Phản ứng trung hòa: axit + bazơ → muối + nước. VD: HCl + NaOH → NaCl + H₂O.' }
          ],
          examples: [
            { q: 'Phân loại: CaO, HCl, NaOH, NaCl.', sol: 'CaO – oxit; HCl – axit; NaOH – bazơ; NaCl – muối.' },
            { q: 'Viết phản ứng trung hòa của H₂SO₄ và NaOH.', sol: 'H₂SO₄ + 2NaOH → Na₂SO₄ + 2H₂O.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Bốn loại: oxit (…+O), axit (H+gốc), bazơ (KL+OH), muối (KL+gốc axit).',
          'Quỳ tím: axit → đỏ, bazơ → xanh, muối trung tính → không đổi.',
          'Axit + bazơ → muối + nước (phản ứng trung hòa).',
          'Axit + kim loại → muối + khí H₂.'
        ],
        formula: 'axit + bazơ → muối + nước   (trung hòa)',
        tip: 'Nhận diện loại chất qua công thức: có H đầu → axit; có OH cuối → bazơ; kim loại + gốc axit → muối.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Chất nào là BAZƠ?', options: ['HCl', 'NaOH', 'NaCl', 'CO₂'], answer: 'NaOH' },
          { id: 'd2', type: 'mcq', question: 'Axit làm quỳ tím chuyển màu?', options: ['đỏ', 'xanh', 'tím', 'vàng'], answer: 'đỏ' },
          { id: 'd3', type: 'mcq', question: 'NaCl thuộc loại hợp chất?', options: ['oxit', 'axit', 'bazơ', 'muối'], answer: 'muối' },
          { id: 'd4', type: 'mcq', question: 'CaO thuộc loại?', options: ['oxit', 'axit', 'bazơ', 'muối'], answer: 'oxit' },
          { id: 'd5', type: 'mcq', question: 'Axit + bazơ → ?', options: ['muối + nước', 'oxit + khí', 'kim loại + nước', 'chỉ khí'], answer: 'muối + nước' },
          { id: 'd6', type: 'mcq', question: 'Axit tác dụng với kim loại thường sinh ra khí?', options: ['H₂', 'O₂', 'CO₂', 'N₂'], answer: 'H₂' },
          { id: 'd7', type: 'mcq', question: 'Bazơ làm phenolphtalein chuyển màu?', options: ['hồng', 'xanh', 'vàng', 'đen'], answer: 'hồng' },
          { id: 'd8', type: 'mcq', question: 'H₂SO₄ là?', options: ['axit', 'bazơ', 'muối', 'oxit'], answer: 'axit' }
        ]
      }
    },

    {
      id: 'kh_09',
      index: 9,
      title: 'Hóa hữu cơ trọng tâm',
      subtitle: 'Hidrocacbon, nhóm chức và hợp chất quen thuộc',
      topic_tag: 'Khoa học · Hóa học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về hóa hữu cơ.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Hợp chất hữu cơ là hợp chất của nguyên tố nào?',
            options: ['cacbon (C)', 'sắt (Fe)', 'natri (Na)', 'oxi (O)'], answer: 'cacbon (C)',
            explain: 'Hợp chất hữu cơ là hợp chất của cacbon (trừ CO, CO₂, muối cacbonat…).' },
          { id: 't2', type: 'mcq', question: 'Công thức hóa học của khí metan là?',
            options: ['CH₄', 'C₂H₆', 'C₂H₄', 'CO₂'], answer: 'CH₄',
            explain: 'Metan là hidrocacbon đơn giản nhất, công thức CH₄.' },
          { id: 't3', type: 'mcq', question: 'Rượu etylic (ancol etylic C₂H₅OH) có nhóm chức nào?',
            options: ['−OH (hidroxyl)', '−COOH (cacboxyl)', '−CHO (anđehit)', '−NH₂ (amino)'], answer: '−OH (hidroxyl)',
            explain: 'Ancol có nhóm chức −OH. Axit có −COOH.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-c', title: 'Hợp chất hữu cơ',
              body: 'Là hợp chất của CACBON (trừ CO, CO₂, muối cacbonat…). Thường gồm C, H, có thể thêm O, N. Hidrocacbon chỉ gồm C và H.' },
            { icon: 'fa-tags', title: 'Nhóm chức quen',
              body: '−OH (ancol/rượu), −COOH (axit hữu cơ). VD: C₂H₅OH là rượu, CH₃COOH là axit axetic (giấm ăn).' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ hóa hữu cơ',
          cards: [
            { icon: 'fa-c', title: 'Đặc điểm hợp chất hữu cơ',
              body: 'Là hợp chất của cacbon (trừ một số như CO, CO₂, muối cacbonat). Đa số dễ cháy, kém bền nhiệt, phản ứng thường chậm và theo nhiều hướng.' },
            { icon: 'fa-link', title: 'Hidrocacbon',
              body: 'Chỉ gồm C và H. Metan CH₄ (ankan), etilen C₂H₄ (anken, có liên kết đôi), axetilen C₂H₂. Là nhiên liệu và nguyên liệu quan trọng.' },
            { icon: 'fa-tags', title: 'Nhóm chức',
              body: 'Nhóm nguyên tử gây ra tính chất đặc trưng: −OH (ancol), −COOH (axit cacboxylic), −CHO (anđehit). Nhận biết chất qua nhóm chức.' },
            { icon: 'fa-wine-bottle', title: 'Một số chất quen thuộc',
              body: 'Metan CH₄ (khí bùn ao, khí gas). Rượu etylic C₂H₅OH. Axit axetic CH₃COOH (giấm). Glucozơ C₆H₁₂O₆ (đường).' }
          ],
          examples: [
            { q: 'C₂H₅OH là chất gì và có nhóm chức nào?', sol: 'Rượu etylic, nhóm chức −OH.' },
            { q: 'Giấm ăn có thành phần chính là axit gì?', sol: 'Axit axetic CH₃COOH (nhóm −COOH).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Hợp chất hữu cơ = hợp chất của cacbon (trừ CO, CO₂, cacbonat).',
          'Hidrocacbon chỉ gồm C và H (metan CH₄, etilen C₂H₄).',
          'Nhóm chức: −OH (ancol), −COOH (axit hữu cơ).',
          'Chất quen: rượu C₂H₅OH, axit axetic CH₃COOH (giấm), glucozơ.'
        ],
        formula: 'Metan CH₄   |   Rượu etylic C₂H₅OH   |   Axit axetic CH₃COOH',
        tip: 'Nhận diện qua nhóm chức: thấy −OH nghĩ tới rượu; thấy −COOH nghĩ tới axit hữu cơ.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Hợp chất hữu cơ là hợp chất của?', options: ['cacbon', 'sắt', 'natri', 'canxi'], answer: 'cacbon' },
          { id: 'd2', type: 'mcq', question: 'Công thức của metan?', options: ['CH₄', 'C₂H₆', 'CO₂', 'H₂O'], answer: 'CH₄' },
          { id: 'd3', type: 'mcq', question: 'Nhóm chức của ancol (rượu) là?', options: ['−OH', '−COOH', '−CHO', '−NH₂'], answer: '−OH' },
          { id: 'd4', type: 'mcq', question: 'Axit axetic (giấm) có công thức?', options: ['CH₃COOH', 'C₂H₅OH', 'CH₄', 'CO₂'], answer: 'CH₃COOH' },
          { id: 'd5', type: 'mcq', question: 'Hidrocacbon gồm những nguyên tố?', options: ['C và H', 'C và O', 'H và O', 'C, H, N'], answer: 'C và H' },
          { id: 'd6', type: 'mcq', question: 'Nhóm chức của axit hữu cơ là?', options: ['−OH', '−COOH', '−CHO', '−O−'], answer: '−COOH' },
          { id: 'd7', type: 'mcq', question: 'Chất nào KHÔNG phải hợp chất hữu cơ?', options: ['CH₄', 'C₂H₅OH', 'CO₂', 'CH₃COOH'], answer: 'CO₂' },
          { id: 'd8', type: 'mcq', question: 'Rượu etylic có công thức?', options: ['C₂H₅OH', 'CH₃COOH', 'CH₄', 'C₆H₁₂O₆'], answer: 'C₂H₅OH' }
        ]
      }
    },

    {
      id: 'kh_10',
      index: 10,
      title: 'Tính toán hóa học',
      subtitle: 'Mol, khối lượng và tính theo phương trình',
      topic_tag: 'Khoa học · Hóa học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về tính toán hóa học.',
        questions: [
          { id: 't1', type: 'fill', question: 'Số mol của 36 gam nước (M = 18 g/mol) là bao nhiêu mol? (nhập số)',
            answer: '2', explain: 'n = m/M = 36/18 = 2 mol.' },
          { id: 't2', type: 'mcq', question: 'Công thức tính số mol từ khối lượng và khối lượng mol là?',
            options: ['n = m·M', 'n = m/M', 'n = M/m', 'n = m + M'], answer: 'n = m/M',
            explain: 'Số mol n = khối lượng m chia cho khối lượng mol M.' },
          { id: 't3', type: 'fill', question: 'Khối lượng của 0,5 mol NaOH (M = 40 g/mol) là bao nhiêu gam? (nhập số)',
            answer: '20', explain: 'm = n·M = 0,5 × 40 = 20 g.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-weight-scale', title: 'Mol & khối lượng',
              body: 'Số mol: <code>n = m/M</code> (m: gam, M: khối lượng mol g/mol). Suy ra m = n·M. Đây là công thức lõi của mọi bài tính hóa.' },
            { icon: 'fa-wind', title: 'Thể tích khí (đktc)',
              body: 'Ở điều kiện tiêu chuẩn: <code>V = n × 22,4</code> (lít). Suy ra n = V/22,4.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ tính toán hóa học',
          cards: [
            { icon: 'fa-hashtag', title: 'Khái niệm mol',
              body: 'Mol là lượng chất chứa 6,022×10²³ hạt (số Avogadro). Khối lượng mol M (g/mol) là khối lượng của 1 mol chất, bằng số phân tử khối tính theo gam.' },
            { icon: 'fa-weight-scale', title: 'Công thức n = m/M',
              body: 'Số mol n = m/M. Từ đó tính khối lượng m = n·M. VD: 36 g nước (M=18) → n = 2 mol.' },
            { icon: 'fa-wind', title: 'Thể tích chất khí',
              body: 'Với chất khí ở đktc: V = n × 22,4 (lít). VD 0,5 mol khí O₂ ở đktc chiếm 0,5 × 22,4 = 11,2 lít.' },
            { icon: 'fa-equals', title: 'Tính theo phương trình hóa học',
              body: 'Dùng hệ số phương trình làm tỉ lệ mol giữa các chất. Bước: viết & cân bằng PT → đổi dữ kiện ra mol → dùng tỉ lệ → đổi ra đại lượng cần tìm.' }
          ],
          examples: [
            { q: 'Tính số mol của 8 g NaOH (M = 40).', sol: 'n = 8/40 = 0,2 mol.' },
            { q: '0,25 mol khí CO₂ ở đktc có thể tích bao nhiêu lít?', sol: 'V = 0,25 × 22,4 = 5,6 lít.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Số mol: n = m/M (m gam, M g/mol); m = n·M.',
          'Thể tích khí ở đktc: V = n × 22,4 (lít).',
          'Số Avogadro: 1 mol chứa 6,022×10²³ hạt.',
          'Tính theo PT: đổi ra mol → dùng tỉ lệ hệ số → đổi ngược lại.'
        ],
        formula: 'n = m/M   |   m = n·M   |   V(khí, đktc) = n × 22,4',
        tip: 'Mọi bài tính hóa đều quy về MOL trước: đổi khối lượng/thể tích ra mol rồi mới dùng tỉ lệ phương trình.'
      },
      drill: {
        time_seconds: 85,
        questions: [
          { id: 'd1', type: 'fill', question: 'Số mol của 18 g nước (M = 18)? (mol, nhập số)', answer: '1' },
          { id: 'd2', type: 'mcq', question: 'Công thức tính số mol theo khối lượng?', options: ['n = m·M', 'n = m/M', 'n = M/m', 'n = m − M'], answer: 'n = m/M' },
          { id: 'd3', type: 'fill', question: 'Khối lượng của 2 mol NaOH (M = 40)? (gam, nhập số)', answer: '80' },
          { id: 'd4', type: 'fill', question: 'Số mol của 8 g NaOH (M = 40)? (mol, nhập số dạng 0,2 → nhập)', answer: '0,2' },
          { id: 'd5', type: 'mcq', question: 'Thể tích 1 mol khí ở đktc là?', options: ['22,4 lít', '18 lít', '24 lít', '1 lít'], answer: '22,4 lít' },
          { id: 'd6', type: 'fill', question: 'Thể tích của 2 mol khí O₂ ở đktc? (lít, nhập số dạng 44,8 → nhập)', answer: '44,8' },
          { id: 'd7', type: 'mcq', question: 'Muốn tính theo phương trình, đầu tiên phải?', options: ['đổi dữ kiện ra mol', 'đổi ra gam', 'đổi ra lít', 'bỏ hệ số'], answer: 'đổi dữ kiện ra mol' },
          { id: 'd8', type: 'fill', question: 'Khối lượng của 0,5 mol H₂O (M = 18)? (gam, nhập số)', answer: '9' }
        ]
      }
    },

    {
      id: 'kh_11',
      index: 11,
      title: 'Tế bào & Chuyển hóa',
      subtitle: 'Cấu tạo tế bào, quang hợp và hô hấp',
      topic_tag: 'Khoa học · Sinh học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> Sinh học của bạn về tế bào.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Đơn vị cấu tạo cơ bản của mọi cơ thể sống là gì?',
            options: ['tế bào', 'nguyên tử', 'phân tử', 'cơ quan'], answer: 'tế bào',
            explain: 'Tế bào là đơn vị cấu tạo và chức năng cơ bản của cơ thể sống.' },
          { id: 't2', type: 'mcq', question: 'Quá trình cây xanh dùng ánh sáng tổng hợp chất hữu cơ từ CO₂ và nước gọi là?',
            options: ['quang hợp', 'hô hấp', 'thoát hơi nước', 'tiêu hóa'], answer: 'quang hợp',
            explain: 'Quang hợp: CO₂ + H₂O + ánh sáng → glucozơ + O₂.' },
          { id: 't3', type: 'mcq', question: 'Bào quan thực hiện quang hợp trong tế bào thực vật là?',
            options: ['lục lạp', 'ti thể', 'nhân', 'ribôxôm'], answer: 'lục lạp',
            explain: 'Lục lạp chứa diệp lục, nơi diễn ra quang hợp. Ti thể thực hiện hô hấp.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-border-all', title: 'Tế bào',
              body: 'Đơn vị cấu tạo cơ bản của sự sống. Gồm màng, chất tế bào và nhân. Tế bào thực vật có thêm THÀNH tế bào và LỤC LẠP.' },
            { icon: 'fa-leaf', title: 'Quang hợp & hô hấp',
              body: 'Quang hợp (ở lục lạp): CO₂ + H₂O + ánh sáng → glucozơ + O₂. Hô hấp (ở ti thể): phân giải glucozơ → năng lượng + CO₂ + H₂O.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ tế bào & chuyển hóa',
          cards: [
            { icon: 'fa-border-all', title: 'Cấu tạo tế bào',
              body: 'Ba thành phần chính: màng tế bào (bao bọc, kiểm soát trao đổi chất), chất tế bào (chứa bào quan), nhân (điều khiển). Tế bào thực vật thêm thành xenlulozơ, không bào, lục lạp.' },
            { icon: 'fa-industry', title: 'Bào quan',
              body: 'Lục lạp: quang hợp (thực vật). Ti thể: hô hấp tế bào, tạo năng lượng (nhà máy điện). Ribôxôm: tổng hợp protein. Nhân: chứa vật chất di truyền.' },
            { icon: 'fa-leaf', title: 'Quang hợp',
              body: 'Cây xanh biến CO₂ và nước thành chất hữu cơ (glucozơ) và nhả O₂ nhờ ánh sáng và diệp lục. Là nguồn thức ăn và oxi cho sự sống.' },
            { icon: 'fa-fire', title: 'Hô hấp tế bào',
              body: 'Phân giải glucozơ trong ti thể để giải phóng năng lượng cho hoạt động sống, tạo ra CO₂ và H₂O. Ngược chiều với quang hợp.' }
          ],
          examples: [
            { q: 'Khí thải ra khi cây quang hợp là gì?', sol: 'Khí oxi (O₂).' },
            { q: 'Bào quan nào tạo năng lượng cho tế bào?', sol: 'Ti thể (qua hô hấp tế bào).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Tế bào = đơn vị cấu tạo cơ bản của cơ thể sống.',
          'Quang hợp (lục lạp): CO₂ + H₂O + ánh sáng → glucozơ + O₂.',
          'Hô hấp (ti thể): glucozơ → năng lượng + CO₂ + H₂O.',
          'Tế bào thực vật có thành tế bào và lục lạp; tế bào động vật thì không.'
        ],
        formula: 'Quang hợp: CO₂ + H₂O + ánh sáng → glucozơ + O₂',
        tip: 'Nhớ cặp đối lập: lục lạp–quang hợp–nhả O₂ ↔ ti thể–hô hấp–thải CO₂.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Đơn vị cơ bản của cơ thể sống?', options: ['tế bào', 'nguyên tử', 'mô', 'cơ quan'], answer: 'tế bào' },
          { id: 'd2', type: 'mcq', question: 'Bào quan quang hợp?', options: ['lục lạp', 'ti thể', 'nhân', 'màng'], answer: 'lục lạp' },
          { id: 'd3', type: 'mcq', question: 'Bào quan hô hấp, tạo năng lượng?', options: ['lục lạp', 'ti thể', 'nhân', 'ribôxôm'], answer: 'ti thể' },
          { id: 'd4', type: 'mcq', question: 'Khí cây nhả ra khi quang hợp?', options: ['O₂', 'CO₂', 'N₂', 'H₂'], answer: 'O₂' },
          { id: 'd5', type: 'mcq', question: 'Quang hợp cần yếu tố nào?', options: ['ánh sáng', 'bóng tối', 'muối', 'axit'], answer: 'ánh sáng' },
          { id: 'd6', type: 'mcq', question: 'Bào quan tổng hợp protein?', options: ['ribôxôm', 'lục lạp', 'ti thể', 'không bào'], answer: 'ribôxôm' },
          { id: 'd7', type: 'mcq', question: 'Tế bào thực vật KHÁC động vật ở chỗ có?', options: ['thành tế bào & lục lạp', 'không có nhân', 'không có màng', 'không có ti thể'], answer: 'thành tế bào & lục lạp' },
          { id: 'd8', type: 'mcq', question: 'Hô hấp tế bào thải ra khí?', options: ['CO₂', 'O₂', 'N₂', 'H₂'], answer: 'CO₂' }
        ]
      }
    },

    {
      id: 'kh_12',
      index: 12,
      title: 'Di truyền',
      subtitle: 'Gen, ADN và quy luật di truyền',
      topic_tag: 'Khoa học · Sinh học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về di truyền.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Vật chất di truyền chủ yếu ở cấp độ phân tử là?',
            options: ['ADN', 'protein', 'lipit', 'gluxit'], answer: 'ADN',
            explain: 'ADN mang thông tin di truyền, quy định các tính trạng.' },
          { id: 't2', type: 'mcq', question: 'Gen là gì?',
            options: ['một đoạn ADN mang thông tin di truyền', 'một loại protein', 'một tế bào', 'một bào quan'], answer: 'một đoạn ADN mang thông tin di truyền',
            explain: 'Gen là một đoạn của phân tử ADN, quy định một tính trạng.' },
          { id: 't3', type: 'mcq', question: 'Người đầu tiên phát hiện ra các quy luật di truyền cơ bản là?',
            options: ['Menđen', 'Đacuyn', 'Newton', 'Pasteur'], answer: 'Menđen',
            explain: 'Menđen (Mendel) nghiên cứu trên cây đậu Hà Lan, tìm ra quy luật di truyền.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-dna', title: 'ADN & gen',
              body: 'ADN là vật chất di truyền, cấu trúc xoắn kép. GEN là một đoạn ADN quy định một tính trạng. Nhiễm sắc thể chứa ADN.' },
            { icon: 'fa-seedling', title: 'Di truyền Menđen',
              body: 'Menđen tìm ra quy luật phân li và phân li độc lập. Tính trạng do cặp gen quy định; con nhận một gen từ bố, một từ mẹ.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ di truyền',
          cards: [
            { icon: 'fa-dna', title: 'ADN — vật chất di truyền',
              body: 'ADN (axit đêôxiribônuclêic) là phân tử xoắn kép, mang thông tin di truyền. Trình tự các nuclêôtit mã hóa thông tin quy định tính trạng.' },
            { icon: 'fa-code', title: 'Gen & nhiễm sắc thể',
              body: 'Gen là một đoạn ADN quy định một tính trạng (màu hoa, chiều cao…). ADN nằm trên nhiễm sắc thể (NST) trong nhân tế bào.' },
            { icon: 'fa-seedling', title: 'Quy luật Menđen',
              body: 'Nghiên cứu đậu Hà Lan, Menđen tìm ra: tính trạng do cặp nhân tố (gen) quy định; khi tạo giao tử, mỗi giao tử chỉ nhận một gen của cặp.' },
            { icon: 'fa-people-arrows', title: 'Di truyền & biến dị',
              body: 'Di truyền: con giống bố mẹ (nhờ ADN truyền lại). Biến dị: con có điểm khác bố mẹ (đột biến, tổ hợp gen). Cả hai là cơ sở của tiến hóa và chọn giống.' }
          ],
          examples: [
            { q: 'Bố mắt nâu, mẹ mắt nâu, con mắt xanh — hiện tượng gì?', sol: 'Biến dị / gen lặn biểu hiện (con nhận gen lặn từ cả bố và mẹ).' },
            { q: 'Vật chất mang thông tin di truyền là gì?', sol: 'ADN (gen).' }
          ]
        }
      },
      notes: {
        key_points: [
          'ADN là vật chất di truyền (cấu trúc xoắn kép).',
          'Gen = một đoạn ADN quy định một tính trạng.',
          'ADN nằm trên nhiễm sắc thể trong nhân tế bào.',
          'Menđen tìm ra quy luật di truyền (đậu Hà Lan).'
        ],
        formula: 'Gen ⊂ ADN ⊂ Nhiễm sắc thể (trong nhân tế bào)',
        tip: 'Nhớ trật tự cấp độ: Nuclêôtit → Gen → ADN → Nhiễm sắc thể — câu HSA hay hỏi cái nào chứa cái nào.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Vật chất di truyền ở cấp phân tử?', options: ['ADN', 'protein', 'lipit', 'nước'], answer: 'ADN' },
          { id: 'd2', type: 'mcq', question: 'Gen là?', options: ['một đoạn ADN', 'một protein', 'một tế bào', 'một mô'], answer: 'một đoạn ADN' },
          { id: 'd3', type: 'mcq', question: 'Người tìm ra quy luật di truyền?', options: ['Menđen', 'Đacuyn', 'Newton', 'Einstein'], answer: 'Menđen' },
          { id: 'd4', type: 'mcq', question: 'ADN có cấu trúc?', options: ['xoắn kép', 'thẳng', 'hình cầu', 'tam giác'], answer: 'xoắn kép' },
          { id: 'd5', type: 'mcq', question: 'ADN nằm chủ yếu ở đâu trong tế bào?', options: ['nhân (trên NST)', 'màng', 'thành tế bào', 'không bào'], answer: 'nhân (trên NST)' },
          { id: 'd6', type: 'mcq', question: 'Con giống bố mẹ là hiện tượng?', options: ['di truyền', 'biến dị', 'tiến hóa', 'chọn lọc'], answer: 'di truyền' },
          { id: 'd7', type: 'mcq', question: 'Con có điểm khác bố mẹ là?', options: ['biến dị', 'di truyền', 'sinh sản', 'hô hấp'], answer: 'biến dị' },
          { id: 'd8', type: 'mcq', question: 'Menđen nghiên cứu trên?', options: ['đậu Hà Lan', 'ruồi giấm', 'chuột', 'vi khuẩn'], answer: 'đậu Hà Lan' }
        ]
      }
    },

    {
      id: 'kh_13',
      index: 13,
      title: 'Tiến hóa',
      subtitle: 'Chọn lọc tự nhiên và thuyết tiến hóa Đacuyn',
      topic_tag: 'Khoa học · Sinh học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về tiến hóa.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Người đề xuất thuyết tiến hóa bằng chọn lọc tự nhiên là?',
            options: ['Đacuyn', 'Menđen', 'Newton', 'Pasteur'], answer: 'Đacuyn',
            explain: 'Đacuyn (Darwin) đề xuất thuyết tiến hóa bằng chọn lọc tự nhiên.' },
          { id: 't2', type: 'mcq', question: 'Động lực chính của tiến hóa theo Đacuyn là?',
            options: ['chọn lọc tự nhiên', 'ý muốn của sinh vật', 'sự tình cờ hoàn toàn', 'con người can thiệp'], answer: 'chọn lọc tự nhiên',
            explain: 'Chọn lọc tự nhiên giữ lại cá thể thích nghi, đào thải cá thể kém thích nghi.' },
          { id: 't3', type: 'mcq', question: 'Chọn lọc tự nhiên GIỮ LẠI những cá thể như thế nào?',
            options: ['thích nghi tốt với môi trường', 'to lớn nhất', 'sinh sau', 'yếu nhất'], answer: 'thích nghi tốt với môi trường',
            explain: 'Cá thể thích nghi tốt sống sót và sinh sản nhiều hơn, truyền lại đặc điểm có lợi.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-timeline', title: 'Tiến hóa',
              body: 'Là quá trình sinh vật biến đổi qua nhiều thế hệ, hình thành loài mới thích nghi với môi trường. Đacuyn là người đặt nền móng.' },
            { icon: 'fa-filter', title: 'Chọn lọc tự nhiên',
              body: 'Cá thể thích nghi TỐT → sống sót, sinh sản nhiều → truyền đặc điểm có lợi. Cá thể kém thích nghi bị đào thải. Đây là động lực của tiến hóa.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ tiến hóa',
          cards: [
            { icon: 'fa-timeline', title: 'Khái niệm tiến hóa',
              body: 'Tiến hóa là sự biến đổi của sinh vật qua các thế hệ, dẫn tới sự đa dạng và thích nghi của sinh giới, hình thành các loài mới.' },
            { icon: 'fa-user-graduate', title: 'Thuyết Đacuyn',
              body: 'Đacuyn (Darwin) giải thích tiến hóa bằng CHỌN LỌC TỰ NHIÊN, dựa trên biến dị, di truyền và đấu tranh sinh tồn.' },
            { icon: 'fa-filter', title: 'Cơ chế chọn lọc tự nhiên',
              body: 'Trong quần thể có biến dị. Đấu tranh sinh tồn khiến cá thể thích nghi tốt sống sót và sinh sản nhiều hơn, truyền đặc điểm có lợi cho đời sau; cá thể kém thích nghi bị loại bỏ.' },
            { icon: 'fa-paw', title: 'Bằng chứng & thích nghi',
              body: 'Bằng chứng: hóa thạch, giải phẫu so sánh, phôi sinh học. Ví dụ thích nghi: cổ hươu cao ngày càng dài, sâu bọ có màu bảo vệ giống môi trường.' }
          ],
          examples: [
            { q: 'Vì sao hươu cao cổ có cổ dài?', sol: 'Chọn lọc tự nhiên: con cổ dài với tới lá cao, sống sót và sinh sản tốt hơn → đặc điểm cổ dài được giữ lại.' },
            { q: 'Sâu ăn lá có màu xanh giúp gì?', sol: 'Ngụy trang, tránh kẻ thù → thích nghi được chọn lọc giữ lại.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Tiến hóa: sinh vật biến đổi qua các thế hệ, hình thành loài mới.',
          'Đacuyn đề xuất thuyết tiến hóa bằng chọn lọc tự nhiên.',
          'Chọn lọc tự nhiên: giữ cá thể thích nghi tốt, đào thải cá thể kém.',
          'Cơ sở: biến dị + di truyền + đấu tranh sinh tồn.'
        ],
        formula: 'Biến dị + Di truyền + Đấu tranh sinh tồn → Chọn lọc tự nhiên → Tiến hóa',
        tip: 'Nhớ: chọn lọc tự nhiên KHÔNG phải sinh vật “tự muốn” thay đổi, mà là môi trường “sàng lọc” cá thể thích nghi.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Người đề xuất thuyết chọn lọc tự nhiên?', options: ['Đacuyn', 'Menđen', 'Newton', 'Pasteur'], answer: 'Đacuyn' },
          { id: 'd2', type: 'mcq', question: 'Động lực chính của tiến hóa?', options: ['chọn lọc tự nhiên', 'ý muốn sinh vật', 'ngẫu nhiên hoàn toàn', 'con người'], answer: 'chọn lọc tự nhiên' },
          { id: 'd3', type: 'mcq', question: 'Chọn lọc tự nhiên giữ lại cá thể?', options: ['thích nghi tốt', 'to nhất', 'yếu nhất', 'sinh sau'], answer: 'thích nghi tốt' },
          { id: 'd4', type: 'mcq', question: 'Cá thể kém thích nghi thường bị?', options: ['đào thải', 'giữ lại', 'nhân đôi', 'biến to'], answer: 'đào thải' },
          { id: 'd5', type: 'mcq', question: 'Bằng chứng tiến hóa gồm?', options: ['hóa thạch, giải phẫu so sánh', 'màu sắc', 'âm thanh', 'nhiệt độ'], answer: 'hóa thạch, giải phẫu so sánh' },
          { id: 'd6', type: 'mcq', question: 'Kết quả của tiến hóa là?', options: ['sự đa dạng & thích nghi', 'sinh vật giống hệt nhau', 'không thay đổi', 'chỉ một loài'], answer: 'sự đa dạng & thích nghi' },
          { id: 'd7', type: 'mcq', question: 'Sâu có màu giống lá là ví dụ về?', options: ['thích nghi', 'di truyền độc lập', 'hô hấp', 'quang hợp'], answer: 'thích nghi' },
          { id: 'd8', type: 'mcq', question: 'Cơ sở của chọn lọc tự nhiên gồm?', options: ['biến dị, di truyền, đấu tranh sinh tồn', 'chỉ ánh sáng', 'chỉ nhiệt độ', 'ý chí'], answer: 'biến dị, di truyền, đấu tranh sinh tồn' }
        ]
      }
    },

    {
      id: 'kh_14',
      index: 14,
      title: 'Sinh thái',
      subtitle: 'Hệ sinh thái, chuỗi thức ăn và quần thể',
      topic_tag: 'Khoa học · Sinh học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về sinh thái.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Trong hệ sinh thái, sinh vật SẢN XUẤT là?',
            options: ['cây xanh (thực vật)', 'động vật ăn thịt', 'vi khuẩn phân hủy', 'động vật ăn cỏ'], answer: 'cây xanh (thực vật)',
            explain: 'Cây xanh tự tổng hợp chất hữu cơ nhờ quang hợp → sinh vật sản xuất.' },
          { id: 't2', type: 'mcq', question: 'Một chuỗi thức ăn thường BẮT ĐẦU từ?',
            options: ['sinh vật sản xuất (cây xanh)', 'động vật ăn thịt', 'con người', 'vi khuẩn'], answer: 'sinh vật sản xuất (cây xanh)',
            explain: 'Chuỗi thức ăn: cây xanh → động vật ăn cỏ → động vật ăn thịt → …' },
          { id: 't3', type: 'mcq', question: 'Quần thể sinh vật là?',
            options: ['tập hợp cá thể cùng loài, sống trong một khu vực', 'tất cả sinh vật trên Trái Đất', 'một cá thể duy nhất', 'các loài khác nhau'], answer: 'tập hợp cá thể cùng loài, sống trong một khu vực',
            explain: 'Quần thể = các cá thể cùng loài, cùng khu vực, cùng thời điểm.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-tree', title: 'Hệ sinh thái',
              body: 'Gồm quần xã sinh vật + môi trường sống. Ba nhóm: sinh vật SẢN XUẤT (cây xanh), TIÊU THỤ (động vật), PHÂN GIẢI (vi khuẩn, nấm).' },
            { icon: 'fa-arrow-right-long', title: 'Chuỗi thức ăn',
              body: 'Cây xanh → động vật ăn cỏ → động vật ăn thịt → … Năng lượng truyền theo một chiều, giảm dần qua mỗi bậc.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ sinh thái',
          cards: [
            { icon: 'fa-users', title: 'Quần thể & quần xã',
              body: 'Quần thể: tập hợp cá thể CÙNG LOÀI, cùng khu vực (đàn cá chép trong ao). Quần xã: tập hợp các quần thể KHÁC loài cùng sống trong một khu vực.' },
            { icon: 'fa-tree', title: 'Hệ sinh thái',
              body: 'Quần xã sinh vật + môi trường (đất, nước, không khí…) tạo thành hệ sinh thái. Các thành phần tương tác, trao đổi chất và năng lượng.' },
            { icon: 'fa-arrow-right-long', title: 'Chuỗi & lưới thức ăn',
              body: 'Chuỗi thức ăn: thứ tự ăn nhau (cỏ → thỏ → cáo). Nhiều chuỗi đan xen tạo LƯỚI thức ăn. Sinh vật sản xuất luôn đứng đầu.' },
            { icon: 'fa-recycle', title: 'Vai trò các nhóm',
              body: 'Sản xuất (cây xanh) tạo chất hữu cơ. Tiêu thụ (động vật) sử dụng chất hữu cơ. Phân giải (vi khuẩn, nấm) trả chất vô cơ về môi trường → tuần hoàn vật chất.' }
          ],
          examples: [
            { q: 'Sắp xếp chuỗi: cáo, cỏ, thỏ.', sol: 'Cỏ → thỏ → cáo (sản xuất → ăn cỏ → ăn thịt).' },
            { q: 'Vi khuẩn phân hủy xác động vật thuộc nhóm nào?', sol: 'Sinh vật phân giải.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Hệ sinh thái = quần xã sinh vật + môi trường sống.',
          'Ba nhóm: sản xuất (cây xanh), tiêu thụ (động vật), phân giải (vi khuẩn/nấm).',
          'Chuỗi thức ăn bắt đầu từ sinh vật sản xuất; năng lượng truyền một chiều.',
          'Quần thể = cá thể cùng loài; quần xã = nhiều quần thể khác loài.'
        ],
        formula: 'Sản xuất → Tiêu thụ → Phân giải (tuần hoàn vật chất)',
        tip: 'Chuỗi thức ăn LUÔN bắt đầu từ cây xanh (sinh vật sản xuất) — nhớ để sắp xếp đúng thứ tự.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Sinh vật sản xuất trong hệ sinh thái?', options: ['cây xanh', 'hổ', 'vi khuẩn', 'nấm'], answer: 'cây xanh' },
          { id: 'd2', type: 'mcq', question: 'Chuỗi thức ăn bắt đầu từ?', options: ['sinh vật sản xuất', 'động vật ăn thịt', 'con người', 'nấm'], answer: 'sinh vật sản xuất' },
          { id: 'd3', type: 'mcq', question: 'Quần thể là tập hợp cá thể?', options: ['cùng loài', 'khác loài', 'toàn Trái Đất', 'một cá thể'], answer: 'cùng loài' },
          { id: 'd4', type: 'mcq', question: 'Vi khuẩn, nấm phân hủy xác thuộc nhóm?', options: ['phân giải', 'sản xuất', 'tiêu thụ', 'ký sinh'], answer: 'phân giải' },
          { id: 'd5', type: 'mcq', question: 'Chuỗi đúng là?', options: ['cỏ → thỏ → cáo', 'cáo → thỏ → cỏ', 'thỏ → cỏ → cáo', 'cáo → cỏ → thỏ'], answer: 'cỏ → thỏ → cáo' },
          { id: 'd6', type: 'mcq', question: 'Động vật ăn cỏ thuộc nhóm?', options: ['tiêu thụ', 'sản xuất', 'phân giải', 'ký sinh'], answer: 'tiêu thụ' },
          { id: 'd7', type: 'mcq', question: 'Nhiều chuỗi thức ăn đan xen tạo thành?', options: ['lưới thức ăn', 'quần thể', 'hệ sinh thái', 'quần xã'], answer: 'lưới thức ăn' },
          { id: 'd8', type: 'mcq', question: 'Năng lượng trong chuỗi thức ăn truyền?', options: ['một chiều, giảm dần', 'hai chiều', 'tăng dần', 'không đổi'], answer: 'một chiều, giảm dần' }
        ]
      }
    },

    {
      id: 'kh_15',
      index: 15,
      title: 'Sinh lý cơ thể',
      subtitle: 'Hệ tuần hoàn, hô hấp và tiêu hóa ở người',
      topic_tag: 'Khoa học · Sinh học',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về sinh lý cơ thể người.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Cơ quan bơm máu đi khắp cơ thể là?',
            options: ['tim', 'phổi', 'gan', 'thận'], answer: 'tim',
            explain: 'Tim co bóp đẩy máu đi nuôi cơ thể (hệ tuần hoàn).' },
          { id: 't2', type: 'mcq', question: 'Cơ quan thực hiện trao đổi khí (nhận O₂, thải CO₂) ở người là?',
            options: ['phổi', 'tim', 'dạ dày', 'thận'], answer: 'phổi',
            explain: 'Phổi là nơi trao đổi khí giữa cơ thể và môi trường.' },
          { id: 't3', type: 'mcq', question: 'Thành phần nào của máu vận chuyển oxi?',
            options: ['hồng cầu', 'bạch cầu', 'tiểu cầu', 'huyết tương'], answer: 'hồng cầu',
            explain: 'Hồng cầu chứa huyết sắc tố (hemoglobin) vận chuyển O₂.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-heart-pulse', title: 'Tuần hoàn & hô hấp',
              body: 'TIM bơm máu đi khắp cơ thể (hệ tuần hoàn). PHỔI trao đổi khí: nhận O₂, thải CO₂ (hệ hô hấp). Hồng cầu vận chuyển O₂.' },
            { icon: 'fa-utensils', title: 'Tiêu hóa',
              body: 'Biến thức ăn thành chất dinh dưỡng hấp thụ vào máu. Đường đi: miệng → thực quản → dạ dày → ruột non (hấp thụ) → ruột già.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ sinh lý cơ thể',
          cards: [
            { icon: 'fa-heart-pulse', title: 'Hệ tuần hoàn',
              body: 'Gồm tim và mạch máu. Tim co bóp đẩy máu theo động mạch đi nuôi cơ thể, máu về tim theo tĩnh mạch. Máu vận chuyển O₂, chất dinh dưỡng và mang CO₂, chất thải đi.' },
            { icon: 'fa-lungs', title: 'Hệ hô hấp',
              body: 'Gồm đường dẫn khí và phổi. Ở phổi diễn ra trao đổi khí: máu nhận O₂ và thải CO₂ ra ngoài. Cung cấp oxi cho hô hấp tế bào.' },
            { icon: 'fa-utensils', title: 'Hệ tiêu hóa',
              body: 'Biến đổi thức ăn thành chất dinh dưỡng đơn giản để hấp thụ. Ruột non là nơi hấp thụ chính. Gan, tụy tiết dịch hỗ trợ tiêu hóa.' },
            { icon: 'fa-droplet', title: 'Máu',
              body: 'Gồm huyết tương và các tế bào máu: hồng cầu (vận chuyển O₂), bạch cầu (bảo vệ, chống bệnh), tiểu cầu (đông máu).' }
          ],
          examples: [
            { q: 'Vì sao khi vận động mạnh ta thở nhanh hơn?', sol: 'Cơ thể cần nhiều O₂ và thải nhiều CO₂ hơn nên nhịp hô hấp tăng.' },
            { q: 'Tế bào máu nào giúp chống nhiễm khuẩn?', sol: 'Bạch cầu.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Tim bơm máu (hệ tuần hoàn); phổi trao đổi khí (hệ hô hấp).',
          'Hồng cầu vận chuyển O₂; bạch cầu bảo vệ; tiểu cầu đông máu.',
          'Tiêu hóa: miệng → thực quản → dạ dày → ruột non (hấp thụ) → ruột già.',
          'Ruột non là nơi hấp thụ chất dinh dưỡng chính.'
        ],
        formula: 'Tim → động mạch → cơ thể → tĩnh mạch → tim (vòng tuần hoàn)',
        tip: 'Gắn cơ quan với chức năng: tim–bơm máu, phổi–trao đổi khí, ruột non–hấp thụ, thận–lọc máu.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Cơ quan bơm máu?', options: ['tim', 'phổi', 'gan', 'thận'], answer: 'tim' },
          { id: 'd2', type: 'mcq', question: 'Cơ quan trao đổi khí?', options: ['phổi', 'tim', 'dạ dày', 'ruột'], answer: 'phổi' },
          { id: 'd3', type: 'mcq', question: 'Thành phần máu vận chuyển O₂?', options: ['hồng cầu', 'bạch cầu', 'tiểu cầu', 'huyết tương'], answer: 'hồng cầu' },
          { id: 'd4', type: 'mcq', question: 'Tế bào máu giúp chống bệnh?', options: ['bạch cầu', 'hồng cầu', 'tiểu cầu', 'huyết tương'], answer: 'bạch cầu' },
          { id: 'd5', type: 'mcq', question: 'Tiểu cầu có vai trò?', options: ['đông máu', 'vận chuyển O₂', 'tiêu hóa', 'hô hấp'], answer: 'đông máu' },
          { id: 'd6', type: 'mcq', question: 'Nơi hấp thụ chất dinh dưỡng chính?', options: ['ruột non', 'dạ dày', 'thực quản', 'ruột già'], answer: 'ruột non' },
          { id: 'd7', type: 'mcq', question: 'Cơ quan lọc máu, tạo nước tiểu?', options: ['thận', 'tim', 'phổi', 'gan'], answer: 'thận' },
          { id: 'd8', type: 'mcq', question: 'Khi vận động mạnh, nhịp thở?', options: ['tăng', 'giảm', 'không đổi', 'dừng'], answer: 'tăng' }
        ]
      }
    },

    {
      id: 'kh_16',
      index: 16,
      title: 'Lịch sử Việt Nam',
      subtitle: 'Các mốc lớn của lịch sử Việt Nam hiện đại',
      topic_tag: 'Khoa học · Lịch sử',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về lịch sử Việt Nam.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Cách mạng tháng Tám thành công, nước Việt Nam Dân chủ Cộng hòa ra đời vào năm nào?',
            options: ['1930', '1945', '1954', '1975'], answer: '1945',
            explain: 'Ngày 2/9/1945, Chủ tịch Hồ Chí Minh đọc Tuyên ngôn Độc lập, khai sinh nước Việt Nam Dân chủ Cộng hòa.' },
          { id: 't2', type: 'mcq', question: 'Chiến thắng Điện Biên Phủ "lừng lẫy năm châu, chấn động địa cầu" diễn ra năm nào?',
            options: ['1945', '1954', '1968', '1975'], answer: '1954',
            explain: 'Chiến thắng Điện Biên Phủ (7/5/1954) kết thúc kháng chiến chống Pháp.' },
          { id: 't3', type: 'mcq', question: 'Đất nước thống nhất, kết thúc kháng chiến chống Mỹ vào năm nào?',
            options: ['1954', '1968', '1973', '1975'], answer: '1975',
            explain: '30/4/1975, miền Nam được giải phóng, đất nước thống nhất.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-flag', title: 'Các mốc "vàng"',
              body: '1930: Đảng CSVN thành lập. 1945: Cách mạng tháng Tám, VNDCCH ra đời. 1954: Điện Biên Phủ. 1975: Thống nhất đất nước.' },
            { icon: 'fa-timeline', title: 'Hai cuộc kháng chiến',
              body: 'Chống Pháp (1945-1954, kết thúc ở Điện Biên Phủ). Chống Mỹ (1954-1975, kết thúc 30/4/1975).' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ lịch sử Việt Nam',
          cards: [
            { icon: 'fa-star', title: '1930 – Thành lập Đảng',
              body: 'Ngày 3/2/1930, Đảng Cộng sản Việt Nam ra đời, do Nguyễn Ái Quốc (Hồ Chí Minh) chủ trì hợp nhất các tổ chức cộng sản.' },
            { icon: 'fa-flag', title: '1945 – Cách mạng tháng Tám',
              body: 'Tổng khởi nghĩa tháng Tám thành công. Ngày 2/9/1945, Hồ Chí Minh đọc Tuyên ngôn Độc lập, khai sinh nước Việt Nam Dân chủ Cộng hòa.' },
            { icon: 'fa-shield-halved', title: '1954 – Điện Biên Phủ',
              body: 'Chiến thắng Điện Biên Phủ (7/5/1954) buộc Pháp ký Hiệp định Giơ-ne-vơ, kết thúc kháng chiến chống Pháp; đất nước tạm chia hai miền.' },
            { icon: 'fa-dove', title: '1975 – Thống nhất',
              body: 'Chiến dịch Hồ Chí Minh toàn thắng, 30/4/1975 giải phóng miền Nam, kết thúc kháng chiến chống Mỹ, thống nhất đất nước.' }
          ],
          examples: [
            { q: 'Tuyên ngôn Độc lập được đọc ngày nào?', sol: '2/9/1945, tại Quảng trường Ba Đình.' },
            { q: 'Hiệp định Giơ-ne-vơ ký sau sự kiện nào?', sol: 'Sau chiến thắng Điện Biên Phủ 1954.' }
          ]
        }
      },
      notes: {
        key_points: [
          '1930: Đảng Cộng sản Việt Nam thành lập.',
          '1945: Cách mạng tháng Tám, khai sinh VNDCCH (2/9/1945).',
          '1954: Chiến thắng Điện Biên Phủ, kết thúc chống Pháp.',
          '1975: Thống nhất đất nước (30/4/1975), kết thúc chống Mỹ.'
        ],
        formula: '1930 → 1945 → 1954 → 1975 (các mốc lớn)',
        tip: 'Nhớ 4 mốc "vàng" 1930-1945-1954-1975 là xử lý được phần lớn câu sử Việt Nam hiện đại.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Cách mạng tháng Tám năm?', options: ['1930', '1945', '1954', '1975'], answer: '1945' },
          { id: 'd2', type: 'mcq', question: 'Chiến thắng Điện Biên Phủ năm?', options: ['1945', '1954', '1968', '1975'], answer: '1954' },
          { id: 'd3', type: 'mcq', question: 'Thống nhất đất nước năm?', options: ['1954', '1973', '1975', '1986'], answer: '1975' },
          { id: 'd4', type: 'mcq', question: 'Đảng Cộng sản Việt Nam thành lập năm?', options: ['1925', '1930', '1945', '1954'], answer: '1930' },
          { id: 'd5', type: 'mcq', question: 'Người đọc Tuyên ngôn Độc lập 2/9/1945?', options: ['Hồ Chí Minh', 'Võ Nguyên Giáp', 'Tôn Đức Thắng', 'Phạm Văn Đồng'], answer: 'Hồ Chí Minh' },
          { id: 'd6', type: 'mcq', question: 'Kháng chiến chống Pháp kết thúc bằng chiến thắng?', options: ['Điện Biên Phủ', 'Bạch Đằng', 'Chi Lăng', 'Đống Đa'], answer: 'Điện Biên Phủ' },
          { id: 'd7', type: 'mcq', question: 'Ngày giải phóng miền Nam?', options: ['30/4/1975', '2/9/1945', '7/5/1954', '19/8/1945'], answer: '30/4/1975' },
          { id: 'd8', type: 'mcq', question: 'Kháng chiến chống Mỹ diễn ra giai đoạn?', options: ['1954-1975', '1930-1945', '1945-1954', '1975-1986'], answer: '1954-1975' }
        ]
      }
    },

    {
      id: 'kh_17',
      index: 17,
      title: 'Lịch sử Thế giới',
      subtitle: 'Các sự kiện lớn của lịch sử thế giới hiện đại',
      topic_tag: 'Khoa học · Lịch sử',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về lịch sử thế giới.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Chiến tranh thế giới thứ hai kết thúc vào năm nào?',
            options: ['1918', '1939', '1945', '1954'], answer: '1945',
            explain: 'Chiến tranh thế giới thứ hai (1939-1945) kết thúc năm 1945.' },
          { id: 't2', type: 'mcq', question: 'Cách mạng tháng Mười Nga thành công vào năm nào?',
            options: ['1789', '1917', '1945', '1991'], answer: '1917',
            explain: 'Cách mạng tháng Mười Nga (1917) lập nên nhà nước xã hội chủ nghĩa đầu tiên.' },
          { id: 't3', type: 'mcq', question: 'Liên bang Xô viết (Liên Xô) tan rã vào năm nào?',
            options: ['1945', '1975', '1991', '2000'], answer: '1991',
            explain: 'Liên Xô tan rã năm 1991, kết thúc Chiến tranh Lạnh.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-earth-americas', title: 'Các mốc lớn',
              body: '1917: Cách mạng tháng Mười Nga. 1939-1945: Chiến tranh thế giới thứ hai. 1991: Liên Xô tan rã, kết thúc Chiến tranh Lạnh.' },
            { icon: 'fa-explosion', title: 'Hai cuộc thế chiến',
              body: 'Thế chiến I (1914-1918). Thế chiến II (1939-1945) — quy mô lớn nhất lịch sử, kết thúc với thắng lợi của phe Đồng minh.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ lịch sử thế giới',
          cards: [
            { icon: 'fa-star', title: 'Cách mạng tháng Mười Nga (1917)',
              body: 'Do Lê-nin lãnh đạo, lật đổ chế độ cũ, lập nên nhà nước Xô viết — nhà nước xã hội chủ nghĩa đầu tiên trên thế giới.' },
            { icon: 'fa-explosion', title: 'Chiến tranh thế giới thứ hai (1939-1945)',
              body: 'Cuộc chiến lớn nhất lịch sử giữa phe Phát xít và phe Đồng minh, kết thúc năm 1945 với thắng lợi của Đồng minh; để lại hậu quả nặng nề.' },
            { icon: 'fa-handshake-angle', title: 'Chiến tranh Lạnh',
              body: 'Sau 1945, thế giới chia thành hai cực (Mỹ – Liên Xô), đối đầu căng thẳng nhưng không xung đột trực tiếp. Kết thúc khi Liên Xô tan rã (1991).' },
            { icon: 'fa-globe', title: 'Xu thế hiện nay',
              body: 'Sau Chiến tranh Lạnh: xu thế hòa bình, hợp tác, toàn cầu hóa; các quốc gia đẩy mạnh phát triển kinh tế và hội nhập.' }
          ],
          examples: [
            { q: 'Ai lãnh đạo Cách mạng tháng Mười Nga?', sol: 'Lê-nin (V.I. Lenin).' },
            { q: 'Chiến tranh Lạnh kết thúc khi nào?', sol: 'Năm 1991, khi Liên Xô tan rã.' }
          ]
        }
      },
      notes: {
        key_points: [
          '1917: Cách mạng tháng Mười Nga (Lê-nin lãnh đạo).',
          '1914-1918: Thế chiến I; 1939-1945: Thế chiến II.',
          'Sau 1945: Chiến tranh Lạnh (Mỹ – Liên Xô hai cực).',
          '1991: Liên Xô tan rã, kết thúc Chiến tranh Lạnh.'
        ],
        formula: '1917 → 1939-1945 → 1991 (mốc lớn LS thế giới hiện đại)',
        tip: 'Gắn sự kiện với con số năm và nhân vật chủ chốt — câu sử thế giới thường hỏi "năm nào / ai".'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Thế chiến II kết thúc năm?', options: ['1918', '1939', '1945', '1954'], answer: '1945' },
          { id: 'd2', type: 'mcq', question: 'Cách mạng tháng Mười Nga năm?', options: ['1789', '1917', '1945', '1991'], answer: '1917' },
          { id: 'd3', type: 'mcq', question: 'Liên Xô tan rã năm?', options: ['1975', '1986', '1991', '2000'], answer: '1991' },
          { id: 'd4', type: 'mcq', question: 'Thế chiến I diễn ra giai đoạn?', options: ['1914-1918', '1939-1945', '1917-1922', '1945-1991'], answer: '1914-1918' },
          { id: 'd5', type: 'mcq', question: 'Người lãnh đạo Cách mạng tháng Mười?', options: ['Lê-nin', 'Stalin', 'Napoleon', 'Hitler'], answer: 'Lê-nin' },
          { id: 'd6', type: 'mcq', question: 'Sau 1945 thế giới bước vào?', options: ['Chiến tranh Lạnh', 'Thế chiến III', 'thời trung cổ', 'thời phục hưng'], answer: 'Chiến tranh Lạnh' },
          { id: 'd7', type: 'mcq', question: 'Thế chiến II là cuộc chiến giữa?', options: ['Phát xít và Đồng minh', 'Nga và Pháp', 'Anh và Mỹ', 'La Mã và Hy Lạp'], answer: 'Phát xít và Đồng minh' },
          { id: 'd8', type: 'mcq', question: 'Chiến tranh Lạnh kết thúc khi?', options: ['Liên Xô tan rã (1991)', 'thế chiến II (1945)', '1975', '2001'], answer: 'Liên Xô tan rã (1991)' }
        ]
      }
    },

    {
      id: 'kh_18',
      index: 18,
      title: 'Chuyên đề lịch sử',
      subtitle: 'Nhân vật và sự kiện tiêu biểu',
      topic_tag: 'Khoa học · Lịch sử',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về nhân vật – sự kiện lịch sử.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Người đọc Tuyên ngôn Độc lập khai sinh nước Việt Nam Dân chủ Cộng hòa (2/9/1945) là?',
            options: ['Hồ Chí Minh', 'Võ Nguyên Giáp', 'Trần Phú', 'Lê Duẩn'], answer: 'Hồ Chí Minh',
            explain: 'Chủ tịch Hồ Chí Minh đọc Tuyên ngôn Độc lập tại Quảng trường Ba Đình.' },
          { id: 't2', type: 'mcq', question: 'Vị tướng chỉ huy chiến dịch Điện Biên Phủ (1954) là?',
            options: ['Võ Nguyên Giáp', 'Nguyễn Huệ', 'Trần Hưng Đạo', 'Lý Thường Kiệt'], answer: 'Võ Nguyên Giáp',
            explain: 'Đại tướng Võ Nguyên Giáp là Tổng tư lệnh chiến dịch Điện Biên Phủ.' },
          { id: 't3', type: 'mcq', question: 'Chiến dịch giải phóng hoàn toàn miền Nam năm 1975 mang tên?',
            options: ['Chiến dịch Hồ Chí Minh', 'Chiến dịch Điện Biên Phủ', 'Chiến dịch Biên giới', 'Chiến dịch Việt Bắc'], answer: 'Chiến dịch Hồ Chí Minh',
            explain: 'Chiến dịch Hồ Chí Minh (1975) giải phóng Sài Gòn, thống nhất đất nước.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-user', title: 'Nhân vật lịch sử tiêu biểu',
              body: 'Hồ Chí Minh (lãnh tụ, đọc Tuyên ngôn Độc lập). Võ Nguyên Giáp (Đại tướng, chỉ huy Điện Biên Phủ, chiến dịch Hồ Chí Minh).' },
            { icon: 'fa-landmark', title: 'Sự kiện gắn nhân vật',
              body: 'Nguyễn Ái Quốc – thành lập Đảng (1930). Anh hùng dân tộc chống ngoại xâm: Trần Hưng Đạo, Nguyễn Huệ, Lý Thường Kiệt.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ chuyên đề lịch sử',
          cards: [
            { icon: 'fa-user-tie', title: 'Hồ Chí Minh',
              body: 'Lãnh tụ vĩ đại: tìm đường cứu nước, sáng lập Đảng (1930), lãnh đạo Cách mạng tháng Tám, đọc Tuyên ngôn Độc lập 2/9/1945.' },
            { icon: 'fa-medal', title: 'Võ Nguyên Giáp',
              body: 'Đại tướng, Tổng tư lệnh; chỉ huy chiến thắng Điện Biên Phủ (1954) và chiến dịch Hồ Chí Minh (1975).' },
            { icon: 'fa-shield-halved', title: 'Anh hùng chống ngoại xâm',
              body: 'Lý Thường Kiệt (chống Tống), Trần Hưng Đạo (ba lần chống Nguyên - Mông), Lê Lợi – Nguyễn Trãi (chống Minh), Quang Trung – Nguyễn Huệ (đại phá quân Thanh).' },
            { icon: 'fa-flag', title: 'Sự kiện tiêu biểu',
              body: 'Chiến thắng Bạch Đằng, Chi Lăng, Đống Đa (chống ngoại xâm thời phong kiến); Cách mạng tháng Tám, Điện Biên Phủ, Đại thắng mùa Xuân 1975 (hiện đại).' }
          ],
          examples: [
            { q: 'Ai đại phá quân Thanh (1789)?', sol: 'Vua Quang Trung – Nguyễn Huệ (chiến thắng Ngọc Hồi – Đống Đa).' },
            { q: 'Ai ba lần lãnh đạo chống quân Nguyên - Mông?', sol: 'Hưng Đạo Vương Trần Quốc Tuấn (Trần Hưng Đạo).' }
          ]
        }
      },
      notes: {
        key_points: [
          'Hồ Chí Minh: sáng lập Đảng, đọc Tuyên ngôn Độc lập 1945.',
          'Võ Nguyên Giáp: chỉ huy Điện Biên Phủ 1954 & chiến dịch Hồ Chí Minh 1975.',
          'Chiến dịch Hồ Chí Minh (1975) giải phóng miền Nam.',
          'Anh hùng chống ngoại xâm: Trần Hưng Đạo, Nguyễn Huệ, Lý Thường Kiệt.'
        ],
        tip: 'Học theo cặp NHÂN VẬT – SỰ KIỆN – NĂM để trả lời nhanh câu hỏi ghép nối trong đề.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Người đọc Tuyên ngôn Độc lập 1945?', options: ['Hồ Chí Minh', 'Võ Nguyên Giáp', 'Trần Phú', 'Lê Duẩn'], answer: 'Hồ Chí Minh' },
          { id: 'd2', type: 'mcq', question: 'Tổng tư lệnh chiến dịch Điện Biên Phủ?', options: ['Võ Nguyên Giáp', 'Nguyễn Huệ', 'Lê Lợi', 'Trần Hưng Đạo'], answer: 'Võ Nguyên Giáp' },
          { id: 'd3', type: 'mcq', question: 'Chiến dịch giải phóng miền Nam 1975 tên?', options: ['Hồ Chí Minh', 'Điện Biên Phủ', 'Việt Bắc', 'Biên giới'], answer: 'Hồ Chí Minh' },
          { id: 'd4', type: 'mcq', question: 'Ai đại phá quân Thanh (1789)?', options: ['Nguyễn Huệ', 'Lê Lợi', 'Trần Hưng Đạo', 'Lý Thường Kiệt'], answer: 'Nguyễn Huệ' },
          { id: 'd5', type: 'mcq', question: 'Ai ba lần chống quân Nguyên - Mông?', options: ['Trần Hưng Đạo', 'Nguyễn Huệ', 'Lê Lợi', 'Ngô Quyền'], answer: 'Trần Hưng Đạo' },
          { id: 'd6', type: 'mcq', question: 'Ai lãnh đạo khởi nghĩa Lam Sơn chống Minh?', options: ['Lê Lợi', 'Nguyễn Huệ', 'Trần Hưng Đạo', 'Lý Thường Kiệt'], answer: 'Lê Lợi' },
          { id: 'd7', type: 'mcq', question: 'Người sáng lập Đảng CSVN (1930)?', options: ['Nguyễn Ái Quốc', 'Võ Nguyên Giáp', 'Phạm Văn Đồng', 'Tôn Đức Thắng'], answer: 'Nguyễn Ái Quốc' },
          { id: 'd8', type: 'mcq', question: 'Chiến thắng chống Tống gắn với ai?', options: ['Lý Thường Kiệt', 'Nguyễn Huệ', 'Lê Lợi', 'Trần Hưng Đạo'], answer: 'Lý Thường Kiệt' }
        ]
      }
    },

    {
      id: 'kh_19',
      index: 19,
      title: 'Kỹ năng mốc – sự kiện',
      subtitle: 'Sắp xếp trục thời gian và tính thế kỉ',
      topic_tag: 'Khoa học · Lịch sử',
      xp_reward: 50,
      test: {
        intro: 'Làm nhanh 3 câu để hệ thống <strong>định vị năng lực</strong> của bạn về kỹ năng thời gian.',
        questions: [
          { id: 't1', type: 'mcq', question: 'Sắp xếp ĐÚNG thứ tự thời gian: Cách mạng tháng Tám (1945), Điện Biên Phủ (1954), Thống nhất (1975)?',
            options: ['1945 → 1954 → 1975', '1954 → 1945 → 1975', '1975 → 1954 → 1945', '1945 → 1975 → 1954'], answer: '1945 → 1954 → 1975',
            explain: 'Xếp theo năm tăng dần: 1945 trước, rồi 1954, rồi 1975.' },
          { id: 't2', type: 'mcq', question: 'Trục thời gian (timeline) được dùng để làm gì?',
            options: ['biểu diễn thứ tự các sự kiện theo thời gian', 'đo chiều dài', 'tính diện tích', 'vẽ bản đồ'], answer: 'biểu diễn thứ tự các sự kiện theo thời gian',
            explain: 'Trục thời gian sắp xếp sự kiện theo trình tự trước – sau.' },
          { id: 't3', type: 'mcq', question: 'Thế kỉ XX (20) gồm những năm nào?',
            options: ['1801 – 1900', '1901 – 2000', '2001 – 2100', '1900 – 1999'], answer: '1901 – 2000',
            explain: 'Thế kỉ XX từ năm 1901 đến hết năm 2000.' }
        ]
      },
      assess: { strong_min: 3, ok_min: 2 },
      theory: {
        condensed: {
          title: 'Tóm tắt nhanh — bạn đã khá vững',
          cards: [
            { icon: 'fa-timeline', title: 'Trục thời gian',
              body: 'Sắp xếp sự kiện theo năm TĂNG DẦN (trước → sau). Kỹ năng cốt lõi để làm câu hỏi thứ tự sự kiện.' },
            { icon: 'fa-calendar', title: 'Tính thế kỉ',
              body: 'Thế kỉ n gồm các năm từ (n−1)×100 + 1 đến n×100. VD thế kỉ XX = 1901-2000; thế kỉ XXI = 2001-2100.' }
          ]
        },
        full: {
          title: 'Lý thuyết đầy đủ — cùng ôn kỹ kỹ năng thời gian',
          cards: [
            { icon: 'fa-timeline', title: 'Đọc & lập trục thời gian',
              body: 'Trục thời gian biểu diễn các sự kiện theo trình tự. Đọc trục để biết sự kiện nào trước, nào sau, khoảng cách giữa các sự kiện.' },
            { icon: 'fa-arrow-down-1-9', title: 'Sắp xếp sự kiện',
              body: 'Dựa vào NĂM để xếp theo thứ tự tăng dần. Câu hỏi HSA hay cho vài sự kiện + năm, yêu cầu chọn thứ tự đúng.' },
            { icon: 'fa-calendar', title: 'Cách tính thế kỉ',
              body: 'Thế kỉ = lấy hai chữ số đầu của năm rồi cộng 1 (với năm không tròn trăm). VD năm 1945 thuộc thế kỉ XX; năm 2025 thuộc thế kỉ XXI.' },
            { icon: 'fa-hourglass', title: 'Tính khoảng thời gian',
              body: 'Khoảng cách giữa hai sự kiện = hiệu hai năm. VD từ 1945 đến 1975 là 30 năm. Trước Công nguyên (TCN) tính lùi về quá khứ.' }
          ],
          examples: [
            { q: 'Năm 1789 thuộc thế kỉ mấy?', sol: 'Thế kỉ XVIII (18) — vì 1789 nằm trong 1701-1800.' },
            { q: 'Từ Điện Biên Phủ (1954) đến Thống nhất (1975) là bao nhiêu năm?', sol: '1975 − 1954 = 21 năm.' }
          ]
        }
      },
      notes: {
        key_points: [
          'Sắp xếp sự kiện theo năm tăng dần (trước → sau).',
          'Trục thời gian biểu diễn thứ tự các sự kiện.',
          'Thế kỉ XX = 1901-2000; thế kỉ XXI = 2001-2100.',
          'Khoảng cách hai sự kiện = hiệu hai năm.'
        ],
        formula: 'Thế kỉ XX = 1901–2000   |   khoảng cách = năm sau − năm trước',
        tip: 'Nhớ: năm 19xx thuộc thế kỉ XX, năm 20xx thuộc thế kỉ XXI — trừ đúng năm tròn trăm.'
      },
      drill: {
        time_seconds: 80,
        questions: [
          { id: 'd1', type: 'mcq', question: 'Thứ tự đúng theo thời gian?', options: ['1945 → 1954 → 1975', '1975 → 1954 → 1945', '1954 → 1945 → 1975', '1945 → 1975 → 1954'], answer: '1945 → 1954 → 1975' },
          { id: 'd2', type: 'mcq', question: 'Năm 1945 thuộc thế kỉ?', options: ['XIX', 'XX', 'XXI', 'XVIII'], answer: 'XX' },
          { id: 'd3', type: 'mcq', question: 'Năm 2025 thuộc thế kỉ?', options: ['XX', 'XXI', 'XXII', 'XIX'], answer: 'XXI' },
          { id: 'd4', type: 'fill', question: 'Từ 1945 đến 1975 là bao nhiêu năm? (nhập số)', answer: '30' },
          { id: 'd5', type: 'mcq', question: 'Trục thời gian dùng để?', options: ['sắp xếp sự kiện theo thời gian', 'đo chiều dài', 'tính diện tích', 'vẽ đồ thị hàm'], answer: 'sắp xếp sự kiện theo thời gian' },
          { id: 'd6', type: 'mcq', question: 'Thế kỉ XX gồm năm?', options: ['1801-1900', '1901-2000', '2001-2100', '1900-1999'], answer: '1901-2000' },
          { id: 'd7', type: 'fill', question: 'Từ 1954 đến 1975 là bao nhiêu năm? (nhập số)', answer: '21' },
          { id: 'd8', type: 'mcq', question: 'Năm 1789 thuộc thế kỉ?', options: ['XVII', 'XVIII', 'XIX', 'XX'], answer: 'XVIII' }
        ]
      }
    }
  ]
};
