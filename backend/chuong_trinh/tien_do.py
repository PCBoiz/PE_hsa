"""TIẾN ĐỘ theo khung chương trình — của cả lớp, và của từng em.

── LUẬT TÍNH (kế hoạch v2 E1, 25/09/2026) ─────────────────────────────────────

Mỗi buổi khung nặng bằng TỔNG trọng số các mục của nó.

  · PHẢI XONG (`phaiXong`) = tổng trọng số các buổi khung đã TỚI: có ít nhất một buổi
    học của lớp gắn vào nó và buổi ấy đã bắt đầu. Đếm mỗi buổi khung MỘT lần, dù gắn
    vào hai buổi học (nội dung dài chia hai buổi). Buổi đã huỷ mà vẫn gắn thì VẪN tính:
    nội dung của nó chưa dạy — đó đúng là "chậm", tới khi học vụ gắn nó sang buổi bù.
  · ĐÃ XONG (`daXong`) = tổng trọng số × tín chỉ của mục trong sổ đầu bài (đã dạy 1,
    dạy một phần 0,5, chưa dạy 0 — `tu_vung.TIN_CHI`). Một mục ghi ở nhiều buổi lấy
    mức CAO NHẤT: dạy dở buổi 3, dạy nốt buổi 4 là 1, không phải 1,5. Chỉ mục của
    ĐÚNG phiên bản lớp đang theo mới tính; mục giảng viên tự thêm (không trong khung)
    không tính. Dạy vượt kế hoạch thì `daXong` > `phaiXong` — lớp đi trước.
  · TRỄ (`treBuoi`) = (phải xong − đã xong) ÷ trọng số trung bình một buổi khung.
  · CHẬM khi phải xong > 0 VÀ (trễ ≥ 2 buổi HOẶC đã xong / phải xong < 80 %) — hai
    ngưỡng ở `tu_vung`.
  · CHƯA GHI SỔ (`chuaGhiSo`) = buổi đã dạy (đã bắt đầu, không huỷ) mà chưa có dòng
    `session_logs`. Chỉ tính cho lớp CÓ khung: lớp chưa nhận khung không bị nhắc ghi sổ
    cho mọi buổi từ đầu khoá.
  · % CỦA MỘT EM = trọng số đã xong trong các buổi em CÓ MẶT hoặc MUỘN (điểm danh)
    ÷ tổng trọng số của phiên bản. Buổi em vắng không tính cho em, dù lớp đã dạy.
    BUỔI BÙ TÍNH CHO BUỔI GỐC (§62e `makeup_for`): em có mặt ở buổi bù của buổi X thì
    được tính như có mặt ở X — sổ của X (và của chính buổi bù, nếu có) cộng cho em.

── SỐ CÂU TRUY VẤN KHÔNG THEO SỐ LỚP ───────────────────────────────────────────

`tien_do_lop` là MỘT câu cho bất kỳ số lớp nào (thêm một câu khi xin kèm danh sách
buổi chưa ghi sổ); `tien_do_em` là MỘT câu. Tổng quan trung tâm gọi nó cho ~400 lớp
(`tests_tien_do.py` đếm câu với 2 và 20 lớp).
"""
from decimal import Decimal

from chuong_trinh.tu_vung import NGUONG_TI_LE, NGUONG_TRE_BUOI, TIN_CHI
from common.clock import local_now
from common.db import q
from teaching.vocab import chi_hoc_vien

#: Số buổi chưa ghi sổ mỗi lớp trả kèm khi `kem_buoi` — "Việc hôm nay" là danh sách
#: việc, không phải sổ.
TRAN_BUOI_CHUA_GHI = 5


def sql_tin_chi(cot):
    """Biểu thức SQL đổi trạng thái mục → tín chỉ, dựng từ MỘT nguồn (`TIN_CHI`).
    Giá trị là hằng số trong mã, không phải dữ liệu người dùng — nhúng thẳng an toàn."""
    return 'CASE %s %s ELSE 0 END' % (
        cot, ' '.join("WHEN '%s' THEN %s" % (k, v) for k, v in TIN_CHI.items()))


