/**
 * ĐO NHIỀU MÀN TRONG MỘT LƯỢT — để soát bảng nghiệm thu bằng SỐ, không bằng trí nhớ.
 *
 * ── VÌ SAO (26/09/2026) ─────────────────────────────────────────────────────
 *
 * Anh Sơn hỏi cách đẩy nhanh tiến độ mà đỡ tốn token. Đo bảng nghiệm thu hôm ấy
 * ra một con số đáng chú ý: trong bốn dòng lead đi kiểm, **cả bốn đều đã làm
 * xong mà bị ghi thấp hơn thực tế** (17, 21, 14, 18) — việc làm rồi mà không ai
 * quay lại gạch khỏi kế hoạch. Soát rẻ hơn viết rất nhiều, nhưng soát từng màn
 * một thì mỗi màn là một lượt mở trình duyệt, một lượt đọc kết quả dài.
 *
 * Tệp này mở TẤT CẢ màn cần soát trong MỘT phiên (một trình duyệt, mỗi vai một
 * trang dùng lại — xem `lib/phien_do.mjs`) và nhả ra JSON gọn: mỗi màn chỉ còn
 * tiêu đề, danh sách nút/liên kết, và trả lời Có/Không cho những câu mình hỏi.
 * Không dump cả trang — phần đắt nhất của một lượt soát là chữ phải đọc lại.
 *
 * ── CÁCH DÙNG ───────────────────────────────────────────────────────────────
 *
 *     node scripts/do_man_hang_loat.mjs --man scripts/man/nghiem_thu.json
 *     node scripts/do_man_hang_loat.mjs --man <json> --json ra.json --anh <thư-mục>
 *
 * Tệp `--man` là JSON, một mảng:
 *
 *     [{ "dong": 17, "ten": "GV · giao bài", "duong": "/giang-day/bai-tap/7322",
 *        "vai": "gv", "hoi": { "suaBai": "Sửa bài", "doiNguoiNhan": "Đổi người nhận" } }]
 *
 * `hoi` là các câu hỏi Có/Không: khoá là tên ngắn, giá trị là chuỗi (hoặc mẫu
 * regex) phải tìm thấy trong chữ của màn hoặc trong nhãn một nút.
 *
 * Thêm màn cần soát = thêm một mục vào JSON. Không sửa tệp này.
 */
import { readFileSync, writeFileSync } from 'node:fs';

import { chay } from './lib/phien_do.mjs';

const co = (t) => process.argv.includes(t);
const sau = (t) => { const i = process.argv.indexOf(t); return i > 0 ? process.argv[i + 1] : null; };

const duongMan = sau('--man');
if (!duongMan) {
  console.error('Thiếu --man <tệp JSON mô tả các màn>. Xem đầu tệp này.');
  process.exit(2);
}
const MAN = JSON.parse(readFileSync(duongMan, 'utf8'));
const GOC = process.env.PE_WEB || 'http://localhost:3100';

/** Đọc màn: tiêu đề, nút đang hiện, và trả lời từng câu hỏi Có/Không. */
const DOC = (hoi) => {
  const t = document.body.innerText || '';
  const hien = (e) => {
    const s = getComputedStyle(e);
    return s.display !== 'none' && s.visibility !== 'hidden' && e.getBoundingClientRect().width > 0;
  };
  // Nhãn của một nút KHÔNG chỉ nằm trong `textContent`: nút mắt ở ô mật khẩu
  // chỉ có `aria-label="Hiện mật khẩu"` và một hình vẽ bên trong. Bản cũ đọc
  // riêng `textContent` nên trả "không có" cho một tính năng đang dựng đúng —
  // đúng loại dương tính giả mà tệp này viết ra để tránh (đo 26/09, dòng 1).
  const nut = [...new Set([...document.querySelectorAll('button, a[href], [role="button"]')]
    .filter(hien)
    .flatMap((e) => [e.textContent || '', e.getAttribute('aria-label') || '', e.getAttribute('title') || ''])
    .map((t) => t.trim()).filter(Boolean))];
  const tra = {};
  for (const [k, mau] of Object.entries(hoi || {})) {
    const re = new RegExp(mau, 'i');
    tra[k] = re.test(t) || nut.some((n) => re.test(n));
  }
  return {
    tieuDe: (document.querySelector('h1, h2')?.textContent || '').trim().slice(0, 80),
    url: location.pathname,
    soTu: t.split(/\s+/).filter(Boolean).length,
    nut: nut.slice(0, 20),
    tra,
  };
};

