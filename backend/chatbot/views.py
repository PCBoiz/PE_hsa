"""Endpoint /api/chat — Trợ lý HSA. Key DeepSeek nằm SERVER-SIDE (env), không lộ
ra frontend như bản Gemini cũ. Context engineering: bơm tên + hợp phần yếu nhất."""
import json

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from chatbot.graph import chat
from common.db import q1


def _user_context(user):
    parts = []
    name = getattr(user, "name", None)
    if name:
        parts.append(f"Tên: {name}")
    # Hợp phần yếu nhất từ lần thi thử gần nhất (nếu có) — để trợ lý tư vấn sát hơn.
    try:
        row = q1(
            "SELECT section_scores_json FROM mock_attempts WHERE user_id=%s "
            "ORDER BY submitted_at DESC LIMIT 1",
            (user.id,),
        )
        ss = row and row.get("section_scores_json")
        if isinstance(ss, str):
            ss = json.loads(ss)
        if ss:
            weak = min(
                ss.items(),
                key=lambda kv: (kv[1]["correct"] / kv[1]["total"]) if kv[1].get("total") else 1.0,
            )[0]
            parts.append(f"Hợp phần yếu nhất (đề thi thử gần nhất): {weak}")
    except Exception:
        pass
    return " · ".join(parts)


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
        except Exception as exc:  # lỗi mạng/key/model → báo gọn, không lộ trace
            return Response({"error": f"Trợ lý gặp sự cố khi trả lời: {exc}"}, status=502)
        return Response({"reply": reply})
