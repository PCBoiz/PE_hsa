/**
 * Unit test — bộ lọc màn Tài khoản (`quan-tri/tai-khoan/loc.ts`, mục 1.4b, 24/09/2026).
 *
 * Hai nơi đọc cùng hàm: trang MÁY CHỦ dựng trang đầu từ URL (`docLoc`), màn TRÌNH DUYỆT
 * gõ tới đâu lọc tới đó rồi ghi bộ lọc lên URL (`thamSoLoc`). Vòng đi–về URL → bộ lọc →
 * URL phải giữ nguyên, nếu không thì tải lại trang (hay mở link đồng nghiệp gửi) là thấy
 * một danh sách KHÁC cái vừa nhìn — và "chưa xếp lớp" lặng lẽ thành "tất cả".
 *
 * Duyệt theo `LOC_RONG` (bảng trường trong chính mã nguồn), không liệt kê tay: ô lọc
 * thứ sáu thêm sau này tự vào phép kiểm — cùng cách `lop-hoc.test.mjs` làm.
 *
 * Chạy: node e2e/unit/loc-tai-khoan.test.mjs
 */
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const GOC = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const TEP = join(GOC, 'src', 'app', '(standalone)', 'quan-tri', 'tai-khoan', 'loc.ts');
const { CHUA_XEP_LOP, LOC_RONG, docLoc, nhanHoatDong, thamSoLoc } = await import(
  'file://' + TEP.replace(/\\/g, '/')
);

let failures = 0;
function check(name, cond, them) {
  if (cond) console.log('  ✓', name);
  else {
    console.error('  ✗', name, them === undefined ? '' : '→ ' + them);
    failures++;
  }
}

const quaUrl = (loc) => {
  const sp = new URLSearchParams(thamSoLoc(loc).toString());
  return docLoc((k) => (sp.get(k) ?? '').trim());
};

console.log('Vòng đi–về URL giữ nguyên từng ô lọc');
/* Mỗi ô một giá trị KHÁC rỗng — ô nào để rỗng thì vòng đi–về đúng một cách tình cờ. */
const MAU = {
  q: 'Nguyễn An', role: 'Học viên', status: 'suspended', lop: '42', khongHoatDong: '14',
  tinhTrangHoc: 'da_nghi', hocPhi: 'sap_het',
};
check('mẫu phủ MỌI ô của LOC_RONG', Object.keys(LOC_RONG).every((k) => MAU[k]),
  Object.keys(LOC_RONG).filter((k) => !MAU[k]).join(', '));
for (const k of Object.keys(LOC_RONG)) {
  const loc = { ...LOC_RONG, [k]: MAU[k] };
  check(`ô "${k}" đi–về`, JSON.stringify(quaUrl(loc)) === JSON.stringify(loc), JSON.stringify(quaUrl(loc)));
}
check('cả bộ đi–về', JSON.stringify(quaUrl(MAU)) === JSON.stringify(MAU));
check('bộ rỗng → URL rỗng', thamSoLoc(LOC_RONG).toString() === '');

console.log('"Chưa xếp lớp" và "lớp X" loại trừ nhau');
const chua = thamSoLoc({ ...LOC_RONG, lop: CHUA_XEP_LOP });
check('chưa xếp lớp → chua_xep_lop=1, không class_id', chua.get('chua_xep_lop') === '1' && !chua.has('class_id'),
  chua.toString());
check('lớp X → class_id, không chua_xep_lop', (() => {
  const s = thamSoLoc({ ...LOC_RONG, lop: '7' });
  return s.get('class_id') === '7' && !s.has('chua_xep_lop');
})());
check('URL mang cả hai → "chưa xếp lớp" thắng (ô Lớp chỉ giữ được một giá trị)',
  docLoc((k) => ({ chua_xep_lop: '1', class_id: '7' }[k] ?? '')).lop === CHUA_XEP_LOP);
check('chua_xep_lop=0 không phải đang lọc', docLoc((k) => ({ chua_xep_lop: '0' }[k] ?? '')).lop === '');
check('q chỉ khoảng trắng không gửi', !thamSoLoc({ ...LOC_RONG, q: '   ' }).has('q'));

console.log('Chữ cột "Hoạt động cuối"');
check('backend cũ (không có khoá) → "—", KHÔNG "chưa vào"', nhanHoatDong(undefined) === '—');
check('null → "chưa vào"', nhanHoatDong(null) === 'chưa vào');
check('0 → "hôm nay"', nhanHoatDong(0) === 'hôm nay');
check('1 → "hôm qua"', nhanHoatDong(1) === 'hôm qua');
check('3 → "3 ngày trước"', nhanHoatDong(3) === '3 ngày trước');

if (failures) {
  console.error(`\n${failures} phép kiểm hỏng`);
  process.exit(1);
}
console.log('\nĐạt.');
