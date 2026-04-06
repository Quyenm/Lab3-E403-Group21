# REPORT_NGUYEN_MANH_QUYEN

## Individual Report: Lab 3 - Chatbot vs ReAct Agent

**Student Name:** Nguyễn Mạnh Quyền  
**Student ID:** 2A202600481  
**Date:** 2026-04-06

---

## I. Technical Contribution (15 Points)

Trong project **Weather Outdoor Planner**, phần việc chính của em là **viết tool** và **viết documentation** cho hệ thống.

### Modules Implemented
- `src/tools/weather_tools.py` hoặc file tools tương đương trong project
- Các phần docs liên quan đến:
  - use case
  - tool list
  - test cases
  - system prompt
  - flowchart explanation
  - evaluation support

### Code Highlights
Em tập trung làm 3 tool chính:

1. **`get_current_weather(city)`**  
   Tool này dùng để lấy thời tiết hiện tại của một thành phố.  
   Output chính gồm nhiệt độ, độ ẩm, gió, mô tả thời tiết.

2. **`get_forecast(city, date)`**  
   Tool này dùng để lấy dự báo thời tiết cho một ngày cụ thể.  
   Em có định hướng chuẩn hóa output để agent không phải đọc raw JSON quá dài từ API.

3. **`assess_outdoor_suitability(activity, weather_data)`**  
   Đây là tool quan trọng nhất về mặt use case, vì nó không chỉ lấy dữ liệu mà còn biến dữ liệu thời tiết thành gợi ý thực tế, ví dụ có phù hợp đi chơi ngoài trời hay không.

### Documentation
Ngoài phần code tool, em còn làm phần docs để nhóm có cấu trúc rõ ràng hơn. Cụ thể gồm:
- mô tả use case **Weather Outdoor Planner**
- đặc tả tool list
- input / output của từng tool
- 5 test cases có mục đích
- system prompt
- giải thích flowchart
- hỗ trợ phần evaluation

### How My Code Interacts with the ReAct Loop
Tool em viết là phần để agent “hành động” trong vòng lặp ReAct.

- Ở bước **Thought**, agent xác định cần dữ liệu gì
- Ở bước **Action**, agent chọn tool phù hợp
- Ở bước **Observation**, output từ tool sẽ quay trở lại để agent suy luận tiếp

Ví dụ:
- nếu user hỏi thời tiết hiện tại → agent gọi `get_current_weather`
- nếu user hỏi ngày mai / cuối tuần → agent gọi `get_forecast`
- nếu user hỏi “có nên đi không” → agent kết hợp forecast với `assess_outdoor_suitability`

Nói ngắn gọn, phần em làm là giúp agent có dữ liệu thật để reasoning, chứ không chỉ trả lời theo kiến thức chung.

---

## II. Debugging Case Study (10 Points)

### Problem Description
Một lỗi mà em thấy khá đáng chú ý trong lab này là trường hợp agent gặp giới hạn của tool forecast nhưng không xử lý tốt.

Ví dụ ở các test case như:
- so sánh hai địa điểm trong cuối tuần
- gợi ý ngày tốt hơn để đi biển

có lúc tool trả về trạng thái kiểu:
`FORECAST_NOT_AVAILABLE`

Khi đó, agent có thể dừng luôn hoặc trả lời không hữu ích.

### Log Source
Phần này em dựa trên:
- log chạy test của nhóm
- trace trong evaluation
- quan sát ở các case như TC3 và TC4

### Diagnosis
Theo em, lỗi này không chỉ đến từ model mà đến từ cả **tool spec** và **agent policy**.

Cụ thể:
1. Tool có giới hạn nhưng agent chưa được hướng dẫn rõ phải làm gì khi tool fail
2. Prompt chưa nói rõ fallback strategy
3. Agent có xu hướng coi lỗi tool là điểm dừng cuối, thay vì coi đó là một observation để reasoning tiếp

Điều này cho em thấy một vấn đề rất thực tế:  
**tool viết ra không chỉ cần chạy đúng, mà còn cần trả lỗi rõ ràng để agent biết cách phản ứng.**

### Solution
Cách nhóm xử lý là:
- làm rõ hơn output khi tool lỗi
- bổ sung rule trong prompt để agent không dừng ngay khi tool fail
- hướng agent thử fallback như kiểm tra ngày gần nhất hoặc dữ liệu còn khả dụng

