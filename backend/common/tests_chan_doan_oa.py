"""Công cụ đo quyền của một Zalo OA — và các chốt hãm an toàn của nó.

KHÔNG lời gọi mạng thật nào: `requests` của `common.zalo` bị thay bằng bản giả.
Gọi Zalo thật trong bộ kiểm là gửi tin thật, tới người thật, mất phí thật.

── THỨ ĐANG ĐƯỢC CANH ────────────────────────────────────────────────────────

  1. Zalo trả **HTTP 200 kèm `error != 0`** cho lỗi nghiệp vụ. Chỉ nhìn mã HTTP
     là báo "gọi được" cho một lời gọi đã bị từ chối — đúng cái bẫy đã có sẵn
     trong `gui_zns` và phải giữ cho phần OA mới.
  2. Không có `--gui-toi` thì **không một lời gọi ghi nào** được thực hiện. Một
     lệnh chẩn đoán mà tự gửi tin là một lệnh không ai dám chạy.
  3. `ZALO_CHE_DO_THU=1` chặn được cả đường tin tư vấn, không chỉ đường ZNS.
  4. Chế độ thử **không được nhận là "gửi được"**: nó dừng trước khi Zalo kịp
     có ý kiến, nên nó không chứng minh gì về quyền gửi. Kết luận phải nói
     "chưa biết". Đây là chốt quan trọng nhất của tệp này — cả lệnh sinh ra để
     trả lời đúng một câu, và tự khen mình là cách hỏng câu trả lời ấy.
  5. Token **không bao giờ** được in đủ: đầu ra sẽ vào chat, vào tài liệu, vào
     ảnh chụp màn hình.
"""
import io

import pytest
from django.core.management import call_command

from common import zalo

#: Dài như token thật để phép kiểm che token có thứ thật để che.
THE = 'AbCdEf0123456789' * 4


class _PhanHoiGia:
    """Bản giả của `requests.Response` — chỉ hai thứ mã ở `zalo` thật sự đọc."""

    def __init__(self, than, status_code=200):
        self._than = than
        self.status_code = status_code

    def json(self):
        return self._than


@pytest.fixture
def mang(monkeypatch):
    """Thay `requests` của `common.zalo`. Trả về sổ ghi mọi lời gọi đã đi."""
    so = {'get': [], 'post': []}
    than = {'get': {'error': 0, 'data': {}}, 'post': {'error': 0, 'data': {}}}

    class Gia:
        RequestException = Exception

        @staticmethod
        def get(url, **kw):
            so['get'].append((url, kw))
            return _PhanHoiGia(than['get'])

        @staticmethod
        def post(url, **kw):
            so['post'].append((url, kw))
            return _PhanHoiGia(than['post'])

    monkeypatch.setattr(zalo, 'requests', Gia)
    so['than'] = than
    return so


def _chay(**kw):
    ra, loi = io.StringIO(), io.StringIO()
    call_command('chan_doan_oa', stdout=ra, stderr=loi, **kw)
    return ra.getvalue() + loi.getvalue()


# ── 1. HTTP 200 + error != 0 vẫn là HỎNG ────────────────────────────────────

def test_http_200_kem_ma_loi_van_la_hong(mang, monkeypatch):
    """Zalo báo lỗi nghiệp vụ bằng `error` trong thân, không bằng mã HTTP."""
    monkeypatch.delenv('ZALO_CHE_DO_THU', raising=False)
    mang['than']['get'] = {'error': -216, 'message': 'Access token is invalid'}

    ok, than, loi = zalo.thong_tin_oa(THE)

    assert ok is False, 'error=-216 mà vẫn coi là gọi được'
    assert 'Access token is invalid' in loi and '-216' in loi
    # Thân NGUYÊN VẸN phải trả về: màn chẩn đoán in đúng chữ Zalo nói, chứ
    # không in bản diễn giải — người đọc cần tra được mã lỗi ấy trên tài liệu.
    assert than == {'error': -216, 'message': 'Access token is invalid'}


def test_ma_loi_that_cua_zalo_hien_ra_trong_dau_ra(mang, monkeypatch):
    monkeypatch.delenv('ZALO_CHE_DO_THU', raising=False)
    mang['than']['get'] = {'error': -216, 'message': 'Access token is invalid'}

    ra = _chay(token=THE)

    assert '-216' in ra and 'Access token is invalid' in ra
    assert 'DỪNG ở bước 1' in ra
    # Hỏng ở bước 1 thì KHÔNG được đi tiếp: hai bước sau vô nghĩa, và in tiếp
    # ba khối "✗" chồng nhau chỉ làm người đọc mất dấu lỗi thật.
    assert len(mang['get']) == 1, 'đã hỏng ở getoa mà vẫn gọi tiếp'


# ── 2. Không có --gui-toi thì KHÔNG gửi gì ─────────────────────────────────

def test_khong_co_co_gui_thi_khong_mot_loi_goi_GHI_nao(mang, monkeypatch):
    monkeypatch.delenv('ZALO_CHE_DO_THU', raising=False)
    mang['than']['get'] = {'error': 0, 'data': {'name': 'OA Thu', 'oa_id': '1',
                                                'is_verified': False}}

    ra = _chay(token=THE)

    assert mang['post'] == [], 'lệnh chẩn đoán đã tự gửi tin khi không được bảo gửi'
    assert 'bỏ qua' in ra
    assert 'CHƯA biết' in ra


