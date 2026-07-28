# 📋 SỔ TAY PHÂN CÔNG & CHECKLIST THỰC HÀNH (ZERO-CONFLICT WORKFLOW)
## 🛒 ĐỀ TÀI: TRỢ LÝ TRA CỨU ĐƠN HÀNG & XỬ LÝ ĐỔI TRẢ (E-COMMERCE ORDER & RETURN ASSISTANT)

> 💡 **Hướng dẫn**: Mỗi thành viên mở đúng file được phân công trong thư mục dự án và thực hiện checklist theo 4 Mốc.

---

## 💡 1. NỀN TẢNG LÝ THUYẾT: 4 CẤP ĐỘ AI HỘI THOẠI IN THE LAB

| Cấp độ | Loại hệ thống | Đặc điểm chính | Phân bổ trong bài lab |
| :--- | :--- | :--- | :--- |
| **Cấp 1** | **Rule-Based Bot** | Khớp từ khóa `if/else` cố định, không có LLM | Minh họa lịch sử |
| **Cấp 2** | **LLM Chatbot** | Dùng LLM sinh text mượt, nhưng **không gọi được Tool** (bị ảo giác/không biết DB thực tế) | `CHATBOT_BASELINE` (Phần so sánh) |
| **Cấp 3** | **Reactive Agent** | Suy luận `Thought -> Action -> Observation` & gọi **Tool** tra cứu DB thực tế | **ReAct Agent Loop (Trọng tâm Bài Lab)** |
| **Cấp 4** | **Autonomous Agent** | Tự rã mục tiêu (Planning), tự đánh giá (Self-Reflection) & có Memory | Phần Bonus Nâng cao (+10%) |

---

## 🗄️ 2. MÔ HÌNH DỮ LIỆU THỰC THỂ (11 BẢNG DATABASE)

Hệ thống quản lý các bảng:
- `User` (1 - 1 `Cart`, 1 - * `Order`, 1 - * `ReturnRequest`, 1 - * `ChatSession`)
- `Category` (1 - * `Product`)
- `Product` (1 - * `CartItem`, 1 - * `OrderItem`)
- `Cart` (1 - * `CartItem`)
- `Order` (1 - * `OrderItem`, 1 - 1 `Shipping`, 1 - * `ReturnRequest`)
- `Shipping` (Thông tin giao hàng: carrier, tracking_number, status, delivered_at)
- `ReturnRequest` (Yêu cầu đổi trả: reason, description, status, image_url)
- `ChatSession` (1 - * `ChatMessage`)

---

## 👥 3. BẢNG PHÂN VAI & FILE ĐẢM NHẬN

| Vai trò (Role) | File đảm nhận | Nhiệm vụ chính trong Đề tài Đơn Hàng & Đổi Trả | Người đảm nhận |
| :--- | :--- | :--- | :--- |
| **Role 1: Product Architect** | `config/test_cases.json` | Định hướng bài toán Tra cứu Đơn & Đổi trả. Soạn 5 Test Cases (Câu thường, câu tra cứu đơn, tra cứu vận chuyển, tạo đơn đổi trả, bẫy quá hạn 7 ngày). | `2A202601247 - Trần Duy Trường` |
| **Role 2: Tool Engineer** | `src/tools.py` | Viết 5 Tools: `get_order_details`, `get_shipping_status`, `check_return_eligibility`, `create_return_request`, `get_user_orders`. | `2A202601165 - Nguyễn Quang Huy` |
| **Role 3: Prompt Engineer** | `src/prompts.py` | Viết `CHATBOT_BASELINE_PROMPT` và `REACT_SYSTEM_PROMPT` cài đặt phanh Guardrail 7 ngày đổi trả & `MAX_ITERATIONS = 3`. | `2A202601907 - Hồ Văn Thi` |
| **Role 4: Core Developer / Integrator** | `src/app.py` | **Đầu mối kéo code (`git pull`), Vibe Code kết nối Tools + Prompts + Test cases hoàn thiện App chạy demo.** | `2A202601541 - Lê Nguyễn Phi Trường` |
| **Role 5: Observability Analyst** | `docs/trace_eval.md` | Điền Scoring Matrix & Ghi nhật ký Trace Log so sánh Chatbot Cấp 2 vs ReAct Agent Cấp 3. | `2A202601843 - Nguyễn Khánh Toàn` |

---

## ⏱️ 4. CHECKLIST THỰC HÀNH THEO 4 MỐC

### 📍 MỐC 1: Định hình & Đánh giá độ phù hợp (Agentic Fit) (20 phút)

*Mục tiêu: Chứng minh bài toán Tra cứu đơn hàng & Đổi trả CẦN dùng Agent Cấp 3 chứ không chỉ Chatbot Cấp 2.*

