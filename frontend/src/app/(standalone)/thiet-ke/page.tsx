import {
  Button,
  Card,
  CardHead,
  Chip,
  EmptyState,
  Field,
  TableWrap,
  Tbody,
  Td,
  Th,
  Thead,
  Tile,
  TileRow,
  Tr,
} from '@/components/ui';

/**
 * Trang tra cứu hệ thiết kế.
 *
 * Mục đích: xem mọi token và mọi component ở một chỗ, ở cả hai theme, mà không
 * phải mở file CSS. Trước đây không có trang này nên mỗi khối tính năng lại tự
 * đoán một cỡ chữ, một bán kính bo — và sản phẩm có 33 cỡ chữ với 25 bán kính.
 *
 * Không nối vào thanh điều hướng: đây là công cụ nội bộ, tới bằng cách gõ
 * thẳng /thiet-ke.
 */
export const metadata = { title: 'Hệ thiết kế — pe_hsa' };

/* Tên lớp phải viết NGUYÊN VĂN, không ghép chuỗi `text-${cls}`: Tailwind quét
   mã nguồn dưới dạng văn bản tĩnh, tên lớp dựng lúc chạy sẽ không được sinh ra
   và chữ rơi về cỡ mặc định. */
const TYPE = [
  ['text-display', 'display', 'Tỉ lệ và phần trăm', '34px · 800 · 1.15'],
  ['text-title', 'title', 'Bản đồ năng lực', '26px · 700 · 1.25'],
  ['text-section', 'section', 'Kế hoạch tuần này', '19px · 600 · 1.35'],
  ['text-subhead', 'subhead', 'Bước 3 · Lý thuyết', '17px · 600 · 1.5'],
  ['text-body', 'body', 'Cỡ chữ thân bài. Mọi đoạn văn học viên phải đọc đều dùng cỡ này.', '15px · 400 · 1.6'],
  ['text-small', 'small', 'Chữ phụ: chú thích, mô tả, ô trong bảng dày.', '13px · 400 · 1.5'],
  ['text-label', 'label', 'Nhãn — sàn tuyệt đối', '12px · 700 · giãn 0.05em'],
] as const;

const COLORS = [
  ['--bg', 'Nền trang', 'bg-ground'],
  ['--card', 'Mặt thẻ', 'bg-surface'],
  ['--lift', 'Mặt chìm', 'bg-sunken'],
  ['--brand', 'Tím thương hiệu', 'bg-brand'],
  ['--success', 'Teal hoàn thành', 'bg-success'],
  ['--warning', 'Cảnh báo', 'bg-warning'],
  ['--danger', 'Nguy hiểm', 'bg-danger'],
] as const;

