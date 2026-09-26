# Sổ nguồn ngoài — anh Sơn gửi gì, lấy được gì, bỏ gì

Anh Sơn 26/09: *"tôi còn gửi rất nhiều nguồn khác nữa… tổng hợp luôn vào để sau
còn nhớ mà áp dụng"*. Tệp này là **sổ sống**: mỗi lần anh gửi nguồn mới thì thêm
một dòng vào bảng, và khi nào áp được thì điền cột "đã thành gì".

Nguyên tắc: một nguồn chỉ đáng lấy khi nó giải một vấn đề ĐANG CÓ ở đây, đo
được. Lấy vì nó hay là cách nhanh nhất để dựng thêm thứ phải nuôi. Cột cuối nói
thẳng chỗ nào **chưa áp** và vì sao — để lần sau khỏi đọc lại từ đầu.

## Bảng tổng hợp

| # | Nguồn | Anh gửi | Đã thành gì ở đây | Trạng thái |
|---|---|---|---|---|
| 1 | [grilling (mattpocock)](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md) | 24/09 | Luật "việc lớn thì hỏi dồn theo vòng cho tới khi hết mơ hồ" — `CLAUDE.md`, `RULES.md` bước 1 | **Đã áp** |
| 2 | [ai-native-sdlc-playbook](https://claude.com/blog/the-ai-native-sdlc-playbook) | 24/09 | Khung 6 bước trong `RULES.md` (hiểu+hỏi → nghiên cứu+nghi ngờ → làm đúng miền → đo → soát → ghi) | **Đã áp** |
| 3 | [system-design-primer](https://github.com/donnemartin/system-design-primer) | 24/09 | `docs/THIET_KE_HE_THONG.md` — vai, miền §4, luật thiết kế §8 | **Đã áp** |
| 4 | [graphify](https://github.com/Graphify-Labs/graphify) | 24/09 | `docs/BAN_DO_MA.md` (133 tệp backend, 445 cạnh) + `scripts/tong_hop_graphify.py`; đẻ tiếp ra `scripts/ban_do.mjs` (477 nút / 1.586 cạnh) | **Đã áp** |
| 5 | [archify](https://github.com/tt-a1i/archify) | 24/09 | Ý "sơ đồ kiến trúc sinh từ mã, không vẽ tay" — nằm trong `ban_do.mjs` và `cau_truc.py` | **Đã áp (phần ý)** |
| 6 | [diagram-design](https://github.com/cathrynlavery/diagram-design) | 24/09 | Luật vẽ sơ đồ: lưới 4px, nối vuông góc bo r=8, nhãn có nền che, trần 9 nút / 12 mũi tên mỗi hình, màu theo VAI, SVG có `role="img"` + `<title>` + `<desc>` | **Đã áp** |
| 7 | [chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | 24/09 | `scripts/do_hieu_nang.mjs` — trước đó chưa đo hiệu năng lần nào | **Đã áp** |
| 8 | [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 24/09 | Thứ tự ưu tiên ①–⑦ của `scripts/do_giao_dien.mjs`: tương phản → vùng chạm → tràn ngang → lỗi JS → chữ bị che → sàn cỡ chữ → lời gọi ghi lọt ra | **Đã áp** |
| 9 | [emilkowalski/skills](https://github.com/emilkowalski/skills) | 24/09 | — | **Chưa** — chuyển động; xem ghi chú dưới |
| 10 | [uiverse.io](https://uiverse.io/) | 24/09 | — | **Chưa** — thư viện thành phần CSS |
| 11 | [horizonx.so](https://horizonx.so/) | 24/09 | — | **Chưa** |
| 12 | [shaders.com](https://shaders.com/) | 24/09 | — | **Chưa** — nền shader |
| 13 | [contentcore.xyz](https://contentcore.xyz/) | 24/09 | — | **Chưa** |
| 14 | [agency-agents](https://github.com/msitarzewski/agency-agents) | 24/09 | Ý "mỗi agent một vai rõ" → `.claude/skills/giao-viec-agent/SKILL.md` | **Đã áp (phần ý)** |
| 15 | [jev-ultrafast](https://github.com/browser-use/jev-ultrafast) | 26/09 | `scripts/lib/phien_do.mjs` — ba kỹ thuật, chi tiết §1 | **Đã áp** |
| 16 | [security-audit-skill](https://github.com/cloudflare/security-audit-skill) | 26/09 | `scripts/quet_bi_mat.py` + bước f8 pre-push + `.claude/skills/soat-bao-mat/` | **Đã áp** |
| 17 | [LightRAG](https://github.com/HKUDS/LightRAG) | 26/09 | — | **Chưa dựng có chủ ý** — lý do §3 |
| 18 | SOLID cho Agent Skills | 26/09 | `.claude/skills/README.md` + ba kỹ năng | **Đã áp** |

---

## 1 · browser-use/jev-ultrafast — LẤY, và đúng lúc

**Nguồn giải quyết gì**: tự động hoá trình duyệt chậm và tốn. Bên ấy hạ số lời
gọi giao thức trình duyệt từ **1.092 xuống 101** cho cùng một việc, bằng cách
gom quyết định, đọc trạng thái có cấu trúc thay vì chụp ảnh, và chờ theo dấu
hiệu với trần thời gian.

**Vấn đề đang có ở đây**: trưa 26/09 máy anh Sơn đứng — 11 Chromium giữ 788 MB
cho một tab trống, 22 tiến trình Node/Python mồ côi. Gốc rễ: 8 trên 9 bộ đo
trong `scripts/` mở trình duyệt mà không có `finally`.

**Đã lấy ba kỹ thuật**, đặt ở `scripts/lib/phien_do.mjs`:

| Kỹ thuật bên ấy | Thành gì ở đây |
|---|---|
| Tái dùng thay vì mở mới | Một trình duyệt cho cả lượt, mỗi vai một trang dùng lại (cũ: 4 ngữ cảnh + 4 trang cho 4 màn) |
| Không chụp ảnh khi không cần | Ảnh tắt mặc định, bật bằng `--anh` |
| Chờ theo dấu hiệu, có trần | Chờ `main` có chữ và chiều cao thôi đổi, trần 4 s (cũ: ngủ cứng 6 s mỗi màn) |

**Đo sau khi áp**: 5 màn trong **17,8 s**, Chromium còn sót **0** — kể cả khi cố
tình trỏ bộ đo vào một cổng chết.

**Không lấy**: phần lõi của họ — mô hình chọn thao tác và phần tử trong một vòng
mạng. Bộ đo ở đây không cần agent điều khiển trình duyệt; nó biết trước phải mở
màn nào và đếm gì.

---

## 2 · cloudflare/security-audit-skill — LẤY hai nguyên tắc, bỏ sáu pha

**Nguồn giải quyết gì**: biến agent thành người soát bảo mật, qua sáu pha
(trinh sát → săn theo sổ bao phủ → xác minh → kết quả có cấu trúc → kiểm chéo →
báo cáo), với bộ xác thực JSON bằng Node và hơn 12 nhóm tấn công.

**Đã lấy hai nguyên tắc**, đặt ở `.claude/skills/soat-bao-mat/SKILL.md`:

1. **Người tìm khác người xác minh.** Trùng khít với mô hình anh Sơn đang yêu
   cầu: một agent làm, một agent soát. Một mình thì đổi vai có ý thức — viết
   phát hiện ra giấy rồi quay lại cố chứng minh nó sai.
2. **Không có vết nguồn thì chưa phải phát hiện.** Mỗi mục phải có `tệp:dòng`,
   đường đi từ đầu vào tới chỗ nguy hiểm, và một kết quả quan sát được. "Có vẻ
   thiếu kiểm tra" là câu hỏi, không phải phát hiện. Đây đúng là RULES §2 của
   dự án, nói bằng chữ khác.

**Thành sản phẩm**: `scripts/quet_bi_mat.py` + bước **f8** của `pre-push`. Repo
này CÔNG KHAI, mà 13 bước trước đó không bước nào đọc nội dung tệp sắp đẩy.

Bản đầu kêu oan cả **7 chỗ** (`user:password@`, `u:matkhau@`,
`postgres:tam@localhost` — toàn mật khẩu mẫu). Siết lại: **0 báo oan trên 698
tệp**, vẫn bắt đủ 4 loại bí mật thật trên tệp thử. Một cổng kêu oan là một cổng
sắp bị tắt đi.

**Tìm được thật**: `PROGRESS.md` trên GitHub — cả `erp` lẫn `master` — mang
đường dẫn `C:/Users/<tên tài khoản>/…` ở hai chỗ. Không phải khoá, nhưng RULES
§10 cấm.

**Không lấy**: sáu pha đầy đủ và bộ xác thực JSON. Quy mô ấy hợp với một tổ chức
soát mã của người lạ. Ở đây phần đắt nhất là quét bí mật và bốn câu hỏi về xác
thực / phân quyền / cách ly dữ liệu / cửa mở — đã nằm trong kỹ năng.

---

## 3 · HKUDS/LightRAG — ĐỌC, và CHƯA dựng

**Nguồn giải quyết gì**: RAG dựa trên đồ thị tri thức. Trích thực thể và quan hệ
từ tài liệu, truy hồi hai tầng (cục bộ theo thực thể, toàn cục theo chủ đề), cập
nhật tăng dần thay vì lập chỉ mục lại. Rẻ và nhanh hơn GraphRAG vì bỏ phần báo
cáo cộng đồng.

**Vấn đề nó nhắm tới có ở đây không**: có một nửa. Tài liệu dự án đã **19.019
dòng** (`PROGRESS.md` một mình 9.500), và mỗi phiên mới đều tốn token đọc lại —
đúng điều anh Sơn muốn giảm.

**Vì sao vẫn chưa dựng**:

- **Phần MÃ NGUỒN đã có đồ thị tốt hơn.** `scripts/ban_do.mjs` dựng **477 nút,
  1.586 cạnh** (tuyến → view → quyền → bảng, khoá ngoại, cầu sang JS cũ) từ cây
  cú pháp — **tất định và đúng**. Đồ thị của LightRAG do mô hình trích ra, nên
  có thể sai và không ai biết nó sai. Thay một thứ đúng bằng một thứ có thể sai
  là đi lùi.
- **Chỉ mục cũ đi nhanh hơn ta lập lại.** Mã ở đây đổi hàng ngày; lập chỉ mục
  lại cần gọi mô hình cho từng tài liệu, tức đúng khoản token anh Sơn muốn tiết
  kiệm.
- **Thêm một hạ tầng phải nuôi**: kho vector, khoá API, một chỗ nữa để hỏng lúc
  deploy.

**Điều kiện dựng lại** (viết ra để lần sau khỏi cãi nhau bằng cảm tính): khi
người trong nhóm phải tra cứu chéo tài liệu nhiều lần mỗi ngày mà `grep` và
`BAN-GIAO-PHIEN.md` không đủ, **hoặc** khi tài liệu vượt chừng 40.000 dòng.
Lúc ấy Postgres đã có sẵn (Neon), nên phần hạ tầng rẻ đi nhiều.

**Lấy được ngay mà không cần dựng**: ý *truy hồi hai tầng*. Đây chính là cái
`BAN-GIAO-PHIEN.md` (tổng quan) + `PROGRESS.md` (chi tiết) đang làm — và cũng
là luật **bóc lớp dần** của `docs/HUONG_GIAO_DIEN_2026-09-26.md`. Cùng một ý,
ba chỗ khác nhau.

---

## 4 · SOLID cho Agent Skills — LÀM

`.claude/skills/README.md` viết ra năm câu hỏi SOLID hỏi về một kỹ năng, kèm chỗ
đã sai. Ba kỹ năng đầu: `do-man-that`, `soat-bao-mat`, `giao-viec-agent`.

Chữ **D** là chữ đắt nhất ở đây, và là chữ đã trả giá: kỹ năng gọi
`python scripts/quet_bi_mat.py` chứ không chép regex vào bài, vì bản sao thứ hai
bao giờ cũng là bản sai sau vài tháng. Đúng lỗi mà bảy bộ đo đã mắc khi mỗi cái
tự lo vòng đời trình duyệt.

---

## 5 · Nhóm nguồn giao diện (9–13) — vì sao còn để đó

`emilkowalski/skills` (chuyển động), `uiverse.io` (thư viện thành phần CSS),
`horizonx.so`, `shaders.com` (nền shader), `contentcore.xyz`.

Chúng là nguồn **thêm vào**: hiệu ứng đẹp, thành phần lạ mắt, nền động. Nhưng
góp ý của khách 23/09 lại đi hướng **ngược lại**: *"giao diện đang hơi nhiều
chữ, ngay màn hình đầu đã khá nhiều thông tin nên đọc hơi rối, các bạn xem cân
nhắc rút gọn"*. Đợt việc đang chạy là **gọt bớt**, không phải thêm vào — thêm
hiệu ứng lúc này là đi ngược điều người dùng vừa kêu.

**Khi nào mở lại**: sau khi các màn đầu đạt chỉ tiêu ở
`docs/HUONG_GIAO_DIEN_2026-09-26.md` §5 (Giảng dạy ≤ 450 từ, ≤ 6 ô số, 0 câu dài
quá 12 từ). Lúc ấy chuyển động có chỗ đứng đúng của nó: dẫn mắt giữa hai trạng
thái, không phải trang trí. `emilkowalski/skills` là nguồn tốt nhất trong nhóm
cho việc ấy.

Ràng buộc giữ nguyên khi mở lại: không hardcode px (clamp / rem / vw / ch), dùng
token màu sẵn có, vùng chạm ≥ 44 px, và `do_axe.mjs` vẫn phải 0 vi phạm —
`prefers-reduced-motion` phải được tôn trọng.

---

## 6 · Nguồn tự tra thêm trong lúc làm

Không phải anh Sơn gửi, nhưng đã dùng và nên nhớ:

| Nguồn | Dùng vào việc gì |
|---|---|
| [FSRS — The Algorithm](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm) | Lịch ôn tập giãn cách |
| [django-outbox-pattern](https://github.com/juntossomosmais/django-outbox-pattern) | Gửi thư / tin nhắn không mất khi lỗi |
| [GitLab handbook — bounded contexts](https://handbook.gitlab.com/handbook/engineering/architecture/design-documents/modular_monolith/decisions/002_bounded_contexts_definition) | Cách chia miền trong `scripts/so_mien.json` |
| [GitLab Design — navigation sidebar](https://design.gitlab.com/patterns/navigation-sidebar/) | Menu theo vai |
| Dashboard / progressive disclosure (3 bài) | Chỉ tiêu 3–7 ô số mỗi màn — `docs/HUONG_GIAO_DIEN_2026-09-26.md` §2 |
| dotb.vn · eduspace.vn · emis.misa.vn | Đối chiếu tính năng với phần mềm trung tâm đào tạo ở VN |

---

## Thêm nguồn mới thế nào

1. Thêm một dòng vào **bảng tổng hợp**, cột "đã thành gì" để trống, trạng thái
   **Chưa**.
2. Trước khi áp, trả lời được: *nó giải vấn đề nào đang có ở đây, đo bằng gì?*
   Không trả lời được thì để nguyên trạng thái **Chưa** — như nhóm 9–13.
3. Áp xong thì điền cột "đã thành gì" bằng **đường dẫn tệp thật**, kèm số đo
   trước/sau nếu có. Không ghi "đã tham khảo" — sáu tháng sau không ai kiểm được
   câu ấy.
