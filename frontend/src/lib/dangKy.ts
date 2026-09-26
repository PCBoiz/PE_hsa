/**
 * TỰ ĐĂNG KÝ (§73, E5) — hình dạng phản hồi của ba cửa `/auth/dang-ky`,
 * `/auth/xac-thuc-email`, `/auth/gui-lai-xac-thuc`.
 *
 * Danh mục "nguồn biết tới trung tâm" do MÁY CHỦ trả (`GET /auth/dang-ky`, lấy từ
 * `teaching/ho_so.NGUON_TUYEN_SINH`, khớp CHECK `users_enroll_source_check` §51).
 * Gõ lại tám mục ấy ở đây là bản thứ hai sẽ trôi, rồi một lựa chọn trên màn sẽ bị
 * CSDL từ chối bằng một lỗi 500 không ai hiểu (RULES §7).
 *
 * `zod/mini`: tệp này được cả trang máy chủ lẫn component `'use client'` nhập
 * (`e2e/unit/zod-phia-trinh-duyet.test.mjs`).
 */
import * as z from 'zod/mini';

export const HD_LUA_CHON_DANG_KY = z.looseObject({
  nguon: z.array(z.looseObject({ ma: z.string(), nhan: z.string() })),
});
export type LuaChonDangKy = z.infer<typeof HD_LUA_CHON_DANG_KY>;

/** Ô nào trên phiếu — khớp khoá `errors` mà `accounts/tu_dang_ky._kiem` trả về. */
export type OPhieu = 'name' | 'email' | 'phone' | 'password' | 'nguon';

/** Khớp `accounts/validators.validate_password_field` (8–128 ký tự). */
export const MK_TOI_THIEU = 8;

/**
 * Câu nói khi mạng đứt hoặc máy chủ trả thứ không đọc được.
 *
 * MỘT chuỗi cho cả ba màn của luồng đăng ký: ba màn tự viết ba câu thì người dùng
 * gặp cùng một sự cố ở hai chỗ lại đọc hai lời khác nhau và tưởng là hai lỗi.
 */
export const CAU_MAT_MANG = 'Không kết nối được tới máy chủ. Kiểm tra mạng rồi thử lại.';
export const CAU_QUA_NHIEU =
  'Đã có quá nhiều lượt gửi từ mạng này. Đợi khoảng một giờ rồi thử lại, hoặc nhắn học vụ TopHSA.';
