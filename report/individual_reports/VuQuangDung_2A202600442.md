# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: [Vũ Quang Dũng]
- **Student ID**: [2A202600442]
- **Date**: [06/04/2026]

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: [ `src/agent/react-agent.py`]
- **Code Highlights**: [
    """
react_agent.py - ReAct Agent với fix lỗi Action không hợp lệ
"""

import re
import json
from typing import List, Dict, Any

from telemetry.logger import logger
from telemetry.metrics import tracker

_WEATHER_KEYWORDS = [
    "thời tiết", "nhiệt độ", "mưa", "nắng", "gió", "độ ẩm", "dự báo",
    "weather", "rain", "temperature", "forecast", "bão", "nóng", "lạnh",
    "đá bóng", "picnic", "beach", "running", "chạy bộ", "đi biển",
    "ngoài trời", "outdoor", "cuối tuần", "hôm nay", "ngày mai",
    "có nên", "phù hợp", "thích hợp", "nha trang", "đà nẵng", "đà lạt",
    "biển", "núi", "du lịch", "chuyến đi",
]

def is_weather_related(query: str) -> bool:
    return any(kw in query.lower() for kw in _WEATHER_KEYWORDS)


class ReActAgent:
    def __init__(self, llm, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps

    def get_system_prompt(self) -> str:
        tool_names = [t["name"] for t in self.tools]
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )
        return f"""You are a Weather Outdoor Planner. Today is April 6, 2026 (Sunday).
This week: Mon Apr 7 → Sun Apr 13. "This Saturday" = Apr 12, "This Sunday" = Apr 13.

Your job is to help users make outdoor plans based on weather conditions.

Available tools (ONLY these tool names are valid):
{tool_descriptions}

CRITICAL RULES FOR ACTION:
- Action MUST use ONLY one of these exact tool names: {tool_names}
- NEVER write "Action: Ask for city", "Action: clarify", or any non-tool Action
- If city or date is missing → skip Action, go directly to Final Answer to ask the user
- Action format must be exactly: Action: tool_name(arguments)

Instructions:
1. Only handle queries related to weather and outdoor planning.
2. If city/date/activity is missing → use Final Answer to ask, do NOT use Action.
3. For forecast queries, calculate the exact date from natural language (e.g. "this Saturday" = 2026-04-11).
4. For multi-step queries (compare days, find best day), call tools one by one.
5. When recommending a better day, compare rain_probability and temperature across days.
6. Reply in Vietnamese, clearly and in a friendly manner.

Format (one Action per turn):
Thought: <brief reasoning>
Action: <tool_name>(<arguments>)
Observation: <filled by system>
...
Final Answer: <complete answer in Vietnamese>
"""

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {
            "input": user_input,
            "model": self.llm.model_name,
            "max_steps": self.max_steps
        })

        if not is_weather_related(user_input):
            logger.log_event("SCOPE_GUARD_REJECT", {"input": user_input})
            return (
                "Xin lỗi, tôi chỉ hỗ trợ các câu hỏi liên quan đến "
                "thời tiết và hoạt động ngoài trời. "
                "Bạn có thể hỏi về nhiệt độ, dự báo mưa, hoặc "
                "liệu có nên đi picnic / đá bóng / đi biển không nhé!"
            )

        accumulated_prompt = user_input
        steps = 0
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        total_latency = 0
        valid_tool_names = {t["name"] for t in self.tools}

        while steps < self.max_steps:
            steps += 1
            logger.log_event("AGENT_STEP_START", {"step": steps})

            # 1. Gọi LLM
            try:
                result = self.llm.generate(
                    accumulated_prompt,
                    system_prompt=self.get_system_prompt()
                )
                llm_text   = result["content"]
                usage      = result.get("usage", {})
                latency_ms = result.get("latency_ms", 0)

                tracker.track_request(
                    provider=result.get("provider", "unknown"),
                    model=self.llm.model_name,
                    usage=usage,
                    latency_ms=latency_ms
                )
                for k in total_usage:
                    total_usage[k] += usage.get(k, 0)
                total_latency += latency_ms

                logger.log_event("LLM_RESPONSE", {
                    "step": steps,
                    "latency_ms": latency_ms,
                    "tokens": usage,
                    "response_preview": llm_text[:300]
                })

            except Exception as e:
                logger.error(f"LLM call failed at step {steps}: {e}")
                logger.log_event("LLM_ERROR", {"step": steps, "error": str(e)})
                return "Xin lỗi, có lỗi xảy ra khi kết nối tới AI. Vui lòng thử lại."

            # 2. Kiểm tra Final Answer
            final_match = re.search(r"Final Answer:\s*(.+)", llm_text, re.DOTALL)
            if final_match:
                answer = final_match.group(1).strip()
                logger.log_event("AGENT_END", {
                    "status": "success",
                    "steps_used": steps,
                    "total_tokens": total_usage,
                    "total_latency_ms": total_latency,
                })
                return answer

            # 3. Parse Action — chỉ chấp nhận tool hợp lệ
            action_match = re.search(r"Action:\s*(\w+)\((.+)\)", llm_text, re.DOTALL)
            if action_match:
                tool_name = action_match.group(1).strip()
                tool_args = action_match.group(2).strip()

                # *** FIX: từ chối Action không phải tool hợp lệ ***
                if tool_name not in valid_tool_names:
                    logger.log_event("INVALID_ACTION", {
                        "step": steps,
                        "tool_name": tool_name,
                        "reason": "not a valid tool name"
                    })
                    # Trích xuất Thought làm câu trả lời tạm, yêu cầu LLM sửa
                    thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|\Z)", llm_text, re.DOTALL)
                    thought_text  = thought_match.group(1).strip() if thought_match else ""

                    # Cho LLM cơ hội sửa lại
                    accumulated_prompt = (
                        accumulated_prompt
                        + "\n" + llm_text.rstrip()
                        + f"\nObservation: ERROR - '{tool_name}' is not a valid tool. "
                        f"Valid tools are: {list(valid_tool_names)}. "
                        f"If information is missing, use Final Answer to ask the user instead of Action."
                    )
                    continue

                logger.log_event("TOOL_CALL", {
                    "step": steps,
                    "tool": tool_name,
                    "args_preview": tool_args[:150]
                })

                observation = self._execute_tool(tool_name, tool_args)

                try:
                    obs_status = json.loads(observation).get("status", "unknown")
                except Exception:
                    obs_status = "raw_string"

                logger.log_event("TOOL_RESULT", {
                    "step": steps,
                    "tool": tool_name,
                    "status": obs_status,
                    "result_preview": observation[:200]
                })

                accumulated_prompt = (
                    accumulated_prompt
                    + "\n" + llm_text.rstrip()
                    + f"\nObservation: {observation}"
                )

            else:
                # Không có Action → coi như Final Answer luôn
                logger.log_event("AGENT_END", {
                    "status": "no_action_treated_as_answer",
                    "steps_used": steps,
                    "total_tokens": total_usage,
                    "total_latency_ms": total_latency
                })
                return llm_text.strip() or "Tôi không thể xử lý yêu cầu này."

        logger.log_event("AGENT_END", {
            "status": "max_steps_reached",
            "steps_used": steps,
            "total_tokens": total_usage,
            "total_latency_ms": total_latency
        })
        return (
            "Xin lỗi, tôi không thể hoàn thành yêu cầu trong số bước cho phép. "
            "Bạn hãy thử đặt câu hỏi cụ thể hơn nhé!"
        )

    def _execute_tool(self, tool_name: str, args: str) -> str:
        for tool in self.tools:
            if tool["name"] == tool_name:
                func = tool.get("func")
                if func is None:
                    return json.dumps({"status": "error",
                        "message": f"Tool '{tool_name}' chưa có hàm thực thi."}, ensure_ascii=False)
                try:
                    return func(args)
                except Exception as e:
                    logger.error(f"Tool '{tool_name}' exception: {e}")
                    return json.dumps({"status": "error",
                        "error_code": "TOOL_EXECUTION_ERROR",
                        "message": str(e)}, ensure_ascii=False)
        return json.dumps({"status": "error",
            "error_code": "TOOL_NOT_FOUND",
            "message": f"Không tìm thấy tool '{tool_name}'."}, ensure_ascii=False)
]
- **Documentation**: [File react_agent.py xây dựng một ReAct Agent chuyên xử lý các câu hỏi liên quan đến thời tiết và lập kế hoạch hoạt động ngoài trời bằng cách kết hợp giữa mô hình ngôn ngữ (LLM) và các công cụ (tools/API). Trước tiên, hệ thống sử dụng danh sách từ khóa để kiểm tra xem câu hỏi của người dùng có thuộc phạm vi thời tiết hay không; nếu không, agent sẽ từ chối xử lý để tránh lan man. Khi nhận được câu hỏi hợp lệ, agent khởi tạo một vòng lặp suy luận nhiều bước (multi-step reasoning), trong đó ở mỗi bước sẽ gọi LLM với một system prompt được thiết kế chặt chẽ nhằm ép mô hình tuân theo định dạng ReAct (Thought → Action → Observation → Final Answer) và chỉ được phép sử dụng các tool hợp lệ đã định nghĩa. Nếu LLM đưa ra “Final Answer”, hệ thống trả kết quả ngay; nếu không, agent sẽ phân tích phần “Action” bằng regex để xác định tool cần gọi và tham số tương ứng. Một điểm quan trọng của code là cơ chế fix lỗi Action không hợp lệ: nếu LLM gọi sai tên tool (ví dụ tự bịa ra action), agent sẽ không thực thi mà phản hồi lại bằng một Observation báo lỗi, đồng thời bổ sung vào prompt để buộc LLM tự sửa ở bước tiếp theo. Khi Action hợp lệ, agent sẽ gọi hàm tương ứng trong tool, nhận kết quả (Observation), rồi đưa ngược lại cho LLM để tiếp tục suy luận cho đến khi có câu trả lời hoàn chỉnh hoặc đạt giới hạn số bước. Ngoài ra, hệ thống còn tích hợp logging và tracking (token, latency, trạng thái từng bước) để phục vụ giám sát và debug trong môi trường production. Tổng thể, đoạn code này biến LLM từ một chatbot chỉ trả lời văn bản thành một agent thông minh có khả năng ra quyết định, gọi API, tự sửa lỗi và đưa ra câu trả lời chính xác hơn dựa trên dữ liệu thực tế.]

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: [e.g., Agent caught in an infinite loop with `Action: search(None)`]
- **Log Source**: [Link or snippet from `logs/YYYY-MM-DD.log`]
- **Diagnosis**: [Why did the LLM do this? Was it the prompt, the model, or the tool spec?]
- **Solution**: [How did you fix it? (e.g., updated `Thought` examples in the system prompt)]

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: The `Thought` block forced the LLM to explicitly decompose complex queries into logical steps before taking action. For example, when asked "Should I go to Nha Trang this Saturday?", a Chatbot might immediately say "Yes, good place". In contrast, the ReAct Agent first reasons: "I need to check the weather forecast for Nha Trang on April 12, 2026, then compare it with the user's activity requirements." This explicit reasoning dramatically improved accuracy and allowed the agent to decide whether to call tools or ask for clarification.

