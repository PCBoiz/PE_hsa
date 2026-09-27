import Link from 'next/link';

import { Card, CardHead, Chip, EmptyState, TableWrap, Tbody, Td, Th, Thead, Tr } from '@/components/ui';
import { serverJson } from '@/lib/server-api';
import { z } from 'zod';

/**
 * KẾT QUẢ THEO MÔN — bảng chéo MÔN × LỚP (bảng TopHSA dòng 6, 27/09/2026). CHỈ ĐỌC.
 *
 * Trả lời câu ở GIỮA hai báo cáo đã có: "môn nào đang tụt, và lớp nào trong môn ấy".
 * Trước hôm nay trung tâm hỏi được "lớp này em nào chưa nộp bài" (bảng chấm từng bài) và
 * "khoá này điểm thế nào" (báo cáo lớp), nhưng muốn so MÔN với MÔN thì phải mở ~400 lớp
 * rồi tự gộp trong đầu — nên thực tế là không ai biết.
 *
 * VÌ SAO LÀ TRANG RIÊNG, KHÔNG PHẢI MỘT KHU CỦA "TOÀN TRUNG TÂM". Hai lý do đo được, chứ
 * không phải sở thích:
 *  · Trang "Toàn trung tâm" đã có 8 khối và ~550 dòng mã, khối cuối ("Từng lớp") đã phải
 *    cắt còn 50 dòng. Thêm một bảng chéo có NHÓM (mỗi môn một bảng con) là đẩy nó xuống
 *    dưới nếp gấp thứ ba — đúng lỗi "màn đầu rối" mà TopHSA đã góp ý 24/09.
 *  · Bộ lọc KHÁC nhau. Trang kia lọc đợt + kỳ xem; trang này còn lọc MÔN, và hai biểu mẫu
 *    GET trên cùng một URL sẽ ăn tham số của nhau (`KyXem` phải mang `term_id` trong ô ẩn
 *    đúng vì lý do đó — thêm cái thứ ba là thêm hai ô ẩn nữa cho mỗi form).
 *
 * KHÔNG MỘT DÒNG JS PHÍA TRÌNH DUYỆT. Bộ lọc là `<form method="get">` và liên kết thường,
 * cùng khuôn với "Chấm công" và bộ lọc Lớp học: mọi trạng thái nằm trên URL (gửi link
 * "môn Định lượng tháng 9" cho đồng nghiệp là họ thấy đúng thứ mình thấy), và ô lọc dùng
 * được NGAY khi HTML về — không có khoảng thời gian React chưa gắn để bấm vào hư không, nên
 * ở đây không cần `useDaGan()`. (`useDaGan` là hàng rào cho ô lọc CÓ JS: nó khoá ô tới khi
 * React gắn xong. Trang không có JS thì thứ cần bảo vệ không tồn tại.)
 *
 * Danh mục môn và đợt LẤY TỪ MÁY CHỦ (`monOptions` / `dotOptions`), không gõ lại ở đây
 * (RULES §7). Số `—` hiện là `—`, không bao giờ là `0%`: xem `pct` bên dưới.
 */
export const dynamic = 'force-dynamic';
export const metadata = { title: 'Kết quả theo môn | TopHSA' };

const so = z.number();
const soHoacTrong = z.number().nullable();

/* HÌNH DẠNG phản hồi `/api/admin/bao-cao-cheo` (`teaching/bao_cao_cheo.py::bao_cao_cheo`).
   `looseObject`: máy chủ thêm khoá thì màn hình không hỏng; thiếu khoá màn hình ĐỌC mới là
   lỗi (T18 mức 2). */
