/**
 * ĐO MẬT ĐỘ CHỮ trên màn đầu của từng vai — để nói chuyện "nhiều chữ" bằng SỐ.
 *
 * Khách 23/09: *"giao diện đang hơi nhiều chữ, ngay màn hình đầu đã khá nhiều
 * thông tin nên đọc hơi rối"*. Chỉ tiêu và luật gọt nằm ở
 * `docs/HUONG_GIAO_DIEN_2026-09-26.md`; tệp này chỉ đưa ra con số.
 *
 *     node scripts/do_mat_do_chu.mjs                 # đo, in bảng
 *     node scripts/do_mat_do_chu.mjs --anh <thư-mục> # kèm chụp ảnh
 *     node scripts/do_mat_do_chu.mjs --json ra.json  # ghi số ra tệp
 *
 * Cổng và thư mục thẻ đọc từ môi trường, vì mỗi worktree chạy một cổng riêng:
 *
 *     PE_WEB=http://localhost:3500 PE_THE=D:/pe_hsa_wt/gy/.the node scripts/do_mat_do_chu.mjs
 *
 * VÒNG ĐỜI TRÌNH DUYỆT KHÔNG NẰM Ở ĐÂY. Bản đầu (26/09 sáng) tự gọi
 * `chromium.launch()` và đóng ở dòng cuối, không `finally` — một lỗi giữa chừng
 * là Chromium sống tới lúc tắt máy. Chiều 26/09 anh Sơn báo máy sập vì đúng
 * chuyện đó. Nay giao cho `lib/phien_do.mjs`: một trình duyệt cho cả lượt, mỗi
 * vai một trang dùng lại, và đóng cả khi lỗi lẫn khi bị Ctrl-C.
 */
import { writeFileSync } from 'node:fs';
import { chay } from './lib/phien_do.mjs';

const WEB = process.env.PE_WEB || 'http://localhost:3100';
const co = (t) => process.argv.includes(t);
const sau = (t) => { const i = process.argv.indexOf(t); return i > 0 ? process.argv[i + 1] : null; };

/** [tên màn, đường, vai] — thêm màn mới = thêm một dòng. */
const MAN = [
  ['Học viên · Trang của tôi', '/dashboard', 'hv'],
  ['Giảng dạy', '/giang-day', 'ad'],
  // Cùng màn, thẻ GIẢNG VIÊN: người thật mở nó mỗi tối là giảng viên, và số lớp
  // họ thấy khác quản trị nên số chữ cũng khác. Thiếu thẻ thì `phien_do` bỏ trống.
  ['Giảng dạy (giảng viên)', '/giang-day', 'gv'],
  ['Vận hành · Tổng quan', '/quan-tri/tong-quan', 'ad'],
  ['Lịch học', '/giang-day/lich', 'ad'],
];

/**
 * Đếm trong MỘT lần vào trang (kỹ thuật ① của jev-ultrafast: gom lời gọi).
 * Bản cũ gọi `evaluate` nhiều lần cho cùng một trang; mỗi lời gọi là một vòng
 * qua giao thức trình duyệt.
 */
const DEM = () => {
  const hien = (e) => {
    const s = getComputedStyle(e);
    return s.display !== 'none' && s.visibility !== 'hidden' && e.getBoundingClientRect().width > 0;
  };
  const chu = (document.querySelector('main') || document.body).innerText || '';
  const tu = chu.split(/\s+/).filter(Boolean);
  const cau = chu.split('\n').map((x) => x.trim()).filter(Boolean);
  const khoi = [...document.querySelectorAll('section, [class*=card], [class*=Card], [class*=tile]')].filter(hien);
  const nut = [...document.querySelectorAll('button, a[href]')].filter(hien);
  // Ô số = phần tử lá chỉ chứa một con số (các thẻ thống kê trên đầu màn).
  const oSo = [...document.querySelectorAll('*')].filter((e) =>
    hien(e) && e.children.length === 0 && /^\d+([.,]\d+)?%?$/.test((e.textContent || '').trim()));
  const cauDai = cau.filter((c) => c.split(/\s+/).length > 12);
  return {
    soTu: tu.length,
    soDong: cau.length,
    soKhoi: khoi.length,
    soNut: nut.length,
    soOSo: oSo.length,
    cauDai: cauDai.length,
    dongDaiNhat: cauDai.sort((a, b) => b.length - a.length).slice(0, 3),
    caoTrang: document.documentElement.scrollHeight,
  };
};

const batDau = Date.now();
const ra = await chay({ goc: WEB, anh: sau('--anh') }, async (phien) => {
  const ds = [];
  for (const [ten, duong, vai] of MAN) {
    const page = await phien.man(duong, vai);
    const d = await page.evaluate(DEM);
    d.man = ten;
    ds.push(d);
    await phien.chup(page, `man_${vai}${duong.replace(/\//g, '_')}`);
  }
  return ds;
});

console.log(`| Màn | từ | dòng | khối | nút | ô số | dòng >12 từ | cao (px) |`);
console.log('|---|---|---|---|---|---|---|---|');
for (const d of ra) {
  console.log(`| ${d.man} | ${d.soTu} | ${d.soDong} | ${d.soKhoi} | ${d.soNut} | ${d.soOSo} | ${d.cauDai} | ${d.caoTrang} |`);
}
console.log('\nBa dòng dài nhất mỗi màn:');
for (const d of ra) {
  console.log(`\n· ${d.man}`);
  for (const c of d.dongDaiNhat) console.log(`   "${c.slice(0, 120)}"`);
}
console.log(`\nĐo xong ${ra.length} màn trong ${((Date.now() - batDau) / 1000).toFixed(1)}s`);

const j = sau('--json');
if (j) writeFileSync(j, JSON.stringify(ra, null, 2), 'utf8');
