# Bàn giao phiên — đọc tệp này đầu tiên khi mở phiên mới

*Cập nhật 26/09/2026 sáng. Thay bản 16/09 (lịch sử: `git log -- BAN-GIAO-PHIEN.md`). Viết cho một phiên Claude mới
và cho anh Sơn: đọc xong tệp này là bắt tay làm được, không phải đọc lại nhật ký.*

---

## 1. Đọc theo thứ tự (mỗi tệp một vai)

| # | Tệp | Để làm gì |
|---|---|---|
| 1 | `CLAUDE.md` | nhánh, luật cứng, lệnh — ngắn |
| 2 | `PROGRESS.md` (khối "Lệnh đang hiệu lực" + mục trên cùng dưới `<!-- MỚI NHẤT -->`) | lệnh của anh Sơn + trạng thái mới nhất |
| 3 | `docs/KE_HOACH_TOPHSA_THU_NGHIEM_2026-09-24.md` mục **"KẾ HOẠCH v2"** | bảng theo dõi việc (P0, N, V, E1–E5, 1.5B/C, 1.6, Đ2…) |
| 4 | `docs/NGHIEM_THU_TOPHSA.md` | 32 dòng khách nghiệm thu (cột TRUE = khách đã ký dòng ấy — mình KHÔNG tick hộ) |
| 5 | `docs/VIEC_CUA_ANH.md` — bảng đầu tệp | mọi việc chỉ anh Sơn làm được (lời thường) |
| 6 | `docs/THIET_KE_HE_THONG.md` | vai × phạm vi, trang theo vai, 10 miền (§4), luật thiết kế (§8), việc kiến trúc S1–S7 |
| 7 | `docs/CAU_TRUC_MA.md`, `docs/CAU_TRUC_DU_LIEU.md` (tự sinh) | tệp nào thuộc miền nào, bảng/cột/khoá theo miền, sổ nợ ghi chéo |
| 8 | `REVIEW.md`, `RULES.md` | soát trước khi đẩy; luật kèm lý do |
| 9 | `docs/cloud/BAO_CAO_*.md` | báo cáo các phiên cloud (A1, A2, E1, cấu trúc, pytest) |

## 2. Trạng thái lúc bàn giao (26/09/2026 sáng)

**Nhánh** (repo công khai `PCBoiz/PE_hsa`):

| Nhánh | Là gì | Trạng thái |
|---|---|---|
| `master` | **production** (Vercel + Render tự deploy) | `bd58824` (24/09) — **chậm erp 113 commit**. Có lỗi rò ghi chú chuyển lớp lên tờ phụ huynh; bản vá đã ở erp |
| `erp` | nhánh thử nghiệm — MỌI việc commit ở đây | đã gộp A1 + A2 + E1 + cấu trúc; cổng pre-push ĐẠT |
| `erp-DB` | nhánh CSDL riêng của Cao Văn Nhân | **không đụng** (anh chốt: Nhân làm CSDL ở nhánh riêng) |
| `cloud/e2-b`, `cloud/e3-b` | phiên cloud E2 (thông báo) / E3 (hộp Yêu cầu) | đã đẩy BACKEND rồi dừng; chưa giao diện, chưa báo cáo — xem việc 1–2 |
| `agent/luong-a1`, `agent/luong-a2`, `agent/e1`, `cloud/cau-truc-b` | đã gộp vào erp | xoá được |
| `cloud/pytest-d255ca8` | báo cáo pytest cũ | xoá được |

**CSDL**: máy dev nối Neon nhánh **dev** (máy chủ `ep-little-water`, trong `backend/.env` — đừng in, đừng sửa). Production
là `ep-billowing-fog`. Lược đồ dev: `bootstrap_schema` ×2 → 0/64 mục, `kiem_luoc_do` 63/63. Mục § đang có: tới §70
(§61 của E2, §65 của E3 nằm trên nhánh của chúng). Tài khoản e2e (id 36029) đã ở lớp mẫu 7322 (26/09).

