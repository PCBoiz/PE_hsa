/**
 * CÒN SÓT — bước NGHIÊN CỨU của vòng lặp: đọc sổ nghiệm thu, moi ra mọi chỗ nó tự nhận là
 * chưa xong, rồi chia làm hai cột: thứ TÔI LÀM ĐƯỢC NGAY và thứ CHỜ NGƯỜI KHÁC.
 *
 *     node scripts/con_sot.mjs              # cả hai cột
 *     node scripts/con_sot.mjs --lam-duoc   # chỉ thứ không vướng ai
 *     node scripts/con_sot.mjs --dong 11    # một dòng của bảng phân rã
 *
 * ── VÌ SAO CÓ TỆP NÀY (28/09/2026) ──────────────────────────────────────────
 *
 * `docs/NGHIEM_THU_TOPHSA.md` dài hơn 700 dòng và mỗi ô của bảng phân rã mang một đoạn văn
 * dày. Những câu QUAN TRỌNG NHẤT trong đó — "Còn thiếu…", "Còn sót…", "CHƯA…" — là do chính
 * tôi viết ra lúc đo, và rồi chìm nghỉm giữa phần kể công.
 *
 * Bằng chứng: dòng 11 mang câu "Còn sót (ngoài phạm vi dòng 11): hạn xử lý / cờ quá hạn, ô
 * tìm theo chữ" từ 26/09. Hai ngày sau không ai quay lại — kể cả tôi — vì cột "Hiện nay" của
 * dòng ấy ghi **CÓ**, và mắt đọc bảng thì dừng ở cột ấy. Hai ô đó không vướng anh Sơn, không
 * vướng khoá ngoài nào; chúng chỉ vướng việc không ai nhìn thấy chúng.
 *
 * Bảng tóm tắt trả lời "dòng này xong chưa". Tệp này trả lời câu khác hẳn, và là câu mở đầu
 * mỗi vòng: **việc gì đang chờ, và trong đó việc gì tôi tự làm được?**
 *
 * ── HAI CỘT, VÀ VÌ SAO PHẢI TÁCH ────────────────────────────────────────────
 *
 * Gộp chung một danh sách thì thứ chờ khoá R2 nằm cạnh thứ chỉ cần ngồi viết, và cả hai cùng
 * trông như "việc còn lại". Đọc một danh sách như thế thì kết luận tự nhiên là "còn nhiều
 * lắm, chờ anh Sơn đã" — trong khi phần tự làm được có thể đóng ngay trong buổi.
 *
 * Tệp này KHÔNG chấm điểm và không có mã thoát đỏ: nó là bước đọc, không phải bước gác cổng.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = dirname(fileURLToPath(import.meta.url));
const SO = join(GOC, '..', 'docs', 'NGHIEM_THU_TOPHSA.md');

const CHI_LAM_DUOC = process.argv.includes('--lam-duoc');
const DONG = process.argv.includes('--dong')
  ? process.argv[process.argv.indexOf('--dong') + 1] : null;

/**
 * Chữ mở đầu một lời tự thú. Phân biệt HOA / thường có chủ ý: "CHƯA" viết hoa là lời khẳng
 * định tôi cố tình gào lên lúc đo, còn "chưa" thường xuất hiện ở mọi câu bình thường
 * ("chưa ai có điểm", "chưa tới giờ") và bắt nó sẽ chôn danh sách dưới hàng trăm dòng nhiễu.
 */
const DAU_HIEU = [
  'Còn thiếu', 'còn thiếu', 'Còn sót', 'còn sót', 'Còn lại:', 'còn lại:',
  'CHƯA', 'chưa ai', 'không có màn nào', 'chờ khoá', 'chờ anh',
];

/**
 * Câu đã kèm LỜI ĐÓNG thì không còn là việc. Sổ này giữ nguyên câu cũ theo RULES §29 — lời
 * tự thú hôm qua nằm ngay cạnh lời báo đóng hôm nay, trong cùng một ô — nên không lọc chỗ
 * này thì danh sách việc phần lớn là chuyện đã xong, và một danh sách như thế thì đọc vài
 * lượt là thôi đọc.
 */
