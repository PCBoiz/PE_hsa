"""H3 (24/09/2026) — `bootstrap_schema` với sổ `luoc_do_da_chay`, trên CSDL THẬT nhưng trong
một SCHEMA TẠM (`common.luoc_do_sql.schema_tam`) và cuộn lại hết.

Vì sao được chạy DDL ở đây dù `common/tests.py::test_khong_phep_kiem_nao_chay_DDL_tren_CSDL_dung_chung`
cấm: luật ấy chặn khoá ACCESS EXCLUSIVE trên bảng DÙNG CHUNG. Mọi bảng ở đây sinh ra trong
schema riêng của phép kiểm, và mỗi phép kiểm dựng lược đồ đều ĐÒI `khoa_ngoai() == []` — tức
đo bằng `pg_locks` rằng không một bảng nào ngoài schema tạm bị khoá.

Chậm (mỗi lần dựng đủ ~260 câu; từ máy dev ~290 ms một vòng gọi Neon): hai phép kiểm dựng
đủ, còn lại dùng mục tổng hợp vài câu.
"""
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import connection

from common.luoc_do_sql import (
    SO,
    LoiLuocDo,
    chia_muc,
    dien_tap,
    doc_so,
    doc_tat_ca,
    luot,
    schema_tam,
)


def _co_bang(ten):
    with connection.cursor() as cur:
        cur.execute('SELECT to_regclass(%s)', [ten])
        return cur.fetchone()[0] is not None


def _cot(bang, cot):
    with connection.cursor() as cur:
        cur.execute("SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() "
                    "AND table_name = %s AND column_name = %s", [bang, cot])
        return cur.fetchone() is not None


def _so():
    with connection.cursor() as cur:
        return doc_so(cur)


# ── Đủ lược đồ, qua ĐÚNG lệnh Render chạy ────────────────────────────────────

def test_csdl_moi_dung_du_va_lan_HAI_khong_do_dung_gi(db):
    """CSDL mới toanh: lượt 1 dựng đủ và ghi sổ MỌI mục; lượt 2 (= mọi deploy sau đó) không
    chạy lại mục nào và không dỡ-dựng một ràng buộc / chỉ mục nào; `kiem_luoc_do` đủ; không
    đụng bảng ngoài schema.

    Đỏ trên lệnh cũ (chạy lại cả tệp mỗi lượt): lượt 2 dỡ-dựng lại `class_members_pkey`,
    `users_role_check`… — đúng cơ chế đã làm §55 hỏng ở lượt thứ hai (24/09)."""
    import re
    ket = dien_tap()
    assert ket['loi'] == [], '\n'.join(ket['loi'])
    assert ket['so_dong_so'] == ket['so_muc'] == len(doc_tat_ca())
    tao = {re.match(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)', c, re.I).group(1).lower()
           for m in doc_tat_ca() for c in m.cau if re.match(r'CREATE\s+TABLE\b', c, re.I)}
    assert ket['so_bang'] == len(tao) + 1, 'mỗi CREATE TABLE một bảng, cộng bảng sổ'
    assert not _co_bang(ket['schema'] + '.users'), 'schema tạm phải bị cuộn lại'


def _sua_36(cac_muc, them=None, cu=None, moi=None):
    """Bản `cac_muc` với §36 sửa: thêm câu `them`, hoặc sửa TẠI CHỖ chuỗi `cu` → `moi`."""
    from common.luoc_do_sql import Muc, _bam
    i = next(i for i, m in enumerate(cac_muc) if m.khoa == 'legacy_schema.sql §36')
    m = cac_muc[i]
    if them is not None:
        cau = m.cau + (them,)
    else:
        assert sum(c.count(cu) for c in m.cau) == 1, '§36 đã đổi — sửa phép kiểm'
        cau = tuple(c.replace(cu, moi) for c in m.cau)
    return i, cac_muc[:i] + [Muc(m.tep, m.ma, m.tieu_de, m.dong, cau, _bam(cau))] + cac_muc[i + 1:]


