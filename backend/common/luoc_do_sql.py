"""Lược đồ SQL thô: chia `sql/*.sql` thành MỤC và ghi SỔ mục đã chạy (H3, 24/09/2026).

`bootstrap_schema` là vỏ dòng lệnh; mọi luật nằm ở đây để phép kiểm gọi thẳng được.

── VÌ SAO CÓ SỔ ─────────────────────────────────────────────────────────────

Tới 24/09/2026 `bootstrap_schema` chạy lại TOÀN BỘ `legacy_schema.sql` ở mỗi deploy.
"Idempotent" chỉ đúng trọn với `CREATE … IF NOT EXISTS`; tệp còn những cặp DROP + ADD
(khoá chính §36, CHECK vai trò §35/§44, …) và UPDATE điền ngược (§51) — mỗi deploy DỠ
rồi DỰNG lại chúng trên bảng đang phục vụ, kiểm lại mọi dòng. Hai lần điều ấy đã chặn
hoặc suýt chặn deploy:
  · 18/09: một bản CHECK cũ nằm trên bản mới → lượt chạy lại áp luật CŨ lên dữ liệu MỚI
    (`common/tests.py::test_rang_buoc_them_nhieu_lan_phai_GIONG_HET_nhau`);
  · 24/09: §36 bỏ khoá chính mỗi lượt, mà khoá ngoại §55 phụ thuộc nó → lần bootstrap
    THỨ HAI hỏng (vá bằng CASCADE).
Sổ `luoc_do_da_chay` nhớ mục nào đã chạy với nội dung nào (checksum), nên mỗi deploy chỉ
chạy phần mới. CSDL chưa có sổ (production lúc H3 lên, nhánh Neon cũ) → lượt đầu chạy
mọi mục MỘT lần như trước rồi ghi sổ; an toàn vì mọi mục đã chạy lại mỗi deploy từ trước.

── MỤC LÀ GÌ ────────────────────────────────────────────────────────────────

Tệp chia theo DÒNG TIÊU ĐỀ đánh số. `legacy_schema.sql` viết qua nhiều đợt nên có ba kiểu:

    -- 12. lesson_progress --------------        §1–§22: số + gạch nối cuối dòng
    -- ==================================        §23–§38, §49–§51: số đứng NGAY SAU
    -- 23. Nhiệm vụ hằng ngày …                    một vạch `====`
    -- §39 · Thu hồi phiên …                    §39 trở đi: dấu § + chấm giữa `·`
    -- ── §52 · QUÊN MẬT KHẨU QUA EMAIL ──

MỤC MỚI viết kiểu cuối: `-- ── §NN · TIÊU ĐỀ (ngày) ──`. Phần trước tiêu đề đầu tiên là
mục `nền`; tệp không có tiêu đề nào (`mockexam_schema.sql`) là MỘT mục `nền`.
Khoá sổ = `<tên tệp> <mã>`, ví dụ `legacy_schema.sql §36`. Hai tiêu đề cùng mã (hai nhánh
cùng lấy một số) → DỪNG, không đoán: đổi số một bên.

── CHECKSUM ĐỌC CÂU LỆNH, KHÔNG ĐỌC CHÚ THÍCH ───────────────────────────────

Băm các câu SAU KHI bỏ chú thích `--`, dòng trống và khoảng trắng cuối dòng: sửa lời giải
thích (việc làm hằng ngày ở tệp này) không làm mục chạy lại; CRLF hay LF cũng không.

── SỬA MỘT MỤC CŨ → CHẠY LẠI NÓ VÀ MỌI MỤC ĐỨNG SAU ────────────────────────

Không chỉ riêng mục đổi. Các mục phụ thuộc nhau theo THỨ TỰ TỆP: §36 `DROP CONSTRAINT
class_members_pkey CASCADE` kéo mất khoá ngoại của §55, và chỉ §55 — chạy SAU — gắn lại.
Chạy riêng §36 là mất khoá ngoại ấy trong im lặng (phép kiểm
`tests_luoc_do_csdl::test_sua_muc_cu_chay_lai_ca_muc_sau` tái hiện đúng cảnh này). Chạy
từ mục đổi tới hết là lặp lại đúng trình tự đã chạy an toàn mỗi deploy trước H3. Mục mới
thêm ở CUỐI tệp (trường hợp thường gặp) thì chỉ mình nó chạy.

── MỖI MỤC MỘT GIAO DỊCH ────────────────────────────────────────────────────

Câu hỏng → cuộn lại CẢ mục (kể cả câu DROP đứng trước nó: hết cảnh DROP đã commit mà ADD
hỏng, CSDL mất ràng buộc), không ghi sổ, dừng lệnh — trên Render là build đỏ, bản cũ vẫn
phục vụ. Mục ĐẦU TIÊN của lượt còn xoá dòng sổ của mọi mục sau nó trong cùng giao dịch:
lượt đứt giữa chừng thì lượt sau chạy lại đúng phần chưa xong, không bỏ sót mục nào đứng
sau một mục đã chạy lại.

Postgres làm được DDL trong giao dịch; hai thứ KHÔNG làm được là `CREATE INDEX
CONCURRENTLY` và `ALTER TYPE … ADD VALUE` (bản cũ) — tệp chưa dùng, và đừng dùng.

Cái giá của giao dịch theo mục: khoá của MỌI câu trong mục giữ tới cuối mục (autocommit
nhả sau từng câu). Lượt chạy đầu trên nhánh dev (24/09) bế tắc thật ở §43 với một phiên
khác. Nên mỗi mục đặt `lock_timeout` ngắn (`CHO_KHOA`) và THỬ LẠI khi bế tắc / hết giờ
chờ khoá (`CHO_THU_LAI`) — an toàn vì mục cuộn lại trọn và mọi câu chạy lại được. Sau lượt
đầu, deploy thường chỉ chạy mục mới (vài câu), nên cửa sổ giữ khoá nhỏ hẳn so với trước.

── SỔ GHI Ý ĐỊNH, `kiem_luoc_do` HỎI SỰ THẬT ────────────────────────────────

Sổ nói "câu lệnh đã được PHÁT với nội dung này", không nói "kết quả CÒN ở đó". Một ALTER
tay đảo ngược nó thì sổ không biết. `manage.py kiem_luoc_do` vẫn là phép kiểm sự thật
(hỏi thẳng `pg_catalog`); hai bên lệch nhau → `bootstrap_schema --tat-ca`.
"""
import hashlib
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