**Số đo 26/09 trên dev** (sau gộp): pytest 30 mô-đun chạm tới xanh trên Neon (có bài thật); e2e hai khổ các spec
chuong-trinh / van-hanh-a2 / ho-so-hoc-vien / danh-sach-hoc-vien / vai-tro-cong xanh; `do_axe` 0 vi phạm / 104 lượt;
`do_giao_dien` 36 trang × 2 khổ 0 mọi luật, `--tu-kiem` 72/72. **CHƯA chạy**: pytest ĐỦ BỘ trên Neon sau gộp, e2e ĐỦ BỘ.

## 3. Việc làm tiếp — theo thứ tự

0. **(anh Sơn) Đăng nhập lại tài khoản cloud** (việc C2-cloud) — 26/09 06:15 mọi lượt mở phiên cloud trả **401** dù
   `auth status` báo đã đăng nhập (thẻ hết hạn; tiện ích VS Code vừa lên 2.1.282). Trong PowerShell:
   ```powershell
   $env:CLAUDE_CONFIG_DIR = "$HOME\.claude-son"
   $bin = (Get-ChildItem "$HOME\.vscode\extensions\anthropic.claude-code-*\resources\native-binary\claude.exe" | Sort-Object FullName | Select-Object -Last 1).FullName
   & $bin auth logout; & $bin auth login
   ```
   (đăng nhập trên trình duyệt bằng tài khoản claude.ai dùng cho cloud). Cloud credits hết hạn 05/11/2026.
1. **Mở lại phiên cloud nối tiếp E2 và E3** (sau việc 0). Cách làm ở mục 5 "Claude cloud". Nội dung việc: làm TIẾP trên
   `cloud/e2-b` / `cloud/e3-b` (không làm lại backend): gộp `origin/erp` trước; thêm bảng mới vào `scripts/so_mien.json`
   (E2 → miền `thong_bao`: outbox, announcements; E3 → miền `yeu_cau`: yeu_cau, yeu_cau_su_kien) vì cổng f7 sẽ đòi;
   giao diện React + test đỏ-trước + đột biến + hướng dẫn/quyền + NGHIEM_THU; báo cáo `docs/cloud/BAO_CAO_E2.md` /
   `BAO_CAO_E3.md`. Brief chi tiết = mục "Luồng B" / "Luồng C" của kế hoạch v2 + `docs/THIET_KE_HE_THONG.md`.
2. **Gộp E2, E3 khi có báo cáo** — `git fetch` NGAY trước khi gộp (26/09 gộp thiếu 8 commit vì fetch sớm); giải xung đột
   giữ cả hai phía; `bootstrap_schema` ×2 + `kiem_luoc_do` trên dev; pytest từng mô-đun đã chạm TRÊN NEON (máy cloud
   không có bài học → ~70 test luôn đỏ ở đó vì môi trường); e2e hai khổ `E2E_GHI=1`; `do_axe` + `do_giao_dien`
   (`--tu-kiem` trước); thêm màn mới vào danh sách trang của hai bộ đo.
3. **Cổng cho N4** (gộp erp → master = deploy production): pytest đủ bộ trên Neon dev (~54 phút, từng mô-đun), e2e
   đủ bộ hai khổ, `do_axe`, `do_giao_dien`. Xanh hết → báo anh **"erp đã thử xong"** kèm số đo. Trước đó anh phải làm
   **N6** (xếp lớp cho mọi học viên thật — bản mới khoá môn theo lớp). Thứ tự deploy: backend + lược đồ (Render) trước,
   đợi Render xong (~45 phút), rồi mới tới frontend; khoá mới trong phản hồi đều `.optional()` trong zod.
