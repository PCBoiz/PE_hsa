/**
 * PHIÊN ĐO — vòng đời trình duyệt dùng chung cho mọi bộ đo trong `scripts/`.
 *
 * VÌ SAO CÓ TỆP NÀY (26/09/2026). Anh Sơn: *"chạy duplicate tabs liên tục gây
 * sập máy tôi"*. Đo thật lúc 09:51 trên máy anh: 11 tiến trình Chromium giữ
 * 788 MB cho MỘT tab trống, cộng 12 tiến trình Python và 10 Node mồ côi — máy
 * chỉ có 15,9 GB. Nguyên nhân không phải "mở nhiều tab" mà là **mở rồi không
 * đóng**: 8 trên 9 bộ đo gọi `chromium.launch()` ở thân tệp, `browser.close()`
 * ở dòng cuối, KHÔNG có `finally`. Bộ đo ném lỗi giữa chừng — trang trả 500,
 * thẻ `pe_at` hết hạn, chờ quá giờ — là Chromium sống tiếp đến khi tắt máy. Mỗi
 * lượt chạy lại cộng thêm một bộ.
 *
 * LUẬT: bộ đo KHÔNG được tự gọi `chromium.launch()`. Gọi `chay()` và nhận
 * `phien`. Ai mở thì người đó đóng, và đóng cả khi mọi thứ hỏng.
 *
 * ── Năm nguyên tắc SOLID, áp vào đây cho ra cái gì ──────────────────────────
 *
 *   S · Một việc: tệp này CHỈ lo vòng đời (mở, cấp thẻ, mở màn, đóng). Nó không
 *       biết đo cái gì — đếm chữ, bắt tương phản hay chạy axe là việc của bộ đo.
 *   O · Mở để nới, đóng để sửa: thêm bộ đo mới thì viết tệp mới gọi `chay()`;
 *       không phải sửa tệp này. Thêm vai mới thì thêm một dòng vào `THE_VAI`.
 *   L · Thay được: mọi bộ đo nhận cùng một `page` của Playwright, nên một bộ đo
 *       viết cho vai học viên chạy được nguyên xi cho vai giáo vụ.
 *   I · Giao diện hẹp: bộ đo chỉ xem trang thì gọi `phien.man()`; bộ đo cần
 *       nhiều khổ màn mới đụng tới `phien.khoMan()`. Không ai phải nhận thứ
 *       mình không dùng.
 *   D · Phụ thuộc vào trừu tượng: bộ đo phụ thuộc `phien`, không phụ thuộc
 *       Chromium. Đổi sang Firefox hay đổi cách cấp thẻ thì sửa MỘT tệp.
 *
 * ── Ba kỹ thuật lấy từ browser-use/jev-ultrafast ────────────────────────────
 *
 *   ① TÁI DÙNG thay vì mở mới. Bên ấy hạ số lời gọi giao thức trình duyệt từ
 *      1.092 xuống 101 cho cùng một việc. Ở đây: MỘT trình duyệt cho cả lượt,
 *      mỗi vai MỘT ngữ cảnh, mỗi ngữ cảnh MỘT trang dùng lại. Bộ đo cũ mở 4
 *      ngữ cảnh + 4 trang cho 4 màn.
 *   ② KHÔNG chụp ảnh khi không cần. Ảnh là thứ đắt nhất trong một lượt đo.
 *      Mặc định tắt; bật bằng `--anh` khi thật sự cần soi.
 *   ③ CHỜ THEO DẤU HIỆU, CÓ TRẦN. Bên ấy chờ gợi ý hiện ra, trần 200 ms. Ở đây
 *      chờ `main` có chữ, trần `TRAN_CHO`. Bộ đo cũ ngủ cứng 6 giây mỗi màn —
 *      24 giây cho 4 màn, phần lớn là ngủ thừa.
 */
import { createRequire } from 'node:module';
import { existsSync, readFileSync } from 'node:fs';

const require = createRequire('D:/pe_hsa/frontend/package.json');
const { chromium } = require('@playwright/test');

/**
 * Thư mục thẻ. Mỗi worktree có `.the` riêng nên đọc từ môi trường:
 * `PE_THE=D:/pe_hsa_wt/gy/.the node scripts/do_...`
 */
const THU_MUC_THE = process.env.PE_THE || 'D:/pe_hsa/.the';

