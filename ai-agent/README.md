# 🤖 AI AGENT: TRỢ LÝ TRA CỨU ĐƠN HÀNG & XỬ LÝ ĐỔI TRẢ (E-COMMERCE ORDER & RETURN ASSISTANT)

> **Dự án**: Hệ thống AI Agent Cấp 3 (ReAct Agent) ứng dụng trong thương mại điện tử - Tra cứu trạng thái đơn hàng, vận chuyển và tự động xử lý yêu cầu đổi trả sản phẩm.

---

## 💡 1. NỀN TẢNG LÝ THUYẾT: 4 CẤP ĐỘ AI HỘI THOẠI

Hệ thống được thiết kế dựa trên sự tiến hóa qua 4 cấp độ của AI tương tác:

| Cấp độ | Loại hệ thống | Đặc điểm chính | Sự xuất hiện trong Bài Lab |
| :--- | :--- | :--- | :--- |
| **Cấp 1** | **Rule-Based Bot** | Khớp từ khóa `if/else` cố định, phản hồi theo kịch bản cứng, không có LLM. | Phân tích lịch sử & giới hạn |
| **Cấp 2** | **LLM Chatbot** | Dùng LLM sinh văn bản mượt mà, nhưng **không có khả năng gọi Tool** hay truy vấn database thực tế. | `CHATBOT_BASELINE` (Phần so sánh) |
| **Cấp 3** | **Reactive Agent (ReAct)** | Suy luận chuỗi `Thought -> Action -> Observation`, tự chọn & kích hoạt **Tools** tra cứu DB/xử lý nghiệp vụ. | **TRỌNG TÂM DỰ ÁN** |
| **Cấp 4** | **Autonomous Agent** | Tự rã mục tiêu (Planning), tự đánh giá (Self-Reflection), có Long-term Memory & Multi-agent collaboration. | Định hướng nâng cao |

---

## 🥊 2. SO SÁNH CHATBOT CẤP 2 (BASELINE) VS REACT AGENT CẤP 3

### 🤖 Chatbot Thông Thường (Cấp 2) - "Chuyên Gia Lý Thuyết"
- **Hạn chế**: Chỉ trả lời dựa trên kiến thức tĩnh đã học.
- **Khi khách hỏi**: *"Đơn hàng ORD-8899 của tôi đang ở đâu và có đổi trả được không?"*
- **Phản hồi của Chatbot Cấp 2**: *"Chào bạn, để kiểm tra đơn hàng bạn vui lòng truy cập website hoặc liên hệ tổng đài..."* (Bị ảo giác hoặc từ chối do không truy cập được cơ sở dữ liệu thời gian thực).

### 🧠 ReAct Agent (Cấp 3) - "Trợ Lý Thực Hành"
- **Ưu điểm**: Vừa suy luận logic (Thought), vừa biết gọi công cụ (Action) tra cứu database thực tế, quan sát dữ liệu trả về (Observation) và đưa ra quyết định chính xác.
- **Quy trình xử lý của ReAct Agent**:
  1. `Thought`: Khách hàng muốn kiểm tra đơn hàng `ORD-8899`. Tôi cần dùng tool `get_order_details` để lấy thông tin đơn hàng này.
  2. `Action`: `get_order_details[order_code="ORD-8899"]`
  3. `Observation`: `{"order_code": "ORD-8899", "status": "DELIVERED", "delivered_at": "2026-07-25", "total": 1250000}`
  4. `Thought`: Đơn hàng đã giao ngày 25/07/2026 (trong vòng 7 ngày). Bây giờ tôi dùng tool `check_return_eligibility` để xác minh chính sách đổi trả.
  5. `Action`: `check_return_eligibility[order_code="ORD-8899"]`
  6. `Observation`: `{"eligible": true, "max_return_days": 7, "reason_allowed": ["DEFECTIVE", "WRONG_ITEM", "MIND_CHANGE"]}`
  7. `Thought`: Đơn hàng hợp lệ để đổi trả. Tôi sẽ tổng hợp câu trả lời cho khách hàng.
  8. `Final Answer`: Đơn hàng **ORD-8899** của bạn đã giao thành công vào ngày 25/07/2026. Đơn hàng hiện **ĐỦ ĐIỀU KIỆN ĐỔI TRẢ** (trong hạn 7 ngày). Bạn có muốn tôi khởi tạo yêu cầu đổi trả ngay bây giờ không?

---

## 🗄️ 3. TỔNG QUAN CƠ SỞ DỮ LIỆU & NGHIỆP VỤ

Hệ thống quản lý 11 thực thể cốt lõi trong sơ đồ E-Commerce:
- **Người dùng & Phiên thoại**: `User`, `ChatSession`, `ChatMessage`
- **Sản phẩm & Giỏ hàng**: `Category`, `Product`, `Cart`, `CartItem`
- **Đơn hàng & Giao hàng**: `Order`, `OrderItem`, `Shipping`
- **Đổi trả hàng**: `ReturnRequest`

---

## 📂 4. CẤU TRÚC THƯ MỤC AI-AGENT

```text
ai-agent/
├── README.md                 # Tài liệu tổng quan dự án & 4 Cấp độ AI
├── core/                     # Cấu hình lõi Agent
│   ├── system.prompt.md      # ReAct System Prompt chuyên biệt Đơn hàng & Đổi trả
│   ├── persona/              # Các vai trò (architect, backend, frontend, qa)
│   ├── rules/                # Quy tắc mã nguồn, an ninh, hiệu năng & đặt tên
│   └── templates/            # Mẫu prompt theo các dạng bài toán
├── context/                  # Ngữ cảnh hệ thống
│   ├── database.md           # Schema 11 bảng DB, quan hệ & Enums chi tiết
│   ├── architecture.md       # Kiến trúc ReAct Agent Loop & Safeguards
│   ├── api.md                # Khai báo các Tools (APIs) tra cứu & tạo đơn đổi trả
│   └── stack.md              # Công nghệ sử dụng (Python, LLM Provider, SQLite)
├── memory/                   # Ghi nhớ & Quy ước
│   ├── conventions.md        # Quy ước code & nghiệp vụ đổi trả
│   ├── decisions.md          # Lịch sử quyết định kiến trúc
│   └── known-issues.md       # Các lỗi thường gặp & cách xử lý (Edge Cases)
├── commands/                 # Các lệnh Prompt điều khiển Agent
│   ├── fix-bug.md            # Sửa lỗi logic đổi trả / tool
│   ├── generate-feature.md   # Phát triển tính năng mới
│   ├── optimize.md           # Tối ưu hóa prompt & vòng lặp
│   └── review-code.md        # Kiểm thử mã nguồn
└── workflows/                # Quy trình thực thi nghiệp vụ
    ├── bugfix-flow.md        # Quy trình xử lý lỗi
    ├── deploy-flow.md        # Quy trình đóng gói & triển khai
    ├── feature-flow.md       # Quy trình thêm tool mới
    └── review-flow.md        # Quy trình đánh giá Trace Log
```