const DA_DONG = [
  /\bxong\s+\d\d\/\d\d/, /đóng nốt/i, /đã CŨ/, /sửa nhãn/i, /đã vá/i, /nay mỗi tuần/i,
  /^Bộ kiểm/i, /— nay /,
  // Câu ĐÍNH CHÍNH một nhãn cũ: nó CHỨA chữ "CHƯA" trong ngoặc kép để trích lại nhãn sai,
  // nên bản đầu của tệp này bắt luôn chính câu đính chính và báo việc đã đóng là chưa làm
  // (28/09: `nhãn "CHƯA" là nhãn CŨ, sửa 28/09` bị kê vào cột "tôi làm được ngay").
  /là nhãn C[ŨU]/i, /nhãn C[ŨU],/i,
  // RULES §29 bắt GIỮ câu cũ; câu nào tự dẫn ra luật ấy chính là câu đang nói "đoạn dưới
  // đây đã cũ", nên nó là lời đóng chứ không phải việc.
  /RULES §29/,
];

/**
 * Dấu cho biết việc ấy VƯỚNG NGƯỜI KHÁC. Gồm cả mã việc trong `VIEC_CUA_ANH.md` (D1 = khoá
 * Cloudflare R2, D2 = pháp nhân Zalo, E4 = khoá Zoom, Z1 = API Zoom, K2 = khách phải đồng ý)
 * vì nhiều ô chỉ ghi mã chứ không nhắc lại lý do.
 */
const VUONG = [
  /chờ anh/i, /chờ khoá/i, /bộ khoá/i, /chờ khách/i, /chờ TopHSA/i, /chờ pháp nhân/i, /chờ con số/i,
  /anh Sơn chưa quyết/i, /chưa có trả lời/i, /khách phải đồng ý/i,
  /\bR2\b/, /Zoom/, /Zalo/, /\bK2\b/, /\bD1\b/, /\bD2\b/, /\bE4\b/, /\bZ1\b/,
];

const chu = readFileSync(SO, 'utf8').split('\n');

