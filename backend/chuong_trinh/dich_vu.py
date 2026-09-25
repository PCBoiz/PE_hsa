"""CỬA DUY NHẤT miền khác gọi vào miền chương trình (luật S4, `docs/THIET_KE_HE_THONG.md` §4).

Ba hàm công khai:
  · `nhan_khung(class_id, version_id, dry_run=…, request=…)` — lớp nhận một phiên bản khung;
  · `tien_do_lop(class_ids, …)` — tiến độ từng lớp (một câu SQL cho mọi số lớp);
  · `tien_do_em(user_id, class_ids)` — tiến độ của một em trong các lớp của em.

Tổng quan, danh sách lớp, "Việc hôm nay", "Lớp của tôi", tờ phụ huynh CHỈ gọi ba hàm
này; không mô-đun nào ngoài `chuong_trinh/` đọc hay ghi thẳng bảng §63–§64.

── NHẬN KHUNG GHI VÀO ĐÂU ─────────────────────────────────────────────────────

Miền này ghi đúng HAI cột trên bảng của miền khác — cột nó sở hữu: `classes.
syllabus_version_id` và `class_sessions.syllabus_session_id` — cộng `class_sessions.
topic` CHỈ ở buổi đang để trống (lấy tên buổi khung). Không đè tên buổi ai đã đặt.
"""
from django.db import transaction

from chuong_trinh.tien_do import tien_do_em, tien_do_lop
from chuong_trinh.tu_vung import BAN_XUAT_BAN
from common.audit import CLASS_SYLLABUS, record
from common.db import q, q1, x

__all__ = ['LoiChuongTrinh', 'nhan_khung', 'tien_do_em', 'tien_do_lop']


class LoiChuongTrinh(Exception):
    """Lỗi nghiệp vụ, kèm mã HTTP cho view và câu tiếng Việt cho người dùng."""

    def __init__(self, ma, cau):
        super().__init__(cau)
        self.ma = ma
        self.cau = cau


def _buoi_dict(r):
    return {'sessionId': r['id'], 'startsAt': r['starts_at'].isoformat(), 'topic': r['topic'],
            'status': r['status']}


