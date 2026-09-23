"""BỎ THI, PHA A (1.5A, 24/09/2026) — tuyến thi đã tháo, dữ liệu §57 đã đổi.

Anh Sơn chốt 24/09: "Bỏ mọi thứ về thi, giữ ngày thi HSA" — thi thử online, nhập
kết quả kỳ thi tại trung tâm, khối điểm thi. Pha A (đảo ngược được) chỉ THÁO
TUYẾN và đổi dữ liệu hiển thị: bảng giữ nguyên, mã của app thi còn tới pha C.

Tệp nằm ở `common/` chứ không ở `mockexam/`: pha C xoá cả thư mục ấy, còn phép
kiểm "tuyến thi không mở lại" thì phải sống qua pha C.

Frontend canh phần của nó ở `frontend/e2e/unit/bo-thi.test.mjs`.
"""
import uuid
from pathlib import Path

import pytest
from django.conf import settings
from django.db import connection
from django.urls import Resolver404, resolve

from common.db import q1, x

#: Mọi tuyến của tính năng thi. `1` đứng chỗ id — `resolve` chỉ so khuôn đường.
TUYEN_THI = [
    '/api/mock-exams',
    '/api/mock-exams/1/start',
    '/api/mock-exams/1/save',
    '/api/mock-exams/1/submit',
    '/api/mock-attempts',
    '/api/admin/mock-exams',
    '/api/admin/mock-exams/template.xlsx',
    '/api/admin/mock-exams/import',
    '/api/admin/mock-exams/1/publish',
    '/api/teach/classes/1/ket-qua-thi/doc',
    '/api/teach/classes/1/ket-qua-thi/ghi',
]


def test_tuyen_thi_da_thao_khoi_cay_tuyen():
    """Hỏi thẳng bộ phân giải tuyến, KHÔNG gọi qua HTTP rồi đọc mã 404.

    Vì sao: `POST /api/mock-exams/999999/start` trên mã CŨ cũng trả 404 — do view
    tự báo "không có đề". Phép kiểm theo mã HTTP sẽ xanh trên mã chưa tháo gì,
    tức là hằng đúng (RULES §19). `Resolver404` chỉ xảy ra khi tuyến thật sự vắng.
    """
    con = []
    for duong in TUYEN_THI:
        try:
            resolve(duong)
            con.append(duong)
        except Resolver404:
            pass
    assert not con, 'tuyến thi còn mở: %s' % con


def test_tuyen_ben_canh_van_con():
    """Đối chứng cho phép kiểm trên: bộ phân giải vẫn nhận tuyến của cùng hai app
    (lớp học, báo cáo phụ huynh). Thiếu đối chứng thì một cây tuyến hỏng toàn bộ
    cũng làm phép kiểm trên xanh."""
    for duong in ('/api/teach/classes/1/sessions',
                  '/api/teach/classes/1/students/2/parent-report',
                  '/api/admin/courses'):
        resolve(duong)          # ném Resolver404 là đỏ


@pytest.mark.django_db
def test_goi_that_tuyen_thi_ra_404(auth_api, admin_api):
    """Đi ĐỦ đường thật một lượt (middleware, `handler404` JSON): học viên mở danh
    sách đề và quản trị mở khu soạn đề đều nhận 404, không phải 200/403."""
    assert auth_api.get('/api/mock-exams').status_code == 404
    assert admin_api.get('/api/admin/mock-exams').status_code == 404


# ── Dữ liệu sinh ra từ mã: nhiệm vụ ngày + lộ trình ─────────────────────────

def test_seed_khong_con_nhiem_vu_thi_thu():
    """`seed_data` BẬT LẠI mọi nhiệm vụ nó liệt kê (`is_active = TRUE` ở nhánh
    ON CONFLICT) — nên §57 tắt `daily_mock` mà danh sách vẫn còn nó thì lần
    seed sau bật lại."""
    from common.management.commands.seed_data import HSA_MISSIONS

    ma = {m[0] for m in HSA_MISSIONS}
    assert 'daily_mock' not in ma, ma
    assert all(m[4] != 'mocks_today' for m in HSA_MISSIONS)
    chu = ' '.join('%s %s' % (m[1], m[2]) for m in HSA_MISSIONS).lower()
    assert 'thi thử' not in chu, chu


def test_lo_trinh_mau_khong_con_luyen_de_cbt():
    from common.management.commands.seed_data import HSA_ROADMAP_MERMAID, HSA_ROADMAP_NODES

    for chu in (HSA_ROADMAP_MERMAID, str(HSA_ROADMAP_NODES)):
        assert 'Luyện đề tổng (CBT)' not in chu
        assert 'Thi thử' not in chu
    assert 'Ôn tổng hợp' in HSA_ROADMAP_NODES['hsa_mock']['title']


