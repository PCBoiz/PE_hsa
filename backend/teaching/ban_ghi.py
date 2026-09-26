"""BẢN GHI BUỔI HỌC — em xem lại được, và trợ giảng biết ai chưa xem.

── VÌ SAO CÓ (26/09/2026, bảng phân rã dòng 21–22) ───────────────────────────

Dòng 22 (trợ giảng · quản lý record Zoom): *"Cho phép trợ giảng dán link record
buổi học vào ô buổi học tương ứng · Học sinh đã xem/chưa xem · Nhắc học sinh
chưa xem"*. Dòng 21: *"Theo dõi việc xem record"*.

Nửa đầu đã có từ lâu: `class_sessions.recording_url` và ô nhập ở màn Buổi học.
Đo lại 26/09 thì lộ ra tính năng đứt ở giữa — **`recording_url` không xuất hiện
ở bất kỳ màn nào của học viên**. Trợ giảng dán link, không em nào mở được, và
cũng không ai biết là không mở được. Cái thiếu lớn hơn không phải bảng thống kê,
mà là đường cho em xem lại bài.

── ĐO ĐƯỢC GÌ, VÀ CỐ Ý KHÔNG ĐO GÌ ───────────────────────────────────────────

Bản ghi nằm trên Zoom hoặc Drive, ngoài tầm hệ thống. Không biết em xem mấy
phút, xem hết hay tua cái rồi tắt. Thứ duy nhất biết chắc: em đã BẤM mở, lúc
nào, mấy lần. Nên bảng §72 chỉ ghi bấy nhiêu và chữ trên màn cũng nói đúng bấy
nhiêu — "đã mở" chứ không phải "đã xem xong". Đếm một thứ mình không đo được là
cách nhanh nhất để có một con số không ai tin.

── AI XEM ĐƯỢC GÌ ────────────────────────────────────────────────────────────

  · Ghi nhận lượt mở: em CỦA LỚP ẤY. Người ngoài lớp mở đường dẫn → 403 và không
    ghi dòng nào (một yêu cầu bị từ chối mà vẫn đổi dữ liệu là thứ người gửi
    không biết).
  · Xem ai đã mở / chưa mở: `IsTeachingStaff` của lớp — giảng viên, trợ giảng,
    học vụ, quản trị. KHÔNG cho học viên: ai đã xem bài là việc của người dạy,
    không phải của bạn cùng lớp.

Danh sách "chưa mở" chỉ đếm HỌC VIÊN (`chi_hoc_vien`); trợ giảng cũng nằm trong
`class_members` nhưng không phải người phải xem lại bài.
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.db import q, q1
from common.permissions import IsTeachingStaff, can_see_class
from notifications.service import notify
from teaching.nguoi_buoi import thuoc_buoi
from teaching.vocab import chi_hoc_vien

#: Trợ giảng nhìn lại bấy nhiêu buổi gần nhất có bản ghi — đủ để nhắc, không
#: thành một trang dài vô tận.
SO_BUOI = 12

#: Nhắc lại trong vòng bấy nhiêu phút thì gộp vào chuông cũ — bấm nút hai lần
#: không thành hai dòng chuông cho cùng một em.
NHAC_GOP_PHUT = 120


def _thuoc_lop(user_id, session_id):
    """Buổi này có phải buổi CỦA EM không. None = buổi không tồn tại.

    Hai điều kiện, không phải một: em đang học lớp ấy, VÀ em thuộc buổi ấy. Buổi
    bù (V-g, §62e `session_participants`) chỉ có vài em — cả lớp vẫn "đang học"
    nhưng buổi ấy không phải của họ.
    """
    r = q1('''SELECT s.id, s.class_id, s.recording_url,
                     (EXISTS (SELECT 1 FROM class_members m
                               WHERE m.class_id = s.class_id AND m.user_id = %s
                                 AND m.left_at IS NULL)
                      AND ''' + thuoc_buoi('s.id', '%s') + ''') AS trong_lop
                FROM class_sessions s WHERE s.id = %s''',
           (user_id, user_id, session_id))
    return r


class GhiLuotMoView(APIView):
    """POST /api/sessions/<id>/ban-ghi/da-mo — em bấm mở bản ghi.

    Trả `{lanMo}` để màn hiện "bạn đã mở N lần" mà không phải tải lại cả trang.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        r = _thuoc_lop(request.user.id, session_id)
        if not r:
            return Response({'detail': 'Không tìm thấy buổi học.'}, status=404)
        if not r['trong_lop']:
            return Response({'detail': 'Bạn không học lớp này.'}, status=403)
        if not (r['recording_url'] or '').strip():
            # Không đếm lượt mở của một thứ không tồn tại: con số ấy sẽ nói dối
            # trợ giảng rằng em đã xem lại bài.
            return Response({'detail': 'Buổi này chưa có bản ghi.'}, status=400)

        row = q1('''INSERT INTO recording_views (session_id, user_id)
                    VALUES (%s, %s)
                    ON CONFLICT (session_id, user_id) DO UPDATE
                       SET lan_mo = recording_views.lan_mo + 1,
                           mo_gan_nhat = now()
                    RETURNING lan_mo''', (session_id, request.user.id))
        return Response({'lanMo': row['lan_mo']})


