'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { coAnh } from '@/lib/coAnh';
import { dinhDangTinNhan } from '@/lib/dinhDangTinNhan';
import { nguCanhBaiHoc } from '@/lib/nguCanhBaiHoc';

import { BieuTuong } from './bieuTuong';

/**
 * Trợ lý HSA — toàn bộ ở React (20/09/2026).
 *
 * ── CÁI NÓ THAY THẾ ──────────────────────────────────────────────────────
 *
 * Tới hôm nay logic nằm ở `public/static/js/chatbot.js` (457 dòng, tầng cũ),
 * còn component này chỉ là markup rỗng để tệp ấy gắn sự kiện vào. Ba lý do
 * dời:
 *   · Trợ lý cần STREAM: v4-pro trả mẩu đầu sau ~1 s nhưng trọn câu sau 4–11 s;
 *     đọc `ReadableStream` rồi vẽ dần là việc của state, không phải của
 *     `innerHTML +=` trên một nút tìm bằng `getElementById`.
 *   · Trần tầng cũ (`chot-ham-tang-cu.test.mjs`) đã phải nới hai lần cho đúng
 *     tệp này (nút gửi ảnh, 20/09). Dời được thì hạ — đây là hạ 457 dòng.
 *   · Tàn dư PE_test còn nguyên: nút "Lộ trình" mở `prompt('… React, Python
 *     …', 'Web Development')` trên một nền tảng luyện thi HSA.
 *
 * Ba việc thuần (định dạng chữ, ngữ cảnh bài, co ảnh) ở `src/lib/` để kiểm
 * riêng; component chỉ giữ state và luồng.
 *
 * `data-chi-hoc-vien`: trợ lý là công cụ ÔN THI — prompt coi người dùng là học
 * sinh và bơm hồ sơ học tập; nhân sự không thấy (`lib/nhomVai.ts`).
 */

type TinNhan = { role: 'user' | 'assistant'; content: string; anh?: string };

const LOI_CHAO = 'Chào bạn! 👋 Mình là Trợ lý HSA. Hỏi mình về bài đang học, cách làm một dạng bài, hay chụp đề gửi lên để mình hướng dẫn nhé.';
const LOI_MANG = 'Lỗi kết nối tới trợ lý. Vui lòng thử lại.';

/** Đọc `text/event-stream` của `/api/chat` (`data: {"chunk"|"error"}`), gọi
 *  `nhan` với chữ đã ghép sau mỗi mẩu. Trả chữ cuối. */
async function docLuong(res: Response, nhan: (chu: string) => void): Promise<string> {
  const reader = res.body?.getReader();
  if (!reader) return '';
  const dec = new TextDecoder();
  let bo = '';
  let chu = '';
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    bo += dec.decode(value, { stream: true });
    let i: number;
    while ((i = bo.indexOf('\n\n')) >= 0) {
      const suKien = bo.slice(0, i);
      bo = bo.slice(i + 2);
      const dong = suKien.split('\n').find((l) => l.startsWith('data: '));
      if (!dong) continue;
      let d: { chunk?: string; error?: string };
      try { d = JSON.parse(dong.slice(6)); } catch { continue; }
      if (d.chunk) chu += d.chunk;
      if (d.error) chu += (chu ? '\n\n' : '') + d.error;
      nhan(chu);
    }
  }
  return chu;
}

