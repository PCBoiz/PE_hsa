import { serverJson } from '@/lib/server-api';

import AccountsClient, { type ClassLite, type UserRow } from './AccountsClient';

export const metadata = { title: 'Tài khoản | TopHSA' };

type UsersPayload = {
  users: UserRow[];
  total: number;
  page: number;
  per_page: number;
  roles: string[];
};

/**
 * Danh sách tài khoản của trung tâm.
 *
 * Dựng sẵn trang đầu ngay trên máy chủ rồi mới trả HTML: mỗi vòng gọi Neon mất
 * khoảng 245 ms, nên để trình duyệt tự gọi sau khi tải xong JavaScript là bắt
 * trợ giảng nhìn khung trống thêm ngần ấy thời gian, mỗi lần mở trang.
 */
export default async function TaiKhoanPage() {
  const [data, classes] = await Promise.all([
    serverJson<UsersPayload>('/api/admin/users?page=1&per_page=25', { requireAuth: true }),
    serverJson<{ classes: ClassLite[] }>('/api/admin/classes', { requireAuth: true }),
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
