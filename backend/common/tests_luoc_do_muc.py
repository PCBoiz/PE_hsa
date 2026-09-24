"""H3 (24/09/2026) — chia `sql/*.sql` thành MỤC + lập kế hoạch chạy. KHÔNG chạm CSDL.

Phần chạm CSDL (giao dịch từng mục, schema tạm, hai lượt) ở `tests_luoc_do_csdl.py`.
Cổng pre-push (`.githooks/pre-push`) chạy tệp NÀY vì nó nhanh và không cần mạng.
"""
import re

import pytest

from common.luoc_do_sql import (
    LoiLuocDo,
    _split_statements,
    chia_muc,
    doc_tat_ca,
    lap_ke_hoach,
    mo_coi,
    thu_muc_sql,
)

MAU = (
    '-- đầu tệp\n'
    'CREATE EXTENSION IF NOT EXISTS pg_trgm;\n'
    '\n'
    '-- 1. users ----------------------------------------\n'
    'CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY);\n'
    '-- ============================================================\n'
    '-- 2. Lớp học (2026-08-24)\n'
    '-- ============================================================\n'
    '-- 1. dòng đánh số TRONG lời giải thích, không phải tiêu đề\n'
    '-- §31 đã nhận ra điều này — câu văn, không phải tiêu đề\n'
    'CREATE TABLE IF NOT EXISTS classes (\n'
    '    id   SERIAL PRIMARY KEY,\n'
    '    name TEXT\n'
    ');\n'
    '-- §3 · Kiểu giữa (31/08)\n'
    'ALTER TABLE users ADD COLUMN IF NOT EXISTS a INT;\n'
    '-- ── §4 · KIỂU MỚI (24/09) ──────────\n'
    'ALTER TABLE users ADD COLUMN IF NOT EXISTS b INT;\n'
    'ALTER TABLE users ADD COLUMN IF NOT EXISTS c INT;\n'
)


def _ma(ds):
    return [m.ma for m in ds]


def test_chia_du_ba_kieu_tieu_de_va_muc_nen():
    ds = chia_muc('t.sql', MAU)
    assert _ma(ds) == ['nền', '§1', '§2', '§3', '§4']
    assert [len(m.cau) for m in ds] == [1, 1, 1, 1, 2]
    assert ds[2].tieu_de == 'Lớp học (2026-08-24)'
    assert ds[4].tieu_de == 'KIỂU MỚI (24/09)'
    assert ds[4].khoa == 't.sql §4'


def test_tep_khong_tieu_de_la_mot_muc_nen():
    ds = chia_muc('m.sql', 'CREATE TABLE a (x INT);\nCREATE TABLE b (y INT);\n')
    assert _ma(ds) == ['nền'] and len(ds[0].cau) == 2


def test_hai_tieu_de_cung_ma_thi_DUNG():
    """Hai nhánh cùng lấy §57 — gộp xong phải đổi số, không được đoán mục nào là mục nào."""
    with pytest.raises(LoiLuocDo, match='cùng mã §4'):
        chia_muc('t.sql', MAU + '-- ── §4 · TRÙNG SỐ ──\nSELECT 1;\n')


@pytest.mark.parametrize('dong', [
    '-- ── §5 TÊN (quên chấm giữa) ──',
    '-- §5 — Tên (gạch dài thay chấm giữa)',
    '-- §5: Tên',
])
def test_tieu_de_viet_lech_mau_thi_DUNG(dong):
    """Tiêu đề sai mẫu không được lặng lẽ gộp vào mục trước."""
    with pytest.raises(LoiLuocDo, match='sai mẫu'):
        chia_muc('t.sql', MAU + dong + '\nSELECT 1;\n')


def test_cau_cuoi_muc_thieu_cham_phay_thi_DUNG():
    """Thiếu `;` trước tiêu đề: chạy theo mục và chạy cả tệp phát ra hai thứ khác nhau."""
    hong = MAU.replace('ADD COLUMN IF NOT EXISTS a INT;', 'ADD COLUMN IF NOT EXISTS a INT')
    with pytest.raises(LoiLuocDo, match='thiếu `;`'):
        chia_muc('t.sql', hong)


def test_checksum_bo_qua_chu_thich_CRLF_khoang_trang_cuoi_dong():
    goc = {m.ma: m.checksum for m in chia_muc('t.sql', MAU)}
    doi_chu_thich = MAU.replace('-- 2. Lớp học (2026-08-24)', '-- 2. Lớp học — viết lại lời')
    doi_chu_thich = doi_chu_thich.replace('INT;\n-- ── §4', 'INT;   -- thêm lời cuối dòng\n-- ── §4')
    # Lời cuối dòng GIỮA một câu nhiều dòng (việc hay làm nhất: chú thích một cột) để lại
    # khoảng trắng cuối dòng sau khi bỏ `--` — checksum phải bỏ qua nó (đột biến A3 bắt được
    # bản đầu của phép kiểm này thiếu đúng trường hợp ấy).
    loi_cot = MAU.replace('    name TEXT\n', '    name TEXT   -- tên lớp, người nhập tự đặt\n')
    for bien in (doi_chu_thich, loi_cot, MAU.replace('\n', '\r\n'), MAU.replace(';\n', ';   \n')):
        assert {m.ma: m.checksum for m in chia_muc('t.sql', bien)} == goc


