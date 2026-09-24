"""Tín hiệu của miền `stats` — để miền khác nghe mà `stats` KHÔNG import ngược (25/09/2026).

Trước: `stats/views.py` import `chatbot.profile` chỉ để bỏ đệm hồ sơ của trợ lý sau khi học viên
ghi nhật ký, trong khi `chatbot` vốn đọc `stats` — vòng phụ thuộc duy nhất giữa các app backend
(graphify 25/09, `docs/THIET_KE_HE_THONG.md` việc S5). Nay `stats` chỉ BÁO; ai cần thì tự nghe.
"""
from django.dispatch import Signal

#: Nhật ký học của một người vừa được ghi, sửa hoặc xoá. Gửi kèm `user_id`.
nhat_ky_doi = Signal()
