/**
 * HỒ SƠ SẢN PHẨM gửi TopHSA — sinh ra tệp PDF.
 *
 * ── VÌ SAO SINH BẰNG MÃ, KHÔNG GÕ TAY MỘT TỆP .docx ────────────────────────
 *
 * Hồ sơ này có rất nhiều CON SỐ: bao nhiêu vai trò, bao nhiêu đường API, bao
 * nhiêu bảng, bao nhiêu học viên thật. Gõ tay xong là nó bắt đầu sai dần, và
 * một hồ sơ gửi đối tác mà nói sai số thì hỏng đúng thứ nó sinh ra để làm.
 *
 * Nên: `scripts/kiem_ke_san_pham.py` đọc thẳng mã nguồn + CSDL ra `ho_so.json`,
 * tệp này đọc JSON ấy rồi dựng trang. Chạy lại lệnh là hồ sơ đúng lại.
 *
 *     python scripts/kiem_ke_san_pham.py --ra ho_so.json
 *     node   scripts/ho_so_tophsa.mjs ho_so.json "Ho so PE_HSA.pdf"
 *
 * ── VÌ SAO HTML → PDF CHỨ KHÔNG PHẢI reportlab ─────────────────────────────
 *
 * `teaching/bao_cao_pdf.py` dùng reportlab vì tờ báo cáo ấy do MÁY CHỦ sinh ra
 * cho từng phụ huynh, và máy chủ trên Render không nên kèm cả một Chromium.
 *
 * Hồ sơ này thì khác hẳn: sinh MỘT LẦN, trên máy người viết, và nó cần thứ
 * reportlab làm rất tệ — sơ đồ. Mermaid vẽ được use case, C4 và luồng hoạt
 * động bằng vài dòng chữ; vẽ ngần ấy sơ đồ bằng toạ độ tay là việc vài ngày và
 * sửa một mũi tên là vẽ lại.
 *
 * ── BA ĐIỀU VỀ CHỮ TRONG HỒ SƠ NÀY ─────────────────────────────────────────
 *
 * 1. Người đọc KHÔNG phải lập trình viên. Không có tên hàm, tên bảng, tên lớp
 *    trong phần A và B; chúng chỉ xuất hiện ở phần C, đúng chỗ bên kỹ thuật
 *    cần đối chiếu.
 * 2. Mỗi con số đi kèm NGÀY ĐO. "3 học viên" hôm nay và "300 học viên" sáu
 *    tháng nữa là hai câu khác nhau, và người đọc lại hồ sơ sau cần biết mình
 *    đang đọc ảnh chụp của lúc nào.
 * 3. Nói thẳng chỗ CHƯA CÓ. Một hồ sơ chỉ kể phần đã xong sẽ khiến bên kia lập
 *    kế hoạch trên nền không có thật, và họ sẽ phát hiện ra vào đúng lúc tệ nhất.
 */
import { chromium } from 'file:///D:/pe_hsa/frontend/node_modules/.pnpm/playwright@1.61.1/node_modules/playwright/index.mjs';
import fs from 'node:fs';
import path from 'node:path';

const [, , nguonJson, raPdf] = process.argv;
if (!nguonJson) {
  console.error('Dùng: node scripts/ho_so_tophsa.mjs <ho_so.json> [ra.pdf]');
  process.exit(1);
}
const D = JSON.parse(fs.readFileSync(nguonJson, 'utf8'));
const RA = path.resolve(raPdf || 'Ho so san pham PE_HSA.pdf');

const NGAY = new Date(D.ngayDo + 'T00:00:00').toLocaleDateString('vi-VN', {
  day: '2-digit', month: '2-digit', year: 'numeric',
});
const S = D.soLieu;
const API = D.api;
const soCong = (ten) => API.coCong.filter((r) => r.quyen.join('+') === ten).length;
const soBangCoDuLieu = D.bang.filter((b) => (b.dong || 0) > 0).length;

