"""Đệm hồ sơ học của trợ lý AI phải bỏ ngay khi học viên ghi/xoá nhật ký (25/09/2026).

Trợ lý đọc nhật ký để tư vấn (`chatbot/profile.py`, đệm theo người). `stats` báo "nhật ký đổi" qua
tín hiệu `stats.tin_hieu.nhat_ky_doi`; `chatbot` tự nghe (`ChatbotConfig.ready`) — `stats` không import
ngược `chatbot` nữa (phá vòng phụ thuộc stats ↔ chatbot, việc S5 của `docs/THIET_KE_HE_THONG.md`).
Đi qua API thật `/api/hsa/journal`.
"""
import pytest

from common.clock import local_today

pytestmark = pytest.mark.django_db


def _dem_san(uid):
    from chatbot import profile
    profile.learner_profile(uid)
    assert uid in profile._cache, 'phải có hồ sơ trong đệm trước khi thử'
    return profile


def test_ghi_nhat_ky_bo_dem_ho_so(auth_api, temp_user):
    profile = _dem_san(temp_user)
    r = auth_api.put('/api/hsa/journal', {'date': local_today().isoformat(), 'minutes': 30,
                                          'topic': 'Tỉ lệ'}, format='json')
    assert r.status_code == 200, r.data
    assert temp_user not in profile._cache, 'trợ lý phải thấy nhật ký vừa ghi'


def test_xoa_nhat_ky_bo_dem_ho_so(auth_api, temp_user):
    hom_nay = local_today().isoformat()
    assert auth_api.put('/api/hsa/journal', {'date': hom_nay, 'minutes': 20}, format='json').status_code == 200
    profile = _dem_san(temp_user)
    r = auth_api.delete('/api/hsa/journal?date=%s' % hom_nay)
    assert r.status_code == 200, r.data
    assert temp_user not in profile._cache, 'trợ lý phải thấy nhật ký vừa xoá'


def test_stats_khong_import_chatbot():
    """Chiều phụ thuộc đúng: chatbot đọc stats; stats không biết chatbot."""
    import ast
    from pathlib import Path

    from django.conf import settings
    for tep in (Path(settings.BASE_DIR) / 'stats').rglob('*.py'):
        if 'tests' in tep.name:
            continue
        cay = ast.parse(tep.read_text(encoding='utf-8'))
        for nut in ast.walk(cay):
            ten = (nut.module or '') if isinstance(nut, ast.ImportFrom) else \
                  ' '.join(a.name for a in nut.names) if isinstance(nut, ast.Import) else ''
            assert not ten.startswith('chatbot'), '%s import %s' % (tep.name, ten)