def test_sua_muc_cu_chay_lai_ca_muc_sau(db, monkeypatch):
    """Sửa TẠI CHỖ §36 (mục bỏ khoá chính class_members CASCADE) → CHECK mới có hiệu lực VÀ
    khoá ngoại §55b còn; lượt ĐỨT giữa §36 với §55 không được để sổ nói dối.

    Phần 1 — đúng việc kế hoạch sắp làm: thêm 'reserved' vào CHECK lý do rời lớp của §36.
    Luật hậu tố: chỉ chạy lại riêng mục đổi thì CASCADE kéo mất
    `class_members_transferred_to_fk` và không mục nào gắn lại — mất trong im lặng.
    Phần 2 — tái hiện sự cố nhánh dev 24/09 (khoá ngoại §55b mất): lượt chạy §36 rồi hỏng
    ở §43. CSDL lúc ấy THIẾU khoá ngoại (không tránh được khi mỗi mục một giao dịch), nhưng
    sổ không được ghi §55 là đã chạy — lượt kế tiếp phải chạy lại §43..hết và gắn lại nó."""
    from common import luoc_do_sql
    from common.management.commands.kiem_luoc_do import _check_co_gia_tri, _fk

    def fk55():
        return _fk('class_members', 'class_members_transferred_to_fk', 'SET NULL')

    cac_muc = doc_tat_ca()
    with schema_tam() as st:
        luot(cac_muc=cac_muc)
        assert fk55()[0]
        assert not _check_co_gia_tri('class_members_leave_reason_check', 'reserved')[0]

        # ── Phần 1
        i, sua = _sua_36(cac_muc, cu="'dropped', 'transferred')",
                         moi="'dropped', 'transferred', 'reserved')")
        viec = luot(cac_muc=sua)
        assert viec[0].muc.khoa == 'legacy_schema.sql §36'
        assert [v.muc.khoa for v in viec] == [x.khoa for x in sua[i:]]
        assert _check_co_gia_tri('class_members_leave_reason_check', 'reserved')[0], (
            'sửa tại chỗ CHECK §36 mà CSDL chưa nhận giá trị mới')
        ok, vi_sao = fk55()
        assert ok, 'khoá ngoại §55 mất sau khi sửa §36: ' + vi_sao

        # ── Phần 2
        _, sua2 = _sua_36(cac_muc, them='SELECT 2')
        m43 = next(m for m in sua2 if m.khoa == 'legacy_schema.sql §43')
        that = luoc_do_sql._thuc_thi

        def hong_o_43(cur, cau):
            if cau == m43.cau[0]:
                raise RuntimeError('mạng đứt giữa lượt (giả)')
            return that(cur, cau)

        monkeypatch.setattr(luoc_do_sql, '_thuc_thi', hong_o_43)
        with pytest.raises(LoiLuocDo, match='§43'):
            luot(cac_muc=sua2)
        so = _so()
        sau_36 = [m.khoa for m in sua2[i + 1:]]
        chua = [k for k in sau_36 if k in so]
        assert chua == ['legacy_schema.sql §%d' % n for n in range(37, 43)], (
            'sổ phải có đúng §37..§42 (đã chạy lại trong lượt hỏng), không mục nào từ §43: %s' % chua)
        assert not fk55()[0], 'giả định của phép kiểm: §36 đã gỡ khoá ngoại và §55 chưa chạy'

        monkeypatch.setattr(luoc_do_sql, '_thuc_thi', that)
        viec = luot(cac_muc=sua2)
        assert viec[0].muc.khoa == 'legacy_schema.sql §43'
        assert 'legacy_schema.sql §55' in [v.muc.khoa for v in viec]
        ok, vi_sao = fk55()
        assert ok, 'lượt sau lượt hỏng không gắn lại khoá ngoại §55: ' + vi_sao
        assert st.khoa_ngoai() == []


# ── Mục tổng hợp: giao dịch, sổ, lượt đứt giữa chừng ─────────────────────────

