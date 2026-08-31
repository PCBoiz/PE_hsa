"""Endpoint /api/chat — Trợ lý HSA. Key DeepSeek nằm SERVER-SIDE (env), không lộ
ra frontend như bản Gemini cũ.

Context engineering: bơm hồ sơ học tập THẬT của học viên (chatbot/profile.py) +
bài đang mở. Trước 24/08 chỗ này tự tính "hợp phần yếu nhất" từ lượt thi thử gần
nhất — một phép tính thứ ba về điểm yếu, thô hơn bản đồ năng lực và có thể mâu
thuẫn với con số Trang của tôi đang hiện cho cùng học viên đó.
"""
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from chatbot.graph import chat
from chatbot.profile import learner_profile


def _user_context(user):
    return learner_profile(user.id, getattr(user, "name", None))


# Ngữ cảnh trang do client gửi: chỉ nhận đúng các khoá này, cắt độ dài, để nội
# dung người dùng bơm vào không làm phình/điều khiển system prompt.
_CTX_FIELDS = {
    "course_title": ("Khoá đang học", 80),
    "lesson_index": ("Bài số", 8),
    "lesson_title": ("Tên bài", 120),
    "lesson_topic": ("Chủ đề", 80),
    "step": ("Đang ở bước", 40),
    "formula": ("Công thức của bài", 200),
}


def _lesson_context(page_context):
    """Mô tả gọn bài học viên đang mở, để trợ lý bám đúng nội dung đang học."""
    if not isinstance(page_context, dict):
        return ""
    lines = []
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


class ChatView(APIView):
    """POST /api/chat — body {messages:[{role,content}]} → {reply}."""
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
        # Ghép hồ sơ người học + bài đang mở (client gửi kèm) thành một khối
        # bối cảnh cho system prompt.
        ctx = " · ".join(p for p in [_user_context(request.user)] if p)
        lesson_ctx = _lesson_context(data.get("page_context"))
        if lesson_ctx:
            ctx = (ctx + "\n\n" + lesson_ctx) if ctx else lesson_ctx
        try:
            reply = chat(messages, ctx)
        # noqa CÓ LÝ DO: đây là RANH GIỚI với dịch vụ ngoài. Bắt hẹp lại là
        # phải liệt kê hết loại lỗi của thư viện LLM, và mỗi lần nó nâng bản
        # là một loại mới lọt ra thành 500 trắng cho học viên.
        except Exception as exc:  # noqa: BLE001 — lỗi mạng/key/model → báo gọn, không lộ trace
            return Response({"error": f"Trợ lý gặp sự cố khi trả lời: {exc}"}, status=502)
        return Response({"reply": reply})
