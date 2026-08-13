"""Một đồng hồ duy nhất cho toàn app: giờ Việt Nam.

Trước 2026-08-14 tồn tại HAI đồng hồ lệch nhau 7 tiếng:
  - Python/Django: ``date.today()`` theo TIME_ZONE = Asia/Ho_Chi_Minh
  - SQL thô: ``now()`` do Neon trả, tức UTC

Nên ``lesson_progress.completed_at::date`` (UTC) so với ``date.today()`` (VN)
lệch một ngày trong khung 0h–7h sáng giờ Việt Nam: học viên học lúc 1h sáng thì
nhiệm vụ "học 1 bài hôm nay" đếm 0/1, và nhật ký XP ghi sang ngày hôm trước.

Mọi mốc thời gian NGƯỜI DÙNG nhìn thấy (ngày học, chuỗi ngày, nhiệm vụ ngày,
BXH tuần) phải đi qua hai hàm dưới đây, không dùng ``date.today()`` hay SQL
``now()`` trực tiếp nữa.
"""
from django.utils import timezone


def local_today():
    """Ngày hôm nay theo giờ Việt Nam."""
    return timezone.localdate()


def local_now():
    """Thời điểm hiện tại theo giờ Việt Nam, dạng naive.

    Naive vì các cột thời gian của schema legacy là ``TIMESTAMP WITHOUT TIME
    ZONE`` — ghi giá trị có tzinfo vào đó sẽ bị Postgres quy đổi lại về UTC,
    đúng cái lỗi ta đang sửa.
    """
    return timezone.localtime().replace(tzinfo=None)
