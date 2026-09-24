import { expect, test, type Page } from '@playwright/test';

import { LY_DO_BO_QUA, LY_DO_THIEU_VAI, goiApi, taiKhoanCuaVai, vaoBangThe, vaoTheoVai } from './helpers';

/**
 * DANH SÁCH HỌC VIÊN (1.4b, 24/09/2026) — màn Vận hành → Tài khoản, đi bằng GIAO DIỆN,
 * hai khổ máy. CHỈ ĐỌC.
 *
 * Ghi chú họp TopHSA: "quản lý lớp là priority số 1, rồi quản lý học sinh". Màn Tài khoản
 * thêm cột Lớp (kèm chip Gia sư), Hoạt động cuối, Tiến độ; ô lọc "Chưa xếp lớp" (một lựa
 * chọn của ô Lớp) và "Lâu không vào ≥ N ngày"; nút Chuyển lớp mở lại hộp của màn Lớp học.
 * `teaching/tests_danh_sach_hoc_vien.py` canh phía máy chủ (định nghĩa, số câu). Tệp này
 * canh phần view không thấy: nhãn ô lọc có hiện không, chọn lọc có lên URL không, số dòng
 * màn hình báo có khớp tổng của máy chủ không, hộp chuyển lớp có mở đúng lớp đi không.
 *
 * KHÔNG ghi gì: chặn theo PHƯƠNG THỨC (RULES §22) — mọi lời gọi không phải GET/HEAD bị giả
 * lập và GHI LẠI, cuối mỗi phép kiểm khẳng định danh sách ấy rỗng. Hộp chuyển lớp chỉ được
 * mở rồi đóng, không bấm "Chuyển lớp" trong hộp.
 */

const HOC_VU = 'Quản lý học vụ';
const DUONG = '/quan-tri/tai-khoan';

/** Chặn mọi lời gọi GHI (sau khi đã đăng nhập) và trả về danh sách lời ghi bị chặn. */
async function chanGhi(page: Page): Promise<string[]> {
  const ghiLen: string[] = [];
  await page.route('**/api/**', (r, req) => {
    const m = req.method();
    if (m === 'GET' || m === 'HEAD') return r.fallback();
    ghiLen.push(`${m} ${req.url()}`);
    return r.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });
  return ghiLen;
}

type Dong = {
  id: number; name: string | null; role: string;
  lopDangHoc?: { id: number; name: string; classType?: string | null }[];
  hoatDongCuoi?: string | null; ngayKhongHoatDong?: number | null;
  tienDo?: { xong: number; tong: number } | null;
};
type DanhSach = { users: Dong[]; total: number; nguongNgu?: number[]; chiHocVien?: boolean };

/** Tổng trong dòng phụ dưới tiêu đề thẻ "Tài khoản": "N học viên khớp bộ lọc …". */
async function tongTrenMan(page: Page): Promise<number> {
  const dong = page.getByText(/\d+ (học viên|tài khoản) khớp bộ lọc hiện tại/);
  await expect(dong).toBeVisible({ timeout: 30_000 });
  return Number((await dong.innerText()).match(/(\d+) (học viên|tài khoản)/)![1]);
}

