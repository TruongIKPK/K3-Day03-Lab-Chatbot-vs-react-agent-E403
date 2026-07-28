# ⚡ QUY TẮC HIỆU NĂNG (PERFORMANCE RULES)

1. **Giới hạn số vòng lặp (`MAX_ITERATIONS = 3`)**: Tránh để ReAct Loop chạy quá 3 bước gây lãng phí token và thời gian phản hồi.
2. **Tối ưu Prompt**: Giữ System Prompt ngắn gọn, súc tích, chỉ chứa danh sách Tool cần thiết.
3. **Caching**: Cache thông tin danh mục hoặc cấu hình chính sách đổi trả nếu không thay đổi thường xuyên.
