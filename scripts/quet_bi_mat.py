"""QUÉT BÍ MẬT trước khi đẩy — repo này CÔNG KHAI.

── VÌ SAO (26/09/2026) ─────────────────────────────────────────────────────

`.gitignore` đã chặn `.env*` và `.the/`, và cổng `pre-push` có 13 bước. Nhưng
không bước nào đọc NỘI DUNG tệp sắp đẩy. Hai thứ khác nhau: `.gitignore` chặn
một TỆP bí mật lọt vào; nó không chặn ai đó dán một JWT còn sống vào tài liệu,
hay để nguyên đường dẫn máy mình trong một kịch bản.

Đo ngày 26/09: `PROGRESS.md` trên GitHub — cả `erp` lẫn `master` — chứa đường
dẫn `C:/Users/<tên tài khoản>/...` ở hai chỗ, và `scripts/do_mat_do_chu.mjs`
chứa thêm một chỗ nữa. Không phải khoá, không phải mật khẩu, nhưng là thứ RULES
§10 cấm đưa lên repo công khai, và không cửa nào bắt được.

── CÁCH DÙNG ───────────────────────────────────────────────────────────────

    python scripts/quet_bi_mat.py              # tệp sắp đẩy (so với origin/master)
    python scripts/quet_bi_mat.py --staged     # tệp đang trong vùng chờ commit
    python scripts/quet_bi_mat.py --tat-ca     # mọi tệp git theo dõi
    python scripts/quet_bi_mat.py --tu-kiem    # ĐÒI bộ quét phải bắt được mẫu giả

Thoát 1 nếu có phát hiện. Muốn bỏ qua một dòng (ví dụ mẫu regex, tài liệu dạy
cách nhận biết khoá): thêm `quet-bi-mat: bo-qua` vào chính dòng ấy.

── HAI Ý MƯỢN CỦA cloudflare/security-audit-skill ──────────────────────────

  · **Phát hiện phải có vết nguồn và kết quả quan sát được.** Bên ấy không nhận
    một phát hiện nếu thiếu đường dẫn đầy đủ tới chỗ sinh ra nó. Ở đây mỗi phát
    hiện in `tệp:dòng` kèm đoạn chữ đã che — đủ để người đọc tự mở ra xem, không
    phải tin lời công cụ.
  · **Người tìm khác người xác minh.** Bên ấy cho một agent khác đi CHỨNG MINH
    ĐIỀU NGƯỢC LẠI với từng phát hiện. Một mình tệp này không làm được thế, nên
    nó làm phần khả thi: `--tu-kiem` bắt CHÍNH NÓ phải đỏ với mẫu giả của từng
    quy tắc. Một bộ quét chưa bao giờ đỏ là một bộ quét chưa ai chứng minh là
    còn chạy (cùng bài học với `do_giao_dien.mjs --tu-kiem`, RULES §2).

── SOLID ───────────────────────────────────────────────────────────────────

  S · Tệp này chỉ tìm và báo. Nó không sửa tệp, không commit, không chặn push —
      việc chặn là của `pre-push` đọc mã thoát.
  O · Thêm loại bí mật mới = thêm một `Luat` vào `LUAT`. Không hàm nào phải sửa,
      và `--tu-kiem` tự động phủ luôn quy tắc mới vì nó đọc `mau_gia`.
  L · Mọi `Luat` dùng chung một giao diện, nên hàm quét không cần biết nó đang
      tìm khoá AWS hay đường dẫn Windows.
  I · Nguồn tệp tách khỏi bộ quét: `tep_sap_day()`, `tep_staged()`, `tep_tat_ca()`
      đều chỉ trả danh sách đường dẫn. Bộ quét không biết git là gì.
  D · `quet()` nhận danh sách tệp và danh sách luật từ ngoài vào, nên gọi được
      từ pytest với tệp giả, không cần repo thật.
"""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent

#: Đuôi tệp không đọc (nhị phân, ảnh, tài liệu đóng gói) — đọc cũng ra rác.
BO_DUOI = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.pdf', '.docx', '.xlsx',
    '.zip', '.gz', '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.webm', '.db', '.sqlite3',
}

#: Thư mục không quét.
BO_THU_MUC = ('node_modules/', '.venv/', '.next/', 'dist/', 'build/', '.git/')

#: Dòng có chữ này thì bỏ qua — dành cho chính tài liệu dạy cách nhận biết khoá.
MIEN = 'quet-bi-mat: bo-qua'


