"""TRÙNG LỊCH GIỮA CÁC LỚP — bảng yêu cầu TopHSA (tab "Nhi" #4), 23/09/2026.

`sessions._overlap_warning` đã canh trùng giờ TRONG MỘT LỚP. Ba kiểu trùng mà
nó không thấy — và đều đắt hơn nhiều khi phát hiện muộn:

  giảng-viên  cùng giảng viên có buổi ở LỚP KHÁC chồng giờ → một lớp ngồi chờ.
  hoc-vien    một em đang học CẢ HAI lớp, hai buổi chồng giờ → em phải bỏ một.
  phong       hai buổi OFFLINE cùng PHÒNG chồng giờ → hai lớp tới một phòng.

CÙNG TRIẾT LÝ với `_overlap_warning`: CẢNH BÁO chứ không chặn. Trung tâm có
những ca trùng CÓ CHỦ Ý (giảng viên dạy ghép hai lớp một phòng, em học bù ở lớp
khác) — chặn là chặn nhầm việc có thật. Nhưng trả về từng ca có TÊN, để người
sắp lịch quyết định trong một giây chứ không phải đi dò.

Buổi đã HUỶ không chiếm giờ của ai. Hình thức và phòng của một buổi lấy theo
§53: `coalesce(buổi, lớp)` — buổi để trống là theo lớp.
"""
from common.db import q

#: Độ dài mặc định khi buổi không ghi — cùng số với `sessions.DEFAULT_SESSION_MINUTES`.
PHUT_MAC_DINH = 90

#: Tối đa bao nhiêu ca mỗi loại — đủ để hiểu chuyện, không thành một trang dài.
TRAN_MOI_LOAI = 5

_CHONG_GIO = '''s.status <> 'cancelled'
    AND s.starts_at < %(bat_dau)s + (%(phut)s::int * INTERVAL '1 minute')
    AND s.starts_at + (COALESCE(s.duration_minutes, %(mac_dinh)s::int) * INTERVAL '1 minute') > %(bat_dau)s
    AND (%(bo_qua)s::int IS NULL OR s.id <> %(bo_qua)s::int)'''


def tim_trung(class_id, starts_at, minutes, bo_qua_id=None, mode=None, room=None):
    """Mọi ca trùng của một buổi (sắp tạo hoặc vừa dời) ở LỚP KHÁC.

    `mode`/`room` là giá trị của CHÍNH buổi ấy (None = theo lớp). Trả danh sách
    `{loai, buoiId, lopId, lop, batDau, soEm?, tenEm?}` — rỗng nếu không trùng.
    """
    ts = {'bat_dau': starts_at, 'phut': minutes or PHUT_MAC_DINH, 'mac_dinh': PHUT_MAC_DINH,
          'bo_qua': bo_qua_id, 'lop': class_id, 'tran': TRAN_MOI_LOAI}
    ra = []

    for r in q('''SELECT s.id, s.starts_at, c.id AS lop_id, c.name
                    FROM class_sessions s JOIN classes c ON c.id = s.class_id
                   WHERE c.teacher_id IS NOT NULL
                     AND c.teacher_id = (SELECT teacher_id FROM classes WHERE id = %(lop)s)
                     AND s.class_id <> %(lop)s AND ''' + _CHONG_GIO + '''
                   ORDER BY s.starts_at LIMIT %(tran)s''', ts):
        ra.append({'loai': 'giang-vien', 'buoiId': r['id'], 'lopId': r['lop_id'], 'lop': r['name'],
                   'batDau': r['starts_at'].isoformat()})

    for r in q('''SELECT s.id, s.starts_at, c.id AS lop_id, c.name,
                         count(DISTINCT u.id) AS so_em,
                         (array_agg(DISTINCT coalesce(u.name, u.email)))[1:3] AS ten_em
                    FROM class_members m1
                    JOIN class_members m2 ON m2.user_id = m1.user_id AND m2.class_id <> m1.class_id
                                         AND m2.left_at IS NULL
                    JOIN users u ON u.id = m1.user_id AND u.role = 'Học viên'
                    JOIN class_sessions s ON s.class_id = m2.class_id
                    JOIN classes c ON c.id = s.class_id
                   WHERE m1.class_id = %(lop)s AND m1.left_at IS NULL AND ''' + _CHONG_GIO + '''
                   GROUP BY s.id, s.starts_at, c.id, c.name
                   ORDER BY s.starts_at LIMIT %(tran)s''', ts):
        ra.append({'loai': 'hoc-vien', 'buoiId': r['id'], 'lopId': r['lop_id'], 'lop': r['name'],
                   'batDau': r['starts_at'].isoformat(), 'soEm': r['so_em'], 'tenEm': r['ten_em']})

    # Phòng: chỉ khi buổi NÀY là offline và có phòng (sau khi kế thừa lớp).
    lop = q('SELECT mode, room FROM classes WHERE id = %(lop)s', ts)
    hinh_thuc = mode or (lop[0]['mode'] if lop else None)
    phong = (room or (lop[0]['room'] if lop else None) or '').strip()
    if hinh_thuc == 'offline' and phong:
        ts['phong'] = phong.lower()
        for r in q('''SELECT s.id, s.starts_at, c.id AS lop_id, c.name
                        FROM class_sessions s JOIN classes c ON c.id = s.class_id
                       WHERE s.class_id <> %(lop)s
                         AND coalesce(s.mode, c.mode) = 'offline'
                         AND lower(trim(coalesce(s.room, c.room))) = %(phong)s AND ''' + _CHONG_GIO + '''
                       ORDER BY s.starts_at LIMIT %(tran)s''', ts):
            ra.append({'loai': 'phong', 'buoiId': r['id'], 'lopId': r['lop_id'], 'lop': r['name'],
                       'batDau': r['starts_at'].isoformat(), 'phong': phong})
    return ra