def test_checksum_doi_khi_cau_lenh_doi():
    goc = {m.ma: m.checksum for m in chia_muc('t.sql', MAU)}
    sua = {m.ma: m.checksum for m in chia_muc('t.sql', MAU.replace('b INT', 'b BIGINT'))}
    assert [k for k in goc if goc[k] != sua[k]] == ['§4']


def _so(ds, tru=()):
    return {m.khoa: m.checksum for m in ds if m.ma not in tru}


def test_ke_hoach_so_trong_thi_chay_het():
    ds = chia_muc('t.sql', MAU)
    for so in (None, {}):
        assert [v.muc.ma for v in lap_ke_hoach(ds, so)] == _ma(ds)


def test_ke_hoach_khong_doi_gi_thi_rong():
    ds = chia_muc('t.sql', MAU)
    assert lap_ke_hoach(ds, _so(ds)) == []


def test_ke_hoach_muc_moi_o_cuoi_chi_chay_minh_no():
    ds = chia_muc('t.sql', MAU)
    viec = lap_ke_hoach(ds, _so(ds, tru=('§4',)))
    assert [(v.muc.ma, v.ly_do) for v in viec] == [('§4', 'mới')]


def test_ke_hoach_sua_muc_cu_chay_no_VA_MOI_MUC_SAU():
    """§36 bỏ khoá chính CASCADE → khoá ngoại §55 chỉ được gắn lại nếu §55 cũng chạy."""
    ds = chia_muc('t.sql', MAU)
    so = _so(ds)
    so['t.sql §2'] = 'checksum-cu'
    viec = lap_ke_hoach(ds, so)
    assert [v.muc.ma for v in viec] == ['§2', '§3', '§4']
    assert viec[0].ly_do == 'đổi nội dung'
    assert viec[1].ly_do == 'đứng sau t.sql §2'


def test_ke_hoach_tat_ca_bo_qua_so():
    ds = chia_muc('t.sql', MAU)
    viec = lap_ke_hoach(ds, _so(ds), tat_ca=True)
    assert [v.muc.ma for v in viec] == _ma(ds)


def test_mo_coi_chi_bao_khoa_khong_con_trong_tep():
    ds = chia_muc('t.sql', MAU)
    so = _so(ds)
    so['t.sql §99'] = 'x'
    assert mo_coi(ds, so) == ['t.sql §99']
    assert mo_coi(ds, None) == []


# ── Tệp THẬT ──────────────────────────────────────────────────────────────────

def _tep_that():
    return (thu_muc_sql() / 'legacy_schema.sql').read_text(encoding='utf-8')


def test_tep_that_chia_duoc_va_du_cac_muc_da_co():
    """Mọi mục của tệp thật đọc ra được, không trùng số (chia_muc dừng khi trùng).

    KHÔNG đòi số tăng dần: số mục là TÊN, thứ tự chạy là thứ tự trong tệp. §58–§61 đang giữ
    chỗ cho nhánh khác và sẽ nằm SAU §62 trong tệp — thêm ở cuối là đúng luật."""
    ds = doc_tat_ca()
    so = {int(m.ma[1:]) for m in ds if m.tep == 'legacy_schema.sql' and m.ma != 'nền'}
    assert set(range(1, 58)) <= so, 'thiếu mục: %s' % sorted(set(range(1, 58)) - so)
    # Ghép câu của mọi mục = câu của cả tệp (chia_muc tự kiểm; đây ghim thêm con số).
    for p in sorted(thu_muc_sql().glob('*.sql')):
        ca_tep = _split_statements(p.read_text(encoding='utf-8'))
        assert sum(len(m.cau) for m in ds if m.tep == p.name) == len(ca_tep)


def _ke_hoach_sau_khi_sua(sua):
    """(các mục hiện tại, kế hoạch lượt kế) nếu `legacy_schema.sql` bị `sua(raw)`, trên một
    CSDL đã chạy đủ bản hiện tại (sổ = checksum của bản hiện tại)."""
    goc = doc_tat_ca()
    so = {m.khoa: m.checksum for m in goc}
    sau = chia_muc('legacy_schema.sql', sua(_tep_that()))
    return goc, lap_ke_hoach(sau + [m for m in goc if m.tep != 'legacy_schema.sql'], so)


XUONG = chr(10)


