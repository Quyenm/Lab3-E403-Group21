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