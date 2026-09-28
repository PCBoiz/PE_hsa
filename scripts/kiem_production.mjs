/**
 * KIỂM PRODUCTION — chạy TRƯỚC buổi trình diễn, và sau mỗi lượt đẩy `master`.
 *
 *     node scripts/kiem_production.mjs                    # phần công khai, không cần thẻ
 *     PE_THE=<thư mục thẻ> node scripts/kiem_production.mjs   # thêm phần cần đăng nhập
 *
 * ── VÌ SAO CÓ TỆP NÀY (27/09/2026) ─────────────────────────────────────────
 *
 * Hai chuyện xảy ra cùng ngày:
 *
 * ① **CI trên GitHub đã chết từ lâu mà không ai biết.** Chú giải công khai của GitHub nói
 *    thẳng: *"The job was not started because your account is locked due to a billing
 *    issue."* Ba workflow — CI, giữ ấm, sao lưu CSDL — đều hỏng ở MỌI lượt. Tức bốn thứ CI
 *    vẫn chạy mà cổng `pre-push` không chạy đã không còn ai chạy: pytest toàn bộ,
 *    `pnpm build` thật, `pip-audit`, `pnpm audit`.
 *
 * ② **`erp` xanh không có nghĩa production ổn.** Anh Sơn nói đúng một câu: *"erp ổn nhưng
 *    nếu production chưa thì cũng như không"*. Và hoá ra bộ đo màn của mình ghim cookie vào
 *    `localhost`, nên chưa lần nào đo được bản thật.
 *
 * Tệp này kiểm THỨ ĐÃ DEPLOY, bằng lời gọi thật tới hai tên miền thật. Nó không thay CI —
 * nó trả lời đúng một câu mà CI không trả lời được: *bản đang chạy có dùng được không?*
 *
 * ── BA NHÓM CÂU HỎI ───────────────────────────────────────────────────────
 *
 *   A · SỐNG      — máy chủ trả lời chưa, mất bao lâu (gói Render free ngủ sau 15 phút,
 *                   lượt gọi đầu mất 40–85 giây; đó là ĐANG THỨC DẬY, không phải chết).
 *   B · KÍN       — những cửa PHẢI đóng thì đang đóng chưa (audit 27/09 tìm ra 28 đường
 *                   tài khoản của allauth mở toang trên production).
 *   C · ĐỦ DỮ LIỆU — sáu khối làm buổi demo trông như "chưa làm" nếu rỗng. Cần thẻ quản trị.
 *
 * Mã thoát: 0 = mọi câu ĐẠT · 1 = có câu hỏng · 2 = không đo được (máy chủ không trả lời).
 */
import { existsSync, readFileSync } from 'node:fs';

const API = process.env.PE_API || 'https://pe-hsa-backend.onrender.com';
const WEB = process.env.PE_WEB || 'https://pe-hsa.vercel.app';
const THU_MUC_THE = process.env.PE_THE || null;

const buoc = [];
function ghi(nhom, ten, dat, chiTiet) {
  buoc.push({ nhom, dat });
  console.log(`${dat ? 'ĐẠT ' : 'HỎNG'} ${nhom} · ${ten}${chiTiet ? ` — ${chiTiet}` : ''}`);
}

/** Một lời gọi, kèm thời gian. `tran` rộng vì cold-start của gói free là 40–85 giây. */
async function goi(url, { tran = 120000, dau = null, method = 'GET' } = {}) {
  const bo = AbortSignal.timeout(tran);
  const t0 = Date.now();
  try {
    const r = await fetch(url, {
      method,
      headers: dau ? { Authorization: `Bearer ${dau}` } : {},
      redirect: 'manual',
      signal: bo,
    });
    return { ma: r.status, giay: (Date.now() - t0) / 1000, than: await r.text().catch(() => '') };
  } catch (e) {
    return { ma: 0, giay: (Date.now() - t0) / 1000, than: String(e).slice(0, 120) };
  }
}

function docThe(ten) {
  if (!THU_MUC_THE) return null;
  const d = `${THU_MUC_THE}/${ten}`;
  if (!existsSync(d)) return null;
  try {
    const j = JSON.parse(readFileSync(d, 'utf8'));
    return j.access || Object.values(j)[0] || null;
  } catch {
    return null;
  }
}

// ── A · SỐNG ────────────────────────────────────────────────────────────────
const suc_khoe = await goi(`${API}/api/health`);
if (suc_khoe.ma === 0) {
  console.log(`\nKHÔNG ĐO ĐƯỢC — ${API} không trả lời sau 120 giây (${suc_khoe.than}).`);
  console.log('Máy chủ có thể đang thức dậy hoặc Render đang hỏng. Mở Render → Logs.');
  process.exit(2);
}
ghi('SỐNG', 'máy chủ trả lời', suc_khoe.ma === 200, `${suc_khoe.ma} sau ${suc_khoe.giay.toFixed(1)}s`);
if (suc_khoe.giay > 15) {
  console.log('     (lượt này phải ĐÁNH THỨC máy chủ — nó vừa ngủ. Khách bấm lúc ấy cũng chờ chừng này.)');
}
const trang = await goi(`${WEB}/login`);
ghi('SỐNG', 'màn đăng nhập mở được', trang.ma === 200, `${trang.ma} sau ${trang.giay.toFixed(1)}s`);
const proxy = await goi(`${WEB}/api/user`);
ghi('SỐNG', 'proxy của màn nối được máy chủ', proxy.ma === 401 && proxy.than.includes('Chưa đăng nhập'),
    `${proxy.ma} · ${proxy.than.slice(0, 40)}`);

