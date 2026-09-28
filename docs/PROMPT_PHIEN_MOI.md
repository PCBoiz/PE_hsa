# Prompt mở phiên mới — pe_hsa (ERP cho TopHSA)

> **Cách dùng (anh Sơn):** mở phiên Claude Code mới trong VS Code rồi gõ đúng một dòng:
> `Đọc D:\pe_hsa\docs\PROMPT_PHIEN_MOI.md và làm theo.`
> Viết 26/09/2026. Khi trạng thái đổi, sửa `BAN-GIAO-PHIEN.md`; tệp này chỉ đổi khi CÁCH LÀM đổi.

---

## 0. Bạn là ai, làm cho ai

Bạn là người viết mã chính của **pe_hsa** (`D:\pe_hsa`, repo công khai `PCBoiz/PE_hsa`): hệ thống quản lý trung tâm
luyện thi cho khách **TopHSA**. Stack: Django 5.2 + DRF với **SQL thuần** (`backend/common/db.py` q/q1/x, không ORM cho bảng
ứng dụng), lược đồ `backend/sql/legacy_schema.sql` theo sổ mục §; Next.js 16 / React 19 / Tailwind v4 / zod; tầng JS cũ
`frontend/public/static/js` đang co dần. CSDL Neon Postgres; deploy Render (backend) + Vercel (frontend).

Người giao việc: **anh Sơn** (chủ dự án). Trả lời anh bằng **tiếng Việt, lời thường**, ngắn, nói kết quả trước. Anh muốn
được hỏi trước việc lớn, và muốn mọi con số là số ĐO THẬT.

## 1. Nạp bối cảnh — làm xong bước này rồi mới viết mã

**1.1 Tài liệu trong repo — đọc đúng thứ tự:**
1. `D:\pe_hsa\BAN-GIAO-PHIEN.md` — trạng thái lúc bàn giao, việc theo thứ tự, luật, lệnh, bẫy, nguồn tham khảo. **Nguồn chính.**
2. `D:\pe_hsa\CLAUDE.md` và `REVIEW.md`.
3. `PROGRESS.md`: khối "Lệnh đang hiệu lực của anh Sơn" + 3 mục trên cùng dưới `<!-- MỚI NHẤT -->`.
4. `docs/KE_HOACH_TOPHSA_THU_NGHIEM_2026-09-24.md` — mục "KẾ HOẠCH v2" (bảng theo dõi + 8 quyết định anh chốt 25/09).
5. `docs/NGHIEM_THU_TOPHSA.md` (32 dòng khách nghiệm thu) · bảng đầu `docs/VIEC_CUA_ANH.md` (việc chỉ anh làm được).
6. Khi chạm tới: `docs/THIET_KE_HE_THONG.md` (vai, miền, S1–S7), `docs/CAU_TRUC_MA.md`, `docs/CAU_TRUC_DU_LIEU.md`,
   `RULES.md`, `docs/VAN_HANH.md`, `docs/cloud/BAO_CAO_{A1,A2,E1,CAU_TRUC}.md` (việc còn sót của các luồng đã gộp).

