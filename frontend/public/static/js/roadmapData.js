// ── Roadmap catalogue HSA (browse grid) ───────────────────────
// 2026-08-10: bộ lộ trình LUYỆN THI ĐGNL ĐHQGHN (HSA), thay 26 lộ trình lập
// trình kế thừa từ ProgrammingEdu. Bám khung curriculum 76 bài (3 khoá × 6
// chương) trong curricula.json / lesson_content_hsa.js.
// Schema (roadmap.js): ROADMAP_LIST=[{name,emoji,group,desc,isNew?}];
//   ROADMAP_DATA[name]=[{main:[label,status], left/right:[[label,status]|"label"]}];
//   ROADMAP_DETAILS[label.toLowerCase()] = {desc, resources:[{type,title,source}], course_id?}.
// Node dạng ["label","status"] (status: done|active|locked) hoặc "label" (=locked).

var ROADMAP_LIST = [
  { name: "Lộ trình tổng HSA",     emoji: "🎯", group: "Tổng quan",     desc: "Lộ trình luyện thi Đánh giá năng lực ĐHQG Hà Nội từ chẩn đoán đến về đích", isNew: true },
  { name: "Tư duy Định lượng",     emoji: "🔢", group: "Hợp phần HSA",  desc: "Toán học & xử lý số liệu — Phần 1 (50 câu, 75 phút, bắt buộc)" },
  { name: "Tư duy Định tính",      emoji: "✍️", group: "Hợp phần HSA",  desc: "Ngôn ngữ – Văn học — Phần 2 (50 câu, 60 phút, bắt buộc)" },
  { name: "Khoa học",              emoji: "🔬", group: "Hợp phần HSA",  desc: "Lý · Hóa · Sinh · Sử · Địa — Phần 3 (chọn 3/5, 50 câu, 60 phút)" },
];

var ROADMAP_DATA = {

  "Lộ trình tổng HSA": [
    { main: ["1. Chẩn đoán đầu vào", "active"], right: [["Làm bài khảo sát năng lực", "active"], "Xác định điểm mạnh – yếu", "Nhận lộ trình cá nhân hoá"] },
    { main: "2. Tư duy Định lượng (Phần 1)", left: ["Số & Đại số nền tảng", "Hàm số & Giải tích", "Hình học & Đo lường", "Thống kê & Xác suất", "Xử lý số liệu"] },
    { main: "3. Tư duy Định tính (Phần 2)", right: ["Từ vựng & Ngữ pháp", "Đọc hiểu", "Văn học", "Ngôn ngữ – Văn hóa – Xã hội"] },
    { main: "4. Khoa học (Phần 3 · chọn 3/5)", left: ["Vật lý", "Hóa học", "Sinh học", "Lịch sử", "Địa lý"] },
    { main: "5. Luyện đề tổng (CBT)", right: ["Thi thử 150 câu bấm giờ", "Phân tích mạnh – yếu", "Điều chỉnh chiến thuật"] },
    { main: "6. Về đích", left: ["Chiến thuật phòng thi", "Ổn định tâm lý", "Rà soát điểm yếu cuối"] },
  ],

  "Tư duy Định lượng": [
    { main: ["Chương 1: Số & Đại số nền tảng", "active"], right: [["Tỉ lệ & phần trăm", "active"], "Dãy số & quy luật", "Biểu thức & rút gọn", "Phương trình & bất phương trình", "Hệ phương trình"] },
    { main: "Chương 2: Hàm số & Giải tích", left: ["Hàm bậc nhất & đồ thị", "Hàm bậc hai & parabol", "Hàm mũ – logarit", "Đạo hàm & ứng dụng", "GTLN – GTNN"] },
    { main: "Chương 3: Hình học & Đo lường", right: ["Hệ thức lượng trong tam giác", "Đường tròn", "Khối & thể tích", "Tọa độ phẳng Oxy", "Tọa độ không gian Oxyz"] },
    { main: "Chương 4: Thống kê & Xác suất", left: ["Tổ hợp – chỉnh hợp", "Xác suất cơ bản", "Thống kê mô tả", "Biến cố & quy tắc đếm"] },
    { main: "Chương 5: Xử lý số liệu", right: ["Đọc bảng số liệu", "Đọc biểu đồ", "Bài toán thực tế", "Ước lượng & tính nhẩm nhanh"] },
    { main: "Chương 6: Chiến thuật phòng thi", left: ["Phân bổ thời gian phần Toán", "Dạng câu điền đáp án", "Mẹo loại trừ nhanh", "Luyện đề bấm giờ"] },
  ],

  "Tư duy Định tính": [
    { main: ["Chương 1: Từ vựng & Nghĩa từ", "active"], right: [["Từ đồng nghĩa & trái nghĩa", "active"], "Nghĩa của từ trong ngữ cảnh", "Từ loại", "Thành ngữ – tục ngữ"] },
    { main: "Chương 2: Ngữ pháp & Câu", left: ["Thành phần câu", "Dấu câu & liên kết", "Lỗi diễn đạt", "Biến đổi câu"] },
    { main: "Chương 3: Đọc hiểu", right: ["Ý chính & ý phụ", "Suy luận & hàm ý", "Thái độ – giọng điệu tác giả", "Văn bản thông tin & nghị luận"] },
    { main: "Chương 4: Văn học", left: ["Tác giả – tác phẩm trọng tâm", "Thể loại văn học", "Biện pháp tu từ", "Giá trị nội dung – nghệ thuật"] },
    { main: "Chương 5: Ngôn ngữ – Văn hóa – Xã hội", right: ["Sự phát triển & biến thể ngôn ngữ", "Phong cách hành văn", "Văn hóa – Lịch sử – Địa lý trong văn bản"] },
    { main: "Chương 6: Chiến thuật phòng thi", left: ["Đọc lướt & đọc quét", "Quản lý thời gian đọc hiểu", "Loại trừ nhanh", "Luyện đề"] },
  ],

  "Khoa học": [
    { main: ["Chương 1: Vật lý", "active"], right: [["Cơ học", "active"], "Điện học", "Quang – Nhiệt", "Dao động & Sóng", "Vật lý hạt nhân"] },
    { main: "Chương 2: Hóa học", left: ["Nguyên tử & Bảng tuần hoàn", "Liên kết & Phản ứng", "Hóa vô cơ trọng tâm", "Hóa hữu cơ trọng tâm", "Tính toán hóa học"] },
    { main: "Chương 3: Sinh học", right: ["Tế bào & Chuyển hóa", "Di truyền", "Tiến hóa", "Sinh thái", "Sinh lý cơ thể"] },
    { main: "Chương 4: Lịch sử", left: ["Lịch sử Việt Nam", "Lịch sử Thế giới", "Chuyên đề lịch sử", "Kỹ năng mốc – sự kiện"] },
    { main: "Chương 5: Địa lý", right: ["Địa lý tự nhiên", "Địa lý kinh tế – xã hội", "Kỹ năng Atlat", "Đọc biểu đồ địa lý"] },
    { main: "Chương 6: Chọn tổ hợp & Chiến thuật", left: ["Chọn 3/5 theo thế mạnh", "Chiến thuật từng môn", "Luyện đề tổ hợp"] },
  ],

};