4. **Còn lại của kế hoạch v2** (xem bảng theo dõi):
   - **N**: bộ e2e `frontend/e2e/nghiem-thu/dong-NN.spec.ts` đi đúng kịch bản demo từng dòng NGHIEM_THU.
   - **E1 phần sót**: bài tập trỏ về mục khung; sửa tên/trọng số mục trên màn (API đã có); "buổi đã dạy chưa ghi sổ" ở
     Việc hôm nay (`tien_do_lop(kem_buoi=True)` có sẵn); ô "Đề xuất" của sổ đầu bài → tạo Yêu cầu (sau E3).
   - **1.5B** thay khối thi bằng tiến trình; **1.5C** xoá mã thi (HOÃN tới khi điểm kiểm tra V-h chạy thật).
   - **1.6** thuật ngữ "Môn học"/"phân môn", bỏ "Mọi …", guard thuật ngữ.
   - **Đ2** §58 đổi GV/TG một buổi · §59 khoá tháng chấm công · §60 tài liệu lớp trên R2 (+ nộp tệp) — cần D1 của anh.
   - **E4** Zoom (record tự gắn, HS xem record, thử "% đã xem") — cần Z1 của anh. **E5** tự đăng ký + hàng chờ xếp lớp
     (§67; BẪY: mọi câu ở `accounts/quen_mat_khau.py` phải lọc `purpose='reset'`). **§66** link phụ huynh sống (nếu E3 chưa làm).
   - **S1** sổ quyền một nguồn · **S2** một hàm màn chặn cho mọi trang khu · **S6** danh mục trang sinh menu ·
     **S7** graphify mỗi mốc gộp (chạy trong PowerShell) và ghi số vào PROGRESS.
   - Co sổ nợ ghi chéo (11 mục, `so_mien.json`); `common/management/commands/ve_erd.py` còn bảng `MIEN` riêng → đọc
     `so_mien.json`.
   - Rà giao diện bằng Chrome DevTools MCP theo TỪNG VAI (GV, TG, học vụ, biên tập — hai bộ đo hiện chỉ đi thẻ quản trị
     + học viên): mở từng màn hai khổ, soi ảnh, console, mạng.
5. **Việc của anh đang chờ** (bảng đầu `docs/VIEC_CUA_ANH.md`): C2-cloud (việc 0), N6, N4 (khi tôi báo), N7, K2 (4 câu hỏi
   TopHSA + NGÀY buổi xem lại), K1 (một khung chương trình thật), N3, A7, N5, T6, C1–C8…, Z1, D1.

## 4. Luật đang hiệu lực (không được quên)

- Chỉ làm trong `D:\pe_hsa`. Mọi commit lên **`erp`**; KHÔNG commit/đẩy `master` — anh gộp khi tôi báo.
- `.env` không bao giờ commit/in/sửa: `git diff --cached --name-only | grep -i "\.env$"` trước MỖI commit.
- Repo CÔNG KHAI: không bí mật, token, JWT, chìa link phụ huynh, mật khẩu tạm; không đưa PDF/DOCX của khách, giá, hợp
  đồng, email/tên khách, link bảng tính của khách vào repo (tệp khách trong `docs/` để untracked).
- Không gửi email/Zalo tới phụ huynh thật. Không ghi vào tài khoản/lớp thử nghiệm của TopHSA (42409, 42843–42850, lớp 7586).
- Neon = mock production = buổi TỔNG DUYỆT: ghi thử thoải mái, nhưng hạ tầng/bảo mật/phân quyền phải như thật.
- DDL chỉ cộng thêm; mục mới `-- ── §NN · TÊN ──` + dòng trong `kiem_luoc_do.py`; nới CHECK thì SỬA TẠI CHỖ (test cấm
  thêm lại ràng buộc cùng tên khác nội dung); vocab = CHECK; `bootstrap_schema` hai lần.