/**
 * BẤM một nút theo NHÃN, sau khi nó thật sự bấm được.
 *
 * Trang dựng ở máy chủ hiện nút ra TRƯỚC khi React gắn vào; bấm trong khoảng ấy
 * thì không có gì xảy ra và màn trông như "không phản ứng". Đã mất một lượt đo
 * vì chuyện này (26/09). Nên: chờ phần tử có nhãn ấy hiện ra VÀ hết `disabled`,
 * trần 8 giây, rồi mới bấm; chờ xong thì chờ tiếp một nhịp cho khối mới nạp.
 *
 * Trả về `null` khi bấm được, hoặc một câu vì sao không bấm được — câu ấy đi
 * thẳng vào cột "KHÔNG ĐO ĐƯỢC", không thành dấu ✗.
 */
async function bam(page, nhan, choSau = 2000) {
  const o = page.locator(
    `button:has-text("${nhan}"), a:has-text("${nhan}"), summary:has-text("${nhan}"), [role="button"]:has-text("${nhan}")`,
  ).first();
  try {
    await o.waitFor({ state: 'visible', timeout: 8000 });
  } catch {
    return `không thấy nút "${nhan}"`;
  }
  const het = Date.now() + 8000;
  while (Date.now() < het && (await o.isDisabled().catch(() => false))) {
    await page.waitForTimeout(150);
  }
  try {
    await o.click({ timeout: 5000 });
  } catch (e) {
    return `bấm "${nhan}" không được: ${String(e).slice(0, 90)}`;
  }
  await page.waitForTimeout(choSau);
  return null;
}

const anh = sau('--anh');
const ra = await chay({ goc: GOC, anh }, async (phien) => {
  const ds = [];
  let thuTu = 0;
  for (const m of MAN) {
    thuTu += 1;
    const page = await phien.man(m.duong, m.vai || 'ad');
    // Màn nào tải dữ liệu sau khi dựng thì cần thêm một nhịp; `phien.man` đã chờ
    // tới lúc chiều cao thôi đổi, nhịp này là cho khối nạp bằng `useEffect`.
    await page.waitForTimeout(m.cho ?? 2500);
    /* `bam` = dãy nhãn phải bấm trước khi đo. Nhiều thứ bảng nghiệm thu đòi nằm
       SAU một cú bấm (sổ điểm danh của một buổi, "Lịch sử thay đổi của lớp",
       khối học viên của lớp). Đo màn ngoài rồi kết luận "không có" là cách chắc
       nhất để ghi CHƯA cho một tính năng đang chạy. */
    /* `chon` = [[id-ô-select, giá-trị]…]: vài màn chỉ nạp dữ liệu SAU khi chọn
       một mục trong ô thả xuống (Khung chương trình mở ra ở môn đầu bảng chữ
       cái, không phải môn mình cần). Không chọn được thì màn đứng ở trạng thái
       rỗng, và bộ đo chấm "không có" cho cả một màn đang chạy. */
    let loiChon = null;
    for (const [oId, gt] of m.chon || []) {
      try {
        await page.selectOption(`#${oId}`, gt, { timeout: 8000 });
        await page.waitForTimeout(m.choSauChon ?? 2500);
      } catch (e) {
        loiChon = `không chọn được "${gt}" ở ô #${oId}: ${String(e).slice(0, 80)}`;
        break;
      }
    }
    let loiBam = loiChon;
    for (const nhan of loiChon ? [] : (m.bam || [])) {
      loiBam = await bam(page, nhan, m.choSauBam ?? 2000);
      if (loiBam) break;
    }
    const d = await page.evaluate(DOC, m.hoi || {});
    d.loiBam = loiBam;
    d.dong = m.dong;
    d.ten = m.ten;
    d.ma = page.maHTTP;
    d.xin = m.duong;
    /* Tên ảnh mang SỐ THỨ TỰ, không chỉ dòng + vai: một dòng nghiệm thu thường
       cần hai màn (dòng 15 = Chương trình lớp + Sổ đầu bài), và tên trùng thì
       ảnh sau đè ảnh trước — soát lại còn đúng một nửa bằng chứng. */
    if (anh) {
      await phien.chup(page, `man_${String(thuTu).padStart(2, '0')}_d${m.dong}_${m.vai || 'ad'}`, { toi: 'main' });
    }
    ds.push(d);
  }
  return ds;
});