@pytest.mark.django_db
def test_lo_trinh_sinh_tu_khao_sat_khong_con_luyen_de_cbt(temp_user):
    """Lộ trình cá nhân dựng lúc em nộp khảo sát (`accounts/views.py`). Gọi hàm
    dựng THẬT rồi đọc dòng đã ghi — không đọc hằng trong mã."""
    from accounts.views import _generate_user_roadmap

    _generate_user_roadmap(temp_user, None, {'target_score': 100})
    r = q1("SELECT nodes_json::text AS n, mermaid_def AS m FROM roadmaps WHERE id = %s",
           ('u%s_generated' % temp_user,))
    assert r, 'không dựng được lộ trình'
    for chu in (r['n'], r['m']):
        assert 'Luyện đề tổng (CBT)' not in chu
        assert 'Thi thử' not in chu
        assert 'Ôn tổng hợp' in chu


# ── §57 · dữ liệu đã nằm trong CSDL ─────────────────────────────────────────

def _cau_muc_57():
    """Đúng các câu của mục §57, tách bằng CHÍNH hàm `bootstrap_schema` dùng —
    tách kiểu khác là kiểm một thứ Render không chạy."""
    from common.management.commands.bootstrap_schema import _split_statements

    tho = (Path(settings.BASE_DIR) / 'sql' / 'legacy_schema.sql').read_text(encoding='utf-8')
    dau = tho.find('§57 ·')
    assert dau >= 0, 'legacy_schema.sql chưa có mục §57'
    cuoi = tho.find('§58 ·', dau)
    cau = _split_statements(tho[tho.rfind('\n', 0, dau):cuoi if cuoi > 0 else None])
    assert cau, 'mục §57 không có câu nào'
    return cau


def _chay(cau):
    so = []
    with connection.cursor() as cur:
        for c in cau:
            cur.execute(c)
            so.append(cur.rowcount)
    return so


@pytest.mark.django_db
def test_muc_57_tat_nhiem_vu_doi_nhan_lo_trinh_va_chay_lai_khong_doi_gi():
    """Dựng dữ liệu CŨ của chính mình (cuộn lại cuối test), chạy §57, đọc lại.

    Rồi chạy LẦN HAI: `bootstrap_schema` chạy cả tệp ở MỌI lần deploy, nên một
    mục không idempotent là một mục ghi lại dữ liệu mỗi lần đẩy mã.
    """
    x("""INSERT INTO missions (code, title, description, xp_reward, condition_type,
                               condition_value, sort_order, is_active)
         VALUES ('daily_mock', 'Làm 1 đề thi thử', 'x', 50, 'mocks_today', 1, 3, TRUE)
         ON CONFLICT (code) DO UPDATE SET is_active = TRUE""")
    x("""INSERT INTO missions (code, title, description, xp_reward, condition_type,
                               condition_value, sort_order, is_active)
         VALUES ('daily_xp', 'Kiếm 100 XP hôm nay', 'Cộng dồn từ bài học và đề thi thử.',
                 30, 'xp_today', 100, 2, TRUE)
         ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description""")
    rid = 'kiem_bo_thi_%s' % uuid.uuid4().hex[:10]
    # Hai bản mô tả CŨ: bản mẫu `seed_data` ghi "+", bản sinh từ khảo sát ghi "và".
    x("""INSERT INTO roadmaps (id, source, title, nodes_json, edges_json, mermaid_def)
         VALUES (%s, 'generated', 'kiem', %s::jsonb, '{}'::jsonb, %s)""",
      (rid,
       '{"hsa_mock": {"title": "5. Luyện đề tổng (CBT)", '
       '"desc": "Thi thử đầy đủ 150 câu trên máy, chấm điểm + phân tích."}, '
       '"hsa_x": {"title": "6. Luyện đề tổng (CBT)", '
       '"desc": "Thi thử đầy đủ 150 câu trên máy, chấm điểm và phân tích."}}',
       'flowchart TD\n    hsa_mock["5. Luyện đề tổng (CBT)"]\n'))

    _chay(_cau_muc_57())

    m = q1("SELECT is_active FROM missions WHERE code = 'daily_mock'")
    assert m['is_active'] is False, m
    d = q1("SELECT description FROM missions WHERE code = 'daily_xp'")
    assert 'thi thử' not in d['description'], d
    r = q1("SELECT nodes_json::text AS n, mermaid_def AS m FROM roadmaps WHERE id = %s", (rid,))
    for chu in (r['n'], r['m']):
        assert 'Luyện đề tổng (CBT)' not in chu, chu
        assert 'Thi thử' not in chu, chu
    assert r['n'].count('Ôn tổng hợp') == 2, r['n']

    lan_hai = _chay(_cau_muc_57())
    assert all(n == 0 for n in lan_hai), 'chạy lại §57 vẫn ghi: %s' % lan_hai


@pytest.mark.django_db
def test_kiem_luoc_do_nhin_thay_muc_57():
    """Mục mới mà thiếu dòng trong `kiem_luoc_do.MUC` thì lệnh ấy im lặng báo
    "sạch" cho một mục nó chưa hề nhìn tới."""
    from common.management.commands.kiem_luoc_do import MUC

    ma = {m[0] for m in MUC}
    assert {'§57a', '§57b'} <= ma, sorted(ma)
