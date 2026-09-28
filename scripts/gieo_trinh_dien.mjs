/**
 * GIEO DỮ LIỆU TRÌNH DIỄN QUA CỬA API THẬT — dùng cho production, nơi không ai có shell.
 *
 *     PE_THE=<thư mục thẻ> node scripts/gieo_trinh_dien.mjs [--that]
 *
 * Không có `--that` thì chỉ XEM: in ra thiếu gì, không ghi gì.
 *
 * ── VÌ SAO KHÔNG DÙNG `du_lieu_mau --lam-moi` ──────────────────────────────
 *
 * Lệnh ấy vẫn là đường chính, và vẫn tốt hơn ở dev. Nhưng nó cần shell của Render, tức cần
 * chính chủ dự án ngồi vào máy — nên suốt nhiều ngày `kiem_production.mjs` báo sáu khối
 * DỮ LIỆU rỗng mà không ai lấp được. Tệp này lấp bằng đúng những cửa mà người dùng thật bấm.
 *
 * Nên nó còn là thứ dự án chưa từng có: **một lượt đi trọn luồng GHI trên bản đã deploy**.
 * Cổng `pre-push` và pytest đều chạy trên máy cục bộ; E2E chạy trên `localhost`. Nếu một
 * cửa ghi hỏng RIÊNG trên production — thiếu cột sau lượt `bootstrap_schema`, quyền lệch,
 * biến môi trường vắng — thì đây là chỗ đầu tiên phát hiện ra.
 *
 * Chỉ gieo THÊM, không xoá gì. Chạy hai lần thì lượt sau bỏ qua phần đã có.
 */
import { existsSync, readFileSync } from 'node:fs';

const API = process.env.PE_API || 'https://pe-hsa-backend.onrender.com';
const THE = process.env.PE_THE;
const THAT = process.argv.includes('--that');
const DAU = '[gieo]';
const TEN_KHUNG = 'Khung luyện HSA — 3 buổi mẫu';

if (!THE || !existsSync(`${THE}/tokens_ad.json`)) {
  console.log('Cần PE_THE trỏ tới thư mục có tokens_ad.json (thẻ quản trị). ĐỪNG để trong repo.');
  process.exit(2);
}
const token = JSON.parse(readFileSync(`${THE}/tokens_ad.json`, 'utf8')).access;

const buoc = [];
function ghi(ten, dat, chiTiet) {
  buoc.push({ dat });
  console.log(`${dat ? 'ĐẠT ' : 'HỎNG'} ${ten}${chiTiet ? ` — ${chiTiet}` : ''}`);
}