#: (em, buổi được tính là em CÓ MẶT): buổi em có mặt / muộn, CỘNG buổi GỐC của mọi buổi
#: bù em có mặt (§62e) — buổi bù dạy lại nội dung buổi gốc. `dieu_kien` lọc trên
#: `a` (attendance) và `cs` (buổi em điểm danh); là chuỗi hằng trong mã, không phải dữ liệu.
_CO_MAT = """
    SELECT DISTINCT a.user_id, b.sid AS session_id
      FROM attendance a
      JOIN class_sessions cs ON cs.id = a.session_id
      CROSS JOIN LATERAL (VALUES (cs.id), (cs.makeup_for)) AS b(sid)
     WHERE a.status IN ('present', 'late') AND b.sid IS NOT NULL AND {dieu_kien}"""

#: CTE dùng chung: lớp có khung, trọng số từng buổi khung, tổng của phiên bản, phần
#: phải xong tới `nay`. Tham số có tên `ids`, `nay`.
_CTE = '''
lop AS (
    SELECT c.id AS class_id, c.syllabus_version_id AS vid, c.status AS trang_thai
      FROM classes c
     WHERE c.id = ANY(%(ids)s) AND c.syllabus_version_id IS NOT NULL
),
buoi_khung AS (
    SELECT ss.id, ss.version_id, COALESCE(SUM(i.weight), 0) AS w
      FROM syllabus_sessions ss
      LEFT JOIN syllabus_items i ON i.session_id = ss.id
     WHERE ss.version_id IN (SELECT vid FROM lop)
     GROUP BY ss.id, ss.version_id
),
tong AS (
    SELECT version_id, SUM(w) AS tong_w, COUNT(*) AS so_buoi_khung
      FROM buoi_khung GROUP BY version_id
),
den_han AS (
    SELECT l.class_id, SUM(bk.w) AS phai_w, COUNT(*) AS so_den_han
      FROM lop l
      JOIN buoi_khung bk ON bk.version_id = l.vid
     WHERE EXISTS (SELECT 1 FROM class_sessions cs
                    WHERE cs.class_id = l.class_id AND cs.syllabus_session_id = bk.id
                      AND cs.starts_at <= %(nay)s)
     GROUP BY l.class_id
)'''


def _so(v):
    return Decimal(v or 0)


def _pct(tu, mau):
    return None if not mau else round(float(tu * 100 / mau), 1)


def danh_gia(tong_w, so_buoi_khung, phai_w, xong_w):
    """Phần THUẦN của luật: bốn con số → trễ, tỉ lệ, cờ chậm. Tách ra để phép kiểm
    ngưỡng chạy không cần CSDL, và để mọi chỗ gọi dùng đúng một luật."""
    tong_w, phai_w, xong_w = _so(tong_w), _so(phai_w), _so(xong_w)
    tb = tong_w / so_buoi_khung if so_buoi_khung else Decimal(0)
    tre = (phai_w - xong_w) / tb if tb else None
    cham = bool(phai_w > 0 and (
        (tre is not None and tre >= NGUONG_TRE_BUOI) or xong_w < NGUONG_TI_LE * phai_w))
    return {
        'tongTrongSo': float(tong_w),
        'phaiXong': float(phai_w),
        'daXong': float(xong_w),
        # Trễ âm = đi trước kế hoạch. Làm tròn MỘT chữ số để HIỆN; cờ `cham` so trên
        # số chưa làm tròn.
        'treBuoi': None if tre is None else round(float(tre), 1),
        'tiLe': _pct(xong_w, phai_w),
        'pct': _pct(xong_w, tong_w),
        'keHoachPct': _pct(phai_w, tong_w),
        'cham': cham,
    }


