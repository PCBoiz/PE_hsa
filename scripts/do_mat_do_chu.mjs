// ĐO mật độ chữ trên các màn đầu của từng vai — để nói chuyện "nhiều chữ" bằng số.
// Khách 23/09: "giao diện đang hơi nhiều chữ, ngay màn hình đầu đã khá nhiều thông tin nên đọc hơi rối".
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
const require = createRequire('D:/pe_hsa/frontend/package.json');
const { chromium } = require('@playwright/test');

const WEB = 'http://localhost:3100';
const S = 'C:/Users/sonkh/AppData/Local/Temp/claude/d--pe-hsa/49d830d0-6a50-4cf5-b9ae-2943d284b22d/scratchpad';
const doc = (p) => { try { return JSON.parse(readFileSync(p, 'utf8')); } catch { return null; } };
const hv = doc('D:/pe_hsa/.the/tokens_hv.json');
const ad = doc('D:/pe_hsa/.the/tokens_ad.json');

const MAN = [
  ['Học viên · Trang của tôi', '/dashboard', hv],
  ['Giảng dạy', '/giang-day', ad],
  ['Vận hành · Tổng quan', '/quan-tri/tong-quan', ad],
  ['Lịch học', '/giang-day/lich', ad],
];

const browser = await chromium.launch();
const ra = [];
for (const [ten, duong, the] of MAN) {
  const t = the?.access || Object.values(the || {})[0];
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  if (t) await ctx.addCookies([{ name: 'pe_at', value: t, domain: 'localhost', path: '/' }]);
  const p = await ctx.newPage();
  await p.goto(WEB + duong, { waitUntil: 'domcontentloaded', timeout: 90_000 }).catch(() => {});
  await p.waitForTimeout(6000);

  const d = await p.evaluate(() => {
    const hien = (e) => {
      const s = getComputedStyle(e);
      return s.display !== 'none' && s.visibility !== 'hidden' && e.getBoundingClientRect().width > 0;
    };
    const chu = (document.querySelector('main') || document.body).innerText || '';
    const tu = chu.split(/\s+/).filter(Boolean);
    const cau = chu.split('\n').map((x) => x.trim()).filter((x) => x.length > 0);
    // Một "khối" = thẻ/card/section người dùng phải quét mắt qua.
    const khoi = [...document.querySelectorAll('section, [class*=card], [class*=Card], [class*=tile]')].filter(hien);
    const nut = [...document.querySelectorAll('button, a[href]')].filter(hien);
    // Ô số: phần tử chỉ chứa số (các "tile" thống kê)
    const oSo = [...document.querySelectorAll('*')].filter((e) =>
      hien(e) && e.children.length === 0 && /^\d+([.,]\d+)?%?$/.test((e.textContent || '').trim()));
    // Câu dài = dòng trên 12 từ (chỗ dễ làm người đọc mệt)
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
  });
  d.man = ten;
  ra.push(d);
  await p.screenshot({ path: `${S}/man_${duong.replace(/\//g, '_')}.png`, fullPage: false });
  await ctx.close();
}
await browser.close();

console.log('| Màn | từ | dòng | khối | nút | ô số | dòng >12 từ | cao (px) |');
console.log('|---|---|---|---|---|---|---|---|');
for (const d of ra) {
  console.log(`| ${d.man} | ${d.soTu} | ${d.soDong} | ${d.soKhoi} | ${d.soNut} | ${d.soOSo} | ${d.cauDai} | ${d.caoTrang} |`);
}
console.log('\nBa dòng dài nhất mỗi màn:');
for (const d of ra) {
  console.log(`\n· ${d.man}`);
  for (const c of d.dongDaiNhat) console.log(`   "${c.slice(0, 120)}"`);
}
writeFileSync(`${S}/mat_do_chu.json`, JSON.stringify(ra, null, 2), 'utf8');