@dataclass(frozen=True)
class Luat:
    """Một loại bí mật. `mau_gia` là chuỗi mà quy tắc này BẮT BUỘC phải bắt được."""

    ma: str
    ten: str
    mau: str
    mau_gia: str
    vi_sao: str
    chi_duoi: tuple[str, ...] = field(default=())   # rỗng = mọi đuôi tệp
    bo_tep: str = ''                                # regex đường dẫn KHÔNG áp quy tắc này


LUAT: tuple[Luat, ...] = (
    Luat(
        'khoa-rieng', 'Khoá riêng',
        r'-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----',
        '-----BEGIN RSA PRIVATE KEY-----',
        'Khoá riêng lên repo công khai là mất khoá, không có cách thu hồi nửa vời.',
    ),
    Luat(
        'jwt', 'Thẻ JWT',
        r'\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}',
        'eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo3fQ.aBcDeFgHiJkLmNoPqRsTuVwXyZ012345',
        'Thẻ `pe_at` sống 30 phút — đủ để ai đọc được đăng nhập bằng quyền của chủ thẻ.',
    ),
    Luat(
        'chuoi-ket-noi', 'Chuỗi kết nối có mật khẩu',
        # Mật khẩu THẬT, không phải chỗ điền: ≥ 8 ký tự và trộn chữ với số.
        # Bản đầu chỉ đòi "≥ 3 ký tự bất kỳ" và kêu oan cả năm chỗ trong repo —
        # `user:password@`, `u:matkhau@`, `postgres:tam@localhost`. Một cổng kêu
        # oan là một cổng sắp bị tắt.
        r'\b(?:postgres|postgresql|mysql|mongodb|redis|amqp)://[^:/\s\'"]+:'
        r'(?=[^@\s\'"]*[A-Za-z])(?=[^@\s\'"]*\d)[^@\s\'"]{8,}@'
        r'(?!localhost|127\.0\.0\.1|db[:/]|postgres[:/]|mysql[:/])',
        'postgresql://neondb_owner:npg_A1b2C3d4E5f6@ep-that-123.neon.tech/neondb',
        'Một dòng này là toàn bộ CSDL Neon, kể cả nhánh production.',
    ),
    Luat(
        'khoa-nha-cung-cap', 'Khoá dịch vụ ngoài',
        r'\b(?:AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}'
        r'|xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9]{32,}|SG\.[A-Za-z0-9_-]{20,}\.)',
        'AKIAIOSFODNN7EXAMPLE',
        'Khoá AWS / GitHub / Slack / SendGrid: người nhặt được dùng được ngay, tốn tiền thật.',
    ),
    Luat(
        'duong-dan-nguoi-dung', 'Đường dẫn có tên tài khoản Windows',
        # Tên phải BẮT ĐẦU bằng chữ hoặc số: `C:/Users/.../Temp` là đường dẫn đã
        # che tay, không phải rò rỉ (bản đầu bắt cả nó vì `.` nằm trong lớp ký tự).
        r'[Cc]:[\\/]+Users[\\/]+(?!Public\b|Default\b|All\ Users\b|<)[A-Za-z0-9][A-Za-z0-9._-]{1,}',
        r'C:\Users\tenthat\AppData\Local',
        'RULES §10: repo công khai không mang tên tài khoản của người làm. '
        'Viết %USERPROFILE% hoặc %TEMP%.',
    ),
    Luat(
        'mat-khau-gan-cung', 'Mật khẩu gán thẳng trong mã',
        r'(?i)\b(?:password|passwd|mat_khau|secret_key|api_key|access_token)\s*[=:]\s*'
        r'[\'"](?!\s*$)(?!(?:x{3,}|\*{3,}|<|\{|\$|%|thay-|doi-|vi-du|example|changeme|password))[^\'"\n]{8,}[\'"]',
        'password = "Sup3rBiMatThat!"',
        'Mật khẩu trong mã đi theo mọi bản sao repo và mọi lần clone.',
        chi_duoi=('.py', '.mjs', '.js', '.ts', '.tsx', '.jsx', '.sql', '.sh', '.ps1', '.yml', '.yaml'),
        # Tệp kiểm thử tự đặt mật khẩu cho tài khoản nó vừa tạo trong CSDL dev
        # (`mat_khau='MatKhau#2026'`). Đó là dữ liệu của phép kiểm, không phải bí
        # mật — và mọi dữ liệu hiện có đều là GIẢ (anh Sơn 26/09).
        bo_tep=r'(^|/)(tests?_[^/]+|[^/]+_tests?)\.(py|mjs|ts|tsx)$|(^|/)(tests?|e2e)/',
    ),
)


def _chay_git(*dt: str) -> list[str]:
    r = subprocess.run(['git', *dt], cwd=GOC, capture_output=True, text=True, encoding='utf-8')
    if r.returncode != 0:
        return []
    return [d.strip() for d in r.stdout.splitlines() if d.strip()]