def tien_do_lop(class_ids, nay=None, kem_buoi=False):
    """{class_id: tiến độ} cho các lớp CÓ khung trong `class_ids`. Lớp chưa nhận khung
    thì KHÔNG có khoá — bên gọi phân biệt "chưa có khung" với "0 %".

    `kem_buoi=True`: thêm `buoiChuaGhiSo` (tối đa `TRAN_BUOI_CHUA_GHI` buổi gần nhất
    mỗi lớp) — thêm đúng MỘT câu.
    """
    ids = sorted({int(i) for i in class_ids or []})
    if not ids:
        return {}
    nay = nay or local_now()
    tham = {'ids': ids, 'nay': nay}
    rows = q('WITH ' + _CTE + ''',
tin_chi AS (
    SELECT l.class_id, li.item_id, MAX(''' + sql_tin_chi('li.status') + ''') AS tc
      FROM lop l
      JOIN class_sessions cs ON cs.class_id = l.class_id
      JOIN session_log_items li ON li.session_id = cs.id
      JOIN syllabus_items i ON i.id = li.item_id
      JOIN syllabus_sessions ss ON ss.id = i.session_id AND ss.version_id = l.vid
     GROUP BY l.class_id, li.item_id
),
da_xong AS (
    SELECT t.class_id, SUM(t.tc * i.weight) AS xong_w
      FROM tin_chi t JOIN syllabus_items i ON i.id = t.item_id
     GROUP BY t.class_id
),
so_ghi AS (
    SELECT cs.class_id, COUNT(*) AS da_day,
           COUNT(*) FILTER (WHERE sl.session_id IS NULL) AS chua_ghi
      FROM class_sessions cs
      JOIN lop l ON l.class_id = cs.class_id
      LEFT JOIN session_logs sl ON sl.session_id = cs.id
     WHERE cs.status <> 'cancelled' AND cs.starts_at <= %(nay)s
     GROUP BY cs.class_id
)
SELECT l.class_id, l.vid, l.trang_thai, v.status AS trang_thai_ban, v.name AS ten_khung,
       COALESCE(t.tong_w, 0) AS tong_w, COALESCE(t.so_buoi_khung, 0) AS so_buoi_khung,
       COALESCE(d.phai_w, 0) AS phai_w, COALESCE(d.so_den_han, 0) AS so_den_han,
       COALESCE(x.xong_w, 0) AS xong_w,
       COALESCE(g.da_day, 0) AS da_day, COALESCE(g.chua_ghi, 0) AS chua_ghi
  FROM lop l
  JOIN syllabus_versions v ON v.id = l.vid
  LEFT JOIN tong t ON t.version_id = l.vid
  LEFT JOIN den_han d ON d.class_id = l.class_id
  LEFT JOIN da_xong x ON x.class_id = l.class_id
  LEFT JOIN so_ghi g ON g.class_id = l.class_id''', tham)

    ra = {}
    for r in rows:
        d = danh_gia(r['tong_w'], r['so_buoi_khung'], r['phai_w'], r['xong_w'])
        d.update({
            'versionId': r['vid'], 'tenKhung': r['ten_khung'], 'trangThaiBan': r['trang_thai_ban'],
            'trangThaiLop': r['trang_thai'],
            'soBuoiKhung': r['so_buoi_khung'], 'soBuoiDenHan': r['so_den_han'],
            'buoiDaDay': r['da_day'], 'chuaGhiSo': r['chua_ghi'],
            'nguong': {'treBuoi': float(NGUONG_TRE_BUOI), 'tiLe': round(float(NGUONG_TI_LE) * 100)},
        })
        if kem_buoi:
            d['buoiChuaGhiSo'] = []
        ra[r['class_id']] = d

    if kem_buoi and ra:
        for r in q('''SELECT id, class_id, starts_at, topic FROM (
                          SELECT cs.id, cs.class_id, cs.starts_at, cs.topic,
                                 ROW_NUMBER() OVER (PARTITION BY cs.class_id
                                                    ORDER BY cs.starts_at DESC, cs.id DESC) AS tt
                            FROM class_sessions cs
                           WHERE cs.class_id = ANY(%(ids)s) AND cs.status <> 'cancelled'
                             AND cs.starts_at <= %(nay)s
                             AND NOT EXISTS (SELECT 1 FROM session_logs sl
                                              WHERE sl.session_id = cs.id)) x
                       WHERE tt <= %(tran)s
                       ORDER BY starts_at DESC, id DESC''',
                   {'ids': sorted(ra), 'nay': nay, 'tran': TRAN_BUOI_CHUA_GHI}):
            ra[r['class_id']]['buoiChuaGhiSo'].append({
                'sessionId': r['id'], 'startsAt': r['starts_at'].isoformat(),
                'topic': r['topic']})
    return ra


