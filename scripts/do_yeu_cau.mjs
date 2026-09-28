/**
 * ĐO HỘP YÊU CẦU (E3, §65) TRÊN MÀN THẬT — đi trọn dòng 11 bảng phân rã TopHSA
 * ("Giáo vụ · Hỗ trợ lớp học") bằng chuột và bàn phím, không gọi API tay.
 *
 * Bảy gạch đầu dòng của dòng 11, mỗi cái một bước ở đây:
 *   1 tiếp nhận yêu cầu      → học viên gửi ở /yeu-cau
 *   2 phân loại              → học vụ "Đổi loại…" sang Hỗ trợ kỹ thuật
 *   3 phân công người xử lý  → học vụ "Giao người xử lý…"
 *   4 theo dõi trạng thái    → "Nhận xử lý" (Mới → Đang xử lý), chip trạng thái
 *   5 ghi nhận kết quả       → "Đã xong…" kèm ô Kết quả, người gửi đọc được
 *   6 chuyển cho GV/TG       → cùng ô "Giao cho" (danh sách GV/TG của lớp)
 *   7 lưu lịch sử            → dòng thời gian "Trao đổi và lịch sử"
 * Thêm một lượt của phụ huynh qua link tờ báo cáo (dòng 25).
 *
 * KHÔNG tự gọi `chromium.launch()` — dùng `chay()` của `lib/phien_do.mjs` để trình
 * duyệt đóng cả khi lỗi (luật 26/09/2026, máy anh Sơn đứng vì 11 Chromium mồ côi).
 *
 * Chạy (cần Next + Django của worktree, và bốn thẻ còn sống):
 *   PE_WEB=http://localhost:3700 PE_THE=D:/pe_hsa_wt/e3/.the \
 *     node scripts/do_yeu_cau.mjs --anh <thư mục>
 * Thoát 1 nếu một bước nào của dòng 11 không chạy được.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { chay } from './lib/phien_do.mjs';

const DAY = dirname(fileURLToPath(import.meta.url));
const WEB = process.env.PE_WEB || 'http://localhost:3100';
const THE = process.env.PE_THE || join(DAY, '..', '.the');
const sau = (c) => { const i = process.argv.indexOf(c); return i > 0 ? process.argv[i + 1] : null; };
const ANH = sau('--anh');
const CHIA = JSON.parse(readFileSync(join(THE, 'chia_mau.json'), 'utf8'));

const dau = `E3-${Date.now().toString(36)}`;   // dấu riêng của lượt đo, để tìm lại đúng yêu cầu mình tạo
const buoc = [];                                // { ma, viec, dat, ghi }
const ghiBuoc = (ma, viec, dat, ghi = '') => {
  buoc.push({ ma, viec, dat, ghi });
  console.log(`${dat ? '  ✓' : '  ✗'} ${ma}  ${viec}${ghi ? `  — ${ghi}` : ''}`);
};

/** Chờ một câu chữ hiện ra trong trang; trả true/false, không ném. */
async function co(page, chu, giay = 8) {
  try {
    await page.getByText(chu, { exact: false }).first().waitFor({ state: 'visible', timeout: giay * 1000 });
    return true;
  } catch { return false; }
}

/**
 * Bấm một nút theo tên ĐÚNG NGUYÊN VĂN.
 *
 * `exact: true` không phải cho đẹp: mặc định Playwright khớp CHUỖI CON, nên
 * `name: 'Đổi loại'` trúng cái nút mở bảng "Đổi loại…" đứng trước — bộ đo bấm
 * mở rồi bấm đóng, và báo "phân loại hỏng" trong khi màn hình chạy đúng. Cùng
 * bẫy với "Giao" và "Giao người xử lý…".
 */
async function bam(page, ten) {
  const n = page.getByRole('button', { name: ten, exact: true }).first();
  await n.waitFor({ state: 'visible', timeout: 8000 });
  await n.click();
}

/**
 * Chờ React GẮN XONG rồi mới bấm hay gõ.
 *
 * Đo 26/09/2026: `phien.man()` trả trang khi chữ đã đứng yên, mà lúc ấy React
 * còn chưa hydrate. Gõ vào biểu mẫu học viên khi ấy là gõ vào DOM React chưa
 * cầm — bấm xong trình duyệt gửi GET mặc định, chữ bay sạch (đúng cái bẫy
 * `useDaGan` sinh ra để chặn). Bấm "Nhận xử lý" khi ấy thì KHÔNG có gì xảy ra:
 * nút `type="button"`, `onClick` chưa gắn. Ba bước của dòng 11 báo đỏ oan vì thế.
 *
 * Dấu hiệu: React gắn khoá `__reactFiber$…` lên nút DOM khi hydrate xong —
 * đo được, không phải ngủ đoán (RULES §2). Trên máy này: 0 khoá ở nhịp đầu,
 * 8/8 khoá sau ~400 ms.
 */
