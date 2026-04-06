# **Individual Report – Lab 3: Production-Grade Agentic System**

**Student Name:** Nguyễn Trương Công Nhị  
**Student ID:** 2A202600505  
**Role:** System Integration – Tool & API Connection  
**Project:** Weather Outdoor Planner  
**Deployment Date:** 2026-04-06

---

## **1. Overview of My Contribution**

Trong project _Weather Outdoor Planner_, tôi đảm nhận vai trò **tổng hợp hệ thống và tích hợp các thành phần kỹ thuật**, bao gồm:

- Kết nối **LLM với hệ thống tool**
    
- Thiết kế và triển khai **pipeline giao tiếp giữa agent và API**
    
- Chuẩn hóa **input/output format giữa các module**
    
- Đảm bảo **data flow xuyên suốt trong ReAct loop**
    

Vai trò của tôi mang tính **bridge layer (middleware)** giữa:

- Agent reasoning (LLM)
    
- Tool execution (weather APIs)
    
- Output formatting (UI layer)
    

---

## **2. System Integration Architecture**

### **2.1 End-to-End Data Flow**

Tôi triển khai luồng xử lý tổng thể như sau:

1. **User Input**
    
2. → Parse intent (simple vs multi-step)
    
3. → Agent quyết định gọi tool
    
4. → **API Layer (do tôi xây dựng)**
    
5. → Tool execution
    
6. → Return structured observation
    
7. → Inject lại vào agent context
    
8. → Final Answer
    

Điểm quan trọng nhất trong phần tôi phụ trách là:

> **Observation từ tool phải được chuẩn hóa và đưa ngược lại vào prompt đúng format để agent reasoning tiếp.**

---

### **2.2 Tool Integration Layer**

Tôi thiết kế interface thống nhất cho các tool:

#### **1. get_current_weather**

```json
{
  "city": "string"
}
```

#### **2. get_forecast**

```json
{
  "city": "string",
  "date": "string"
}
```

#### **3. assess_outdoor_suitability**

```json
{
  "activity": "string",
  "weather_data": "object"
}
```

### **Key Implementation Decisions**

- Chuẩn hóa toàn bộ output thành **JSON object**
    
- Thêm field trạng thái lỗi:
    

```json
{
  "status": "OK | ERROR",
  "data": {...},
  "error": "FORECAST_NOT_AVAILABLE"
}
```

- Điều này giúp agent:
    
    - detect lỗi
        
    - đưa ra fallback strategy
        

---

## **3. Handling ReAct Loop Communication**

Một trong những phần khó nhất tôi xử lý là:

### **Inject Observation vào Prompt**

Sau mỗi lần tool trả về, tôi đảm bảo:

- Observation được đưa vào đúng format:
    

```
Observation: {structured JSON}
```

- Không để:
    
    - mất dữ liệu
        
    - sai format → gây fail reasoning
        

---

### **Example Flow (Simplified)**

```
Thought → Need weather data
Action → get_forecast
Observation → {weather data}
Thought → Evaluate suitability
Action → assess_outdoor_suitability
Observation → {recommendation}
Final Answer → user-friendly response
```

Nếu thiếu bước injection đúng → agent sẽ:

- hallucinate
    
- hoặc dừng loop sớm
    

---

## **4. Key Challenges & Solutions**

### **4.1 Tool Response Constraint Handling**

**Problem:**  
Tool có thể trả:

```
FORECAST_NOT_AVAILABLE
```

**Issue observed (Agent v2):**

- Agent dừng ngay
    
- Không xử lý tiếp
    

**Root cause (liên quan integration):**

- Không enforce schema rõ ràng cho error handling
    

**Solution tôi đề xuất:**

- Chuẩn hóa error response
    
- Gợi ý thêm:
    
    - retry với ngày khác
        
    - fallback sang current weather
        

---

### **4.2 Data Consistency Between Tools**

**Problem:**

- Output của weather tool và input của suitability tool không đồng nhất
    

**Solution:**

- Chuẩn hóa weather_data schema:
    

```json
{
  "temperature": number,
  "humidity": number,
  "condition": "string",
  "wind_speed": number
}
```

→ giúp `assess_outdoor_suitability` hoạt động ổn định

---

### **4.3 Preventing Reasoning Leakage**

Dù phần này chủ yếu thuộc prompt design, nhưng integration cũng ảnh hưởng:

**Issue (Agent v1):**

- Output chứa:
    
    - Thought
        
    - Action
        

**Impact:**

- UX fail
    

**Observation:**

- Cần tách rõ:
    
    - internal state
        
    - final response
        

---

## **5. Performance Impact of My Work**

Những phần tôi triển khai ảnh hưởng trực tiếp tới:

### **1. Reliability**

- Agent v1 đạt **4/5**
    
- Lý do:
    
    - Tool integration ổn định
        
    - Data flow rõ ràng
        

### **2. Loop Stability**

- Average loop: **~2.4 steps**
    
- Không bị:
    
    - mất context
        
    - sai dữ liệu giữa các bước
        

### **3. Failure Cases (liên quan integration)**

|Case|Issue|
|---|---|
|TC3, TC4 (Agent v2)|Không xử lý lỗi tool|
|TC5 (Agent v1)|Không tách output|

---

## **6. Lessons Learned**

### **1. Integration quan trọng ngang với model**

Không chỉ LLM quyết định chất lượng hệ thống, mà:

> **Cách kết nối tool và format dữ liệu quyết định agent có hoạt động đúng hay không**

---

### **2. Structured Data > Free Text**

- JSON output giúp:
    
    - dễ parse
        
    - dễ debug
        
    - giảm hallucination
        

---

### **3. Error Handling là bắt buộc**

Nếu không có:

- fallback strategy
    
- retry logic
    

→ hệ thống sẽ fail ngay cả khi logic đúng

---

## **7. Future Improvements**

Nếu tiếp tục phát triển, tôi sẽ:

### **1. Thêm Retry & Fallback Layer**

- Auto thử:
    
    - ngày gần nhất
        
    - current weather
        

---

### **2. Introduce Tool Orchestrator**

- Ví dụ:
    
    - rule-based middleware
        
    - hoặc framework như LangGraph
        

---

### **3. Monitoring & Logging**

- Track:
    
    - tool call success rate
        
    - latency từng bước
        
    - error distribution
        

---

## **8. Conclusion**

Trong project này, tôi đóng vai trò đảm bảo:

> **Agent không chỉ “nghĩ được” mà còn “làm được” thông qua việc kết nối đúng với tool và API.**

Kết quả cho thấy:

- Một agent mạnh không chỉ cần reasoning tốt
    
- Mà cần:
    
    - **data flow rõ ràng**
        
    - **tool integration chuẩn**
        
    - **error handling đầy đủ**
        

Đây là yếu tố giúp **ReAct Agent v1 đạt reliability cao nhất trong hệ thống**.

---

Nếu bạn muốn, mình có thể:

- rút gọn xuống còn 1–2 trang để nộp
    
- hoặc format lại theo chuẩn IEEE / ACM paper cho “xịn” hơn 😄