/* ── mảnh dựng trang ────────────────────────────────────────────────────── */
const esc = (s) => String(s ?? '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const muc = (so, ten) => `<h2 id="m${so.replace(/\./g, '-')}"><span class="so">${so}</span> ${ten}</h2>`;
const so = (n) => (n === null || n === undefined ? '—' : String(n));
const bang = (dau, hang) => `<table><thead><tr>${dau.map((h) => `<th>${h}</th>`).join('')}</tr></thead>`
  + `<tbody>${hang.map((r) => `<tr>${r.map((c, i) => `<td${i ? '' : ' class="dau"'}>${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
const mer = (chu) => `<div class="so-do"><pre class="mermaid">${esc(chu)}</pre></div>`;
const ghi = (t) => `<p class="ghi">${t}</p>`;
const canh = (t) => `<p class="canh">${t}</p>`;
const trang = () => '<div class="ngat"></div>';

/* ═══════════════════════════════════════════════════════════════════════════
   NỘI DUNG
   ═══════════════════════════════════════════════════════════════════════════ */

const BIA = `
<section class="bia">
  <p class="nhan">Hồ sơ sản phẩm</p>
  <h1>Hệ thống quản lý học tập<br>và vận hành trung tâm</h1>
  <p class="phu">Xây dựng cho TopHSA · luyện thi Đánh giá năng lực HSA</p>
  <div class="bia-so">
    <div><b>${so(S.baiHoc)}</b><span>bài học đã soạn</span></div>
    <div><b>${so(S.khoaHoc)}</b><span>hợp phần HSA</span></div>
    <div><b>${D.vaiTro.danhSach.length}</b><span>vai trò người dùng</span></div>
    <div><b>${D.trang.length}</b><span>màn hình</span></div>
  </div>
  <p class="bia-chan">Số liệu đo trực tiếp trên hệ thống ngày <b>${NGAY}</b>.<br>
     Tài liệu này sinh tự động từ chính mã nguồn và cơ sở dữ liệu — không gõ tay.</p>
</section>`;

const MUC_LUC = `
<section>
  <h2 class="khong-so">Mục lục</h2>
  <p class="dan">Tài liệu chia ba phần đọc độc lập được. Không ai phải đọc hết.</p>
  <table class="ml">
    <tr><td class="ml-p">PHẦN A</td><td><b>Cho ban lãnh đạo</b> — sản phẩm là gì, khác gì hệ thống khảo thí đang dùng, cần quyết những gì. <i>Đọc 10 phút.</i></td></tr>
    <tr><td class="ml-p">PHẦN B</td><td><b>Cho học vụ và giảng viên</b> — ai làm được gì, từng luồng thao tác, màn hình nào ở đâu.</td></tr>
    <tr><td class="ml-p">PHẦN C</td><td><b>Cho bên kỹ thuật</b> — kiến trúc, mô hình dữ liệu, phân quyền, điểm nối hệ thống.</td></tr>
    <tr><td class="ml-p">PHẦN D</td><td><b>Cần gì từ TopHSA</b> — dữ liệu, thông tin, quyết định. Mỗi mục ghi rõ nó đang chặn việc gì.</td></tr>
    <tr><td class="ml-p">PHẦN E</td><td><b>Làm tiếp được ngay</b> — những việc không phải chờ TopHSA.</td></tr>
  </table>
</section>`;

/* ── PHẦN A ─────────────────────────────────────────────────────────────── */
const PHAN_A = `
<section class="phan"><p class="phan-nhan">Phần A</p><h1 class="phan-ten">Cho ban lãnh đạo</h1>
<p class="phan-mo">Phần này trả lời ba câu: sản phẩm này làm được gì cho trung tâm, nó khác gì
hệ thống khảo thí TopHSA đang dùng, và TopHSA cần quyết những gì để đi tiếp.</p></section>

${muc('A.1', 'Sản phẩm này là gì')}
<p>Đây là <b>phần mềm vận hành trung tâm</b> — thứ nằm giữa lúc một học viên ghi danh và
lúc em ấy đi thi. Nó trả lời những câu mà một trung tâm phải trả lời mỗi ngày:</p>
<ul class="to">
  <li><b>Em ấy có đi học không?</b> Điểm danh từng buổi, và phân biệt rõ "vắng" với "giảng viên chưa tick".</li>
  <li><b>Em ấy học tới đâu?</b> Bao nhiêu bài đã xong trên tổng số, theo từng hợp phần HSA.</li>
  <li><b>Em ấy yếu chỗ nào?</b> Đo theo từng chủ đề, không phải một điểm trung bình chung.</li>
  <li><b>Phụ huynh biết gì?</b> Mỗi kỳ một tờ báo cáo, gửi qua email, kèm bản PDF in được.</li>
  <li><b>Trung tâm nhìn thấy gì?</b> Bảng điều khiển toàn trung tâm, và cơ sở tính học phí theo buổi.</li>
</ul>
${ghi('Sản phẩm còn có phần <b>tự học</b> cho học viên: 76 bài đã soạn, ba hợp phần HSA, kèm thi thử và lộ trình cá nhân.')}

${muc('A.2', 'Khác gì hệ thống khảo thí TopHSA đang dùng')}
<p>Hai hệ thống làm hai việc khác nhau, và chỗ chồng lấn rất nhỏ.</p>
${bang(['', 'Hệ thống khảo thí hiện tại', 'Hệ thống này'], [
  ['<b>Trả lời câu hỏi</b>', 'Bài thi này em làm được bao nhiêu điểm?', 'Em này học hành thế nào trong suốt khoá?'],
  ['<b>Đơn vị thời gian</b>', 'Một buổi thi', 'Cả một đợt học, nhiều tuần'],
  ['<b>Nắm giữ</b>', 'Ngân hàng câu hỏi, ma trận đề, tổ chức thi, giám sát', 'Lớp học, buổi học, điểm danh, giáo trình, học phí, báo cáo phụ huynh'],
  ['<b>Người dùng chính</b>', 'Cán bộ khảo thí', 'Học vụ, giảng viên, học viên, phụ huynh'],
])}
${canh('<b>Khuyến nghị:</b> không làm lại ngân hàng câu hỏi và ma trận đề ở bên này. Hệ thống khảo thí đã có, và làm lại là tốn hai lần cho cùng một việc. Thứ nên nối là <b>kết quả thi</b> — xem Phần D.')}

${muc('A.3', 'Hiện trạng — đo ngày ' + NGAY)}
<p>Bảng dưới là ảnh chụp thật của hệ thống, không phải kế hoạch.</p>
${bang(['Hạng mục', 'Số lượng', 'Ý nghĩa'], [
  ['Bài học đã soạn', `<b>${so(S.baiHoc)}</b>`, `Chia cho ${so(S.khoaHoc)} hợp phần HSA. Nội dung đã nằm trong hệ thống, học được ngay.`],
  ['Màn hình', `<b>${D.trang.length}</b>`, 'Đã dựng và chạy được, không phải bản vẽ.'],
  ['Vai trò người dùng', `<b>${D.vaiTro.danhSach.length}</b>`, 'Mỗi vai thấy đúng phần việc của mình.'],
  ['Tài khoản đang có', `<b>${so(S.taiKhoan)}</b>`, `Trong đó ${so(S.hocVien)} học viên. Đây là môi trường chạy thật, chưa mở rộng.`],
  ['Lớp học', `<b>${so(S.lop)}</b>`, `Một lớp mẫu, ${so(S.buoiHoc)} buổi, ${so(S.diemDanh)} lượt điểm danh.`],
  ['Liên lạc phụ huynh đã khai', `<b>${so(S.coEmailPhuHuynh)}</b>`, 'Chưa em nào. Đây là thứ chặn việc gửi báo cáo — xem Phần D.'],
])}
${canh('<b>Đọc bảng này cho đúng:</b> phần <i>chức năng</i> đã dựng xong và kiểm kỹ; phần <i>dữ liệu</i> mới có một lớp mẫu. Hệ thống chưa từng chạy với một lớp thật của TopHSA — và đó chính là bước tiếp theo.')}

${muc('A.4', 'Bốn việc cần TopHSA quyết')}
${bang(['#', 'Việc', 'Đang chặn điều gì'], [
  ['1', '<b>Cho một lớp thật chạy thử</b> — một lớp, một giảng viên, một đợt', 'Không có lớp thật thì không biết luồng nào vướng khi dùng hàng ngày.'],
  ['2', '<b>Địa chỉ email của trung tâm</b> (dạng <i>tên@tophsa.vn</i>)', 'Báo cáo phụ huynh đã dựng xong nhưng chưa gửi được dưới danh nghĩa trung tâm.'],
  ['3', '<b>Cách lấy kết quả thi thử</b> từ hệ thống khảo thí', 'Ô "điểm thi thử" trong báo cáo phụ huynh đang trống.'],
  ['4', '<b>Quy trình thu học phí thật</b>', 'Hệ thống mới dựng phần đếm buổi; chưa dựng phần tiền vì chưa biết quy trình.'],
])}
<p>Chi tiết từng mục ở <b>Phần D</b>.</p>
${trang()}`;

/* ── PHẦN B ─────────────────────────────────────────────────────────────── */
const PHAN_B = `
<section class="phan"><p class="phan-nhan">Phần B</p><h1 class="phan-ten">Cho học vụ và giảng viên</h1>
<p class="phan-mo">Ai làm được gì, và mỗi việc đi qua những màn hình nào.</p></section>

${muc('B.1', 'Sáu vai trò')}
<p>Nguyên tắc xuyên suốt: <b>quyền theo ngữ cảnh, không theo chức danh</b>. "Được xem lớp này"
nghĩa là "tôi có phụ trách lớp này", chứ không phải "tôi là giảng viên nên xem được mọi lớp".</p>
${bang(['Vai trò', 'Thấy gì', 'Làm được gì', 'KHÔNG làm được'], [
  ['<b>Quản trị viên</b>', 'Toàn bộ', 'Mọi việc: tài khoản, vai trò, lớp, đợt, giáo trình, báo cáo', '—'],
  ['<b>Quản lý học vụ</b>', 'Mọi lớp', 'Quản lý lớp và đợt học, xem báo cáo lớp', 'Đổi vai trò · đặt lại mật khẩu · mở báo cáo phụ huynh'],
  ['<b>Giảng viên</b>', 'Lớp mình phụ trách', 'Buổi học, điểm danh, giao bài, chấm, <b>gửi báo cáo phụ huynh</b>', 'Lớp của người khác'],
  ['<b>Trợ giảng</b>', 'Lớp được gán', 'Điểm danh, chấm bài', 'Xoá buổi · mở báo cáo phụ huynh · tải file có cột liên lạc'],
  ['<b>Học viên</b>', 'Dữ liệu của chính mình', 'Học, thi thử, xem lộ trình và bản đồ năng lực', 'Dữ liệu của bạn học'],
  ['<b>Biên tập nội dung</b>', 'Giáo trình', 'Soạn bài, nhập đề thi thử', 'Lớp học · học viên · báo cáo'],
])}
${canh('<b>Ranh giới về dữ liệu liên lạc:</b> trợ giảng <i>nhìn được</i> email học viên trên màn điểm danh và chấm bài (vì có em chưa điền tên, email là thứ duy nhất để biết đang tick cho ai), nhưng <i>không mang ra ngoài được</i> — báo cáo phụ huynh bị chặn, và hai tệp CSV của lớp bị bỏ cột email và số điện thoại.')}

${muc('B.2', 'Ai làm được việc gì — sơ đồ')}
${mer(`flowchart TB
  subgraph h["HỌC VIÊN"]
    direction LR
    u1["Học bài · làm quiz"]
    u2["Thi thử · xem kết quả"]
    u3["Xem lộ trình và<br/>điểm mạnh yếu"]
    u4["Khai liên lạc<br/>phụ huynh"]
  end
  subgraph d["GIẢNG DẠY — giảng viên và trợ giảng"]
    direction LR
    u5["Điểm danh"]
    u6["Chấm bài"]
    u7["Mở · huỷ buổi<br/><i>chỉ giảng viên</i>"]
    u8["Giao bài<br/><i>chỉ giảng viên</i>"]
    u10["Gửi báo cáo phụ huynh<br/><i>chỉ giảng viên</i>"]
  end
  subgraph v["VẬN HÀNH — học vụ và quản trị viên"]
    direction LR
    u11["Tạo lớp · tạo đợt"]
    u12["Xếp học viên"]
    u9["Xem báo cáo lớp"]
    u15["Tài khoản và vai trò<br/><i>chỉ quản trị viên</i>"]
    u17["Cơ sở học phí<br/><i>chỉ quản trị viên</i>"]
  end
  subgraph n["NỘI DUNG"]
    direction LR
    u13["Soạn giáo trình"]
    u14["Nhập đề thi thử"]
  end
  subgraph p["PHỤ HUYNH — không cần tài khoản"]
    u18["Mở báo cáo bằng đường dẫn<br/>gửi trong email"]
  end`)}
${ghi('Phụ huynh <b>không có tài khoản</b>. Họ mở báo cáo bằng một đường dẫn riêng, có hạn dùng và thu hồi được — đây là quyết định có chủ ý, để không phải quản lý thêm một loại tài khoản nữa.')}
${trang()}

${muc('B.3', 'Luồng 1 — Mở lớp và dạy')}
${mer(`flowchart TD
  A["Học vụ tạo ĐỢT HỌC<br/>(ví dụ: Đợt 1/2027)"] --> B["Tạo LỚP, gán giảng viên"]
  B --> C["Xếp học viên vào lớp"]
  C --> D["Mở BUỔI HỌC theo lịch"]
  D --> E{"Buổi diễn ra"}
  E --> F["Giảng viên ĐIỂM DANH<br/>có mặt · muộn · vắng · có phép"]
  E --> G["Ghi sổ đầu bài:<br/>hôm nay dạy tới đâu"]
  F --> H["Hệ thống đánh dấu<br/>buổi này ĐÃ điểm danh"]
  H --> I["Báo cáo lớp và báo cáo<br/>phụ huynh tự cập nhật"]`)}
<p><b>Một chi tiết quan trọng:</b> hệ thống phân biệt <b>"em vắng"</b> với <b>"giảng viên chưa tick"</b>.
Buổi chưa điểm danh không bao giờ bị tính thành buổi vắng của học viên — nó được báo riêng
là việc còn tồn của giảng viên. Gộp hai thứ này là vu cho học viên một buổi nghỉ, và lời
buộc tội ấy đi thẳng về nhà trong tờ báo cáo.</p>

${muc('B.4', 'Luồng 2 — Báo cáo phụ huynh')}
${mer(`flowchart TD
  A["Giảng viên mở màn<br/>Báo cáo phụ huynh của lớp"] --> B["Hệ thống SOẠN SẴN:<br/>ai nhận được, ai thiếu liên lạc"]
  B --> C{"Giảng viên<br/>xem lại và bấm Gửi"}
  C -->|"Có email phụ huynh"| D["Gửi email:<br/>tóm tắt + PDF đính kèm + đường dẫn"]
  C -->|"Chưa khai liên lạc"| E["Chỉ cấp đường dẫn<br/>để gửi tay"]
  D --> F["Ghi vào SỔ GỬI:<br/>gửi cho ai, lúc nào, thành công không"]
  F --> G["Phụ huynh mở đường dẫn<br/>trên điện thoại, không cần đăng nhập"]`)}
<p>Ba phần trong một lá thư, mỗi phần một việc:</p>
${bang(['Phần', 'Nội dung', 'Vì sao có'], [
  ['<b>Tóm tắt</b> trong thư', 'Chuyên cần, số bài đã xong, điểm thi thử, hai chủ đề yếu nhất', 'Phụ huynh mở thư trên điện thoại giữa lúc bận và thường không bấm gì thêm.'],
  ['<b>PDF đính kèm</b>', 'Bản đầy đủ 5 mục, in ra được', 'Mang đi họp được, và còn nguyên khi đường dẫn đã hết hạn.'],
  ['<b>Đường dẫn</b>', 'Bản luôn cập nhật', 'Điểm danh sửa sau khi gửi thì đường dẫn hiện số đúng. Thư nói rõ khác biệt này.'],
])}
${canh('<b>Không có gì tự động bắn đi.</b> Mỗi lượt gửi cần một cái gật của con người. Một tin đã tới phụ huynh thì không thu về được, nên hệ thống hỏi lại kèm <i>đúng số người sẽ nhận</i> — không hỏi "bạn có chắc không".')}
${trang()}

${muc('B.5', 'Luồng 3 — Học viên học và thi thử')}
${mer(`flowchart TD
  A["Học viên đăng nhập"] --> B["Trang của tôi:<br/>hôm nay học gì"]
  B --> C["Vào bài học"]
  C --> D["Làm quiz cuối bài"]
  D --> E["Hệ thống ghi nhận:<br/>bài xong, chủ đề nào đã chạm"]
  E --> F["Bản đồ năng lực cập nhật<br/>theo TỪNG CHỦ ĐỀ"]
  F --> G["Lộ trình đề xuất bài tiếp theo"]
  B --> H["Thi thử bấm giờ"]
  H --> I["Kết quả theo ba hợp phần"]
  I --> F`)}
${ghi('Năng lực đo <b>theo từng chủ đề</b>, không quy thành một điểm trung bình. Bình quân hoá 20 chủ đề thành một con số sẽ che mất đúng thông tin dùng được — "em yếu ở Số học" — và đẻ ra một con số thứ hai không khớp bản đồ mà chính em ấy nhìn thấy.')}

${muc('B.6', 'Luồng 4 — Soạn giáo trình và nhập đề')}
${mer(`flowchart LR
  A["Biên tập nội dung"] --> B["Soạn bài trực tiếp<br/>trên màn Soạn giáo trình"]
  A --> C["Tải mẫu .xlsx"]
  C --> D["Điền: mỗi dòng một câu hỏi"]
  D --> E["Tải lên"]
  E --> F{"Hệ thống KIỂM<br/>trước khi ghi"}
  F -->|"Có dòng sai"| G["Báo đúng số dòng như trong Excel.<br/>KHÔNG dòng nào được ghi."]
  F -->|"Sạch"| H["Xem trước rồi mới nhập"]`)}
${ghi('Nguyên tắc "một dòng sai thì không dòng nào được ghi" là có chủ ý: nhập một nửa rồi hỏng là trạng thái khó dọn nhất — người dùng không biết đã vào tới đâu.')}

${muc('B.7', `Toàn bộ ${D.trang.length} màn hình`)}
${bang(['Màn hình', 'Ai vào được', 'Làm gì ở đó'], [
  ['Trang giới thiệu', 'Bất kỳ ai', 'Giới thiệu trung tâm, thử ba câu hỏi mẫu, xem tờ báo cáo mẫu'],
  ['Đăng nhập', 'Bất kỳ ai', 'Đăng nhập bằng email hoặc số điện thoại'],
  ['Báo cáo phụ huynh', 'Người có đường dẫn', 'Xem báo cáo học tập của con — không cần tài khoản'],
  ['Trang của tôi', 'Học viên', 'Hôm nay học gì, tiến độ, chuỗi ngày học, ba hợp phần'],
  ['Danh sách khoá', 'Học viên', 'Ba hợp phần HSA, chọn khoá để vào'],
  ['Chi tiết khoá', 'Học viên', 'Danh sách bài, tiến độ từng bài'],
  ['Bài học', 'Học viên', 'Học nội dung, làm quiz cuối bài'],
  ['Thi thử', 'Học viên', 'Làm đề bấm giờ, xem kết quả theo hợp phần'],
  ['Bài tập của tôi', 'Học viên', 'Bài giảng viên giao, nộp bài'],
  ['Khảo sát', 'Học viên', 'Khảo sát đầu vào để dựng lộ trình'],
  ['Đổi mật khẩu', 'Mọi người đã đăng nhập', 'Đổi mật khẩu của chính mình'],
  ['Buổi học &amp; điểm danh', 'Giảng viên · trợ giảng', 'Mở buổi, điểm danh, ghi sổ đầu bài, xuất tệp'],
  ['Bài tập của lớp', 'Giảng viên · trợ giảng', 'Giao bài, xem ai đã nộp'],
  ['Chấm bài', 'Giảng viên · trợ giảng', 'Đọc bài làm, chấm điểm, nhận xét'],
  ['Báo cáo cả lớp', 'Giảng viên · học vụ', 'Bảng điều khiển lớp, gửi báo cáo phụ huynh, xuất Excel và PDF'],
  ['Tờ báo cáo một em', 'Giảng viên', 'Xem đúng tờ phụ huynh sẽ nhận, cấp và thu hồi đường dẫn'],
  ['Tổng quan trung tâm', 'Quản trị · học vụ', 'Số liệu toàn trung tâm: lớp, học viên, tiến độ, cảnh báo'],
  ['Tài khoản', 'Quản trị viên', 'Tạo tài khoản, đổi vai trò, khoá, đặt lại mật khẩu'],
  ['Lớp học', 'Quản trị · học vụ', 'Tạo lớp, gán giảng viên, xếp học viên'],
  ['Đợt học', 'Quản trị · học vụ', 'Tạo đợt, gắn lớp vào đợt'],
  ['Nhật ký kiểm toán', 'Quản trị viên', 'Ai đã sửa gì, lúc nào, từ đâu'],
  ['Ai làm được gì', 'Quản trị viên', 'Sơ đồ phân quyền sinh từ chính mã nguồn'],
  ['Cơ sở học phí', 'Quản trị viên', 'Số buổi từng em trong kỳ — cơ sở để tính tiền'],
  ['Hướng dẫn', 'Quản trị viên', 'Tài liệu dùng hệ thống, viết cho người không rành máy tính'],
  ['Soạn giáo trình', 'Biên tập nội dung', 'Viết bài, sắp thứ tự, gắn chủ đề'],
  ['Nhập đề thi thử', 'Biên tập nội dung', 'Tải mẫu Excel, điền, tải lên, xem trước rồi mới ghi'],
])}

${muc('B.8', 'Ma trận phân quyền chi tiết')}
<p>Dấu <b>&#10003;</b> = làm được. Ô trống = không. Đây là bản đọc được bằng mắt của
thứ hệ thống thực sự chặn ở máy chủ, không phải một bản mô tả riêng.</p>
${bang(['Việc', 'Quản trị', 'Học vụ', 'Giảng viên', 'Trợ giảng', 'Học viên', 'Biên tập'], [
  ['Học bài · thi thử', '&#10003;', '', '', '', '&#10003;', ''],
  ['Xem dữ liệu của chính mình', '&#10003;', '&#10003;', '&#10003;', '&#10003;', '&#10003;', '&#10003;'],
  ['Điểm danh buổi học', '&#10003;', '&#10003;', '&#10003;', '&#10003;', '', ''],
  ['Chấm bài', '&#10003;', '&#10003;', '&#10003;', '&#10003;', '', ''],
  ['Mở · huỷ buổi học', '&#10003;', '&#10003;', '&#10003;', '', '', ''],
  ['Giao bài cho lớp', '&#10003;', '&#10003;', '&#10003;', '', '', ''],
  ['Xem báo cáo lớp', '&#10003;', '&#10003;', '&#10003;', '&#10003;', '', ''],
  ['<b>Mở báo cáo phụ huynh</b>', '&#10003;', '', '&#10003;', '', '', ''],
  ['<b>Tải tệp có cột liên lạc</b>', '&#10003;', '&#10003;', '&#10003;', '', '', ''],
  ['Tạo lớp · tạo đợt học', '&#10003;', '&#10003;', '', '', '', ''],
  ['Xếp học viên vào lớp', '&#10003;', '&#10003;', '', '', '', ''],
  ['Soạn giáo trình · nhập đề', '&#10003;', '', '', '', '', '&#10003;'],
  ['<b>Đổi vai trò tài khoản</b>', '&#10003;', '', '', '', '', ''],
  ['<b>Đặt lại mật khẩu người khác</b>', '&#10003;', '', '', '', '', ''],
  ['Xem nhật ký kiểm toán', '&#10003;', '', '', '', '', ''],
  ['Xem cơ sở tính học phí', '&#10003;', '', '', '', '', ''],
])}
${ghi('Ba dòng in đậm là ba ranh giới được cân nhắc kỹ nhất, vì chúng chạm dữ liệu liên lạc của trẻ em hoặc chạm chính hệ thống phân quyền.')}
${canh('Với giảng viên và trợ giảng, dấu &#10003; luôn kèm điều kiện <b>"của lớp mình phụ trách"</b>. Không có ô nào nghĩa là "mọi lớp".')}
${trang()}`;

/* ── PHẦN C ─────────────────────────────────────────────────────────────── */
const PHAN_C = `
<section class="phan"><p class="phan-nhan">Phần C</p><h1 class="phan-ten">Cho bên kỹ thuật</h1>
<p class="phan-mo">Kiến trúc, dữ liệu, phân quyền, và điểm nối với hệ thống khảo thí.</p></section>

${muc('C.1', 'C4 mức 1 — Bức tranh chung')}
${mer(`flowchart TB
  subgraph nguoi["Người dùng"]
    HV["Học viên"]
    GV["Giảng viên · Trợ giảng"]
    HVU["Học vụ · Quản trị viên"]
    PH["Phụ huynh"]
  end

  HT["<b>Hệ thống quản lý học tập</b><br/>(sản phẩm này)<br/>Lớp · điểm danh · giáo trình<br/>báo cáo · học phí"]

  KT["<b>Hệ thống khảo thí</b><br/>(TopHSA đang dùng)<br/>Ngân hàng câu hỏi · ma trận đề<br/>tổ chức thi · giám sát"]
  MAIL["<b>Dịch vụ gửi thư</b><br/>email tới phụ huynh"]
  ZALO["<b>Zalo OA</b><br/><i>chưa nối — cần xác thực doanh nghiệp</i>"]

  HV --> HT
  GV --> HT
  HVU --> HT
  HT -->|"gửi báo cáo"| MAIL
  MAIL --> PH
  PH -->|"mở đường dẫn"| HT
  HT -.->|"CHƯA NỐI:<br/>cần kết quả thi"| KT
  HT -.-> ZALO

  style KT stroke-dasharray: 5 5
  style ZALO stroke-dasharray: 5 5`)}
${canh('Hai đường nét đứt là hai chỗ <b>chưa nối</b>. Đường tới hệ thống khảo thí là mục quan trọng nhất trong Phần D.')}

${muc('C.2', 'C4 mức 2 — Các khối bên trong')}
${mer(`flowchart TB
  subgraph tt["Trình duyệt người dùng"]
    WEB["<b>Giao diện web</b><br/>Next.js / React<br/>${D.trang.length} màn hình"]
  end

  subgraph mc["Máy chủ"]
    API["<b>Tầng API</b><br/>Django REST<br/>${API.tong} đường"]
    CONG["<b>Tầng phân quyền</b><br/>${D.vaiTro.lopQuyen.length} lớp cổng<br/>+ kiểm theo ngữ cảnh lớp"]
    NV["<b>Tầng nghiệp vụ</b><br/>báo cáo · năng lực · điểm danh<br/>học phí · gửi thư"]
    PDF["<b>Bộ dựng PDF</b><br/>báo cáo phụ huynh<br/>báo cáo lớp"]
  end

  DB[("<b>Cơ sở dữ liệu</b><br/>PostgreSQL<br/>${D.bang.length} bảng")]
  SMTP["Dịch vụ gửi thư"]

  WEB -->|"HTTPS"| API
  API --> CONG
  CONG --> NV
  NV --> DB
  NV --> PDF
  PDF --> SMTP`)}
${bang(['Khối', 'Trách nhiệm', 'Con số'], [
  ['Giao diện web', 'Trình bày; không tự quyết quyền — mọi cổng nằm ở máy chủ', `${D.trang.length} màn hình`],
  ['Tầng API', 'Nhận yêu cầu, trả dữ liệu', `${API.tong} đường`],
  ['Tầng phân quyền', 'Chặn trước khi chạm dữ liệu', `${D.vaiTro.lopQuyen.length} lớp cổng`],
  ['Tầng nghiệp vụ', 'Toàn bộ phép tính; chỉ MỘT nơi tính mỗi con số', '—'],
  ['Cơ sở dữ liệu', 'Nguồn sự thật duy nhất', `${D.bang.length} bảng, ${soBangCoDuLieu} bảng có dữ liệu`],
])}
${trang()}

${muc('C.3', 'C4 mức 3 — Bên trong khối Báo cáo phụ huynh')}
<p>Chọn khối này để vẽ sâu vì nó chạm nhiều thứ nhất: dữ liệu học tập, điểm danh,
phân quyền, gửi ra ngoài, và quyền riêng tư của một đứa trẻ.</p>
${mer(`flowchart TB
  subgraph vao["Đầu vào"]
    DD["Điểm danh<br/>của lớp"]
    HT2["Tiến độ học<br/>của từng em"]
    NL["Bản đồ năng lực<br/>theo chủ đề"]
    TT["Kết quả thi thử"]
  end

  DUNG["<b>Bộ dựng báo cáo</b><br/>một hàm duy nhất<br/>dùng chung cho MỌI đường ra"]

  subgraph ra["Bốn đường ra"]
    MH["Màn hình giảng viên"]
    CHIA["Đường dẫn cho phụ huynh<br/>(có hạn dùng · thu hồi được)"]
    PDF2["Tệp PDF đính kèm"]
    MAIL2["Thư điện tử"]
  end

  SO[("Sổ gửi:<br/>ai · lúc nào · kênh nào<br/>thành công hay lỗi")]

  DD --> DUNG
  HT2 --> DUNG
  NL --> DUNG
  TT -.->|"đang trống —<br/>chờ nối khảo thí"| DUNG
  DUNG --> MH
  DUNG --> CHIA
  DUNG --> PDF2
  PDF2 --> MAIL2
  MAIL2 --> SO

  style TT stroke-dasharray: 5 5`)}
${ghi('<b>Một bộ dựng, bốn đường ra.</b> Nếu mỗi đường tự dựng lấy số liệu thì bốn bản sẽ trôi khỏi nhau, và bản gửi phụ huynh sẽ nói khác bản giảng viên nhìn thấy — không ai biết bản nào đúng.')}

${muc('C.4', 'Mô hình dữ liệu')}
<p>${D.bang.length} bảng, nhóm theo chủ đề. Chỉ nêu nhóm, không liệt kê từng cột.</p>
${mer(`erDiagram
  NGUOI_DUNG ||--o{ THANH_VIEN_LOP : "thuộc"
  LOP ||--o{ THANH_VIEN_LOP : "gồm"
  DOT_HOC ||--o{ LOP : "chứa"
  LOP ||--o{ BUOI_HOC : "có"
  BUOI_HOC ||--o{ DIEM_DANH : "ghi"
  NGUOI_DUNG ||--o{ DIEM_DANH : "của"
  KHOA_HOC ||--o{ BAI_HOC : "gồm"
  NGUOI_DUNG ||--o{ SU_KIEN_HOC : "sinh ra"
  BAI_HOC ||--o{ SU_KIEN_HOC : "liên quan"
  LOP ||--o{ BAI_GIAO : "giao"
  BAI_GIAO ||--o{ BAI_NOP : "nhận"
  LOP ||--o{ CHIA_BAO_CAO : "cấp"
  CHIA_BAO_CAO ||--o{ SO_GUI : "ghi"
  NGUOI_DUNG ||--o{ NHAT_KY_KIEM_TOAN : "thực hiện"`)}
${bang(['Nhóm', 'Nội dung', 'Trạng thái'], [
  ['<b>Người dùng &amp; quyền</b>', 'Tài khoản, vai trò, phiên đăng nhập, nhật ký kiểm toán', `Đang chạy (${so(S.taiKhoan)} tài khoản)`],
  ['<b>Giáo trình</b>', 'Hợp phần, bài học, quiz, lộ trình', `Đang chạy (${so(S.baiHoc)} bài)`],
  ['<b>Lớp &amp; vận hành</b>', 'Đợt học, lớp, thành viên, buổi học, điểm danh', `Đang chạy (${so(S.lop)} lớp, ${so(S.buoiHoc)} buổi)`],
  ['<b>Học tập</b>', 'Sự kiện học, tiến độ bài, năng lực theo chủ đề, kế hoạch học', 'Đang chạy'],
  ['<b>Thi thử</b>', 'Đề, câu hỏi, lượt làm bài, kết quả', 'Đang chạy'],
  ['<b>Bài tập</b>', 'Bài giao, bài nộp, điểm chấm', '<b>Đã dựng, chưa dùng lần nào</b>'],
  ['<b>Báo cáo phụ huynh</b>', 'Chìa xem báo cáo, sổ gửi', 'Đã dựng, chờ liên lạc phụ huynh'],
])}
${trang()}

${muc('C.5', 'Phân quyền ở tầng mã')}
${bang(['Nhóm đường', 'Số lượng', 'Nghĩa'], [
  ['Không cần đăng nhập', `<b>${API.congKhai.length}</b>`, 'Danh sách khoá học công khai, và đường dẫn báo cáo phụ huynh (bảo vệ bằng chìa dài, có hạn dùng).'],
  ['Chỉ cần đăng nhập', `<b>${API.chiDangNhap.length}</b>`, 'Dữ liệu của <i>chính người đang đăng nhập</i>. Mỗi đường tự lọc theo người gọi.'],
  ['Có cổng vai trò', `<b>${API.coCong.length}</b>`, 'Chặn theo vai trò <i>và</i> theo ngữ cảnh lớp.'],
])}
${bang(['Lớp cổng', 'Chặn cho', 'Số đường'], [
  ['<code>IsTeachingStaff</code>', 'Giảng viên · trợ giảng · học vụ · quản trị', String(soCong('IsTeachingStaff'))],
  ['<code>IsSeniorTeachingStaff</code>', 'Như trên nhưng <b>bỏ trợ giảng</b> — dùng cho báo cáo phụ huynh', String(soCong('IsSeniorTeachingStaff'))],
  ['<code>IsAdminOrAcademic</code>', 'Quản trị viên · quản lý học vụ', String(soCong('IsAdminOrAcademic'))],
  ['<code>IsAdminRole</code>', 'Chỉ quản trị viên', String(soCong('IsAdminRole'))],
  ['<code>IsContentEditor</code>', 'Biên tập nội dung · quản trị', String(soCong('IsContentEditor'))],
])}
${mer(`flowchart LR
  R["Yêu cầu tới"] --> A{"Đã đăng nhập?"}
  A -->|"Không"| X1["Từ chối 401"]
  A -->|"Rồi"| B{"Vai trò có<br/>trong cổng?"}
  B -->|"Không"| X2["Từ chối 403"]
  B -->|"Có"| C{"Có phụ trách<br/>lớp này?"}
  C -->|"Không"| X3["Trả 404 — KHÔNG phải 403"]
  C -->|"Có"| OK["Cho qua"]`)}
${ghi('<b>404 chứ không 403</b> khi người dùng không phụ trách lớp: trả 403 là xác nhận lớp ấy <i>tồn tại</i>, tức rò một mẩu thông tin cho người không có quyền.')}
${canh(`<b>Điểm cần siết:</b> ${API.chiDangNhap.filter((r) => !r.khaiTay).length} đường không tự khai cổng mà dựa vào mặc định của khung. Mặc định ấy đúng (phải đăng nhập), nhưng một đường mới quên khai sẽ mở cho mọi người đã đăng nhập, im lặng, trông y hệt một quyết định có chủ ý. Xem Phần E.`)}

${muc('C.6', 'Điểm nối với hệ thống khảo thí')}
<p>Ba cách, từ tốt nhất tới dễ nhất:</p>
${bang(['Cách', 'Cần gì từ TopHSA', 'Đánh giá'], [
  ['<b>Nối trực tiếp</b>', 'Khoá truy cập hoặc webhook từ hệ thống khảo thí', 'Tốt nhất — kết quả tự chảy sang sau mỗi kỳ thi. Cần bên kỹ thuật hai bên nói chuyện.'],
  ['<b>Nhập tệp bảng tính</b>', 'Chức năng xuất danh sách điểm ra Excel/CSV', 'Đủ dùng. Học vụ tải về rồi đẩy lên, có bước xem trước.'],
  ['<b>Nhập tệp báo cáo PDF</b>', 'Tệp "Báo cáo kết quả thi" của từng học viên', 'Khả thi — chúng tôi đã đọc thử một tệp và bóc được đầy đủ: điểm ba phần, tổng điểm, và mức đạt của từng đơn vị kiến thức.'],
])}
${ghi('Chúng tôi cần <b>một trong ba</b>, không cần cả ba.')}

${muc('C.7', 'Hạ tầng — và những chỗ yếu đã đo')}
${bang(['Chỗ yếu', 'Đo được', 'Ảnh hưởng'], [
  ['<b>Máy chủ ngủ đông</b>', 'Gói miễn phí tắt dịch vụ sau ~15 phút không ai dùng; lần gọi đầu sau đó mất <b>~40 giây</b>', 'Người đăng nhập đầu ngày tưởng hệ thống hỏng. Đã đặt lịch giữ ấm giờ hành chính; dứt điểm cần nâng gói (~7 USD/tháng).'],
  ['<b>Chưa có sao lưu</b>', 'Không tìm thấy quy trình sao lưu nào trong hệ thống', 'Mất dữ liệu là mất hẳn. <b>Việc cần làm sớm nhất.</b>'],
  ['<b>Chưa có giám sát</b>', 'Không có cảnh báo khi hệ thống ngừng chạy', 'Chỉ biết hỏng khi có người báo.'],
  ['<b>Giới hạn truy cập dùng chung một bộ đếm</b>', 'Mọi người dùng chung một hạn mức đăng nhập', 'Một người gõ sai nhiều lần có thể chặn cả lớp. Cách sửa đã có sẵn trong mã, chờ cấu hình.'],
])}

${muc('C.8', 'Bảo mật — những gì đã làm')}
${bang(['Mối lo', 'Cách xử lý'], [
  ['<b>Mật khẩu bị lộ nếu cơ sở dữ liệu rò</b>', 'Mật khẩu không bao giờ được lưu nguyên văn — chỉ lưu bản băm một chiều. Kể cả người quản trị hệ thống cũng không đọc được mật khẩu của ai.'],
  ['<b>Đánh cắp phiên đăng nhập</b>', 'Vé đăng nhập lưu trong cookie mà mã JavaScript trên trang KHÔNG đọc được, và chỉ truyền qua kết nối mã hoá. Đăng xuất thì vé bị thu hồi ngay, không đợi hết hạn.'],
  ['<b>Dò mật khẩu bằng máy</b>', 'Giới hạn số lần thử đăng nhập theo thời gian.'],
  ['<b>Chèn mã độc qua ô nhập liệu</b>', 'Mọi chuỗi người dùng nhập đều được vô hiệu hoá trước khi hiển thị. Đã tìm và vá ba lỗ loại này trong đợt rà soát.'],
  ['<b>Chèn lệnh vào cơ sở dữ liệu</b>', 'Mọi truy vấn dùng tham số, không nối chuỗi. Đã rà toàn bộ.'],
  ['<b>Xem trộm dữ liệu của lớp khác</b>', 'Mọi đường dẫn tới dữ liệu lớp đều kiểm "người này có phụ trách lớp đó không", và trả về "không tìm thấy" thay vì "không có quyền".'],
  ['<b>Đường dẫn báo cáo bị chuyển tiếp lung tung</b>', 'Chìa dài, ngẫu nhiên, có hạn dùng, và thu hồi được bất cứ lúc nào.'],
  ['<b>Không biết ai đã sửa gì</b>', 'Nhật ký kiểm toán ghi mọi hành động sửa: ai, lúc nào, sửa gì, từ địa chỉ nào.'],
])}

${muc('C.9', 'Quyền riêng tư của học viên')}
<p>Người học ở đây phần lớn là học sinh lớp 12 — vẫn là trẻ em theo phần lớn khung
pháp lý. Ba ranh giới dưới đây là <b>quyết định</b>, không phải mặc định kỹ thuật.</p>
${bang(['Ranh giới', 'Hiện tại', 'Vì sao'], [
  ['<b>Nhật ký học viên tự ghi</b>', 'KHÔNG có trong báo cáo phụ huynh', 'Đó là chỗ em viết cho chính mình. Đưa vào tờ gửi về nhà là biến một chỗ riêng tư thành một chỗ bị theo dõi, và em sẽ ngừng viết thật.'],
  ['<b>Dữ liệu liên lạc</b>', 'Trợ giảng nhìn được khi làm việc, nhưng không tải ra tệp được', 'Nhìn để biết đang tick cho em nào là cần. Mang ra ngoài thì không — tệp tải về rời khỏi tầm kiểm soát ngay khi ai đó bấm.'],
  ['<b>Đường dẫn báo cáo</b>', 'Có hạn dùng, thu hồi được, gửi nhầm thì huỷ được', 'Một đường dẫn vĩnh viễn là một đường dẫn sẽ bị chuyển tiếp.'],
  ['<b>Dữ liệu học viên thật trên trang công khai</b>', 'Tuyệt đối không', 'Trang giới thiệu dùng số liệu của một học viên KHÔNG có thật, và nói thẳng điều đó ngay cạnh.'],
])}
${canh('<b>Cần TopHSA chốt thành chính sách:</b> phụ huynh được xem những gì. Hiện tại là "tiến độ và điểm — có; nhật ký riêng — không". Nếu trung tâm muốn khác thì phải quyết rõ ràng, đừng để ngầm.')}

${muc('C.10', 'Chất lượng — cách chúng tôi biết hệ thống còn chạy đúng')}
${bang(['Lớp bảo vệ', 'Nội dung', 'Con số'], [
  ['<b>Bộ kiểm tự động</b>', 'Chạy lại toàn bộ nghiệp vụ trên cơ sở dữ liệu thật, trong giao dịch được huỷ sau đó', `<b>453</b> phép kiểm, chạy hết trong ~29 phút (đo ${NGAY})`],
  ['<b>Bộ đo giao diện</b>', 'Mở từng màn hình bằng trình duyệt thật, đo độ tương phản chữ, kích thước vùng bấm, tràn ngang, lỗi JavaScript', `${D.trang.length} màn hình × 2 khổ (điện thoại và máy tính) × 2 bộ màu`],
  ['<b>Cổng trước mỗi lần cập nhật</b>', 'Kiểm kiểu dữ liệu, kiểm quy ước mã, dựng bản production thử', 'Chạy tự động trên mỗi lần đẩy mã'],
  ['<b>Tệp kiểm thử</b>', 'Mã kiểm nằm cạnh mã sản phẩm', `${D.kiemThu.tepBackend} tệp phía máy chủ, ${D.kiemThu.tepFrontend} tệp phía giao diện`],
])}
${ghi('<b>Một nguyên tắc đáng nói:</b> viết xong một phép kiểm, chúng tôi lùi mã về bản cũ để xem nó có báo đỏ không. Nếu phép kiểm vẫn xanh khi mã đã hỏng thì nó vô dụng — và một phép kiểm vô dụng còn tệ hơn không có, vì nó tạo cảm giác an toàn giả.')}
${trang()}`;

/* ── PHẦN D ─────────────────────────────────────────────────────────────── */
const PHAN_D = `
<section class="phan"><p class="phan-nhan">Phần D</p><h1 class="phan-ten">Cần gì từ TopHSA</h1>
<p class="phan-mo">Mỗi mục ghi rõ: cần gì, vì sao cần, và nó đang chặn việc gì. Không mục nào là "cho đầy đủ".</p></section>

${muc('D.1', 'Dữ liệu')}
${bang(['Cần', 'Vì sao', 'Đang chặn'], [
  ['<b>Email (và/hoặc số Zalo) của phụ huynh</b>', 'Không có thì không gửi báo cáo cho ai được', `Toàn bộ luồng báo cáo phụ huynh. Hiện <b>${so(S.coEmailPhuHuynh)}/${so(S.hocVien)}</b> em đã khai.`],
  ['<b>Kết quả thi thử của học viên</b>', 'Ô "điểm thi thử" trong báo cáo phụ huynh đang trống', 'Phần giá trị nhất của tờ báo cáo. Xem C.6 để chọn cách trao đổi.'],
  ['<b>Danh sách lớp và học viên thật</b> của một đợt', 'Hệ thống mới chạy với một lớp mẫu', 'Không biết luồng nào vướng khi dùng thật.'],
  ['<b>Lịch học thật</b> của lớp ấy', 'Để sinh buổi học tự động thay vì tạo tay từng buổi', 'Học vụ phải nhập tay nhiều hơn cần thiết.'],
])}

${muc('D.2', 'Thông tin và quy trình')}
${bang(['Cần', 'Vì sao'], [
  ['<b>Trung tâm có những chức danh nào</b>', 'Hệ thống hiện có 6 vai trò do chúng tôi đặt ra. Nếu TopHSA có chức danh khác (ví dụ: chủ nhiệm, tư vấn tuyển sinh) thì phải thêm — dựng màn hình cho một vai trò không tồn tại là tốn và phải đập đi.'],
  ['<b>Quy trình thu học phí</b>', 'Hệ thống mới dựng phần <i>đếm buổi</i> (cơ sở tính). Phần tiền — giá, hoá đơn, công nợ — chưa dựng vì sai một chi tiết là sai sổ sách.'],
  ['<b>Quy trình tuyển sinh</b>', 'Ai nghe điện, ghi những gì, lúc nào một người quan tâm trở thành học viên. Trang giới thiệu đang dẫn người tới mà chưa có chỗ hứng.'],
  ['<b>Có chấm tự luận không</b>', 'Quyết định hình dạng màn chấm bài. Hệ thống đã dựng phần chấm tay nhưng chưa ai dùng.'],
  ['<b>Phụ huynh được xem những gì</b>', 'Hiện tờ báo cáo <b>không</b> có nhật ký học viên tự ghi — đó là chỗ riêng của em. Nếu TopHSA muốn khác, cần chốt thành chính sách chứ không để ngầm.'],
])}

${muc('D.3', 'Quyết định')}
${bang(['Quyết định', 'Lựa chọn', 'Hệ quả nếu hoãn'], [
  ['<b>Địa chỉ email của trung tâm</b>', 'Tên miền riêng (dạng <i>tên@tophsa.vn</i>) hay một hộp thư dùng chung', 'Báo cáo phụ huynh chưa gửi được dưới danh nghĩa trung tâm.'],
  ['<b>Zalo OA</b>', 'Có xác thực doanh nghiệp để dùng Zalo không', 'Phụ huynh Việt đọc Zalo nhiều hơn email. Xác thực cần giấy phép kinh doanh — hộ kinh doanh cũng được.'],
  ['<b>Nâng gói máy chủ</b>', '~7 USD/tháng để hết ngủ đông', 'Người đăng nhập đầu ngày phải chờ ~40 giây.'],
  ['<b>Ranh giới với hệ thống khảo thí</b>', 'Nối hai hệ thống, hay gộp về một', 'Ảnh hưởng lớn tới thứ tự làm việc. Khuyến nghị: nối, đừng làm lại.'],
])}
${trang()}`;

/* ── PHẦN E ─────────────────────────────────────────────────────────────── */
const PHAN_E = `
<section class="phan"><p class="phan-nhan">Phần E</p><h1 class="phan-ten">Làm tiếp được ngay</h1>
<p class="phan-mo">Những việc không phải chờ TopHSA. Xếp theo mức rủi ro mà chúng giảm được.</p></section>

${muc('E.1', 'Nhóm 1 — Giữ cho hệ thống không mất dữ liệu')}
${bang(['Việc', 'Vì sao ưu tiên nhất'], [
  ['<b>Sao lưu cơ sở dữ liệu định kỳ</b>', 'Đo hôm nay: không có quy trình sao lưu nào. Mất dữ liệu là mất hẳn, và đây là dữ liệu học tập của trẻ em. Rẻ khi làm sớm, không cứu được khi làm muộn.'],
  ['<b>Cảnh báo khi hệ thống ngừng chạy</b>', 'Hiện chỉ biết hỏng khi có người báo. Đã có sẵn một địa chỉ kiểm tra sức khoẻ; chỉ cần nối vào một dịch vụ giám sát miễn phí.'],
  ['<b>Tách môi trường kiểm thử khỏi dữ liệu thật</b>', 'Mỗi lần cập nhật mã, bộ kiểm tự động chạy thẳng vào cơ sở dữ liệu đang dùng thật. Nó có dọn sạch sau mỗi lượt, nhưng không nên như thế.'],
])}

${muc('E.2', 'Nhóm 2 — Siết những chỗ đã biết là yếu')}
${bang(['Việc', 'Vì sao'], [
  ['<b>Khai cổng phân quyền tường minh cho mọi đường</b>', `${API.chiDangNhap.filter((r) => !r.khaiTay).length} đường đang dựa vào mặc định của khung. Mặc định ấy đúng, nhưng một đường mới quên khai sẽ mở cho mọi người đã đăng nhập — im lặng, không báo gì.`],
  ['<b>Bộ đếm giới hạn truy cập dùng chung</b>', 'Hiện mỗi tiến trình đếm riêng, nên hạn mức thực tế gấp đôi con số khai báo và bị đặt lại mỗi lần cập nhật.'],
  ['<b>Chuyển nốt phần giao diện cũ sang nền mới</b>', 'Còn 13 tệp không đi qua bộ kiểm tự động. Hai lỗ hổng bảo mật đã từng nằm đúng ở đó.'],
])}

${muc('E.3', 'Nhóm 3 — Làm sản phẩm dùng được hơn')}
${bang(['Việc', 'Giải quyết điều gì'], [
  ['<b>Màn nhập liệu nhanh cho học vụ</b>', 'Một luồng dẫn từng bước: tạo đợt → sinh buổi theo lịch → điểm danh → điền liên lạc phụ huynh. Nhắm thẳng vào thứ đang chặn: hệ thống đã dựng xong nhưng chưa có dữ liệu.'],
  ['<b>Bảng nhắc việc hàng ngày cho giảng viên</b>', '"Hôm nay buổi nào chưa điểm danh, em nào chưa nộp bài." Dữ liệu đã có sẵn, chỉ chưa có màn hình.'],
  ['<b>Bộ nhập kết quả thi từ tệp PDF</b>', 'Dựng và kiểm được ngay trên tệp báo cáo mẫu, để lúc TopHSA đồng ý là chạy được luôn.'],
  ['<b>Xuất báo cáo toàn trung tâm</b>', 'Hiện xuất được từng lớp; bản toàn trung tâm là thứ mang đi họp ban giám đốc.'],
  ['<b>Đưa vào dùng ba mô-đun đã dựng mà chưa chạy</b>', 'Bài tập, bài nộp và thông báo trong ứng dụng đều đã xong nhưng chưa có dòng dữ liệu nào.'],
])}

${muc('E.4', 'Cách chúng tôi làm việc')}
<p>Ghi ra đây để TopHSA biết cái gì đứng sau những con số ở trên:</p>
<ul class="to">
  <li><b>Đo, không đoán.</b> Mọi con số trong tài liệu này đọc thẳng từ mã nguồn và cơ sở dữ liệu lúc sinh tệp.</li>
  <li><b>Phép kiểm phải chứng minh được là nó bắt được lỗi.</b> Viết xong một phép kiểm, chúng tôi lùi mã về bản cũ để xem nó có báo đỏ không — nếu không thì phép kiểm ấy vô dụng.</li>
  <li><b>Không có dữ liệu thì nói là không có,</b> không viết số 0. "Điểm thi thử: 0" đọc như em ấy làm sai hết, trong khi sự thật là em chưa thi lần nào.</li>
  <li><b>Không con số nào được tính ở hai nơi.</b> Màn hình, tệp Excel và tệp PDF phải nói cùng một chuyện — nếu không, không ai biết bản nào đúng.</li>
</ul>
${muc('E.5', 'Lộ trình đề xuất')}
${bang(['Giai đoạn', 'Việc', 'Cần TopHSA?'], [
  ['<b>1. Ngay</b><br><i>1–2 tuần</i>', 'Sao lưu cơ sở dữ liệu · cảnh báo khi hệ thống ngừng · tách môi trường kiểm thử', 'Không'],
  ['<b>2. Chạy thử thật</b><br><i>2–4 tuần</i>', 'Một lớp thật, một giảng viên, một đợt. Học vụ nhập liệu thật và ghi lại chỗ nào vướng.', '<b>Có</b> — cần một lớp'],
  ['<b>3. Nối phụ huynh</b><br><i>song song</i>', 'Địa chỉ email của trung tâm · thu thập liên lạc phụ huynh · gửi tờ báo cáo đầu tiên', '<b>Có</b> — địa chỉ email'],
  ['<b>4. Nối kết quả thi</b>', 'Đưa điểm thi thử từ hệ thống khảo thí vào báo cáo phụ huynh', '<b>Có</b> — chọn cách trao đổi'],
  ['<b>5. Học phí</b>', 'Từ cơ sở tính (đã có) sang hoá đơn và công nợ', '<b>Có</b> — quy trình thu chi'],
  ['<b>6. Tuyển sinh</b>', 'Luồng từ người quan tâm tới học viên ghi danh', '<b>Có</b> — quy trình tư vấn'],
])}
${canh('Giai đoạn 1 nên bắt đầu ngay và không phải chờ ai. Giai đoạn 2 là <b>nút thắt</b>: mọi thứ sau nó đều dễ hơn khi đã có một lớp thật chạy qua hệ thống một lần.')}

${muc('E.6', 'Thuật ngữ dùng trong tài liệu')}
${bang(['Từ', 'Nghĩa trong hệ thống này'], [
  ['<b>Đợt học</b>', 'Một khoá luyện thi có ngày bắt đầu và ngày thi. Một đợt chứa nhiều lớp.'],
  ['<b>Lớp</b>', 'Một nhóm học viên do một giảng viên phụ trách, thuộc một đợt.'],
  ['<b>Buổi học</b>', 'Một lần lớp gặp nhau, có giờ cụ thể. Điểm danh gắn vào buổi.'],
  ['<b>Hợp phần</b>', 'Một trong ba phần của đề HSA: Định lượng, Định tính, Khoa học &amp; Tiếng Anh.'],
  ['<b>Chủ đề</b>', 'Đơn vị nhỏ hơn hợp phần, ví dụ "Hàm số" hay "Đọc hiểu". Năng lực đo theo đơn vị này.'],
  ['<b>Bản đồ năng lực</b>', 'Mức nắm của học viên trên từng chủ đề, không quy thành một điểm chung.'],
  ['<b>Chìa báo cáo</b>', 'Đường dẫn riêng gửi cho phụ huynh, có hạn dùng, thu hồi được.'],
  ['<b>Nhật ký kiểm toán</b>', 'Sổ ghi mọi thao tác sửa dữ liệu: ai, lúc nào, sửa gì.'],
  ['<b>Cơ sở tính học phí</b>', 'Số buổi từng em trong kỳ. Là <i>cơ sở</i> để tính tiền, chưa phải hoá đơn.'],
])}

<p class="ket">Tài liệu sinh ngày ${NGAY} · số liệu đo trực tiếp trên hệ thống ·
chạy lại lệnh sinh là tài liệu đúng lại.</p>`;

/* ── khung trang ────────────────────────────────────────────────────────── */
const HTML = `<!doctype html><html lang="vi"><head><meta charset="utf-8">
<title>Hồ sơ sản phẩm PE_HSA — TopHSA</title>
<style>
  @page { size: A4; margin: 18mm 16mm 16mm; }
  * { box-sizing: border-box; }
  body { margin: 0; font: 10.5pt/1.55 "Segoe UI", "Helvetica Neue", Arial, sans-serif;
         color: #23232b; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  h1, h2, h3 { line-height: 1.25; }
  h2 { font-size: 14pt; margin: 22px 0 8px; color: #2A1F6F; break-after: avoid; }
  h2 .so { display: inline-block; min-width: 2.6em; color: #6F63D8; font-weight: 700; }
  h2.khong-so { color: #2A1F6F; }
  p { margin: 0 0 9px; }
  ul.to { margin: 0 0 12px; padding-left: 18px; }
  ul.to li { margin-bottom: 6px; }
  code { font-family: "Cascadia Mono", Consolas, monospace; font-size: 9pt;
         background: #F2F1FA; padding: 1px 4px; border-radius: 3px; }

  /* bìa */
  .bia { height: 245mm; display: flex; flex-direction: column; justify-content: center; }
  .bia .nhan { text-transform: uppercase; letter-spacing: .16em; font-size: 9pt;
               color: #6F63D8; font-weight: 700; margin-bottom: 10px; }
  .bia h1 { font-size: 30pt; margin: 0 0 14px; color: #1B1440; letter-spacing: -.01em; }
  .bia .phu { font-size: 12pt; color: #5A5A6B; margin-bottom: 40px; }
  .bia-so { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 40px; }
  .bia-so div { border: 1px solid #DDDBEE; border-radius: 8px; padding: 14px 12px; }
  .bia-so b { display: block; font-size: 22pt; color: #2A1F6F; line-height: 1; }
  .bia-so span { display: block; font-size: 8.5pt; color: #6B6B7B; margin-top: 5px; }
  .bia-chan { font-size: 9pt; color: #6B6B7B; border-top: 1px solid #E4E2F0; padding-top: 12px; }

  /* trang mở phần */
  .phan { break-before: page; padding: 34px 0 14px; border-bottom: 2px solid #2A1F6F;
          margin-bottom: 18px; }
  .phan-nhan { text-transform: uppercase; letter-spacing: .16em; font-size: 8.5pt;
               color: #6F63D8; font-weight: 700; margin: 0 0 4px; }
  .phan-ten { font-size: 22pt; margin: 0 0 8px; color: #1B1440; }
  .phan-mo { font-size: 10.5pt; color: #55556A; margin: 0; max-width: 62ch; }

  table { width: 100%; border-collapse: collapse; margin: 6px 0 14px; font-size: 9.5pt;
          break-inside: avoid; }
  th { text-align: left; background: #F2F1FA; color: #2A1F6F; font-weight: 700;
       padding: 6px 8px; border: 1px solid #DDDBEE; }
  td { padding: 6px 8px; border: 1px solid #E4E2F0; vertical-align: top; }
  td.dau { width: 26%; }
  table.ml td { border: none; padding: 7px 0; border-bottom: 1px solid #EEEDF6; }
  table.ml .ml-p { width: 15%; color: #6F63D8; font-weight: 700; }

  .ghi, .canh { font-size: 9.5pt; padding: 9px 12px; border-radius: 6px; margin: 4px 0 14px;
                break-inside: avoid; }
  .ghi { background: #F6F5FC; border-left: 3px solid #9C93E8; color: #3A3A50; }
  .canh { background: #FFF7EC; border-left: 3px solid #E0A150; color: #4A3722; }
  /* Chú thích đứng NGAY SAU một sơ đồ phải đi cùng trang với sơ đồ ấy.
     Không có luật này thì nó rơi sang trang sau MỘT MÌNH, và trang ấy chỉ có
     đúng một câu — đo ở bản trước: hai trang như thế, 220 và 198 ký tự. Trong
     một hồ sơ gửi đối tác, một trang gần trắng đọc như một lỗi in. */
  .so-do + .ghi, .so-do + .canh, .so-do + p { break-before: avoid; }
  .dan { color: #55556A; }
  .ket { margin-top: 26px; padding-top: 12px; border-top: 1px solid #E4E2F0;
         font-size: 9pt; color: #6B6B7B; }

  .so-do { margin: 10px 0 16px; text-align: center; break-inside: avoid; }
  .so-do svg { max-width: 100%; height: auto; }
  /* Chiều cao do JS đặt sau khi mermaid vẽ xong — xem chú thích ở cuối tệp. */
  .ngat { break-after: page; }
</style></head><body>
${BIA}${trang()}${MUC_LUC}${PHAN_A}${PHAN_B}${PHAN_C}${PHAN_D}${PHAN_E}
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({
    startOnLoad: false, securityLevel: 'loose', fontFamily: 'Segoe UI, Arial, sans-serif',
    themeVariables: {
      primaryColor: '#F2F1FA', primaryTextColor: '#23232b', primaryBorderColor: '#9C93E8',
      lineColor: '#7A72B8', fontSize: '13px',
      /* Hộp NHÓM mặc định của mermaid màu vàng, lệch hẳn bảng màu tím của tài
         liệu — trong một hồ sơ gửi đối tác thì nó đọc như hai người làm hai
         phần. Đặt lại cho khớp. */
      clusterBkg: '#FAF9FE', clusterBorder: '#C9C3EC',
      tertiaryColor: '#FFFFFF', tertiaryBorderColor: '#DDDBEE',
    },
  });
  await mermaid.run({ querySelector: '.mermaid' });

  /* CO SƠ ĐỒ CHO VỪA MỘT TRANG.
   *
   * Bản đầu để mermaid tự đặt kích thước và luật "break-inside: avoid" lo
   * phần ngắt trang. Không đủ: một sơ đồ CAO HƠN một trang thì không có chỗ
   * nào để mà tránh, nên trình duyệt cắt nó ra — đo được ở bản đầu, sơ đồ use
   * case bị xé thành BA trang và sơ đồ dữ liệu bị cắt làm đôi.
   *
   * Thuộc tính "max-height" trong CSS không cứu được: SVG của mermaid có
   * "width" cố định, nên hạn chiều cao chỉ cắt bớt chứ không co lại. Phải
   * tính tay từ "viewBox" rồi đặt CHIỀU NGANG — chiều cao tự theo tỉ lệ.
   *
   * (Và chú thích này KHÔNG được chứa dấu huyền ngược: cả khối HTML là một
   * chuỗi template, nên một cặp dấu ấy trong chú thích sẽ kết thúc chuỗi sớm.
   * Đã mắc đúng lỗi đó ở bản đầu.)
   *
   * 673px = bề ngang in được của A4 với lề 16mm. 800px = chiều cao còn lại
   * sau khi trừ lề, tiêu đề mục và dòng chú thích dưới sơ đồ. */
  const RONG_TOI_DA = 673;
  /* 800px thì sơ đồ VỪA một trang nhưng không còn chỗ cho tiêu đề mục và đoạn
   * dẫn ở trên nó — nên cả cụm bị đẩy sang trang sau và để lại một trang gần
   * như trắng. Đo ở bản trước: trang 6 chỉ có đúng một đoạn chú thích.
   * 600px để tiêu đề + đoạn dẫn + sơ đồ + chú thích đi được cùng một trang. */
  const CAO_TOI_DA = 600;
  for (const svg of document.querySelectorAll('.so-do svg')) {
    const vb = svg.viewBox && svg.viewBox.baseVal;
    if (!vb || !vb.width || !vb.height) continue;
    const tiLe = vb.width / vb.height;
    const rong = Math.min(RONG_TOI_DA, CAO_TOI_DA * tiLe);
    svg.removeAttribute('height');
    svg.style.width = rong + 'px';
    svg.style.maxWidth = '100%';
    svg.style.height = 'auto';
  }

  window.__soDoXong = true;
</script></body></html>`;

/* ── dựng PDF ───────────────────────────────────────────────────────────── */
const b = await chromium.launch({ channel: 'chrome' });
const p = await b.newPage();
await p.setContent(HTML, { waitUntil: 'networkidle' });
// Đợi mermaid vẽ XONG. In trước khi nó vẽ thì mọi sơ đồ ra một khối chữ thô —
// và tệp vẫn "thành công", nên phải chờ bằng CỜ do chính mermaid đặt.
await p.waitForFunction('window.__soDoXong === true', null, { timeout: 60000 });
await p.waitForTimeout(1200);

const soDo = await p.locator('.so-do svg').count();
// Đo chiều cao thật của từng sơ đồ SAU khi co. Cao hơn một trang in được thì
// nó sẽ bị cắt, và tệp vẫn "thành công" — nên phải tự kiểm, đừng tin mắt.
const qua_cao = await p.evaluate((max) => [...document.querySelectorAll('.so-do')]
  .map((d, i) => ({ i: i + 1, cao: Math.round(d.getBoundingClientRect().height) }))
  .filter((d) => d.cao > max), 660);
await p.pdf({
  path: RA, format: 'A4', printBackground: true,
  displayHeaderFooter: true,
  headerTemplate: '<div></div>',
  footerTemplate: `<div style="width:100%;font-size:8pt;color:#8A8A9B;
     font-family:Segoe UI,Arial,sans-serif;padding:0 16mm;display:flex;
     justify-content:space-between"><span>Hồ sơ sản phẩm PE_HSA · ${NGAY}</span>
     <span class="pageNumber"></span>/<span class="totalPages"></span></div>`,
  margin: { top: '18mm', bottom: '16mm', left: '16mm', right: '16mm' },
});
await b.close();

const kb = (fs.statSync(RA).size / 1024).toFixed(0);
console.log('Đã dựng: %s  (%s KB, %d sơ đồ)', RA, kb, soDo);
if (soDo < 8) {
  console.error('CẢNH BÁO: chỉ %d sơ đồ vẽ được — mermaid có thể chưa chạy xong.', soDo);
  process.exit(1);
}
if (qua_cao.length) {
  console.error('CẢNH BÁO: %d sơ đồ cao hơn một trang, sẽ bị cắt: %s',
    qua_cao.length, JSON.stringify(qua_cao));
  process.exit(1);
}
console.log('  mọi sơ đồ đều lọt một trang ✓');
