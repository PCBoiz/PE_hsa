import Link from 'next/link';

/**
 * Hai câu trả lời cho hai chuyện KHÁC NHAU, cố ý không gộp:
 *
 *   `KhongDocDuoc`   · backend sập / mạng hỏng — không biết bạn có quyền hay không
 *   `KhongDuQuyen`   · đọc được tài khoản, và tài khoản ấy không đủ quyền
 *
 * Gộp lại thành một câu "bạn không có quyền" là đẩy người dùng đi hỏi nhầm chỗ
 * mỗi lần máy chủ ngủ đông (Render gói free ngủ sau ~15 phút).
 */

function Khung({ tieu_de, children }: { tieu_de: string; children: React.ReactNode }) {
  return (
    <main className="mx-auto max-w-3xl px-4 py-16">
      <h1 className="text-title text-ink">{tieu_de}</h1>
      <p className="mt-2 text-body text-ink-2">{children}</p>
      <Link href="/dashboard" className="mt-6 inline-block text-body text-brand-ink underline">
        ← Về trang của tôi
      </Link>
    </main>
  );
}

export function KhongDocDuoc({ loi }: { loi: string }) {
  return <Khung tieu_de="Chưa mở được khu quản trị">{loi}</Khung>;
}

export function KhongDuQuyen({ can }: { can?: string }) {
  return (
    <Khung tieu_de="Không đủ quyền vào trang này">
      {can
        ? `Trang này dành cho ${can}. Nếu bạn cần quyền ấy, liên hệ người quản lý hệ thống.`
        : 'Tài khoản của bạn không có quyền vào đây. Nếu bạn là nhân sự của TopHSA và cần quyền này, liên hệ người quản lý hệ thống.'}
    </Khung>
  );
}