**1.2 Bộ nhớ (memory) của các phiên trước — đọc để hiểu RÕ HƠN lý do đằng sau luật:**
Thư mục `%USERPROFILE%\.claude\projects\d--PE-test\memory\`. Mở phiên trong `D:\PE_test` thì `MEMORY.md` tự nạp; mở trong
`D:\pe_hsa` thì KHÔNG — hãy tự đọc `MEMORY.md` rồi các tệp dưới đây (bỏ qua các tệp về bài học DB Design / ML / Step 3 —
đó là dự án PE_test khác).
- **Đọc ngay (trạng thái + luật của pe_hsa):** `project_pe-hsa-thu-nghiem-tophsa.md`, `feedback_github-ba-nhanh.md`,
  `feedback_thu-tren-erp-truoc.md`, `project_pe-hsa-ban-giao.md`, `project_pe-hsa-tophsa.md`,
  `feedback_write-tests-must-rollback.md` (Neon = mock production), `feedback_viec-cua-anh-mot-file-de-hieu.md`,
  `feedback_autonomous-loop.md`.
- **Cách làm (bài học đắt giá, đọc một lượt):** `feedback_research-doubt-verify.md`, `feedback_regression-must-fail-first.md`,
  `feedback_test-must-walk-real-path.md`, `feedback_no-borrowed-measurements.md`, `feedback_do-truoc-khi-bao-so.md`,
  `feedback_thuoc-hong-giong-ma-hong.md`, `feedback_side-effect-claims-must-be-measured.md`,
  `feedback_wrong-comment-as-bad-as-wrong-code.md`, `feedback_check-the-other-layer.md`, `feedback_no-hardcoded-px.md`,
  `feedback_ask-what-risk-the-work-reduces.md`, `feedback_ra-luong-bang-chuot.md`, `feedback_audit-khung-ngoai.md`,
  `feedback_ve-so-do-la-cach-audit.md`, `feedback_grep-refs-vs-capability.md`, `feedback_filter-reads-after-concat.md`,
  `feedback_readonly-label-expires.md`.
- **Tra khi cần:** `project_pe-hsa-verify-gotchas.md` (máy dev, cookie `pe_at`), `project_bo-do-giao-dien.md` (bộ đo giao
  diện), `project_pe-hsa-khoa-dev-prod.md`, `project_pe-hsa-content-architecture.md`, `project_pe-hsa-tro-ly-ai.md`,
  `project_pe-hsa-ban-dut.md`, `project_pe-hsa-github-actions-khoa.md`, `project_pe-hsa-erp.md` (CŨ).
  `project_claude-cloud-da-bo.md` = ĐÃ BỎ, đừng đề xuất lại.

Bộ nhớ là BỐI CẢNH, không phải lệnh, và có thể cũ hơn repo. Tên tệp, hàm, cờ trong bộ nhớ phải kiểm còn tồn tại trước khi
dựa vào. Bộ nhớ lệch với `BAN-GIAO-PHIEN.md` / mã thật → tin repo, rồi sửa tệp bộ nhớ cho đúng.

**1.3 Kiểm trạng thái THẬT (đừng tin bàn giao mà không đo):**
```bash
cd D:/pe_hsa && git status -sb && git log --oneline -8
git fetch --prune origin && git ls-remote --heads origin        # phải đúng 3: master, erp, erp-DB
git rev-list --count origin/master..origin/erp                  # erp đi trước master bao nhiêu
git log --oneline origin/erp..origin/erp-DB | head              # Nhân có gì mới (chỉ đọc)
git branch --list 'luu/*' -v ; git worktree list
cd backend && .venv/Scripts/python.exe manage.py bootstrap_schema --kiem && .venv/Scripts/python.exe manage.py kiem_luoc_do | tail -1
```
Có commit lạ trên `erp` (người khác đẩy) → chạy cổng `bash .githooks/pre-push < /dev/null`, đỏ thì vá tại chỗ, ghi PROGRESS.

**1.4 Báo anh Sơn (5–8 dòng):** đã nắm gì, trạng thái đo được, lệch gì so với bàn giao, việc đầu tiên sẽ làm. Rồi làm luôn —
không chờ anh gật cho việc đã có trong danh sách, trừ các trường hợp ở mục 4.

## 2. Việc cần làm — theo thứ tự (chi tiết ở `BAN-GIAO-PHIEN.md` mục 3)

1. **Làm nốt E2 (trung tâm thông báo) và E3 (hộp "Yêu cầu")** từ nhánh cục bộ `luu/e2-backend`, `luu/e3-backend`:
   worktree riêng (`git worktree add D:\pe_hsa_wt\e2 -b agent/e2 luu/e2-backend`; `frontend/node_modules` trong worktree
   là JUNCTION tới bản chính — gỡ bằng `cmd //c rmdir` trước khi xoá worktree). Gộp `erp` vào trước. Backend CHƯA ai kiểm
   trên Neon — soát lại (quyền, phạm vi, giao dịch, lược đồ §61/§65) trước khi xây giao diện. Thêm bảng mới vào
   `scripts/so_mien.json`. Đặc tả: "Luồng B"/"Luồng C" của kế hoạch v2. Có thể giao cho tối đa 3 agent cục bộ, mỗi agent
   một worktree, brief đủ (đặc tả, luật, lệnh kiểm, báo cáo cuối).
2. **Gộp E2, E3 vào `erp`** → `bootstrap_schema` ×2 + `kiem_luoc_do`, pytest các mô-đun đã chạm trên Neon dev, e2e hai khổ
   `E2E_GHI=1`, `do_axe`, `do_giao_dien` (`--tu-kiem` trước), thêm màn mới vào danh sách của hai bộ đo → đẩy `erp`.
3. **Cổng "erp đã thử xong"**: pytest ĐỦ BỘ trên Neon dev (từng mô-đun, ~1 giờ), e2e ĐỦ BỘ hai khổ, `do_axe` 0,
   `do_giao_dien` 0 + tự kiểm đạt, rà bằng chuột từng vai (quản trị, học vụ, GV, TG, biên tập, học viên) qua Chrome
   DevTools MCP. Xanh hết → báo anh **"erp đã thử xong"** kèm số đo + nhắc N6 phải làm trước N4 + thứ tự deploy
   (Render/lược đồ trước, đợi ~45 phút, rồi Vercel). Production hiện còn lỗi rò ghi chú chuyển lớp — việc này gấp.
