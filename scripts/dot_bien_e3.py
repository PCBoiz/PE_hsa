"""Đột biến E3 (hộp Yêu cầu, §65) — 26/09/2026.

Mỗi mục: (luật, [(tệp, chuỗi cũ, chuỗi mới), …], biểu thức -k). Nền (cả mô-đun) phải xanh; mỗi
đột biến phải làm ĐỎ các phép kiểm khớp -k của nó; thoát 1 nếu còn đột biến sống mà không ghi
"hai lớp chặn". Một đột biến có nhiều cặp = gỡ CÙNG LÚC mọi lớp chặn của một luật (luật có hai
lớp — quyền ở view VÀ ở dịch vụ — thì gỡ một lớp phải sống, gỡ cả hai phải chết).

Chạy (máy có backend/.env, nối Neon dev): python scripts/dot_bien_e3.py
Mỗi đột biến chỉ chạy vài phép kiểm (Neon ~11 s/phép kiểm từ VN) — cả bộ ~20 phút.
"""
import os
import subprocess
import sys

GOC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend') + os.sep
LENH = [sys.executable, '-m', 'pytest', '-x', '-q', '-p', 'no:cacheprovider', 'yeu_cau/tests_yeu_cau.py']
DV, VW, LO, TT = 'yeu_cau/dich_vu.py', 'yeu_cau/views.py', 'yeu_cau/loai.py', 'yeu_cau/thuc_thi.py'

