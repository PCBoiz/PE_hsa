/**
 * Unit test (Node thuần) — TÊN NGƯỜI DÙNG không được chạy được thành mã.
 *
 * ── VÌ SAO CÓ TỆP NÀY (04/09/2026) ────────────────────────────────────────
 *
 * `dashboard.js` dựng nút "Trả lời" của diễn đàn như thế này:
 *
 *     onclick="forumToggleReply('12','34','" + escHtml(c.author) + "')"
 *
 * Nhìn thì có thoát. Nhưng `escHtml` là hàm thoát cho ngữ cảnh HTML, còn chỗ nó
 * đứng là một chuỗi JAVASCRIPT nằm bên trong một thuộc tính HTML. Trình duyệt
 * GIẢI MÃ THỰC THỂ TRƯỚC KHI BIÊN DỊCH JS, nên `&#39;` mà `escHtml` sinh ra
 * quay lại thành `'` đúng lúc trình biên dịch JS nhìn vào. Bước thoát không
 * những vô dụng — nó bị hoàn tác bởi chính cái bước giải mã ấy.
 *
 * Đây là hàng rào đặc quyền THẤP NHẤT trong cả sản phẩm. Không cần vai gì: một
 * tài khoản học viên, ô "Họ tên" trong trang cá nhân (chỉ bị kiểm ĐỘ DÀI,
 * `accounts/validators.py::validate_name_field`), một bình luận — và mã chạy
 * trên trình duyệt của mọi người mở bài viết đó.
 *
 * ── VÌ SAO PHÉP KIỂM NÀY CHẠY THẬT CHỨ KHÔNG ĐỌC CHỮ ──────────────────────
 *
 * Kiểm "trong `onclick` có gọi `escHtml` không" thì bản HỎNG cũng xanh — nó CÓ
 * gọi `escHtml`. Kiểm "chuỗi kết quả không chứa `alert`" thì bản ĐÚNG cũng đỏ
 * nếu ai đó tên là "alert". Cả hai đều không phân biệt được đúng với sai.
 *
 * Nên phép kiểm này làm đúng việc trình duyệt làm: rút thuộc tính `onclick` ra,
 * GIẢI MÃ THỰC THỂ, rồi CHẠY đoạn JS thu được với `ATTACK` là một hàm gián
 * điệp. Tên người dùng chạy được thành mã ⟺ `ATTACK` bị gọi. Không có cách nào
 * lách qua bằng cách viết lại phép kiểm cho vừa.
 *
 * Biểu thức dựng nút được RÚT RA TỪ `dashboard.js` chứ không chép sang đây —
 * chép một bản thì bản chép sẽ được vá còn tệp thật thì không.
 *
 * Chạy: node e2e/unit/onclick-noi-suy.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const MA = readFileSync(join(GOC, 'public', 'static', 'js', 'dashboard.js'), 'utf8');

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

/* Rút biểu thức dựng nút "Trả lời" ra khỏi mã nguồn thật.
   Neo đầu ở tên lớp CSS, neo cuối ở nhãn nút — hai mốc này ổn định qua cả bản
   hỏng (một dòng) lẫn bản vá (hai dòng). */
const NEO_DAU = `'<button class="fpc-cmt-act-btn fpc-cmt-reply-btn`;
const NEO_CUOI = `Trả lời</button>'`;

function rutBieuThuc(ma) {
  const ra = [];
  let i = 0;
  for (;;) {
    const d = ma.indexOf(NEO_DAU, i);
    if (d < 0) break;
    const c = ma.indexOf(NEO_CUOI, d);
    if (c < 0) break;
    ra.push(ma.slice(d, c + NEO_CUOI.length));
    i = c + NEO_CUOI.length;
  }
  return ra;
}

const bieuThuc = rutBieuThuc(MA);

/* Hàm thoát HTML thật của tệp — dùng bản đủ 5 ký tự, tức bản TỐT NHẤT có thể.
   Nếu phép kiểm vẫn đỏ với bản thoát tốt nhất thì lỗi nằm ở NGỮ CẢNH, không
   nằm ở hàm thoát; đó chính là điều cần chứng minh. */
const escHtml = (s) =>
  String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

/* Bóc thẻ như trình duyệt bóc, KHÔNG quét chuỗi thô.
 *
 * Bản đầu của phép kiểm này chỉ tìm chuỗi con `/\son[a-z]+=/` trong HTML — và
 * nó đỏ trên bản ĐÃ VÁ: tên `x" onmouseover="ATTACK()` sau khi thoát thành
 * `x&quot; onmouseover=&quot;ATTACK()`, tức là CHỮ nằm trong giá trị thuộc
 * tính, hoàn toàn vô hại, nhưng chuỗi con `onmouseover=` vẫn còn nguyên ở đó.
 * Một phép kiểm báo đỏ đúng lúc mã đã đúng thì lần sau sẽ bị ai đó tắt đi.
 *
 * Phân biệt "thuộc tính thật" với "chữ trông giống thuộc tính" đòi hỏi bóc
 * tách, không đòi hỏi một biểu thức chính quy khéo hơn.
 *
 * Theo đặc tả HTML, `<` chỉ MỞ MỘT THẺ khi ngay sau nó là chữ cái hoặc `/`;
 * mọi `<` khác là ký tự văn bản. */
