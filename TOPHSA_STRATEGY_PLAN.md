# ProgrammingEdu × TopHSA — Chiến lược & Kế hoạch phát triển (luyện thi ĐGNL HSA)

> Chốt với chủ dự án (2026-08-10):
> - Sản phẩm **vẫn là ProgrammingEdu** (của mình), **hợp tác TopHSA** để dạy **luyện thi Đánh giá năng lực (HSA) — ĐHQG Hà Nội**, KHÔNG dạy lập trình.
> - Làm **tại chỗ trong `D:\pe_hsa`** (đổi domain nội dung + đồng thương hiệu).
> - Dựng **KHUNG cả 3 phần thi trước**, nội dung mỏng (1–2 bài mẫu/phần).
> - Format học: **giữ gamification + thêm chế độ BẤM GIỜ mạnh**.
> - **Thêm trụ cột 4: Đề thi thử CBT đầy đủ** (~150 câu, chấm /150, phân tích mạnh/yếu).
> - **DB RIÊNG bắt buộc**: dữ liệu HSA khác hoàn toàn → **tạo một NeonDB mới**, KHÔNG dùng chung DB với bản lập trình.

---

## 0. Nguyên tắc nền — tận dụng tối đa hạ tầng đã migrate

`pe_hsa` là bản migrate hoàn chỉnh (Django 5.2 + DRF, Next.js 16, NeonDB, JWT/OAuth, 83 test).
Kiến trúc **content-driven** nên đổi lĩnh vực = đổi **dữ liệu + branding**, KHÔNG viết lại hạ tầng:

| Hạ tầng dùng lại NGUYÊN | Phải làm MỚI cho HSA |
|---|---|
| Auth JWT + OAuth, users, XP/streak/achievement, leaderboard, forum, notifications | Domain nội dung: 3 phần HSA thay khóa lập trình |
| Roadmap engine (nodes/edges/mermaid + progress) | Bộ roadmap-template HSA + logic sinh theo khảo sát HSA |
| Questionnaire → roadmap (bảng `surveys`, `_pick_roadmap_template`, `_generate_user_roadmap`) | Bộ câu hỏi khảo sát HSA (mục tiêu điểm/trường, trình độ từng phần, deadline) |
| Lesson shell 4 bước (`lesson_db_design.js`) + XP khi hoàn thành | Bước 4 "code IDE" → "Phòng luyện BẤM GIỜ"; hero mới theo môn |
| Quiz engine (generate/submit/history) | Ngân hàng câu hỏi HSA + engine **đề thi thử CBT** (trụ cột 4) |
| Courses (row DB) + curricula.json + enrollment/progress | 3 "course" = 3 phần HSA + curricula HSA |

**Quy tắc bất di bất dịch (kế thừa PE):** mọi con số hiển thị phải THẬT (từ engine/đáp án chuẩn);
verify E2E + tự soi ảnh; hỏi trước mỗi hạng mục lớn; commit local, push chỉ khi được phép.

---

## 0.5. Kiến trúc DB — **NeonDB RIÊNG cho HSA** (chốt 2026-08-10)

Dữ liệu HSA khác hoàn toàn bản lập trình → **KHÔNG dùng chung DB**. Cùng codebase ProgrammingEdu
(đã adapted cho HSA) nhưng **trỏ tới một NeonDB mới** → 2 sản phẩm cô lập dữ liệu tuyệt đối.

**Việc chuyển DB rất gọn** (đã khảo sát `backend/config/settings.py`):
- DB chỉ đọc từ **env `DATABASE_URL`** (parse qua `dj_database_url`). Đổi DB = đổi 1 biến env
  → deploy HSA dùng `DATABASE_URL` của NeonDB mới. Không sửa code DB.

**Bootstrap NeonDB HSA mới cần 3 lớp:**
1. **Schema 22 bảng legacy** (`courses`, `users`, `roadmaps`, `lessons`, `surveys`, `enrollments`,
   `xp/streak/achievements`…): các model Django đang `managed=False` → Django **không tự tạo**. Dùng
   **DDL gốc `D:/PE_test/db/schema.py`** (`init_db`) để tạo schema trên DB mới.
