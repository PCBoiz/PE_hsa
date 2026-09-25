/**
 * NGÀY GIỜ THEO GIỜ VIỆT NAM — cho mã chạy ở CẢ máy chủ lẫn trình duyệt.
 *
 * ── VÌ SAO CÓ (14/09/2026, tối) ────────────────────────────────────────────
 *
 * Dải "Lịch học tuần này" trên Trang của tôi tô ô hôm nay bằng
 * `new Date().getDay()` — tức đồng hồ của MÁY ĐANG CHẠY mã. Khi tầng cũ vẽ nó
 * ở trình duyệt thì đúng. Chuyển sang dựng ở máy chủ thì Vercel chạy UTC: từ 0h
 * tới 7h sáng giờ Việt Nam, máy chủ vẫn là HÔM QUA → ô hôm nay tô sai một ngày,
 * và React báo lỗi hydrate vì trình duyệt (giờ VN) dựng ra thứ khác.
 *
 * Backend đã học bài này ở `common.clock.local_today()`. Đây là bản cho phía
 * frontend: luôn hỏi `Intl` theo múi `Asia/Ho_Chi_Minh`, nên máy nào chạy cũng
 * ra cùng một kết quả.
 */
const MUI = 'Asia/Ho_Chi_Minh';
const THU_EN = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

/** Thứ trong tuần theo giờ VN, **thứ Hai = 0 … Chủ nhật = 6** (lịch Việt). */
export function thuTrongTuanVN(luc: Date = new Date()): number {
  const ten = new Intl.DateTimeFormat('en-US', { timeZone: MUI, weekday: 'short' }).format(luc);
  const i = THU_EN.indexOf(ten);
  // Không bao giờ nên xảy ra; rơi về 0 thay vì -1 để mảng không vỡ.
  return i < 0 ? 0 : i;
}

/** "2026-09-24" — ngày hôm nay theo giờ VN, cùng dạng ngày máy chủ trả. So CHUỖI
 *  với ngày của buổi học (máy chủ đã tính theo giờ VN), không dựng `Date`: máy
 *  chủ Vercel chạy UTC nên `new Date('2026-09-24T19:00')` đọc theo UTC. */
export function ngayVN(luc: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: MUI, year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(luc);
}

/**
 * "25/09/2026 20:15" từ chuỗi giờ VN NGÂY THƠ máy chủ trả ('2026-09-25T20:15:03.12';
 * chỉ có ngày thì "25/09/2026"). TÁCH CHUỖI, không qua `Date` — `new Date(...)` trên
 * Vercel (UTC) đọc chuỗi ấy theo UTC rồi định dạng lại là lệch múi. Chuỗi lạ trả
 * nguyên, không đoán; rỗng trả '—'.
 */
export function lucVN(iso: string | null | undefined): string {
  if (!iso) return '—';
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/.exec(iso);
  if (!m) return iso;
  return m[4] ? `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}` : `${m[3]}/${m[2]}/${m[1]}`;
}

/** "Thứ Hai, 22/09/2026" theo giờ VN — cho dòng ngày dưới tiêu đề "Việc hôm nay"
 *  (22/09/2026, agent GV→PH F14: màn không nói "hôm nay" là ngày nào). */
export function ngayDayDuVN(luc: Date = new Date()): string {
  const s = new Intl.DateTimeFormat('vi-VN', {
    timeZone: MUI, weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric',
  }).format(luc);
  return s.charAt(0).toUpperCase() + s.slice(1);
}
