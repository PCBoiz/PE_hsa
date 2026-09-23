import { Card, CardHead } from '@/components/ui';
import { VAI_TRO, VIEC, cacNhom, vaiLamDuoc } from '@/lib/quyenVai';
import SoDoVaiTro from './SoDoVaiTro';

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
          hint="Vai nào làm được việc nào. Máy chủ mới là nơi chặn; bảng này để đọc và bàn."
          chiTiet="Bảng không tự cấp hay chặn quyền gì — việc ấy do máy chủ làm với từng yêu cầu. Một phép kiểm tự động so bảng với máy chủ từng vai, nên thứ đọc ở đây là thứ đang chạy thật."
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

      {/* HÌNH trước BẢNG. Người mở trang này lần đầu cần biết hệ thống có
          HÌNH DẠNG gì trước khi tra từng ô — và trong buổi họp thì hình là
          thứ chỉ tay vào được, bảng là thứ tra sau. */}
      <Card>
        <CardHead
          title="Hình dạng của hệ thống quyền"
          hint="Bốn lớp quyền lồng vào nhau; biên tập nội dung đứng ở trục riêng."
          chiTiet="Hình vẽ từ cùng dữ liệu với bảng bên dưới chứ không vẽ tay, nên hai bên không lệch nhau được."
        />
        <SoDoVaiTro />
      </Card>

      {cacNhom().map((nhom) => (
        <Card key={nhom}>
          <CardHead title={nhom} />
          {/* ── KHỔ HẸP: mỗi việc một THẺ ─────────────────────────────────
              Ma trận bảy cột trên màn 390px không đọc được, kể cả khi nó
              không tràn. Đo 07/09/2026: bảng rộng tối thiểu 593px, và bề rộng
              ấy làm phình khung chứa gốc tới 639px — thanh `position: fixed`
              co giãn theo, nên CẢ TRANG trượt ngang 249px.

              Ba cách vá thử đều không đủ: `w:auto min-w:100%` không đổi gì,
              `overflow-x: clip` ở body không đổi gì, kẹp bề ngang thanh chỉ
              giấu triệu chứng. Thứ thật sự sửa là KHÔNG dựng bảng rộng ở khổ
              ấy — cùng lối `Table.tsx` đã dùng: dưới 640px, mỗi dòng thành
              một thẻ tự mang nhãn của nó. */}
          <ul className="flex flex-col gap-3 sm:hidden">
            {VIEC.filter((v) => v.nhom === nhom).map((v) => {
              const duoc = vaiLamDuoc(v);
              return (
                <li key={v.nhan} className="rounded-md border border-line bg-surface px-4 py-3">
                  <p className="text-body font-semibold text-ink">{v.nhan}</p>
                  <p className="mt-0.5 text-small text-ink-2">{v.giaiThich}</p>
                  {v.chan_them && (
                    <p className="mt-1 text-small text-warning-ink">
                      Thêm điều kiện: {v.chan_them}
                    </p>
                  )}
                  <p className="mt-2 text-label text-ink-3">Làm được:</p>
                  <p className="text-small text-ink">
                    {VAI_TRO.filter((r) => duoc.includes(r.ma)).map((r) => r.nhan).join(' · ')}
                  </p>
                  {/* Dòng `tệp.py::View · lớp quyền` từng in ở đây đã gỡ
                      (24/09/2026): đó là đường dẫn mã, người vận hành không
                      đọc được (RULES §10). Bảng vẫn không phải lời khẳng
                      định suông — `quyen-vai.test.mjs` đối chiếu `nguon`
                      với máy chủ từng vai. */}
                </li>
              );
            })}
          </ul>

          <div className="hidden overflow-x-auto overflow-y-hidden rounded-md border border-line bg-surface sm:block">
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
                        {/* Đường dẫn mã từng in ở đây — gỡ 24/09/2026, cùng lý
                            do với dòng ở khổ hẹp phía trên. */}
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
          {/* Hai ý cũ ở đây là ghi chú lập trình viên (tên người, ngày chốt,
              đường dẫn tệp mã) — gỡ 24/09/2026 theo góp ý "nhiều chữ" của
              TopHSA. Ý "ba vai chưa có ai (đo 07/09)" bỏ hẳn: nó đã hết đúng
              từ lượt rà sáu vai bằng tài khoản thật 20/09. */}
          <li>
            Chưa có vai <strong>Quản lý</strong>. Khi trung tâm cần, thêm được vai
            này mà không phải sửa từng màn hình.
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
