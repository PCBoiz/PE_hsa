import { serverJson, type HinhDang } from '@/lib/server-api';
import { z } from 'zod';

import AccountsClient, { type ClassLite, type UserRow } from './AccountsClient';

export const metadata = { title: 'Tài khoản | TopHSA' };

type UsersPayload = {
  users: UserRow[];
  total: number;
  page: number;
  per_page: number;
  roles: string[];
};

/* HÌNH DẠNG hai phản hồi trang này đọc. `satisfies HinhDang<…>`: kiểu đang
   dùng ở `AccountsClient` là nguồn; thiếu một khoá bắt buộc trong hình dạng là
   `tsc` đỏ, thừa khoá ở máy chủ thì `looseObject` cho qua (T18 mức 2). */
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
  })),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
  roles: z.array(z.string()),
}) satisfies HinhDang<UsersPayload>;
const HD_CLASSES = z.looseObject({
  classes: z.array(z.looseObject({ id: z.number(), name: z.string(), code: z.string().nullable().optional() })),
}) satisfies HinhDang<{ classes: ClassLite[] }>;

/**
 * Danh sách tài khoản của trung tâm.
 *
 * Dựng sẵn trang đầu ngay trên máy chủ rồi mới trả HTML: mỗi vòng gọi Neon mất
 * khoảng 245 ms, nên để trình duyệt tự gọi sau khi tải xong JavaScript là bắt
 * trợ giảng nhìn khung trống thêm ngần ấy thời gian, mỗi lần mở trang.
 */
export default async function TaiKhoanPage() {
  const [data, classes] = await Promise.all([
    serverJson<UsersPayload>('/api/admin/users?page=1&per_page=25', { requireAuth: true }, HD_USERS),
    serverJson<{ classes: ClassLite[] }>('/api/admin/classes', { requireAuth: true }, HD_CLASSES),
  ]);

  return (
    <AccountsClient
      initial={data.ok ? data.data : { users: [], total: 0, page: 1, per_page: 25, roles: [] }}
      classes={classes.ok ? classes.data.classes : []}
      /* Backend không với tới được là chuyện khác hẳn với "không có tài khoản
         nào" — nói rõ để trợ giảng biết nên gọi kỹ thuật hay tự thêm dữ liệu.
         Nay truyền thẳng CÂU của backend thay vì một câu chung: 403 thiếu
         quyền, 400 tham số sai và 500 sập CSDL trước đây ra cùng một dòng chữ. */
      loi={data.ok ? null : data.message}
    />
  );
}
