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
    'CREATE TABLE IF NOT EXISTS classes (id SERIAL PRIMARY KEY);\n'
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
    for bien in (doi_chu_thich, MAU.replace('\n', '\r\n'), MAU.replace(';\n', ';   \n')):
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

def test_tep_that_chia_duoc_va_so_muc_tang_dan():
    """Mọi mục của `legacy_schema.sql` đọc ra, số tăng NGHIÊM NGẶT (gộp hai nhánh mà thứ tự
    đảo — §57 trước §56 — là đỏ ở đây, không đợi tới deploy)."""
    ds = doc_tat_ca()
    legacy = [m for m in ds if m.tep == 'legacy_schema.sql']
    so = [int(m.ma[1:]) for m in legacy if m.ma != 'nền']
    assert so == sorted(set(so)), 'số mục không tăng nghiêm ngặt: %s' % so
    assert so[0] == 1 and so[-1] >= 56
    # Ghép câu của mọi mục = câu của cả tệp (chia_muc tự kiểm; đây ghim thêm con số).
    for p in sorted(thu_muc_sql().glob('*.sql')):
        ca_tep = _split_statements(p.read_text(encoding='utf-8'))
        assert sum(len(m.cau) for m in ds if m.tep == p.name) == len(ca_tep)


def test_moi_muc_trong_kiem_luoc_do_tro_toi_mot_muc_co_that():
    """`kiem_luoc_do` đặt tên dòng theo mục (`§55a` → §55). Đổi số một mục mà quên bên ấy thì
    lệnh kia báo về một mục không tồn tại."""
    from common.management.commands.kiem_luoc_do import MUC
    co = {m.ma for m in doc_tat_ca() if m.tep == 'legacy_schema.sql'}
    lac = [ma for ma, _, _ in MUC if re.sub(r'[a-z]$', '', ma) not in co]
    assert lac == [], lac
