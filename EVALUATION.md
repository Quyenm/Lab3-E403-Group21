# Thiết lập đánh giá
* Use case: Weather Outdoor Planner
* Các hệ thống so sánh:
  * Chatbot Baseline
  * ReAct Agent
* Model sử dụng: OpenAI GPT-4o
* Tools:
  * `get_current_weather(city)`
  * `get_forecast(city, date)`
  * `assess_outdoor_suitability(activity, weather_data)`
* Tập test:
  * TC1: Thời tiết hiện tại ở Hà Nội
  * TC2: Dự báo ngày mai ở TP.HCM
  * TC3: So sánh Đà Lạt vs Nha Trang
  * TC4: Gợi ý ngày đi biển tốt hơn trong cuối tuần
  * TC5: Câu hỏi mơ hồ cần làm rõ

---

# Kết quả theo từng test case

| Test Case | Expected Winner | Agent v1 | Agent v2    |
| --------- | --------------- | -------- | ----------- |
| TC1       | Agent           | Pass     | **Partial** |
| TC2       | Agent           | Pass     | **Pass**    |
| TC3       | Agent           | Pass     | **Fail**    |
| TC4       | Agent           | Pass     | **Fail**    |
| TC5       | Agent           | Fail     | **Pass**    |

---

# Tổng hợp metrics

## Chatbot Baseline (5 test cases)

| Metric      | Giá trị     |
| ----------- | ----------- |
| Avg Tokens  | ~684 tokens |
| Avg Latency | ~4s         |
| Loop Count  | 1.0         |
| Failures    | 3/5         |
| Reliability | 2/5         |

## ReAct Agent

| Metric         | Giá trị      |
| -------------- | ------------ |
| Avg Tokens     | ~1650 tokens |
| Avg Latency    | ~7s          |
| Avg Loop Count | 2.4 steps    |
| Failures       | 1/5          |
| Reliability    | 4/5          |

## ReAct Agent V2

| Metric         | Giá trị      |
| -------------- | ------------ |
| Avg Tokens     | ~1346 tokens |
| Avg Latency    | ~7s          |
| Avg Loop Count | 2.4 steps    |
| Failures       | 2/5          |
| Reliability    | 3/5          |

---

# Phân tích lỗi (Failure Analysis)

### Lỗi 1: Chatbot không truy cập được dữ liệu thời gian thực
* **Test cases**: TC1, TC2, TC4
* **Hiện tượng**: Luôn trả lời kiểu "không thể cung cấp dữ liệu thời gian thực”
* **Nguyên nhân**: Không có tool integration
* **Hậu quả**: Fail hoàn toàn các task chính của bài toán

---

### Lỗi 2: Chatbot trả lời không có grounding
* Test case: TC3
* Hiện tượng:
  * So sánh Đà Lạt vs Nha Trang bằng kiến thức chung
  * Không có số liệu thời tiết thực tế
* Nguyên nhân: Không gọi được tool → suy đoán
* Hậu quả: Chỉ đạt mức Partial

### Lỗi 3: Agent v1 lộ internal reasoning (UX bug nghiêm trọng)

* Test case: TC5
* Hiện tượng:
  * Output chứa:
    ```
    Thought: ...
    Action: Ask for city
    ```
* Nguyên nhân:
  * Thiếu rule tách reasoning và final answer
* Kỳ vọng:
  * Phải hỏi tự nhiên: *“Bạn muốn đi chơi ở thành phố nào?”*
* Hậu quả:
  * Bị tính Fail dù logic đúng

### Lỗi 4: Không xử lý tool constraint (critical)
- **Test cases**: TC3, TC4
- Hiện tượng:
    - Tool trả về:
        ```
        FORECAST_NOT_AVAILABLE
        ```
    - Agent dừng luôn

**So với v1:**
- v1 có attempt fallback (check ngày khác)
- v2 → fail ngay

**Nguyên nhân:**
- Thiếu error-handling policy trong agent loop

**Hậu quả:**
- Fail các task planning (core use case)

### Lỗi 5: Không có fallback strategy
Ví dụ TC3:
- Thay vì thử ngày gần nhất trong 5 ngày hoặc so sánh theo available data

→ Agent v2 trả lời:
> “Bạn quay lại sau”

## 5. So sánh tổng thể
Chatbot Baseline có ưu điểm:
* Ít token hơn
* Nhanh hơn
* Không có loop nên đơn giản

Tuy nhiên, nhược điểm rất lớn:
* Không sử dụng được dữ liệu thời gian thực
* Không giải được các bài toán planning
* Reliability thấp
ReAct Agent:
* Giải được đầy đủ các task cần reasoning nhiều bước
* Biết gọi tool và sử dụng dữ liệu thật
* Là hệ thống duy nhất trả lời đúng các câu hỏi cốt lõi

Trade-off:
* Tốn ~2.3x token
* Chậm hơn
* Phức tạp hơn (multi-step loop)

ReAct Agent v2:
- Tốt hơn về UX và efficiency
- Nhưng:
    - yếu hơn về robustness
    - fail các case quan trọng
## 6. Kết luận
Trong bài toán Weather Outdoor Planner:
* Chatbot Baseline chỉ phù hợp với câu hỏi lý thuyết, không phù hợp với thực tế
* ReAct Agent mang lại giá trị rõ ràng nhờ khả năng reasoning + tool usage
Dù chi phí và latency cao hơn, Agent vẫn là lựa chọn đúng vì:
* Độ chính xác cao hơn
* Khả năng xử lý multi-step tốt hơn
* Reliability vượt trội
