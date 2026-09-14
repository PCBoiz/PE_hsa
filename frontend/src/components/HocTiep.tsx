import Link from 'next/link';

import HocTiepRong from '@/components/HocTiepRong';
import { layKhoaDangHoc, layTomTat, type KhoaDangHoc } from '@/lib/duLieuHsa';

/**
 * THẺ "HỌC TIẾP" — dựng Ở MÁY CHỦ, không chờ tầng JS cũ.
 *
 * ── VÌ SAO CHUYỂN (14/09/2026) ────────────────────────────────────────────
 *
 * Thẻ này là phần tử LCP của Trang của tôi (8.840 px², lớn nhất màn đầu). Nó
 * vốn do `dashboard.js::renderContinue` vẽ, mà tầng cũ chỉ chạy sau khi React
 * hydrate: đo được **2,2–2,5 s** mới hiện, trong khi trang đã vẽ xong từ giây
 * 0,5. Đưa về đây thì nó nằm sẵn trong HTML máy chủ trả về — người học thấy
 * việc-cần-làm-tiếp ngay lượt sơn đầu tiên.
 *
 * Hai lượt gọi dữ liệu chạy SONG SONG và đều có hình dạng (T18 mức 2). Hỏng
 * một lượt thì hiện khối rỗng "Bắt đầu hành trình HSA" — KHÔNG hiện lỗi đỏ:
 * đây là một khối gợi ý, không phải nội dung chính, và một câu lỗi kỹ thuật ở
 * đầu trang học viên thì đáng sợ hơn là hữu ích.
 *
 * ── LUẬT CHỌN BÀI (giữ NGUYÊN của `renderContinue`) ───────────────────────
 *
 * Số bài đã xong đếm từ `byCourse` (đếm thật trong `lesson_progress`), chỉ khi
 * thiếu mới suy từ `progress` — vì `enrollments.progress` là bộ nhớ đệm và
 * bằng 0 với người học thẳng từ lộ trình. Khoá được chọn là khoá **dở dang
 * nhiều nhất**; nếu mọi khoá đã xong thì lấy khoá đầu danh sách.
 */

/** Tổng số bài của từng hợp phần — CÙNG bảng với `dashboard.js::SECTIONS`. */
const TONG_BAI: Record<string, number> = {
  hsa_quantitative: 27,
  hsa_verbal: 23,
  hsa_science: 26,
};
const MAC_DINH = 27;

// Hình dạng hai phản hồi nay khai MỘT chỗ ở `lib/duLieuHsa.ts` — ba khối dùng chung.
type Khoa = KhoaDangHoc;

function chonKhoa(ds: Khoa[], daXong: Record<string, number>) {
  const soXong = (c: Khoa) =>
    daXong[c.id] ?? Math.round(((c.progress ?? 0) / 100) * (TONG_BAI[c.id] ?? MAC_DINH));
  const xep = [...ds].sort((a, b) => soXong(b) - soXong(a));
  return xep.find((c) => soXong(c) < (TONG_BAI[c.id] ?? MAC_DINH)) ?? xep[0] ?? null;
}

/**
 * ĐƯA LUÔN HAI PHẢN HỒI XUỐNG CHO TẦNG CŨ, khỏi gọi lần hai.
 *
 * `dashboard.js` vẽ bốn thẻ số + dải 7 ngày từ `hsa/summary`, dải tiến độ ba
 * hợp phần từ `courses-enrolled` — đúng hai lượt máy chủ vừa gọi ở đây. Trước
 * 14/09 trình duyệt gọi lại cả hai (qua `NapTruocDuLieu`): hai lượt thừa mỗi
 * lần mở trang, và bốn thẻ số phải chờ thêm một vòng mạng sau hydrate.
 *
 * Cách đưa: một `<script>` nhỏ chảy cùng khối, đặt lời hứa ĐÃ GIẢI vào
 * `window.__napTruoc` — cùng ổ khoá mà `main.js::__apiGet` đọc. Trình duyệt
 * chạy script trong luồng HTML lúc phân tích, kể cả khi nó nằm trong khung
 * ẩn của React; tầng cũ chạy sau hydrate nên thường tới sau. Nếu tới TRƯỚC
 * (máy chủ trả chậm), `__apiGet` không thấy khoá thì tự `fetch` như cũ — chỉ
 * mất phần lợi, không mất dữ liệu.
 *
 * `<` thay cho `<`: JSON là dữ liệu của chính người dùng, nhưng tên khoá
 * học là chữ người khác soạn; một chuỗi `</script>` trong đó là đóng thẻ sớm.
 */
function DuaXuong({ duLieu }: { duLieu: Record<string, unknown> }) {
  const than = Object.entries(duLieu)
    .map(([k, v]) => `w[${JSON.stringify(k)}]=Promise.resolve(${JSON.stringify(v).replace(/</g, '\\u003c')})`)
    .join(';');
  return (
    <script
      dangerouslySetInnerHTML={{ __html: `(function(){var w=window.__napTruoc=window.__napTruoc||{};${than}})();` }}
    />
  );
}

export default async function HocTiep() {
  // `cache()` ở `duLieuHsa`: hàng thẻ số và dải tiến độ gọi cùng hai hàm này
  // trong cùng lượt dựng — ba khối, hai lượt API.
  const [sum, khoa] = await Promise.all([layTomTat(), layKhoaDangHoc()]);
  // Chỉ còn `courses-enrolled` cần đưa xuống: `main.js::loadCoursesAndEnrolled`
  // (tab Khoá học) đọc nó qua `__apiGet`. `hsa/summary` từng đưa xuống cho
  // `renderTiles` — hàm ấy đã sang React (`TheSoHsa`), không ai ở tầng cũ đọc nữa.
  const duaXuong: Record<string, unknown> = {};
  if (khoa.ok) duaXuong['/api/courses-enrolled'] = khoa.data;

  const daXong = sum.ok ? sum.data.byCourse : {};
  const c = khoa.ok ? chonKhoa(khoa.data.enrolled, daXong) : null;
  if (!c) {
    return (
      <>
        <DuaXuong duLieu={duaXuong} />
        <HocTiepRong />
      </>
    );
  }

  const tong = TONG_BAI[c.id] ?? MAC_DINH;
  const xong = daXong[c.id] ?? Math.round(((c.progress ?? 0) / 100) * tong);
  const baiKe = Math.min(tong, xong + 1);
  const pct = Math.round((xong / tong) * 100);

  return (
    <>
    <DuaXuong duLieu={duaXuong} />
    <Link className="hsa-cont-link" href={`/lesson/${c.id}?lesson=${baiKe}`}>
      <span className="hsa-cont-badge">{baiKe}</span>
      <span className="hsa-cont-txt">
        <span className="hsa-cont-eyebrow">Học tiếp</span>
        <div className="hsa-cont-title">
          {c.title || 'Khoá học'} — Bài {baiKe}
        </div>
        <span className="hsa-cont-meta">
          {pct}% hoàn thành · {tong} bài
        </span>
      </span>
      <span className="hsa-cont-go">Vào học →</span>
    </Link>
    </>
  );
}