/** Thẻ đăng nhập theo vai. Thêm vai mới = thêm một dòng, không sửa hàm nào. */
export const THE_VAI = {
  hv: `${THU_MUC_THE}/tokens_hv.json`,
  gv: `${THU_MUC_THE}/tokens_gv.json`,
  tg: `${THU_MUC_THE}/tokens_tg.json`,
  ad: `${THU_MUC_THE}/tokens_ad.json`,
  // Quản lý học vụ — vai DUYỆT của hộp Yêu cầu (§65). Đo bằng thẻ quản trị thì không thấy
  // được chỗ nào học vụ bị chặn mà quản trị thì không.
  hvu: `${THU_MUC_THE}/tokens_hvu.json`,
  // Học viên THỨ HAI — cần khi một tính năng chỉ có dữ liệu ở lớp khác (bản ghi
  // Zoom nằm ở lớp 1, còn lớp mẫu 7322 không có buổi nào có `recording_url`).
  // Đo dòng 29 bằng thẻ `hv` của lớp 7322 thì ra "không có bản ghi" — đúng với
  // lớp ấy, sai với sản phẩm.
  hv2: `${THU_MUC_THE}/tokens_hv2.json`,
};

/** Chờ trang "đứng yên" lâu nhất bấy nhiêu mili giây rồi đo, dù chưa yên hẳn. */
const TRAN_CHO = 4000;

/** Nhịp ngó xem trang đã có chữ chưa. Ngắn để không ngủ thừa. */
const NHIP = 150;

function docThe(vai) {
  const d = THE_VAI[vai];
  if (!d || !existsSync(d)) return null;
  try {
    const j = JSON.parse(readFileSync(d, 'utf8'));
    return j.access || Object.values(j)[0] || null;
  } catch {
    return null;
  }
}

/**
 * Mở một phiên đo. KHÔNG gọi thẳng — gọi `chay()` để chắc chắn có người đóng.
 *
 * `goc`     — gốc web đang đo (mặc định cổng 3100 của bản dev chính).
 * `kho`     — khổ màn mặc định.
 * `toi`     — chủ đề tối.
 * `anh`     — thư mục chụp ảnh; bỏ trống thì KHÔNG chụp (kỹ thuật ②).
 */
async function moPhien({ goc = 'http://localhost:3100', kho = { width: 1440, height: 900 }, toi = false, anh = null } = {}) {
  const browser = await chromium.launch();
  const ngu = new Map();      // vai → { ctx, page } — mỗi vai dùng lại một trang

  async function choVai(vai) {
    if (ngu.has(vai)) return ngu.get(vai);
    const ctx = await browser.newContext({
      viewport: kho,
      hasTouch: kho.width <= 430,
      colorScheme: toi ? 'dark' : 'light',
    });
    const the = docThe(vai);
    if (the) {
      await ctx.addCookies([{
        name: 'pe_at', value: the, domain: 'localhost', path: '/',
        httpOnly: true, sameSite: 'Lax',
      }]);
    }
    const page = await ctx.newPage();
    const o = { ctx, page, coThe: Boolean(the) };
    ngu.set(vai, o);
    return o;
  }

  /**
   * Mở một màn và trả `page` đã sẵn sàng để đo. Dùng lại trang của vai ấy.
   *
   * Chờ theo dấu hiệu (kỹ thuật ③): trang coi là xong khi `main` có chữ và
   * chiều cao thôi đổi giữa hai nhịp. Quá `TRAN_CHO` thì đo luôn — thà có số
   * của một trang chưa yên hẳn còn hơn treo cả lượt.
   */
  async function man(duong, vai = 'ad') {
    const { page } = await choVai(vai);
    /* GIỮ MÃ HTTP. `goto` nuốt lỗi bằng `.catch` để một màn hỏng không giết cả
       lượt — nhưng nuốt luôn cả mã trạng thái thì bộ đo không phân biệt được
       "trang 500 của máy chủ dev" với "trang thật thiếu tính năng". Đo 26/09:
       `/giang-day/bai-tap/7322` trả 500 (`__webpack_modules__[moduleId] is not
       a function`) mà bộ đo vẫn chấm ✗ cho ba câu hỏi, y như sản phẩm thiếu ba
       tính năng. `page.maHTTP` là 0 khi chính `goto` ném. */
    const traLoi = await page.goto(goc + duong, { waitUntil: 'domcontentloaded', timeout: 30_000 }).catch(() => null);
    page.maHTTP = traLoi ? traLoi.status() : 0;
    const het = Date.now() + TRAN_CHO;
    let truoc = -1;
    while (Date.now() < het) {
      const cao = await page.evaluate(() => {
        const m = document.querySelector('main') || document.body;
        return (m.innerText || '').trim().length ? document.documentElement.scrollHeight : 0;
      }).catch(() => 0);
      if (cao > 0 && cao === truoc) break;
      truoc = cao;
      await page.waitForTimeout(NHIP);
    }
    return page;
  }

  /** Đổi khổ màn cho MỘT vai — chỉ bộ đo nào cần hai khổ mới gọi (nguyên tắc I). */
  async function khoMan(vai, w, h) {
    const { page } = await choVai(vai);
    await page.setViewportSize({ width: w, height: h });
    return page;
  }

  /**
   * Chụp ảnh — không làm gì nếu phiên không bật `anh` (kỹ thuật ②).
   *
   * `toanTrang` chụp cả trang, `toi` cuộn tới một phần tử rồi mới chụp. Không có
   * hai thứ này thì ảnh chỉ bắt được phần đầu màn, và một khối nằm dưới nếp gấp
   * trông y hệt như một khối không dựng — đã mất một lượt đo vì nhầm thế
   * (26/09/2026).
   */
  async function chup(page, ten, { toanTrang = false, toi = null } = {}) {
    if (!anh) return null;
    if (toi) {
      await page.evaluate((s) => {
        document.querySelector(s)?.scrollIntoView({ block: 'center' });
      }, toi).catch(() => {});
      await page.waitForTimeout(300);
    }
    const d = `${anh}/${ten}.png`;
    await page.screenshot({ path: d, fullPage: toanTrang }).catch(() => {});
    return d;
  }

  let daDong = false;
  async function dong() {
    if (daDong) return;
    daDong = true;
    for (const { ctx } of ngu.values()) await ctx.close().catch(() => {});
    await browser.close().catch(() => {});
  }

  return { browser, man, khoMan, chup, dong, goc };
}

