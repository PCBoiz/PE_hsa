import NutIn from '@/components/NutIn';
import { ToBaoCao, type BaoCao } from '@/components/ToBaoCao';
import { serverJson } from '@/lib/server-api';

/**
 * Trang PHỤ HUYNH mở từ tin Zalo — không tài khoản, không đăng nhập.
 *
 * ── ĐƯỜNG DẪN NGẮN CÓ CHỦ Ý ───────────────────────────────────────────────
 *
 * `/bc/<chìa>` chứ không `/bao-cao-phu-huynh/<chìa>`: chìa đã 43 ký tự, và cả
 * địa chỉ này sẽ nằm trong một tin nhắn ZNS có giới hạn độ dài. Mỗi ký tự
 * trong tiền tố là một ký tự bớt đi cho phần lời nhắn.
 *
 * ── `noindex` LÀ BẮT BUỘC, KHÔNG PHẢI CẨN THẬN THỪA ──────────────────────
 *
 * Trang này mở được không cần tài khoản, và nội dung là dữ liệu học tập của
 * một đứa trẻ có tên thật. Một phụ huynh dán link vào đâu đó công khai — nhóm
 * lớp trên Facebook, một câu hỏi trên diễn đàn — là đủ để máy tìm kiếm bò tới.
 * `robots` chặn phần lớn đường ấy; hạn dùng và thu hồi lo phần còn lại.
 *
 * ── VÌ SAO KHÔNG CÓ ĐƯỜNG "VỀ TRANG CHỦ" ─────────────────────────────────
 *
 * Người đọc trang này không có tài khoản. Một nút dẫn về `/dashboard` chỉ đưa
 * họ tới màn đăng nhập mà họ không đăng nhập được — tức mời người ta vào một
 * ngõ cụt. Thay vào đó, chân tờ báo cáo nói rõ liên hệ ai (xem `ToBaoCao`).
 */
export const dynamic = 'force-dynamic';
export const metadata = {
  title: 'Báo cáo học tập | TopHSA',
  robots: { index: false, follow: false, nocache: true },
};

export default async function BaoCaoTheoChiaPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;

  /* `requireAuth` để MẶC ĐỊNH (false): thiếu cookie thì đi tiếp chứ không đá
     về `/login` — đúng thứ cần ở đây. Nếu người mở tình cờ đang đăng nhập
     (giảng viên tự kiểm lại link chẳng hạn) thì thẻ vẫn được gắn vào, nhưng
     máy chủ khai `authentication_classes = []` nên nó bị bỏ qua hoàn toàn. */
  const kq = await serverJson<BaoCao>(
    `/api/public/parent-report/${encodeURIComponent(token)}`,
  );

  if (!kq.ok) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-16">
        <h1 className="text-title text-ink">Không mở được báo cáo này</h1>
        {/* Máy chủ trả CÙNG MỘT CÂU cho chìa sai, chìa hết hạn và chìa bị thu
            hồi — nói rõ "đã bị thu hồi" là xác nhận với người cầm link rằng nó
            từng đúng. Ở đây chỉ in lại câu ấy, không đoán thêm. */}
        <p className="mt-2 text-body text-ink-2">{kq.message}</p>
        <p className="mt-6 text-small text-ink-3">
          Nếu bạn nhận đường dẫn này từ trung tâm, hãy nhắn lại cho giảng viên
          phụ trách lớp để nhận đường dẫn mới.
        </p>
      </main>
    );
  }

  const bc = kq.data;

  return (
    <div className="min-h-dvh bg-ground print:bg-white">
      {/* Thanh trên KHÔNG in ra giấy. Nó chỉ có đúng một việc: cho phụ huynh
          lưu tờ này thành PDF để giữ lại hoặc gửi tiếp cho người nhà. */}
      <header className="border-b border-line bg-surface print:hidden">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-4">
          <span className="flex-1 text-section text-ink">Báo cáo học tập</span>
          <NutIn />
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-6 print:max-w-none print:px-0 print:py-0">
        <ToBaoCao bc={bc} />
      </main>
    </div>
  );
}