2. **Bảng hạ tầng Django/allauth/JWT-blacklist**: `python manage.py migrate` tạo bình thường (managed).
3. **Seed nội dung HSA**: viết `manage.py seed_data` (MIGRATION_NOTES đã dự trù cho đúng tình huống
   "dựng DB mới từ đầu") — seed 3 course HSA + roadmap-template HSA + achievements/mốc + (mỏng) ngân
   hàng câu hỏi. Idempotent.

**Bảng HSA MỚI (đề thi thử, ngân hàng câu hỏi, lượt làm)** → app Django mới `mockexam` với model
**`managed=True`** + migration thật. Vì DB HSA là DB trắng, Django tạo sạch — KHÔNG đụng schema legacy.

**Hệ quả cho kế hoạch:** thêm **GĐ 0.5 — Bootstrap NeonDB HSA** (tạo DB Neon mới → chạy schema DDL →
`migrate` → khung `seed_data`) làm **trước GĐ 1** (questionnaire/roadmap cần DB có bảng để ghi).
Việc tạo instance NeonDB + lấy `DATABASE_URL` là thao tác **thủ công phía chủ dự án** (tôi hướng dẫn
+ chuẩn bị script bootstrap; không tự tạo tài nguyên cloud).

---

## 1. Định vị & đồng thương hiệu

- **Tên/định vị**: "ProgrammingEdu × TopHSA — Luyện thi Đánh giá năng lực HSA (ĐHQG Hà Nội)".
  Platform = ProgrammingEdu; TopHSA = đối tác nội dung/đề thi (logo đồng hành, nguồn đề thi thử).
- **Đối tượng**: học sinh 12 / thí sinh tự do luyện HSA để xét tuyển ĐHQGHN & nhiều trường công nhận HSA.
- **Lời hứa sản phẩm**: "Biết mình đang ở đâu (khảo sát) → biết đường đi (lộ trình) → luyện đúng cách,
  vui và NHANH (format bấm giờ) → đo bằng đề thi thử thật (CBT /150)."

---

## 2. Mô hình bài thi HSA (khung để dựng nội dung/đề)

> ⚠️ Format HSA cập nhật theo năm — **cần TopHSA xác nhận cấu trúc đề mới nhất** trước khi khóa số liệu.
> Khung tham chiếu (2024–2025):

| Phần | Tên | Số câu | Thời gian | Dạng câu |
|---|---|---|---|---|
| 1 | **Tư duy định lượng** (Toán & xử lý số liệu) | ~50 | ~75' | TN 4 lựa chọn + **điền đáp án** |
| 2 | **Tư duy định tính** (Văn học – Ngôn ngữ) | ~50 | ~60' | TN 4 lựa chọn (đọc hiểu, ngữ pháp, từ vựng) |
| 3 | **Khoa học** (Lý/Hóa/Sinh/Sử/Địa) *hoặc* **Tiếng Anh** | ~50 | ~60' | TN + vài câu điền |
| | **Tổng** | **~150** | **~195–199'** | Thang điểm **150** |

Hệ quả thiết kế: engine câu hỏi phải hỗ trợ **2 dạng**: trắc nghiệm 4 lựa chọn + **điền đáp án**
(số/chuỗi). Đây là khác biệt lớn so với PE (chỉ có MCQ + code).

---

## 3. Bốn trụ cột — thiết kế chi tiết

### Trụ 1 — Questionnaire (khảo sát đầu vào HSA)
Tái dùng `surveys` + `_pick_roadmap_template` + `_generate_user_roadmap`. Thay bộ câu hỏi:
- Mục tiêu: **trường/ngành xét HSA**, **điểm mục tiêu** (/150), **mốc thi** (đợt/tháng).
- Trình độ tự đánh giá + (tùy chọn) **1 bài chẩn đoán ngắn 9 câu** (3 câu/phần) để định vị khách quan.
- Điểm yếu ưu tiên (phần nào, dạng nào).
→ Kết quả chọn **roadmap-template HSA** phù hợp (theo điểm mục tiêu + thời gian còn lại) rồi sinh
lộ trình cá nhân. **Cải tiến**: thêm nhánh chẩn đoán để lộ trình bám năng lực thật, không chỉ tự khai.

### Trụ 2 — Roadmap (lộ trình + tiến độ)
Tái dùng roadmap engine (nodes_json/edges_json/mermaid + `roadmap_progress`). Nội dung mới:
- Nút = **chủ đề HSA** nhóm theo 3 phần (VD Định lượng: Đại số → Hàm số → Hình học → Xác suất–Thống kê →
  Đọc bảng/biểu đồ). Cạnh = thứ tự học đề nghị.
