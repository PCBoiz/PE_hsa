'use client';

import { goiLegacy } from '@/lib/goiLegacy';
import { khuCua } from '@/lib/khuTheoVai';
import { useVaiHienTai } from '@/lib/useVaiHienTai';
import { NHAN_VAI } from '@/lib/vaiTro';

import { BieuTuong } from './bieuTuong';

/**
 * "Trang của tôi" của NHÂN SỰ — thay cho màn luyện thi của học viên.
 *
 * Luôn nằm trong DOM, ẩn/hiện bằng `data-chi-nhan-su` (xem `lib/nhomVai.ts`):
 * dựng có điều kiện theo state thì lần đầu mở trang, học viên nào cũng phải
 * chờ hook biết vai mới thấy đúng màn — còn ẩn bằng CSS thì nhóm được đặt từ
 * script đầu trang, trước khi React chạy.
 */
/** Đệm của thẻ — nội tuyến, xem chú thích trong thân component. */
const DEM = { padding: '1rem' } as const;

export default function KhuNhanSu() {
  const vai = useVaiHienTai();
  const khu = khuCua(vai);

  return (
    <section data-chi-nhan-su="" className="flex flex-col gap-4 fx-fade-up" aria-labelledby="khu-nhan-su-tieu-de">
      {/* KHOẢNG CÁCH VIẾT NỘI TUYẾN hoặc bằng `gap`, KHÔNG bằng `p-*`/`m-*`: trang
          này nạp `style.css`, dòng đầu của nó là `* { margin: 0; padding: 0 }` và
          `.section-card { margin-bottom: 24px }` — CSS cũ không nằm trong lớp nào
          nên thắng mọi tiện ích Tailwind (vốn ở `@layer utilities`). Viết `p-4`
          ở đây là viết một dòng không có tác dụng (đo 20/09: thẻ đệm 0px). */}
      <div className="section-card flex flex-col gap-1" style={{ marginBottom: 0 }}>
        <h2 id="khu-nhan-su-tieu-de" className="text-xl font-bold text-ink [text-wrap:balance]">
          Khu làm việc của bạn
        </h2>
        <p className="text-ink-2">
          {vai ? <>Bạn đang đăng nhập với vai <strong>{NHAN_VAI[vai] ?? vai}</strong>. </> : null}
          Phần luyện thi — kế hoạch học, nhiệm vụ, bảng xếp hạng — là của học viên
          nên không hiện ở đây.
        </p>
      </div>

      {/* `auto-fit` + `minmax(min(100%, 16rem), 1fr)`: số cột tự theo bề ngang,
          không mốc breakpoint cứng; `min(100%, …)` để khổ hẹp hơn 16rem vẫn không
          tràn ngang. */}
      <ul className="grid list-none gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,16rem),1fr))]">
        {khu.map((k) => {
          const noiDung = (
            <>
              <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-brand-soft text-brand" aria-hidden="true">
                <BieuTuong ten={k.icon} co={20} />
              </span>
              <span className="flex min-w-0 flex-col gap-1">
                <span className="font-semibold text-ink">{k.nhan}</span>
                <span className="text-sm leading-snug text-ink-2">{k.moTa}</span>
              </span>
            </>
          );
          // KHÔNG dùng `.section-card` ở đây — lý do ở trên: lề dưới 24px của nó
          // cộng vào `h-full` làm thẻ phình, và viền của nó đè mất `hover:`.
          const lop = 'flex h-full w-full cursor-pointer items-start gap-3 rounded-lg border border-line bg-surface text-left text-ink no-underline shadow-e1 [font:inherit] transition-colors duration-150 hover:border-brand hover:bg-brand-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand';
          return (
            <li key={k.nhan}>
              {k.url ? (
                <a href={k.url} className={lop} style={DEM}>{noiDung}</a>
              ) : (
                <button type="button" className={lop} style={DEM} onClick={() => goiLegacy('navigate', k.tab)}>
                  {noiDung}
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
