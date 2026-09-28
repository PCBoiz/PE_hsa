/**
 * ĐO MÀN SOẠN THÔNG BÁO (§61, bảng TopHSA dòng 20 + 27) — bấm chuột trên màn thật.
 *
 * Hai màn, hai vai, một phiên trình duyệt:
 *   `/giang-day/thong-bao/<lớp>`  vai TRỢ GIẢNG — dòng 20 ("trợ giảng nhắn / nhắc")
 *   `/quan-tri/thong-bao`         vai HỌC VỤ    — dòng 27, phần soạn của trung tâm
 *
 *     node scripts/do_thong_bao_lop.mjs [--anh <thư mục>] [--lop <id>]
 *
 * Đo bằng CHUỘT chứ không gọi API: cả hai dòng nghiệm thu đỏ suốt mấy lượt vì backend xong
 * mà màn chưa dựng, nên một lượt đo qua API sẽ lại báo "đạt" cho đúng thứ chưa tới tay
 * người dùng (E2 đã đo hết phần API — xem `docs/agent/BAO_CAO_E2.md` §4.5).
 *
 * BỘ ĐO NÀY GHI THẬT. Nó bấm nút Gửi, nên nó tạo thông báo thật cho học viên thật của lớp
 * thử: mọi dữ liệu hiện có là GIẢ (anh Sơn 26/09) nên được phép, nhưng ô "Gửi kèm email"
 * để TRỐNG ở bước gửi — thư ra khỏi hệ thống là không cuộn lại được. Bước xem trước có bật
 * ô ấy, và xem trước không gửi gì (`thong_bao.xem_truoc` chỉ SELECT).
 *
 * Thẻ đọc từ `$PE_THE` (mặc định `D:/pe_hsa/.the`):
 *     python scripts/cap_the.py --id <trợ giảng> --ra .the/tokens_tg.json
 *     python scripts/cap_the.py --id <học vụ>    --ra .the/tokens_hvu.json
 *
 * Không tự gọi `chromium.launch()` — `chay()` của `lib/phien_do.mjs` đóng trình duyệt cả
 * khi lỗi lẫn khi Ctrl-C (máy anh Sơn từng đứng vì 22 tiến trình mồ côi).
 */
import { chay } from './lib/phien_do.mjs';

const WEB = process.env.PE_WEB || 'http://localhost:3100';
const doi = (co, macDinh) => (process.argv.includes(co)
  ? process.argv[process.argv.indexOf(co) + 1]
  : macDinh);
const anh = doi('--anh', null);
const LOP = doi('--lop', '7586');

const buoc = [];
function ghi(ten, dat, chiTiet) {
  buoc.push({ ten, dat, chiTiet });
  console.log(`${dat ? 'ĐẠT ' : 'HỎNG'} ${ten}${chiTiet ? ` — ${chiTiet}` : ''}`);
}

/** Trần chờ một lượt gọi máy chủ xong. Dài vì lượt ĐẦU trên máy dev còn phải biên dịch. */
const TRAN = 12_000;

/** Nhãn để đánh dấu thông báo do bộ đo tạo ra — nhìn danh sách là biết dòng nào của ai. */
const DAU = `[bộ đo ${new Date().toISOString().slice(11, 19)}]`;

/**
 * Chờ tới khi React GẮN XONG: một nút hành động của khối thôi `disabled`.
 *
 * Trang dựng ở máy chủ nên biểu mẫu có mặt trong HTML đầu tiên, còn `useDaGan` chỉ mở khoá
 * khi React gắn vào. Gõ/bấm giữa hai mốc ấy thì chữ bị lượt hydrate đầu xoá và không lời
 * gọi nào đi — bộ đo sẽ báo "màn không gửi được" cho một màn hoàn toàn đúng. Lead mất một
 * lượt đo ngày 26/09 vì đúng chuyện này ở trang `/thong-bao`.
 */
async function choGan(khu, chon) {
  await khu.locator(chon).first().waitFor({ state: 'visible', timeout: TRAN }).catch(() => {});
  const het = Date.now() + TRAN;
  while (Date.now() < het) {
    if (!(await khu.locator(chon).first().isDisabled().catch(() => true))) return true;
    await khu.page().waitForTimeout(120);
  }
  return false;
}

/** Chờ một phần tử hiện ra và trả CHỮ của nó; '' nếu quá trần. */
async function choChu(o) {
  await o.first().waitFor({ state: 'visible', timeout: TRAN }).catch(() => {});
  return (await o.first().innerText().catch(() => '')).trim();
}

