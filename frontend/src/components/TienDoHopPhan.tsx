import { HOP_PHAN, layKhoaDangHoc, layTomTat } from '@/lib/duLieuHsa';

/**
 * DẢI TIẾN ĐỘ BA HỢP PHẦN — dựng hẳn ở máy chủ, không cần phần client.
 *
 * Trước 14/09/2026 tối do `dashboard.js::renderSections` đổ vào một `div` rỗng
 * sau khi tầng cũ chạy. Không cần làm mới tại chỗ: nhận thưởng nhiệm vụ hay sửa
 * mục tiêu đều không đổi số bài đã xong.
 *
 * Luật giữ NGUYÊN của bản cũ: số bài xong đếm thật từ `byCourse`
 * (`lesson_progress`); chỉ khi thiếu mới suy từ `enrollments.progress` — bộ
 * nhớ đệm bằng 0 với người học thẳng từ lộ trình.
 */
function Dong({ ten, xong, tong, pct }: { ten: string; xong: number | null; tong: number; pct: number | null }) {
  return (
    <div className="hsa-sec-row">
      <span className="hsa-sec-name">{ten}</span>
      <span className="hsa-sec-num">{xong == null || pct == null ? '—' : `${xong}/${tong} bài · ${pct}%`}</span>
      <span className="hsa-sec-track"><i style={{ width: `${pct ?? 0}%` }}></i></span>
    </div>
  );
}

/** Khung chờ: ba dòng cùng class, chiều cao như bản thật — không nhảy bố cục. */
export function KhungTienDo() {
  return (
    <>
      {HOP_PHAN.map((h) => <Dong key={h.key} ten={h.ten} xong={null} tong={h.tong} pct={null} />)}
    </>
  );
}

const kep = (n: number) => Math.max(0, Math.min(100, Math.round(n)));

export default async function TienDoHopPhan() {
  const [sum, khoa] = await Promise.all([layTomTat(), layKhoaDangHoc()]);
  const daXong = sum.ok ? sum.data.byCourse : {};
  const theoId = new Map((khoa.ok ? khoa.data.enrolled : []).map((c) => [c.id, c]));
  return (
    <>
      {HOP_PHAN.map((h) => {
        const dem = daXong[h.id];
        const pct = dem != null ? kep((dem / h.tong) * 100) : kep(theoId.get(h.id)?.progress ?? 0);
        const xong = dem != null ? dem : Math.round((pct / 100) * h.tong);
        return <Dong key={h.key} ten={h.ten} xong={xong} tong={h.tong} pct={pct} />;
      })}
    </>
  );
}
