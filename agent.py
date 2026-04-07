"""
app.py — Gradio UI cho ReAct Weather Agent (compatible Gradio 4.x+)
Chạy: python app.py
"""

import gradio as gr

from core.openai_provider import OpenAIProvider
from tools import WEATHER_TOOLS
from react_agent.react_agent import ReActAgent
from telemetry.logger import logger

# ============================================================
# Khởi tạo agent singleton
# ============================================================
_llm   = OpenAIProvider(model_name="gpt-4o")
_agent = ReActAgent(llm=_llm, tools=WEATHER_TOOLS, max_steps=5)


def chat_with_agent(message: str, history: list) -> str:
    logger.log_event("GRADIO_INPUT", {"message": message})
    try:
        answer = _agent.run(message)
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        answer = "Đã xảy ra lỗi không mong muốn. Vui lòng thử lại!"
    logger.log_event("GRADIO_OUTPUT", {"answer_preview": answer[:200]})
    return answer


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="🌤️ Weather Outdoor Planner", theme=gr.themes.Soft()) as demo:

        gr.Markdown("""
        # 🌤️ Weather Outdoor Planner
        Hỏi tôi về thời tiết hoặc lên kế hoạch hoạt động ngoài trời!

        **Ví dụ:**
        - *Thời tiết hiện tại ở Hà Nội thế nào?*
        - *Dự báo ngày mai ở TP.HCM khả năng mưa, gió và nắng như thế nào?*
        - *Tôi định đi chơi ngoài trời vào cuối tuần này. Giữa Đà Lạt và Nha Trang, nơi nào thời tiết đẹp hơn để đi thư giãn?*
        - *Tôi muốn đi biển ở Nha Trang vào thứ Bảy tuần này. Nếu thời tiết không tốt thì hãy gợi ý cho tôi ngày khác trong cuối tuần có thời tiết đẹp hơn.*
        - *Cuối tuần này tôi muốn đi chơi, tư vấn giúp tôi.*
        """)

        # type="messages" → dùng format {"role", "content"} — Gradio 4.x+
        chatbot = gr.Chatbot(
            label="Trợ lý thời tiết",
            height=480,
        )

        with gr.Row():
            txt = gr.Textbox(
                placeholder="Nhập câu hỏi của bạn...",
                show_label=False,
                scale=9,
                autofocus=True,
            )
            send_btn = gr.Button("Gửi", variant="primary", scale=1)

        clear_btn = gr.Button("🗑️ Xoá lịch sử")

        # history lưu dạng [{"role": "user/assistant", "content": "..."}]
        state = gr.State([])

        def respond(message: str, history: list):
            if not message.strip():
                return history, history, ""
            bot_reply = chat_with_agent(message, history)
            history = history + [
                {"role": "user",      "content": message},
                {"role": "assistant", "content": bot_reply},
            ]
            return history, history, ""

        def clear(_):
            return [], [], ""

        send_btn.click(fn=respond, inputs=[txt, state], outputs=[chatbot, state, txt])
        txt.submit(fn=respond,     inputs=[txt, state], outputs=[chatbot, state, txt])
        clear_btn.click(fn=clear,  inputs=[state],      outputs=[chatbot, state, txt])

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(share=True)