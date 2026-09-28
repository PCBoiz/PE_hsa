/**
 * Unit test — `thuTrongTuanVN` phải trả CÙNG một thứ dù máy chạy ở múi nào.
 *
 * ── VÌ SAO (14/09/2026, tối) ───────────────────────────────────────────────
 *
 * Dải "Lịch học tuần này" chuyển từ tầng cũ (trình duyệt, giờ VN) sang dựng ở
 * máy chủ (Vercel, UTC). `new Date().getDay()` ở hai nơi ấy lệch nhau một ngày
 * từ 0h tới 7h sáng giờ VN → ô "hôm nay" tô sai và React báo lỗi hydrate.
 *
 * Phép kiểm chạy HAI LẦN trong hai tiến trình con, một với `TZ=UTC`, một với
 * `TZ=Asia/Ho_Chi_Minh`, cho cùng những mốc giờ sát nửa đêm — và đòi cả hai ra
 * đúng thứ theo lịch VN. Kèm một hàng rào: cách ngây thơ `getDay()` PHẢI cho
 * kết quả khác nhau giữa hai múi ở mốc 03:00 sáng VN, không thì phép kiểm này
 * chẳng kiểm được gì.
 *
 * Chạy: node e2e/unit/gio-vn.test.mjs
 */
import { execFileSync } from 'node:child_process';
import { register } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');

// ── Tiến trình con: in kết quả cho các mốc rồi thoát ───────────────────────
if (process.argv[2] === '--con') {
  register('./hooks-nap-nguon.mjs', import.meta.url);
  const { thuTrongTuanVN, lucVN } = await import(pathToFileURL(join(GOC, 'src', 'lib', 'gioVN.ts')).href);
  const MOC = [
    '2026-09-13T20:00:00Z', // 03:00 thứ Hai 14/09 giờ VN — UTC vẫn là Chủ nhật
    '2026-09-13T16:59:59Z', // 23:59:59 Chủ nhật 13/09 giờ VN
    '2026-09-13T17:00:00Z', // 00:00 thứ Hai 14/09 giờ VN
    '2026-09-20T10:00:00Z', // 17:00 Chủ nhật 20/09 giờ VN
  ];
  const ra = MOC.map((m) => ({ moc: m, vn: thuTrongTuanVN(new Date(m)), ngayTho: (new Date(m).getDay() + 6) % 7 }));
  // `lucVN` (25/09/2026): chuỗi giờ VN ngây thơ của máy chủ → chữ, KHÔNG qua Date.
  ra.push({ luc: [lucVN('2026-09-25T20:15:03.123'), lucVN('2026-09-25'), lucVN(null), lucVN('hôm qua')] });
  process.stdout.write(JSON.stringify(ra));
  process.exit(0);
}

let loi = 0;
const check = (ten, ok, ct = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${ten}${ok || !ct ? '' : `  → ${ct}`}`);
  if (!ok) loi += 1;
};

const chay = (tz) => JSON.parse(execFileSync(process.execPath, [fileURLToPath(import.meta.url), '--con'], {
  env: { ...process.env, TZ: tz }, encoding: 'utf8',
}));
const utcDu = chay('UTC');
const vnDu = chay('Asia/Ho_Chi_Minh');
const MONG_LUC = ['25/09/2026 20:15', '25/09/2026', '—', 'hôm qua'];
for (const [tz, du] of [['UTC', utcDu], ['Asia/HCM', vnDu]]) {
  const luc = du[du.length - 1].luc;
  check(`lucVN không lệch múi (TZ=${tz})`, JSON.stringify(luc) === JSON.stringify(MONG_LUC), JSON.stringify(luc));
}
const utc = utcDu.slice(0, -1);
const vn = vnDu.slice(0, -1);

const MONG = [0, 6, 0, 6]; // thứ Hai=0 … Chủ nhật=6
utc.forEach((x, i) => {
  check(`TZ=UTC        ${x.moc} → ${x.vn}`, x.vn === MONG[i], `mong ${MONG[i]}`);
  check(`TZ=Asia/HCM   ${vn[i].moc} → ${vn[i].vn}`, vn[i].vn === MONG[i], `mong ${MONG[i]}`);
});
check('hàng rào: getDay() ngây thơ LỆCH giữa hai múi ở 03:00 sáng VN (tức phép kiểm có răng)',
  utc[0].ngayTho !== vn[0].ngayTho, `UTC=${utc[0].ngayTho} VN=${vn[0].ngayTho}`);

console.log(loi ? `\n${loi} lỗi` : '\nOK — thứ trong tuần theo giờ VN không phụ thuộc múi của máy');
process.exit(loi ? 1 : 0);
