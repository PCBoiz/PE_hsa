/**
 * AI LÀM ĐƯỢC GÌ — một bảng, và nó phải KHÔNG TRÔI ĐƯỢC khỏi backend.
 *
 * ── VÌ SAO CÓ TỆP NÀY (07/09/2026) ────────────────────────────────────────
 *
 * Hệ thống đã có sáu vai trò và sáu lớp quyền cưỡng chế ở backend. Nhưng
 * **không ai nhìn thấy chúng**: muốn biết `Trợ giảng` làm được gì thì phải đọc
 * `common/permissions.py`, rồi grep xem view nào dùng lớp nào. Anh Sơn không
 * đọc Python mỗi lần cần trả lời câu ấy, và cô Hương thì càng không.
 *
 * Cô Hương (chủ tịch HSA) đang soạn một bảng mô tả tính năng từng vai trò để
 * gửi trước khi họp. Anh Sơn chốt: **làm CƠ CHẾ ngay, điền nội dung sau**. Nên
 * tệp này là cơ chế — nội dung (`nhan`, `giaiThich`, và việc có thêm vai
 * `Quản lý` hay không) sẽ sửa khi bảng của cô về.
 *
 * ── LUẬT QUAN TRỌNG NHẤT: KHÔNG GÕ TAY VAI CHO TỪNG VIỆC ─────────────────
 *
 * Mỗi việc chỉ khai nó bị chặn bởi LỚP QUYỀN nào; danh sách vai suy ra từ
 * `VAI_CUA_LOP_QUYEN`. Gõ tay vai cho từng việc là dựng bản chép thứ hai của
 * `permissions.py` — và bản chép thứ hai luôn trôi, im lặng, theo hướng NỚI
 * chứ không siết (người ta thêm vai vào bảng cho tiện, không ai gỡ).
 *
 * `e2e/unit/quyen-vai.test.mjs` đọc THẲNG `common/permissions.py` và đối chiếu
 * cả hai chiều: mỗi lớp quyền ở đây phải tồn tại và cho đúng ngần ấy vai; mỗi
 * `nguon` phải là một view có thật khai đúng lớp quyền ấy.
 *
 * ── ĐÂY KHÔNG PHẢI HÀNG RÀO ─────────────────────────────────────────────
 *
 * Hàng rào là `permission_classes` ở backend. Bảng này chỉ để NHÌN THẤY và để
 * bàn. Không màn nào được dùng nó thay cho một cổng thật.
 */

import {
  VAI_BIEN_TAP,
  VAI_GIANG_VIEN,
  VAI_HOC_VIEN,
  VAI_HOC_VU,
  VAI_QUAN_TRI,
  VAI_TRO_GIANG,
} from './vaiTro';

/** Thứ tự hiện trên bảng — từ rộng quyền nhất tới hẹp nhất. */
export const VAI_TRO: readonly { ma: string; nhan: string; mo_ta: string }[] = [
  {
    ma: VAI_QUAN_TRI,
    nhan: 'Quản trị viên',
    mo_ta: 'Làm được mọi việc. Vai duy nhất đổi được vai của người khác và đặt lại mật khẩu.',
  },
  {
    ma: VAI_HOC_VU,
    nhan: 'Quản lý học vụ',
    mo_ta: 'Xếp lớp, mở đợt học, theo dõi cả trung tâm. KHÔNG đổi được vai trò và KHÔNG đặt lại được mật khẩu.',
  },
  {
    ma: VAI_GIANG_VIEN,
    nhan: 'Giảng viên',
    mo_ta: 'Dạy và theo dõi LỚP MÌNH PHỤ TRÁCH. Không thấy lớp của người khác.',
  },
  {
    ma: VAI_TRO_GIANG,
    nhan: 'Trợ giảng',
    mo_ta: 'Vào được khu giảng dạy của lớp được gán, nhưng không xem dữ liệu liên lạc của học viên và không xoá được gì.',
  },
  {
    ma: VAI_BIEN_TAP,
    nhan: 'Biên tập nội dung',
    mo_ta: 'Soạn khoá học, bài học và đề thi thử. Đứng ở TRỤC KHÁC với bốn vai trên — không đụng tới con người.',
  },
  {
    ma: VAI_HOC_VIEN,
    nhan: 'Học viên',
    mo_ta: 'Học, làm bài, thi thử. Vai mặc định của mọi tài khoản mới.',
  },
] as const;

