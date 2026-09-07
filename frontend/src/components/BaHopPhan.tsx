'use client';

import { useEffect, useRef, useState } from 'react';

/**
 * BA HỢP PHẦN HSA — bạn đang dồn sức vào đâu.
 *
 * ── VÌ SAO NÓ Ở `src/` CHỨ KHÔNG Ở `dashboard.js` ────────────────────────
 *
 * Bản đầu (07/09/2026) tôi viết khối này thẳng vào `public/static/js/dashboard.js`
 * vì phần Kỹ năng quanh nó nằm ở đó. `e2e/unit/chot-ham-tang-cu.test.mjs` ĐỎ
 * ngay: tầng JS cũ chỉ được phép nhỏ đi, mà tôi vừa thêm 38 dòng logic.
 *
 * Chốt hãm ấy không phải thủ tục. Tầng cũ không có bundler, không lint, không
 * typecheck — CI chỉ chạy `node --check`. Đó là nơi hai lỗ stored-XSS đã nằm,
 * và CHÍNH HÔM NAY tôi tìm ra lỗ thứ ba ở đó (`renderSkills` nối thẳng tên bài
 * giảng vào `innerHTML`). Thêm logic mới vào đúng tầng ấy trong lúc đang vá một
 * lỗ của nó là đi ngược hẳn.
 *
 * ── VÌ SAO CHỈ TẢI KHI TAB HIỆN RA ───────────────────────────────────────
 *
 * "Trang của tôi" là màn chậm nhất (LCP 2740ms, vượt ngưỡng 2500ms). Hai lượt
 * gọi thêm lúc trang tải là đi ngược việc tối ưu cùng ngày.
 *
 * `#page-skills` để `display: none` cho tới khi người dùng bấm sang tab, mà
 * phần tử `display:none` thì KHÔNG BAO GIỜ giao với khung nhìn — nên
 * `IntersectionObserver` vừa là "đã hiện ra chưa" vừa là "đã cuộn tới chưa",
 * không cần biết gì về `navigate()` của tầng cũ. Nó quan sát PANEL CHA chứ
 * không quan sát chính ô này; lý do nằm ở chỗ đặt `io.observe` bên dưới.
 *
 * HAI CẢNH BÁO đã trả giá:
 *   · `IntersectionObserver` gọi callback NGAY khi `observe()`, trước cả khi
 *     bố cục ổn định — phải đọc `isIntersecting`, không coi "có callback" là
 *     "đã hiện";
 *   · quan sát chính ô này thì khoá chết với `.sk-hopphan:empty{display:none}`.
 *
 * ── VÌ SAO KHÔNG PHẢI BẢNG ĐIỂM THƯỞNG ──────────────────────────────────
 *
 * Bài HSA có ba hợp phần và điểm cuối cộng cả ba. Học lệch một hợp phần là cách
 * hỏng điểm phổ biến nhất, mà học viên thường không tự thấy vì mỗi lần vào học
 * đều thấy mình tiến bộ. Khối này trả lời đúng MỘT câu: ba hợp phần của bạn có
 * lệch nhau không.
 *
 * ── VÌ SAO GHÉP XP VÀO `/api/skills` ────────────────────────────────────
 *
 * `xp-by-course` chỉ trả về khoá ĐÃ CÓ XP — hợp phần chưa học vắng mặt hẳn khỏi
 * phản hồi. Vẽ thẳng nó ra thì màn hình khoe "Định lượng 195 XP" và im lặng về
 * hai hợp phần kia, tức giấu đúng cái nó sinh ra để chỉ. `/api/skills` trả đủ
 * ba hợp phần, nên lấy khung từ đó rồi ghép XP vào.
 */

type BoKyNang = { id: string; title: string };
type Hop = { ten: string; xp: number };

