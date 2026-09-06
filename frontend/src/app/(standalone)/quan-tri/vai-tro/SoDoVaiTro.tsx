import { VAI_TRO, VIEC, nhanVai, soDoVai } from '@/lib/quyenVai';

/**
 * SƠ ĐỒ PHÂN QUYỀN — hình dạng của hệ thống, không phải bảng tra cứu.
 *
 * ── VÌ SAO CÓ HÌNH NÀY (07/09/2026) ───────────────────────────────────────
 *
 * Bảng ô vuông ngay dưới trả lời tốt câu "vai X có làm được việc Y không".
 * Nhưng có những câu nó KHÔNG trả lời được, mà lại đúng là những câu sẽ hỏi
 * trong buổi làm việc với cô Hương:
 *
 *   · "Nới quyền cho trợ giảng thì những ai bị ảnh hưởng?"
 *   · "Vai Quản lý sắp thêm nằm ở đâu — trên hay dưới học vụ?"
 *   · "Vì sao biên tập viên không xếp được lớp?"
 *
 * Ba câu ấy hỏi về HÌNH DẠNG. Và hình dạng thì có thật: bốn lớp quyền lồng
 * khít vào nhau như bốn vòng đồng tâm, mỗi vòng ra ngoài thêm đúng một vai;
 * còn biên tập nội dung đứng ở trục khác hẳn, chạm vào lõi quản trị chứ không
 * nằm trên chuỗi ấy.
 *
 * ── VÌ SAO LỒNG HỘP CHỨ KHÔNG PHẢI SVG ───────────────────────────────────
 *
 * Bốn vòng đồng tâm vẽ bằng SVG thì phải đặt toạ độ, và toạ độ là thứ vỡ đầu
 * tiên khi khổ máy đổi — đúng vết xe của khối lộ trình đã phải dựng lại cả
 * tuần này. Hộp lồng hộp thì "chứa nhau" là quan hệ CÓ SẴN của bố cục: thu
 * màn hình lại, các vòng vẫn lồng đúng, chữ vẫn xuống dòng, in ra giấy vẫn
 * đúng. Không một con số toạ độ nào phải giữ cho khớp.
 *
 * ── VÌ SAO KHÔNG VẼ SẴN BỐN VÒNG ─────────────────────────────────────────
 *
 * Vẽ tay là ghim một khẳng định vào hình. Hôm nay nó đúng; ngày ai đó thêm
 * một lớp quyền cắt ngang chuỗi (ví dụ `{học vụ, giảng viên}` — không có quản
 * trị) thì chuỗi gãy, mà hình vẫn vẽ y như cũ và vẫn trông rất thuyết phục.
 *
 * `soDoVai()` tự tìm chuỗi từ dữ liệu và đẩy MỌI lớp không xếp được sang
 * `nhanh`. Không lớp nào biến mất im lặng, và trang này hiện `nhanh` ra ngang
 * hàng với chuỗi chính.
 */

/** Đậm dần vào lõi: vòng trong càng ít vai qua được thì nền càng đặc. */
const NEN = ['bg-surface', 'bg-sunken', 'bg-surface', 'bg-sunken'];

