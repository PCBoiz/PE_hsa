/**
 * ĐO LUỒNG TỰ ĐĂNG KÝ (§73, E5 — bảng TopHSA dòng 26) — BẤM CHUỘT trên màn thật.
 *
 *     node scripts/do_dang_ky.mjs [--anh <thư mục>]
 *     PE_WEB=http://localhost:3600 PE_BE=D:/pe_hsa_wt/e2/backend node scripts/do_dang_ky.mjs
 *
 * Gọi `chay()` của `lib/phien_do.mjs` — không tự `chromium.launch()`, nên trình duyệt
 * đóng cả khi bộ đo ném lỗi lẫn khi bị Ctrl-C.
 *
 * ── CHỖ DUY NHẤT KHÔNG ĐI QUA TRÌNH DUYỆT, VÀ VÌ SAO ───────────────────────
 * Một bước của luồng thật nằm NGOÀI trình duyệt: em mở hộp thư rồi bấm đường dẫn.
 * Bộ đo không có hộp thư, nên nó đọc thân lá thư đang chờ trong HỘP THƯ ĐI (§61)
 * để lấy đúng đường dẫn ấy — rồi ĐIỀU HƯỚNG TỚI ĐÓ như em bấm. Việc xác nhận, việc
 * đăng nhập sau đó, và hàng chờ của học vụ đều đo bằng màn thật.
 *
 * Thân thư bị xoá ngay sau khi gửi (`xoa_than`, để mã không nằm lại trong CSDL), nên
 * bộ đo phải đọc SỚM — nó bắt đầu ngó ngay khi màn hiện câu "đã nhận đăng ký". Đọc
 * không kịp thì in "KHÔNG ĐO ĐƯỢC" cho những bước phụ thuộc, KHÔNG in HỎNG: một bước
 * không đo được và một bước sai là hai chuyện khác nhau (RULES §8).
 */
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';

import { chay } from './lib/phien_do.mjs';

const WEB = process.env.PE_WEB || 'http://localhost:3600';
const BE = process.env.PE_BE || 'D:/pe_hsa_wt/e2/backend';
const anh = process.argv.includes('--anh') ? process.argv[process.argv.indexOf('--anh') + 1] : null;

const buoc = [];
function ghi(ten, dat, chiTiet) {
  buoc.push({ dat });
  console.log(`${dat ? 'ĐẠT ' : 'HỎNG'} ${ten}${chiTiet ? ` — ${chiTiet}` : ''}`);
}
function boQua(ten, viSao) {
  console.log(`—    ${ten} — KHÔNG ĐO ĐƯỢC: ${viSao}`);
}

/** Python của repo chính: worktree agent không có `.venv` riêng. */
const PY = ['D:/pe_hsa/backend/.venv/Scripts/python.exe', `${BE}/.venv/Scripts/python.exe`]
  .find((p) => existsSync(p));

/* DỌN trước khi đo. Mỗi lượt đo hỏng giữa chừng để lại MỘT tài khoản chưa xác thực, và
   `tu_dang_ky.TRAN_IP_MOI_NGAY` chỉ cho một địa chỉ mạng mở 5 cái trong 24 giờ — nên lượt
   đo thứ sáu bị chính hàng rào của mình chặn, cửa đăng ký im lặng không tạo gì, và bước
   "chưa xác nhận thì không đăng nhập được" nhận 401 thay vì 403. Mất hai lượt đo vì chỗ
   này (27/09/2026) — hàng rào chạy ĐÚNG, bộ đo mới là cái sai.
   Chỉ xoá tài khoản do CHÍNH bộ đo này dựng: `do_dk_…@example.com`, chưa xác thực. */
const DON = `
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from common.db import x
x("DELETE FROM users WHERE self_registered AND NOT coalesce(is_verified, FALSE) "
  "AND email LIKE %s ESCAPE '~'", ('do~_dk~_%',))
`;

