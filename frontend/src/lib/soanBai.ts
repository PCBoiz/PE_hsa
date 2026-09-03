/**
 * Soạn nội dung một bài học — kiểu dữ liệu và phép GỘP.
 *
 * ── VÌ SAO GỘP, KHÔNG DỰNG LẠI ────────────────────────────────────────────
 *
 * Bộ soạn cũ (`public/static/js/pages/admin.inline.js`) dựng lại đối tượng bài
 * TỪ ĐẦU mỗi lần lưu: nó liệt kê các trường nó biết rồi gói thành một object
 * mới. Hệ quả là mọi trường nó KHÔNG biết đều biến mất.
 *
 * Đo 04/09/2026 trên cả 76 bài đang có, hai trường rơi vào đúng cảnh đó:
 *
 *   · `drill.time_seconds` — bộ soạn đọc/ghi `seconds`, còn `lesson_hsa.js`
 *     đọc `time_seconds` (cả chỗ hiện "N giây" lẫn đồng hồ đếm ngược);
 *   · `notes` — `{tip, formula, key_points[]}`, engine đọc ở
 *     `lesson_hsa.js:418`. Bộ soạn xử lý `note` số ít với hình dạng khác hẳn,
 *     tức người soạn gõ vào một ô không nối với gì.
 *
 * Cái thứ nhất bị bộ kiểm phía máy chủ CHẶN (`lessons/content.py` báo đúng
 * "dùng time_seconds chứ không phải seconds"), nên bộ soạn cũ không xoá dữ
 * liệu — nó chỉ **không dùng được** cho bất kỳ bài nào có phòng luyện, tức cả
 * 76. Nhưng cái thứ hai KHÔNG có hàng rào nào: sửa đúng một cái tên kia thôi là
 * `notes` biến mất lặng lẽ.
 *
 * Đó là lý do bản này gộp thay vì dựng lại. Hàng rào phía máy chủ bắt được
 * trường nào nó BIẾT là quan trọng; gộp thì giữ được cả trường chưa ai kịp
 * dạy cho nó.
 *
 * ── TẠI SAO LÀ MỘT HÀM THUẦN, TÁCH RIÊNG ──────────────────────────────────
 *
 * Không đụng DOM, không đụng React, không gọi mạng — nên kiểm được bằng Node
 * thuần trong `e2e/unit/`, nơi CI chạy từ 01/09. Phép kiểm quan trọng nhất ở đó
 * không phải "trường tôi biết được lưu đúng" mà **"trường tôi KHÔNG biết vẫn
 * còn"**, và một hàm còn dính DOM thì không kiểm được điều đó cho gọn.
 */

/** Nội dung bài như nó nằm trong `lessons.content_json`. Trường lạ được phép. */
export type NoiDungBai = Record<string, unknown>;

export type CauHoi = {
  id: string;
  type: 'mcq' | 'fill';
  question: string;
  options?: string[];
  answer: string;
  explain?: string;
};

export type The = {
  icon?: string;
  title: string;
  body: string;
  /** Minh hoạ: 8 kiểu (bars/numline/curve/flow/table/pie/tree/timeline). */
  visual?: unknown;
};

export type BanLyThuyet = { title: string; cards: The[] };

/** Đúng những gì biểu mẫu trên màn hình cầm. KHÔNG phải toàn bộ một bài. */
export type BieuMau = {
  id: string;
  index: number;
  title: string;
  subtitle: string;
  topic_tag: string;
  xp_reward: number;
  testIntro: string;
  testQuestions: CauHoi[];
  strongMin: string;
  okMin: string;
  fullTitle: string;
  fullCards: The[];
  condTitle: string;
  condCards: The[];
  /** Khối ghi nhớ — ĐÚNG hình dạng engine đọc. */
  notesTip: string;
  notesFormula: string;
  notesKeyPoints: string[];
  drillIntro: string;
  /** Đồng hồ phòng luyện. Tên trường khi ghi ra là `time_seconds`. */
  drillSeconds: number;
  drillQuestions: CauHoi[];
};

/** Trường cấp cao nhất mà biểu mẫu này quản. Mọi trường khác được GIỮ NGUYÊN. */
export const TRUONG_BIEU_MAU = [
  'id', 'index', 'title', 'subtitle', 'topic_tag', 'xp_reward',
  'test', 'assess', 'theory', 'notes', 'drill',
] as const;

