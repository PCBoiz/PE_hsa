'use client';

import { useEffect, useState } from 'react';

import { Button } from '@/components/ui';
import { apiFetch, errorText } from '@/lib/api';

/**
 * "Thêm lịch học vào điện thoại" — địa chỉ lịch riêng (§71, 26/09/2026).
 *
 * Người dùng bấm một lần, nhận một địa chỉ, dán vào Google Calendar / Lịch
 * iPhone / Outlook. Từ đó mọi buổi mới, buổi dời và buổi huỷ tự về máy họ mà
 * không phải mở lại trang này.
 *
 * VÌ SAO ĐỊA CHỈ CHỈ HIỆN MỘT LẦN: máy chủ chỉ giữ BĂM của chìa, nên không có
 * cách nào hiện lại địa chỉ cũ — muốn xem lại thì cấp cái mới, và cái cũ chết
 * ngay lúc ấy. Đổi lại, ai đọc được cơ sở dữ liệu cũng không mở được lịch của
 * người khác. Chữ trên màn phải nói rõ điều đó trước khi họ đóng hộp thoại.
 *
 * Chuyển động: chỉ đổi độ mờ, 160 ms, và tắt hẳn khi người dùng đã chọn "giảm
 * chuyển động" trong hệ điều hành.
 */
export default function ThemVaoLich({ nhan = 'Thêm vào lịch điện thoại' }: { nhan?: string }) {
  const [dangCo, setDangCo] = useState<boolean | null>(null);
  const [diaChi, setDiaChi] = useState('');
  const [dangLay, setDangLay] = useState(false);
  const [loi, setLoi] = useState('');
  const [daChep, setDaChep] = useState(false);

  useEffect(() => {
    let con = true;
    apiFetch('/api/lich/dia-chi')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => con && setDangCo(Boolean(d?.daCo)))
      .catch(() => con && setDangCo(false));
    return () => {
      con = false;
    };
  }, []);

  async function lay() {
    setDangLay(true);
    setLoi('');
    try {
      const r = await apiFetch('/api/lich/dia-chi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scope: 'toi' }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(errorText(r.status, d));
      setDiaChi(new URL(d.duongDan, window.location.origin).toString());
      setDangCo(true);
    } catch (e) {
      setLoi(e instanceof Error ? e.message : 'Không lấy được địa chỉ lịch. Thử lại giúp tôi.');
    } finally {
      setDangLay(false);
    }
  }

  async function chep() {
    try {
      await navigator.clipboard.writeText(diaChi);
      setDaChep(true);
      setTimeout(() => setDaChep(false), 2500);
    } catch {
      setLoi('Trình duyệt không cho chép tự động — anh/chị bôi đen rồi chép tay giúp tôi.');
    }
  }

  return (
    <section className="rounded-lg border border-line bg-surface-2 p-4">
      <h2 className="text-body font-semibold text-ink">Xem lịch học trên điện thoại</h2>
      <p className="mt-1 text-small text-ink-2">
        Thêm một lần, sau đó buổi mới, buổi dời và buổi huỷ tự hiện trong ứng dụng lịch — không cần
        mở lại trang này.
      </p>

      {!diaChi && (
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <Button onClick={() => void lay()} loading={dangLay}>
            {dangCo ? 'Lấy địa chỉ mới' : nhan}
          </Button>
          {dangCo && (
            <span className="text-small text-ink-3">
              Lấy địa chỉ mới sẽ ngừng địa chỉ cũ đang dùng.
            </span>
          )}
        </div>
      )}

      {diaChi && (
        <div className="mt-3 motion-safe:transition-opacity motion-safe:duration-150">
          <label className="text-small text-ink-2" htmlFor="dia-chi-lich">
            Địa chỉ lịch của bạn — chép rồi dán vào ứng dụng lịch:
          </label>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <input
              id="dia-chi-lich"
              readOnly
              value={diaChi}
              onFocus={(e) => e.currentTarget.select()}
              className="min-w-0 flex-1 rounded-md border border-line bg-surface px-3 py-2 font-mono text-small text-ink"
            />
            <Button onClick={() => void chep()} variant="ghost">
              {daChep ? 'Đã chép' : 'Chép'}
            </Button>
          </div>
          <p className="mt-2 text-small text-warning-ink">
            Địa chỉ này chỉ hiện đúng lần này. Đóng trang mà chưa dán thì phải lấy địa chỉ mới.
          </p>
          <details className="mt-2">
            <summary className="cursor-pointer text-small text-ink-2">Dán vào đâu?</summary>
            <ul className="mt-1 list-disc pl-5 text-small text-ink-2">
              <li>
                <b>Google Calendar</b> (máy tính): Cài đặt → Thêm lịch → Từ URL → dán → Thêm lịch.
              </li>
              <li>
                <b>iPhone</b>: Cài đặt → Ứng dụng → Lịch → Tài khoản → Thêm tài khoản → Khác → Thêm
                lịch đăng ký → dán.
              </li>
              <li>
                <b>Outlook</b>: Lịch → Thêm lịch → Đăng ký từ web → dán.
              </li>
            </ul>
          </details>
          <p className="mt-2 text-small text-ink-3">
            Ai có địa chỉ này đều xem được lịch của bạn, nên đừng đăng nó ở chỗ công khai.
          </p>
        </div>
      )}

      {loi && (
        <p role="alert" className="mt-2 text-small text-danger">
          {loi}
        </p>
      )}
    </section>
  );
}