const DOC_THU = `
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from common.db import q1
r = q1("SELECT body FROM outbox WHERE source_type='verify_email' "
       "AND user_id = (SELECT id FROM users WHERE lower(email)=%s) "
       "ORDER BY id DESC LIMIT 1", (sys.argv[1].lower(),))
sys.stdout.write((r or {}).get('body') or '')
`;

/** Đường dẫn xác nhận trong lá thư gửi tới `email`, hoặc null. */
function duongDanTrongThu(email) {
  if (!PY) return null;
  try {
    const ra = execFileSync(PY, ['-c', DOC_THU, email], { cwd: BE, encoding: 'utf8' });
    const m = /(\/xac-thuc-email#chia=[A-Za-z0-9_-]+)/.exec(ra);
    return m ? m[1] : null;
  } catch {
    return null;
  }
}

function don() {
  if (!PY) return;
  try {
    execFileSync(PY, ['-c', DON], { cwd: BE, encoding: 'utf8' });
  } catch {
    /* dọn không được thì cứ đo — cùng lắm là chạm trần và bước 4 nói ra */
  }
}

const rieng = Date.now().toString(36).slice(-7);
const EMAIL = `do_dk_${rieng}@example.com`;
// Số điện thoại 10 chữ số bắt đầu bằng 0 (CHECK của `validate_phone_field`), lấy từ
// dấu thời gian để hai lượt đo không tranh chỉ mục duy nhất `users.phone`.
const SDT = `0${String(Date.now()).slice(-9)}`;

async function dienPhieu(page, email, sdt) {
  await page.locator('#dk-name').fill('Em Đo Đăng Ký');
  await page.locator('#dk-email').fill(email);
  await page.locator('#dk-phone').fill(sdt);
  await page.locator('#dk-password').fill('MatKhauDo#2026');
  await page.locator('#dk-xacNhanMk').fill('MatKhauDo#2026');
  await page.locator('#dk-nguon').selectOption('facebook');
  await page.locator('button[type="submit"]').click();
}

don();

await chay({ goc: WEB, anh }, async (phien) => {
  // ── 1 · Màn đăng ký, KHÔNG đăng nhập ─────────────────────────────────────
  // Vai 'khach': không có tệp thẻ nào tên ấy nên `phien.man` mở trang mà không gắn
  // cookie — đúng tình huống của người chưa có tài khoản.
  const page = await phien.man('/dang-ky', 'khach');
  ghi('mở được /dang-ky mà chưa đăng nhập', page.maHTTP === 200, `HTTP ${page.maHTTP}`);
  ghi('có thẻ phiếu đăng ký', (await page.locator('[data-khu="dang-ky"]').count()) === 1);

  const nut = page.locator('button[type="submit"]');
  // `useDaGan` khoá nút tới khi React gắn xong. Hỏi ngay lúc nút vừa hiện là hỏi SAI
  // LÚC; chờ nó mở, có trần — đừng ngủ cứng một khoảng.
  await page.locator('button[type="submit"]:not([disabled])')
    .waitFor({ state: 'visible', timeout: 15_000 }).catch(() => {});
  ghi('nút gửi khoá lúc đầu rồi mở khi React gắn', await nut.isEnabled().catch(() => false));

  const oChon = page.locator('#dk-nguon option');
  const soMuc = await oChon.count();
  ghi('ô "biết TopHSA từ đâu" nhận danh mục TỪ MÁY CHỦ (không gõ lại trên màn)',
      soMuc >= 9, `${soMuc} mục (1 dòng "— Chọn —" + 8 nguồn của §51)`);

  await phien.chup(page, 'dang-ky-phieu', { toanTrang: true });

  // ── 2 · Câu lỗi tiếng Việt, cạnh đúng ô ──────────────────────────────────
  await page.locator('#dk-name').fill('Em Đo');
  await page.locator('#dk-email').fill('khong-phai-email');
  await nut.click();
  const loiEmail = page.locator('#dk-email-error');
  await loiEmail.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
  const chuLoi = (await loiEmail.innerText().catch(() => '')).trim();
  ghi('email sai dạng → câu lỗi tiếng Việt ngay dưới ô email',
      chuLoi.length > 0 && !/[{}_]|null|undefined/.test(chuLoi), chuLoi || '(không thấy)');

  // ── 3 · Gửi phiếu thật ───────────────────────────────────────────────────
  await dienPhieu(page, EMAIL, SDT);
  const daGui = page.locator('[data-khu="da-gui"]');
  await daGui.waitFor({ state: 'visible', timeout: 20_000 }).catch(() => {});
  const cauChung = (await daGui.innerText().catch(() => '')).trim();
  ghi('gửi được phiếu, màn hiện câu chung của máy chủ',
      cauChung.includes('thư xác nhận'), cauChung.replace(/\s+/g, ' ').slice(0, 110));

  await phien.chup(page, 'dang-ky-da-gui', { toanTrang: true });

  // ── 4 · Chưa xác nhận thì KHÔNG đăng nhập được ───────────────────────────
  const dn = await phien.man('/login', 'khach');
  await dn.locator('button#loginBtn:not([disabled])')
    .waitFor({ state: 'visible', timeout: 15_000 }).catch(() => {});
  await dn.locator('#login-email').fill(EMAIL);
  await dn.locator('#login-password').fill('MatKhauDo#2026');
  await dn.locator('button#loginBtn').click();
  /* Chờ đúng MỘT dấu hiệu: khối "chờ xác thực" chỉ dựng khi máy chủ trả 403 kèm
     `canXacThuc`. Trần rộng vì lượt gọi đầu trên máy dev còn biên dịch tuyến proxy.

     KHÔNG gộp hai bộ chọn bằng dấu phẩy rồi `.first()`: đo 27/09/2026, câu
     `locator('[data-khu="cho-xac-thuc"], [role="alert"]').first().waitFor()` trả về sau
     54 ms trong khi TRANG CHƯA CÓ phần tử nào khớp (lời gọi `/auth/login` còn chưa bay
     đi) — bộ đo đọc một chuỗi rỗng rồi chấm HỎNG cho một màn hoàn toàn đúng. Cùng phép
     đo với bộ chọn ĐƠN: 880 ms, ĐẠT. Mất bốn lượt đo vì chỗ này. */
  await dn.locator('[data-khu="cho-xac-thuc"]')
    .waitFor({ state: 'visible', timeout: 60_000 }).catch(() => {});
  const cauChan = (await dn.locator('[role="alert"]').first().innerText().catch(() => '')).trim();
  ghi('tài khoản chưa xác nhận bị chặn ở cửa đăng nhập',
      dn.url().includes('/login') && cauChan.toLowerCase().includes('xác nhận'),
      cauChan.replace(/\s+/g, ' ').slice(0, 110));
  ghi('câu chặn KHÔNG in mã kỹ thuật (RULES §10)',
      cauChan.length > 0 && !/self_registered|is_verified|403|null/.test(cauChan));

  const nutGuiLai = dn.locator('[data-khu="cho-xac-thuc"] button');
  ghi('có nút "Gửi lại thư xác nhận" ngay tại chỗ bị chặn',
      (await nutGuiLai.count()) === 1);
  if (await nutGuiLai.count()) {
    await nutGuiLai.click();
    const daGuiLai = dn.locator('[data-khu="da-gui-lai"]');
    await daGuiLai.waitFor({ state: 'visible', timeout: 20_000 }).catch(() => {});
    ghi('bấm gửi lại thì máy chủ trả lời bằng câu chung',
        (await daGuiLai.innerText().catch(() => '')).includes('thư xác nhận'));
  }
  await phien.chup(dn, 'dang-nhap-chua-xac-thuc', { toanTrang: true });

  // Đọc thân lá thư — ĐẶT Ở ĐÂY, sau các bước trên trình duyệt, chứ không ngay sau khi
  // gửi phiếu. `execFileSync` dựng một tiến trình Python + `django.setup()` và KHOÁ vòng
  // lặp sự kiện của Node vài giây; đặt nó giữa hai thao tác trình duyệt thì lượt gọi
  // `/auth/login` đang bay bị treo tới khi bộ đo bỏ cuộc (đo 27/09/2026: 886 ms khi
  // không có lời gọi này, quá 60 s khi có). Thân thư bị xoá sau khi gửi xong (~7–13 s
  // trên máy dev), nên vẫn phải đọc SỚM — vòng lặp dưới bù cho lượt đọc hụt.
  let duong = duongDanTrongThu(EMAIL);
  for (let i = 0; i < 4 && !duong; i += 1) {
    await dn.waitForTimeout(200);
    duong = duongDanTrongThu(EMAIL);
  }
  ghi('thư xác nhận được xếp vào hộp thư đi, mã nằm sau dấu #',
      Boolean(duong && duong.includes('#chia=')), duong ? duong.slice(0, 40) + '…' : '(không đọc được)');

  // ── 5 · Đường dẫn xác nhận SAI → nói rõ cách sửa ─────────────────────────
  const sai = await phien.man('/xac-thuc-email#chia=khong-phai-ma-cua-ai', 'khach');
  await sai.locator('[data-khu="khong-thay"]').waitFor({ state: 'visible', timeout: 15_000 })
    .catch(() => {});
  const cauSai = (await sai.locator('[data-khu="khong-thay"]').innerText().catch(() => '')).trim();
  ghi('mã bịa ra → màn nói hết hạn kèm đường về, không phải màn trắng',
      cauSai.toLowerCase().includes('hết hạn'), cauSai.replace(/\s+/g, ' ').slice(0, 90));
  ghi('mã bị xoá khỏi thanh địa chỉ sau khi đọc', !sai.url().includes('chia='), sai.url());

  // ── 6 · Bấm đường dẫn thật → xác nhận → đăng nhập được ───────────────────
  if (!duong) {
    boQua('xác nhận email rồi đăng nhập được', 'không đọc được thân lá thư (đã gửi xong và xoá?)');
    boQua('yêu cầu "Đăng ký mới" hiện trong hộp Yêu cầu của học vụ', 'chưa xác nhận được');
  } else {
    // Gửi lại thư ở bước 4 đã cấp mã MỚI và giết mã cũ — đọc lại đúng mã đang sống.
    const moi = duongDanTrongThu(EMAIL) || duong;
    // Vai 'khach2' = một ngữ cảnh MỚI, không phải trang đã ở `/xac-thuc-email` của bước
    // 5: `goto` sang cùng đường dẫn chỉ khác phần `#` là một lượt chuyển TRONG CÙNG tài
    // liệu, React không gắn lại, và bước này sẽ đo lại đúng màn của bước trước.
    const xt = await phien.man(moi, 'khach2');
    await xt.locator('[data-khu="xong"], [data-khu="khong-thay"]')
      .first().waitFor({ state: 'visible', timeout: 20_000 }).catch(() => {});
    const xong = (await xt.locator('[data-khu="xong"]').count()) === 1;
    ghi('bấm đường dẫn trong thư → xác nhận xong', xong,
        (await xt.locator('[data-khu="xac-thuc-email"]').innerText().catch(() => ''))
          .replace(/\s+/g, ' ').slice(0, 110));
    await phien.chup(xt, 'xac-thuc-xong', { toanTrang: true });

    const dn2 = await phien.man('/login', 'khach2');
    await dn2.locator('button#loginBtn:not([disabled])')
      .waitFor({ state: 'visible', timeout: 15_000 }).catch(() => {});
    await dn2.locator('#login-email').fill(EMAIL);
    await dn2.locator('#login-password').fill('MatKhauDo#2026');
    await dn2.locator('button#loginBtn').click();
    await dn2.waitForURL((u) => !u.pathname.startsWith('/login'), { timeout: 30_000 })
      .catch(() => {});
    ghi('xác nhận xong thì đăng nhập được', !dn2.url().includes('/login'), dn2.url());

    // ── 7 · Hàng chờ xếp lớp = hộp Yêu cầu của học vụ ─────────────────────
    // `/yeu-cau` của nhân sự nạp sẵn các yêu cầu CÒN MỞ (`?mo=1` ở phía trang), nên
    // lượt đăng ký vừa sinh phải nằm ngay trên đó — không cần bộ lọc nào.
    const hvu = await phien.man('/yeu-cau', 'hvu');
    if (!hvu.url().includes('/yeu-cau')) {
      ghi('hộp Yêu cầu của học vụ mở được', false, `bị đẩy sang ${hvu.url()}`);
    } else {
      const chu = await hvu.locator('main').innerText().catch(() => '');
      ghi('yêu cầu "Đăng ký mới" hiện trong hộp Yêu cầu của học vụ',
          chu.includes('Đăng ký mới') && chu.includes('Em Đo Đăng Ký'),
          (chu.split('\n').find((d) => d.includes('Đăng ký mới')) || '(không thấy)').slice(0, 90));
      ghi('hiện NHÃN loại, không hiện mã `tk_dang_ky` (RULES §10)', !chu.includes('tk_dang_ky'));
      await phien.chup(hvu, 'hang-cho-dang-ky', { toanTrang: true });

      // ── 8 · Màn duyệt: học vụ CHỌN LỚP rồi xem trước việc hệ thống sẽ làm ──
      // Chỉ đi tới bước XEM TRƯỚC (GET, máy chủ không ghi gì). Lượt duyệt thật — xếp em
      // vào lớp trong MỘT giao dịch — đo ở `accounts/tests_tu_dang_ky.py`, nơi giao dịch
      // được cuộn lại; bấm Duyệt ở đây sẽ nhét một học viên thử vào một lớp thật.
      await hvu.locator('a', { hasText: 'Đăng ký mới:' }).first().click();
      const nutDuyet = hvu.locator('button', { hasText: 'Duyệt' }).first();
      await nutDuyet.waitFor({ state: 'visible', timeout: 20_000 }).catch(() => {});
      ghi('học vụ thấy nút Duyệt trên lượt đăng ký', (await nutDuyet.count()) > 0);
      await nutDuyet.click();
      const oLop = hvu.locator('select').filter({ hasText: 'Chọn lớp' });
      await oLop.first().waitFor({ state: 'visible', timeout: 20_000 }).catch(() => {});
      ghi('màn duyệt hiện ô "Xếp vào lớp" (cờ chonLopToi từ máy chủ)',
          (await oLop.count()) > 0);
      if (await oLop.count()) {
        const ma = await oLop.first().locator('option').nth(1).getAttribute('value');
        await oLop.first().selectOption(ma);
        const xem = hvu.locator('[aria-live="polite"]');
        await xem.first().waitFor({ state: 'visible', timeout: 20_000 }).catch(() => {});
        const cauXem = (await xem.first().innerText().catch(() => '')).trim();
        ghi('xem trước nói đúng việc sẽ làm: xếp em vào lớp đã chọn',
            cauXem.includes('Xếp') && cauXem.includes('Em Đo Đăng Ký'),
            cauXem.replace(/\s+/g, ' ').slice(0, 100));
      }
      await phien.chup(hvu, 'duyet-dang-ky', { toanTrang: true });
    }
  }

  const dat = buoc.filter((b) => b.dat).length;
  console.log(`\n${dat}/${buoc.length} bước ĐẠT`);
  if (dat < buoc.length) process.exitCode = 1;
});