M = [
    ('GV/TG thấy hỗ trợ tài khoản',
     [(DV, "\"y.loai <> 'ht_tai_khoan' AND (y.class_id", '"TRUE AND (y.class_id')], 'khong_thay_ho_tro_tai_khoan'),
    ('TG thấy SĐT phụ huynh',
     [(DV, '            d.pop(k, None)', '            pass')], 'khong_thay_sdt'),
    ('HS / PH thấy ghi chú nội bộ',
     [(DV, "+ ('' if xem_noi_bo else ' AND NOT noi_bo')", "+ ''")], 'noi_bo'),
    ('GV thấy yêu cầu lớp khác',
     [(DV, '(y.class_id = ANY(%s) OR y.nguoi_xu_ly', '(y.class_id IS NOT NULL OR y.class_id = ANY(%s) OR y.nguoi_xu_ly')],
     'lop_minh_khong_toi_gv_lop_khac'),
    ('HS thấy yêu cầu về mình do người khác gửi (bản đầu)',
     [(DV, "return ('y.nguoi_tao = %s', [user.id], False)",
       "return ('(y.hoc_vien_id = %s OR y.nguoi_tao = %s)', [user.id, user.id], False)")], 'chi_thay_yeu_cau_minh_gui'),
    ('PH thấy yêu cầu gửi qua link khác (bản đầu)',
     [(DV, "(\"y.link_id = %s AND y.nguon = 'phu_huynh'\", [link['id']], False)",
       "(\"y.hoc_vien_id = %s AND y.nguon = 'phu_huynh'\", [link['user_id']], False)")], 'qua_chinh_link'),
    ('link thu hồi vẫn dùng được',
     [('teaching/parent_link.py', "    if d['revoked_at'] is not None:\n        return None, 'khong_thay'\n", '')],
     'link_thu_hoi'),
    ('trần 5 yêu cầu mở: >= → >',
     [(DV, 'if n >= L.TRAN_MO_PHU_HUYNH:', 'if n > L.TRAN_MO_PHU_HUYNH:')], 'toi_da_nam'),
    ('duyệt hai lần: gỡ kiểm "đã duyệt" (còn lớp máy trạng thái — phải sống)',
     [(DV, "if yc['trang_thai'] in ('da_duyet', 'da_xong') or yc['thuc_thi'] is not None:", 'if False:')],
     'hai_lan', 'hai lớp chặn'),
    ('duyệt hai lần: gỡ CẢ kiểm "đã duyệt" lẫn máy trạng thái',
     [(DV, "if yc['trang_thai'] in ('da_duyet', 'da_xong') or yc['thuc_thi'] is not None:", 'if False:'),
      (DV, "if L.ai_duoc_chuyen(yc['loai'], yc['trang_thai'], 'da_duyet') != L.DUYET:", 'if False:')], 'hai_lan'),
    ('TG / GV duyệt: gỡ lớp quyền view (còn kiểm ở dịch vụ — phải sống)',
     [(VW, 'permission_classes = [IsAdminOrAcademic]\n\n    def get(self, request, yc_id):\n        p = request.query_params',
       'permission_classes = [IsTeachingStaff]\n\n    def get(self, request, yc_id):\n        p = request.query_params')],
     'duyet_403', 'hai lớp chặn'),
    ('TG / GV duyệt: gỡ CẢ lớp quyền view lẫn kiểm dịch vụ',
     [(VW, 'permission_classes = [IsAdminOrAcademic]\n\n    def get(self, request, yc_id):\n        p = request.query_params',
       'permission_classes = [IsTeachingStaff]\n\n    def get(self, request, yc_id):\n        p = request.query_params'),
      (DV, "    if not nguoi.la_duyet:\n        raise LoiYeuCau(403, 'Chỉ học vụ hoặc quản trị viên duyệt được.')\n    ket_qua",
       '    ket_qua')], 'duyet_403'),
    ('nhân sự tạo yêu cầu cho lớp không phụ trách',
     [(DV, "if class_id is not None and not can_see_class(nguoi.user, class_id):\n            raise LoiYeuCau(404, 'Không tìm thấy lớp này.')",
       "if False:\n            raise LoiYeuCau(404, 'Không tìm thấy lớp này.')")], 'bao_len_giang_vien'),
    ('PH chọn được em / lớp khác qua thân request',
     [(DV, "hoc_vien_id, class_id = nguoi.link['user_id'], nguoi.link['class_id']",
       "hoc_vien_id, class_id = hoc_vien_id or nguoi.link['user_id'], class_id or nguoi.link['class_id']")],
     'phu_huynh_chi_thay_yeu_cau_phu_huynh'),
    ('TG mở lại lượt xin đã bị từ chối',
     [(LO, "    ('tu_choi', 'dang_xu_ly'): DUYET,\n", '')], 'mo_lai_yeu_cau_thay_doi'),
    ('GV phân loại: gỡ CẢ lớp quyền view lẫn kiểm dịch vụ',
     [(VW, 'permission_classes = [IsAdminOrAcademic]\n\n    def post(self, request, yc_id):\n        try:\n            return Response(dv.phan_loai',
       'permission_classes = [IsTeachingStaff]\n\n    def post(self, request, yc_id):\n        try:\n            return Response(dv.phan_loai'),
      (DV, "    if not nguoi.la_duyet:\n        raise LoiYeuCau(403, 'Chỉ học vụ hoặc quản trị viên phân loại được.')\n", '')],
     'phan_loai_ghi_lich_su'),
    ('phân loại sang loại xin–duyệt',
     [(DV, 'if loai_moi not in L.PHAN_LOAI_DUOC:', 'if loai_moi not in L.LOAI:')], 'phan_loai_ghi_lich_su'),
    ('lỗi việc khi duyệt trả 404',
     [(TT, 'raise LoiYeuCau(MA_VIEC_HONG if ma == 404 else ma,', 'raise LoiYeuCau(ma,')], '409_khong_phai_404'),
    ('TG đọc email em chưa có tên (tên em)',
     [(DV, "yc['hv_ten'] or (yc['hv_email'] if nguoi.la_duyet else", "yc['hv_ten'] or (yc['hv_email'] if True else")],
     'email_em_chua_co_ten'),
    ('TG đọc email em chưa có tên (lịch sử)',
     [(DV, "return getattr(self.user, 'name', None) or ('#%s' % self.id if self.id else '—')",
       "return getattr(self.user, 'name', None) or getattr(self.user, 'email', None)")], 'email_em_chua_co_ten'),
    ('mất cờ "em không phản hồi"',
     [(DV, '        if d.get(k) is True:', '        if False:')], 'khong_phan_hoi'),
    ('câu lỗi in mã khoá',
     [(DV, 'ra[k] = _chu(d[k], tran, nhan)', 'ra[k] = _chu(d[k], tran, k)')], 'chu_nguoi_dung'),
    ('học viên gửi được "báo lên"',
     [(LO, "'hoc_vien': tuple(k for k in LOAI if k != 'bao_cao_len'),", "'hoc_vien': tuple(LOAI),")],
     'loai_cua_minh'),
    ('bảo lưu: không xoá đệm quyền môn sau commit',
     [(DV, 'transaction.on_commit(lambda: _quen_truy_cap(em))', 'pass')], 'mat_quyen_mon'),
    ('danh sách em của lớp ngoài phạm vi',
     [(VW, 'if cid and cid in ids:', 'if cid:')], 'lua_chon_em'),
    ('đổi trạng thái thẳng sang "đã duyệt" (bỏ qua thực thi)',
     [(DV, "    if den == L.CHI_QUA_DUYET:\n        raise LoiYeuCau(400, 'Duyệt yêu cầu bằng nút Duyệt.')\n", '')],
     'khong_dong_xong_khi_chua_duyet'),
    ('đóng "đã xong" một lượt xin chưa duyệt',
     [(LO, "    if cho_nhom == 'khac' and la_thay_doi(loai):\n        return None\n", '')],
     'khong_dong_xong_khi_chua_duyet'),
    ('báo lỗi bản ghi không cần buổi',
     [(DV, "if thong_tin.get('can_buoi') and session_id is None:", 'if False:')], 'bat_buoc_buoi'),
    ('học viên gửi vào lớp không học',
     [(DV, "if class_id is not None and not _tung_hoc(nguoi.id, class_id):\n            raise LoiYeuCau(404, 'Em không học lớp này.')",
       "if False:\n            raise LoiYeuCau(404, 'Em không học lớp này.')")], 'lop_minh_khong_toi_gv_lop_khac'),
    ('nhãn lịch sử mất (mã trần lên màn)',
     [(DV, "'tuNhan': _nhan_moc(r['kieu'], r['tu']), 'denNhan': _nhan_moc(r['kieu'], r['den']),",
       "'tuNhan': r['tu'], 'denNhan': r['den'],")], 'lich_su_co_nhan'),
]