- Mỗi nút gắn: bài học (Trụ 3) + drill bấm giờ + (mốc) đề thi thử phần.
- **Cải tiến**: nút hiển thị **trạng thái theo năng lực** (chưa đạt/đang lên/vững) dựa trên kết quả drill
  + đề thi thử, không chỉ "done/chưa done". Lộ trình **tự gợi ý ôn lại** phần yếu sau mỗi đề thi thử.

### Trụ 3 — Format học (gamified + BẤM GIỜ mạnh)
Giữ shell 4 bước `lesson_db_design.js`, đổi nội hàm cho HSA:
1. **Khái niệm** — hero tương tác theo môn (đồ thị hàm số kéo tham số; trực quan xác suất; đọc bảng số
   liệu; với Định tính: highlight cấu trúc đoạn văn / bẫy ngữ nghĩa). Số liệu THẬT.
2. **3 MCQ** — bẫy đúng các lỗi sai phổ biến của dạng câu HSA.
3. **Kéo-thả** — sắp **các bước giải** đúng thứ tự / ghép dạng câu ↔ chiến thuật / phân loại.
4. **PHÒNG LUYỆN BẤM GIỜ (thay code IDE)** — 5–10 câu cùng dạng, **đồng hồ đếm ngược**, chấm ngay,
   mở **lời giải từng bước**, thống kê **tốc độ (giây/câu) + độ chính xác**; đạt ngưỡng mới "hoàn thành".
- **Cải tiến vs PE**: thêm **speed stats** (HSA ăn nhau ở tốc độ), lời-giải-từng-bước, engine
  **điền-đáp-án** cạnh MCQ. XP thưởng theo cả đúng lẫn nhanh.

### Trụ 4 — Đề thi thử CBT (mới)
App/bảng mới (`mockexam`): ngân hàng câu hỏi (theo phần/chủ đề/độ khó) + đề (150 câu, 3 phần) +
lượt làm + chấm.
- Giao diện **CBT giống thi thật**: điều hướng câu, đánh dấu, đồng hồ theo TỪNG phần, tự nộp khi hết giờ.
- Chấm **/150** + **phân tích mạnh/yếu theo phần/chủ đề/dạng** + so mốc mục tiêu.
- **Vòng phản hồi**: kết quả đề thi thử → cập nhật trạng thái nút roadmap + gợi ý bài/drill cần ôn.
- Nguồn đề: phối hợp TopHSA (đề thi thử của trung tâm) — bắt đầu bằng **1 đề mẫu** để dựng engine.

---

## 4. Kiến trúc nội dung (đặt đâu, thêm sao)

| Thành phần | Vị trí | Thêm cho HSA |
|---|---|---|
| Course (3 phần) | bảng `courses` (seed) | 3 course: `hsa_dinhluong`, `hsa_dinhtinh`, `hsa_khoahoc_anh` |
| Curriculum (module/bài) | `frontend/src/lib/curricula.json` | 3 khối module HSA |
| Nội dung bài học | `frontend/public/static/js/lesson_content_hsa_*.js` | file nội dung/phần (khung + bài mẫu) |
| Shell render | `lesson_db_design.js` (byte-identical) | thêm hero + "phòng bấm giờ" + engine điền-đáp-án |
| Sync nội dung → DB | `content-tools/sync-lesson-content.mjs` | thêm course HSA vào cấu hình sync |
| Khảo sát | `backend/accounts` (survey) | bộ câu hỏi + template HSA |
| Roadmap template | bảng `roadmaps` (user_id NULL) | seed template HSA + nodes/edges |
| Đề thi thử | app mới `backend/mockexam` + bảng mới | engine + ngân hàng + chấm |
| Branding | `frontend/src/app/layout.tsx`, `Topbar.tsx`, landing, login, register, dashboard | ProgrammingEdu × TopHSA |

**Lưu ý kỹ thuật đã phát hiện:** `pe_hsa/frontend/public/static/js/` hiện có `lesson_content.js/_nc/_tc`
+ `lesson_db_design.js` nhưng **CHƯA có `lesson_content_ml.js`** (khóa ML mới build ở PE_test). Không
ảnh hưởng HSA, nhưng cần thống nhất nguồn shell (`lesson_db_design.js` ở pe_hsa là bản byte-identical —
mọi cải tiến hero/bấm-giờ sẽ làm trên bản này + sync).