2.  **Reliability**: The Agent performed *worse* than a Chatbot in scenarios where information retrieval failed (e.g., city name not recognized by the weather API). The Chatbot would quickly provide a generic response, whereas the Agent would retry multiple times within max_steps, frustrating the user. Additionally, for purely informational queries not requiring real-time data (e.g., "What's a good outdoor activity?"), the Agent's multi-step overhead was unnecessary—a simple Chatbot was faster and equally helpful.

3.  **Observation**: The environment feedback (Observations from tools) was crucial in shaping the next action. When `get_weather_forecast(city="Hanoi", date="2026-04-12")` returned `{"temperature": 28°C, "rain_probability": 15%}`, the agent's Thought process immediately shifted: instead of recommending the day, it would call `compare_weather_days()` if the user had mentioned multiple options. The Observation acted as ground truth, preventing the agent from hallucinating weather data and forcing it to base recommendations on actual retrieved information, significantly increasing reliability.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Implement asynchronous batch tool execution using async/await or message queues (e.g., Celery + Redis). Currently, the agent processes actions sequentially within max_steps. For multi-user scenarios with hundreds of concurrent requests, each waiting for API responses would block the event loop. Solution: Parallelize tool calls (e.g., fetch weather for multiple cities simultaneously), and use Redis to cache repeated queries (weather for the same city/date within 1 hour) to reduce redundant API calls.

- **Safety**: Deploy a dedicated "Supervisor LLM" that audits each agent action before execution. The Supervisor would verify: (1) is the tool call legitimate and safe? (2) do the arguments match the schema? (3) is there a risk of bias in recommendations? Additionally, implement rate limiting per user/IP and API quotas to prevent abuse. Add a "confirm_action" mode where high-stakes decisions (e.g., booking a trip) require explicit user approval before the agent proceeds.

- **Performance**: Replace linear tool lookup with a Vector Embedding-based retriever for systems with hundreds of tools. Instead of the current `for tool in self.tools` iteration, embed tool names and descriptions, then use semantic similarity to find the best matching tool. Also, implement smart prompt caching: if multiple users ask similar weather queries, reuse the LLM's cached tokens to reduce latency. Monitor and optimize the regex parsing in Action extraction using compiled patterns and fallback parsers for robustness.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