def chay(k=None):
    lenh = LENH + (['-k', k] if k else [])
    return subprocess.run(lenh, cwd=GOC, capture_output=True, text=True, timeout=2400).returncode


if '--bo-nen' not in sys.argv:
    if chay() != 0:
        print('NỀN ĐỎ — dừng')
        sys.exit(2)
    print('nền xanh (cả mô-đun)')
song, song_co_chu_y = [], []
for muc in M:
    luat, cap, k = muc[0], muc[1], muc[2]
    co_chu_y = len(muc) > 3
    goc = {}
    try:
        hong = False
        for tep, cu, moi in cap:
            p = GOC + tep
            noi = goc.get(p) or open(p, encoding='utf-8', newline='').read()
            goc.setdefault(p, noi)
            # Tệp làm việc có thể là CRLF (Windows, autocrlf) — so theo \n rồi ghi lại đúng kiểu dòng.
            crlf = '\r\n' in noi
            chu = noi.replace('\r\n', '\n')
            n = chu.count(cu)
            if n != 1:
                print('  ?? %s: chuỗi xuất hiện %d lần — %s' % (tep, n, luat))
                hong = True
                break
            chu = chu.replace(cu, moi)
            open(p, 'w', encoding='utf-8', newline='').write(chu.replace('\n', '\r\n') if crlf else chu)
        rc = 0 if hong else chay(k)
    finally:
        for p, noi in goc.items():
            open(p, 'w', encoding='utf-8', newline='').write(noi)
    if hong:
        song.append(luat)
        continue
    nhan = 'ĐỎ ✓' if rc != 0 else ('SỐNG (có chủ ý: %s)' % muc[3] if co_chu_y else 'SỐNG ✗')
    print('  %s %s' % (nhan, luat))
    if rc == 0:
        (song_co_chu_y if co_chu_y else song).append(luat)
tong = len(M)
print('%d đột biến · %d bị giết · %d sống có chủ ý (một lớp chặn, lớp kia còn) · %d sống ngoài dự kiến'
      % (tong, tong - len(song) - len(song_co_chu_y), len(song_co_chu_y), len(song)))
sys.exit(1 if song else 0)