export default function DesignSystemPage() {
  return (
    /* Trang này không nạp file CSS cũ nào, nên tự sơn nền: body của sản phẩm
       lấy nền từ style.css của từng trang, không phải từ theme.css. */
    <main className="min-h-dvh bg-ground px-6 py-12 text-ink-2 [&>*]:mx-auto [&>*]:max-w-[960px]">
      <p className="mb-3 text-label text-brand">Hệ thiết kế · pe_hsa</p>
      <h1 className="mb-3 text-display text-ink">Tra cứu token và component</h1>
      <p className="mb-8 max-w-[62ch] text-body">
        Mọi màn hình mới dựng từ trang này. Màu lấy nguyên từ{' '}
        <code className="font-mono text-small">theme.css</code> — token Tailwind chỉ trỏ{' '}
        <code className="font-mono text-small">var()</code> vào đó, nên không thể có hai nguồn
        màu lệch nhau. Chuyển sáng/tối bằng công tắc sẵn có của sản phẩm để kiểm cả hai bộ.
      </p>

      {/* ── Màu ── */}
      <h2 className="mb-3 text-title text-ink">Màu</h2>
      <p className="mb-4 max-w-[62ch] text-body">
        Bảng màu đã khoá. Bảy biến dưới đây là toàn bộ những gì được dùng; mọi sắc độ khác
        sinh ra từ chúng bằng độ mờ.
      </p>
      <div className="mb-10 grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,150px),1fr))]">
        {COLORS.map(([token, name, cls]) => (
          <Card key={token} padding="sm">
            <div className={`mb-2 h-12 rounded-sm border border-line ${cls}`} />
            <p className="text-small font-semibold text-ink">{name}</p>
            <p className="font-mono text-label text-ink-3 normal-case">{token}</p>
          </Card>
        ))}
      </div>

      {/* ── Chữ ── */}
      <h2 className="mb-3 text-title text-ink">Thang chữ</h2>
      <p className="mb-4 max-w-[62ch] text-body">
        Tám bậc, thay cho 33 cỡ rời rạc trước đây. Sàn tuyệt đối 12px. Khoảng dòng rộng hơn
        thông lệ tiếng Anh vì tiếng Việt có dấu chồng hai tầng — bó dòng lại là cắt mất dấu.
      </p>
      <Card padding="none" className="mb-10 overflow-hidden">
        {TYPE.map(([cls, name, sample, spec]) => (
          <div
            key={name}
            className="grid items-baseline gap-3 border-b border-line/50 px-4 py-3 last:border-b-0 [grid-template-columns:minmax(0,84px)_minmax(0,124px)_minmax(0,1fr)]"
          >
            <b className="font-mono text-label text-brand normal-case">{name}</b>
            <i className="text-label text-ink-3 not-italic normal-case">{spec}</i>
            <span className={`${cls} text-ink`}>{sample}</span>
          </div>
        ))}
      </Card>

      {/* ── Nút ── */}
      <h2 className="mb-3 text-title text-ink">Nút</h2>
      <p className="mb-4 max-w-[62ch] text-body">
        Cao tối thiểu 44px — sàn vùng chạm cho ngón tay. Mỗi màn hình chỉ nên có một nút
        chính; những hành động còn lại phải nhạt hơn hẳn.
      </p>
      <div className="mb-10 flex flex-wrap items-center gap-3">
        <Button>Bắt đầu bài học</Button>
        <Button variant="ghost">Để sau</Button>
        <Button variant="danger">Xoá lớp</Button>
        <Button size="sm" variant="ghost">
          Cỡ nhỏ
        </Button>
        <Button loading>Đang lưu</Button>
        <Button disabled>Chưa mở</Button>
      </div>

      {/* ── Chip ── */}
      <h2 className="mb-3 text-title text-ink">Chip trạng thái</h2>
      <p className="mb-4 max-w-[62ch] text-body">
        Bốn bậc thành thạo dùng chung giữa bản đồ năng lực của học viên và bảng lớp của giảng
        viên — một chủ đề phải trông giống nhau ở cả hai bên.
      </p>
      <div className="mb-10 flex flex-wrap gap-2">
        <Chip level={4}>Đã nắm vững</Chip>
        <Chip level={3}>Khá</Chip>
        <Chip level={2}>Cần ôn lại</Chip>
        <Chip level={1}>Yếu</Chip>
        <Chip>Chưa đủ dữ liệu</Chip>
        <Chip tone="brand">Đang học</Chip>
      </div>

      {/* ── Ô số ── */}
      <h2 className="mb-3 text-title text-ink">Ô số thống kê</h2>
      <p className="mb-4 max-w-[62ch] text-body">
        Số dùng phông đơn cách và thẳng cột. Ô cảnh báo chỉ đổi màu khi số lớn hơn 0 — bảng
        lúc nào cũng đỏ thì mắt bỏ qua ngay.
      </p>
      <div className="mb-10">
        <TileRow>
          <Tile value="3" label="học viên" />
          <Tile value="4%" label="tiến độ trung bình" />
          <Tile value="2" label="cần chú ý ngay" tone="warn" />
          <Tile value="0" label="chậm tiến độ" />
          <Tile value="12" label="bài đã xong" tone="good" />
        </TileRow>
      </div>

      {/* ── Ô nhập ── */}
      <h2 className="mb-3 text-title text-ink">Ô nhập</h2>
      <div className="mb-10 grid max-w-[520px] gap-4">
        <Field id="demo-email" label="Email hoặc số điện thoại" placeholder="ban@email.com" />
        <Field
          id="demo-err"
          label="Mật khẩu"
          type="password"
          defaultValue="123"
          error="Mật khẩu phải có ít nhất 8 ký tự."
        />
        <Field
          id="demo-hint"
          label="Ngày thi dự kiến"
          type="date"
          hint="Dùng để tính lịch học mỗi tuần từ nay tới ngày thi."
        />
      </div>

      {/* ── Bảng ── */}
      <h2 className="mb-3 text-title text-ink">Bảng</h2>
      <p className="mb-4 max-w-[62ch] text-body">
        Luôn cuộn ngang trong khung riêng để trang không bao giờ trượt ngang. Học viên đã rời
        lớp thì làm mờ, không xoá khỏi bảng.
      </p>
      <div className="mb-10">
        <TableWrap>
          <Thead>
            <tr>
              <Th>Học viên</Th>
              <Th align="right">Tiến độ</Th>
              <Th align="right">Đề đã làm</Th>
              <Th>Trạng thái</Th>
            </tr>
          </Thead>
          <Tbody>
            <Tr>
              <Td label="Học viên">
                <b className="text-ink">Nguyễn Minh Anh</b>
                <div className="text-small text-ink-3">minhanh@email.com</div>
              </Td>
              <Td label="Tiến độ" num>3/76</Td>
              <Td label="Đề đã làm" num>1</Td>
              <Td label="Trạng thái">
                <Chip tone="warn">Nghỉ 10 ngày</Chip>
              </Td>
            </Tr>
            <Tr>
              <Td label="Học viên">
                <b className="text-ink">Trần Bảo Long</b>
                <div className="text-small text-ink-3">baolong@email.com</div>
              </Td>
              <Td label="Tiến độ" num>5/76</Td>
              <Td label="Đề đã làm" num>0</Td>
              <Td label="Trạng thái">
                <Chip tone="good">Đang học đều</Chip>
              </Td>
            </Tr>
            <Tr dim>
              <Td label="Học viên">
                <b className="text-ink">Lê Thu Hà</b>
                <div className="text-small text-ink-3">thuha@email.com</div>
              </Td>
              <Td label="Tiến độ" num>18/76</Td>
              <Td label="Đề đã làm" num>4</Td>
              <Td label="Trạng thái">
                <Chip>Đã rời lớp</Chip>
              </Td>
            </Tr>
          </Tbody>
        </TableWrap>
      </div>

      {/* ── Trạng thái rỗng ── */}
      <h2 className="mb-3 text-title text-ink">Trạng thái rỗng</h2>
      <p className="mb-4 max-w-[62ch] text-body">
        Dạng thứ hai là dạng riêng của sản phẩm này: hệ thống từ chối chấm điểm khi chưa đủ
        dữ liệu, và nói thẳng lý do thay vì hiện số 0.
      </p>
      <div className="mb-10 grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr))]">
        <EmptyState
          title="Chưa có lớp nào"
          hint="Tạo lớp đầu tiên rồi thêm học viên bằng email của các em."
          action={<Button size="sm">Tạo lớp</Button>}
        />
        <EmptyState
          tone="measuring"
          title="Chưa đủ dữ liệu để đánh giá"
          hint="Cần ít nhất 2 lần làm bài ở chủ đề này. Làm thêm một bài nữa là hệ thống chấm được."
        />
      </div>

      {/* ── Thẻ ── */}
      <h2 className="mb-3 text-title text-ink">Thẻ</h2>
      <div className="grid gap-3 [grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr))]">
        <Card>
          <CardHead title="Tuần này" hint="4 bài, 2 đề thi thử" />
          <p className="text-body">
            Thẻ nổi dùng cho khối nội dung chính. Bên trong không lồng thêm thẻ nổi nữa.
          </p>
        </Card>
        <Card tone="sunken">
          <CardHead title="Ô phụ" hint="Nằm bên trong một thẻ khác" />
          <p className="text-body">Mặt chìm dùng cho khối phụ, để thứ bậc luôn rõ.</p>
        </Card>
      </div>
    </main>
  );
}
