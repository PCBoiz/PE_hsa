'use client';

import { useEffect, useState } from 'react';

/**
 * KHOÁ ô liên hệ phụ huynh ở Cài đặt khi trung tâm đã nhập (§47, C5 — 14/09/2026).
 *
 * Máy chủ mới là hàng rào (`PUT /api/user` trả 400 nêu đúng ô). Khối này chỉ
 * làm cho hàng rào ấy NHÌN THẤY ĐƯỢC trước khi em bấm Lưu: ô đã có thông tin
 * thành chỉ-đọc kèm một câu nói vì sao, ô còn trống vẫn gõ được.
 *
 * ── VÌ SAO Ở `src/` VÀ TỰ GỌI `/api/user` ───────────────────────────────
 *
 * Ô nhập do `main.js::loadUser` (tầng cũ) điền giá trị theo `[data-ho-so]`.
 * Đặt thêm vài dòng vào đó là thêm LOGIC MỚI vào tầng đang bị chốt hãm
 * (`chot-ham-tang-cu`), nên khối này đứng riêng ở `src/` và tự hỏi máy chủ.
 * Tốn một lượt `/api/user` thứ hai — chấp nhận, vì nó chỉ chạy khi người dùng
 * MỞ tab Cài đặt (quan sát panel cha, cùng lối với `BaHopPhan`).
 *
 * Quyết định "ô nào khoá" lấy từ CHÍNH phản hồi máy chủ (giá trị đang lưu),
 * không đọc `value` trong DOM: `loadUser` của tầng cũ có thể điền sau hoặc
 * trước khối này, và đọc DOM lúc nào cũng có thể đọc phải ô còn rỗng.
 */
type HoSo = {
  parent_contact_locked?: boolean;
  parent_name?: string | null;
  parent_phone?: string | null;
  parent_email?: string | null;
};

const O: (keyof HoSo)[] = ['parent_name', 'parent_phone', 'parent_email'];

export default function KhoaLienHePhuHuynh() {
  const [khoa, setKhoa] = useState<{ o: string[] } | null>(null);

  useEffect(() => {
    const goc = document.getElementById('lien-he-phu-huynh');
    if (!goc) return;
    let huy = false;

    const nap = async () => {
      try {
        const r = await fetch('/api/user', { credentials: 'same-origin' });
        if (!r.ok) return;
        const u = (await r.json()) as HoSo;
        if (huy || !u.parent_contact_locked) return;
        const daCo = O.filter((k) => (u[k] ?? '') !== '');
        for (const k of daCo) {
          const o = goc.querySelector<HTMLInputElement>(`[data-ho-so="${k}"]`);
          if (o) {
            o.readOnly = true;
            o.setAttribute('aria-describedby', 'khoa-lien-he-ph');
          }
        }
        setKhoa({ o: daCo });
      } catch {
        /* mất mạng chốc lát: máy chủ vẫn chặn, chỉ thiếu lời báo trước */
      }
    };

    const canh = goc.closest('.page') ?? goc;
    const io = new IntersectionObserver((cac) => {
      if (cac.some((e) => e.isIntersecting)) {
        io.disconnect();
        void nap();
      }
    });
    io.observe(canh);
    return () => {
      huy = true;
      io.disconnect();
    };
  }, []);

  if (!khoa) return null;
  return (
    <p id="khoa-lien-he-ph" className="goal-hint" role="note">
      Trung tâm đã nhập liên hệ phụ huynh của bạn, nên ô đã có thông tin chỉ học vụ
      sửa được — cần đổi thì báo học vụ.
      {khoa.o.length < O.length && ' Ô còn trống bạn vẫn tự điền được.'}
    </p>
  );
}
