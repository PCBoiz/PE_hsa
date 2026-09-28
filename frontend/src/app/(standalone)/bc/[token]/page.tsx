import NutIn from '@/components/NutIn';
import TaiLaiTrang from '@/components/TaiLaiTrang';
import { ToBaoCao, type BaoCao } from '@/components/ToBaoCao';
import YeuCauPhuHuynh from '@/components/YeuCauPhuHuynh';
import { HD_BAO_CAO } from '@/lib/hinhDang';
import { serverJson } from '@/lib/server-api';
import { HD_PHU_HUYNH, type PhuHuynhDS } from '@/lib/yeuCau';

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
  /* Tờ báo cáo và hộp yêu cầu của link (E3) gọi SONG SONG. Hộp yêu cầu hỏng (máy chủ cũ
     chưa có tuyến — Vercel lên trước Render) thì tờ vẫn hiện, chỉ thiếu khối gửi yêu cầu. */
  const [kq, yc] = await Promise.all([
    serverJson<BaoCao>(`/api/public/parent-report/${encodeURIComponent(token)}`, {}, HD_BAO_CAO),
    serverJson<PhuHuynhDS>(`/api/public/phu-huynh/${encodeURIComponent(token)}/yeu-cau`, {}, HD_PHU_HUYNH),
  ]);

  /* MÁY CHỦ NGỦ KHÁC CHÌA HỎNG — và nhầm hai thứ này đắt hơn nó trông (28/09/2026).
     `serverJson` chỉ trả `status: null` khi KHÔNG với tới được máy chủ; mọi mã HTTP thật
     (404 chìa sai, 410 thu hồi, 500 sập) đều là số. Đường này là đường công khai duy nhất
     của hệ thống: phụ huynh mở từ một tin Zalo, không tài khoản, không ai gõ cửa đánh thức
     máy chủ hộ — mà lượt gọi đầu khi Render vừa ngủ đo được 63–73 giây trên production.
     `loading.tsx` lo phần CHỜ; đây là phần lượt gọi ấy THẤT BẠI.
     Nói "Không mở được báo cáo này" ở đây là bảo người ta rằng chìa hỏng, trong khi chìa
     vẫn tốt. Họ đóng tab, nhắn giảng viên xin link mới, link mới cũng không vào được vì
     máy chủ vẫn đang ngủ — và không ai trong chuỗi ấy biết là không có gì hỏng. */
  if (!kq.ok && kq.status === null) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-16">
        <h1 className="text-title text-ink">Chưa tải được, thử lại sau một phút</h1>
        <p className="mt-2 text-body text-ink-2">
          Máy chủ đang thức dậy (hệ thống tạm dừng khi không ai dùng). Đường dẫn của bạn
          <strong> vẫn dùng được</strong> — không cần xin đường dẫn mới.
        </p>
        <TaiLaiTrang />
        <p className="mt-6 text-small text-ink-3">
          Nếu sau vài phút vẫn chưa mở được, hãy nhắn giảng viên phụ trách lớp.
        </p>
      </main>
    );
  }

  if (!kq.ok) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-16">
        <h1 className="text-title text-ink">Không mở được báo cáo này</h1>
        {/* Máy chủ trả CÙNG MỘT CÂU cho chìa sai, chìa hết hạn và chìa bị thu
            hồi — nói rõ "đã bị thu hồi" là xác nhận với người cầm link rằng nó
            từng đúng. Ở đây chỉ in lại câu ấy, không đoán thêm. */}
        <p className="mt-2 text-body text-ink-2">{kq.message}</p>
        {/* Chìa sai/hết hạn (404): câu của máy chủ ĐÃ nói "liên hệ trung tâm để
            nhận đường dẫn mới" — in thêm câu dưới là nói một ý hai lần (22/09/2026,
            agent GV→PH F16). Chỉ giữ nó cho lỗi khác (máy chủ không trả lời…),
            nơi câu của máy chủ không chỉ đường. */}
        {kq.status !== 404 && (
          <p className="mt-6 text-small text-ink-3">
            Nếu bạn nhận đường dẫn này từ trung tâm, hãy nhắn lại cho giảng viên
            phụ trách lớp để nhận đường dẫn mới.
          </p>
        )}
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
          {/* `h1`, không phải `span`: tờ này có `h2` (tên em) và `h3` (từng mục), nên
              thiếu cấp một là axe báo `page-has-heading-one` — đo 26/09/2026, 2 lượt trang.
              `m-0` giữ nguyên chỗ đứng; cỡ chữ vẫn do `text-section`. */}
          <h1 className="m-0 flex-1 text-section text-ink">Báo cáo học tập</h1>
          <NutIn />
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-6 print:max-w-none print:px-0 print:py-0">
        <ToBaoCao bc={bc} choPhuHuynh />
        {yc.ok && <YeuCauPhuHuynh token={token} initial={yc.data} />}
      </main>
    </div>
  );
}