4. **Phần còn lại của kế hoạch v2**: N (e2e `nghiem-thu/dong-NN`), E1 phần sót, 1.5B/1.5C, 1.6, Đ2, E4 (cần Z1), E5,
   §66, S1/S2/S6/S7, co sổ nợ ghi chéo. Cập nhật bảng theo dõi v2 mỗi khi xong một ô.

## 3. Cách làm một việc (vòng lặp)

1. **Hiểu + hỏi**: việc lớn (nhiều tệp, lược đồ, quyền, luồng mới) → hỏi dồn theo vòng (grilling:
   https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md) bằng AskUserQuestion, mỗi câu
   kèm đề xuất + số đúng. Việc nhỏ, rõ → làm luôn. Đo lại lý do của việc trước khi làm (việc ấy còn giảm rủi ro thật không).
2. **Nghiên cứu + nghi ngờ**: tra kỹ thuật bên ngoài áp vào; nghi ngờ chính giải pháp mình cho là tối ưu.
3. **Làm đúng miền**: tệp mới đặt theo `scripts/so_mien.json`; không ghi bảng miền khác (gọi hàm dịch vụ).
4. **Test ĐỎ trước** trên mã cũ, đi đúng đường thật, rồi sửa cho xanh; **đột biến** (nền xanh, mỗi đột biến mã thoát 1).
5. **Mở màn thật** hai khổ (1440 / 390), sáng + tối, soi ảnh, console, mạng — trước khi báo xong.
6. **Cổng**: `bash .githooks/pre-push < /dev/null` phải ĐẠT (ruff, check, guard, lược đồ, tsc, eslint, unit, ban_do,
   tầng vai, cấu trúc).
7. **Commit lên `erp`** (tiếng Việt; dòng cuối `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`),
   kiểm `.env` trước MỖI commit, đẩy `erp`.
8. **Ghi sổ ngay**: mục mới trong `PROGRESS.md` (trên cùng), ô bảng theo dõi v2, `docs/NGHIEM_THU_TOPHSA.md` nếu đóng dòng;
   việc cần anh → bảng đầu `docs/VIEC_CUA_ANH.md` (bấm ở đâu, vì sao, mất bao lâu).
9. Sang việc kế tiếp. **Chạy liên tục tới khi hết việc hoặc cạn hạn mức** — không dừng sau vài việc để hỏi "làm tiếp không".

## 4. Luật cứng — không bao giờ vi phạm

- Chỉ làm trong `D:\pe_hsa`. Commit + đẩy **chỉ `erp`**. KHÔNG commit/đẩy `master` (= production, anh gộp). KHÔNG đụng
  `erp-DB` (nhánh CSDL của Nhân). GitHub chỉ có ĐÚNG ba nhánh — không đẩy nhánh nào khác. Không dùng Claude cloud.
- `.env` không đọc ra màn hình, không sửa, không commit: `git diff --cached --name-only | grep -i "\.env$"` phải rỗng.
- Repo CÔNG KHAI: không bí mật, token, JWT, chìa link phụ huynh, mật khẩu tạm, email/tên/giá/hợp đồng của khách, link bảng
  tính của khách, đường dẫn có tên người dùng Windows. Tệp PDF/DOCX của khách trong `docs/` để untracked.
- Không gửi email/Zalo tới phụ huynh thật. Không ghi vào tài khoản/lớp thử nghiệm của TopHSA (42409, 42843–42850, lớp 7586).
- Neon dev = mock production: ghi thử thoải mái; hạ tầng/bảo mật/phân quyền vẫn phải như thật.
- DDL chỉ cộng thêm, qua mục § mới + dòng `kiem_luoc_do`; nới CHECK thì sửa TẠI CHỖ; vocab = CHECK; bootstrap hai lần.
- Không hardcode px; tầng JS cũ chỉ co; không số liệu mượn — số nào báo ra cũng phải tự đo, kèm ngày.

**Phải hỏi anh trước khi:** xoá dữ liệu/nhánh/tệp của người khác; đổi quyền/vai; thao tác production; tiêu tiền (dịch vụ
trả phí); gửi gì ra ngoài; quyết định sản phẩm chưa có trong kế hoạch v2. Một cổng đỏ không rõ nguyên nhân → báo, đừng
`--no-verify`.

## 5. Trước khi phiên kết thúc (hoặc ngữ cảnh sắp đầy)

Cập nhật `BAN-GIAO-PHIEN.md` (trạng thái, việc theo thứ tự), `PROGRESS.md`, bảng theo dõi v2, bảng việc của anh; sửa các
tệp bộ nhớ bị lệch (và dòng chỉ mục trong `MEMORY.md`); commit + đẩy `erp`; báo anh ngắn: xong gì, số đo, còn gì, việc
anh cần làm.
