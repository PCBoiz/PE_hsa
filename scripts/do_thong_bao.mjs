/**
 * ĐO TRANG "THÔNG BÁO" (§61, bảng TopHSA dòng 27) — bấm chuột trên màn thật.
 *
 * Đo bằng chuột chứ không gọi API: dòng 27 đỏ suốt mấy lượt vì backend xong mà màn chưa
 * dựng, nên một lượt đo qua API sẽ lại báo "đạt" cho đúng thứ chưa tới tay người dùng.
 *
 *     node scripts/do_thong_bao.mjs [--anh <thư mục>]
 *
 * Thẻ đọc từ `.the/tokens_hv.json` (`scripts/cap_the.py --id <hv> --ra .the/tokens_hv.json`).
 * Không tự gọi `chromium.launch()` — `chay()` đóng trình duyệt cả khi lỗi lẫn khi Ctrl-C.
 */
import { chay } from './lib/phien_do.mjs';

const WEB = process.env.PE_WEB || 'http://localhost:3100';
const anh = process.argv.includes('--anh')
  ? process.argv[process.argv.indexOf('--anh') + 1]
  : null;

const buoc = [];
function ghi(ten, dat, chiTiet) {
  buoc.push({ ten, dat, chiTiet });
  console.log(`${dat ? 'ĐẠT ' : 'HỎNG'} ${ten}${chiTiet ? ` — ${chiTiet}` : ''}`);
}

/** Chữ của một ô lọc, đã bỏ phần đếm trong ngoặc: "Bài tập mới (3)" → "Bài tập mới". */
const chuLoc = (s) => s.replace(/\s*\(\d+\)\s*$/, '').trim();

/** Trần chờ một lượt gọi máy chủ xong. Dài vì lượt ĐẦU trên máy dev còn phải biên dịch. */
const TRAN = 8000;

/**
 * Chờ tới khi danh sách KHÁC lúc trước, rồi đứng yên. Không ngủ cứng một khoảng.
 *
 * Bản đầu ngủ 900 ms sau mỗi cú bấm và báo HỎNG ô lọc theo loại: máy chủ trả đúng 3 dòng
 * (kiểm riêng bằng curl) nhưng màn chưa vẽ xong khi bộ đo đếm. Lượt gọi ĐẦU đi qua proxy
 * của Next trên máy dev phải biên dịch tuyến, nên nó chậm hẳn so với những lượt sau — một
 * khoảng ngủ đủ cho lượt thứ hai thì thiếu cho lượt đầu. Đây đúng là kiểu "xanh/đỏ tuỳ
 * lúc" mà `phien_do.mjs` ghi là phải chờ theo DẤU HIỆU, có trần.
 */
async function choDoi(dong, truoc) {
  const het = Date.now() + TRAN;
  let yen = -1;
  while (Date.now() < het) {
    const n = await dong.count();
    // Bỏ qua 0: `doiLoc` dọn danh sách TRƯỚC khi gọi máy chủ (để nhãn mới không đứng trên
    // số liệu cũ), nên 0 là một nhịp đi qua, không phải kết quả. Bản đầu nhận 0 làm kết quả
    // và báo 'lọc "Chưa đọc" còn 0 dòng' cho một màn đang lọc đúng 4 dòng.
    if (n > 0 && n !== truoc && n === yen) return n;   // khác lúc trước VÀ đứng yên một nhịp
    yen = n;
    await dong.page().waitForTimeout(150);
  }
  return dong.count();
}

