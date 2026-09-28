"""Bộ sinh tệp lịch (.ics) — §71, 26/09/2026.

Những phép kiểm ở đây KHÔNG chạm CSDL: chúng đưa sẵn danh sách buổi rồi soi đúng
chuỗi trả ra. Lý do: thứ hay hỏng ở .ics không phải câu SQL mà là dạng chuỗi —
ứng dụng lịch không báo lỗi, nó chỉ IM LẶNG bỏ qua tệp sai, và khi ấy người dùng
chỉ thấy "lịch trống" chứ không thấy dòng nào giải thích.
"""
from datetime import datetime, timezone

import pytest

from lich.ics import dung_ics, thoat_chu


def _buoi(**kw):
    m = {'id': 1, 'starts_at': datetime(2026, 9, 28, 19, 30, tzinfo=timezone.utc), 'duration_minutes': 90,
         'lop': 'HSA-01', 'topic': 'Tỉ lệ & phần trăm', 'status': 'planned',
         'mode_hl': 'online', 'room_hl': None, 'meeting_url': 'https://zoom.us/j/123',
         'giang_vien': 'Nguyễn Văn A', 'updated_at': None}
    m.update(kw)
    return m


def _dong(vb):
    """Bỏ gấp dòng của RFC 5545 (dòng nối bắt đầu bằng một dấu cách) rồi tách dòng."""
    return vb.replace('\r\n ', '').split('\r\n')


def test_khung_tep_va_ket_thuc_bang_crlf():
    vb = dung_ics([_buoi()], 'Lịch học của tôi')
    assert vb.startswith('BEGIN:VCALENDAR\r\n')
    assert vb.endswith('END:VCALENDAR\r\n')
    d = _dong(vb)
    assert 'VERSION:2.0' in d
    assert 'BEGIN:VEVENT' in d and 'END:VEVENT' in d


def test_gio_viet_nam_doi_sang_utc():
    # 19:30 giờ Việt Nam = 12:30 UTC; buổi 90 phút kết thúc 21:00 VN = 14:00 UTC.
    d = _dong(dung_ics([_buoi()], 'x'))
    assert 'DTSTART:20260928T123000Z' in d
    assert 'DTEND:20260928T140000Z' in d


def test_buoi_huy_van_co_mat_nhung_danh_dau_da_huy():
    """Buổi huỷ phải ĐI THEO vào lịch với STATUS:CANCELLED.

    Bỏ hẳn buổi huỷ ra khỏi tệp thì Google Calendar giữ nguyên buổi cũ đã tải lần
    trước — em vẫn tới lớp đúng giờ một buổi không còn tồn tại.
    """
    d = _dong(dung_ics([_buoi(status='cancelled')], 'x'))
    assert 'STATUS:CANCELLED' in d
    assert any(l.startswith('UID:') for l in d)


def test_uid_on_dinh_theo_buoi():
    a = _dong(dung_ics([_buoi()], 'x'))
    b = _dong(dung_ics([_buoi(topic='Đổi tên khác')], 'x'))
    uid = [l for l in a if l.startswith('UID:')][0]
    assert uid == [l for l in b if l.startswith('UID:')][0]
    assert uid.endswith('@pe-hsa')


def test_thoat_dau_phay_cham_phay_va_xuong_dong():
    # RFC 5545: bốn ký tự này phải thoát, không thì ứng dụng lịch cắt nhầm trường.
    assert thoat_chu('a,b') == 'a\\,b'
    assert thoat_chu('a;b') == 'a\\;b'
    assert thoat_chu('a\\b') == 'a\\\\b'
    assert thoat_chu('a\nb') == 'a\\nb'


def test_ten_lop_co_dau_phay_khong_lam_vo_dong():
    d = _dong(dung_ics([_buoi(lop='HSA-01, ca tối', topic=None)], 'x'))
    tom = [l for l in d if l.startswith('SUMMARY:')][0]
    assert tom == 'SUMMARY:HSA-01\\, ca tối'


def test_link_zoom_nam_trong_mo_ta_va_o_dia_diem_truc_tuyen():
    d = _dong(dung_ics([_buoi()], 'x'))
    assert any('https://zoom.us/j/123' in l for l in d)
    assert 'LOCATION:Trực tuyến' in d


def test_hoc_tai_trung_tam_thi_dia_diem_la_phong():
    d = _dong(dung_ics([_buoi(mode_hl='offline', room_hl='P.301', meeting_url=None)], 'x'))
    assert 'LOCATION:P.301' in d


def test_dong_dai_duoc_gap_dung_75_octet():
    """Dòng quá 75 octet phải gấp; octet chứ không phải ký tự — chữ Việt 2–3 byte."""
    dai = 'Chuyên đề ôn tập tổng hợp phần tư duy định lượng và xử lý số liệu dài thật là dài'
    vb = dung_ics([_buoi(topic=dai)], 'x')
    for dong in vb.split('\r\n'):
        assert len(dong.encode('utf-8')) <= 75, dong
    assert dai in _dong(vb)[[i for i, l in enumerate(_dong(vb)) if l.startswith('SUMMARY:')][0]]


def test_ten_lich_vao_x_wr_calname():
    d = _dong(dung_ics([_buoi()], 'Lịch dạy của tôi'))
    assert 'X-WR-CALNAME:Lịch dạy của tôi' in d


def test_khong_co_buoi_nao_van_ra_tep_hop_le():
    vb = dung_ics([], 'Lịch trống')
    assert vb.startswith('BEGIN:VCALENDAR\r\n') and vb.endswith('END:VCALENDAR\r\n')
    assert 'BEGIN:VEVENT' not in vb


# Giờ UTC, không phải giờ Việt Nam: 19:30 VN + 60' = 20:30 VN = 13:30 UTC;
# + 45' = 20:15 VN = 13:15 UTC. (Bản đầu của phép kiểm này ghi giờ VN nên đỏ oan.)
@pytest.mark.parametrize('phut,ket', [(None, '133000Z'), (45, '131500Z')])
def test_buoi_khong_ghi_thoi_luong_mac_dinh_mot_tieng(phut, ket):
    """Thiếu `duration_minutes` thì lấy 60 phút — sự kiện KHÔNG có giờ kết thúc sẽ
    bị một số ứng dụng lịch coi là cả ngày."""
    d = _dong(dung_ics([_buoi(duration_minutes=phut)], 'x'))
    assert any(l == 'DTEND:20260928T' + ket for l in d), d