export default function BaHopPhan() {
  const oRef = useRef<HTMLDivElement>(null);
  const [ds, setDs] = useState<Hop[] | null>(null);

  useEffect(() => {
    const o = oRef.current;
    if (!o) return;

    let huy = false;
    const nap = async () => {
      try {
        const [rKn, rXp] = await Promise.all([
          fetch('/api/skills', { credentials: 'same-origin' }),
          fetch('/api/stats/xp-by-course', { credentials: 'same-origin' }),
        ]);
        if (!rKn.ok) return;
        const kn = (await rKn.json()) as { skill_sets?: BoKyNang[] };
        /* Lỗi của lượt XP KHÔNG được nuốt mất cả khối: thiếu XP thì ba hợp phần
           vẫn hiện với "chưa bắt đầu", và đó vẫn là thông tin đúng. */
        const xp = rXp.ok
          ? ((await rXp.json()) as { subjects?: { courseId: string; xp: number }[] })
          : { subjects: [] };
        const theo: Record<string, number> = {};
        for (const s of xp.subjects ?? []) theo[s.courseId] = s.xp;
        if (!huy) {
          setDs((kn.skill_sets ?? []).map((b) => ({ ten: b.title, xp: theo[b.id] || 0 })));
        }
      } catch {
        /* im lặng: khối phụ, mất nó thì tab Kỹ năng vẫn dùng được */
      }
    };

    /* Quan sát PANEL CHA, không quan sát chính mình.
     *
     * Bản đầu quan sát chính `o`, và nó KHOÁ CHẾT: `dashboard.css` có
     * `.sk-hopphan:empty { display: none }` để ô chưa có dữ liệu khỏi chiếm
     * chỗ. Ô rỗng ⇒ bị ẩn ⇒ không bao giờ giao với khung nhìn ⇒ không bao giờ
     * tải ⇒ mãi mãi rỗng. Đo được: khối hiện 0 hàng.
     *
     * Panel `.page` cha thì không dính luật `:empty` ấy, và nó chính là thứ
     * `navigate()` của tầng cũ bật lên khi người dùng sang tab Kỹ năng — tức
     * đúng tín hiệu cần, mà không phải biết gì về `navigate()`. */
    const canh = o.closest('.page') ?? o;
    const io = new IntersectionObserver((cac) => {
      // `isIntersecting`, KHÔNG phải "có callback" — xem chú thích đầu tệp.
      if (cac.some((e) => e.isIntersecting)) {
        io.disconnect();
        void nap();
      }
    });
    io.observe(canh);
    return () => { huy = true; io.disconnect(); };
  }, []);

  // Chưa tải, hoặc không có hợp phần nào: giữ ô rỗng để `IntersectionObserver`
  // còn thứ để quan sát, nhưng CSS `:empty` làm nó không chiếm chỗ.
  if (!ds || ds.length === 0) {
    return <div ref={oRef} className="sk-hopphan" id="sk-hopphan" />;
  }

  const tong = ds.reduce((s, d) => s + d.xp, 0);
  const chuaBatDau = ds.filter((d) => d.xp === 0);

  return (
    <div ref={oRef} className="sk-hopphan fx-fade-up" id="sk-hopphan">
      <div className="sk-hp-tit">Ba hợp phần — bạn đang dồn sức vào đâu</div>
      <div className="sk-hp-ds">
        {ds.map((d) => (
          <div className="sk-hp-hang" key={d.ten}>
            <span className="sk-hp-ten">{d.ten}</span>
            {/* Bề rộng theo TỈ LỆ trong tổng, không theo một mốc cố định: mốc
                cố định thì mọi thanh đều ngắn ở người mới học và đều đầy ở
                người học lâu — cả hai đều không nói được gì về sự lệch. */}
            <span className="sk-hp-thanh">
              <i style={{ width: tong > 0 ? `${Math.round((d.xp * 100) / tong)}%` : 0 }} />
            </span>
            <span className="sk-hp-so">{d.xp ? `${d.xp} XP` : 'chưa bắt đầu'}</span>
          </div>
        ))}
      </div>
      <p className="sk-hp-luu">
        {tong === 0
          ? 'Chưa hợp phần nào có bài hoàn thành.'
          : chuaBatDau.length > 0
            ? <>Chưa đụng tới: <strong>{chuaBatDau.map((d) => d.ten).join(', ')}</strong>. Điểm HSA cộng cả ba hợp phần.</>
            : 'Cả ba hợp phần đều đã có bài hoàn thành.'}
        {' '}Con số này đếm XP của bài đã hoàn thành, không phải dự đoán điểm thi.
      </p>
    </div>
  );
}
