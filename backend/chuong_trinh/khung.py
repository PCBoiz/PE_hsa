"""MỤC LỤC KHUNG CHƯƠNG TRÌNH — màn soạn khung mở ra đọc gì trước (E1).

GET /api/admin/chuong-trinh/khung (`IsCurriculumPlanner`): mọi môn, mỗi môn các phiên
bản khung (trạng thái, số buổi, số lớp đang dùng) — HAI câu cho mọi số môn. Có vì
học vụ soạn được khung nhưng KHÔNG đọc được `api/admin/courses` (cửa của biên tập nội
dung): màn soạn khung cần đúng danh sách môn, không cần nội dung bài.

Kèm nhãn trạng thái và loại mục từ `tu_vung` — màn hình không gõ lại chữ.
Sửa cây khung đi qua các cửa của `courseadmin/syllabus.py`.
"""
from rest_framework.response import Response
from rest_framework.views import APIView

from chuong_trinh.tu_vung import LOAI_MUC, NHAN_LOAI_MUC, NHAN_TRANG_THAI_BAN, TRANG_THAI_BAN
from common.db import q
from common.permissions import IsCurriculumPlanner


class MucLucKhungView(APIView):
    permission_classes = [IsCurriculumPlanner]

    def get(self, request):
        mon = q('SELECT id, title FROM courses ORDER BY title, id')
        ban = {}
        for r in q('''SELECT v.id, v.course_id, v.name, v.status, v.is_demo, v.created_at,
                             COALESCE(v.lineage_id, v.id) AS chuoi,
                             (SELECT COUNT(*) FROM syllabus_sessions s
                               WHERE s.version_id = v.id) AS so_buoi,
                             (SELECT COUNT(*) FROM classes c
                               WHERE c.syllabus_version_id = v.id) AS so_lop
                        FROM syllabus_versions v
                       ORDER BY v.created_at DESC, v.id DESC'''):
            ban.setdefault(r['course_id'], []).append({
                'id': r['id'], 'name': r['name'], 'status': r['status'],
                'statusLabel': NHAN_TRANG_THAI_BAN.get(r['status'], r['status']),
                'chuoi': r['chuoi'], 'soBuoi': r['so_buoi'], 'soLop': r['so_lop'],
                'isDemo': r['is_demo'], 'createdAt': r['created_at'].isoformat(),
            })
        return Response({
            'mon': [{'id': m['id'], 'title': m['title'], 'versions': ban.get(m['id'], [])}
                    for m in mon],
            'trangThai': [{'ma': k, 'nhan': NHAN_TRANG_THAI_BAN[k]} for k in TRANG_THAI_BAN],
            'loaiMuc': [{'ma': k, 'nhan': NHAN_LOAI_MUC[k]} for k in LOAI_MUC],
        })
