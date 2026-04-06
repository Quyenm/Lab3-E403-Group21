# GROUP_REPORT_Group21

## Group Report: Lab 3 - Production-Grade Agentic System

**Team Name:** Group 21  
**Team Members:**  
- Nguyễn Mạnh Quyền - 2A202600481 - viết tool + docs  
- Vũ Quang Dũng - 2A202600442 - agent gọi tool  
- Nguyễn Trương Công Nhị - 2A202600505 - tổng hợp code, kết nối tool + API  
- Phạm Hoàng Long - 2A202600261 - UI/UX  

**Deployment Date:** 2026-04-06

---

## 1. Executive Summary

Nhóm 21 xây dựng hệ thống **Weather Outdoor Planner**, một hệ thống hỗ trợ người dùng ra quyết định cho các hoạt động ngoài trời dựa trên dữ liệu thời tiết thực tế. Hệ thống được thiết kế để xử lý cả truy vấn đơn giản như xem thời tiết hiện tại, lẫn truy vấn nhiều bước như so sánh địa điểm hoặc gợi ý ngày đi phù hợp hơn trong cuối tuần.

Trong quá trình thực nghiệm, nhóm so sánh ba cấu hình:
- **Chatbot Baseline**
- **ReAct Agent v1**
- **ReAct Agent v2**

Kết quả cho thấy:
- Chatbot Baseline nhanh hơn và ít tốn token hơn, nhưng không xử lý được các câu hỏi cần dữ liệu thời gian thực.
- Agent v1 đạt độ ổn định tốt nhất và trả lời đúng hầu hết các truy vấn cốt lõi.
- Agent v2 cải thiện về UX và token efficiency, nhưng lại yếu hơn ở robustness khi gặp constraint của tool.

### Success Rate

| Hệ thống | Kết quả tổng quát |
|---|---|
| Chatbot Baseline | Reliability khoảng **2/5** |
| ReAct Agent v1 | Reliability khoảng **4/5** |
| ReAct Agent v2 | Reliability khoảng **3/5** |

### Key Outcome

Kết quả nổi bật nhất của nhóm là: **ReAct Agent v1 là hệ thống duy nhất xử lý tốt các truy vấn thời tiết nhiều bước nhờ khả năng gọi tool và reasoning theo chu trình Thought → Action → Observation**, trong khi chatbot baseline chỉ phù hợp làm mốc so sánh.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

Kiến trúc hệ thống được chia thành hai nhánh chính:

- **Chatbot Baseline Path**: dùng cho các truy vấn trực tiếp, đơn giản.
- **ReAct Agent Path**: dùng cho các truy vấn nhiều bước, cần suy luận và gọi tool liên tiếp.

Với ReAct Agent, nhóm triển khai chu trình:

**Thought → Action → Tool Call → Observation → Final Answer**

Luồng xử lý tổng quát:
1. Nhận câu hỏi người dùng
2. Xác định câu hỏi có thuộc domain thời tiết / hoạt động ngoài trời hay không
3. Nếu thiếu thông tin quan trọng thì hỏi lại
4. Nếu là truy vấn đơn giản thì trả lời theo nhánh baseline
5. Nếu là truy vấn nhiều bước thì đi theo agent loop
6. Gọi tool, nhận observation, rồi quyết định có cần bước tiếp theo hay không
7. Nếu đủ thông tin thì trả lời cuối cùng

Flowchart minh họa đã được nhóm xây dựng riêng để mô tả toàn bộ luồng xử lý này. Điểm quan trọng trong kiến trúc là observation từ tool phải được đưa trở lại vào prompt ở bước tiếp theo, giúp agent reasoning dựa trên dữ liệu thật thay vì suy đoán thuần túy.

### 2.2 Tool Definitions (Inventory)

| Tool Name | Input Format | Use Case |
|---|---|---|
| `get_current_weather(city)` | `{"city": "string"}` | Lấy thời tiết hiện tại của một thành phố |
| `get_forecast(city, date)` | `{"city": "string", "date": "string"}` | Lấy dự báo thời tiết cho một thành phố vào một ngày cụ thể |
| `assess_outdoor_suitability(activity, weather_data)` | `{"activity": "string", "weather_data": "object"}` | Đánh giá thời tiết có phù hợp cho hoạt động ngoài trời hay không |

Trong đó:
- `get_current_weather` phục vụ các câu hỏi về thời tiết hiện tại.
- `get_forecast` phục vụ các câu hỏi về ngày mai, cuối tuần, hoặc ngày cụ thể.
- `assess_outdoor_suitability` là tool mang tính quyết định, giúp biến dữ liệu thời tiết thành recommendation thực tế.

