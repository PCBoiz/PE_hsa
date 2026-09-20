"""Endpoint /api/chat — Trợ lý HSA. Key DeepSeek nằm SERVER-SIDE (env), không lộ
ra frontend như bản Gemini cũ.

Context engineering: bơm hồ sơ học tập THẬT của học viên (chatbot/profile.py) +
bài đang mở. Trước 24/08 chỗ này tự tính "hợp phần yếu nhất" từ lượt thi thử gần
nhất — một phép tính thứ ba về điểm yếu, thô hơn bản đồ năng lực và có thể mâu
thuẫn với con số Trang của tôi đang hiện cho cùng học viên đó.
"""
import base64
import json
import logging

from django.conf import settings
from django.http import StreamingHttpResponse
from openai import APIStatusError
from rest_framework.response import Response

from chatbot.graph import chat, chat_stream
from chatbot.profile import learner_profile
from common.db import q1
from common.throttling import (
    ChatDailyUserThrottle,
    ChatHourlyUserThrottle,
    DailyIPThrottle,
    HourlyIPThrottle,
)
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


# Bước học viên đang đứng — chuỗi CỐ ĐỊNH của engine (`lesson_hsa.js`), chỉ
# nhận đúng năm giá trị này. Mọi thứ khác về bài thì tra CSDL (bên dưới).
_BUOC = ('Kiểm tra', 'Đánh giá', 'Lý thuyết', 'Ghi chú', 'Luyện tốc độ')


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


def _mot_dong(chu, limit):
    """Một dòng, không ký tự điều khiển: một giá trị nhiều dòng là cách rẻ nhất
    để "viết thêm" gạch đầu dòng vào system prompt."""
    return " ".join(str(chu or "").split())[:limit]


def _bai_theo_so(course_id, index):
    """Tên bài, chủ đề, ý chính, công thức — ĐỌC TỪ `lessons.content_json`.

    Tới 20/09/2026 bốn thứ này do TRÌNH DUYỆT gửi và được nối thẳng vào system
    prompt (`lesson_title`, `lesson_topic`, `formula`, `key_points`), chỉ cắt
    độ dài, không cắt xuống dòng. Tức bất kỳ ai đăng nhập cũng viết được vài
    dòng vào lời hệ thống của mô hình, ngay trên đường đi đúng thiết kế —
    OWASP LLM01 (Prompt Injection). Bài nằm trong CSDL từ 19/08/2026, nên máy
    chủ tra được; client chỉ còn gửi `course_id` + `lesson_index` (tham số
    truy vấn) và `step` (năm giá trị cố định). Cùng lối với `_ten_khoa`.
    """
    cid = str(course_id or "").strip()[:64]
    try:
        so = int(index)
    except (TypeError, ValueError):
        return None
    if not cid or not 1 <= so <= 999:
        return None
    r = q1("SELECT content_json FROM lessons WHERE course_id = %s AND sort_order = %s "
           "AND content_json IS NOT NULL", (cid, so))
    if not r:
        return None
    d = r["content_json"]
    if isinstance(d, str):
        try:
            d = json.loads(d)
        except ValueError:
            return None
    if not isinstance(d, dict):
        return None
    ghi_chu = d.get("notes") if isinstance(d.get("notes"), dict) else {}
    y = ghi_chu.get("key_points") if isinstance(ghi_chu.get("key_points"), list) else []
    return {
        "so": so,
        "ten": _mot_dong(d.get("title"), 120),
        "chu_de": _mot_dong(d.get("topic_tag"), 80),
        "cong_thuc": _mot_dong(ghi_chu.get("formula"), 200),
        "y_chinh": [_mot_dong(p, 160) for p in y[:6] if _mot_dong(p, 160)],
    }


