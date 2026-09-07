import { Card, CardHead, EmptyState } from '@/components/ui';
import { serverJson } from '@/lib/server-api';

import BangCoSo, { type Lop } from './BangCoSo';

/**
 * CƠ SỞ TÍNH HỌC PHÍ — những con số ai tính học phí cũng cần, và không hơn.
 *
 * ── RANH GIỚI, VÀ VÌ SAO NÓ NẰM ĐÚNG Ở ĐÂY ────────────────────────────────
 *
 * `docs/ERP_TOPHSA` §7 nói về nhóm kinh doanh: "không tận dụng được gì đã dựng
 * và **sai một chi tiết là sai sổ sách**", khuyến nghị chỉ làm sau khi có quy
 * trình thu chi thật của TopHSA. Anh Sơn chốt 07/09/2026: dựng **cơ sở tính**,
 * không dựng bảng giá / hoá đơn / công nợ.
 *
 * Trang này vì thế **không có một con số tiền nào**. Nó trả lời đúng những câu
 * đã xảy ra thật ở trung tâm — em vào lớp ngày nào, lớp đã mở mấy buổi, em có
 * mặt mấy buổi — những câu đúng như nhau dù TopHSA thu theo tháng, theo khoá
 * hay theo buổi.
 *
 * `tests_co_so_hoc_phi.py::test_KHONG_co_truong_tien_nao_trong_phan_hoi` canh
 * ranh giới ấy bằng máy, vì một dòng `donGia` thêm vào lúc nào đó sẽ xoá nó đi
 * mà không ai nhận ra.
 *
 * ── TRANG NÀY HÔM NAY GẦN NHƯ TRỐNG, VÀ NÓ PHẢI NÓI THẾ ──────────────────
 *
 * Đo 07/09/2026 trên CSDL thật: **0 đợt học, 0 buổi học, 0 lượt điểm danh.**
 * Nên bảng dưới sẽ không có gì. Trang không được vẽ một khung trống rồi để
 * người xem tự đoán — nó phải nói ra rằng chưa có gì để tính, và nói **cần ghi
 * gì thì mới có**.
 */
export const dynamic = 'force-dynamic';
export const metadata = { title: 'Cơ sở tính học phí | TopHSA' };

type Payload = {
  ky: { tu: string | null; den: string | null };
  dot: { id: number; code: string; name: string } | null;
  lop: Lop[];
};

export default async function CoSoHocPhiPage() {
  const kq = await serverJson<Payload>('/api/admin/co-so-hoc-phi', { requireAuth: true });
  const lop = kq.ok ? kq.data.lop : [];
  const coBuoi = lop.some((l) => l.buoiDaMo > 0);

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHead
          title="Cơ sở tính học phí"
          hint="Bảng này KHÔNG có giá và KHÔNG tính tiền. Nó gộp những gì đã xảy ra thật — ai học lớp nào, từ ngày nào, lớp đã mở mấy buổi, em dự mấy buổi — để người tính học phí có một chỗ lấy số thay vì đếm tay."
        />

        {!kq.ok && (
          <p role="alert" className="text-small text-danger-ink">{kq.message}</p>
        )}

        {/* Vì sao dừng ở đây. Người mở trang lần đầu sẽ hỏi ngay "thế tiền
            đâu", và câu trả lời phải nằm ngay trên màn chứ không nằm trong một
            tệp .md nào đó. */}
        <div className="rounded-md border border-line bg-sunken px-4 py-3">
          <p className="text-body font-semibold text-ink">Vì sao chưa có phần tính tiền</p>
          <p className="mt-1 text-small text-ink-2">
            Đặc tả ERP §7 ghi rõ: nhóm kinh doanh <strong>sai một chi tiết là sai
            sổ sách</strong>, và khuyên nên nối với phần mềm kế toán trung tâm đang
            dùng thay vì viết lại. Giá một buổi, thu theo tháng hay theo khoá, nghỉ
            có phép có trừ tiền không — đều là chính sách của TopHSA, không phải
            thứ đoán được. Cột bên dưới là phần <em>không</em> phụ thuộc vào những
            câu trả lời ấy.
          </p>
        </div>
      </Card>

      {lop.length === 0 ? (
        <Card>
          <EmptyState
            title="Chưa có lớp nào để tính"
            hint="Tạo lớp ở mục Lớp học, rồi xếp học viên vào."
          />
        </Card>
      ) : !coBuoi ? (
        <Card>
          <CardHead title="Chưa có buổi học nào được mở" />
          {/* Nói CẦN GÌ, không chỉ nói THIẾU GÌ. Đây là trạng thái thật của
              trung tâm hôm nay, nên nó là màn hình người ta gặp đầu tiên. */}
          <p className="text-body text-ink-2">
            Có {lop.length} lớp, nhưng chưa lớp nào mở buổi học nào — nên chưa có
            gì để tính. Bảng này chỉ có số khi ba việc sau đã chạy:
          </p>
          <ol className="mt-3 flex list-decimal flex-col gap-2 pl-5 text-body text-ink-2">
            <li>
              <strong>Mở đợt học</strong> và gán lớp vào đợt — để bảng cắt được
              theo kỳ thu thay vì gộp toàn bộ lịch sử.
            </li>
            <li>
              <strong>Tạo buổi học</strong> trong lớp — đây là thứ đang thiếu
              hoàn toàn (đo hôm nay: 0 buổi).
            </li>
            <li>
              <strong>Điểm danh</strong>{' '}từng buổi — cột &ldquo;có mặt&rdquo; lấy
              thẳng từ đó.
            </li>
          </ol>
          <p className="mt-3 text-small text-ink-3">
            Ngày vào lớp và ngày rời lớp thì đã có sẵn, nên cột &ldquo;buổi trong
            kỳ&rdquo; sẽ đúng ngay từ buổi đầu tiên được ghi.
          </p>
        </Card>
      ) : (
        <BangCoSo lop={lop} />
      )}
    </div>
  );
}
