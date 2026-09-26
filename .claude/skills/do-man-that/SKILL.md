---
name: do-man-that
description: Mở một màn THẬT của pe_hsa trong trình duyệt đã đăng nhập rồi ĐO bằng số — dùng khi cần báo "giao diện đỡ rối hơn", "đã sửa xong màn X", "gọt chữ xong", khi so trước/sau một thay đổi giao diện, hoặc trước khi tick một dòng nghiệm thu. Bắt buộc trước mọi câu "xong" về giao diện (RULES §1, §2). Không dùng cho thay đổi thuần backend.
---

# Đo màn thật

Luật dự án: **mở màn thật, soi ảnh, rồi mới báo xong** (RULES §1) và **đo, đừng
suy** (§2). Kỹ năng này là đường đi ngắn nhất làm đúng cả hai.

## Khi nào

Mọi lúc sắp nói một câu về giao diện mà người nghe sẽ tin: "gọn hơn", "đã sửa",
"không còn lỗi". Cảm nhận không đếm được; bảng số thì có.

## Các bước

### 1 · Dọn máy trước khi đo

```bash
powershell -File scripts/don_may.ps1          # xem có gì mồ côi
powershell -File scripts/don_may.ps1 -Don     # dọn
```

Bỏ bước này thì mỗi lượt đo cộng thêm một bộ Chromium vào máy người khác. Máy anh
Sơn có 15,9 GB; trưa 26/09 nó đứng vì 22 tiến trình mồ côi.

### 2 · Cấp lại thẻ (thẻ sống 30 phút)

```bash
cd backend && .venv/Scripts/python.exe ../scripts/cap_the.py --vai "Học viên"  --ra ../.the/tokens_hv.json
cd backend && .venv/Scripts/python.exe ../scripts/cap_the.py --vai "Giảng viên" --ra ../.the/tokens_gv.json
cd backend && .venv/Scripts/python.exe ../scripts/cap_the.py                    --ra ../.the/tokens_ad.json
```

Thẻ hết hạn thì bộ đo rơi về màn đăng nhập và **vẫn in ra số** — số của trang
đăng nhập. Đây là cách dễ nhất để tự lừa mình.

### 3 · Đo

```bash
node scripts/do_mat_do_chu.mjs                 # chữ: số từ, ô số, câu dài
node scripts/do_giao_dien.mjs --tu-kiem        # tương phản, vùng chạm, tràn ngang
node scripts/do_axe.mjs                        # tiếp cận (phải 0 vi phạm)
```

Worktree khác cổng thì đặt môi trường: `PE_WEB=http://localhost:3500 PE_THE=D:/pe_hsa_wt/<tên>/.the`.

`--tu-kiem` bắt bộ đo phải ĐỎ được với một lỗi cố ý cài vào. Một bộ đo không đỏ
được là một bộ đo giả — `do_giao_dien.mjs` từng báo "0 vi phạm" suốt nhiều ngày
vì một dấu gạch chéo bị nuốt trong regex.

### 4 · So với chỉ tiêu, dán hai bảng cạnh nhau

Chỉ tiêu ở `docs/HUONG_GIAO_DIEN_2026-09-26.md` §5. Báo cáo phải có **bảng trước
và bảng sau**, không được thay bằng chữ "đã gọn hơn".

### 5 · Dọn lại

```bash
powershell -File scripts/don_may.ps1 -Don
```

## Cổng kiểm

- `do_axe.mjs` 0 vi phạm · `do_giao_dien.mjs` 0 luật vi phạm
- Spec e2e sẵn có còn xanh — chúng tìm nút theo TÊN, nên đổi tên nút thì sửa spec
  trong cùng lượt
- Đã soi ảnh ở hai khổ 1440 và 390, sáng và tối

## Chỗ nới (đừng sửa quy trình, hãy thêm dữ liệu)

- Thêm màn cần đo: thêm một dòng vào `MAN` trong `scripts/do_mat_do_chu.mjs`
- Thêm vai: thêm một dòng vào `THE_VAI` trong `scripts/lib/phien_do.mjs`

## Bẫy đã có người vấp

- **`next start` cũ giữ cổng** làm mọi tuyến mới trả 500, trông hệt như mã mới
  hỏng. Trước khi nghi mã, xem ai giữ cổng và nó chạy `start` hay `dev`.
- **Django `--noreload` không nạp tuyến mới** — thêm tuyến thì tắt/bật lại.
- **Đừng tự gọi `chromium.launch()`** trong bộ đo mới. Gọi `chay()` của
  `scripts/lib/phien_do.mjs`: nó đóng trình duyệt cả khi lỗi lẫn khi bị Ctrl-C.
  Sáu bộ đo cũ quên `finally`, và đó là nguyên nhân máy sập.
