/**
 * Unit test — trang báo cáo phụ huynh KHÔNG được nói "không mở được" khi máy chủ chỉ đang ngủ.
 *
 * ── LỖI ĐANG CHẶN LẠI (28/09/2026) ────────────────────────────────────────
 *
 * `/bc/<chìa>` là đường CÔNG KHAI duy nhất của hệ thống: phụ huynh mở từ một tin Zalo, không
 * tài khoản, không ai gõ cửa đánh thức máy chủ hộ. Đo trên production cùng ngày: lượt gọi đầu
 * khi Render vừa ngủ mất **63–73 giây**.
 *
 * `loading.tsx` đã lo phần CHỜ rất tử tế — khung tờ báo cáo hiện ngay, và sau 6 giây có câu
 * "Máy chủ đang thức dậy…". Nhưng nếu lượt gọi ấy THẤT BẠI (hàm của Vercel hết giờ, mạng đứt),
 * `serverJson` trả `{ ok: false, status: null }` và trang rơi vào đúng một nhánh hỏng, dùng
 * chung với chìa sai / chìa hết hạn / chìa bị thu hồi:
 *
 *     <h1>Không mở được báo cáo này</h1>
 *
 * Bốn chuyện khác hẳn nhau, một câu. Với ba chuyện đầu thì câu ấy đúng: chìa hỏng thật, và
 * phụ huynh nên nhắn giảng viên xin link mới. Với chuyện thứ tư thì nó SAI theo hướng đắt
 * nhất — chìa vẫn tốt, chỉ cần tải lại sau một phút, mà phụ huynh được bảo là link hỏng. Họ
 * đóng tab, nhắn giảng viên "link không vào được", giảng viên cấp chìa mới, chìa mới cũng
 * không vào được vì máy chủ vẫn đang ngủ. Không ai trong chuỗi ấy biết là không có gì hỏng.
 *
 * `status === null` là ĐÚNG thứ phân biệt hai chuyện: `serverJson` chỉ trả `null` khi không
 * với tới máy chủ. Mọi mã HTTP thật (404, 410, 500) đều là số.
 *
 * Kiểm bằng chữ trong nguồn chứ không dựng trang: nhánh này chỉ hiện khi backend thật sự
 * không trả lời, và không bộ đo nào của dự án dựng lại được tình huống ấy trên máy.
 *
 * Chạy: node e2e/unit/bao-cao-may-chu-ngu.test.mjs
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const DUONG = join(GOC, 'src', 'app', '(standalone)', 'bc', '[token]', 'page.tsx');
const NUT = join(GOC, 'src', 'components', 'TaiLaiTrang.tsx');

/** Bỏ chú thích trước khi đo: câu trong chú thích KHÔNG phải câu người đọc thấy, và đếm cả
 *  chúng thì viết một dòng giải thích là làm đỏ phép kiểm của chính mình. */
function boChuThich(ma) {
  return ma.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
}
const MA = boChuThich(readFileSync(DUONG, 'utf8'));

let hong = 0;
function kiem(ten, dung, them) {
  if (dung) console.log('  ✓', ten);
  else {
    console.error('  ✗', ten, them === undefined ? '' : '→ ' + them);
    hong++;
  }
}

console.log('Trang /bc/<chìa> — máy chủ ngủ KHÁC chìa hỏng');

// 1 · Có nhánh riêng cho "không với tới máy chủ".
kiem('phân biệt status === null (không với tới máy chủ)',
     /kq\.status\s*===\s*null/.test(MA),
     'không thấy phép so `kq.status === null` — mọi lỗi đang đi chung một nhánh');

// 2 · Nhánh ấy KHÔNG được mang tiêu đề của nhánh chìa hỏng.
const soLanCauChiaHong = (MA.match(/Không mở được báo cáo này/g) || []).length;
kiem('câu "Không mở được báo cáo này" chỉ dùng cho chìa hỏng, đúng MỘT chỗ',
     soLanCauChiaHong === 1, `đếm được ${soLanCauChiaHong} chỗ`);

// Nhánh máy chủ ngủ: từ phép so `status === null` tới chỗ nhánh chìa-hỏng bắt đầu.
const dau = MA.search(/kq\.status\s*===\s*null/);
const cuoi = MA.indexOf('if (!kq.ok)', dau);
const khoiNgu = MA.slice(dau, cuoi > dau ? cuoi : undefined);

// 3 · Nhánh ấy phải nói ra HAI điều: chìa vẫn dùng được, và nên làm gì.
kiem('nói rõ đường dẫn VẪN dùng được',
     /vẫn dùng được|chưa hỏng|không hỏng|vẫn còn dùng/.test(khoiNgu),
     'phụ huynh phải biết đây không phải link chết, nếu không họ đi xin link mới');
kiem('có nút tải lại thật, không chỉ một câu "thử lại sau"',
     /<TaiLaiTrang\s*\/>/.test(khoiNgu)
     && /Tải lại trang/.test(boChuThich(readFileSync(NUT, 'utf8'))),
     'nói "thử lại sau" mà không có nút thì người ta đóng tab');

// 4 · Máy chủ ngủ KHÔNG phải lỗi của người đọc — đừng bảo họ đi nhắn giảng viên NGAY.
//    Câu ấy đúng cho chìa sai / hết hạn / thu hồi, và chỉ đúng ở đây SAU KHI đã chờ.
// Đo CHỈ THỊ, không đo chữ. Nói "KHÔNG CẦN xin đường dẫn mới" là đúng ý nhất — bản đầu của
// phép kiểm này cấm nguyên cụm "đường dẫn mới" nên chấm đỏ đúng câu tốt nhất viết ra được.
const nhacXin = [...khoiNgu.matchAll(/đường dẫn mới/g)]
  .filter((m) => !/không cần/i.test(khoiNgu.slice(Math.max(0, m.index - 40), m.index)));
kiem('nhánh máy chủ ngủ KHÔNG bảo đi xin đường dẫn mới',
     nhacXin.length === 0,
     'chìa vẫn tốt — bảo đi xin link mới là đẩy cả giảng viên vào việc thừa');

console.log(hong === 0 ? `\n${'ĐẠT'} — 5/5` : `\nHỎNG — ${hong} phép kiểm`);
process.exit(hong === 0 ? 0 : 1);
