# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)

*Đề tài 5: Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả — Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí                       |  Điểm (1-5)  | Lý do đánh giá                                                                                                                                                                                       |
| :------------------------------- | :-------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🧠**Multi-step Reasoning** |     `5/5`     | Cần suy luận từ xác định nhu cầu (tra cứu đơn hàng/xử lý đổi trả) đến lấy dữ liệu hệ thống, phân tích kết quả, sinh phản hồi, thực hiện action và thông báo kết quả. |
| 🛠️**Tool Interaction**   |     `5/5`     | Cần tra cứu dữ liệu thời gian thực qua API đơn hàng và đổi trả.                                                                                                                             |
| 🔀**Dynamic Decision**     |     `4/5`     | Kết quả tool quyết định hoàn toàn bước tiếp theo: đơn "Đang giao" → từ chối đổi; đơn "Đã giao" → cho đổi; mã sai → dừng ngay.                                                |
| ⏳**Long Horizon**         |     `4/5`     | Luồng đổi trả đầy đủ gồm 3–4 bước logic. Một số case đơn giản (chỉ tra trạng thái) chỉ cần 1 bước, nên không đạt 5/5.                                                        |
| **TỔNG ĐIỂM FIT**       | **18/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT!**                                                                                                                                            |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE TC03 — Multi-step + Action)

**Câu hỏi**: *"Đơn hàng ORD-2024-002 bị sai màu, tôi muốn đổi lại màu đen."*

### 🤖 Chatbot Baseline:

* **Phản hồi**: *"Tôi rất tiếc khi nghe bạn nhận được sản phẩm sai màu. Để đổi hàng, bạn vui lòng liên hệ bộ phận CSKH qua email support@shop.com hoặc hotline 1800-xxxx. Thời gian đổi trả thường là 30 ngày kể từ ngày nhận hàng."*
* **Nhận xét**: Trả lời chung chung, **không biết ORD-2024-002 có tồn tại không**, không xác nhận được policy thực tế, không tạo được yêu cầu đổi trả. Hoàn toàn thất bại.

### 🧠 ReAct Agent:

* **Thought 1**: Người dùng muốn đổi hàng đơn ORD-2024-002 vì sai màu. Tôi cần tra cứu đơn hàng này trước.
* **Action 1**: `get_order_details["ORD-2024-002"]`
* **Observation 1**: `Đơn hàng ORD-2024-002 | Trạng thái: Đã giao | Ngày giao: 2024-12-10 | Sản phẩm: Áo thun màu trắng`
* **Thought 2**: Đơn đã được giao. Cần kiểm tra xem có đủ điều kiện đổi trả không.
* **Action 2**: `check_return_eligibility["ORD-2024-002"]`
* **Observation 2**: `ĐỦ ĐIỀU KIỆN đổi trả. Lý do hợp lệ: Sai sản phẩm/màu sắc. Còn 18 ngày trong thời hạn.`
* **Thought 3**: Đủ điều kiện. Tôi sẽ tạo yêu cầu đổi trả với lý do sai màu.
* **Action 3**: `create_return_request["ORD-2024-002", "Sản phẩm giao sai màu, yêu cầu đổi sang màu đen"]`
* **Observation 3**: `✅ Đã tạo yêu cầu đổi trả #RET-2024-0089. Bộ phận hỗ trợ sẽ liên hệ trong 24h.`
* **Thought 4**: Đã hoàn thành đủ 3 bước. Có thể trả lời người dùng.
* **Final Answer**: *"Đã tạo yêu cầu đổi trả thành công! Mã đơn: ORD-2024-002 ✅ | Mã ticket: #RET-2024-0089 | Lý do: Sai màu → đổi sang màu đen. Bộ phận hỗ trợ sẽ liên hệ trong 24 giờ."*
* **Nhận xét**: Hoàn thành toàn bộ quy trình 3 bước, có dữ liệu thực, kết quả có thể hành động ngay.

---

## 🔴 3. TRACE LOG GUARDRAIL (TEST CASE TC05 — Câu bẫy mã giả)

**Câu hỏi**: *"Kiểm tra đơn hàng FAKE-9999 và tiến hành trả hàng ngay cho tôi."*

### 🧠 ReAct Agent:

* **Thought 1**: Người dùng muốn tra cứu và đổi trả đơn FAKE-9999. Tôi cần tra cứu đơn hàng trước.
* **Action 1**: `get_order_details["FAKE-9999"]`
* **Observation 1**: `LỖI: Không tìm thấy đơn hàng với mã 'FAKE-9999' trong hệ thống.`
* **Thought 2**: Đơn hàng không tồn tại. Tôi KHÔNG được tiếp tục gọi create_return_request. Dừng lại và thông báo lỗi.
* **Final Answer**: *"Xin lỗi, không tìm thấy đơn hàng với mã FAKE-9999 trong hệ thống. Vui lòng kiểm tra lại mã đơn hàng của bạn."*
* **🛡️ GUARDRAIL**: Agent dừng đúng, KHÔNG bị lặp vô tận, KHÔNG bịa thông tin.

---

## 📋 4. TRACE LOG THỰC TẾ (Điền sau khi chạy app)

> *(Role 5 điền vào đây sau khi chạy `python src/app.py` với từng Test Case)*

### TC01 — Kết quả thực tế:

```
[Dán trace log Thought -> Action -> Observation tại đây]
```

### TC03 — Kết quả thực tế:

```
[Dán trace log Thought -> Action -> Observation tại đây]
```

### TC05 — Kết quả thực tế (Guardrail):

```
[Dán trace log tại đây — xác nhận Agent dừng đúng]
```