const O_SO = {
  dangHoc: so,
  phaiNop: so,
  daNop: so,
  daCham: so,
  soDiem: so,
  luotDiemDanh: so,
  coMat: so,
  soLop: so,
  tiLeNop: soHoacTrong,
  tiLeCham: soHoacTrong,
  diemTB: soHoacTrong,
  tiLeChuyenCan: soHoacTrong,
  tienDoPct: soHoacTrong,
  lopCoKhung: so,
  lopCham: so,
};
const LOP_ROW = z.looseObject({
  ...O_SO,
  classId: so,
  name: z.string(),
  status: z.string(),
  trangThai: z.string(),
  termName: z.string().nullable(),
  teacherName: z.string().nullable(),
  chuongTrinhCham: z.boolean(),
});
const MON_ROW = z.looseObject({
  courseId: z.string().nullable(),
  courseTitle: z.string(),
  tong: z.looseObject(O_SO),
  lopTong: so,
  lop: z.array(LOP_ROW),
});
const HINH_DANG = z.looseObject({
  tu: z.string(),
  den: z.string(),
  courseId: z.string().nullable(),
  termId: soHoacTrong,
  mon: z.array(MON_ROW),
  tong: z.looseObject(O_SO),
  monOptions: z.array(z.looseObject({ id: z.string(), title: z.string() })),
  dotOptions: z.array(z.looseObject({ id: so, name: z.string().nullable() })),
  incomplete: z.array(z.string()),
  generatedAt: z.string().optional(),
});
type Payload = z.infer<typeof HINH_DANG>;
type OSo = Payload['tong'];

const DUONG = '/quan-tri/bao-cao-mon';
const O = 'min-h-11 w-full min-w-0 rounded-md border border-line-input bg-sunken px-3 text-input text-ink';

const THIEU_NHAN: Record<string, string> = {
  baiTap: 'bài tập',
  diem: 'điểm đã chấm',
  chuyenCan: 'chuyên cần',
  chuongTrinh: 'tiến độ chương trình',
  danhMuc: 'danh mục môn và đợt',
};

/**
 * `null` = CHƯA TÍNH ĐƯỢC (không có mẫu số) → dấu gạch, KHÔNG phải `0%`.
 *
 * Hai thứ ấy là hai câu trả lời khác nhau và khách sẽ hỏi: "0 %" nghĩa là đã giao bài mà
 * không em nào nộp — một lời buộc tội; `—` nghĩa là chưa có gì để đo. Máy chủ đã cẩn thận
 * trả `None` chứ không 0 (`bao_cao_cheo._chot`), nên chỗ duy nhất có thể làm mất công ấy
 * là đây.
 */
function pct(v: number | null) {
  return v === null ? '—' : `${v}%`;
}