def test_co_co_gui_thi_moi_goi_message_cs(mang, monkeypatch):
    monkeypatch.delenv('ZALO_CHE_DO_THU', raising=False)
    mang['than']['get'] = {'error': 0, 'data': {'name': 'OA Thu', 'is_verified': False}}
    mang['than']['post'] = {'error': 0, 'data': {'message_id': 'm-1'}}

    # Truyền `chu` rõ ràng thay vì đọc lại nội dung từ chính request đã gửi:
    # đọc lại thì vế trái và vế phải của `assert` cùng đến từ một nguồn, và
    # phép kiểm đúng kể cả khi mã gửi đi một câu hoàn toàn khác.
    ra = _chay(token=THE, gui_toi='u-123', chu='xin chào')

    assert len(mang['post']) == 1
    url, kw = mang['post'][0]
    assert url.endswith('/v3.0/oa/message/cs')
    assert kw['json'] == {'recipient': {'user_id': 'u-123'},
                          'message': {'text': 'xin chào'}}
    assert kw['headers']['access_token'] == THE
    assert 'GỬI ĐƯỢC' in ra


# ── 3 & 4. Chế độ thử: chặn thật, và KHÔNG tự nhận là gửi được ─────────────

def test_che_do_thu_chan_duong_tin_tu_van(mang, monkeypatch):
    monkeypatch.setenv('ZALO_CHE_DO_THU', '1')

    ok, ma, loi = zalo.gui_tin_tu_van('u-999', 'chào')

    assert ok is True and loi is None
    assert ma.startswith('THU:')
    assert mang['post'] == [], 'chế độ thử vẫn gọi Zalo'


def test_che_do_thu_KHONG_duoc_ket_luan_la_gui_duoc(mang, monkeypatch):
    """Chốt hãm quan trọng nhất của lệnh.

    Chế độ thử dừng TRƯỚC khi Zalo kịp có ý kiến, nên nó không chứng minh gì
    về quyền gửi. Nếu kết luận đọc "GỬI ĐƯỢC" từ một lượt chạy chế độ thử thì
    cả lệnh trở thành thứ tự khen mình — và anh Sơn sẽ đi tạo OA, chờ 14 ngày,
    rồi mới biết là không gửi được.
    """
    monkeypatch.setenv('ZALO_CHE_DO_THU', '1')
    mang['than']['get'] = {'error': 0, 'data': {'name': 'OA Thu', 'is_verified': False}}

    ra = _chay(token=THE, gui_toi='u-123')

    assert 'CHƯA biết' in ra
    assert 'GỬI ĐƯỢC' not in ra
    assert mang['post'] == []


# ── 5. Không lộ token ──────────────────────────────────────────────────────

def test_khong_in_du_token(mang, monkeypatch):
    monkeypatch.delenv('ZALO_CHE_DO_THU', raising=False)
    mang['than']['get'] = {'error': 0, 'data': {'name': 'OA Thu', 'is_verified': False}}

    ra = _chay(token=THE)

    assert THE not in ra, 'đầu ra chứa nguyên access token'
    assert THE[:6] in ra, 'che kỹ tới mức không đối chiếu được token nào đang dùng'
    assert str(len(THE)) in ra


# ── Hồ sơ OA: đọc đúng trường Zalo trả về ─────────────────────────────────

def test_noi_thang_OA_da_xac_thuc_hay_chua(mang, monkeypatch):
    monkeypatch.delenv('ZALO_CHE_DO_THU', raising=False)
    mang['than']['get'] = {'error': 0, 'data': {'name': 'TopHSA', 'oa_id': '42',
                                                'is_verified': False,
                                                'package_name': 'Dùng thử'}}

    ra = _chay(token=THE)

    assert 'TopHSA' in ra and '42' in ra and 'Dùng thử' in ra
    assert 'CHƯA xác thực' in ra


def test_zalo_khong_tra_is_verified_thi_KHONG_doan(mang, monkeypatch):
    """Thiếu trường thì nói là thiếu, không mặc định thành False.

    `d.get('is_verified')` trả `None` khi Zalo đổi tên trường hoặc không gửi.
    Coi `None` như `False` là in ra "OA này CHƯA xác thực" cho một điều chưa
    hề đo được — và đó đúng là loại câu mà cả lệnh này sinh ra để dẹp bỏ.
    """
    monkeypatch.delenv('ZALO_CHE_DO_THU', raising=False)
    mang['than']['get'] = {'error': 0, 'data': {'name': 'TopHSA'}}

    ra = _chay(token=THE)

    assert 'CHƯA xác thực' not in ra
    assert 'không trả trường is_verified' in ra


def test_thieu_token_thi_dung_va_chi_duong(mang):
    ra = _chay(token='')

    assert 'DỪNG' in ra and 'developers.zalo.me' in ra
    assert mang['get'] == [] and mang['post'] == []
