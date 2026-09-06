import { Card, CardHead } from '@/components/ui';
import { VAI_TRO, VIEC, cacNhom, vaiLamDuoc } from '@/lib/quyenVai';

/**
 * "Ai làm được gì" — bảng quyền, nhìn thấy được.
 *
 * ── VÌ SAO CÓ TRANG NÀY (07/09/2026) ──────────────────────────────────────
 *
 * Hệ thống đã có sáu vai trò và sáu lớp quyền cưỡng chế ở backend, nhưng không
 * ai nhìn thấy chúng: muốn biết `Trợ giảng` làm được gì thì phải đọc
 * `common/permissions.py` rồi grep xem view nào dùng lớp nào.
 *
 * Cô Hương đang soạn một bảng mô tả tính năng từng vai trò. Trang này là chỗ
 * để ĐỐI CHIẾU bảng ấy với sự thật đang chạy — chứ không phải một sơ đồ vẽ lại
 * theo trí nhớ. Mỗi ô lấy từ `lib/quyenVai.ts`, và
 * `e2e/unit/quyen-vai.test.mjs` buộc bảng ấy khớp `permissions.py` từng vai.
 *
 * ── IN RA ĐƯỢC LÀ MỘT YÊU CẦU, KHÔNG PHẢI TIỆN ÍCH ───────────────────────
 *
 * Cuộc họp với cô Hương sẽ diễn ra quanh một tờ giấy có người khoanh bút vào.
 * Nên bảng phải in ra A4 đọc được: không nền tối, không thanh điều hướng, cột
 * không bị cắt.
 */
export const dynamic = 'force-dynamic';
export const metadata = { title: 'Ai làm được gì | TopHSA' };

export default function VaiTroPage() {
  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHead
          title="Ai làm được gì"
          hint="Bảng này KHÔNG phải hàng rào — hàng rào là `permission_classes` ở máy chủ. Đây là chỗ đọc và bàn lại ranh giới, và một phép kiểm buộc nó khớp máy chủ từng vai."
        />
        <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,17rem),1fr))]">
          {VAI_TRO.map((v) => (
            <div key={v.ma} className="rounded-md border border-line bg-surface px-4 py-3">
              <p className="text-subhead text-ink">{v.nhan}</p>
              {/* Giá trị THẬT trong cột `users.role`. Người vận hành cần biết
                  chuỗi này khi đối chiếu với bảng tính hay khi báo lỗi. */}
              <p className="mt-0.5 font-mono text-label text-ink-3">{v.ma}</p>
              <p className="mt-2 text-small text-ink-2">{v.mo_ta}</p>
            </div>
          ))}
        </div>
      </Card>

      {cacNhom().map((nhom) => (
        <Card key={nhom}>
          <CardHead title={nhom} />
          <div className="overflow-x-auto overflow-y-hidden rounded-md border border-line bg-surface">
            <table className="w-full border-collapse text-small">
              <caption className="sr-only">
                {`Việc thuộc nhóm ${nhom} và vai trò làm được từng việc`}
              </caption>
              <thead>
                <tr>
                  <th scope="col" className="border-b border-line bg-sunken px-3 py-2 text-left text-label text-ink-3">
                    Việc
                  </th>
                  {VAI_TRO.map((v) => (
                    <th
                      key={v.ma}
                      scope="col"
                      /* Tiêu đề cột hẹp, chữ đứng: sáu vai × chữ ngang là bảng
                         rộng gấp đôi khổ giấy. `writing-mode` giữ được cả sáu
                         cột trên một trang A4. */
                      className="border-b border-line bg-sunken px-2 py-2 text-label text-ink-3 [writing-mode:vertical-rl] [text-orientation:mixed] print:[writing-mode:vertical-rl]"
                    >
                      {v.nhan}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {VIEC.filter((v) => v.nhom === nhom).map((v) => {
                  const duoc = vaiLamDuoc(v);
                  return (
                    <tr key={v.nhan} className="align-top">
                      <td className="border-b border-line/50 px-3 py-3">
                        <span className="block font-semibold text-ink">{v.nhan}</span>
                        <span className="mt-0.5 block text-ink-2">{v.giaiThich}</span>
                        {/* Ranh giới THỨ HAI. Không nói ra thì bảng hứa rộng
                            hơn sự thật: giảng viên có vai đúng nhưng chỉ xem
                            được lớp mình phụ trách. */}
                        {v.chan_them && (
                          <span className="mt-1 block text-warning-ink">
                            Thêm điều kiện: {v.chan_them}
                          </span>
                        )}
                        {/* Chỗ cưỡng chế THẬT. In ra để người đọc lần được tới
                            mã, và để bảng này không thể là một lời khẳng định
                            suông. */}
                        <span className="mt-1 block font-mono text-label text-ink-3">
                          {v.nguon} · {v.lopQuyen}
                        </span>
                      </td>
                      {VAI_TRO.map((r) => {
                        const co = duoc.includes(r.ma);
                        return (
                          <td
                            key={r.ma}
                            className="border-b border-line/50 px-2 py-3 text-center"
                          >
                            {/* Ký hiệu KÈM chữ cho trình đọc màn hình: một ô
                                chỉ có màu hoặc chỉ có dấu ✓ thì người dùng
                                trình đọc nghe một hàng im lặng. */}
                            <span className={co ? 'text-success-ink' : 'text-ink-3'}>
                              {co ? '✓' : '—'}
                            </span>
                            <span className="sr-only">
                              {co ? `${r.nhan} làm được` : `${r.nhan} không làm được`}
                            </span>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      ))}

      <Card>
        <CardHead title="Còn thiếu gì" />
        <ul className="flex list-disc flex-col gap-2 pl-5 text-body text-ink-2">
          <li>
            Chưa có vai <strong>Quản lý</strong>. Anh Sơn chốt 07/09/2026: dựng cơ
            chế trước, điền nội dung khi bảng của cô Hương về — thêm một vai là
            thêm một dòng ở <code className="font-mono">lib/quyenVai.ts</code> và
            một hàm <code className="font-mono">is_*</code> ở{' '}
            <code className="font-mono">common/permissions.py</code>, không phải
            sửa từng màn hình.
          </li>
          <li>
            Ba vai <strong>Quản lý học vụ</strong>, <strong>Trợ giảng</strong>,{' '}
            <strong>Biên tập nội dung</strong> hiện <strong>chưa có ai</strong> (đo
            07/09/2026: 1 quản trị viên, 1 giảng viên, 4 học viên). Nghĩa là ba cột
            trong bảng trên chưa từng được ai dùng thử trên tài khoản thật.
          </li>
          <li>
            Bảng này chỉ liệt kê việc có <em>hàng rào riêng</em>. Việc mà mọi người
            đăng nhập đều làm được — học bài, làm đề, đọc diễn đàn — không có ở đây.
          </li>
        </ul>
      </Card>
    </div>
  );
}