def tien_do_em(user_id, class_ids, nay=None):
    """{class_id: tiến độ của EM này} cho các lớp CÓ khung. MỘT câu.

    `pct` = trọng số đã xong trong buổi em có mặt / muộn ÷ tổng trọng số phiên bản;
    `keHoachPct` = phần CẢ LỚP phải xong tới hôm nay — để em (và phụ huynh) so "mình"
    với "kế hoạch" trên cùng một thước.
    """
    ids = sorted({int(i) for i in class_ids or []})
    if not ids or not user_id:
        return {}
    nay = nay or local_now()
    rows = q('WITH ' + _CTE + ''',
co_mat AS (''' + _CO_MAT.format(dieu_kien='a.user_id = %(uid)s AND cs.class_id IN (SELECT class_id FROM lop)') + '''),
tin_chi AS (
    SELECT l.class_id, li.item_id, MAX(''' + sql_tin_chi('li.status') + ''') AS tc
      FROM lop l
      JOIN class_sessions cs ON cs.class_id = l.class_id
      JOIN co_mat m ON m.session_id = cs.id
      JOIN session_log_items li ON li.session_id = cs.id
      JOIN syllabus_items i ON i.id = li.item_id
      JOIN syllabus_sessions ss ON ss.id = i.session_id AND ss.version_id = l.vid
     GROUP BY l.class_id, li.item_id
),
da_xong AS (
    SELECT t.class_id, SUM(t.tc * i.weight) AS xong_w, COUNT(*) FILTER (WHERE t.tc > 0) AS so_muc
      FROM tin_chi t JOIN syllabus_items i ON i.id = t.item_id
     GROUP BY t.class_id
)
SELECT l.class_id, COALESCE(t.tong_w, 0) AS tong_w, COALESCE(d.phai_w, 0) AS phai_w,
       COALESCE(x.xong_w, 0) AS xong_w, COALESCE(x.so_muc, 0) AS so_muc,
       (SELECT COUNT(*) FROM syllabus_items i JOIN syllabus_sessions ss ON ss.id = i.session_id
         WHERE ss.version_id = l.vid) AS tong_muc
  FROM lop l
  LEFT JOIN tong t ON t.version_id = l.vid
  LEFT JOIN den_han d ON d.class_id = l.class_id
  LEFT JOIN da_xong x ON x.class_id = l.class_id''', {'ids': ids, 'nay': nay, 'uid': user_id})
    ra = {}
    for r in rows:
        tong_w, xong_w, phai_w = _so(r['tong_w']), _so(r['xong_w']), _so(r['phai_w'])
        ra[r['class_id']] = {
            'pct': _pct(xong_w, tong_w),
            'keHoachPct': _pct(phai_w, tong_w),
            'daXong': float(xong_w),
            'tongTrongSo': float(tong_w),
            'soMucDaHoc': r['so_muc'],
            'tongMuc': r['tong_muc'],
        }
    return ra


def tien_do_tung_em(class_id, nay=None):
    """[{userId, name, pct}] cho mọi HỌC VIÊN đang học lớp CÓ khung — MỘT câu. Nội bộ
    miền (màn "Chương trình lớp"); miền khác cần % của một em thì gọi `tien_do_em`.
    Cùng luật với `tien_do_em`: chỉ buổi em có mặt / muộn (buổi bù tính cho buổi gốc)."""
    rows = q('''WITH lop AS (
                    SELECT syllabus_version_id AS vid FROM classes
                     WHERE id = %(cid)s AND syllabus_version_id IS NOT NULL),
                tong AS (
                    SELECT COALESCE(SUM(i.weight), 0) AS tong_w
                      FROM syllabus_items i JOIN syllabus_sessions ss ON ss.id = i.session_id
                     WHERE ss.version_id = (SELECT vid FROM lop)),
                co_mat AS (''' + _CO_MAT.format(dieu_kien='cs.class_id = %(cid)s') + '''),
                tin_chi AS (
                    SELECT m.user_id, li.item_id, MAX(''' + sql_tin_chi('li.status') + ''') AS tc
                      FROM co_mat m
                      JOIN session_log_items li ON li.session_id = m.session_id
                      JOIN syllabus_items i ON i.id = li.item_id
                      JOIN syllabus_sessions ss ON ss.id = i.session_id
                                               AND ss.version_id = (SELECT vid FROM lop)
                     GROUP BY m.user_id, li.item_id)
                SELECT u.id, COALESCE(NULLIF(u.name, ''), u.email) AS ten,
                       COALESCE(SUM(t.tc * i.weight), 0) AS xong_w, (SELECT tong_w FROM tong) AS tong_w
                  FROM class_members m
                  JOIN users u ON u.id = m.user_id
                  LEFT JOIN tin_chi t ON t.user_id = u.id
                  LEFT JOIN syllabus_items i ON i.id = t.item_id
                 WHERE m.class_id = %(cid)s AND m.left_at IS NULL AND EXISTS (SELECT 1 FROM lop)
                   AND ''' + chi_hoc_vien('u') + '''
                 GROUP BY u.id, u.name, u.email
                 ORDER BY 3, 2''', {'cid': class_id})
    return [{'userId': r['id'], 'name': r['ten'], 'pct': _pct(_so(r['xong_w']), _so(r['tong_w']))}
            for r in rows]
