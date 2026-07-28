# ⚠️ CÁC LỖI THƯỜNG GẶP & KHẮC PHỤC (KNOWN ISSUES & EDGE CASES)

1. **Khách hàng nhập sai mã đơn hàng (VD: `ORD-99999`)**:
   - *Hành vi*: Tool trả về `LỖI: Không tìm thấy đơn hàng ORD-99999 trong hệ thống.`
   - *Cách xử lý của Agent*: Agent đọc Observation, thông báo cho khách kiểm tra lại mã và gợi ý gọi tool `get_user_orders` để xem danh sách đơn của mình.
2. **Khách yêu cầu đổi trả đơn hàng đã giao quá 7 ngày**:
   - *Hành vi*: Tool `check_return_eligibility` trả về `KHÔNG HỢP LỆ (Quá hạn 7 ngày)`.
   - *Cách xử lý của Agent*: Agent từ chối tạo `ReturnRequest` và giải thích quy định chính sách đổi trả nhẹ nhàng, lịch sự.
