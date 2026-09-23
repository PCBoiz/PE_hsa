"""Hàng rào CSDL production (H1, 24/09/2026) — `common/hang_rao_csdl.py`.

Không cần CSDL: so điểm cuối là phép toán trên chuỗi, còn hai chỗ nối dây
(`conftest.pytest_configure`, `CommonConfig.ready`) được gọi thẳng với biến môi
trường giả lập "host đang dùng chính là production".
"""
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured

from common import hang_rao_csdl as hr

DEV = 'ep-little-water-axrfb9a2-pooler.c-4.us-east-2.aws.neon.tech'
PROD = 'ep-billowing-fog-a1b2c3d4-pooler.c-4.us-east-2.aws.neon.tech'


def test_diem_cuoi_bo_pooler_hoa_thuong_va_nhan_ca_chuoi_ket_noi():
    assert hr.diem_cuoi(PROD) == 'ep-billowing-fog-a1b2c3d4'
    assert hr.diem_cuoi('EP-BILLOWING-FOG-A1B2C3D4.c-4.us-east-2.aws.neon.tech') == 'ep-billowing-fog-a1b2c3d4'
    assert hr.diem_cuoi('postgresql://u:matkhau@%s/neondb?sslmode=require' % PROD) == 'ep-billowing-fog-a1b2c3d4'
    assert hr.diem_cuoi('') == ''


def test_cung_diem_cuoi_du_khac_pooler_la_production():
    # Máy dev dùng host -pooler, người dán biến có thể lấy host trực tiếp (hoặc ngược lại).
    assert hr.dang_tro_production(host=PROD, host_production=PROD.replace('-pooler', ''))
    assert hr.dang_tro_production(host=PROD.replace('-pooler', ''), host_production=PROD)
    assert not hr.dang_tro_production(host=DEV, host_production=PROD)


def test_chua_dat_bien_thi_khong_chan():
    assert not hr.dang_tro_production(host=PROD, host_production='')
    assert not hr.dang_tro_production(host='', host_production=PROD)


def test_cau_loi_khong_lo_mat_khau_va_co_loi_thoat(monkeypatch):
    monkeypatch.setattr(hr, 'host_dang_dung', lambda: PROD)
    monkeypatch.setenv(hr.BIEN_PRODUCTION, 'postgresql://u:MATKHAU_BI_MAT@%s/neondb' % PROD)
    monkeypatch.delenv(hr.BIEN_CHO_PHEP, raising=False)
    loi = hr.loi_neu_production('pytest')
    assert loi and 'ep-billowing-fog-a1b2c3d4' in loi and 'MATKHAU_BI_MAT' not in loi
    monkeypatch.setenv(hr.BIEN_CHO_PHEP, '1')
    assert hr.loi_neu_production('pytest') is None


def test_pytest_dung_khi_tro_production(monkeypatch):
    import conftest
    monkeypatch.setattr(hr, 'host_dang_dung', lambda: PROD)
    monkeypatch.setenv(hr.BIEN_PRODUCTION, PROD)
    monkeypatch.delenv(hr.BIEN_CHO_PHEP, raising=False)
    with pytest.raises(pytest.exit.Exception):
        conftest.pytest_configure(None)


def test_runserver_tu_choi_khi_tro_production(monkeypatch):
    from django.apps import apps
    monkeypatch.setattr(hr, 'host_dang_dung', lambda: PROD)
    monkeypatch.setenv(hr.BIEN_PRODUCTION, PROD)
    monkeypatch.delenv(hr.BIEN_CHO_PHEP, raising=False)
    monkeypatch.setattr(sys, 'argv', ['manage.py', 'runserver', '--noreload'])
    # Chặn TRƯỚC khi luồng giữ ấm kịp chạy — không có lối nào vào production.
    monkeypatch.setattr('common.keepalive.start_keepalive', lambda: pytest.fail('giữ ấm chạy trước hàng rào'))
    with pytest.raises(ImproperlyConfigured):
        apps.get_app_config('common').ready()
