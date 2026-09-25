# CLAUDE.md — làm việc trên PE_hsa (TopHSA ERP)

Next.js (Vercel) → Django + SQL thuần (Render) → Postgres (Neon). Viết, commit, trả lời bằng tiếng Việt.

## Nhánh
- Làm trên `erp` (Preview Vercel tự dựng) hoặc nhánh con của nó. `master` = production — CHỈ chủ dự án gộp.
- GitHub chỉ có ĐÚNG ba nhánh: `master`, `erp`, `erp-DB` (nhánh CSDL của Nhân — không đụng). Nhánh agent để CỤC BỘ
  (worktree), lead gộp vào `erp` rồi mới đẩy; không đẩy nhánh nào khác lên GitHub.

## Đọc trước (theo thứ tự)
1. `docs/KE_HOACH_TOPHSA_THU_NGHIEM_2026-09-24.md` — kế hoạch v2, bảng theo dõi việc.
2. `docs/THIET_KE_HE_THONG.md` — vai, miền (§4), luật thiết kế (§8).
3. `docs/CAU_TRUC_MA.md` — tệp nào thuộc miền nào, "Đặt mã mới ở đâu", sổ nợ ghi chéo (tự sinh).
4. `docs/CAU_TRUC_DU_LIEU.md` — bảng, cột, khoá ngoài, CHECK theo miền (tự sinh từ `backend/sql`).
5. `docs/VAN_HANH.md` — deploy, sổ lược đồ, cổng pre-push.
6. `docs/NGHIEM_THU_TOPHSA.md` (dòng khách nghiệm thu) · `docs/VIEC_CUA_ANH.md` (việc chờ chủ dự án).
7. `RULES.md` — luật bắt buộc, kèm lý do từng luật.

## Luật cứng
- DDL CHỈ cộng thêm (`IF NOT EXISTS`, `DROP CONSTRAINT IF EXISTS` rồi `ADD`), mục mới `-- ── §NN · Tên (ngày) ──`
  ở cuối `backend/sql/legacy_schema.sql` + dòng kiểm trong `kiem_luoc_do.py`. Không `DO $$`, không `SET`.
- Test ĐỎ trước (trên mã cũ) rồi mới sửa; báo số đột biến bị giết. Test backend chạy trong giao dịch cuộn lại,
  chỉ đếm dữ liệu của chính nó.
- Không đọc / in / commit `.env`, khoá, mật khẩu.
- Không hardcode px trong giao diện: clamp / rem / vw / ch, token màu có sẵn.
- Tầng JS cũ `frontend/public/static/js` chỉ được CO (trần ở `e2e/unit/chot-ham-tang-cu.test.mjs`); chạm mục
  học viên nào thì dời sang React.
- Không ghi vào tài khoản người dùng thử nghiệm của TopHSA; e2e ghi dùng tài khoản riêng + `E2E_GHI=1`.
  Không gửi thư / Zalo tới phụ huynh thật.
- Mã mới đặt ĐÚNG miền (`scripts/so_mien.json`); không INSERT/UPDATE/DELETE bảng miền khác — gọi hàm dịch vụ.
  Sổ nợ ghi chéo chỉ được co.
- Chữ trên giao diện: tiếng Việt của người dùng, không mã kỹ thuật (RULES §10).

## Lệnh
```bash
cd backend && python manage.py bootstrap_schema          # chạy HAI lần: lượt 2 phải "0/N mục chạy"
cd backend && python manage.py kiem_luoc_do              # mọi dòng ✓
cd backend && python -m pytest teaching/tests_lich.py -q # pytest TỪNG mô-đun (toàn bộ ~54 phút)
cd backend && python -m ruff check . && python manage.py check
cd frontend && npx --yes pnpm@11.12.0 e2e                # E2E_GHI=1 cho luồng có ghi
python scripts/cau_truc.py [--kiem]                      # sinh / kiểm docs CAU_TRUC_* + ghi chéo miền
node scripts/ban_do.mjs --kiem && python scripts/tang_vai.py --kiem
bash .githooks/pre-push < /dev/null                      # cổng kiểm đủ (bật: git config core.hooksPath .githooks)
```

## Cách làm việc
- Việc lớn (nhiều tệp, lược đồ, quyền, luồng mới) → HỎI DỒN theo vòng (grilling) cho tới khi hết chỗ mơ hồ,
  rồi mới làm. Việc nhỏ, rõ → làm luôn.
- Mở màn thật trong trình duyệt đã đăng nhập, xem ảnh chụp, trước khi báo xong (RULES §1). Đo, đừng suy (§2).
- Ghi `PROGRESS.md` sau mỗi việc; soát theo `REVIEW.md` trước khi đẩy.
