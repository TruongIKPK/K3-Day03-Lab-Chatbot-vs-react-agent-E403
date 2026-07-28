# 📌 QUY ƯỚC NGHIỆP VỤ & CODE (CONVENTIONS)

1. Mọi truy vấn đơn hàng đều ưu tiên sử dụng mã đơn hàng `order_code` thay vì `id` số nguyên để thân thiện với khách hàng.
2. Chính sách hạn đổi trả mặc định là 7 ngày tính từ mốc `delivered_at` của bảng `Shipping`.
3. Khi tạo `ReturnRequest`, `status` khởi tạo luôn là `REQUESTED`.
