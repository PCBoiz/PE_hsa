import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

import AccountsClient, { type ClassLite, type UserRow } from './AccountsClient';
import { docLoc, thamSoLoc } from './loc';

export const metadata = { title: 'Tài khoản | TopHSA' };

type UsersPayload = {
  users: UserRow[];
  total: number;
  page: number;
  per_page: number;
  roles: string[];
  chiHocVien?: boolean;
  nguongNgu?: number[];
};

/* HÌNH DẠNG hai phản hồi trang này đọc. `satisfies HinhDang<…>`: kiểu đang
   dùng ở `AccountsClient` là nguồn; thiếu một khoá bắt buộc trong hình dạng là
   `tsc` đỏ, thừa khoá ở máy chủ thì `looseObject` cho qua (T18 mức 2).
   Bốn khoá dòng của 1.4b (lớp đang học, hoạt động cuối, tiến độ) và `nguongNgu`
   là TUỲ CHỌN: Vercel và Render deploy lệch nhau, backend cũ không trả — cột khi
   ấy vẽ "—", không đổ cả trang. */
const HD_USERS = z.looseObject({
  users: z.array(z.looseObject({
    id: z.number(),
    name: z.string().nullable(),
    email: z.string().nullable(),
    phone: z.string().nullable(),
    role: z.string(),
    status: z.string(),
    must_change_password: z.boolean().optional(),
    password_changed_at: z.string().nullable().optional(),
    created_at: z.string().nullable().optional(),
    classes: z.array(z.string()).optional(),
    studentCode: z.string().nullable().optional(),
    username: z.string().nullable().optional(),
    lopDangHoc: z.array(z.looseObject({
      id: z.number(), name: z.string(), classType: z.string().nullable().optional(),
    })).optional(),
    hoatDongCuoi: z.string().nullable().optional(),
    ngayKhongHoatDong: z.number().nullable().optional(),
    tienDo: z.looseObject({ xong: z.number(), tong: z.number() }).nullable().optional(),
  })),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
  roles: z.array(z.string()),
  chiHocVien: z.boolean().optional(),
  nguongNgu: z.array(z.number()).optional(),
}) satisfies HinhDang<UsersPayload>;
const HD_CLASSES = z.looseObject({
  classes: z.array(z.looseObject({ id: z.number(), name: z.string(), code: z.string().nullable().optional(), startsOn: z.string().nullable().optional() })),
}) satisfies HinhDang<{ classes: ClassLite[] }>;

/**
 * Danh sách tài khoản của trung tâm.
 *
 * Dựng sẵn trang đầu ngay trên máy chủ rồi mới trả HTML: mỗi vòng gọi Neon mất
 * khoảng 245 ms, nên để trình duyệt tự gọi sau khi tải xong JavaScript là bắt
 * trợ giảng nhìn khung trống thêm ngần ấy thời gian, mỗi lần mở trang.
 *
 * Bộ lọc ĐỌC từ URL (1.4b): `?chua_xep_lop=1`, `?khong_hoat_dong=14`, `?q=`… mở thẳng
 * danh sách đã lọc — liên kết "học viên lâu không vào" từ nơi khác dẫn tới đúng tập
 * ấy. Tên tham số URL = tên tham số API, không dịch hai lần.
 */
export default async function TaiKhoanPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const mot = (k: string) => {
    const v = sp[k];
    return ((Array.isArray(v) ? v[0] : v) ?? '').trim();
  };
  const loc = docLoc(mot);
  const qs = thamSoLoc(loc);
  qs.set('page', '1');
  qs.set('per_page', '25');

  const [data, classes] = await Promise.all([
    serverJson<UsersPayload>(`/api/admin/users?${qs}`, { requireAuth: true }, HD_USERS),
    // Danh sách GỌN (§54): `/api/admin/classes` nay phân trang 25 lớp — đọc nó ở
    // đây thì ô lọc lặng lẽ chỉ còn 25 lớp đầu trong khi trung tâm có ~400.
    serverJson<{ classes: ClassLite[] }>('/api/admin/classes/options', { requireAuth: true }, HD_CLASSES),
  ]);

  return (
    <AccountsClient
      initial={data.ok ? data.data : { users: [], total: 0, page: 1, per_page: 25, roles: [] }}
      initialLoc={loc}
      classes={classes.ok ? classes.data.classes : []}
      /* Backend không với tới được là chuyện khác hẳn với "không có tài khoản
         nào" — nói rõ để trợ giảng biết nên gọi kỹ thuật hay tự thêm dữ liệu.
         Nay truyền thẳng CÂU của backend thay vì một câu chung: 403 thiếu
         quyền, 400 tham số sai và 500 sập CSDL trước đây ra cùng một dòng chữ. */
      loi={data.ok ? null : data.message}
    />
  );
}