async function goi(duong, { method = 'GET', than = null } = {}) {
  const r = await fetch(`${API}${duong}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(than ? { 'Content-Type': 'application/json' } : {}),
    },
    body: than ? JSON.stringify(than) : undefined,
    signal: AbortSignal.timeout(180000),
  });
  const chu = await r.text();
  let d = null;
  try { d = JSON.parse(chu); } catch { /* trang lỗi HTML của Render */ }
  return { ma: r.status, d, chu };
}

/** Ghi thật, hoặc chỉ nói sẽ ghi gì. Trả `null` khi đang ở chế độ xem. */
async function viet(ten, duong, than, method = 'POST') {
  if (!THAT) { console.log(`     (sẽ ${method} ${duong})`); return null; }
  const r = await goi(duong, { method, than });
  if (r.ma >= 400) {
    ghi(ten, false, `HTTP ${r.ma} · ${(r.chu || '').slice(0, 160)}`);
    return null;
  }
  console.log(`  ok  ${ten}`);
  return r.d;
}

// ── 0 · Lớp mẫu ─────────────────────────────────────────────────────────────
const traLop = await goi('/api/admin/classes');
if (traLop.ma === 401 || traLop.ma === 403) {
  console.log(`${DAU} KHÔNG GIEO ĐƯỢC — thẻ quản trị hết hạn (HTTP ${traLop.ma}). Cấp lại rồi chạy lại.`);
  process.exit(2);
}
const dsLop = traLop.d?.classes || [];
if (!dsLop.length) {
  console.log(`${DAU} KHÔNG GIEO ĐƯỢC — CSDL không có lớp nào.`);
  process.exit(2);
}
// Lớp đông nhất = lớp bộ trình diễn dựng ra để trình bày. `PE_LOP` ép một lớp khác — cần
// khi lớp phải gieo là lớp của MỘT giảng viên cụ thể (bộ soát màn đo bằng thẻ giảng viên ấy,
// nên lớp mẫu đông nhất không giúp gì nếu giảng viên ấy không phụ trách nó).
const epLop = process.env.PE_LOP ? Number(process.env.PE_LOP) : null;
const LOP = epLop
  ? dsLop.find((l) => l.id === epLop)
  : [...dsLop].sort((a, b) => (b.members || 0) - (a.members || 0))[0];
if (!LOP) {
  console.log(`${DAU} KHÔNG GIEO ĐƯỢC — không có lớp #${epLop}.`);
  process.exit(2);
}
console.log(`${DAU} lớp mẫu: "${LOP.name}" (#${LOP.id}, ${LOP.members} em, môn ${LOP.course})`);
console.log(`${DAU} chế độ: ${THAT ? 'GHI THẬT' : 'chỉ xem — thêm --that để ghi'}\n`);

// ── 1 · Khung chương trình ──────────────────────────────────────────────────
const mucLuc = (await goi('/api/admin/chuong-trinh/khung')).d;
const mon = (mucLuc?.mon || []).find((m) => m.id === LOP.course);
let banKhung = (mon?.versions || []).find((v) => v.status === 'xuat_ban');
ghi('môn của lớp đã có khung xuất bản', Boolean(banKhung),
    banKhung ? `"${banKhung.name}"` : 'chưa có khung nào — gieo tiếp');

// Bản nháp mang đúng tên này là bản LƯỢT GIEO TRƯỚC bỏ dở (28/09: lượt đầu dựng xong ba
// buổi rồi chết ở bước xuất bản vì gõ sai tên trạng thái). Dùng lại, đừng đẻ bản thứ hai —
// hai bản khung cùng tên trong một môn là thứ người soạn khung phải đi dọn tay.
const donDo = (mon?.versions || []).find((v) => v.status === 'nhap' && v.name === TEN_KHUNG);
if (!banKhung && donDo) {
  console.log(`${DAU} có bản nháp "${TEN_KHUNG}" từ lượt trước — xuất bản luôn, không dựng lại.`);
  const xb = await viet('xuất bản bản nháp cũ', `/api/admin/syllabus/${donDo.id}`,
                        { status: 'xuat_ban' }, 'PUT');
  if (xb) banKhung = { id: donDo.id, name: TEN_KHUNG };
}

if (!banKhung) {
  const v = await viet('tạo bản khung', `/api/admin/courses/${LOP.course}/syllabus`,
                       { name: TEN_KHUNG });
  const vid = v?.id;
  if (vid) {
    // Ba buổi khung, mỗi buổi đủ các loại mục. Mục `bai_tap`/`kiem_tra` là thứ §74 hỏi
    // "buổi này đã giao bài chưa" — thiếu chúng thì màn Chương trình lớp mở ra trống trơn.
    const buoiKhung = [
      { name: 'Buổi 1 · Hàm số và đồ thị', homework: 'Làm 20 câu hàm số bậc hai' },
      { name: 'Buổi 2 · Xác suất – thống kê', homework: 'Đọc bảng số liệu, 15 câu' },
      { name: 'Buổi 3 · Ôn tập và kiểm tra giữa chặng', homework: 'Ôn toàn bộ hai buổi trước' },
    ];
    for (const [i, bk] of buoiKhung.entries()) {
      const s = await viet(`buổi khung ${i + 1}`, `/api/admin/syllabus/${vid}/sessions`,
                           { name: bk.name, durationMinutes: 90, homework: bk.homework });
      const sid = s?.id;
      if (!sid) continue;
      const muc = [
        { title: 'Lý thuyết và ví dụ mẫu', kind: 'bai_hoc', weight: 40 },
        { title: 'Thảo luận dạng bài hay sai', kind: 'chu_de', weight: 10 },
        { title: 'Bài về nhà sau buổi', kind: 'bai_tap', weight: 25 },
      ];
      if (i === 2) muc.push({ title: 'Kiểm tra giữa chặng', kind: 'kiem_tra', weight: 25 });
      for (const m of muc) {
        await viet(`  mục "${m.title}"`, `/api/admin/syllabus-sessions/${sid}/items`, m);
      }
      await viet('  học liệu khung', `/api/admin/syllabus-sessions/${sid}/materials`,
                 { title: `Slide ${bk.name}`, fileUrl: 'https://example.com/slide.pdf',
                   fileType: 'pdf' });
    }
    const xb = await viet('xuất bản khung', `/api/admin/syllabus/${vid}`,
                          { status: 'xuat_ban' }, 'PUT');
    if (xb) banKhung = { id: vid };
    ghi('khung dựng xong và xuất bản', Boolean(xb));
  }
}

// ── 2 · Lớp nhận khung ──────────────────────────────────────────────────────
const ctLop = (await goi(`/api/teach/classes/${LOP.id}/chuong-trinh`)).d;
ghi('lớp đã nhận khung', Boolean(ctLop?.khung),
    ctLop?.khung ? `${(ctLop.buoiKhung || []).length} buổi khung` : 'chưa nhận — gieo tiếp');
if (!ctLop?.khung && banKhung?.id) {
  const nhan = await viet('lớp nhận khung', `/api/admin/classes/${LOP.id}/chuong-trinh`,
                          { versionId: banKhung.id }, 'PUT');
  if (THAT) ghi('lớp nhận khung', Boolean(nhan));
}

// ── 3 · Bài KIỂM TRA ────────────────────────────────────────────────────────
// Không có bài `kiem_tra` nào thì nút "Nhập điểm" không hiện, và một dòng nghiệm thu mở ra
// trắng dù mã chạy đúng.
const dsBai = (await goi(`/api/teach/classes/${LOP.id}/assignments`)).d?.assignments || [];
const soKt = dsBai.filter((b) => b.kind === 'kiem_tra').length;
ghi('có bài KIỂM TRA', soKt > 0, `${dsBai.length} bài, ${soKt} kiểm tra`);
// Mục khung chưa có bài nào: §74 hỏi "buổi này đã giao bài chưa", nên một khung mà mục nào
// cũng "Chưa giao bài" trả lời đúng nhưng không trình bày được nửa còn lại của tính năng.
const mucKhung = ((await goi(`/api/teach/classes/${LOP.id}/chuong-trinh`)).d?.buoiKhung || [])
  .flatMap((k) => (k.items || []).filter((i) => i.baiDaGiao !== undefined));
const mucTrong = mucKhung.filter((i) => !(i.baiDaGiao || []).length);
ghi('mục khung đã có bài gắn vào', mucKhung.length > mucTrong.length,
    `${mucKhung.length - mucTrong.length}/${mucKhung.length} mục đã giao`);

const han = new Date(Date.now() + 7 * 864e5).toISOString().slice(0, 16);
if (!soKt) {
  await viet('giao bài kiểm tra', `/api/teach/classes/${LOP.id}/assignments`,
             { title: 'Kiểm tra giữa chặng — Tư duy định lượng', kind: 'kiem_tra',
               max_score: 10, due_at: han, status: 'open',
               syllabus_item_id: mucTrong.find((i) => i.kind === 'kiem_tra')?.id ?? null,
               description: 'Làm trong 45 phút, nộp trên lớp.' });
}
if (mucKhung.length && mucTrong.length === mucKhung.length) {
  const muc = mucTrong.find((i) => i.kind === 'bai_tap') || mucTrong[0];
  await viet('giao bài về nhà gắn vào mục khung', `/api/teach/classes/${LOP.id}/assignments`,
             { title: 'Bài về nhà buổi 1 — Hàm số bậc hai', kind: 'bai_tap', max_score: 10,
               due_at: han, status: 'open', syllabus_item_id: muc?.id ?? null,
               description: 'Làm 20 câu, nộp trên hệ thống.' });
}
// Một bài NHÁP để màn Bài tập hiện được đủ hai trạng thái (đang soạn / đã mở cho lớp).
const coNhap = dsBai.some((b) => b.status === 'draft');
ghi('có bài đang soạn (nháp)', coNhap, coNhap ? '' : 'chưa có — màn chỉ hiện một trạng thái');
if (!coNhap) {
  await viet('soạn một bài nháp', `/api/teach/classes/${LOP.id}/assignments`,
             { title: 'Bài luyện thêm — đang soạn', kind: 'bai_tap', max_score: 10,
               status: 'draft', description: 'Chưa mở cho lớp.' });
}

// ── 4 · Học liệu lớp ────────────────────────────────────────────────────────
const dsHl = (await goi(`/api/teach/classes/${LOP.id}/hoc-lieu`)).d?.items || [];
ghi('có học liệu lớp', dsHl.length > 0, `${dsHl.length} tài liệu`);
if (!dsHl.length) {
  for (const t of [
    { ten: 'Đề minh hoạ HSA 2026', url: 'https://example.com/de-minh-hoa.pdf', an: false },
    { ten: 'Đáp án chi tiết (chưa mở cho lớp)', url: 'https://example.com/dap-an.pdf', an: true },
  ]) {
    await viet(`học liệu "${t.ten}"`, `/api/teach/classes/${LOP.id}/hoc-lieu`,
               { ten: t.ten, url: t.url, an: t.an, mo_ta: 'Dữ liệu trình diễn.' });
  }
}

// ── 5 · Bản ghi buổi học ────────────────────────────────────────────────────
const tk = (await goi(`/api/teach/classes/${LOP.id}/ban-ghi`)).d;
ghi('có buổi đã dán link bản ghi', (tk?.buoi || []).length > 0, `${(tk?.buoi || []).length} buổi`);
if (!(tk?.buoi || []).length) {
  const ds = (await goi(`/api/teach/classes/${LOP.id}/sessions`)).d?.sessions || [];
  const daQua = ds.filter((s) => new Date(s.startsAt || s.starts_at) < new Date()).slice(-2);
  ghi('tìm được buổi đã qua để dán link', daQua.length > 0, `${daQua.length} buổi`);
  for (const s of daQua) {
    await viet(`dán link bản ghi buổi #${s.id}`, `/api/teach/sessions/${s.id}`,
               { recording_url: `https://example.com/ban-ghi/${s.id}` }, 'PATCH');
  }
}

// ── 6 · Hộp Yêu cầu ─────────────────────────────────────────────────────────
// AI GỬI mới là điều quan trọng, không phải có bao nhiêu dòng. Lượt gieo 28/09 tạo ba yêu
// cầu bằng thẻ quản trị: hộp đầy, nhưng cột "Người gửi" trống, màn "Hỏi & yêu cầu" của em
// vẫn trắng, và không yêu cầu nào có nút Duyệt — ba dòng nghiệm thu trông như chưa làm.
// Nên nếu có thẻ học viên thì gửi BẰNG VAI ẤY, và gửi kèm một loại CẦN DUYỆT.
const traYc = (await goi('/api/teach/yeu-cau')).d;
const dsYc = traYc?.yeuCau || traYc?.items || [];
const doEm = dsYc.filter((y) => y.hocVien).length;
const canDuyet = dsYc.filter((y) => y.canDuyet).length;
ghi('hộp Yêu cầu có việc do EM gửi', doEm > 0, `${dsYc.length} yêu cầu, ${doEm} do em gửi`);
ghi('có yêu cầu cần DUYỆT (nút Duyệt mới hiện)', canDuyet > 0, `${canDuyet} yêu cầu`);

const theHv = existsSync(`${THE}/tokens_hv.json`)
  ? JSON.parse(readFileSync(`${THE}/tokens_hv.json`, 'utf8')).access : null;
if ((!doEm || !canDuyet) && !theHv) {
  console.log(`${DAU} (không có tokens_hv.json — bỏ qua phần yêu cầu do em gửi.)`);
} else if (!doEm || !canDuyet) {
  const guiHo = async (ten, than) => {
    if (!THAT) { console.log(`     (sẽ POST /api/yeu-cau bằng vai học viên: ${ten})`); return; }
    const r = await fetch(`${API}/api/yeu-cau`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${theHv}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(than), signal: AbortSignal.timeout(180000),
    });
    const chu = await r.text();
    if (r.status >= 400) ghi(`yêu cầu "${ten}"`, false, `HTTP ${r.status} · ${chu.slice(0, 160)}`);
    else console.log(`  ok  em gửi "${ten}"`);
  };
  for (const y of [
    { loai: 'ht_ky_thuat', tieu_de: 'Không mở được bản ghi buổi 3',
      noi_dung: 'Em bấm vào link bản ghi thì báo lỗi.' },
    { loai: 'hoi_dap', tieu_de: 'Nhờ giảng viên giảng lại dạng bài xác suất',
      noi_dung: 'Em vẫn chưa hiểu phần biến cố độc lập.', class_id: LOP.id },
    // Loại này có `viec: 'tu_dong'` — đây là yêu cầu làm màn Duyệt hiện đủ nút Duyệt,
    // ô chọn lớp tới, và dòng "Hệ thống sẽ…" xem trước việc sắp làm.
    { loai: 'tt_chuyen_lop', tieu_de: 'Xin chuyển sang lớp ca tối',
      noi_dung: 'Em đi làm thêm ca chiều, mong trung tâm xếp giúp ca tối.', class_id: LOP.id },
  ]) {
    await guiHo(y.tieu_de, y);
  }
}