- Test ĐỎ trước trên mã cũ + đột biến (nền xanh, mỗi đột biến mã 1); đi đúng đường thật; thước báo oan cũng là lỗi.
- Không hardcode px (clamp/rem/vw/ch); tầng JS cũ chỉ co; mã mới đặt đúng miền, không ghi bảng miền khác.
- Tối đa 3 agent cục bộ (hạn mức tuần); việc nặng → phiên cloud.
- Việc cần anh → MỘT bảng lời thường ở đầu `docs/VIEC_CUA_ANH.md`.
- Mọi số báo ra phải tự đo (không mượn số của agent/phiên khác mà không ghi rõ); số hiệu năng chỉ sau A/B xen kẽ.
- Commit tiếng Việt, dòng cuối `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.
- Việc lớn → hỏi dồn theo vòng (grilling) trước khi làm; câu hỏi phải kèm số đúng.

## 5. Lệnh và công cụ

```bash
# máy chủ dev (Django --noreload: thêm tuyến mới thì tắt/bật lại)
cd backend && .venv/Scripts/python.exe manage.py runserver 9000 --noreload
cd frontend && npx next dev -p 3100            # pnpm có thể không có trong PATH của Git Bash

# lược đồ + test
cd backend && .venv/Scripts/python.exe manage.py bootstrap_schema     # hai lần; lượt 2 = 0/N
cd backend && .venv/Scripts/python.exe manage.py kiem_luoc_do
cd backend && .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider <mô-đun>   # TỪNG mô-đun, Neon ~1–4 phút/mô-đun

# e2e (tài khoản đọc từ .the/e2e.json)
cd frontend && E2E_GHI=1 npx playwright test -c e2e/playwright.config.ts <spec…> --reporter=line

# bộ đo giao diện — thẻ sống 30 phút, cấp lại ngay trước mỗi lượt
backend/.venv/Scripts/python.exe scripts/cap_the.py
backend/.venv/Scripts/python.exe scripts/cap_the.py --e2e --ra .the/tokens_hv.json   # KHÔNG quên --ra (đè thẻ admin)
node scripts/do_axe.mjs
cd scripts && node do_giao_dien.mjs --tu-kiem && node do_giao_dien.mjs [--json ra.json]

# thước cấu trúc (cổng pre-push chạy đủ: bash .githooks/pre-push < /dev/null)
python scripts/cau_truc.py --kiem ; node scripts/ban_do.mjs --kiem ; python scripts/tang_vai.py --kiem
```

**graphify** (hiểu cấu trúc mã): chạy trong **PowerShell** (Git Bash làm nó sập): `graphify update backend`,
`graphify update frontend/src`, `graphify update frontend/public/static/js`; tổng hợp `python scripts/tong_hop_graphify.py`
→ `docs/BAN_DO_MA.md`.

**Claude cloud** — tài khoản cloud riêng của anh (Pro, 100 USD credits tới 05/11/2026), đăng nhập ở `%USERPROFILE%\.claude-son`;
trình mở phiên `%USERPROFILE%\cloud-son.ps1` (ngoài repo, không commit). Quy trình:
1. Bản clone SẠCH (không `.env`): `git clone https://github.com/PCBoiz/PE_hsa <thư mục nháp>`; mỗi nhánh một worktree
   `git worktree add ../cloud_<nhánh> origin/<nhánh> -B <nhánh>` — phiên cloud clone đúng nhánh của thư mục.
2. Viết brief ra tệp .txt. Đầu brief: nhánh làm tiếp, gộp `origin/erp`, CSDL Postgres 16 cục bộ của máy cloud
   (`postgres://postgres:postgres@localhost:5432/pe_hsa`, bảng `lessons` trống), danh sách kiểm cuối, báo cáo
   `docs/cloud/BAO_CAO_*.md`, đẩy sau MỖI commit, không đẩy erp/master. KHÔNG dán bí mật hay DATABASE_URL thật.
