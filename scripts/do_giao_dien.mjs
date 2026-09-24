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
 *   ② Vùng chạm — tối thiểu 44×44 CSS px (chuột: 24×24, WCAG 2.5.8)
 *   ③ Tràn ngang ở khổ điện thoại, và khối bị CẮT trong khung không cuộn được
 *   ④ Lỗi JS + vi phạm CSP
 *   ⑤ Chữ bị thanh cố định che · hai nút neo khung nhìn chồng nhau
 *   ⑥ Sàn cỡ chữ 12px (0,75rem)
 *   ⑦ Lời gọi GHI lọt ra ngoài (trang chỉ xem thì không được ghi gì)
 *
 * CỜ: `--json <tệp>` · `--toi` (chủ đề tối) · `--trang-thai` (rê chuột + vòng
 * nét) · `--tu-kiem` (đòi bộ đo phải ĐỎ được ở TỪNG trang, cho cả luật ① và ⑥)
 * · `--cong` (thoát 1 nếu còn bất kỳ điểm xấu nào — mặc định chỉ thoát 1 khi có
 * lời gọi ghi lọt ra hoặc có trang không đo được).
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
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
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
  /* BẢY VIEW SPA của Trang của tôi (22/09/2026, agent thuoc-4). Tới hôm nay bộ
     đo chỉ mở view MẶC ĐỊNH của /dashboard, trong khi Khoá học, Lộ trình, Kỹ
     năng, Diễn đàn, Cài đặt, Hồ sơ là sáu màn học viên mở hằng ngày — cùng một
     tài liệu HTML, chỉ khác khối `#page-<view>.active`. Agent hồi quy (21/09)
     áp NGUYÊN VĂN luật sàn 12px lên sáu view ấy và đếm được 196 phần tử < 12px
     ở 390, 234 ở 1366 (vd `.sk-badge` 9px) — lúc bộ đo in "chữ < 12px: 0".
     Đi bằng đường người dùng gõ thật: `/courses` → 307 → `/dashboard#courses`
     (next.config.ts) — mỗi mục là một ĐƯỜNG KHÁC NHAU nên `goto` luôn tải lại
     cả trang, không rơi vào bẫy "cùng trang chỉ đổi mảnh #". Mở xong phải
     KIỂM view đã active thật (xem `VIEW_SPA` dưới vòng lặp), không thì dừng
     trang ấy và báo "không đo được" — chứ không đo nhầm view mặc định. */
  ['/courses', 'View · Khoá học'],
  // `plan` (Kế hoạch) là view thứ bảy — nằm trong nhóm "Học" của thanh, cùng tài liệu.
  ['/plan', 'View · Kế hoạch'],
  ['/roadmap', 'View · Lộ trình'],
  ['/skills', 'View · Kỹ năng'],
  ['/forum', 'View · Diễn đàn'],
  ['/settings', 'View · Cài đặt'],
  ['/profile', 'View · Hồ sơ'],
  ['/courses/hsa_quantitative', 'Chi tiết khoá'],
  ['/lesson/hsa_quantitative?lesson=1', 'Bài học'],
  // `/mock` (Thi thử) bỏ 24/09/2026 — bỏ thi, pha A: đường ấy chỉ còn chuyển hướng
  // về /dashboard, đo nó là đo trùng trang đích dưới tên sai.
  ['/bai-tap', 'Bài tập của tôi'],
  ['/questionaire', 'Khảo sát'],
  ['/quan-tri/tong-quan', 'Quản trị · tổng quan'],
  ['/quan-tri/tai-khoan', 'Quản trị · tài khoản'],
  // Thêm 23/09/2026: form hồ sơ học viên (§51) — dài, có thanh Lưu dính đáy.
  // Tờ báo cáo từng em (nay có ô mục tiêu của giảng viên) đã có ở dưới: /bao-cao/1/9.
  ['/quan-tri/tai-khoan/35695', 'Quản trị · hồ sơ học viên'],
  ['/quan-tri/dot-hoc', 'Quản trị · đợt học'],
  ['/quan-tri/nhat-ky', 'Quản trị · nhật ký'],
  ['/doi-mat-khau', 'Đổi mật khẩu'],
  // Quên mật khẩu (§52, 23/09/2026) — hai trang không cần đăng nhập; trang đặt lại
  // mở không kèm chìa là trạng thái 'đường dẫn hỏng'.
  ['/quen-mat-khau', 'Quên mật khẩu'],
  ['/dat-lai-mat-khau', 'Đặt lại mật khẩu (đường dẫn hỏng)'],
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
  // `/` bỏ khỏi danh sách 24/09/2026: trang quảng cáo đã gỡ, `/` chỉ còn chuyển hướng
  // (tới khu của vai / màn đăng nhập) — đo nó là đo trùng trang đích dưới tên sai.
  ['/giao-trinh', 'Giáo trình'],
  ['/quan-tri/lop-hoc', 'Quản trị · lớp học'],
  /* Bốn màn dựng 07/09/2026. Thêm vào đây NGAY trong cùng phiên, vì chú thích
     ba dòng phía trên đã nói rõ chuyện gì xảy ra khi quên: bộ đo báo "0 vi
     phạm" trên một tập không đầy đủ, và con số 0 ấy là giấy chứng nhận sạch
     cấp cho phần chưa ai nhìn tới.

     `/bc/<chìa>` (trang phụ huynh) từng KHÔNG có ở đây vì cần một chìa thật.
     Từ 17/09/2026 `scripts/cap_chia_mau.py` cấp chìa cho một em LỚP MẪU và cất
     ở `.the/chia_mau.json`; có tệp ấy thì trang được thêm vào cuối danh sách
     (xem sau mảng). Không có tệp thì bỏ qua VÀ NÓI RA — không im lặng quét
     thiếu một trang rồi in "0 vi phạm". */
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
  // `/giang-day/ket-qua-thi/1` (nhập kết quả thi thử, thêm 16/09) bỏ 24/09/2026 cùng
  // màn ấy — bỏ thi, pha A; đường cũ chuyển hướng về sổ buổi học (đã đo ở trên).
  // Thêm 14/09/2026 cùng ngày dựng — trang mở mỗi tối của giảng viên.
  ['/giang-day', 'Giảng dạy · việc hôm nay'],
  // Thêm 24/09/2026 cùng ngày dựng (§53) — lịch gộp theo tuần, bảy dòng ngày.
  ['/giang-day/lich', 'Giảng dạy · lịch học'],
];
/* Trang phụ huynh — bề mặt DUY NHẤT người ngoài hệ thống nhìn thấy, mở trên điện
   thoại từ tin nhắn. Mỗi lượt quét là một lượt "mở" (tăng opened_count của chìa
   mẫu) — chấp nhận, vì chìa thuộc lớp mẫu. */
{
  const TEP_CHIA = join(DAY, '..', '.the', 'chia_mau.json');
  if (existsSync(TEP_CHIA)) {
    const { token } = JSON.parse(readFileSync(TEP_CHIA, 'utf8'));
    TRANG.push([`/bc/${token}`, 'Phụ huynh · tờ báo cáo qua chìa']);
  } else {
    console.log('⚠ Không có .the/chia_mau.json → BỎ QUA trang phụ huynh /bc/<chìa>. '
      + 'Cấp bằng: backend/.venv/Scripts/python.exe scripts/cap_chia_mau.py');
  }
}

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
    /* Điều khiển ĐANG TẮT không có yêu cầu tương phản (WCAG 1.4.3: "part of an
       inactive user interface component"); axe cũng bỏ qua. Trước 23/09/2026
       chuyện này tự đúng vì bộ đo mù với `opacity` — thấy được độ đục rồi thì
       nút `disabled:opacity-50` thành báo oan (đo: "Lưu hồ sơ" khi chưa đổi gì). */
    if (el.closest(':disabled, [aria-disabled="true"]')) return null;
    const cs = getComputedStyle(el);
    const clip = cs.webkitBackgroundClip || cs.backgroundClip;
    const fill = String(cs.webkitTextFillColor || '');
    // Chữ gradient: màu chữ THẬT là các chặng gradient, `color` chỉ là dự phòng.
    const chu_gradient = clip === 'text'
      && (fill.split(' ').join('') === 'rgba(0,0,0,0)' || fill === 'transparent');

    let truoc, sau;
    /* ĐỘ ĐỤC THẬT của chữ = alpha của chính màu chữ × `opacity` của nó và MỌI tổ
       tiên. Bản trước bỏ cả hai: đo 23/09/2026 hàng `opacity-50` (thành phần
       dùng chung `Tr dim`) ở Soạn giáo trình ra 0 vi phạm, trong khi axe đo đúng
       hàng ấy 2,14:1 — chữ `text-ink-3` bị làm mờ một nửa lên nền trắng. Pha chữ
       vào nền theo độ đục ấy rồi mới tính tương phản (cách axe làm). */
    let duc = 1;
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const o = parseFloat(getComputedStyle(n).opacity);
      if (!Number.isNaN(o)) duc *= o;
    }
    if (chu_gradient) {
      const mau = (cs.backgroundImage.match(/rgba?\([^)]*\)|color\([^)]*\)/g) || [])
        .map((x) => doc_mau(x).slice(0, 3));
      truoc = mau.length ? mau : [doc_mau(cs.color).slice(0, 3)];
      sau = el.parentElement ? nen(el.parentElement) : [[255, 255, 255]];
    } else {
      const m = doc_mau(cs.color);
      truoc = [m.slice(0, 3)];
      if (m.length > 3 && !Number.isNaN(m[3])) duc *= m[3];
      sau = nen(el);
    }
    /* Độ đục TÍCH LUỸ gần 0 = không hiện pixel nào — cùng ngưỡng 0,05 mà `hien()`
       dùng cho độ đục của CHÍNH phần tử. Thiếu dòng này, lượt đo toàn bộ đầu tiên
       sau khi thước thấy được độ đục báo 47 "vi phạm" ở Bài học: toàn chữ trong
       khung bước đang ẩn bằng `opacity: 0` ở tổ tiên (axe coi là ẩn, đo ra 0). */
    if (duc <= 0.05) return null;
    const pha = (fg, bg) => (duc < 1 ? fg.map((c, i) => c * duc + bg[i] * (1 - duc)) : fg);

    let xau_nhat = Infinity;
    let xau_tho = Infinity;     // KHÔNG pha — để biết vi phạm nào sinh ra DO độ đục
    for (const fg of truoc) for (const bg of sau) {
      xau_nhat = Math.min(xau_nhat, tp(pha(fg, bg), bg));
      xau_tho = Math.min(xau_tho, tp(fg, bg));
    }
    if (!isFinite(xau_nhat)) return null;

    const co = parseFloat(cs.fontSize);
    const dam = (parseInt(cs.fontWeight, 10) || 400) >= 700;
    const lon = co >= 24 || (co >= 18.66 && dam);
    const nguong = lon ? 3 : 4.5;
    // `duc` đi theo vi phạm xuống bước soi điểm ảnh — xem chú thích ở đó.
    // `do_mo`: màu gốc ĐẠT, pha theo độ đục mới trượt — `--tu-kiem` đếm riêng loại này.
    return { tp: Math.round(xau_nhat * 100) / 100, nguong, co: Math.round(co),
             duc: Math.round(duc * 1000) / 1000, do_mo: xau_tho >= nguong && xau_nhat < nguong };
  };

  const vi_pham = [];
  /* MẪU SỐ, không chỉ tử số.
     "0 vi phạm" trên một trang chỉ soi được 7 phần tử nói ít hơn nhiều so với
     "0 vi phạm" trên trang soi 260 — mà bảng cũ in cả hai giống hệt nhau. Trang
     Khảo sát hiện MỘT câu mỗi lần và có 32 câu: 136 phần tử có chữ, chỉ 7 phần
     tử NHÌN THẤY. In mẫu số ra để không ai đọc số 0 ấy thành "đã soi cả bài". */
  let so_soi = 0;
  /* SÀN CỠ CHỮ 12px — luật thứ sáu, thêm 21/09/2026.
     Vì sao cần: bộ đo hỏi "chữ có đủ tương phản không" nhưng chưa bao giờ hỏi
     "chữ có đọc nổi không". Quét tay hôm nay tìm ra 10px ở nhãn hợp phần thẻ
     khoá, 10,4px ở badge, 11,2px ở nhãn chân thẻ, 11,84px ở hai nút, 10px ở
     nhãn "XP" của hộp hoàn thành bài — toàn những chỗ đã qua bốn đợt audit.
     Ngưỡng 12px là sàn dự án tự đặt từ 20/09 (nhỏ hơn cỡ thân 16px một bậc);
     chữ trang trí có `aria-hidden` thì bỏ qua vì nó không để đọc. */
  const chu_nho = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!hien(el) || !co_chu(el)) continue;
    so_soi += 1;
    const co_chu_px = parseFloat(getComputedStyle(el).fontSize);
    if (co_chu_px < 12 && !el.closest('[aria-hidden="true"]')) {
      chu_nho.push({ duong: duong(el), co: Math.round(co_chu_px * 10) / 10, chu: el.textContent.trim().slice(0, 30) });
    }
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
      /* NGĂN TRƯỢT ĐANG ĐÓNG không phải là nội dung bị cắt (22/09/2026).
         Luật này báo `.rm-browse` ở CẢ HAI khổ (+390px và +680px) — đó là ngăn
         "Duyệt bài" của Lộ trình, đỗ ngoài khung bằng `transform:translateX(100%)`
         đúng như thiết kế và trượt vào khi bấm. `hien()` vẫn coi nó là hiện vì
         nó không `display:none` cũng không `visibility:hidden`.

         Phân biệt bằng HAI dấu hiệu cùng lúc, chứ không bỏ qua mọi thứ đỗ ngoài:
           · nằm TRỌN ngoài khung (`left >= rộng`). Nội dung BỊ CẮT thì còn một
             phần lọt trong khung, nên luật vẫn bắt được nó;
           · bản thân hoặc tổ tiên có `transform`, tức bị ĐẨY ra bằng biến hình.
             Nội dung bị bố cục đẩy tràn — lỗi thật — không có transform nào. */
      if (r.left >= rong - 1) {
        let m = el, do_bien_hinh = false;
        while (m && m !== document.documentElement) {
          const t = getComputedStyle(m).transform;
          if (t && t !== 'none') { do_bien_hinh = true; break; }
          m = m.parentElement;
        }
        if (do_bien_hinh) continue;
      }
      // Chỉ giữ phần tử NGOÀI CÙNG của một cụm: con của nó cũng thò ra, báo cả
      // cụm thì một lỗi thành mười dòng.
      if (ngoai_khung.some((v) => v.el.contains(el))) continue;
      ngoai_khung.push({ el, duong: duong(el), thua: Math.round(r.right - rong) });
    }
    for (const v of ngoai_khung) delete v.el;
  }

  /* ── CHỮ NẰM DƯỚI THANH CỐ ĐỊNH (20/09/2026) ──────────────────────────────
     Chỗ mù thứ hai. `13bc3d3` (06/09) dời CSS thanh trên sang `shell.css` và
     xoá `#main { padding-top: 50px }` mà không mang theo. Suốt hai tuần, dòng
     chào "Chào mừng trở lại 👋" của MỌI học viên và nhãn "HSA · ĐỊNH LƯỢNG" ở
     đầu màn khoá học nằm DƯỚI thanh trên khi trang vừa mở — bộ đo không thấy,
     vì nó hỏi tương phản, cỡ chạm, tràn ngang; không hỏi "có bị che không".

     Cách hỏi: ở vị trí cuộn 0, thanh nào cố định/dính ở mép trên và rộng gần
     hết màn là "thanh". Chữ nào có hộp giao với dải của thanh mà điểm giữa mép
     trên của nó lại trả về chính thanh (`elementFromPoint`) thì đang bị che.
     Hỏi điểm chứ không so toạ độ: thanh kính mờ trong suốt một phần, nhưng
     người dùng không đọc xuyên qua nó được. */
  const bi_che = [];
  {
    const cu = window.scrollY;
    window.scrollTo(0, 0);
    const rong = document.documentElement.clientWidth;
    const thanh = [...document.querySelectorAll('body *')].filter((e) => {
      const c = getComputedStyle(e);
      if (!/^(fixed|sticky)$/.test(c.position)) return false;
      const r = e.getBoundingClientRect();
      return r.top <= 1 && r.height > 20 && r.height < 200 && r.width >= rong * 0.8 && hien(e);
    });
    if (thanh.length) {
      const day = Math.max(...thanh.map((e) => e.getBoundingClientRect().bottom));
      for (const el of document.querySelectorAll('body *')) {
        if (thanh.some((t) => t.contains(el))) continue;
        if (![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) continue;
        const r = el.getBoundingClientRect();
        if (r.width <= 1 || r.height <= 1 || r.top >= day - 2 || r.bottom <= 0) continue;
        if (!hien(el)) continue;
        const o = document.elementFromPoint(Math.min(rong - 1, r.left + r.width / 2), Math.max(0, r.top) + 2);
        if (!o || !thanh.some((t) => t.contains(o))) continue;
        if (bi_che.some((v) => v.el.contains(el))) continue;
        bi_che.push({ el, duong: duong(el), chu: el.textContent.trim().slice(0, 30) });
      }
      for (const v of bi_che) delete v.el;
    }
    window.scrollTo(0, cu);
  }

  /* ── HAI NÚT NEO VÀO KHUNG NHÌN CHỒNG NHAU (20/09/2026) ─────────────────────
     Chỗ mù thứ ba. Nút trợ lý AI (`position: fixed`, góc dưới phải) đè lên nút
     "Tiếp theo" của thanh bước bài học 340–461px² ở CẢ HAI khổ — bấm mép trên
     mũi tên là mở trợ lý. Luật cỡ chạm không thấy: từng nút vẫn đủ 44px; nó
     không hỏi hai nút có CHỒNG nhau không.

     "Neo" định nghĩa bằng ĐO, không bằng `position`: bản đầu của luật này hỏi
     `position: fixed|sticky` ở tổ tiên, và báo 0 cho chính trang bài học — thanh
     bước ở đó `position: relative` trong một bố cục cao đúng 100vh, nội dung
     cuộn BÊN TRONG. Nên: cuộn thử (vùng cuộn gần nhất của B, hoặc cửa sổ) 120px;
     B không dịch một pixel nào thì người dùng không có cách nào kéo B ra khỏi
     A — đó mới là chồng thật. Nút nổi đè lên nội dung cuộn thì không tính. */
  const chong_nut = [];
  {
    const co_dinh = (el) => {
      for (let n = el; n && n !== document.body; n = n.parentElement) {
        if (/^(fixed|sticky)$/.test(getComputedStyle(n).position)) return true;
      }
      return false;
    };
    const vung_cuon = (el) => {
      for (let n = el.parentElement; n && n !== document.documentElement; n = n.parentElement) {
        const cs = getComputedStyle(n);
        if (/^(auto|scroll)$/.test(cs.overflowY) && n.scrollHeight > n.clientHeight + 1) return n;
      }
      return null;
    };
    const khong_dich = (el) => {
      const truoc = el.getBoundingClientRect().top;
      const vc = vung_cuon(el);
      const doc = (v) => (vc ? vc.scrollTop = v : window.scrollTo(0, v));
      const lay = () => (vc ? vc.scrollTop : window.scrollY);
      const cu = lay();
      /* Thử CẢ HAI chiều: vùng cuộn đang ở đáy thì +120 không đi đâu cả, và bản
         đầu kết luận "không dịch" cho một phương án trắc nghiệm nằm cuối bài
         (báo oan 2273px², 20/09/2026). Chỉ khi không chiều nào dịch được nó
         mới là neo thật. */
      let dich = false;
      for (const d of [120, -120]) {
        doc(cu + d);
        if (Math.abs(el.getBoundingClientRect().top - truoc) >= 1) { dich = true; }
        doc(cu);
        if (dich) break;
      }
      return !dich;
    };
    /* Hộp NHÌN THẤY: cắt theo mọi tổ tiên có `overflow` khác `visible`. Không
       cắt thì mục điều hướng đã cuộn khuất khỏi dãy (`.topbar-nav` cuộn ngang)
       vẫn mang hộp đè lên nút chủ đề/chuông — bản đầu báo 51 cặp, toàn bộ là
       nút không ai thấy (đo 20/09/2026). */
    const hop_thay = (el) => {
      let r = el.getBoundingClientRect();
      let { left, top, right, bottom } = r;
      for (let n = el.parentElement; n && n !== document.documentElement; n = n.parentElement) {
        const cs = getComputedStyle(n);
        if (cs.overflowX === 'visible' && cs.overflowY === 'visible') continue;
        const c = n.getBoundingClientRect();
        left = Math.max(left, c.left); top = Math.max(top, c.top);
        right = Math.min(right, c.right); bottom = Math.min(bottom, c.bottom);
        if (right <= left || bottom <= top) return null;
      }
      return { left, top, right, bottom, width: right - left, height: bottom - top };
    };
    /* Chỉ NÚT thật. `CHAM` gồm cả `[tabindex]` — đúng cho cỡ chạm, sai cho luật
       này: vùng lý thuyết bài học mang `tabindex="0"` (để bàn phím cuộn được,
       WCAG 2.1.1) và bị coi là "nút" nằm dưới nút trợ lý — 2304px² báo oan
       (20/09/2026). Một vùng cuộn có tiêu điểm không phải thứ người ta bấm. */
    const CHAM_NUT = 'a[href], button, input, select, textarea, [role="button"]';
    const tat_ca = [...document.querySelectorAll(CHAM_NUT)].filter(hien)
      .map((el) => ({ el, r: hop_thay(el) })).filter((x) => x.r && x.r.width > 0 && x.r.height > 0);
    const noi = tat_ca.filter((x) => co_dinh(x.el));
    for (const a of noi) {
      for (const b of tat_ca) {
        if (a === b || a.el.contains(b.el) || b.el.contains(a.el)) continue;
        if (co_dinh(b.el) && noi.indexOf(b) < noi.indexOf(a)) continue;   // cặp đã xét
        const g = Math.max(0, Math.min(a.r.right, b.r.right) - Math.max(a.r.left, b.r.left))
          * Math.max(0, Math.min(a.r.bottom, b.r.bottom) - Math.max(a.r.top, b.r.top));
        if (g < 16) continue;   // chạm mép 1–2px không phải chồng
        if (!co_dinh(b.el) && !khong_dich(b.el)) continue;
        chong_nut.push({ a: duong(a.el), b: duong(b.el), giao: Math.round(g) });
      }
    }
  }

  return {
    bi_che: bi_che.slice(0, 6), so_bi_che: bi_che.length,
    chong_nut: chong_nut.slice(0, 6), so_chong_nut: chong_nut.length,
    dau, net_dau,
    /* Cắt ở 300 chứ không 60: bước XÁC MINH BẰNG ĐIỂM ẢNH ở Node chỉ soi được
       những mục có trong mảng này, nên cắt sớm là loại bỏ mục chưa ai nhìn rồi
       báo một con số nhỏ hơn sự thật. `so_vi_pham_tho` giữ số THÔ để biết có bị
       cắt hay không. */
    vi_pham: vi_pham.slice(0, 300),
    so_vi_pham: vi_pham.length, so_vi_pham_tho: vi_pham.length, so_soi,
    cham_nho: nho.slice(0, 60), so_cham_nho: nho.length, nguong_cham: NGUONG,
    chu_nho: chu_nho.slice(0, 20), so_chu_nho: chu_nho.length,
    /* GOM theo đường + cỡ (22/09/2026): 20 mẫu đầu không đủ để sửa khi một view
       có 60 chữ nhỏ — người sửa cần biết BỘ CHỌN nào, bao nhiêu chỗ. */
    chu_nho_nhom: [...chu_nho.reduce((m, v) => {
      const k = `${v.co}px ${v.duong}`;
      const g = m.get(k) || { k, n: 0, mau: v.chu };
      g.n += 1; m.set(k, g); return m;
    }, new Map()).values()].sort((a, c) => c.n - a.n).slice(0, 30),
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

/* ── THẺ HỌC VIÊN cho các trang học viên (20/09/2026) ─────────────────────────
   Từ 20/09 nhân sự KHÔNG thấy phần luyện thi (`src/lib/nhomVai.ts`): hero,
   ô số, nhiệm vụ, nhật ký, bảng xếp hạng, nút trợ lý… đều `display: none` khi
   `<html data-vai-nhom="nhan-su">`. Bộ đo này đi bằng thẻ QUẢN TRỊ, nên nếu cứ
   thế thì toàn bộ màn học viên biến khỏi lượt đo mà con số vẫn "0 vi phạm" —
   đúng loại xanh giả tệp này sinh ra để tránh. Và nhóm vai nhớ trong
   `sessionStorage` theo TAB, mà bộ đo dùng một tab cho cả lượt: trang đầu đặt
   "nhân sự" là các trang sau đều thế (đo 20/09: nút trợ lý đè lên "Tiếp theo"
   trên bài học không bị bắt khi chạy cả lượt, nhưng bị bắt khi chạy riêng).

   Nên: trang học viên đo bằng thẻ học viên (`PE_TOKENS_HV`, mặc định
   `.the/tokens_hv.json`, cấp bằng `python scripts/cap_the.py --e2e --ra
   .the/tokens_hv.json`), và xoá nhóm vai đã nhớ trước MỖI trang. Không có thẻ
   ấy thì nói to một lần rồi đo bằng thẻ quản trị — con số của các trang học
   viên khi đó KHÔNG gồm phần chỉ-học-viên. */
const TOKEN_HV = process.env.PE_TOKENS_HV || join(DAY, '..', '.the', 'tokens_hv.json');
let tokHv = null;
try { tokHv = JSON.parse(readFileSync(TOKEN_HV, 'utf8')); } catch (e) { /* chưa cấp */ }
const TRANG_HOC_VIEN = new Set(['Dashboard', 'Chi tiết khoá', 'Bài học', 'Thi thử', 'Bài tập của tôi', 'Khảo sát', 'Đổi mật khẩu',
  'View · Khoá học', 'View · Kế hoạch', 'View · Lộ trình', 'View · Kỹ năng', 'View · Diễn đàn', 'View · Cài đặt', 'View · Hồ sơ']);
/* Đường gõ → id view SPA (khối `#page-<id>`). Dùng để KIỂM view đã mở thật. */
const VIEW_SPA = { '/courses': 'courses', '/plan': 'plan', '/roadmap': 'roadmap', '/skills': 'skills',
  '/forum': 'forum', '/settings': 'settings', '/profile': 'profile' };
if (!tokHv) {
  console.log('CHÚ Ý: không có thẻ học viên (' + TOKEN_HV + ') — các trang học viên đo bằng thẻ quản trị,'
    + '\n       phần CHỈ HỌC VIÊN THẤY (hero, ô số, nhiệm vụ, nhật ký, xếp hạng, trợ lý) KHÔNG được đo.'
    + '\n       Cấp: python scripts/cap_the.py --e2e --ra .the/tokens_hv.json');
}
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
    // `PE_CHI_TRANG=Bài học` (hoặc một phần tên) — chạy một trang khi đang sửa một luật.
    if (process.env.PE_CHI_TRANG && !ten.includes(process.env.PE_CHI_TRANG)) continue;
    // Thẻ theo trang (xem TOKEN_HV ở trên); cookie cùng tên ghi đè cookie cũ.
    const the = (TRANG_HOC_VIEN.has(ten) || VIEW_SPA[url]) && tokHv ? tokHv : tok;
    await c.addCookies([{ name: 'pe_at', value: the.access, domain: 'localhost', path: '/', httpOnly: true, sameSite: 'Lax' }]);
    // Nhóm vai nhớ theo TAB — xoá để trang này tự hỏi vai của thẻ vừa đặt.
    await p.evaluate(() => { try { sessionStorage.removeItem('pe_nhom_vai'); } catch (e) { /* trang trống */ } }).catch(() => {});
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
      /* VIEW SPA: KIỂM đã mở đúng view rồi mới đo (22/09/2026, agent thuoc-4).
         `DashboardClient` đọc `location.hash` sau khi hydrate rồi gọi
         `navigate` trong rAF; dữ liệu của view (kỹ năng, bài diễn đàn) về sau
         đó. Chưa active thì gọi `window.navigate` một lần; vẫn chưa thì NÉM —
         rơi xuống nhánh "không đo được" chứ không đo view mặc định rồi gắn nhãn
         view kia. Cuộn hết view một lượt để phần dựng khi cuộn tới hiện ra. */
      const view = VIEW_SPA[url];
      if (view) {
        const daMo = () => p.evaluate((v) => !!document.querySelector(`#page-${v}.active`), view);
        if (!(await daMo())) {
          await p.evaluate((v) => { if (typeof window.navigate === 'function') window.navigate(v); }, view);
          await p.waitForTimeout(1500);
        }
        if (!(await daMo())) throw new Error(`view "${view}" KHÔNG mở (không có #page-${view}.active)`);
        await p.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
        await p.evaluate(async () => {
          for (let y = 0; y < document.documentElement.scrollHeight; y += 600) {
            window.scrollTo(0, y);
            await new Promise((r) => setTimeout(r, 50));
          }
          window.scrollTo(0, 0);
        });
        await p.waitForTimeout(400);
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
        /* HAI kiểu làm hỏng, xen kẽ từng phần tử (23/09/2026). Kiểu cũ — chữ =
           nền — không bao giờ đi qua nhánh ĐỘ ĐỤC, nên hai chỗ mù (phía trang
           và bước soi điểm ảnh đều bỏ `opacity`) sống sót qua mọi lượt tự kiểm
           cho tới khi axe bắt được một hàng `opacity-50` mà bộ này báo 0. Nay
           nửa số phần tử giữ NGUYÊN màu nhưng bị nhét `opacity: .12`; vi phạm
           của chúng được đếm riêng (`do_mo`) và phải > 0 ở mọi lượt. */
        const daHong = await p.evaluate(() => {
          const { hien, co_chu, nen } = globalThis.__pe;
          let n = 0;
          for (const el of document.querySelectorAll('body *')) {
            if (!hien(el) || !co_chu(el)) continue;
            const bg = (nen(el) || [])[0];
            if (!bg) continue;
            /* Độ đục chỉ nhét vào phần tử NỀN TRONG SUỐT — đúng hình dạng lỗi thật
               (chữ trong một hàng bảng mờ). Phần tử có nền riêng thì nền cũng mờ
               theo trong ảnh chụp, và bước soi dùng màu gốc VẪN thấy tương phản
               thấp: ca ấy không phân biệt được bước soi đúng hay sai (lùi thử
               23/09/2026 — khổ điện thoại vẫn xanh vì đúng lý do này). */
            const csEl = getComputedStyle(el);
            const nenTrong = /rgba\(0, 0, 0, 0\)|transparent/.test(csEl.backgroundColor)
              && csEl.backgroundImage === 'none';
            if (n % 2 && nenTrong) el.style.setProperty('opacity', '0.12', 'important');
            else el.style.setProperty('color', `rgb(${Math.round(bg[0])},${Math.round(bg[1])},${Math.round(bg[2])})`, 'important');
            n++;
          }
          return n;
        });
        /* LUẬT SÀN CỠ CHỮ cũng phải đỏ được (22/09/2026, agent thuoc-4).
           Tự kiểm tới hôm nay chỉ làm hỏng MÀU, nên nó chứng minh đúng một luật
           trong sáu. Luật thứ sáu (chữ < 12px) báo 0 trên mọi trang suốt hai
           ngày trong khi sáu view SPA có 196–234 phần tử dưới sàn — số 0 ấy là
           số 0 của một luật chưa ai chứng minh là đỏ được. Nhét 9px vào đúng
           những phần tử luật ấy soi rồi đòi nó đếm ra. */
        const daNho = await p.evaluate(() => {
          const { hien, co_chu } = globalThis.__pe;
          let n = 0;
          for (const el of document.querySelectorAll('body *')) {
            if (!hien(el) || !co_chu(el) || el.closest('[aria-hidden="true"]')) continue;
            el.style.setProperty('font-size', '9px', 'important');
            n++;
          }
          return n;
        });
        /* LUẬT KHỐI BỊ CẮT NGOÀI KHUNG cũng phải đỏ được (22/09/2026).
           Hôm nay tôi vừa thêm một cửa vào luật ấy: bỏ qua thứ nằm TRỌN ngoài
           khung và bị đẩy ra bằng `transform` (ngăn trượt đang đóng). Một cửa
           như thế rất dễ bịt mắt luôn cả luật, nên phải có phép chứng minh nó
           VẪN bắt được cái thật. Nhét một khối chữ thò nửa ra khỏi khung bằng
           BỐ CỤC (position/left, không transform) rồi đòi luật đếm ra nó. */
        await p.evaluate(() => {
          const d = document.createElement('div');
          d.id = '__pe_cat';
          d.textContent = 'KHỐI TỰ KIỂM BỊ CẮT NGOÀI KHUNG';
          d.style.cssText = 'position:absolute;top:0;width:240px;height:40px;'
            + `left:${document.documentElement.clientWidth - 60}px;z-index:2147483647;`;
          document.body.appendChild(d);
        });
        await p.waitForTimeout(150);
        if (!daHong) console.log('      (tự kiểm: KHÔNG có phần tử chữ nào để làm hỏng)');
        if (!daNho) console.log('      (tự kiểm: KHÔNG có phần tử chữ nào để thu nhỏ)');
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
          const nenThat = nen.split(',').map(Number);
          /* Pha chữ vào nền THẬT theo độ đục đã đo phía trang. Bước này từng tính
             bằng màu CSS gốc và gạt đúng các vi phạm do `opacity` thành "báo oan"
             (23/09/2026: chữ gần đen trong hàng `opacity-50` → 16:1 thay vì 3,45:1)
             — tức chỗ mù thứ hai, sau khi phía trang đã sửa. */
          const duc = typeof v.duc === 'number' ? v.duc : 1;
          const chuThat = chu.map((c, k) => c * duc + nenThat[k] * (1 - duc));
          const that = tpN(chuThat, nenThat);
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
      // Vi phạm SAU khi soi điểm ảnh mà chỉ độ đục gây ra — `--tu-kiem` đòi > 0.
      // Chỉ đếm vi phạm ĐÃ soi: mục không soi được vẫn được giữ lại (`chua_soi`),
      // và đếm chúng thì lượt điện thoại xanh ngay cả khi bước soi bỏ độ đục
      // (lùi thử 23/09/2026: máy tính đỏ, điện thoại vẫn xanh).
      d.so_vi_pham_mo = (d.vi_pham || []).filter((v) => v.do_mo && !v.chua_soi).length;

      d.so_thieu_net = d.thieu_net.length;
      d.so_net_do = d.net_dau.length;
      d.so_tuong_tac = d.tuong_tac.length;
      delete d.dau; delete d.net_dau;
      ket.push({ kho: kho.ten, chu_de, ten, url, ...d, loi_js: loi.length, loi: loi.slice(0, 2), vi_pham_csp: csp.length, csp: csp.slice(0, 2) });
      console.log(`[${kho.ten}] ${ten.padEnd(22)} tương phản:${String(d.so_vi_pham).padStart(3)}`
        + `/${String(d.so_soi).padStart(3)}`
        + `  chạm nhỏ:${String(d.so_cham_nho).padStart(3)}/${String(d.so_cham).padStart(3)}`
        + `  chữ<12px:${String(d.so_chu_nho).padStart(3)}`
        + `  tràn:${d.tran_ngang}px  ngoài khung:${String(d.so_ngoai_khung).padStart(2)}`
        + `  bị che:${String(d.so_bi_che).padStart(2)}`
        + `  chồng:${String(d.so_chong_nut).padStart(2)}`
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
/* TRANG KHÔNG ĐO ĐƯỢC (22/09/2026, agent thuoc-4). Trước hôm nay một trang ném
   lỗi lúc tải chỉ in một dòng "KHONG TAI DUOC" giữa bảng rồi biến mất khỏi
   phần TỔNG — mọi tổng cộng coi nó như 0 và mã thoát vẫn 0. Một trang không
   đo được không phải một trang sạch: in số ấy lên đầu và thoát khác 0. */
const khong_do = ket.filter((r) => r.loi_tai);
console.log(`  trang KHÔNG đo được: ${khong_do.length}`);
for (const r of khong_do) console.log(`      ${r.kho} · ${r.ten}: ${r.loi_tai}`);
console.log(`  vi phạm tương phản : ${tong_tp}`);
console.log(`  vùng chạm < 44px   : ${tong_cn}`);
console.log(`  chữ nhỏ hơn 12px   : ${ket.reduce((a, r) => a + (r.so_chu_nho || 0), 0)}`);
for (const r of ket.filter((x) => x.so_chu_nho)) {
  console.log(`      ${r.kho} · ${r.ten} (${r.so_chu_nho}): `
    + (r.chu_nho_nhom || []).map((g) => `${g.n}× ${g.k} "${g.mau}"`).join(' · '));
}
console.log(`  trang tràn ngang   : ${tong_tr}`);
console.log(`  khối bị cắt bên ngoài khung: ${ket.reduce((a, r) => a + (r.so_ngoai_khung || 0), 0)}`);
for (const r of ket.filter((x) => x.so_ngoai_khung)) {
  console.log(`      ${r.kho} · ${r.ten}: ${r.ngoai_khung.map((v) => `${v.duong} (+${v.thua}px)`).join(' · ')}`);
}
console.log(`  chữ dưới thanh cố định: ${ket.reduce((a, r) => a + (r.so_bi_che || 0), 0)}`);
for (const r of ket.filter((x) => x.so_bi_che)) {
  console.log(`      ${r.kho} · ${r.ten}: ${r.bi_che.map((v) => `"${v.chu}" (${v.duong})`).join(' · ')}`);
}
console.log(`  nút neo khung nhìn chồng nhau: ${ket.reduce((a, r) => a + (r.so_chong_nut || 0), 0)}`);
for (const r of ket.filter((x) => x.so_chong_nut)) {
  console.log(`      ${r.kho} · ${r.ten}: ${r.chong_nut.map((v) => `${v.a} × ${v.b} (${v.giao}px²)`).join(' · ')}`);
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
  /* XÉT TỪNG LUẬT, không chỉ luật tương phản (22/09/2026): "đỏ được" phải đúng
     cho CẢ luật sàn cỡ chữ, vì nó cũng là luật đang in ra số 0. */
  const cam = ket.filter((r) => !(r.so_vi_pham > 0));
  const cam_chu = ket.filter((r) => !(r.so_chu_nho > 0));
  const cam_mo = ket.filter((r) => !(r.so_vi_pham_mo > 0));
  if (cam.length || cam_chu.length || cam_mo.length) {
    if (cam.length) {
      console.log(`  HỎNG (tương phản): ${cam.length}/${ket.length} lượt đo KHÔNG đỏ nổi dù đã bị nhét`
        + ' quy tắc hỏng —\n        con số của chúng trong lần đo thật là vô nghĩa:');
      for (const r of cam) console.log(`          ${r.kho} · ${r.ten}`);
    }
    if (cam_mo.length) {
      console.log(`  HỎNG (độ đục): ${cam_mo.length}/${ket.length} lượt đo KHÔNG bắt được chữ bị làm mờ`
        + ' bằng `opacity` (màu gốc đạt):');
      for (const r of cam_mo) console.log(`          ${r.kho} · ${r.ten}`);
    }
    if (cam_chu.length) {
      console.log(`  HỎNG (sàn cỡ chữ): ${cam_chu.length}/${ket.length} lượt đo KHÔNG đếm được chữ 9px:`);
      for (const r of cam_chu) console.log(`          ${r.kho} · ${r.ten}`);
    }
    process.exit(1);
  }
  console.log(`  ĐẠT: cả ${ket.length} lượt đo đều đỏ khi bị nhét quy tắc hỏng`
    + ` — tổng ${tong_tp} vi phạm tương phản (${ket.reduce((a, r) => a + (r.so_vi_pham_mo || 0), 0)} do độ đục),`
    + ` ${ket.reduce((a, r) => a + (r.so_chu_nho || 0), 0)} chữ dưới sàn.`);
  process.exit(0);
}
/* CỔNG (22/09/2026, agent thuoc-4). Mã thoát tới hôm nay chỉ nói về lời gọi GHI
   lọt ra: một lượt quét đầy vi phạm tương phản vẫn "thành công". `--cong` cho
   người gọi đòi SẠCH mọi luật mà không đổi hành vi mặc định của các kịch bản
   đang chạy. */
if (process.argv.includes('--cong')) {
  const xau = tong_tp + tong_cn + tong_tr + tong_js + tong_csp + khong_do.length + ghiLen
    + ket.reduce((a, r) => a + (r.so_chu_nho || 0) + (r.so_ngoai_khung || 0) + (r.so_bi_che || 0) + (r.so_chong_nut || 0), 0);
  console.log(`\nCỔNG: ${xau === 0 ? 'SẠCH' : xau + ' điểm xấu'} (mọi luật gộp lại).`);
  process.exit(xau ? 1 : 0);
}
process.exit(ghiLen || khong_do.length ? 1 : 0);
