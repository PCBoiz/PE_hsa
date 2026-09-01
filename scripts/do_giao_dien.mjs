/**
 * ĐO GIAO DIỆN cả sản phẩm — số nền để so trước/sau.
 *
 *     node scripts/do_giao_dien.mjs            # đo và in
 *     node scripts/do_giao_dien.mjs --json ra.json
 *
 * CHỈ ĐỌC. Chặn theo PHƯƠNG THỨC (RULES §22), không theo tên đường: GET/HEAD đi
 * thật, mọi thứ khác bị giả lập và ĐẾM, rồi báo số lời gọi ghi lọt ra.
 *
 * ĐO GÌ, theo thứ tự ưu tiên của ui-ux-pro-max:
 *   ① Tương phản chữ/nền — WCAG AA: 4,5:1 chữ thường, 3:1 chữ lớn
 *   ② Vùng chạm — tối thiểu 44×44 CSS px
 *   ③ Tràn ngang ở khổ điện thoại
 *   ④ Lỗi JS
 *
 * BỐN LỖI ĐÃ MẮC TRONG CHÍNH BỘ ĐO NÀY (01/09/2026) — đọc trước khi sửa nó:
 *   · bỏ qua nền gradient (`background-image`) → chữ trắng trên hero tím bị
 *     tính là trắng-trên-trắng, 26 dương tính giả;
 *   · bỏ qua chữ gradient (`background-clip: text`) → tiêu đề bài học ra 1:1;
 *   · không đọc được cú pháp `color(srgb 1 1 1 / .95)` mà `color-mix` sinh ra
 *     → thanh gần trắng bị báo 2,1:1;
 *   · regex `[\d.]` nằm trong template literal bị nuốt một gạch chéo thành
 *     `[d.]` → không rút được số nào, mọi tương phản thành NaN, và `NaN < 4.5`
 *     là FALSE — bộ đo báo **0 vi phạm** kể cả khi cố ý đặt chữ chính gần trắng.
 *
 * Vì lỗi cuối, luôn tự kiểm bằng `--tu-kiem`: nó đặt một quy tắc hỏng vào trang
 * rồi đòi bộ đo phải BẮT ĐƯỢC. Một bộ đo không đỏ được là một bộ đo giả.
 */
import { readFileSync, writeFileSync } from 'node:fs';

const PW = 'file:///D:/pe_hsa/frontend/node_modules/.pnpm/playwright@1.61.1/node_modules/playwright/index.mjs';
const TOKEN = process.env.PE_TOKENS
  || 'C:/Users/sonkh/AppData/Local/Temp/claude/d--PE-test/5192ee2d-32a6-400e-b0de-d9b2020fb7a3/scratchpad/tokens_ad.json';
const GOC = process.env.PE_URL || 'http://localhost:3100';

const KHO = [
  // `cham` = `hasTouch`. BẮT BUỘC đúng cho từng khổ: thiếu nó Chromium báo
  // `pointer: fine`, và nút mang `[@media(pointer:fine)]:min-h-9` co xuống 36px
  // — ra 'thiếu 8px' cho một nút thật ra đủ 44px trên điện thoại thật.
  // Đã mất một lượt đo vì chuyện này (T45, 31/08/2026).
  { ten: 'điện thoại', w: 390, h: 844, cham: true },
  { ten: 'máy tính', w: 1440, h: 900, cham: false },
];
const TRANG = [
  ['/dashboard', 'Dashboard'],
  ['/courses/hsa_quantitative', 'Chi tiết khoá'],
  ['/lesson/hsa_quantitative?lesson=1', 'Bài học'],
  ['/mock', 'Thi thử'],
  ['/bai-tap', 'Bài tập của tôi'],
  ['/questionaire', 'Khảo sát'],
  ['/quan-tri/tong-quan', 'Quản trị · tổng quan'],
  ['/quan-tri/tai-khoan', 'Quản trị · tài khoản'],
  ['/quan-tri/dot-hoc', 'Quản trị · đợt học'],
  ['/quan-tri/nhat-ky', 'Quản trị · nhật ký'],
  ['/doi-mat-khau', 'Đổi mật khẩu'],
  /* Khu GIẢNG DẠY. Cần một lớp có thật; `1` là lớp duy nhất đang có. Ba màn này
     giảng viên mở mỗi buổi, và trước 01/09/2026 chưa lượt quét nào chạm tới. */
  ['/giang-day/buoi-hoc/1', 'Giảng dạy · buổi học'],
  ['/giang-day/bai-tap/1', 'Giảng dạy · bài tập'],
];