class ThongKeBanGhiView(APIView):
    """GET /api/teach/classes/<id>/ban-ghi — buổi nào có bản ghi, ai chưa mở.

    Một dòng mỗi buổi: `daMo` / `chuaMo` và danh sách em chưa mở để nhắc thẳng.
    """

    permission_classes = [IsTeachingStaff]

    def get(self, request, class_id):
        if not can_see_class(request.user, class_id):
            return Response({'detail': 'Bạn không phụ trách lớp này.'}, status=403)

        buoi = q('''SELECT id, starts_at, topic, recording_url
                      FROM class_sessions
                     WHERE class_id = %s AND recording_url IS NOT NULL
                       AND recording_url <> ''
                     ORDER BY starts_at DESC LIMIT %s''', (class_id, SO_BUOI))
        # Buổi ĐÃ HỌC mà chưa ai dán link (dòng 22: "Record đã upload/chưa upload").
        # Không có danh sách này thì một buổi bị quên cứ nằm im — không ai thấy
        # cái KHÔNG có mặt trên màn.
        thieu = q('''SELECT id, starts_at, topic FROM class_sessions
                      WHERE class_id = %s AND status <> 'cancelled'
                        AND starts_at < now()
                        AND (recording_url IS NULL OR recording_url = '')
                      ORDER BY starts_at DESC LIMIT %s''', (class_id, SO_BUOI))
        ds_thieu = [{'sessionId': t['id'], 'startsAt': t['starts_at'].isoformat(),
                     'topic': t['topic']} for t in thieu]

        if not buoi:
            return Response({'buoi': [], 'thieuBanGhi': ds_thieu})

        hoc_vien = q('''SELECT u.id, u.name
                          FROM class_members m JOIN users u ON u.id = m.user_id
                         WHERE m.class_id = %s AND m.left_at IS NULL AND '''
                     + chi_hoc_vien('u') + ' ORDER BY u.name', (class_id,))
        ids = [e['id'] for e in buoi]
        da_mo = {}
        if hoc_vien:
            for v in q('SELECT session_id, user_id FROM recording_views '
                       'WHERE session_id = ANY(%s)', (ids,)):
                da_mo.setdefault(v['session_id'], set()).add(v['user_id'])

        # BUỔI BÙ (V-g, §62e): buổi có `session_participants` thì mẫu số là mấy em
        # ấy, không phải sĩ số lớp. Thiếu chỗ này thì một buổi bù cho hai em hiện
        # thành "0/28 đã mở", và nút Nhắc gọi chuông cho 26 em chưa từng dự buổi —
        # họ mở "Lớp của tôi" ra sẽ không thấy bản ghi nào, vì `lop_cua_toi.py` lọc
        # đúng bằng `thuoc_buoi`. §72 tự cãi nhau ở chính chỗ này (agent soát 26/09).
        rieng = {}
        for r in q('SELECT session_id, user_id FROM session_participants '
                   'WHERE session_id = ANY(%s)', (ids,)):
            rieng.setdefault(r['session_id'], set()).add(r['user_id'])

        ra = []
        for b in buoi:
            xong = da_mo.get(b['id'], set())
            thuoc = rieng.get(b['id'])
            trong_buoi = [e for e in hoc_vien if thuoc is None or e['id'] in thuoc]
            chua = [e for e in trong_buoi if e['id'] not in xong]
            ra.append({
                'sessionId': b['id'],
                'startsAt': b['starts_at'].isoformat(),
                'topic': b['topic'],
                'recordingUrl': b['recording_url'],
                'daMo': len(trong_buoi) - len(chua),
                'chuaMo': len(chua),
                'dsChuaMo': [{'id': e['id'], 'name': e['name']} for e in chua],
            })
        return Response({'buoi': ra, 'thieuBanGhi': ds_thieu})


