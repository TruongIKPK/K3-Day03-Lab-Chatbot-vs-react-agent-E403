# 🎯 NHẬT KÝ QUYẾT ĐỊNH KIẾN TRÚC (DECISIONS LOG)

## ADR-001: Lựa chọn mô hình ReAct Agent (Cấp 3) thay vì Chatbot Cấp 2
- **Bối cảnh**: Khách hàng thương mại điện tử cần tra cứu số liệu thực tế thời gian thực và tự động tạo đơn đổi trả.
- **Quyết định**: Dùng ReAct Agent với 5 Tools chủ đạo (`get_order_details`, `get_shipping_status`, `check_return_eligibility`, `create_return_request`, `get_user_orders`).
- **Hệ quả**: Giải quyết triệt để vấn đề ảo giác (Hallucination) của Chatbot Cấp 2.
