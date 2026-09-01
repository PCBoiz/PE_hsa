import { NextResponse, type NextRequest } from 'next/server';

import { AT, RT, AT_MAX_AGE, RT_MAX_AGE, refreshTokens } from '@/lib/auth';

/**
 * Làm mới phiên đăng nhập TRƯỚC khi trang được dựng.
 *
 * ── VÌ SAO PHẢI Ở ĐÂY, KHÔNG PHẢI Ở `server-api.ts` ────────────────────────
 *
 * Phiên đáng lẽ sống 8 tiếng (`RT_MAX_AGE`) nhưng thực tế chết sau 30 phút.
 * Đo được ngày 30/08/2026: cookie chỉ còn `pe_rt` hợp lệ, mở
 * `/quan-tri/tai-khoan` → chuyển thẳng về `/login`, y hệt như không có cookie
 * nào. Hai tầng nguyên nhân chồng lên nhau:
 *
 * 1. `pe_at` có `Max-Age` đúng bằng tuổi thọ token (30 phút), nên tới phút thứ
 *    30 trình duyệt TỰ XOÁ nó. `serverFetch` thấy thiếu access là đá người dùng
 *    đi ngay, chưa kịp nhìn tới `pe_rt` vẫn còn sống thêm bảy tiếng rưỡi.
 *
 * 2. Nguy hơn: khi `serverFetch` CÓ làm mới được thì `SIMPLE_JWT` bật
 *    `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION` nên refresh token cũ
 *    bị thu hồi ngay lập tức — mà **Server Component không có quyền ghi
 *    cookie**, nên bản mới không tới được trình duyệt. Lời gọi kế tiếp cầm đúng
 *    cái token vừa bị thu hồi. Tức là việc làm mới ở tầng dựng trang KHÔNG chỉ
 *    vô ích, nó chủ động giết phiên.
 *
 * Middleware là chỗ duy nhất trong App Router vừa chạy trước khi dựng trang,
 * vừa GHI được cookie lên phản hồi. Nó cũng ghi lại header cookie của chính
 * request đang đi, để lượt dựng trang ngay sau đó thấy token mới.
 *
 * Kịch bản thật đã sửa: giảng viên đăng nhập trước giờ dạy, dạy 40 phút, mở sổ
 * điểm danh — trước đây phải gõ lại mật khẩu trước mặt cả lớp.
 *
 * ── VÌ SAO CHẠY Ở NODE, KHÔNG PHẢI EDGE ───────────────────────────────────
 * Mặc định middleware chạy trên Edge, nơi không dùng được mọi thứ `lib/auth.ts`
 * đụng tới. Ở đây chỉ cần `fetch` và đọc biến môi trường nên Node là đủ và
 * tránh được cả một lớp bất ngờ.
 */
export const runtime = 'nodejs';

/** Làm mới sớm 60 giây, để một request đúng lúc token vừa hết hạn không lọt. */
const SOM_HON_GIAY = 60;

/**
 * Token còn hạn không? ĐỌC claim `exp` mà KHÔNG xác minh chữ ký.
 *
 * Không xác minh là có chủ đích: ở đây chỉ cần biết CÓ NÊN đi làm mới hay
 * không. Thẩm quyền thật vẫn nằm ở Django — nó xác minh chữ ký trên mọi lời
 * gọi. Đọc claim ở đây chỉ để khỏi gọi làm mới thừa mỗi lượt tải trang.
 */
function conHan(token: string | undefined): boolean {
  if (!token) return false;
  const phan = token.split('.');
  if (phan.length !== 3) return false;
  try {
    const payload = JSON.parse(Buffer.from(phan[1], 'base64url').toString('utf8')) as {
      exp?: number;
    };
    if (typeof payload.exp !== 'number') return false;
    return payload.exp - SOM_HON_GIAY > Math.floor(Date.now() / 1000);
  } catch {
    return false;
  }
}