/* Hàm chạy TRONG trang. Viết bằng function thật rồi `.toString()` thay vì nhét
   vào template literal — chuỗi lồng chuỗi là chỗ dấu gạch chéo bị nuốt. */
function DO_TRONG_TRANG(do_trang_thai) {
  const SO = /[0-9.]+/g;

  /* Giải mã màu bằng CHÍNH trình duyệt, không tự viết bộ đổi không gian màu.
     `color-mix(in oklab, ...)` tính ra `oklab(0.958 0.004 -0.0099 / 0.6)` — một
     màu rất SÁNG — nhưng đọc số thô thì ra [0.958, 0.004, 0.0099] (dấu trừ còn
     bị nuốt) và hoá thành gần ĐEN: 29 vi phạm 1,05:1 không có thật ở bảng quản
     trị. Canvas nhận mọi cú pháp CSS Color 4, kể cả cú pháp sinh sau bản này. */
  const _cv = document.createElement('canvas');
  _cv.width = 1; _cv.height = 1;
  const _ctx = _cv.getContext('2d', { willReadFrequently: true });
  _ctx.globalCompositeOperation = 'copy';
  const qua_canvas = (s) => {
    /* Gán một giá trị KHÔNG hợp lệ vào `fillStyle` thì trình duyệt lặng lẽ giữ
       giá trị cũ. Thử hai mồi khác nhau: khớp nhau nghĩa là chuỗi phân giải
       được, khác nhau nghĩa là cả hai lần đều giữ mồi cũ. */
    _ctx.fillStyle = '#000000'; _ctx.fillStyle = s; const a = _ctx.fillStyle;
    _ctx.fillStyle = '#ffffff'; _ctx.fillStyle = s; const b = _ctx.fillStyle;
    if (a !== b) return [];
    _ctx.fillRect(0, 0, 1, 1);
    const d = _ctx.getImageData(0, 0, 1, 1).data;
    return d[3] === 255 ? [d[0], d[1], d[2]] : [d[0], d[1], d[2], d[3] / 255];
  };

  const doc_mau = (s) => {
    const t = String(s).trim();
    const dau = t.slice(0, 4).toLowerCase();
    // Đường nhanh cho hai cú pháp chiếm gần hết số lần gọi.
    if (dau === 'rgb(' || dau === 'rgba') return (t.match(SO) || []).slice(0, 4).map(Number);
    return qua_canvas(t);
  };

  const sang = (rgb) => {
    const [r, g, b] = rgb.map((v) => {
      const x = v / 255;
      return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };

  const tp = (fg, bg) => {
    const a = sang(fg), b = sang(bg);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  };

  const phu = (lop, goc) => {
    let acc = goc.slice(0, 3);
    for (const l of lop) {
      const a = l[3] === undefined ? 1 : l[3];
      acc = [0, 1, 2].map((i) => l[i] * a + acc[i] * (1 - a));
    }
    return acc;
  };

  /* Trả DANH SÁCH nền khả dĩ dưới chữ (một mục cho mỗi chặng gradient).
     Chặng gradient là MỘT LỚP CÓ ALPHA như mọi lớp khác, không phải nền đáy.
     Coi nó là đáy thì `rgba(6,182,212,0.18)` — phủ 18% — bị tính như cyan đặc:
     nút "Nộp & xem đánh giá" ra 2,03:1 trong khi thật là 4,94:1 và ĐẠT.
     (dương tính giả thứ năm của chính bộ đo này, 01/09/2026) */
  const nen = (el) => {
    const lop = [];            // dưới → trên; `null` = chỗ dành cho chặng gradient
    let goc = [255, 255, 255]; // nền đục cuối cùng tìm được
    let chang = null;
    let n = el;
    while (n && n !== document.documentElement) {
      const cs = getComputedStyle(n);
      const bi = cs.backgroundImage;
      // Trong một nút, ảnh nền vẽ ĐÈ lên màu nền — nên chèn chỗ dành trước.
      /* `background-clip: text` KHÔNG phải nền: gradient chỉ tô trong nét chữ
         của chính nút đó, phía sau chữ con vẫn là nền của tổ tiên. Tính nó là
         nền làm `.brand-c1` (màu #8B7CF6) nằm trên chặng gradient #8B7CF6 →
         đúng 1:1, một vi phạm nặng nhất bảng mà không có thật. */
      const cat = cs.webkitBackgroundClip || cs.backgroundClip;
      if (!chang && cat !== 'text' && bi && bi !== 'none' && bi.indexOf('gradient') !== -1) {
        const g = (bi.match(/rgba?\([^)]*\)|color\([^)]*\)/g) || [])
          .map((x) => { const v = doc_mau(x); return v.length === 3 ? [v[0], v[1], v[2], 1] : v; })
          .filter((v) => v.length === 4);
        if (g.length) { chang = g; lop.unshift(null); }
      }
      const bg = doc_mau(cs.backgroundColor);
      if (bg.length === 3) { goc = bg; break; }        // đục → hết đường xuống
      if (bg.length === 4 && bg[3] > 0) lop.unshift([bg[0], bg[1], bg[2], bg[3]]);
      n = n.parentElement;
    }
    return (chang || [null]).map((c) =>
      phu(lop.map((l) => (l === null ? c : l)).filter(Boolean), goc));
  };

  const hien = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const cs = getComputedStyle(el);
    return cs.visibility !== 'hidden' && cs.display !== 'none'
      && parseFloat(cs.opacity) > 0.05;
  };

  const duong = (el) => {
    const p = [];
    let n = el;
    while (n && n.tagName && p.length < 4) {
      const c = (n.className && typeof n.className === 'string')
        ? '.' + n.className.trim().split(/\s+/)[0] : '';
      p.unshift(n.tagName.toLowerCase() + c);
      n = n.parentElement;
    }
    return p.join('>');
  };

  /* Điều kiện "nút này có chữ đáng đo": có chữ TRỰC TIẾP, và không phải chỉ
     biểu tượng cảm xúc — emoji là ảnh nhiều màu do phông màu vẽ, `color` không
     quyết định pixel nào của nó. */
  const co_chu = (el) => {
    let t = '';
    for (const nd of el.childNodes) if (nd.nodeType === 3) t += nd.textContent;
    t = t.trim();
    if (t.length < 2) return false;
    return /[\p{L}\p{N}]/u.test(t.replace(/\p{Extended_Pictographic}/gu, ''));
  };

  /* Tương phản của MỘT nút, theo đúng trạng thái đang có trên trang lúc gọi.
     Tách ra hàm riêng để lượt đo trạng thái tương tác dùng lại y hệt bộ quy
     tắc — hai bộ quy tắc song song là hai bộ sẽ lệch nhau. */
  const do_el = (el) => {
    const cs = getComputedStyle(el);
    const clip = cs.webkitBackgroundClip || cs.backgroundClip;
    const fill = String(cs.webkitTextFillColor || '');
    // Chữ gradient: màu chữ THẬT là các chặng gradient, `color` chỉ là dự phòng.
    const chu_gradient = clip === 'text'
      && (fill.split(' ').join('') === 'rgba(0,0,0,0)' || fill === 'transparent');

    let truoc, sau;
    if (chu_gradient) {
      const mau = (cs.backgroundImage.match(/rgba?\([^)]*\)|color\([^)]*\)/g) || [])
        .map((x) => doc_mau(x).slice(0, 3));
      truoc = mau.length ? mau : [doc_mau(cs.color).slice(0, 3)];
      sau = el.parentElement ? nen(el.parentElement) : [[255, 255, 255]];
    } else {
      truoc = [doc_mau(cs.color).slice(0, 3)];
      sau = nen(el);
    }

    let xau_nhat = Infinity;
    for (const fg of truoc) for (const bg of sau) xau_nhat = Math.min(xau_nhat, tp(fg, bg));
    if (!isFinite(xau_nhat)) return null;

    const co = parseFloat(cs.fontSize);
    const dam = (parseInt(cs.fontWeight, 10) || 400) >= 700;
    const lon = co >= 24 || (co >= 18.66 && dam);
    return { tp: Math.round(xau_nhat * 100) / 100, nguong: lon ? 3 : 4.5, co: Math.round(co) };
  };

  const vi_pham = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!hien(el) || !co_chu(el)) continue;
    const d = do_el(el);
    if (d && d.tp < d.nguong) {
      vi_pham.push({ duong: duong(el), ...d, chu: el.textContent.trim().slice(0, 40) });
    }
  }

  const CHAM = 'a[href], button, input, select, textarea, [role="button"], [tabindex]:not([tabindex="-1"])';
  /* Ngưỡng phụ thuộc THIẾT BỊ TRỎ, không phải một con số chung:
     · cảm ứng → 44×44 (Apple HIG) / 48×48 (Material) — ngón tay không nhắm được;
     · chuột   → 24×24 (WCAG 2.2 SC 2.5.8 mức AA) — con trỏ nhắm chính xác.
     Đo khổ máy tính bằng 44 thì mọi nút cao 30–38px đều "vi phạm" — 80 phát hiện
     không vi phạm chuẩn nào, và chúng chôn mất 11 phát hiện thật ở điện thoại. */
  const cam_ung = matchMedia('(pointer: coarse)').matches;
  const NGUONG = cam_ung ? 44 : 24;
  const nho = [];
  /* Ô đánh dấu nằm TRONG một `<label>` (hoặc có `<label for>`) thì vùng bấm
     thật là cả cái nhãn — trình duyệt chuyển sự kiện về ô. Đo riêng cái ô ra
     28×28 và báo vi phạm là sai: người dùng bấm được cả dòng chữ. */
  const vung = (el) => {
    const r = [el.getBoundingClientRect()];
    if (el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA') {
      const nhan = el.closest('label')
        || (el.id && document.querySelector('label[for="' + CSS.escape(el.id) + '"]'));
      if (nhan && hien(nhan)) r.push(nhan.getBoundingClientRect());
    }
    /* Lấy hộp LỚN HƠN, không phải hộp của nhãn. Nhãn bọc ngoài ô đánh dấu thì
       nó rộng hơn — đúng, vùng bấm là cả nhãn. Nhưng `<label for>` đặt TRÊN ô
       nhập thì nhãn chỉ là dòng chữ 292×17, còn ô mới là đích thật cao 44px:
       trả hộp nhãn là biến một ô đạt chuẩn thành "vi phạm". Bấm được cả hai,
       nên kích thước đích là cái lớn hơn. */
    return r.sort((a, b) => Math.min(b.width, b.height) - Math.min(a.width, a.height))[0];
  };

  for (const el of document.querySelectorAll(CHAM)) {
    if (!hien(el)) continue;
    const r = vung(el);
    /* Trừ hao 0,5px: một đích đặt đúng 44px hay ra 43,98px vì phần lẻ dưới
       pixel của dòng chữ, và làm tròn khi in ra sẽ hiện "44×44 < 44" — một
       vi phạm không ai sửa được vì nó không tồn tại. */
    if (r.width < NGUONG - 0.5 || r.height < NGUONG - 0.5) {
      nho.push({ duong: duong(el), nguong: NGUONG,
        w: Math.round(r.width), h: Math.round(r.height),
        chu: String(el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 30) });
    }
  }

  /* ── TRẠNG THÁI TƯƠNG TÁC — phần ĐÁNH DẤU ───────────────────────────────
     Phép đo tĩnh bỏ lọt cả một lớp lỗi: `.nav-next:hover` đặt `color:#fff` trên
     nền cyan 28% phủ trên trắng (1,14:1) — chữ biến mất khi rê chuột, và không
     lượt quét tĩnh nào thấy.

     KHÔNG tự ép khai báo của luật `:hover` vào kiểu nội tuyến. Làm thế là bỏ
     qua tầng xếp lớp: một luật khác đè lên nó trong sản phẩm thật vẫn bị ép,
     nên bản vá đã có lại bị báo là lỗi. Ở đây chỉ ĐÁNH DẤU phần tử ứng viên;
     việc bật `:hover` giao cho trình duyệt qua CDP `CSS.forcePseudoState`, để
     chính nó giải tầng xếp lớp.

     `:not(:hover)` phải bỏ qua: cắt `:hover` khỏi nó là ĐẢO ngược ý nghĩa luật. */
  const dau = [];
  if (do_trang_thai) {
    const TRANG_THAI = /:(hover|focus-visible|focus)\b/;
    const SON = ['color', 'background-color', 'background-image', '-webkit-text-fill-color'];
    const luat = [];
    for (const bang of document.styleSheets) {
      let ds;
      try { ds = bang.cssRules; } catch (e) { continue; }  // bảng khác nguồn
      const di = (rs) => {
        for (const r of rs) {
          /* KHÔNG viết `if (r.cssRules) { ...; continue; }`. Từ Chrome 112 (CSS
             Nesting) MỌI `CSSStyleRule` đều CÓ `cssRules` — rỗng, nhưng tồn tại
             — nên nhánh đó nuốt sạch luật thường: 371 luật quét được, 0 luật
             chứa `:hover`, và lượt đo báo "0 lỗi rê chuột" vĩnh viễn. */
          if (r.cssRules && r.cssRules.length) di(r.cssRules);
          if (!r.selectorText || !TRANG_THAI.test(r.selectorText)) continue;
          if (/:not\([^)]*:(hover|focus)/.test(r.selectorText)) continue;
          if (!SON.some((k) => r.style.getPropertyValue(k))) continue;
          luat.push(r.selectorText);
        }
      };
      di(ds);
    }

    /* TẮT CHUYỂN TIẾP. Trong tầng xếp lớp CSS, giá trị đang chuyển tiếp thắng
       CẢ `!important` nội tuyến — nên vừa bật `:hover` là một chuyển tiếp khởi
       động và `getComputedStyle` ngay sau đó trả về màu CŨ. Không có dòng này
       thì lượt đo báo 0 vi phạm cho mọi nút có `transition`, tức gần như mọi
       nút. */
    const tat = document.createElement('style');
    tat.id = '__pe_tat_chuyen_tiep';
    tat.textContent = '*, *::before, *::after { transition: none !important;'
      + ' animation: none !important; }';
    document.head.appendChild(tat);

    let n = 0;
    const da_danh = new Set();
    for (const sel of luat) {
      const trang_thai = /focus/.test(sel) ? 'focus' : 'hover';
      const goc = sel.replace(/:(hover|focus-visible|focus)\b/g, '');
      let ds2 = [];
      try { ds2 = [...document.querySelectorAll(goc)]; } catch (e) { continue; }
      for (const el of ds2.filter(hien).slice(0, 2)) {
        if (da_danh.has(el)) continue;
        da_danh.add(el);
        el.setAttribute('data-pe-tt', String(n));
        dau.push({ i: n, trang_thai, sel: sel.slice(0, 70) });
        n++;
      }
    }
  }

  /* ── VÒNG NÉT BÀN PHÍM ─────────────────────────────────────────────────
     WCAG 2.4.7 (AA) chỉ đòi một điều: lấy nét bằng bàn phím thì PHẢI THẤY. Đo
     màu thôi không trả lời được câu đó — một nút có thể đủ tương phản mà khi
     Tab tới thì chẳng đổi gì, và người dùng bàn phím mất dấu hoàn toàn.

     Cách kiểm: chụp dáng vẻ trước, bật `:focus-visible` qua CDP, chụp lại. Y
     hệt nhau = không có dấu hiệu nào.

     Lấy mẫu theo HÌNH DÁNG (thẻ + hai lớp đầu) chứ không quét hết: trang chính
     có 258 phần tử lấy nét được, phần lớn là cùng một nút lặp lại. */
  const net_dau = [];
  if (do_trang_thai) {
    const nhom = new Map();
    for (const el of document.querySelectorAll(CHAM)) {
      if (!hien(el)) continue;
      const k = el.tagName + '|'
        + String(el.className || '').trim().split(/\s+/).slice(0, 2).join('.');
      if ((nhom.get(k) || 0) >= 2) continue;
      nhom.set(k, (nhom.get(k) || 0) + 1);
      if (net_dau.length >= 40) break;
      el.setAttribute('data-pe-net', String(net_dau.length));
      net_dau.push({ i: net_dau.length, duong: duong(el),
        chu: String(el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 28) });
    }
  }

  /* Bộ quy tắc dùng lại cho lượt đo trạng thái, chạy từ phía Node sau khi CDP
     đã bật `:hover`. Hai bộ quy tắc song song là hai bộ sẽ lệch nhau. */
  globalThis.__pe = {
    do_el, hien, co_chu, duong,
    dang: (i) => {
      const el = document.querySelector(`[data-pe-net="${i}"]`);
      if (!el) return null;
      const c = getComputedStyle(el);
      return [c.outlineStyle, c.outlineWidth, c.outlineColor, c.outlineOffset,
        c.boxShadow, c.borderColor, c.borderWidth, c.backgroundColor,
        c.backgroundImage, c.color, c.textDecorationLine].join('|');
    },
  };

  return {
    dau, net_dau,
    vi_pham: vi_pham.slice(0, 60), so_vi_pham: vi_pham.length,
    cham_nho: nho.slice(0, 60), so_cham_nho: nho.length, nguong_cham: NGUONG,
    so_cham: document.querySelectorAll(CHAM).length,
    tran_ngang: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
}

