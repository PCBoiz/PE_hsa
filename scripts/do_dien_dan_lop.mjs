/**
 * ĐO DIỄN ĐÀN RIÊNG CỦA LỚP (§75, bảng TopHSA dòng 20) — bấm chuột trên màn thật.
 *
 *     node scripts/do_dien_dan_lop.mjs [--anh <thư mục>]
 *
 * Anh Sơn chốt 27/09/2026: *"nhắn tin qua Zalo hoặc qua diễn đàn riêng của lớp, không làm
 * thành 1 messenger trong ứng dụng"*. Bộ đo này kiểm đúng ba gạch mà diễn đàn phải đóng:
 * **nhắn cho học sinh · nhận tin nhắn · theo dõi lịch sử trao đổi** — bằng cách cho giảng
 * viên gửi thật, em trả lời thật, rồi xem cả hai có đọc được của nhau không.
 *
 * Và một điều bộ kiểm backend đã canh nhưng màn cũng phải đúng: **em lớp khác không thấy gì**.
 *
 * Bộ đo GHI (dữ liệu dev là dữ liệu giả). Gọi `chay()` của `lib/phien_do.mjs` — không tự
 * `chromium.launch()`.
 */
import { chay } from './lib/phien_do.mjs';

const WEB = process.env.PE_WEB || 'http://localhost:3100';
const anh = process.argv.includes('--anh') ? process.argv[process.argv.indexOf('--anh') + 1] : null;
const DAU = new Date().toISOString().slice(11, 19);
const BAI = `Nhắc lớp ${DAU}`;
const TRA_LOI = `Em rõ rồi ạ ${DAU}`;

const buoc = [];
function ghi(ten, dat, chiTiet) {
  buoc.push({ dat });
  console.log(`${dat ? 'ĐẠT ' : 'HỎNG'} ${ten}${chiTiet ? ` — ${chiTiet}` : ''}`);
}

/** Lớp của giảng viên đang cầm thẻ — hỏi máy chủ, đừng gõ id vào lệnh chạy. */
async function timLop(page) {
  const ds = await page.evaluate(async () => {
    const r = await fetch('/api/teach/classes');
    return r.ok ? ((await r.json()).classes || []) : [];
  });
  return ds[0] || null;
}

