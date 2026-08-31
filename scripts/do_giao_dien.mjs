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
];

/* Hàm chạy TRONG trang. Viết bằng function thật rồi `.toString()` thay vì nhét
   vào template literal — chuỗi lồng chuỗi là chỗ dấu gạch chéo bị nuốt. */
function DO_TRONG_TRANG() {
  const SO = /[0-9.]+/g;

  const doc_mau = (s) => {
    const so = (String(s).match(SO) || []).slice(0, 4).map(Number);
    // `color(srgb 1 1 1 / .95)` — CSS Color 4, thành phần 0–1, không phải 0–255.
    if (String(s).trim().slice(0, 6).toLowerCase() === 'color(') {
      const r = so.slice(0, 3).map((v) => Math.round(v * 255));
      return so.length > 3 ? [r[0], r[1], r[2], so[3]] : r;
    }
    return so;
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
      if (!chang && bi && bi !== 'none' && bi.indexOf('gradient') !== -1) {
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

  const vi_pham = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!hien(el)) continue;
    let co_chu = false;
    for (const nd of el.childNodes) {
      if (nd.nodeType === 3 && nd.textContent.trim().length > 1) { co_chu = true; break; }
    }
    if (!co_chu) continue;

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
    if (!isFinite(xau_nhat)) continue;

    const co = parseFloat(cs.fontSize);
    const dam = (parseInt(cs.fontWeight, 10) || 400) >= 700;
    const lon = co >= 24 || (co >= 18.66 && dam);
    const nguong = lon ? 3 : 4.5;
    if (xau_nhat < nguong) {
      vi_pham.push({ duong: duong(el), tp: Math.round(xau_nhat * 100) / 100, nguong,
        co: Math.round(co), chu: el.textContent.trim().slice(0, 40) });
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

  return {
    vi_pham: vi_pham.slice(0, 60), so_vi_pham: vi_pham.length,
    cham_nho: nho.slice(0, 60), so_cham_nho: nho.length, nguong_cham: NGUONG,
    so_cham: document.querySelectorAll(CHAM).length,
    tran_ngang: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
}

const { chromium } = await import(PW);
const tok = JSON.parse(readFileSync(TOKEN, 'utf8'));
const tu_kiem = process.argv.includes('--tu-kiem');
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
        // TỰ KIỂM: nhét một quy tắc hỏng rồi đòi bộ đo phải bắt được.
        await p.addStyleTag({ content: 'body, body * { color: #F2F2F4 !important; }' });
        await p.waitForTimeout(150);
      }
      const d = await p.evaluate(DO_TRONG_TRANG);
      ket.push({ kho: kho.ten, ten, url, ...d, loi_js: loi.length, loi: loi.slice(0, 2) });
      console.log(`[${kho.ten}] ${ten.padEnd(22)} tương phản:${String(d.so_vi_pham).padStart(3)}`
        + `  chạm nhỏ:${String(d.so_cham_nho).padStart(3)}/${String(d.so_cham).padStart(3)}`
        + `  tràn:${d.tran_ngang}px  lỗiJS:${loi.length}`);
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