test('học vụ: ô lọc có nhãn và "Tất cả", cột mới hiện, "Chưa xếp lớp" + "Lâu không vào" lọc đúng tổng máy chủ', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  const ghiLen = await chanGhi(page);

  // Máy chủ trước: khoá mới có mặt, mốc từ máy chủ.
  const api = await goiApi(page, 'GET', '/api/admin/users?page=1&per_page=100');
  expect(api.ma).toBe(200);
  const du = api.du as DanhSach;
  expect(du.nguongNgu).toEqual([7, 14, 30]);
  expect(du.users.length).toBeGreaterThan(0);
  for (const u of du.users) {
    expect(Object.keys(u)).toEqual(expect.arrayContaining(['lopDangHoc', 'hoatDongCuoi', 'ngayKhongHoatDong', 'tienDo']));
  }

  await page.goto(DUONG, { waitUntil: 'domcontentloaded' });
  await expect(page.locator('[data-chan]')).toHaveCount(0);
  const loc = page.getByRole('search', { name: 'Lọc danh sách tài khoản' });
  // Góp ý TopHSA: ô chọn phải có NHÃN HIỆN, lựa chọn đầu "Tất cả" — không "Mọi …".
  for (const nhan of ['Trạng thái', 'Lớp', 'Lâu không vào']) {
    const o = loc.getByRole('combobox', { name: nhan, exact: true });
    await expect(o).toBeVisible();
    await expect(o.locator('option').first()).toHaveText('Tất cả');
  }
  await expect(loc.getByRole('combobox', { name: 'Vai trò', exact: true }), 'học vụ không có ô lọc vai').toHaveCount(0);
  await expect(page.locator('option', { hasText: /^Mọi / })).toHaveCount(0);
  await expect(loc.getByRole('combobox', { name: 'Lâu không vào', exact: true }).locator('option'))
    .toHaveText(['Tất cả', '≥ 7 ngày', '≥ 14 ngày', '≥ 30 ngày']);

  // Cột mới (dạng bảng ở máy tính; dạng thẻ ở điện thoại thì nhãn nằm trong từng ô).
  const bang = page.getByRole('table');
  await expect(bang.getByText('Hoạt động cuối').first()).toBeAttached();
  await expect(bang.getByText('Tiến độ').first()).toBeAttached();
  const tongDau = await tongTrenMan(page);
  expect(tongDau).toBe(du.total);

  // "Chưa xếp lớp" — một lựa chọn của ô Lớp. Lên URL, và tổng = tổng máy chủ.
  await loc.getByRole('combobox', { name: 'Lớp', exact: true }).selectOption({ label: 'Chưa xếp lớp' });
  await page.waitForURL((u) => u.searchParams.get('chua_xep_lop') === '1');
  const chua = (await goiApi(page, 'GET', '/api/admin/users?chua_xep_lop=1&per_page=100')).du as DanhSach;
  await expect.poll(() => tongTrenMan(page)).toBe(chua.total);
  expect(chua.users.every((u) => (u.lopDangHoc ?? []).length === 0), 'lọc và cột Lớp cùng một luật').toBe(true);
  if (chua.total > 0) {
    await expect(bang.getByText('Chưa xếp lớp').first()).toBeVisible();
    await expect(bang.getByRole('button', { name: /^Chuyển lớp cho / }), 'em chưa có lớp thì không có gì để chuyển').toHaveCount(0);
  } else {
    await expect(page.getByText('Không có tài khoản nào khớp')).toBeVisible();
  }

  // Thêm "Lâu không vào ≥ 14 ngày" — hai ô lọc cộng dồn, cả hai nằm trên URL.
  await loc.getByRole('combobox', { name: 'Lâu không vào', exact: true }).selectOption({ label: '≥ 14 ngày' });
  await page.waitForURL((u) => u.searchParams.get('khong_hoat_dong') === '14' && u.searchParams.get('chua_xep_lop') === '1');
  const ca2 = (await goiApi(page, 'GET', '/api/admin/users?chua_xep_lop=1&khong_hoat_dong=14&per_page=100')).du as DanhSach;
  await expect.poll(() => tongTrenMan(page)).toBe(ca2.total);
  expect(ca2.users.every((u) => u.ngayKhongHoatDong === null || (u.ngayKhongHoatDong ?? 0) >= 14),
    'mọi em trong danh sách "≥ 14 ngày" phải có lần cuối cách ≥ 14 ngày, hoặc chưa vào').toBe(true);

  // Tải lại trang: bộ lọc đọc lại từ URL, ô chọn giữ đúng giá trị.
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(loc.getByRole('combobox', { name: 'Lớp', exact: true })).toHaveValue('chua-xep-lop');
  await expect(loc.getByRole('combobox', { name: 'Lâu không vào', exact: true })).toHaveValue('14');
  expect(await tongTrenMan(page)).toBe(ca2.total);

  expect(ghiLen, 'phép kiểm chỉ đọc không được gửi lời ghi nào').toEqual([]);
});

test('học vụ: nút Chuyển lớp mở hộp chuyển lớp đúng lớp đi (mở rồi đóng — không chuyển)', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  const ghiLen = await chanGhi(page);

  const du = (await goiApi(page, 'GET', '/api/admin/users?page=1&per_page=100')).du as DanhSach;
  const motLop = du.users.find((u) => (u.lopDangHoc ?? []).length === 1);
  test.skip(!motLop, 'không có học viên nào đúng một lớp trên trang đầu');

  await page.goto(`${DUONG}?q=${encodeURIComponent(motLop!.name ?? '')}`, { waitUntil: 'domcontentloaded' });
  const nut = page.getByRole('button', { name: `Chuyển lớp cho ${motLop!.name}` }).first();
  await expect(nut).toBeVisible({ timeout: 30_000 });
  await nut.click();
  // Tìm hộp theo TÊN TRUY CẬP (= tiêu đề, `aria-labelledby` của `components/ui/Modal.tsx`).
  const hop = page.getByRole('dialog', { name: `Chuyển ${motLop!.name} sang lớp khác` });
  await expect(hop).toBeVisible();
  await expect(hop.getByText(`Đang học: ${motLop!.lopDangHoc![0].name}`)).toBeVisible();
  await hop.getByRole('button', { name: 'Huỷ' }).click();
  await expect(hop).toBeHidden();

  expect(ghiLen, 'mở/đóng hộp không được gửi lời ghi nào').toEqual([]);
});

