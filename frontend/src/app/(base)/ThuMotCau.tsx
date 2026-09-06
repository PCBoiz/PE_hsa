'use client';

import { useState } from 'react';

/**
 * "Thử một câu HSA" — ô tương tác duy nhất trên trang giới thiệu.
 *
 * ── VÌ SAO THÊM (07/09/2026) ──────────────────────────────────────────────
 *
 * Đo trang giới thiệu trước hôm nay: cao 5343px trên máy tính, 9651px trên
 * điện thoại, và **sáu liên kết trên toàn trang** — gần như chỉ MỘT hành động
 * là "Đăng nhập". Tức một người vào xem không làm được gì ngoài việc bỏ đi
 * hoặc đăng nhập, mà họ chưa có tài khoản để đăng nhập.
 *
 * Với một sản phẩm LUYỆN THI, thứ thuyết phục nhất không phải câu chữ mô tả —
 * là để người ta làm thử một câu và thấy ngay mình đúng hay sai, kèm lời giải.
 * Ba mươi giây ấy nói được nhiều hơn cả trang.
 *
 * ── VÌ SAO KHÔNG LẤY CÂU THẬT TỪ CSDL ────────────────────────────────────
 *
 * Ngân hàng đề là tài sản của TopHSA và học viên sẽ gặp lại chính những câu ấy
 * khi thi thử. Đưa một câu thật lên trang công khai là đem đáp án ra ngoài.
 * Ba câu dưới đây viết riêng cho trang này, ĐÚNG DẠNG của ba hợp phần nhưng
 * không nằm trong đề nào — và nói thẳng điều đó cho người đọc.
 *
 * ── KHÔNG HỨA CON SỐ NÀO ─────────────────────────────────────────────────
 *
 * Ô này không nói "95% học viên đỗ" hay bất kỳ thống kê nào. Trung tâm chưa có
 * khoá nào chạy xong (đo 07/09: 0 đợt học, 0 buổi). Một con số bịa trên trang
 * bán hàng là thứ đắt nhất trong cả sản phẩm khi bị phát hiện.
 */

type Cau = {
  hop_phan: string;
  de: string;
  lua_chon: readonly string[];
  dung: number;
  giai: string;
};

/** Ba câu MẪU, mỗi hợp phần một câu. Không nằm trong đề thi thử nào. */
const CAU: readonly Cau[] = [
  {
    hop_phan: 'Tư duy Định lượng',
    de: 'Một số tăng 20%, sau đó giảm 20%. So với ban đầu, số ấy thay đổi thế nào?',
    lua_chon: ['Không đổi', 'Tăng 4%', 'Giảm 4%', 'Giảm 20%'],
    dung: 2,
    giai: 'Nhân hệ số: 1,2 × 0,8 = 0,96 — tức còn 96%, giảm 4%. Bẫy ở đây là cộng '
      + 'trừ phần trăm như cộng trừ số, mà phần trăm thì nhân chứ không cộng.',
  },
  {
    hop_phan: 'Tư duy Định tính',
    de: 'Trong câu "Anh ấy chạy rất nhanh nhưng vẫn không kịp chuyến tàu", '
      + 'từ "nhưng" thể hiện quan hệ gì?',
    lua_chon: ['Nguyên nhân – kết quả', 'Tương phản', 'Bổ sung', 'Điều kiện'],
    dung: 1,
    giai: 'Vế sau đi ngược với điều vế trước làm người đọc chờ đợi — chạy nhanh thì '
      + 'lẽ ra kịp. Đó là quan hệ TƯƠNG PHẢN. Câu hỏi dạng này kiểm tra việc đọc '
      + 'quan hệ giữa các vế, không kiểm tra từ vựng.',
  },
  {
    hop_phan: 'Khoa học & Tiếng Anh',
    de: 'Choose the word that best completes the sentence: '
      + '"Despite the heavy rain, the match ___ as scheduled."',
    lua_chon: ['was cancelled', 'went ahead', 'was postponed', 'had ended'],
    dung: 1,
    giai: '"Despite" báo hiệu một sự tương phản: mưa to NHƯNG trận đấu vẫn diễn ra. '
      + 'Ba phương án kia đều đi cùng chiều với mưa to, nên chúng làm câu mất đi '
      + 'chính sự tương phản mà "despite" vừa dựng lên.',
  },
];

export default function ThuMotCau() {
  const [i, setI] = useState(0);
  const [chon, setChon] = useState<number | null>(null);
  const c = CAU[i];
  const xong = chon !== null;
  const dung = chon === c.dung;

  return (
    <div className="thu-cau">
      <div className="thu-cau-dau">
        <span className="thu-cau-nhan">Thử một câu — không cần tài khoản</span>
        <span className="thu-cau-hp">{c.hop_phan}</span>
      </div>

      <p className="thu-cau-de">{c.de}</p>

      <div className="thu-cau-dsach" role="group" aria-label="Các phương án">
        {c.lua_chon.map((v, k) => {
          /* Sau khi chọn: tô ĐÁP ÁN ĐÚNG màu xanh dù người dùng chọn gì, và tô
             lựa chọn SAI của họ màu đỏ. Chỉ tô cái họ chọn thì người chọn sai
             biết mình sai mà không biết đúng là gì — nửa vời, và đúng thứ làm
             người ta bỏ đi. */
          const lop = !xong ? '' : k === c.dung ? ' la-dung' : k === chon ? ' la-sai' : ' mo-di';
          return (
            <button
              key={v}
              type="button"
              className={'thu-cau-nut' + lop}
              onClick={() => { if (!xong) setChon(k); }}
              disabled={xong}
              aria-pressed={chon === k}
            >
              <span className="thu-cau-ky" aria-hidden="true">{String.fromCharCode(65 + k)}</span>
              <span>{v}</span>
            </button>
          );
        })}
      </div>

      {xong && (
        /* `aria-live`: người dùng trình đọc màn hình không thấy màu đổi. Không
           có dòng này thì với họ, bấm xong là không có gì xảy ra. */
        <div className="thu-cau-giai" role="status" aria-live="polite">
          <p className={'thu-cau-ket ' + (dung ? 'dung' : 'sai')}>
            {dung ? 'Đúng rồi.' : `Chưa đúng — đáp án là ${String.fromCharCode(65 + c.dung)}.`}
          </p>
          <p className="thu-cau-vi-sao">{c.giai}</p>
        </div>
      )}

      <div className="thu-cau-cuoi">
        <button
          type="button"
          className="thu-cau-tiep"
          onClick={() => { setI((v) => (v + 1) % CAU.length); setChon(null); }}
        >
          {xong ? 'Câu tiếp →' : 'Đổi câu khác'}
        </button>
        {/* Nói rõ đây là câu MẪU. Người học gặp lại một câu ở đề thi thử rồi
            phát hiện nó nằm sẵn trên trang chủ thì niềm tin vào cả ngân hàng
            đề bị lung lay — nên tách bạch ngay từ đầu. */}
        <span className="thu-cau-luu-y">
          Câu mẫu, đúng dạng HSA · không nằm trong đề thi thử nào
        </span>
      </div>
    </div>
  );
}