// ── B · KÍN ─────────────────────────────────────────────────────────────────
// Audit 27/09: `allauth` từng mở nguyên bộ giao diện tài khoản trên tên miền backend —
// đăng nhập, đổi mật khẩu, quên mật khẩu — ngoài MỌI hàng rào của dự án.
for (const duong of ['/accounts/login/', '/accounts/signup/', '/accounts/password/reset/',
                     '/accounts/password/change/', '/accounts/email/']) {
  const r = await goi(`${API}${duong}`);
  ghi('KÍN', `cửa thư viện ${duong} đã đóng`, r.ma === 404, `HTTP ${r.ma}`);
}
const gg = await goi(`${API}/accounts/google/login/`);
ghi('KÍN', 'đăng nhập Google vẫn sống', gg.ma === 302, `HTTP ${gg.ma}`);
const rieng = await goi(`${API}/api/posts`);
ghi('KÍN', 'cửa cần đăng nhập thì đòi đăng nhập', rieng.ma === 401, `HTTP ${rieng.ma}`);
const bia = await goi(`${API}/duong-khong-ton-tai-${Date.now()}`);
ghi('KÍN', 'đường không có trả 404', bia.ma === 404, `HTTP ${bia.ma}`);

// ── C · ĐỦ DỮ LIỆU ──────────────────────────────────────────────────────────
// Sáu khối dưới đây đều là "mã chạy đúng mà dữ liệu rỗng" — mỗi khối rỗng là một dòng
// nghiệm thu mở ra trắng, và khách kết luận là chưa làm. Đo 27/09 trên production: khung
// chương trình = 0 ở CẢ BA môn, tức bộ dữ liệu ở đó có từ trước E1.
const theAd = docThe('tokens_ad.json');
if (!theAd) {
  console.log('\n(Bỏ qua nhóm ĐỦ DỮ LIỆU: chưa có thẻ quản trị.'
    + ' Đặt PE_THE trỏ tới thư mục chứa tokens_ad.json — ĐỪNG để thư mục ấy trong repo.)');
} else {
  const json = async (d) => {
    const r = await goi(`${API}${d}`, { dau: theAd });
    try { return { ma: r.ma, d: JSON.parse(r.than) }; } catch { return { ma: r.ma, d: null }; }
  };

  const lop = await json('/api/admin/classes');
  const dsLop = lop.d?.classes || [];
  ghi('DỮ LIỆU', 'có lớp để mở ra xem', dsLop.length > 0, `${dsLop.length} lớp`);

  const khung = await json('/api/admin/chuong-trinh/khung');
  const soKhung = (khung.d?.mon || []).reduce((n, m) => n + (m.versions || []).length, 0);
  ghi('DỮ LIỆU', 'có khung chương trình', soKhung > 0,
      soKhung ? `${soKhung} khung` : 'KHÔNG CÓ KHUNG NÀO — màn Chương trình, §74 và sổ đầu bài đều trống');

  // Lớp mẫu: lớp đông nhất là lớp bộ trình diễn dựng ra để trình bày.
  const mau = [...dsLop].sort((a, b) => (b.members || 0) - (a.members || 0))[0];
  if (mau) {
    const ct = await json(`/api/teach/classes/${mau.id}/chuong-trinh`);
    ghi('DỮ LIỆU', `lớp "${mau.name}" đã nhận khung`, Boolean(ct.d?.khung),
        ct.d?.khung ? `${(ct.d.buoiKhung || []).length} buổi khung` : 'chưa nhận khung');

    const bt = await json(`/api/teach/classes/${mau.id}/assignments`);
    const bai = bt.d?.assignments || [];
    ghi('DỮ LIỆU', 'có bài tập', bai.length > 0, `${bai.length} bài`);
    ghi('DỮ LIỆU', 'có bài KIỂM TRA (nút "Nhập điểm" mới hiện)',
        bai.some((b) => b.kind === 'kiem_tra'), `${bai.filter((b) => b.kind === 'kiem_tra').length} bài`);

    const bg = await json(`/api/teach/classes/${mau.id}/ban-ghi`);
    ghi('DỮ LIỆU', 'có bản ghi buổi học', (bg.d?.buoi || []).length > 0,
        `${(bg.d?.buoi || []).length} buổi có bản ghi`);

    const hl = await json(`/api/teach/classes/${mau.id}/hoc-lieu`);
    ghi('DỮ LIỆU', 'có học liệu', (hl.d?.items || []).length > 0, `${(hl.d?.items || []).length} tài liệu`);
  }

  const yc = await json('/api/teach/yeu-cau');
  const dsYc = yc.d?.items || yc.d?.yeuCau || yc.d?.results || [];
  ghi('DỮ LIỆU', 'hộp Yêu cầu có việc', dsYc.length > 0, `${dsYc.length} yêu cầu`);
}

// ── Tổng ────────────────────────────────────────────────────────────────────
const hong = buoc.filter((b) => !b.dat);
console.log(`\n${buoc.length - hong.length}/${buoc.length} câu ĐẠT`);
if (hong.length) {
  const theoNhom = {};
  for (const b of hong) theoNhom[b.nhom] = (theoNhom[b.nhom] || 0) + 1;
  console.log('hỏng theo nhóm: ' + Object.entries(theoNhom).map(([k, v]) => `${k} ${v}`).join(' · '));
  if (theoNhom['DỮ LIỆU']) {
    console.log('\nNhóm DỮ LIỆU hỏng thì mã vẫn đúng — chạy trên Render Shell:'
      + '\n   python manage.py du_lieu_mau --lam-moi');
  }
  process.exit(1);
}
