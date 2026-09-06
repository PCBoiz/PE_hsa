import Link from 'next/link';

import { BieuTuong } from '@/components/bieuTuong';

/**
 * "Hôm nay cần làm gì" — việc còn tồn, đặt TRÊN mọi con số.
 *
 * ── VÌ SAO CÓ KHỐI NÀY (07/09/2026) ───────────────────────────────────────
 *
 * Anh Sơn: khu vận hành "cần cải tiến để người dùng dễ hiểu hơn".
 *
 * Trang cũ mở đầu bằng bốn ô số rồi hai bảng. Đo dữ liệu production cùng ngày:
 * 6 tài khoản · 1 lớp · 2 học viên đang học. Kết quả là màn hình đầu tiên của
 * người quản lý gồm **6 dấu `—`** và một ô `0%`. Không dấu nào là lỗi hiển
 * thị — hệ thống thật sự chưa có dữ liệu — nhưng đọc thì y hệt một trang hỏng.
 *
 * Vấn đề sâu hơn cái vẻ ngoài: một bảng số trả lời câu "mọi thứ thế nào", mà
 * người học vụ mở trang này lúc 8 giờ sáng đang hỏi câu khác — "hôm nay tôi
 * phải làm gì". Câu ấy trang cũ có trả lời, nhưng chôn dưới bảng, dưới dạng
 * hai dòng chữ vàng nhỏ.
 *
 * Khối này KHÔNG thêm chỉ số mới và KHÔNG gọi thêm API. Nó đọc đúng payload
 * `/api/admin/overview` đang có, và chỉ đổi thứ tự ưu tiên: việc phải làm lên
 * trước, số liệu để đối chiếu xuống sau.
 *
 * ── MỖI VIỆC PHẢI CÓ ĐƯỜNG ĐI ─────────────────────────────────────────────
 *
 * Một dòng "3 buổi chưa điểm danh" mà không bấm được thì mới đi được nửa
 * đường: người ta biết có việc, rồi phải tự đi tìm chỗ làm nó. Nên mỗi mục ở
 * đây bắt buộc có `href`; kiểu dữ liệu ép điều đó, `tsc` bắt khi ai thêm mục
 * mới mà quên.
 */

/** Một việc còn tồn. `href` BẮT BUỘC — xem chú thích đầu tệp. */
export type Viec = {
  /** `gap` = số liệu đang sai vì thiếu nó; `nhac` = nên làm, chưa hỏng gì. */
  nang: 'gap' | 'nhac';
  chu: string;
  /** Vì sao nó quan trọng — nói hậu quả, không nhắc lại con số. */
  phu: string;
  href: string;
  icon: string;
};

const TONE = {
  gap: {
    o: 'border-danger/30 bg-danger/5',
    chu: 'text-danger-ink',
    nhan: 'Cần làm ngay',
  },
  nhac: {
    o: 'border-warning/30 bg-warning/5',
    chu: 'text-warning-ink',
    nhan: 'Nên làm',
  },
} as const;

export function ViecCanLam({ viec }: { viec: Viec[] }) {
  if (viec.length === 0) {
    return (
      <div className="flex items-center gap-3 rounded-md border border-success/30 bg-success/5 px-4 py-3">
        <span className="text-success-ink">
          <BieuTuong ten="check-circle-2" co={20} />
        </span>
        <div>
          <p className="text-subhead text-ink">Không còn việc tồn</p>
          <p className="text-small text-ink-3">
            Mọi buổi đã dạy đều được điểm danh, mọi lớp đều có giảng viên, và
            không ai rời lớp mà chưa ghi lý do.
          </p>
        </div>
      </div>
    );
  }

  return (
    <ul className="flex flex-col gap-2">
      {viec.map((v) => {
        const t = TONE[v.nang];
        return (
          <li key={v.chu}>
            <Link
              href={v.href}
              /* `min-h-11` = 44px, ngưỡng chạm Apple HIG. Cả DÒNG là vùng bấm
                 chứ không riêng chữ: đây là màn hình người ta dùng vội. */
              className={`flex min-h-11 items-center gap-3 rounded-md border px-4 py-3 ${t.o}
                transition-colors hover:brightness-[0.98]`}
            >
              <span className={t.chu}>
                <BieuTuong ten={v.icon} co={18} />
              </span>
              <span className="min-w-0 flex-1">
                <span className={`block text-body font-semibold ${t.chu}`}>{v.chu}</span>
                <span className="block text-small text-ink-3">{v.phu}</span>
              </span>
              <span className="shrink-0 text-ink-3" aria-hidden="true">
                <BieuTuong ten="arrow-right" co={16} />
              </span>
              <span className="sr-only">{t.nhan}</span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
