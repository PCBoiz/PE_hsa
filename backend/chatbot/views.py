"""Endpoint /api/chat — Trợ lý HSA. Key DeepSeek nằm SERVER-SIDE (env), không lộ
ra frontend như bản Gemini cũ.

Context engineering: bơm hồ sơ học tập THẬT của học viên (chatbot/profile.py) +
bài đang mở. Trước 24/08 chỗ này tự tính "hợp phần yếu nhất" từ lượt thi thử gần
nhất — một phép tính thứ ba về điểm yếu, thô hơn bản đồ năng lực và có thể mâu
thuẫn với con số Trang của tôi đang hiện cho cùng học viên đó.
"""
import base64
import logging

from django.conf import settings
from openai import APIStatusError
from rest_framework.response import Response

from chatbot.graph import chat
from chatbot.profile import learner_profile
from common.db import q1
from common.views import NguoiDungView

log = logging.getLogger(__name__)

# Lỗi CÓ MÃ từ DeepSeek → câu người đọc hiểu, và một dòng log để trung tâm biết.
# 402 là chuyện sẽ xảy ra: số dư khoá đo 20/09/2026 là 2,54 USD, một lớp dùng thật
# thì vài ngày hết. Trước đó mọi lỗi ra "Trợ lý gặp sự cố khi trả lời: Error
# code: 402 - {…'Insufficient Balance'…}" — học viên đọc JSON, không ai được báo.
_LOI_CO_MA = {
    402: 'Trợ lý tạm nghỉ vì dịch vụ AI hết hạn mức — trung tâm đã được báo. Bạn cứ học tiếp, mai hỏi lại nhé.',
    401: 'Trợ lý chưa được cấu hình đúng (khoá dịch vụ AI không hợp lệ) — trung tâm đã được báo.',
    429: 'Trợ lý đang quá tải, bạn thử lại sau một phút nhé.',
}


def _user_context(user):
    return learner_profile(user.id, getattr(user, "name", None))


# Ngữ cảnh trang do client gửi: chỉ nhận đúng các khoá này, cắt độ dài, để nội
# dung người dùng bơm vào không làm phình/điều khiển system prompt.
_CTX_FIELDS = {
    "lesson_index": ("Bài số", 8),
    "lesson_title": ("Tên bài", 120),
    "lesson_topic": ("Chủ đề", 80),
    "step": ("Đang ở bước", 40),
    "formula": ("Công thức của bài", 200),
}


def _ten_khoa(course_id):
    """Tên khoá TRA TỪ CSDL, không lấy theo lời client.

    Trước 05/09/2026 client gửi thẳng `course_title`. Nó lấy được vì cả 76 bài
    khi ấy nằm trong một tệp JS có sẵn tên khoá; nay nội dung ở CSDL và trang
    bài học KHÔNG hiện tên khoá ở đâu cả, nên mọi cách lấy phía client đều là
    bịa. Ở đây thì chỉ là một lần đọc `courses` — chỗ giữ sự thật.

    Kèm theo là một điều nhỏ mà đáng: client hết cửa nhét chuỗi tuỳ ý vào một
    dòng system prompt. `course_id` vẫn do client gửi, nhưng nó chỉ dùng làm
    tham số truy vấn — sai id thì không có dòng nào, chứ không chèn được gì.
    """
    cid = str(course_id or "").strip()[:64]
    if not cid:
        return ""
    r = q1("SELECT title FROM courses WHERE id = %s", (cid,))
    return (r or {}).get("title") or ""


def _lesson_context(page_context):
    """Mô tả gọn bài học viên đang mở, để trợ lý bám đúng nội dung đang học."""
    if not isinstance(page_context, dict):
        return ""
    lines = []
    ten = _ten_khoa(page_context.get("course_id"))
    if ten:
        lines.append(f"- Khoá đang học: {ten[:80]}")
    for key, (label, limit) in _CTX_FIELDS.items():
        val = page_context.get(key)
        if val in (None, "", []):
            continue
        lines.append(f"- {label}: {str(val)[:limit]}")
    pts = page_context.get("key_points")
    if isinstance(pts, list) and pts:
        joined = "; ".join(str(p)[:160] for p in pts[:6])
        lines.append(f"- Ý chính của bài: {joined}")
    if not lines:
        return ""
    return (
        "Học viên ĐANG mở bài học dưới đây. Hãy bám sát bài này khi trả lời "
        "(giảng lại đúng phần lý thuyết, lấy ví dụ cùng dạng, nhắc bẫy hay gặp):\n"
        + "\n".join(lines)
    )