def test_sua_TAI_CHO_check_o_35_va_36_chay_lai_tu_35_toi_het():
    """Kế hoạch đợt tới sửa TẠI CHỖ: §35 thêm 'paused' vào CHECK trạng thái lớp, §36 thêm
    'reserved' vào CHECK lý do rời lớp. Hai mục ấy đổi checksum → lượt kế chạy §35, §36 VÀ
    mọi mục sau (§36 gỡ khoá chính CASCADE, chỉ §55 gắn lại khoá ngoại)."""
    a = ('ALTER TABLE classes ADD CONSTRAINT classes_status_check' + XUONG
         + "    CHECK (status IN ('active', 'finished', 'cancelled'));")
    b = "leave_reason IN ('completed', 'dropped', 'transferred'))"

    def sua(raw):
        raw = XUONG.join(raw.splitlines())
        assert raw.count(a) == 1 and raw.count(b) == 1, 'CHECK trong tệp đã đổi — sửa phép kiểm'
        raw = raw.replace(a, a.replace("'cancelled'", "'cancelled', 'paused'"))
        return raw.replace(b, b.replace("'transferred'", "'transferred', 'reserved'"))

    goc, viec = _ke_hoach_sau_khi_sua(sua)
    khoa = [m.khoa for m in goc]
    i35 = khoa.index('legacy_schema.sql §35')
    assert [v.muc.khoa for v in viec] == khoa[i35:], 'phải chạy đúng §35 tới HẾT (kể cả mockexam)'
    ly_do = {v.muc.ma: v.ly_do for v in viec if v.muc.tep == 'legacy_schema.sql'}
    assert ly_do['§35'] == ly_do['§36'] == 'đổi nội dung'
    assert ly_do['§55'] == 'đứng sau legacy_schema.sql §35'
    assert "'paused'" in ' '.join(viec[0].muc.cau)


def test_sua_chu_thich_muc_cu_khong_chay_lai_gi():
    cu = '-- 35. Bất biến ở tầng CSDL'
    _, viec = _ke_hoach_sau_khi_sua(lambda raw: raw.replace(cu, cu + ' (viết lại lời)'))
    assert viec == []


def _so_chua_dung():
    """(số lớn chưa dùng, số NHỎ HƠN mục cuối mà chưa dùng) — lấy từ tệp thật để phép kiểm
    không va vào mục có thật (bản đầu dùng §62 cứng; master viết §62 thật cùng ngày)."""
    da = {int(m.ma[1:]) for m in doc_tat_ca() if m.tep == 'legacy_schema.sql' and m.ma != 'nền'}
    lon = max(da) + 40
    nho = min(n for n in range(1, max(da)) if n not in da)
    return lon, nho


def _muc(so, ten, cau):
    return XUONG.join(['', '-- ── §%d · %s (25/09/2026) ──' % (so, ten), cau, ''])


def test_them_muc_moi_o_cuoi_chi_chay_no_va_tep_sau():
    """Thêm một mục ở cuối `legacy_schema.sql`: chạy nó, rồi `mockexam_schema.sql` (tệp đứng sau
    theo tên — 8 câu CREATE … IF NOT EXISTS, vô hại). Không mục cũ nào chạy lại."""
    lon, _ = _so_chua_dung()
    them = _muc(lon, 'MỤC THỬ', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS x INT;')
    _, viec = _ke_hoach_sau_khi_sua(lambda raw: raw + them)
    assert [(v.muc.khoa, v.ly_do) for v in viec] == [
        ('legacy_schema.sql §%d' % lon, 'mới'),
        ('mockexam_schema.sql nền', 'đứng sau legacy_schema.sql §%d' % lon)]


def test_muc_giu_cho_viet_SAU_mot_muc_so_lon_hon_van_hop_le():
    """Số giữ chỗ (§58–§61) viết khi mục số lớn hơn đã nằm trong tệp: thêm ở CUỐI tệp; chỉ nó
    (và tệp sau) chạy."""
    lon, nho = _so_chua_dung()
    them_lon, them_nho = _muc(lon, 'A', 'SELECT 1;'), _muc(nho, 'B', 'SELECT 2;')
    khac = [m for m in doc_tat_ca() if m.tep != 'legacy_schema.sql']
    so = {m.khoa: m.checksum
          for m in chia_muc('legacy_schema.sql', _tep_that() + them_lon) + khac}
    sau = chia_muc('legacy_schema.sql', _tep_that() + them_lon + them_nho)
    viec = lap_ke_hoach(sau + khac, so)
    assert [v.muc.khoa for v in viec] == ['legacy_schema.sql §%d' % nho, 'mockexam_schema.sql nền']


def test_moi_muc_trong_kiem_luoc_do_tro_toi_mot_muc_co_that():
    """`kiem_luoc_do` đặt tên dòng theo mục (`§55a` → §55). Đổi số một mục mà quên bên ấy thì
    lệnh kia báo về một mục không tồn tại."""
    from common.management.commands.kiem_luoc_do import MUC
    co = {m.ma for m in doc_tat_ca() if m.tep == 'legacy_schema.sql'}
    lac = [ma for ma, _, _ in MUC if re.sub(r'[a-z]$', '', ma) not in co]
    assert lac == [], lac
