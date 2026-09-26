'use client';

import { Button } from '@/components/ui';

/**
 * MỘT KHỐI "ai phụ trách lớp này" — dùng chung cho TRỢ GIẢNG và QUẢN LÝ HỌC VỤ.
 *
 * Hai nhóm đi qua đúng một cơ chế: một dòng `class_members` mang vai của người ấy
 * (`teaching/reports.py::_nhan_su_cua_lop`). Nên màn cũng nên là một khối, gọi hai lần —
 * chép khối thứ hai ra là dựng sẵn hai chỗ sẽ lệch nhau sau vài lần sửa.
 *
 * ── GÁN HỌC VỤ KHÔNG PHẢI LÀ CẮT QUYỀN ────────────────────────────────────
 *
 * Quản lý học vụ vẫn thấy MỌI lớp — đó là việc của họ. Khối này trả lời một câu khác:
 * "lớp này ai phụ trách", để khi có chuyện thì biết gọi ai. Chữ trên màn phải nói đúng
 * bấy nhiêu, đừng gợi ý rằng gán xong là người khác hết thấy lớp.
 */
export type NguoiTrongLop = { userId: number; name: string | null; email: string };
export type NguoiChonDuoc = { id: number; name: string | null; email: string };

export default function KhoiNhanSuLop({
  nhan,
  moTaTrong,
  dangCo,
  chonDuoc,
  giaTriChon,
  onChon,
  onGan,
  onGo,
  dangThem,
  khongCoAi,
}: {
  /** "Trợ giảng của lớp" / "Học vụ phụ trách". */
  nhan: string;
  /** Câu hiện khi chưa gán ai — nói bằng lời của người dùng, không phải "rỗng". */
  moTaTrong: string;
  dangCo: NguoiTrongLop[];
  chonDuoc: NguoiChonDuoc[];
  giaTriChon: string;
  onChon: (v: string) => void;
  onGan: () => void;
  onGo: (n: NguoiTrongLop) => void;
  dangThem: boolean;
  /** Câu hiện khi trung tâm chưa có tài khoản nào thuộc vai này. */
  khongCoAi: string;
}) {
  const O = 'min-h-11 rounded-xl border border-line bg-surface px-3 text-small text-ink';
  return (
    <div className="mb-4 rounded-md border border-line bg-sunken p-3" data-khu={`nhan-su-${nhan}`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-label text-ink-3">{nhan}:</span>
        {dangCo.length === 0 && <span className="text-small text-ink-3">{moTaTrong}</span>}
        {dangCo.map((t) => (
          <span
            key={t.userId}
            className="inline-flex items-center gap-1 rounded-full border border-line bg-surface pl-3 text-small text-ink"
          >
            {t.name ?? t.email}
            {/* Vùng chạm ≥ 44px: dấu × trần đo được 16×22 ở 390px (rà 20/09/2026). */}
            <button
              type="button"
              aria-label={`Gỡ ${t.name ?? t.email} khỏi lớp`}
              className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-full text-ink-3 hover:text-danger"
              onClick={() => onGo(t)}
            >
              ×
            </button>
          </span>
        ))}
        <label className="ml-auto flex items-center gap-2">
          <span className="sr-only">Chọn người để gán</span>
          <select
            value={giaTriChon}
            onChange={(e) => onChon(e.target.value)}
            className={`${O} min-w-52`}
          >
            <option value="">— gán thêm —</option>
            {chonDuoc
              .filter((t) => !dangCo.some((g) => g.userId === t.id))
              .map((t) => (
                <option key={t.id} value={String(t.id)}>
                  {t.name ?? t.email}
                </option>
              ))}
          </select>
          <Button size="sm" disabled={!giaTriChon || dangThem} onClick={onGan}>
            Gán
          </Button>
        </label>
      </div>
      {chonDuoc.length === 0 && <p className="mt-2 text-small text-ink-3">{khongCoAi}</p>}
    </div>
  );
}