#: Tên bảng sổ. Không tiền tố schema: nằm cùng schema với lược đồ nó ghi (xem `dien_tap`).
SO = 'luoc_do_da_chay'

_VACH = re.compile(r'^--\s*={10,}\s*$')
_TIEU_DE_PARA = re.compile(r'^--\s+(?:─+\s+)?§(\d+)\s*·\s*(.*)$')
_TIEU_DE_SO = re.compile(r'^--\s+(\d+)\.\s+(\S.*)$')
#: Dòng TRÔNG như tiêu đề mục mà sai mẫu — `-- ── §57 Tên`, `-- §57 — Tên`, `-- §57: Tên` —
#: thứ bộ chia sẽ lặng lẽ gộp vào mục trước. Câu văn mở đầu bằng § ("-- §31 đã nhận ra…")
#: không phải tiêu đề: sau số là chữ, không phải dấu ngắt.
_GIONG_TIEU_DE = re.compile(r'^--\s+(?:[─=]+\s+§\d+|§\d+[a-z]?\s*[—–:.\-])')
_DUOI = re.compile(r'[\s─=\-]+$')


class LoiLuocDo(Exception):
    """Tệp lược đồ không chia được, hoặc một mục chạy hỏng."""


def _split_statements(raw):
    """Tách câu theo `;` SAU KHI bỏ chú thích dòng.

    Bỏ '--' tới hết dòng TRƯỚC — chú thích có thể chứa ';' (không câu/chuỗi DDL nào
    chứa '--' hay ';'). Hệ quả: khối `DO $$ … $$` bị xé ở mọi ';' bên trong — đừng dùng
    (RULES §5). Tên hàm giữ nguyên vì `common/tests.py` và bộ kiểm khác nhập nó."""
    stripped = []
    for line in raw.splitlines():
        idx = line.find('--')
        if idx != -1:
            line = line[:idx]
        stripped.append(line)
    cleaned = '\n'.join(stripped)
    return [s.strip() for s in cleaned.split(';') if s.strip()]