/**
 * Lớp quyền của backend → vai trò nó cho qua.
 *
 * BẢN GỐC là `backend/common/permissions.py`. Bảng này là bản chép DUY NHẤT
 * được phép tồn tại ở frontend, và `quyen-vai.test.mjs` đối chiếu nó với tệp
 * .py kia từng vai một.
 */
export const VAI_CUA_LOP_QUYEN: Record<string, readonly string[]> = {
  IsAdminRole: [VAI_QUAN_TRI],
  IsCourseOwner: [VAI_QUAN_TRI],
  IsAdminOrAcademic: [VAI_QUAN_TRI, VAI_HOC_VU],
  IsSeniorTeachingStaff: [VAI_QUAN_TRI, VAI_HOC_VU, VAI_GIANG_VIEN],
  IsTeachingStaff: [VAI_QUAN_TRI, VAI_HOC_VU, VAI_GIANG_VIEN, VAI_TRO_GIANG],
  IsContentEditor: [VAI_QUAN_TRI, VAI_BIEN_TAP],
};

export type Viec = {
  /** Nhóm để xếp bảng — theo VIỆC của trung tâm, không theo tệp mã. */
  nhom: string;
  nhan: string;
  /** Vì sao ranh giới này ở đúng chỗ đó. Câu này là thứ đem ra bàn với cô Hương. */
  giaiThich: string;
  /** Lớp quyền cưỡng chế ở backend. Vai suy ra từ đây, KHÔNG gõ tay. */
  lopQuyen: keyof typeof VAI_CUA_LOP_QUYEN;
  /** `tệp.py::TênView` — để phép kiểm đối chiếu, và để người đọc lần ra được. */
  nguon: string;
  /**
   * Còn một hàng rào NỮA ngoài vai trò. Ví dụ giảng viên có vai đúng nhưng chỉ
   * xem được lớp mình phụ trách (`can_see_class`). Không nói ra thì bảng này
   * hứa rộng hơn sự thật.
   */
  chan_them?: string;
};

