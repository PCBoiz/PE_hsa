/**
 * ĐO §74 TRÊN MÀN THẬT — "buổi này đã giao bài chưa", và ô chọn mục khung khi giao bài.
 *
 *     node scripts/do_bai_tap_khung.mjs [--anh <thư mục>]
 *
 * Thẻ giảng viên đọc từ `.the/`. Gọi `chay()` của `lib/phien_do.mjs` — không tự
 * `chromium.launch()`.
 *
 * Bộ đo này GHI: nó giao thật một bài trên lớp mẫu để xem chip đổi từ "Chưa giao bài" sang
 * "Đã giao: …". Dữ liệu dev là dữ liệu giả nên ghi được; bài giao xong bộ đo tự xoá.
 */
import { chay } from './lib/phien_do.mjs';

const WEB = process.env.PE_WEB || 'http://localhost:3100';
/** `PE_LOP` ép một lớp cụ thể; bỏ trống thì TỰ TÌM — xem `timLop`. */
const LOP_EP = process.env.PE_LOP || null;
const anh = process.argv.includes('--anh') ? process.argv[process.argv.indexOf('--anh') + 1] : null;
const TEN_BAI = `Bài đo §74 ${new Date().toISOString().slice(11, 19)}`;

const buoc = [];
function ghi(ten, dat, chiTiet) {
  buoc.push({ dat });
  console.log(`${dat ? 'ĐẠT ' : 'HỎNG'} ${ten}${chiTiet ? ` — ${chiTiet}` : ''}`);
}

/**
 * Lớp để đo: lớp đầu tiên của giảng viên CÓ mục khung cần bài.
 *
 * Trước đây id lớp gõ thẳng vào lệnh chạy, và `du_lieu_mau --lam-moi` dựng lại bộ mẫu với
 * id MỚI — nên sau mỗi lượt làm mới, bộ đo trỏ vào một lớp đã bị gỡ và báo hỏng như thể
 * tính năng hỏng. Hỏi máy chủ thì không bao giờ lệch.
 */
async function timLop(page) {
  const ds = await page.evaluate(async () => {
    const r = await fetch('/api/teach/classes');
    if (!r.ok) return [];
    return (await r.json()).classes || [];
  });
  for (const lop of ds) {
    const soMuc = await page.evaluate(async (id) => {
      const r = await fetch(`/api/teach/classes/${id}/chuong-trinh`);
      if (!r.ok) return 0;
      const d = await r.json();
      return (d.buoiKhung || []).reduce(
        (n, k) => n + k.items.filter((i) => i.baiDaGiao !== undefined).length, 0);
    }, lop.id);
    if (soMuc > 0) return { id: String(lop.id), ten: lop.name, soMuc };
  }
  return null;
}

/** Chữ của mọi mục trên màn Chương trình lớp — một lần đọc, nhiều lần hỏi. */
async function chuMuc(page) {
  return (await page.locator('li[data-muc]').allInnerTexts()).map((s) => s.replace(/\s+/g, ' ').trim());
}

