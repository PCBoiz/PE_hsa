/**
 * KHUNG TỜ BÁO CÁO khi chờ — cùng thứ tự khối, cùng lớp chữ với `ToBaoCao.tsx`,
 * để lúc tờ thật thay vào trang không nhảy (CLS). Dùng ở HAI nơi: trang phụ
 * huynh `/bc/<chìa>` và màn giảng viên "Xem tờ" (`/giang-day/bao-cao/<lớp>/<em>`).
 * Tách ra 22/09/2026: màn giảng viên từng đứng im 4,4–4,7 s sau cú bấm, không
 * một dấu hiệu gì (agent GV→PH F5) — trong khi trang phụ huynh đã có khung này.
 * `aria-hidden`: câu "đang tải" có nghĩa nằm ở `role="status"` của nơi dùng.
 */
function O({ rong, cao = '0.9em' }: { rong: string; cao?: string }) {
  return (
    <span
      className="block animate-pulse rounded bg-sunken"
      style={{ width: rong, height: cao }}
    />
  );
}

/** Một ô số như `Ô` trong ToBaoCao: nhãn nhỏ, số to, dòng phụ. */
function OSo() {
  return (
    <div className="rounded-md border border-line bg-surface px-4 py-3">
      <O rong="60%" cao="0.8em" />
      <p className="mt-1 text-title"><O rong="2.5em" cao="1em" /></p>
      <p className="mt-0.5 text-small"><O rong="80%" cao="0.8em" /></p>
    </div>
  );
}

export function KhungToBaoCao() {
  return (
      <article className="rounded-lg border border-line bg-surface p-6" aria-hidden="true">
        <h2 className="text-title"><O rong="min(14rem, 70%)" cao="1em" /></h2>
        <p className="mt-1 text-body"><O rong="min(20rem, 90%)" /></p>
        <p className="mt-2 text-body"><O rong="min(12rem, 55%)" /></p>
        <p className="mt-0.5 text-small"><O rong="min(16rem, 75%)" cao="0.8em" /></p>

        <h3 className="mt-6 text-subhead"><O rong="9rem" cao="1em" /></h3>
        <p className="mt-2 text-body"><O rong="min(22rem, 95%)" /></p>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <OSo /><OSo /><OSo /><OSo />
        </div>

        <h3 className="mt-6 text-subhead"><O rong="11rem" cao="1em" /></h3>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
          <OSo /><OSo /><OSo />
        </div>

        <h3 className="mt-6 text-subhead"><O rong="10rem" cao="1em" /></h3>
        <p className="mt-2 text-body"><O rong="min(24rem, 100%)" /></p>
        <p className="mt-1 text-body"><O rong="min(18rem, 80%)" /></p>
      </article>
  );
}
