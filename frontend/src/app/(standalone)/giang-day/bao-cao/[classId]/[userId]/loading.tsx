import { KhungToBaoCao } from '@/components/KhungToBaoCao';

/**
 * Khung chờ của màn "Báo cáo gửi phụ huynh" phía giảng viên (22/09/2026).
 *
 * `page.tsx` là Server Component đợi Django dựng cả tờ rồi mới gửi HTML. Agent rà
 * đo: bấm "Xem tờ của em này" → 4,4–4,7 s màn hình cũ đứng y nguyên, 0 dấu hiệu
 * đang tải — người dùng bấm lại hoặc tưởng hỏng (F5). Trên production phần dựng
 * tờ chỉ vài trăm mili-giây, nhưng lượt đầu sau khi máy chủ ngủ là cả phút.
 * Cùng bố cục thanh tiêu đề với `page.tsx` để lúc tờ thật tới không nhảy.
 */
export default function DangTaiToCuaEm() {
  return (
    <div className="min-h-dvh bg-ground">
      <main>
        <div className="border-b border-line bg-surface">
          <div className="mx-auto flex max-w-3xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-4">
            <h1 className="min-w-[14ch] flex-1 text-section text-ink">Báo cáo gửi phụ huynh</h1>
          </div>
        </div>
        <div className="mx-auto max-w-3xl px-4 py-6">
          <p role="status" className="mb-4 text-small text-ink-2">Đang dựng tờ báo cáo…</p>
          <KhungToBaoCao />
        </div>
      </main>
    </div>
  );
}