export default function Chatbot() {
  const [mo, setMo] = useState(false);
  const [tin, setTin] = useState<TinNhan[]>([{ role: 'assistant', content: LOI_CHAO }]);
  const [nhap, setNhap] = useState('');
  const [anh, setAnh] = useState<string | null>(null);
  const [dangGui, setDangGui] = useState(false);
  const oTin = useRef<HTMLDivElement>(null);
  const oNhap = useRef<HTMLInputElement>(null);
  const oTep = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const el = oTin.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [tin, mo]);

  const doiMo = useCallback(() => {
    setMo((v) => {
      if (!v) setTimeout(() => oNhap.current?.focus(), 0);
      return !v;
    });
  }, []);

  const boAnh = useCallback(() => {
    setAnh(null);
    if (oTep.current) oTep.current.value = '';
  }, []);

  const chonAnh = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    coAnh(f).then(setAnh).catch(boAnh);
  }, [boAnh]);

  const guiAsync = useCallback(async (chuHoi: string) => {
    const text = chuHoi.trim();
    if ((!text && !anh) || dangGui) return;
    const anhGui = anh;
    const noiDung = text || 'Đây là ảnh đề bài của mình.';
    // Lịch sử gửi lên chỉ giữ CHỮ: ảnh đi kèm lượt hiện tại (`image`), máy chủ
    // gắn vào lượt cuối và chọn model đọc được ảnh (`chatbot/graph.py`).
    const lichSu = [...tin.filter((t) => t.content !== LOI_CHAO && t.content !== ''), { role: 'user' as const, content: noiDung }]
      .map((t) => ({ role: t.role, content: t.content }));
    /* Câu trả lời là PHẦN TỬ CUỐI của `tin` ngay từ đầu (rỗng = ba chấm), và
       được ghi đè tại chỗ khi từng mẩu tới. Dựng ô "đang gõ" riêng rồi thay
       bằng ô tin nhắn khi xong là hai nút React khác nhau: `.chatbot-message`
       có `animation: chatbot-fade-in`, nên câu vừa hiện trọn lại mờ đi rồi
       hiện lại lần nữa (ảnh chụp 20/09/2026). */
    setTin((ds) => [...ds,
      { role: 'user', content: text || '(Hình ảnh)', anh: anhGui ?? undefined },
      { role: 'assistant', content: '' }]);
    setNhap('');
    boAnh();
    setDangGui(true);
    const ghiCuoi = (chu: string) => setTin((ds) => {
      const cuoi = ds[ds.length - 1];
      if (!cuoi || cuoi.role !== 'assistant') return ds;
      return [...ds.slice(0, -1), { ...cuoi, content: chu }];
    });
    let traLoi = '';
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: lichSu,
          page_context: nguCanhBaiHoc(),
          image: anhGui || undefined,
          stream: true,
        }),
      });
      if (!res.ok) {
        traLoi = 'Trợ lý tạm thời chưa sẵn sàng, bạn thử lại sau nhé.';
        try {
          const e = await res.json();
          traLoi = (typeof e.error === 'string' ? e.error : e.error?.message) || traLoi;
          // 429 = hạn mức theo người (60/giờ) — nói vì sao, kèm bao lâu nữa.
          if (res.status === 429) traLoi = 'Bạn hỏi nhanh quá — trợ lý có hạn mức mỗi giờ để giữ chi phí. ' + (e.error?.detail || 'Thử lại sau ít phút nhé.');
        } catch { /* thân không phải JSON */ }
      } else if ((res.headers.get('content-type') || '').startsWith('text/event-stream')) {
        traLoi = await docLuong(res, ghiCuoi);
      } else {
        const d = await res.json();
        traLoi = d.reply || 'Mình chưa nhận được phản hồi, bạn hỏi lại giúp nhé.';
      }
    } catch {
      traLoi = LOI_MANG;
    }
    ghiCuoi(traLoi || LOI_MANG);
    setDangGui(false);
    oNhap.current?.focus();
  }, [anh, dangGui, tin, boAnh]);
  /* Handler cho thuộc tính JSX phải trả `void`; lỗi mạng đã bắt bên trong. */
  const gui = useCallback((chuHoi: string) => { void guiAsync(chuHoi); }, [guiAsync]);

  return (
    <>
      <button
        type="button"
        id="chatbot-toggle"
        className={'chatbot-floating-btn' + (mo ? ' active' : '')}
        aria-label="Mở trợ lý AI"
        aria-expanded={mo}
        data-chi-hoc-vien=""
        onClick={doiMo}
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" className="chatbot-btn-icon" aria-hidden="true">
          <path d="M12 1L13.8 9.2L22 11L13.8 12.8L12 21L10.2 12.8L2 11L10.2 9.2L12 1Z" />
          <path d="M19.5 2L20.5 6L24 7L20.5 8L19.5 12L18.5 8L15 7L18.5 6L19.5 2Z" opacity="0.75" />
          <path d="M5 15L5.8 17.7L8.5 18.5L5.8 19.3L5 22L4.2 19.3L1.5 18.5L4.2 17.7L5 15Z" opacity="0.65" />
        </svg>
        <div className="chatbot-badge"><span className="chatbot-pulse"></span></div>
      </button>

      <div id="chatbot-window" className={'chatbot-window' + (mo ? '' : ' chatbot-hidden')} data-chi-hoc-vien="" role="dialog" aria-label="Trợ lý HSA" aria-hidden={!mo}>
        <div className="chatbot-header">
          <div className="chatbot-header-left">
            <div className="chatbot-avatar"><BieuTuong ten="bot" co={22} /></div>
            <div className="chatbot-header-text">
              <h3>Trợ lý HSA</h3>
              <span className="chatbot-status"><span className="chatbot-status-dot"></span> Trực tuyến</span>
            </div>
          </div>
          <button type="button" id="chatbot-close" className="chatbot-close-btn" aria-label="Đóng chat" onClick={doiMo}>
            <BieuTuong ten="x" co={18} />
          </button>
        </div>

        <div id="chatbot-messages" className="chatbot-messages" ref={oTin} aria-live="polite">
          {tin.map((t, i) => (t.role === 'assistant' ? (
            <div className="chatbot-message chatbot-message-ai" key={i} id={t.content === '' ? 'chatbot-typing-indicator' : undefined}>
              <div className="chatbot-message-avatar"><BieuTuong ten={i === 0 ? 'sparkles' : 'bot'} co={16} /></div>
              <div className="chatbot-message-content">
                {t.content === '' ? (
                  <div className="chatbot-message-bubble">
                    <div className="chatbot-typing"><div className="chatbot-typing-dot"></div><div className="chatbot-typing-dot"></div><div className="chatbot-typing-dot"></div></div>
                  </div>
                ) : (
                  /* HTML sinh từ `dinhDangTinNhan`: THOÁT trước, markdown sau — xem tệp ấy. */
                  <div className="chatbot-message-bubble" dangerouslySetInnerHTML={{ __html: dinhDangTinNhan(t.content) }} />
                )}
              </div>
            </div>
          ) : (
            <div className="chatbot-message chatbot-message-user" key={i}>
              <div className="chatbot-message-content" style={{ textAlign: 'right' }}>
                {t.anh && (
                  /* eslint-disable-next-line @next/next/no-img-element -- data URL do người dùng vừa co, không qua mạng */
                  <img src={t.anh} alt="Ảnh bạn đã gửi" style={{ borderRadius: 8, marginBottom: 8, maxWidth: '100%', maxHeight: 150 }} />
                )}
                <div className="chatbot-message-bubble">{t.content}</div>
              </div>
              <div className="chatbot-message-avatar"><BieuTuong ten="user" co={16} /></div>
            </div>
          )))}
        </div>

        <div id="chatbot-image-preview" className={'chatbot-image-preview' + (anh ? '' : ' chatbot-hidden')}>
          <div className="chatbot-preview-item">
            {anh && (
              /* eslint-disable-next-line @next/next/no-img-element -- data URL cục bộ */
              <img id="chatbot-preview-img" src={anh} alt="Ảnh sắp gửi" />
            )}
            <button type="button" className="chatbot-preview-remove" onClick={boAnh} aria-label="Xóa hình ảnh">
              <BieuTuong ten="trash-2" co={14} />
            </button>
          </div>
        </div>

        <div className="chatbot-input-area">
          {/* Bốn câu hỏi nhanh — việc của ÔN THI. "Lộ trình" hỏi trợ lý dựa trên
              hồ sơ học tập máy chủ đã bơm (mục tiêu, chủ đề yếu), thay cho hộp
              `prompt('… React, Python …')` còn sót từ nền tảng dạy lập trình. */}
          <div className="chatbot-quick-actions">
            <button type="button" className="chatbot-quick-btn" onClick={() => gui('Giải thích giúp mình phần lý thuyết của bài này, cho ví dụ dễ hiểu.')}>
              <BieuTuong ten="lightbulb" co={13} /><span>Giảng lại</span>
            </button>
            <button type="button" className="chatbot-quick-btn" onClick={() => gui('Bài này hay có bẫy gì trong đề HSA? Mẹo làm nhanh là gì?')}>
              <BieuTuong ten="triangle-alert" co={13} /><span>Bẫy &amp; mẹo</span>
            </button>
            <button type="button" className="chatbot-quick-btn" onClick={() => gui('Cho mình 3 câu luyện thêm dạng này, kèm đáp án và lời giải.')}>
              <BieuTuong ten="square-pen" co={13} /><span>Luyện thêm</span>
            </button>
            <button type="button" className="chatbot-quick-btn" onClick={() => gui('Dựa trên hồ sơ học tập của mình, gợi ý lộ trình ôn 4 tuần tới: mỗi tuần tập trung chủ đề nào, mỗi ngày làm gì.')}>
              <BieuTuong ten="map" co={13} /><span>Lộ trình</span>
            </button>
          </div>

          <div className="chatbot-input-box">
            <label htmlFor="chatbot-image-upload" className="chatbot-attach-btn" title="Đính kèm hình ảnh">
              <BieuTuong ten="paperclip" co={16} />
              <input type="file" id="chatbot-image-upload" className="chatbot-hidden" accept="image/*" title="Chọn hình ảnh" ref={oTep} onChange={chonAnh} />
            </label>
            <input
              id="chatbot-input"
              type="text"
              placeholder="Nhập câu hỏi..."
              className="chatbot-input"
              autoComplete="off"
              ref={oNhap}
              value={nhap}
              onChange={(e) => setNhap(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); gui(nhap); } }}
            />
            <button type="button" id="chatbot-send-btn" className="chatbot-send-btn" aria-label="Gửi" disabled={dangGui} onClick={() => gui(nhap)}>
              <BieuTuong ten="arrow-up" co={16} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