MAU = (
    '-- ── §1 · A ──\n'
    'CREATE TABLE IF NOT EXISTS t_a (id INT);\n'
    '-- ── §2 · B ──\n'
    'ALTER TABLE t_a ADD COLUMN IF NOT EXISTS b INT;\n'
    '-- ── §3 · C ──\n'
    'ALTER TABLE t_a ADD COLUMN IF NOT EXISTS c INT;\n'
)


def test_muc_hong_cuon_lai_CA_muc_va_khong_ghi_so(db):
    """Câu thứ hai của §2 hỏng → câu thứ nhất của §2 cũng không còn (không như autocommit:
    DROP đã commit mà ADD hỏng); §2 không vào sổ; §1 đã chạy thì giữ."""
    hong = MAU.replace('ADD COLUMN IF NOT EXISTS b INT;',
                       'ADD COLUMN IF NOT EXISTS b INT;\nSELECT 1/0;')
    with schema_tam():
        with pytest.raises(LoiLuocDo, match=r't.sql §2 · câu 2/2'):
            luot(cac_muc=chia_muc('t.sql', hong))
        assert _cot('t_a', 'id')
        assert not _cot('t_a', 'b'), '§2 hỏng mà cột của câu đầu §2 vẫn còn'
        assert set(_so()) == {'t.sql §1'}

        viec = luot(cac_muc=chia_muc('t.sql', MAU))          # vá xong, chạy lại
        assert [v.muc.ma for v in viec] == ['§2', '§3']
        assert _cot('t_a', 'b') and _cot('t_a', 'c')


def test_luot_dut_giua_chung_thi_luot_sau_chay_not_phan_sau(db):
    """Sửa §1 → lượt phải chạy §1..§3. Lượt ấy hỏng ở §2 → lượt kế (đã vá) vẫn phải chạy §3,
    dù nội dung §3 không đổi và sổ từng ghi nó: §1 đã chạy lại thì mọi mục sau nó phải chạy lại."""
    with schema_tam():
        luot(cac_muc=chia_muc('t.sql', MAU))
        sua_1 = MAU.replace('(id INT)', '(id INT, ghi_chu TEXT)')
        hong_2 = sua_1.replace('b INT;', 'b INT;\nSELECT 1/0;')
        with pytest.raises(LoiLuocDo):
            luot(cac_muc=chia_muc('t.sql', hong_2))
        viec = luot(cac_muc=chia_muc('t.sql', sua_1))
        assert [v.muc.ma for v in viec] == ['§2', '§3']


class _BeTac(Exception):
    """Giả lỗi Postgres bế tắc (SQLSTATE 40P01) — gặp thật trên nhánh dev 24/09 ở §43."""
    sqlstate = '40P01'


def _dem_va_gia(monkeypatch, loi_khi, so_lan):
    """Thay `_thuc_thi`: câu chứa `loi_khi` ném `_BeTac` ở `so_lan` lần đầu. Trả bộ đếm."""
    from common import luoc_do_sql
    that = luoc_do_sql._thuc_thi
    dem = {'goi': 0, 'nem': 0}

    def gia(cur, cau):
        if loi_khi in cau:
            dem['goi'] += 1
            if dem['nem'] < so_lan:
                dem['nem'] += 1
                raise _BeTac('deadlock detected (giả)')
        return that(cur, cau)

    monkeypatch.setattr(luoc_do_sql, '_thuc_thi', gia)
    monkeypatch.setattr(luoc_do_sql, 'CHO_THU_LAI', (0, 0, 0))
    return dem


def test_be_tac_thi_cuon_lai_muc_va_THU_LAI(db, monkeypatch):
    dem = _dem_va_gia(monkeypatch, 'b INT', so_lan=2)
    with schema_tam():
        viec = luot(cac_muc=chia_muc('t.sql', MAU))
        assert [v.muc.ma for v in viec] == ['§1', '§2', '§3']
        assert dem == {'goi': 3, 'nem': 2}
        assert _cot('t_a', 'b') and _cot('t_a', 'c')
        assert set(_so()) == {'t.sql §1', 't.sql §2', 't.sql §3'}