- [ ] **Role 1 & Cả nhóm**: Thống nhất đề tài **Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả** dựa trên CSDL 11 bảng.
- [ ] **Role 5**: Điền bảng **Scoring Matrix** (chấm 1–5 điểm cho 4 tiêu chí: Data Freshness, Multi-step Logic, Tool Integration, Safeguards) vào `docs/trace_eval.md`.
- [ ] **Role 2**: Liệt kê 5 tên công cụ sẽ tạo trong `src/tools.py` (`get_order_details`, `get_shipping_status`, `check_return_eligibility`, `create_return_request`, `get_user_orders`).
- [ ] **Role 3**: Xác định các trường hợp Tool bị lỗi (Failure Modes): Khách nhập sai mã đơn, đơn giao quá 7 ngày, đơn đã hủy.
- [ ] **Role 4**: Mở Terminal gõ `python src/app.py` kiểm tra xem môi trường Python sẵn sàng chưa.
- [ ] 🤝 **Cả nhóm**: Gật đầu thống nhất bài toán trước khi sang Mốc 2.
- [ ] 🔄 **Đồng bộ Git Mốc 1**: `git add .` ➔ `git commit -m "Moc 1: Scoring Matrix & Dinh hinh de tai Don hang & Doi tra"` ➔ `git push`.

---

### 📍 MỐC 2: Baseline Chatbot & Khai báo Tool Specs (30 phút)

*Mục tiêu: Thấy rõ hạn chế của Chatbot Cấp 2 (bị ảo giác khi hỏi về đơn ORD-8899) và chuẩn hóa 5 công cụ cho ReAct Agent.*

- [ ] **Role 1**: Viết bộ **Test Cases** Đơn hàng & Đổi trả vào file `config/test_cases.json`.
- [ ] **Role 2**: Dùng AI viết Docstring chuẩn và logic giả lập DB cho 5 hàm trong `src/tools.py`.
- [ ] **Role 3**: Soạn `CHATBOT_BASELINE_PROMPT` trong file `src/prompts.py`.
- [ ] **Role 4 (Đầu mối Lắp ráp)**: Gõ `git pull` ➔ Vibe Code nối `run_baseline_chatbot()` trong `src/app.py` và bấm chạy thử.
- [ ] **Role 5**: Ghi lại phản hồi từ chối/ảo giác của Chatbot Cấp 2 khi hỏi về đơn `ORD-8899` vào `docs/trace_eval.md`.
- [ ] 🔄 **Đồng bộ Git Mốc 2**: `git add .` ➔ `git commit -m "Moc 2: Chatbot Baseline & Tool Specs Don Hang"` ➔ `git push`.

---

### 📍 MỐC 3: ReAct Loop & Safeguards (60 phút)

*Mục tiêu: Dựng ReAct Agent Cấp 3 suy luận Thought -> Action -> Observation và cài phanh Guardrail 7 ngày đổi trả.*

- [ ] **Role 3**: Soạn `REACT_SYSTEM_PROMPT` (ép AI sinh `Thought -> Action`) và đặt `MAX_ITERATIONS = 3` trong `src/prompts.py`.
- [ ] **Role 2**: Đảm bảo các hàm trong `src/tools.py` khi gặp lỗi (mã đơn không tồn tại) sẽ trả về chuỗi `LỖI: ...` chứ không crash code.
- [ ] **Role 4 (Đầu mối Lắp ráp & Vibe App)**: Gõ `git pull` ➔ Vibe Code lắp vòng lặp ReAct Agent Loop hoàn chỉnh trong `src/app.py` và chạy thử nghiệm.
- [ ] **Role 5**: Trích xuất chuỗi `Thought -> Action -> Observation` dán vào `docs/trace_eval.md`.
- [ ] **Role 1**: Kiểm tra xem Agent có từ chối đổi trả khi đơn giao quá 7 ngày (Edge Case bẫy chính sách) hay không.
- [ ] 🔄 **Đồng bộ Git Mốc 3**: `git add .` ➔ `git commit -m "Moc 3: ReAct Agent Loop & Safeguards 7 ngay doi tra"` ➔ `git push`.

---

### 📍 MỐC 4: Tương tác liên nhóm & Hybrid Flowchart (40 phút)

*Mục tiêu: Thử thách khả năng chịu lỗi trước đòn tấn công từ nhóm khác & Chấm chéo linh hoạt.*

- [ ] ⚔️ **Đội Tấn Công**: Dùng các mã đơn bẫy (như `ORD-99999` hoặc đơn đã hủy `ORD-CANCELLED`) tấn công Agent nhóm bạn.
- [ ] 🛡️ **Đội Phòng Thủ**: Quan sát Agent phản ứng với thông báo lỗi và từ chối an toàn.
- [ ] **Role 5 (Observability)**: Hoàn thiện file `docs/trace_eval.md` và vẽ sơ đồ phân luồng trong `docs/hybrid_flowchart.mermaid`.
- [ ] 🔄 **Đồng bộ Git Mốc 4 (Hoàn thành)**: `git add .` ➔ `git commit -m "Moc 4: Complete Order & Return AI Agent"` ➔ `git push`.

---

## 🛠️ PHẦN BỔ SUNG: NGUYÊN TẮC PHỐI HỢP GIT

1. **Trước khi gõ code**: `git pull`
2. **Sau khi làm xong mốc**: `git add .` ➔ `git commit -m "Role X: ..." ` ➔ `git push`