class NhacXemBanGhiView(APIView):
    """POST /api/teach/classes/<c>/ban-ghi/<s>/nhac — gọi chuông cho em chưa mở.

    Bảng phân rã dòng 22: *"Nhắc học sinh chưa xem"*. Chỉ gửi cho em CHƯA mở —
    nhắc người đã xem rồi là cách nhanh nhất để cả lớp thôi đọc chuông.

    Chỉ chuông, không thư: đây là lời nhắc học, không phải việc gấp như đổi lịch;
    và thư ra khỏi hệ thống rồi thì không rút lại được.
    """

    permission_classes = [IsTeachingStaff]

    def post(self, request, class_id, session_id):
        if not can_see_class(request.user, class_id):
            return Response({'detail': 'Bạn không phụ trách lớp này.'}, status=403)
        buoi = q1('''SELECT id, starts_at, topic, recording_url FROM class_sessions
                      WHERE id = %s AND class_id = %s''', (session_id, class_id))
        if not buoi:
            return Response({'detail': 'Buổi học không thuộc lớp này.'}, status=404)
        if not (buoi['recording_url'] or '').strip():
            return Response({'detail': 'Buổi này chưa có bản ghi.'}, status=400)

        # Chỉ em THUỘC BUỔI: nhắc một em chưa từng dự buổi bù đi "xem lại buổi
        # 23/09" là chỉ em ấy tới một trang không có gì (agent soát 26/09).
        chua = q('''SELECT u.id FROM class_members m JOIN users u ON u.id = m.user_id
                     WHERE m.class_id = %s AND m.left_at IS NULL AND ''' + chi_hoc_vien('u') + '''
                       AND ''' + thuoc_buoi('%s', 'u.id') + '''
                       AND NOT EXISTS (SELECT 1 FROM recording_views v
                                        WHERE v.session_id = %s AND v.user_id = u.id)''',
                 (class_id, session_id, session_id))

        ngay = buoi['starts_at'].strftime('%d/%m')
        chu_de = (buoi['topic'] or '').strip()
        tieu_de = 'Bản ghi buổi %s đã có' % ngay
        noi_dung = ('Em xem lại buổi %s%s trên trang "Lớp của tôi" nhé.'
                    % (ngay, ' (%s)' % chu_de if chu_de else ''))
        for r in chua:
            notify(r['id'], 'ban_ghi_nhac', tieu_de, noi_dung, 'class_session', session_id,
                   coalesce_minutes=NHAC_GOP_PHUT)
        return Response({'daNhac': len(chua)})


class BaoLoiBanGhiView(APIView):
    """POST /api/sessions/<id>/ban-ghi/bao-loi — em báo link bản ghi hỏng.

    Bảng phân rã dòng 22: *"Báo lỗi record"*. Chuông về cho NGƯỜI DẠY của lớp
    (giảng viên + trợ giảng) — trợ giảng là người dán link nên là người sửa được.

    Chuông nói rõ AI báo: link hỏng với một em có thể chỉ là mạng nhà em ấy, nên
    người nhận cần hỏi lại được. Không gửi thư: đây không phải việc gấp, và một
    lời báo nhầm mà đã thành thư thì không rút lại được.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        r = _thuoc_lop(request.user.id, session_id)
        if not r:
            return Response({'detail': 'Không tìm thấy buổi học.'}, status=404)
        if not r['trong_lop']:
            return Response({'detail': 'Bạn không học lớp này.'}, status=403)
        if not (r['recording_url'] or '').strip():
            return Response({'detail': 'Buổi này chưa có bản ghi.'}, status=400)

        buoi = q1('SELECT starts_at FROM class_sessions WHERE id = %s', (session_id,))
        ngay = buoi['starts_at'].strftime('%d/%m')
        nguoi_day = q('''SELECT u.id FROM class_members m JOIN users u ON u.id = m.user_id
                          WHERE m.class_id = %s AND m.left_at IS NULL
                            AND NOT ''' + chi_hoc_vien('u') + '''
                          UNION
                         SELECT teacher_id AS id FROM classes
                          WHERE id = %s AND teacher_id IS NOT NULL''',
                      (r['class_id'], r['class_id']))
        ten = (request.user.name or 'Một học viên').strip()
        for n in nguoi_day:
            if n['id'] == request.user.id:
                continue
            # `title_multi` để cửa gộp ĐẾM thay vì đè: một em báo có thể là mạng
            # nhà em ấy, ba em báo cùng một buổi là link hỏng thật — và đó đúng là
            # điều view này sinh ra để phân biệt. Không có nó, `coalesce_count`
            # nằm im trong CSDL còn người dạy chỉ đọc được "1 em báo" (agent soát
            # 26/09); `notifications/service.py` đã đỡ sẵn nhánh đếm.
            notify(n['id'], 'ban_ghi_loi', 'Bản ghi buổi %s bị báo hỏng' % ngay,
                   '%s báo không mở được bản ghi buổi %s. Kiểm lại link giúp em nhé.' % (ten, ngay),
                   'class_session', session_id, coalesce_minutes=NHAC_GOP_PHUT,
                   title_multi='Bản ghi buổi %s: {n} em báo hỏng' % ngay)
        return Response({'daBao': True})