def _lesson_context(page_context):
    """Mô tả gọn bài học viên đang mở, để trợ lý bám đúng nội dung đang học.

    Mọi dòng về bài là của MÁY CHỦ (tra CSDL); từ client chỉ có ba tham số:
    `course_id`, `lesson_index`, `step`. Trường nào khác client gửi (kể cả
    `lesson_title`, `key_points` như bản cũ) đều bị bỏ qua.
    """
    if not isinstance(page_context, dict):
        return ""
    lines = []
    ten = _ten_khoa(page_context.get("course_id"))
    if ten:
        lines.append(f"- Khoá đang học: {ten[:80]}")
    bai = _bai_theo_so(page_context.get("course_id"), page_context.get("lesson_index"))
    if bai:
        lines.append(f"- Bài số: {bai['so']}")
        if bai["ten"]:
            lines.append(f"- Tên bài: {bai['ten']}")
        if bai["chu_de"]:
            lines.append(f"- Chủ đề: {bai['chu_de']}")
        if bai["cong_thuc"]:
            lines.append(f"- Công thức của bài: {bai['cong_thuc']}")
        if bai["y_chinh"]:
            lines.append("- Ý chính của bài: " + "; ".join(bai["y_chinh"]))
    buoc = page_context.get("step")
    if buoc in _BUOC:
        lines.append(f"- Đang ở bước: {buoc}")
    if not lines:
        return ""
    return (
        "Học viên ĐANG mở bài học dưới đây (dữ liệu do máy chủ tra từ giáo trình). "
        "Hãy bám sát bài này khi trả lời (giảng lại đúng phần lý thuyết, lấy ví dụ "
        "cùng dạng, nhắc bẫy hay gặp):\n" + "\n".join(lines)
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
    # Quota theo IP (mặc định) + theo NGƯỜI (riêng cho đường tốn tiền này) —
    # xem `ChatHourlyUserThrottle`.
    throttle_classes = [DailyIPThrottle, HourlyIPThrottle, ChatHourlyUserThrottle, ChatDailyUserThrottle]
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
        if data.get("stream"):
            return self._luong(messages, ctx, anh, request)
        try:
            reply = chat(messages, ctx, image=anh)
        # noqa CÓ LÝ DO: đây là RANH GIỚI với dịch vụ ngoài. Bắt hẹp lại là
        # phải liệt kê hết loại lỗi của thư viện LLM, và mỗi lần nó nâng bản
        # là một loại mới lọt ra thành 500 trắng cho học viên.
        except Exception as exc:  # noqa: BLE001 — lỗi mạng/key/model → báo gọn, không lộ trace
            return self._loi(exc, request)
        return Response({"reply": reply})

    def _loi(self, exc, request):
        if isinstance(exc, APIStatusError) and exc.status_code in _LOI_CO_MA:
            log.warning('DeepSeek trả %s cho user %s: %s', exc.status_code, request.user.id, str(exc)[:200])
            return Response({"error": _LOI_CO_MA[exc.status_code]}, status=503)
        return Response({"error": f"Trợ lý gặp sự cố khi trả lời: {exc}"}, status=502)

    def _luong(self, messages, ctx, anh, request):
        """`stream: true` → `text/event-stream`, mỗi mẩu một sự kiện `data:
        {"chunk": …}`; kết thúc bằng `event: done`. Lỗi GIỮA chừng thành
        `data: {"error": …}` — không đổi được mã HTTP khi đã phát 200.

        MẨU ĐẦU lấy TRƯỚC khi dựng phản hồi: lỗi 402/401/mạng gần như luôn nổ
        ở lượt gọi đầu, và lúc ấy còn trả được JSON 503/502 y như đường thường
        — trình duyệt xử lý một kiểu lỗi, không phải hai. Vercel/Render không
        gom `text/event-stream`; lớp trung gian (`src/lib/proxy.ts`) có nhánh
        truyền thẳng cho kiểu này."""
        sinh = chat_stream(messages, ctx, image=anh)
        try:
            dau = next(sinh)
        except StopIteration:
            dau = ""
        except Exception as exc:  # noqa: BLE001 — cùng lý do với đường thường
            return self._loi(exc, request)

        def sse():
            yield _sse({"chunk": dau}) if dau else ""
            try:
                for mau in sinh:
                    yield _sse({"chunk": mau})
            except Exception as exc:  # noqa: BLE001 — đã phát 200, chỉ còn cách nói trong luồng
                log.warning('luồng trợ lý đứt giữa chừng (user %s): %s', request.user.id, str(exc)[:200])
                yield _sse({"error": "Trợ lý bị ngắt giữa chừng — bạn hỏi lại giúp mình nhé."})
            yield "event: done\ndata: {}\n\n"

        resp = StreamingHttpResponse(sse(), content_type="text/event-stream; charset=utf-8")
        resp["X-Accel-Buffering"] = "no"
        return resp


def _sse(d) -> str:
    return "data: " + json.dumps(d, ensure_ascii=False) + "\n\n"
