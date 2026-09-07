'use client';

import { useState } from 'react';

/**
 * "Thử ba câu" — bản rút gọn của trải nghiệm thi thử, chạy ngay trên trang.
 *
 * ── VÌ SAO VIẾT LẠI (07/09/2026) ──────────────────────────────────────────
 *
 * Bản trước cho làm MỘT câu rồi hiện đáp án. Anh Sơn: *"ai lại cho 1 câu thử ở
 * landing cơ chứ, mình phải thu hút học viên mà?"* — đúng.
 *
 * Một câu chỉ chứng minh "trang này có ô bấm được". Nó KHÔNG chứng minh thứ
 * TopHSA thật sự bán: **làm xong thì biết mình yếu hợp phần nào.** Mà để nói
 * được câu đó thì cần ít nhất một câu cho mỗi hợp phần — đúng ba câu, đúng cấu
 * trúc đề HSA.
 *
 * Nên ô này nay đi trọn một vòng nhỏ của sản phẩm: làm ba câu → nhận bảng phân
 * tích theo hợp phần → thấy ngay mình lệch ở đâu. Đó là bản rút gọn TRUNG THỰC
 * của đề 150 câu, không phải một trò chơi khác.
 *
 * ── VÌ SAO KHÔNG LẤY CÂU THẬT TỪ CSDL ────────────────────────────────────
 *
 * Ngân hàng đề là tài sản của TopHSA và học viên sẽ gặp lại chính những câu ấy
 * khi thi thử. Đưa câu thật lên trang công khai là đem đáp án ra ngoài. Ba câu
 * dưới đây viết riêng cho trang này, ĐÚNG DẠNG của ba hợp phần nhưng không nằm
 * trong đề nào — và ô này nói thẳng điều đó.
 *
 * ── KHÔNG HỨA CON SỐ NÀO ─────────────────────────────────────────────────
 *
 * Không "95% học viên đỗ", không "điểm trung bình tăng N". Trung tâm chưa có
 * khoá nào chạy xong (đo 07/09: 0 đợt học, 0 buổi). Một con số bịa trên trang
 * bán hàng là thứ đắt nhất trong cả sản phẩm khi bị phát hiện.
 */

type Cau = {
  hop_phan: string;
  ma: 'dinh_luong' | 'dinh_tinh' | 'khoa_hoc';
  de: string;
  lua_chon: readonly string[];
  dung: number;
  giai: string;
};