3. Mở bằng cửa sổ riêng (`--cloud` đòi terminal thật):
   `Start-Process powershell -ArgumentList '-ExecutionPolicy','Bypass','-File',"$HOME\cloud-son.ps1",'-ViecFile',<brief>,'-ThuMuc',<worktree>,'-GhiRa',<log>`
   — log chứa `session_…`; tiêu đề phiên bị cắt = brief bị cắt ở dấu `"`; log báo 401 = việc 0.
4. Phiên cloud không hiện ở phiên cục bộ (khác tài khoản) → nhận kết quả qua nhánh; canh bằng vòng `git ls-remote` tìm
   tên tệp báo cáo CỤ THỂ (nhánh mới thừa hưởng báo cáo cũ từ erp → canh "có BAO_CAO bất kỳ" sẽ báo nhầm).
   Phiên có thể dừng giữa chừng không báo (E2/E3 25/09): quá ~1 giờ không commit mới → mở phiên nối tiếp.

## 6. Bẫy đã gặp (đừng mắc lại)

- Gộp nhánh cloud khi `D:\pe_hsa` chưa fetch lại → thiếu commit; `ban_do --kiem` bắt được qua "tuyến không ai gọi".
- Test lõi ở máy cloud đỏ ~70 cái vì bảng `lessons` trống — so tên với erp trên cùng máy trước khi kết luận.
- Neon dev có thể ĐI TRƯỚC mã erp (agent cục bộ đã bootstrap lược đồ của nhánh mình) → test đỏ "NOT NULL" giả.
- Trên dev, một lượt ghi tới Neon mất ~5 s → e2e chờ xác nhận ghi bằng `timeout: 20_000`.
- `getByLabel('Tháng')` khớp cả `aria-label` chứa "tháng" → dùng `{ exact: true }`.
- `next dev` tự ghi lại khối trong `frontend/AGENTS.md` → commit nó cùng việc, đừng hoàn nguyên.
- Tài khoản e2e phải có lớp thì trang Bài học mới đo được (quyền môn theo lớp).
- Python tạm: viết ra tệp rồi chạy; heredoc làm hỏng dấu `\`; tệp CRLF làm `sed`/so chuỗi không khớp → dùng Edit.
- Ruff trên cloud có thể dễ hơn máy dev (DTZ011 `date.today()` → `common.clock.local_today()`).

## 7. Nguồn tham khảo

**Nội bộ**: các tệp ở mục 1; `docs/BAN_DO_MA.md`, `docs/BAN_DO_VAI.md` (graphify + tầng vai); `docs/VAN_HANH.md`;
`ban_do/BAO_CAO.md`; sách/giáo trình của khách trong `docs/` (untracked — không commit).

**Bảng yêu cầu của khách** ("Bảng phân rã tính năng — Updated 24.9.2026") là Google Sheets riêng của TopHSA — link KHÔNG
để trong repo công khai; anh Sơn giữ, phiên mới hỏi anh nếu cần. `docs/NGHIEM_THU_TOPHSA.md` là bản đối chiếu theo từng dòng.

**Cách làm / thiết kế** (anh gửi 25/09 — dùng làm chuẩn tham khảo và luật chuyển động cho màn MỚI):
- Hỏi dồn trước việc lớn: https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md
- Quy trình phát triển với AI: https://claude.com/blog/the-ai-native-sdlc-playbook
- Thiết kế hệ thống: https://github.com/donnemartin/system-design-primer
- Sơ đồ kiến trúc: https://github.com/tt-a1i/archify · https://github.com/cathrynlavery/diagram-design
- Hiểu cấu trúc mã: https://github.com/Graphify-Labs/graphify
- Kiểm giao diện thật: https://github.com/ChromeDevTools/chrome-devtools-mcp
- Giao diện / chuyển động: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill · https://github.com/emilkowalski/skills ·
  https://uiverse.io/ · https://horizonx.so/ · https://shaders.com/ · https://contentcore.xyz/
- Vai agent: https://github.com/msitarzewski/agency-agents