---

## 5. Kế hoạch theo giai đoạn (mỗi GĐ: build → verify → commit local → báo cáo → chờ duyệt)

**GĐ 0 — Branding & scaffold (nhỏ, làm trước để thấy hình hài)**
- Đồng thương hiệu ProgrammingEdu × TopHSA (layout, topbar, landing, login/register, dashboard).
- Seed 3 course HSA (rỗng) + curricula.json 3 khối module (khung, chưa nội dung).
- Điều hướng dashboard hiển thị 3 phần HSA.
- *Chưa đụng* logic auth/roadmap/quiz.

**GĐ 0.5 — Bootstrap NeonDB HSA (làm TRƯỚC GĐ 1)**
- Chủ dự án tạo instance NeonDB mới → cấp `DATABASE_URL`.
- Chạy schema DDL 22 bảng (từ `D:/PE_test/db/schema.py`) trên DB mới → `manage.py migrate` (infra).
- Viết khung `manage.py seed_data` (idempotent) + seed tối thiểu để GĐ 1 có bảng ghi.
- Verify: register/login trên DB HSA mới hoạt động, hoàn toàn tách khỏi DB lập trình.

**GĐ 1 — Questionnaire + Roadmap HSA**
- Bộ câu hỏi khảo sát HSA (mục tiêu/điểm/mốc/điểm yếu) + (tùy chọn) 9 câu chẩn đoán.
- 2–3 roadmap-template HSA (theo điểm mục tiêu × thời gian) + nodes/edges 3 phần.
- Nối `_pick_roadmap_template` → template HSA; verify sinh lộ trình cá nhân + tiến độ.

**GĐ 2 — Format học (PILOT phần Tư duy định lượng) + Phòng bấm giờ**
- Dựng "phòng luyện bấm giờ" (bước 4) + engine điền-đáp-án + speed stats trong shell.
- 1–2 hero mẫu Định lượng (đồ thị hàm số / đọc biểu đồ) + 1–2 bài mẫu đủ 4 bước.
- Verify E2E + đa viewport + tự soi ảnh.

**GĐ 3 — Đề thi thử CBT (engine + 1 đề mẫu)**
- App `mockexam` + bảng (đề/câu hỏi/lượt làm/đáp án) + API.
- Giao diện CBT (điều hướng câu, đồng hồ theo phần, tự nộp) + chấm /150 + phân tích mạnh/yếu.
- Vòng phản hồi kết quả → roadmap. 1 đề mẫu để nghiệm thu.

**GĐ 4 — Đắp khung 2 phần còn lại (Định tính, Khoa học/Anh)**
- Hero + bài mẫu cho Định tính (đọc hiểu/ngôn ngữ) và Khoa học/Tiếng Anh.
- Ngân hàng câu hỏi mỏng đủ chạy drill + 1 đề thi thử mỗi phần.

**GĐ 5 — Hoàn thiện & cải tiến**
- A11y, đa viewport, i18n số liệu; leaderboard/achievement theo HSA (huy hiệu theo mốc điểm).
- Phân tích học tập (điểm theo thời gian, dự báo điểm HSA).
- Dọn nội dung lập trình cũ (ẩn/gỡ theo quyết định).

---

## 6. Cải tiến đề xuất (so với bản PE hiện tại)

1. **Engine điền-đáp-án** (mới) — HSA có dạng điền, PE chưa có.
2. **Chế độ bấm giờ + speed stats** — HSA ăn nhau ở tốc độ; PE không đo tốc độ.
3. **Lời giải từng bước** (reveal) ở mọi câu luyện — quan trọng cho tự học thi.
4. **Roadmap theo NĂNG LỰC** (trạng thái nút từ kết quả drill/đề thi thử) thay vì chỉ done/chưa.
5. **Vòng phản hồi đề-thi-thử → lộ trình** — biến điểm số thành hành động ôn tập cụ thể.
6. **Dự báo điểm HSA** từ lịch sử drill/đề thi thử (định hướng, tạo động lực).

---

## 7. Rủi ro & điểm cần chốt với TopHSA