// Chi tiết node (drawer) — gắn course_id để bấm "Học ngay" nhảy vào khoá tương ứng.
var ROADMAP_DETAILS = {
  "chương 1: số & đại số nền tảng": {
    course_id: "hsa_quantitative",
    desc: "Nền tảng số học & đại số cho phần Tư duy Định lượng: tỉ lệ – phần trăm, dãy số, biểu thức, phương trình – bất phương trình và hệ phương trình.",
    resources: [
      { type: "course", title: "Khoá Tư duy Định lượng — Chương 1", source: "ProgrammingEdu × TopHSA" },
      { type: "docs", title: "Cấu trúc đề HSA 2025 (Phần 1: Toán & xử lý số liệu)", source: "ĐHQG Hà Nội" }
    ]
  },
  "chương 1: từ vựng & nghĩa từ": {
    course_id: "hsa_verbal",
    desc: "Khởi đầu phần Tư duy Định tính: từ đồng/trái nghĩa, nghĩa trong ngữ cảnh, từ loại và thành ngữ – tục ngữ.",
    resources: [
      { type: "course", title: "Khoá Tư duy Định tính — Chương 1", source: "ProgrammingEdu × TopHSA" },
      { type: "docs", title: "Cấu trúc đề HSA 2025 (Phần 2: Ngôn ngữ – Văn học)", source: "ĐHQG Hà Nội" }
    ]
  },
  "chương 1: vật lý": {
    course_id: "hsa_science",
    desc: "Mở đầu phần Khoa học với Vật lý: cơ học, điện học, quang – nhiệt, dao động & sóng, vật lý hạt nhân.",
    resources: [
      { type: "course", title: "Khoá Khoa học — Chương 1 (Vật lý)", source: "ProgrammingEdu × TopHSA" },
      { type: "docs", title: "Cấu trúc đề HSA 2025 (Phần 3: Khoa học, chọn 3/5)", source: "ĐHQG Hà Nội" }
    ]
  },
  "1. chẩn đoán đầu vào": {
    desc: "Làm bài khảo sát năng lực đầu vào để hệ thống định vị điểm mạnh – yếu và xây dựng lộ trình cá nhân hoá cho bạn.",
    resources: [
      { type: "article", title: "Bài khảo sát năng lực đầu vào", source: "ProgrammingEdu × TopHSA" }
    ]
  },
  "5. luyện đề tổng (cbt)": {
    desc: "Thi thử toàn bộ 150 câu trên máy (CBT) bấm giờ như thi thật, sau đó phân tích điểm mạnh – yếu từng hợp phần để điều chỉnh chiến thuật.",
    resources: [
      { type: "course", title: "Thi thử HSA (CBT) trong ứng dụng", source: "ProgrammingEdu × TopHSA" }
    ]
  }
};