def tim_trung_nhieu(class_id, cac_bat_dau, minutes):
    """Như `tim_trung` nhưng cho CẢ MỘT KỲ sinh lịch một lúc: `{bat_dau: [ca trùng…]}`.

    Ba câu truy vấn cho mọi buổi (giảng viên, học viên, phòng) chứ không phải ba
    câu MỖI buổi — một kỳ 30 buổi là 90 lượt Neon (~22 giây) nếu làm từng buổi.
    Buổi sinh ra lấy hình thức / phòng của LỚP (sinh lịch không đặt riêng từng buổi).
    """
    if not cac_bat_dau:
        return {}
    ts = {'ds': list(cac_bat_dau), 'phut': minutes or PHUT_MAC_DINH, 'mac_dinh': PHUT_MAC_DINH,
          'lop': class_id}
    chong = '''s.status <> 'cancelled'
        AND s.starts_at < u.bat_dau + (%(phut)s::int * INTERVAL '1 minute')
        AND s.starts_at + (COALESCE(s.duration_minutes, %(mac_dinh)s::int) * INTERVAL '1 minute') > u.bat_dau'''
    ra = {}

    def them(bat_dau, muc):
        ra.setdefault(bat_dau, []).append(muc)

    for r in q('''WITH u(bat_dau) AS (SELECT unnest(%(ds)s::timestamp[]))
                  SELECT DISTINCT u.bat_dau, c.id, c.name
                    FROM u JOIN class_sessions s ON ''' + chong + '''
                    JOIN classes c ON c.id = s.class_id
                   WHERE c.teacher_id IS NOT NULL AND s.class_id <> %(lop)s
                     AND c.teacher_id = (SELECT teacher_id FROM classes WHERE id = %(lop)s)''', ts):
        them(r['bat_dau'], {'loai': 'giang-vien', 'lopId': r['id'], 'lop': r['name']})

    for r in q('''WITH u(bat_dau) AS (SELECT unnest(%(ds)s::timestamp[]))
                  SELECT u.bat_dau, c.id, c.name, count(DISTINCT m1.user_id) AS so_em
                    FROM u
                    JOIN class_members m1 ON m1.class_id = %(lop)s AND m1.left_at IS NULL
                    JOIN users us ON us.id = m1.user_id AND us.role = 'Học viên'
                    JOIN class_members m2 ON m2.user_id = m1.user_id AND m2.class_id <> m1.class_id
                                         AND m2.left_at IS NULL
                    JOIN class_sessions s ON s.class_id = m2.class_id AND ''' + chong + '''
                    JOIN classes c ON c.id = s.class_id
                   GROUP BY u.bat_dau, c.id, c.name''', ts):
        them(r['bat_dau'], {'loai': 'hoc-vien', 'lopId': r['id'], 'lop': r['name'], 'soEm': r['so_em']})

    lop = q('SELECT mode, room FROM classes WHERE id = %(lop)s', ts)
    phong = ((lop[0]['room'] if lop else None) or '').strip()
    if lop and lop[0]['mode'] == 'offline' and phong:
        ts['phong'] = phong.lower()
        for r in q('''WITH u(bat_dau) AS (SELECT unnest(%(ds)s::timestamp[]))
                      SELECT DISTINCT u.bat_dau, c.id, c.name
                        FROM u JOIN class_sessions s ON ''' + chong + '''
                        JOIN classes c ON c.id = s.class_id
                       WHERE s.class_id <> %(lop)s AND coalesce(s.mode, c.mode) = 'offline'
                         AND lower(trim(coalesce(s.room, c.room))) = %(phong)s''', ts):
            them(r['bat_dau'], {'loai': 'phong', 'lopId': r['id'], 'lop': r['name'], 'phong': phong})
    return ra


def cau_canh_bao(ds):
    """Một câu tiếng Việt cho danh sách ca trùng — hoặc None nếu không có."""
    if not ds:
        return None
    phan = []
    for t in ds:
        gio = '%s/%s %s' % (t['batDau'][8:10], t['batDau'][5:7], t['batDau'][11:16])
        if t['loai'] == 'giang-vien':
            phan.append('giảng viên đang dạy lớp %s lúc %s' % (t['lop'], gio))
        elif t['loai'] == 'hoc-vien':
            ten = ', '.join(t.get('tenEm') or [])
            phan.append('%d em (%s%s) đang học lớp %s lúc %s'
                        % (t['soEm'], ten, '…' if t['soEm'] > len(t.get('tenEm') or []) else '',
                           t['lop'], gio))
        else:
            phan.append('phòng %s đã có lớp %s lúc %s' % (t['phong'], t['lop'], gio))
    return 'Trùng lịch: %s. Buổi vẫn được lưu — kiểm tra lại nếu không cố ý.' % '; '.join(phan)
