'use client';

import { useEffect, useState } from 'react';

import { KHOA_NHOM_VAI, nhomCuaVai } from './nhomVai';

type NguoiDung = { role?: string | null };

/** Đặt nhóm lên `<html>` và nhớ cho lần mở sau trong CÙNG tab. */
function apNhom(vai: string) {
  const nhom = nhomCuaVai(vai);
  if (!nhom) return;
  document.documentElement.setAttribute('data-vai-nhom', nhom);
  try { sessionStorage.setItem(KHOA_NHOM_VAI, nhom); } catch { /* chế độ riêng tư */ }
}

/**
 * Vai của người đang đăng nhập, cho KHUNG giao diện — xem `nhomVai.ts`.
 *
 * Thứ tự hỏi, rẻ nhất trước:
 *  1. `vaiBiet` — trang đã đọc vai ở máy chủ (khu Vận hành) thì dùng luôn.
 *  2. `window.__currentUser` — trang có `main.js` (`coLegacy`) đã tự gọi
 *     `/api/user`; đợi nó tới 20 s (máy chủ ngủ dậy mất 80 s, nhưng lúc ấy cả
 *     trang cũng đang chờ) thay vì bắn một lượt thứ hai cho cùng câu trả lời.
 *     Trang KHÔNG có `main.js` thì chỉ ngó 1 s rồi tự hỏi.
 *  3. Tự gọi `/api/user`.
 */
export function useVaiHienTai(vaiBiet?: string, coLegacy = false): string | undefined {
  const [vaiHoi, setVaiHoi] = useState<string | undefined>();

  useEffect(() => {
    if (vaiBiet) { apNhom(vaiBiet); return; }
    let xong = false;
    const nhan = (u: NguoiDung | null | undefined) => {
      if (xong || !u?.role) return;
      xong = true;
      apNhom(u.role);
      setVaiHoi(u.role);
    };
    let lan = 0;
    const hen = window.setInterval(() => {
      const u = (window as unknown as { __currentUser?: NguoiDung }).__currentUser;
      if (u?.role) { window.clearInterval(hen); nhan(u); return; }
      if (++lan < (coLegacy ? 200 : 10)) return;
      window.clearInterval(hen);
      fetch('/api/user', { credentials: 'same-origin' })
        .then((r) => (r.ok ? r.json() : null))
        .then(nhan)
        .catch(() => { /* chưa đăng nhập / mạng hỏng: giữ nguyên, không đoán */ });
    }, 100);
    return () => { xong = true; window.clearInterval(hen); };
  }, [vaiBiet, coLegacy]);

  return vaiBiet ?? vaiHoi;
}