export const VIEC: readonly Viec[] = [
  // ── Con người ──
  {
    nhom: 'Tài khoản',
    nhan: 'Cấp tài khoản mới',
    giaiThich: 'Từ 27/08/2026 không còn tự đăng ký; tài khoản do trung tâm cấp.',
    lopQuyen: 'IsAdminRole',
    nguon: 'accounts/views.py::RegisterView',
  },
  {
    nhom: 'Tài khoản',
    nhan: 'Cấp hàng loạt từ danh sách',
    giaiThich: 'Dán danh sách lớp mới vào một ô, hệ thống tạo tài khoản và báo dòng nào trùng.',
    lopQuyen: 'IsAdminRole',
    nguon: 'teaching/admin_users.py::AdminBulkCreateUsersView',
  },
  {
    nhom: 'Tài khoản',
    nhan: 'Đổi vai trò của người khác',
    giaiThich: 'Việc nặng nhất trong hệ thống: nó cấp quyền. Học vụ KHÔNG làm được (anh Sơn chốt 01/09/2026).',
    lopQuyen: 'IsAdminRole',
    nguon: 'teaching/views.py::AdminUserRoleView',
  },
  {
    nhom: 'Tài khoản',
    nhan: 'Đặt lại mật khẩu cho người khác',
    giaiThich: 'Cùng lý do trên: đặt lại mật khẩu là chiếm được tài khoản đó.',
    lopQuyen: 'IsAdminRole',
    nguon: 'teaching/views.py::AdminResetPasswordView',
  },
  {
    nhom: 'Tài khoản',
    nhan: 'Khoá / mở khoá tài khoản',
    giaiThich: 'Khoá là cắt hiệu lực NGAY, kể cả với phiên đang mở.',
    lopQuyen: 'IsAdminRole',
    nguon: 'teaching/admin_users.py::AdminUserStatusView',
  },
  {
    nhom: 'Tài khoản',
    nhan: 'Đọc nhật ký kiểm toán',
    giaiThich: 'Ai đã đổi vai của ai, lúc nào. Đọc được nhật ký là đọc được hành vi của mọi người.',
    lopQuyen: 'IsAdminRole',
    nguon: 'teaching/admin_users.py::AdminAuditView',
  },

  // ── Lớp và đợt ──
  {
    nhom: 'Lớp & đợt học',
    nhan: 'Tạo và sửa lớp',
    giaiThich: 'Việc HẰNG NGÀY của học vụ — đó là lý do vai ấy tồn tại, để không phải cấp quyền quản trị cho người xếp lớp.',
    lopQuyen: 'IsAdminOrAcademic',
    nguon: 'teaching/views.py::AdminClassesView',
  },
  {
    nhom: 'Lớp & đợt học',
    nhan: 'Xếp học viên vào lớp / cho rời lớp',
    giaiThich: 'Ghi lý do rời lớp là bắt buộc để tỉ lệ giữ chân có nghĩa.',
    lopQuyen: 'IsAdminOrAcademic',
    nguon: 'teaching/views.py::AdminClassMembersView',
  },
  {
    nhom: 'Lớp & đợt học',
    nhan: 'Mở và đóng đợt học',
    giaiThich: 'Đợt là khung thời gian để so sánh giữ chân giữa các khoá tuyển sinh.',
    lopQuyen: 'IsAdminOrAcademic',
    nguon: 'teaching/terms.py::AdminTermsView',
  },
  {
    nhom: 'Lớp & đợt học',
    nhan: 'Xem bảng điều khiển toàn trung tâm',
    giaiThich: 'Cuộn số liệu mọi lớp lên một chỗ. Chỉ quản trị viên — nó gộp dữ liệu của cả trung tâm.',
    lopQuyen: 'IsAdminRole',
    nguon: 'teaching/overview.py::AdminOverviewView',
  },

  // ── Dạy học ──
  {
    nhom: 'Dạy học',
    nhan: 'Mở buổi học và điểm danh',
    giaiThich: 'Trợ giảng LÀM ĐƯỢC: điểm danh là việc chính của vai này.',
    lopQuyen: 'IsTeachingStaff',
    nguon: 'teaching/sessions.py::SessionAttendanceView',
    chan_them: 'chỉ lớp mình phụ trách hoặc được gán (can_see_class)',
  },
  {
    nhom: 'Dạy học',
    nhan: 'Giao bài và chấm tay',
    giaiThich: 'Cùng cửa với điểm danh — trợ giảng chấm được bài.',
    lopQuyen: 'IsTeachingStaff',
    nguon: 'teaching/assignments.py::AssignmentGradingView',
    chan_them: 'chỉ lớp mình phụ trách hoặc được gán',
  },
  {
    nhom: 'Dạy học',
    nhan: 'Xem hồ sơ học tập của một em',
    giaiThich: 'Tiến độ, điểm, chuyên cần — không gồm nhật ký em tự ghi.',
    lopQuyen: 'IsTeachingStaff',
    nguon: 'teaching/views.py::TeachStudentView',
    chan_them: 'chỉ lớp mình phụ trách hoặc được gán',
  },
  {
    nhom: 'Dạy học',
    nhan: 'Xuất CSV chuyên cần / tiến độ',
    giaiThich: 'Để đối chiếu ngoài hệ thống hoặc gửi cho kế toán.',
    lopQuyen: 'IsTeachingStaff',
    nguon: 'teaching/exports.py::ClassAttendanceCsvView',
    chan_them: 'chỉ lớp mình phụ trách hoặc được gán',
  },

  // ── Báo cáo phụ huynh ──
  {
    nhom: 'Báo cáo phụ huynh',
    nhan: 'Xem tờ báo cáo gửi phụ huynh',
    giaiThich: 'TRỢ GIẢNG KHÔNG XEM ĐƯỢC: tờ này in email và số điện thoại của học viên. Càng nhiều vai nhìn thấy dữ liệu của một đứa trẻ thì càng khó nói đó là an toàn.',
    lopQuyen: 'IsSeniorTeachingStaff',
    nguon: 'teaching/parent_report.py::ParentReportView',
    chan_them: 'chỉ lớp mình phụ trách',
  },
  {
    nhom: 'Báo cáo phụ huynh',
    nhan: 'Cấp đường dẫn cho phụ huynh mở',
    giaiThich: 'Cấp một đường vào KHÔNG CẦN TÀI KHOẢN là hành vi nặng hơn xem, nên không bao giờ được nới rộng hơn cửa xem.',
    lopQuyen: 'IsSeniorTeachingStaff',
    nguon: 'teaching/parent_link.py::ParentReportLinkView',
    chan_them: 'chỉ lớp mình phụ trách',
  },
  {
    nhom: 'Báo cáo phụ huynh',
    nhan: 'Gửi báo cáo cho cả lớp',
    giaiThich: 'Mỗi tin ZNS mất phí và không thu về được, nên có thêm một cửa xác nhận nêu đúng số người nhận.',
    lopQuyen: 'IsSeniorTeachingStaff',
    nguon: 'teaching/parent_send.py::ParentReportSendAllView',
    chan_them: 'chỉ lớp mình phụ trách',
  },
  {
    nhom: 'Báo cáo phụ huynh',
    nhan: 'Thu hồi một đường dẫn đã gửi',
    giaiThich: 'Phụ huynh chuyển tiếp nhầm vào nhóm lớp thì phải rút lại được ngay.',
    lopQuyen: 'IsSeniorTeachingStaff',
    nguon: 'teaching/parent_link.py::ParentReportLinkRevokeView',
  },

  // ── Nội dung ──
  {
    nhom: 'Nội dung',
    nhan: 'Soạn khoá học và bài học',
    giaiThich: 'Trục KHÁC hẳn bốn vai trên: biên tập viên không đụng tới con người, và người quản lý con người không nhất thiết soạn được bài.',
    lopQuyen: 'IsContentEditor',
    nguon: 'courseadmin/views.py::AdminBase',
  },
  {
    nhom: 'Nội dung',
    nhan: 'Nhập và xuất bản đề thi thử',
    giaiThich: 'Đề nhập từ bảng tính .xlsx; xuất bản rồi thì học viên thi được.',
    lopQuyen: 'IsContentEditor',
    nguon: 'mockexam/quan_tri.py',
  },
] as const;