// ── 7 · Việc của EM: nộp một bài, mở một bản ghi ────────────────────────────
// Hai màn của giảng viên chỉ nói được điều mình định nói khi có em đã làm gì đó: bảng chấm
// phải phân biệt được "ai chưa nộp" với "chưa ai nộp", và thống kê bản ghi phải phân biệt
// "ai chưa mở" với "chưa ai mở". Khoá vắng mặt khác danh sách rỗng — ở đây cũng vậy.
// Thẻ học viên chỉ dùng được cho lớp em ĐANG HỌC. Gieo vào lớp khác thì mọi cửa trả 404 —
// và 404 ấy là hàng rào làm đúng việc, không phải lỗi. Hỏi trước, đừng để nó thành dấu HỎNG.
const lopCuaEm = theHv ? await (async () => {
  const r = await fetch(`${API}/api/classes`, {
    headers: { Authorization: `Bearer ${theHv}` }, signal: AbortSignal.timeout(180000) });
  if (!r.ok) return [];
  const d = await r.json().catch(() => ({}));
  return (d.classes || d.lop || []).map((c) => c.id);
})() : [];
const emTrongLop = theHv && lopCuaEm.includes(LOP.id);
if (theHv && !emTrongLop) {
  console.log(`${DAU} (thẻ học viên không học lớp #${LOP.id} — bỏ qua phần nộp bài / mở bản ghi.)`);
}
if (emTrongLop) {
  const emLam = async (ten, duong, than) => {
    if (!THAT) { console.log(`     (sẽ POST ${duong} bằng vai học viên)`); return null; }
    const r = await fetch(`${API}${duong}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${theHv}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(than), signal: AbortSignal.timeout(180000),
    });
    const chu = await r.text();
    if (r.status >= 400) { ghi(ten, false, `HTTP ${r.status} · ${chu.slice(0, 160)}`); return null; }
    console.log(`  ok  ${ten}`);
    return chu;
  };

  const cham = (await goi(`/api/teach/classes/${LOP.id}/assignments`)).d?.assignments || [];
  // Bài kiểm tra không nộp qua hệ thống (giảng viên nhập điểm) — chọn bài về nhà đang mở.
  const bai = cham.find((b) => b.kind !== 'kiem_tra' && b.status === 'open');
  const daNop = bai ? (bai.submitted || bai.soNop || 0) > 0 : false;
  ghi('có bài đã có em nộp', daNop, bai ? `bài "${bai.title}"` : 'không có bài mở nào');
  if (bai && !daNop) {
    await emLam('em nộp bài', '/api/assignments',
                { assignment_id: bai.id, content: 'Em làm xong 20 câu, câu 17 em chưa chắc ạ.' });
  }

  const buoiCoBanGhi = ((await goi(`/api/teach/classes/${LOP.id}/ban-ghi`)).d?.buoi || []);
  const daMo = buoiCoBanGhi.filter((b) => (b.daMo ?? 0) > 0).length;
  ghi('có buổi đã có em mở bản ghi', daMo > 0, `${daMo}/${buoiCoBanGhi.length} buổi`);
  if (buoiCoBanGhi.length && !daMo) {
    await emLam('em mở bản ghi', `/api/sessions/${buoiCoBanGhi[0].sessionId}/ban-ghi/da-mo`, {});
  }
}

// ── Tổng ────────────────────────────────────────────────────────────────────
const hong = buoc.filter((b) => !b.dat).length;
console.log(`\n${DAU} ${buoc.length - hong}/${buoc.length} khối đã đủ dữ liệu`);
if (!THAT) console.log(`${DAU} chưa ghi gì. Thêm --that để gieo thật.`);
else console.log(`${DAU} gieo xong — chạy lại kiem_production.mjs để chấm lại.`);
