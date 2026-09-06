import Link from 'next/link';

import { Card, CardHead } from '@/components/ui';
import { HUONG_DAN } from '@/lib/huongDan';
import { VAI_TRO } from '@/lib/quyenVai';

/**
 * HƯỚNG DẪN VẬN HÀNH — trong ứng dụng, in ra được.
 *
 * Anh Sơn chốt 07/09/2026: tài liệu đặt ở đây chứ không ở một tệp `.md` trong
 * repo. Người đọc là học vụ và giảng viên; họ không mở GitHub, và họ đọc lúc
 * đang cần làm một việc cụ thể.
 *
 * Nội dung ở `lib/huongDan.ts`. Trang này chỉ dựng — tách ra để
 * `e2e/unit/huong-dan.test.mjs` đọc được dữ liệu mà không phải phân tích JSX.
 *
 * ── PHẦN "HỎNG THÌ SAO" KHÔNG PHẢI PHẦN PHỤ ─────────────────────────────
 *
 * Người mới không mắc ở bước "bấm nút nào". Họ mắc ở lúc màn hình hiện một thứ
 * không giống mong đợi — sáu dấu "—", một câu đỏ, một con số 0% — và không
 * biết đó là lỗi hay là bình thường. Nên mỗi bài có mục ấy, và nó được in ra
 * cùng cỡ chữ với các bước, không bị thu nhỏ thành ghi chú.
 */
export const dynamic = 'force-dynamic';
export const metadata = { title: 'Hướng dẫn vận hành | TopHSA' };

/** Tên đọc được của một vai, lấy từ bảng quyền để hai chỗ không lệch chữ. */
function tenVai(ma: string) {
  return VAI_TRO.find((v) => v.ma === ma)?.nhan ?? ma;
}

export default function HuongDanPage() {
  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHead
          title="Hướng dẫn vận hành"
          hint="Xếp theo VIỆC, không theo màn hình. Bấm Ctrl+P để in ra giấy đưa người mới."
        />
        <ul className="flex flex-wrap gap-x-4 gap-y-1">
          {HUONG_DAN.map((b) => (
            <li key={b.ma}>
              {/* Mục lục là neo trong trang, không phải tuyến riêng: người đọc
                  in ra giấy thì một mục lục dẫn sang trang khác là vô dụng. */}
              {/* `min-h-11` = 44px (Apple HIG). Bộ đo bắt được 17 vùng chạm
                  nhỏ ở trang này, và 8 trong số đó là chính mục lục — chữ cao
                  16px. Mục lục là thứ người dùng bấm ĐẦU TIÊN trên điện thoại. */}
              <a
                href={`#${b.ma}`}
                className="inline-flex min-h-11 items-center text-small text-brand-ink underline"
              >
                {b.tieu_de}
              </a>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-small text-ink-3">
          Không có ảnh chụp màn hình, có chủ ý: ảnh hỏng <em>im lặng</em> khi giao
          diện đổi — nó vẫn nằm đó dạy sai. Các đường dẫn dưới đây là đường thật,
          và một phép kiểm đối chiếu chúng với tuyến của ứng dụng mỗi lần dựng.
        </p>
      </Card>

      {HUONG_DAN.map((b) => (
        <Card key={b.ma}>
          {/* `scroll-mt` để tiêu đề không nằm dưới thanh cố định khi nhảy neo. */}
          <div id={b.ma} className="scroll-mt-[calc(var(--topbar-h)+1rem)]">
            <CardHead title={b.tieu_de} hint={b.khi_nao} />
          </div>

          <p className="mb-3 text-small text-ink-3">
            Dành cho: {b.vai.map(tenVai).join(' · ')}
          </p>

          <ol className="flex list-decimal flex-col gap-3 pl-5">
            {b.buoc.map((s) => (
              <li key={s.lam} className="text-body text-ink-2">
                {s.lam}
                {s.o && (
                  <>
                    {' '}
                    <Link
                      href={s.o}
                      /* `-my-2 py-2` cho vùng chạm 44px mà KHÔNG kéo giãn
                         khoảng cách giữa các bước — cùng lối các bảng trong
                         khu Vận hành đã dùng. */
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

      <Card>
        <CardHead title="Bàn giao công nghệ" />
        <p className="text-body text-ink-2">
          Trang này dành cho người <strong>vận hành</strong>. Người tiếp nhận
          <strong> công nghệ</strong> (kiến trúc, triển khai, cách sửa) cần thứ
          khác hẳn — nằm trong repo:
        </p>
        <ul className="mt-2 flex list-disc flex-col gap-1 pl-5 text-body text-ink-2">
          <li><code className="font-mono">docs/KIEN_TRUC/</code> — kiến trúc từng khối</li>
          <li><code className="font-mono">docs/VIEC_CUA_ANH.md</code> — việc cần tài khoản bên ngoài (Zalo OA, Render, Neon)</li>
          <li><code className="font-mono">RULES.md</code> — luật đã trả giá mới rút ra được</li>
          <li><code className="font-mono">PROGRESS.md</code> — nhật ký từng thay đổi và lý do</li>
        </ul>
      </Card>
    </div>
  );
}