/** Vai nào làm được việc này. Suy ra, không gõ tay — xem chú thích đầu tệp. */
export function vaiLamDuoc(v: Viec): readonly string[] {
  return VAI_CUA_LOP_QUYEN[v.lopQuyen] ?? [];
}

/** Các nhóm việc, giữ đúng thứ tự khai trong `VIEC`. */
export function cacNhom(): string[] {
  return [...new Set(VIEC.map((v) => v.nhom))];
}

/* ═══════════════════════════════════════════════════════════════════════════
   SUY RA HÌNH DẠNG CỦA HỆ THỐNG QUYỀN, ĐỂ VẼ ĐƯỢC

   ── VÌ SAO (07/09/2026) ────────────────────────────────────────────────────

   Bảng ô vuông ở `/quan-tri/vai-tro` trả lời đúng câu "vai X làm được việc Y
   không". Nhưng nó KHÔNG nói được điều quan trọng hơn: sáu lớp quyền kia
   **lồng vào nhau**. Đếm thật trên chính dữ liệu ở trên:

       IsAdminRole            {QT}
       IsAdminOrAcademic      {QT, HV}              ⊃ IsAdminRole
       IsSeniorTeachingStaff  {QT, HV, GV}          ⊃ IsAdminOrAcademic
       IsTeachingStaff        {QT, HV, GV, TG}      ⊃ IsSeniorTeachingStaff

       IsContentEditor        {QT, BT}              ⊄ và ⊅ ba lớp giữa

   Tức bốn lớp đầu là BỐN VÒNG ĐỒNG TÂM — mỗi vòng ra ngoài thì thêm đúng một
   vai — còn biên tập nội dung là một NHÁNH RIÊNG chạm vào lõi quản trị. Nhìn
   ra hình ấy thì trả lời được những câu bảng không trả lời nổi: "nới quyền cho
   trợ giảng thì ai bị ảnh hưởng", "vai Quản lý sắp thêm sẽ nằm ở vòng nào".

   ── VÌ SAO PHẢI SUY RA CHỨ KHÔNG VẼ TAY ───────────────────────────────────

   Vẽ tay bốn vòng là ghim một khẳng định vào hình ảnh. Hôm nay nó đúng; ngày
   ai đó thêm một lớp quyền cắt ngang (ví dụ `{HV, GV}` — không có quản trị)
   thì chuỗi gãy, mà HÌNH thì vẫn vẽ y như cũ và vẫn trông rất thuyết phục.

   Nên hàm này TỰ TÌM chuỗi lồng nhau từ dữ liệu, và mọi lớp không xếp được
   vào chuỗi đều bị đẩy sang `nhanh` — không có lớp nào bị bỏ im lặng. Trang
   vẽ phải hiện `nhanh` ra; `e2e/unit/quyen-vai.test.mjs` kiểm rằng tổng số
   lớp trong `vong` + `nhanh` đúng bằng số lớp đã khai.
   ═════════════════════════════════════════════════════════════════════════ */

