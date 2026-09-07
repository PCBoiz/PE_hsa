'use client';

import { useState } from 'react';

import DuongDanDaCap from './DuongDanDaCap';
import TaoDuongDan from './TaoDuongDan';

/**
 * Ghép "cấp chìa" với "danh sách chìa đang hiệu lực" thành một khối.
 *
 * ── VÌ SAO CẦN MỘT LỚP RIÊNG ──────────────────────────────────────────────
 *
 * Trang cha là Server Component (`page.tsx` dựng ở máy chủ để tờ báo cáo có
 * sẵn trong HTML, in ra được ngay). Server Component không giữ được `useState`,
 * nên nó không thể là chỗ nối "vừa cấp xong" của khối trên với "nạp lại" của
 * khối dưới.
 *
 * Lớp mỏng này giữ đúng một con số đếm. Cấp chìa xong thì tăng nó lên, danh
 * sách thấy số đổi thì nạp lại từ máy chủ.
 *
 * ── VÌ SAO KHÔNG GỘP HẲN HAI KHỐI LÀM MỘT ────────────────────────────────
 *
 * Chúng làm hai việc khác nhau và hỏng theo hai kiểu khác nhau: cấp chìa là
 * một hành động ghi, đọc danh sách là một phép đọc lặp lại. Gộp lại thì một
 * lỗi mạng lúc đọc danh sách sẽ nuốt luôn ô đường dẫn vừa cấp — mà đó đúng là
 * thứ người dùng đang cần chép.
 */
export default function KhoiDuongDan({
  classId,
  userId,
  coSoPhuHuynh,
}: {
  classId: string;
  userId: string;
  coSoPhuHuynh: boolean;
}) {
  const [lan, setLan] = useState(0);

  return (
    <div className="flex flex-col gap-3">
      <TaoDuongDan
        classId={classId}
        userId={userId}
        coSoPhuHuynh={coSoPhuHuynh}
        khiCapXong={() => setLan((v) => v + 1)}
      />
      <DuongDanDaCap classId={classId} userId={userId} lamMoiKhi={lan} />
    </div>
  );
}