### 2.3 LLM Providers Used

| Vai trò | Provider |
|---|---|
| Primary | OpenAI GPT-4o |
| Secondary (Backup) | Chưa triển khai |

Model chính được sử dụng trong toàn bộ quá trình đánh giá là **OpenAI GPT-4o**.

---

## 3. Telemetry & Performance Dashboard

Nhóm đánh giá hệ thống trên 5 test case:

| Test Case | Mô tả |
|---|---|
| TC1 | Thời tiết hiện tại ở Hà Nội |
| TC2 | Dự báo ngày mai ở TP.HCM |
| TC3 | So sánh Đà Lạt vs Nha Trang |
| TC4 | Gợi ý ngày đi biển tốt hơn trong cuối tuần |
| TC5 | Câu hỏi mơ hồ cần làm rõ |

### 3.1 Kết quả theo từng test case

| Test Case | Expected Winner | Agent v1 | Agent v2 |
|---|---|---|---|
| TC1 | Agent | Pass | Partial |
| TC2 | Agent | Pass | Pass |
| TC3 | Agent | Pass | Fail |
| TC4 | Agent | Pass | Fail |
| TC5 | Agent | Fail | Pass |

Kết quả này cho thấy:
- **Agent v1** đạt kết quả tốt hơn trên các task planning cốt lõi.
- **Agent v2** cải thiện được trường hợp UX ở TC5, nhưng lại giảm độ bền khi gặp lỗi từ tool.

### 3.2 Industry Metrics

#### Chatbot Baseline

| Metric | Giá trị |
|---|---|
| Average Latency (P50) | ~4s |
| Average Tokens per Task | ~684 tokens |
| Loop Count | 1.0 |
| Failures | 3/5 |
| Reliability | 2/5 |

#### ReAct Agent v1

| Metric | Giá trị |
|---|---|
| Average Latency (P50) | ~7s |
| Average Tokens per Task | ~1650 tokens |
| Average Loop Count | 2.4 steps |
| Failures | 1/5 |
| Reliability | 4/5 |

#### ReAct Agent v2

| Metric | Giá trị |
|---|---|
| Average Latency (P50) | ~7s |
| Average Tokens per Task | ~1346 tokens |
| Average Loop Count | 2.4 steps |
| Failures | 2/5 |
| Reliability | 3/5 |

### 3.3 Nhận xét dashboard

- **Chatbot Baseline** có chi phí thấp hơn và nhanh hơn, nhưng độ chính xác thấp trong bài toán thực tế.
- **Agent v1** có hiệu năng tốt nhất về chất lượng đầu ra, nhưng token cao hơn.
- **Agent v2** giảm được token usage so với v1, tuy nhiên đánh đổi bằng việc fail ở các case planning quan trọng.

| Chỉ số bổ sung | Trạng thái |
|---|---|
| Max Latency (P99) | Chưa đo riêng |
| Total Cost of Test Suite | Chưa tách riêng thành chi phí USD |

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study 1: Agent v1 lộ internal reasoning

**Input:**  
“Cuối tuần này tôi muốn đi chơi, tư vấn giúp tôi.”

**Observation:**  
Agent v1 xuất ra trực tiếp:
- `Thought: ...`
- `Action: Ask for city`

thay vì hỏi người dùng theo ngôn ngữ tự nhiên.

**Root Cause:**  
Prompt của agent v1 chưa tách biệt rõ giữa **reasoning nội bộ** và **final answer cho người dùng**.

**Impact:**  
Dù logic xử lý đúng hướng, v1 vẫn bị tính là fail ở TC5 vì trải nghiệm người dùng không đạt yêu cầu.

---

### Case Study 2: Agent v2 không xử lý tool constraint

**Input:**  
TC3 và TC4, khi tool trả về trạng thái:
`FORECAST_NOT_AVAILABLE`

**Observation:**  
Agent v2 dừng luôn sau khi gặp lỗi, thay vì thử fallback strategy. Trong khi đó, v1 vẫn có attempt fallback như thử ngày gần nhất hoặc xử lý tiếp theo available data.

**Root Cause:**  
Agent v2 thiếu **error-handling policy** trong agent loop và không có hướng dẫn rõ về fallback strategy khi tool không hỗ trợ truy vấn mong muốn.

**Impact:**  
Agent v2 fail ở các task planning cốt lõi, làm reliability giảm từ 4/5 xuống 3/5.

---

### Case Study 3: Chatbot Baseline không có grounding

