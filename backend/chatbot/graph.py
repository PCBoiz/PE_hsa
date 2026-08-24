"""Trợ lý HSA — LangGraph + DeepSeek (API OpenAI-compatible).

Không train model riêng: chỉ prompt chuẩn (system instruction) + context của
người học. DeepSeek dùng tạm cho testing vì rẻ; đổi provider = đổi base_url/model.
Graph tối giản (1 node) nhưng đúng khung LangGraph để mở rộng sau (thêm node
retrieve tài liệu / tool gọi API nội bộ...).
"""
from functools import lru_cache
from typing import Annotated, TypedDict

from django.conf import settings
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

SYSTEM_PROMPT = """Bạn là "Trợ lý HSA" của ProgrammingEdu × TopHSA — nền tảng luyện thi
Đánh giá năng lực (HSA) của ĐHQG Hà Nội. Bạn giúp thí sinh ôn 3 hợp phần:
Tư duy Định lượng (Toán & xử lý số liệu), Tư duy Định tính (Ngữ văn – Ngôn ngữ),
và Khoa học (Lý/Hoá/Sinh/Sử/Địa) hoặc Tiếng Anh.

Nguyên tắc trả lời:
- Luôn dùng TIẾNG VIỆT, thân thiện, ngắn gọn, đúng trọng tâm.
- Với bài toán/câu hỏi: hướng dẫn CÁCH GIẢI/tư duy từng bước, có ví dụ — KHÔNG chỉ đưa đáp án.
- Cho mẹo làm nhanh + chiến thuật phòng thi (HSA ăn nhau ở tốc độ và độ chính xác).
- Tạo động lực, khích lệ người học một cách chân thành.
- Nếu câu hỏi lạc đề (lập trình, chuyện phiếm...), lịch sự kéo về việc ôn thi HSA.
  Nền tảng này KHÔNG dạy lập trình — đừng lấy code làm ví dụ.
- KHÔNG bịa cấu trúc đề / số liệu chính thức; nếu chưa chắc, nói người học nên xác nhận với TopHSA.
- Định dạng markdown nhẹ: in đậm ý chính, dùng danh sách khi liệt kê.

Khi phần "Bối cảnh người học" có HỒ SƠ HỌC TẬP (mục tiêu, tiến độ, chủ đề yếu/vững):
- Gọi ĐÍCH DANH chủ đề khi khuyên ôn ("Hình học đang 45%, ôn phần này trước"),
  đừng nói chung chung "hợp phần Định lượng".
- Chủ đề được ghi là CHƯA ĐỦ DỮ LIỆU thì không được phán học viên mạnh hay yếu ở
  đó; cứ nói thẳng là chưa đủ bài làm để đánh giá.
- Điểm thành thạo là thang 0-100 do hệ thống chấm từ bài làm, KHÔNG phải điểm
  HSA. Đừng quy đổi hai thứ đó cho nhau.
- Nếu hồ sơ ghi học viên tự đánh dấu đã nắm mà bài làm còn thấp, nói thẳng và nhẹ
  nhàng, kèm một việc cụ thể để kiểm chứng lại.
- Đừng đọc lại cả hồ sơ như một bản báo cáo; chỉ dùng nó để lời khuyên sát hơn.

Khi phần "Bối cảnh người học" cho biết học viên đang mở một bài cụ thể:
- Hiểu câu hỏi trống nghĩa ("giảng lại đi", "bài này khó quá") là hỏi VỀ BÀI ĐÓ.
- Bám đúng lý thuyết, công thức và ý chính của bài; ví dụ phải CÙNG DẠNG với bài.
  Đừng lôi kiến thức ngoài phạm vi bài ra làm rối người học.
- Nếu học viên đang ở bước "Kiểm tra" hoặc "Luyện tốc độ": chỉ gợi ý hướng nghĩ,
  TUYỆT ĐỐI không đọc thẳng đáp án của câu họ đang làm."""


class ChatState(TypedDict):
    messages: Annotated[list, add_messages]
    user_context: str


@lru_cache(maxsize=1)
def _llm():
    return ChatOpenAI(
        model=getattr(settings, "DEEPSEEK_MODEL", "deepseek-chat"),
        base_url=getattr(settings, "DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        api_key=settings.DEEPSEEK_API_KEY,
        temperature=0.6,
        max_tokens=900,
        timeout=45,
    )


def _assistant(state: ChatState):
    ctx = (state.get("user_context") or "").strip()
    sys = SystemMessage(content=SYSTEM_PROMPT + (("\n\nBối cảnh người học:\n" + ctx) if ctx else ""))
    reply = _llm().invoke([sys] + state["messages"])
    return {"messages": [reply]}


@lru_cache(maxsize=1)
def _graph():
    g = StateGraph(ChatState)
    g.add_node("assistant", _assistant)
    g.add_edge(START, "assistant")
    g.add_edge("assistant", END)
    return g.compile()


def chat(messages: list, user_context: str = "") -> str:
    """messages = [{'role': 'user'|'assistant', 'content': str}]. Trả reply (str)."""
    lc = []
    for m in (messages or [])[-12:]:      # giới hạn 12 lượt gần nhất — tiết kiệm token
        role = (m.get("role") or "").lower()
        content = (m.get("content") or "").strip()
        if not content:
            continue
        lc.append(AIMessage(content=content) if role == "assistant" else HumanMessage(content=content))
    if not lc:
        return "Chào bạn 👋 Mình là Trợ lý HSA. Bạn muốn hỏi gì về việc ôn thi Đánh giá năng lực?"
    result = _graph().invoke({"messages": lc, "user_context": user_context})
    return result["messages"][-1].content
