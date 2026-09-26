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
  const nut = [...new Set([...document.querySelectorAll('button, a[href]')]
    .filter(hien).map((e) => (e.textContent || '').trim()).filter(Boolean))];
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

const anh = sau('--anh');
const ra = await chay({ goc: GOC, anh }, async (phien) => {
  const ds = [];
  for (const m of MAN) {
    const page = await phien.man(m.duong, m.vai || 'ad');
    // Màn nào tải dữ liệu sau khi dựng thì cần thêm một nhịp; `phien.man` đã chờ
    // tới lúc chiều cao thôi đổi, nhịp này là cho khối nạp bằng `useEffect`.
    await page.waitForTimeout(m.cho ?? 2500);
    const d = await page.evaluate(DOC, m.hoi || {});
    d.dong = m.dong;
    d.ten = m.ten;
    if (anh) await phien.chup(page, `man_${m.dong}_${m.vai || 'ad'}`, { toi: 'main' });
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
  if (d.soTu === 0) return 'trang rỗng — máy chủ dev có đang chạy không?';
  if (d.url === '/' && m.duong !== '/') return `bị đẩy về trang chủ (xin ${m.duong})`;
  if (d.url.includes('/login')) return 'bị đẩy về màn đăng nhập — thẻ hết hạn, cấp lại rồi đo lại';
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
