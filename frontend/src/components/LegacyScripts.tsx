'use client';

/**
 * Nạp tuần tự các file JS legacy (copy nguyên trong /public/static/js) SAU khi
 * markup của trang đã mount — đúng vị trí <script> cuối <body> của template
 * Flask cũ. KHÔNG rewrite logic legacy; thứ tự mảng src = thứ tự <script> gốc.
 *
 * pe-bridge.js luôn được chèn đầu tiên (fetch/JWT/DOMContentLoaded bridge).
 * CDN script (mermaid, codemirror, confetti...) truyền qua cùng mảng src.
 */
import { useEffect } from 'react';

const BRIDGE = '/static/js/pe-bridge.js';

function loadSequential(srcs: string[]): { cancelled: () => boolean; cancel: () => void } {
  let cancelled = false;
  (async () => {
    for (const src of srcs) {
      if (cancelled) return;
      // Script đã có (điều hướng client-side quay lại trang) → không nạp lại;
      // file legacy khai báo hàm/biến global, nạp 2 lần sẽ lỗi redeclare.
      if (document.querySelector(`script[data-pe-legacy="${src}"]`)) continue;
      await new Promise<void>((resolve) => {
        const el = document.createElement('script');
        el.src = src;
        el.async = false;
        el.dataset.peLegacy = src;
        el.onload = () => resolve();
        el.onerror = () => {
          console.error('[LegacyScripts] không nạp được', src);
          resolve();
        };
        document.body.appendChild(el);
      });
    }
    if (!cancelled) document.dispatchEvent(new Event('pe:legacy-ready'));
  })();
  return { cancelled: () => cancelled, cancel: () => { cancelled = true; } };
}

export default function LegacyScripts({
  srcs,
  globals,
  prepare,
}: {
  srcs: string[];
  /** Globals script legacy cần (thay inline <script> Jinja gốc — React không
   *  thực thi <script> trong JSX). Được gán vào window TRƯỚC khi nạp script. */
  globals?: Record<string, unknown>;
  /** Setup DOM script legacy cần (vd: body data-attr) — chạy TRƯỚC khi nạp script. */
  prepare?: () => void;
}) {
  useEffect(() => {
    // KHÔNG dùng guard useRef "chạy 1 lần": StrictMode dev mount→unmount→remount
    // cùng instance nên ref giữ true, còn cleanup đã cancel() chuỗi nạp giữa
    // chừng → script sau bridge không bao giờ được nạp (bug enroll undefined).
    // Dedup thật sự nằm ở querySelector[data-pe-legacy] trong loadSequential;
    // race giữa 2 lần chạy an toàn vì script async=false thực thi theo thứ tự chèn.
    if (globals) Object.assign(window, globals);
    if (prepare) prepare();
    const all = [BRIDGE, ...srcs];
    const handle = loadSequential(all);
    return () => handle.cancel();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
}
