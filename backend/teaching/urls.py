from django.urls import path

from common import do_proxy
from teaching import (
                      admin_users,
                      assignments,
                      co_so_hoc_phi,
                      dong_thoi_gian,
                      exports,
                      ho_so,
                      lich,
                      lien_he_phu_huynh,
                      lop_cua_toi,
                      lop_gia_su,
                      nhap_ket_qua_view,
                      overview,
                      parent_link,
                      parent_report,
                      parent_send,
                      sessions,
                      sinh_buoi,
                      terms,
                      viec_hom_nay,
                      views,
)

urlpatterns = [
    # ── Khu vực giảng dạy — quyền theo NGỮ CẢNH (lớp mình phụ trách) ──
    path('api/teach/classes', views.TeachClassesView.as_view()),
    # Việc hôm nay — gom mọi lớp của người gọi. Chỉ đọc.
    path('api/teach/viec-hom-nay', viec_hom_nay.ViecHomNayView.as_view()),
    # Lịch gộp theo trung tâm / giảng viên / lớp / học viên (§53, 23/09/2026). Chỉ đọc.
    path('api/teach/lich', lich.LichView.as_view()),
    path('api/teach/classes/<int:class_id>', views.TeachClassDetailView.as_view()),
    path('api/teach/classes/<int:class_id>/students/<int:user_id>',
         views.TeachStudentView.as_view()),
    # Giảng viên cập nhật MỤC TIÊU + NGUYỆN VỌNG của em trong lớp (23/09/2026).
    path('api/teach/classes/<int:class_id>/students/<int:user_id>/profile',
         ho_so.MucTieuHocVienView.as_view()),
    # Báo cáo gửi phụ huynh (đặc tả ERP §6) — khác hồ sơ ở trên: ít số hơn, có
    # ranh giới riêng tư, và in ra giấy được.
    path('api/teach/classes/<int:class_id>/students/<int:user_id>/parent-report',
         parent_report.ParentReportView.as_view()),
    # Cấp / liệt kê ĐƯỜNG DẪN công khai của tờ ấy. Cùng cổng với chính tờ báo
    # cáo: cấp một đường vào KHÔNG CẦN TÀI KHOẢN là hành vi nặng hơn xem, nên
    # tuyệt đối không nới rộng hơn.
    path('api/teach/classes/<int:class_id>/students/<int:user_id>/parent-report/link',
         parent_link.ParentReportLinkView.as_view()),
    path('api/teach/parent-report/links/<int:link_id>/revoke',
         parent_link.ParentReportLinkRevokeView.as_view()),
    # Gửi CẢ LỚP. GET = bản soạn sẵn (không ghi gì), POST = gửi thật. Tách hai
    # bước có chủ ý: tin đã tới Zalo phụ huynh thì không thu về được, và mỗi
    # tin ZNS đều mất phí.
    path('api/teach/classes/<int:class_id>/parent-report/send-all',
         parent_send.ParentReportSendAllView.as_view()),
    # Dán liên hệ phụ huynh cho cả lớp. Cùng cổng với gửi báo cáo ở trên — cùng
    # một thứ cần canh: liên lạc của gia đình em.
    path('api/teach/classes/<int:class_id>/parent-contacts',
         lien_he_phu_huynh.ParentContactsImportView.as_view()),
    # Nhập kết quả thi thử từ tờ PDF của hệ thống khảo thí ngoài (15–16/09/2026).
    # `doc` chỉ đọc từng tờ và phát phiếu đã ký; `ghi` nhận lại phiếu, mặc định
    # chỉ trả bảng khớp, `ghi: true` mới ghi. Cùng cổng với báo cáo phụ huynh —
    # số điểm này đi thẳng vào tờ gửi về nhà. Vì sao tách hai: docstring của view.
    path('api/teach/classes/<int:class_id>/ket-qua-thi/doc',
         nhap_ket_qua_view.DocKetQuaThiView.as_view()),
    path('api/teach/classes/<int:class_id>/ket-qua-thi/ghi',
         nhap_ket_qua_view.GhiKetQuaThiView.as_view()),

    # ── ĐƯỜNG CÔNG KHAI ──
    # KHÔNG nằm dưới `api/teach/`: tiền tố ấy mang nghĩa "sau cổng giảng dạy",
    # và một tuyến AllowAny nấp trong đó là thứ người đọc sau sẽ bỏ sót khi rà
    # bề mặt công khai. Đặt tên `api/public/` để nó tự khai mình là gì.
    path('api/public/parent-report/<str:token>',
         parent_link.PublicParentReportView.as_view()),

    # ── Buổi học & điểm danh (đặc tả ERP §4) ──
    path('api/teach/classes/<int:class_id>/sessions', sessions.ClassSessionsView.as_view()),
    # Sinh lịch cả kỳ theo thứ trong tuần. GET = gợi ý (không ghi), POST có
    # `dry_run`. Trợ giảng bị chặn TRONG view — xem docstring `sinh_buoi.py`.
    path('api/teach/classes/<int:class_id>/sessions/generate',
         sinh_buoi.GenerateSessionsView.as_view()),
    path('api/teach/sessions/<int:session_id>', sessions.ClassSessionDetailView.as_view()),
    path('api/teach/sessions/<int:session_id>/attendance',
         sessions.SessionAttendanceView.as_view()),

    # ── Giao bài & chấm tay (đặc tả ERP §5) ──
    path('api/teach/classes/<int:class_id>/assignments',
         assignments.ClassAssignmentsView.as_view()),
    path('api/teach/assignments/<int:assignment_id>',
         assignments.AssignmentDetailView.as_view()),
    path('api/teach/assignments/<int:assignment_id>/submissions',
         assignments.AssignmentGradingView.as_view()),
    # Bài làm ĐỦ của MỘT em. Bảng chấm ở trên chỉ gửi 400 ký tự đầu mỗi bài —
    # xem `assignments.XEM_TRUOC`.
    path('api/teach/assignments/<int:assignment_id>/submissions/<int:user_id>',
         assignments.AssignmentSubmissionView.as_view()),
    # Phía học viên: KHÔNG nhận user_id, luôn là chính mình — xem docstring.
    path('api/assignments', assignments.MyAssignmentsView.as_view()),
    # Lớp của chính em: buổi tới, link phòng, chuyên cần của mình. Chỉ đọc.
    path('api/lop-cua-toi', lop_cua_toi.LopCuaToiView.as_view()),

    # ── Xuất dữ liệu (đặc tả ERP §6) ──
    path('api/teach/classes/<int:class_id>/export/progress.csv',
         exports.ClassProgressCsvView.as_view()),
    path('api/teach/classes/<int:class_id>/export/attendance.csv',
         exports.ClassAttendanceCsvView.as_view()),
    # PDF cấp lớp: bản ĐỌC, khác hai tệp CSV ở trên là bản LÀM VIỆC.
    path('api/teach/classes/<int:class_id>/export/report.pdf',
         exports.ClassReportPdfView.as_view()),
    path('api/admin/export/users.csv', exports.AdminUsersCsvView.as_view()),

    # ── Quản trị lớp & vai trò — chỉ quản trị viên ──
    # ── Bảng điều khiển trung tâm (đặc tả ERP §6) ──
    path('api/admin/overview', overview.AdminOverviewView.as_view()),

    # ── Đợt học (§36) ──
    path('api/teach/terms', terms.TermsLiteView.as_view()),
    path('api/admin/terms', terms.AdminTermsView.as_view()),
    path('api/admin/terms/<int:term_id>', terms.AdminTermDetailView.as_view()),
    # Ngày nghỉ của đợt (§46) — sinh lịch cả kỳ bỏ các ngày này.
    path('api/admin/terms/<int:term_id>/holidays', terms.TermHolidaysView.as_view()),
    path('api/admin/terms/<int:term_id>/holidays/<int:holiday_id>',
         terms.TermHolidayDetailView.as_view()),

    path('api/admin/classes', views.AdminClassesView.as_view()),
    # TRƯỚC `<int:class_id>` cho dễ đọc (int không khớp chữ, nhưng thứ tự nói rõ ý).
    path('api/admin/classes/options', views.AdminClassOptionsView.as_view()),
    # Tạo nhanh lớp gia sư (1.2b): lớp + em + lịch trong một giao dịch.
    path('api/admin/classes/gia-su', lop_gia_su.TaoLopGiaSuView.as_view()),
    path('api/admin/classes/<int:class_id>', views.AdminClassDetailView.as_view()),
    path('api/admin/classes/<int:class_id>/members', views.AdminClassMembersView.as_view()),

    # ── Tài khoản ──
    path('api/admin/users', admin_users.AdminUsersView.as_view()),
    path('api/admin/users/create', views.AdminCreateUserView.as_view()),
    path('api/admin/users/bulk', admin_users.AdminBulkCreateUsersView.as_view()),
    path('api/admin/users/<int:user_id>/role', views.AdminUserRoleView.as_view()),
    path('api/admin/users/<int:user_id>/status', admin_users.AdminUserStatusView.as_view()),
    path('api/admin/users/<int:user_id>/reset-password',
         views.AdminResetPasswordView.as_view()),
    # Hồ sơ học viên mở rộng (§51, 23/09/2026) — quản trị viên + học vụ.
    path('api/admin/users/<int:user_id>/profile', ho_so.HoSoHocVienView.as_view()),
    # Dòng thời gian học viên (23/09/2026) — CHỈ ĐỌC, gom từ bảy nguồn sẵn có.
    path('api/admin/users/<int:user_id>/timeline', dong_thoi_gian.DongThoiGianView.as_view()),

    # ── Nhật ký kiểm toán (đặc tả ERP §9, khối 5) ──
    path('api/admin/audit', admin_users.AdminAuditView.as_view()),
    # ĐO số chặng proxy — thứ duy nhất còn thiếu để đóng T38 và T66.
    # Chỉ quản trị viên, chỉ trả header liên quan tới proxy. Xem common/do_proxy.py.
    path('api/admin/do-proxy', do_proxy.DoProxyView.as_view()),
    # CƠ SỞ TÍNH học phí — không có trường tiền nào, xem co_so_hoc_phi.py
    path('api/admin/co-so-hoc-phi', co_so_hoc_phi.AdminBillingBasisView.as_view()),
]