export type Vong = {
  /** Lớp quyền mở ra ở vòng này. */
  lopQuyen: string;
  /** Vai MỚI được thêm so với vòng trong. Vòng lõi thì là toàn bộ vai của nó. */
  vaiThem: readonly string[];
  /** Tất cả vai qua được vòng này. */
  vaiTatCa: readonly string[];
  /** Số việc trong `VIEC` do lớp này chặn. 0 = lớp có khai nhưng chưa việc nào dùng. */
  soViec: number;
};

export type SoDo = {
  /** Từ LÕI ra ngoài. Vòng sau chứa trọn vòng trước. */
  vong: readonly Vong[];
  /** Lớp không xếp được vào chuỗi — trục khác. Phải được vẽ ra, không được giấu. */
  nhanh: readonly Vong[];
  /** Vai không qua được lớp quyền nào: đứng ngoài mọi vòng. */
  vaiNgoai: readonly string[];
};

/** Đếm việc do một lớp quyền chặn. */
function demViec(lop: string): number {
  return VIEC.filter((v) => v.lopQuyen === lop).length;
}

/**
 * Tìm hình dạng: chuỗi vòng lồng nhau DÀI NHẤT, phần còn lại là nhánh.
 *
 * Cách tìm: xếp mọi lớp theo số vai tăng dần, rồi đi từ hẹp nhất ra — lớp nào
 * CHỨA TRỌN vòng đang đứng thì nối tiếp vào chuỗi, không thì thành nhánh.
 *
 * Lớp TRÙNG tập vai (`IsAdminRole` và `IsCourseOwner` đều là {quản trị}) gộp
 * vào cùng một vòng chứ không dựng hai vòng chồng khít — hai vòng vẽ trùng
 * nhau thì người xem tưởng có hai mức, mà thật ra chỉ có một.
 */
export function soDoVai(): SoDo {
  const cac = Object.entries(VAI_CUA_LOP_QUYEN)
    .map(([lop, vai]) => ({ lop, vai }))
    .sort((a, b) => a.vai.length - b.vai.length);

  const vong: Vong[] = [];
  const nhanh: Vong[] = [];
  let trong: readonly string[] = [];

  for (const { lop, vai } of cac) {
    const chuaTron = trong.every((r) => vai.includes(r));
    const trungVongCuoi = vong.length > 0
      && vai.length === vong[vong.length - 1].vaiTatCa.length
      && chuaTron;

    if (trungVongCuoi) {
      // Cùng tập vai với vòng ngoài cùng: gộp nhãn, không dựng vòng mới.
      const v = vong[vong.length - 1];
      vong[vong.length - 1] = {
        ...v,
        lopQuyen: `${v.lopQuyen} · ${lop}`,
        soViec: v.soViec + demViec(lop),
      };
      continue;
    }

    if (chuaTron) {
      vong.push({
        lopQuyen: lop,
        vaiThem: vai.filter((r) => !trong.includes(r)),
        vaiTatCa: vai,
        soViec: demViec(lop),
      });
      trong = vai;
    } else {
      nhanh.push({ lopQuyen: lop, vaiThem: vai, vaiTatCa: vai, soViec: demViec(lop) });
    }
  }

  const quaDuoc = new Set([...vong, ...nhanh].flatMap((v) => v.vaiTatCa));
  return {
    vong,
    nhanh,
    vaiNgoai: VAI_TRO.map((v) => v.ma).filter((m) => !quaDuoc.has(m)),
  };
}

/** Nhãn tiếng Việt của một mã vai; trả lại chính mã nếu chưa khai (để lộ ra). */
export function nhanVai(ma: string): string {
  return VAI_TRO.find((v) => v.ma === ma)?.nhan ?? ma;
}
