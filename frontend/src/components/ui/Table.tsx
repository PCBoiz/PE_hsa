import type { ReactNode } from 'react';

/**
 * Bảng dữ liệu.
 *
 * Bảng LUÔN cuộn ngang trong khung riêng của nó (`overflow-x-auto`), để trang
 * không bao giờ trượt ngang. Trang trượt ngang trên điện thoại là lỗi khó chịu
 * nhất và cũng khó phát hiện nhất, vì trên máy tính không thấy gì cả.
 *
 * Cỡ chữ ở đây là 13px chứ không phải 15px như thân bài: màn hình giảng viên
 * là màn hình CÔNG CỤ, người ta quét mắt tìm "ai cần gọi điện hôm nay" nên
 * cần mật độ cao. Nhưng 13px là SÀN — bản cũ có ô 10.5px, không đọc nổi.
 */
export function TableWrap({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-md border border-line bg-surface">
      <table className="w-full border-collapse text-small">{children}</table>
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

export function Td({
  children,
  num = false,
  muted = false,
}: {
  children: ReactNode;
  /** Ô chứa số: phông đơn cách, thẳng cột, không xuống dòng. */
  num?: boolean;
  muted?: boolean;
}) {
  return (
    <td
      className={[
        'border-b border-line/50 px-3 py-3 align-top',
        num ? 'whitespace-nowrap text-right font-mono tabular-nums' : '',
        muted ? 'text-ink-3' : 'text-ink-2',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {children}
    </td>
  );
}

/** Dòng đã rời lớp / đã huỷ: mờ đi nhưng KHÔNG xoá khỏi bảng. */
export function Tr({ children, dim = false }: { children: ReactNode; dim?: boolean }) {
  return (
    <tr className={`last:[&>td]:border-b-0 hover:bg-sunken/60 ${dim ? 'opacity-50' : ''}`}>
      {children}
    </tr>
  );
}