**Input:**  
TC3 - So sánh Đà Lạt vs Nha Trang

**Observation:**  
Chatbot trả lời bằng kiến thức chung, không dùng dữ liệu thời tiết thực tế.

**Root Cause:**  
Không có tool integration nên chatbot buộc phải suy đoán thay vì grounding theo dữ liệu thật.

**Impact:**  
Kết quả chỉ đạt mức partial, không đủ để hỗ trợ ra quyết định thực tế.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Agent v1 vs Agent v2

| Hạng mục | Agent v1 | Agent v2 |
|---|---|---|
| UX | Chưa tốt, lộ Thought/Action | Tốt hơn ở TC5 |
| Token usage | ~1650 tokens | ~1346 tokens |
| Reliability | 4/5 | 3/5 |
| Robustness | Tốt hơn | Yếu hơn |
| Fallback handling | Có attempt fallback | Thiếu fallback strategy |

### Diff

Agent v2 được chỉnh theo hướng:
- cải thiện cách hỏi lại người dùng
- giảm bớt verbosity
- tối ưu output cho UX

### Result

Kết quả là:
- **v2 tốt hơn về UX và efficiency**
- nhưng **kém hơn về robustness**
- fail các case quan trọng liên quan đến planning và tool constraint

---

### Experiment 2: Chatbot vs Agent

| Case | Chatbot Result | Agent Result | Winner |
|---|---|---|---|
| Simple current weather | Fail | Correct | Agent |
| Tomorrow forecast | Fail | Correct | Agent |
| Compare two locations | Partial | Correct | Agent |
| Better weekend day suggestion | Fail | Correct | Agent |
| Ambiguous query | Partial | v1 Fail / v2 Correct | Agent v2 |

### Nhận xét

Ở use case Weather Outdoor Planner, gần như toàn bộ các truy vấn cốt lõi đều cần dữ liệu thật hoặc reasoning nhiều bước. Vì vậy, chatbot baseline không còn là lựa chọn đủ tốt, mà chỉ phù hợp để làm baseline so sánh.

---

## 6. Production Readiness Review

### Security
- Cần validate và sanitize input cho `city`, `date`, `activity`
- Cần tránh để output nội bộ như Thought/Action lộ ra giao diện người dùng
- Cần tách rõ dữ liệu tool output và câu trả lời hiển thị

### Guardrails
- Giới hạn số vòng loop để tránh infinite loop và tăng chi phí
- Nếu thiếu `city`, `date`, hoặc `activity` thì phải hỏi lại trước
- Nếu tool trả lỗi thì không được dừng ngay, mà cần có fallback strategy
- Chặn các truy vấn ngoài domain thời tiết / hoạt động ngoài trời

### Scaling
Nếu đưa lên production, hệ thống có thể mở rộng theo các hướng:
- thêm geocoding để hỗ trợ địa điểm chính xác hơn
- thêm backup provider
- thêm rule engine mạnh hơn cho `assess_outdoor_suitability(...)`
- chuyển sang framework orchestration như LangGraph nếu workflow có nhiều nhánh hơn
- bổ sung theo dõi chi phí và latency chi tiết hơn

---

## 7. Team Contribution

| Thành viên | MSSV | Vai trò |
|---|---|---|
| Nguyễn Mạnh Quyền | 2A202600481 | Viết tool + docs |
| Vũ Quang Dũng | 2A202600442 | Agent gọi tool |
| Nguyễn Trương Công Nhị | 2A202600505 | Tổng hợp code, kết nối tool + API |
| Phạm Hoàng Long | 2A202600261 | UI/UX |

---

## 8. Conclusion

Trong bài toán **Weather Outdoor Planner**, kết quả của nhóm cho thấy:

- **Chatbot Baseline** chỉ phù hợp để làm mốc so sánh, vì không có khả năng xử lý tốt các truy vấn thời tiết thực tế.
- **ReAct Agent v1** là phiên bản mạnh nhất về chất lượng reasoning và reliability.
- **ReAct Agent v2** cho thấy một hướng cải thiện về UX và token efficiency, nhưng chưa đủ mạnh về robustness khi gặp lỗi từ tool.

Từ thí nghiệm này, nhóm rút ra hai kết luận quan trọng:
1. Trong hệ thống agentic, **tool usage** là điều kiện bắt buộc nếu muốn giải các bài toán cần dữ liệu thời gian thực.
2. **Failure analysis và trace quality** quan trọng không kém việc hệ thống chạy được, vì chỉ khi đọc đúng trace và hiểu đúng lỗi thì mới cải tiến hệ thống theo hướng thực sự hiệu quả.