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
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const DAY = dirname(fileURLToPath(import.meta.url));

/* Playwright: HỎI Node nó nằm đâu, đừng ghi cứng đường dẫn.
   Bản trước ghim `D:/pe_hsa/frontend/node_modules/.pnpm/playwright@1.61.1/...`
   — đúng ổ đĩa, đúng trình quản lý gói, ĐÚNG SỐ PHIÊN BẢN. Nâng playwright một
   lần là công cụ chết, và triệu chứng sẽ là "không tìm thấy mô-đun", không phải
   "bạn vừa nâng cấp gói". */
const _doi = createRequire(join(DAY, '..', 'frontend', 'package.json'));
let PW = null;
for (const ten of ['@playwright/test', 'playwright']) {
  try { PW = pathToFileURL(_doi.resolve(ten)).href; break; } catch { /* thử tên sau */ }
}
if (!PW) {
  console.error('Không tìm thấy Playwright. Cài ở frontend:  pnpm install');
  process.exit(1);
}

/* Thẻ JWT. Mặc định là `<gốc repo>/.the/tokens_ad.json`, sinh bằng
   `python scripts/cap_the.py` (thư mục `.the/` đã vào .gitignore).

   BẢN TRƯỚC GHI CỨNG MỘT ĐƯỜNG DẪN TRONG THƯ MỤC TẠM CỦA MỘT PHIÊN LÀM VIỆC.
   Thư mục ấy bị dọn, nên bộ đo bị đẩy về màn đăng nhập và không đo được 15/16
   trang — trong khi vẫn in ra một bảng số trông rất bình thường. Nó có nói
   "cấp thẻ mới (mint_ad.py) rồi đo lại", nhưng `mint_ad.py` cũng là script nháp
   chưa từng được commit: công cụ chỉ người đọc tới một tệp không tồn tại, để
   sửa một đường dẫn không tồn tại. */