/** Số dòng của bảng phân rã mà một dòng văn bản thuộc về, hoặc null. */
function dongCuaBang(s, cuoi) {
  const bang = s.match(/^\|\s*(\d+)\s*\|/);
  if (bang) return bang[1];
  const tieu = s.match(/^##+\s*Dòng\s+(\d+)/);
  if (tieu) return tieu[1];
  return cuoi;
}

/**
 * Cắt một mẩu đọc được bắt đầu từ chỗ có dấu hiệu. Dừng ở ranh giới câu (`. ` trước chữ hoa),
 * ở `·` hay ở vách ô `|` — cắt cứng theo số ký tự sẽ chặt ngang từ và mất luôn vế quan trọng.
 */
function mau(s, tu) {
  let t = s.slice(tu);
  const het = [t.search(/\.\s+[A-ZĐÀ-Ỹ]/), t.indexOf(' | '), t.indexOf(' · ')]
    .filter((i) => i > 30);
  if (het.length) t = t.slice(0, Math.min(...het) + 1);
  return t.replace(/\*\*/g, '').replace(/`/g, '').trim().slice(0, 240);
}

const thay = [];
let cuoi = null;
chu.forEach((s, i) => {
  cuoi = dongCuaBang(s, cuoi);
  if (s.startsWith('<!--')) return;
  // Ô TRẠNG THÁI của bảng tóm tắt, đọc riêng: `| 5 | Quản trị viên · … | MỘT PHẦN | …`.
  // Một dòng chưa trọn là việc dù không ai viết thêm câu "còn thiếu" nào cho nó — và ô ấy
  // ngắn nên phép lọc độ dài bên dưới sẽ ném nó đi nếu gộp chung.
  const o = s.match(/^\|\s*(\d+)\s*\|([^|]+)\|([^|]+)\|/);
  if (o && /MỘT PHẦN|CHƯA|THAY|gần đủ/.test(o[3])) {
    thay.push({ dong: o[1], taiDong: i + 1, vuong: VUONG.some((r) => r.test(s)),
                mau: `[bảng tóm tắt] ${o[2].trim()} — ${o[3].replace(/\*\*/g, '').trim()}` });
    return;
  }
  // Ô TRẠNG THÁI của bảng CHI TIẾT đã ghi CÓ / XONG: mọi lời "còn thiếu" trong ô bằng chứng
  // bên cạnh là kể lại thứ TỪNG thiếu, không phải việc đang chờ. Bắt chúng thì danh sách việc
  // đầy những câu kiểu "cái còn thiếu chỉ là …" của một ô đã đóng (dòng 4, 28/09).
  // `(\*|\s|$)` chứ KHÔNG `\b`: `\b` của JavaScript chỉ biết `[A-Za-z0-9_]`, nên cạnh chữ "Ó"
  // nó không thấy ranh giới nào và mẫu `(CÓ|XONG)\b` không bao giờ khớp. Im lặng, và chỉ sai
  // với tiếng Việt — đúng loại lỗi sẽ sống lâu trong một sản phẩm viết bằng tiếng Việt.
  const ct = s.match(/^\|([^|]+)\|([^|]+)\|/);
  if (ct && /^\s*\**\s*(CÓ|XONG)(\*|\s|$)/.test(ct[2])) return;
  for (const d of DAU_HIEU) {
    const tu = s.indexOf(d);
    if (tu < 0) continue;
    // Dấu hiệu nằm TRONG ngoặc kép là lời TRÍCH — thường là chính câu anh Sơn nói, hay một
    // nhãn cũ đang được dẫn lại để đính chính. Đếm dấu nháy đứng trước: lẻ là đang ở trong
    // một cặp ngoặc chưa đóng.
    if ((s.slice(0, tu).match(/"/g) || []).length % 2 === 1) continue;
    const m = mau(s, tu);
    if (m.length < 40 || DA_DONG.some((r) => r.test(m))) continue;
    // Cùng một câu hay khớp hai dấu hiệu ("CHƯA" nằm trong "Còn thiếu: … CHƯA …") — giữ bản
    // dài nhất, đừng in một việc hai lần với hai độ dài khác nhau.
    const trung = thay.findIndex((x) => x.taiDong === i + 1);
    if (trung >= 0) {
      if (m.length > thay[trung].mau.length) thay[trung].mau = m;
      continue;
    }
    thay.push({ dong: cuoi, taiDong: i + 1, mau: m, vuong: VUONG.some((r) => r.test(m)) });
  }
});

const loc = thay.filter((x) => (!DONG || x.dong === DONG) && (!CHI_LAM_DUOC || !x.vuong));
const lamDuoc = loc.filter((x) => !x.vuong);
const choNguoi = loc.filter((x) => x.vuong);

function in_ra(ten, ds) {
  if (!ds.length) return;
  console.log(`\n${'─'.repeat(78)}\n  ${ten} — ${ds.length} chỗ\n${'─'.repeat(78)}`);
  for (const x of ds) {
    console.log(`\n  ${x.dong ? `dòng ${x.dong}` : '(ngoài bảng)'}  ·  NGHIEM_THU_TOPHSA.md:${x.taiDong}`);
    console.log(`    ${x.mau}`);
  }
}

in_ra('TÔI LÀM ĐƯỢC NGAY — không vướng ai', lamDuoc);
if (!CHI_LAM_DUOC) in_ra('CHỜ NGƯỜI KHÁC — anh Sơn, khách, hoặc khoá ngoài', choNguoi);

console.log(`\n  Tổng: ${lamDuoc.length} chỗ tự làm được · ${choNguoi.length} chỗ vướng người khác.`);
console.log('  Đây là bước ĐỌC của vòng lặp — không phải cổng kiểm, nên luôn thoát 0.');
