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

/** Khoá NỘI BỘ của biểu mẫu, KHÔNG bao giờ được ghi xuống CSDL.
 *
 * Nó tồn tại vì một lý do duy nhất: nối một dòng trên màn hình với đúng phần tử
 * gốc của nó, kể cả sau khi người soạn xoá một dòng phía trên. Xem `gopTheoKhoa`.
 */
export type CoKhoa = { _k?: number };

export type CauHoi = CoKhoa & {
  id: string;
  type: 'mcq' | 'fill';
  question: string;
  options?: string[];
  answer: string;
  explain?: string;
};

export type The = CoKhoa & {
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

/** Gộp một danh sách THEO KHOÁ `_k`, không theo vị trí.
 *
 * ── VÌ SAO KHÔNG THEO VỊ TRÍ (vá 04/09/2026) ───────────────────────────────
 *
 * Bản đầu gộp theo vị trí, và chú thích của nó chỉ cảnh báo trường hợp ĐẢO thứ
 * tự. Nhưng thao tác nguy hiểm là XOÁ — thứ có nút riêng ngay trên màn hình.
 * Xoá phần tử thứ i làm mọi phần tử sau đó tụt lên một chỗ, nên chúng gộp vào
 * SAI phần tử gốc và thừa hưởng khoá lạ của người khác.
 *
 * Đo trên toàn bộ 76 bài đang chạy, mô phỏng "xoá đúng một phần tử" ở mọi vị trí:
 *
 *     thẻ lý thuyết:  8 / 456 lượt xoá làm một thẻ KHÁC đổi nội dung
 *     câu hỏi:      227 / 836 lượt xoá làm một câu KHÁC đổi nội dung
 *
 * Ví dụ thật (`hsa_quantitative#7`): xoá thẻ "Đỉnh & trục đối xứng" thì thẻ
 * "Giá trị lớn nhất / nhỏ nhất" — vốn KHÔNG có minh hoạ — mọc ra đồ thị parabol
 * của thẻ vừa bị xoá. `visual` là thứ engine VẼ RA, nên đó là hiển thị sai cho
 * học viên, không phải rác ẩn.
 *
 * ── VÌ SAO KHOÁ RIÊNG, KHÔNG DÙNG `id` ─────────────────────────────────────
 *
 * Biểu mẫu cho sửa `id` của câu hỏi. Khớp theo `id` thì một câu vừa đổi mã trở
 * thành "câu mới" và mất khoá lạ. `_k` do `docRaBieuMau` gán lúc NẠP và không
 * ai sửa được, nên nó bám đúng phần tử qua mọi thao tác — xoá, chèn, đảo.
 * Phần tử mới thêm không có `_k` → gộp vào không cái nào, đúng như mong đợi.
 *
 * `_k` bị BỎ khỏi kết quả: nó là chuyện của màn hình, không phải của giáo trình.
 */
function gopTheoKhoa<T extends CoKhoa>(goc: unknown, moi: T[]): unknown[] {
  const cu = Array.isArray(goc) ? goc : [];
  return moi.map((m) => {
    const { _k, ...sach } = m;
    const nen = typeof _k === 'number' && la(cu[_k]) ? cu[_k] : null;
    return nen ? { ...nen, ...sach } : { ...sach };
  });
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
  ra.test = { ...testGoc, intro: m.testIntro, questions: gopTheoKhoa(testGoc.questions, m.testQuestions) };

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
    th.full = { ...b, title: m.fullTitle, cards: gopTheoKhoa(b.cards, m.fullCards) };
  } else delete th.full;
  if (m.condCards.length) {
    const b = la(thGoc.condensed) ? thGoc.condensed : {};
    th.condensed = { ...b, title: m.condTitle, cards: gopTheoKhoa(b.cards, m.condCards) };
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
    d.questions = gopTheoKhoa(d.questions, m.drillQuestions);
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
  /* Gán `_k` = vị trí LÚC NẠP. Từ đó trở đi nó là danh tính của phần tử, và
     không thao tác nào trên màn hình đổi được nó.
     RIÊNG cho mảng ĐỐI TƯỢNG. Bản đầu tôi dùng chung một hàm cho mọi mảng, và
     nó bọc `_k` vào cả `notes.key_points` — một mảng CHUỖI. Trải một chuỗi ra
     thành object thì `"…".trim` biến mất, và `hopNhat` ném ngay ở lượt đầu.
     Chính bộ kiểm mới thêm bắt được, chứ `tsc` thì không: `ds<string>` khớp
     kiểu hoàn toàn. */
  const dsKhoa = <T,>(v: unknown): (T & CoKhoa)[] =>
    (Array.isArray(v) ? (v as T[]) : []).map((x, i) => ({ ...(x as T), _k: i }));

  return {
    id: ch(c.id),
    index: so(c.index, sortOrder),
    title: ch(c.title),
    subtitle: ch(c.subtitle),
    topic_tag: ch(c.topic_tag),
    xp_reward: so(c.xp_reward, 50),
    testIntro: ch(test.intro),
    testQuestions: dsKhoa<CauHoi>(test.questions),
    strongMin: soChuoi(assess.strong_min),
    okMin: soChuoi(assess.ok_min),
    fullTitle: ch(full.title),
    fullCards: dsKhoa<The>(full.cards),
    condTitle: ch(cond.title),
    condCards: dsKhoa<The>(cond.cards),
    notesTip: ch(notes.tip),
    notesFormula: ch(notes.formula),
    notesKeyPoints: ds<string>(notes.key_points),
    drillIntro: ch(drill.intro),
    // Đọc `time_seconds`. Nếu gặp bản do bộ soạn CŨ ghi (`seconds`) thì vẫn đọc
    // được, để người soạn không phải gõ lại một con số vốn đã có.
    drillSeconds: so(drill.time_seconds, so(drill.seconds, 60)),
    drillQuestions: dsKhoa<CauHoi>(drill.questions),
  };
}