function la(o: unknown): o is Record<string, unknown> {
  return typeof o === 'object' && o !== null && !Array.isArray(o);
}

/** Gộp mảng câu hỏi THEO VỊ TRÍ, giữ mọi khoá lạ của từng câu.
 *
 * Theo vị trí chứ không theo `id`: biểu mẫu cho sửa `id`, nên khớp theo id sẽ
 * làm một câu vừa đổi mã trở thành "câu mới" và mất khoá lạ của nó. Đánh đổi:
 * ĐẢO thứ tự câu thì khoá lạ đi theo vị trí chứ không theo câu. Chấp nhận được
 * vì hôm nay chưa câu nào có khoá lạ (đo 04/09 trên 76 bài), và cách này không
 * bao giờ mất dữ liệu khi chỉ SỬA — thao tác chiếm gần hết số lần dùng. */
function gopCauHoi(goc: unknown, moi: CauHoi[]): unknown[] {
  const cu = Array.isArray(goc) ? goc : [];
  return moi.map((c, i) => (la(cu[i]) ? { ...cu[i], ...c } : { ...c }));
}

function gopThe(goc: unknown, moi: The[]): unknown[] {
  const cu = Array.isArray(goc) ? goc : [];
  return moi.map((t, i) => (la(cu[i]) ? { ...cu[i], ...t } : { ...t }));
}

/**
 * Gộp biểu mẫu vào bản gốc. Trả một object MỚI, không sửa `goc`.
 *
 * Luật xoá: một khối chỉ biến mất khi người soạn làm nó RỖNG HẲN (không câu
 * hỏi, không chữ). Rỗng một phần thì giữ khối lại — người soạn xoá tạm một câu
 * để gõ lại không phải là người soạn muốn bỏ cả phòng luyện.
 */
export function hopNhat(goc: NoiDungBai | null | undefined, m: BieuMau): NoiDungBai {
  const ra: NoiDungBai = la(goc) ? { ...goc } : {};

  ra.id = m.id;
  ra.index = m.index;
  ra.title = m.title;
  ra.topic_tag = m.topic_tag;
  ra.xp_reward = m.xp_reward;
  if (m.subtitle) ra.subtitle = m.subtitle;
  else delete ra.subtitle;

  // ── test: bắt buộc, luôn có ────────────────────────────────────────────
  const testGoc = la(ra.test) ? ra.test : {};
  ra.test = { ...testGoc, intro: m.testIntro, questions: gopCauHoi(testGoc.questions, m.testQuestions) };

  // ── assess: chỉ giữ khi có ít nhất một ngưỡng ──────────────────────────
  const sm = m.strongMin.trim() === '' ? null : Number(m.strongMin);
  const om = m.okMin.trim() === '' ? null : Number(m.okMin);
  if (sm === null && om === null) {
    delete ra.assess;
  } else {
    const a = la(ra.assess) ? { ...ra.assess } : {};
    if (sm === null) delete a.strong_min; else a.strong_min = sm;
    if (om === null) delete a.ok_min; else a.ok_min = om;
    ra.assess = a;
  }

  // ── theory: cần ít nhất một bản ────────────────────────────────────────
  const thGoc = la(ra.theory) ? ra.theory : {};
  const th: Record<string, unknown> = { ...thGoc };
  if (m.fullCards.length) {
    const b = la(thGoc.full) ? thGoc.full : {};
    th.full = { ...b, title: m.fullTitle, cards: gopThe(b.cards, m.fullCards) };
  } else delete th.full;
  if (m.condCards.length) {
    const b = la(thGoc.condensed) ? thGoc.condensed : {};
    th.condensed = { ...b, title: m.condTitle, cards: gopThe(b.cards, m.condCards) };
  } else delete th.condensed;
  ra.theory = th;

  // ── notes: ĐÚNG tên và hình dạng engine đọc ────────────────────────────
  const diem = m.notesKeyPoints.map((s) => s.trim()).filter(Boolean);
  if (!m.notesTip.trim() && !m.notesFormula.trim() && !diem.length) {
    delete ra.notes;
  } else {
    const n = la(ra.notes) ? { ...ra.notes } : {};
    if (m.notesTip.trim()) n.tip = m.notesTip.trim(); else delete n.tip;
    if (m.notesFormula.trim()) n.formula = m.notesFormula.trim(); else delete n.formula;
    if (diem.length) n.key_points = diem; else delete n.key_points;
    ra.notes = n;
  }

  // ── drill: `time_seconds`, KHÔNG phải `seconds` ────────────────────────
  if (!m.drillQuestions.length && !m.drillIntro.trim()) {
    delete ra.drill;
  } else {
    const d = la(ra.drill) ? { ...ra.drill } : {};
    d.intro = m.drillIntro;
    d.time_seconds = m.drillSeconds;
    // Dọn dấu vết của bộ soạn cũ nếu có: để lại `seconds` thì bộ kiểm phía máy
    // chủ từ chối cả bài (`lessons/content.py`), và câu lỗi sẽ nói về một
    // trường mà màn hình này không hề hiện ra.
    delete d.seconds;
    d.questions = gopCauHoi(d.questions, m.drillQuestions);
    ra.drill = d;
  }

  return ra;
}

