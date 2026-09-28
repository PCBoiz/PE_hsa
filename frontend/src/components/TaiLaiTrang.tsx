'use client';

import { useEffect, useState } from 'react';

import { Button } from '@/components/ui';
import { useDaGan } from '@/lib/daGan';

/** Giây giữa hai lượt tự tải lại. Render đo 28/09: lượt đánh thức mất 63–73 giây. */
const NHIP = 20;
/** Tự thử tối đa chừng này lượt rồi thôi — hơn 3 phút mà chưa lên là hỏng thật. */
const SO_LUOT = 9;

/**
 * "Tải lại" cho trang không có tài khoản — và tự thử lại hộ trong lúc máy chủ thức dậy.
 *
 * ── VÌ SAO TỰ THỬ, KHÔNG CHỈ ĐỂ MỘT CÁI NÚT (28/09/2026) ──────────────────
 *
 * Người đọc trang này là phụ huynh, mở từ một tin Zalo, trên điện thoại, không tài khoản.
 * Một cái nút kèm câu "thử lại sau một phút" đòi họ tự canh giờ và tự bấm — phần lớn sẽ
 * đóng tab trước đó và nhắn giảng viên "link hỏng", trong khi chìa vẫn tốt.
 *
 * Nên trang tự gõ cửa lại mỗi 20 giây, và NÓI RA là đang làm thế. Nút vẫn còn cho ai không
 * muốn chờ. Dừng sau 9 lượt (~3 phút): quá đó thì không còn là máy chủ ngủ nữa, và gõ mãi
 * chỉ tốn pin của người ta.
 *
 * Đếm ngược chỉ chạy sau khi React gắn (`useDaGan`) — máy chủ và trình duyệt phải dựng ra
 * cùng một HTML, và "còn 20 giây" thì không.
 */
export default function TaiLaiTrang() {
  const daGan = useDaGan();
  const [con, setCon] = useState(NHIP);
  const [luot, setLuot] = useState(0);
  const het = luot >= SO_LUOT;

  useEffect(() => {
    if (!daGan || het) return;
    const dongHo = setInterval(() => {
      setCon((c) => {
        if (c > 1) return c - 1;
        setLuot((n) => n + 1);
        // `location.reload()` chứ không `router.refresh()`: trang này là Server Component
        // và thứ hỏng nằm ở lượt gọi Django của máy chủ Next, không ở trạng thái React.
        window.location.reload();
        return NHIP;
      });
    }, 1000);
    return () => clearInterval(dongHo);
  }, [daGan, het]);

  return (
    <div className="mt-6 flex flex-wrap items-center gap-3">
      <Button onClick={() => window.location.reload()} disabled={!daGan}>
        Tải lại trang
      </Button>
      {daGan && !het && (
        <span role="status" className="text-small text-ink-3">
          Trang sẽ tự thử lại sau {con} giây.
        </span>
      )}
      {het && (
        <span role="status" className="text-small text-ink-3">
          Đã thử lại {SO_LUOT} lần mà chưa được — bấm nút trên để thử tiếp.
        </span>
      )}
    </div>
  );
}