- **Cấu trúc đề HSA chính xác năm nay** (số câu/thời gian/tỉ lệ dạng điền) — cần TopHSA xác nhận.
- **Nguồn đề thi thử & bản quyền** — dùng đề TopHSA hay tự soạn; cách phối hợp.
- **Chuẩn lời giải** — cần đội chuyên môn TopHSA duyệt lời giải từng bước.
- **Mức độ giữ/ẩn nội dung lập trình cũ** trong cùng codebase.
- Ngân sách nội dung: 3 phần × nhiều chủ đề là khối lượng lớn — pilot Định lượng trước là hợp lý.

---

## 8. Đề xuất bước kế tiếp

Hai việc đầu tiên, theo thứ tự:
1. **GĐ 0.5 — NeonDB HSA riêng**: chủ dự án tạo instance NeonDB mới + cấp `DATABASE_URL`; tôi chuẩn bị
   script bootstrap schema (từ `db/schema.py`) + khung `seed_data`. Đây là **cổng chặn** — mọi tính năng
   ghi dữ liệu (questionnaire/roadmap/lesson progress/mock) đều cần DB này trước.
2. **GĐ 0 — Branding + scaffold** (song song được, chỉ frontend/nội dung tĩnh): đồng thương hiệu
   ProgrammingEdu × TopHSA + khung 3 course/curricula HSA.

Sau khi bạn duyệt kế hoạch + xác nhận cách làm DB, tôi sẽ hỏi vài câu thiết kế cụ thể rồi mới thực hiện.

*(Tài liệu này là bản kế hoạch để bạn duyệt/sửa — CHƯA động vào code sản phẩm, đúng yêu cầu "nghiên cứu trước".)*

---

## 9. NHẬT KÝ THỰC HIỆN

### GĐ 0.5 — Bootstrap NeonDB HSA riêng ✅ XONG (2026-08-10)

DB HSA mới (Neon project **PE_TopHSA**, host `ep-[đã ẩn]-pooler…/neondb`) đã được
dựng từ trống → chạy được end-to-end. Lưu ý: endpoint `ep-[endpoint đã ẩn]` là **DB HSA MỚI** (không
phải DB cũ PE_test — tên endpoint Neon khác tên project, chỉ phân biệt bằng nội dung).

**Đã làm:**
- Xác minh DB trống: `public` 0 bảng (chỉ có schema `neon_auth` của Neon, vô hại).
- **Không dùng `PE_test/db/schema.py`** vì file đó chỉ có 13/23 bảng, lẫn seed nội dung lập trình,
  và một số bảng đã drift (roadmaps/notifications/courses…). Thay bằng DDL tự dựng theo **model pe_hsa**.
- `backend/sql/legacy_schema.sql` — DDL đầy đủ **22 bảng nền** (bỏ `playing_with_neon`), DEFAULT
  lấy từ schema.py, thứ tự phụ thuộc FK đúng, idempotent.
- `manage.py bootstrap_schema` (app `common`) → tạo 22 bảng.
- `manage.py migrate` → hạ tầng Django (auth/sessions/sites/allauth/socialaccount/token_blacklist);
  bảng managed=False chỉ ghi nhận, không tạo lại. FK tới `users` chạy vì tạo `users` trước.
- `manage.py seed_data` → **3 course HSA** (`hsa_quantitative` / `hsa_verbal` / `hsa_science`) +
  **1 roadmap template** `hsa_master`.
- venv: `backend/.venv` (Python 3.14, psycopg3 cp314).

**Verify (chạy app thật trên DB mới):** register 200 · login 200 · `GET /api/user` 200 (đủ cột,
default 0 đúng, **password không lộ**) · `GET /api/courses` 200 (đúng 3 course HSA) · enroll 200 ·
`courses-enrolled` 200 · guard 401 · `POST /api/survey` 200. Log sạch, không RuntimeWarning datetime.
User test đã dọn sạch (DB chỉ còn seed).

**Khoảng trống cần xử ở GĐ sau:**
- `_pick_roadmap_template` / `_generate_user_roadmap` (accounts/views.py) còn theo template lập trình
  → `/api/survey` chưa sinh roadmap HSA. Cần map lại questionnaire→roadmap cho HSA (GĐ 1).
- `backend/.env`: `SECRET_KEY` + OAuth creds đang là **placeholder** (dev chạy, prod phải thay thật).

**Tiếp theo:** GĐ 0 — branding ProgrammingEdu × TopHSA + khung curricula/nội dung HSA (chờ duyệt + hỏi thiết kế).
