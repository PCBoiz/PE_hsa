/**
 * VÒNG LẶP KIỂM PRODUCTION — một lệnh thay cho năm lệnh và một trí nhớ.
 *
 *     PE_THE=<thư mục thẻ> node scripts/vong_lap.mjs            # đo, gieo nếu thiếu, đo lại
 *     PE_THE=<thư mục thẻ> node scripts/vong_lap.mjs --chi-xem  # chỉ đo, không ghi gì
 *     PE_THE=… node scripts/vong_lap.mjs --cho-ban $(git rev-parse --short HEAD)
 *     PE_WEB=http://localhost:3100 PE_API=http://localhost:9000 node scripts/vong_lap.mjs
 *
 * `--cho-ban <sha>` đợi `/api/health` báo đúng commit ấy rồi mới đo — dùng NGAY SAU khi đẩy
 * `master`. Không có nó thì lượt đo rơi vào khoảng 45 phút Render đang dựng, và mọi con số
 * đều thật nhưng là của BẢN CŨ: cách sai đắt nhất, vì nó trông y hệt một lượt đo thành công.
 *
 * ── VÌ SAO CÓ TỆP NÀY (28/09/2026) ──────────────────────────────────────────
 *
 * Kiểm một lượt bản đã deploy hiện là NĂM việc, phải làm đúng thứ tự, và mỗi việc có một cái
 * bẫy riêng đã cắn ít nhất một lần trong ngày:
 *
 *   1. cấp lại thẻ — thẻ sống 30 phút, hết hạn giữa lượt thì MỌI phép đếm ra 0 và trông hệt
 *      như "chưa làm gì" (`kiem_production` báo 0 lớp; `gieo` báo em không học lớp nào);
 *   2. `kiem_production.mjs` — sống / kín / đủ dữ liệu;
 *   3. `gieo_trinh_dien.mjs` — lấp chỗ dữ liệu còn thiếu;
 *   4. `kiem_production.mjs` LẦN NỮA — vì bước 3 vừa đổi dữ liệu;
 *   5. `do_man_hang_loat.mjs` — soát 41 màn bằng thẻ của năm vai.
 *
 * Làm tay thì quên bước, quên thứ tự, hoặc đọc kết quả cũ. Tệp này chạy cả năm, dừng đúng chỗ
 * đáng dừng, và in MỘT bảng điểm ở cuối.
 *
 * ── KHÔNG ĐO ĐƯỢC LÀ TRẠNG THÁI THỨ BA ──────────────────────────────────────
 *
 * "Xanh", "đỏ" và "chưa biết" là ba chuyện. Thẻ hết hạn, máy chủ không trả lời, thiếu thẻ của
 * một vai — cả ba đều KHÔNG phải "đỏ", và gọi chúng là đỏ thì người đọc đi sửa nhầm chỗ. Mã
 * thoát: 0 mọi thứ xanh · 1 có thứ đỏ thật · 2 có thứ chưa đo được.
 */
import { spawn } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = dirname(fileURLToPath(import.meta.url));
const API = process.env.PE_API || 'https://pe-hsa-backend.onrender.com';
const WEB = process.env.PE_WEB || 'https://pe-hsa.vercel.app';
const THE = process.env.PE_THE;
const CHI_XEM = process.argv.includes('--chi-xem');
/** `--cho-ban <sha>`: đợi production báo đúng commit ấy rồi mới đo. */
const CHO_BAN = process.argv.includes('--cho-ban')
  ? (process.argv[process.argv.indexOf('--cho-ban') + 1] || '').slice(0, 7) : null;
/** Render dựng lại mất ~45 phút; chờ tối đa 60 để còn báo "quá lâu" thay vì treo im. */
const CHO_TOI_DA_PHUT = Number(process.env.PE_CHO_PHUT || 60);

const buoc = [];

function ghi(ten, trang_thai, chi_tiet) {
  buoc.push({ ten, trang_thai, chi_tiet });
  const dau = { xanh: '✓', do: '✗', chua: '?' }[trang_thai];
  console.log(`\n${dau} ${ten}${chi_tiet ? ` — ${chi_tiet}` : ''}`);
}