/** Ba câu MẪU, mỗi hợp phần một câu — đúng cấu trúc đề HSA. */
const CAU: readonly Cau[] = [
  {
    hop_phan: 'Tư duy Định lượng',
    ma: 'dinh_luong',
    de: 'Một số tăng 20%, sau đó giảm 20%. So với ban đầu, số ấy thay đổi thế nào?',
    lua_chon: ['Không đổi', 'Tăng 4%', 'Giảm 4%', 'Giảm 20%'],
    dung: 2,
    giai: 'Nhân hệ số: 1,2 × 0,8 = 0,96 — tức còn 96%, giảm 4%. Bẫy ở đây là cộng '
      + 'trừ phần trăm như cộng trừ số, mà phần trăm thì nhân chứ không cộng.',
  },
  {
    hop_phan: 'Tư duy Định tính',
    ma: 'dinh_tinh',
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
    ma: 'khoa_hoc',
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
  const [chon, setChon] = useState<(number | null)[]>([null, null, null]);
  const [xongHet, setXongHet] = useState(false);

  const c = CAU[i];
  const daChon = chon[i];
  const xong = daChon !== null;
  const dung = daChon === c.dung;
  const soDung = chon.filter((v, k) => v === CAU[k].dung).length;

  function traLoi(k: number) {
    if (xong) return;
    const moi = [...chon];
    moi[i] = k;
    setChon(moi);
  }

  function tiep() {
    if (i < CAU.length - 1) setI(i + 1);
    else setXongHet(true);
  }

  function lamLai() {
    setChon([null, null, null]);
    setI(0);
    setXongHet(false);
  }

  /* ── MÀN KẾT: bảng phân tích theo hợp phần ───────────────────────────────
     Đây là lý do ô này tồn tại. Một câu đúng/sai thì trang nào cũng làm được;
     thứ người học chưa từng thấy ở nơi khác là NHÌN RA MÌNH LỆCH Ở ĐÂU. */
  if (xongHet) {
    return (
      <div className="thu-cau">
        <div className="thu-cau-dau">
          <span className="thu-cau-nhan">Kết quả — {soDung}/{CAU.length} câu đúng</span>
        </div>

        <ul className="thu-cau-bang" aria-label="Kết quả theo hợp phần">
          {CAU.map((q, k) => {
            const ok = chon[k] === q.dung;
            return (
              <li key={q.ma} className={'thu-cau-hang ' + (ok ? 'la-dung' : 'la-sai')}>
                <span className="thu-cau-hp-ten">{q.hop_phan}</span>
                {/* Ký hiệu KÈM CHỮ: một ô chỉ có màu thì người dùng trình đọc
                    màn hình nghe một hàng im lặng. */}
                <span className="thu-cau-hp-kq">{ok ? 'Đúng' : 'Chưa đúng'}</span>
              </li>
            );
          })}
        </ul>

        <p className="thu-cau-vi-sao">
          {soDung === CAU.length
            ? 'Cả ba hợp phần đều đúng. Đề thật dài hơn nhiều, nên thứ quyết định điểm là giữ đều được ở cả ba — không phải giỏi một phần.'
            : 'Điểm HSA cộng cả ba hợp phần, nên phần bạn vừa sai chính là phần kéo điểm xuống nhiều nhất. Học viên TopHSA nhận đúng bảng này sau mỗi đề thi thử, nhưng chi tiết tới từng chủ đề.'}
        </p>

        <div className="thu-cau-cuoi">
          <button type="button" className="thu-cau-tiep" onClick={lamLai}>
            Làm lại
          </button>
          <span className="thu-cau-luu-y">
            Bản rút gọn 3 câu · đề thi thử thật bấm giờ như thi trên máy
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="thu-cau">
      <div className="thu-cau-dau">
        <span className="thu-cau-nhan">
          Thử {CAU.length} câu — không cần tài khoản · câu {i + 1}/{CAU.length}
        </span>
        <span className="thu-cau-hp">{c.hop_phan}</span>
      </div>

      {/* Ba ô tiến độ: người dùng biết còn bao lâu thì xong, tức ô này hứa một
          việc NGẮN chứ không phải một bài kiểm tra. */}
      <ol className="thu-cau-buoc" aria-label={`Câu ${i + 1} trên ${CAU.length}`}>
        {CAU.map((q, k) => (
          <li
            key={q.ma}
            className={
              'thu-cau-buoc-o'
              + (k === i ? ' dang-lam' : '')
              + (chon[k] !== null ? (chon[k] === q.dung ? ' la-dung' : ' la-sai') : '')
            }
            aria-current={k === i ? 'step' : undefined}
          >
            <span className="sr-only">{q.hop_phan}</span>
          </li>
        ))}
      </ol>

      <p className="thu-cau-de">{c.de}</p>

      <div className="thu-cau-dsach" role="group" aria-label="Các phương án">
        {c.lua_chon.map((v, k) => {
          /* Sau khi chọn: tô ĐÁP ÁN ĐÚNG màu xanh dù người dùng chọn gì, và tô
             lựa chọn SAI của họ màu đỏ. Chỉ tô cái họ chọn thì người chọn sai
             biết mình sai mà không biết đúng là gì — nửa vời, và đúng thứ làm
             người ta bỏ đi. */
          const lop = !xong ? '' : k === c.dung ? ' la-dung' : k === daChon ? ' la-sai' : ' mo-di';
          return (
            <button
              key={v}
              type="button"
              className={'thu-cau-nut' + lop}
              onClick={() => traLoi(k)}
              disabled={xong}
              aria-pressed={daChon === k}
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
        <button type="button" className="thu-cau-tiep" onClick={tiep} disabled={!xong}>
          {i < CAU.length - 1 ? 'Câu tiếp →' : 'Xem kết quả →'}
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