# Ảnh đính kèm: data URL do trình duyệt gửi, đã thu nhỏ về ≤1280px JPEG
# (`chatbot.js::handleChatbotImageUpload`) nên thường 100–400 kB. Trần 1,6 triệu
# ký tự ≈ 1,2 MB nhị phân: dưới DATA_UPLOAD_MAX_MEMORY_SIZE mặc định của Django
# (2,5 MB) và trần thân request của Vercel (4,5 MB), mà vẫn đủ cho một ảnh chụp
# đề đã co. Ảnh 20/09/2026 dùng để đo (PNG 900×260 chữ đen nền trắng) là 22 kB.
MAX_KY_TU_ANH = 1_600_000
_DAU_ANH = {
    'jpeg': b'\xff\xd8\xff',
    'png': b'\x89PNG',
    'webp': b'RIFF',
}


def _anh_hop_le(anh):
    """Trả (data_url, lỗi). Chỉ nhận data URL JPEG/PNG/WebP, base64 hợp lệ, đúng
    byte đầu của định dạng khai báo. Không có ảnh → ('', '')."""
    if anh in (None, ''):
        return '', ''
    if not isinstance(anh, str):
        return '', "Trường 'image' phải là chuỗi data URL."
    if len(anh) > MAX_KY_TU_ANH:
        return '', 'Ảnh quá lớn (tối đa khoảng 1 MB sau khi thu nhỏ). Bạn chụp lại gần hơn hoặc cắt bớt nhé.'
    dau, _, phan = anh.partition(',')
    loai = dau[len('data:image/'):-len(';base64')] if dau.startswith('data:image/') and dau.endswith(';base64') else ''
    if loai not in _DAU_ANH:
        return '', 'Chỉ nhận ảnh JPEG, PNG hoặc WebP.'
    try:
        raw = base64.b64decode(phan, validate=True)
    except (ValueError, TypeError):
        return '', 'Dữ liệu ảnh không đọc được (base64 hỏng).'
    if not raw.startswith(_DAU_ANH[loai]):
        return '', 'Nội dung tệp không phải ảnh ' + loai.upper() + '.'
    return anh, ''


class ChatView(NguoiDungView):
    """POST /api/chat — body {messages:[{role,content}], page_context?, image?} → {reply}.

    `image` là data URL của ảnh đề bài (tuỳ chọn); chỉ gắn vào lượt cuối và đi
    model đọc được ảnh (xem `chatbot/graph.py`).
    """
    def post(self, request):
        if not getattr(settings, "DEEPSEEK_API_KEY", None):
            return Response(
                {"error": "Trợ lý AI chưa được cấu hình (thiếu DEEPSEEK_API_KEY trong .env)."},
                status=503,
            )
        data = request.data if isinstance(request.data, dict) else {}
        messages = data.get("messages")
        if not isinstance(messages, list):
            return Response({"error": "Trường 'messages' phải là mảng."}, status=400)
        anh, loi = _anh_hop_le(data.get("image"))
        if loi:
            return Response({"error": loi}, status=400)
        # Ghép hồ sơ người học + bài đang mở (client gửi kèm) thành một khối
        # bối cảnh cho system prompt.
        ctx = " · ".join(p for p in [_user_context(request.user)] if p)
        lesson_ctx = _lesson_context(data.get("page_context"))
        if lesson_ctx:
            ctx = (ctx + "\n\n" + lesson_ctx) if ctx else lesson_ctx
        try:
            reply = chat(messages, ctx, image=anh)
        # noqa CÓ LÝ DO: đây là RANH GIỚI với dịch vụ ngoài. Bắt hẹp lại là
        # phải liệt kê hết loại lỗi của thư viện LLM, và mỗi lần nó nâng bản
        # là một loại mới lọt ra thành 500 trắng cho học viên.
        except APIStatusError as exc:
            if exc.status_code in _LOI_CO_MA:
                log.warning('DeepSeek trả %s cho user %s: %s', exc.status_code, request.user.id, str(exc)[:200])
                return Response({"error": _LOI_CO_MA[exc.status_code]}, status=503)
            return Response({"error": f"Trợ lý gặp sự cố khi trả lời: {exc}"}, status=502)
        except Exception as exc:  # noqa: BLE001 — lỗi mạng/key/model → báo gọn, không lộ trace
            return Response({"error": f"Trợ lý gặp sự cố khi trả lời: {exc}"}, status=502)
        return Response({"reply": reply})