async function choHydrate(page) {
  await page.waitForFunction(() => {
    const n = document.querySelector('main button') || document.querySelector('button');
    return Boolean(n) && Object.keys(n).some((k) => k.startsWith('__react'));
  }, null, { timeout: 20000 }).catch(() => {});
}

/** Chip trạng thái ở đầu màn chi tiết. */
const trangThai = (page) => page.locator('main h1 ~ div span, h1 ~ div span').first().innerText().catch(() => '');

await chay({ goc: WEB, anh: ANH }, async (phien) => {
  /* ── 1 · Học viên gửi yêu cầu (tiếp nhận) ─────────────────────────────── */
  let page = await phien.man('/yeu-cau', 'hv');
  const coHop = await co(page, 'Gửi câu hỏi hoặc yêu cầu');
  ghiBuoc('hv-hop', 'Học viên mở "Hỏi & yêu cầu"', coHop,
    coHop ? '' : 'không thấy thẻ gửi — thẻ hv hết hạn hay tuyến 500?');
  if (!coHop) return;
  await phien.chup(page, '01-hv-hop-1440-sang');

  const tieuDe = `${dau} máy tính không mở được bài`;
  await choHydrate(page);
  await page.getByLabel('Bạn cần gì?').selectOption('ht_hoc_tap');
  await page.getByLabel('Tóm tắt một dòng').fill(tieuDe);
  await page.getByLabel('Nội dung (không bắt buộc)').fill('Đo lượt E3: em bấm vào bài thì trang trắng.');
  await phien.chup(page, '02-hv-dien-form');
  await bam(page, 'Gửi yêu cầu');
  const daGui = await co(page, 'Trả lời sẽ hiện ở danh sách bên dưới', 10);
  ghiBuoc('dong11-1', '① Tiếp nhận yêu cầu — học viên gửi, hộp nhận', daGui,
    daGui ? `tiêu đề "${tieuDe}"` : 'không thấy câu xác nhận');
  await phien.chup(page, '03-hv-da-gui');
  if (!daGui) return;

  // Mở chính yêu cầu vừa gửi, lấy id từ URL.
  await page.locator('a[href^="/yeu-cau/"]').filter({ hasText: dau }).first().click();
  await page.waitForURL(/\/yeu-cau\/\d+/, { timeout: 8000 });
  const id = Number(page.url().match(/\/yeu-cau\/(\d+)/)[1]);
  console.log(`  · yêu cầu vừa tạo: #${id}`);
  await phien.chup(page, `04-hv-chi-tiet-${id}`);
  const hvKhongThayXuLy = (await page.getByRole('button', { name: 'Nhận xử lý' }).count()) === 0;
  ghiBuoc('hv-khong-xu-ly', 'Học viên KHÔNG thấy thẻ "Xử lý" của nhân sự', hvKhongThayXuLy);

  /* ── 2 · Học vụ: nhận, phân loại, phân công, trả lời, đóng ────────────── */
  let ns = await phien.man('/yeu-cau', 'hvu');
  const coHopNs = await co(ns, 'Yêu cầu');
  ghiBuoc('ns-hop', 'Học vụ mở hộp yêu cầu chung', coHopNs);
  if (!coHopNs) return;
  const thayCuaEm = await co(ns, dau, 10);
  ghiBuoc('ns-thay', 'Yêu cầu mới hiện trong hộp học vụ (mặc định lọc "đang mở")', thayCuaEm);
  await phien.chup(ns, '05-hvu-hop-1440-sang');

  ns = await phien.man(`/yeu-cau/${id}`, 'hvu');
  await choHydrate(ns);
  await bam(ns, 'Nhận xử lý');
  const dangXuLy = await co(ns, 'Đã nhận xử lý');
  ghiBuoc('dong11-4', '④ Theo dõi trạng thái — Mới → Đang xử lý', dangXuLy,
    `chip: ${(await trangThai(ns)) || '?'}`);
  await phien.chup(ns, `06-hvu-dang-xu-ly-${id}`);

  // ② phân loại
  await bam(ns, 'Đổi loại…');
  await ns.getByLabel('Loại đúng của yêu cầu').selectOption('ht_ky_thuat');
  await phien.chup(ns, `07-hvu-phan-loai-${id}`);
  await bam(ns, 'Đổi loại');
  const daDoiLoai = await co(ns, 'Đã đổi loại');
  ghiBuoc('dong11-2', '② Phân loại — học tập → kỹ thuật', daDoiLoai,
    daDoiLoai ? 'bốn loại hỗ trợ: học tập / lịch học / kỹ thuật / tài khoản' : '');

  // ③ + ⑥ phân công / chuyển cho GV-TG
  await bam(ns, 'Giao người xử lý…');
  const oGiao = ns.getByLabel('Giao cho');
  await oGiao.waitFor({ state: 'visible', timeout: 8000 });
  await ns.waitForFunction(() => {
    const s = document.querySelector('select');
    return document.querySelectorAll('select option').length > 2;
  }, null, { timeout: 8000 }).catch(() => {});
  const nguoiNhan = await oGiao.locator('option').allInnerTexts();
  const gvTg = nguoiNhan.filter((t) => /Giảng viên|Trợ giảng/.test(t));
  ghiBuoc('dong11-6', '⑥ Chuyển yêu cầu cho GV/TG — danh sách người nhận', gvTg.length > 0,
    gvTg.length ? gvTg.join(' | ') : 'ô "Giao cho" không có GV/TG nào');
  await phien.chup(ns, `08-hvu-giao-${id}`);
  if (gvTg.length) {
    await oGiao.selectOption({ label: gvTg[0] });
    await ns.getByLabel('Ghi chú cho người nhận').fill('Đo lượt E3: nhờ thầy xem giúp máy của em.');
    await bam(ns, 'Giao');
    const daGiao = await co(ns, 'Đã giao người xử lý');
    ghiBuoc('dong11-3', '③ Phân công người xử lý', daGiao, daGiao ? `giao cho ${gvTg[0]}` : '');
    await phien.chup(ns, `09-hvu-da-giao-${id}`);
  } else {
    ghiBuoc('dong11-3', '③ Phân công người xử lý', false, 'không có ai để giao');
  }

  // Trả lời ra ngoài + một ghi chú nội bộ
  await ns.getByLabel('Trả lời').fill('Bên kỹ thuật đã mở lại quyền xem bài cho em.');
  await bam(ns, 'Gửi trả lời');
  const daTraLoi = await co(ns, 'Đã gửi trả lời');
  ghiBuoc('ns-tra-loi', 'Học vụ trả lời — người gửi đọc được', daTraLoi);

  await ns.getByLabel('Ghi chú nội bộ (học viên, phụ huynh không thấy)').check();
  await ns.getByLabel('Ghi chú nội bộ', { exact: false }).first().fill('Nội bộ: máy của em dùng Windows cũ.');
  await bam(ns, 'Lưu ghi chú');
  const daGhiChu = await co(ns, 'Đã ghi chú nội bộ');
  ghiBuoc('ns-ghi-chu', 'Ghi chú nội bộ lưu riêng (tô vàng)', daGhiChu);

  // ⑤ ghi nhận kết quả
  await bam(ns, 'Đã xong…');
  await ns.getByLabel('Kết quả (người gửi đọc được)').fill('Đã cấp lại quyền xem bài; em thử lại và báo nếu còn lỗi.');
  await phien.chup(ns, `10-hvu-ket-qua-${id}`);
  await bam(ns, 'Đánh dấu đã xong');
  const daXong = await co(ns, 'Đã đóng yêu cầu');
  ghiBuoc('dong11-5', '⑤ Ghi nhận kết quả xử lý', daXong, `chip: ${(await trangThai(ns)) || '?'}`);
  await phien.chup(ns, `11-hvu-da-xong-${id}`);

  // ⑦ lịch sử
  const moc = await ns.getByRole('list', { name: 'Lịch sử yêu cầu' }).locator('li').allInnerTexts().catch(() => []);
  const lichSu = moc.join('\n');
  const duMoc = ['Gửi yêu cầu', 'Chuyển sang', 'Đổi loại', 'Giao cho', 'Trả lời', 'Ghi chú nội bộ']
    .filter((m) => new RegExp(m, 'i').test(lichSu));
  ghiBuoc('dong11-7', '⑦ Lưu lịch sử hỗ trợ — dòng thời gian', duMoc.length >= 3,
    `${moc.length} mốc, khớp: ${duMoc.join(', ')}`);
  await phien.chup(ns, `12-hvu-lich-su-${id}`);

  /* ── 3 · Học viên đọc lại: thấy kết quả, KHÔNG thấy ghi chú nội bộ ─────── */
  page = await phien.man(`/yeu-cau/${id}`, 'hv');
  const thayKetQua = await co(page, 'Đã cấp lại quyền xem bài');
  const anGhiChu = !(await co(page, 'Windows cũ', 2));
  ghiBuoc('hv-doc-ket-qua', 'Học viên đọc được Kết quả', thayKetQua);
  ghiBuoc('hv-an-noi-bo', 'Ghi chú nội bộ ẨN với học viên', anGhiChu);
  await phien.chup(page, `13-hv-sau-khi-xong-${id}`);

  /* ── 4 · Phụ huynh qua link tờ báo cáo ────────────────────────────────── */
  const ph = await phien.man(`/bc/${CHIA.token}`, 'ph');
  await choHydrate(ph);
  const coHopPh = await co(ph, 'Gửi yêu cầu cho trung tâm', 10);
  ghiBuoc('ph-hop', 'Phụ huynh mở tờ báo cáo, thấy chỗ gửi yêu cầu', coHopPh);
  await phien.chup(ph, '14-ph-to-bao-cao-1440-sang');
  if (coHopPh) {
    const oLoai = ph.getByLabel('Anh / chị cần gì?');
    if (await oLoai.count()) {
      await choHydrate(ph);
      await oLoai.first().selectOption('ht_lich_hoc');
      await ph.getByLabel('Tóm tắt một dòng').first().fill(`${dau} phụ huynh xin đổi giờ học`);
      await phien.chup(ph, '15-ph-dien-form');
      await bam(ph, 'Gửi yêu cầu');
      const phDaGui = await co(ph, 'Trung tâm đã nhận yêu cầu', 10);
      ghiBuoc('ph-gui', 'Phụ huynh gửi được yêu cầu qua link (không đăng nhập)', phDaGui);
      await phien.chup(ph, '16-ph-da-gui');
    } else {
      ghiBuoc('ph-gui', 'Phụ huynh gửi được yêu cầu qua link', false, 'không thấy ô "Anh / chị cần gì?" — có thể đã đủ trần 5 yêu cầu đang chờ');
    }
  }

  /* ── 5 · Hai khổ, hai chủ đề — chụp để soi ────────────────────────────── */
  for (const [vai, duong, ten] of [['hv', '/yeu-cau', 'hv-hop'], ['hvu', '/yeu-cau', 'hvu-hop'],
    ['hvu', `/yeu-cau/${id}`, 'hvu-chi-tiet']]) {
    const p = await phien.khoMan(vai, 390, 844);
    await p.goto(WEB + duong, { waitUntil: 'domcontentloaded' }).catch(() => {});
    await p.waitForTimeout(1200);
    await phien.chup(p, `17-${ten}-390-sang`);
    await phien.khoMan(vai, 1440, 900);
  }
  return id;
});

/* ── Khổ 390 và chủ đề TỐI: một phiên riêng (chủ đề đặt lúc mở ngữ cảnh) ─── */
for (const [kho, toi, hau] of [[{ width: 1440, height: 900 }, true, '1440-toi'],
  [{ width: 390, height: 844 }, true, '390-toi']]) {
  await chay({ goc: WEB, anh: ANH, kho, toi }, async (phien) => {
    for (const [vai, duong, ten] of [['hv', '/yeu-cau', 'hv-hop'], ['hvu', '/yeu-cau', 'hvu-hop']]) {
      const p = await phien.man(duong, vai);
      await phien.chup(p, `18-${ten}-${hau}`);
    }
    const p = await phien.man(`/bc/${CHIA.token}`, 'ph');
    await phien.chup(p, `18-ph-to-bao-cao-${hau}`);
  });
}

const hong = buoc.filter((b) => !b.dat);
console.log(`\n${buoc.length - hong.length}/${buoc.length} bước ĐẠT · dấu lượt đo: ${dau}`);
if (hong.length) {
  console.log('HỎNG: ' + hong.map((b) => b.ma).join(', '));
  process.exit(1);
}