def _bam(cau):
    chuan = '\n;\n'.join(
        '\n'.join(d.rstrip() for d in c.splitlines() if d.strip()) for c in cau)
    return hashlib.sha256(chuan.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class Muc:
    tep: str           # 'legacy_schema.sql'
    ma: str            # '§36' | 'nền'
    tieu_de: str
    dong: int          # dòng tiêu đề (đếm từ 1)
    cau: tuple         # các câu lệnh, đúng thứ tự
    checksum: str

    @property
    def khoa(self):
        return '%s %s' % (self.tep, self.ma)


def _tieu_de(dong, truoc, sau):
    """(mã, tiêu đề) nếu `dong` là dòng tiêu đề mục. Kiểu `-- 23. …` phải KẸP giữa hai vạch
    `====` (một dòng "-- 1. …" ngay dưới vạch đóng là lời giải thích đánh số, không phải mục)."""
    m = _TIEU_DE_PARA.match(dong)
    if m:
        return '§' + m.group(1), m.group(2)
    m = _TIEU_DE_SO.match(dong)
    if m and ((_VACH.match(truoc) and _VACH.match(sau)) or re.search(r'-{3,}\s*$', dong)):
        return '§' + m.group(1), m.group(2)
    return None


def chia_muc(tep, raw):
    """Chia nội dung MỘT tệp .sql thành danh sách `Muc` theo thứ tự tệp.

    Ném `LoiLuocDo` khi: hai tiêu đề cùng mã; một dòng trông như tiêu đề mà sai mẫu; hoặc
    ghép câu của các mục KHÔNG ra đúng câu của cả tệp (tiêu đề nằm giữa một câu, hay câu
    cuối mục thiếu `;` — khi ấy chạy theo mục và chạy cả tệp sẽ phát ra hai thứ khác nhau)."""
    khuc = [['nền', '(phần đầu tệp)', 1, []]]
    dong_tep = raw.splitlines()
    truoc = ''
    for so, dong in enumerate(dong_tep, 1):
        td = _tieu_de(dong, truoc, dong_tep[so] if so < len(dong_tep) else '')
        if td:
            khuc.append([td[0], _DUOI.sub('', td[1]), so, []])
        elif _GIONG_TIEU_DE.match(dong):
            raise LoiLuocDo('%s dòng %d trông như tiêu đề mục nhưng sai mẫu '
                            '(viết `-- ── §NN · Tiêu đề`): %s' % (tep, so, dong.strip()[:80]))
        khuc[-1][3].append(dong)
        truoc = dong

    ra, da_thay = [], {}
    for ma, td, so, dong in khuc:
        cau = tuple(_split_statements('\n'.join(dong)))
        if ma == 'nền' and not cau:
            continue
        if ma in da_thay:
            raise LoiLuocDo('%s: hai tiêu đề cùng mã %s (dòng %d và %d) — đổi số một bên'
                            % (tep, ma, da_thay[ma], so))
        da_thay[ma] = so
        ra.append(Muc(tep, ma, td, so, cau, _bam(cau)))

    ghep = [c for m in ra for c in m.cau]
    ca_tep = _split_statements(raw)
    if ghep != ca_tep:
        lech = 0
        while lech < min(len(ghep), len(ca_tep)) and ghep[lech] == ca_tep[lech]:
            lech += 1
        noi, dem = '?', 0
        for m in ra:
            dem += len(m.cau)
            if lech < dem:
                noi = m.khoa
                break
        raise LoiLuocDo('%s: chia theo mục ra câu khác chia cả tệp (câu #%d, quanh %s) — '
                        'tiêu đề nằm giữa một câu, hoặc câu cuối mục thiếu `;`'
                        % (tep, lech + 1, noi))
    return ra


def thu_muc_sql():
    from django.conf import settings
    return Path(settings.BASE_DIR) / 'sql'


def doc_tat_ca(thu_muc=None):
    """Mọi mục của mọi tệp `sql/*.sql`, theo `sorted()` tên tệp (legacy trước mockexam —
    thứ tự ấy là luật: `mockexam_schema.sql` tham chiếu `users`)."""
    thu_muc = Path(thu_muc) if thu_muc else thu_muc_sql()
    tep = sorted(thu_muc.glob('*.sql'))
    if not tep:
        raise LoiLuocDo('Không thấy tệp .sql nào trong %s' % thu_muc)
    ra = []
    for p in tep:
        ra.extend(chia_muc(p.name, p.read_text(encoding='utf-8')))
    return ra


@dataclass(frozen=True)
class Viec:
    muc: Muc
    ly_do: str


def tim_muc(cac_muc, ma):
    """Khoá sổ của mục mà người gõ `ma` muốn: nhận khoá đủ (`legacy_schema.sql §57`) hoặc chỉ
    mã (`§57`) khi mã ấy chỉ có ở MỘT tệp."""
    khop = [m.khoa for m in cac_muc if m.khoa == ma] or [m.khoa for m in cac_muc if m.ma == ma]
    if not khop:
        raise LoiLuocDo('không có mục %s trong sql/*.sql' % ma)
    if len(khop) > 1:
        raise LoiLuocDo('mã %s có ở hai tệp trở lên (%s) — gõ khoá đủ' % (ma, ', '.join(khop)))
    return khop[0]


def lap_ke_hoach(cac_muc, so, tat_ca=False, tu=None):
    """Mục phải chạy ở lượt này — luôn là một ĐUÔI của `cac_muc` (xem đầu tệp).

    `so`: {khoá: checksum} đọc từ sổ; `None` hay {} = CSDL chưa có sổ → chạy hết.
    `tu`: khoá một mục (`tim_muc`) — coi như nó đổi: chạy nó và mọi mục sau (`--tu`)."""
    so = so or {}

    def vi_sao(m):
        if tat_ca:
            return 'chạy lại hết (--tat-ca)'
        if tu is not None and m.khoa == tu:
            return 'chạy lại theo yêu cầu (--tu)'
        if m.khoa not in so:
            return 'mới'
        if so[m.khoa] != m.checksum:
            return 'đổi nội dung'
        return None

    for i, m in enumerate(cac_muc):
        dau = vi_sao(m)
        if dau is None:
            continue
        ra = [Viec(m, dau)]
        for sau in cac_muc[i + 1:]:
            ra.append(Viec(sau, vi_sao(sau) or 'đứng sau %s' % m.khoa))
        return ra
    return []


def mo_coi(cac_muc, so):
    """Khoá có trong sổ mà không còn trong tệp (mục đổi số / bị gỡ) — vô hại, chỉ để báo."""
    co = {m.khoa for m in cac_muc}
    return sorted(k for k in (so or {}) if k not in co)


# ── Phần chạm CSDL ─────────────────────────────────────────────────────────────

def tao_so(cur):
    cur.execute('CREATE TABLE IF NOT EXISTS %s (muc TEXT PRIMARY KEY, '
                'checksum TEXT NOT NULL, chay_luc TIMESTAMP NOT NULL)' % SO)


def _so_cua_schema(cur):
    """Tên đầy đủ `schema.luoc_do_da_chay` của schema HIỆN HÀNH nếu bảng sổ có ở đó, không thì
    None. Không tra theo `search_path`: trong schema tạm (có `public` phía sau) một sổ chưa
    dựng sẽ "tìm thấy" sổ của `public` — đo được 24/09: `--kiem` trong schema tạm đọc ra
    43 mục của nhánh dev."""
    cur.execute("SELECT format('%%I.%%I', current_schema(), %s::text)", [SO])
    ten = cur.fetchone()[0]
    cur.execute('SELECT to_regclass(%s)', [ten])
    return ten if cur.fetchone()[0] is not None else None


def doc_so(cur):
    """{khoá: checksum}; `None` khi schema hiện hành CHƯA có bảng sổ (không tạo — `--kiem`
    phải chỉ đọc)."""
    ten = _so_cua_schema(cur)
    if ten is None:
        return None
    cur.execute('SELECT muc, checksum FROM %s' % ten)
    return dict(cur.fetchall())


def dem_bang(cur):
    cur.execute("SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema = current_schema() AND table_type = 'BASE TABLE'")
    return cur.fetchone()[0]


#: Chờ tối đa để GIÀNH một khoá, mỗi câu (SET LOCAL — chết cùng giao dịch, an toàn với
#: pgbouncer). Một ALTER đứng chờ khoá sau một truy vấn dài sẽ chặn MỌI truy vấn mới vào
#: bảng ấy — đó là cách một lệnh DDL vô hại làm đứng cả production; 5 s rồi bỏ cuộc và
#: thử lại rẻ hơn nhiều (cùng cách strong_migrations, GitLab đặt `lock_timeout`).
CHO_KHOA = '5s'
#: Giây chờ trước mỗi lần thử lại một mục vướng khoá / bế tắc. Mục là một giao dịch và
#: mọi câu chạy lại được, nên thử lại là an toàn.
CHO_THU_LAI = (1, 2, 4, 8)
#: SQLSTATE đáng thử lại: 40P01 bế tắc, 55P03 hết `lock_timeout`.
_THU_LAI_DUOC = {'40P01', '55P03'}


def _sqlstate(exc):
    while exc is not None:
        ma = getattr(exc, 'sqlstate', None)
        if ma:
            return ma
        exc = exc.__cause__
    return None


def _thuc_thi(cur, cau):
    """Một câu lệnh của mục. Tách riêng để phép kiểm giả được lỗi khoá."""
    cur.execute(cau)


def _chay_muc(m, j, viec, local_now):
    """Một lần thử cho một mục: MỘT giao dịch gồm (xoá sổ các mục sau) + câu + ghi sổ."""
    from django.db import connection, transaction

    with transaction.atomic(), connection.cursor() as cur:
        cur.execute("SELECT set_config('lock_timeout', %s, true)", [CHO_KHOA])
        if j == 0 and len(viec) > 1:
            cur.execute('DELETE FROM %s WHERE muc = ANY(%%s)' % SO,
                        [[x.muc.khoa for x in viec[1:]]])
        for i, cau in enumerate(m.cau, 1):
            try:
                _thuc_thi(cur, cau)
            except Exception as exc:
                exc.vi_tri = (i, cau)
                raise
        cur.execute('INSERT INTO %s (muc, checksum, chay_luc) VALUES (%%s, %%s, %%s) '
                    'ON CONFLICT (muc) DO UPDATE SET checksum = EXCLUDED.checksum, '
                    'chay_luc = EXCLUDED.chay_luc' % SO,
                    [m.khoa, m.checksum, local_now()])


def chay_ke_hoach(viec, ghi=lambda s: None):
    """Chạy từng mục của `viec` trong giao dịch riêng, ghi sổ cùng giao dịch ấy. Vướng khoá
    hay bế tắc với truy vấn đang chạy (đo 24/09 trên nhánh dev: §43 giữ ShareLock của một
    `CREATE INDEX IF NOT EXISTS` không làm gì, chờ AccessExclusive trên `courses`, một phiên
    khác chờ ngược lại → Postgres huỷ mục) thì cuộn lại cả mục và thử lại."""
    import time

    from common.clock import local_now

    for j, v in enumerate(viec):
        m = v.muc
        for lan in range(len(CHO_THU_LAI) + 1):
            try:
                _chay_muc(m, j, viec, local_now)
                break
            except Exception as exc:
                i, cau = getattr(exc, 'vi_tri', (0, ''))
                if _sqlstate(exc) in _THU_LAI_DUOC and lan < len(CHO_THU_LAI):
                    ghi('  ↻ %s vướng khoá (%s) ở câu %d — cuộn lại, thử lại sau %s s'
                        % (m.khoa, _sqlstate(exc), i, CHO_THU_LAI[lan]))
                    time.sleep(CHO_THU_LAI[lan])
                    continue
                dau = ' '.join(cau.split())[:90]
                raise LoiLuocDo(
                    '[%s · câu %d/%d, dòng tiêu đề %d] LỖI ở: %s\n  -> %s\n'
                    'Đã cuộn lại cả mục này, không ghi sổ. %d mục trước nó đã chạy và ghi sổ.'
                    % (m.khoa, i, len(m.cau), m.dong, dau, exc, j)) from exc
        ghi('  · %-26s %3d câu — %s' % (m.khoa, len(m.cau), v.ly_do))


def luot(tat_ca=False, cac_muc=None, ghi=lambda s: None):
    """Một lượt `bootstrap_schema`: tạo sổ nếu thiếu, lập kế hoạch, chạy. Trả danh sách việc."""
    from django.db import connection

    cac_muc = doc_tat_ca() if cac_muc is None else cac_muc
    with connection.cursor() as cur:
        tao_so(cur)
        so = doc_so(cur)
    viec = lap_ke_hoach(cac_muc, so, tat_ca=tat_ca)
    chay_ke_hoach(viec, ghi=ghi)
    return viec


_KHOA_CUA_TOI = """
    SELECT n.nspname, c.relname, l.mode
      FROM pg_locks l
      JOIN pg_class c ON c.oid = l.relation
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE l.pid = pg_backend_pid() AND l.locktype = 'relation'
       AND n.nspname NOT IN (%s, 'pg_catalog', 'information_schema')
       AND n.nspname NOT LIKE 'pg\\_toast%%'
"""


class schema_tam:
    """Ngữ cảnh: tạo một schema Postgres MỚI, đặt nó đứng đầu `search_path`, và CUỘN LẠI hết
    khi ra khỏi khối (kể cả khi khối chạy êm).

    `set_config(…, true)` = `SET LOCAL`: sống đúng tới hết giao dịch, nên không rò sang kết
    nối khác qua pgbouncer — khác hẳn `SET` trần mà RULES §5 cấm. `public` vẫn nằm SAU trong
    đường tìm vì `gin_trgm_ops` của pg_trgm ở đó; cái giá là một câu trỏ nhầm bảng ngoài lược
    đồ sẽ âm thầm tìm thấy bảng thật — `khoa_ngoai()` bắt đúng chuyện ấy qua `pg_locks`."""

    def __init__(self, co_public=True):
        self.ten = 'pe_dien_tap_' + uuid.uuid4().hex[:12]
        self.co_public = co_public
        self._atomic = None
        self._truoc = set()

    def __enter__(self):
        from django.db import connection, transaction
        self._atomic = transaction.atomic()
        self._atomic.__enter__()
        with connection.cursor() as cur:
            cur.execute(_KHOA_CUA_TOI, [self.ten])
            self._truoc = set(cur.fetchall())
            cur.execute('CREATE SCHEMA %s' % self.ten)       # tên tự sinh: chữ thường + hex
            cur.execute("SELECT set_config('search_path', %s, true)",
                        [self.ten + (', public' if self.co_public else '')])
        return self

    def khoa_ngoai(self):
        """Khoá bảng mà giao dịch này giữ NGOÀI schema tạm (trừ khoá đã có trước khối)."""
        from django.db import connection
        with connection.cursor() as cur:
            cur.execute(_KHOA_CUA_TOI, [self.ten])
            return sorted(set(cur.fetchall()) - self._truoc)

    def __exit__(self, kieu, loi, vet):
        from django.db import transaction
        # Khối chạy êm cũng cuộn lại: đánh dấu rồi để atomic tự ROLLBACK (không COMMIT).
        transaction.set_rollback(True)
        self._atomic.__exit__(kieu, loi, vet)
        return False


_DOI_TUONG = """
    SELECT 'ràng buộc ' || conrelid::regclass::text || '.' || conname, oid FROM pg_constraint
     WHERE connamespace = current_schema()::regnamespace
    UNION ALL
    SELECT 'chỉ mục ' || relname, oid FROM pg_class
     WHERE relnamespace = current_schema()::regnamespace AND relkind = 'i'
"""


def _anh(cur):
    """{ràng buộc/chỉ mục: oid} trong schema hiện hành, và {mục sổ: lúc chạy}. OID đổi giữa
    hai lượt = đối tượng bị DỠ rồi DỰNG lại — đúng thứ lượt thứ hai không được làm."""
    cur.execute(_DOI_TUONG)
    doi_tuong = dict(cur.fetchall())
    ten = _so_cua_schema(cur)
    so = {}
    if ten is not None:
        cur.execute('SELECT muc, chay_luc FROM %s' % ten)
        so = dict(cur.fetchall())
    return doi_tuong, so


def dien_tap():
    """Diễn tập CSDL MỚI TOANH qua ĐÚNG lệnh Render chạy: dựng mọi mục vào một schema trống
    bằng `call_command('bootstrap_schema')`, chạy lệnh ấy lần HAI, đối chiếu `kiem_luoc_do`,
    rồi cuộn lại. Trả dict số đo + `loi` (rỗng = đạt); không để lại gì trên CSDL.

    Đây là đường Render đi khi dựng một CSDL mới (staging, khôi phục sau sự cố, nhánh Neon
    trống) — đường mà CSDL đang chạy không bao giờ thử, vì ở đó mọi bảng đã có sẵn. Và lượt
    thứ hai là đường MỌI deploy sau đó đi (§55 hỏng đúng ở lượt thứ hai, 24/09)."""
    from io import StringIO

    from django.core.management import call_command
    from django.db import connection

    from common.management.commands.kiem_luoc_do import MUC

    cac_muc = doc_tat_ca()
    ket = {'so_muc': len(cac_muc), 'kiem_tong': len(MUC)}
    with schema_tam() as st:
        ket['schema'] = st.ten
        call_command('bootstrap_schema', stdout=StringIO())
        with connection.cursor() as cur:
            anh1, so1 = _anh(cur)
            ket['so_bang'] = dem_bang(cur)
        call_command('bootstrap_schema', stdout=StringIO())
        with connection.cursor() as cur:
            anh2, so2 = _anh(cur)
        ket['so_dong_so'] = len(so1)
        ket['doi_luot2'] = sorted(k for k in anh1.keys() | anh2.keys()
                                  if anh1.get(k) != anh2.get(k))
        ket['chay_lai_luot2'] = sorted(k for k in so2 if so1.get(k) != so2[k])
        thieu = []
        for ma, mo_ta, kiem in MUC:
            try:
                ok, vi_sao = kiem()
            except Exception as e:      # noqa: BLE001 — giao dịch đã hỏng: dừng đối chiếu
                thieu.append('%s %s — không kiểm được: %s' % (ma, mo_ta, e))
                break
            if not ok:
                thieu.append('%s %s — %s' % (ma, mo_ta, vi_sao))
        ket['kiem_thieu'] = thieu
        ket['khoa_ngoai'] = st.khoa_ngoai()

    loi = []
    if ket['so_dong_so'] != ket['so_muc']:
        loi.append('lượt 1: sổ ghi %d/%d mục' % (ket['so_dong_so'], ket['so_muc']))
    loi += ['lượt 2 chạy lại %s' % k for k in ket['chay_lai_luot2']]
    loi += ['lượt 2 dỡ-dựng lại %s' % k for k in ket['doi_luot2']]
    loi += ['kiem_luoc_do: ' + t for t in ket['kiem_thieu']]
    loi += ['đụng bảng NGOÀI lược đồ: %s.%s (%s) — trên CSDL mới bảng ấy chưa có' % k
            for k in ket['khoa_ngoai']]
    ket['loi'] = loi
    return ket