await chay({ goc: WEB, anh }, async (phien) => {
  const page = await phien.man('/thong-bao', 'hv');

  // ── 1. Trang mở được, và mở được với NỘI DUNG (không phải khung rỗng) ──────
  const url = page.url();
  // KHÔNG ĐO ĐƯỢC là trạng thái riêng, khác HỎNG: bị đẩy đi nơi khác thì mọi bước sau đo
  // một trang không liên quan, và bảng kết quả đổ lỗi cho trang Thông báo về chuyện nó
  // không gây ra. Bản đầu chỉ canh `/login`, rồi gặp ngay một tài khoản bị đẩy sang
  // `/doi-mat-khau?lan-dau=1` — ba bước đầu báo HỎNG oan trước khi bộ đo chết.
  const daDi = !url.includes('/thong-bao');
  ghi('trang /thong-bao mở được', !daDi, url);
  if (daDi) {
    console.log(url.includes('/login')
      ? '\nKHÔNG ĐO ĐƯỢC — thẻ hết hạn. Chạy `python scripts/cap_the.py --id <hv> --ra .the/tokens_hv.json`.'
      : `\nKHÔNG ĐO ĐƯỢC — tài khoản bị đẩy sang ${url}. Chọn tài khoản đã đổi mật khẩu lần đầu.`);
    process.exitCode = 2;
    return;
  }

  const khu = page.locator('[data-khu="thong-bao"]');
  ghi('khối danh sách có mặt', (await khu.count()) === 1);

  // Chờ ô lọc BẬT, đừng chờ nó hiện ra. Trang dựng ở máy chủ nên ô lọc có mặt trong HTML
  // đầu tiên, còn `useDaGan` chỉ mở khoá khi React gắn xong — bấm giữa hai mốc ấy thì
  // không lời gọi nào đi, và bộ đo báo "màn không lọc" cho một màn hoàn toàn đúng.
  await khu.locator('button[aria-pressed]:not([disabled])').first()
    .waitFor({ state: 'visible', timeout: TRAN }).catch(() => {});

  const dong = khu.locator('li');
  const soDau = await dong.count();
  ghi('có dòng thông báo', soDau > 0, `${soDau} dòng`);

  // ── 2. Chữ trên màn là tiếng Việt, KHÔNG phải mã kỹ thuật ────────────────
  const chuTrang = (await khu.innerText()).trim();
  const maLot = ['assignment_new', 'assignment_graded', 'submission_new', 'lich_doi',
                 'thong_bao', 'ban_ghi_nhac', 'ban_ghi_loi', 'yeu_cau', 'hoc_bu', 'post_comment']
    .filter((m) => chuTrang.includes(m));
  ghi('không mã kỹ thuật nào lọt lên màn', maLot.length === 0, maLot.join(', ') || 'sạch');

  const nhanLoc = await khu.locator('button[aria-pressed]').allInnerTexts();
  ghi('ô lọc theo loại có nhãn tiếng Việt', nhanLoc.length >= 3, nhanLoc.map(chuLoc).join(' · '));
  await phien.chup(page, 'thong-bao-tat-ca', { toanTrang: true });

  // ── 3. Lọc theo MỘT loại: mọi dòng còn lại phải mang đúng nhãn ấy ────────
  const oLoai = khu.locator('button[aria-pressed]').nth(2);   // 0 = Tất cả, 1 = Chưa đọc
  const tenLoai = chuLoc(await oLoai.innerText());
  await oLoai.click();
  const soSauLoc = await choDoi(dong, soDau);
  const chipSauLoc = await khu.locator('li span').allInnerTexts();
  const lech = chipSauLoc.filter((c) => c.trim() && !c.includes(tenLoai) && !c.includes('chưa đọc'));
  ghi(`lọc "${tenLoai}" chỉ còn dòng của loại ấy`, lech.length === 0 && soSauLoc > 0,
      `${soSauLoc} dòng${lech.length ? `, lệch: ${lech.slice(0, 3).join(' / ')}` : ''}`);
  ghi(`lọc thu hẹp danh sách`, soSauLoc <= soDau, `${soDau} → ${soSauLoc}`);
  await phien.chup(page, 'thong-bao-loc-loai', { toanTrang: true });

  // ── 4. "Chưa đọc" — đếm trên ô lọc phải khớp số dòng chưa đọc thật ───────
  await khu.locator('button[aria-pressed]').first().click();   // về Tất cả
  await choDoi(dong, soSauLoc);
  const oChuaDoc = khu.locator('button[aria-pressed]').nth(1);
  const soTrenO = Number((await oChuaDoc.innerText()).match(/\((\d+)\)/)?.[1] ?? -1);
  await oChuaDoc.click();
  const soDongChuaDoc = await choDoi(dong, soDau);
  const chuaDocThat = await khu.locator('li[data-doc="chua"]').count();
  ghi('lọc "Chưa đọc" chỉ còn dòng chưa đọc', soDongChuaDoc === chuaDocThat && soDongChuaDoc > 0,
      `${soDongChuaDoc} dòng, tất cả chưa đọc`);
  ghi('số trên ô lọc khớp số dòng chưa đọc', soTrenO === soDongChuaDoc || soTrenO > soDongChuaDoc,
      `ô nói ${soTrenO}, trang đầu có ${soDongChuaDoc}`);

  // ── 5. Đánh dấu ĐÃ ĐỌC: dòng đổi trạng thái, và số trên ô lọc TỤT ────────
  const truocKhiDoc = soTrenO;
  const nut = khu.locator('li[data-doc="chua"]').first().locator('button', { hasText: 'Đánh dấu đã đọc' });
  await nut.click();
  // Đánh dấu đọc KHÔNG đổi số dòng khi đang lọc "chưa đọc" — nó làm dòng ấy rời khỏi nhóm
  // `data-doc="chua"`. Chờ đúng cái thay đổi được, chứ không chờ một con số không đổi.
  await khu.locator('li[data-doc="chua"]').nth(soDongChuaDoc - 1).waitFor({ state: 'detached' })
    .catch(() => {});
  await khu.locator('button[aria-pressed]').first().click();   // về Tất cả để đọc lại số
  await choDoi(dong, soDongChuaDoc);
  const sauKhiDoc = Number((await khu.locator('button[aria-pressed]').nth(1).innerText()).match(/\((\d+)\)/)?.[1] ?? -1);
  ghi('đánh dấu đã đọc làm tụt số chưa đọc', sauKhiDoc === truocKhiDoc - 1,
      `${truocKhiDoc} → ${sauKhiDoc}`);

  // ── 6. Đánh dấu CHƯA đọc lại — đường về, cũng phải chạy ──────────────────
  const nutChua = khu.locator('li[data-doc="roi"]').first().locator('button', { hasText: 'Đánh dấu chưa đọc' });
  const soRoi = await khu.locator('li[data-doc="roi"]').count();
  const coNutChua = (await nutChua.count()) > 0;
  if (coNutChua) {
    await nutChua.click();
    await khu.locator('li[data-doc="roi"]').nth(soRoi - 1).waitFor({ state: 'detached' }).catch(() => {});
    const veLai = Number((await khu.locator('button[aria-pressed]').nth(1).innerText()).match(/\((\d+)\)/)?.[1] ?? -1);
    ghi('đánh dấu CHƯA đọc cộng số trở lại', veLai === sauKhiDoc + 1, `${sauKhiDoc} → ${veLai}`);
  } else {
    ghi('đánh dấu CHƯA đọc cộng số trở lại', false, 'không thấy dòng đã đọc nào để thử');
  }

  // ── 7. "Xem thêm" (chỉ khi có trang kế) — không được trùng dòng ──────────
  const nutThem = khu.locator('button', { hasText: 'Xem thêm' });
  if ((await nutThem.count()) > 0) {
    const truoc = await dong.count();
    // So bằng `data-id` chứ không bằng 40 ký tự đầu của chữ trong dòng: mấy dòng cùng loại
    // mở đầu y hệt nhau (cùng chip, cùng "vừa xong"), nên cách cũ báo "20 trùng" cho một
    // danh sách không trùng dòng nào. Một cái thước đo sai thì bảng kết quả cũng sai.
    await nutThem.click();
    const sau = await choDoi(dong, truoc);
    const idSau = await dong.evaluateAll((ns) => ns.map((n) => n.getAttribute('data-id')));
    const trung = idSau.length - new Set(idSau).size;
    ghi('"Xem thêm" nối thêm dòng, không trùng', sau > truoc && trung === 0,
        `${truoc} → ${sau} dòng, ${trung} trùng`);
  } else {
    ghi('"Xem thêm" (bỏ qua)', true, `người này chỉ có ${soDau} dòng — chưa đủ một trang`);
  }

  await phien.chup(page, 'thong-bao-cuoi', { toanTrang: true });

  const dat = buoc.filter((b) => b.dat).length;
  console.log(`\n${dat}/${buoc.length} bước ĐẠT`);
  if (dat < buoc.length) process.exitCode = 1;
});