/**
 * Chạy một lượt đo. Mở phiên, giao cho `viec`, và ĐÓNG DÙ CÓ CHUYỆN GÌ.
 *
 *     await chay({ goc: WEB }, async (phien) => {
 *       const page = await phien.man('/dashboard', 'hv');
 *       ...
 *     });
 *
 * `finally` lo đường thoát thường và đường ném lỗi. Còn Ctrl-C, `taskkill`, lỗi
 * không ai bắt và hứa bị bỏ rơi thì `finally` KHÔNG chạy — nên bắt riêng. Đây
 * đúng là bốn cách Chromium mồ côi đã sinh ra trên máy anh Sơn.
 */
export async function chay(tuyChon, viec) {
  const phien = await moPhien(tuyChon);
  const thoat = () => { phien.dong().finally(() => process.exit(130)); };
  process.once('SIGINT', thoat);
  process.once('SIGTERM', thoat);
  process.once('uncaughtException', (e) => { console.error(e); thoat(); });
  process.once('unhandledRejection', (e) => { console.error(e); thoat(); });
  try {
    return await viec(phien);
  } finally {
    await phien.dong();
  }
}

/**
 * BẢO HIỂM cho bộ đo CHƯA chuyển sang `chay()`.
 *
 * Bảy bộ đo vẫn tự `chromium.launch()` (đo 27/09). Chuyển hết sang `chay()` là việc đúng
 * nhưng không nhỏ: mỗi bộ đo là một cổng của RULES §4, đổi cách nó mở trình duyệt thì phải
 * đo lại cả bộ để biết con số có còn nghĩa cũ không. Trong lúc chưa làm xong, thứ nguy
 * hiểm không phải là "mở kiểu nào" mà là "có đóng không".
 *
 *     const b = await chromium.launch();
 *     baoHiem(b);                        // ← một dòng, ngay sau launch
 *
 * Đóng trình duyệt trên bốn đường mà `finally` KHÔNG chạy: Ctrl-C, `taskkill`, lỗi không ai
 * bắt, hứa bị bỏ rơi. Đúng bốn cách Chromium mồ côi đã sinh ra trên máy anh Sơn — ngày
 * 26/09 là 11 tiến trình giữ 788 MB cho một tab trống, và 27/09 lại góp phần làm máy còn
 * 1,5 GB. `e2e/unit/bo-do-phai-dong-trinh-duyet.test.mjs` canh để không ai quên dòng này.
 */
export function baoHiem(browser) {
  let xong = false;
  const dong = () => {
    if (xong) return Promise.resolve();
    xong = true;
    return browser.close().catch(() => {});
  };
  const thoat = () => { dong().finally(() => process.exit(130)); };
  process.once('SIGINT', thoat);
  process.once('SIGTERM', thoat);
  process.once('uncaughtException', (e) => { console.error(e); thoat(); });
  process.once('unhandledRejection', (e) => { console.error(e); thoat(); });
  // Thoát bình thường mà quên `close()` cũng để lại tiến trình: đóng nốt ở đây.
  process.once('beforeExit', () => { void dong(); });
  return dong;
}

export default { chay, THE_VAI, baoHiem };