const { chromium } = await import(PW);
const tok = JSON.parse(readFileSync(TOKEN, 'utf8'));
const tu_kiem = process.argv.includes('--tu-kiem');
const chu_de = process.argv.includes('--toi') ? 'dark' : 'light';
const do_tt = process.argv.includes('--trang-thai');
const i_json = process.argv.indexOf('--json');
const ra_json = i_json >= 0 ? process.argv[i_json + 1] : null;

const b = await chromium.launch();
const ket = [];
let ghiLen = 0;

for (const kho of KHO) {
  /* Mỗi khổ MỘT ngữ cảnh, vì `hasTouch` chỉ đặt được lúc mở ngữ cảnh.
     Hai ngữ cảnh dùng CHUNG cặp thẻ vừa cấp: thẻ truy cập sống 30 phút, lượt đo
     hết ~4 phút nên không lần nào phải làm mới. Nếu vẫn hết hạn, chốt chặn dưới
     sẽ DỪNG — chứ không lặng lẽ đo cái vỏ đăng nhập. */
  const c = await b.newContext({
    viewport: { width: kho.w, height: kho.h }, hasTouch: kho.cham });
  /* Chủ đề đọc từ `localStorage.theme` (main.js:1898) rồi mới gắn `body.dark`.
     Đặt TRƯỚC khi trang chạy, chứ gắn class sau khi tải thì đã đo xong nửa
     trang bằng bảng màu kia. */
  await c.addInitScript((t) => {
    try { localStorage.setItem('theme', t); } catch (e) { /* chế độ riêng tư */ }
  }, chu_de);
  await c.addCookies([
    { name: 'pe_at', value: tok.access, domain: 'localhost', path: '/', httpOnly: true, sameSite: 'Lax' },
    { name: 'pe_rt', value: tok.refresh, domain: 'localhost', path: '/', httpOnly: true, sameSite: 'Lax' }]);
  const p = await c.newPage();
  await p.route('**/api/**', (r, req) => {
    const m = req.method();
    if (m === 'GET' || m === 'HEAD') return r.fallback();
    ghiLen++;
    return r.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });

  for (const [url, ten] of TRANG) {
    const loi = [];
    p.removeAllListeners('pageerror');
    p.on('pageerror', (e) => loi.push(String(e.message).slice(0, 80)));
    try {
      await p.goto(GOC + url, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await p.waitForTimeout(2800);
      // Bị đẩy về màn đăng nhập thì DỪNG, đừng báo một con số của cái vỏ.
      if (/(dang-nhap|login)/.test(new URL(p.url()).pathname)) {
        console.log('');
        console.log('BI DAY VE DANG NHAP tai ' + url + ' - cap the moi (mint_ad.py) roi do lai.');
        await b.close();
        process.exit(2);
      }
      if (tu_kiem) {
        /* TỰ KIỂM: nhét một quy tắc hỏng rồi đòi bộ đo phải bắt được.
           Màu nhét phải GẦN NỀN của chính chủ đề đang đo. Nhét #F2F2F4 vào chủ
           đề tối thì đó là chữ gần trắng trên nền đen — tương phản CAO, và phép
           tự kiểm "thất bại" mà chẳng chứng minh được gì về bộ đo. */
        await p.addStyleTag({ content: 'body, body * { color: '
          + (chu_de === 'dark' ? '#14141C' : '#F2F2F4') + ' !important; }' });
        await p.waitForTimeout(150);
      }
      const that = await p.evaluate(() => document.body.classList.contains('dark') ? 'dark' : 'light');
      if (that !== chu_de) {
        console.log('');
        console.log('CHU DE KHONG DUNG: xin ' + chu_de + ' nhung trang dang ' + that
          + ' — do se ra con so cua bang mau kia.');
        await b.close();
        process.exit(3);
      }
      const d = await p.evaluate(DO_TRONG_TRANG, do_tt);
      d.tuong_tac = [];
      if (do_tt && d.dau.length) {
        /* Bật `:hover`/`:focus` bằng CDP `CSS.forcePseudoState` — tức bảo chính
           trình duyệt coi phần tử đang được rê chuột, rồi để NÓ giải tầng xếp
           lớp. Ép tay khai báo của một luật thì bỏ qua luật đè lên nó: bản vá
           `body.light .nav-next:hover` đã có vẫn bị báo là lỗi. */
        const cdp = await c.newCDPSession(p);
        await cdp.send('DOM.enable'); await cdp.send('CSS.enable');
        const { root } = await cdp.send('DOM.getDocument', { depth: -1 });
        for (const m of d.dau) {
          const q = await cdp.send('DOM.querySelector',
            { nodeId: root.nodeId, selector: `[data-pe-tt="${m.i}"]` });
          if (!q.nodeId) continue;
          await cdp.send('CSS.forcePseudoState',
            { nodeId: q.nodeId, forcedPseudoClasses: [m.trang_thai] });
          const v = await p.evaluate((i) => {
            const el = document.querySelector(`[data-pe-tt="${i}"]`);
            if (!el) return [];
            const { do_el, hien, co_chu, duong } = globalThis.__pe;
            const ra = [];
            for (const dich of [el, ...el.querySelectorAll('*')]
                .filter(hien).filter(co_chu).slice(0, 3)) {
              const x = do_el(dich);
              if (x && x.tp < x.nguong) {
                ra.push({ duong: duong(dich), ...x, chu: dich.textContent.trim().slice(0, 34) });
              }
            }
            return ra;
          }, m.i);
          await cdp.send('CSS.forcePseudoState',
            { nodeId: q.nodeId, forcedPseudoClasses: [] });
          for (const x of v) d.tuong_tac.push({ ...x, sel: m.sel, trang_thai: m.trang_thai });
        }
        await cdp.detach();
      }
      d.thieu_net = [];
      if (do_tt && d.net_dau.length) {
        const cdp2 = await c.newCDPSession(p);
        await cdp2.send('DOM.enable'); await cdp2.send('CSS.enable');
        const g = await cdp2.send('DOM.getDocument', { depth: -1 });
        const truoc = await p.evaluate((n) => {
          const r = [];
          for (let i = 0; i < n; i++) r.push(globalThis.__pe.dang(i));
          return r;
        }, d.net_dau.length);
        for (const m of d.net_dau) {
          const q = await cdp2.send('DOM.querySelector',
            { nodeId: g.root.nodeId, selector: `[data-pe-net="${m.i}"]` });
          if (!q.nodeId) continue;
          await cdp2.send('CSS.forcePseudoState',
            { nodeId: q.nodeId, forcedPseudoClasses: ['focus', 'focus-visible'] });
          const sau = await p.evaluate((i) => globalThis.__pe.dang(i), m.i);
          await cdp2.send('CSS.forcePseudoState',
            { nodeId: q.nodeId, forcedPseudoClasses: [] });
          if (sau !== null && sau === truoc[m.i]) {
            d.thieu_net.push({ duong: m.duong, chu: m.chu });
          }
        }
        await cdp2.detach();
      }
      d.so_thieu_net = d.thieu_net.length;
      d.so_net_do = d.net_dau.length;
      d.so_tuong_tac = d.tuong_tac.length;
      delete d.dau; delete d.net_dau;
      ket.push({ kho: kho.ten, chu_de, ten, url, ...d, loi_js: loi.length, loi: loi.slice(0, 2) });
      console.log(`[${kho.ten}] ${ten.padEnd(22)} tương phản:${String(d.so_vi_pham).padStart(3)}`
        + `  chạm nhỏ:${String(d.so_cham_nho).padStart(3)}/${String(d.so_cham).padStart(3)}`
        + `  tràn:${d.tran_ngang}px  lỗiJS:${loi.length}`
        + (do_tt ? `  rê:${String(d.so_tuong_tac).padStart(2)}`
            + `  thiếu nét:${String(d.so_thieu_net).padStart(2)}/${String(d.so_net_do).padStart(2)}` : ''));
    } catch (e) {
      ket.push({ kho: kho.ten, ten, url, loi_tai: String(e.message).slice(0, 80) });
      console.log(`[${kho.ten}] ${ten.padEnd(22)} KHONG TAI DUOC: ${String(e.message).slice(0, 50)}`);
    }
  }
  await c.close();
}
await b.close();

if (ra_json) writeFileSync(ra_json, JSON.stringify(ket, null, 1), 'utf8');

const tong_tp = ket.reduce((a, r) => a + (r.so_vi_pham || 0), 0);
const tong_cn = ket.reduce((a, r) => a + (r.so_cham_nho || 0), 0);
const tong_tr = ket.filter((r) => (r.tran_ngang || 0) > 1).length;
const tong_js = ket.reduce((a, r) => a + (r.loi_js || 0), 0);
console.log(`\nTỔNG (${KHO.length} khổ × ${TRANG.length} trang):`);
console.log(`  vi phạm tương phản : ${tong_tp}`);
console.log(`  vùng chạm < 44px   : ${tong_cn}`);
console.log(`  trang tràn ngang   : ${tong_tr}`);
console.log(`  lỗi JS             : ${tong_js}`);
if (do_tt) {
  console.log(`  tương phản khi rê  : ${ket.reduce((a, r) => a + (r.so_tuong_tac || 0), 0)}`);
  console.log(`  KHÔNG có vòng nét  : ${ket.reduce((a, r) => a + (r.so_thieu_net || 0), 0)}`
    + ` / ${ket.reduce((a, r) => a + (r.so_net_do || 0), 0)} phần tử đã thử`);
}
console.log(`  lời gọi GHI lọt ra : ${ghiLen}`);

if (tu_kiem) {
  console.log(`\n── TỰ KIỂM ──`);
  if (tong_tp > 50) {
    console.log(`  ĐẠT: bộ đo bắt được ${tong_tp} vi phạm khi bị nhét quy tắc hỏng.`);
    process.exit(0);
  }
  console.log(`  HỎNG: chỉ bắt được ${tong_tp} — một bộ đo không đỏ được là bộ đo giả.`);
  process.exit(1);
}
process.exit(ghiLen ? 1 : 0);
