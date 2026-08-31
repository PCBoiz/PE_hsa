import type { ReactNode } from 'react';

/**
 * Bảng dữ liệu — bảng thật trên màn rộng, XẾP THÀNH THẺ trên màn hẹp.
 *
 * ── Vì sao phải đổi bố cục, không chỉ cuộn ngang ────────────────────────────
 * Đo ngày 30/08/2026 ở khổ 390px: bảng Tài khoản rộng 796px nằm trong khung
 * 306px, tức **giấu đi 490px — 62% nội dung**. Cột rơi ra ngoài là cột "Thao
 * tác", nên trên điện thoại KHÔNG bấm được "Đặt lại mật khẩu" và "Khoá" — đúng
 * hai việc mà màn hình đó sinh ra để làm. Nhật ký giấu 45% và mất cột "Nội
 * dung", thứ duy nhất nói chuyện gì đã xảy ra.
 *
 * `overflow-x-auto` giữ cho TRANG không trượt ngang, và điều đó vẫn đúng. Nhưng
 * nó chỉ dời vấn đề vào trong khung: không có gợi ý thị giác nào báo còn nội
 * dung bên phải, nên người dùng không biết mà cuộn.
 *
 * Dưới 640px, mỗi dòng trở thành một THẺ: nhãn cột hiện bên trái, giá trị bên
 * phải, không còn gì bị cắt. Trên 640px vẫn là bảng nguyên vẹn — màn hình công
 * cụ cần mật độ cao để quét mắt.
 *
 * ── Vì sao `label` là BẮT BUỘC ──────────────────────────────────────────────
 * Ở dạng thẻ, phần đầu bảng biến mất, nên mỗi ô phải tự mang tên cột của nó.
 * Khai `label` là bắt buộc trong kiểu để `tsc` chặn ngay khi ai đó thêm cột mới
 * mà quên — nếu để tuỳ chọn thì cột mới sẽ hiện một giá trị trần không rõ là
 * cái gì, và chỉ ai mở đúng trang đó trên điện thoại mới phát hiện ra.
 *
 * Cỡ chữ 13px chứ không phải 15px như thân bài: đây là màn hình CÔNG CỤ, người
 * ta quét mắt tìm "ai cần gọi điện hôm nay". Nhưng 13px là SÀN — bản cũ có ô
 * 10.5px, không đọc nổi.
 */
export function TableWrap({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-md border border-line bg-surface">
      <table className="w-full border-collapse text-small max-sm:block">{children}</table>
    </div>
  );
}

export function Th({
  children,
  align = 'left',
}: {
  children: ReactNode;
  align?: 'left' | 'right';
}) {
  return (
    <th
      className={`whitespace-nowrap border-b border-line bg-sunken px-3 py-2 text-label text-ink-3 ${
        align === 'right' ? 'text-right' : 'text-left'
      }`}
    >
      {children}
    </th>
  );
}

/** Phần đầu bảng. Ẩn hẳn ở dạng thẻ — mỗi ô đã tự mang nhãn của nó. */
export function Thead({ children }: { children: ReactNode }) {
  return <thead className="max-sm:hidden">{children}</thead>;
}

export function Tbody({ children }: { children: ReactNode }) {
  return <tbody className="max-sm:block">{children}</tbody>;
}

export function Td({
  children,
  label,
  num = false,
  muted = false,
}: {
  children: ReactNode;
  /**
   * Tên cột. BẮT BUỘC: ở dạng thẻ (dưới 640px) phần đầu bảng bị ẩn nên đây là
   * thứ duy nhất cho biết giá trị này là cái gì.
   */
  label: string;
  /** Ô chứa số: phông đơn cách, thẳng cột, không xuống dòng. */
  num?: boolean;
  muted?: boolean;
}) {
  return (
    <td
      className={[
        'border-b border-line/50 px-3 py-3 align-top',
        // Ở dạng thẻ: nhãn bên trái, giá trị bên phải, cùng một hàng.
        'max-sm:flex max-sm:items-baseline max-sm:justify-between max-sm:gap-3',
        'max-sm:border-b-0 max-sm:px-0 max-sm:py-1',
        num ? 'whitespace-nowrap text-right font-mono tabular-nums' : '',
        muted ? 'text-ink-3' : 'text-ink-2',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {/* KHÔNG `aria-hidden`. Chú thích cũ ở đây viết "trình đọc màn hình đã
          lấy tên cột từ `<th>`" — đúng trên màn rộng, SAI đúng ở chế độ mà đoạn
          mã này sinh ra: dưới 640px `<thead>` là `display:none`, tức bị loại
          khỏi cây trợ năng, nên không còn `<th>` nào để lấy tên.

          Đo bằng CDP ngày 31/08/2026 ở khổ 390px: số ô `columnheader` trong cây
          trợ năng = 0, và tên các ô là "a", "a@gmail.com", "Đang hoạt động" —
          không ô nào cho biết đó là cột gì. Người dùng trình đọc màn hình trên
          điện thoại nghe một chuỗi giá trị trần.

          Ở màn rộng nhãn này `display:none` nên không có chuyện đọc hai lần. */}
      <span className="hidden text-label text-ink-3 max-sm:block">{label}</span>
      <span className="max-sm:min-w-0 max-sm:flex-1 max-sm:text-right">{children}</span>
    </td>
  );
}

/** Dòng đã rời lớp / đã huỷ: mờ đi nhưng KHÔNG xoá khỏi bảng. */
export function Tr({ children, dim = false }: { children: ReactNode; dim?: boolean }) {
  return (
    <tr
      className={[
        'last:[&>td]:border-b-0 hover:bg-sunken/60',
        // Mỗi dòng là một thẻ có viền riêng ở khổ hẹp, để mắt biết chỗ nào là
        // hết một người và bắt đầu người tiếp theo.
        'max-sm:block max-sm:border-b max-sm:border-line max-sm:px-3 max-sm:py-3',
        'max-sm:last:border-b-0',
        dim ? 'opacity-50' : '',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {children}
    </tr>
  );
}