/** Trường cấp cao nhất có trong bài mà biểu mẫu KHÔNG hiện ra.
 *
 * Dùng để nói thẳng với người soạn "bài này còn N trường khác, chúng được giữ
 * nguyên" — im lặng giữ cũng là một cách làm người ta bất ngờ về sau. */
export function truongLa(goc: NoiDungBai | null | undefined): string[] {
  if (!la(goc)) return [];
  const biet = new Set<string>(TRUONG_BIEU_MAU);
  return Object.keys(goc).filter((k) => !biet.has(k)).sort();
}

/** Đọc bản ghi trong CSDL ra biểu mẫu. Ngược chiều với `hopNhat`. */
export function docRaBieuMau(goc: NoiDungBai | null | undefined, sortOrder: number): BieuMau {
  const c = la(goc) ? goc : {};
  const test = la(c.test) ? c.test : {};
  const assess = la(c.assess) ? c.assess : {};
  const theory = la(c.theory) ? c.theory : {};
  const full = la(theory.full) ? theory.full : {};
  const cond = la(theory.condensed) ? theory.condensed : {};
  const notes = la(c.notes) ? c.notes : {};
  const drill = la(c.drill) ? c.drill : {};
  const so = (v: unknown, mac: number) => (typeof v === 'number' ? v : mac);
  const ch = (v: unknown) => (typeof v === 'string' ? v : '');
  /* KHÔNG `String(v)`: `content_json` là dữ liệu ngoài, `assess.strong_min` có
     thể là bất cứ thứ gì. `String({})` ra `"[object Object]"` — 15 ký tự,
     truthy, đi lọt mọi phép kiểm "có nhập chưa" rồi hiện lên ô nhập như một
     giá trị thật. Đúng lớp lỗi T22, thứ đã hiện lên banner đỏ trước mặt trợ
     giảng; `no-base-to-string` bắt được nó ngay lúc viết dòng này. */
  const soChuoi = (v: unknown) =>
    typeof v === 'number' || typeof v === 'string' ? String(v) : '';
  const ds = <T,>(v: unknown): T[] => (Array.isArray(v) ? (v as T[]) : []);

  return {
    id: ch(c.id),
    index: so(c.index, sortOrder),
    title: ch(c.title),
    subtitle: ch(c.subtitle),
    topic_tag: ch(c.topic_tag),
    xp_reward: so(c.xp_reward, 50),
    testIntro: ch(test.intro),
    testQuestions: ds<CauHoi>(test.questions),
    strongMin: soChuoi(assess.strong_min),
    okMin: soChuoi(assess.ok_min),
    fullTitle: ch(full.title),
    fullCards: ds<The>(full.cards),
    condTitle: ch(cond.title),
    condCards: ds<The>(cond.cards),
    notesTip: ch(notes.tip),
    notesFormula: ch(notes.formula),
    notesKeyPoints: ds<string>(notes.key_points),
    drillIntro: ch(drill.intro),
    // Đọc `time_seconds`. Nếu gặp bản do bộ soạn CŨ ghi (`seconds`) thì vẫn đọc
    // được, để người soạn không phải gõ lại một con số vốn đã có.
    drillSeconds: so(drill.time_seconds, so(drill.seconds, 60)),
    drillQuestions: ds<CauHoi>(drill.questions),
  };
}