const TOKEN = process.env.PE_TOKENS || join(DAY, '..', '.the', 'tokens_ad.json');
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
  /* Ba trang thêm 04/09/2026. Trước hôm nay bộ đo báo "0 vi phạm tương phản"
     trong khi ba màn này chưa từng được nhìn tới — một con số 0 tính trên tập
     KHÔNG ĐẦY ĐỦ là một tờ giấy chứng nhận sạch cấp cho phần chưa ai xem.

     `/` là TRANG CHỦ, không cần đăng nhập: chỗ hiển thị có tầm với rộng nhất
     trong cả sản phẩm và là chỗ duy nhất khách vãng lai lẫn đối tác đều mở.
     Nó vắng mặt ở danh sách này từ đầu.

     `/admin` và `/quan-tri/lop-hoc` dựng trong ngày 04/09 — khu soạn giáo trình
     (kèm khối nhập đề thi) và khu xếp lớp. */
  ['/', 'Trang chủ (công khai)'],
  ['/admin', 'Soạn giáo trình'],
  ['/quan-tri/lop-hoc', 'Quản trị · lớp học'],
  /* Bốn màn dựng 07/09/2026. Thêm vào đây NGAY trong cùng phiên, vì chú thích
     ba dòng phía trên đã nói rõ chuyện gì xảy ra khi quên: bộ đo báo "0 vi
     phạm" trên một tập không đầy đủ, và con số 0 ấy là giấy chứng nhận sạch
     cấp cho phần chưa ai nhìn tới.

     `/bc/<chìa>` (trang phụ huynh) KHÔNG có ở đây: nó cần một chìa THẬT, tức
     một dòng ghi vào Neon production mỗi lượt quét. Đã đo tay trong phiên
     07/09 ở ngữ cảnh không cookie; ghi ra đây để không ai tưởng nó cũng nằm
     trong lượt quét tự động. */
  ['/quan-tri/vai-tro', 'Quản trị · ai làm được gì'],
  ['/quan-tri/huong-dan', 'Quản trị · hướng dẫn'],
  /* Thêm 07/09/2026 cùng ngày trang được dựng. Lần audit chiều nay bộ đo
     chạy sạch 20 trang và KHÔNG có trang này — đúng cái bẫy đã vá hôm
     04/09 ("bộ đo không nhìn thấy bốn trang vừa dựng") lặp lại. Trang mới
     mà không vào danh sách này thì nó là trang DUY NHẤT không ai đo, và
     bảng tổng vẫn in ra một dãy số 0 rất thuyết phục. */
  ['/quan-tri/co-so-hoc-phi', 'Quản trị · cơ sở học phí'],
  ['/giang-day/bao-cao/1', 'Giảng dạy · báo cáo cả lớp'],
  ['/giang-day/bao-cao/1/9', 'Giảng dạy · tờ báo cáo một em'],
  // Thêm 16/09/2026 cùng ngày dựng (vòng 25). Lượt quét chỉ thấy bước 1 (chọn tệp):
  // bảng khớp chỉ hiện sau khi tải PDF — phần ấy soi bằng kịch bản đi trọn đường.
  ['/giang-day/ket-qua-thi/1', 'Giảng dạy · nhập kết quả thi thử'],
  // Thêm 14/09/2026 cùng ngày dựng — trang mở mỗi tối của giảng viên.
  ['/giang-day', 'Giảng dạy · việc hôm nay'],
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

  /* Tách `background-image` thành từng LỚP. Không dùng `split(',')`: dấu phẩy
     nằm khắp nơi bên trong `rgba(…)` và `radial-gradient(…)`. Đếm ngoặc.

     Thứ tự CSS: lớp ĐẦU vẽ TRÊN CÙNG, lớp CUỐI nằm dưới đáy. */
  const tach_lop = (bi) => {
    const ra = [];
    let sau = 0;
    let dau = 0;
    for (let i = 0; i < bi.length; i++) {
      const c = bi[i];
      if (c === '(') sau += 1;
      else if (c === ')') sau -= 1;
      else if (c === ',' && sau === 0) { ra.push(bi.slice(dau, i)); dau = i + 1; }
    }
    ra.push(bi.slice(dau));
    return ra.map((s) => s.trim()).filter(Boolean);
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
    let chang_duc = false;     // chặng gradient tìm được có ĐỤC không
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
        /* TÁCH THÀNH TỪNG LỚP, và nhớ rằng lớp CUỐI nằm DƯỚI CÙNG.
           `background-image` nhận nhiều lớp; lớp đầu vẽ TRÊN, lớp cuối là đáy.

           Dương tính giả thứ NĂM của bộ đo này (đo 04/09/2026): trang chủ có
           **9 lớp** trên `body`, lớp cuối là
           `linear-gradient(rgb(7,20,42) 0%, rgb(12,29,61) 45%, rgb(9,7,21))` —
           ĐỤC và navy đậm, tức nền thật của cả trang. Bản cũ gom chặng màu của
           CẢ CHÍN lớp vào một rổ rồi phủ từng cái lên nền mặc định TRẮNG, nên
           một chặng `rgba(45,212,191,0.12)` ra gần trắng và chữ trắng thành
           1,00:1. Kết quả: **54 vi phạm không có thật** trên đúng trang có tầm
           với rộng nhất — và không cái nào là lỗi của trang.

           Nên: duyệt từ ĐÁY LÊN, gặp lớp nào có chặng ĐỤC thì lớp ấy là nền
           đáy — dừng, và lấy chính các chặng đục ấy làm nền khả dĩ. */
        const lop_anh = tach_lop(bi);
        for (let i = lop_anh.length - 1; i >= 0 && !chang; i--) {
          const g = (lop_anh[i].match(/rgba?\([^)]*\)|color\([^)]*\)/g) || [])
            .map((x) => { const v = doc_mau(x); return v.length === 3 ? [v[0], v[1], v[2], 1] : v; })
            .filter((v) => v.length === 4);
          if (!g.length) continue;
          const duc = g.filter((v) => v[3] >= 0.999);
          if (duc.length) {
            chang_duc = true;
            // Lớp đục = NỀN ĐÁY. Đặt chỗ dành ở ĐÁY chồng lớp để mỗi chặng đục
            // thành MỘT ứng viên riêng — không gộp chúng lại, vì một gradient
            // navy→đen cho hai nền rất khác nhau và chữ phải đạt trên cả hai.
            chang = duc;
            lop.unshift(null);
          }
        }
        // Không lớp nào đục: giữ nguyên cách cũ — coi các chặng là lớp phủ.
        if (!chang) {
          const g = (bi.match(/rgba?\([^)]*\)|color\([^)]*\)/g) || [])
            .map((x) => { const v = doc_mau(x); return v.length === 3 ? [v[0], v[1], v[2], 1] : v; })
            .filter((v) => v.length === 4);
          if (g.length) { chang = g; lop.unshift(null); }
        }
        /* CHỈ dừng khi chặng tìm được là ĐỤC — tức đã chạm nền đáy thật.
           Bản trước dừng ngay cả khi mọi chặng đều trong suốt, nên `goc` ở
           nguyên mặc định TRẮNG: ở chủ đề TỐI, thẻ điểm bước Đánh giá có nền
           `linear-gradient(rgba(251,191,36,.16) …)` bị ghép lên nền trắng
           tưởng tượng và chữ #E2E8F0 ra 1,13:1 — trong khi nền thật là màu tối
           và tương phản thật ~11:1. Dương tính giả thứ SÁU của bộ đo này
           (đo 17/09/2026); chặng trong suốt phải là LỚP PHỦ, rồi leo tiếp tìm
           nền đục ở tổ tiên. */
        if (chang && chang_duc) break;
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
    /* `<= 1`, KHÔNG phải `< 1`.
     *
     * Lối giấu chữ cho trình đọc màn hình (`.sr-only`) dựng hộp ĐÚNG 1×1px —
     * `1 < 1` là false, nên chữ ấy lọt qua bộ lọc và bị chấm tương phản. Đo
     * 07/09/2026 trên trang chủ: nhãn `.sr-only` trong thanh tiến độ "Thử ba
     * câu" bị báo 2.2:1, trong khi nó không hiện ra pixel nào.
     *
     * Báo oan ở đây đắt: người đọc báo cáo sẽ đi "sửa" một đoạn chữ vốn CỐ Ý
     * bị giấu, và cách sửa dễ nhất là xoá nó — tức xoá đúng phần dành cho
     * người khiếm thị. Một bộ đo a11y làm hỏng a11y. */
    if (r.width <= 1 || r.height <= 1) return false;
    const cs = getComputedStyle(el);
    /* Giấu bằng CẮT: `clip-path: inset(50%)` (lối mới) và `clip: rect(0…)`
       (lối cũ) đều để hộp có kích thước thật nhưng không vẽ pixel nào. */
    const cat = cs.clipPath || '';
    if (cat.includes('inset(50%)') || /rect\(0px[, ]/.test(cs.clip || '')) return false;
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
  /* MẪU SỐ, không chỉ tử số.
     "0 vi phạm" trên một trang chỉ soi được 7 phần tử nói ít hơn nhiều so với
     "0 vi phạm" trên trang soi 260 — mà bảng cũ in cả hai giống hệt nhau. Trang
     Khảo sát hiện MỘT câu mỗi lần và có 32 câu: 136 phần tử có chữ, chỉ 7 phần
     tử NHÌN THẤY. In mẫu số ra để không ai đọc số 0 ấy thành "đã soi cả bài". */
  let so_soi = 0;
  for (const el of document.querySelectorAll('body *')) {
    if (!hien(el) || !co_chu(el)) continue;
    so_soi += 1;
    const d = do_el(el);
    if (d && d.tp < d.nguong) {
      /* Đánh dấu để bước XÁC MINH BẰNG ĐIỂM ẢNH ở Node tìm lại được phần tử.
         Cùng cách với `data-pe-net` của phép đo vòng nét. */
      el.dataset.peVp = String(vi_pham.length);
      const r = el.getBoundingClientRect();
      vi_pham.push({
        duong: duong(el), ...d, chu: el.textContent.trim().slice(0, 40),
        i: vi_pham.length, mau_chu: getComputedStyle(el).color,
        hop: { x: r.x, y: r.y, w: r.width, h: r.height },
      });
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
    do_el, hien, co_chu, duong, nen,
    dang: (i) => {
      const el = document.querySelector(`[data-pe-net="${i}"]`);
      if (!el) return null;
      const c = getComputedStyle(el);
      return [c.outlineStyle, c.outlineWidth, c.outlineColor, c.outlineOffset,
        c.boxShadow, c.borderColor, c.borderWidth, c.backgroundColor,
        c.backgroundImage, c.color, c.textDecorationLine].join('|');
    },
  };

  const CUON = /^(auto|scroll)$/;
  const ngoai_khung = [];
  {
    const rong = document.documentElement.clientWidth;
    for (const el of document.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect();
      if (r.width <= 1 || r.height <= 1 || r.right <= rong + 1) continue;
      if (!hien(el)) continue;
      let n = el.parentElement, cuon_duoc = false;
      while (n && n !== document.documentElement) {
        if (CUON.test(getComputedStyle(n).overflowX)) { cuon_duoc = true; break; }
        n = n.parentElement;
      }
      if (cuon_duoc) continue;
      /* Chỉ tính khối CÓ NỘI DUNG. Nền trang trí (`.bg-blob`, quầng sáng của
         hero) cố ý tràn ra ngoài khung — bản đầu của luật này báo chúng ở cả hai
         khổ máy, tức 4 dòng báo oan trên 46 lượt. Mất nội dung mới là lỗi. */
      if (!el.innerText || !el.innerText.trim()) {
        if (!el.querySelector('img, video, canvas, table')) continue;
      }
      // Chỉ giữ phần tử NGOÀI CÙNG của một cụm: con của nó cũng thò ra, báo cả
      // cụm thì một lỗi thành mười dòng.
      if (ngoai_khung.some((v) => v.el.contains(el))) continue;
      ngoai_khung.push({ el, duong: duong(el), thua: Math.round(r.right - rong) });
    }
    for (const v of ngoai_khung) delete v.el;
  }

  return {
    dau, net_dau,
    /* Cắt ở 300 chứ không 60: bước XÁC MINH BẰNG ĐIỂM ẢNH ở Node chỉ soi được
       những mục có trong mảng này, nên cắt sớm là loại bỏ mục chưa ai nhìn rồi
       báo một con số nhỏ hơn sự thật. `so_vi_pham_tho` giữ số THÔ để biết có bị
       cắt hay không. */
    vi_pham: vi_pham.slice(0, 300),
    so_vi_pham: vi_pham.length, so_vi_pham_tho: vi_pham.length, so_soi,
    cham_nho: nho.slice(0, 60), so_cham_nho: nho.length, nguong_cham: NGUONG,
    so_cham: document.querySelectorAll(CHAM).length,
    tran_ngang: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    /* TRÀN BỊ CẮT BÊN TRONG — chỗ mù của bộ đo này tới 17/09/2026.
       `tran_ngang` chỉ thấy tràn ở cấp TRANG. Nhưng một thẻ rộng hơn màn hình
       nằm trong khung KHÔNG cuộn ngang thì trang không tràn: phần thừa bị cắt,
       và người dùng không có cách nào xem. Đo được trên bài "Đọc bảng số liệu"
       khổ 390: thẻ lý thuyết 459px, mất cột cuối và một phần chữ — bộ đo báo
       "tràn 0px" đúng lúc nội dung bị mất.
       Bỏ qua phần tử nằm trong tổ tiên CUỘN NGANG được (overflow-x auto/scroll):
       ở đó phần thừa vẫn xem được, đó là thiết kế chứ không phải lỗi. */
    ngoai_khung: ngoai_khung.slice(0, 8), so_ngoai_khung: ngoai_khung.length,
  };
}

const _pw = await import(PW);
const chromium = _pw.chromium || (_pw.default && _pw.default.chromium);
if (!chromium) { console.error('Nạp được Playwright nhưng không thấy `chromium`.'); process.exit(1); }
const tok = JSON.parse(readFileSync(TOKEN, 'utf8'));
const tu_kiem = process.argv.includes('--tu-kiem');
const chu_de = process.argv.includes('--toi') ? 'dark' : 'light';
const do_tt = process.argv.includes('--trang-thai');
const i_json = process.argv.indexOf('--json');
const ra_json = i_json >= 0 ? process.argv[i_json + 1] : null;

const b = await chromium.launch();
const ket = [];
let ghiLen = 0;
/* Lời gọi ghi do CHÍNH bộ đo bấm ra khi đi bài học (nộp bài kiểm tra đầu bài).
   Đếm riêng: bất biến "trang không tự ghi gì khi chỉ mở ra xem" vẫn phải đúng,
   còn thao tác do bộ đo chủ động bấm thì không được tính vào đó. Cả hai loại đều
   bị CHẶN ở `p.route` và trả `{}` — không lời gọi nào tới máy chủ. */
let ghiDi = 0;
let dangDiBaiHoc = false;

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
    ...(tok.refresh
      ? [{ name: 'pe_rt', value: tok.refresh, domain: 'localhost', path: '/', httpOnly: true, sameSite: 'Lax' }]
      : [])]);
  const p = await c.newPage();
  await p.route('**/api/**', (r, req) => {
    const m = req.method();
    if (m === 'GET' || m === 'HEAD') return r.fallback();
    if (dangDiBaiHoc) ghiDi++; else ghiLen++;
    return r.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });

  for (const [url, ten] of TRANG) {
    const loi = [];
    p.removeAllListeners('pageerror');
    p.on('pageerror', (e) => loi.push(String(e.message).slice(0, 80)));
    /* VI PHẠM CSP (14/09/2026, cùng lúc Vercel bắt đầu gửi CSP). Trình duyệt
       KHÔNG ném `pageerror` khi chặn một script/ảnh/phông — nó chỉ in một dòng
       đỏ "Refused to … Content Security Policy" vào console, và trang trông
       vẫn bình thường tới lúc người dùng bấm đúng nút cần thứ bị chặn. Không
       đếm ở đây thì một CSP làm gãy tính năng vẫn ra "lỗiJS: 0". */
    const csp = [];
    p.removeAllListeners('console');
    p.on('console', (m) => {
      if (m.type() === 'error' && /Content Security Policy/i.test(m.text())) csp.push(m.text().slice(0, 160));
    });
    try {
      await p.goto(GOC + url, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await p.waitForTimeout(2800);
      // Bị đẩy về màn đăng nhập thì DỪNG, đừng báo một con số của cái vỏ.
      if (/(dang-nhap|login)/.test(new URL(p.url()).pathname)) {
        console.log('');
        console.log('BI DAY VE DANG NHAP tai ' + url + ' - the het han hoac khong hop le.');
        console.log('Cap the moi:  python scripts/cap_the.py     (khong ghi gi vao CSDL)');
        console.log('Roi do lai :  cd scripts && node do_giao_dien.mjs');
        await b.close();
        process.exit(2);
      }
      /* BÀI HỌC: đi tới BƯỚC LÝ THUYẾT trước khi đo.

         Trang bài học mở ra ở bước 1 (làm bài kiểm tra đầu bài). Mọi thứ đáng đo
         của bài — thẻ lý thuyết, 158 khối minh hoạ của 76 bài — nằm ở bước 3, và
         bước ấy đang ẩn. Tức mọi con số của trang "Bài học" tới 17/09/2026 chỉ
         nói về màn hỏi đáp, không nói gì về phần người mua sẽ mở ra xem. Chính vì
         thế bộ đo báo "0 tràn" trong khi thẻ lý thuyết có bảng bị CẮT mất cột
         cuối ở khổ 390 (vòng 32 tìm ra bằng tay, không phải bằng bộ đo này).

         Đi bằng đúng thao tác của học viên: chọn phương án đầu cho mọi câu → Tiếp
         → Tiếp. Hỏng ở bước nào thì bỏ qua, đo như cũ — không để một thay đổi
         giao diện làm CẢ lượt quét chết. */
      if (/^\/lesson\//.test(url)) {
        dangDiBaiHoc = true;
        try {
          await p.waitForSelector('.hsa-q', { timeout: 20000 });
          for (const q of await p.locator('.hsa-q').all()) {
            const o = q.locator('.hsa-opt');
            if (await o.count()) await o.first().click();
            else await q.locator('.hsa-fill').fill('1');
          }
          await p.click('#nav-next');
          await p.waitForSelector('.step-pane[data-step="2"].active', { timeout: 20000 });
          await p.click('#nav-next');
          await p.waitForSelector('.step-pane[data-step="3"].active .hsa-cards', { timeout: 20000 });
          await p.waitForTimeout(600);
        } catch (e) {
          console.log(`      (bài học: không tới được bước lý thuyết — ${String(e.message).slice(0, 60)})`);
        } finally {
          dangDiBaiHoc = false;
        }
      }

      if (tu_kiem) {
        /* TỰ KIỂM: làm hỏng màu rồi ĐÒI bộ đo phải bắt được.

           ── Vì sao đổi cách làm (17/09/2026) ───────────────────────────────

           Bản trước nhét MỘT màu cho cả trang, đoán từ nền đọc tại điểm giữa
           màn hình: nền tối thì nhét chữ tối, nền sáng thì nhét chữ sáng. Nó
           sai ở đúng những trang mà điểm giữa màn hình KHÔNG đại diện cho nền
           của phần lớn chữ — và đó là lý do "Quản trị · tổng quan" khổ điện
           thoại không đỏ nổi ở BA lượt tự kiểm (16/09 hai lượt, 17/09 một
           lượt), tức mọi con số "0 vi phạm" của trang ấy ở khổ ấy là vô nghĩa.

           Nay không đoán nữa: dựng `__pe` bằng chính bộ đo, rồi với TỪNG phần
           tử có chữ, đặt `color` đúng bằng NỀN ĐÃ GHÉP của chính nó — tương
           phản 1,0:1 tại mọi chỗ bộ đo sẽ soi. Trang nào vẫn ra 0 vi phạm sau
           lượt này là trang bộ đo thật sự không nhìn thấy. */
        await p.evaluate(DO_TRONG_TRANG, false);   // dựng `globalThis.__pe`; số liệu bỏ đi
        const daHong = await p.evaluate(() => {
          const { hien, co_chu, nen } = globalThis.__pe;
          let n = 0;
          for (const el of document.querySelectorAll('body *')) {
            if (!hien(el) || !co_chu(el)) continue;
            const bg = (nen(el) || [])[0];
            if (!bg) continue;
            el.style.setProperty('color', `rgb(${Math.round(bg[0])},${Math.round(bg[1])},${Math.round(bg[2])})`, 'important');
            n++;
          }
          return n;
        });
        await p.waitForTimeout(150);
        if (!daHong) console.log('      (tự kiểm: KHÔNG có phần tử chữ nào để làm hỏng)');
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
      /* ── XÁC MINH TỪNG VI PHẠM BẰNG ĐIỂM ẢNH THẬT ─────────────────────
       *
       * Phép dò nền bằng CSS phải đoán: nó leo cây tìm một màu đục, và khi
       * không thấy thì lấy TRẮNG làm đáy. Đoán sai là ra 1,00:1 — trắng trên
       * trắng — cho một trang thật ra chữ sáng trên nền tối.
       *
       * Đo 04/09/2026, hai lượt liên tiếp:
       *   · bản SÁNG: 108 vi phạm báo về, **106 không có thật** (nền đáy là lớp
       *     gradient thứ 9 của `body`, đục và navy đậm — bản cũ gom chặng màu
       *     của cả 9 lớp rồi phủ lên trắng);
       *   · bản TỐI: 13 vi phạm, và cả 6 cái tôi lấy mẫu đều giả — giá trị THẬT
       *     là 5,58 đến 14,93, tức đạt thoải mái.
       *
       * Một bộ đo kêu 121 lần mà đúng 1 lần thì lần sau sẽ không ai đọc nó nữa.
       *
       * Nên: vi phạm chỉ được TÍNH sau khi soi điểm ảnh. Ẩn màu chữ đi, chụp
       * đúng ô ấy, lấy màu XUẤT HIỆN NHIỀU NHẤT làm nền thật, rồi tính lại. Giá
       * phải trả có giới hạn vì vi phạm vốn hiếm — và nếu nó KHÔNG hiếm thì
       * chậm một chút là điều nhỏ nhất đang xảy ra.
       */
      if (d.vi_pham.length) {
        const sangN = (c) => {
          const [r, g, b2] = [c[0], c[1], c[2]].map((v) => {
            const x = v / 255;
            return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
          });
          return 0.2126 * r + 0.7152 * g + 0.0722 * b2;
        };
        const tpN = (a, c) => {
          const [x, y] = [sangN(a) + 0.05, sangN(c) + 0.05];
          return Math.max(x, y) / Math.min(x, y);
        };
        const con = [];
        for (const v of d.vi_pham) {
          const el = p.locator(`[data-pe-vp="${v.i}"]`).first();
          let nen = null;
          try {
            await el.scrollIntoViewIfNeeded({ timeout: 3000 });
            const hop = await el.boundingBox();
            if (!hop || hop.width < 2 || hop.height < 2) throw new Error('không hiện');
            await el.evaluate((e) => { e.dataset.peMau = e.style.color; e.style.color = 'transparent'; });
            const anh = await p.screenshot({
              clip: { x: Math.round(hop.x), y: Math.round(hop.y),
                      width: Math.max(2, Math.round(hop.width)),
                      height: Math.max(2, Math.round(hop.height)) },
            });
            await el.evaluate((e) => { e.style.color = e.dataset.peMau || ''; });
            nen = await p.evaluate(async (b64) => {
              const img = new Image();
              img.src = 'data:image/png;base64,' + b64;
              await img.decode();
              const cv = document.createElement('canvas');
              cv.width = img.width; cv.height = img.height;
              const g = cv.getContext('2d');
              g.drawImage(img, 0, 0);
              const px = g.getImageData(0, 0, img.width, img.height).data;
              const dem = new Map();
              for (let i = 0; i < px.length; i += 4) {
                const k = `${px[i]},${px[i + 1]},${px[i + 2]}`;
                dem.set(k, (dem.get(k) || 0) + 1);
              }
              return [...dem.entries()].sort((a, c2) => c2[1] - a[1])[0][0];
            }, anh.toString('base64'));
          } catch {
            /* Không soi được (phần tử biến mất, nằm ngoài trang cuộn được…):
               GIỮ LẠI vi phạm. Bỏ đi thì một lỗi soi được biến thành một trang
               sạch — im lặng, và đúng theo hướng có lợi cho người viết bộ đo. */
            con.push({ ...v, chua_soi: true });
            continue;
          }
          const chu = (String(v.mau_chu).match(/[\d.]+/g) || []).slice(0, 3).map(Number);
          const that = tpN(chu, nen.split(',').map(Number));
          if (that < v.nguong) con.push({ ...v, tp_that: Math.round(that * 100) / 100, nen_that: nen });
        }
        const bo = d.vi_pham.length - con.length;
        // Mục bị cắt ở `slice(0, 300)` KHÔNG được soi, nên KHÔNG được bỏ: cộng
        // lại phần chưa soi thay vì lặng lẽ coi chúng là sạch.
        const chua_soi = Math.max(0, d.so_vi_pham_tho - d.vi_pham.length);
        d.vi_pham = con;
        d.so_vi_pham = con.length + chua_soi;
        d.bo_qua_gia = bo;
        d.chua_soi = chua_soi;
      }

      d.so_thieu_net = d.thieu_net.length;
      d.so_net_do = d.net_dau.length;
      d.so_tuong_tac = d.tuong_tac.length;
      delete d.dau; delete d.net_dau;
      ket.push({ kho: kho.ten, chu_de, ten, url, ...d, loi_js: loi.length, loi: loi.slice(0, 2), vi_pham_csp: csp.length, csp: csp.slice(0, 2) });
      console.log(`[${kho.ten}] ${ten.padEnd(22)} tương phản:${String(d.so_vi_pham).padStart(3)}`
        + `/${String(d.so_soi).padStart(3)}`
        + `  chạm nhỏ:${String(d.so_cham_nho).padStart(3)}/${String(d.so_cham).padStart(3)}`
        + `  tràn:${d.tran_ngang}px  ngoài khung:${String(d.so_ngoai_khung).padStart(2)}`
        + `  lỗiJS:${loi.length}  CSP:${csp.length}`
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
const tong_csp = ket.reduce((a, r) => a + (r.vi_pham_csp || 0), 0);
console.log(`\nTỔNG (${KHO.length} khổ × ${TRANG.length} trang):`);
console.log(`  vi phạm tương phản : ${tong_tp}`);
console.log(`  vùng chạm < 44px   : ${tong_cn}`);
console.log(`  trang tràn ngang   : ${tong_tr}`);
console.log(`  khối bị cắt bên ngoài khung: ${ket.reduce((a, r) => a + (r.so_ngoai_khung || 0), 0)}`);
for (const r of ket.filter((x) => x.so_ngoai_khung)) {
  console.log(`      ${r.kho} · ${r.ten}: ${r.ngoai_khung.map((v) => `${v.duong} (+${v.thua}px)`).join(' · ')}`);
}
console.log(`  lỗi JS             : ${tong_js}`);
console.log(`  vi phạm CSP        : ${tong_csp}`);
for (const r of ket.filter((x) => x.vi_pham_csp)) console.log(`      ${r.kho} · ${r.ten}: ${r.csp[0]}`);
if (do_tt) {
  console.log(`  tương phản khi rê  : ${ket.reduce((a, r) => a + (r.so_tuong_tac || 0), 0)}`);
  console.log(`  KHÔNG có vòng nét  : ${ket.reduce((a, r) => a + (r.so_thieu_net || 0), 0)}`
    + ` / ${ket.reduce((a, r) => a + (r.so_net_do || 0), 0)} phần tử đã thử`);
}
console.log(`  lời gọi GHI lọt ra : ${ghiLen}`);
console.log(`  (ghi do lượt đi bài học, đã chặn: ${ghiDi})`);

if (tu_kiem) {
  console.log(`\n── TỰ KIỂM ──`);
  /* XÉT TỪNG TRANG, không chỉ một con số gộp.

     Tiêu chí cũ là `tong_tp > 50` trên toàn bộ 32 lượt đo. Nó ĐẠT dễ dàng nhờ
     vài trang nhiều chữ, và che mất việc `/questionaire` bắt được ĐÚNG 0 ở cả
     hai khổ màn hình — tức con số "0 vi phạm" của trang ấy trong lần đo thật
     không chứng minh điều gì. Một màu xanh GỘP che một số 0 của TỪNG MỤC là
     đúng cái bẫy bộ kiểm này sinh ra để tránh. */
  const cam = ket.filter((r) => !(r.so_vi_pham > 0));
  if (cam.length) {
    console.log(`  HỎNG: ${cam.length}/${ket.length} lượt đo KHÔNG đỏ nổi dù đã bị nhét`
      + ' quy tắc hỏng —\n        con số của chúng trong lần đo thật là vô nghĩa:');
    for (const r of cam) console.log(`          ${r.kho} · ${r.ten}`);
    process.exit(1);
  }
  console.log(`  ĐẠT: cả ${ket.length} lượt đo đều đỏ khi bị nhét quy tắc hỏng`
    + ` — tổng ${tong_tp} vi phạm.`);
  process.exit(0);
}
process.exit(ghiLen ? 1 : 0);