await chay({ goc: WEB, anh }, async (phien) => {
  // ════════════════════ MÀN A · LỚP, vai TRỢ GIẢNG (dòng 20) ════════════════════
  const duongLop = `/giang-day/thong-bao/${LOP}`;
  const pTg = await phien.man(duongLop, 'tg');

  // KHÔNG ĐO ĐƯỢC là trạng thái riêng, khác HỎNG: bị đẩy đi nơi khác thì mọi bước sau đo
  // một trang không liên quan, và bảng kết quả đổ lỗi cho màn này về chuyện nó không gây ra.
  if (!pTg.url().includes('/giang-day/thong-bao')) {
    ghi('màn soạn của lớp mở được', false, pTg.url());
    console.log(pTg.url().includes('/login')
      ? '\nKHÔNG ĐO ĐƯỢC — thẻ trợ giảng hết hạn. Cấp lại: python scripts/cap_the.py --id <tg> --ra .the/tokens_tg.json'
      : `\nKHÔNG ĐO ĐƯỢC — bị đẩy sang ${pTg.url()}. Chọn tài khoản đã đổi mật khẩu lần đầu.`);
    process.exitCode = 2;
    return;
  }
  ghi('màn soạn của lớp mở được bằng thẻ TRỢ GIẢNG', true, duongLop);

  const khuLop = pTg.locator('[data-khu="soan-thong-bao-lop"]');
  ghi('khối soạn có mặt', (await khuLop.count()) === 1);

  // Tab trên thanh: trợ giảng phải có đường BẤM tới màn này, không phải chỉ gõ tay URL.
  const tab = pTg.locator(`a[href="${duongLop}"]`);
  ghi('thanh khu Giảng dạy có tab dẫn tới màn này', (await tab.count()) > 0,
      `${await tab.count()} đường dẫn`);

  const daGan = await choGan(khuLop, '[data-nut="xem-truoc"]');
  ghi('ô và nút mở khoá sau khi React gắn (useDaGan)', daGan);

  // ── Xem trước: bật "Gửi kèm email" rồi đếm. Xem trước KHÔNG GỬI GÌ ───────────
  await khuLop.locator('[data-o="kem-email"]').check();
  await khuLop.locator('[data-nut="xem-truoc"]').click();
  const oXem = khuLop.locator('[data-xem-truoc]');
  const cauXem = await choChu(oXem);
  const tongXem = Number(await oXem.first().getAttribute('data-tong').catch(() => null));
  ghi('ô "Xem trước" nói số em sẽ nhận', tongXem > 0 && /\d+ em/.test(cauXem), cauXem);
  ghi('xem trước nói riêng phần EMAIL (không gộp vào một con số)',
      /nhận email|tắt nhận thư|chưa có địa chỉ/.test(cauXem), cauXem);
  await phien.chup(pTg, 'soan-lop-xem-truoc', { toanTrang: true });

  // ── Chữ trên màn là tiếng Việt, không mã kỹ thuật (RULES §10) ────────────────
  const chuLop = await khuLop.innerText();
  const maLot = ['classIds', 'courseIds', 'sendEmail', 'recipientCount', 'thong_bao',
                 'draft', 'cancelled', 'announcement'].filter((m) => chuLop.includes(m));
  ghi('không mã kỹ thuật nào lọt lên màn lớp', maLot.length === 0, maLot.join(', ') || 'sạch');

  // ── Gửi thật. Ô email TẮT lại trước khi gửi: thư ra ngoài là không cuộn lại được ──
  await khuLop.locator('[data-o="kem-email"]').uncheck();
  const tieuDe = `${DAU} Nhắc làm bài trước buổi tối mai`;
  await khuLop.locator('[data-o="tieu-de"]').fill(tieuDe);
  await khuLop.locator('[data-o="noi-dung"]').fill('Các em làm hết phần Định lượng trước 20h mai nhé.');
  const soDongTruoc = await khuLop.locator('[data-ds="da-gui"] li').count();

  await khuLop.locator('[data-nut="gui"]').click();
  const cauHoi = await choChu(khuLop.locator('[data-nut="xac-nhan"]').locator('xpath=../..'));
  ghi('bước hỏi lại nêu ĐÚNG SỐ người, không hỏi "bạn có chắc"',
      /\d+ em/.test(cauHoi) && !/có chắc/i.test(cauHoi), cauHoi.split('\n')[0]);

  await khuLop.locator('[data-nut="xac-nhan"]').click();
  const cauXong = await choChu(khuLop.locator('[data-xong]'));
  ghi('gửi xong: màn nói đã báo cho bao nhiêu em', /\d+ em/.test(cauXong), cauXong);

  const dong = khuLop.locator('[data-ds="da-gui"] li');
  await dong.first().waitFor({ state: 'visible', timeout: TRAN }).catch(() => {});
  const soDongSau = await dong.count();
  ghi('thông báo vừa gửi hiện trong danh sách của lớp', soDongSau === soDongTruoc + 1,
      `${soDongTruoc} → ${soDongSau} dòng`);
  const dongDau = await dong.first().innerText();
  ghi('dòng đầu là đúng thông báo vừa gửi, kèm số em nhận',
      dongDau.includes(tieuDe) && /\d+ em nhận/.test(dongDau),
      dongDau.replace(/\n+/g, ' · ').slice(0, 110));
  ghi('ô soạn được dọn sau khi gửi (không gửi lại lần hai vì tưởng chưa xong)',
      (await khuLop.locator('[data-o="tieu-de"]').inputValue()) === '');
  await phien.chup(pTg, 'soan-lop-da-gui', { toanTrang: true });

  // ── Lớp KHÔNG phải của mình: máy chủ trả 404, màn phải nói đúng câu ấy ───────
  const pKhac = await phien.man('/giang-day/thong-bao/1', 'tg');
  const chuKhac = await pKhac.locator('main').innerText().catch(() => '');
  ghi('lớp không phụ trách: màn nói không mở được, không hiện ô soạn',
      /Không mở được lớp này/.test(chuKhac)
        && (await pKhac.locator('[data-khu="soan-thong-bao-lop"]').count()) === 0,
      chuKhac.split('\n')[0]);

  // ════════════════════ MÀN B · TRUNG TÂM, vai HỌC VỤ (dòng 27) ════════════════
  const pHv = await phien.man('/quan-tri/thong-bao', 'hvu');
  if (!pHv.url().includes('/quan-tri/thong-bao')) {
    ghi('màn thông báo trung tâm mở được bằng thẻ HỌC VỤ', false, pHv.url());
    ketLuan();
    return;
  }
  const khuTt = pHv.locator('[data-khu="thong-bao-trung-tam"]');
  ghi('màn thông báo trung tâm mở được bằng thẻ HỌC VỤ', (await khuTt.count()) === 1);

  const tabTt = pHv.locator('a[href="/quan-tri/thong-bao"]');
  ghi('thanh khu Vận hành có tab dẫn tới màn này', (await tabTt.count()) > 0);

  // Dò trên Ô TICK MÔN, không trên nút "Lưu nháp": nút ấy còn khoá vì một lý do THỨ HAI
  // (chưa nhập tiêu đề), nên nó không phân biệt được "React chưa gắn" với "biểu mẫu chưa
  // đủ" — bản đầu của bộ đo dò ở đó và báo HỎNG cho một màn đã gắn xong. Một cái thước
  // không tách được hai nguyên nhân thì con số nó cho cũng không tách được.
  ghi('ô và nút mở khoá sau khi React gắn (useDaGan)',
      await choGan(khuTt, '[data-nhom="mon"] input[type="checkbox"]'));

  // Danh mục đối tượng phải ĐẾN TỪ MÁY CHỦ — đo bằng số ô tick, và bằng nhãn môn tiếng Việt.
  const oLop = khuTt.locator('[data-nhom="lop"] label[data-lop]');
  const oMon = khuTt.locator('[data-nhom="mon"] label[data-mon]');
  const nhanMon = (await oMon.allInnerTexts()).map((s) => s.trim());
  ghi('ô chọn LỚP dựng từ danh mục máy chủ trả', (await oLop.count()) > 0,
      `${await oLop.count()} lớp`);
  ghi('ô chọn MÔN có nhãn tiếng Việt, không mã kỹ thuật',
      (await oMon.count()) === 3 && !nhanMon.some((s) => /hsa_/.test(s)), nhanMon.join(' · '));

  // ── Xem trước theo MỘT môn: phạm vi rộng hơn một lớp, và phải đếm được ───────
  await oMon.first().locator('input').check();
  await khuTt.locator('[data-nut="xem-truoc"]').click();
  const oXemTt = khuTt.locator('[data-xem-truoc]');
  const cauXemTt = await choChu(oXemTt);
  const tongTt = Number(await oXemTt.first().getAttribute('data-tong').catch(() => null));
  ghi('xem trước theo MÔN đếm được người nhận', tongTt > 0, cauXemTt);

  // ── Đổi ô "Gửi kèm email" phải làm bản xem trước CŨ biến mất (không nói dối) ──
  await khuTt.locator('[data-o="kem-email"]').check();
  await oXemTt.first().waitFor({ state: 'detached', timeout: TRAN }).catch(() => {});
  ghi('đổi ô "Gửi kèm email" thì bản xem trước cũ hết hạn', (await oXemTt.count()) === 0);
  await khuTt.locator('[data-o="kem-email"]').uncheck();
  await phien.chup(pHv, 'thong-bao-trung-tam', { toanTrang: true });

  // ── LƯU NHÁP → nút Gửi + nút Huỷ trên dòng nháp ──────────────────────────────
  const tieuDeTt = `${DAU} Nghỉ lễ — các lớp học bù cuối tuần`;
  await khuTt.locator('[data-o="tieu-de"]').fill(tieuDeTt);
  await khuTt.locator('[data-o="noi-dung"]').fill('Lịch bù sẽ nhắn lại trong tuần.');
  await khuTt.locator('[data-nut="luu-nhap"]').click();
  const nhap = khuTt.locator('[data-ds="da-soan"] li[data-trang-thai="draft"]').first();
  await nhap.waitFor({ state: 'visible', timeout: TRAN }).catch(() => {});
  const chuNhap = await nhap.innerText().catch(() => '');
  ghi('lưu nháp: dòng mới mang nhãn "Bản nháp" và có nút Gửi / Huỷ',
      chuNhap.includes('Bản nháp') && (await nhap.locator('[data-nut="gui-nhap"]').count()) === 1
        && (await nhap.locator('[data-nut="huy-nhap"]').count()) === 1,
      chuNhap.replace(/\n+/g, ' · ').slice(0, 100));

  // ── HUỶ bản nháp vừa lưu: đường huỷ phải chạy, và dòng phải đổi nhãn ─────────
  await nhap.locator('[data-nut="huy-nhap"]').click();
  const daHuy = khuTt.locator('[data-ds="da-soan"] li[data-trang-thai="cancelled"]').first();
  await daHuy.waitFor({ state: 'visible', timeout: TRAN }).catch(() => {});
  ghi('huỷ bản nháp: dòng đổi sang "Đã huỷ", không còn nút Gửi',
      (await daHuy.count()) === 1 && (await daHuy.locator('[data-nut="gui-nhap"]').count()) === 0,
      (await choChu(khuTt.locator('[data-xong]'))) || '—');

  // ── Rồi lưu một nháp nữa và GỬI nó: nút Gửi bản nháp là tuyến cuối chưa đo ───
  //
  // Đổi phạm vi sang LỚP NHỎ NHẤT trước khi gửi. Một môn là ~58 em, và bộ đo này GHI thật
  // (chuông của từng em) — dữ liệu là giả nên được phép, nhưng không có lý do gì để mỗi
  // lượt đo đẻ ra 58 dòng khi 3 dòng chứng minh đúng một điều. Lấy lớp nhỏ nhất theo con
  // số TRÊN Ô TICK, do máy chủ trả, chứ không ghim một id lớp vào bộ đo.
  await oMon.first().locator('input').uncheck();
  const soEm = await oLop.evaluateAll((ns) => ns.map((n) => ({
    lop: n.getAttribute('data-lop'), em: Number((n.innerText.match(/\((\d+) em\)/) || [])[1] ?? 1e9),
  })));
  const nhoNhat = soEm.sort((a, b) => a.em - b.em)[0];
  await khuTt.locator(`[data-nhom="lop"] label[data-lop="${nhoNhat.lop}"] input`).check();
  await khuTt.locator('[data-o="tieu-de"]').fill(`${DAU} Nhắc lịch thi thử`);
  await khuTt.locator('[data-nut="luu-nhap"]').click();
  const nhap2 = khuTt.locator('[data-ds="da-soan"] li[data-trang-thai="draft"]').first();
  await nhap2.waitFor({ state: 'visible', timeout: TRAN }).catch(() => {});
  await nhap2.locator('[data-nut="gui-nhap"]').click();
  const cauGuiNhap = await choChu(khuTt.locator('[data-xong]'));
  ghi('gửi bản nháp: màn nói đã gửi tới bao nhiêu em', /\d+ em/.test(cauGuiNhap), cauGuiNhap);

  const chuTt = await khuTt.innerText();
  const maLotTt = ['classIds', 'courseIds', 'sendEmail', 'recipientCount', 'hsa_',
                   'draft', 'cancelled'].filter((m) => chuTt.includes(m));
  ghi('không mã kỹ thuật nào lọt lên màn trung tâm', maLotTt.length === 0,
      maLotTt.join(', ') || 'sạch');
  await phien.chup(pHv, 'thong-bao-trung-tam-cuoi', { toanTrang: true });

  ketLuan();
});

function ketLuan() {
  const dat = buoc.filter((b) => b.dat).length;
  console.log(`\n${dat}/${buoc.length} bước ĐẠT`);
  if (dat < buoc.length) process.exitCode = 1;
}
