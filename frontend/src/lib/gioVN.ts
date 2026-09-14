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
