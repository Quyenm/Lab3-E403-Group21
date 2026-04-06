"""
app_chatbot.py — Chatbot thuần, chỉ gọi GPT không có tool
Chạy: python app_chatbot.py
"""

import gradio as gr

from core.openai_provider import OpenAIProvider
from telemetry.logger import logger

# ============================================================
# Khởi tạo
# ============================================================
_llm = OpenAIProvider(model_name="gpt-4o")

SYSTEM_PROMPT = """Bạn là trợ lý thông minh chuyên về thời tiết và hoạt động ngoài trời.
Hãy trả lời dựa trên kiến thức có sẵn của bạn.
Lưu ý: bạn KHÔNG có công cụ tra cứu thời tiết thực tế, hãy nói rõ khi không chắc chắn.
Trả lời bằng tiếng Việt, rõ ràng và thân thiện."""


# ============================================================
# Xử lý tin nhắn — gọi thẳng LLM, không qua agent
# ============================================================
def chat(message: str, history: list) -> str:
    logger.log_event("PLAIN_CHATBOT_INPUT", {"message": message})

    # Gộp history vào prompt để giữ ngữ cảnh hội thoại
    conversation = ""
    for turn in history:
        conversation += f"User: {turn['content']}\n" if turn["role"] == "user" else f"Assistant: {turn['content']}\n"
    conversation += f"User: {message}"

    try:
        result = _llm.generate(conversation, system_prompt=SYSTEM_PROMPT)
        answer = result["content"]
    except Exception as e:
        logger.error(f"Plain chatbot error: {e}")
        answer = "Đã xảy ra lỗi. Vui lòng thử lại!"

    logger.log_event("PLAIN_CHATBOT_OUTPUT", {
        "answer_preview": answer[:200],
        "tokens": result.get("usage", {}),
        "latency_ms": result.get("latency_ms", 0),
    })
    return answer


# ============================================================
# UI
# ============================================================
def build_ui() -> gr.Blocks:
    with gr.Blocks(title="🤖 Chatbot thuần", theme=gr.themes.Soft()) as demo:

        gr.Markdown("""
        # 🤖 Chatbot thuần (không có tool)
        Trả lời dựa trên kiến thức GPT — **không** tra cứu thời tiết thực tế.

        **Thử hỏi:**
        - *Hà Nội hôm nay bao nhiêu độ?*
        - *Ngày mai Đà Nẵng có mưa không?*
        - *Chiều mai có nên đá bóng ở Hà Nội không?*
        """)

        chatbot = gr.Chatbot(
            label="Chatbot thuần",
            height=480,
        )

        with gr.Row():
            txt = gr.Textbox(
                placeholder="Nhập câu hỏi...",
                show_label=False,
                scale=9,
                autofocus=True,
            )
            send_btn = gr.Button("Gửi", variant="primary", scale=1)

        clear_btn = gr.Button("🗑️ Xoá lịch sử")
        state = gr.State([])

        def respond(message: str, history: list):
            if not message.strip():
                return history, history, ""
            reply = chat(message, history)
            history = history + [
                {"role": "user",      "content": message},
                {"role": "assistant", "content": reply},
            ]
            return history, history, ""

        def clear(_):
            return [], [], ""

        send_btn.click(fn=respond, inputs=[txt, state], outputs=[chatbot, state, txt])
        txt.submit(fn=respond,     inputs=[txt, state], outputs=[chatbot, state, txt])
        clear_btn.click(fn=clear,  inputs=[state],      outputs=[chatbot, state, txt])

    return demo


if __name__ == "__main__":
    build_ui().launch(share=True)