test('học vụ: em học HAI lớp → hỏi "từ lớp nào" trước, rồi mở hộp với đúng lớp đã chọn', async ({ page }) => {
  test.skip(!taiKhoanCuaVai(HOC_VU), LY_DO_THIEU_VAI);
  expect(await vaoTheoVai(page, HOC_VU)).toBe(true);
  const ghiLen = await chanGhi(page);

  const du = (await goiApi(page, 'GET', '/api/admin/users?page=1&per_page=100')).du as DanhSach;
  const em = du.users.find((u) => (u.lopDangHoc ?? []).length === 1);
  test.skip(!em, 'không có học viên nào đúng một lớp trên trang đầu');
  /* Dữ liệu thử KHÔNG có em nào học hai lớp (đo 24/09/2026: 0 trên 55 học viên), mà dựng
     một em như thế là GHI. Nên giả lập ở TẦNG TRÌNH DUYỆT: sửa phản hồi GET danh sách mà
     màn hình tự gọi (gõ ô Tìm), thêm cho em một lớp thứ hai. Chỉ mở rồi đóng hộp — lớp giả
     không bao giờ tới máy chủ (mọi lời ghi đã bị `chanGhi` chặn và đếm). Route đăng ký SAU
     `chanGhi` nên chạy TRƯỚC nó. */
  const LOP_2 = { id: -1, name: 'Lớp thứ hai giả lập', classType: 'gia_su' };
  await page.route('**/api/admin/users?**', async (r) => {
    const res = await r.fetch();
    const d = (await res.json()) as DanhSach;
    for (const u of d.users) if (u.id === em!.id) u.lopDangHoc = [...(u.lopDangHoc ?? []), LOP_2];
    await r.fulfill({ response: res, json: d });
  });

  await page.goto(DUONG, { waitUntil: 'domcontentloaded' });
  await page.getByRole('textbox', { name: 'Tìm tài khoản' }).fill(em!.name ?? '');
  const nut = page.getByRole('button', { name: `Chuyển lớp cho ${em!.name}` }).first();
  // Hai lớp hiện trong ô Lớp (chip "Gia sư" cho lớp gia sư) rồi mới bấm.
  await expect(page.getByRole('table').getByText(LOP_2.name)).toBeVisible({ timeout: 30_000 });
  await nut.click();
  const hoi = page.getByRole('dialog', { name: `Chuyển ${em!.name} từ lớp nào?` });
  const lua = hoi.getByRole('list', { name: 'Lớp em đang học' }).getByRole('button');
  await expect(lua).toHaveCount(2);
  await lua.filter({ hasText: LOP_2.name }).click();
  const hop = page.getByRole('dialog', { name: `Chuyển ${em!.name} sang lớp khác` });
  await expect(hop.getByText(`Đang học: ${LOP_2.name}`)).toBeVisible();
  await hop.getByRole('button', { name: 'Huỷ' }).click();
  await expect(hop).toBeHidden();

  expect(ghiLen, 'mở/đóng hộp không được gửi lời ghi nào').toEqual([]);
});

test('quản trị viên: ô Vai trò có nhãn + "Tất cả"; Tải CSV mang theo bộ lọc mới', async ({ page }) => {
  // Chặn TRƯỚC khi vào: vào bằng thẻ không cần lời ghi nào (khác đăng nhập mật khẩu).
  const ghiLen = await chanGhi(page);
  const vao = await vaoBangThe(page);
  test.skip(!vao, LY_DO_BO_QUA);

  await page.goto(`${DUONG}?khong_hoat_dong=30`, { waitUntil: 'domcontentloaded' });
  test.skip(await page.locator('[data-chan]').count() > 0, 'thẻ không phải quản trị viên');
  const loc = page.getByRole('search', { name: 'Lọc danh sách tài khoản' });
  const vai = loc.getByRole('combobox', { name: 'Vai trò', exact: true });
  await expect(vai).toBeVisible({ timeout: 30_000 });
  await expect(vai.locator('option').first()).toHaveText('Tất cả');
  await expect(loc.getByRole('combobox', { name: 'Lâu không vào', exact: true })).toHaveValue('30');
  const csv = page.getByRole('link', { name: 'Tải Excel (CSV)' });
  await expect(csv).toHaveAttribute('href', /khong_hoat_dong=30/);
  const du = (await goiApi(page, 'GET', '/api/admin/users?khong_hoat_dong=30&per_page=1')).du as DanhSach;
  expect(await tongTrenMan(page)).toBe(du.total);

  expect(ghiLen).toEqual([]);
});
