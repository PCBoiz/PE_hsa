/**
 * NHÓM VAI trên giao diện: `hoc-vien` hay `nhan-su` — và chỉ để GIẤU, không để chặn.
 *
 * ── VÌ SAO (20/09/2026) ─────────────────────────────────────────────────────
 *
 * Đi cùng 22 trang bằng sáu tài khoản sáu vai: quyền ở máy chủ đúng hết (vai
 * nào không được vào thì trang nói rõ vì sao), nhưng NHÂN SỰ mở `/dashboard` là
 * thấy nguyên màn học viên — chuỗi ngày học, "còn 50 ngày tới kỳ thi", nhiệm vụ
 * +XP, kế hoạch học, nhật ký, bảng xếp hạng — cùng các mục "Thi thử", "Bài tập",
 * "Kế hoạch" trên thanh. Một giảng viên không thi HSA; mấy thứ ấy chỉ làm họ
 * phải tự đoán đâu là việc của mình. Anh Sơn yêu cầu: vai nào chỉ thấy biểu
 * tượng, nút, phần của vai đó.
 *
 * ── CƠ CHẾ ──────────────────────────────────────────────────────────────────
 *
 * `<html data-vai-nhom="nhan-su">` + hai luật CSS ở `tailwind.css`:
 *   `[data-chi-hoc-vien]` ẩn với nhân sự, `[data-chi-nhan-su]` ẩn với học viên.
 *
 * Vai chỉ biết SAU khi `/api/user` trả về — đợi nó ở máy chủ là cộng một vòng
 * gọi mạng vào byte đầu tiên của Trang của tôi cho MỌI học viên (LCP đã phải
 * giành từng trăm mili-giây, xem `dashboard/page.tsx`). Nên: lần đầu trong một
 * tab dựng như học viên rồi đổi khi biết vai; từ lần sau, script đầu trang đọc
 * `sessionStorage` và đặt thuộc tính TRƯỚC khi vẽ — không nháy.
 *
 * `sessionStorage` chứ không `localStorage`: máy dùng chung ở trung tâm, người
 * sau mở tab mới là không thừa hưởng nhóm của người trước. Và giá trị nhớ chỉ
 * là điểm xuất phát — hook luôn xác nhận lại bằng tài khoản thật.
 *
 * ĐÂY KHÔNG PHẢI HÀNG RÀO. Ai sửa thuộc tính trong DevTools thì thấy lại nút —
 * và bấm vào vẫn gặp `permission_classes` ở máy chủ, như trước.
 */
import { VAI_HOC_VIEN } from './vaiTro';

export type NhomVai = 'hoc-vien' | 'nhan-su';

export const KHOA_NHOM_VAI = 'pe_nhom_vai';

/** Vai rỗng/không rõ → `null` (chưa biết, không đoán). */
export function nhomCuaVai(vai?: string | null): NhomVai | null {
  if (!vai) return null;
  return vai === VAI_HOC_VIEN ? 'hoc-vien' : 'nhan-su';
}

/** Script chạy trước khi vẽ (đặt trong `<head>` của layout gốc). Chỉ nhận
 *  đúng hai giá trị — chuỗi lạ trong kho không được thành thuộc tính. */
export const SCRIPT_NHOM_VAI =
  `(function(){try{var n=sessionStorage.getItem('${KHOA_NHOM_VAI}');`
  + `if(n==='nhan-su'||n==='hoc-vien')document.documentElement.setAttribute('data-vai-nhom',n)}catch(e){}})();`;