/**
 * Màn KHÔNG MỞ ĐƯỢC thì mọi câu hỏi đều trả lời "không" — và một bảng đầy dấu ✗
 * trông y hệt như sản phẩm thiếu cả chục tính năng. Đây là dương tính giả nguy
 * hiểm nhất của việc soát bằng máy: nó khiến người đọc kết luận ngược hẳn sự
 * thật. Đo 26/09: chín màn cùng ra "0 từ" chỉ vì hai máy chủ dev đã tắt.
 *
 * Nên phân biệt rành mạch: KHÔNG ĐO ĐƯỢC là một trạng thái thứ ba, không phải
 * một kết quả xấu.
 */
function khongDoDuoc(d, m) {
  if (d.loiBam) return `${d.loiBam} — chưa vào được chỗ cần đo`;
  // Đường dẫn XIN, đã bỏ phần truy vấn — `location.pathname` không mang `?lop=7322`,
  // nên so nguyên chuỗi thì mọi màn có tham số đều bị báo "đi lạc".
  const xin = (m.duong || '/').split('?')[0].replace(/\/$/, '') || '/';
  const den = (d.url || '/').replace(/\/$/, '') || '/';
  if (d.soTu === 0) return 'trang rỗng — máy chủ dev có đang chạy không?';
  if (d.ma === 0) return 'không mở nổi trang (goto ném / quá 30 giây) — máy chủ dev có đang chạy không?';
  if (d.ma >= 500) return `máy chủ trả ${d.ma} — lỗi của máy chủ dev, chưa kết luận gì về màn này`;
  if (/doi-mat-khau/.test(den)) return 'bị đẩy sang đổi mật khẩu lần đầu — chọn tài khoản đã đổi mật khẩu';
  // `/login` là một màn ĐÁNG ĐO (dòng 1 · 8 · 13 · 19). Chỉ coi là hỏng khi
  // KHÔNG PHẢI màn mình xin — bản cũ gạch luôn cả lượt đo màn đăng nhập.
  if (/\/login$/.test(den) && !/\/login$/.test(xin)) {
    return 'bị đẩy về màn đăng nhập — thẻ hết hạn, cấp lại rồi đo lại';
  }
  // Đi lạc sang MỘT đường khác (không chỉ trang chủ). `phien.man` dùng lại một
  // trang cho mỗi vai, nên một `goto` bị huỷ để trang NẰM LẠI màn trước — và
  // bộ đo chấm điểm màn trước dưới tên màn sau. Đo 26/09: xin `/giao-trinh`,
  // đo được `/quan-tri/lop-hoc`, báo dòng 5 thiếu hai tính năng đang có.
  if (den !== xin && !(m.chapNhan && new RegExp(m.chapNhan).test(den))) {
    return `đi lạc sang ${den} (xin ${xin}) — trang nằm lại màn trước, chưa kết luận gì`;
  }
  if (/không có trang này/i.test(d.tieuDe)) return 'đường dẫn không tồn tại';
  return null;
}

let hong = 0;
for (let i = 0; i < ra.length; i++) {
  const d = ra[i];
  const vi_sao = khongDoDuoc(d, MAN[i]);
  if (vi_sao) {
    hong++;
    console.log(`? dòng ${d.dong} · ${d.ten} · KHÔNG ĐO ĐƯỢC — ${vi_sao}`);
    continue;
  }
  const thieu = Object.entries(d.tra).filter(([, v]) => !v).map(([k]) => k);
  console.log(`${thieu.length === 0 ? '✓' : '✗'} dòng ${d.dong} · ${d.ten} · ${d.url} · ${d.soTu} từ`);
  if (thieu.length) console.log(`    THIẾU: ${thieu.join(', ')}`);
}
if (hong) {
  console.log(`\n!! ${hong}/${ra.length} màn KHÔNG ĐO ĐƯỢC — chưa kết luận gì về chúng.`);
  console.log('   Bật máy chủ dev, cấp lại thẻ (thẻ sống 30 phút), rồi đo lại.');
}

const j = sau('--json');
if (j) writeFileSync(j, JSON.stringify(ra, null, 1), 'utf8');
console.log(`\nĐo ${ra.length} màn trong một phiên trình duyệt.`);