function bocThe(html) {
  const the = [];
  let i = 0;
  while (i < html.length) {
    const d = html.indexOf('<', i);
    if (d < 0) break;
    const sau = html[d + 1];
    if (!sau || !/[a-zA-Z/]/.test(sau)) { i = d + 1; continue; }   // `<` là chữ thường

    let j = d + 1;
    const dong = html[j] === '/';
    if (dong) j++;
    const dauTen = j;
    while (j < html.length && /[a-zA-Z0-9]/.test(html[j])) j++;
    const ten = (dong ? '/' : '') + html.slice(dauTen, j).toLowerCase();
    const thuocTinh = [];

    while (j < html.length && html[j] !== '>') {
      if (/\s|\//.test(html[j])) { j++; continue; }
      const dauTt = j;
      while (j < html.length && !/[\s=>/]/.test(html[j])) j++;
      const tenTt = html.slice(dauTt, j).toLowerCase();
      if (tenTt) thuocTinh.push(tenTt);
      while (j < html.length && /\s/.test(html[j])) j++;
      if (html[j] !== '=') continue;
      j++;
      while (j < html.length && /\s/.test(html[j])) j++;
      const nhay = html[j];
      if (nhay === '"' || nhay === "'") {
        j++;
        while (j < html.length && html[j] !== nhay) j++;
        j++;
      } else {
        while (j < html.length && !/[\s>]/.test(html[j])) j++;
      }
    }
    the.push({ ten, thuocTinh });
    i = j + 1;
  }
  return the;
}

/** Giải mã thực thể — đúng bước trình duyệt làm trước khi biên dịch JS. */
function giaiMa(s) {
  return s
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
    .replace(/&#x([0-9a-fA-F]+);/g, (_, n) => String.fromCharCode(parseInt(n, 16)))
    .replace(/&quot;/g, '"').replace(/&apos;/g, "'")
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&');
}

/* Tên tấn công. Chuỗi `');ATTACK();//` thoát ra khỏi đối số thứ ba rồi gọi tiếp;
   `" onmouseover=` thử thoát ra khỏi cả thuộc tính để gắn một trình xử lý mới. */
const TEN_TAN_CONG = [
  `x');ATTACK();//`,
  `x&#39;);ATTACK();//`,          // đã thoát sẵn một lần — thoát hai lần vẫn phải chặn
  `x" onmouseover="ATTACK()`,
  `x</button><img src=q onerror=ATTACK()>`,
];

/** Tên NGƯỜI THẬT có dấu nháy — hàng rào không được chặn oan. */
const TEN_THAT = [`Trần Thị D'Angelo`, `Nguyễn Văn A & B`, `Lê "Tí" Hùng`];

check(`tìm thấy đúng 2 chỗ dựng nút "Trả lời" trong dashboard.js`,
  bieuThuc.length === 2, `${bieuThuc.length} chỗ`);

for (let n = 0; n < bieuThuc.length; n++) {
  const bt = bieuThuc[n];
  let dung;
  try {
    dung = new Function('escHtml', 'postId', 'c', 'r', 'return ' + bt);
  } catch (e) {
    check(`chỗ #${n + 1}: dựng lại được biểu thức`, false, e.message);
    continue;
  }

  for (const ten of TEN_TAN_CONG) {
    const html = dung(escHtml, 12, { id: 34, author: ten }, { id: 56, author: ten });

    // Thuộc tính dùng dấu nháy KÉP và `escHtml` đã đổi `"` thành `&quot;`, nên
    // cắt tới dấu nháy kép kế tiếp là đúng như trình duyệt cắt.
    const m = /onclick="([^"]*)"/.exec(html);
    if (!m) {
      check(`chỗ #${n + 1} · ${JSON.stringify(ten)}: có thuộc tính onclick`, false, html.slice(0, 120));
      continue;
    }

    let goi = 0;
    const ATTACK = () => { goi++; };
    const forumToggleReply = () => {};
    let noiChay = null;
    try {
      new Function('forumToggleReply', 'ATTACK', 'this_', giaiMa(m[1]).replace(/\bthis\b/g, 'this_'))(
        forumToggleReply, ATTACK, { dataset: { mention: ten } },
      );
    } catch (e) {
      noiChay = e.message;   // không biên dịch được cũng là KHÔNG chạy được mã
    }
    check(`chỗ #${n + 1} · tên ${JSON.stringify(ten)} KHÔNG chạy thành mã`,
      goi === 0, noiChay ? `gọi ${goi} lần (và: ${noiChay})` : `ATTACK bị gọi ${goi} lần`);

    // Không được mọc thêm THẺ nào, cũng không mọc thêm thuộc tính nào.
    const the = bocThe(html);
    const tenThe = the.map((t) => t.ten);
    const la = the.flatMap((t) => t.thuocTinh)
      .filter((a) => !['class', 'data-mention', 'onclick'].includes(a));
    check(`chỗ #${n + 1} · tên ${JSON.stringify(ten)} không mọc thêm thẻ`,
      tenThe.join() === 'button,/button', tenThe.join());
    check(`chỗ #${n + 1} · tên ${JSON.stringify(ten)} không mọc thêm thuộc tính`,
      la.length === 0, la.join());
  }

  for (const ten of TEN_THAT) {
    const html = dung(escHtml, 12, { id: 34, author: ten }, { id: 56, author: ten });
    const m = /data-mention="([^"]*)"/.exec(html);
    check(`chỗ #${n + 1} · tên thật ${JSON.stringify(ten)} tới nơi NGUYÊN VẸN`,
      m !== null && giaiMa(m[1]) === ten, m ? giaiMa(m[1]) : '(không có data-mention)');
  }
}

console.log(failures === 0 ? '\nOK — tên người dùng không chạy được thành mã' : `\n${failures} lỗi`);
process.exitCode = failures === 0 ? 0 : 1;