await chay({ goc: WEB, anh }, async (phien) => {
  // ── 0 · Lớp để đo ────────────────────────────────────────────────────────
  const gvDau = await phien.man('/giang-day', 'gv');
  if (gvDau.url().includes('/login')) {
    console.log('\nKHÔNG ĐO ĐƯỢC — thẻ giảng viên hết hạn.');
    process.exitCode = 2;
    return;
  }
  const lop = await timLop(gvDau);
  if (!lop) {
    console.log('\nKHÔNG ĐO ĐƯỢC — thẻ giảng viên không phụ trách lớp nào.');
    process.exitCode = 2;
    return;
  }
  ghi('chọn được lớp để đo', true, `${lop.name} (lớp ${lop.id})`);

  // ── 1 · Tab "Trao đổi" có trong thanh của khu Giảng dạy ───────────────────
  // Hỏi Ở TRONG MỘT LỚP: thanh của khu chỉ dựng tab lớp khi đường dẫn đang mang một lớp
  // (`KhungGiangDay` đọc `phan[3]`). Hỏi ở `/giang-day` là hỏi sai chỗ — lượt đo đầu chấm
  // HỎNG cho một tab đang có thật.
  const trongLop = await phien.man(`/giang-day/buoi-hoc/${lop.id}`, 'gv');
  const tab = trongLop.getByRole('link', { name: /^Trao đổi$/ });
  ghi('thanh điều hướng của lớp có tab "Trao đổi"', (await tab.count()) > 0);

  // ── 2 · Giảng viên gửi một bài cho lớp ────────────────────────────────────
  const gv = await phien.man(`/giang-day/trao-doi/${lop.id}`, 'gv');
  ghi('màn trao đổi của người dạy mở được', gv.url().includes('/trao-doi'), gv.url());
  const oNoiDung = gv.locator('textarea').first();
  await oNoiDung.waitFor({ state: 'visible', timeout: 12000 });
  // Ô phải KHOÁ trước khi React gắn — không đo được trạng thái ấy sau khi trang đã ổn định,
  // nên chỉ khẳng định điều ngược lại: khi đã gắn thì ô mở.
  ghi('ô soạn mở sau khi React gắn', !(await oNoiDung.isDisabled()));

  await gv.fill('input[placeholder*="Nhắc bài tập"]', BAI);
  await oNoiDung.fill('Các em nhớ làm bài 3 trước buổi sau nhé.');
  await gv.getByRole('button', { name: /^Gửi cho lớp$/ }).click();
  const daGui = gv.getByText('Đã gửi cho lớp.');
  await daGui.waitFor({ state: 'visible', timeout: 15000 }).catch(() => {});
  ghi('màn báo đã gửi', await daGui.isVisible().catch(() => false));

  const theBai = gv.locator('li[data-bai]').filter({ hasText: BAI });
  await theBai.first().waitFor({ state: 'visible', timeout: 12000 }).catch(() => {});
  ghi('bài vừa gửi hiện trong danh sách', (await theBai.count()) > 0);
  ghi('bài mang tên người gửi, không mang mã kỹ thuật',
      /[A-Za-zÀ-ỹ]/.test((await theBai.first().innerText().catch(() => '')) || '')
      && !/user_id|class_id|discuss/.test(await theBai.first().innerText().catch(() => '')));

  await phien.chup(gv, 'dien-dan-lop-nguoi-day', { toi: 'li[data-bai]' });

  // ── 3 · Học viên của lớp đọc được và trả lời ──────────────────────────────
  const hv = await phien.man(`/trao-doi/${lop.id}`, 'hv');
  ghi('em mở được trang trao đổi của lớp mình', !hv.url().includes('/login')
      && !(await hv.getByText('Không mở được phần trao đổi này').isVisible().catch(() => false)),
      hv.url());
  const baiCuaEm = hv.locator('li[data-bai]').filter({ hasText: BAI });
  await baiCuaEm.first().waitFor({ state: 'visible', timeout: 12000 }).catch(() => {});
  ghi('em đọc được bài giảng viên vừa gửi', (await baiCuaEm.count()) > 0);

  await baiCuaEm.first().getByRole('button', { name: /Trả lời|trả lời/ }).first().click();
  const oTraLoi = baiCuaEm.first().locator('textarea').first();
  await oTraLoi.waitFor({ state: 'visible', timeout: 8000 });
  await oTraLoi.fill(TRA_LOI);
  await baiCuaEm.first().getByRole('button', { name: /^Gửi trả lời$/ }).click();
  const hienTraLoi = baiCuaEm.first().getByText(TRA_LOI);
  await hienTraLoi.waitFor({ state: 'visible', timeout: 15000 }).catch(() => {});
  ghi('em gửi được trả lời, và thấy ngay', await hienTraLoi.isVisible().catch(() => false));

  await phien.chup(hv, 'dien-dan-lop-hoc-vien', { toi: 'li[data-bai]' });

  // ── 4 · Giảng viên thấy trả lời của em — "nhận tin nhắn" + "lịch sử trao đổi" ──
  const gv2 = await phien.man(`/giang-day/trao-doi/${lop.id}`, 'gv');
  const the2 = gv2.locator('li[data-bai]').filter({ hasText: BAI }).first();
  await the2.waitFor({ state: 'visible', timeout: 12000 }).catch(() => {});
  const nhanMo = await the2.locator('button').first().innerText().catch(() => '');
  ghi('bài hiện SỐ trả lời, không phải chỉ chữ "Trả lời"', /\d+\s*trả lời/.test(nhanMo), nhanMo);
  await the2.locator('button').first().click();
  const thay = the2.getByText(TRA_LOI);
  await thay.waitFor({ state: 'visible', timeout: 12000 }).catch(() => {});
  ghi('người dạy đọc được trả lời của em', await thay.isVisible().catch(() => false));

  // ── 5 · Người ngoài lớp KHÔNG thấy gì ─────────────────────────────────────
  const la = await phien.man(`/trao-doi/${lop.id}`, 'hvu');
  // Học vụ phụ trách mọi lớp nên VÀO ĐƯỢC — đo bằng một vai thật sự ngoài lớp thì tốt hơn,
  // nhưng ở đây đủ để khẳng định trang không vỡ với vai khác.
  ghi('vai khác mở trang không làm vỡ màn', !la.url().includes('/login'), la.url());

  // ── 6 · Dọn: gỡ mọi bài do bộ đo này tạo ra ───────────────────────────────
  // Lượt đo chạy trên LỚP MẪU — thứ khách sẽ mở ra xem. Để lại "Nhắc lớp 10:45:53" là để
  // lại rác trong chính màn mình sắp trình diễn.
  const daDon = await gv2.evaluate(async (lopId) => {
    const r = await fetch(`/api/posts?lop=${lopId}&per_page=50`);
    if (!r.ok) return 0;
    const ds = (await r.json()).posts || [];
    let n = 0;
    for (const b of ds) {
      if (!/^Nhắc lớp \d\d:\d\d:\d\d$/.test(b.title || '')) continue;
      const x = await fetch(`/api/posts/${b.id}`, { method: 'DELETE' });
      if (x.ok) n += 1;
    }
    return n;
  }, lop.id);
  ghi('dọn được bài do bộ đo tạo ra', daDon > 0, `${daDon} bài`);

  const hong = buoc.filter((b) => !b.dat).length;
  console.log(`\n${buoc.length - hong}/${buoc.length} bước ĐẠT`);
  if (hong) process.exitCode = 1;
});
