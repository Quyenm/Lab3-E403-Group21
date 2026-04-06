# Individual Report: Lab 3 - Chatbot vs ReAct Agent
- **Student Name**: Pham Hoang Long  
- **Student ID**: 2A202600261  
- **Date**: 06/04/2026  

---

## I. Technical Contribution (15 Points)

Trong project này, tôi phụ trách phần **UI/UX cho hệ thống Weather Outdoor Planner**, tập trung vào việc xây dựng giao diện tương tác giữa người dùng và agent, đảm bảo trải nghiệm mượt mà, dễ hiểu và phù hợp với đặc thù của hệ thống agentic.

- **Modules Implemented**:
  - Chat UI (input + response rendering)
  - Streaming response (real-time output)
  - Integration frontend với backend agent (API / Python script)
  - Gradio-based demo interface

- **Code Highlights**:
  - Sử dụng **Gradio ChatInterface** để nhanh chóng xây dựng UI demo
  - Thiết kế hàm streaming bằng `yield` để hiển thị output theo thời gian thực
  - Kết nối trực tiếp với backend `chat_with_agent`
  - Xử lý hiển thị từng phần response thay vì đợi full output

- **Documentation**:

  Flow UI hoạt động như sau:

  1. User nhập câu hỏi (ví dụ: “Thời tiết Hà Nội hôm nay”)
  2. UI gửi request đến backend agent
  3. Backend xử lý (có thể qua nhiều bước reasoning + tool call)
  4. Response được stream từng phần về UI
  5. UI render theo thời gian thực (giống ChatGPT)

  Điểm quan trọng trong thiết kế là:
  - **Streaming giúp giảm cảm giác latency**
  - **Tăng độ tin tưởng của người dùng vào hệ thống**

---

## II. Debugging Case Study (10 Points)

- **Problem Description**:  
  Agent bị lỗi **lộ internal reasoning (Thought/Action)** trực tiếp lên UI (TC5).

- **Observation trên UI**:
    Thought: Need to ask user for location
    Action: Ask for city

- **Diagnosis**:
    - UI hiển thị raw output từ agent mà không có filter
    - Backend chưa tách biệt rõ giữa:
        - internal reasoning
        - final answer

- **Impact (UX)**:
    - Trải nghiệm người dùng bị phá vỡ
    - Output trở nên khó hiểu và không tự nhiên
    - Bị đánh giá là fail dù logic đúng

- **Solution**:
    - Cập nhật backend prompt để: chỉ trả về final answer
    - Định hướng UI: chỉ hiển thị nội dung đã được "clean"
    - Nếu thiếu thông tin: hiển thị câu hỏi tự nhiên thay vì action

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning (từ góc nhìn UI)

ReAct Agent mạnh hơn Chatbot ở khả năng:
- xử lý multi-step
- sử dụng dữ liệu thực

Tuy nhiên, từ góc nhìn UI:
- reasoning không nên hiển thị trực tiếp
- cần được "ẩn" hoặc chuyển thành dạng thân thiện với người dùng

---

### 2. Reliability

- Chatbot:
    - output ổn định (vì đơn giản)
    - nhưng thiếu chính xác

- Agent:
    - chính xác hơn
    - nhưng dễ gặp lỗi UX nếu:
        - lộ reasoning
        - output không được format tốt

👉 Insight:
**Reliability không chỉ là đúng/sai, mà còn là trải nghiệm người dùng**

---

### 3. Observation (ảnh hưởng đến UI)

Observation từ tool:
- giúp agent đưa ra câu trả lời chính xác hơn
- nhưng không nên hiển thị raw data lên UI

UI cần:
- chuyển dữ liệu thành dạng dễ hiểu
- tránh hiển thị JSON / technical output

---

## IV. Future Improvements (5 Points)

### UX Improvements
- Thêm trạng thái:
    - “Thinking...”
    - “Calling weather API...”

---

### Streaming Enhancements
- Stream theo token (thay vì theo word)
- Thêm typing animation

---

### Debug Mode
- Thêm chế độ:
    - hiển thị reasoning (dành cho developer)
    - ẩn reasoning (dành cho user)

---

### UI Scalability
- Chuyển từ Gradio sang React để:
- tùy biến UI tốt hơn
- deploy production

---

## V. Conclusion

Trong hệ thống Weather Outdoor Planner:

- Chatbot:
    - đơn giản
    - UX ổn định nhưng không hữu ích

- ReAct Agent:
    - mạnh về logic và dữ liệu
    - nhưng yêu cầu UI tốt để phát huy hiệu quả

👉 Từ góc nhìn UI/UX:

**Một agent tốt không chỉ cần reasoning đúng, mà còn cần trình bày output đúng cách.**

Streaming, formatting và kiểm soát output là các yếu tố quan trọng để:
- giảm latency cảm nhận
- tăng độ tin tưởng
- cải thiện trải nghiệm người dùng

---

## Tổng kết cá nhân

Đóng góp chính của tôi trong project là:

- Xây dựng UI tương tác cho agent
- Tích hợp streaming để cải thiện UX
- Phát hiện và xử lý vấn đề lộ reasoning

Qua đó, tôi nhận ra rằng:

> Trong hệ thống AI hiện đại, UI/UX không chỉ là phần hiển thị, mà là một phần quan trọng quyết định hệ thống có usable hay không.