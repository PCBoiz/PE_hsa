// Nạp CSS byte-nguyên-xi từ /public/static/css qua <link> — đúng cơ chế Flask cũ:
// mỗi trang chỉ load ĐÚNG tổ hợp CSS của nó, đúng thứ tự; không qua bundler
// (CSS gốc có vài đoạn non-strict mà parser của Next từ chối, trình duyệt thì không).
// Link tag nằm trong JSX của page → unmount trang là CSS được gỡ, không bleed
// giữa các route khi client-side navigate.
export default function PageStyles({ hrefs }: { hrefs: string[] }) {
  return (
    <>
      {hrefs.map((href) => (
        <link key={href} rel="stylesheet" href={href} />
      ))}
    </>
  );
}