def test_be_tac_mai_thi_dung_sau_so_lan_thu_va_khong_ghi_so(db, monkeypatch):
    dem = _dem_va_gia(monkeypatch, 'b INT', so_lan=99)
    with schema_tam():
        with pytest.raises(LoiLuocDo, match='deadlock'):
            luot(cac_muc=chia_muc('t.sql', MAU))
        assert dem['goi'] == 4, 'một lần đầu + ba lần thử lại'
        assert set(_so()) == {'t.sql §1'}


def test_loi_khong_phai_khoa_thi_KHONG_thu_lai(db, monkeypatch):
    """Chia cho 0 (SQLSTATE 22012) là lỗi của câu lệnh — thử lại chỉ tốn giờ build."""
    dem = _dem_va_gia(monkeypatch, '1/0', so_lan=0)
    hong = MAU.replace('b INT;', 'b INT;\nSELECT 1/0;')
    with schema_tam():
        with pytest.raises(LoiLuocDo, match='division by zero'):
            luot(cac_muc=chia_muc('t.sql', hong))
        assert dem['goi'] == 1


def test_moi_muc_dat_lock_timeout_ngan(db, monkeypatch):
    """Một ALTER đứng chờ khoá sau một truy vấn dài chặn MỌI truy vấn mới vào bảng ấy. Mỗi mục
    phải tự đặt `lock_timeout` (SET LOCAL) để bỏ cuộc sớm rồi thử lại."""
    from common import luoc_do_sql
    that = luoc_do_sql._thuc_thi
    thay = []

    def gia(cur, cau):
        that(cur, cau)
        cur.execute('SHOW lock_timeout')
        thay.append(cur.fetchone()[0])

    monkeypatch.setattr(luoc_do_sql, '_thuc_thi', gia)
    with schema_tam():
        luot(cac_muc=chia_muc('t.sql', MAU))
    assert thay and set(thay) == {luoc_do_sql.CHO_KHOA}, thay


def test_do_khoa_bat_duoc_cau_tro_nham_bang_that(db):
    """Thước `khoa_ngoai()` phải ĐỎ được: một câu nhắc tới bảng mà lược đồ chưa dựng sẽ âm
    thầm rơi xuống `public` (còn trong `search_path` vì pg_trgm) — trên CSDL mới toanh câu
    ấy hỏng. Chỉ một SELECT (AccessShareLock, như mọi phép kiểm khác đọc `users`)."""
    with schema_tam() as st:
        luot(cac_muc=chia_muc('t.sql', '-- ── §1 · A ──\nSELECT 1 FROM users LIMIT 0;\n'))
        assert ('public', 'users', 'AccessShareLock') in st.khoa_ngoai()


def test_kiem_chi_doc_khong_tao_so(db):
    with schema_tam():
        ra = StringIO()
        call_command('bootstrap_schema', '--kiem', stdout=ra)
        assert 'CHƯA có' in ra.getvalue()
        with connection.cursor() as cur:
            cur.execute("SELECT to_regclass(format('%%I.%%I', current_schema(), %s::text))", [SO])
            assert cur.fetchone()[0] is None, '--kiem đã tạo bảng sổ — lệnh ấy phải chỉ đọc'


def test_kiem_ma_loi_thoat_1_khi_con_muc_cho(db):
    with schema_tam():
        with pytest.raises(SystemExit) as e:
            call_command('bootstrap_schema', '--kiem', '--ma-loi', stdout=StringIO())
        assert e.value.code == 1


def test_kiem_luoc_do_hoi_dung_schema_hien_hanh(db):
    """`kiem_luoc_do` phải hỏi schema ĐANG dùng — nếu không, lượt diễn tập trong schema tạm
    được `public` "chấm đỗ" hộ mọi mục."""
    from common.management.commands import kiem_luoc_do as k
    with schema_tam(co_public=False):
        k_cot, _chi_muc, _check_co_gia_tri = k._cot, k._chi_muc, k._check_co_gia_tri
        assert k_cot('users', 'id')[0] is False
        assert _chi_muc('idx_levents_ref')[0] is False
        assert _check_co_gia_tri('users_role_check', 'admin')[0] is False