def nhan_khung(class_id, version_id, *, dry_run=False, request=None):
    """Lớp `class_id` nhận phiên bản `version_id` (phải ĐANG xuất bản).

    Gắn buổi học CHƯA GẮN, chưa huỷ của lớp vào buổi khung 1..N CÒN TRỐNG theo thứ tự
    ngày. Buổi đã gắn (tay hay lượt trước) giữ nguyên — kể cả khi đổi sang phiên bản
    khác: khi ấy gắn cũ được DỊCH sang buổi khung CÙNG SỐ của bản mới (và các mục đã ghi
    trong sổ đầu bài dịch sang mục cùng buổi, cùng tên) để lịch sử dạy không rơi khỏi
    tiến độ. Gọi lại với CÙNG phiên bản sau khi sinh thêm buổi = gắn nốt buổi mới.

    `dry_run=True`: tính y hệt, KHÔNG ghi gì. Trả dict mô tả kết quả; lỗi nghiệp vụ ném
    `LoiChuongTrinh`.

    TODO (V-g): buổi bù (`class_sessions.makeup_for`) chưa có trên nhánh này — khi có,
    buổi bù phải bị bỏ khỏi lượt gắn tự động (nó dạy lại nội dung buổi gốc).
    """
    with transaction.atomic():
        # FOR UPDATE: hai lượt nhận khung cùng lúc cho một lớp xếp hàng, không gắn chéo.
        lop = q1('SELECT id, name, course_id, syllabus_version_id FROM classes '
                 'WHERE id = %s FOR UPDATE', (class_id,))
        if not lop:
            raise LoiChuongTrinh(404, 'Không tìm thấy lớp này.')
        ban = q1('''SELECT v.id, v.version, v.status, s.id AS syllabus_id, s.name, s.course_id,
                           co.title AS course_title
                      FROM syllabus_versions v
                      JOIN syllabi s ON s.id = v.syllabus_id
                      LEFT JOIN courses co ON co.id = s.course_id
                     WHERE v.id = %s''', (version_id,))
        if not ban:
            raise LoiChuongTrinh(404, 'Không tìm thấy phiên bản khung này.')
        if ban['status'] != BAN_XUAT_BAN:
            raise LoiChuongTrinh(409, 'Lớp chỉ nhận được bản ĐANG DÙNG của khung. Bản này '
                                      'là bản nháp hoặc đã được thay — xuất bản nó trước, '
                                      'hoặc chọn bản đang dùng.')
        if lop['course_id'] and lop['course_id'] != ban['course_id']:
            raise LoiChuongTrinh(400, 'Khung "%s" là của môn %s, lớp này học môn khác.'
                                 % (ban['name'], ban['course_title'] or ban['course_id']))

        khung = q('SELECT id, so_buoi, title FROM syllabus_sessions WHERE version_id = %s '
                  'ORDER BY so_buoi', (version_id,))
        theo_so = {k['so_buoi']: k for k in khung}
        buoi = q('''SELECT cs.id, cs.starts_at, cs.status, cs.topic, cs.syllabus_session_id,
                           ss.version_id AS ban_cu, ss.so_buoi AS so_cu
                      FROM class_sessions cs
                      LEFT JOIN syllabus_sessions ss ON ss.id = cs.syllabus_session_id
                     WHERE cs.class_id = %s
                     ORDER BY cs.starts_at, cs.id''', (class_id,))

        # 1. Gắn cũ trỏ sang phiên bản KHÁC → dịch theo số buổi. Không có buổi cùng số ở
        #    bản mới thì bỏ gắn, buổi ấy vào hàng chờ gắn lại như buổi chưa gắn.
        giu = sum(1 for b in buoi if b['syllabus_session_id'] and b['ban_cu'] == version_id)
        dich, bo_gan = [], []
        for b in buoi:
            if b['syllabus_session_id'] and b['ban_cu'] != version_id:
                moi = theo_so.get(b['so_cu'])
                if moi:
                    dich.append((b['id'], b['syllabus_session_id'], moi['id']))
                    b['syllabus_session_id'] = moi['id']
                else:
                    bo_gan.append((b['id'], b['syllabus_session_id']))
                    b['syllabus_session_id'] = None

        # 2. Buổi khung còn trống ↔ buổi học chưa gắn, chưa huỷ, theo thứ tự ngày.
        da_dung = {b['syllabus_session_id'] for b in buoi if b['syllabus_session_id']}
        trong = [k for k in khung if k['id'] not in da_dung]
        cho = [b for b in buoi if not b['syllabus_session_id'] and b['status'] != 'cancelled']
        cap = list(zip(cho, trong, strict=False))
        gan = [(b['id'], k['id']) for b, k in cap]
        dien_ten = [(b['id'], k['title']) for b, k in cap if b['topic'] is None]

        ket = {
            'classId': class_id, 'versionId': version_id, 'dryRun': bool(dry_run),
            'khung': {'syllabusId': ban['syllabus_id'], 'name': ban['name'],
                      'version': ban['version']},
            'doiBan': bool(lop['syllabus_version_id'] and lop['syllabus_version_id'] != version_id),
            'ganMoi': [dict(_buoi_dict(b), soBuoi=k['so_buoi'], title=k['title']) for b, k in cap],
            'giuNguyen': giu,
            'dichSang': len(dich),
            'boGan': len(bo_gan),
            'buoiThua': [_buoi_dict(b) for b in cho[len(trong):]],
            'khungThieu': [{'soBuoi': k['so_buoi'], 'title': k['title']}
                           for k in trong[len(cho):]],
            'dienTen': len(dien_ten),
            'boQuaBuoiHuy': sum(1 for b in buoi
                                if b['status'] == 'cancelled' and not b['syllabus_session_id']),
        }
        if dry_run:
            return ket

        x('UPDATE classes SET syllabus_version_id = %s WHERE id = %s', (version_id, class_id))
        if dich:
            # Điều kiện `= cu` ở WHERE: chỉ đè đúng gắn đã đọc, một lượt gắn tay xen giữa
            # (hiếm) được giữ.
            x('''UPDATE class_sessions cs SET syllabus_session_id = m.moi
                   FROM unnest(%s::int[], %s::int[], %s::int[]) AS m(sid, cu, moi)
                  WHERE cs.id = m.sid AND cs.syllabus_session_id = m.cu''',
              ([d[0] for d in dich], [d[1] for d in dich], [d[2] for d in dich]))
        if ket['doiBan']:
            # Mục đã ghi trong sổ đầu bài → mục CÙNG số buổi, CÙNG tên ở bản mới. Mục không
            # khớp giữ nguyên (không vào tiến độ bản mới — vẫn đọc được trong sổ nhờ `label`).
            # DISTINCT ON: hai dòng sổ cùng buổi không được dịch vào CÙNG một mục mới (chỉ
            # mục duy nhất (buổi, mục) sẽ chặn cả câu).
            x('''WITH doi AS (
                     SELECT DISTINCT ON (li.session_id, moi.id) li.id AS li_id, moi.id AS moi_id
                       FROM session_log_items li
                       JOIN syllabus_items cu ON cu.id = li.item_id
                       JOIN syllabus_sessions scu ON scu.id = cu.syl_session_id
                                                 AND scu.version_id <> %(ban)s
                       JOIN syllabus_sessions smoi ON smoi.version_id = %(ban)s
                                                  AND smoi.so_buoi = scu.so_buoi
                       JOIN LATERAL (SELECT i.id FROM syllabus_items i
                                      WHERE i.syl_session_id = smoi.id AND i.label = cu.label
                                      ORDER BY i.sort, i.id LIMIT 1) moi ON TRUE
                      WHERE li.session_id IN (SELECT id FROM class_sessions
                                               WHERE class_id = %(lop)s)
                        AND NOT EXISTS (SELECT 1 FROM session_log_items k
                                         WHERE k.session_id = li.session_id
                                           AND k.item_id = moi.id)
                      ORDER BY li.session_id, moi.id, li.id)
                 UPDATE session_log_items li SET item_id = doi.moi_id
                   FROM doi WHERE li.id = doi.li_id''',
              {'ban': version_id, 'lop': class_id})
        if bo_gan:
            x('''UPDATE class_sessions cs SET syllabus_session_id = NULL
                   FROM unnest(%s::int[], %s::int[]) AS m(sid, cu)
                  WHERE cs.id = m.sid AND cs.syllabus_session_id = m.cu''',
              ([d[0] for d in bo_gan], [d[1] for d in bo_gan]))
        if gan:
            # `IS NULL`: không bao giờ đè một gắn — kể cả gắn tay xen giữa lúc đọc và lúc ghi.
            x('''UPDATE class_sessions cs SET syllabus_session_id = m.ss
                   FROM unnest(%s::int[], %s::int[]) AS m(sid, ss)
                  WHERE cs.id = m.sid AND cs.class_id = %s AND cs.syllabus_session_id IS NULL''',
              ([g[0] for g in gan], [g[1] for g in gan], class_id))
        if dien_ten:
            x('''UPDATE class_sessions cs SET topic = m.t
                   FROM unnest(%s::int[], %s::text[]) AS m(sid, t)
                  WHERE cs.id = m.sid AND cs.topic IS NULL''',
              ([d[0] for d in dien_ten], [d[1] for d in dien_ten]))

        record(request, CLASS_SYLLABUS, target_type='class', target_id=class_id,
               target_label=lop['name'],
               summary='Lớp %s nhận khung "%s" bản %d: gắn %d buổi, %d buổi thừa, %d buổi khung '
                       'chưa có buổi học' % (lop['name'], ban['name'], ban['version'], len(gan),
                                             len(ket['buoiThua']), len(ket['khungThieu'])),
               detail={'version_id': version_id, 'truoc': lop['syllabus_version_id'],
                       'gan': gan, 'dich': dich, 'bo_gan': bo_gan,
                       'dien_ten': [d[0] for d in dien_ten]})
        return ket