await chay({ goc: WEB, anh }, async (phien) => {
  // ── 0 · Chọn lớp ─────────────────────────────────────────────────────────
  const dau = await phien.man('/giang-day', 'gv');
  if (dau.url().includes('/login')) {
    console.log('\nKHÔNG ĐO ĐƯỢC — thẻ hết hạn. Cấp lại: python scripts/cap_the.py --vai "Giảng viên" --ra .the/tokens_gv.json');
    process.exitCode = 2;
    return;
  }
  const chon = LOP_EP ? { id: LOP_EP, ten: '(ép bằng PE_LOP)', soMuc: null } : await timLop(dau);
  if (!chon) {
    console.log('\nKHÔNG ĐO ĐƯỢC — không lớp nào của giảng viên này có mục khung cần bài.'
                + '\nChạy `python manage.py du_lieu_mau --lam-moi` rồi đo lại.');
    process.exitCode = 2;
    return;
  }
  const LOP = chon.id;
  ghi('chọn được lớp để đo', true, `${chon.ten} (lớp ${LOP}${chon.soMuc ? `, ${chon.soMuc} mục cần bài` : ''})`);

  // ── 1 · Màn Chương trình lớp: mục cần bài nói rõ đã giao hay chưa ─────────
  const ct = await phien.man(`/giang-day/chuong-trinh/${LOP}`, 'gv');
  if (!ct.url().includes('/chuong-trinh')) {
    console.log(`\nKHÔNG ĐO ĐƯỢC — bị đẩy sang ${ct.url()}`);
    process.exitCode = 2;
    return;
  }
  const muc = ct.locator('li[data-muc]');
  await muc.first().waitFor({ state: 'visible', timeout: 12000 }).catch(() => {});
  const soMuc = await muc.count();
  ghi('mục của buổi khung hiện trên màn', soMuc > 0, `${soMuc} mục`);
  if (soMuc === 0) {
    console.log('\nLớp này chưa nhận khung? Chạy `python manage.py du_lieu_mau --lam-moi`.');
    process.exitCode = 1;
    return;
  }

  const truoc = await chuMuc(ct);
  const canBai = truoc.filter((s) => /Chưa giao bài|Đã giao|Đang soạn/.test(s));
  ghi('mục CẦN bài mang câu trả lời "giao bài chưa"', canBai.length > 0,
      `${canBai.length}/${soMuc} mục: ${canBai.slice(0, 2).join(' | ')}`);
  // Mục chủ đề KHÔNG được mang câu ấy — khoá vắng mặt khác danh sách rỗng.
  const chuDe = truoc.filter((s) => !/Chưa giao bài|Đã giao|Đang soạn/.test(s));
  ghi('mục chủ đề KHÔNG bị hỏi "giao bài chưa"', chuDe.length > 0,
      `${chuDe.length} mục không có chip`);
  const chuaGiao = truoc.filter((s) => s.includes('Chưa giao bài')).length;
  ghi('có mục đang "Chưa giao bài" để đo tiếp', chuaGiao > 0, `${chuaGiao} mục`);

  await phien.chup(ct, 'khung-da-giao-truoc', { toanTrang: true, toi: 'li[data-muc]' });

  // ── 2 · Biểu mẫu giao bài: ô chọn mục khung ───────────────────────────────
  const bt = await phien.man(`/giang-day/bai-tap/${LOP}`, 'gv');
  ghi('màn Bài tập mở được', bt.url().includes('/bai-tap'), bt.url());

  const nutMo = bt.getByRole('button', { name: /Giao bài mới/i }).first();
  await nutMo.waitFor({ state: 'visible', timeout: 12000 });
  await nutMo.click();

  const oChon = bt.locator('select[name="syllabus_item_id"]');
  await oChon.waitFor({ state: 'visible', timeout: 8000 }).catch(() => {});
  ghi('biểu mẫu có ô "Mục khung chương trình"', (await oChon.count()) === 1);
  if ((await oChon.count()) !== 1) {
    process.exitCode = 1;
    return;
  }

  const nhan = await oChon.locator('option').allInnerTexts();
  ghi('ô chọn dựng từ danh mục máy chủ trả', nhan.length > 1, `${nhan.length - 1} mục + "Không gắn"`);
  ghi('nhãn mang số buổi, không mang id', nhan.slice(1).every((s) => /Buổi \d/.test(s)),
      nhan.slice(1, 3).join(' | '));
  ghi('không mã kỹ thuật nào lọt lên ô chọn',
      !nhan.some((s) => /bai_tap|kiem_tra|chu_de|syllabus|item_id/.test(s)));
  ghi('có mục "Không gắn vào khung" — ô này KHÔNG bắt buộc',
      nhan.some((s) => /Không gắn vào khung/.test(s)), nhan[0]);

  await phien.chup(bt, 'khung-o-chon-muc-giao-bai', { toi: 'select[name="syllabus_item_id"]' });

  // ── 3 · Giao thật một bài vào mục chưa có bài, xem chip đổi ───────────────
  // Chọn mục chưa có bài: nhãn không mang "— đã có bài".
  const gt = await oChon.locator('option').evaluateAll((os) => os
    .filter((o) => o.value && !o.textContent.includes('đã có bài'))
    .map((o) => ({ v: o.value, t: o.textContent.trim() })));
  ghi('tìm được mục chưa có bài để gắn vào', gt.length > 0, gt[0]?.t);
  if (gt.length === 0) { process.exitCode = 1; return; }

  await bt.fill('input[name="title"]', TEN_BAI);
  await oChon.selectOption(gt[0].v);
  await bt.getByRole('button', { name: /^Giao bài$/i }).first().click();

  const bao = bt.getByText(new RegExp(`Đã giao bài "${TEN_BAI.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}"`));
  await bao.waitFor({ state: 'visible', timeout: 15000 }).catch(() => {});
  ghi('màn báo đã giao bài', await bao.isVisible().catch(() => false));

  const ct2 = await phien.man(`/giang-day/chuong-trinh/${LOP}`, 'gv');
  await ct2.locator('li[data-muc]').first().waitFor({ state: 'visible', timeout: 12000 }).catch(() => {});
  const sau = await chuMuc(ct2);
  const dong = sau.find((s) => s.includes(TEN_BAI));
  ghi('mục vừa gắn đổi sang "Đã giao: <tên bài>"', Boolean(dong && dong.includes('Đã giao')),
      dong || '(không thấy tên bài trên màn Chương trình)');
  ghi('số mục "Chưa giao bài" giảm đúng một',
      sau.filter((s) => s.includes('Chưa giao bài')).length === chuaGiao - 1,
      `${chuaGiao} → ${sau.filter((s) => s.includes('Chưa giao bài')).length}`);

  await phien.chup(ct2, 'khung-da-giao-sau', { toanTrang: true, toi: 'li[data-muc]' });

  // ── 4 · Dọn: xoá bài vừa giao để lượt đo sau bắt đầu như lượt này ────────
  const bt2 = await phien.man(`/giang-day/bai-tap/${LOP}`, 'gv');
  const the = bt2.locator('li, article').filter({ hasText: TEN_BAI }).first();
  const xoa = the.getByRole('button', { name: /Xoá/i }).first();
  let daXoa = false;
  if (await xoa.count()) {
    bt2.once('dialog', (d) => void d.accept());
    await xoa.click();
    await bt2.getByText(TEN_BAI).first().waitFor({ state: 'detached', timeout: 12000 })
      .then(() => { daXoa = true; }).catch(() => {});
  }
  ghi('dọn được bài đo (lượt sau bắt đầu như lượt này)', daXoa,
      daXoa ? '' : `còn lại "${TEN_BAI}" — xoá tay trên màn Bài tập`);

  const hong = buoc.filter((b) => !b.dat).length;
  console.log(`\n${buoc.length - hong}/${buoc.length} bước ĐẠT`);
  if (hong) process.exitCode = 1;
});