/** 'YYYY-MM-DD' → 'DD/MM/YYYY'. */
function ngayVN(iso: string) {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

/**
 * Tông màu so với TRUNG BÌNH TOÀN TRUNG TÂM, không so với một ngưỡng nghĩ ra ở đây.
 *
 * Không có chuẩn ngành nào cho "tỉ lệ nộp bài bao nhiêu là khoẻ" — khác hẳn tỉ lệ giữ chân
 * ở trang Toàn trung tâm (ngưỡng ấy có tra cứu, và do MÁY CHỦ cấp). Viết cứng "dưới 80 %
 * là đỏ" ở đây sẽ là một giả định vô căn cứ nằm trong giao diện, và giả định trong giao
 * diện thì không ai bàn lại được. Cái đo được là: môn này so với cả trung tâm thế nào.
 */
function toneSo(v: number | null, tb: number | null) {
  if (v === null || tb === null) return 'neutral' as const;
  return v < tb ? 'warn' : 'good';
}

/** Một hàng số của bảng so sánh môn / bảng lớp — cùng thứ tự cột ở cả hai bảng. */
function CacCotSo({ r, tb }: { r: OSo; tb: number | null }) {
  return (
    <>
      <Td label="Đang học" num>
        {r.dangHoc}
      </Td>
      <Td label="Nộp bài">
        <span className="flex justify-end">
          <Chip tone={toneSo(r.tiLeNop, tb)}>{pct(r.tiLeNop)}</Chip>
        </span>
      </Td>
      <Td label="Đã nộp / phải nộp" num muted>
        {r.phaiNop === 0 ? '—' : `${r.daNop}/${r.phaiNop}`}
      </Td>
      <Td label="Đã chấm" num>
        {pct(r.tiLeCham)}
      </Td>
      <Td label="Điểm trung bình" num>
        {pct(r.diemTB)}
      </Td>
      <Td label="Chuyên cần" num>
        {pct(r.tiLeChuyenCan)}
      </Td>
      <Td label="Tiến độ chương trình" num>
        {pct(r.tienDoPct)}
      </Td>
    </>
  );
}

/** Phần đầu bảng — dùng chung để bảng môn và bảng lớp không thể lệch cột. */
function DauBang({ cot1 }: { cot1: string }) {
  return (
    <Thead>
      <tr>
        <Th>{cot1}</Th>
        <Th align="right">Đang học</Th>
        <Th align="right">Nộp bài</Th>
        <Th align="right">Đã nộp / phải nộp</Th>
        <Th align="right">Đã chấm</Th>
        <Th align="right">Điểm trung bình</Th>
        <Th align="right">Chuyên cần</Th>
        <Th align="right">Tiến độ</Th>
      </tr>
    </Thead>
  );
}

export default async function BaoCaoMonPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const mot = (k: string) => {
    const v = sp[k];
    return ((Array.isArray(v) ? v[0] : v) ?? '').trim();
  };
  const loc = { course_id: mot('course_id'), term_id: mot('term_id'), tu: mot('tu'), den: mot('den') };
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(loc)) if (v) qs.set(k, v);
  const chuoi = qs.toString();
  const kq = await serverJson<Payload>(
    `/api/admin/bao-cao-cheo${chuoi ? `?${chuoi}` : ''}`,
    { requireAuth: true },
    HINH_DANG,
  );

  if (!kq.ok) {
    return (
      <Card>
        <CardHead title="Kết quả theo môn" />
        <div className="rounded-md border border-danger/30 bg-danger/5 px-4 py-6" role="alert">
          <p className="text-subhead text-ink">Chưa mở được báo cáo</p>
          <p className="mt-1 text-body text-ink-2">{kq.message}</p>
        </div>
      </Card>
    );
  }

  const d = kq.data;
  const tb = d.tong.tiLeNop;
  const dangLoc = Boolean(loc.course_id || loc.term_id);
  /* Bảng tính mang ĐÚNG bộ lọc của màn: người ta tải về để mang đi họp, và một tệp lọc
     khác màn thì hai bản không bản nào tin được. `tu`/`den` gửi kèm cả khi người dùng
     chưa đặt — dùng kỳ xem máy chủ ĐÃ chọn, để tệp không rơi sang tháng khác nếu tải lúc
     nửa đêm. */
  const qsTai = new URLSearchParams({ tu: d.tu, den: d.den, dinh_dang: 'xlsx' });
  if (loc.course_id) qsTai.set('course_id', loc.course_id);
  if (loc.term_id) qsTai.set('term_id', loc.term_id);

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHead
          title="Kết quả theo môn"
          hint={`Từ ${ngayVN(d.tu)} đến ${ngayVN(d.den)}. Môn có tỉ lệ nộp bài thấp nhất xếp lên đầu.`}
          chiTiet={
            'Điểm trung bình quy về phần trăm theo thang của TỪNG bài, nên bài thang 10 và ' +
            'bài thang 100 so được với nhau. Học viên đã rời lớp không được tính. Ô có màu ' +
            'cam là thấp hơn trung bình toàn trung tâm. Dấu — nghĩa là chưa có gì để đo, ' +
            'khác hẳn 0%.'
          }
          action={
            <a
              href={`/api/admin/bao-cao-cheo?${qsTai.toString()}`}
              className="inline-flex min-h-11 items-center rounded-md border border-line px-4 text-small font-semibold text-ink-2 hover:border-brand hover:text-brand-ink"
            >
              Tải Excel
            </a>
          }
        />

        {d.incomplete.length > 0 && (
          <p
            role="alert"
            className="mb-3 rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-small text-danger-ink"
          >
            Chưa đọc được: {d.incomplete.map((k) => THIEU_NHAN[k] ?? k).join(' · ')}. Những cột
            liên quan bên dưới đang KHÔNG đáng tin — tải lại trang, nếu vẫn vậy thì báo kỹ thuật.
          </p>
        )}

        <form
          method="get"
          action={DUONG}
          role="search"
          aria-label="Lọc báo cáo theo môn, đợt học và khoảng ngày"
          className="mb-4 flex flex-wrap items-end gap-x-3 gap-y-2"
        >
          <label className="flex min-w-0 flex-[1_1_14rem] flex-col gap-1">
            <span className="text-label text-ink-3">Môn</span>
            {/* Danh mục từ máy chủ (`monOptions`), không gõ lại ở màn — RULES §7. */}
            <select name="course_id" defaultValue={loc.course_id} className={O}>
              <option value="">Tất cả các môn</option>
              {d.monOptions.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.title}
                </option>
              ))}
            </select>
          </label>
          <label className="flex min-w-0 flex-[1_1_12rem] flex-col gap-1">
            <span className="text-label text-ink-3">Đợt học</span>
            <select name="term_id" defaultValue={loc.term_id} className={O}>
              <option value="">Tất cả các đợt</option>
              {d.dotOptions.map((t) => (
                <option key={t.id} value={String(t.id)}>
                  {t.name ?? `Đợt ${t.id}`}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Từ ngày</span>
            <input type="date" name="tu" defaultValue={d.tu} className={O} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-label text-ink-3">Đến ngày</span>
            <input type="date" name="den" defaultValue={d.den} className={O} />
          </label>
          <span className="flex flex-wrap items-center gap-x-4">
            <button
              type="submit"
              className="min-h-11 rounded-md bg-brand-fill px-4 text-body font-semibold text-white hover:brightness-110"
            >
              Xem
            </button>
            {dangLoc && (
              <Link href={DUONG} className="inline-flex min-h-11 items-center text-small text-brand-ink underline">
                Bỏ lọc
              </Link>
            )}
          </span>
        </form>

        {d.mon.length === 0 ? (
          <EmptyState
            title="Chưa có lớp nào khớp bộ lọc"
            hint="Bỏ bớt điều kiện lọc, hoặc mở rộng khoảng ngày."
          />
        ) : (
          <TableWrap caption="So sánh các môn: tỉ lệ nộp bài, tỉ lệ chấm, điểm trung bình, chuyên cần, tiến độ">
            <DauBang cot1="Môn" />
            <Tbody>
              {d.mon.map((m) => (
                <Tr key={m.courseId ?? 'khong-gan'}>
                  <Td label="Môn">
                    <span className="font-semibold text-ink">{m.courseTitle}</span>
                    <span className="block text-ink-3">
                      {m.lopTong} lớp
                      {m.tong.lopCham > 0 ? ` · ${m.tong.lopCham} lớp chậm chương trình` : ''}
                    </span>
                  </Td>
                  <CacCotSo r={m.tong} tb={tb} />
                </Tr>
              ))}
              <Tr dim>
                <Td label="Môn">
                  <span className="font-semibold text-ink">Toàn trung tâm</span>
                  <span className="block text-ink-3">{d.tong.soLop} lớp</span>
                </Td>
                {/* Dòng tổng không tô màu so với chính nó. */}
                <CacCotSo r={d.tong} tb={null} />
              </Tr>
            </Tbody>
          </TableWrap>
        )}
      </Card>

      {/* Từng môn một thẻ: lớp TỤT NHẤT lên đầu (máy chủ xếp, `_khoa_xep_lop`). */}
      {d.mon.map((m) => (
        <Card key={m.courseId ?? 'khong-gan'}>
          <CardHead
            title={m.courseTitle}
            hint={
              m.lopTong > m.lop.length
                ? `Lớp cần xem lên đầu — đang hiện ${m.lop.length} trên ${m.lopTong} lớp. Bản tải Excel có đủ.`
                : `${m.lopTong} lớp, lớp tụt nhất lên đầu.`
            }
          />
          <TableWrap caption={`Từng lớp của môn ${m.courseTitle}: nộp bài, chấm bài, điểm, chuyên cần, tiến độ`}>
            <DauBang cot1="Lớp" />
            <Tbody>
              {m.lop.map((c) => (
                <Tr key={c.classId} dim={c.status !== 'active'}>
                  <Td label="Lớp">
                    <Link
                      href={`/giang-day/buoi-hoc/${c.classId}`}
                      /* `py-3.5` cho vùng chạm 48px, `-my-3.5` giữ nguyên chiều cao hàng —
                         cùng cách với bảng "Từng lớp" ở Toàn trung tâm. */
                      className="-my-3.5 inline-block py-3.5 font-semibold text-brand-ink underline"
                    >
                      {c.name}
                    </Link>
                    <span className="block text-ink-3">
                      {[c.termName, c.teacherName || 'chưa phân công giảng viên',
                        c.status === 'active' ? null : c.trangThai]
                        .filter(Boolean)
                        .join(' · ')}
                    </span>
                  </Td>
                  <CacCotSo r={c} tb={tb} />
                </Tr>
              ))}
            </Tbody>
          </TableWrap>
        </Card>
      ))}
    </div>
  );
}
