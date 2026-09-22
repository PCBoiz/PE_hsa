import Link from 'next/link';

import { Card, CardHead } from '@/components/ui';
import { HUONG_DAN } from '@/lib/huongDan';
import { VAI_TRO } from '@/lib/quyenVai';

/**
 * PHẦN DỰNG của Hướng dẫn — dùng chung cho hai khu.
 *
 * ── VÌ SAO TÁCH RA (22/09/2026) ───────────────────────────────────────────
 *
 * `quan-tri/huong-dan/layout.tsx` tự ghi nhận khoảng trống của chính nó:
 * "Giảng viên và trợ giảng KHÔNG vào được khu này, nên họ chưa đọc được hướng
 * dẫn phần dạy học… cách sửa đúng là một khu tài liệu riêng ngoài khu Vận
 * hành, không phải nới cổng khu."
 *
 * Nay có khu ấy (`/huong-dan`). Nhưng hai trang cùng in một nội dung thì sớm
 * muộn lệch nhau — và bản lệch sẽ là bản ít người đọc hơn, tức bản không ai
 * phát hiện. Nên nội dung dựng ở ĐÂY, hai trang chỉ khác nhau ở cổng và ở
 * việc lọc.
 *
 * ── LỌC, KHÔNG PHẢI CHẶN ─────────────────────────────────────────────────
 *
 * `loc` giấu các bài không thuộc vai người đọc. Đây là phép lịch sự với người
 * đọc, KHÔNG phải hàng rào bảo mật: bài hướng dẫn không chứa dữ liệu của ai,
 * và quyền thật nằm ở cổng của từng màn hình. Đừng bao giờ dựa vào nó để giấu
 * thứ cần giấu.
 *
 * Người đọc vẫn bật được "xem tất cả" — một trợ giảng muốn biết giảng viên
 * làm gì tiếp theo là chuyện nên khuyến khích, không nên chặn.
 */
export default function BangHuongDan({
  vai,
  loc = false,
}: {
  /** Vai của người đang đọc. `undefined` thì hiện tất cả. */
  vai?: string;
  /** Chỉ hiện bài thuộc vai trên. */
  loc?: boolean;
}) {
  const bai = loc && vai ? HUONG_DAN.filter((b) => b.vai.includes(vai)) : [...HUONG_DAN];
  const an = HUONG_DAN.length - bai.length;

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHead
          title="Hướng dẫn"
          hint={
            loc && vai
              ? `Các việc thuộc vai ${tenVai(vai)}. Bấm Ctrl+P để in ra giấy.`
              : 'Xếp theo VIỆC, không theo màn hình. Bấm Ctrl+P để in ra giấy đưa người mới.'
          }
        />

        {bai.length === 0 ? (
          <p className="text-body text-ink-2">
            Chưa có bài hướng dẫn nào viết riêng cho vai này. Xem{' '}
            <Link href="/huong-dan?tat-ca=1" className="text-brand-ink underline">
              toàn bộ hướng dẫn
            </Link>
            .
          </p>
        ) : (
          <ul className="flex flex-wrap gap-x-4 gap-y-1">
            {bai.map((b) => (
              <li key={b.ma}>
                {/* Mục lục là neo TRONG trang, không phải tuyến riêng: người đọc
                    in ra giấy thì một mục lục dẫn sang trang khác là vô dụng. */}
                {/* `min-h-11` = 44px (Apple HIG). Bộ đo từng bắt 17 vùng chạm nhỏ
                    ở trang này, 8 trong số đó là chính mục lục. */}
                <a
                  href={`#${b.ma}`}
                  className="inline-flex min-h-11 items-center text-small text-brand-ink underline"
                >
                  {b.tieu_de}
                </a>
              </li>
            ))}
          </ul>
        )}

        {an > 0 && (
          <p className="mt-3 text-small text-ink-3">
            Còn {an} bài dành cho vai khác đang ẩn.{' '}
            <Link href="/huong-dan?tat-ca=1" className="text-brand-ink underline">
              Xem tất cả
            </Link>
            .
          </p>
        )}

        <p className="mt-3 text-small text-ink-3">
          Không có ảnh chụp màn hình, có chủ ý: ảnh hỏng <em>im lặng</em> khi giao diện
          đổi — nó vẫn nằm đó dạy sai. Các đường dẫn dưới đây là đường thật, và một
          phép kiểm đối chiếu chúng với tuyến của ứng dụng mỗi lần dựng.
        </p>
      </Card>

      {bai.map((b) => (
        <Card key={b.ma}>
          {/* `scroll-mt` để tiêu đề không nằm dưới thanh cố định khi nhảy neo. */}
          <div id={b.ma} className="scroll-mt-[calc(var(--topbar-h)+1rem)]">
            <CardHead title={b.tieu_de} hint={b.khi_nao} />
          </div>

          <p className="mb-3 text-small text-ink-3">Dành cho: {b.vai.map(tenVai).join(' · ')}</p>

          <ol className="flex list-decimal flex-col gap-3 pl-5">
            {b.buoc.map((s) => (
              <li key={s.lam} className="text-body text-ink-2">
                {s.lam}
                {s.o && (
                  <>
                    {' '}
                    <Link
                      href={s.o}
                      /* `-my-2.5 py-2.5` cho vùng chạm 44px mà KHÔNG kéo giãn khoảng
                         cách giữa các bước. */
                      className="-my-2.5 inline-block py-2.5 text-brand-ink underline"
                    >
                      Mở màn hình này
                    </Link>
                  </>
                )}
                {s.luu_y && (
                  <span className="mt-1 block text-small text-warning-ink">
                    Dễ sai chỗ này: {s.luu_y}
                  </span>
                )}
              </li>
            ))}
          </ol>

          {b.hong_thi_sao && b.hong_thi_sao.length > 0 && (
            <div className="mt-4 rounded-md border border-line bg-sunken px-4 py-3">
              <p className="text-label text-ink-3">Trông như hỏng thì làm gì</p>
              <dl className="mt-2 flex flex-col gap-3">
                {b.hong_thi_sao.map((h) => (
                  <div key={h.trieu_chung}>
                    <dt className="text-body font-semibold text-ink">{h.trieu_chung}</dt>
                    <dd className="text-body text-ink-2">{h.xu_ly}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </Card>
      ))}
    </div>
  );
}

/** Tên đọc được của một vai, lấy từ bảng quyền để hai chỗ không lệch chữ. */
function tenVai(ma: string) {
  return VAI_TRO.find((v) => v.ma === ma)?.nhan ?? ma;
}