export async function middleware(req: NextRequest) {
  const access = req.cookies.get(AT)?.value;
  const refresh = req.cookies.get(RT)?.value;

  // Còn hạn, hoặc không có gì để làm mới → đi tiếp, không đụng vào.
  if (conHan(access) || !refresh) return NextResponse.next();

  /* GỌI `refreshTokens`, KHÔNG tự viết lại lời gọi `/auth/refresh`.
     Bản chép tay trước đây bắt lỗi bằng `try/catch` quanh `fetch` và coi mọi
     phản hồi không-ok là "phiên hết thật". Nhưng `catch` chỉ chạy khi `fetch`
     NÉM — tức mất mạng, DNS hỏng. Một phản hồi **502/503** thì `fetch` thành
     công, `r.ok` là false, và luồng rơi thẳng xuống nhánh XOÁ CẢ HAI COOKIE.

     Đó chính là kịch bản mà `refreshTokens` được viết ra để dập, và nó phân
     biệt rất kỹ `invalid` (401/403 — máy chủ ĐÃ xem token và từ chối) với
     `unreachable` (5xx — máy chủ chưa trả lời được, chưa kết luận gì).

     Không phải giả thiết: Render gói free ngủ sau ~15 phút, nên 502 lúc tỉnh
     dậy là chuyện thường ngày — và hậu quả là giảng viên đang giữa buổi dạy bị
     văng ra màn đăng nhập trong khi refresh token còn sống bảy tiếng rưỡi. */
  const kq = await refreshTokens(refresh);

  if (!kq.ok) {
    if (kq.lyDo === 'unreachable') {
      // Chưa kết luận được gì: đi tiếp với cookie cũ. Trang sẽ tự xử lý như
      // mọi lần backend không với tới được, thay vì đá người dùng ra vô cớ.
      return NextResponse.next();
    }
    // `invalid`: máy chủ đã xem token và từ chối — phiên hết thật. Xoá cookie
    // để lần sau khỏi gọi lại vô ích; trang sẽ tự đưa về đăng nhập.
    const res = NextResponse.next();
    res.cookies.delete(AT);
    res.cookies.delete(RT);
    return res;
  }
  const moi = { access: kq.access, refresh: kq.refresh };

  // Ghi đè cookie TRÊN CHÍNH REQUEST đang đi, để lượt dựng trang ngay sau đây
  // đọc được token mới — không phải chờ tới lượt tải trang kế tiếp.
  const headers = new Headers(req.headers);
  const conLai = req.cookies
    .getAll()
    .filter((c) => c.name !== AT && c.name !== RT)
    .map((c) => `${c.name}=${c.value}`);
  headers.set(
    'cookie',
    [...conLai, `${AT}=${moi.access}`, `${RT}=${moi.refresh ?? refresh}`].join('; '),
  );

  const res = NextResponse.next({ request: { headers } });
  const chung = {
    httpOnly: true,
    sameSite: 'lax' as const,
    path: '/',
    secure: process.env.NODE_ENV === 'production',
  };
  res.cookies.set(AT, moi.access, { ...chung, maxAge: AT_MAX_AGE });
  if (moi.refresh) res.cookies.set(RT, moi.refresh, { ...chung, maxAge: RT_MAX_AGE });
  return res;
}

export const config = {
  /**
   * Chỉ chạy trên các trang, KHÔNG chạy trên `/api/*` và `/auth/*`.
   *
   * Hai nhóm đó đã tự lo phần làm mới ở `src/lib/proxy.ts` — và ở đó thì làm
   * mới được đúng, vì route handler ghi cookie được. Cho middleware chạy chồng
   * lên sẽ thành hai chỗ cùng đổi refresh token một lúc, đúng cuộc đua mà
   * `ROTATE_REFRESH_TOKENS` biến thành đăng xuất.
   */
  matcher: ['/((?!api|auth|_next/static|_next/image|static|favicon.ico).*)'],
};