Về mặt cá nhân, sau case này em thấy khi viết tool thì không thể chỉ nghĩ đến “happy path”, mà phải nghĩ luôn:
- nếu lỗi thì output thế nào
- agent đọc lỗi đó ra sao
- có thể dùng lỗi đó như observation được không

### Result
Sau khi phân tích lỗi này, em hiểu rõ hơn rằng trong hệ thống agentic, **tool design ảnh hưởng trực tiếp đến chất lượng reasoning**.  
Đây là điều em thấy khác khá nhiều so với việc chỉ viết một function bình thường.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning: Thought block giúp agent như thế nào?
Điểm khác biệt rõ nhất giữa Chatbot và ReAct Agent là agent có thể chia một bài toán thành nhiều bước nhỏ.

Trong use case này:
- chatbot thường trả lời luôn
- agent thì biết dừng lại để xác định mình cần dữ liệu gì trước

Ví dụ nếu user hỏi:
“Cuối tuần này giữa Đà Lạt và Nha Trang chỗ nào đẹp hơn để đi chơi?”

thì chatbot dễ trả lời theo kiểu chung chung.  
Còn agent có thể:
1. lấy forecast của Đà Lạt
2. lấy forecast của Nha Trang
3. so sánh
4. kết luận

Theo em, chính cái block **Thought** làm cho agent “biết nghĩ trước khi làm”, thay vì trả lời ngay.

### 2. Reliability: Khi nào agent lại kém chatbot?
Agent không phải lúc nào cũng hơn hoàn toàn.

Trong bài này có lúc agent làm chưa tốt, ví dụ:
- lộ `Thought` và `Action` ra output
- gặp lỗi tool thì dừng luôn
- đúng logic nhưng trải nghiệm người dùng không tự nhiên

Trong khi đó, chatbot dù không có grounding tốt, nhưng đôi lúc lại trả lời trơn tru hơn về mặt ngôn ngữ.

Điều này làm em thấy rằng:
- **agent mạnh hơn về năng lực giải bài toán**
- nhưng **chatbot đôi lúc mượt hơn về mặt UX**
- hệ thống tốt cần cân bằng cả hai

### 3. Observation: Feedback từ môi trường ảnh hưởng thế nào?
Theo em, observation là phần quan trọng nhất trong ReAct.

Vì khi tool trả về dữ liệu thật, agent có thể đổi hướng reasoning ngay lập tức:
- forecast đẹp → xác nhận ngày đi
- forecast xấu → đổi ngày hoặc đổi gợi ý
- tool lỗi → hỏi lại hoặc fallback

Nếu không có observation, agent chỉ đang “đoán”.  
Còn khi có observation, agent mới thực sự đang phản ứng với môi trường.

Đây là điểm em thấy khác biệt rõ nhất giữa chatbot thường và agent.

---

## IV. Future Improvements (5 Points)

### Scalability
Nếu phát triển thêm, em nghĩ hệ thống này nên:
- tách rõ phần tool thành service riêng
- thêm geocoding để hỗ trợ địa điểm linh hoạt hơn
- hỗ trợ queue hoặc async nếu số lượng request tăng

### Safety
Về safety, em sẽ ưu tiên:
- validate kỹ `city`, `date`, `activity`
- không để lộ Thought/Action ra output cuối
- thêm rule rõ ràng cho fallback khi tool fail
- chặn các query ngoài domain weather/outdoor planning

### Performance
Để cải thiện hiệu năng, em sẽ:
- tối ưu prompt để giảm token
- cache kết quả thời tiết ngắn hạn
- chuẩn hóa output tool để agent đọc nhanh hơn
- thêm cơ chế chọn tool gọn hơn nếu sau này số lượng tool tăng

### Long-term Direction
Nếu mở rộng tiếp, em nghĩ hệ thống này có thể phát triển thành:
- travel planner assistant
- hệ multi-agent, trong đó mỗi agent phụ trách một phần
- hoặc hệ tích hợp thêm RAG để lấy thông tin du lịch, địa điểm, phương tiện

---

## Conclusion

Qua bài lab này, em thấy phần **tool design** không hề là phần phụ, mà là phần rất quan trọng trong hệ thống agentic.  
Đóng góp chính của em là xây dựng tool và documentation để hệ thống có nền tảng rõ ràng cho việc reasoning trên dữ liệu thật.

Điều em rút ra lớn nhất là:  
**một agent tốt không chỉ cần model tốt, mà còn cần tool tốt, schema output rõ ràng, và cách xử lý lỗi hợp lý.**