def tep_sap_day() -> list[str]:
    """Tệp khác `origin/master` — tức phần sắp đẩy lên repo công khai."""
    ds = _chay_git('diff', '--name-only', 'origin/master...HEAD')
    return ds or tep_staged()


def tep_staged() -> list[str]:
    return _chay_git('diff', '--cached', '--name-only')


def tep_tat_ca() -> list[str]:
    return _chay_git('ls-files')


def _doc(duong: Path) -> list[str]:
    try:
        return duong.read_text(encoding='utf-8', errors='replace').splitlines()
    except (OSError, ValueError):
        return []


def _che(s: str) -> str:
    """Che phần giữa: đủ để nhận ra chỗ nào, không đủ để dùng lại."""
    s = s.strip()
    if len(s) <= 24:
        return s[:8] + '…'
    return f'{s[:12]}…{s[-6:]}'


def quet(tep: list[str], luat: tuple[Luat, ...] = LUAT, goc: Path = GOC) -> list[dict]:
    """Trả danh sách phát hiện, mỗi cái có tệp, dòng, luật và đoạn đã che.

    Nhận tệp và luật từ ngoài (SOLID · D) nên pytest gọi được với thư mục giả.
    """
    ra: list[dict] = []
    da_dich = [(l, re.compile(l.mau)) for l in luat]
    for t in tep:
        if any(t.startswith(d) or f'/{d}' in t for d in BO_THU_MUC):
            continue
        p = goc / t
        if p.suffix.lower() in BO_DUOI or not p.is_file():
            continue
        # Chính tệp này chứa mẫu của mọi quy tắc — quét nó là tự cắn đuôi.
        if p.name == Path(__file__).name:
            continue
        for i, dong in enumerate(_doc(p), 1):
            if MIEN in dong:
                continue
            for l, rx in da_dich:
                if l.chi_duoi and p.suffix.lower() not in l.chi_duoi:
                    continue
                if l.bo_tep and re.search(l.bo_tep, t):
                    continue
                m = rx.search(dong)
                if m:
                    ra.append({'tep': t, 'dong': i, 'ma': l.ma, 'ten': l.ten,
                               'doan': _che(m.group(0)), 'vi_sao': l.vi_sao})
    return ra


def tu_kiem() -> int:
    """ĐÒI mỗi quy tắc bắt được mẫu giả của chính nó, và chỉ mẫu ấy.

    Bắt hụt = quy tắc chết (regex hỏng sau một lần sửa). Bắt chéo = quy tắc quá
    rộng, sẽ kêu oan trên mã lành và rồi bị người ta tắt đi.
    """
    hong = 0
    for l in LUAT:
        rx = re.compile(l.mau)
        if not rx.search(l.mau_gia):
            print(f'✗ {l.ma}: KHÔNG bắt được mẫu giả của chính nó — quy tắc đã chết')
            hong += 1
            continue
        cheo = [k.ma for k in LUAT if k.ma != l.ma and re.compile(k.mau).search(l.mau_gia)]
        if cheo:
            print(f'✗ {l.ma}: mẫu giả còn bị {", ".join(cheo)} bắt — quy tắc quá rộng')
            hong += 1
            continue
        print(f'✓ {l.ma:22} {l.ten}')
    if hong:
        print(f'\n{hong}/{len(LUAT)} quy tắc hỏng.')
        return 1
    print(f'\n{len(LUAT)}/{len(LUAT)} quy tắc đỏ được đúng chỗ của nó.')
    return 0


def main() -> int:
    if '--tu-kiem' in sys.argv:
        return tu_kiem()

    if '--tat-ca' in sys.argv:
        tep, nhan = tep_tat_ca(), 'mọi tệp git theo dõi'
    elif '--staged' in sys.argv:
        tep, nhan = tep_staged(), 'tệp trong vùng chờ commit'
    else:
        tep, nhan = tep_sap_day(), 'tệp khác origin/master'

    if not tep:
        print(f'Không có {nhan} để quét.')
        return 0

    ra = quet(tep)
    if not ra:
        print(f'✓ Quét {len(tep)} tệp ({nhan}): không thấy bí mật nào.')
        return 0

    print(f'✗ {len(ra)} phát hiện trong {len(tep)} tệp ({nhan}):\n')
    for p in ra:
        print(f"  {p['tep']}:{p['dong']}  [{p['ma']}]  {p['doan']}")
        print(f"      {p['vi_sao']}")
    print('\nSửa rồi đẩy lại. Nếu là mẫu ví dụ trong tài liệu, thêm '
          f"`{MIEN}` vào chính dòng ấy.")
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
