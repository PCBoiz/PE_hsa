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
        try:
            reply = chat(messages, _user_context(request.user))
        except Exception as exc:  # lỗi mạng/key/model → báo gọn, không lộ trace
            return Response({"error": f"Trợ lý gặp sự cố khi trả lời: {exc}"}, status=502)
        return Response({"reply": reply})