/** Chạy một script con, cho output chảy thẳng ra màn. Trả `{ma, chu}`. */
function chay(tep, tham = [], moi_truong = {}) {
  return new Promise((ok) => {
    const p = spawn(process.execPath, [join(GOC, tep), ...tham], {
      env: { ...process.env, ...moi_truong },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let chu = '';
    const gom = (d) => { const s = String(d); chu += s; process.stdout.write(s); };
    p.stdout.on('data', gom);
    p.stderr.on('data', gom);
    p.on('close', (ma) => ok({ ma: ma ?? 0, chu }));
  });
}

function tieu(n) {
  console.log(`\n${'─'.repeat(72)}\n  ${n}\n${'─'.repeat(72)}`);
}

// ── −1 · Đợi bản mới lên (chỉ khi có `--cho-ban`) ───────────────────────────
// Đo một bản CŨ rồi kết luận "production ổn" là cách sai đắt nhất sau mỗi lượt đẩy: mọi con
// số đều thật, chỉ là của bản khác. Hỏi `/api/health` thay vì đếm phút.
if (CHO_BAN) {
  tieu(`−1 · Đợi production lên bản ${CHO_BAN}`);
  const het = Date.now() + CHO_TOI_DA_PHUT * 60_000;
  let ban = null;
  let lan = 0;
  while (Date.now() < het) {
    lan += 1;
    const r = await fetch(`${API}/api/health`, { signal: AbortSignal.timeout(180000) })
      .then((x) => x.json()).catch(() => null);
    ban = r?.ban ?? null;
    if (ban === CHO_BAN) break;
    const con = Math.round((het - Date.now()) / 60_000);
    console.log(`  lượt ${lan}: production đang chạy "${ban ?? '(không hỏi được)'}"`
      + ` — chờ "${CHO_BAN}", còn tối đa ${con} phút`);
    await new Promise((ok) => setTimeout(ok, 60_000));
  }
  if (ban !== CHO_BAN) {
    ghi(`bản ${CHO_BAN} đã lên production`, 'chua',
        `sau ${CHO_TOI_DA_PHUT} phút vẫn thấy "${ban ?? '(không hỏi được)'}" —`
        + ' mở Render → Logs xem lượt dựng có đỏ không');
    process.exit(2);
  }
  ghi(`bản ${CHO_BAN} đã lên production`, 'xanh', `sau ${lan} lượt hỏi`);
}

// ── 0 · Thẻ còn sống chưa ───────────────────────────────────────────────────
// Hỏi TRƯỚC khi đo, không đợi phép đếm ra 0 rồi đoán. Một lời gọi rẻ đổi lấy việc không bao
// giờ phải phân vân "0 lớp" nghĩa là CSDL trống hay thẻ chết.
tieu('0 · Thẻ');
if (!THE || !existsSync(`${THE}/tokens_ad.json`)) {
  console.log('Cần PE_THE trỏ tới thư mục có tokens_ad.json. ĐỪNG để thư mục ấy trong repo.');
  process.exit(2);
}
const theAd = JSON.parse(readFileSync(`${THE}/tokens_ad.json`, 'utf8')).access;
const thu = await fetch(`${API}/api/admin/classes`, {
  headers: { Authorization: `Bearer ${theAd}` }, signal: AbortSignal.timeout(180000),
}).catch(() => null);
if (!thu) {
  ghi('thẻ quản trị', 'chua', `${API} không trả lời`);
  process.exit(2);
}
if (thu.status === 401 || thu.status === 403) {
  ghi('thẻ quản trị', 'chua', `hết hạn (HTTP ${thu.status}) — cấp lại rồi chạy lại`);
  process.exit(2);
}
ghi('thẻ quản trị', 'xanh', `còn sống (HTTP ${thu.status})`);

const vaiThieu = ['gv', 'tg', 'hvu', 'hv', 'hv2']
  .filter((v) => !existsSync(`${THE}/tokens_${v}.json`));
if (vaiThieu.length) {
  ghi('thẻ các vai', 'chua', `thiếu: ${vaiThieu.join(', ')} — lượt soát màn sẽ bỏ qua phần của họ`);
} else {
  ghi('thẻ các vai', 'xanh', 'đủ năm vai');
}

// ── 1 · Sống · kín · đủ dữ liệu ─────────────────────────────────────────────
tieu('1 · Sống, kín, đủ dữ liệu');
let kp = await chay('kiem_production.mjs');
const soKp = (c) => (c.match(/(\d+)\/(\d+) câu ĐẠT/) || []).slice(1).join('/');
if (kp.ma === 2) {
  ghi('kiem_production', 'chua', 'không đo được — xem dòng cuối ở trên');
  process.exit(2);
}
ghi('kiem_production (lượt đầu)', kp.ma === 0 ? 'xanh' : 'do', soKp(kp.chu));

// ── 2 · Gieo chỗ còn thiếu, rồi chấm lại ────────────────────────────────────
// CHỈ gieo khi lượt đầu đỏ: bộ gieo vốn không ghi đè gì, nhưng chạy một bước ghi khi không có
// việc gì để ghi vẫn là một bước ghi — và mỗi bước ghi vào production là một chỗ để hỏng.
if (kp.ma !== 0 && !CHI_XEM) {
  tieu('2 · Gieo dữ liệu trình diễn');
  const g = await chay('gieo_trinh_dien.mjs', ['--that']);
  ghi('gieo_trinh_dien', g.ma === 0 ? 'xanh' : 'do',
      (g.chu.match(/\[gieo\] (\d+\/\d+) khối/) || [])[1] || '');

  tieu('3 · Chấm lại sau khi gieo');
  kp = await chay('kiem_production.mjs');
  ghi('kiem_production (sau gieo)', kp.ma === 0 ? 'xanh' : 'do', soKp(kp.chu));
} else if (kp.ma !== 0) {
  console.log('\n(--chi-xem: có chỗ thiếu dữ liệu nhưng KHÔNG gieo.)');
}

// ── 3 · Soát màn ────────────────────────────────────────────────────────────
tieu('4 · Soát màn nghiệm thu');
const raJson = join(process.env.TEMP || '/tmp', `vong_lap_man_${Date.now()}.json`);
const m = await chay('do_man_hang_loat.mjs',
                     ['--man', join(GOC, 'man', 'nghiem_thu.json'), '--json', raJson],
                     { PE_WEB: WEB });
const man = { dat: 0, do: 0, chua: 0, tong: 0, doDs: [], chuaDs: [] };
if (existsSync(raJson)) {
  for (const x of JSON.parse(readFileSync(raJson, 'utf8'))) {
    man.tong += 1;
    if (x.khongDoDuoc) { man.chua += 1; man.chuaDs.push(`${x.dong} ${x.ten}`); continue; }
    const thieu = Object.entries(x.tra || {}).filter(([, v]) => !v).map(([k]) => k);
    if (thieu.length) { man.do += 1; man.doDs.push(`${x.dong} ${x.ten} → ${thieu.join(', ')}`); }
    else man.dat += 1;
  }
}
// MỘT dòng cho bước này, không hai. Không dựng được phiên đo là "chưa biết gì về 41 màn" —
// khác hẳn "41 màn đều xanh", mà `0/0 ĐẠT · 0 đỏ` thì đọc thoáng qua trông như vế sau.
if (!man.tong) {
  ghi('soát màn', 'chua', `không dựng được phiên đo (mã ${m.ma}) — chưa biết gì về 41 màn`);
} else {
  ghi('soát màn', man.do ? 'do' : (man.chua ? 'chua' : 'xanh'),
      `${man.dat}/${man.tong} ĐẠT · ${man.do} đỏ · ${man.chua} chưa đo được`);
}

// ── Bảng điểm ───────────────────────────────────────────────────────────────
tieu('BẢNG ĐIỂM');
for (const b of buoc) {
  const dau = { xanh: '✓', do: '✗', chua: '?' }[b.trang_thai];
  console.log(`  ${dau} ${b.ten.padEnd(30)} ${b.chi_tiet || ''}`);
}
if (man.doDs.length) {
  console.log('\n  Màn ĐỎ — đọc kỹ trước khi kết luận là mã sai:');
  for (const d of man.doDs) console.log(`    ✗ ${d}`);
}
if (man.chuaDs.length) {
  console.log('\n  Màn CHƯA ĐO ĐƯỢC — chưa kết luận gì về chúng:');
  for (const d of man.chuaDs) console.log(`    ? ${d}`);
}
console.log(`\n  Bản đo: ${WEB} → ${API}`);
console.log(`  Chi tiết từng màn: ${raJson}`);

const coDo = buoc.some((b) => b.trang_thai === 'do');
const coChua = buoc.some((b) => b.trang_thai === 'chua');
console.log(coDo ? '\nCÓ THỨ ĐỎ.' : coChua ? '\nXanh, nhưng có thứ CHƯA ĐO ĐƯỢC.' : '\nXANH HẾT.');
process.exit(coDo ? 1 : coChua ? 2 : 0);