export default function SoDoVaiTro() {
  const { vong, nhanh, vaiNgoai } = soDoVai();
  const soCanhBao = VIEC.filter((v) => v.chan_them).length;

  /* Dựng từ LÕI RA: bắt đầu bằng lõi, mỗi lần lặp BỌC THÊM một vòng ra ngoài.
     `vong` xếp từ hẹp nhất (lõi) tới rộng nhất, nên `reduce` xuôi làm phần tử
     CUỐI — lớp nhiều vai nhất — thành hộp ngoài cùng.

     Bản đầu viết `reduceRight` và hình lồng NGƯỢC: ngoài cùng hoá ra
     `IsAdminOrAcademic` (2 vai) còn `IsTeachingStaff` (4 vai) nằm trong, tức
     hình nói ngược hẳn cái nhãn "càng ra ngoài càng nhiều vai" in ngay trên
     nó. Bắt được bằng cách MỞ ẢNH CHỤP RA NHÌN, không phải bằng kiểu: cả hai
     chiều đều hợp kiểu, đều dựng ra bốn hộp lồng nhau, và bản sai trông không
     kém thuyết phục chút nào. */
  const loi = (
    /* `data-*`: mốc để `so-do-vai.test.mjs` bám vào. Bám theo tên lớp CSS thì
       phép kiểm vỡ mỗi lần đổi màu; bám theo `data-lop-quyen` thì nó chỉ vỡ
       khi CẤU TRÚC đổi — mà cấu trúc đổi thì đúng là phải xem lại thật. */
    <div
      data-lop-quyen={vong[0]?.lopQuyen}
      data-so-vai={vong[0]?.vaiTatCa.length}
      className="rounded-md border border-brand/40 bg-brand-soft px-3 py-3 text-center"
    >
      <p className="text-label uppercase tracking-wide text-ink-3">Lõi</p>
      <p className="text-subhead text-ink">{nhanVai(vong[0]?.vaiTatCa[0] ?? '')}</p>
      <p className="mt-1 font-mono text-label text-ink-3 [overflow-wrap:anywhere]">
        {vong[0]?.lopQuyen}
      </p>
      <p className="mt-1 text-small text-ink-2">{vong[0]?.soViec} việc</p>
    </div>
  );

  const hinh = vong.slice(1).reduce<React.ReactNode>(
    (ben_trong, v, i) => (
      <div
        key={v.lopQuyen}
        data-lop-quyen={v.lopQuyen}
        data-so-vai={v.vaiTatCa.length}
        /* `p-3 sm:p-4` là bề dày của MỘT vòng. Dùng thang khoảng cách của hệ
           thống chứ không ghim px: bốn vòng lồng nhau trên màn 390px vẫn còn
           chỗ cho chữ, và trên màn rộng thì vòng dày ra theo. */
        className={`rounded-lg border border-line ${NEN[(i + 1) % NEN.length]} p-3 sm:p-4`}
      >
        <div className="mb-2 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
          <p className="text-body font-semibold text-ink">
            {/* Vòng này MỞ RA cho ai — đó là thông tin của một vòng, chứ không
                phải danh sách tất cả những ai qua được (danh sách ấy chỉ là
                cộng dồn các vòng bên trong, nói lại là thừa). */}
            + {v.vaiThem.map(nhanVai).join(' · ')}
          </p>
          <p className="text-small text-ink-2">{v.soViec} việc</p>
        </div>
        <p className="mb-3 font-mono text-label text-ink-3 [overflow-wrap:anywhere]">
          {v.lopQuyen}
        </p>
        {ben_trong}
      </div>
    ),
    loi,
  );

  return (
    <div className="flex flex-col gap-4">
      {/* Người dùng trình đọc màn hình không "thấy" hộp lồng hộp — với họ đây
          chỉ là các div lồng nhau không nghĩa. Câu tóm tắt này nói THÀNH LỜI
          đúng điều mà hình nói bằng mắt. */}
      <p className="sr-only">
        {`Hệ thống quyền có ${vong.length} vòng lồng nhau, từ rộng tới hẹp: `}
        {[...vong].reverse().map((v) => `${v.lopQuyen} cho ${v.vaiTatCa.map(nhanVai).join(', ')}`).join('; ')}
        {nhanh.length > 0
          ? `. Ngoài chuỗi ấy còn ${nhanh.length} lớp quyền ở trục khác: ${nhanh
              .map((v) => `${v.lopQuyen} cho ${v.vaiTatCa.map(nhanVai).join(', ')}`)
              .join('; ')}.`
          : '.'}
      </p>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div aria-hidden="true">
          <p className="mb-2 text-label uppercase tracking-wide text-ink-3">
            Chuỗi chính — càng ra ngoài càng nhiều vai qua được
          </p>
          {hinh}
        </div>

        <div className="flex flex-col gap-4">
          {/* ── NHÁNH: lớp không xếp được vào chuỗi ───────────────────────
              Phải hiện ra. Giấu đi thì hình nói dối theo hướng nguy hiểm
              nhất: trông như hệ thống chỉ có một trục quyền duy nhất. */}
          {nhanh.length > 0 && (
            <div>
              <p className="mb-2 text-label uppercase tracking-wide text-ink-3">
                Trục khác — không nằm trên chuỗi trên
              </p>
              <div className="flex flex-col gap-2">
                {nhanh.map((v) => (
                  <div
                    key={v.lopQuyen}
                    data-lop-quyen={v.lopQuyen}
                    data-so-vai={v.vaiTatCa.length}
                    data-nhanh="1"
                    className="rounded-lg border border-dashed border-line bg-surface p-3 sm:p-4"
                  >
                    <p className="text-body font-semibold text-ink">
                      {v.vaiTatCa.map(nhanVai).join(' · ')}
                    </p>
                    <p className="mt-1 font-mono text-label text-ink-3 [overflow-wrap:anywhere]">
                      {v.lopQuyen}
                    </p>
                    <p className="mt-1 text-small text-ink-2">{v.soViec} việc</p>
                  </div>
                ))}
              </div>
              <p className="mt-2 text-small text-ink-2">
                Chạm vào lõi (quản trị viên qua được cả hai) nhưng KHÔNG nằm trên
                chuỗi: biên tập viên soạn được bài mà không xếp được lớp, và học
                vụ xếp được lớp mà không sửa được bài.
              </p>
            </div>
          )}

          {/* ── HÀNG RÀO THỨ HAI ──────────────────────────────────────────
              Vòng chỉ là cửa THỨ NHẤT. Không nói ra thì hình hứa rộng hơn
              sự thật: nhìn hình thì tưởng cứ là giảng viên là xem được mọi
              lớp. */}
          <div className="rounded-lg border border-warning/40 bg-surface p-3 sm:p-4">
            <p className="text-body font-semibold text-ink">Còn một cửa nữa sau vòng</p>
            <p className="mt-1 text-small text-ink-2">
              Qua được vòng mới chỉ là qua cửa thứ nhất. {soCanhBao} trong{' '}
              {VIEC.length} việc còn bị chặn lần hai bởi{' '}
              <code className="font-mono text-label">can_see_class</code>: đúng vai
              nhưng sai lớp thì vẫn không vào. Cửa ấy cắt NGANG mọi vòng — nên
              giảng viên và trợ giảng chỉ thấy lớp mình phụ trách, không thấy lớp
              của người khác.
            </p>
          </div>

          {/* ── AI ĐỨNG NGOÀI ────────────────────────────────────────────── */}
          {vaiNgoai.length > 0 && (
            <div className="rounded-lg border border-line bg-surface p-3 sm:p-4">
              <p className="text-body font-semibold text-ink">
                Ngoài mọi vòng: {vaiNgoai.map(nhanVai).join(' · ')}
              </p>
              <p className="mt-1 text-small text-ink-2">
                Không qua lớp quyền nào ở trên — nghĩa là không có việc quản trị
                nào trong bảng dưới. Việc của{' '}
                {vaiNgoai.map(nhanVai).join(' và ')} (học bài, làm đề, xem tiến độ
                của chính mình) không cần hàng rào riêng nên không xuất hiện ở
                đây. Đó là chỗ hình này KHÔNG nói được gì, chứ không phải chỗ
                trống vì thiếu quyền.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Con số ở đây là để đối chiếu, không phải trang trí: tổng việc trên
          hình phải bằng tổng việc trong bảng dưới. Lệch là hình đã bỏ sót một
          lớp quyền. */}
      <p className="text-small text-ink-3">
        {vong.length} vòng + {nhanh.length} nhánh ={' '}
        {vong.reduce((s, v) => s + v.soViec, 0) + nhanh.reduce((s, v) => s + v.soViec, 0)} việc,
        khớp {VIEC.length} việc trong bảng dưới · {VAI_TRO.length} vai trò
      </p>
    </div>
  );
}
