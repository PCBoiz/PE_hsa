---
name: giao-viec-agent
description: Giao một việc cho agent phụ trong pe_hsa — dùng khi anh Sơn bảo "gọi agent hỗ trợ", khi một việc đủ lớn để chạy song song, hoặc khi cần một agent soát chất lượng việc của agent khác. Gồm cách viết brief, dựng worktree, chia cổng, và DỌN sau khi xong. Không dùng cho việc nhỏ làm thẳng cũng được — mỗi agent tốn token và tốn RAM máy anh.
---

# Giao việc cho agent phụ

## Trần cứng: 2 agent

Anh Sơn 26/09, sau khi một agent chết vì hết hạn mức: *"TỐI ĐA là 2 agents thôi
(Đốt tokens usage nhanh quá), có thể tìm cách giảm usage tokens lại để công việc
diễn ra lâu hơn"*. Trần này không co giãn.

Mô hình anh muốn: **một agent làm, một agent soát việc của agent ấy** — người tìm
khác người xác minh (xem `soat-bao-mat`).

## Trước khi gọi: hỏi đã đáng chưa

Mỗi agent phụ mở một worktree (13–240 MB đĩa), thường kèm một Django và một Next
riêng (~300 MB RAM). Máy anh Sơn có 15,9 GB và đã có lúc đứng vì chuyện này.

Việc nhỏ, rõ, một hai tệp: làm thẳng. Việc lớn, nhiều tệp, chạy được song song:
gọi agent.

## Dựng chỗ làm

```bash
git worktree add D:/pe_hsa_wt/<tên> -b agent/<tên>
mkdir D:/pe_hsa_wt/<tên>/.the
cp D:/pe_hsa/.the/e2e.json D:/pe_hsa/.the/audit_tk.json D:/pe_hsa_wt/<tên>/.the/
```

Mỗi agent MỘT cặp cổng riêng, không dùng chung: Django 9400/9500/9600, Next
3500/3600/3700. Hai agent cùng cổng thì cái sau không bind được và chạy vô ích —
đã xảy ra ngày 26/09, bốn tiến trình cùng đòi cổng 9300.

## Brief phải có đủ bảy phần

1. **Chỗ làm** — worktree, nhánh, cổng Django/Next, đường dẫn Python của repo.
2. **Nguồn việc** — ai yêu cầu, ngày nào, nguyên văn câu của họ. Agent cần biết
   mình đang phục vụ ai, không chỉ biết phải gõ gì.
3. **Việc**, đánh số, mỗi mục kèm *đo trước rồi hãy sửa*.
4. **Luật** — test ĐỎ trước, đột biến phải giết được, chữ tiếng Việt, không
   hardcode px, đúng miền (`scripts/so_mien.json`), không đẩy nhánh lên GitHub.
5. **Bẫy đã có người vấp** — cổng bị tiến trình cũ giữ, `--noreload` không nạp
   tuyến mới, thẻ sống 30 phút.
6. **Báo cáo** — ghi ra `docs/agent/BAO_CAO_<việc>.md`: mỗi mục đã làm gì, bằng
   chứng `tệp:dòng`, số tự đo kèm ngày, việc còn sót, câu hỏi cần anh Sơn quyết.
7. **Dọn** — xem dưới.

## Ranh giới không được vượt

- Nhánh agent để **CỤC BỘ**. Chỉ lead gộp vào `erp` rồi mới đẩy. GitHub chỉ có
  đúng ba nhánh: `master`, `erp`, `erp-DB`.
- Không commit `.env`, khoá, mật khẩu. Kiểm
  `git diff --cached --name-only | grep -i "\.env$"` rỗng trước MỖI commit.
- Không đụng `master` (production) hay `erp-DB` (của Nhân).
- Thư và tin nhắn chỉ gửi tới địa chỉ thử.

## Ba cái vướng riêng của worktree (agent E3 báo 26/09/2026)

1. **`next dev` mặc định KHÔNG chạy trong worktree.** `frontend/node_modules` là
   junction trỏ ra ngoài gốc, Turbopack coi đó là lỗi và tắt máy chủ:
   *"Symlink [project]/node_modules is invalid, it points out of the filesystem
   root"*. Dùng **`next dev --webpack -p <cổng>`**. Mọi agent dùng worktree đều
   vấp chỗ này.
2. **Worktree không có `.venv` riêng** — nó dùng venv của repo chính. Gọi python
   bằng đường dẫn tuyệt đối `D:/pe_hsa/backend/.venv/Scripts/python.exe`.
   `scripts/nap_lai_be.ps1` nay tự tìm sang repo chính khi không thấy venv tại chỗ.
3. **Ảnh chụp mang tên học viên của lớp mẫu** — để trong thư mục nháp của phiên,
   ĐỪNG commit. Báo cáo chỉ ghi tên tệp và nói soi thấy gì.


## Dọn sau khi xong — phần hay bị quên nhất

```bash
powershell -File scripts/don_may.ps1 -Don     # tắt Django/Next của agent
git worktree remove D:/pe_hsa_wt/<tên>        # sau khi đã gộp
```

Ngày 26/09 có 14 worktree trên đĩa (1,2 GB), tám trong số đó đã gộp xong từ lâu;
và server của một agent đã dừng vẫn chạy suốt buổi sáng.

## Khi agent dừng giữa chừng

Đừng coi việc là xong vì agent im. Kiểm trước:

```bash
git -C D:/pe_hsa_wt/<tên> status --short      # có gì chưa commit
git log --oneline erp..agent/<tên>            # có commit nào chưa gộp
```

Ngày 26/09 cả hai agent dừng không báo; agent `gop-y` để lại bảy tệp đã sửa mà
chưa commit — suýt mất nếu dọn worktree trước khi xem.
